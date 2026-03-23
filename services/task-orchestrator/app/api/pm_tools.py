from fastapi import APIRouter, Depends, HTTPException, Request, Body
from typing import Dict, Any, Optional
from pydantic import BaseModel
from src.dopemux.pm.writes import (
    pm_update_work_item,
    pm_transition_work_item,
    pm_log_progress,
    PMWriteConfig,
    CanonicalReceipt
)
from src.dopemux.pm.models import PMTaskStatus

router = APIRouter(prefix="/api/pm", tags=["pm-plane"])


def get_pm_config(request: Request) -> PMWriteConfig:
    """
    Extract canonical clients from the Task Orchestrator application state
    to populate the `PMWriteConfig` dependency for normalized PM-plane writes.

    If a client has not been initialized (e.g., during testing or partial boot),
    it evaluates to `None`, which the underlying `writes.py` logic uses to trigger
    a fail-closed condition enforcing architectural authority bounds.

    Args:
        request (Request): The incoming FastAPI request.

    Returns:
        PMWriteConfig: A configuration container mapping the underlying subsystem
                       clients to the normalized interface.
    """
    coordinator = getattr(request.app.state, "coordinator", None)

    leantime = getattr(coordinator, "leantime_client", None)
    orchestrator = getattr(coordinator, "workflow_service", None)
    conport = getattr(coordinator, "conport_client", None)
    memory = getattr(coordinator, "memory_client", None)

    return PMWriteConfig(
        leantime_client=leantime,
        orchestrator_client=orchestrator,
        conport_client=conport,
        memory_client=memory
    )


class UpdateWorkItemRequest(BaseModel):
    updates: Dict[str, Any]
    idempotency_key: str

class TransitionWorkItemRequest(BaseModel):
    new_status: PMTaskStatus
    reason: str
    idempotency_key: str
    expected_version: int

class LogProgressRequest(BaseModel):
    progress_notes: str
    idempotency_key: str
    is_decision: bool = False


@router.post("/work-items/{task_id}/update", response_model=CanonicalReceipt)
async def update_work_item(
    task_id: str,
    payload: UpdateWorkItemRequest,
    config: PMWriteConfig = Depends(get_pm_config)
):
    """
    API endpoint to update a PM work item's passive metadata.

    Routes canonical changes to Leantime. Explicitly rejects updates to
    workflow-significant fields (e.g., status, version).

    Args:
        task_id (str): Target task ID.
        payload (UpdateWorkItemRequest): JSON body containing updates and idempotency key.
        config (PMWriteConfig): Injected client configuration dependencies.

    Returns:
        CanonicalReceipt: Result object containing success and downstream mirror state.

    Raises:
        HTTPException 400: If workflow-significant fields are submitted or the request is invalid.
        HTTPException 500: If the canonical write fails due to connection or logic errors.
    """
    try:
        return pm_update_work_item(
            config=config,
            task_id=task_id,
            updates=payload.updates,
            idempotency_key=payload.idempotency_key
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/work-items/{task_id}/transition", response_model=CanonicalReceipt)
async def transition_work_item(
    task_id: str,
    payload: TransitionWorkItemRequest,
    config: PMWriteConfig = Depends(get_pm_config)
):
    """
    API endpoint to transition the workflow state of a work item.

    Routes canonical workflow validation and state changes to the Task Orchestrator.
    After successful workflow enforcement, the operation mirrors back to Leantime.

    Args:
        task_id (str): Target task ID.
        payload (TransitionWorkItemRequest): JSON body with new_status, reason, idempotency_key, expected_version.
        config (PMWriteConfig): Injected client configuration dependencies.

    Returns:
        CanonicalReceipt: Result object tracking canonical and mirror statuses.

    Raises:
        HTTPException 400: If the payload validation fails (e.g., empty idempotency key).
        HTTPException 500: If the orchestrator canonical write fails.
    """
    try:
        return pm_transition_work_item(
            config=config,
            task_id=task_id,
            new_status=payload.new_status,
            reason=payload.reason,
            idempotency_key=payload.idempotency_key,
            expected_version=payload.expected_version
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/work-items/{task_id}/progress", response_model=CanonicalReceipt)
async def log_progress(
    task_id: str,
    payload: LogProgressRequest,
    config: PMWriteConfig = Depends(get_pm_config)
):
    """
    API endpoint to log progress or append decision context to a task.

    Routes canonical decisions to ConPort (Decision Authority) and mirrors
    the temporal event to dope-memory (Chronicle Authority).

    Args:
        task_id (str): Target task ID.
        payload (LogProgressRequest): JSON body with progress notes and flag for decisions.
        config (PMWriteConfig): Injected client configuration dependencies.

    Returns:
        CanonicalReceipt: Result object containing canonical and mirror success states.

    Raises:
        HTTPException 400: If the progress notes or idempotency key are empty.
        HTTPException 500: If the canonical ConPort storage fails.
    """
    try:
        return pm_log_progress(
            config=config,
            task_id=task_id,
            progress_notes=payload.progress_notes,
            idempotency_key=payload.idempotency_key,
            is_decision=payload.is_decision
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
