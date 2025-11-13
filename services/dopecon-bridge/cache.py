"""
Multi-Tier Caching System for DopeconBridge

Implements 3-tier caching strategy for optimal performance:
- Tier 1: Memory cache (5s TTL, <0.1ms access)
- Tier 2: Redis cache (60s TTL, ~2ms access)
- Tier 3: Database (permanent storage)

Features:
- Automatic tier population on cache miss
- Write-through to all tiers
- Pattern-based cache invalidation
- Cache hit rate tracking
- ADHD-optimized: Fast, transparent caching
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Set
from dataclasses import dataclass

import redis.asyncio as redis

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Single cache entry with metadata"""
    key: str
    value: Any
    created_at: float
    ttl_seconds: int

    def is_expired(self) -> bool:
        """Check if entry has expired"""
        if self.ttl_seconds <= 0:
            return False  # No expiry
        elapsed = time.time() - self.created_at
        return elapsed >= self.ttl_seconds


class MemoryCache:
    """
    In-memory cache tier (Tier 1).

    Features:
    - Fastest access (<0.1ms)
    - Short TTL (5 seconds)
    - LRU eviction when max size reached
    - No persistence across restarts
    """

    def __init__(self, max_size: int = 1000, default_ttl: int = 5):
        """
        Initialize memory cache.

        Args:
            max_size: Maximum number of entries (default: 1000)
            default_ttl: Default TTL in seconds (default: 5)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, CacheEntry] = {}
        self.access_order: list = []  # For LRU eviction

        # Metrics
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from memory cache.

        Args:
            key: Cache key

        Returns:
            Cached value if found and not expired, None otherwise
        """
        entry = self.cache.get(key)

        if entry is None:
            self.misses += 1
            return None

        # Check expiry
        if entry.is_expired():
            del self.cache[key]
            self.misses += 1
            return None

        # Update access order (LRU)
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)

        self.hits += 1
        return entry.value

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set value in memory cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: TTL in seconds (default: use default_ttl)
        """
        # Evict if at max size
        if len(self.cache) >= self.max_size and key not in self.cache:
            self._evict_lru()

        entry = CacheEntry(
            key=key,
            value=value,
            created_at=time.time(),
            ttl_seconds=ttl if ttl is not None else self.default_ttl
        )

        self.cache[key] = entry

        # Update access order
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)

    def delete(self, key: str):
        """Delete entry from memory cache"""
        if key in self.cache:
            del self.cache[key]
            if key in self.access_order:
                self.access_order.remove(key)

    def clear(self):
        """Clear all entries"""
        self.cache.clear()
        self.access_order.clear()

    def _evict_lru(self):
        """Evict least recently used entry"""
        if self.access_order:
            lru_key = self.access_order.pop(0)
            if lru_key in self.cache:
                del self.cache[lru_key]
                self.evictions += 1

    def get_metrics(self) -> Dict[str, Any]:
        """Get cache metrics"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0.0

        return {
            "tier": "memory",
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "hit_rate_percent": round(hit_rate, 2)
        }


class MultiTierCache:
    """
    Multi-tier caching system with automatic tier population.

    Tiers:
    1. Memory: Fastest (<0.1ms), shortest TTL (5s)
    2. Redis: Fast (~2ms), medium TTL (60s)
    3. Database: Permanent storage

    On read:
    - Check memory → Redis → Database
    - Populate higher tiers on miss (write-back)

    On write:
    - Write to all tiers (write-through)
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        database_client: Optional[Any] = None,
        memory_ttl: int = 5,
        redis_ttl: int = 60
    ):
        """
        Initialize multi-tier cache.

        Args:
            redis_client: Async Redis client
            database_client: Optional database client (for Tier 3)
            memory_ttl: Memory tier TTL in seconds (default: 5)
            redis_ttl: Redis tier TTL in seconds (default: 60)
        """
        self.memory = MemoryCache(max_size=1000, default_ttl=memory_ttl)
        self.redis_client = redis_client
        self.database_client = database_client
        self.redis_ttl = redis_ttl

        # Metrics
        self.redis_hits = 0
        self.redis_misses = 0
        self.db_hits = 0
        self.db_misses = 0

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache (checks all tiers).

        Args:
            key: Cache key

        Returns:
            Cached value if found, None otherwise
        """
        # Tier 1: Check memory
        value = self.memory.get(key)
        if value is not None:
            return value

        # Tier 2: Check Redis
        try:
            redis_value = await self.redis_client.get(key)
            if redis_value:
                self.redis_hits += 1

                # Deserialize
                value = json.loads(redis_value)

                # Populate memory tier (write-back)
                self.memory.set(key, value, ttl=self.memory.default_ttl)

                return value

            self.redis_misses += 1

        except Exception as e:
            logger.error(f"Redis cache error: {e}")
            self.redis_misses += 1

        # Tier 3: Check database (if available)
        if self.database_client:
            try:
                value = await self._get_from_database(key)
                if value is not None:
                    self.db_hits += 1

                    # Populate higher tiers (write-back)
                    await self.set(key, value, ttl=self.redis_ttl)

                    return value

                self.db_misses += 1

            except Exception as e:
                logger.error(f"Database cache error: {e}")
                self.db_misses += 1

        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set value in cache (write-through to all tiers).

        Args:
            key: Cache key
            value: Value to cache
            ttl: TTL for Redis tier (default: use redis_ttl)
        """
        # Tier 1: Memory
        self.memory.set(key, value, ttl=self.memory.default_ttl)

        # Tier 2: Redis
        try:
            serialized = json.dumps(value)
            ttl_seconds = ttl if ttl is not None else self.redis_ttl

            await self.redis_client.set(
                key,
                serialized,
                ex=ttl_seconds
            )

        except Exception as e:
            logger.error(f"Failed to set Redis cache: {e}")

        # Tier 3: Database (optional, for permanent caching)
        if self.database_client:
            try:
                await self._set_in_database(key, value)
            except Exception as e:
                logger.error(f"Failed to set database cache: {e}")

    async def delete(self, key: str):
        """Delete entry from all cache tiers"""
        # Memory
        self.memory.delete(key)

        # Redis
        try:
            await self.redis_client.delete(key)
        except Exception as e:
            logger.error(f"Failed to delete from Redis: {e}")

        # Database
        if self.database_client:
            try:
                await self._delete_from_database(key)
            except Exception as e:
                logger.error(f"Failed to delete from database: {e}")

    async def invalidate_pattern(self, pattern: str):
        """
        Invalidate all keys matching pattern.

        Args:
            pattern: Pattern to match (e.g., "pattern:*", "agent:metrics:*")
        """
        # Memory: Check all keys
        keys_to_delete = [
            k for k in list(self.memory.cache.keys())
            if self._matches_pattern(k, pattern)
        ]

        for key in keys_to_delete:
            self.memory.delete(key)

        # Redis: Use SCAN + DELETE
        try:
            cursor = 0
            while True:
                cursor, keys = await self.redis_client.scan(
                    cursor=cursor,
                    match=pattern,
                    count=100
                )

                if keys:
                    await self.redis_client.delete(*keys)

                if cursor == 0:
                    break

        except Exception as e:
            logger.error(f"Failed to invalidate Redis pattern: {e}")

        logger.info(f"Invalidated cache pattern: {pattern}")

    def _matches_pattern(self, key: str, pattern: str) -> bool:
        """Simple pattern matching (supports * wildcard)"""
        import re
        regex_pattern = pattern.replace("*", ".*")
        return bool(re.match(f"^{regex_pattern}$", key))

    async def _get_from_database(self, key: str) -> Optional[Any]:
        """Get value from database tier (placeholder)"""
        # Would query database for cached value
        # For now, not implemented (database caching optional)
        return None

    async def _set_in_database(self, key: str, value: Any):
        """Set value in database tier (placeholder)"""
        # Would store in database for permanent caching
        # For now, not implemented
        pass

    async def _delete_from_database(self, key: str):
        """Delete from database tier (placeholder)"""
        pass

    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive cache metrics"""
        memory_metrics = self.memory.get_metrics()

        redis_total = self.redis_hits + self.redis_misses
        redis_hit_rate = (
            (self.redis_hits / redis_total * 100)
            if redis_total > 0
            else 0.0
        )

        db_total = self.db_hits + self.db_misses
        db_hit_rate = (
            (self.db_hits / db_total * 100)
            if db_total > 0
            else 0.0
        )

        # Overall hit rate (any tier)
        total_requests = memory_metrics["hits"] + memory_metrics["misses"]
        memory_hit_rate = memory_metrics["hit_rate_percent"]

        # Combined hit rate: % of requests served from cache (any tier)
        total_cache_hits = memory_metrics["hits"] + self.redis_hits + self.db_hits
        overall_hit_rate = (
            (total_cache_hits / total_requests * 100)
            if total_requests > 0
            else 0.0
        )

        return {
            "memory": memory_metrics,
            "redis": {
                "hits": self.redis_hits,
                "misses": self.redis_misses,
                "hit_rate_percent": round(redis_hit_rate, 2)
            },
            "database": {
                "hits": self.db_hits,
                "misses": self.db_misses,
                "hit_rate_percent": round(db_hit_rate, 2)
            },
            "overall": {
                "total_requests": total_requests,
                "total_cache_hits": total_cache_hits,
                "hit_rate_percent": round(overall_hit_rate, 2),
                "target_hit_rate": 80.0
            }
        }

    def reset_metrics(self):
        """Reset all cache metrics"""
        self.memory.hits = 0
        self.memory.misses = 0
        self.memory.evictions = 0
        self.redis_hits = 0
        self.redis_misses = 0
        self.db_hits = 0
        self.db_misses = 0
