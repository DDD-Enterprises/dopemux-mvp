"""
Shared cache implementation for MCP servers
"""
import os
import redis.asyncio as redis
from typing import Any, Optional

class RedisCache:
    """Redis-based cache with async operations."""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            value = await self.redis.get(key)
            return value
        except Exception:
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL."""
        try:
            if ttl:
                return await self.redis.setex(key, ttl, str(value))
            else:
                return await self.redis.set(key, str(value))
        except Exception:
            return False

def get_cache() -> RedisCache:
    """Get cache instance."""
    from redis_pool import get_redis_client
    redis_client = get_redis_client()
    return RedisCache(redis_client)
