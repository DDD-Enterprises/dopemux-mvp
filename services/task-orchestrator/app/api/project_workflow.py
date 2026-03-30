"""Project-scoped workflow endpoints for the Task Orchestrator PM-plane contract."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, Optional

from fastapi import APIRouter, HTTPException, Request

from dopemux.pm.mapping import CANONICAL_TO_ORCHESTRATOR
from dopemux.pm.models import PMTaskStatus, PMTransitionRequest
from dopemux.pm.store import IdempotencyMismatchError, StaleWriteError, TaskNotFoundError

from app.models.workflow import (
    BlockersResult,
    PriorityQueueResult,
    TransitionResult,
    TransitionWorkflowRequest,
    WorkflowStateResult,
)

router = APIRouter(prefix="/api/projects/{project_id}/workflow", tags=["project-workflow"])


_ALLOWED_TRANSITIONS: dict[PMTaskStatus, dict[str, PMTaskStatus]] = {
    PMTaskStatus.TODO: {
        "start": PMTaskStatus.IN_PROGRESS,
        "in_progress": PMTaskStatus.IN_PROGRESS,
        "block": PMTaskStatus.BLOCKED,
        "blocked": PMTaskStatus.BLOCKED,
        "cancel": PMTaskStatus.CANCELED,
        "cancelled": PMTaskStatus.CANCELED,
        "canceled": PMTaskStatus.CANCELED,
        "todo": PMTaskStatus.TODO,
        "planned": PMTaskStatus.TODO,
    },
    PMTaskStatus.IN_PROGRESS: {
        "done": PMTaskStatus.DONE,
        "complete": PMTaskStatus.DONE,
        "completed": PMTaskStatus.DONE,
        "block": PMTaskStatus.BLOCKED,
        "blocked": PMTaskStatus.BLOCKED,
        "cancel": PMTaskStatus.CANCELED,
        "cancelled": PMTaskStatus.CANCELED,
        "canceled": PMTaskStatus.CANCELED,
    },
    PMTaskStatus.BLOCKED: {
        "start": PMTaskStatus.IN_PROGRESS,
        "resume": PMTaskStatus.IN_PROGRESS,
        "in_progress": PMTaskStatus.IN_PROGRESS,
        "cancel": PMTaskStatus.CANCELED,
        "cancelled": PMTaskStatus.CANCELED,
        "canceled": PMTaskStatus.CANCELED,
    },
    PMTaskStatus.DONE: {},
    PMTaskStatus.CANCELED: {},
}


def _project_linked_ids(project_id: str, workflow_id: Optional[str] = None) -> dict[str, str]:
    linked_ids = {"project": project_id}
    if workflow_id:
        linked_ids["workflow"] = workflow_id
    return linked_ids


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _coordinator_from_request(request: Optional[Request]) -> Any:
    if request is not None:
        coordinator = getattr(request.app.state, "coordinator", None)
        if coordinator is not None:
            return coordinator

    from app.main import app
    return getattr(app.state, "coordinator", None)


def _task_runtime(request: Optional[Request]) -> Any:
    coordinator = _coordinator_from_request(request)
    return getattr(coordinator, "task_coordinator", None)


def _coerce_task_dict(task: Any) -> dict[str, Any]:
    if task is None:
        return {}
    if hasattr(task, "model_dump"):
        return task.model_dump()
    if is_dataclass(task):
        return asdict(task)
    if hasattr(task, "__dict__"):
        return dict(task.__dict__)
    return {}


def _project_matches(project_id: str, task_data: dict[str, Any], pm_task: Any) -> bool:
    scoped_project = (
        task_data.get("project_id")
        or pm_task.linked_ids.get("project")
        or pm_task.refs.get("project_id")
        or pm_task.meta.get("project_id")
    )
    if scoped_project is None:
        return True
    return str(scoped_project) == project_id


def _runtime_entries(project_id: str, request: Optional[Request]) -> list[dict[str, Any]]:
    runtime = _task_runtime(request)
    if runtime is None:
        return []

    entries: list[dict[str, Any]] = []
    task_ids: Iterable[str] = sorted(set(runtime.tasks.keys()))
    for task_id in task_ids:
        task = runtime.tasks.get(task_id)
        pm_task = runtime.pm_store.get(task_id)
        if pm_task is None:
            continue

        task_data = _coerce_task_dict(task)
        if not _project_matches(project_id, task_data, pm_task):
            continue

        dependencies = list(task_data.get("dependencies") or pm_task.meta.get("dependencies") or [])
        entry = {
            "task_id": task_id,
            "title": task_data.get("title") or pm_task.title,
            "description": task_data.get("description") or pm_task.description or "",
            "priority": task_data.get("priority", 0),
            "dependencies": dependencies,
            "canonical_status": pm_task.status,
            "canonical_version": pm_task.version,
            "linked_ids": {**_project_linked_ids(project_id, task_id), **pm_task.linked_ids},
            "assignee": task_data.get("assigned_agent") or task_data.get("assigned_to"),
        }
        entries.append(entry)

    return entries


def _blocked_dependencies(entries_by_id: dict[str, dict[str, Any]], entry: dict[str, Any]) -> list[str]:
    blocked: list[str] = []
    for dependency_id in entry.get("dependencies", []):
        dependency = entries_by_id.get(dependency_id)
        if dependency is None or dependency["canonical_status"] != PMTaskStatus.DONE:
            blocked.append(dependency_id)
    return blocked


def _sort_queue(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        entries,
        key=lambda item: (
            -(int(item.get("priority") or 0)),
            str(item.get("title") or ""),
            item["task_id"],
        ),
    )


def _allowed_transitions_for_status(status: PMTaskStatus) -> list[str]:
    return sorted(_ALLOWED_TRANSITIONS.get(status, {}).keys())


def _build_priority_queue_result(project_id: str, request: Optional[Request] = None) -> PriorityQueueResult:
    runtime = _task_runtime(request)
    if runtime is None:
        return PriorityQueueResult(
            project_id=project_id,
            linked_ids=_project_linked_ids(project_id),
            legality_result="unavailable",
            blockers=[],
            next_action=None,
            queue_items=[],
        )

    entries = _runtime_entries(project_id, request)
    entries_by_id = {entry["task_id"]: entry for entry in entries}
    queue_items = [
        {
            "id": entry["task_id"],
            "title": entry["title"],
            "description": entry["description"],
            "priority": entry["priority"],
            "linked_ids": entry["linked_ids"],
            "version": entry["canonical_version"],
        }
        for entry in _sort_queue(entries)
        if entry["canonical_status"] == PMTaskStatus.TODO and not _blocked_dependencies(entries_by_id, entry)
    ]
    blockers = [entry["task_id"] for entry in entries if _blocked_dependencies(entries_by_id, entry)]
    next_action = queue_items[0] if queue_items else None

    legality_result = "allowed" if queue_items or not blockers else "blocked"
    return PriorityQueueResult(
        project_id=project_id,
        linked_ids=_project_linked_ids(project_id),
        legality_result=legality_result,
        blockers=blockers,
        next_action=next_action,
        queue_items=queue_items,
    )


def _build_blockers_result(project_id: str, request: Optional[Request] = None) -> BlockersResult:
    runtime = _task_runtime(request)
    if runtime is None:
        return BlockersResult(
            project_id=project_id,
            linked_ids=_project_linked_ids(project_id),
            legality_result="unavailable",
            blockers=[],
            next_action=None,
            active_blockers=[],
        )

    entries = _runtime_entries(project_id, request)
    entries_by_id = {entry["task_id"]: entry for entry in entries}
    active_blockers = []
    blocker_ids: list[str] = []
    for entry in entries:
        unresolved = _blocked_dependencies(entries_by_id, entry)
        if entry["canonical_status"] == PMTaskStatus.BLOCKED or unresolved:
            blocker_ids.append(entry["task_id"])
            active_blockers.append(
                {
                    "id": entry["task_id"],
                    "summary": entry["title"],
                    "blocked_by": unresolved,
                    "status": entry["canonical_status"].value,
                    "linked_ids": entry["linked_ids"],
                }
            )

    next_action = None
    if active_blockers:
        next_action = {"type": "resolve_blocker", "workflow_id": active_blockers[0]["id"]}

    legality_result = "blocked" if active_blockers else "allowed"
    return BlockersResult(
        project_id=project_id,
        linked_ids=_project_linked_ids(project_id),
        legality_result=legality_result,
        blockers=blocker_ids,
        next_action=next_action,
        active_blockers=active_blockers,
    )


def _build_workflow_state_result(project_id: str, request: Optional[Request] = None) -> WorkflowStateResult:
    runtime = _task_runtime(request)
    if runtime is None:
        return WorkflowStateResult(
            project_id=project_id,
            linked_ids=_project_linked_ids(project_id),
            legality_result="unavailable",
            blockers=[],
            next_action=None,
            state={},
            allowed_transitions=[],
        )

    queue_result = _build_priority_queue_result(project_id, request)
    blockers_result = _build_blockers_result(project_id, request)
    entries = _runtime_entries(project_id, request)
    status_counts: dict[str, int] = {}
    allowed_transitions = set()
    for entry in entries:
        status_key = entry["canonical_status"].value
        status_counts[status_key] = status_counts.get(status_key, 0) + 1
        allowed_transitions.update(_allowed_transitions_for_status(entry["canonical_status"]))

    state = {
        "task_count": len(entries),
        "status_counts": status_counts,
        "ready_count": len(queue_result.queue_items),
        "blocked_count": len(blockers_result.active_blockers),
    }

    legality_result = "allowed"
    if blockers_result.active_blockers and not queue_result.queue_items:
        legality_result = "blocked"

    return WorkflowStateResult(
        project_id=project_id,
        linked_ids=_project_linked_ids(project_id),
        legality_result=legality_result,
        blockers=blockers_result.blockers,
        next_action=queue_result.next_action,
        state=state,
        allowed_transitions=sorted(allowed_transitions),
    )


def _unavailable_transition_result(project_id: str, request: TransitionWorkflowRequest, reason: str) -> TransitionResult:
    return TransitionResult(
        project_id=project_id,
        workflow_id=request.workflow_id,
        linked_ids=_project_linked_ids(project_id, request.workflow_id),
        legality_result="unavailable",
        blockers=[],
        next_action=None,
        transition_receipt={
            "transition": request.transition,
            "status": "unavailable",
            "reason": reason,
        },
        resulting_state={},
    )


def _illegal_transition_result(
    project_id: str,
    request: TransitionWorkflowRequest,
    *,
    blockers: list[str],
    allowed_transitions: list[str],
    current_status: Optional[str],
    reason: str,
) -> TransitionResult:
    return TransitionResult(
        project_id=project_id,
        workflow_id=request.workflow_id,
        linked_ids=_project_linked_ids(project_id, request.workflow_id),
        legality_result="illegal",
        blockers=blockers,
        next_action={"allowed_transitions": allowed_transitions} if allowed_transitions else None,
        transition_receipt={
            "transition": request.transition,
            "status": "illegal",
            "reason": reason,
        },
        resulting_state={
            "workflow_id": request.workflow_id,
            "current_status": current_status,
            "allowed_transitions": allowed_transitions,
        },
    )


async def execute_transition_project_workflow(
    project_id: str,
    request: TransitionWorkflowRequest,
    http_request: Optional[Request] = None,
) -> TransitionResult:
    runtime = _task_runtime(http_request)
    if runtime is None:
        return _unavailable_transition_result(
            project_id,
            request,
            "project-scoped workflow transition runtime is unavailable",
        )

    pm_task = runtime.pm_store.get(request.workflow_id)
    if pm_task is None:
        raise HTTPException(status_code=404, detail="missing required workflow entity linkage")

    normalized_transition = request.transition.strip().lower()
    allowed_map = _ALLOWED_TRANSITIONS.get(pm_task.status, {})
    target_status = allowed_map.get(normalized_transition)
    blockers_result = _build_blockers_result(project_id, http_request)
    blockers = []
    for blocker in blockers_result.active_blockers:
        if blocker["id"] == request.workflow_id:
            blockers.extend(blocker.get("blocked_by", []))

    if target_status is None:
        return _illegal_transition_result(
            project_id,
            request,
            blockers=blockers,
            allowed_transitions=_allowed_transitions_for_status(pm_task.status),
            current_status=pm_task.status.value,
            reason="transition request references illegal or unresolved target",
        )

    if blockers and target_status == PMTaskStatus.IN_PROGRESS:
        return _illegal_transition_result(
            project_id,
            request,
            blockers=blockers,
            allowed_transitions=_allowed_transitions_for_status(pm_task.status),
            current_status=pm_task.status.value,
            reason="workflow item is blocked by unresolved dependencies",
        )

    expected_version = request.expected_version or pm_task.version
    try:
        updated = runtime.pm_store.transition(
            request.workflow_id,
            PMTransitionRequest(
                idempotency_key=request.idempotency_key or f"workflow-{project_id}-{request.workflow_id}-{normalized_transition}-{expected_version}",
                expected_version=expected_version,
                new_status=target_status,
                ts_utc=_utc_now(),
                source=request.actor or "task-orchestrator",
                reason=request.reason,
            ),
        )
    except StaleWriteError as exc:
        return _illegal_transition_result(
            project_id,
            request,
            blockers=[],
            allowed_transitions=_allowed_transitions_for_status(pm_task.status),
            current_status=pm_task.status.value,
            reason=f"stale version rejected: expected {exc.expected_version}, actual {exc.actual_version}",
        )
    except IdempotencyMismatchError:
        return _illegal_transition_result(
            project_id,
            request,
            blockers=[],
            allowed_transitions=_allowed_transitions_for_status(pm_task.status),
            current_status=pm_task.status.value,
            reason="idempotency key reused with a different transition payload",
        )
    except TaskNotFoundError:
        raise HTTPException(status_code=404, detail="missing required workflow entity linkage")

    task = runtime.tasks.get(request.workflow_id)
    if task is not None:
        task.status = task.status.__class__(CANONICAL_TO_ORCHESTRATOR[updated.status])

    return TransitionResult(
        project_id=project_id,
        workflow_id=request.workflow_id,
        linked_ids={**_project_linked_ids(project_id, request.workflow_id), **updated.linked_ids},
        legality_result="allowed",
        blockers=[],
        next_action=None,
        transition_receipt={
            "transition": request.transition,
            "status": "allowed",
            "canonical_backend": "task-orchestrator",
            "canonical_id": updated.task_id,
            "version_before": expected_version,
            "version_after": updated.version,
            "idempotency_key": request.idempotency_key,
            "actor": request.actor or "task-orchestrator",
        },
        resulting_state={
            "workflow_id": updated.task_id,
            "status": updated.status.value,
            "version": updated.version,
        },
    )


@router.get("/queue", response_model=PriorityQueueResult)
async def get_project_workflow_queue(project_id: str, request: Request):
    if not project_id or project_id == "unknown":
        raise HTTPException(status_code=404, detail="project not found")
    return _build_priority_queue_result(project_id, request)


@router.get("/blockers", response_model=BlockersResult)
async def get_project_workflow_blockers(project_id: str, request: Request):
    if not project_id or project_id == "unknown":
        raise HTTPException(status_code=404, detail="project not found")
    return _build_blockers_result(project_id, request)


@router.get("/state", response_model=WorkflowStateResult)
async def get_project_workflow_state(project_id: str, request: Request):
    if not project_id or project_id == "unknown":
        raise HTTPException(status_code=404, detail="project not found")
    return _build_workflow_state_result(project_id, request)


@router.post("/transition", response_model=TransitionResult)
async def transition_project_workflow(project_id: str, request: TransitionWorkflowRequest, http_request: Request):
    if not project_id or project_id == "unknown":
        raise HTTPException(status_code=404, detail="project not found")
    return await execute_transition_project_workflow(project_id, request, http_request)
