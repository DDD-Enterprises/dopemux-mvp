"""
Persistent Data Storage Layer for ADHD Services

Provides PostgreSQL integration for long-term data persistence
with Redis caching layer for high-performance access patterns.
"""

import asyncio
import logging
import json
from typing import Dict, Any, List, Optional, TypeVar, Generic
from datetime import datetime, timezone
from contextlib import asynccontextmanager
import os

logger = logging.getLogger(__name__)

T = TypeVar('T')


class PostgreSQLStorage:
    """
    PostgreSQL storage backend for persistent data.

    Handles long-term data storage, migrations, and complex queries
    for ADHD services requiring data persistence.
    """

    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize PostgreSQL storage.

        Args:
            connection_string: PostgreSQL connection string
        """
        self.connection_string = connection_string or os.getenv(
            "DATABASE_URL",
            "postgresql://dopemux_age:dopemux_age_dev_password@dopemux-postgres-age:5432/dopemux_knowledge_graph"
        )
        self.pool = None
        self.initialized = False

    async def initialize(self):
        """Initialize PostgreSQL connection pool and schema."""
        if self.initialized:
            return

        try:
            # Import asyncpg for PostgreSQL
            import asyncpg

            # Create connection pool
            self.pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=5,
                max_size=20,
                command_timeout=60,
                init=self._init_connection
            )

            # Run schema migrations
            await self._run_migrations()

            self.initialized = True
            logger.info("PostgreSQL storage initialized")

        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL storage: {e}")
            raise

    async def close(self):
        """Close PostgreSQL connection pool."""
        if self.pool:
            await self.pool.close()
            self.pool = None
            self.initialized = False
            logger.info("PostgreSQL storage closed")

    async def _init_connection(self, conn):
        """Initialize connection with settings."""
        await conn.set_type_codec(
            'json',
            encoder=json.dumps,
            decoder=json.loads,
            schema='pg_catalog'
        )

    async def _run_migrations(self):
        """Run database schema migrations."""
        try:
            async with self.pool.acquire() as conn:
                # Create ADHD services schema
                await conn.execute("""
                    CREATE SCHEMA IF NOT EXISTS adhd_services;
                """)

                # User profiles table
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS adhd_services.user_profiles (
                        user_id VARCHAR(255) PRIMARY KEY,
                        profile_data JSONB NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                """)

                # Service metrics table
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS adhd_services.service_metrics (
                        service_name VARCHAR(255) NOT NULL,
                        metric_name VARCHAR(255) NOT NULL,
                        metric_value JSONB,
                        timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        PRIMARY KEY (service_name, metric_name, timestamp)
                    );
                """)

                # Activity logs table
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS adhd_services.activity_logs (
                        id SERIAL PRIMARY KEY,
                        user_id VARCHAR(255),
                        activity_type VARCHAR(255),
                        activity_data JSONB,
                        timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                """)

                # Decision logs table (integration with ConPort)
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS adhd_services.decision_logs (
                        decision_id VARCHAR(255) PRIMARY KEY,
                        summary TEXT,
                        rationale TEXT,
                        implementation_details JSONB,
                        tags TEXT[],
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                """)

                # Create indexes for performance
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id
                    ON adhd_services.user_profiles(user_id);
                """)

                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_service_metrics_service_name
                    ON adhd_services.service_metrics(service_name);
                """)

                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_activity_logs_user_id
                    ON adhd_services.activity_logs(user_id);
                """)

                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_decision_logs_tags
                    ON adhd_services.decision_logs USING GIN(tags);
                """)

                logger.info("Database schema migrations completed")

        except Exception as e:
            logger.error(f"Database migration failed: {e}")
            raise

    async def store_user_profile(self, user_id: str, profile_data: Dict[str, Any]):
        """
        Store or update user profile.

        Args:
            user_id: User identifier
            profile_data: Profile data
        """
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO adhd_services.user_profiles (user_id, profile_data, updated_at)
                VALUES ($1, $2, NOW())
                ON CONFLICT (user_id) DO UPDATE SET
                    profile_data = EXCLUDED.profile_data,
                    updated_at = NOW()
            """, user_id, json.dumps(profile_data))

    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve user profile.

        Args:
            user_id: User identifier

        Returns:
            Profile data or None if not found
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT profile_data FROM adhd_services.user_profiles
                WHERE user_id = $1
            """, user_id)

            if row:
                return json.loads(row['profile_data'])
            return None

    async def store_service_metric(self, service_name: str, metric_name: str, metric_value: Any):
        """
        Store service metric.

        Args:
            service_name: Service name
            metric_name: Metric name
            metric_value: Metric value (will be JSON serialized)
        """
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO adhd_services.service_metrics
                (service_name, metric_name, metric_value, timestamp)
                VALUES ($1, $2, $3, NOW())
            """, service_name, metric_name, json.dumps(metric_value))

    async def get_service_metrics(
        self,
        service_name: str,
        metric_name: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Retrieve service metrics.

        Args:
            service_name: Service name
            metric_name: Optional specific metric name
            limit: Maximum number of records to return

        Returns:
            List of metric records
        """
        async with self.pool.acquire() as conn:
            if metric_name:
                rows = await conn.fetch("""
                    SELECT * FROM adhd_services.service_metrics
                    WHERE service_name = $1 AND metric_name = $2
                    ORDER BY timestamp DESC
                    LIMIT $3
                """, service_name, metric_name, limit)
            else:
                rows = await conn.fetch("""
                    SELECT * FROM adhd_services.service_metrics
                    WHERE service_name = $1
                    ORDER BY timestamp DESC
                    LIMIT $2
                """, service_name, limit)

            return [dict(row) for row in rows]

    async def log_activity(self, user_id: str, activity_type: str, activity_data: Dict[str, Any]):
        """
        Log user activity.

        Args:
            user_id: User identifier
            activity_type: Type of activity
            activity_data: Activity details
        """
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO adhd_services.activity_logs
                (user_id, activity_type, activity_data, timestamp)
                VALUES ($1, $2, $3, NOW())
            """, user_id, activity_type, json.dumps(activity_data))

    async def get_activity_logs(
        self,
        user_id: Optional[str] = None,
        activity_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Retrieve activity logs.

        Args:
            user_id: Optional user filter
            activity_type: Optional activity type filter
            limit: Maximum records to return

        Returns:
            List of activity log records
        """
        async with self.pool.acquire() as conn:
            if user_id and activity_type:
                rows = await conn.fetch("""
                    SELECT * FROM adhd_services.activity_logs
                    WHERE user_id = $1 AND activity_type = $2
                    ORDER BY timestamp DESC
                    LIMIT $3
                """, user_id, activity_type, limit)
            elif user_id:
                rows = await conn.fetch("""
                    SELECT * FROM adhd_services.activity_logs
                    WHERE user_id = $1
                    ORDER BY timestamp DESC
                    LIMIT $2
                """, user_id, limit)
            elif activity_type:
                rows = await conn.fetch("""
                    SELECT * FROM adhd_services.activity_logs
                    WHERE activity_type = $1
                    ORDER BY timestamp DESC
                    LIMIT $2
                """, activity_type, limit)
            else:
                rows = await conn.fetch("""
                    SELECT * FROM adhd_services.activity_logs
                    ORDER BY timestamp DESC
                    LIMIT $1
                """, limit)

            return [dict(row) for row in rows]

    async def store_decision_log(self, decision_data: Dict[str, Any]):
        """
        Store decision log (integration with ConPort).

        Args:
            decision_data: Decision details
        """
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO adhd_services.decision_logs
                (decision_id, summary, rationale, implementation_details, tags, created_at)
                VALUES ($1, $2, $3, $4, $5, NOW())
                ON CONFLICT (decision_id) DO UPDATE SET
                    summary = EXCLUDED.summary,
                    rationale = EXCLUDED.rationale,
                    implementation_details = EXCLUDED.implementation_details,
                    tags = EXCLUDED.tags
            """,
            decision_data['decision_id'],
            decision_data['summary'],
            decision_data.get('rationale'),
            json.dumps(decision_data.get('implementation_details', {})),
            decision_data.get('tags', [])
            )

    async def health_check(self) -> Dict[str, Any]:
        """Perform storage health check."""
        try:
            async with self.pool.acquire() as conn:
                # Simple query to test connectivity
                result = await conn.fetchval("SELECT COUNT(*) FROM adhd_services.user_profiles")

                return {
                    "status": "healthy",
                    "user_profiles_count": result,
                    "connection_pool_size": len(self.pool._holders) if hasattr(self.pool, '_holders') else 0
                }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


class UnifiedStorage:
    """
    Unified storage layer combining Redis cache and PostgreSQL persistence.

    Provides optimal data access patterns:
    - Redis for hot data and caching
    - PostgreSQL for persistence and complex queries
    """

    def __init__(self):
        self.redis_pool = None
        self.postgres = PostgreSQLStorage()

    async def initialize(self):
        """Initialize unified storage."""
        # Initialize Redis pool
        from .redis_pool import get_redis_pool
        self.redis_pool = await get_redis_pool()

        # Initialize PostgreSQL
        await self.postgres.initialize()

        logger.info("Unified storage initialized")

    async def close(self):
        """Close unified storage."""
        await self.postgres.close()
        logger.info("Unified storage closed")

    @asynccontextmanager
    async def user_profile(self, user_id: str):
        """
        Context manager for user profile with cache-first access.

        Args:
            user_id: User identifier

        Yields:
            Profile data (dict)
        """
        cache_key = f"user:profile:{user_id}"

        # Try cache first
        from .cache import get_cache
        cache = await get_cache()
        profile = await cache.get(cache_key)

        if profile is None:
            # Load from PostgreSQL
            profile = await self.postgres.get_user_profile(user_id)
            if profile:
                # Cache for 5 minutes
                await cache.set(cache_key, profile, ttl=300)

        # Yield profile (empty dict if not found)
        current_profile = profile or {}

        try:
            yield current_profile
        finally:
            # Save back to storage if modified
            if current_profile != (profile or {}):
                await self.postgres.store_user_profile(user_id, current_profile)
                await cache.set(cache_key, current_profile, ttl=300)

    async def log_activity(self, user_id: str, activity_type: str, activity_data: Dict[str, Any]):
        """
        Log activity to PostgreSQL (no caching needed for logs).

        Args:
            user_id: User identifier
            activity_type: Activity type
            activity_data: Activity details
        """
        await self.postgres.log_activity(user_id, activity_type, activity_data)

    async def store_service_metric(self, service_name: str, metric_name: str, metric_value: Any):
        """
        Store service metric to PostgreSQL.

        Args:
            service_name: Service name
            metric_name: Metric name
            metric_value: Metric value
        """
        await self.postgres.store_service_metric(service_name, metric_name, metric_value)

    async def health_check(self) -> Dict[str, Any]:
        """Unified health check."""
        postgres_health = await self.postgres.health_check()

        redis_health = {"status": "unknown"}
        if self.redis_pool:
            try:
                redis_health = await self.redis_pool.health_check()
            except Exception as e:
                redis_health = {"status": "error", "error": str(e)}

        return {
            "overall_status": "healthy" if postgres_health["status"] == "healthy" and redis_health["status"] == "healthy" else "degraded",
            "postgres": postgres_health,
            "redis": redis_health
        }


# Global storage instance
_storage: Optional[UnifiedStorage] = None

async def get_storage() -> UnifiedStorage:
    """Get global unified storage instance."""
    global _storage
    if _storage is None:
        _storage = UnifiedStorage()
        await _storage.initialize()
    return _storage

async def storage_health_check() -> Dict[str, Any]:
    """Convenience function for storage health check."""
    storage = await get_storage()
    return await storage.health_check()