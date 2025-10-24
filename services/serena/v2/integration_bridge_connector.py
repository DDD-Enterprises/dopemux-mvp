"""
Integration Bridge Connector for Serena

Connects Serena to ConPort-KG event system for automatic event emission.
Lazy-loads to avoid circular dependencies and allows graceful degradation.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional, Any

logger = logging.getLogger(__name__)

# Lazy-loaded integration manager
_integration_manager: Optional[Any] = None
_integration_enabled = True


def initialize_integration(workspace_id: str, event_bus_url: str = "redis://localhost:6379"):
    """
    Initialize Serena integration with ConPort-KG event system.

    Args:
        workspace_id: Workspace identifier
        event_bus_url: EventBus Redis URL

    Call this once on Serena startup to enable event emission.
    """
    global _integration_manager, _integration_enabled

    try:
        # Add mcp-integration-bridge to path
        bridge_path = str(Path(__file__).parent.parent.parent / "mcp-integration-bridge")
        if bridge_path not in sys.path:
            sys.path.insert(0, bridge_path)

        # Import integration components
        from event_bus import EventBus
        from integrations.serena import SerenaIntegrationManager

        # Initialize EventBus
        event_bus = EventBus(redis_url=event_bus_url)

        # Create integration manager
        _integration_manager = SerenaIntegrationManager(
            event_bus=event_bus,
            workspace_id=workspace_id
        )

        # Initialize EventBus connection (async, but we'll handle it)
        asyncio.create_task(_initialize_async(event_bus))

        logger.info(f"✅ Serena integration with ConPort-KG enabled for {workspace_id}")

    except Exception as e:
        logger.warning(f"⚠️  Serena integration disabled: {e}")
        _integration_enabled = False


async def _initialize_async(event_bus):
    """Initialize EventBus connection asynchronously"""
    try:
        await event_bus.initialize()
    except Exception as e:
        logger.error(f"EventBus initialization failed: {e}")


async def emit_complexity_analyzed(
    file_path: str,
    complexity_score: float,
    metrics: Optional[dict] = None
):
    """
    Emit complexity analysis event.

    Args:
        file_path: Path to analyzed file
        complexity_score: Calculated complexity (0.0-1.0)
        metrics: Optional detailed metrics

    Call this after complexity analysis completes.
    """
    if not _integration_enabled or _integration_manager is None:
        return  # Gracefully skip if integration not available

    try:
        await _integration_manager.handle_complexity_result(
            file_path=file_path,
            complexity_score=complexity_score,
            metrics=metrics
        )

    except Exception as e:
        logger.debug(f"Event emission failed (non-blocking): {e}")


def is_integration_enabled() -> bool:
    """Check if integration is enabled"""
    return _integration_enabled and _integration_manager is not None


def get_integration_metrics() -> dict:
    """Get integration metrics"""
    if _integration_manager:
        return _integration_manager.get_metrics()
    return {"integration_enabled": False}
