"""PM Plane write tools — canonical mutation with authority enforcement."""

import logging
from typing import Any, Dict, List, Optional

from dopemux.pm.adapters.conport import ConPortAdapter
from dopemux.pm.adapters.orchestrator import TaskOrchestratorAdapter
from dopemux.pm.chronicle import pm_append_work_chronicle
from dopemux.pm.models import (
    PMTask,
)
from dopemux.pm.store import PMTaskStore

logger = logging.getLogger(__name__)


async def pm_transition_command(*, adapter, command: Dict[str, Any]) -> Dict[str, Any]:
    """The explicit authenticated v2 path never mutates a local mirror first."""
    from .adapters.ownership import AsyncOwnershipAdapter
    if not isinstance(adapter, AsyncOwnershipAdapter):
        raise RuntimeError("Explicit authenticated v2 adapter required")
    return await adapter.transition_command(command)

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
    """Legacy local-first lifecycle writes are held; use an explicit v2 command."""
    raise RuntimeError("Canonical ownership requires authenticated v2 transition_command")


async def pm_update_work_item(
    *,
    store: PMTaskStore,
    task_id: str,
    patch: Dict[str, Any],
    expected_version: Optional[int] = None,
    idempotency_key: Optional[str] = None,
) -> PMTask:
    """Legacy PM store mutation cannot bypass protected ownership."""
    raise RuntimeError("Canonical metadata and graph edits are unavailable in ownership v2")
