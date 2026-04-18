from dataclasses import dataclass, field
from math import log1p


@dataclass
class DeveloperProfile:
    username: str
    score: int
    confidence: int
    level: str
    verified_skills: dict[str, dict]
    repos_analyzed: int
    total_stars: int
    risk_flags: list[str] = field(default_factory=list)


class ProfileAggregator:
    def aggregate(
        self,
        username: str,
        verified_skills: dict[str, dict],
        repos_analyzed: int,
        total_stars: int,
        uncertainty_multiplier: float,
    ) -> DeveloperProfile:
        overall_score = self._aggregate_score(verified_skills)
        overall_confidence = self._aggregate_confidence(
            verified_skills,
            uncertainty_multiplier=uncertainty_multiplier,
        )
        level = self._level_from_score(overall_score)

        risk_flags = []
        if repos_analyzed < 3:
            risk_flags.append("limited_repository_evidence")
        if overall_confidence < 40:
            risk_flags.append("low_confidence")
        if not verified_skills:
            risk_flags.append("no_skill_evidence")

        return DeveloperProfile(
            username=username,
            score=overall_score,
            confidence=overall_confidence,
            level=level,
            verified_skills=verified_skills,
            repos_analyzed=max(0, int(repos_analyzed)),
            total_stars=max(0, int(total_stars)),
            risk_flags=risk_flags,
        )

    def _aggregate_score(self, verified_skills: dict[str, dict]) -> int:
        if not verified_skills:
            return 0

        weighted_sum = 0.0
        weight_total = 0.0
        for details in verified_skills.values():
            repos = max(int(details.get("repos", 0)), 0)
            score = max(0, min(100, int(details.get("score", 0))))
            weight = max(log1p(repos), 0.25)
            weighted_sum += score * weight
            weight_total += weight

        if weight_total <= 0:
            return 0

        return max(0, min(100, int(round(weighted_sum / weight_total))))

    def _aggregate_confidence(
        self,
        verified_skills: dict[str, dict],
        uncertainty_multiplier: float,
    ) -> int:
        if not verified_skills:
            return 0

        weighted_sum = 0.0
        weight_total = 0.0
        for details in verified_skills.values():
            repos = max(int(details.get("repos", 0)), 0)
            confidence = max(0, min(100, int(details.get("confidence", 0))))
            weight = max(log1p(repos), 0.25)
            weighted_sum += confidence * weight
            weight_total += weight

        if weight_total <= 0:
            return 0

        avg_confidence = weighted_sum / weight_total
        adjusted = avg_confidence * max(0.55, min(uncertainty_multiplier, 1.0))
        return max(0, min(100, int(round(adjusted))))

    def _level_from_score(self, score: int) -> str:
        if score < 35:
            return "beginner"
        if score < 70:
            return "intermediate"
        return "senior"
