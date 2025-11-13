"""
DopeconBridge Connector for Desktop Commander

Connects Desktop Commander to ConPort-KG event system for workspace switch tracking.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional, Any, Dict

logger = logging.getLogger(__name__)

_integration_manager: Optional[Any] = None
_integration_enabled = True


def initialize_integration(workspace_id: str, event_bus_url: str = "redis://localhost:6379"):
    """Initialize Desktop Commander integration with ConPort-KG"""
    global _integration_manager, _integration_enabled

    try:
        bridge_path = str(Path(__file__).parent.parent.parent.parent / "services" / "mcp-dopecon-bridge")
        if bridge_path not in sys.path:
            sys.path.insert(0, bridge_path)

        from event_bus import EventBus
        from integrations.desktop_commander import DesktopCommanderIntegrationManager

        event_bus = EventBus(redis_url=event_bus_url)
        _integration_manager = DesktopCommanderIntegrationManager(
            event_bus=event_bus,
            workspace_id=workspace_id
        )

        asyncio.create_task(_initialize_async(event_bus))

        logger.info(f"✅ Desktop Commander integration enabled")

    except Exception as e:
        logger.warning(f"⚠️  Desktop Commander integration disabled: {e}")
        _integration_enabled = False


async def _initialize_async(event_bus):
    """Initialize EventBus connection"""
    try:
        await event_bus.initialize()
    except Exception as e:
        logger.error(f"EventBus initialization failed: {e}")


async def emit_workspace_switched(
    from_workspace: str,
    to_workspace: str,
    switch_type: str = "manual",
    context_data: Optional[Dict[str, Any]] = None
):
    """
    Emit workspace switch event.

    Args:
        from_workspace: Previous workspace
        to_workspace: New workspace
        switch_type: manual/automatic/forced
        context_data: Optional context to preserve
    """
    if not _integration_enabled or _integration_manager is None:
        return

    try:
        await _integration_manager.handle_workspace_switch(
            from_workspace=from_workspace,
            to_workspace=to_workspace,
            switch_type=switch_type,
            context_data=context_data
        )
    except Exception as e:
        logger.debug(f"Event emission failed (non-blocking): {e}")


def get_integration_metrics() -> dict:
    """Get integration metrics"""
    if _integration_manager:
        return _integration_manager.get_metrics()
    return {"integration_enabled": False}
