"""
Event Deduplication for DopeconBridge
Prevents duplicate event processing using content-based hashing

Features:
- SHA256 content hashing for event data
- Redis-backed deduplication with TTL
- Configurable deduplication window
- ADHD-optimized: Fast (<2ms), non-blocking
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class EventDeduplicator:
    """
    Content-based event deduplication using Redis.

    Uses SHA256 hashing of event data to detect duplicates within a time window.
    Duplicate events are silently dropped to prevent wasted processing.

    Example:
        deduplicator = EventDeduplicator(redis_client, ttl_seconds=300)

        if not await deduplicator.is_duplicate(event):
            await process_event(event)
            await deduplicator.mark_processed(event)
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        ttl_seconds: int = 300,
        key_prefix: str = "dedup"
    ):
        """
        Initialize event deduplicator.

        Args:
            redis_client: Async Redis client for storing hashes
            ttl_seconds: Time window for deduplication (default: 5 minutes)
            key_prefix: Redis key prefix for namespacing (default: "dedup")
        """
        self.redis_client = redis_client
        self.ttl_seconds = ttl_seconds
        self.key_prefix = key_prefix

        # Metrics
        self.total_checks = 0
        self.duplicates_found = 0
        self.errors = 0

    def _compute_content_hash(self, event_data: Dict[str, Any]) -> str:
        """
        Compute SHA256 hash of event content.

        Uses stable JSON serialization to ensure consistent hashing.
        Excludes timestamp to focus on content similarity.

        Args:
            event_data: Event data dictionary

        Returns:
            Hex-encoded SHA256 hash
        """
        # Create hashable content (exclude timestamp for content-based dedup)
        hashable_content = {
            "type": event_data.get("type", ""),
            "data": event_data.get("data", {}),
            "source": event_data.get("source", "")
        }

        # Stable JSON serialization
        json_str = json.dumps(hashable_content, sort_keys=True, separators=(',', ':'))

        # SHA256 hash
        hash_obj = hashlib.sha256(json_str.encode('utf-8'))
        return hash_obj.hexdigest()

    def _make_redis_key(self, content_hash: str) -> str:
        """
        Create Redis key for content hash.

        Args:
            content_hash: SHA256 hash of event content

        Returns:
            Redis key with namespace prefix
        """
        return f"{self.key_prefix}:{content_hash}"

    async def is_duplicate(self, event_data: Dict[str, Any]) -> bool:
        """
        Check if event is a duplicate within TTL window.

        Args:
            event_data: Event data dictionary with type, data, source

        Returns:
            True if duplicate (hash exists in Redis), False otherwise
        """
        self.total_checks += 1

        try:
            # Compute content hash
            content_hash = self._compute_content_hash(event_data)
            redis_key = self._make_redis_key(content_hash)

            # Check if hash exists in Redis
            exists = await self.redis_client.exists(redis_key)

            if exists:
                self.duplicates_found += 1
                logger.debug(
                    f"Duplicate event detected: {event_data.get('type')} "
                    f"(hash: {content_hash[:8]}...)"
                )
                return True

            return False

        except Exception as e:
            self.errors += 1
            logger.error(f"Error checking duplicate: {e}")
            # Fail open - treat as non-duplicate to avoid blocking events
            return False

    async def mark_processed(self, event_data: Dict[str, Any]) -> bool:
        """
        Mark event as processed by storing its hash in Redis with TTL.

        Args:
            event_data: Event data dictionary

        Returns:
            True if successfully marked, False on error
        """
        try:
            # Compute content hash
            content_hash = self._compute_content_hash(event_data)
            redis_key = self._make_redis_key(content_hash)

            # Store hash with TTL
            await self.redis_client.set(
                redis_key,
                datetime.utcnow().isoformat(),
                ex=self.ttl_seconds
            )

            logger.debug(
                f"Marked event as processed: {event_data.get('type')} "
                f"(hash: {content_hash[:8]}..., TTL: {self.ttl_seconds}s)"
            )
            return True

        except Exception as e:
            self.errors += 1
            logger.error(f"Error marking event as processed: {e}")
            return False

    async def check_and_mark(self, event_data: Dict[str, Any]) -> bool:
        """
        Combined check and mark operation (atomic-like).

        Checks if event is duplicate, and if not, marks it as processed.
        This is the recommended method for most use cases.

        Args:
            event_data: Event data dictionary

        Returns:
            True if event is NEW (not duplicate), False if duplicate
        """
        is_dup = await self.is_duplicate(event_data)

        if not is_dup:
            await self.mark_processed(event_data)
            return True  # New event

        return False  # Duplicate event

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get deduplication metrics.

        Returns:
            Dictionary with total_checks, duplicates_found, dedup_rate, errors
        """
        dedup_rate = (
            (self.duplicates_found / self.total_checks * 100)
            if self.total_checks > 0
            else 0.0
        )

        return {
            "total_checks": self.total_checks,
            "duplicates_found": self.duplicates_found,
            "dedup_rate_percent": round(dedup_rate, 2),
            "errors": self.errors
        }

    def reset_metrics(self):
        """Reset metrics counters."""
        self.total_checks = 0
        self.duplicates_found = 0
        self.errors = 0
