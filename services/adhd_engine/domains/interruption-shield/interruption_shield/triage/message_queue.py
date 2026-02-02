"""
MessageQueue - Redis-backed queue for messages during focus sessions.

Handles message persistence, retrieval, and delivery.
"""

import asyncio
import json
import logging
from collections import Counter, defaultdict
from datetime import datetime
from typing import List, Optional

import redis.asyncio as redis

from .models import QueuedMessage, QueuedSummary, SlackMessage, UrgencyLevel

logger = logging.getLogger(__name__)


class MessageQueue:
    """
    Redis-backed message queue with persistence and prioritization.

    Features:
    - Redis persistence (survives restarts)
    - Size limits (prevent memory bloat)
    - Urgency-based prioritization
    - Duplicate detection
    """

    def __init__(
        self, redis_url: str = "redis://localhost:6379", max_size: int = 100, db: int = 2
    ):
        self.redis_url = redis_url
        self.max_size = max_size
        self.db = db
        self.redis_client: Optional[redis.Redis] = None

        # In-memory cache for fast access
        self._cache: List[QueuedMessage] = []

    async def connect(self):
        """Connect to Redis."""
        try:
            self.redis_client = await redis.from_url(
                self.redis_url, db=self.db, decode_responses=True
            )
            await self.redis_client.ping()
            logger.info(f"✅ Connected to Redis at {self.redis_url}")

            # Load existing queue from Redis
            await self._load_from_redis()

        except Exception as e:
            logger.warning(
                f"⚠️ Redis connection failed: {e}. "
                f"Falling back to in-memory queue (no persistence)"
            )
            self.redis_client = None

    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Disconnected from Redis")

    async def add(self, message: SlackMessage, urgency: UrgencyLevel):
        """Add message to queue."""
        # Check for duplicates
        if any(qm.message.id == message.id for qm in self._cache):
            logger.debug(f"Duplicate message {message.id}, skipping")
            return

        # Enforce size limit (remove oldest LOW urgency)
        if len(self._cache) >= self.max_size:
            await self._evict_oldest_low_urgency()

        # Create queued message
        queued = QueuedMessage(
            message=message, urgency=urgency, queued_at=datetime.now(), delivered=False
        )

        # Add to cache
        self._cache.append(queued)

        # Persist to Redis
        if self.redis_client:
            await self._persist_to_redis(queued)

        logger.info(
            f"➕ Queued {urgency.name} message from {message.user}: "
            f"'{message.text[:30]}...' (queue size: {len(self._cache)})"
        )

    async def get_all(self) -> List[QueuedMessage]:
        """Get all queued messages, sorted by urgency (highest first)."""
        return sorted(
            self._cache, key=lambda qm: (qm.urgency.value, qm.queued_at), reverse=True
        )

    async def get_summary(self) -> QueuedSummary:
        """Generate summary of queued messages."""
        messages = await self.get_all()

        # Count by urgency
        urgency_counts = Counter(qm.urgency for qm in messages)

        # Get unique channels
        channels = list(set(qm.message.channel for qm in messages))

        # Top senders
        sender_counts = Counter(qm.message.user for qm in messages)
        top_senders = sender_counts.most_common(3)

        return QueuedSummary(
            total_count=len(messages),
            critical_count=urgency_counts.get(UrgencyLevel.CRITICAL, 0),
            high_count=urgency_counts.get(UrgencyLevel.HIGH, 0),
            medium_count=urgency_counts.get(UrgencyLevel.MEDIUM, 0),
            low_count=urgency_counts.get(UrgencyLevel.LOW, 0),
            channels=channels,
            top_senders=top_senders,
        )

    async def clear(self):
        """Clear all queued messages."""
        count = len(self._cache)
        self._cache = []

        # Clear Redis
        if self.redis_client:
            await self.redis_client.delete("shield:message_queue")

        logger.info(f"🗑️ Cleared {count} queued messages")

    async def mark_delivered(self, message_id: str):
        """Mark a message as delivered."""
        for qm in self._cache:
            if qm.message.id == message_id:
                qm.delivered = True
                logger.debug(f"Marked message {message_id} as delivered")
                break

    async def _evict_oldest_low_urgency(self):
        """Remove oldest LOW urgency message to make space."""
        low_urgency = [qm for qm in self._cache if qm.urgency == UrgencyLevel.LOW]

        if low_urgency:
            oldest = min(low_urgency, key=lambda qm: qm.queued_at)
            self._cache.remove(oldest)
            logger.debug(
                f"Evicted oldest LOW urgency message: {oldest.message.id} "
                f"(queued {oldest.queued_at})"
            )
        else:
            # If no LOW urgency, remove oldest MEDIUM
            medium = [qm for qm in self._cache if qm.urgency == UrgencyLevel.MEDIUM]
            if medium:
                oldest = min(medium, key=lambda qm: qm.queued_at)
                self._cache.remove(oldest)
                logger.warning(f"Evicted MEDIUM urgency message (queue full)")

    async def _persist_to_redis(self, queued: QueuedMessage):
        """Persist queued message to Redis."""
        if not self.redis_client:
            return

        try:
            # Serialize to JSON
            data = {
                "message_id": queued.message.id,
                "user": queued.message.user,
                "channel": queued.message.channel,
                "channel_type": queued.message.channel_type,
                "text": queued.message.text,  # Note: Only store if configured
                "timestamp": queued.message.timestamp.isoformat(),
                "urgency": queued.urgency.value,
                "queued_at": queued.queued_at.isoformat(),
            }

            # Add to Redis list
            await self.redis_client.rpush("shield:message_queue", json.dumps(data))

        except Exception as e:
            logger.error(f"Failed to persist to Redis: {e}")

    async def _load_from_redis(self):
        """Load queued messages from Redis on startup."""
        if not self.redis_client:
            return

        try:
            # Get all messages from Redis
            messages = await self.redis_client.lrange("shield:message_queue", 0, -1)

            for msg_json in messages:
                data = json.loads(msg_json)

                # Reconstruct SlackMessage
                message = SlackMessage(
                    id=data["message_id"],
                    user=data["user"],
                    channel=data["channel"],
                    channel_type=data["channel_type"],
                    text=data["text"],
                    timestamp=datetime.fromisoformat(data["timestamp"]),
                )

                # Reconstruct QueuedMessage
                queued = QueuedMessage(
                    message=message,
                    urgency=UrgencyLevel(data["urgency"]),
                    queued_at=datetime.fromisoformat(data["queued_at"]),
                    delivered=False,
                )

                self._cache.append(queued)

            logger.info(f"📥 Loaded {len(self._cache)} queued messages from Redis")

        except Exception as e:
            logger.error(f"Failed to load from Redis: {e}")
