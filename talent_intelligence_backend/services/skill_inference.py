from collections import defaultdict
from dataclasses import dataclass, field
from math import exp

from config.skill_config import (
    EXCEPTIONAL_CONFIDENCE_THRESHOLD,
    GITHUB_LANGUAGE_MAP,
    MIN_CONFIRMED_SIGNALS,
    MIN_REPO_VIABILITY,
    REPO_SIGNAL_CAP,
    SIGNAL_WEIGHTS,
    SKILL_KEYWORDS,
)
from services.repo_heuristics import (
    normalize_signal_text,
    text_matches_any_keyword,
    topic_matches_skill,
)


@dataclass
class SkillMetrics:
    raw_confidence: float = 0.0
    confidence: float = 0.0
    avg_quality: float = 0.0
    avg_structure: float = 0.0
    repo_type_pressure: float = 1.0
    repo_count: int = 0
    evidence: list[str] = field(default_factory=list)
    signal_counts: dict = field(default_factory=dict)
    strongest_signals: list[str] = field(default_factory=list)
    exceptional: bool = False


class SkillSignalExtractor:
    def extract(self, repo_features, skill, keywords, mapped_skill=None):
        combined_text = f"{repo_features.name} {repo_features.description}"
        topic_hit = bool(
            repo_features.topics and topic_matches_skill(repo_features.topics, keywords)
        )
        keyword_hit = text_matches_any_keyword(combined_text, keywords)
        language_hit = mapped_skill == skill
        structure_hit = repo_features.structure_score >= 0.35 and (
            topic_hit or keyword_hit or language_hit
        )

        return {
            "language_hit": language_hit,
            "topic_hit": topic_hit,
            "keyword_hit": keyword_hit,
            "structure_hit": structure_hit,
            "signal_weight": sum(
                SIGNAL_WEIGHTS[name]
                for name, hit in {
                    "language": language_hit,
                    "topic": topic_hit,
                    "keyword": keyword_hit,
                    "structure": structure_hit,
                }.items()
                if hit
            ),
        }


class SkillEvidenceStore:
    def __init__(self):
        self.data = defaultdict(list)

    def add(self, skill, repo_features, signals):
        entry = {
            "repo": repo_features.name,
            "quality": repo_features.quality_score,
            "repo_type": repo_features.repo_type,
            "repo_type_weight": repo_features.repo_type_weight,
            "structure_score": repo_features.structure_score,
            "structure_signals": list(repo_features.structure_signals),
            "penalties": list(repo_features.penalties),
            "signal_weight": min(signals.get("signal_weight", 0.0), REPO_SIGNAL_CAP),
            "signals": {
                name
                for name, hit in {
                    "language": signals.get("language_hit", False),
                    "topic": signals.get("topic_hit", False),
                    "keyword": signals.get("keyword_hit", False),
                    "structure": signals.get("structure_hit", False),
                }.items()
                if hit
            },
        }
        self.data[skill].append(entry)


class SkillScorer:
    def score(self, evidence_list, total_repos, repo_type_pressure=1.0):
        confirmed_items = []
        for item in evidence_list:
            contribution, confirmed = self._confirmed_repo_contribution(item)
            if not confirmed:
                continue
            normalized_item = dict(item)
            normalized_item["contribution"] = contribution
            confirmed_items.append(normalized_item)

        repo_count = len(confirmed_items)
        if repo_count == 0:
            return SkillMetrics(
                signal_counts={name: 0 for name in SIGNAL_WEIGHTS},
                strongest_signals=[],
            )

        weighted_usage = sum(item["contribution"] for item in confirmed_items)
        total_repo_type_weight = sum(
            item.get("repo_type_weight", 0.0) for item in confirmed_items
        )
        frequency = min(total_repo_type_weight / max(total_repos, 1), 1.0)

        avg_quality = sum(
            item["quality"] * item["contribution"] for item in confirmed_items
        ) / max(weighted_usage, 1e-9)
        avg_structure = sum(
            item["structure_score"] * item["contribution"] for item in confirmed_items
        ) / max(weighted_usage, 1e-9)

        diversity_bonus = min(repo_count / 5, 1.0)
        type_bonus = min(max(total_repo_type_weight / max(repo_count, 1), 0.0), 1.0)
        raw_confidence = min(
            frequency * 0.25
            + avg_quality * 0.3
            + avg_structure * 0.15
            + diversity_bonus * 0.15
            + type_bonus * 0.15,
            1.0,
        )

        signal_counts, strongest_signals = self._summarize_signal_support(
            confirmed_items
        )
        confidence, exceptional = self._soft_cap_confidence(
            raw_confidence * repo_type_pressure,
            repo_count,
            avg_quality,
            signal_counts,
        )

        evidence = [
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

        return SkillMetrics(
            raw_confidence=round(raw_confidence, 4),
            confidence=confidence,
            avg_quality=round(avg_quality, 2),
            avg_structure=round(avg_structure, 2),
            repo_type_pressure=round(repo_type_pressure, 2),
            repo_count=repo_count,
            evidence=evidence,
            signal_counts=signal_counts,
            strongest_signals=strongest_signals,
            exceptional=exceptional,
        )

    def _confirmed_repo_contribution(self, repo_item):
        signal_count = len(repo_item["signals"])
        structure_supported = repo_item["structure_score"] >= 0.35
        repo_viability = 0.6 * repo_item["quality"] + 0.4 * repo_item["structure_score"]
        repo_type_weight = repo_item.get("repo_type_weight", 0.0)

        if signal_count < MIN_CONFIRMED_SIGNALS:
            return 0.0, False
        if not structure_supported and signal_count < 3:
            return 0.0, False
        if repo_viability < MIN_REPO_VIABILITY:
            return 0.0, False

        contribution = repo_item["quality"] * repo_type_weight
        if repo_item.get("repo_type") == "tutorial_or_clone":
            contribution *= 0.15
        elif repo_item.get("repo_type") == "educational_content":
            contribution *= 0.0
        elif repo_item.get("repo_type") == "organization_repo":
            contribution *= 0.7

        if any("tutorial" in penalty for penalty in repo_item["penalties"]):
            contribution *= 0.55
        if any(
            "tiny repo" in penalty or "single-file" in penalty
            for penalty in repo_item["penalties"]
        ):
            contribution *= 0.7

        return round(min(contribution, 1.0), 4), True

    def _summarize_signal_support(self, repo_items):
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

    def _soft_cap_confidence(
        self, raw_confidence, repo_count, avg_quality, signal_counts
    ):
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
