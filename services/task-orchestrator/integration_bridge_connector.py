"""
Integration Bridge Connector for Task-Orchestrator

Connects Task-Orchestrator to ConPort-KG event system for task progress tracking.
Enhances existing event subscription with publishing capabilities.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional, Any

logger = logging.getLogger(__name__)

_integration_manager: Optional[Any] = None
_integration_enabled = True


def initialize_integration(workspace_id: str, event_bus_url: str = "redis://localhost:6379"):
    """Initialize Task-Orchestrator integration with ConPort-KG"""
    global _integration_manager, _integration_enabled

    try:
        bridge_path = str(Path(__file__).parent.parent / "mcp-integration-bridge")
        if bridge_path not in sys.path:
            sys.path.insert(0, bridge_path)

        from event_bus import EventBus
        from integrations.task_orchestrator import TaskOrchestratorIntegrationManager

        event_bus = EventBus(redis_url=event_bus_url)
        _integration_manager = TaskOrchestratorIntegrationManager(
            event_bus=event_bus,
            workspace_id=workspace_id
        )

        asyncio.create_task(_initialize_async(event_bus))

        logger.info(f"✅ Task-Orchestrator integration enabled (bidirectional)")

    except Exception as e:
        logger.warning(f"⚠️  Task-Orchestrator integration disabled: {e}")
        _integration_enabled = False


async def _initialize_async(event_bus):
    """Initialize EventBus connection"""
    try:
        await event_bus.initialize()
    except Exception as e:
        logger.error(f"EventBus initialization failed: {e}")


async def emit_task_status_change(
    task_id: str,
    task_title: str,
    old_status: str,
    new_status: str,
    progress_percentage: float = 0.0,
    complexity: Optional[float] = None
):
    """
    Emit task status change event.

    Args:
        task_id: Task identifier
        task_title: Task title/description
        old_status: Previous status
        new_status: New status (TODO/IN_PROGRESS/DONE/BLOCKED)
        progress_percentage: Completion percentage
        complexity: Optional task complexity
    """
    if not _integration_enabled or _integration_manager is None:
        return

    try:
        await _integration_manager.handle_task_status_change(
            task_id=task_id,
            task_title=task_title,
            old_status=old_status,
            new_status=new_status,
            progress_percentage=progress_percentage,
            complexity=complexity
        )
    except Exception as e:
        logger.debug(f"Event emission failed (non-blocking): {e}")


def get_integration_metrics() -> dict:
    """Get integration metrics"""
    if _integration_manager:
        return _integration_manager.get_metrics()
    return {"integration_enabled": False}
