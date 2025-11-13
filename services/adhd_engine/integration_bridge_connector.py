"""
DopeconBridge Connector for ADHD Engine

Connects ADHD Engine to ConPort-KG event system for cognitive state tracking.
Handles buffered state changes (30s intervals) to prevent event storms.
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
    """Initialize ADHD Engine integration with ConPort-KG"""
    global _integration_manager, _integration_enabled

    try:
        bridge_path = str(Path(__file__).parent.parent.parent / "mcp-dopecon-bridge")
        if bridge_path not in sys.path:
            sys.path.insert(0, bridge_path)

        from event_bus import EventBus
        from integrations.adhd_engine import ADHDEngineIntegrationManager

        event_bus = EventBus(redis_url=event_bus_url)
        _integration_manager = ADHDEngineIntegrationManager(
            event_bus=event_bus,
            workspace_id=workspace_id,
            buffer_interval_seconds=30  # Prevent event storms
        )

        # Initialize EventBus and start background worker
        asyncio.create_task(_initialize_async(event_bus, _integration_manager))

        logger.info(f"✅ ADHD Engine integration enabled (buffered 30s)")

    except Exception as e:
        logger.warning(f"⚠️  ADHD Engine integration disabled: {e}")
        _integration_enabled = False


async def _initialize_async(event_bus, manager):
    """Initialize EventBus and start background worker"""
    try:
        await event_bus.initialize()
        await manager.start_background_worker()
    except Exception as e:
        logger.error(f"ADHD Engine integration initialization failed: {e}")


async def emit_state_update(attention_state: str, energy_level: str, cognitive_load: float):
    """
    Emit cognitive state update (buffered, emitted every 30s).

    Args:
        attention_state: focused/scattered/transitioning
        energy_level: high/medium/low
        cognitive_load: 0.0-1.0
    """
    if not _integration_enabled or _integration_manager is None:
        return

    try:
        await _integration_manager.handle_state_update(
            attention_state=attention_state,
            energy_level=energy_level,
            cognitive_load=cognitive_load
        )
    except Exception as e:
        logger.debug(f"Event emission failed (non-blocking): {e}")


async def emit_break_needed(session_duration_minutes: int, last_break_minutes_ago: int):
    """Emit break recommendation"""
    if not _integration_enabled or _integration_manager is None:
        return

    try:
        await _integration_manager.handle_break_needed(
            session_duration_minutes=session_duration_minutes,
            last_break_minutes_ago=last_break_minutes_ago
        )
    except Exception as e:
        logger.debug(f"Event emission failed (non-blocking): {e}")


def get_integration_metrics() -> dict:
    """Get integration metrics"""
    if _integration_manager:
        return _integration_manager.get_metrics()
    return {"integration_enabled": False}
