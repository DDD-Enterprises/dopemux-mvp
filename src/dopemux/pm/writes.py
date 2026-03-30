"""
Normalized PM-plane writes.

Implements ADR-PM-001 boundary enforcement and canonical receipts.
"""

from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from .models import PMTaskStatus, WORKFLOW_SIGNIFICANT_FIELDS
from .mapping import CANONICAL_TO_ORCHESTRATOR

ALLOWED_METADATA_FIELDS = frozenset(
    {
        "title",
        "headline",
        "description",
        "details",
        "assignee",
        "assigned_to",
        "owner",
        "labels",
        "tags",
        "due_date",
        "start_date",
        "end_date",
        "priority",
        "estimate",
        "story_points",
        "notes",
        "comments",
        "reflection_metadata",
        "linked_ids",
        "refs",
        "meta",
        "source_task_id",
        "milestone",
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
        "promote",
        "demote",
        "next_action",
    }
)

WORKFLOW_FIELD_SUFFIXES = ("_status", "_state", "_phase", "_stage")


def _looks_workflow_significant_key(key_lower: str) -> bool:
    """Fail closed for likely workflow keys without substring collisions."""

    return key_lower.endswith(WORKFLOW_FIELD_SUFFIXES)


def classify_pm_write(payload: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """Classify payload keys into metadata and workflow-significant fields.

    Unknown fields default to metadata unless they match a workflow-like key
    pattern, in which case they fail closed into the workflow bucket.
    """

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
    operation_type: Optional[str] = None
    reflection_state: str = "succeeded"
    mirror_receipts: List[MirrorReceipt] = Field(default_factory=list)
    reconciliation_state: str = "SYNCED"

class PMWriteConfig(BaseModel):
    """Dependencies for PM-plane writes."""
    leantime_client: Any
    orchestrator_client: Any
    conport_client: Any
    memory_client: Any


def _transition_name_for_status(status: PMTaskStatus) -> str:
    return CANONICAL_TO_ORCHESTRATOR.get(status, status.value).lower()

def pm_update_work_item(
    config: PMWriteConfig,
    task_id: str,
    updates: Dict[str, Any],
    idempotency_key: str,
) -> CanonicalReceipt:
    """
    Update passive metadata for a work item.
    
    Canonical Authority: Leantime (PM Entity Store)
    
    Rejects any workflow-significant payload as determined by PM write
    classification. Those changes must be routed through
    pm_transition_work_item instead.
    """
    metadata_fields, workflow_fields = classify_pm_write(updates)

    if workflow_fields:
        raise ValueError(
            f"Cannot update workflow-significant fields {workflow_fields} via pm_update_work_item. "
            "Use pm_transition_work_item instead."
        )

    if not metadata_fields:
        raise ValueError("No metadata fields provided for pm_update_work_item.")

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
        operation_type="metadata_update",
        reflection_state="succeeded",
        reconciliation_state="SYNCED"
    )

def pm_transition_work_item(
    config: PMWriteConfig,
    task_id: str,
    new_status: PMTaskStatus,
    reason: str,
    idempotency_key: str,
    expected_version: int,
    *,
    project_id: str = "default",
    workflow_id: Optional[str] = None,
    actor: str = "dopemux",
) -> CanonicalReceipt:
    """
    Transition the workflow state of a work item.
    
    Canonical Authority: Task Orchestrator (Workflow Engine)
    Mirror: Leantime (PM Entity Store)
    """
    # Fail closed if authority client is missing
    if config.orchestrator_client is None:
        raise RuntimeError("Task Orchestrator client (Workflow Authority) is not configured.")

    version_after = expected_version + 1
    try:
        transition_response = None
        transition_name = _transition_name_for_status(new_status)
        target_workflow_id = workflow_id or task_id
        try:
            transition_response = config.orchestrator_client.transition(
                project_id=project_id,
                workflow_id=target_workflow_id,
                transition_name=transition_name,
                actor=actor,
                idempotency_key=idempotency_key,
                expected_version=expected_version,
                reason=reason,
            )
        except TypeError:
            # Compatibility path for older sync bridge clients that still expose
            # the task-centric transition signature.
            transition_response = config.orchestrator_client.transition(
                task_id,
                new_status,
                reason,
                expected_version,
                idempotency_key=idempotency_key,
            )
        if isinstance(transition_response, dict):
            legality_result = transition_response.get("legality_result")
            if legality_result and legality_result != "allowed":
                raise RuntimeError(
                    f"Task Orchestrator rejected transition with legality_result={legality_result}"
                )
            version_after = (
                transition_response.get("resulting_state", {}).get("version")
                or transition_response.get("transition_receipt", {}).get("version_after")
                or version_after
            )
    except Exception as e:
        raise RuntimeError(f"Canonical write failed: {e}") from e

    # Mirror to Leantime (Partial Failure Handling)
    mirror_success = True
    mirror_error = None
    reflection_state = "succeeded"
    try:
        if config.leantime_client is not None:
            config.leantime_client.update_status(task_id, new_status.value, idempotency_key=idempotency_key)
        else:
            mirror_success = False
            mirror_error = "Leantime client missing"
            reflection_state = "degraded"
    except Exception as e:
        mirror_success = False
        mirror_error = str(e)
        reflection_state = "degraded"
    
    return CanonicalReceipt(
        canonical_system="task-orchestrator",
        canonical_id=task_id,
        success=True,
        version=version_after,
        operation_type="transition",
        reflection_state=reflection_state,
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
    reflection_state = "succeeded"
    try:
        if config.memory_client is not None:
            config.memory_client.append_chronicle(task_id, progress_notes, is_decision, idempotency_key=idempotency_key)
        else:
            mirror_success = False
            mirror_error = "Memory client missing"
            reflection_state = "degraded"
    except Exception as e:
        mirror_success = False
        mirror_error = str(e)
        reflection_state = "degraded"

    return CanonicalReceipt(
        canonical_system="conport",
        canonical_id=task_id,
        success=True,
        operation_type="log_progress",
        reflection_state=reflection_state,
        mirror_receipts=[
            MirrorReceipt(system="dope-memory", success=mirror_success, error=mirror_error)
        ],
        reconciliation_state="SYNCED" if mirror_success else "PARTIAL"
    )
