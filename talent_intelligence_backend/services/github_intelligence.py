import os
from math import log1p

from config.skill_config import SKILL_KEYWORDS
from services.calibration_engine import CalibrationConfig, CalibrationEngine
from services.github_client import GitHubClient
from services.profile_aggregator import DeveloperProfile, ProfileAggregator
from services.profile_presenter import ProfilePresenter
from services.repo_feature_extractor import RepoFeatureExtractor, SkillEvidence
from services.repo_heuristics import normalize_signal_text
from services.skill_embedding_engine import SkillEmbeddingEngine
from services.skill_scorer import SkillScorer


class GitHubIntelligenceService:
    STRICT_ML_MARKERS = {
        "machine learning",
        "deep learning",
        "neural network",
        "computer vision",
        "natural language processing",
        "nlp",
        "model training",
        "model inference",
        "feature engineering",
        "scikit learn",
        "sklearn",
        "tensorflow",
        "pytorch",
        "keras",
        "xgboost",
        "lightgbm",
        "catboost",
        "classification model",
        "regression model",
    }

    def __init__(
        self,
        client=None,
        feature_extractor=None,
        embedding_engine=None,
        calibration_engine=None,
        scorer=None,
        aggregator=None,
        presenter=None,
    ):
        self.client = client or GitHubClient(token=os.environ.get("GITHUB_TOKEN"))
        self.feature_extractor = feature_extractor or RepoFeatureExtractor()
        self.embedding_engine = embedding_engine or SkillEmbeddingEngine()
        self.calibration_engine = calibration_engine or CalibrationEngine(
            CalibrationConfig(sigmoid_k=10.0, sigmoid_bias=0.35)
        )
        self.scorer = scorer or SkillScorer(self.calibration_engine)
        self.aggregator = aggregator or ProfileAggregator()
        self.presenter = presenter or ProfilePresenter()

    def analyze(self, username):
        repos, error = self.client.get_repos(username)
        if error:
            return None, error

        github_repos = self._build_repo_objects(repos)
        if not github_repos:
            return None, "No usable repositories found."

        repo_features = [self.feature_extractor.extract(repo) for repo in github_repos]
        evidence_by_skill = self._build_skill_evidence(repo_features)

        uncertainty_multiplier = self._uncertainty_multiplier(repo_features)

        verified_skills = {}
        for skill, evidences in evidence_by_skill.items():
            score_result = self.scorer.score_skill(
                evidences,
                uncertainty_multiplier=uncertainty_multiplier,
            )
            if score_result.repos == 0:
                continue

            lexical_evidence_count = sum(
                1
                for evidence in evidences
                if (
                    evidence.language_score >= 1.0
                    or evidence.keyword_score >= 0.12
                    or evidence.topic_score >= 0.15
                )
            )
            strong_embedding_count = sum(
                1 for evidence in evidences if evidence.embedding_score >= 0.7
            )

            # Reject embedding-only noise unless support is very strong across repos.
            if lexical_evidence_count == 0:
                if score_result.repos < 3:
                    continue
                if strong_embedding_count < 2:
                    continue
                if score_result.score < 75:
                    continue

            # Keep final output focused on meaningful, non-trivial skill signals.
            if score_result.score < 20 or score_result.confidence < 18:
                continue

            verified_skills[skill] = {
                "score": score_result.score,
                "confidence": score_result.confidence,
                "repos": score_result.repos,
                "evidence": score_result.evidence,
            }

        profile = self.aggregator.aggregate(
            username=username,
            verified_skills=verified_skills,
            repos_analyzed=len(repo_features),
            total_stars=sum(feature.repo.stars for feature in repo_features),
            uncertainty_multiplier=uncertainty_multiplier,
        )

        return profile, None

    def present(self, profile):
        return self.presenter.build(profile)

    def present_compact(self, profile):
        return self.presenter.build_compact(profile)

    def _weighted_average(self, repo_features, field_name):
        if not repo_features:
            return 0.0
        weighted_total = (
            sum(feature.repo_importance for feature in repo_features) or 1.0
        )
        numerator = sum(
            getattr(feature, field_name, 0.0) * feature.repo_importance
            for feature in repo_features
        )
        return numerator / weighted_total

    def _uncertainty_multiplier(self, repo_features):
        if not repo_features:
            return 0.55

        avg_quality = self._weighted_average(repo_features, "quality_score")
        avg_structure = self._weighted_average(repo_features, "structure_score")
        repo_count_factor = min(log1p(len(repo_features)) / log1p(12), 1.0)

        multiplier = (
            0.55 + 0.25 * avg_quality + 0.15 * avg_structure + 0.05 * repo_count_factor
        )
        return max(0.55, min(multiplier, 1.0))

    def _build_repo_objects(self, repos):
        repo_objects = []
        for raw_repo in repos:
            readme_text = ""
            full_name = str(raw_repo.get("full_name") or "")
            if full_name:
                readme_text = self.client.get_repo_readme(full_name)

            repo_objects.append(
                self.feature_extractor.from_api_payload(
                    raw_repo, readme_text=readme_text
                )
            )
        return repo_objects

    def _build_skill_evidence(self, repo_features):
        evidence_by_skill = {skill: [] for skill in SKILL_KEYWORDS}

        for feature in repo_features:
            repo_text = " ".join(
                [
                    feature.repo.name,
                    feature.repo.description,
                    " ".join(feature.repo.topics),
                    feature.repo.readme_text[:3500],
                ]
            )

            for skill, keywords in SKILL_KEYWORDS.items():
                skill_prompt = self.embedding_engine.skill_prompt(skill, keywords)
                embedding_score = self.embedding_engine.similarity(
                    skill_prompt, repo_text
                )
                keyword_score = feature.keyword_scores.get(skill, 0.0)
                topic_score = feature.topic_scores.get(skill, 0.0)
                language_score = feature.language_scores.get(skill, 0.0)

                lexical_signal = (
                    language_score >= 1.0 or keyword_score >= 0.16 or topic_score >= 0.2
                )
                mixed_signal = embedding_score >= 0.45 and (
                    language_score >= 1.0
                    or keyword_score >= 0.08
                    or topic_score >= 0.08
                )
                strong_embedding_only_signal = (
                    embedding_score >= 0.72
                    and feature.quality_score >= 0.25
                    and feature.structure_score >= 0.2
                )

                # Avoid broad semantic matches creating unrelated skills.
                has_signal = (
                    lexical_signal or mixed_signal or strong_embedding_only_signal
                )
                if not has_signal:
                    continue

                if skill == "machine learning":
                    strict_ml_signal = self._has_strict_ml_signal(repo_text)
                    # ML should require explicit ML evidence; generic semantic proximity is not enough.
                    if not (
                        strict_ml_signal
                        and (
                            keyword_score >= 0.12
                            or topic_score >= 0.12
                            or embedding_score >= 0.6
                        )
                    ):
                        continue

                evidence_by_skill[skill].append(
                    SkillEvidence(
                        skill=skill,
                        repo_name=feature.repo.name,
                        keyword_score=min(keyword_score, 1.0),
                        language_score=min(language_score, 1.0),
                        topic_score=min(topic_score, 1.0),
                        embedding_score=min(max(embedding_score, 0.0), 1.0),
                        repo_structure_score=min(
                            max(feature.structure_score, 0.0), 1.0
                        ),
                        repo_quality_score=min(max(feature.quality_score, 0.0), 1.0),
                        repo_importance=min(max(feature.repo_importance, 0.4), 1.5),
                    )
                )

        return evidence_by_skill

    def _has_strict_ml_signal(self, repo_text):
        normalized = normalize_signal_text(repo_text)
        if not normalized:
            return False

        token_set = set(normalized.split())
        for marker in self.STRICT_ML_MARKERS:
            normalized_marker = normalize_signal_text(marker)
            if " " in normalized_marker:
                if normalized_marker in normalized:
                    return True
                continue
            if normalized_marker in token_set:
                return True

        return False


def fetch_github_profile(username):
    intelligence_service = GitHubIntelligenceService()
    profile, error = intelligence_service.analyze(username)
    if error:
        return None, error
    return intelligence_service.present(profile), None


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
