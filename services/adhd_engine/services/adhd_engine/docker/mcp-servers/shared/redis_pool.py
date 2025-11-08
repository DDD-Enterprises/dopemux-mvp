"""
Shared Redis pool for MCP servers
"""
import os
import redis.asyncio as redis
from typing import Optional

_pool: Optional[redis.ConnectionPool] = None

def get_redis_pool() -> redis.ConnectionPool:
    """Get or create Redis connection pool."""
    global _pool
    if _pool is None:
        redis_url = os.getenv("REDIS_URL", "redis://redis-primary:6379")
        _pool = redis.ConnectionPool.from_url(redis_url, decode_responses=True)
    return _pool

def get_redis_client() -> redis.Redis:
    """Get Redis client from pool."""
    pool = get_redis_pool()
    return redis.Redis(connection_pool=pool)
