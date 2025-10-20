#!/usr/bin/env python3
"""
Redis Cache Layer for Task-Orchestrator
========================================

High-performance caching layer for Component 5 query endpoints with ADHD-aware TTLs.

**Performance Impact**:
- Cache hit: ~1.76ms (from Serena benchmarks)
- Cache miss: ~100ms+ (full ConPort query)
- Expected hit rate: 80%+
- Latency reduction: 50-100ms per cached query

**ADHD-Optimized TTLs**:
- ADHD state: 30s (matches attention check frequency)
- Task lists: 10s (high-change frequency)
- Session info: 60s (stable during sessions)
- Sprint data: 300s (5min, rarely changes)

**Architecture**:
Task-Orchestrator → RedisCache → ConPort MCP (on cache miss)
"""

import redis.asyncio as redis
import json
import logging
import os
from typing import Optional, Any, Dict, List
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_DB = int(os.getenv("REDIS_DB_CACHE", "1"))  # Use DB 1 for cache (DB 0 for coordination)

# ADHD-aware TTLs (seconds)
TTL_ADHD_STATE = 30      # 30s - attention check frequency
TTL_TASK_LIST = 10       # 10s - tasks change frequently
TTL_TASK_DETAIL = 60     # 60s - stable during work
TTL_SESSION = 60         # 60s - session duration
TTL_SPRINT = 300         # 5min - sprint data rarely changes
TTL_RECOMMENDATIONS = 30 # 30s - ADHD-aware suggestions


class RedisCache:
    """
    High-performance Redis cache for Task-Orchestrator queries.

    **Features**:
    - ADHD-aware TTLs for different data types
    - Automatic JSON serialization
    - Workspace isolation (key prefixing)
    - Cache invalidation on state changes
    - Performance metrics tracking
    """

    def __init__(self, workspace_id: str):
        """
        Initialize Redis cache for workspace.

        Args:
            workspace_id: Workspace ID for key prefixing
        """
        self.workspace_id = workspace_id
        self.workspace_hash = hashlib.md5(workspace_id.encode()).hexdigest()[:8]
        self.redis_client: Optional[redis.Redis] = None
        self.enabled = os.getenv("USE_REDIS_CACHE", "true").lower() == "true"

        # Performance metrics
        self.hits = 0
        self.misses = 0
        self.errors = 0

    async def connect(self):
        """Connect to Redis server."""
        if not self.enabled:
            logger.info("🔕 Redis cache disabled (USE_REDIS_CACHE=false)")
            return

        try:
            self.redis_client = redis.Redis.from_url(
                REDIS_URL,
                password=REDIS_PASSWORD,
                db=REDIS_DB,
                decode_responses=True
            )

            # Test connection
            await self.redis_client.ping()
            logger.info(f"✅ Redis cache connected (workspace: {self.workspace_hash})")

        except Exception as e:
            logger.warning(f"⚠️  Redis cache connection failed: {e}")
            self.enabled = False
            self.redis_client = None

    async def close(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("📪 Redis cache disconnected")

    def _make_key(self, category: str, identifier: str = "") -> str:
        """
        Generate cache key with workspace prefix.

        Args:
            category: Data category (adhd_state, task_list, session, etc.)
            identifier: Optional identifier (task_id, sprint_id, etc.)

        Returns:
            Prefixed cache key
        """
        if identifier:
            return f"cache:{self.workspace_hash}:{category}:{identifier}"
        return f"cache:{self.workspace_hash}:{category}"

    async def get(self, category: str, identifier: str = "") -> Optional[Any]:
        """
        Get value from cache.

        Args:
            category: Data category
            identifier: Optional identifier

        Returns:
            Cached value or None if not found
        """
        if not self.enabled or not self.redis_client:
            return None

        try:
            key = self._make_key(category, identifier)
            value = await self.redis_client.get(key)

            if value:
                self.hits += 1
                logger.debug(f"🎯 Cache hit: {category}/{identifier}")
                return json.loads(value)
            else:
                self.misses += 1
                logger.debug(f"❌ Cache miss: {category}/{identifier}")
                return None

        except Exception as e:
            self.errors += 1
            logger.error(f"Cache get error: {e}")
            return None

    async def set(
        self,
        category: str,
        value: Any,
        identifier: str = "",
        ttl: Optional[int] = None
    ):
        """
        Set value in cache with TTL.

        Args:
            category: Data category
            value: Value to cache (will be JSON serialized)
            identifier: Optional identifier
            ttl: Time-to-live in seconds (defaults to category-specific TTL)
        """
        if not self.enabled or not self.redis_client:
            return

        try:
            key = self._make_key(category, identifier)

            # Auto-select TTL based on category
            if ttl is None:
                ttl = self._get_default_ttl(category)

            # Serialize and cache
            serialized = json.dumps(value, default=str)  # default=str handles datetime
            await self.redis_client.setex(key, ttl, serialized)

            logger.debug(f"💾 Cached: {category}/{identifier} (TTL: {ttl}s)")

        except Exception as e:
            self.errors += 1
            logger.error(f"Cache set error: {e}")

    def _get_default_ttl(self, category: str) -> int:
        """Get default TTL for category."""
        ttl_map = {
            "adhd_state": TTL_ADHD_STATE,
            "task_list": TTL_TASK_LIST,
            "task_detail": TTL_TASK_DETAIL,
            "session": TTL_SESSION,
            "sprint": TTL_SPRINT,
            "recommendations": TTL_RECOMMENDATIONS
        }
        return ttl_map.get(category, 60)  # Default 60s

    async def invalidate(self, category: str, identifier: str = ""):
        """
        Invalidate cache entry.

        Args:
            category: Data category to invalidate
            identifier: Optional identifier
        """
        if not self.enabled or not self.redis_client:
            return

        try:
            key = self._make_key(category, identifier)
            await self.redis_client.delete(key)
            logger.debug(f"🗑️  Invalidated: {category}/{identifier}")

        except Exception as e:
            logger.error(f"Cache invalidate error: {e}")

    async def invalidate_pattern(self, pattern: str):
        """
        Invalidate all keys matching pattern.

        Args:
            pattern: Redis key pattern (e.g., "task_*")
        """
        if not self.enabled or not self.redis_client:
            return

        try:
            full_pattern = f"cache:{self.workspace_hash}:{pattern}"
            keys = await self.redis_client.keys(full_pattern)

            if keys:
                await self.redis_client.delete(*keys)
                logger.debug(f"🗑️  Invalidated {len(keys)} keys matching: {pattern}")

        except Exception as e:
            logger.error(f"Cache invalidate pattern error: {e}")

    async def get_metrics(self) -> Dict[str, Any]:
        """
        Get cache performance metrics.

        Returns:
            Dict with hits, misses, hit_rate, errors
        """
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0.0

        return {
            "hits": self.hits,
            "misses": self.misses,
            "total_requests": total_requests,
            "hit_rate": f"{hit_rate:.1f}%",
            "errors": self.errors,
            "enabled": self.enabled
        }

    async def flush_workspace(self):
        """Flush all cache entries for this workspace."""
        if not self.enabled or not self.redis_client:
            return

        try:
            pattern = f"cache:{self.workspace_hash}:*"
            keys = await self.redis_client.keys(pattern)

            if keys:
                await self.redis_client.delete(*keys)
                logger.info(f"🗑️  Flushed {len(keys)} cache entries for workspace")

        except Exception as e:
            logger.error(f"Cache flush error: {e}")


class CacheInvalidator:
    """
    Automatic cache invalidation on state changes.

    **Invalidation Rules**:
    - Task status change → invalidate task_detail, task_list
    - ADHD state change → invalidate adhd_state, recommendations
    - Session state change → invalidate session
    - Sprint change → invalidate sprint, task_list
    """

    def __init__(self, cache: RedisCache):
        """
        Initialize cache invalidator.

        Args:
            cache: RedisCache instance
        """
        self.cache = cache

    async def on_task_status_change(self, task_id: str):
        """Invalidate cache when task status changes."""
        await self.cache.invalidate("task_detail", task_id)
        await self.cache.invalidate("task_list")
        logger.debug(f"🔄 Invalidated cache: task {task_id} status changed")

    async def on_adhd_state_change(self):
        """Invalidate cache when ADHD state changes."""
        await self.cache.invalidate("adhd_state")
        await self.cache.invalidate("recommendations")
        logger.debug("🔄 Invalidated cache: ADHD state changed")

    async def on_session_change(self):
        """Invalidate cache when session state changes."""
        await self.cache.invalidate("session")
        logger.debug("🔄 Invalidated cache: session changed")

    async def on_sprint_change(self):
        """Invalidate cache when sprint changes."""
        await self.cache.invalidate("sprint")
        await self.cache.invalidate("task_list")
        logger.debug("🔄 Invalidated cache: sprint changed")

    async def on_task_list_change(self):
        """Invalidate cache when task list changes (new task, delete, etc.)."""
        await self.cache.invalidate("task_list")
        await self.cache.invalidate_pattern("task_detail:*")
        logger.debug("🔄 Invalidated cache: task list changed")
