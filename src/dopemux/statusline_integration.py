"""Compatibility statusline rendering for profile suggestions and routing mode."""

from __future__ import annotations

from pathlib import Path

import yaml


def _get_routing_mode() -> str:
    """Read routing mode from ~/.dopemux/routing.yaml without raising."""
    config_path = Path.home() / ".dopemux" / "routing.yaml"
    try:
        if config_path.exists():
            with open(config_path) as f:
                config = yaml.safe_load(f) or {}
            return config.get("mode", "subscription")
    except Exception:
        pass
    return "subscription"


def render_profile_statusline(active_profile=None, pending_match=None) -> str:
    """Render a compact statusline payload."""

    profile = active_profile or "none"
    mode = _get_routing_mode()
    mode_indicator = "api" if mode == "api" else "direct"

    base = f"profile:{profile} routing:{mode_indicator}"

    if pending_match is None:
        return base

    confidence = int(round(float(pending_match.confidence) * 100))
    return (
        f"{base} "
        f"suggest:{pending_match.profile_name}({confidence}%) "
        f"mode:{pending_match.suggestion_level}"
    )
