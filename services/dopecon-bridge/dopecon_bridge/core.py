"""
DopeconBridge Core - Database and Cache managers.

Extracted from main.py lines 229-309.
"""

import logging
from typing import Optional

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .config import settings
from .models import Base


logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages PostgreSQL connections for shared state."""

    def __init__(self):
        self.engine = None
        self.session_factory: Optional[async_sessionmaker] = None
        self._initialized = False

    async def initialize(self):
        """Initialize database connection and create tables."""
        if self._initialized:
            return
            
        try:
            self.engine = create_async_engine(
                settings.postgres_url,
                echo=False,
                pool_size=settings.db_pool_size,
                max_overflow=settings.db_max_overflow,
                pool_pre_ping=True
            )

            self.session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )

            # Create tables if they don't exist
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            self._initialized = True
            logger.info("✅ Database connection established")

        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise

    async def get_session(self) -> AsyncSession:
        """Get database session."""
        if not self.session_factory:
            raise RuntimeError("Database not initialized")
        return self.session_factory()

    async def close(self):
        """Close database connection."""
        if self.engine:
            await self.engine.dispose()
            self._initialized = False


class CacheManager:
    """Manages Redis connections for caching and session state."""

    def __init__(self):
        self.redis_client = None
        self._initialized = False

    async def initialize(self):
        """Initialize Redis connection."""
        if self._initialized:
            return
            
        try:
            self.redis_client = redis.from_url(
                settings.redis_url,
                password=settings.redis_password if settings.redis_password else None,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )

            # Test connection
            await self.redis_client.ping()
            self._initialized = True
            logger.info("✅ Redis connection established")

        except Exception as e:
            logger.error(f"❌ Redis initialization failed: {e}")
            raise

    async def get_client(self):
        """Get Redis client."""
        if not self.redis_client:
            raise RuntimeError("Redis not initialized")
        return self.redis_client

    async def close(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            self._initialized = False


# Global singleton instances
db_manager = DatabaseManager()
cache_manager = CacheManager()
