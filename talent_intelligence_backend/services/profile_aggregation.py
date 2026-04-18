"""Compatibility layer for the renamed profile aggregation module."""

from services.profile_aggregator import DeveloperProfile, ProfileAggregator

__all__ = ["DeveloperProfile", "ProfileAggregator"]
