"""
Normalized PM-plane writes.

Implements ADR-PM-001 boundary enforcement and canonical receipts.
Provides the primary unified interface for agents and tools to modify
PM entities across the multi-system Dopemux architecture.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from .models import PMTaskStatus, WORKFLOW_SIGNIFICANT_FIELDS


class MirrorReceipt(BaseModel):
    """
    Result of a best-effort mirror write to a secondary system.

    Attributes:
        system (str): The identifier of the secondary system (e.g., 'leantime', 'dope-memory').
        success (bool): Whether the mirror operation succeeded.
        persisted_id (Optional[str]): The ID of the record in the mirror system, if applicable.
        error (Optional[str]): Error message if the operation failed.
    """
    system: str
    success: bool
    persisted_id: Optional[str] = None
    error: Optional[str] = None


class CanonicalReceipt(BaseModel):
    """
    Result of a canonical PM-plane write operation.

    This receipt guarantees that the primary authority system successfully
    processed the write. It also aggregates the status of any synchronous
    mirroring operations.

    Attributes:
        canonical_system (str): The authority system that owns this write (e.g., 'leantime').
        canonical_id (str): The ID of the modified entity in the canonical system.
        success (bool): Whether the canonical write succeeded. Must be True if returned.
        version (Optional[int]): The new optimistic concurrency version, if applicable.
        mirror_receipts (List[MirrorReceipt]): Results of downstream mirror writes.
        reconciliation_state (str): 'SYNCED' if all mirrors succeeded, 'PARTIAL' otherwise.
    """
    canonical_system: str
    canonical_id: str
    success: bool
    version: Optional[int] = None
    mirror_receipts: List[MirrorReceipt] = Field(default_factory=list)
    reconciliation_state: str = "SYNCED"


class PMWriteConfig(BaseModel):
    """
    Dependencies for PM-plane writes.

    Contains initialized clients for the various plane authorities.
    If a required client for a specific operation is None, the operation
    will fail-closed to preserve architectural integrity.

    Attributes:
        leantime_client (Any): PM Entity Authority client.
        orchestrator_client (Any): Workflow Authority client.
        conport_client (Any): Decision/Context Authority client.
        memory_client (Any): Chronicle/Memory Authority client.
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
    """
    Update passive metadata for a work item.

    Canonical Authority: Leantime (PM Entity Store)

    This function strictly rejects updates to workflow-significant fields
    (e.g., 'status'). Those updates must be explicitly routed through the
    Workflow Authority via `pm_transition_work_item`.

    Args:
        config (PMWriteConfig): The client configuration.
        task_id (str): The ID of the task to update.
        updates (Dict[str, Any]): The metadata fields to update.
        idempotency_key (str): Key to ensure safe retries. Client implementations
                               must enforce idempotency using this key.

    Returns:
        CanonicalReceipt: The receipt of the update operation.

    Raises:
        ValueError: If updates contain workflow-significant fields.
        RuntimeError: If the Leantime client is missing or the update fails.
    """
    if not isinstance(task_id, str):
        raise TypeError("task_id must be a string")
    if not idempotency_key or not idempotency_key.strip():
        raise ValueError("idempotency_key is required and cannot be empty")

    if not updates:
        raise ValueError("updates dictionary cannot be empty")

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

    This operation validates workflow rules (e.g., next-action computation, blockers)
    via the Task Orchestrator before applying the transition and subsequently
    mirroring the status change to the PM Entity store.

    Args:
        config (PMWriteConfig): The client configuration.
        task_id (str): The ID of the task to transition.
        new_status (PMTaskStatus): The target workflow status.
        reason (str): The justification for the transition.
        idempotency_key (str): Key to ensure safe retries.
        expected_version (int): The current optimistic version of the task to prevent stale writes.

    Returns:
        CanonicalReceipt: The receipt containing the canonical result and mirror status.

    Raises:
        ValueError: If required arguments are missing or invalid.
        RuntimeError: If the Task Orchestrator client is missing or the transition fails.
    """
    if not isinstance(task_id, str):
        raise TypeError("task_id must be a string")
    if not idempotency_key or not idempotency_key.strip():
        raise ValueError("idempotency_key is required and cannot be empty")

    if not isinstance(new_status, PMTaskStatus):
        raise ValueError("new_status must be a valid PMTaskStatus enum value")

    if expected_version < 1:
        raise ValueError("expected_version must be >= 1")

    # Fail closed if authority client is missing
    if config.orchestrator_client is None:
        raise RuntimeError("Task Orchestrator client (Workflow Authority) is not configured.")

    try:
        # Client implementations are responsible for enforcing idempotency
        config.orchestrator_client.transition(
            task_id, new_status, reason, expected_version, idempotency_key=idempotency_key
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
    """
    Log progress or record a decision context.

    Canonical Authority: ConPort (Decision/Context Authority)
    Mirror: dope-memory (Chronicle Work Log)

    Progress and decisions are owned by ConPort, which acts as the structured
    context authority. The operation is then mirrored to dope-memory to
    maintain the temporal chronological sequence of work.

    Args:
        config (PMWriteConfig): The client configuration.
        task_id (str): The ID of the task the progress relates to.
        progress_notes (str): The content of the progress or decision.
        idempotency_key (str): Key to ensure safe retries.
        is_decision (bool): Flag indicating if this log represents an architectural or workflow decision.

    Returns:
        CanonicalReceipt: The receipt containing the canonical result and mirror status.

    Raises:
        ValueError: If required arguments are missing or invalid.
        RuntimeError: If the ConPort client is missing or the canonical write fails.
    """
    if not isinstance(task_id, str):
        raise TypeError("task_id must be a string")
    if not idempotency_key or not idempotency_key.strip():
        raise ValueError("idempotency_key is required and cannot be empty")

    if not progress_notes or not progress_notes.strip():
        raise ValueError("progress_notes cannot be empty")

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
