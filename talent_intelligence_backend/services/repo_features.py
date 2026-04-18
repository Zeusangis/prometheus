from dataclasses import dataclass, field

from services.repo_heuristics import (
    classify_repo_intent,
    infer_repo_structure,
    score_repo_quality,
)


@dataclass(frozen=True)
class RepoFeatures:
    name: str
    language: str | None
    topics: list[str]
    size: int
    stars: int
    forks: int
    structure_score: float
    structure_signals: list[str] = field(default_factory=list)
    penalties: list[str] = field(default_factory=list)
    repo_type: str = "unknown"
    repo_type_weight: float = 0.0
    repo_type_confidence: float = 0.0
    repo_type_reason: list[str] = field(default_factory=list)
    quality_score: float = 0.0
    owner_type: str = ""
    description: str = ""
    pushed_at: str | None = None
    updated_at: str | None = None
    low_signal: bool = False


class RepoFeatureExtractor:
    def extract(self, repo):
        structure_score, structure_signals, penalties = infer_repo_structure(repo)
        repo_type_data = classify_repo_intent(
            repo,
            structure_score=structure_score,
            structure_signals=structure_signals,
            penalties=penalties,
        )
        quality_score = score_repo_quality(
            repo,
            structure_score=structure_score,
            penalties=penalties,
        )
        owner = repo.get("owner") or {}

        return RepoFeatures(
            name=repo.get("name", ""),
            language=repo.get("language"),
            topics=list(repo.get("topics") or []),
            size=repo.get("size", 0),
            stars=repo.get("stargazers_count", 0),
            forks=repo.get("forks_count", 0),
            structure_score=structure_score,
            structure_signals=structure_signals,
            penalties=penalties,
            repo_type=repo_type_data["repo_type"],
            repo_type_weight=repo_type_data["repo_type_weight"],
            repo_type_confidence=repo_type_data["repo_type_confidence"],
            repo_type_reason=repo_type_data["repo_type_reason"],
            quality_score=quality_score,
            owner_type=str(owner.get("type") or "").strip().lower(),
            description=repo.get("description") or "",
            pushed_at=repo.get("pushed_at"),
            updated_at=repo.get("updated_at"),
            low_signal=repo_type_data["low_signal"],
        )
