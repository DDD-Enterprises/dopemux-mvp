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
logger = logging.getLogger(__name__)

def _record_metrics_and_log(request: Request, operation: str, receipt: CanonicalReceipt = None, failed: bool = False):
    """Log structured info and update Prometheus metrics on the coordinator."""
    coordinator = getattr(request.app.state, "coordinator", None)
    if not coordinator:
        return
        
    if not hasattr(coordinator, "metrics"):
        coordinator.metrics = {}
        
    m = coordinator.metrics
    
    # Initialize metric keys if missing
    for k in ["pm_canonical_writes_total", "pm_canonical_write_failures_total", "pm_mirror_failures_total", "pm_reconciliation_pending_total", "pm_degraded_results_total"]:
        if k not in m:
            m[k] = 0

    if failed:
        m["pm_canonical_write_failures_total"] += 1
        logger.error(f"PM Write | op={operation} | canonical_success=False")
        return
        
    m["pm_canonical_writes_total"] += 1
    
    logger.info(
        f"PM Write | op={operation} | canonical_id={receipt.canonical_id} | "
        f"canonical_system={receipt.canonical_system} | "
        f"canonical_success={receipt.success} | "
        f"reconciliation_state={receipt.reconciliation_state}"
    )

    mirror_failed = False
    for mr in receipt.mirror_receipts:
        if mr.success:
            logger.info(f"Mirror Success | system={mr.system}")
        else:
            mirror_failed = True
            logger.warning(
                f"Mirror Failure (Reconciliation Pending) | "
                f"system={mr.system} | error={mr.error}"
            )
            
    if mirror_failed:
        m["pm_mirror_failures_total"] += 1
        m["pm_reconciliation_pending_total"] += 1
        m["pm_degraded_results_total"] += 1


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
    request: Request,
    task_id: str, 
    updates: Dict[str, Any], 
    idempotency_key: str,
    config: PMWriteConfig = Depends(get_pm_config)
):
    try:
        receipt = pm_update_work_item(
            config=config,
            task_id=task_id,
            updates=updates,
            idempotency_key=idempotency_key
        )
        _record_metrics_and_log(request, "pm_update_work_item", receipt=receipt)
        return receipt
    except ValueError as e:
        _record_metrics_and_log(request, "pm_update_work_item", failed=True)
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        _record_metrics_and_log(request, "pm_update_work_item", failed=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/work-items/{task_id}/transition", response_model=CanonicalReceipt)
async def transition_work_item(
    request: Request,
    task_id: str, 
    new_status: PMTaskStatus, 
    reason: str, 
    idempotency_key: str,
    expected_version: int,
    config: PMWriteConfig = Depends(get_pm_config)
):
    try:
        receipt = pm_transition_work_item(
            config=config,
            task_id=task_id,
            new_status=new_status,
            reason=reason,
            idempotency_key=idempotency_key,
            expected_version=expected_version
        )
        _record_metrics_and_log(request, "pm_transition_work_item", receipt=receipt)
        return receipt
    except RuntimeError as e:
        _record_metrics_and_log(request, "pm_transition_work_item", failed=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/work-items/{task_id}/progress", response_model=CanonicalReceipt)
async def log_progress(
    request: Request,
    task_id: str, 
    progress_notes: str, 
    idempotency_key: str,
    is_decision: bool = False,
    config: PMWriteConfig = Depends(get_pm_config)
):
    try:
        receipt = pm_log_progress(
            config=config,
            task_id=task_id,
            progress_notes=progress_notes,
            idempotency_key=idempotency_key,
            is_decision=is_decision
        )
        _record_metrics_and_log(request, "pm_log_progress", receipt=receipt)
        return receipt
    except RuntimeError as e:
        _record_metrics_and_log(request, "pm_log_progress", failed=True)
        raise HTTPException(status_code=500, detail=str(e))
