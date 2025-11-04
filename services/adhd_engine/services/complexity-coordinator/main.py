"""
Complexity Coordinator Service - Code Complexity Analysis & Coordination

Monitors code complexity across the development environment and coordinates
with ADHD Engine for appropriate accommodations.
"""

import asyncio
import json
import logging
import os
from typing import Dict, Any

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class ComplexityCoordinator:
    """
    Coordinates code complexity monitoring and ADHD accommodations.

    Monitors complexity events and coordinates with ADHD Engine for
    appropriate focus and break recommendations.
    """

    def __init__(self, redis_url: str, user_id: str):
        self.redis_url = redis_url
        self.user_id = user_id
        self.redis: redis.Redis = None

        # Complexity thresholds
        self.complexity_threshold = float(os.getenv("COMPLEXITY_THRESHOLD", "0.6"))
        self.analysis_interval = int(os.getenv("ANALYSIS_INTERVAL", "30"))

    async def initialize(self):
        """Initialize Redis connection."""
        self.redis = redis.from_url(self.redis_url)
        logger.info("Complexity Coordinator initialized")

    async def process_complexity_event(self, event_data: Dict[str, Any]):
        """
        Process code complexity event.

        Args:
            event_data: Complexity analysis data
        """
        try:
            complexity_score = event_data.get("complexity_score", 0)
            file_path = event_data.get("file_path", "unknown")

            logger.info(f"Processing complexity event: {file_path} = {complexity_score}")

            if complexity_score >= self.complexity_threshold:
                # High complexity detected - notify ADHD Engine
                await self._notify_high_complexity(event_data)

        except Exception as e:
            logger.error(f"Error processing complexity event: {e}")

    async def _notify_high_complexity(self, event_data: Dict[str, Any]):
        """
        Notify ADHD Engine of high complexity code.

        Args:
            event_data: Complexity event data
        """
        try:
            notification = {
                "type": "code.complexity.high",
                "user_id": self.user_id,
                "complexity_score": event_data.get("complexity_score"),
                "file_path": event_data.get("file_path"),
                "function_name": event_data.get("function_name"),
                "recommendations": [
                    "Consider taking a break after this complex section",
                    "High complexity detected - monitor attention levels"
                ]
            }

            # Send to ADHD Engine
            await self.redis.xadd("dopemux:events", {
                "type": "code.complexity.high",
                "data": notification
            })

            logger.info(f"Notified ADHD Engine of high complexity: {event_data.get('file_path')}")

        except Exception as e:
            logger.error(f"Failed to notify ADHD Engine: {e}")


async def start_complexity_coordinator(user_id: str = "default"):
    """
    Start complexity coordinator service.

    Monitors for complexity events and coordinates with ADHD Engine.
    """
    redis_url = os.getenv("REDIS_URL", "redis://redis-primary:6379")

    coordinator = ComplexityCoordinator(redis_url, user_id)
    await coordinator.initialize()

    redis_client = redis.from_url(redis_url)

    logger.info("Complexity Coordinator started")

    while True:
        try:
            # Listen for complexity events
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

                        # Process complexity events
                        if event_type == "code.complexity.analyzed":
                            await coordinator.process_complexity_event(event_data)

                        # Acknowledge message
                        await redis_client.xack("dopemux:events", f"complexity-coordinator-{user_id}", message_id)

                    except Exception as e:
                        logger.error(f"Error processing message: {e}")

        except Exception as e:
            logger.error(f"Complexity coordinator error: {e}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    user_id = os.getenv("USER_ID", "default")
    asyncio.run(start_complexity_coordinator(user_id))