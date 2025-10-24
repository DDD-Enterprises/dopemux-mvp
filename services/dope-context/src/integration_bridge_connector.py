"""
Integration Bridge Connector for Dope-Context

Connects Dope-Context to ConPort-KG event system for search pattern tracking.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional, Any, List, Dict

logger = logging.getLogger(__name__)

_integration_manager: Optional[Any] = None
_integration_enabled = True


def initialize_integration(workspace_id: str, event_bus_url: str = "redis://localhost:6379"):
    """Initialize Dope-Context integration with ConPort-KG"""
    global _integration_manager, _integration_enabled

    try:
        bridge_path = str(Path(__file__).parent.parent.parent.parent / "mcp-integration-bridge")
        if bridge_path not in sys.path:
            sys.path.insert(0, bridge_path)

        from event_bus import EventBus
        from integrations.dope_context import DopeContextIntegrationManager

        event_bus = EventBus(redis_url=event_bus_url)
        _integration_manager = DopeContextIntegrationManager(
            event_bus=event_bus,
            workspace_id=workspace_id
        )

        asyncio.create_task(_initialize_async(event_bus))

        logger.info(f"✅ Dope-Context integration enabled for {workspace_id}")

    except Exception as e:
        logger.warning(f"⚠️  Dope-Context integration disabled: {e}")
        _integration_enabled = False


async def _initialize_async(event_bus):
    """Initialize EventBus connection"""
    try:
        await event_bus.initialize()
    except Exception as e:
        logger.error(f"EventBus initialization failed: {e}")


async def emit_search_completed(query: str, results: List[Dict[str, Any]]):
    """
    Emit search completion event.

    Args:
        query: Search query text
        results: Search results with relevance scores
    """
    if not _integration_enabled or _integration_manager is None:
        return

    try:
        await _integration_manager.handle_search_result(query=query, results=results)
    except Exception as e:
        logger.debug(f"Event emission failed (non-blocking): {e}")


def get_integration_metrics() -> dict:
    """Get integration metrics"""
    if _integration_manager:
        return _integration_manager.get_metrics()
    return {"integration_enabled": False}
