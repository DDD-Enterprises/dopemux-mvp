"""PM Plane read tools — canonical access to Orchestrator and ConPort."""

import logging
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel, Field

from dopemux.pm.adapters.conport import ConPortAdapter
from dopemux.pm.adapters.dope_memory import DopeMemoryAdapter
from dopemux.pm.adapters.orchestrator import TaskOrchestratorAdapter

logger = logging.getLogger(__name__)


class PMReadProvenance(BaseModel):
    """Minimal provenance envelope for PM-plane reads."""

    source: str
    query_mode: str


class PMReadSupportingSource(BaseModel):
    """Single supporting backend used to answer a read."""

    backend: str
    kind: str = "canonical"


class PMReadEnvelope(BaseModel):
    """Shared read envelope contract for PM-plane compatibility."""

    project_id: str
    canonical_backend: str
    linked_ids: Dict[str, str] = Field(default_factory=dict)
    provenance: PMReadProvenance
    supporting_sources: List[PMReadSupportingSource] = Field(default_factory=list)
    error: Optional[str] = None


class PMProjectContextResult(PMReadEnvelope):
    context_data: Dict[str, Any] = Field(default_factory=dict)


class PMPriorityQueueResult(PMReadEnvelope):
    legality_result: str = "unavailable"
    blockers: List[str] = Field(default_factory=list)
    next_action: Optional[Dict[str, Any]] = None
    queue_items: List[Dict[str, Any]] = Field(default_factory=list)


class PMBlockersResult(PMReadEnvelope):
    legality_result: str = "unavailable"
    blockers: List[str] = Field(default_factory=list)
    next_action: Optional[Dict[str, Any]] = None
    active_blockers: List[Dict[str, Any]] = Field(default_factory=list)


class PMWorkflowStateResult(PMReadEnvelope):
    legality_result: str = "unavailable"
    blockers: List[str] = Field(default_factory=list)
    next_action: Optional[Dict[str, Any]] = None
    state: Dict[str, Any] = Field(default_factory=dict)
    allowed_transitions: List[str] = Field(default_factory=list)


class PMSprintSnapshotResult(PMReadEnvelope):
    snapshot_data: Dict[str, Any] = Field(default_factory=dict)


class PMDecisionContextResult(PMReadEnvelope):
    decisions: List[Dict[str, Any]] = Field(default_factory=list)
    count: int = 0


_orchestrator = TaskOrchestratorAdapter()
_conport = ConPortAdapter()
_memory = DopeMemoryAdapter()


def _supporting_source(backend: str) -> List[PMReadSupportingSource]:
    return [PMReadSupportingSource(backend=backend)]


def _project_provenance(query_mode: str) -> PMReadProvenance:
    return PMReadProvenance(source="leantime", query_mode=query_mode)


def _decision_provenance() -> PMReadProvenance:
    return PMReadProvenance(source="conport", query_mode="decision_context")


def _queue_result(project_id: str, *, error: Optional[str] = None, payload: Optional[Dict[str, Any]] = None) -> PMPriorityQueueResult:
    payload = payload or {}
    return PMPriorityQueueResult(
        project_id=project_id,
        canonical_backend="leantime",
        linked_ids=payload.get("linked_ids", {}),
        provenance=_project_provenance("priority_queue"),
        supporting_sources=_supporting_source("leantime"),
        legality_result=payload.get("legality_result", "unavailable"),
        blockers=payload.get("blockers", []),
        next_action=payload.get("next_action"),
        queue_items=payload.get("queue_items", []),
        error=error,
    )


def _blockers_result(project_id: str, *, error: Optional[str] = None, payload: Optional[Dict[str, Any]] = None) -> PMBlockersResult:
    payload = payload or {}
    return PMBlockersResult(
        project_id=project_id,
        canonical_backend="leantime",
        linked_ids=payload.get("linked_ids", {}),
        provenance=_project_provenance("blockers"),
        supporting_sources=_supporting_source("leantime"),
        legality_result=payload.get("legality_result", "unavailable"),
        blockers=payload.get("blockers", []),
        next_action=payload.get("next_action"),
        active_blockers=payload.get("active_blockers", []),
        error=error,
    )


def _workflow_state_result(project_id: str, *, error: Optional[str] = None, payload: Optional[Dict[str, Any]] = None) -> PMWorkflowStateResult:
    payload = payload or {}
    return PMWorkflowStateResult(
        project_id=project_id,
        canonical_backend="leantime",
        linked_ids=payload.get("linked_ids", {}),
        provenance=_project_provenance("workflow_state"),
        supporting_sources=_supporting_source("leantime"),
        legality_result=payload.get("legality_result", "unavailable"),
        blockers=payload.get("blockers", []),
        next_action=payload.get("next_action"),
        state=payload.get("state", {}),
        allowed_transitions=payload.get("allowed_transitions", []),
        error=error,
    )


def _project_context_result(project_id: str, *, error: Optional[str] = None, payload: Optional[Dict[str, Any]] = None) -> PMProjectContextResult:
    payload = payload or {}
    return PMProjectContextResult(
        project_id=project_id,
        canonical_backend="leantime",
        linked_ids=payload.get("linked_ids", {}),
        provenance=_project_provenance("project_context"),
        supporting_sources=_supporting_source("leantime"),
        context_data=payload.get("context_data", {}),
        error=error,
    )


def _sprint_snapshot_result(project_id: str, *, error: Optional[str] = None, payload: Optional[Dict[str, Any]] = None) -> PMSprintSnapshotResult:
    payload = payload or {}
    return PMSprintSnapshotResult(
        project_id=project_id,
        canonical_backend="leantime",
        linked_ids=payload.get("linked_ids", {}),
        provenance=_project_provenance("sprint_snapshot"),
        supporting_sources=_supporting_source("leantime"),
        snapshot_data=payload.get("snapshot_data", {}),
        error=error,
    )


def _decision_context_result(project_id: str, *, error: Optional[str] = None, payload: Optional[Dict[str, Any]] = None) -> PMDecisionContextResult:
    payload = payload or {}
    decisions = payload.get("decisions", [])
    return PMDecisionContextResult(
        project_id=project_id,
        canonical_backend="conport",
        linked_ids=payload.get("linked_ids", {}),
        provenance=_decision_provenance(),
        supporting_sources=_supporting_source("conport"),
        decisions=decisions,
        count=payload.get("count", len(decisions)),
        error=error,
    )


async def pm_get_priority_queue(project_id: str) -> PMPriorityQueueResult:
    """Read prioritized next actions from the PM plane with compatibility envelopes."""

    try:
        return _queue_result(project_id, payload=await _orchestrator.get_queue(project_id))
    except httpx.HTTPError:
        logger.warning("task-orchestrator backend unavailable. Returning fail-closed empty result.")
        return _queue_result(project_id)
    except Exception as exc:
        logger.error("Unexpected error calling task-orchestrator: %s", exc)
        return _queue_result(project_id, error=str(exc))


async def pm_get_blockers(project_id: str) -> PMBlockersResult:
    """Read active blockers from the PM plane with compatibility envelopes."""

    try:
        return _blockers_result(project_id, payload=await _orchestrator.get_blockers(project_id))
    except httpx.HTTPError:
        logger.warning("task-orchestrator backend unavailable. Returning fail-closed empty result.")
        return _blockers_result(project_id)
    except Exception as exc:
        logger.error("Unexpected error calling task-orchestrator: %s", exc)
        return _blockers_result(project_id, error=str(exc))


async def pm_get_workflow_state(project_id: str) -> PMWorkflowStateResult:
    """Read workflow state from the PM plane with compatibility envelopes."""

    try:
        return _workflow_state_result(project_id, payload=await _orchestrator.get_state(project_id))
    except httpx.HTTPError:
        logger.warning("task-orchestrator backend unavailable. Returning fail-closed empty result.")
        return _workflow_state_result(project_id)
    except Exception as exc:
        logger.error("Unexpected error calling task-orchestrator: %s", exc)
        return _workflow_state_result(project_id, error=str(exc))


async def pm_get_decision_context(
    project_id: str,
    tag: Optional[str] = None,
    text: Optional[str] = None,
    limit: int = 3,
) -> PMDecisionContextResult:
    """Read decision context from ConPort while preserving the legacy envelope."""

    try:
        payload = await _conport.search_decisions(tag=tag, text=text, limit=limit)
        return _decision_context_result(project_id, payload=payload)
    except httpx.HTTPError:
        logger.warning("conport backend unavailable. Returning fail-closed empty result.")
        return _decision_context_result(project_id)
    except Exception as exc:
        logger.error("Unexpected error calling conport: %s", exc)
        return _decision_context_result(project_id, error=str(exc))


async def pm_get_project_context(project_id: str) -> PMProjectContextResult:
    """Read project context with a stable fail-closed envelope."""

    try:
        payload = await _orchestrator.get_project_context(project_id)
        return _project_context_result(project_id, payload=payload)
    except Exception as exc:
        logger.error("Error calling pm_get_project_context: %s", exc)
        return _project_context_result(project_id, error=str(exc))


async def pm_get_sprint_snapshot(project_id: str) -> PMSprintSnapshotResult:
    """Read sprint snapshot with a stable fail-closed envelope."""

    try:
        payload = await _orchestrator.get_sprint_snapshot(project_id)
        return _sprint_snapshot_result(project_id, payload=payload)
    except Exception as exc:
        logger.error("Error calling pm_get_sprint_snapshot: %s", exc)
        return _sprint_snapshot_result(project_id, error=str(exc))


async def pm_check_readiness() -> Dict[str, Any]:
    """Check readiness of all PM Plane authoritative backends."""

    orchestrator_ok = await _orchestrator.health()
    conport_ok = await _conport.health()
    memory_ok = await _memory.health()

    status = "healthy" if all([orchestrator_ok, conport_ok, memory_ok]) else "degraded"
    if not any([orchestrator_ok, conport_ok, memory_ok]):
        status = "unavailable"

    return {
        "status": status,
        "backends": {
            "task-orchestrator": "online" if orchestrator_ok else "offline",
            "conport-kg": "online" if conport_ok else "offline",
            "dope-memory": "online" if memory_ok else "offline",
        },
    }
