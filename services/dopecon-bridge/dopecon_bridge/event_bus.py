"""Minimal Redis Streams event bus for dopecon_bridge routes."""

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, Optional, Tuple

import redis.asyncio as redis

from .core import cache_manager


logger = logging.getLogger(__name__)


@dataclass
class Event:
    """Structured event payload for stream publishing/subscription."""

    type: str
    data: Dict[str, Any]
    source: str = "dopecon-bridge"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "data": self.data,
            "source": self.source,
            "timestamp": self.timestamp,
        }

    def to_redis_fields(self) -> Dict[str, str]:
        return {
            "type": self.type,
            "data": json.dumps(self.data),
            "source": self.source,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_redis_fields(cls, payload: Dict[Any, Any]) -> "Event":
        def _get(key: str, default: str = "") -> str:
            value = payload.get(key)
            if value is None:
                value = payload.get(key.encode())
            if value is None:
                return default
            if isinstance(value, bytes):
                return value.decode("utf-8", errors="replace")
            return str(value)

        raw_data = _get("data", "{}")
        try:
            parsed_data = json.loads(raw_data)
        except json.JSONDecodeError:
            parsed_data = {"raw": raw_data}

        return cls(
            type=_get("type", "unknown"),
            data=parsed_data,
            source=_get("source", "unknown"),
            timestamp=_get("timestamp", datetime.now(timezone.utc).isoformat()),
        )


class EventBus:
    """Redis Streams wrapper with route-friendly defaults."""

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None

    async def initialize(self):
        if self.redis_client:
            return
        await cache_manager.initialize()
        self.redis_client = await cache_manager.get_client()

    async def publish(self, stream: str, event: Event) -> str:
        if not self.redis_client:
            await self.initialize()
        msg_id = await self.redis_client.xadd(stream, event.to_redis_fields())
        if isinstance(msg_id, bytes):
            return msg_id.decode("utf-8", errors="replace")
        return str(msg_id)

    async def subscribe(
        self,
        stream: str,
        consumer_group: str,
        consumer_name: Optional[str] = None,
    ) -> AsyncGenerator[Tuple[str, Event], None]:
        if not self.redis_client:
            await self.initialize()

        consumer = consumer_name or f"consumer-{uuid.uuid4().hex[:8]}"
        try:
            await self.redis_client.xgroup_create(
                name=stream,
                groupname=consumer_group,
                id="0",
                mkstream=True,
            )
        except redis.ResponseError as exc:
            if "BUSYGROUP" not in str(exc):
                raise

        while True:
            events = await self.redis_client.xreadgroup(
                groupname=consumer_group,
                consumername=consumer,
                streams={stream: ">"},
                count=50,
                block=1000,
            )
            if not events:
                continue

            for _stream_name, messages in events:
                for msg_id, payload in messages:
                    event = Event.from_redis_fields(payload)
                    normalized_id = msg_id.decode("utf-8") if isinstance(msg_id, bytes) else str(msg_id)
                    yield normalized_id, event
                    await self.redis_client.xack(stream, consumer_group, msg_id)
