"""
Compatibility facade for profile analytics.

Historically referenced as ``dopemux.analytics`` in Epic-4 planning notes.
This module keeps that import path stable by re-exporting profile analytics.
"""

from .profile_analytics import (
    ProfileAnalytics,
    ProfileStats,
    ProfileSwitch,
    archive_optimization_suggestions_sync,
    display_stats,
    generate_optimization_suggestions,
    get_stats_sync,
    log_switch_sync,
)

__all__ = [
    "ProfileAnalytics",
    "ProfileStats",
    "ProfileSwitch",
    "archive_optimization_suggestions_sync",
    "display_stats",
    "generate_optimization_suggestions",
    "get_stats_sync",
    "log_switch_sync",
]

