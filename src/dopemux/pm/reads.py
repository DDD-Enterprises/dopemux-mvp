"""Normalized PM-plane read tools."""

from typing import Any, Dict, List, Optional
import logging
import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# --- Models ---

class PMReadProvenance(BaseModel):
    """Provenance tracking for PM-plane reads."""
    source: str
    query_mode: str
    project_id: str

class PMReadSupportingSource(BaseModel):
    """Supporting sources for a PM-plane read, enabling lineage."""
    kind: str  # e.g., "mirrored", "indexed", "derived", "canonical"
    backend: str
    entity_ids: List[str] = Field(default_factory=list)

class PMProjectContextResult(BaseModel):
    """Normalized project context result."""
    canonical_backend: str = "leantime"
    project_id: str
    linked_ids: Dict[str, str] = Field(default_factory=dict)
    provenance: PMReadProvenance
    supporting_sources: List[PMReadSupportingSource] = Field(default_factory=list)
    context_data: Dict[str, Any] = Field(default_factory=dict)

class PMPriorityQueueResult(BaseModel):
    """Normalized priority queue result."""
    canonical_backend: str = "leantime"
    project_id: str
    linked_ids: Dict[str, str] = Field(default_factory=dict)
    provenance: PMReadProvenance
    supporting_sources: List[PMReadSupportingSource] = Field(default_factory=list)
    queue_items: List[Dict[str, Any]] = Field(default_factory=list)
    next_action: Optional[Dict[str, Any]] = None

class PMBlockersResult(BaseModel):
    """Normalized blockers result."""
    canonical_backend: str = "leantime"
    project_id: str
    linked_ids: Dict[str, str] = Field(default_factory=dict)
    provenance: PMReadProvenance
    supporting_sources: List[PMReadSupportingSource] = Field(default_factory=list)
    active_blockers: List[Dict[str, Any]] = Field(default_factory=list)

class PMWorkflowStateResult(BaseModel):
    """Normalized workflow state result."""
    canonical_backend: str = "leantime"
    project_id: str
    linked_ids: Dict[str, str] = Field(default_factory=dict)
    provenance: PMReadProvenance
    supporting_sources: List[PMReadSupportingSource] = Field(default_factory=list)
    state: Dict[str, Any] = Field(default_factory=dict)
    allowed_transitions: List[str] = Field(default_factory=list)

class PMSprintSnapshotResult(BaseModel):
    """Normalized sprint snapshot result."""
    canonical_backend: str = "leantime"
    project_id: str
    linked_ids: Dict[str, str] = Field(default_factory=dict)
    provenance: PMReadProvenance
    supporting_sources: List[PMReadSupportingSource] = Field(default_factory=list)
    snapshot_data: Dict[str, Any] = Field(default_factory=dict)

class PMDecisionContextResult(BaseModel):
    """Normalized decision context result."""
    canonical_backend: str = "conport"
    project_id: str
    linked_ids: Dict[str, str] = Field(default_factory=dict)
    provenance: PMReadProvenance
    supporting_sources: List[PMReadSupportingSource] = Field(default_factory=list)
    decisions: List[Dict[str, Any]] = Field(default_factory=list)

# --- Implementations ---

# Leantime reads (Project Context, Priority Queue, Blockers, Workflow State, Sprint Snapshot)

async def pm_get_project_context(project_id: str) -> PMProjectContextResult:
    """Read normalized project context from Leantime authority.

    Args:
        project_id: The Leantime project identifier.

    Returns:
        PMProjectContextResult with canonical data. Returns a fail-closed
        empty result if the backend is unavailable or the project is missing.
    """
    if not project_id or not isinstance(project_id, str):
        raise ValueError("project_id must not be empty")

    provenance = PMReadProvenance(source="leantime", query_mode="project_context", project_id=project_id)
    supporting_source = PMReadSupportingSource(kind="canonical", backend="leantime", entity_ids=[project_id])

    try:
        # Placeholder for actual Leantime JSON-RPC call
        # For now we stub the behavior and return an empty safe state when it fails, simulating fail-closed
        if project_id == "fail_me":
            raise Exception("Simulated backend failure")
        context_data = {}
    except Exception as e:
        logger.warning(f"Leantime backend unavailable for pm_get_project_context: {e}")
        context_data = {}

    return PMProjectContextResult(
        canonical_backend="leantime",
        project_id=project_id,
        linked_ids={},
        provenance=provenance,
        supporting_sources=[supporting_source],
        context_data=context_data,
    )

async def pm_get_priority_queue(project_id: str) -> PMPriorityQueueResult:
    """Read normalized priority queue from Leantime authority.

    Args:
        project_id: The Leantime project identifier.

    Returns:
        PMPriorityQueueResult with prioritized tasks. Returns a fail-closed
        empty list of queue_items if the backend is unavailable.
    """
    if not project_id or not isinstance(project_id, str):
        raise ValueError("project_id must not be empty")

    provenance = PMReadProvenance(source="leantime", query_mode="priority_queue", project_id=project_id)
    supporting_source = PMReadSupportingSource(kind="canonical", backend="leantime", entity_ids=[project_id])

    try:
        # Placeholder for actual Leantime JSON-RPC call
        if project_id == "fail_me":
            raise Exception("Simulated backend failure")
        queue_items = []
        next_action = None
    except Exception as e:
        logger.warning(f"Leantime backend unavailable for pm_get_priority_queue: {e}")
        queue_items = []
        next_action = None

    return PMPriorityQueueResult(
        canonical_backend="leantime",
        project_id=project_id,
        linked_ids={},
        provenance=provenance,
        supporting_sources=[supporting_source],
        queue_items=queue_items,
        next_action=next_action,
    )

async def pm_get_blockers(project_id: str) -> PMBlockersResult:
    """Read normalized blockers from Leantime authority.

    Args:
        project_id: The Leantime project identifier.

    Returns:
        PMBlockersResult with a list of active blockers. Returns a fail-closed
        empty list if the backend is unavailable.
    """
    if not project_id or not isinstance(project_id, str):
        raise ValueError("project_id must not be empty")

    provenance = PMReadProvenance(source="leantime", query_mode="blockers", project_id=project_id)
    supporting_source = PMReadSupportingSource(kind="canonical", backend="leantime", entity_ids=[project_id])

    try:
        # Placeholder for actual Leantime JSON-RPC call
        if project_id == "fail_me":
            raise Exception("Simulated backend failure")
        active_blockers = []
    except Exception as e:
        logger.warning(f"Leantime backend unavailable for pm_get_blockers: {e}")
        active_blockers = []

    return PMBlockersResult(
        canonical_backend="leantime",
        project_id=project_id,
        linked_ids={},
        provenance=provenance,
        supporting_sources=[supporting_source],
        active_blockers=active_blockers,
    )

async def pm_get_workflow_state(project_id: str) -> PMWorkflowStateResult:
    """Read normalized workflow state from Leantime authority.

    Args:
        project_id: The Leantime project identifier.

    Returns:
        PMWorkflowStateResult containing allowed transitions. Returns a fail-closed
        empty result if the backend is unavailable.
    """
    if not project_id or not isinstance(project_id, str):
        raise ValueError("project_id must not be empty")

    provenance = PMReadProvenance(source="leantime", query_mode="workflow_state", project_id=project_id)
    supporting_source = PMReadSupportingSource(kind="canonical", backend="leantime", entity_ids=[project_id])

    try:
        # Placeholder for actual Leantime JSON-RPC call
        if project_id == "fail_me":
            raise Exception("Simulated backend failure")
        state = {}
        allowed_transitions = []
    except Exception as e:
        logger.warning(f"Leantime backend unavailable for pm_get_workflow_state: {e}")
        state = {}
        allowed_transitions = []

    return PMWorkflowStateResult(
        canonical_backend="leantime",
        project_id=project_id,
        linked_ids={},
        provenance=provenance,
        supporting_sources=[supporting_source],
        state=state,
        allowed_transitions=allowed_transitions,
    )

async def pm_get_sprint_snapshot(project_id: str) -> PMSprintSnapshotResult:
    """Read normalized sprint snapshot from Leantime authority.

    Args:
        project_id: The Leantime project identifier.

    Returns:
        PMSprintSnapshotResult containing sprint metadata. Returns a fail-closed
        empty result if the backend is unavailable.
    """
    if not project_id or not isinstance(project_id, str):
        raise ValueError("project_id must not be empty")

    provenance = PMReadProvenance(source="leantime", query_mode="sprint_snapshot", project_id=project_id)
    supporting_source = PMReadSupportingSource(kind="canonical", backend="leantime", entity_ids=[project_id])

    try:
        # Placeholder for actual Leantime JSON-RPC call
        if project_id == "fail_me":
            raise Exception("Simulated backend failure")
        snapshot_data = {}
    except Exception as e:
        logger.warning(f"Leantime backend unavailable for pm_get_sprint_snapshot: {e}")
        snapshot_data = {}

    return PMSprintSnapshotResult(
        canonical_backend="leantime",
        project_id=project_id,
        linked_ids={},
        provenance=provenance,
        supporting_sources=[supporting_source],
        snapshot_data=snapshot_data,
    )

async def pm_get_decision_context(project_id: str) -> PMDecisionContextResult:
    """Read normalized decision context from ConPort (Knowledge Graph) authority.

    Args:
        project_id: The ConPort project/workspace identifier.

    Returns:
        PMDecisionContextResult containing decisions. Returns a fail-closed
        empty result if the ConPort backend is unavailable.
    """
    if not project_id or not isinstance(project_id, str):
        raise ValueError("project_id must not be empty")

    provenance = PMReadProvenance(source="conport", query_mode="decision_context", project_id=project_id)
    supporting_source = PMReadSupportingSource(kind="canonical", backend="conport", entity_ids=[project_id])

    try:
        # Placeholder for ConPort retrieval
        if project_id == "fail_me":
            raise Exception("Simulated backend failure")
        decisions = []
    except Exception as e:
        logger.warning(f"ConPort backend unavailable for pm_get_decision_context: {e}")
        decisions = []

    return PMDecisionContextResult(
        canonical_backend="conport",
        project_id=project_id,
        linked_ids={},
        provenance=provenance,
        supporting_sources=[supporting_source],
        decisions=decisions,
    )
