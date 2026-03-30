"""PM Plane write tools — canonical mutation with authority enforcement."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from dopemux.pm.adapters.conport import ConPortAdapter
from dopemux.pm.adapters.orchestrator import TaskOrchestratorAdapter
from dopemux.pm.chronicle import pm_append_work_chronicle
from dopemux.pm.models import (
    PMTask,
    PMTransitionRequest,
    WORKFLOW_SIGNIFICANT_FIELDS,
)
from dopemux.pm.store import PMTaskStore

logger = logging.getLogger(__name__)

# Single instances of the adapters
_orchestrator = TaskOrchestratorAdapter()
_conport = ConPortAdapter()


async def pm_log_progress(
    *,
    workspace_id: str,
    task_id: str,
    status: str,
    summary: str,
    percentage: int = 0,
    linked_ids: Optional[Dict[str, str]] = None,
    tags: Optional[List[str]] = None,
    idempotency_key: str,
) -> Dict[str, Any]:
    """Log progress to both ConPort (Decision Graph) and Dope-Memory (Chronicle)."""
    
    # 1. Write to ConPort
    progress_payload = {
        "status": status,
        "description": summary,
        "percentage": percentage,
        "source": "pm-plane",
    }
    
    # Ensure this is awaited
    conport_result = await _conport.save_custom_data(
        workspace_id=workspace_id,
        category="progress",
        key=task_id,
        value=progress_payload,
    )
    
    # 2. Write to Dope-Memory Chronicle
    chronicle_result = await pm_append_work_chronicle(
        workspace_id=workspace_id,
        canonical_id=task_id,
        linked_ids=linked_ids or {},
        entry_type="task_progress",
        summary=summary,
        details=progress_payload,
        tags=tags,
        idempotency_key=idempotency_key,
    )
    
    return {
        "success": conport_result.get("success", False) and chronicle_result.success,
        "task_id": task_id,
        "conport_receipt": conport_result,
        "chronicle_receipt": chronicle_result,
    }


async def pm_transition_work_item(
    *,
    store: PMTaskStore,
    task_id: str,
    project_id: str,
    workflow_id: str,
    new_status: str,
    expected_version: int,
    idempotency_key: str,
    reason: Optional[str] = None,
) -> PMTask:
    """Execute a workflow transition in both the store and the Orchestrator."""
    
    # 1. Perform local store transition (verifies version and idempotency)
    req = PMTransitionRequest(
        idempotency_key=idempotency_key,
        expected_version=expected_version,
        new_status=new_status,
        ts_utc=datetime.now(timezone.utc),
        source="pm-plane",
        reason=reason,
    )
    
    task = store.transition(task_id, req)
    
    # 2. Update Task Orchestrator (Mirror the transition)
    try:
        await _orchestrator.transition(
            project_id=project_id,
            workflow_id=workflow_id,
            transition_name=new_status.lower(),
        )
    except Exception as e:
        logger.error(f"Failed to mirror transition to Task Orchestrator: {e}")
        
    return task


async def pm_update_work_item(
    *,
    store: PMTaskStore,
    task_id: str,
    patch: Dict[str, Any],
    expected_version: Optional[int] = None,
    idempotency_key: Optional[str] = None,
) -> PMTask:
    """Update a work item, enforcing authority boundaries."""
    
    # Check if this is a workflow update
    has_workflow_fields = any(k in WORKFLOW_SIGNIFICANT_FIELDS for k in patch)
    
    if has_workflow_fields:
        if expected_version is None or idempotency_key is None:
            raise ValueError("Workflow-significant updates require expected_version and idempotency_key")
            
        if "status" in patch:
            req = PMTransitionRequest(
                idempotency_key=idempotency_key,
                expected_version=expected_version,
                new_status=patch["status"],
                ts_utc=datetime.now(timezone.utc),
                source="pm-plane",
            )
            task = store.transition(task_id, req)
            
            # Apply remaining metadata from the same patch
            metadata_patch = {k: v for k, v in patch.items() if k not in WORKFLOW_SIGNIFICANT_FIELDS}
            if metadata_patch:
                task = store.patch_metadata(task_id, metadata_patch)
                
            return task
    
    # 2. Pure metadata patch
    return store.patch_metadata(task_id, patch)
