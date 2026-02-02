"""
Dope-Memory EventBus Consumer — Real-time Event Ingestion.

Subscribes to activity.events.v1 stream and processes events through
the promotion engine to create curated work_log_entries.

Per spec:
- Input stream: activity.events.v1
- Output stream: memory.derived.v1
- Consumer group: dope-memory-ingestor
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import redis.asyncio as redis

from chronicle.store import ChronicleStore
from promotion.redactor import Redactor
from promotion.promotion import PromotionEngine

logger = logging.getLogger(__name__)

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
INPUT_STREAM = os.getenv("DOPE_MEMORY_INPUT_STREAM", "activity.events.v1")
OUTPUT_STREAM = os.getenv("DOPE_MEMORY_OUTPUT_STREAM", "memory.derived.v1")
CONSUMER_GROUP = os.getenv("DOPE_MEMORY_CONSUMER_GROUP", "dope-memory-ingestor")
DATA_DIR = Path(os.getenv("DOPE_MEMORY_DATA_DIR", str(Path.home() / ".dope-memory")))


class EventBusConsumer:
    """
    EventBus consumer for Dope-Memory.

    Subscribes to activity.events.v1 and:
    1. Stores all events in raw_activity_events (with TTL)
    2. Promotes eligible events to work_log_entries
    3. Publishes derived events to memory.derived.v1
    """

    def __init__(
        self,
        redis_url: str = REDIS_URL,
        redis_password: Optional[str] = REDIS_PASSWORD,
        data_dir: Path = DATA_DIR,
        input_stream: str = INPUT_STREAM,
        output_stream: str = OUTPUT_STREAM,
        consumer_group: str = CONSUMER_GROUP,
    ):
        self.redis_url = redis_url
        self.redis_password = redis_password
        self.data_dir = data_dir
        self.input_stream = input_stream
        self.output_stream = output_stream
        self.consumer_group = consumer_group
        self.consumer_name = f"consumer-{uuid.uuid4().hex[:8]}"

        self.redis_client: Optional[redis.Redis] = None
        self.redactor = Redactor()
        self.promotion_engine = PromotionEngine()
        self._stores: dict[str, ChronicleStore] = {}
        self._running = False

    async def initialize(self) -> None:
        """Initialize Redis connection and create consumer group."""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                password=self.redis_password,
                decode_responses=False,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            )
            await self.redis_client.ping()
            logger.info(f"✅ Dope-Memory EventBus consumer connected to Redis")

            # Create consumer group (idempotent)
            try:
                await self.redis_client.xgroup_create(
                    self.input_stream, self.consumer_group, id="0", mkstream=True
                )
                logger.info(f"✅ Created consumer group: {self.consumer_group}")
            except redis.ResponseError as e:
                if "BUSYGROUP" not in str(e):
                    raise
                # Group already exists

            # Ensure data directory
            self.data_dir.mkdir(parents=True, exist_ok=True)

        except Exception as e:
            logger.error(f"❌ Failed to initialize EventBus consumer: {e}")
            raise

    def _get_store(self, workspace_id: str) -> ChronicleStore:
        """Get or create ChronicleStore for workspace."""
        if workspace_id not in self._stores:
            db_path = self.data_dir / workspace_id / "chronicle.db"
            db_path.parent.mkdir(parents=True, exist_ok=True)
            store = ChronicleStore(db_path)
            store.initialize_schema()
            self._stores[workspace_id] = store
        return self._stores[workspace_id]

    async def start(self) -> None:
        """Start consuming events."""
        if not self.redis_client:
            await self.initialize()

        self._running = True
        logger.info(
            f"📥 Starting Dope-Memory EventBus consumer: "
            f"{self.input_stream} -> {self.consumer_group}/{self.consumer_name}"
        )

        while self._running:
            try:
                # Read from stream (blocking with 1s timeout)
                events = await self.redis_client.xreadgroup(
                    groupname=self.consumer_group,
                    consumername=self.consumer_name,
                    streams={self.input_stream: ">"},
                    count=10,
                    block=1000,
                )

                if events:
                    for stream_name, messages in events:
                        for msg_id, msg_data in messages:
                            try:
                                await self._process_message(msg_id, msg_data)
                                await self.redis_client.xack(
                                    self.input_stream, self.consumer_group, msg_id
                                )
                            except Exception as e:
                                logger.error(f"❌ Error processing message {msg_id}: {e}")
                                # Don't ack - message will be retried

            except redis.RedisError as e:
                logger.error(f"❌ Redis error in consumer: {e}")
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"❌ Unexpected error in consumer: {e}")
                await asyncio.sleep(1)

    async def stop(self) -> None:
        """Stop consuming events."""
        self._running = False
        if self.redis_client:
            await self.redis_client.close()
        logger.info("📭 Dope-Memory EventBus consumer stopped")

    async def _process_message(self, msg_id: bytes, msg_data: dict[bytes, bytes]) -> None:
        """Process a single event message."""
        # Parse event envelope
        try:
            event = self._parse_event(msg_data)
        except Exception as e:
            logger.warning(f"⚠️  Failed to parse event {msg_id}: {e}")
            return

        workspace_id = event.get("workspace_id", "default")
        instance_id = event.get("instance_id", "A")
        event_type = event.get("type", "unknown")
        source = event.get("source", "unknown")
        data = event.get("data", {})

        logger.debug(f"📨 Processing event: {event_type} from {source}")

        store = self._get_store(workspace_id)

        # Step 1: Redact payload
        redacted_data = self.redactor.redact_payload(data)

        # Step 2: Store raw event (with TTL)
        store.insert_raw_event(
            workspace_id=workspace_id,
            instance_id=instance_id,
            event_id=event.get("id", str(uuid.uuid4())),
            event_type=event_type,
            source=source,
            payload=redacted_data,
            ts_utc=event.get("ts", datetime.now(timezone.utc).isoformat()),
            session_id=event.get("session_id"),
        )

        # Step 3: Attempt promotion
        # The promotion engine expects the data payload fields at top level
        entry = self.promotion_engine.promote(event_type, redacted_data)

        if entry:
            entry_id = store.insert_work_log_entry(
                workspace_id=workspace_id,
                instance_id=instance_id,
                category=entry.category,
                entry_type=entry.entry_type,
                summary=entry.summary,
                session_id=event.get("session_id"),
                importance_score=entry.importance_score,
                tags=entry.tags,
                details=entry.details,
                reasoning=entry.reasoning,
                outcome=entry.outcome,
                linked_files=entry.linked_files,
                linked_commits=entry.linked_commits,
                linked_decisions=entry.linked_decisions,
            )

            logger.info(f"✅ Promoted {event_type} -> {entry.category}/{entry.entry_type} ({entry_id})")

            # Step 4: Publish derived event
            await self._publish_derived_event(
                event_type="worklog.created",
                data={
                    "entry_id": entry_id,
                    "category": entry.category,
                    "entry_type": entry.entry_type,
                    "importance_score": entry.importance_score,
                    "summary": entry.summary[:100],
                },
                workspace_id=workspace_id,
                instance_id=instance_id,
            )
        else:
            logger.debug(f"⏭️  Event {event_type} not promoted (raw-only)")

    def _parse_event(self, msg_data: dict[bytes, bytes]) -> dict[str, Any]:
        """Parse event from Redis message data."""
        # Handle both string and binary keys/values
        result = {}
        for key, value in msg_data.items():
            key_str = key.decode("utf-8") if isinstance(key, bytes) else key
            val_str = value.decode("utf-8") if isinstance(value, bytes) else value

            # Parse JSON fields
            if key_str == "data":
                try:
                    result[key_str] = json.loads(val_str)
                except json.JSONDecodeError:
                    result[key_str] = {"raw": val_str}
            else:
                result[key_str] = val_str

        # Map old event type field to new
        if "event_type" in result and "type" not in result:
            result["type"] = result["event_type"]

        return result

    async def _publish_derived_event(
        self,
        event_type: str,
        data: dict[str, Any],
        workspace_id: str,
        instance_id: str,
    ) -> None:
        """Publish derived event to output stream."""
        if not self.redis_client:
            return

        try:
            event_envelope = {
                b"id": str(uuid.uuid4()).encode(),
                b"ts": datetime.now(timezone.utc).isoformat().encode(),
                b"workspace_id": workspace_id.encode(),
                b"instance_id": instance_id.encode(),
                b"type": event_type.encode(),
                b"source": b"dope-memory",
                b"data": json.dumps(data).encode(),
            }
            msg_id = await self.redis_client.xadd(self.output_stream, event_envelope)
            logger.debug(f"📤 Published {event_type} to {self.output_stream} ({msg_id.decode()})")
        except Exception as e:
            logger.warning(f"⚠️  Failed to publish derived event: {e}")


async def run_consumer() -> None:
    """Run the EventBus consumer (entry point)."""
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    consumer = EventBusConsumer()
    await consumer.initialize()
    await consumer.start()


if __name__ == "__main__":
    asyncio.run(run_consumer())
