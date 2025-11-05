"""
Shared Redis-based cache for Dopemux MCP servers.

Provides caching functionality using the shared Redis pool.
"""

import json
import hashlib
from typing import Any, Optional
from redis_pool import get_redis_client


class RedisCache:
    """Redis-based cache implementation."""

    def __init__(self, prefix: str = "dopemux"):
        self.prefix = prefix
        self._client = None

    async def _get_client(self):
        """Get Redis client instance."""
        if self._client is None:
            self._client = await get_redis_client()
        return self._client

    def _make_key(self, key: str) -> str:
        """Create a prefixed cache key."""
        return f"{self.prefix}:{key}"

    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        client = await self._get_client()
        cache_key = self._make_key(key)

        try:
            value = await client.get(cache_key)
            if value:
                return json.loads(value)
        except Exception:
            # Cache miss or error
            pass

        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set a value in cache.

        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl: Time to live in seconds (optional)

        Returns:
            True if successful, False otherwise
        """
        client = await self._get_client()
        cache_key = self._make_key(key)

        try:
            json_value = json.dumps(value)
            if ttl:
                await client.setex(cache_key, ttl, json_value)
            else:
                await client.set(cache_key, json_value)
            return True
        except Exception:
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete a value from cache.

        Args:
            key: Cache key

        Returns:
            True if successful, False otherwise
        """
        client = await self._get_client()
        cache_key = self._make_key(key)

        try:
            await client.delete(cache_key)
            return True
        except Exception:
            return False

    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        client = await self._get_client()
        cache_key = self._make_key(key)

        try:
            return bool(await client.exists(cache_key))
        except Exception:
            return False


# Global cache instance
_cache_instance: Optional[RedisCache] = None


def get_cache() -> RedisCache:
    """
    Get the global cache instance.

    Returns:
        RedisCache instance
    """
    global _cache_instance

    if _cache_instance is None:
        _cache_instance = RedisCache()

    return _cache_instance