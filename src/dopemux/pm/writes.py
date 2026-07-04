"""Normalized PM-plane writes with explicit phase-1 authority boundaries."""

from __future__ import annotations

import os
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from dopemux.memory.capture_client import try_emit_promotable_capture_event

from .models import PMTaskStatus, WORKFLOW_SIGNIFICANT_FIELDS

# Phase-1 metadata writes are limited to the fields proven on the active
# leantime-bridge `update_ticket` tool surface.
ALLOWED_METADATA_FIELDS = frozenset(
    {
        "title",
        "headline",
        "description",
        "details",
        "notes",
        "assignee",
        "assigned_to",
        "assignedto",
    }
)

EXPLICIT_WORKFLOW_FIELDS = frozenset(
    {field.lower() for field in WORKFLOW_SIGNIFICANT_FIELDS}
    | {
        "state",
        "phase",
        "stage",
        "transition",
        "blocked",
        "blocker",
        "queue",
        "queue_position",
        "approval",
        "approval_state",
        "next_action",
        "promote",
        "demote",
    }
)

WORKFLOW_FIELD_SUFFIXES = ("_status", "_state", "_phase", "_stage")

LEANTIME_METADATA_FIELD_MAP = {
    "title": "headline",
    "headline": "headline",
    "description": "description",
    "details": "description",
    "notes": "description",
    "assignee": "assignedTo",
    "assigned_to": "assignedTo",
    "assignedto": "assignedTo",
}

TASK_ORCHESTRATOR_TRANSITIONS = {
    PMTaskStatus.IN_PROGRESS: "start",
    PMTaskStatus.BLOCKED: "block",
    PMTaskStatus.DONE: "done",
}

# NOTE: task.failed enum add DEFERRED (contract risk). PMTaskStatus has an
# enforced 5-value invariant (see models.py docstring "Exactly 5 values" and
# tests/unit/pm/test_pm_models.py::TestPMTaskStatus.test_exactly_five_values /
# test_canonical_values) plus exhaustive CANONICAL_TO_ORCHESTRATOR /
# CANONICAL_TO_CONPORT dialect maps in pm/mapping.py and an exhaustive
# TASK_ORCHESTRATOR_TRANSITIONS above (only IN_PROGRESS/BLOCKED/DONE have a
# proven orchestrator transition trigger — no "fail" trigger exists). Adding
# PMTaskStatus.FAILED would break that invariant test and require touching
# pm/mapping.py (out of scope here) with no proven transition semantics.
# The WMA promotion engine already has a ready _promote_task_failed handler
# (services/working-memory-assistant/promotion/promotion.py) waiting for a
# producer once a FAILED status (or an equivalent producer) is introduced
# under its own contract review.
TASK_STATUS_CAPTURE_EVENTS = {
    PMTaskStatus.BLOCKED: "task.blocked",
    PMTaskStatus.DONE: "task.completed",
}

# Values must stay within chronicle VALID_WORKFLOW_PHASES
# (services/working-memory-assistant/chronicle/store.py).
WORKFLOW_PHASE_CAPTURE_BY_STATUS = {
    PMTaskStatus.TODO: "planning",
    PMTaskStatus.IN_PROGRESS: "implementation",
    PMTaskStatus.BLOCKED: "review",
    PMTaskStatus.DONE: "deployment",
    PMTaskStatus.CANCELED: "maintenance",
}


class PMActionKind(str, Enum):
    """Supported phase-1 PM write classes."""

    METADATA_UPDATE = "metadata_update"
    WORKFLOW_TRANSITION = "workflow_transition"
    PROGRESS_LOG = "progress_log"
    DECISION_LOG = "decision_log"
    HISTORY_MIRROR = "history_mirror"


def _looks_workflow_significant_key(key_lower: str) -> bool:
    """Fail closed for likely workflow keys without substring collisions."""

    return key_lower.endswith(WORKFLOW_FIELD_SUFFIXES)


def _unsupported_metadata_fields(payload: Dict[str, Any]) -> List[str]:
    unsupported: List[str] = []
    for key in payload:
        normalized = key.lower()
        if normalized not in ALLOWED_METADATA_FIELDS and normalized not in EXPLICIT_WORKFLOW_FIELDS and not _looks_workflow_significant_key(normalized):
            unsupported.append(key)
    return unsupported


def _normalize_leantime_metadata_payload(task_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"ticketId": task_id}
    for key, value in updates.items():
        normalized_key = key.lower()
        target_key = LEANTIME_METADATA_FIELD_MAP.get(normalized_key)
        if target_key is None:
            continue
        payload[target_key] = value
    return payload


def _call_leantime_metadata_update(
    *,
    leantime_client: Any,
    task_id: str,
    updates: Dict[str, Any],
    idempotency_key: str,
) -> None:
    normalized = _normalize_leantime_metadata_payload(task_id, updates)
    if hasattr(leantime_client, "update_ticket"):
        leantime_client.update_ticket(task_id, normalized)
        return
    if hasattr(leantime_client, "update_task"):
        # Legacy shim retained for callers still injecting bridge wrapper objects.
        leantime_client.update_task(task_id, normalized, idempotency_key=idempotency_key)
        return
    raise RuntimeError("Leantime metadata client does not expose update_ticket or update_task")


def classify_pm_write(payload: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """Classify payload keys into metadata and workflow-significant fields."""

    metadata_fields: List[str] = []
    workflow_fields: List[str] = []
    for key in payload.keys():
        key_lower = key.lower()
        if key_lower in EXPLICIT_WORKFLOW_FIELDS:
            workflow_fields.append(key)
        elif key_lower in ALLOWED_METADATA_FIELDS:
            metadata_fields.append(key)
        elif _looks_workflow_significant_key(key_lower):
            workflow_fields.append(key)
        else:
            metadata_fields.append(key)
    return metadata_fields, workflow_fields


def classify_pm_action(payload: Dict[str, Any], *, is_decision: bool = False) -> PMActionKind:
    """Classify a payload into one explicit PM authority target."""

    metadata_fields, workflow_fields = classify_pm_write(payload)
    unsupported_fields = _unsupported_metadata_fields(payload)

    if workflow_fields:
        return PMActionKind.WORKFLOW_TRANSITION
    if unsupported_fields:
        raise ValueError(
            "Unsupported metadata fields for phase-1 Leantime writes: "
            f"{unsupported_fields}. The proven update_ticket tool surface only supports headline, description, and assignedTo aliases."
        )
    if metadata_fields:
        return PMActionKind.METADATA_UPDATE
    if is_decision:
        return PMActionKind.DECISION_LOG
    return PMActionKind.PROGRESS_LOG


def is_workflow_significant_payload(payload: Dict[str, Any]) -> bool:
    """Return True when a payload contains workflow-significant fields."""

    _, workflow_fields = classify_pm_write(payload)
    return bool(workflow_fields)


class MirrorReceipt(BaseModel):
    """Result of a best-effort downstream mirror write."""

    system: str
    success: bool
    persisted_id: Optional[str] = None
    error: Optional[str] = None


class CanonicalReceipt(BaseModel):
    """Result of a canonical PM-plane write operation."""

    canonical_system: str
    canonical_id: str
    success: bool
    operation_type: str
    version: Optional[int] = None
    mirror_receipts: List[MirrorReceipt] = Field(default_factory=list)
    reconciliation_state: str = "SYNCED"


class PMWriteConfig(BaseModel):
    """Dependency injection container for PM-plane write operations."""

    leantime_client: Any
    orchestrator_client: Any
    conport_client: Any
    memory_client: Any
    project_id: str = "default"


def _resolve_capture_repo_root(repo_root: Optional[Path], project_id: str) -> Optional[Path]:
    """Resolve the workspace root for capture ledger resolution.

    ``emit_capture_event`` otherwise falls back to ``Path.cwd()``, which fails
    in the composed Task Orchestrator container (runs from ``/app`` with
    ``.git``/``.dopemux`` excluded from the build), silently dropping PM source
    events even when the event bus is enabled. Prefer an explicit root, then the
    configured-workspace env vars the container sets, then ``project_id`` when it
    is itself a filesystem path. Returns ``None`` to let capture fall back to
    cwd (correct for the in-repo dopemux CLI runtime).
    """
    if repo_root is not None:
        return repo_root
    candidates = [
        os.getenv("DOPEMUX_WORKSPACE_ROOT", "").strip(),
        os.getenv("WORKSPACE_ID", "").strip(),
        os.getenv("DOPEMUX_PROJECT_ROOT", "").strip(),
        project_id.strip() if isinstance(project_id, str) else "",
    ]
    for value in candidates:
        if value:
            candidate = Path(value)
            if candidate.exists():
                return candidate
    return None


def emit_pm_promotable_source_event(
    event_type: str,
    *,
    project_id: str,
    work_item_id: str,
    canonical_system: str,
    operation_type: str,
    payload: Dict[str, Any],
    repo_root: Optional[Path] = None,
) -> None:
    """Emit a best-effort promotable capture event without changing PM authority.

    Source events become promotion-CAPABLE when the event bus is provisioned
    (ENABLE_EVENTBUS + REDIS_URL, via DOPEMUX_CAPTURE_EMIT_EVENTBUS); default
    dev environments remain ledger-only. ``emit_event_bus=None`` defers the
    fan-out decision to ``emit_capture_event``'s env resolution instead of
    hardcoding it off, so this is a no-op unless an operator opts in.

    Passes an explicit workspace root (from ``repo_root`` or the configured
    workspace env vars) so the composed Task Orchestrator container — which runs
    from ``/app`` without ``.git``/``.dopemux`` — doesn't silently drop the event
    via a failed ``Path.cwd()`` resolution.
    """

    event_payload = {
        **payload,
        "project_id": project_id,
        "task_id": work_item_id,
        "work_item_id": work_item_id,
        "canonical_system": canonical_system,
        "operation_type": operation_type,
        "authority": canonical_system,
    }
    try_emit_promotable_capture_event(
        event_type,
        event_payload,
        source="dopemux.pm",
        mode="auto",
        emit_event_bus=None,
        repo_root=_resolve_capture_repo_root(repo_root, project_id),
    )


def pm_update_work_item(
    config: PMWriteConfig,
    task_id: str,
    updates: Dict[str, Any],
    idempotency_key: str,
) -> CanonicalReceipt:
    """Update passive metadata for a work item through Leantime."""

    metadata_fields, workflow_fields = classify_pm_write(updates)
    if workflow_fields:
        raise ValueError(
            f"Cannot update workflow-significant fields {workflow_fields} via pm_update_work_item. "
            "Use pm_transition_work_item instead."
        )

    unsupported_fields = _unsupported_metadata_fields(updates)
    if unsupported_fields:
        raise ValueError(
            "Unsupported metadata fields for phase-1 Leantime writes: "
            f"{unsupported_fields}. The proven update_ticket tool surface only supports headline, description, and assignedTo aliases."
        )

    if not metadata_fields:
        raise ValueError("No supported metadata fields were provided.")

    if config.leantime_client is None:
        raise RuntimeError("Leantime client (PM metadata authority) is not configured.")

    try:
        _call_leantime_metadata_update(
            leantime_client=config.leantime_client,
            task_id=task_id,
            updates=updates,
            idempotency_key=idempotency_key,
        )
    except Exception as exc:
        raise RuntimeError(f"Canonical write failed: {exc}") from exc

    return CanonicalReceipt(
        canonical_system="leantime",
        canonical_id=task_id,
        success=True,
        operation_type=PMActionKind.METADATA_UPDATE.value,
        reconciliation_state="SYNCED",
    )


def pm_transition_work_item(
    config: PMWriteConfig,
    task_id: str,
    new_status: PMTaskStatus,
    reason: str,
    idempotency_key: str,
    expected_version: int,
) -> CanonicalReceipt:
    """Transition workflow state through the active task-orchestrator route only."""

    if config.orchestrator_client is None:
        raise RuntimeError("Task Orchestrator client (workflow authority) is not configured.")

    transition_name = TASK_ORCHESTRATOR_TRANSITIONS.get(new_status)
    if transition_name is None:
        raise ValueError(
            f"Unsupported phase-1 workflow target {new_status.value}. "
            "The proven project-scoped transition route currently supports only IN_PROGRESS, BLOCKED, and DONE transitions."
        )

    try:
        transition_result = config.orchestrator_client.transition(
            project_id=config.project_id,
            workflow_id=task_id,
            transition_name=transition_name,
            actor="dopemux",
            idempotency_key=idempotency_key,
            expected_version=expected_version,
            reason=reason,
        )
    except Exception as exc:
        raise RuntimeError(f"Canonical write failed: {exc}") from exc

    # Derive the prior phase from the orchestrator's receipt when available;
    # "unknown" only when the backend didn't report from_status.
    from_status = None
    if isinstance(transition_result, dict):
        receipt = transition_result.get("transition_receipt")
        if isinstance(receipt, dict):
            from_status = receipt.get("from_status")
    from_phase = "unknown"
    if from_status:
        try:
            from_phase = WORKFLOW_PHASE_CAPTURE_BY_STATUS.get(
                PMTaskStatus(from_status), "unknown"
            )
        except ValueError:
            from_phase = "unknown"

    emit_pm_promotable_source_event(
        "workflow.phase_changed",
        project_id=config.project_id,
        work_item_id=task_id,
        canonical_system="task-orchestrator",
        operation_type=PMActionKind.WORKFLOW_TRANSITION.value,
        payload={
            "from_phase": from_phase,
            "from_status": from_status,
            "to_phase": WORKFLOW_PHASE_CAPTURE_BY_STATUS.get(new_status, "maintenance"),
            "status": new_status.value,
            "transition": transition_name,
            "reason": reason,
            "expected_version": expected_version,
        },
    )
    task_event_type = TASK_STATUS_CAPTURE_EVENTS.get(new_status)
    if task_event_type:
        emit_pm_promotable_source_event(
            task_event_type,
            project_id=config.project_id,
            work_item_id=task_id,
            canonical_system="task-orchestrator",
            operation_type=PMActionKind.WORKFLOW_TRANSITION.value,
            payload={
                "title": f"Workflow item {task_id}",
                "status": new_status.value,
                "transition": transition_name,
                "reason": reason,
            },
        )
    if from_status == PMTaskStatus.BLOCKED.value and new_status != PMTaskStatus.BLOCKED:
        emit_pm_promotable_source_event(
            "blocker.cleared",
            project_id=config.project_id,
            work_item_id=task_id,
            canonical_system="task-orchestrator",
            operation_type=PMActionKind.WORKFLOW_TRANSITION.value,
            payload={
                "task_id": task_id,
                "title": f"Workflow item {task_id}",
                "status": new_status.value,
                "transition": transition_name,
                "reason": reason,
            },
        )

    return CanonicalReceipt(
        canonical_system="task-orchestrator",
        canonical_id=task_id,
        success=True,
        operation_type=PMActionKind.WORKFLOW_TRANSITION.value,
        version=expected_version + 1,
        mirror_receipts=[],
        reconciliation_state="SYNCED",
    )


def pm_log_progress(
    config: PMWriteConfig,
    task_id: str,
    progress_notes: str,
    idempotency_key: str,
    is_decision: bool = False,
) -> CanonicalReceipt:
    """Log progress or decisions to ConPort with dope-memory mirror receipts."""

    if config.conport_client is None:
        raise RuntimeError("ConPort client (decision/progress authority) is not configured.")

    operation_type = (
        PMActionKind.DECISION_LOG.value if is_decision else PMActionKind.PROGRESS_LOG.value
    )

    try:
        config.conport_client.record_progress(
            task_id,
            progress_notes,
            is_decision,
            idempotency_key=idempotency_key,
        )
    except Exception as exc:
        raise RuntimeError(f"Canonical write failed: {exc}") from exc

    if is_decision:
        emit_pm_promotable_source_event(
            "decision.logged",
            project_id=config.project_id,
            work_item_id=task_id,
            canonical_system="conport",
            operation_type=operation_type,
            payload={
                "decision_id": task_id,
                "title": f"Decision for {task_id}",
                "rationale": progress_notes,
            },
        )

    mirror_success = True
    mirror_error = None
    mirror_id = None
    try:
        if config.memory_client is not None:
            result = config.memory_client.append_chronicle(
                task_id,
                progress_notes,
                is_decision,
                idempotency_key=idempotency_key,
            )
            if isinstance(result, dict):
                mirror_id = result.get("entry_id")
        else:
            mirror_success = False
            mirror_error = "Memory client missing"
    except Exception as exc:
        mirror_success = False
        mirror_error = str(exc)

    return CanonicalReceipt(
        canonical_system="conport",
        canonical_id=task_id,
        success=True,
        operation_type=operation_type,
        mirror_receipts=[
            MirrorReceipt(
                system="dope-memory",
                success=mirror_success,
                persisted_id=mirror_id,
                error=mirror_error,
            )
        ],
        reconciliation_state="SYNCED" if mirror_success else "PARTIAL",
    )


def pm_log_decision(
    config: PMWriteConfig,
    task_id: str,
    decision_notes: str,
    idempotency_key: str,
) -> CanonicalReceipt:
    """Convenience wrapper for explicit decision logging."""

    return pm_log_progress(
        config=config,
        task_id=task_id,
        progress_notes=decision_notes,
        idempotency_key=idempotency_key,
        is_decision=True,
    )
