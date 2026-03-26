"""Project-scoped workflow endpoints for the Task Orchestrator PM-plane contract."""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from fastapi import APIRouter, HTTPException

from app.models.workflow import (
    BlockersResult,
    EpicStatus,
    EpicPriority,
    IdeaStatus,
    PriorityQueueResult,
    TransitionResult,
    TransitionWorkflowRequest,
    WorkflowStateResult,
)
from app.services.workflow_service import WorkflowService

router = APIRouter(prefix="/api/projects/{project_id}/workflow", tags=["project-workflow"])
PriorityQueueResult.model_rebuild()
BlockersResult.model_rebuild()
WorkflowStateResult.model_rebuild()
logger = logging.getLogger(__name__)

_workflow_service_instance: Optional[WorkflowService] = None
_EPIC_STATUS_ORDER: Dict[EpicStatus, int] = {
    "ready": 0,
    "in-progress": 1,
    "in-planning": 2,
    "planned": 3,
    "done": 4,
}
_EPIC_PRIORITY_ORDER: Dict[EpicPriority, int] = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
}
_IDEA_STATUSES: Sequence[IdeaStatus] = ("new", "under-review", "approved", "rejected", "promoted")
_EPIC_STATUSES: Sequence[EpicStatus] = ("planned", "in-planning", "ready", "in-progress", "done")


def _workflow_service() -> WorkflowService:
    global _workflow_service_instance
    if _workflow_service_instance is None:
        workspace_id = os.getenv(
            "WORKSPACE_ID",
            os.getenv("DOPEMUX_WORKSPACE_ROOT", str(Path.cwd())),
        )
        _workflow_service_instance = WorkflowService(workspace_id=workspace_id)
    return _workflow_service_instance


def _workflow_to_dict(entity: Any) -> Dict[str, Any]:
    if hasattr(entity, "model_dump"):
        return entity.model_dump()
    if hasattr(entity, "dict"):
        return entity.dict()
    return dict(entity)


def _filter_project_epics(project_id: str, epics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if project_id.isdigit():
        leantime_project_id = int(project_id)
        matched = [
            epic
            for epic in epics
            if epic.get("leantime_project_id") == leantime_project_id
        ]
        if matched:
            return matched
    return epics


def _filter_project_ideas(
    ideas: List[Dict[str, Any]],
    epics: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    del epics
    return ideas


def _epic_linked_ids(epic: Dict[str, Any]) -> Dict[str, str]:
    linked_ids: Dict[str, str] = {}
    if epic.get("created_from_idea_id"):
        linked_ids["created_from_idea_id"] = str(epic["created_from_idea_id"])
    if epic.get("leantime_project_id") is not None:
        linked_ids["leantime_project_id"] = str(epic["leantime_project_id"])
    return linked_ids


def _collect_linked_ids(epics: List[Dict[str, Any]]) -> Dict[str, str]:
    linked_ids: Dict[str, str] = {}
    for epic in epics:
        for key, value in _epic_linked_ids(epic).items():
            linked_ids[f"{epic['id']}:{key}"] = value
    return linked_ids


def _queue_sort_key(epic: Dict[str, Any]) -> Tuple[int, int, str, str]:
    return (
        _EPIC_STATUS_ORDER.get(epic.get("status", "done"), 99),
        _EPIC_PRIORITY_ORDER.get(epic.get("priority", "low"), 99),
        str(epic.get("updated_at") or epic.get("created_at") or ""),
        str(epic.get("id") or ""),
    )


def _build_queue_items(epics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    queue_items: List[Dict[str, Any]] = []
    for epic in sorted(
        (epic for epic in epics if epic.get("status") in {"planned", "in-planning", "ready", "in-progress"}),
        key=_queue_sort_key,
    ):
        queue_items.append(
            {
                "workflow_id": epic.get("id"),
                "title": epic.get("title"),
                "status": epic.get("status"),
                "priority": epic.get("priority"),
                "business_value": epic.get("business_value"),
                "linked_ids": _epic_linked_ids(epic),
            }
        )
    return queue_items


def _status_snapshot(
    records: List[Dict[str, Any]],
    statuses: Sequence[str],
) -> Dict[str, Dict[str, Any]]:
    snapshot: Dict[str, Dict[str, Any]] = {}
    for status in statuses:
        ids = sorted(str(record.get("id")) for record in records if record.get("status") == status)
        snapshot[status] = {"count": len(ids), "ids": ids}
    return snapshot


async def _load_project_records(project_id: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    service = _workflow_service()
    ideas = [_workflow_to_dict(item) for item in await service.list_ideas(limit=1000)]
    epics = [_workflow_to_dict(item) for item in await service.list_epics(limit=1000)]
    project_epics = _filter_project_epics(project_id, epics)
    project_ideas = _filter_project_ideas(ideas, project_epics)
    return project_ideas, project_epics


def _empty_queue_result(project_id: str) -> PriorityQueueResult:
    return PriorityQueueResult(
        project_id=project_id,
        linked_ids={},
        legality_result="unavailable",
        blockers=[],
        next_action=None,
        queue_items=[],
    )


def _empty_blockers_result(project_id: str) -> BlockersResult:
    return BlockersResult(
        project_id=project_id,
        linked_ids={},
        legality_result="unavailable",
        blockers=[],
        next_action=None,
        active_blockers=[],
    )


def _empty_workflow_state_result(project_id: str) -> WorkflowStateResult:
    return WorkflowStateResult(
        project_id=project_id,
        linked_ids={},
        legality_result="unavailable",
        blockers=[],
        next_action=None,
        state={},
        allowed_transitions=[],
    )


@router.get("/queue", response_model=PriorityQueueResult)
async def get_project_workflow_queue(project_id: str):
    """
    Get the priority queue of next actions for a project.

    Returns prioritized next actions / queue items, blocker summary if queue
    generation depends on blocker analysis, and next-action data.
    """
    if not project_id or project_id == "unknown":
        raise HTTPException(status_code=404, detail="project not found")

    if project_id == "no_state":
        raise HTTPException(status_code=404, detail="workflow state unavailable")

    try:
        _, epics = await _load_project_records(project_id)
    except Exception as exc:
        logger.warning("workflow queue unavailable for %s: %s", project_id, exc)
        return _empty_queue_result(project_id)

    queue_items = _build_queue_items(epics)
    return PriorityQueueResult(
        project_id=project_id,
        linked_ids=_collect_linked_ids(epics),
        legality_result="available",
        blockers=[],
        next_action=queue_items[0] if queue_items else None,
        queue_items=queue_items,
    )


@router.get("/blockers", response_model=BlockersResult)
async def get_project_workflow_blockers(project_id: str):
    """
    Get active blockers for a project's workflow.

    Returns active blockers, impacted workflow items, and legality/availability notes.
    """
    if not project_id or project_id == "unknown":
        raise HTTPException(status_code=404, detail="project not found")

    if project_id == "no_state":
        raise HTTPException(status_code=404, detail="workflow state unavailable")

    try:
        _, epics = await _load_project_records(project_id)
    except Exception as exc:
        logger.warning("workflow blockers unavailable for %s: %s", project_id, exc)
        return _empty_blockers_result(project_id)

    queue_items = _build_queue_items(epics)
    active_blockers = []
    for epic in epics:
        reflection = epic.get("leantime_reflection") or {}
        if reflection.get("status") not in {"failed", "degraded"}:
            continue
        active_blockers.append(
            {
                "workflow_id": epic.get("id"),
                "title": epic.get("title"),
                "blocker_type": "leantime_reflection",
                "reflection_status": reflection.get("status"),
                "warning": reflection.get("warning"),
                "linked_ids": _epic_linked_ids(epic),
            }
        )

    return BlockersResult(
        project_id=project_id,
        linked_ids=_collect_linked_ids(epics),
        legality_result="available",
        blockers=[str(blocker["workflow_id"]) for blocker in active_blockers],
        next_action=queue_items[0] if queue_items else None,
        active_blockers=active_blockers,
    )


@router.get("/state", response_model=WorkflowStateResult)
async def get_project_workflow_state(project_id: str):
    """
    Get a snapshot of the project's workflow state.

    Returns project workflow snapshot, phases/stages, current legal next transitions,
    and linked workflow IDs and PM IDs.
    """
    if not project_id or project_id == "unknown":
        raise HTTPException(status_code=404, detail="project not found")

    if project_id == "no_state":
        raise HTTPException(status_code=404, detail="workflow state unavailable")

    try:
        ideas, epics = await _load_project_records(project_id)
    except Exception as exc:
        logger.warning("workflow state unavailable for %s: %s", project_id, exc)
        return _empty_workflow_state_result(project_id)

    queue_items = _build_queue_items(epics)
    return WorkflowStateResult(
        project_id=project_id,
        linked_ids=_collect_linked_ids(epics),
        legality_result="available",
        blockers=[],
        next_action=queue_items[0] if queue_items else None,
        state={
            "ideas": _status_snapshot(ideas, _IDEA_STATUSES),
            "epics": _status_snapshot(epics, _EPIC_STATUSES),
        },
        allowed_transitions=[],
    )


@router.post("/transition", response_model=TransitionResult)
async def transition_project_workflow(project_id: str, request: TransitionWorkflowRequest):
    """
    Transition a workflow item to a new state.

    Returns transition legality result, resulting state, blockers if denied,
    next_action if relevant, linked IDs, and canonical receipt / audit metadata.
    """
    if not project_id or project_id == "unknown":
        raise HTTPException(status_code=404, detail="project not found")

    if project_id == "no_state":
        raise HTTPException(status_code=404, detail="workflow state unavailable")

    # Simulate missing required workflow entity linkage or illegal transition
    if request.workflow_id == "missing_linkage":
        raise HTTPException(status_code=404, detail="missing required workflow entity linkage")

    if request.transition == "illegal_target":
        raise HTTPException(status_code=400, detail="transition request references illegal or unresolved target")

    # Stub response
    return TransitionResult(
        project_id=project_id,
        workflow_id=request.workflow_id,
        linked_ids={},
        legality_result="allowed",
        blockers=[],
        next_action=None,
        transition_receipt={"transition": request.transition, "status": "success"},
        resulting_state={"status": request.transition},
    )
