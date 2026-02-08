"""
Event Subscriber for Activity Capture

Subscribes to Redis Streams and routes events to activity tracker.
"""

import asyncio
import json
import logging
from typing import Optional

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class EventSubscriber:
    """
    Redis Streams subscriber for activity events.

    Subscribes to dopemux:events stream and forwards relevant events
    to the activity tracker for processing.
    """

    def __init__(
        self,
        redis_url: str,
        stream_name: str,
        consumer_group: str,
        consumer_name: str,
        activity_tracker
    ):
        """
        Initialize event subscriber.

        Args:
            redis_url: Redis connection URL
            stream_name: Stream to subscribe to
            consumer_group: Consumer group name
            consumer_name: Consumer name
            activity_tracker: ActivityTracker instance
        """
        self.redis_url = redis_url
        self.stream_name = stream_name
        self.consumer_group = consumer_group
        self.consumer_name = consumer_name
        self.activity_tracker = activity_tracker

        self.redis_client: Optional[redis.Redis] = None
        self.running = False

        # Metrics
        self.events_processed = 0
        self.errors = 0

    async def initialize(self):
        """Initialize Redis connection."""
        self.redis_client = redis.from_url(self.redis_url)

        # Create consumer group if it doesn't exist
        try:
            await self.redis_client.xgroup_create(
                self.stream_name,
                self.consumer_group,
                "$",
                mkstream=True
            )
            logger.info(f"Created consumer group: {self.consumer_group}")
        except redis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

    async def start(self):
        """Start event subscription loop."""
        if not self.redis_client:
            await self.initialize()

        self.running = True
        logger.info(f"Starting event subscription to {self.stream_name}")

        while self.running:
            try:
                # Read pending messages
                messages = await self.redis_client.xreadgroup(
                    self.consumer_group,
                    self.consumer_name,
                    {self.stream_name: ">"},
                    count=10,
                    block=1000  # 1 second block
                )

                for stream, message_list in messages:
                    for message_id, message_data in message_list:
                        try:
                            await self._process_message(message_data)
                            self.events_processed += 1

                            # Acknowledge message
                            await self.redis_client.xack(
                                self.stream_name,
                                self.consumer_group,
                                message_id
                            )

                        except Exception as e:
                            logger.error(f"Error processing message {message_id}: {e}")
                            self.errors += 1

            except Exception as e:
                logger.error(f"Error in event subscription loop: {e}")
                self.errors += 1
                await asyncio.sleep(5)  # Back off on errors

    async def _process_message(self, message_data: dict):
        """
        Process incoming message.

        Routes different event types to appropriate handlers.
        """
        event_type = message_data.get("type", "")
        event_data = message_data.get("data", {})

        logger.debug(f"Processing event: {event_type}")

        if event_type == "workspace.switched":
            await self.activity_tracker.handle_workspace_switch(event_data)
        elif event_type == "progress.updated":
            await self.activity_tracker.handle_progress_update(event_data)
        elif event_type == "session.started":
            await self.activity_tracker.handle_session_start(event_data)
        elif event_type == "break.taken":
            await self.activity_tracker.handle_break_taken(event_data)
        else:
            logger.debug(f"Ignoring unknown event type: {event_type}")

    async def stop(self):
        """Stop event subscription."""
        self.running = False

        if self.redis_client:
            await self.redis_client.close()

        logger.info("Event subscriber stopped")