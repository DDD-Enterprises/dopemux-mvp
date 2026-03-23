"""
Normalized PM-plane writes.

Implements ADR-PM-001 boundary enforcement and canonical receipts.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from .models import PMTaskStatus, WORKFLOW_SIGNIFICANT_FIELDS

class MirrorReceipt(BaseModel):
    """Result of a best-effort mirror write."""
    system: str
    success: bool
    persisted_id: Optional[str] = None
    error: Optional[str] = None

class CanonicalReceipt(BaseModel):
    """Result of a canonical PM-plane write."""
    canonical_system: str
    canonical_id: str
    success: bool
    version: Optional[int] = None
    mirror_receipts: List[MirrorReceipt] = Field(default_factory=list)
    reconciliation_state: str = "SYNCED"

class PMWriteConfig(BaseModel):
    """Dependencies for PM-plane writes."""
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
    """
    Update passive metadata for a work item.

    Canonical Authority: Leantime (PM Entity Store)

    Rejects any fields in WORKFLOW_SIGNIFICANT_FIELDS. Those must be
    routed through pm_transition_work_item.
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
    """
    Transition the workflow state of a work item.

    Canonical Authority: Task Orchestrator (Workflow Engine)
    Mirror: Leantime (PM Entity Store)
    """
    # Fail closed if authority client is missing
    if config.orchestrator_client is None:
        raise RuntimeError("Task Orchestrator client (Workflow Authority) is not configured.")

    try:
        # Client implementations are responsible for enforcing idempotency
        config.orchestrator_client.transition(task_id, new_status, reason, expected_version, idempotency_key=idempotency_key)
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
    """
    Log progress or record a decision context.

    Canonical Authority: ConPort (Decision/Context Authority)
    Mirror: dope-memory (Chronicle Work Log)
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
