from collections import defaultdict
from datetime import datetime, timezone
import os
import re
import requests

from config.skill_config import (
    EXCEPTIONAL_CONFIDENCE_THRESHOLD,
    GITHUB_LANGUAGE_MAP,
    MIN_CONFIRMED_SIGNALS,
    MIN_REPO_VIABILITY,
    PACKAGE_MARKERS,
    QUALITY_KEYWORDS,
    REPO_SIGNAL_CAP,
    SIGNAL_WEIGHTS,
    SKILL_KEYWORDS,
    STRUCTURE_MARKERS,
    TUTORIAL_MARKERS,
)

MAX_SIGNAL_WEIGHT = sum(SIGNAL_WEIGHTS.values())


def normalize_signal_text(text):
    return re.sub(r"[^a-z0-9]+", " ", str(text).lower()).strip()


def keyword_matches_text(text, keyword):
    normalized_text = normalize_signal_text(text)
    normalized_keyword = normalize_signal_text(keyword)

    if not normalized_text or not normalized_keyword:
        return False

    if len(normalized_keyword) <= 2:
        return normalized_keyword in normalized_text.split()

    return (
        normalized_keyword in normalized_text
        or normalized_text in normalized_keyword
        or normalized_keyword in normalized_text.split()
    )


def text_matches_any_keyword(text, keywords):
    return any(keyword_matches_text(text, keyword) for keyword in keywords)


def topic_matches_skill(topics, keywords):
    return any(text_matches_any_keyword(topic, keywords) for topic in topics)


def infer_repo_structure(repo):
    """Infer structure quality from repo metadata only."""
    name = normalize_signal_text(repo.get("name", ""))
    description = normalize_signal_text(repo.get("description") or "")
    topics = " ".join(
        normalize_signal_text(topic) for topic in repo.get("topics") or []
    )
    combined = f"{name} {description} {topics}"

    score = 0.0
    signals = []
    penalties = []

    size = repo.get("size", 0)
    if size >= 1000:
        score += 0.25
        signals.append("large codebase")
    elif size >= 300:
        score += 0.18
        signals.append("non-trivial codebase")
    elif size >= 80:
        score += 0.14
    elif size >= 30:
        score += 0.06
    elif size < 20:
        score -= 0.08
        penalties.append("single-file or tiny repo")

    if description:
        score += 0.05
    else:
        score -= 0.02
        penalties.append("missing description")

    if any(marker in combined for marker in STRUCTURE_MARKERS):
        score += 0.15
        signals.append("modular/project-oriented metadata")

    if any(marker in combined for marker in PACKAGE_MARKERS):
        score += 0.18
        signals.append("package/config indicator")

    if any(marker in combined for marker in TUTORIAL_MARKERS):
        score -= 0.3
        penalties.append("tutorial-like repo")

    if "clone" in combined or "demo" in combined:
        score -= 0.12

    score = max(0.02, min(score, 1.0))
    return round(score, 2), signals, penalties


def summarize_signal_support(repo_items):
    signal_counts = {signal_type: 0 for signal_type in SIGNAL_WEIGHTS}
    signal_strength = {signal_type: 0.0 for signal_type in SIGNAL_WEIGHTS}

    for item in repo_items:
        for signal_type in item["signals"]:
            signal_counts[signal_type] += 1
            signal_strength[signal_type] += item["signal_weight"]

    strongest_signals = [
        signal_type
        for signal_type in sorted(
            SIGNAL_WEIGHTS,
            key=lambda current: (
                signal_counts[current] * SIGNAL_WEIGHTS[current],
                signal_strength[current],
            ),
            reverse=True,
        )
        if signal_counts[signal_type] > 0
    ]

    return signal_counts, strongest_signals


def soft_cap_confidence(raw_confidence, repo_count, avg_quality, signal_counts):
    exceptional = (
        repo_count >= 3
        and avg_quality >= 0.6
        and signal_counts["language"] > 0
        and signal_counts["topic"] + signal_counts["keyword"] > 0
        and raw_confidence >= EXCEPTIONAL_CONFIDENCE_THRESHOLD
    )

    if raw_confidence <= 0.3:
        capped = raw_confidence
    elif raw_confidence <= 0.6:
        capped = 0.3 + (raw_confidence - 0.3) * 0.85
    elif raw_confidence <= 0.85:
        capped = 0.555 + (raw_confidence - 0.6) * 0.9
    else:
        capped = 0.78 + (raw_confidence - 0.85) * 0.5

    return round(min(capped, 1.0 if exceptional else 0.92), 4), exceptional


def build_signals_used(signal_counts):
    signals = []
    if signal_counts["language"]:
        signals.append("language")
    if signal_counts["topic"]:
        signals.append("topics")
    if signal_counts["keyword"]:
        signals.append("keywords")
    if signal_counts.get("structure", 0):
        signals.append("structure")
    return signals


def build_skill_explanation(metrics):
    signal_counts = metrics["signal_counts"]
    strongest_signals = metrics["strongest_signals"]
    top_repos = metrics["evidence"][:3]

    why_detected = (
        "language-led"
        if signal_counts["language"]
        else "topic-led" if signal_counts["topic"] else "keyword-led"
    )

    strength_factors = []
    if metrics["repo_count"] >= 3:
        strength_factors.append("multiple repositories")
    if metrics["avg_quality"] >= 0.6:
        strength_factors.append("high repo quality")
    if metrics.get("avg_structure", 0.0) >= 0.5:
        strength_factors.append("strong repo structure")
    if signal_counts["language"] > 0:
        strength_factors.append("language signal")
    if signal_counts["topic"] > 0:
        strength_factors.append("topic signal")
    if signal_counts["keyword"] > 0:
        strength_factors.append("keyword signal")
    if signal_counts.get("structure", 0) > 0:
        strength_factors.append("structure signal")

    weakness_factors = []
    if metrics["avg_quality"] < 0.35:
        weakness_factors.append("low repo quality")
    if metrics["repo_count"] == 1:
        weakness_factors.append("single-repo evidence")
    if signal_counts["keyword"] and not signal_counts["language"]:
        weakness_factors.append("keyword-heavy signal mix")
    if metrics.get("avg_structure", 0.0) < 0.3:
        weakness_factors.append("flat or unclear repo structure")
    if any(repo.startswith("test") or repo.startswith("demo") for repo in top_repos):
        weakness_factors.append("tutorial-like repos")

    return {
        "why_detected": why_detected,
        "signals_used": build_signals_used(signal_counts),
        "strength_factors": (
            strength_factors[:4] if strength_factors else ["consistent usage"]
        ),
        "weakness_factors": weakness_factors[:3],
        "strongest_signals": strongest_signals[:2],
    }


def score_repo_quality(repo, structure_score=0.0, penalties=None):
    """Compute metadata-only quality score for repository relevance."""
    score = 0.0

    stars = repo.get("stargazers_count", 0)
    forks = repo.get("forks_count", 0)
    size = repo.get("size", 0)
    description = (repo.get("description") or "").strip()
    combined_text = f"{repo.get('name', '')} {description}".lower()

    score += min(stars / 25, 1.0) * 0.25
    score += min(forks / 10, 1.0) * 0.15

    if description:
        score += 0.10

    if size >= 1000:
        score += 0.20
    elif size >= 300:
        score += 0.15
    elif size >= 80:
        score += 0.08

    updated_at = repo.get("pushed_at") or repo.get("updated_at")
    if updated_at:
        try:
            updated_dt = datetime.strptime(updated_at, "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=timezone.utc
            )
            days_old = (datetime.now(timezone.utc) - updated_dt).days
            if days_old <= 90:
                score += 0.15
            elif days_old <= 365:
                score += 0.10
            elif days_old <= 730:
                score += 0.05
        except ValueError:
            pass

    keyword_hits = sum(1 for kw in QUALITY_KEYWORDS if kw in combined_text)
    score += min(keyword_hits * 0.05, 0.15)

    # Structural quality is a strong proxy for serious project work.
    score += min(structure_score * 0.25, 0.25)

    if size < 20:
        score *= 0.6

    if penalties:
        if "tutorial-like repo" in penalties:
            score *= 0.5
        if "single-file or tiny repo" in penalties:
            score *= 0.7
        if "missing description" in penalties:
            score *= 0.95

    return round(min(score, 1.0), 2)


def register_skill_signal(
    skill_evidence,
    skill,
    repo_name,
    repo_quality,
    signal_type,
    structure_score=0.0,
    structure_signals=None,
    penalties=None,
):
    bucket = skill_evidence[skill]
    signal_weight = SIGNAL_WEIGHTS[signal_type]

    if repo_name not in bucket:
        bucket[repo_name] = {
            "repo": repo_name,
            "quality": repo_quality,
            "structure_score": structure_score,
            "structure_signals": structure_signals or [],
            "penalties": penalties or [],
            "signal_weight": 0.0,
            "signals": set(),
        }

    entry = bucket[repo_name]
    if signal_type in entry["signals"]:
        return

    entry["signals"].add(signal_type)
    entry["signal_weight"] = min(
        entry["signal_weight"] + signal_weight, REPO_SIGNAL_CAP
    )
    entry["structure_score"] = max(entry["structure_score"], structure_score)
    entry["structure_signals"] = list(
        dict.fromkeys(entry["structure_signals"] + (structure_signals or []))
    )
    entry["penalties"] = list(dict.fromkeys(entry["penalties"] + (penalties or [])))


def confirmed_repo_contribution(repo_item):
    signal_count = len(repo_item["signals"])
    structure_supported = repo_item["structure_score"] >= 0.35
    repo_viability = 0.6 * repo_item["quality"] + 0.4 * repo_item["structure_score"]

    # A skill only counts when we have at least two independent signals.
    if signal_count < MIN_CONFIRMED_SIGNALS:
        return 0.0, False

    if not structure_supported and signal_count < 3:
        return 0.0, False

    if repo_viability < MIN_REPO_VIABILITY:
        return 0.0, False

    signal_total = min(repo_item["signal_weight"], REPO_SIGNAL_CAP)
    quality_multiplier = 0.35 + 0.65 * repo_item["quality"]
    structure_multiplier = 0.5 + 0.5 * repo_item["structure_score"]
    contribution = signal_total * quality_multiplier * structure_multiplier

    if any("tutorial" in penalty for penalty in repo_item["penalties"]):
        contribution *= 0.55
    if any(
        "tiny repo" in penalty or "single-file" in penalty
        for penalty in repo_item["penalties"]
    ):
        contribution *= 0.7

    return round(min(contribution, 1.0), 4), True


def compute_skill_metrics(repo_items, total_repos):
    confirmed_items = []
    for item in repo_items:
        contribution, confirmed = confirmed_repo_contribution(item)
        if not confirmed:
            continue
        normalized_item = dict(item)
        normalized_item["contribution"] = contribution
        confirmed_items.append(normalized_item)

    repo_count = len(confirmed_items)
    if repo_count == 0:
        return {
            "raw_confidence": 0.0,
            "confidence": 0.0,
            "avg_quality": 0.0,
            "avg_structure": 0.0,
            "repo_count": 0,
            "evidence": [],
            "signal_counts": {signal_type: 0 for signal_type in SIGNAL_WEIGHTS},
            "strongest_signals": [],
            "exceptional": False,
        }

    weighted_usage = sum(item["contribution"] for item in confirmed_items)
    frequency = min(repo_count / max(total_repos, 1), 1.0)

    avg_quality = sum(
        item["quality"] * item["contribution"] for item in confirmed_items
    ) / max(weighted_usage, 1e-9)

    avg_structure = sum(
        item["structure_score"] * item["contribution"] for item in confirmed_items
    ) / max(weighted_usage, 1e-9)

    diversity_bonus = min(repo_count / 5, 1.0)
    raw_confidence = min(
        frequency * 0.35
        + avg_quality * 0.35
        + avg_structure * 0.15
        + diversity_bonus * 0.15,
        1.0,
    )

    signal_counts, strongest_signals = summarize_signal_support(confirmed_items)
    confidence, exceptional = soft_cap_confidence(
        raw_confidence, repo_count, avg_quality, signal_counts
    )

    top_evidence = [
        item["repo"]
        for item in sorted(
            confirmed_items,
            key=lambda item: (
                item["contribution"] * item["quality"],
                item["contribution"],
            ),
            reverse=True,
        )[:5]
    ]

    return {
        "raw_confidence": round(raw_confidence, 4),
        "confidence": confidence,
        "avg_quality": round(avg_quality, 2),
        "avg_structure": round(avg_structure, 2),
        "repo_count": repo_count,
        "evidence": top_evidence,
        "signal_counts": signal_counts,
        "strongest_signals": strongest_signals,
        "exceptional": exceptional,
    }


def normalize_skill_confidences(skill_metrics):
    if not skill_metrics:
        return {}

    max_raw = max(m["confidence"] for m in skill_metrics.values())
    if max_raw <= 0:
        max_raw = 1.0

    normalized = {}
    for skill, metrics in skill_metrics.items():
        normalized_relative = metrics["confidence"] / max_raw
        normalized_confidence = metrics["confidence"] * (
            0.8 + 0.2 * normalized_relative
        )
        final_confidence = min(
            normalized_confidence, 1.0 if metrics["exceptional"] else 0.88
        )
        explanation = build_skill_explanation(metrics)

        normalized[skill] = {
            "confidence": round(final_confidence, 2),
            "avg_quality": metrics["avg_quality"],
            "avg_structure": metrics["avg_structure"],
            "repo_count": metrics["repo_count"],
            "evidence": metrics["evidence"],
            "explanation": explanation,
        }

    return dict(
        sorted(
            normalized.items(),
            key=lambda item: item[1]["confidence"],
            reverse=True,
        )
    )


def build_compact_github_profile(profile):
    sorted_skills = sorted(
        profile["skills"].items(),
        key=lambda item: item[1].get("confidence", 0),
        reverse=True,
    )
    top_skills = [
        {
            "skill": skill,
            "confidence": details.get("confidence", 0),
            "evidence": details.get("evidence", []),
        }
        for skill, details in sorted_skills[:5]
    ]

    return {
        "username": profile["username"],
        "developer_level": profile["developer_level"],
        "skills_count": len(profile["skills"]),
        "top_skills": top_skills,
    }


def fetch_github_profile(username):
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    url = f"https://api.github.com/users/{username}/repos"
    params = {"per_page": 30, "sort": "updated"}

    try:
        res = requests.get(url, headers=headers, params=params, timeout=10)
        if res.status_code != 200:
            return None, "GitHub user not found or API limit reached."
    except requests.RequestException:
        return None, "GitHub API request failed."

    repos = [r for r in res.json() if not r.get("fork")]

    if not repos:
        return None, "No usable repositories found."

    skill_evidence = defaultdict(dict)
    repo_count = len(repos)
    structure_scores = []
    repo_quality_scores = []

    for repo in repos:
        repo_name = repo["name"]
        structure_score, structure_signals, structure_penalties = infer_repo_structure(
            repo
        )
        repo_quality_score = score_repo_quality(
            repo,
            structure_score=structure_score,
            penalties=structure_penalties,
        )
        structure_scores.append(structure_score)
        repo_quality_scores.append(repo_quality_score)
        topics = repo.get("topics") or []
        combined_text = f"{repo_name} {repo.get('description') or ''}"

        lang = repo.get("language")
        mapped_skill = GITHUB_LANGUAGE_MAP.get(lang)
        if mapped_skill:
            register_skill_signal(
                skill_evidence,
                mapped_skill,
                repo_name,
                repo_quality_score,
                signal_type="language",
                structure_score=structure_score,
                structure_signals=structure_signals,
                penalties=structure_penalties,
            )

        for skill, keywords in SKILL_KEYWORDS.items():
            topic_hit = bool(topics and topic_matches_skill(topics, keywords))
            keyword_hit = text_matches_any_keyword(combined_text, keywords)
            structure_hit = structure_score >= 0.35
            language_hit = mapped_skill == skill

            if topic_hit:
                register_skill_signal(
                    skill_evidence,
                    skill,
                    repo_name,
                    repo_quality_score,
                    signal_type="topic",
                    structure_score=structure_score,
                    structure_signals=structure_signals,
                    penalties=structure_penalties,
                )

            if keyword_hit:
                register_skill_signal(
                    skill_evidence,
                    skill,
                    repo_name,
                    repo_quality_score,
                    signal_type="keyword",
                    structure_score=structure_score,
                    structure_signals=structure_signals,
                    penalties=structure_penalties,
                )

            # Structure acts as confirmation, never as a standalone skill claim.
            if structure_hit and (topic_hit or keyword_hit or language_hit):
                register_skill_signal(
                    skill_evidence,
                    skill,
                    repo_name,
                    repo_quality_score,
                    signal_type="structure",
                    structure_score=structure_score,
                    structure_signals=structure_signals,
                    penalties=structure_penalties,
                )

    skill_metrics = {}
    for skill, repo_map in skill_evidence.items():
        repo_items = list(repo_map.values())
        metrics = compute_skill_metrics(repo_items, repo_count)
        if metrics["repo_count"] == 0:
            continue
        skill_metrics[skill] = metrics

    skills_profile = normalize_skill_confidences(skill_metrics)

    total_stars = sum(r.get("stargazers_count", 0) for r in repos)
    avg_repo_quality = round(sum(repo_quality_scores) / max(repo_count, 1), 2)
    avg_structure_score = round(sum(structure_scores) / max(repo_count, 1), 2)
    strong_skills = [
        skill_name
        for skill_name, skill_data in skills_profile.items()
        if skill_data["confidence"] >= 0.6
    ]
    strong_skill_count = len(strong_skills)
    skill_diversity = len(skills_profile)

    if (
        repo_count > 20
        and skill_diversity >= 5
        and avg_repo_quality >= 0.55
        and avg_structure_score >= 0.5
    ):
        level = "senior"
        level_reason = [
            f"{repo_count} repositories analyzed",
            f"skill diversity is high ({skill_diversity} skills detected)",
            f"average repo quality score: {avg_repo_quality:.2f}",
            f"average structure score: {avg_structure_score:.2f}",
            f"{strong_skill_count} strong skills detected",
        ]
    elif (
        repo_count >= 8
        and skill_diversity >= 3
        and avg_repo_quality >= 0.4
        and avg_structure_score >= 0.35
    ):
        level = "intermediate"
        level_reason = [
            f"{repo_count} repositories analyzed",
            f"moderate skill diversity ({skill_diversity} skills detected)",
            f"average repo quality score: {avg_repo_quality:.2f}",
            f"average structure score: {avg_structure_score:.2f}",
            f"{strong_skill_count} strong skills detected",
        ]
    elif repo_count >= 2 and skill_diversity >= 1:
        level = "junior"
        level_reason = [
            f"{repo_count} repositories analyzed",
            f"limited-to-moderate skill diversity ({skill_diversity} skills detected)",
            f"average repo quality score: {avg_repo_quality:.2f}",
            f"average structure score: {avg_structure_score:.2f}",
            f"{strong_skill_count} strong skills detected",
        ]
    else:
        level = "beginner"
        level_reason = [
            f"{repo_count} repositories analyzed",
            "minimal GitHub evidence available",
            f"average repo quality score: {avg_repo_quality:.2f}",
            f"average structure score: {avg_structure_score:.2f}",
            f"{strong_skill_count} strong skills detected",
        ]

    return {
        "username": username,
        "repos_analyzed": repo_count,
        "total_stars": total_stars,
        "avg_repo_quality": avg_repo_quality,
        "avg_structure_score": avg_structure_score,
        "skills": skills_profile,
        "developer_level": level,
        "developer_level_explanation": {
            "level": level,
            "reason": level_reason,
        },
    }, None
