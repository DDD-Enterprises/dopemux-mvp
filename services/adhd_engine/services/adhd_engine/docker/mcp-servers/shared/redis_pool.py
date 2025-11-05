"""
Shared Redis connection pool for Dopemux MCP servers.

Provides a singleton Redis connection pool that can be shared across multiple MCP servers.
"""

import os
import redis.asyncio as redis
from typing import Optional


_redis_pool: Optional[redis.ConnectionPool] = None


def get_redis_pool() -> redis.ConnectionPool:
    """
    Get or create a shared Redis connection pool.

    Returns:
        Redis connection pool instance
    """
    global _redis_pool

    if _redis_pool is None:
        # Get Redis URL from environment, fallback to default
        redis_url = os.getenv("REDIS_URL", "redis://redis-primary:6379")

        # Create connection pool
        _redis_pool = redis.ConnectionPool.from_url(
            redis_url,
            decode_responses=True,
            max_connections=20,
            retry_on_timeout=True
        )

    return _redis_pool


async def get_redis_client() -> redis.Redis:
    """
    Get a Redis client from the shared pool.

    Returns:
        Redis client instance
    """
    pool = get_redis_pool()
    return redis.Redis(connection_pool=pool)