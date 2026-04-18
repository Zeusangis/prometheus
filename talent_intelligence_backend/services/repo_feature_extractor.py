from dataclasses import dataclass, field
from datetime import datetime, timezone
from math import log1p
from typing import Any

from config.skill_config import (
    GITHUB_LANGUAGE_MAP,
    PACKAGE_MARKERS,
    QUALITY_KEYWORDS,
    SKILL_KEYWORDS,
    STRUCTURE_MARKERS,
)
from services.repo_heuristics import infer_repo_structure, normalize_signal_text


@dataclass(frozen=True)
class GitHubRepo:
    name: str
    full_name: str
    language: str
    topics: list[str]
    description: str
    readme_text: str
    size: int
    stars: int
    forks: int
    pushed_at: str
    updated_at: str


@dataclass(frozen=True)
class RepoFeatures:
    repo: GitHubRepo
    language_skill: str
    keyword_scores: dict[str, float]
    topic_scores: dict[str, float]
    language_scores: dict[str, float]
    structure_score: float
    quality_score: float
    repo_importance: float


@dataclass(frozen=True)
class SkillEvidence:
    skill: str
    repo_name: str
    keyword_score: float
    language_score: float
    topic_score: float
    embedding_score: float
    repo_structure_score: float
    repo_quality_score: float
    repo_importance: float


class RepoFeatureExtractor:
    def from_api_payload(
        self, payload: dict[str, Any], readme_text: str = ""
    ) -> GitHubRepo:
        return GitHubRepo(
            name=str(payload.get("name") or ""),
            full_name=str(payload.get("full_name") or ""),
            language=str(payload.get("language") or "").strip(),
            topics=[str(t).strip().lower() for t in (payload.get("topics") or []) if t],
            description=str(payload.get("description") or ""),
            readme_text=str(readme_text or ""),
            size=int(payload.get("size") or 0),
            stars=int(payload.get("stargazers_count") or 0),
            forks=int(payload.get("forks_count") or 0),
            pushed_at=str(payload.get("pushed_at") or ""),
            updated_at=str(payload.get("updated_at") or ""),
        )

    def extract(self, repo: GitHubRepo) -> RepoFeatures:
        structure_score, _, penalties = infer_repo_structure(
            {
                "name": repo.name,
                "description": repo.description,
                "topics": repo.topics,
                "size": repo.size,
            }
        )
        quality_score = self._quality_score(repo, structure_score, penalties)
        keyword_scores, topic_scores = self._lexical_signals(repo)
        language_scores = self._language_signals(repo.language)
        repo_importance = self._repo_importance(repo)

        return RepoFeatures(
            repo=repo,
            language_skill=GITHUB_LANGUAGE_MAP.get(repo.language, ""),
            keyword_scores=keyword_scores,
            topic_scores=topic_scores,
            language_scores=language_scores,
            structure_score=structure_score,
            quality_score=quality_score,
            repo_importance=repo_importance,
        )

    def _lexical_signals(
        self, repo: GitHubRepo
    ) -> tuple[dict[str, float], dict[str, float]]:
        base_text = normalize_signal_text(
            f"{repo.name} {repo.description} {' '.join(repo.topics)} {repo.readme_text[:2500]}"
        )
        normalized_topics = [normalize_signal_text(topic) for topic in repo.topics]

        keyword_scores: dict[str, float] = {}
        topic_scores: dict[str, float] = {}
        for skill, keywords in SKILL_KEYWORDS.items():
            if not keywords:
                keyword_scores[skill] = 0.0
                topic_scores[skill] = 0.0
                continue

            keyword_hits = sum(
                1 for keyword in keywords if normalize_signal_text(keyword) in base_text
            )
            topic_hits = sum(
                1
                for topic in normalized_topics
                if any(normalize_signal_text(keyword) in topic for keyword in keywords)
            )

            keyword_scores[skill] = min(keyword_hits / max(len(keywords), 1), 1.0)
            topic_scores[skill] = min(topic_hits / max(len(normalized_topics), 1), 1.0)

        return keyword_scores, topic_scores

    def _language_signals(self, language: str) -> dict[str, float]:
        scores = {skill: 0.0 for skill in SKILL_KEYWORDS}
        mapped_skill = GITHUB_LANGUAGE_MAP.get(language)
        if mapped_skill in scores:
            scores[mapped_skill] = 1.0
        return scores

    def _repo_importance(self, repo: GitHubRepo) -> float:
        # Bounded importance prevents any single repository from dominating skill scores.
        stars_term = min(log1p(repo.stars) / 4.0, 0.45)
        forks_term = min(log1p(repo.forks) / 3.5, 0.25)
        size_term = min(log1p(max(repo.size, 1)) / 8.0, 0.3)
        importance = 0.7 + stars_term + forks_term + size_term
        return max(0.7, min(importance, 1.5))

    def _quality_score(
        self, repo: GitHubRepo, structure_score: float, penalties: list[str]
    ) -> float:
        score = 0.0
        score += min(log1p(max(repo.stars, 0)) / 5.0, 0.25)
        score += min(log1p(max(repo.forks, 0)) / 4.5, 0.15)
        if repo.description:
            score += 0.10

        if repo.size >= 1000:
            score += 0.20
        elif repo.size >= 300:
            score += 0.14
        elif repo.size >= 80:
            score += 0.08

        recent_score = self._recency_score(repo.pushed_at or repo.updated_at)
        score += recent_score

        text_blob = normalize_signal_text(f"{repo.name} {repo.description}")
        quality_hits = sum(1 for keyword in QUALITY_KEYWORDS if keyword in text_blob)
        score += min(quality_hits * 0.04, 0.14)
        score += min(structure_score * 0.22, 0.22)

        if "tutorial-like repo" in penalties:
            score *= 0.75
        if "single-file or tiny repo" in penalties:
            score *= 0.82

        return max(0.02, min(round(score, 4), 1.0))

    def _recency_score(self, timestamp: str) -> float:
        if not timestamp:
            return 0.0

        try:
            updated_dt = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=timezone.utc
            )
        except ValueError:
            return 0.0

        days_old = (datetime.now(timezone.utc) - updated_dt).days
        if days_old <= 90:
            return 0.16
        if days_old <= 365:
            return 0.10
        if days_old <= 730:
            return 0.05
        return 0.0
