"""
Dopemux Event Bus Implementation

Event-driven architecture with ADHD optimizations and multi-instance support.
"""

import json
import asyncio
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Callable, Any
from enum import Enum

import redis.asyncio as redis


class Priority(Enum):
    """Event priority levels for ADHD-optimized filtering."""
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class CognitiveLoad(Enum):
    """Cognitive load levels for ADHD accommodation."""
    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ADHDMetadata:
    """ADHD-specific event metadata for intelligent filtering."""
    cognitive_load: CognitiveLoad
    attention_required: bool = False
    interruption_safe: bool = True
    focus_context: str = "general"
    batching_allowed: bool = True


@dataclass
class EventEnvelope:
    """Standard event envelope for all Dopemux events."""
    id: str
    timestamp: str
    version: str
    source: str
    namespace: str
    type: str
    priority: Priority
    adhd_metadata: ADHDMetadata


@dataclass
class EventRouting:
    """Event routing configuration."""
    targets: List[str]
    filters: List[str]
    ttl_seconds: int = 3600


@dataclass
class DopemuxEvent:
    """Complete Dopemux event with envelope, payload, and routing."""
    envelope: EventEnvelope
    payload: Dict[str, Any]
    routing: EventRouting

    @classmethod
    def create(
        cls,
        event_type: str,
        namespace: str,
        payload: Dict[str, Any],
        source: str = "dopemux",
        priority: Priority = Priority.NORMAL,
        adhd_metadata: Optional[ADHDMetadata] = None,
        targets: Optional[List[str]] = None,
        filters: Optional[List[str]] = None
    ) -> "DopemuxEvent":
        """Create a new DopemuxEvent with auto-generated metadata."""
        envelope = EventEnvelope(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            version="1.0",
            source=source,
            namespace=namespace,
            type=event_type,
            priority=priority,
            adhd_metadata=adhd_metadata or ADHDMetadata(
                cognitive_load=CognitiveLoad.LOW
            )
        )

        routing = EventRouting(
            targets=targets or [namespace.split('.')[0]],
            filters=filters or [],
            ttl_seconds=3600
        )

        return cls(envelope=envelope, payload=payload, routing=routing)

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "envelope": {
                **asdict(self.envelope),
                "priority": self.envelope.priority.value,
                "adhd_metadata": {
                    **asdict(self.envelope.adhd_metadata),
                    "cognitive_load": self.envelope.adhd_metadata.cognitive_load.value
                }
            },
            "payload": self.payload,
            "routing": asdict(self.routing)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DopemuxEvent":
        """Create event from dictionary."""
        envelope_data = data["envelope"]
        adhd_data = envelope_data["adhd_metadata"]

        envelope = EventEnvelope(
            id=envelope_data["id"],
            timestamp=envelope_data["timestamp"],
            version=envelope_data["version"],
            source=envelope_data["source"],
            namespace=envelope_data["namespace"],
            type=envelope_data["type"],
            priority=Priority(envelope_data["priority"]),
            adhd_metadata=ADHDMetadata(
                cognitive_load=CognitiveLoad(adhd_data["cognitive_load"]),
                attention_required=adhd_data["attention_required"],
                interruption_safe=adhd_data["interruption_safe"],
                focus_context=adhd_data["focus_context"],
                batching_allowed=adhd_data["batching_allowed"]
            )
        )

        routing = EventRouting(**data["routing"])

        return cls(envelope=envelope, payload=data["payload"], routing=routing)


class EventBus(ABC):
    """Abstract event bus interface for Dopemux."""

    @abstractmethod
    async def publish(self, event: DopemuxEvent) -> bool:
        """Publish an event to the bus."""
        pass

    @abstractmethod
    async def subscribe(
        self,
        namespace_pattern: str,
        callback: Callable[[DopemuxEvent], None],
        consumer_group: str = "default"
    ) -> str:
        """Subscribe to events matching namespace pattern."""
        pass

    @abstractmethod
    async def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from events."""
        pass

    @abstractmethod
    async def get_health(self) -> Dict[str, Any]:
        """Get event bus health status."""
        pass


class RedisStreamsAdapter(EventBus):
    """Redis Streams implementation of EventBus."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.subscriptions: Dict[str, Dict] = {}
        self.consumer_tasks: Dict[str, asyncio.Task] = {}

    async def connect(self):
        """Connect to Redis."""
        self.redis_client = redis.from_url(self.redis_url)
        await self.redis_client.ping()

    async def disconnect(self):
        """Disconnect from Redis and cleanup."""
        for task in self.consumer_tasks.values():
            task.cancel()
        if self.redis_client:
            await self.redis_client.close()

    async def publish(self, event: DopemuxEvent) -> bool:
        """Publish event to Redis Streams."""
        if not self.redis_client:
            await self.connect()

        stream_name = f"dopemux:events:{event.envelope.namespace}"
        event_data = {"event": json.dumps(event.to_dict())}

        try:
            await self.redis_client.xadd(stream_name, event_data)

            # Set TTL on stream if specified
            if event.routing.ttl_seconds > 0:
                await self.redis_client.expire(stream_name, event.routing.ttl_seconds)

            return True
        except Exception as e:
            print(f"Failed to publish event: {e}")
            return False

    async def subscribe(
        self,
        namespace_pattern: str,
        callback: Callable[[DopemuxEvent], None],
        consumer_group: str = "default"
    ) -> str:
        """Subscribe to events using Redis consumer groups."""
        if not self.redis_client:
            await self.connect()

        subscription_id = str(uuid.uuid4())
        stream_name = f"dopemux:events:{namespace_pattern}"

        # Create consumer group if it doesn't exist
        try:
            await self.redis_client.xgroup_create(
                stream_name, consumer_group, id="0", mkstream=True
            )
        except redis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

        # Store subscription info
        self.subscriptions[subscription_id] = {
            "stream": stream_name,
            "consumer_group": consumer_group,
            "callback": callback,
            "pattern": namespace_pattern
        }

        # Start consumer task
        consumer_name = f"consumer-{subscription_id[:8]}"
        task = asyncio.create_task(
            self._consume_events(subscription_id, stream_name, consumer_group, consumer_name, callback)
        )
        self.consumer_tasks[subscription_id] = task

        return subscription_id

    async def _consume_events(
        self,
        subscription_id: str,
        stream_name: str,
        consumer_group: str,
        consumer_name: str,
        callback: Callable[[DopemuxEvent], None]
    ):
        """Consumer task for processing events."""
        while subscription_id in self.subscriptions:
            try:
                # Read from stream
                messages = await self.redis_client.xreadgroup(
                    consumer_group,
                    consumer_name,
                    {stream_name: ">"},
                    count=10,
                    block=1000
                )

                for stream, msgs in messages:
                    for msg_id, fields in msgs:
                        try:
                            # Parse event
                            event_data = json.loads(fields[b"event"])
                            event = DopemuxEvent.from_dict(event_data)

                            # Call callback
                            await asyncio.get_event_loop().run_in_executor(
                                None, callback, event
                            )

                            # Acknowledge message
                            await self.redis_client.xack(stream_name, consumer_group, msg_id)

                        except Exception as e:
                            print(f"Error processing event {msg_id}: {e}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Consumer error: {e}")
                await asyncio.sleep(5)  # Back off on error

    async def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from events."""
        if subscription_id in self.subscriptions:
            # Cancel consumer task
            if subscription_id in self.consumer_tasks:
                self.consumer_tasks[subscription_id].cancel()
                del self.consumer_tasks[subscription_id]

            # Remove subscription
            del self.subscriptions[subscription_id]
            return True
        return False

    async def get_health(self) -> Dict[str, Any]:
        """Get Redis Streams health status."""
        if not self.redis_client:
            return {"status": "disconnected"}

        try:
            await self.redis_client.ping()
            info = await self.redis_client.info("memory")

            return {
                "status": "healthy",
                "backend": "redis_streams",
                "memory_usage": info.get("used_memory_human", "unknown"),
                "active_subscriptions": len(self.subscriptions),
                "consumer_tasks": len(self.consumer_tasks)
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}


class InMemoryAdapter(EventBus):
    """In-memory implementation for testing."""

    def __init__(self):
        self.subscriptions: Dict[str, Dict] = {}
        self.events: List[DopemuxEvent] = []

    async def publish(self, event: DopemuxEvent) -> bool:
        """Publish event to memory store."""
        self.events.append(event)

        # Notify subscribers
        for sub_id, sub_info in self.subscriptions.items():
            pattern = sub_info["pattern"]
            if self._matches_pattern(event.envelope.namespace, pattern):
                callback = sub_info["callback"]
                await asyncio.get_event_loop().run_in_executor(
                    None, callback, event
                )

        return True

    def _matches_pattern(self, namespace: str, pattern: str) -> bool:
        """Simple pattern matching for namespaces."""
        if pattern == "*":
            return True
        if pattern.endswith("*"):
            return namespace.startswith(pattern[:-1])
        return namespace == pattern

    async def subscribe(
        self,
        namespace_pattern: str,
        callback: Callable[[DopemuxEvent], None],
        consumer_group: str = "default"
    ) -> str:
        """Subscribe to events in memory."""
        subscription_id = str(uuid.uuid4())
        self.subscriptions[subscription_id] = {
            "pattern": namespace_pattern,
            "callback": callback,
            "consumer_group": consumer_group
        }
        return subscription_id

    async def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from events."""
        if subscription_id in self.subscriptions:
            del self.subscriptions[subscription_id]
            return True
        return False

    async def get_health(self) -> Dict[str, Any]:
        """Get in-memory adapter health."""
        return {
            "status": "healthy",
            "backend": "in_memory",
            "events_stored": len(self.events),
            "active_subscriptions": len(self.subscriptions)
        }