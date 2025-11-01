"""
Event Emitter for Workspace Switch Events

Emits workspace switch events to Redis Streams.
"""

import json
import time
from typing import Dict, Optional

import redis.asyncio as redis
import logging

logger = logging.getLogger(__name__)


class WorkspaceSwitchEmitter:
    """
    Emits workspace switch events to Redis Streams.

    Publishes structured events for activity tracking and ADHD accommodations.
    """

    def __init__(self, redis_url: str):
        """
        Initialize event emitter.

        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self.redis: Optional[redis.Redis] = None

        # Metrics
        self.events_emitted = 0
        self.errors = 0

    async def initialize(self):
        """Initialize Redis connection."""
        self.redis = redis.from_url(self.redis_url)

    async def close(self):
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()

    async def emit_workspace_switch(
        self,
        from_workspace: Optional[str],
        to_workspace: Optional[str],
        from_app: str,
        to_app: str,
        file_activity: Optional[Dict] = None
    ) -> bool:
        """
        Emit workspace switch event.

        Args:
            from_workspace: Previous workspace path
            to_workspace: New workspace path
            from_app: Previous application name
            to_app: New application name
            file_activity: Optional file activity data

        Returns:
            True if event emitted successfully
        """
        try:
            event_data = {
                "type": "workspace.switched",
                "data": {
                    "from_workspace": from_workspace,
                    "to_workspace": to_workspace,
                    "from_app": from_app,
                    "to_app": to_app,
                    "file_activity": file_activity,
                    "timestamp": time.time()
                }
            }

            # Emit to Redis Stream
            await self.redis.xadd("dopemux:events", event_data)

            self.events_emitted += 1
            logger.debug(f"Emitted workspace switch event: {from_app} → {to_app}")

            return True

        except Exception as e:
            self.errors += 1
            logger.error(f"Failed to emit workspace switch event: {e}")
            return False

    def get_metrics(self) -> Dict[str, int]:
        """Get emitter metrics."""
        return {
            "events_emitted": self.events_emitted,
            "errors": self.errors
        }