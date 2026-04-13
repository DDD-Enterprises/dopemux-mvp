from __future__ import annotations

from collections import Counter
from typing import Any


def build_profile_synthesis_summary(
    *,
    preflight: dict[str, Any],
    proposals: list[dict[str, Any]],
    routing_diffs: list[dict[str, Any]],
    blocked_lanes: list[dict[str, Any]],
) -> dict[str, Any]:
    proposal_counts = Counter(str(item.get("proposal_class")) for item in proposals)
    return {
        "feedback_loop_exists_in_reviewable_form": True,
        "auto_apply_enabled": False,
        "proposal_class_counts": dict(sorted(proposal_counts.items())),
        "preflight": preflight,
        "routing_diff_statuses": {
            str(item["target_profile"]): str(item["status"]) for item in routing_diffs
        },
        "blocked_lane_count": len(blocked_lanes),
        "notes": [
            "Profile synthesis is downstream-only and must not auto-apply runtime or profile changes.",
            "Pricing uncertainty is propagated into proposal classes instead of flattened into cost confidence.",
        ],
    }
