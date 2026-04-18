"""Compatibility layer for renamed skill scoring modules."""

from services.repo_feature_extractor import SkillEvidence
from services.skill_scorer import SkillScoreResult, SkillScorer

__all__ = ["SkillEvidence", "SkillScoreResult", "SkillScorer"]
