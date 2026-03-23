"""Normalized PM-plane read tools."""

from typing import Any, Dict, List, Optional
import logging
import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# --- Models ---

class PMReadProvenance(BaseModel):
    source: str
    query_mode: str
    project_id: str

class PMReadSupportingSource(BaseModel):
    kind: str  # e.g., "mirrored", "indexed", "derived", "canonical"
    backend: str
    entity_ids: List[str] = Field(default_factory=list)

class PMProjectContextResult(BaseModel):
    canonical_backend: str = "leantime"
    project_id: str
    linked_ids: Dict[str, str] = Field(default_factory=dict)
    provenance: PMReadProvenance
    supporting_sources: List[PMReadSupportingSource] = Field(default_factory=list)
    context_data: Dict[str, Any] = Field(default_factory=dict)

class PMPriorityQueueResult(BaseModel):
    canonical_backend: str = "leantime"
    project_id: str
    linked_ids: Dict[str, str] = Field(default_factory=dict)
    provenance: PMReadProvenance
    supporting_sources: List[PMReadSupportingSource] = Field(default_factory=list)
    queue_items: List[Dict[str, Any]] = Field(default_factory=list)
    next_action: Optional[Dict[str, Any]] = None

class PMBlockersResult(BaseModel):
    canonical_backend: str = "leantime"
    project_id: str
    linked_ids: Dict[str, str] = Field(default_factory=dict)
    provenance: PMReadProvenance
    supporting_sources: List[PMReadSupportingSource] = Field(default_factory=list)
    active_blockers: List[Dict[str, Any]] = Field(default_factory=list)

class PMWorkflowStateResult(BaseModel):
    canonical_backend: str = "leantime"
    project_id: str
    linked_ids: Dict[str, str] = Field(default_factory=dict)
    provenance: PMReadProvenance
    supporting_sources: List[PMReadSupportingSource] = Field(default_factory=list)
    state: Dict[str, Any] = Field(default_factory=dict)
    allowed_transitions: List[str] = Field(default_factory=list)

class PMSprintSnapshotResult(BaseModel):
    canonical_backend: str = "leantime"
    project_id: str
    linked_ids: Dict[str, str] = Field(default_factory=dict)
    provenance: PMReadProvenance
    supporting_sources: List[PMReadSupportingSource] = Field(default_factory=list)
    snapshot_data: Dict[str, Any] = Field(default_factory=dict)

class PMDecisionContextResult(BaseModel):
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

    Returns fail-closed empty result if backend is down.
    """
    provenance = PMReadProvenance(source="leantime", query_mode="project_context", project_id=project_id)
    supporting_source = PMReadSupportingSource(kind="canonical", backend="leantime", entity_ids=[project_id])

    try:
        # Placeholder for actual Leantime JSON-RPC call
        # For now we stub the behavior and return an empty safe state when it fails, simulating fail-closed
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

    Returns fail-closed empty result if backend is down.
    """
    provenance = PMReadProvenance(source="leantime", query_mode="priority_queue", project_id=project_id)
    supporting_source = PMReadSupportingSource(kind="canonical", backend="leantime", entity_ids=[project_id])

    try:
        # Placeholder for actual Leantime JSON-RPC call
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

    Returns fail-closed empty result if backend is down.
    """
    provenance = PMReadProvenance(source="leantime", query_mode="blockers", project_id=project_id)
    supporting_source = PMReadSupportingSource(kind="canonical", backend="leantime", entity_ids=[project_id])

    try:
        # Placeholder for actual Leantime JSON-RPC call
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

    Returns fail-closed empty result if backend is down.
    """
    provenance = PMReadProvenance(source="leantime", query_mode="workflow_state", project_id=project_id)
    supporting_source = PMReadSupportingSource(kind="canonical", backend="leantime", entity_ids=[project_id])

    try:
        # Placeholder for actual Leantime JSON-RPC call
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

    Returns fail-closed empty result if backend is down.
    """
    provenance = PMReadProvenance(source="leantime", query_mode="sprint_snapshot", project_id=project_id)
    supporting_source = PMReadSupportingSource(kind="canonical", backend="leantime", entity_ids=[project_id])

    try:
        # Placeholder for actual Leantime JSON-RPC call
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

    Returns fail-closed empty result if backend is down.
    """
    provenance = PMReadProvenance(source="conport", query_mode="decision_context", project_id=project_id)
    supporting_source = PMReadSupportingSource(kind="canonical", backend="conport", entity_ids=[project_id])

    try:
        # Placeholder for ConPort retrieval
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
