from __future__ import annotations

from typing import Any

from .models import AVAILABLE_STATUSES, needs_supervisor_route


def select_preferred_route(
    *,
    direct_routes: list[dict[str, Any]],
    pal_routes: list[dict[str, Any]],
    fallback_routes: list[dict[str, Any]],
    allow_fallback: bool,
) -> dict[str, Any]:
    for route in direct_routes:
        if route.get("status") in AVAILABLE_STATUSES:
            return route

    for route in pal_routes:
        if route.get("status") in AVAILABLE_STATUSES:
            return route

    if allow_fallback:
        for route in fallback_routes:
            if (
                route.get("tool") == "copilot-cli"
                and route.get("status") == "FALLBACK_ONLY"
            ):
                return route

    return needs_supervisor_route(
        "No direct Tier 1 route or audit-safe PAL clink route is available."
    )
