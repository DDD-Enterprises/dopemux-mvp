"""
Shared Redis Connection Pool for ADHD Services

Provides a singleton Redis connection pool with proper configuration,
connection reuse, and performance monitoring across all ADHD services.
"""

import asyncio
import logging
import os
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool

logger = logging.getLogger(__name__)


class RedisConnectionPool:
    """
    Singleton Redis connection pool for efficient resource usage.

    Provides connection pooling, automatic reconnection, and monitoring
    across all ADHD services to prevent connection overhead.
    """

    _instance: Optional['RedisConnectionPool'] = None
    _lock = asyncio.Lock()

    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://redis-primary:6379")
        self.pool: Optional[ConnectionPool] = None
        self.client: Optional[redis.Redis] = None
        self.connection_count = 0
        self.max_connections = int(os.getenv("REDIS_MAX_CONNECTIONS", "20"))
        self.connection_timeout = float(os.getenv("REDIS_CONNECTION_TIMEOUT", "5.0"))
        self.retry_on_timeout = os.getenv("REDIS_RETRY_ON_TIMEOUT", "true").lower() == "true"

        # Monitoring
        self.operations_count = 0
        self.errors_count = 0

    @classmethod
    async def get_instance(cls) -> 'RedisConnectionPool':
        """
        Get singleton instance of Redis connection pool.

        Thread-safe singleton pattern for connection pool sharing.
        """
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
                    await cls._instance.initialize()
        return cls._instance

    async def initialize(self):
        """Initialize Redis connection pool."""
        try:
            # Parse Redis URL
            parsed_url = redis.from_url(self.redis_url)

            # Create connection pool with optimized settings
            self.pool = ConnectionPool.from_url(
                self.redis_url,
                max_connections=self.max_connections,
                decode_responses=True,
                retry_on_timeout=self.retry_on_timeout,
                socket_timeout=self.connection_timeout,
                socket_connect_timeout=self.connection_timeout,
                health_check_interval=30  # Health check every 30 seconds
            )

            # Create client from pool
            self.client = redis.Redis(connection_pool=self.pool)

            # Test connection
            await self.client.ping()

            logger.info("Redis connection pool initialized")
            logger.info(f"Max connections: {self.max_connections}")
            logger.info(f"Connection timeout: {self.connection_timeout}s")

        except Exception as e:
            logger.error(f"Failed to initialize Redis connection pool: {e}")
            raise

    async def close(self):
        """Close connection pool and cleanup resources."""
        if self.client:
            await self.client.close()
            self.client = None

        if self.pool:
            await self.pool.disconnect()
            self.pool = None

        logger.info("Redis connection pool closed")

    @asynccontextmanager
    async def get_client(self):
        """
        Context manager for getting a Redis client.

        Ensures proper connection management and monitoring.
        """
        if not self.client:
            await self.initialize()

        try:
            yield self.client
        except Exception as e:
            self.errors_count += 1
            logger.error(f"Redis operation error: {e}")
            raise

    async def execute_command(self, command: str, *args, **kwargs):
        """
        Execute Redis command with monitoring.

        Args:
            command: Redis command name
            *args: Command arguments
            **kwargs: Command keyword arguments

        Returns:
            Command result
        """
        async with self.get_client() as client:
            self.operations_count += 1

            try:
                method = getattr(client, command.lower())
                result = await method(*args, **kwargs)
                return result

            except Exception as e:
                self.errors_count += 1
                logger.error(f"Redis command '{command}' failed: {e}")
                raise

    async def get_metrics(self) -> Dict[str, Any]:
        """Get connection pool metrics."""
        pool_stats = {}

        if self.pool:
            # Get pool statistics
            pool_stats = {
                "max_connections": self.max_connections,
                "total_connections_created": getattr(self.pool, '_created_connections', 0),
                "available_connections": len(getattr(self.pool, '_available_connections', [])),
                "in_use_connections": len(getattr(self.pool, '_in_use_connections', [])),
            }

        return {
            "operations_count": self.operations_count,
            "errors_count": self.errors_count,
            "error_rate": self.errors_count / max(self.operations_count, 1),
            "pool_stats": pool_stats,
            "redis_url": self.redis_url.replace(self._extract_password(), "***"),  # Hide password
        }

    def _extract_password(self) -> str:
        """Extract password from Redis URL for hiding in logs."""
        try:
            if "@" in self.redis_url and "://" in self.redis_url:
                # Extract password part
                auth_part = self.redis_url.split("://")[1].split("@")[0]
                if ":" in auth_part:
                    return auth_part.split(":")[1]
        except Exception as e:
            logger.error(f"Error: {e}")
        return ""

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on Redis connection."""
        try:
            async with self.get_client() as client:
                start_time = asyncio.get_event_loop().time()
                await client.ping()
                response_time = asyncio.get_event_loop().time() - start_time

                return {
                    "status": "healthy",
                    "response_time_ms": round(response_time * 1000, 2),
                    "connection_pool_size": self.max_connections,
                }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "connection_pool_size": self.max_connections,
            }


            logger.error(f"Error: {e}")
# Global instance for easy access
_pool_instance: Optional[RedisConnectionPool] = None

async def get_redis_pool() -> RedisConnectionPool:
    """Convenience function to get Redis connection pool instance."""
    return await RedisConnectionPool.get_instance()

async def get_redis_client():
    """Convenience context manager for Redis client access."""
    pool = await get_redis_pool()
    return pool.get_client()

async def redis_health_check() -> Dict[str, Any]:
    """Convenience function for Redis health check."""
    pool = await get_redis_pool()
    return await pool.health_check()

async def redis_metrics() -> Dict[str, Any]:
    """Convenience function for Redis metrics."""
    pool = await get_redis_pool()
    return await pool.get_metrics()