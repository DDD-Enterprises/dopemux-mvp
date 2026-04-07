import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, Any
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
    # Attempt to load concrete clients from the coordinator state,
    # mapping them into the standardized PM write config struct.
    # Note: Depending on actual client mappings, these might be None
    # if the system is partially initialized, which correctly triggers fail-closed in writes.py.
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

@router.post("/work-items/{task_id}/update", response_model=CanonicalReceipt)
async def update_work_item(
    task_id: str, 
    updates: Dict[str, Any], 
    idempotency_key: str,
    config: PMWriteConfig = Depends(get_pm_config)
):
    try:
        return pm_update_work_item(
            config=config,
            task_id=task_id,
            updates=updates,
            idempotency_key=idempotency_key
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/work-items/{task_id}/transition", response_model=CanonicalReceipt)
async def transition_work_item(
    task_id: str, 
    new_status: PMTaskStatus, 
    reason: str, 
    idempotency_key: str,
    expected_version: int,
    config: PMWriteConfig = Depends(get_pm_config)
):
    try:
        return pm_transition_work_item(
            config=config,
            task_id=task_id,
            new_status=new_status,
            reason=reason,
            idempotency_key=idempotency_key,
            expected_version=expected_version
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/work-items/{task_id}/progress", response_model=CanonicalReceipt)
async def log_progress(
    task_id: str, 
    progress_notes: str, 
    idempotency_key: str,
    is_decision: bool = False,
    config: PMWriteConfig = Depends(get_pm_config)
):
    try:
        return pm_log_progress(
            config=config,
            task_id=task_id,
            progress_notes=progress_notes,
            idempotency_key=idempotency_key,
            is_decision=is_decision
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
