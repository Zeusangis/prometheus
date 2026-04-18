from collections import Counter
import os

from config.skill_config import GITHUB_LANGUAGE_MAP, SKILL_KEYWORDS
from services.github_client import GitHubClient
from services.profile_aggregation import DeveloperProfile, ProfileAggregator
from services.profile_presenter import ProfilePresenter
from services.repo_features import RepoFeatureExtractor
from services.skill_inference import (
    SkillEvidenceStore,
    SkillSignalExtractor,
    SkillScorer,
)


class GitHubIntelligenceService:
    def __init__(
        self,
        client=None,
        extractor=None,
        signal_extractor=None,
        scorer=None,
        aggregator=None,
        presenter=None,
    ):
        self.client = client or GitHubClient(token=os.environ.get("GITHUB_TOKEN"))
        self.extractor = extractor or RepoFeatureExtractor()
        self.signal_extractor = signal_extractor or SkillSignalExtractor()
        self.scorer = scorer or SkillScorer()
        self.aggregator = aggregator or ProfileAggregator()
        self.presenter = presenter or ProfilePresenter()

    def analyze(self, username):
        repos, error = self.client.get_repos(username)
        if error:
            return None, error

        repo_features = [self.extractor.extract(repo) for repo in repos]
        repo_distribution = self._repo_type_distribution(repo_features)
        repo_distribution_weighted = self._repo_type_distribution_weighted(
            repo_features
        )
        weighted_repo_type_signal = self._weighted_repo_type_signal(repo_features)
        uncertainty_indicator = self._uncertainty_indicator(
            repo_distribution,
            repo_features,
        )

        evidence_store = SkillEvidenceStore()
        for feature in repo_features:
            mapped_skill = GITHUB_LANGUAGE_MAP.get(feature.language)
            if mapped_skill:
                language_signals = self.signal_extractor.extract(
                    feature,
                    mapped_skill,
                    SKILL_KEYWORDS.get(mapped_skill, []),
                    mapped_skill=mapped_skill,
                )
                evidence_store.add(mapped_skill, feature, language_signals)

            for skill, keywords in SKILL_KEYWORDS.items():
                signals = self.signal_extractor.extract(
                    feature, skill, keywords, mapped_skill=mapped_skill
                )
                if any(
                    signals[name]
                    for name in (
                        "language_hit",
                        "topic_hit",
                        "keyword_hit",
                        "structure_hit",
                    )
                ):
                    evidence_store.add(skill, feature, signals)

        skill_metrics = {}
        for skill, evidence_list in evidence_store.data.items():
            skill_metrics[skill] = self.scorer.score(
                evidence_list,
                total_repos=len(repo_features),
                repo_type_pressure=uncertainty_indicator["confidence_multiplier"],
            )

        adjusted_confidence_scores = self._normalize_skill_confidences(skill_metrics)
        weighted_skills = {
            skill: {
                "weighted_score": round(
                    details.confidence * max(details.repo_count, 1), 3
                ),
                "repo_count": details.repo_count,
                "evidence": details.evidence,
                "repo_type_pressure": details.repo_type_pressure,
            }
            for skill, details in adjusted_confidence_scores.items()
        }

        avg_repo_quality = round(
            self._weighted_average(repo_features, "quality_score"), 2
        )
        avg_structure_score = round(
            self._weighted_average(repo_features, "structure_score"), 2
        )

        profile = self.aggregator.aggregate(
            username=username,
            repositories=[
                self._feature_to_repository_payload(feature)
                for feature in repo_features
            ],
            weighted_skills=weighted_skills,
            adjusted_confidence_scores=self._metrics_to_payload(
                adjusted_confidence_scores
            ),
            repo_type_distribution=repo_distribution,
            repo_type_distribution_weighted=repo_distribution_weighted,
            weighted_repo_type_signal=weighted_repo_type_signal,
            avg_repo_quality=avg_repo_quality,
            avg_structure_score=avg_structure_score,
            uncertainty_indicator=uncertainty_indicator,
        )

        return profile, None

    def present(self, profile):
        return self.presenter.build(profile)

    def present_compact(self, profile):
        return self.presenter.build_compact(profile)

    def _repo_type_distribution(self, repo_features):
        counts = Counter(feature.repo_type for feature in repo_features)
        for repo_type in [
            "personal_project",
            "library_or_framework",
            "unknown",
            "organization_repo",
            "tutorial_or_clone",
            "educational_content",
        ]:
            counts.setdefault(repo_type, 0)
        return dict(counts)

    def _repo_type_distribution_weighted(self, repo_features):
        total = sum(feature.repo_type_weight for feature in repo_features) or 1.0
        return {
            feature.repo_type: round(feature.repo_type_weight / total, 4)
            for feature in repo_features
        }

    def _weighted_repo_type_signal(self, repo_features):
        if not repo_features:
            return 0.0
        return round(
            sum(feature.repo_type_weight for feature in repo_features)
            / len(repo_features),
            4,
        )

    def _uncertainty_indicator(self, repo_distribution, repo_features):
        total = sum(repo_distribution.values()) or 1
        tutorial_share = repo_distribution.get("tutorial_or_clone", 0) / total
        educational_share = repo_distribution.get("educational_content", 0) / total
        organization_share = repo_distribution.get("organization_repo", 0) / total
        personal_share = repo_distribution.get("personal_project", 0) / total
        meaningful_share = (
            repo_distribution.get("personal_project", 0)
            + repo_distribution.get("library_or_framework", 0)
            + repo_distribution.get("unknown", 0)
        ) / total
        weighted_quality = self._weighted_average(repo_features, "quality_score")

        reasons = []
        level = "low"
        is_uncertain = False

        noisy_share = tutorial_share + educational_share
        if noisy_share >= 0.5:
            level = "high"
            is_uncertain = True
            reasons.append("tutorial or educational repositories dominate")
        elif noisy_share >= 0.3:
            level = "medium"
            is_uncertain = True
            reasons.append("noise-heavy repository mix")

        if meaningful_share < 0.35:
            level = "high"
            is_uncertain = True
            reasons.append("too few meaningful repositories")

        if personal_share < 0.2 and organization_share >= 0.5:
            level = "high"
            is_uncertain = True
            reasons.append("footprint is mostly non-personal")

        if weighted_quality < 0.3:
            level = "medium" if level == "low" else level
            reasons.append("low weighted repo quality")

        if noisy_share >= 0.5:
            confidence_multiplier = 0.35
        elif noisy_share >= 0.3:
            confidence_multiplier = 0.6
        elif personal_share >= 0.5:
            confidence_multiplier = 0.9
        else:
            confidence_multiplier = 1.0

        return {
            "is_uncertain": is_uncertain,
            "level": level,
            "reasons": reasons or ["signal is reasonably clear"],
            "confidence_multiplier": confidence_multiplier,
        }

    def _weighted_average(self, repo_features, field_name):
        if not repo_features:
            return 0.0
        weighted_total = (
            sum(feature.repo_type_weight for feature in repo_features) or 1.0
        )
        numerator = sum(
            getattr(feature, field_name, 0.0) * feature.repo_type_weight
            for feature in repo_features
        )
        return numerator / weighted_total

    def _feature_to_repository_payload(self, feature):
        return {
            "name": feature.name,
            "repo_type": feature.repo_type,
            "repo_type_weight": feature.repo_type_weight,
            "repo_type_confidence": feature.repo_type_confidence,
            "repo_type_reason": feature.repo_type_reason,
            "quality_score": feature.quality_score,
            "structure_score": feature.structure_score,
            "signals": feature.structure_signals,
            "penalties": feature.penalties,
            "stars": feature.stars,
            "forks": feature.forks,
            "language": feature.language,
        }

    def _metrics_to_payload(self, metrics_map):
        payload = {}
        for skill, metrics in metrics_map.items():
            payload[skill] = {
                "raw_confidence": metrics.raw_confidence,
                "confidence": metrics.confidence,
                "avg_quality": metrics.avg_quality,
                "avg_structure": metrics.avg_structure,
                "repo_type_pressure": metrics.repo_type_pressure,
                "repo_count": metrics.repo_count,
                "evidence": metrics.evidence,
                "signal_counts": metrics.signal_counts,
                "strongest_signals": metrics.strongest_signals,
                "exceptional": metrics.exceptional,
            }
        return payload

    def _normalize_skill_confidences(self, skill_metrics):
        if not skill_metrics:
            return {}

        max_raw = max(metrics.confidence for metrics in skill_metrics.values())
        if max_raw <= 0:
            max_raw = 1.0

        normalized = {}
        for skill, metrics in skill_metrics.items():
            normalized_relative = metrics.confidence / max_raw
            normalized_confidence = metrics.confidence * (
                0.8 + 0.2 * normalized_relative
            )
            final_confidence = min(
                normalized_confidence, 1.0 if metrics.exceptional else 0.88
            )

            normalized[skill] = type(
                "NormalizedSkill",
                (),
                {
                    "raw_confidence": metrics.raw_confidence,
                    "confidence": round(final_confidence, 2),
                    "avg_quality": metrics.avg_quality,
                    "avg_structure": metrics.avg_structure,
                    "repo_type_pressure": metrics.repo_type_pressure,
                    "repo_count": metrics.repo_count,
                    "evidence": metrics.evidence,
                    "signal_counts": metrics.signal_counts,
                    "strongest_signals": metrics.strongest_signals,
                    "exceptional": metrics.exceptional,
                },
            )

        return dict(
            sorted(
                normalized.items(), key=lambda item: item[1].confidence, reverse=True
            )
        )


def fetch_github_profile(username):
    profile, error = GitHubIntelligenceService().analyze(username)
    if error:
        return None, error
    return GitHubIntelligenceService().present(profile), None


def build_compact_github_profile(profile):
    if isinstance(profile, DeveloperProfile):
        return GitHubIntelligenceService().present_compact(profile)

    verified_skills = profile.get("verified_skills", {})
    sorted_skills = sorted(
        verified_skills.items(),
        key=lambda item: item[1].get("score", 0),
        reverse=True,
    )
    developer_profile = profile.get("developer_profile", {})

    return {
        "username": profile.get("username"),
        "developer_level": developer_profile.get("level"),
        "total_score": developer_profile.get("score", 0),
        "confidence": developer_profile.get("confidence", 0),
        "skills_count": len(verified_skills),
        "top_skills": [
            {
                "skill": skill,
                "score": details.get("score", 0),
                "repos": details.get("repos", 0),
                "evidence": details.get("evidence", []),
            }
            for skill, details in sorted_skills[:5]
        ],
        "repo_summary": profile.get("repo_summary", {}),
        "risk_flags": profile.get("risk_flags", []),
    }
