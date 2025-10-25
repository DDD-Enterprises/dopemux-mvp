"""
Event Subscriber - Redis Streams Consumer for Activity Events

Subscribes to workspace.switched events from Desktop-Commander and forwards
them to the Activity Tracker for aggregation and logging to ADHD Engine.

Features:
- Redis Streams consumer with consumer group
- Automatic reconnection on failure
- Event filtering (workspace.switched only for MVP)
- Error handling and logging
- Background task execution
"""

import asyncio
import logging
import json
from typing import Any, Dict, Optional
from datetime import datetime

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class EventSubscriber:
    """
    Redis Streams event subscriber for activity capture.

    Subscribes to dopemux:events stream and forwards workspace events
    to the Activity Tracker.
    """

    def __init__(
        self,
        redis_url: str,
        stream_name: str,
        consumer_group: str,
        consumer_name: str,
        activity_tracker: Any
    ):
        """
        Initialize event subscriber.

        Args:
            redis_url: Redis connection URL
            stream_name: Stream to subscribe to (dopemux:events)
            consumer_group: Consumer group name
            consumer_name: This consumer's name
            activity_tracker: ActivityTracker instance to forward events to
        """
        self.redis_url = redis_url
        self.stream_name = stream_name
        self.consumer_group = consumer_group
        self.consumer_name = consumer_name
        self.activity_tracker = activity_tracker

        # Connection
        self.redis: Optional[redis.Redis] = None

        # State
        self.running = False
        self.subscriber_task: Optional[asyncio.Task] = None

        # Metrics
        self.events_processed = 0
        self.workspace_switches = 0
        self.errors = 0

    async def start(self):
        """Start event subscriber in background"""
        # Connect to Redis
        self.redis = redis.from_url(self.redis_url, decode_responses=True)

        # Create consumer group (ignore error if exists)
        try:
            await self.redis.xgroup_create(
                name=self.stream_name,
                groupname=self.consumer_group,
                id="0",
                mkstream=True
            )
            logger.info(f"✅ Created consumer group: {self.consumer_group}")
        except redis.ResponseError as e:
            if "BUSYGROUP" in str(e):
                logger.info(f"📋 Consumer group already exists: {self.consumer_group}")
            else:
                raise

        # Start subscriber task
        self.running = True
        self.subscriber_task = asyncio.create_task(self._subscribe_loop())
        logger.info(f"▶️  Started event subscriber: {self.stream_name}")

    async def _subscribe_loop(self):
        """Main event subscription loop"""
        while self.running:
            try:
                # Read events from stream
                events = await self.redis.xreadgroup(
                    groupname=self.consumer_group,
                    consumername=self.consumer_name,
                    streams={self.stream_name: ">"},
                    count=10,
                    block=1000  # Block for 1 second
                )

                # Process events
                for stream, messages in events:
                    for message_id, data in messages:
                        await self._process_event(message_id, data)

                        # Acknowledge message
                        await self.redis.xack(
                            self.stream_name,
                            self.consumer_group,
                            message_id
                        )

            except asyncio.CancelledError:
                logger.info("⏹️  Subscriber loop cancelled")
                break
            except Exception as e:
                self.errors += 1
                logger.error(f"Subscriber error: {e}")
                await asyncio.sleep(5)  # Back off on error

    async def _process_event(self, message_id: str, data: Dict[str, str]):
        """
        Process a single event from the stream.

        Args:
            message_id: Redis stream message ID
            data: Event data from stream
        """
        try:
            # Parse event data - Redis uses "event_type" not "type"
            event_type = data.get("event_type", data.get("type", ""))
            event_data_str = data.get("data", "{}")
            event_data = json.loads(event_data_str) if isinstance(event_data_str, str) else event_data_str

            self.events_processed += 1

            # Debug: Log what events we're seeing
            logger.info(f"📥 Event #{self.events_processed}: {event_type}")

            # Handle workspace.switched events
            if event_type == "workspace.switched":
                logger.info(f"🔍 Processing workspace.switched event: {event_data.get('from_workspace', '?')} → {event_data.get('to_workspace', '?')}")
                await self._handle_workspace_switched(event_data)

            # Future: Handle other event types
            # elif event_type == "progress.updated":
            #     await self._handle_progress_updated(event_data)

        except Exception as e:
            self.errors += 1
            logger.error(f"Event processing error: {e} | Data: {data}")

    async def _handle_workspace_switched(self, event_data: Dict[str, Any]):
        """
        Handle workspace switch event from Desktop-Commander.

        Args:
            event_data: Event payload with from_workspace, to_workspace, etc.
        """
        from_workspace = event_data.get("from_workspace", "")
        to_workspace = event_data.get("to_workspace", "")
        switch_type = event_data.get("switch_type", "manual")

        self.workspace_switches += 1

        # Detect if switching TO dopemux workspace (start session)
        if "dopemux" in to_workspace.lower():
            logger.info(f"📍 Session started: {to_workspace}")
            await self.activity_tracker.start_session()

        # Detect if switching FROM dopemux workspace (end session, log activity)
        elif "dopemux" in from_workspace.lower():
            logger.info(f"📤 Session ended: {from_workspace} → {to_workspace}")
            await self.activity_tracker.end_session(interruption=True)

        # Switching between other workspaces (count as interruption if session active)
        else:
            logger.debug(f"🔄 Workspace switch: {from_workspace} → {to_workspace}")
            await self.activity_tracker.record_interruption()

    async def stop(self):
        """Stop event subscriber gracefully"""
        self.running = False

        if self.subscriber_task:
            self.subscriber_task.cancel()
            try:
                await self.subscriber_task
            except asyncio.CancelledError:
                pass

        if self.redis:
            await self.redis.close()

        logger.info("⏹️  Event subscriber stopped")

    def get_metrics(self) -> Dict[str, Any]:
        """Get subscriber metrics"""
        return {
            "running": self.running,
            "events_processed": self.events_processed,
            "workspace_switches": self.workspace_switches,
            "errors": self.errors,
            "stream_name": self.stream_name,
            "consumer_group": self.consumer_group
        }
