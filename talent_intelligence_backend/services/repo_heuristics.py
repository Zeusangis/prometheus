from datetime import datetime, timezone
import re

from config.skill_config import (
    EDUCATIONAL_MARKERS,
    GITHUB_LANGUAGE_MAP,
    LIBRARY_MARKERS,
    PACKAGE_MARKERS,
    QUALITY_KEYWORDS,
    REPO_TYPE_WEIGHTS,
    STRUCTURE_MARKERS,
    TUTORIAL_MARKERS,
)


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


def normalize_repo_owner_type(repo):
    owner = repo.get("owner") or {}
    return str(owner.get("type") or "").strip().lower()


def normalize_repo_topics(repo):
    return [normalize_signal_text(topic) for topic in repo.get("topics") or []]


def infer_repo_structure(repo):
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


def classify_repo_intent(
    repo, structure_score=0.0, structure_signals=None, penalties=None
):
    name = normalize_signal_text(repo.get("name", ""))
    description = normalize_signal_text(repo.get("description") or "")
    topics = normalize_repo_topics(repo)
    combined = f"{name} {description} {' '.join(topics)}"
    owner_type = normalize_repo_owner_type(repo)
    structure_signals = structure_signals or []
    penalties = penalties or []

    educational_signal = text_matches_any_keyword(combined, EDUCATIONAL_MARKERS)
    tutorial_signal = text_matches_any_keyword(combined, TUTORIAL_MARKERS)
    library_signal = text_matches_any_keyword(combined, LIBRARY_MARKERS)
    package_signal = any(marker in combined for marker in PACKAGE_MARKERS)
    structure_signal = structure_score >= 0.35 or bool(structure_signals)
    low_signal = structure_score < 0.15 and not description and repo.get("size", 0) < 40

    repo_type = "unknown"
    reasons = []
    confidence = 0.2

    if educational_signal:
        repo_type = "educational_content"
        confidence = 0.96
        reasons.append("educational keywords present")
    elif tutorial_signal:
        repo_type = "tutorial_or_clone"
        confidence = 0.92
        reasons.append("tutorial/demo/clone style naming")
    elif owner_type == "organization":
        repo_type = "organization_repo"
        confidence = 0.88
        reasons.append("owned by organization account")
    elif library_signal or (
        package_signal and (structure_signal or repo.get("stargazers_count", 0) >= 5)
    ):
        repo_type = "library_or_framework"
        confidence = 0.84
        reasons.append("library/package/framework style signals")
    elif owner_type == "user" and (
        structure_signal or description or repo.get("stargazers_count", 0) > 0
    ):
        repo_type = "personal_project"
        confidence = 0.76
        reasons.append("user-owned project with project-like signals")
    elif not owner_type and structure_signal:
        repo_type = "personal_project"
        confidence = 0.7
        reasons.append("project-like structure without owner metadata")

    if repo_type == "personal_project" and any(
        "tutorial" in penalty for penalty in penalties
    ):
        repo_type = "tutorial_or_clone"
        confidence = max(confidence, 0.9)
        reasons.append("tutorial penalties present")

    if repo_type == "unknown" and low_signal:
        reasons.append("low signal repository metadata")

    return {
        "repo_type": repo_type,
        "repo_type_weight": REPO_TYPE_WEIGHTS[repo_type],
        "repo_type_confidence": round(confidence, 2),
        "repo_type_reason": reasons or ["heuristic fallback"],
        "low_signal": low_signal,
    }


def score_repo_quality(repo, structure_score=0.0, penalties=None):
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
