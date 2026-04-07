"""
Normalized PM-plane writes.

Implements ADR-PM-001 boundary enforcement and canonical receipts.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from .models import PMTaskStatus, WORKFLOW_SIGNIFICANT_FIELDS

# Allowed PM metadata fields that do not change workflow legality
ALLOWED_METADATA_FIELDS = {
    "title", "headline", "description", "details",
    "assignee", "assigned_to", "owner",
    "labels", "tags",
    "due_date", "start_date", "end_date",
    "priority", "estimate", "story_points",
    "notes", "comments",
    "reflection_metadata"
}

EXPLICIT_WORKFLOW_FIELDS = frozenset(
    {field.lower() for field in WORKFLOW_SIGNIFICANT_FIELDS}
    | {"state", "phase", "stage", "transition", "blocked", "blocker", "promote", "demote", "next_action"}
)

WORKFLOW_FIELD_SUFFIXES = ("_status", "_state", "_phase", "_stage")


def _looks_workflow_significant_key(key_lower: str) -> bool:
    """Fail closed for likely workflow keys without substring collisions."""

    return key_lower.endswith(WORKFLOW_FIELD_SUFFIXES)


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


def is_workflow_significant_payload(payload: Dict[str, Any]) -> bool:
    """Return True when a payload contains workflow-significant fields."""
    _, workflow_fields = classify_pm_write(payload)
    return bool(workflow_fields)


class MirrorReceipt(BaseModel):
    """Result of a best-effort mirror write to an external system.
    
    A mirror write is a secondary update to a projection path (like Leantime)
    that follows a primary canonical write.
    """
    system: str
    success: bool
    persisted_id: Optional[str] = None
    error: Optional[str] = None

class CanonicalReceipt(BaseModel):
    """Result of a canonical PM-plane write operation.
    
    Contains the authoritative system used, the resulting canonical ID, 
    and any receipts from downstream mirrors updated during the operation.
    """
    canonical_system: str
    canonical_id: str
    success: bool
    version: Optional[int] = None
    mirror_receipts: List[MirrorReceipt] = Field(default_factory=list)
    reconciliation_state: str = "SYNCED"

class PMWriteConfig(BaseModel):
    """Dependency injection container for PM-plane write operations.
    
    Encapsulates the various client authorities required to perform 
    cross-plane task synchronization.
    """
    leantime_client: Any
    orchestrator_client: Any
    conport_client: Any
    memory_client: Any

def pm_update_work_item(
    config: PMWriteConfig,
    task_id: str,
    updates: Dict[str, Any],
    idempotency_key: str,
) -> CanonicalReceipt:
    """Update passive metadata for a work item.
    
    Authority: Leantime (PM Entity Store) serves as the authority for 
    non-structural metadata (title, description, etc.).
    
    Boundary Enforcement: This function rejects any fields present in 
    WORKFLOW_SIGNIFICANT_FIELDS. Such fields must be routed through 
    the strict `pm_transition_work_item` pathway.

    Args:
        config: Injected dependencies.
        task_id: The canonical ID of the task.
        updates: Dictionary of metadata updates.
        idempotency_key: Unique key for the operation.

    Returns:
        A CanonicalReceipt for the Leantime update.
    """
    # Enforce workflow authority boundary
    illegal_fields = set(updates.keys()) & WORKFLOW_SIGNIFICANT_FIELDS
    if illegal_fields:
        raise ValueError(
            f"Cannot update workflow-significant fields {illegal_fields} via pm_update_work_item. "
            "Use pm_transition_work_item instead."
        )

    # Fail closed if authority client is missing
    if config.leantime_client is None:
        raise RuntimeError("Leantime client (PM Entity Authority) is not configured.")

    try:
        # Client implementations are responsible for enforcing idempotency
        config.leantime_client.update_task(task_id, updates, idempotency_key=idempotency_key)
    except Exception as e:
        raise RuntimeError(f"Canonical write failed: {e}") from e

    return CanonicalReceipt(
        canonical_system="leantime",
        canonical_id=task_id,
        success=True,
        reconciliation_state="SYNCED"
    )

def pm_transition_work_item(
    config: PMWriteConfig,
    task_id: str,
    new_status: PMTaskStatus,
    reason: str,
    idempotency_key: str,
    expected_version: int,
) -> CanonicalReceipt:
    """Transition the workflow state of a work item across authorities.
    
    This function implements the core Two-Plane transition logic:
    1. Primary Write: Task Orchestrator (Workflow/Execution Authority).
    2. Mirror Write: Leantime (PM Entity Store).

    Args:
        config: Injected dependencies.
        task_id: The canonical task ID.
        new_status: Target PMTaskStatus.
        reason: Justification for the state change.
        idempotency_key: Unique key to prevent duplicate transitions.
        expected_version: Version check for optimistic concurrency.

    Returns:
        A CanonicalReceipt outlining the transition status.
    """
    # Fail closed if authority client is missing
    if config.orchestrator_client is None:
        raise RuntimeError("Task Orchestrator client (Workflow Authority) is not configured.")

    try:
        # Client implementations are responsible for enforcing idempotency
        config.orchestrator_client.transition(
            project_id="default",
            workflow_id=task_id,
            transition_name=new_status.value.lower(),
            actor="dopemux",
            idempotency_key=idempotency_key,
            expected_version=expected_version,
            reason=reason,
        )
    except Exception as e:
        raise RuntimeError(f"Canonical write failed: {e}") from e

    # Mirror to Leantime (Partial Failure Handling)
    mirror_success = True
    mirror_error = None
    try:
        if config.leantime_client is not None:
            config.leantime_client.update_status(task_id, new_status.value, idempotency_key=idempotency_key)
        else:
            mirror_success = False
            mirror_error = "Leantime client missing"
    except Exception as e:
        mirror_success = False
        mirror_error = str(e)
    
    return CanonicalReceipt(
        canonical_system="task-orchestrator",
        canonical_id=task_id,
        success=True,
        version=expected_version + 1,
        mirror_receipts=[
            MirrorReceipt(system="leantime", success=mirror_success, persisted_id=task_id if mirror_success else None, error=mirror_error)
        ],
        reconciliation_state="SYNCED" if mirror_success else "PARTIAL"
    )

def pm_log_progress(
    config: PMWriteConfig,
    task_id: str,
    progress_notes: str,
    idempotency_key: str,
    is_decision: bool = False,
) -> CanonicalReceipt:
    """Log progress or record a decision context in the Knowledge Graph.
    
    1. Primary Write: ConPort (Decision/Context Authority).
    2. Mirror Write: Dope-Memory (Chronicle Ledger).

    Args:
        config: Injected dependencies.
        task_id: Canonical task ID.
        progress_notes: Description of the work or decision.
        idempotency_key: Unique key for the ledger entry.
        is_decision: Boolean flag indicating an authoritative decision.

    Returns:
        A CanonicalReceipt for the context write.
    """
    # Fail closed if authority client is missing
    if config.conport_client is None:
        raise RuntimeError("ConPort client (Decision/Context Authority) is not configured.")

    # Canonical write
    try:
        # Client implementations are responsible for enforcing idempotency
        config.conport_client.record_progress(task_id, progress_notes, is_decision, idempotency_key=idempotency_key)
    except Exception as e:
        raise RuntimeError(f"Canonical write failed: {e}") from e
    
    # Mirror to dope-memory chronicle (Partial Failure Handling)
    mirror_success = True
    mirror_error = None
    try:
        if config.memory_client is not None:
            config.memory_client.append_chronicle(task_id, progress_notes, is_decision, idempotency_key=idempotency_key)
        else:
            mirror_success = False
            mirror_error = "Memory client missing"
    except Exception as e:
        mirror_success = False
        mirror_error = str(e)

    return CanonicalReceipt(
        canonical_system="conport",
        canonical_id=task_id,
        success=True,
        mirror_receipts=[
            MirrorReceipt(system="dope-memory", success=mirror_success, error=mirror_error)
        ],
        reconciliation_state="SYNCED" if mirror_success else "PARTIAL"
    )
