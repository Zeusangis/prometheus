"""Compatibility layer for the renamed repo feature extraction module."""

from services.repo_feature_extractor import (
    GitHubRepo,
    RepoFeatureExtractor,
    RepoFeatures,
)

__all__ = ["GitHubRepo", "RepoFeatures", "RepoFeatureExtractor"]
