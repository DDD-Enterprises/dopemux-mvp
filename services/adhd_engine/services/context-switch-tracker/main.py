"""
Context Switch Tracker Service - Context Switching Monitoring

Tracks context switches and provides insights for ADHD accommodation.
Monitors switching patterns and suggests optimizations.
"""

import asyncio
import json
import logging
import os
from typing import Dict, Any, List
from collections import defaultdict

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class ContextSwitchTracker:
    """
    Tracks and analyzes context switching patterns.

    Monitors workspace switches, interruption patterns, and provides
    insights for ADHD accommodation and productivity optimization.
    """

    def __init__(self, redis_url: str, user_id: str):
        self.redis_url = redis_url
        self.user_id = user_id
        self.redis: redis.Redis = None

        # Tracking configuration
        self.switch_detection_threshold = int(os.getenv("SWITCH_DETECTION_THRESHOLD", "10"))
        self.context_save_enabled = os.getenv("CONTEXT_SAVE_ENABLED", "true").lower() == "true"

        # Switch tracking
        self.current_context = None
        self.context_history: List[Dict[str, Any]] = []
        self.switch_count = 0

    async def initialize(self):
        """Initialize Redis connection."""
        self.redis = redis.from_url(self.redis_url)
        logger.info("Context Switch Tracker initialized")

    async def process_workspace_switch(self, switch_data: Dict[str, Any]):
        """
        Process workspace switch event.

        Args:
            switch_data: Workspace switch event data
        """
        try:
            from_workspace = switch_data.get("from_workspace")
            to_workspace = switch_data.get("to_workspace")

            logger.info(f"Context switch: {from_workspace} → {to_workspace}")

            # Track switch
            switch_event = {
                "timestamp": asyncio.get_event_loop().time(),
                "from_workspace": from_workspace,
                "to_workspace": to_workspace,
                "from_app": switch_data.get("from_app"),
                "to_app": switch_data.get("to_app"),
                "file_activity": switch_data.get("file_activity")
            }

            self.context_history.append(switch_event)
            self.switch_count += 1

            # Analyze switching patterns
            await self._analyze_switching_patterns()

        except Exception as e:
            logger.error(f"Error processing workspace switch: {e}")

    async def _analyze_switching_patterns(self):
        """Analyze context switching patterns for insights."""
        try:
            # Check for excessive switching
            recent_switches = [
                switch for switch in self.context_history[-10:]  # Last 10 switches
                if asyncio.get_event_loop().time() - switch["timestamp"] < 3600  # Last hour
            ]

            if len(recent_switches) >= self.switch_detection_threshold:
                # Excessive switching detected
                await self._notify_excessive_switching(recent_switches)

        except Exception as e:
            logger.error(f"Error analyzing switching patterns: {e}")

    async def _notify_excessive_switching(self, recent_switches: List[Dict[str, Any]]):
        """
        Notify of excessive context switching.

        Args:
            recent_switches: Recent switch events
        """
        try:
            notification = {
                "type": "context_switching.excessive",
                "user_id": self.user_id,
                "switch_count": len(recent_switches),
                "time_window_minutes": 60,
                "recommendations": [
                    "Consider focusing on one workspace for extended periods",
                    "High context switching detected - may impact productivity"
                ]
            }

            # Send to ADHD Engine
            await self.redis.xadd("dopemux:events", {
                "type": "context_switching.excessive",
                "data": notification
            })

            logger.info(f"Detected excessive context switching: {len(recent_switches)} switches/hour")

        except Exception as e:
            logger.error(f"Failed to notify of excessive switching: {e}")

    def get_switching_metrics(self) -> Dict[str, Any]:
        """Get context switching metrics."""
        return {
            "total_switches": self.switch_count,
            "current_context": self.current_context,
            "recent_switches": len([
                switch for switch in self.context_history[-20:]
                if asyncio.get_event_loop().time() - switch["timestamp"] < 3600
            ]),
            "switching_rate_per_hour": len([
                switch for switch in self.context_history[-100:]
                if asyncio.get_event_loop().time() - switch["timestamp"] < 3600
            ])
        }


async def start_context_switch_tracker(user_id: str = "default"):
    """
    Start context switch tracker service.

    Monitors workspace switches and analyzes patterns.
    """
    redis_url = os.getenv("REDIS_URL", "redis://redis-primary:6379")

    tracker = ContextSwitchTracker(redis_url, user_id)
    await tracker.initialize()

    redis_client = redis.from_url(redis_url)

    logger.info("Context Switch Tracker started")

    while True:
        try:
            # Listen for workspace switch events
            messages = await redis_client.xread(
                {"dopemux:events": "$"},
                block=1000,
                count=10
            )

            for stream, message_list in messages:
                for message_id, message_data in message_list:
                    try:
                        event_type = message_data.get("type", "")
                        event_data = message_data.get("data", {})

                        # Process workspace switches
                        if event_type == "workspace.switched":
                            await tracker.process_workspace_switch(event_data)

                        # Acknowledge message
                        await redis_client.xack("dopemux:events", f"context-switch-tracker-{user_id}", message_id)

                    except Exception as e:
                        logger.error(f"Error processing message: {e}")

        except Exception as e:
            logger.error(f"Context switch tracker error: {e}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    user_id = os.getenv("USER_ID", "default")
    asyncio.run(start_context_switch_tracker(user_id))