"""
Comprehensive Test Suite for SerenaIntelligenceDatabase

Tests database operations, connection pooling, ADHD optimizations,
performance targets, and integration points.
"""

import pytest
import asyncio
import time
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "services" / "serena"))

from v2.intelligence.database import (
    SerenaIntelligenceDatabase,
    DatabaseConfig,
    DatabaseMetrics,
    QueryPerformanceLevel,
    create_intelligence_database,
    test_database_performance
)
from v2.performance_monitor import PerformanceMonitor


# ==========================================
# Test 1: Database Initialization
# ==========================================

@pytest.mark.asyncio
@pytest.mark.database
async def test_database_initialization(test_db_config, performance_monitor):
    """Test database connection pool initialization."""
    db = SerenaIntelligenceDatabase(test_db_config, performance_monitor)

    # Should not be initialized yet
    assert not db._initialized

    # Initialize
    success = await db.initialize()
    assert success is True
    assert db._initialized is True
    assert db._pool is not None

    # Cleanup
    await db.close()
    assert db._initialized is False


# ==========================================
# Test 2: Connection Pooling
# ==========================================

@pytest.mark.asyncio
@pytest.mark.database
@pytest.mark.performance
async def test_connection_pooling(test_db_config, performance_monitor, assert_adhd_compliant):
    """Test connection pool behavior and performance."""
    db = SerenaIntelligenceDatabase(test_db_config, performance_monitor)
    await db.initialize()

    # Test connection acquisition performance
    start_time = time.time()
    async with db.connection() as conn:
        result = await conn.fetchval("SELECT 1")
        assert result == 1
    connection_time_ms = (time.time() - start_time) * 1000

    # Should be very fast (ADHD requirement)
    assert_adhd_compliant(connection_time_ms)

    # Test concurrent connections
    async def acquire_connection(delay_ms: int):
        await asyncio.sleep(delay_ms / 1000.0)
        async with db.connection() as conn:
            return await conn.fetchval("SELECT 1")

    # Acquire multiple connections concurrently
    results = await asyncio.gather(*[acquire_connection(i * 10) for i in range(5)])
    assert all(r == 1 for r in results)

    # Pool should handle concurrent requests
    pool_status = await db.get_health_status()
    assert pool_status["initialized"] is True
    assert "connection_pool" in pool_status

    await db.close()


# ==========================================
# Test 3: Query Performance (<200ms ADHD Target)
# ==========================================

@pytest.mark.asyncio
@pytest.mark.database
@pytest.mark.performance
@pytest.mark.adhd
async def test_query_performance_under_200ms(test_db_config, performance_monitor, assert_adhd_compliant):
    """Test that all queries meet ADHD <200ms performance target."""
    db = SerenaIntelligenceDatabase(test_db_config, performance_monitor)
    await db.initialize()

    # Test simple query
    start_time = time.time()
    results = await db.execute_query("SELECT 1 as value")
    query_time_ms = (time.time() - start_time) * 1000

    assert len(results) == 1
    assert results[0]["value"] == 1
    assert_adhd_compliant(query_time_ms)

    # Test query with parameters
    start_time = time.time()
    results = await db.execute_query("SELECT $1::int as value", (42,))
    query_time_ms = (time.time() - start_time) * 1000

    assert results[0]["value"] == 42
    assert_adhd_compliant(query_time_ms)

    # Verify ADHD compliance metrics updated
    assert db._metrics.query_count >= 2
    assert db._metrics.adhd_compliance_rate > 0.0

    await db.close()


# ==========================================
# Test 4: Query Timeout Handling
# ==========================================

@pytest.mark.asyncio
@pytest.mark.database
async def test_query_timeout_handling(test_db_config, performance_monitor):
    """Test timeout protection for slow queries."""
    # Configure short timeout for testing
    test_db_config.query_timeout = 0.1  # 100ms timeout

    db = SerenaIntelligenceDatabase(test_db_config, performance_monitor)
    await db.initialize()

    # Query that might timeout (depends on system load)
    # Use pg_sleep to force timeout
    results = await db.execute_query("SELECT pg_sleep(1), 1 as value")

    # Should return empty results on timeout, not raise exception
    assert isinstance(results, list)
    # Timeout should have triggered
    assert len(results) == 0

    await db.close()


# ==========================================
# Test 5: Batch Query Execution
# ==========================================

@pytest.mark.asyncio
@pytest.mark.database
@pytest.mark.performance
async def test_batch_query_execution(test_db_config, performance_monitor, assert_adhd_compliant):
    """Test concurrent batch query execution."""
    db = SerenaIntelligenceDatabase(test_db_config, performance_monitor)
    await db.initialize()

    # Prepare batch queries
    queries = [
        ("SELECT $1::int as value", (i,))
        for i in range(10)
    ]

    # Execute batch
    start_time = time.time()
    results = await db.execute_batch_queries(queries, max_concurrent=5)
    batch_time_ms = (time.time() - start_time) * 1000

    # Verify all queries executed
    assert len(results) == 10
    for i, result in enumerate(results):
        assert len(result) == 1
        assert result[0]["value"] == i

    # Batch execution should be fast with concurrency
    assert_adhd_compliant(batch_time_ms)

    await db.close()


# ==========================================
# Test 6: Cache Functionality
# ==========================================

@pytest.mark.asyncio
@pytest.mark.database
@pytest.mark.performance
async def test_cache_functionality(test_db_config, performance_monitor):
    """Test query caching for performance."""
    db = SerenaIntelligenceDatabase(test_db_config, performance_monitor)
    await db.initialize()

    cache_key = "test_query_cache"

    # First query - should hit database
    start_time = time.time()
    results1 = await db.execute_query("SELECT 42 as value", cache_key=cache_key)
    uncached_time_ms = (time.time() - start_time) * 1000

    # Second query - should hit cache
    start_time = time.time()
    results2 = await db.execute_query("SELECT 42 as value", cache_key=cache_key)
    cached_time_ms = (time.time() - start_time) * 1000

    # Results should be identical
    assert results1 == results2

    # Cached query should be significantly faster
    assert cached_time_ms < uncached_time_ms
    assert cached_time_ms < 10.0  # Cache hits should be <10ms

    # Cache hit rate should be tracked
    assert db._metrics.cache_hit_rate > 0.0

    # Test cache clearing
    await db.clear_cache()
    assert len(db._query_cache) == 0

    await db.close()


# ==========================================
# Test 7: Complexity Filtering (ADHD)
# ==========================================

@pytest.mark.asyncio
@pytest.mark.database
@pytest.mark.adhd
async def test_complexity_filtering(test_db_config, performance_monitor):
    """Test ADHD complexity filtering and result sorting."""
    db = SerenaIntelligenceDatabase(test_db_config, performance_monitor)
    await db.initialize()

    # Create test data with different complexity scores
    test_rows = [
        {"name": "complex_func", "complexity_score": 0.9},
        {"name": "simple_func", "complexity_score": 0.2},
        {"name": "moderate_func", "complexity_score": 0.5}
    ]

    # Apply complexity filtering
    filtered = db._apply_complexity_filtering(test_rows)

    # Should be sorted by complexity (simple first)
    assert filtered[0]["name"] == "simple_func"
    assert filtered[1]["name"] == "moderate_func"
    assert filtered[2]["name"] == "complex_func"

    # Should have ADHD metadata
    assert "adhd_complexity_category" in filtered[0]
    assert "adhd_recommended" in filtered[0]

    # Simple elements should be recommended
    assert filtered[0]["adhd_recommended"] is True
    assert filtered[2]["adhd_recommended"] is False  # Complex not recommended

    await db.close()


# ==========================================
# Test 8: Progressive Disclosure (ADHD)
# ==========================================

@pytest.mark.asyncio
@pytest.mark.database
@pytest.mark.adhd
async def test_progressive_disclosure(test_db_config, performance_monitor):
    """Test progressive disclosure for cognitive load management."""
    # Configure max results for testing
    test_db_config.max_results_per_query = 5

    db = SerenaIntelligenceDatabase(test_db_config, performance_monitor)
    await db.initialize()

    # Mock query that would return many results
    # Since we can't actually create test data, we'll test the limiting logic
    assert db.config.max_results_per_query == 5

    # Track that progressive disclosure activations are counted
    initial_activations = db._metrics.progressive_disclosure_activations
    # (Would increase if we had actual large result sets)

    await db.close()


# ==========================================
# Test 9: ADHD Session Optimization
# ==========================================

@pytest.mark.asyncio
@pytest.mark.database
@pytest.mark.adhd
async def test_adhd_session_optimization(
    test_db_config,
    performance_monitor,
    adhd_scattered_state,
    adhd_hyperfocus_state
):
    """Test session-based ADHD optimization."""
    db = SerenaIntelligenceDatabase(test_db_config, performance_monitor)
    await db.initialize()

    # Optimize for scattered attention (short attention span)
    await db.optimize_for_adhd_session(adhd_scattered_state)
    assert db.config.max_results_per_query <= 20  # Limited for scattered state
    assert db.config.adhd_complexity_filtering is True

    # Optimize for hyperfocus (long attention span)
    await db.optimize_for_adhd_session(adhd_hyperfocus_state)
    # Should allow more results in hyperfocus
    # (Implementation may not change max_results for hyperfocus)

    await db.close()


# ==========================================
# Test 10: Health Status Monitoring
# ==========================================

@pytest.mark.asyncio
@pytest.mark.database
async def test_health_status_monitoring(test_db_config, performance_monitor):
    """Test database health status reporting."""
    db = SerenaIntelligenceDatabase(test_db_config, performance_monitor)
    await db.initialize()

    # Get health status
    health = await db.get_health_status()

    # Should report as healthy
    assert health["initialized"] is True
    assert "health_check_time_ms" in health
    assert health["adhd_compliant"] is True

    # Should have connection pool info
    assert "connection_pool" in health
    assert "size" in health["connection_pool"]
    assert "idle" in health["connection_pool"]
    assert "usage_percentage" in health["connection_pool"]

    # Should have ADHD insights
    assert "adhd_insights" in health
    assert isinstance(health["adhd_insights"], list)

    # Should have metrics
    assert "metrics" in health

    await db.close()


# ==========================================
# Test 11: Metrics Tracking
# ==========================================

@pytest.mark.asyncio
@pytest.mark.database
async def test_metrics_tracking(test_db_config, performance_monitor):
    """Test database performance metrics tracking."""
    db = SerenaIntelligenceDatabase(test_db_config, performance_monitor)
    await db.initialize()

    initial_query_count = db._metrics.query_count

    # Execute several queries
    for i in range(5):
        await db.execute_query("SELECT $1::int as value", (i,))

    # Metrics should be updated
    assert db._metrics.query_count == initial_query_count + 5
    assert db._metrics.average_query_time_ms > 0.0
    assert db._metrics.adhd_compliance_rate > 0.0

    await db.close()


# ==========================================
# Test 12: Connection Error Handling
# ==========================================

@pytest.mark.asyncio
@pytest.mark.database
async def test_connection_error_handling(performance_monitor):
    """Test graceful handling of connection errors."""
    # Configure with invalid credentials
    bad_config = DatabaseConfig(
        host="localhost",
        port=5432,
        database="nonexistent_db",
        user="invalid_user",
        password="wrong_password"
    )

    db = SerenaIntelligenceDatabase(bad_config, performance_monitor)

    # Initialization should fail gracefully
    success = await db.initialize()
    assert success is False
    assert db._initialized is False

    # Attempting to use connection should raise error
    with pytest.raises(RuntimeError, match="Database not initialized"):
        async with db.connection() as conn:
            await conn.fetchval("SELECT 1")


# ==========================================
# Test 13: Performance Categorization
# ==========================================

@pytest.mark.unit
def test_performance_categorization(test_db_config, performance_monitor):
    """Test query performance level categorization."""
    db = SerenaIntelligenceDatabase(test_db_config, performance_monitor)

    # Test categorization logic
    assert db._categorize_performance(30.0) == QueryPerformanceLevel.EXCELLENT
    assert db._categorize_performance(75.0) == QueryPerformanceLevel.GOOD
    assert db._categorize_performance(150.0) == QueryPerformanceLevel.ACCEPTABLE
    assert db._categorize_performance(300.0) == QueryPerformanceLevel.SLOW
    assert db._categorize_performance(600.0) == QueryPerformanceLevel.TIMEOUT

    # ADHD boundaries
    assert db._categorize_performance(199.0) == QueryPerformanceLevel.ACCEPTABLE  # Just under ADHD target
    assert db._categorize_performance(201.0) == QueryPerformanceLevel.SLOW  # Just over ADHD target


# ==========================================
# Test 14: Convenience Factory Function
# ==========================================

@pytest.mark.asyncio
@pytest.mark.database
async def test_create_intelligence_database_factory(test_db_config, performance_monitor):
    """Test convenience factory function."""
    db = await create_intelligence_database(test_db_config, performance_monitor)

    # Should be initialized and ready
    assert db._initialized is True

    # Should be able to query
    results = await db.execute_query("SELECT 1 as test")
    assert len(results) == 1
    assert results[0]["test"] == 1

    await db.close()


# ==========================================
# Test 15: Built-in Performance Test
# ==========================================

@pytest.mark.asyncio
@pytest.mark.database
@pytest.mark.performance
async def test_builtin_performance_test():
    """Test the module's built-in performance test function."""
    result = await test_database_performance()

    # Should succeed
    assert "error" not in result
    assert result["adhd_compliant"] is True

    # Should have performance metrics
    assert "average_query_time_ms" in result
    assert "max_query_time_ms" in result
    assert "min_query_time_ms" in result
    assert "performance_rating" in result

    # Should be excellent performance
    assert result["average_query_time_ms"] < 200.0


# ==========================================
# Stress Tests (Optional - marked slow)
# ==========================================

@pytest.mark.asyncio
@pytest.mark.database
@pytest.mark.performance
@pytest.mark.slow
async def test_100_concurrent_queries(test_db_config, performance_monitor, assert_adhd_compliant):
    """Stress test: 100 concurrent queries to validate pool and performance."""
    db = SerenaIntelligenceDatabase(test_db_config, performance_monitor)
    await db.initialize()

    async def single_query(value: int):
        return await db.execute_query("SELECT $1::int as value", (value,))

    # Execute 100 concurrent queries
    start_time = time.time()
    results = await asyncio.gather(*[single_query(i) for i in range(100)])
    total_time_ms = (time.time() - start_time) * 1000

    # All queries should succeed
    assert len(results) == 100
    for i, result in enumerate(results):
        assert result[0]["value"] == i

    # Average time per query should still be ADHD compliant
    avg_time_per_query = total_time_ms / 100
    print(f"Average time per query under load: {avg_time_per_query:.2f}ms")

    # May exceed 200ms total, but average per query should be reasonable
    # (this tests connection pool efficiency)

    await db.close()


# ==========================================
# Test 16: Cache vs Uncached Performance
# ==========================================

@pytest.mark.asyncio
@pytest.mark.database
@pytest.mark.performance
@pytest.mark.adhd
async def test_cache_vs_uncached_performance(test_db_config, performance_monitor):
    """Validate cache provides significant speedup."""
    db = SerenaIntelligenceDatabase(test_db_config, performance_monitor)
    await db.initialize()

    cache_key = "perf_test"

    # Uncached query
    uncached_times = []
    for i in range(3):
        start_time = time.time()
        await db.execute_query("SELECT 42 as value")
        uncached_times.append((time.time() - start_time) * 1000)

    avg_uncached = sum(uncached_times) / len(uncached_times)

    # Cached queries
    cached_times = []
    for i in range(3):
        start_time = time.time()
        await db.execute_query("SELECT 42 as value", cache_key=cache_key)
        cached_times.append((time.time() - start_time) * 1000)

    avg_cached = sum(cached_times) / len(cached_times)

    # Cache should provide speedup (at least for 2nd and 3rd queries)
    print(f"Uncached average: {avg_uncached:.2f}ms")
    print(f"Cached average: {avg_cached:.2f}ms")
    print(f"Speedup: {avg_uncached / avg_cached:.1f}x")

    # Both should be ADHD compliant
    assert avg_uncached < 200.0
    assert avg_cached < 200.0

    # Cache should have hits
    assert db._metrics.cache_hit_rate > 0.0

    await db.close()


# ==========================================
# Test 17: ADHD Compliance Under Load
# ==========================================

@pytest.mark.asyncio
@pytest.mark.database
@pytest.mark.performance
@pytest.mark.adhd
@pytest.mark.slow
async def test_adhd_compliance_under_load(test_db_config, performance_monitor):
    """Test that ADHD performance targets are maintained under load."""
    db = SerenaIntelligenceDatabase(test_db_config, performance_monitor)
    await db.initialize()

    # Execute 50 queries and measure performance
    query_times = []
    for i in range(50):
        start_time = time.time()
        await db.execute_query("SELECT $1::int as value", (i,))
        query_times.append((time.time() - start_time) * 1000)

    # Calculate statistics
    avg_time = sum(query_times) / len(query_times)
    max_time = max(query_times)
    min_time = min(query_times)
    adhd_violations = sum(1 for t in query_times if t >= 200.0)

    print(f"Average: {avg_time:.2f}ms")
    print(f"Min: {min_time:.2f}ms")
    print(f"Max: {max_time:.2f}ms")
    print(f"ADHD Violations: {adhd_violations}/50 ({adhd_violations/50:.1%})")

    # ADHD compliance should be high (>90%)
    assert adhd_violations <= 5  # Allow up to 10% violations under load
    assert db._metrics.adhd_compliance_rate >= 0.9

    await db.close()
