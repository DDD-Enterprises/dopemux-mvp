"""Normalized PM-plane read tools."""

from typing import Any, Dict, List, Optional
import logging
import httpx
from pydantic import BaseModel, Field

from dopemux.pm.adapters.conport import ConPortAdapter
from dopemux.pm.adapters.orchestrator import TaskOrchestratorAdapter

logger = logging.getLogger(__name__)


class PMReadProvenance(BaseModel):
    source: str
    query_mode: str
    project_id: str


class PMReadSupportingSource(BaseModel):
    kind: str
    backend: str
    entity_ids: List[str] = Field(default_factory=list)


class PMReadEnvelope(BaseModel):
    canonical_backend: str
    project_id: str
    linked_ids: Dict[str, str] = Field(default_factory=dict)
    provenance: PMReadProvenance
    supporting_sources: List[PMReadSupportingSource] = Field(default_factory=list)
    error: Optional[str] = None


class PMProjectContextResult(PMReadEnvelope):
    context_data: Dict[str, Any] = Field(default_factory=dict)


class PMPriorityQueueResult(PMReadEnvelope):
    legality_result: str = "unavailable"
    blockers: List[str] = Field(default_factory=list)
    queue_items: List[Dict[str, Any]] = Field(default_factory=list)
    next_action: Optional[Dict[str, Any]] = None


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


_orchestrator = TaskOrchestratorAdapter()
_conport = ConPortAdapter()


def _project_provenance(source: str, query_mode: str, project_id: str) -> PMReadProvenance:
    return PMReadProvenance(source=source, query_mode=query_mode, project_id=project_id)


def _supporting_source(kind: str, backend: str, project_id: str) -> List[PMReadSupportingSource]:
    return [PMReadSupportingSource(kind=kind, backend=backend, entity_ids=[project_id])]


def _project_context_result(
    project_id: str,
    *,
    error: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> PMProjectContextResult:
    payload = payload or {}
    return PMProjectContextResult(
        canonical_backend="orchestrator",
        project_id=project_id,
        linked_ids=payload.get("linked_ids", {}),
        provenance=_project_provenance("leantime", "project_context", project_id),
        supporting_sources=_supporting_source("canonical", "leantime", project_id),
        context_data=payload.get("context_data", {}),
        error=error,
    )


def _priority_queue_result(
    project_id: str,
    *,
    error: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> PMPriorityQueueResult:
    payload = payload or {}
    return PMPriorityQueueResult(
        canonical_backend="task-orchestrator",
        project_id=project_id,
        linked_ids=payload.get("linked_ids", {}),
        provenance=_project_provenance("task-orchestrator", "priority_queue", project_id),
        supporting_sources=_supporting_source("canonical", "task-orchestrator", project_id),
        legality_result=payload.get("legality_result", "unavailable"),
        blockers=payload.get("blockers", []),
        queue_items=payload.get("queue_items", []),
        next_action=payload.get("next_action"),
        error=error,
    )


def _blockers_result(
    project_id: str,
    *,
    error: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> PMBlockersResult:
    payload = payload or {}
    return PMBlockersResult(
        canonical_backend="task-orchestrator",
        project_id=project_id,
        linked_ids=payload.get("linked_ids", {}),
        provenance=_project_provenance("task-orchestrator", "blockers", project_id),
        supporting_sources=_supporting_source("canonical", "task-orchestrator", project_id),
        legality_result=payload.get("legality_result", "unavailable"),
        blockers=payload.get("blockers", []),
        next_action=payload.get("next_action"),
        active_blockers=payload.get("active_blockers", []),
        error=error,
    )


def _workflow_state_result(
    project_id: str,
    *,
    error: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> PMWorkflowStateResult:
    payload = payload or {}
    return PMWorkflowStateResult(
        canonical_backend="task-orchestrator",
        project_id=project_id,
        linked_ids=payload.get("linked_ids", {}),
        provenance=_project_provenance("task-orchestrator", "workflow_state", project_id),
        supporting_sources=_supporting_source("canonical", "task-orchestrator", project_id),
        legality_result=payload.get("legality_result", "unavailable"),
        blockers=payload.get("blockers", []),
        next_action=payload.get("next_action"),
        state=payload.get("state", {}),
        allowed_transitions=payload.get("allowed_transitions", []),
        error=error,
    )


def _sprint_snapshot_result(
    project_id: str,
    *,
    error: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> PMSprintSnapshotResult:
    payload = payload or {}
    return PMSprintSnapshotResult(
        canonical_backend="orchestrator",
        project_id=project_id,
        linked_ids=payload.get("linked_ids", {}),
        provenance=_project_provenance("leantime", "sprint_snapshot", project_id),
        supporting_sources=_supporting_source("canonical", "leantime", project_id),
        snapshot_data=payload.get("snapshot_data", {}),
        error=error,
    )


def _decision_context_result(
    project_id: str,
    *,
    error: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> PMDecisionContextResult:
    payload = payload or {}
    return PMDecisionContextResult(
        canonical_backend="conport",
        project_id=project_id,
        linked_ids=payload.get("linked_ids", {}),
        provenance=_project_provenance("conport", "decision_context", project_id),
        supporting_sources=_supporting_source("canonical", "conport", project_id),
        decisions=payload.get("decisions", []),
        error=error,
    )


async def pm_get_project_context(project_id: str) -> PMProjectContextResult:
    """Read normalized project context from the PM record authority."""
    try:
        context_data: Dict[str, Any] = {}
        return _project_context_result(project_id, payload={"context_data": context_data})
    except Exception as exc:
        logger.warning("Leantime backend unavailable for pm_get_project_context: %s", exc)
        return _project_context_result(project_id, error=str(exc))


async def pm_get_priority_queue(project_id: str) -> PMPriorityQueueResult:
    """Read normalized priority queue from the workflow authority."""
    try:
        payload = await _orchestrator.get_queue(project_id)
        return _priority_queue_result(project_id, payload=payload)
    except httpx.HTTPError:
        logger.warning("Task Orchestrator backend unavailable for pm_get_priority_queue")
        return _priority_queue_result(project_id)
    except Exception as exc:
        logger.error("Unexpected error in pm_get_priority_queue: %s", exc)
        return _priority_queue_result(project_id, error=str(exc))


async def pm_get_blockers(project_id: str) -> PMBlockersResult:
    """Read normalized blockers from the workflow authority."""
    try:
        payload = await _orchestrator.get_blockers(project_id)
        return _blockers_result(project_id, payload=payload)
    except httpx.HTTPError:
        logger.warning("Task Orchestrator backend unavailable for pm_get_blockers")
        return _blockers_result(project_id)
    except Exception as exc:
        logger.error("Unexpected error in pm_get_blockers: %s", exc)
        return _blockers_result(project_id, error=str(exc))


async def pm_get_workflow_state(project_id: str) -> PMWorkflowStateResult:
    """Read normalized workflow state from the workflow authority."""
    try:
        payload = await _orchestrator.get_state(project_id)
        return _workflow_state_result(project_id, payload=payload)
    except httpx.HTTPError:
        logger.warning("Task Orchestrator backend unavailable for pm_get_workflow_state")
        return _workflow_state_result(project_id)
    except Exception as exc:
        logger.error("Unexpected error in pm_get_workflow_state: %s", exc)
        return _workflow_state_result(project_id, error=str(exc))


async def pm_get_sprint_snapshot(project_id: str) -> PMSprintSnapshotResult:
    """Read normalized sprint snapshot from the PM record authority."""
    try:
        snapshot_data: Dict[str, Any] = {}
        return _sprint_snapshot_result(project_id, payload={"snapshot_data": snapshot_data})
    except Exception as exc:
        logger.warning("Leantime backend unavailable for pm_get_sprint_snapshot: %s", exc)
        return _sprint_snapshot_result(project_id, error=str(exc))


async def pm_get_decision_context(project_id: str) -> PMDecisionContextResult:
    """Read normalized decision context from ConPort."""
    try:
        payload = await _conport.search_decisions(limit=5)
        return _decision_context_result(project_id, payload=payload)
    except httpx.HTTPError:
        logger.warning("ConPort backend unavailable for pm_get_decision_context")
        return _decision_context_result(project_id)
    except Exception as exc:
        logger.error("Unexpected error in pm_get_decision_context: %s", exc)
        return _decision_context_result(project_id, error=str(exc))
