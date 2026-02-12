"""Compatibility scorer facades for profile detection."""

from __future__ import annotations


def score_best_profile(detector, context=None):
    """Return the best profile match from a detector."""

    return detector.detect(context=context)


def score_all_profiles(detector, context=None):
    """Return all profile scores from a detector."""

    return detector.get_all_scores(context=context)

