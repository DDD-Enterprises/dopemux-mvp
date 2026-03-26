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
    """Read prioritized next actions from the Task Orchestrator canonical authority.
    
    This function abstracts the REST call to the Task Orchestrator backend,
    serving as the sole normalized entry point for retrieving the project queue
    in the PM Plane.

    Returns fail-closed empty result if backend is down.

    Args:
        project_id: The identifier of the project to retrieve the queue for.

    Returns:
        A dictionary containing the `queue_items` and `blockers`. If the backend
        is unavailable or an error occurs, it returns an empty `queue_items` list
        and logs the failure.
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
    """Read active workflow blockers from the Task Orchestrator canonical authority.

    This ensures consumers retrieve real-time blocking constraints evaluated
    by the execution plane.

    Args:
        project_id: The identifier of the project to retrieve blockers for.

    Returns:
        A dictionary containing `active_blockers`. If the backend is unavailable,
        returns an empty list.
    """
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
    """Read the full workflow state snapshot from the Task Orchestrator canonical authority.

    Retrieves the complete state machine data for the specified project, including
    transition history and current nodal states.

    Args:
        project_id: The identifier of the project.

    Returns:
        A dictionary containing the `state` object.
    """
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
    """Read historical decision context from the ConPort knowledge graph.
    
    Provides context resolution by fetching previously recorded Architectural
    Decision Records (ADRs) or progress logs. Supports filtering by semantic
    tags or free-text search.

    Args:
        tag: Optional semantic tag to filter decisions.
        text: Optional string to perform a full-text search against summaries.
        limit: Maximum number of decisions to return (default 3).

    Returns:
        A dictionary containing the `decisions` list and total `count`.
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

async def pm_get_project_context(
    project_id: str,
) -> Dict[str, Any]:
    """Read project context from the canonical authority.

    Args:
        project_id: The identifier of the project.

    Returns:
        A dictionary containing the project context.
    """
    try:
        return await _orchestrator.get_project_context(project_id)
    except Exception as e:
        logger.error(f"Error calling pm_get_project_context: {e}")
        return {"project_id": project_id, "error": str(e)}

async def pm_get_sprint_snapshot(
    project_id: str,
) -> Dict[str, Any]:
    """Read sprint snapshot from the canonical authority.

    Args:
        project_id: The identifier of the project.

    Returns:
        A dictionary containing the sprint snapshot.
    """
    try:
        return await _orchestrator.get_sprint_snapshot(project_id)
    except Exception as e:
        logger.error(f"Error calling pm_get_sprint_snapshot: {e}")
        return {"project_id": project_id, "error": str(e)}

async def pm_check_readiness() -> Dict[str, Any]:
    """Check readiness of all PM Plane authoritative backends.

    Evaluates the operational status of the three pillars of the PM plane:
    1. Task Orchestrator (Workflow/Queue authority)
    2. ConPort-KG (Knowledge Graph / Decision authority)
    3. Dope-Memory (Chronicle / Ledger authority)

    Returns:
        A diagnostic dictionary outlining the global `status` ("healthy", 
        "degraded", or "unavailable") and individual backend states.
    """
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
