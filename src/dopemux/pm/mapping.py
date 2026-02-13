"""
Status dialect mapping tables for PM canonical statuses.

Maps between component-specific status dialects and canonical PMTaskStatus.
Pure data — no runtime wiring, no service imports.

Lossy mappings are documented with dialect_status and reason fields.
"""

from .models import PMTaskStatus


# ─── Orchestrator dialect ↔ Canonical ───────────────────────────

# Orchestrator TaskStatus values (from services/task-orchestrator/task_orchestrator/models.py:13-21)
# pending, in_progress, completed, blocked, needs_break, context_switch, paused

ORCHESTRATOR_TO_CANONICAL: dict[str, PMTaskStatus] = {
    "pending": PMTaskStatus.TODO,
    "in_progress": PMTaskStatus.IN_PROGRESS,
    "completed": PMTaskStatus.DONE,
    "blocked": PMTaskStatus.BLOCKED,
    # Lossy mappings — ADHD states map to BLOCKED with dialect preserved
    "needs_break": PMTaskStatus.BLOCKED,
    "context_switch": PMTaskStatus.BLOCKED,
    "paused": PMTaskStatus.BLOCKED,
}

CANONICAL_TO_ORCHESTRATOR: dict[PMTaskStatus, str] = {
    PMTaskStatus.TODO: "pending",
    PMTaskStatus.IN_PROGRESS: "in_progress",
    PMTaskStatus.DONE: "completed",
    PMTaskStatus.BLOCKED: "blocked",
    PMTaskStatus.CANCELED: "completed",  # Lossy: orchestrator has no canceled
}

# Reason strings for lossy orchestrator → canonical mappings
ORCHESTRATOR_LOSSY_REASONS: dict[str, str] = {
    "needs_break": "ADHD state: needs_break mapped to BLOCKED",
    "context_switch": "ADHD state: context_switch mapped to BLOCKED",
    "paused": "ADHD state: paused mapped to BLOCKED",
}


# ─── ConPort dialect ↔ Canonical ────────────────────────────────

# ConPort status strings (from services/task-orchestrator/app/adapters/schema_mapping.py:308-321)
# TODO, IN_PROGRESS, DONE, BLOCKED

CONPORT_TO_CANONICAL: dict[str, PMTaskStatus] = {
    "TODO": PMTaskStatus.TODO,
    "IN_PROGRESS": PMTaskStatus.IN_PROGRESS,
    "DONE": PMTaskStatus.DONE,
    "BLOCKED": PMTaskStatus.BLOCKED,
}

CANONICAL_TO_CONPORT: dict[PMTaskStatus, str] = {
    PMTaskStatus.TODO: "TODO",
    PMTaskStatus.IN_PROGRESS: "IN_PROGRESS",
    PMTaskStatus.DONE: "DONE",
    PMTaskStatus.BLOCKED: "BLOCKED",
    PMTaskStatus.CANCELED: "DONE",  # Lossy: ConPort has no canceled
}


# ─── Taskmaster dialect ↔ Canonical ─────────────────────────────

# Taskmaster bridge writes hardcoded "TODO" (bridge_adapter.py:69)
# and emits status_updated events with arbitrary strings

TASKMASTER_TO_CANONICAL: dict[str, PMTaskStatus] = {
    "TODO": PMTaskStatus.TODO,
    "IN_PROGRESS": PMTaskStatus.IN_PROGRESS,
    "DONE": PMTaskStatus.DONE,
    "BLOCKED": PMTaskStatus.BLOCKED,
}

CANONICAL_TO_TASKMASTER: dict[PMTaskStatus, str] = {
    PMTaskStatus.TODO: "TODO",
    PMTaskStatus.IN_PROGRESS: "IN_PROGRESS",
    PMTaskStatus.DONE: "DONE",
    PMTaskStatus.BLOCKED: "BLOCKED",
    PMTaskStatus.CANCELED: "DONE",  # Lossy: taskmaster has no canceled
}


# ─── Lossy mapping documentation ────────────────────────────────

# All lossy mappings documented here for audit trail.
# Format: (source_dialect, source_status) -> (canonical_status, reason)
LOSSY_MAPPINGS: list[dict[str, str]] = [
    {
        "source": "orchestrator",
        "dialect_status": "needs_break",
        "canonical_status": "BLOCKED",
        "reason": "ADHD overlay state; not a lifecycle state",
    },
    {
        "source": "orchestrator",
        "dialect_status": "context_switch",
        "canonical_status": "BLOCKED",
        "reason": "ADHD overlay state; not a lifecycle state",
    },
    {
        "source": "orchestrator",
        "dialect_status": "paused",
        "canonical_status": "BLOCKED",
        "reason": "ADHD overlay state; temporarily blocked",
    },
    {
        "source": "orchestrator",
        "dialect_status": "canceled (reverse)",
        "canonical_status": "completed",
        "reason": "Orchestrator has no canceled status; maps to completed",
    },
    {
        "source": "conport",
        "dialect_status": "canceled (reverse)",
        "canonical_status": "DONE",
        "reason": "ConPort has no canceled status; maps to DONE",
    },
    {
        "source": "taskmaster",
        "dialect_status": "canceled (reverse)",
        "canonical_status": "DONE",
        "reason": "Taskmaster has no canceled status; maps to DONE",
    },
]
