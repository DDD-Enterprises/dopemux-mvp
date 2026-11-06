"""Project-scoped workflow endpoints for the Task Orchestrator PM-plane contract."""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from fastapi import APIRouter, HTTPException, Request
from dopemux.pm.mapping import ORCHESTRATOR_TO_CANONICAL
from dopemux.pm.models import PMTaskStatus

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
TransitionResult.model_rebuild()
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
_RUNTIME_TRANSITIONS: Dict[str, Tuple[Tuple[PMTaskStatus, ...], PMTaskStatus]] = {
    "start": ((PMTaskStatus.TODO,), PMTaskStatus.IN_PROGRESS),
    "block": ((PMTaskStatus.TODO, PMTaskStatus.IN_PROGRESS, PMTaskStatus.BLOCKED), PMTaskStatus.BLOCKED),
    "done": ((PMTaskStatus.IN_PROGRESS,), PMTaskStatus.DONE),
}


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


def _workflow_service_from_request(request: Request):
    """Get the workflow service from the app state coordinator."""
    coordinator = getattr(request.app.state, "coordinator", None)
    if not coordinator:
        raise HTTPException(status_code=503, detail="coordinator unavailable")
    
    service = getattr(coordinator, "workflow_service", None)
    if not service:
        raise HTTPException(status_code=503, detail="workflow service unavailable")
    
    return service


def _task_runtime(request: Optional[Request] = None):
    """Return the task runtime when the service is running in runtime mode."""

    if request is None:
        return None
    app = getattr(request, "app", None)
    state = getattr(app, "state", None)
    return getattr(state, "task_runtime", None)


def _runtime_canonical_status(runtime: Any, task_id: str) -> Optional[PMTaskStatus]:
    """Resolve a task's canonical PM status from the runtime and PM mirror."""

    pm_store = getattr(runtime, "pm_store", None)
    if pm_store is not None:
        pm_task = pm_store.get(task_id)
        if pm_task is not None:
            return pm_task.status

    task = getattr(runtime, "tasks", {}).get(task_id)
    if task is None:
        return None
    return ORCHESTRATOR_TO_CANONICAL.get(getattr(task.status, "value", str(task.status)))


def _runtime_blockers_for_task(runtime: Any, task: Any) -> List[str]:
    """Return dependency ids preventing a runtime task from becoming ready."""

    blockers: List[str] = []
    for dependency_id in getattr(task, "dependencies", []):
        if _runtime_canonical_status(runtime, dependency_id) != PMTaskStatus.DONE:
            blockers.append(dependency_id)
    return blockers


def _runtime_queue_snapshot(runtime: Any) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Build ready queue items and blocker ids from the runtime task graph."""

    queue_items: List[Dict[str, Any]] = []
    blockers: List[str] = []
    tasks = getattr(runtime, "tasks", {})
    for task in tasks.values():
        canonical_status = _runtime_canonical_status(runtime, task.id)
        if canonical_status == PMTaskStatus.DONE:
            continue

        dependency_blockers = _runtime_blockers_for_task(runtime, task)
        if dependency_blockers:
            blockers.append(task.id)
            continue

        if canonical_status == PMTaskStatus.TODO:
            queue_items.append(
                {
                    "id": task.id,
                    "workflow_id": task.id,
                    "title": task.title,
                    "status": canonical_status.value,
                    "priority": getattr(task, "priority", None),
                    "dependencies": list(getattr(task, "dependencies", [])),
                }
            )

    queue_items.sort(key=lambda item: (-int(item.get("priority") or 0), str(item["id"])))
    blockers.sort()
    return queue_items, blockers


@router.get("/queue", response_model=PriorityQueueResult)
async def get_project_workflow_queue(project_id: str, request: Request):
    raise HTTPException(status_code=503, detail="Canonical ownership v2 required; v1 reads held")


@router.get("/blockers", response_model=BlockersResult)
async def get_project_workflow_blockers(project_id: str, request: Request):
    raise HTTPException(status_code=503, detail="Canonical ownership v2 required; v1 reads held")


@router.get("/state", response_model=WorkflowStateResult)
async def get_project_workflow_state(project_id: str, request: Request):
    raise HTTPException(status_code=503, detail="Canonical ownership v2 required; v1 reads held")


async def execute_transition_project_workflow(
    project_id: str,
    payload: TransitionWorkflowRequest,
    request: Optional[Request] = None,
):
    raise HTTPException(status_code=503, detail="Canonical ownership v2 required; v1 transitions held")


@router.post("/transition", response_model=TransitionResult)
async def transition_project_workflow(project_id: str, payload: TransitionWorkflowRequest, request: Request):
    return await execute_transition_project_workflow(project_id, payload, request)
