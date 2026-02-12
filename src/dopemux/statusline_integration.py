"""Compatibility statusline rendering for profile suggestions."""

from __future__ import annotations


def render_profile_statusline(active_profile=None, pending_match=None) -> str:
    """Render a compact statusline payload."""

    profile = active_profile or "none"
    if pending_match is None:
        return f"profile:{profile}"

    confidence = int(round(float(pending_match.confidence) * 100))
    return (
        f"profile:{profile} "
        f"suggest:{pending_match.profile_name}({confidence}%) "
        f"mode:{pending_match.suggestion_level}"
    )

