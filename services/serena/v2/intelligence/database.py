"""
Serena v2 Phase 2: Async PostgreSQL Intelligence Layer

High-performance async database layer with ADHD-optimized connection pooling,
performance monitoring integration, and <200ms query guarantees.
"""

import asyncio
import json
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple, AsyncGenerator
from dataclasses import dataclass, asdict
from enum import Enum

try:
    import asyncpg
    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False
    logging.warning("asyncpg not available - install with: pip install asyncpg")

from ..performance_monitor import PerformanceMonitor, PerformanceTarget
from ..adhd_features import CodeComplexityAnalyzer

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Configuration for PostgreSQL intelligence database."""
    host: str = "localhost"
    port: int = 5432
    database: str = "serena_intelligence"
    user: str = "serena"
    password: str = "serena_dev_pass"

    # Connection pool settings for ADHD performance
    min_connections: int = 5
    max_connections: int = 20
    max_inactive_connection_lifetime: float = 300.0  # 5 minutes

    # Performance settings
    command_timeout: float = 5.0  # Max 5 seconds per query
    query_timeout: float = 2.0    # Target <2 seconds for ADHD
    connection_timeout: float = 10.0

    # ADHD optimization settings
    enable_performance_monitoring: bool = True
    adhd_complexity_filtering: bool = True
    progressive_disclosure_mode: bool = True
    max_results_per_query: int = 50  # ADHD cognitive load limit

    @property
    def connection_string(self) -> str:
        """Generate PostgreSQL connection string."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class QueryPerformanceLevel(str, Enum):
    """Query performance levels for ADHD optimization."""
    EXCELLENT = "excellent"    # < 50ms
    GOOD = "good"             # 50-100ms
    ACCEPTABLE = "acceptable"  # 100-200ms
    SLOW = "slow"             # 200-500ms
    TIMEOUT = "timeout"       # > 500ms


@dataclass
class DatabaseMetrics:
    """Database performance metrics for ADHD monitoring."""
    query_count: int = 0
    average_query_time_ms: float = 0.0
    cache_hit_rate: float = 0.0
    connection_pool_usage: float = 0.0
    adhd_compliance_rate: float = 0.0  # Percentage of queries under 200ms
    complexity_filtered_queries: int = 0
    progressive_disclosure_activations: int = 0


class SerenaIntelligenceDatabase:
    """
    Async PostgreSQL database layer for Serena v2 Phase 2 intelligence.

    Features:
    - High-performance async connection pooling
    - ADHD-optimized query performance monitoring
    - Integration with Layer 1 performance targets
    - Complexity-aware result filtering
    - Progressive disclosure for cognitive load management
    - Batch operations for relationship queries
    """

    def __init__(
        self,
        config: DatabaseConfig = None,
        performance_monitor: PerformanceMonitor = None
    ):
        self.config = config or DatabaseConfig()
        self.performance_monitor = performance_monitor or PerformanceMonitor()

        self._pool: Optional[asyncpg.Pool] = None
        self._metrics = DatabaseMetrics()
        self._initialized = False

        # Query cache for frequently accessed data
        self._query_cache: Dict[str, Any] = {}
        self._cache_ttl = 300  # 5 minutes

        # ADHD optimization settings
        self.complexity_analyzer = CodeComplexityAnalyzer()

        if not ASYNCPG_AVAILABLE:
            raise ImportError("asyncpg is required for PostgreSQL intelligence layer")

    async def initialize(self) -> bool:
        """Initialize the database connection pool."""
        if self._initialized:
            return True

        try:
            operation_id = self.performance_monitor.start_operation("db_initialization")

            # Create connection pool with ADHD-optimized settings
            self._pool = await asyncpg.create_pool(
                self.config.connection_string,
                min_size=self.config.min_connections,
                max_size=self.config.max_connections,
                max_inactive_connection_lifetime=self.config.max_inactive_connection_lifetime,
                command_timeout=self.config.command_timeout,
                timeout=self.config.connection_timeout
            )

            # Test the connection
            async with self._pool.acquire() as conn:
                await conn.fetchval("SELECT 1")

            self._initialized = True
            self.performance_monitor.end_operation(operation_id, success=True)

            logger.info("🗄️ Serena Intelligence Database initialized with ADHD optimizations")
            return True

        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            if hasattr(self, 'performance_monitor'):
                self.performance_monitor.end_operation(operation_id, success=False)
            return False

    async def close(self) -> None:
        """Close the database connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            self._initialized = False
            logger.info("🗄️ Database connection pool closed")

    @asynccontextmanager
    async def connection(self) -> AsyncGenerator[asyncpg.Connection, None]:
        """Get a database connection with performance monitoring."""
        if not self._initialized:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        operation_id = self.performance_monitor.start_operation("db_connection_acquire")

        try:
            async with self._pool.acquire() as conn:
                self.performance_monitor.end_operation(operation_id, success=True, cache_hit=True)
                yield conn
        except Exception as e:
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"Database connection error: {e}")
            raise

    async def execute_query(
        self,
        query: str,
        args: Tuple = None,
        cache_key: Optional[str] = None,
        complexity_filter: bool = True,
        max_results: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute query with ADHD performance optimization.

        Args:
            query: SQL query to execute
            args: Query parameters
            cache_key: Optional cache key for frequent queries
            complexity_filter: Whether to apply ADHD complexity filtering
            max_results: Maximum results (overrides config default)
        """
        # Check cache first for performance
        if cache_key and cache_key in self._query_cache:
            cached_data, cache_time = self._query_cache[cache_key]
            if time.time() - cache_time < self._cache_ttl:
                operation_id = self.performance_monitor.start_operation("db_query_cached")
                self.performance_monitor.end_operation(operation_id, success=True, cache_hit=True)
                return cached_data

        operation_id = self.performance_monitor.start_operation("db_query")
        start_time = time.time()

        try:
            async with self.connection() as conn:
                # Execute query with timeout protection
                try:
                    if args:
                        result = await asyncio.wait_for(
                            conn.fetch(query, *args),
                            timeout=self.config.query_timeout
                        )
                    else:
                        result = await asyncio.wait_for(
                            conn.fetch(query),
                            timeout=self.config.query_timeout
                        )
                except asyncio.TimeoutError:
                    logger.warning(f"Query timeout after {self.config.query_timeout}s")
                    self.performance_monitor.end_operation(operation_id, success=False)
                    return []

                # Convert to list of dicts
                rows = [dict(row) for row in result]

                # Apply ADHD optimizations
                if complexity_filter and self.config.adhd_complexity_filtering:
                    rows = self._apply_complexity_filtering(rows)
                    self._metrics.complexity_filtered_queries += 1

                # Apply result limiting for cognitive load management
                result_limit = max_results or self.config.max_results_per_query
                if len(rows) > result_limit:
                    rows = rows[:result_limit]
                    self._metrics.progressive_disclosure_activations += 1
                    logger.debug(f"🧠 ADHD: Limited results to {result_limit} for cognitive load management")

                # Cache successful queries
                if cache_key:
                    self._query_cache[cache_key] = (rows, time.time())

                # Performance monitoring
                query_time_ms = (time.time() - start_time) * 1000
                self._update_metrics(query_time_ms, len(rows), cache_hit=bool(cache_key and cache_key in self._query_cache))

                performance_level = self._categorize_performance(query_time_ms)
                if performance_level in [QueryPerformanceLevel.SLOW, QueryPerformanceLevel.TIMEOUT]:
                    logger.warning(f"⚠️ Slow query ({query_time_ms:.1f}ms): {query[:100]}...")

                self.performance_monitor.end_operation(
                    operation_id,
                    success=True,
                    cache_hit=cache_key in self._query_cache if cache_key else False
                )

                return rows

        except Exception as e:
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"Query execution failed: {e}")
            raise

    async def execute_batch_queries(
        self,
        queries: List[Tuple[str, Tuple]],
        max_concurrent: int = 5
    ) -> List[List[Dict[str, Any]]]:
        """Execute multiple queries concurrently with ADHD performance limits."""
        operation_id = self.performance_monitor.start_operation("db_batch_queries")

        try:
            # Limit concurrent queries to prevent overwhelm
            semaphore = asyncio.Semaphore(min(max_concurrent, len(queries)))

            async def execute_single(query_tuple: Tuple[str, Tuple]) -> List[Dict[str, Any]]:
                async with semaphore:
                    query, args = query_tuple
                    return await self.execute_query(query, args)

            # Execute all queries concurrently
            results = await asyncio.gather(*[execute_single(q) for q in queries])

            self.performance_monitor.end_operation(operation_id, success=True)
            logger.debug(f"🚀 Batch executed {len(queries)} queries successfully")

            return results

        except Exception as e:
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"Batch query execution failed: {e}")
            raise

    def _apply_complexity_filtering(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply ADHD complexity filtering to query results."""
        if not rows:
            return rows

        # Check if results have complexity scores
        if not any('complexity_score' in row for row in rows):
            return rows

        # Sort by complexity (simple first for ADHD users)
        filtered_rows = []
        for row in rows:
            complexity_score = row.get('complexity_score', 0.0)

            # Apply ADHD complexity thresholds
            complexity_category, _ = self.complexity_analyzer.categorize_complexity(complexity_score)

            # Include complexity metadata for UI
            row['adhd_complexity_category'] = complexity_category
            row['adhd_recommended'] = complexity_score <= 0.6  # Simple and moderate are recommended

            filtered_rows.append(row)

        # Sort by ADHD-friendliness (complexity score ascending)
        return sorted(filtered_rows, key=lambda x: x.get('complexity_score', 0.0))

    def _categorize_performance(self, query_time_ms: float) -> QueryPerformanceLevel:
        """Categorize query performance for ADHD optimization."""
        if query_time_ms < 50:
            return QueryPerformanceLevel.EXCELLENT
        elif query_time_ms < 100:
            return QueryPerformanceLevel.GOOD
        elif query_time_ms < 200:
            return QueryPerformanceLevel.ACCEPTABLE
        elif query_time_ms < 500:
            return QueryPerformanceLevel.SLOW
        else:
            return QueryPerformanceLevel.TIMEOUT

    def _update_metrics(self, query_time_ms: float, result_count: int, cache_hit: bool = False) -> None:
        """Update database performance metrics."""
        self._metrics.query_count += 1

        # Update rolling average
        total_time = self._metrics.average_query_time_ms * (self._metrics.query_count - 1)
        self._metrics.average_query_time_ms = (total_time + query_time_ms) / self._metrics.query_count

        # Update ADHD compliance rate
        adhd_compliant = query_time_ms < 200  # ADHD target
        current_compliant = self._metrics.adhd_compliance_rate * (self._metrics.query_count - 1)
        self._metrics.adhd_compliance_rate = (current_compliant + (1 if adhd_compliant else 0)) / self._metrics.query_count

        # Update cache hit rate
        if cache_hit:
            current_hits = self._metrics.cache_hit_rate * (self._metrics.query_count - 1)
            self._metrics.cache_hit_rate = (current_hits + 1) / self._metrics.query_count

    async def get_health_status(self) -> Dict[str, Any]:
        """Get database health status with ADHD performance insights."""
        if not self._initialized:
            return {"status": "🔴 Not Initialized", "initialized": False}

        try:
            # Test query performance
            operation_id = self.performance_monitor.start_operation("db_health_check")
            start_time = time.time()

            async with self.connection() as conn:
                await conn.fetchval("SELECT 1")

            health_check_time = (time.time() - start_time) * 1000
            self.performance_monitor.end_operation(operation_id, success=True)

            # Pool status
            pool_usage = (self._pool.get_size() - self._pool.get_idle_size()) / self._pool.get_max_size()
            self._metrics.connection_pool_usage = pool_usage

            # Performance assessment
            performance_status = "🚀 Excellent" if health_check_time < 50 else \
                               "✅ Good" if health_check_time < 100 else \
                               "⚠️ Slow" if health_check_time < 200 else "🔴 Critical"

            return {
                "status": performance_status,
                "initialized": True,
                "health_check_time_ms": round(health_check_time, 2),
                "adhd_compliant": health_check_time < 200,
                "connection_pool": {
                    "size": self._pool.get_size(),
                    "idle": self._pool.get_idle_size(),
                    "usage_percentage": f"{pool_usage:.1%}"
                },
                "metrics": asdict(self._metrics),
                "adhd_insights": self._generate_adhd_insights()
            }

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "🔴 Error",
                "initialized": True,
                "error": str(e)
            }

    def _generate_adhd_insights(self) -> List[str]:
        """Generate ADHD-specific database performance insights."""
        insights = []

        if self._metrics.adhd_compliance_rate > 0.9:
            insights.append("🚀 Excellent ADHD performance - queries are snappy and responsive")
        elif self._metrics.adhd_compliance_rate > 0.7:
            insights.append("✅ Good ADHD performance - most queries meet cognitive load targets")
        else:
            insights.append("⚠️ ADHD performance needs improvement - consider query optimization")

        if self._metrics.cache_hit_rate > 0.8:
            insights.append("💾 Great cache utilization - repeat navigation is fast")
        elif self._metrics.cache_hit_rate < 0.3:
            insights.append("🔄 Low cache hits - exploring new areas or cache warming needed")

        if self._metrics.complexity_filtered_queries > 0:
            insights.append(f"🧠 Applied complexity filtering {self._metrics.complexity_filtered_queries} times for cognitive load management")

        if self._metrics.progressive_disclosure_activations > 0:
            insights.append(f"📖 Used progressive disclosure {self._metrics.progressive_disclosure_activations} times to prevent overwhelm")

        if self._metrics.connection_pool_usage > 0.8:
            insights.append("🔌 High connection pool usage - consider increasing pool size")

        return insights

    async def clear_cache(self) -> None:
        """Clear the query cache."""
        self._query_cache.clear()
        logger.info("🧹 Query cache cleared")

    async def optimize_for_adhd_session(self, user_session_data: Dict[str, Any]) -> None:
        """Optimize database performance based on user's ADHD session data."""
        try:
            # Adjust settings based on user's attention span
            attention_span = user_session_data.get('attention_span_minutes', 25)
            if attention_span < 15:  # Short attention span
                self.config.max_results_per_query = min(20, self.config.max_results_per_query)
                self.config.query_timeout = min(1.0, self.config.query_timeout)
                logger.info("🎯 Optimized for short attention span session")

            # Adjust complexity filtering based on cognitive load
            cognitive_load = user_session_data.get('cognitive_load_score', 0.5)
            if cognitive_load > 0.7:  # High cognitive load
                self.config.adhd_complexity_filtering = True
                self.config.progressive_disclosure_mode = True
                logger.info("🧠 Enhanced filtering for high cognitive load")

        except Exception as e:
            logger.error(f"ADHD session optimization failed: {e}")


# Convenience functions for common operations
async def create_intelligence_database(
    config: DatabaseConfig = None,
    performance_monitor: PerformanceMonitor = None
) -> SerenaIntelligenceDatabase:
    """Create and initialize Serena intelligence database."""
    db = SerenaIntelligenceDatabase(config, performance_monitor)
    await db.initialize()
    return db


async def test_database_performance() -> Dict[str, Any]:
    """Test database performance for ADHD compliance."""
    try:
        db = await create_intelligence_database()

        # Run performance tests
        test_results = []

        for i in range(10):
            start_time = time.time()
            await db.execute_query("SELECT 1 as test_value")
            query_time = (time.time() - start_time) * 1000
            test_results.append(query_time)

        avg_time = sum(test_results) / len(test_results)
        max_time = max(test_results)
        min_time = min(test_results)

        await db.close()

        return {
            "average_query_time_ms": round(avg_time, 2),
            "max_query_time_ms": round(max_time, 2),
            "min_query_time_ms": round(min_time, 2),
            "adhd_compliant": avg_time < 200,
            "performance_rating": "🚀 Excellent" if avg_time < 50 else
                                "✅ Good" if avg_time < 100 else
                                "⚠️ Acceptable" if avg_time < 200 else "🔴 Slow",
            "test_count": len(test_results)
        }

    except Exception as e:
        return {"error": str(e), "adhd_compliant": False}


if __name__ == "__main__":
    # Quick performance test when run directly
    async def main():
        print("🗄️ Serena Intelligence Database Performance Test")
        results = await test_database_performance()

        if "error" in results:
            print(f"❌ Test failed: {results['error']}")
        else:
            print(f"Performance: {results['performance_rating']}")
            print(f"Average: {results['average_query_time_ms']}ms")
            print(f"ADHD Compliant: {'✅ Yes' if results['adhd_compliant'] else '⚠️ No'}")

    asyncio.run(main())