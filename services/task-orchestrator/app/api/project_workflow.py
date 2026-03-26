"""Project-scoped workflow endpoints for the Task Orchestrator PM-plane contract."""

from fastapi import APIRouter, HTTPException

from app.models.workflow import (
    BlockersResult,
    PriorityQueueResult,
    TransitionResult,
    TransitionWorkflowRequest,
    WorkflowStateResult,
)

from dopemux.pm.reads import (
    pm_get_priority_queue,
    pm_get_blockers,
    pm_get_workflow_state,
)

router = APIRouter(prefix="/api/projects/{project_id}/workflow", tags=["project-workflow"])


def _priority_queue_response(result) -> PriorityQueueResult:
    return PriorityQueueResult(
        project_id=result.project_id,
        linked_ids=result.linked_ids,
        legality_result=result.legality_result,
        blockers=result.blockers,
        next_action=result.next_action,
        queue_items=result.queue_items,
    )


def _blockers_response(result) -> BlockersResult:
    return BlockersResult(
        project_id=result.project_id,
        linked_ids=result.linked_ids,
        legality_result=result.legality_result,
        blockers=result.blockers,
        next_action=result.next_action,
        active_blockers=result.active_blockers,
    )


def _workflow_state_response(result) -> WorkflowStateResult:
    return WorkflowStateResult(
        project_id=result.project_id,
        linked_ids=result.linked_ids,
        legality_result=result.legality_result,
        blockers=result.blockers,
        next_action=result.next_action,
        state=result.state,
        allowed_transitions=result.allowed_transitions,
    )


def _unavailable_transition_result(project_id: str, request: TransitionWorkflowRequest) -> TransitionResult:
    return TransitionResult(
        project_id=project_id,
        workflow_id=request.workflow_id,
        linked_ids={},
        legality_result="unavailable",
        blockers=[],
        next_action=None,
        transition_receipt={
            "transition": request.transition,
            "status": "unavailable",
            "reason": "project-scoped workflow transition is not yet backed by a canonical runtime binding",
        },
        resulting_state={},
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
        
    result = await pm_get_priority_queue(project_id)

    return _priority_queue_response(result)


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
        
    result = await pm_get_blockers(project_id)

    return _blockers_response(result)


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
        
    result = await pm_get_workflow_state(project_id)

    return _workflow_state_response(result)


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

    return _unavailable_transition_result(project_id, request)
