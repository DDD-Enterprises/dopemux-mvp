"""
Event Emitter - Publishes Workspace Switch Events to Redis Streams

Publishes workspace.switched events when active application changes.
Integrates with Activity Capture service for ADHD session tracking.

ADHD Benefit: Automatic workspace switch detection enables:
- Session duration tracking
- Interruption counting
- Break recommendations
- Context switch recovery
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

# Add DopeconBridge to path for EventBus
bridge_path = Path(__file__).parent.parent.parent / "services" / "mcp-dopecon-bridge"
if str(bridge_path) not in sys.path:
    sys.path.insert(0, str(bridge_path))

from event_bus import Event, EventBus

logger = logging.getLogger(__name__)


class WorkspaceSwitchEmitter:
    """
    Emits workspace.switched events to Redis Streams.

    Integrates with ConPort-KG event system for ADHD tracking.
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """
        Initialize event emitter.

        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self.event_bus: Optional[EventBus] = None
        self.events_emitted = 0
        self.errors = 0

    async def initialize(self):
        """Initialize connection to Redis Streams"""
        try:
            self.event_bus = EventBus(redis_url=self.redis_url)
            await self.event_bus.initialize()
            logger.info(f"Event emitter initialized (Redis: {self.redis_url})")
        except Exception as e:
            logger.error(f"Failed to initialize event bus: {e}")
            raise

    async def emit_workspace_switch(
        self,
        from_workspace: Optional[str],
        to_workspace: Optional[str],
        from_app: str,
        to_app: str,
        file_activity: Optional[dict] = None
    ) -> bool:
        """
        Emit workspace.switched event.

        Args:
            from_workspace: Previous workspace path (or None)
            to_workspace: New workspace path (or None)
            from_app: Previous application name
            to_app: New application name

        Returns:
            True if event emitted successfully
        """
        if not self.event_bus:
            logger.warning("Event bus not initialized")
            return False

        # Don't emit if both workspaces are None (both non-dev apps)
        if from_workspace is None and to_workspace is None:
            logger.debug(f"Skipping: {from_app} → {to_app} (both non-dev apps)")
            return False

        # Don't emit if workspace didn't actually change
        if from_workspace == to_workspace and from_workspace is not None:
            logger.debug(f"Skipping: Same workspace ({from_workspace})")
            return False

        try:
            import time

            event = Event(
                type="workspace.switched",
                data={
                    "from_workspace": from_workspace or "unknown",
                    "to_workspace": to_workspace or "unknown",
                    "from_app": from_app,
                    "to_app": to_app,
                    "switch_type": "automatic",  # Detected by watcher
                    "context_data": {},
                    "workspace_id": to_workspace or "unknown",
                    "adhd_context_capture": {
                        "timestamp": f"{time.time()}",
                        "recovery_priority": "high" if from_workspace and to_workspace else "low",
                        "detection_method": "workspace_watcher",
                        "file_activity": file_activity  # Include file modification data
                    }
                },
                source="workspace-watcher"
            )

            msg_id = await self.event_bus.publish("dopemux:events", event)

            if msg_id:
                self.events_emitted += 1
                logger.info(
                    f"Emitted workspace.switched: "
                    f"{from_app} ({from_workspace or 'N/A'}) → "
                    f"{to_app} ({to_workspace or 'N/A'})"
                )
                return True
            else:
                logger.warning("Event publish returned None (deduplicated or rate-limited)")
                return False

        except Exception as e:
            self.errors += 1
            logger.error(f"Failed to emit event: {e}")
            return False

    async def close(self):
        """Close event bus connection"""
        if self.event_bus:
            await self.event_bus.close()
            logger.info("Event emitter closed")

    def get_metrics(self) -> dict:
        """Get emission metrics"""
        return {
            "events_emitted": self.events_emitted,
            "errors": self.errors,
            "success_rate": (
                self.events_emitted / (self.events_emitted + self.errors)
                if (self.events_emitted + self.errors) > 0
                else 0.0
            )
        }
