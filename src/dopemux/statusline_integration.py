"""
Statusline helpers for profile and suggestion visibility.
"""

from typing import Optional

from .profile_detector import ProfileMatch


def render_profile_statusline(
    active_profile: Optional[str],
    pending_match: Optional[ProfileMatch] = None,
) -> str:
    """
    Render concise profile status text for terminal statuslines.
    """
    profile_label = active_profile or "none"
    if pending_match is None:
        return f"profile:{profile_label}"

    confidence = int(round(pending_match.confidence * 100))
    return (
        f"profile:{profile_label} "
        f"suggest:{pending_match.profile_name}({confidence}%) "
        f"mode:{pending_match.suggestion_level}"
    )

