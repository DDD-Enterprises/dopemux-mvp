"""
Shared Redis Caching Layer for ADHD Services

Provides TTL-based caching with invalidation strategies for improved performance
across all ADHD services. Uses the shared Redis connection pool.
"""

import asyncio
import json
import logging
import hashlib
import pickle
from typing import Any, Optional, Dict, Callable, Union
from functools import wraps

logger = logging.getLogger(__name__)


class RedisCache:
    """
    Redis-based caching layer with TTL and invalidation.

    Provides efficient caching for user profiles, workspace mappings,
    and frequent API responses across all ADHD services.
    """

    def __init__(self, default_ttl: int = 300):
        """
        Initialize Redis cache.

        Args:
            default_ttl: Default time-to-live in seconds (5 minutes)
        """
        self.default_ttl = default_ttl
        self.redis_pool = None

        # Cache key prefixes for organization
        self.prefixes = {
            "user_profile": "cache:user:profile:",
            "workspace_map": "cache:workspace:map:",
            "adhd_metrics": "cache:adhd:metrics:",
            "session_data": "cache:session:data:",
            "api_response": "cache:api:response:",
        }

        # Cache statistics
        self.hits = 0
        self.misses = 0
        self.sets = 0

    async def initialize(self):
        """Initialize Redis connection pool."""
        if not self.redis_pool:
            from .redis_pool import get_redis_pool
            self.redis_pool = await get_redis_pool()
        logger.info("Redis cache initialized")

    async def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache.

        Args:
            key: Cache key
            default: Default value if key not found

        Returns:
            Cached value or default
        """
        if not self.redis_pool:
            await self.initialize()

        try:
            async with self.redis_pool.get_client() as client:
                value = await client.get(key)
                if value is not None:
                    self.hits += 1
                    # Try to deserialize JSON, fallback to raw value
                    try:
                        return json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        return value
                else:
                    self.misses += 1
                    return default

        except Exception as e:
            logger.error(f"Cache get error for key '{key}': {e}")
            return default

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time-to-live in seconds (uses default if None)

        Returns:
            True if successful, False otherwise
        """
        if not self.redis_pool:
            await self.initialize()

        if ttl is None:
            ttl = self.default_ttl

        try:
            # Serialize value to JSON
            if isinstance(value, (dict, list, str, int, float, bool)):
                serialized_value = json.dumps(value)
            else:
                # Fallback to pickle for complex objects
                serialized_value = pickle.dumps(value)
                logger.warning(f"Using pickle serialization for key '{key}'")

            async with self.redis_pool.get_client() as client:
                result = await client.setex(key, ttl, serialized_value)
                if result:
                    self.sets += 1
                return bool(result)

        except Exception as e:
            logger.error(f"Cache set error for key '{key}': {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if key was deleted, False otherwise
        """
        if not self.redis_pool:
            await self.initialize()

        try:
            async with self.redis_pool.get_client() as client:
                result = await client.delete(key)
                return result > 0

        except Exception as e:
            logger.error(f"Cache delete error for key '{key}': {e}")
            return False

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key to check

        Returns:
            True if key exists, False otherwise
        """
        if not self.redis_pool:
            await self.initialize()

        try:
            async with self.redis_pool.get_client() as client:
                return await client.exists(key) > 0

        except Exception as e:
            logger.error(f"Cache exists error for key '{key}': {e}")
            return False

    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching a pattern.

        Args:
            pattern: Redis pattern (e.g., "cache:user:*")

        Returns:
            Number of keys deleted
        """
        if not self.redis_pool:
            await self.initialize()

        try:
            async with self.redis_pool.get_client() as client:
                # Get all keys matching pattern
                keys = await client.keys(pattern)
                if keys:
                    # Delete all matching keys
                    result = await client.delete(*keys)
                    logger.info(f"Invalidated {result} cache keys matching '{pattern}'")
                    return result
                return 0

        except Exception as e:
            logger.error(f"Cache invalidation error for pattern '{pattern}': {e}")
            return 0

    def make_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Create a standardized cache key.

        Args:
            prefix: Key prefix (from self.prefixes)
            *args: Positional arguments to include in key
            **kwargs: Keyword arguments to include in key

        Returns:
            Standardized cache key
        """
        # Start with prefix
        key_parts = [self.prefixes.get(prefix, prefix)]

        # Add positional args
        key_parts.extend(str(arg) for arg in args)

        # Add sorted keyword args
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            key_parts.extend(f"{k}:{v}" for k, v in sorted_kwargs)

        # Join and create hash for consistent length
        key_string = ":".join(key_parts)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()[:8]

        return f"{key_parts[0]}{key_hash}"

    async def cached(self, ttl: Optional[int] = None, key_prefix: str = "api_response"):
        """
        Decorator for caching function results.

        Args:
            ttl: Cache TTL in seconds
            key_prefix: Cache key prefix

        Returns:
            Decorated function with caching
        """
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key from function name and arguments
                cache_key = self.make_key(
                    key_prefix,
                    func.__name__,
                    *args,
                    **kwargs
                )

                # Try to get from cache first
                cached_result = await self.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cached_result

                # Execute function and cache result
                result = await func(*args, **kwargs)
                await self.set(cache_key, result, ttl)

                logger.debug(f"Cache miss for {func.__name__}, cached result")
                return result

            return wrapper
        return decorator

    def get_metrics(self) -> Dict[str, Any]:
        """Get cache performance metrics."""
        total_requests = self.hits + self.misses
        hit_rate = self.hits / max(total_requests, 1)

        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "hit_rate": round(hit_rate, 3),
            "total_requests": total_requests,
            "default_ttl": self.default_ttl,
        }

    async def clear_all(self) -> bool:
        """Clear all cached data (use with caution)."""
        try:
            async with self.redis_pool.get_client() as client:
                # Clear all cache keys
                for prefix in self.prefixes.values():
                    await self.invalidate_pattern(f"{prefix}*")

            logger.warning("All cache data cleared")
            return True

        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False


# Global cache instance
_cache_instance: Optional[RedisCache] = None

async def get_cache(default_ttl: int = 300) -> RedisCache:
    """Get global cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = RedisCache(default_ttl=default_ttl)
        await _cache_instance.initialize()
    return _cache_instance

async def cache_get(key: str, default: Any = None) -> Any:
    """Convenience function for cache get."""
    cache = await get_cache()
    return await cache.get(key, default)

async def cache_set(key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """Convenience function for cache set."""
    cache = await get_cache()
    return await cache.set(key, value, ttl)

async def cache_delete(key: str) -> bool:
    """Convenience function for cache delete."""
    cache = await get_cache()
    return await cache.delete(key)

async def cache_metrics() -> Dict[str, Any]:
    """Get cache performance metrics."""
    cache = await get_cache()
    return cache.get_metrics()