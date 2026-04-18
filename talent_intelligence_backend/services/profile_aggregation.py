from dataclasses import dataclass, field
from math import exp


@dataclass
class DeveloperProfile:
    username: str
    repos_analyzed: int
    total_stars: int
    avg_repo_quality: float
    avg_structure_score: float
    repo_type_distribution: dict
    repo_type_distribution_weighted: dict
    weighted_repo_type_signal: float
    repositories: list[dict]
    weighted_skills: dict
    adjusted_confidence_scores: dict
    developer_level: str
    developer_level_explanation: dict
    uncertainty_indicator: dict


class ProfileAggregator:
    def aggregate(
        self,
        username,
        repositories,
        weighted_skills,
        adjusted_confidence_scores,
        repo_type_distribution,
        repo_type_distribution_weighted,
        weighted_repo_type_signal,
        avg_repo_quality,
        avg_structure_score,
        uncertainty_indicator,
    ):
        total_stars = sum(repo.get("stars", 0) for repo in repositories)
        total_repo_type_weight = (
            sum(repo.get("repo_type_weight", 0.0) for repo in repositories) or 1.0
        )
        personal_ratio = repo_type_distribution.get("personal_project", 0) / max(
            len(repositories), 1
        )
        meaningful_ratio = (
            repo_type_distribution.get("personal_project", 0)
            + repo_type_distribution.get("library_or_framework", 0)
            + repo_type_distribution.get("unknown", 0)
        ) / max(len(repositories), 1)

        strong_skills = [
            skill_name
            for skill_name, skill_data in adjusted_confidence_scores.items()
            if skill_data["confidence"] >= 0.6
        ]
        meaningful_skills = [
            skill_name
            for skill_name, skill_data in adjusted_confidence_scores.items()
            if skill_data["confidence"] >= 0.35
        ]

        skill_strength = self._weighted_skill_strength(adjusted_confidence_scores)
        repo_diversity = min(len(meaningful_skills) / 8, 1.0)
        project_complexity = self._project_complexity_score(
            avg_repo_quality,
            avg_structure_score,
            personal_ratio,
            weighted_repo_type_signal,
        )
        consistency = self._consistency_score(
            repo_type_distribution, uncertainty_indicator
        )

        latent_score = self._sigmoid(
            2.1 * skill_strength
            + 1.2 * repo_diversity
            + 1.0 * project_complexity
            + 0.8 * consistency
            - self._non_personal_penalty(repo_type_distribution, personal_ratio)
        )

        developer_level = self._level_from_score(
            latent_score, repo_type_distribution, uncertainty_indicator
        )
        developer_level_explanation = self._explain_level(
            developer_level,
            latent_score,
            repo_type_distribution,
            personal_ratio,
            meaningful_skills,
            strong_skills,
            avg_repo_quality,
            avg_structure_score,
            uncertainty_indicator,
        )

        return DeveloperProfile(
            username=username,
            repos_analyzed=len(repositories),
            total_stars=total_stars,
            avg_repo_quality=avg_repo_quality,
            avg_structure_score=avg_structure_score,
            repo_type_distribution=repo_type_distribution,
            repo_type_distribution_weighted=repo_type_distribution_weighted,
            weighted_repo_type_signal=weighted_repo_type_signal,
            repositories=repositories,
            weighted_skills=weighted_skills,
            adjusted_confidence_scores=adjusted_confidence_scores,
            developer_level=developer_level,
            developer_level_explanation=developer_level_explanation,
            uncertainty_indicator=uncertainty_indicator,
        )

    def _weighted_skill_strength(self, adjusted_confidence_scores):
        if not adjusted_confidence_scores:
            return 0.0
        numerator = sum(
            details["confidence"] * max(details.get("repo_count", 0), 1)
            for details in adjusted_confidence_scores.values()
        )
        denominator = sum(
            max(details.get("repo_count", 0), 1)
            for details in adjusted_confidence_scores.values()
        )
        return min(numerator / max(denominator, 1e-9), 1.0)

    def _project_complexity_score(
        self,
        avg_repo_quality,
        avg_structure_score,
        personal_ratio,
        weighted_repo_type_signal,
    ):
        score = (
            0.4 * avg_repo_quality
            + 0.35 * avg_structure_score
            + 0.15 * personal_ratio
            + 0.10 * weighted_repo_type_signal
        )
        return max(0.0, min(score, 1.0))

    def _consistency_score(self, repo_type_distribution, uncertainty_indicator):
        total = sum(repo_type_distribution.values()) or 1
        tutorial_share = repo_type_distribution.get("tutorial_or_clone", 0) / total
        educational_share = repo_type_distribution.get("educational_content", 0) / total
        noise_share = tutorial_share + educational_share
        certainty = 1.0 - min(noise_share, 1.0)
        return certainty * uncertainty_indicator.get("confidence_multiplier", 1.0)

    def _non_personal_penalty(self, repo_type_distribution, personal_ratio):
        total = sum(repo_type_distribution.values()) or 1
        org_share = repo_type_distribution.get("organization_repo", 0) / total
        tutorial_share = repo_type_distribution.get("tutorial_or_clone", 0) / total
        educational_share = repo_type_distribution.get("educational_content", 0) / total
        non_personal = org_share + tutorial_share + educational_share
        return max(0.0, non_personal - personal_ratio * 0.25)

    def _sigmoid(self, value):
        return 1.0 / (1.0 + exp(-value))

    def _level_from_score(self, score, repo_type_distribution, uncertainty_indicator):
        total = sum(repo_type_distribution.values()) or 1
        tutorial_share = repo_type_distribution.get("tutorial_or_clone", 0) / total
        educational_share = repo_type_distribution.get("educational_content", 0) / total
        organization_share = repo_type_distribution.get("organization_repo", 0) / total
        if tutorial_share + educational_share >= 0.5:
            return "unknown"
        if uncertainty_indicator.get("is_uncertain") and organization_share >= 0.5:
            return "unknown"
        if score < 0.3:
            return "beginner"
        if score < 0.55:
            return "junior"
        if score < 0.75:
            return "intermediate"
        return "senior"

    def _explain_level(
        self,
        level,
        latent_score,
        repo_type_distribution,
        personal_ratio,
        meaningful_skills,
        strong_skills,
        avg_repo_quality,
        avg_structure_score,
        uncertainty_indicator,
    ):
        total = sum(repo_type_distribution.values()) or 1
        tutorial_share = repo_type_distribution.get("tutorial_or_clone", 0) / total
        educational_share = repo_type_distribution.get("educational_content", 0) / total
        org_share = repo_type_distribution.get("organization_repo", 0) / total

        if level == "unknown":
            if tutorial_share + educational_share >= 0.5:
                reason = "tutorial and educational repositories dominate the footprint"
            elif org_share >= 0.5 and personal_ratio < 0.2:
                reason = "profile is mostly non-personal or organization-owned"
            else:
                reason = "signal is too weak or too noisy for a reliable level"
        else:
            reason = (
                f"latent capability score {latent_score:.2f} derived from weighted skills, repo structure, "
                f"and repo-type distribution; {len(meaningful_skills)} meaningful skills and {len(strong_skills)} strong skills detected"
            )

        return {
            "level": level,
            "reason": [
                reason,
                f"weighted repo quality: {avg_repo_quality:.2f}",
                f"weighted repo structure: {avg_structure_score:.2f}",
                f"uncertainty level: {uncertainty_indicator.get('level', 'low')}",
            ],
            "latent_score": round(latent_score, 4),
            "uncertainty": uncertainty_indicator,
        }
