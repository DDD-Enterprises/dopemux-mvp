"""PM Plane read tools — canonical access to Orchestrator and ConPort."""

import logging
from typing import Any, Dict, List, Optional
from dopemux.pm.adapters.orchestrator import TaskOrchestratorAdapter
from dopemux.pm.adapters.conport import ConPortAdapter
from dopemux.pm.adapters.dope_memory import DopeMemoryAdapter
import httpx

logger = logging.getLogger(__name__)

# Single instances of the adapters to use
_orchestrator = TaskOrchestratorAdapter()
_conport = ConPortAdapter()
_memory = DopeMemoryAdapter()

async def pm_get_priority_queue(
    *,
    project_id: str,
) -> Dict[str, Any]:
    """Read prioritized next actions from Task Orchestrator authority.
    
    Returns fail-closed empty result if backend is down.
    """
    try:
        return await _orchestrator.get_queue(project_id)
    except httpx.HTTPError:
        logger.warning("task-orchestrator backend unavailable. Returning fail-closed empty result.")
        return {
            "project_id": project_id,
            "queue_items": [],
            "blockers": [],
            "legality_result": "unavailable"
        }
    except Exception as e:
        logger.error(f"Unexpected error calling task-orchestrator: {e}")
        return {
            "project_id": project_id,
            "queue_items": [],
            "error": str(e)
        }

async def pm_get_blockers(
    *,
    project_id: str,
) -> Dict[str, Any]:
    """Read active blockers from Task Orchestrator authority."""
    try:
        return await _orchestrator.get_blockers(project_id)
    except httpx.HTTPError:
        logger.warning("task-orchestrator backend unavailable. Returning fail-closed empty result.")
        return {
            "project_id": project_id,
            "active_blockers": [],
            "legality_result": "unavailable"
        }
    except Exception as e:
        logger.error(f"Unexpected error calling task-orchestrator: {e}")
        return {
            "project_id": project_id,
            "active_blockers": [],
            "error": str(e)
        }

async def pm_get_workflow_state(
    *,
    project_id: str,
) -> Dict[str, Any]:
    """Read full workflow state snapshot from Task Orchestrator authority."""
    try:
        return await _orchestrator.get_state(project_id)
    except httpx.HTTPError:
        logger.warning("task-orchestrator backend unavailable. Returning fail-closed empty result.")
        return {
            "project_id": project_id,
            "state": {},
            "legality_result": "unavailable"
        }
    except Exception as e:
        logger.error(f"Unexpected error calling task-orchestrator: {e}")
        return {
            "project_id": project_id,
            "state": {},
            "error": str(e)
        }

async def pm_get_decision_context(
    *,
    tag: Optional[str] = None,
    text: Optional[str] = None,
    limit: int = 3,
) -> Dict[str, Any]:
    """Read decision context from ConPort knowledge graph.
    
    Supports tag or text search.
    """
    try:
        return await _conport.search_decisions(tag=tag, text=text, limit=limit)
    except httpx.HTTPError:
        logger.warning("conport backend unavailable. Returning fail-closed empty result.")
        return {
            "decisions": [],
            "count": 0,
            "legality_result": "unavailable"
        }
    except Exception as e:
        logger.error(f"Unexpected error calling conport: {e}")
        return {
            "decisions": [],
            "error": str(e)
        }

async def pm_check_readiness() -> Dict[str, Any]:
    """Check readiness of all PM Plane authoritative backends."""
    orchestrator_ok = await _orchestrator.health()
    conport_ok = await _conport.health()
    memory_ok = await _memory.health()
    
    status = "healthy" if all([orchestrator_ok, conport_ok, memory_ok]) else "degraded"
    if not any([orchestrator_ok, conport_ok, memory_ok]):
        status = "unavailable"
        
    return {
        "status": status,
        "backends": {
            "task-orchestrator": "online" if orchestrator_ok else "offline",
            "conport-kg": "online" if conport_ok else "offline",
            "dope-memory": "online" if memory_ok else "offline"
        }
    }
