"""Generate read-only Copilot repair packets from PR Action Bridge output."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


SCHEMA_VERSION = "1.0.0"
COPILOT_AUTHORITY = "implementer-only"
IMPLEMENTER_CATEGORIES = {
    "unresolved-thread",
    "failed-check",
    "request-changes",
    "must-fix",
}
SUGGESTED_ACTIONS = {
    "unresolved-thread": (
        "Address the local code change requested by the unresolved review "
        "thread; leave GitHub thread resolution to the operator."
    ),
    "failed-check": (
        "Fix the failing CI check locally, then rerun the relevant focused "
        "validation."
    ),
    "request-changes": (
        "Address the requested review changes in the smallest coherent code "
        "change."
    ),
    "must-fix": (
        "Resolve the must-fix review item before asking for another readiness "
        "evaluation."
    ),
}


def _utc_now_seconds() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _zulu_seconds(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"generated_at must be ISO 8601 UTC: {value}") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"generated_at must include UTC timezone: {value}")
    return (
        parsed.astimezone(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def generate_repair_packet(
    action_plan: dict[str, Any],
    *,
    generated_at: str | None = None,
    source_action_plan_id: str | None = None,
) -> dict[str, Any]:
    """Map implementer-role ACTION_PLAN items to a CopilotRepairPacket.

    This function performs no filesystem I/O and no GitHub mutation.
    """
    if action_plan.get("mutation_performed") is not False:
        raise ValueError("ACTION_PLAN mutation_performed must be false")

    required = ("pr_number", "repo", "actions")
    missing = [key for key in required if key not in action_plan]
    if missing:
        raise KeyError(f"ACTION_PLAN missing required fields: {', '.join(missing)}")

    packet: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _zulu_seconds(
            generated_at or str(action_plan.get("generated_at") or _utc_now_seconds())
        ),
        "pr_number": int(action_plan["pr_number"]),
        "repo": str(action_plan["repo"]),
        "copilot_authority": COPILOT_AUTHORITY,
        "mutation_performed": False,
        "source_action_plan_id": source_action_plan_id,
        "items": [],
    }

    items: list[dict[str, Any]] = []
    for action in action_plan["actions"]:
        if action.get("target_role") != "implementer":
            continue
        category = str(action.get("category", ""))
        if category not in IMPLEMENTER_CATEGORIES:
            raise ValueError(f"unsupported implementer category: {category}")
        items.append(
            {
                "id": f"repair-{len(items) + 1:04d}",
                "category": category,
                "source_blocker": str(action["source_blocker"]),
                "source_item_id": action.get("source_item_id"),
                "rationale": str(action["rationale"]),
                "suggested_action": SUGGESTED_ACTIONS[category],
            }
        )
    packet["items"] = items
    return packet
