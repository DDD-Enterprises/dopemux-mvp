"""
Redis Streams Event Bus for Integration Bridge
Async event coordination between ConPort, ADHD Engine, and Dashboard
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, AsyncGenerator, Dict, Optional, Tuple
from dataclasses import dataclass, asdict

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Defined event types for Dopemux coordination"""
    TASKS_IMPORTED = "tasks_imported"
    SESSION_STARTED = "session_started"
    SESSION_PAUSED = "session_paused"
    SESSION_COMPLETED = "session_completed"
    PROGRESS_UPDATED = "progress_updated"
    DECISION_LOGGED = "decision_logged"
    ADHD_STATE_CHANGED = "adhd_state_changed"
    BREAK_REMINDER = "break_reminder"


@dataclass
class Event:
    """Structured event with type and data"""
    type: str
    data: Dict[str, Any]
    timestamp: Optional[str] = None
    source: Optional[str] = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

    def to_redis_dict(self) -> Dict[str, str]:
        """Convert to Redis Stream message format"""
        return {
            "event_type": self.type,
            "timestamp": self.timestamp,
            "source": self.source or "integration-bridge",
            "data": json.dumps(self.data)
        }

    @classmethod
    def from_redis_dict(cls, msg_data: Dict[bytes, bytes]) -> 'Event':
        """Parse from Redis Stream message"""
        return cls(
            type=msg_data[b"event_type"].decode("utf-8"),
            timestamp=msg_data[b"timestamp"].decode("utf-8"),
            source=msg_data.get(b"source", b"unknown").decode("utf-8"),
            data=json.loads(msg_data[b"data"].decode("utf-8"))
        )


class EventBus:
    """
    Redis Streams-based event bus for async coordination

    Features:
    - Publish events to named streams
    - Subscribe with consumer groups for load balancing
    - Automatic consumer group creation
    - Message acknowledgment
    - ADHD-optimized: Non-blocking, resilient to interruptions
    """

    def __init__(self, redis_url: str, password: Optional[str] = None):
        """
        Initialize EventBus with Redis connection

        Args:
            redis_url: Redis connection URL
            password: Optional Redis password
        """
        self.redis_url = redis_url
        self.password = password
        self.redis_client: Optional[redis.Redis] = None
        self._subscribers: Dict[str, bool] = {}  # Track active subscribers

    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                password=self.password if self.password else None,
                decode_responses=False,  # Keep binary for Stream compatibility
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )

            # Test connection
            await self.redis_client.ping()
            logger.info("✅ EventBus Redis connection established")

        except Exception as e:
            logger.error(f"❌ EventBus Redis initialization failed: {e}")
            raise

    async def publish(self, stream: str, event: Event) -> str:
        """
        Publish event to Redis Stream

        Args:
            stream: Stream name (e.g., "dopemux:events")
            event: Event to publish

        Returns:
            Message ID from Redis
        """
        if not self.redis_client:
            raise RuntimeError("EventBus not initialized")

        try:
            msg_id = await self.redis_client.xadd(
                stream,
                event.to_redis_dict()
            )

            logger.info(f"📤 Published {event.type} to {stream} (ID: {msg_id.decode()})")
            return msg_id.decode()

        except Exception as e:
            logger.error(f"❌ Failed to publish event: {e}")
            raise

    async def subscribe(
        self,
        stream: str,
        consumer_group: str,
        consumer_name: Optional[str] = None
    ) -> AsyncGenerator[Tuple[str, Event], None]:
        """
        Subscribe to Redis Stream with consumer group

        Args:
            stream: Stream name to subscribe to
            consumer_group: Consumer group name for load balancing
            consumer_name: Optional consumer name (auto-generated if not provided)

        Yields:
            Tuple of (message_id, Event)
        """
        if not self.redis_client:
            raise RuntimeError("EventBus not initialized")

        # Generate consumer name if not provided
        if not consumer_name:
            consumer_name = f"consumer-{uuid.uuid4().hex[:8]}"

        # Create consumer group if not exists
        try:
            await self.redis_client.xgroup_create(
                stream,
                consumer_group,
                id='0',
                mkstream=True  # Create stream if it doesn't exist
            )
            logger.info(f"✅ Created consumer group: {consumer_group} on {stream}")
        except redis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                logger.error(f"❌ Failed to create consumer group: {e}")
                raise
            # Group already exists, continue

        # Mark as active subscriber
        subscriber_key = f"{stream}:{consumer_group}:{consumer_name}"
        self._subscribers[subscriber_key] = True

        logger.info(f"📥 Subscribing to {stream} as {consumer_group}/{consumer_name}")

        try:
            # Read events from stream
            while self._subscribers.get(subscriber_key, False):
                try:
                    # Read from stream (blocking with 1 second timeout)
                    events = await self.redis_client.xreadgroup(
                        groupname=consumer_group,
                        consumername=consumer_name,
                        streams={stream: '>'},
                        count=10,
                        block=1000
                    )

                    # Process received events
                    if events:
                        for stream_name, messages in events:
                            for msg_id, msg_data in messages:
                                try:
                                    # Parse event
                                    event = Event.from_redis_dict(msg_data)

                                    # Yield to consumer
                                    yield msg_id.decode(), event

                                    # Acknowledge message
                                    await self.redis_client.xack(
                                        stream,
                                        consumer_group,
                                        msg_id
                                    )

                                except Exception as e:
                                    logger.error(f"❌ Error processing message {msg_id}: {e}")
                                    # Don't ack, message will be retried

                except redis.RedisError as e:
                    logger.error(f"❌ Redis error in subscriber: {e}")
                    # Wait before retry
                    await asyncio.sleep(1)

        finally:
            # Cleanup on exit
            self._subscribers.pop(subscriber_key, None)
            logger.info(f"📭 Unsubscribed: {consumer_group}/{consumer_name}")

    async def unsubscribe(self, stream: str, consumer_group: str, consumer_name: str):
        """Stop a specific subscriber"""
        subscriber_key = f"{stream}:{consumer_group}:{consumer_name}"
        self._subscribers[subscriber_key] = False

    async def close(self):
        """Close Redis connection and stop all subscribers"""
        # Stop all subscribers
        for key in list(self._subscribers.keys()):
            self._subscribers[key] = False

        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()
            logger.info("📪 EventBus closed")

    async def get_stream_info(self, stream: str) -> Dict[str, Any]:
        """Get information about a stream (for debugging/monitoring)"""
        if not self.redis_client:
            raise RuntimeError("EventBus not initialized")

        try:
            info = await self.redis_client.xinfo_stream(stream)
            return {
                "length": info.get(b"length", 0),
                "groups": info.get(b"groups", 0),
                "first_entry": info.get(b"first-entry"),
                "last_entry": info.get(b"last-entry")
            }
        except redis.ResponseError:
            # Stream doesn't exist
            return {"length": 0, "groups": 0}


# Convenience functions for common event types

async def publish_tasks_imported(bus: EventBus, task_count: int, sprint_id: str):
    """Publish tasks_imported event"""
    event = Event(
        type=EventType.TASKS_IMPORTED,
        data={"task_count": task_count, "sprint_id": sprint_id}
    )
    await bus.publish("dopemux:events", event)


async def publish_session_started(bus: EventBus, task_id: str, duration_minutes: int = 25):
    """Publish session_started event"""
    event = Event(
        type=EventType.SESSION_STARTED,
        data={"task_id": task_id, "duration_minutes": duration_minutes}
    )
    await bus.publish("dopemux:events", event)


async def publish_progress_updated(bus: EventBus, task_id: str, status: str, progress: float):
    """Publish progress_updated event"""
    event = Event(
        type=EventType.PROGRESS_UPDATED,
        data={"task_id": task_id, "status": status, "progress": progress}
    )
    await bus.publish("dopemux:events", event)
