from typing import Callable, Optional

import logging

logger = logging.getLogger(__name__)

from dataclasses import dataclass
from enum import Enum
import asyncio
import json
import redis.asyncio as redis
from typing import Dict, Any

class EventType(Enum):
    """Types of events for Genetic Agent."""
    BUG_DETECTED = "bug_detected"
    REPAIR_ATTEMPTED = "repair_attempted"
    REPAIR_SUCCESSFUL = "repair_successful"
    TEST_RESULTS = "test_results"
    USER_FEEDBACK = "user_feedback"

@dataclass
class Event:
    """Event structure for EventBus."""
    type: EventType
    source: str
    payload: Dict[str, Any]
    workspace_id: str
    user_id: str
    timestamp: float = None

class SimpleEventBus:
    """Simple EventBus implementation for Genetic Agent."""

    def __init__(self, redis_url: str = "redis://localhost:6379", db: int = 2):
        self.redis_url = redis_url
        self.db = db
        self.redis_client = None
        self.subscribers: Dict[EventType, list[Callable]] = {}

    async def initialize(self):
        """Initialize the EventBus with Redis."""
        self.redis_client = redis.from_url(self.redis_url, db=self.db)
        await self.redis_client.ping()
        logger.info("EventBus initialized with Redis")

    async def publish(self, event: Event) -> bool:
        """Publish an event to Redis Stream."""
        if not self.redis_client:
            await self.initialize()

        event.timestamp = time.time()
        event_json = json.dumps({
            "type": event.type.value,
            "source": event.source,
            "payload": event.payload,
            "workspace_id": event.workspace_id,
            "user_id": event.user_id,
            "timestamp": event.timestamp
        })

        try:
            await self.redis_client.xadd("genetic_events", {"event": event_json})
            logger.info(f"Published {event.type.value} event")
            return True
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            return False

    async def subscribe(self, event_type: EventType, callback: Callable, filter_fn: Optional[Callable] = None):
        """Subscribe to events of a specific type."""
        if not self.redis_client:
            await self.initialize()

        if event_type not in self.subscribers:
            self.subscribers[event_type] = []

        self.subscribers[event_type].append((callback, filter_fn))

        # Start background consumer
        asyncio.create_task(self._consume_events(event_type))

    async def _consume_events(self, event_type: EventType):
        """Consume events from Redis Stream."""
        stream_name = "genetic_events"
        consumer_group = f"genetic_sub_{event_type.value}"

        try:
            # Create consumer group if not exists
            await self.redis_client.xgroup_create(stream_name, consumer_group, id="0", mkstream=True)
        except redis.ResponseError:
            # Group already exists
            pass

        while True:
            try:
                messages = await self.redis_client.xreadgroup(
                    consumer_group,
                    f"consumer_{asyncio.current_task().get_name()}",
                    streams={stream_name: ">"},
                    count=1,
                    block=1000
                )

                for stream, message_list in messages:
                    for message_id, message_data in message_list:
                        event_data = json.loads(message_data[b'event'])
                        event = Event(
                            type=EventType(event_data['type']),
                            source=event_data['source'],
                            payload=event_data['payload'],
                            workspace_id=event_data['workspace_id'],
                            user_id=event_data['user_id']
                        )

                        for callback, filter_fn in self.subscribers.get(event_type, []):
                            if filter_fn is None or filter_fn(event):
                                asyncio.create_task(callback(event))

                        # Acknowledge message
                        await self.redis_client.xack(stream_name, consumer_group, message_id)

            except Exception as e:
                logger.error(f"Error consuming events: {e}")
                await asyncio.sleep(5)