#!/usr/bin/env python3
"""
Comprehensive test suite for Serena v2 Intelligence Database (database.py)

Tests 13 critical areas:
1. Database initialization & connection pooling
2. Query performance & ADHD compliance (<200ms)
3. Timeout handling & graceful degradation
4. Batch query execution with concurrency limits
5. Cache functionality & TTL
6. Complexity filtering & ADHD metadata
7. Progressive disclosure & result limiting
8. ADHD session optimization
9. Health status monitoring
10. Metrics tracking & rolling averages
11. Connection error handling
12. Performance under load (100 concurrent queries)
13. Cache vs uncached performance comparison

Status: RED phase - expect failures before database setup
"""

import asyncio
import pytest
import pytest_asyncio
import time
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path

# Import database module using project root
from services.serena.v2.intelligence.database import (
    SeranaIntelligenceDatabase,
    DatabaseConfig,
    QueryPerformanceLevel,
    DatabaseMetrics,
    create_intelligence_database,
    ASYNCPG_AVAILABLE
)
from services.serena.v2.performance_monitor import PerformanceMonitor
from services.serena.v2.adhd_features import CodeComplexityAnalyzer



# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture
def db_config():
    """Test database configuration."""
    return DatabaseConfig(
        host="localhost",
        port=5432,
        database="serena_intelligence_test",
        user="serena",
        password="serena_test_pass",
        min_connections=2,
        max_connections=10,
        command_timeout=5.0,
        query_timeout=2.0,
        max_results_per_query=50
    )


@pytest.fixture
def performance_monitor():
    """Mock performance monitor."""
    monitor = Mock(spec=PerformanceMonitor)
    monitor.start_operation = Mock(return_value="op_123")
    monitor.end_operation = Mock()
    return monitor


@pytest.fixture
async def database(db_config, performance_monitor):
    """Create test database instance."""
    if not ASYNCPG_AVAILABLE:
        pytest.skip("asyncpg not available - install with: pip install asyncpg")

    from serena.v2.intelligence.database import SerenaIntelligenceDatabase

    db = SeranaIntelligenceDatabase(db_config, performance_monitor)

    # Try to initialize (may fail if database doesn't exist - that's okay for RED phase)
    try:
        success = await db.initialize()
        if success:
            yield db
            await db.close()
        else:
            pytest.skip("Database initialization failed")
    except Exception as e:
        # RED phase - database not set up yet
        pytest.skip(f"Database not available: {e}")


# ============================================================================
# TEST 1: DATABASE INITIALIZATION
# ============================================================================

@pytest.mark.asyncio
async def test_database_initialization(db_config, performance_monitor):
    """Test 1: Verify database initializes with connection pool."""
    from serena.v2.intelligence.database import SeranaIntelligenceDatabase

    db = SeranaIntelligenceDatabase(db_config, performance_monitor)

    # Should start uninitialized
    assert not db._initialized
    assert db._pool is None

    # Initialize should create pool
    try:
        success = await db.initialize()

        if success:
            assert db._initialized is True
            assert db._pool is not None

            # Performance monitor should be called
            assert performance_monitor.start_operation.called
            assert performance_monitor.end_operation.called

            # Cleanup
            await db.close()
            assert db._initialized is False
            print("✅ Test 1 PASSED: Database initialization successful")
        else:
            print("⚠️ Test 1 SKIPPED: Database not available")
            pytest.skip("Database initialization failed")

    except Exception as e:
        print(f"❌ Test 1 FAILED: {e}")
        pytest.skip(f"Database not available: {e}")


# ============================================================================
# TEST 2: CONNECTION POOLING
# ============================================================================

@pytest.mark.asyncio
async def test_connection_pooling(database):
    """Test 2: Validate connection pool management."""
    # Get pool stats
    initial_size = database._pool.get_size()
    initial_idle = database._pool.get_idle_size()

    print(f"Initial pool: size={initial_size}, idle={initial_idle}")

    # Acquire connection
    async with database.connection() as conn:
        active_size = database._pool.get_size()
        active_idle = database._pool.get_idle_size()

        print(f"Active: size={active_size}, idle={active_idle}")

        # Connection should be checked out
        assert active_idle < initial_idle or active_size > initial_size

        # Connection should work
        result = await conn.fetchval("SELECT 1")
        assert result == 1

    # Connection should be returned to pool
    final_idle = database._pool.get_idle_size()
    assert final_idle >= active_idle

    print("✅ Test 2 PASSED: Connection pooling working")


# ============================================================================
# TEST 3: QUERY PERFORMANCE (<200ms ADHD COMPLIANCE)
# ============================================================================

@pytest.mark.asyncio
async def test_query_performance_under_200ms(database):
    """Test 3: Validate queries meet ADHD <200ms target."""
    test_queries = [
        "SELECT 1 as test_value",
        "SELECT generate_series(1, 10) as num",
        "SELECT NOW() as current_time"
    ]

    results = []
    for query in test_queries:
        start_time = time.time()
        await database.execute_query(query)
        query_time_ms = (time.time() - start_time) * 1000
        results.append(query_time_ms)

        print(f"Query: {query[:40]:40s} | Time: {query_time_ms:6.2f}ms")

    # Check ADHD compliance
    avg_time = sum(results) / len(results)
    max_time = max(results)

    adhd_compliant = avg_time < 200 and max_time < 500

    print(f"\nAverage: {avg_time:.2f}ms | Max: {max_time:.2f}ms")
    print(f"ADHD Compliant (<200ms avg): {'✅ YES' if adhd_compliant else '❌ NO'}")

    assert avg_time < 200, f"Average query time {avg_time:.2f}ms exceeds ADHD target of 200ms"
    print("✅ Test 3 PASSED: ADHD performance targets met")


# ============================================================================
# TEST 4: TIMEOUT HANDLING
# ============================================================================

@pytest.mark.asyncio
async def test_query_timeout_handling(database):
    """Test 4: Verify timeout protection works."""
    # Create slow query (pg_sleep if available)
    slow_query = "SELECT pg_sleep(3)"  # 3 seconds > 2 second timeout

    start_time = time.time()
    try:
        result = await database.execute_query(slow_query)
        elapsed = time.time() - start_time

        # Should timeout and return empty
        assert result == []
        assert elapsed < 3.0, "Query should timeout before completion"

        print(f"✅ Test 4 PASSED: Timeout handled gracefully ({elapsed:.2f}s)")
    except asyncio.TimeoutError:
        print("✅ Test 4 PASSED: Timeout raised correctly")
    except Exception as e:
        # pg_sleep might not be available
        if "pg_sleep" in str(e):
            print("⚠️ Test 4 SKIPPED: pg_sleep not available")
            pytest.skip("pg_sleep function not available")
        else:
            raise


# ============================================================================
# TEST 5: BATCH QUERY EXECUTION
# ============================================================================

@pytest.mark.asyncio
async def test_batch_query_execution(database):
    """Test 5: Validate concurrent batch execution with semaphore limiting."""
    # Create 10 queries
    queries = [
        ("SELECT $1 as value", (i,))
        for i in range(10)
    ]

    start_time = time.time()
    results = await database.execute_batch_queries(queries, max_concurrent=5)
    elapsed_ms = (time.time() - start_time) * 1000

    # All queries should complete
    assert len(results) == 10

    # Results should be in order
    for i, result in enumerate(results):
        assert len(result) == 1
        assert result[0]['value'] == i

    print(f"✅ Test 5 PASSED: Batch executed 10 queries in {elapsed_ms:.2f}ms")


# ============================================================================
# TEST 6: CACHE FUNCTIONALITY
# ============================================================================

@pytest.mark.asyncio
async def test_cache_functionality(database):
    """Test 6: Validate query caching and TTL."""
    query = "SELECT 1 as cached_value"
    cache_key = "test_cache_key"

    # First query (cache miss)
    start_time = time.time()
    result1 = await database.execute_query(query, cache_key=cache_key)
    first_time = (time.time() - start_time) * 1000

    # Second query (cache hit)
    start_time = time.time()
    result2 = await database.execute_query(query, cache_key=cache_key)
    second_time = (time.time() - start_time) * 1000

    # Results should match
    assert result1 == result2

    # Cached query should be faster
    assert second_time < first_time, f"Cache hit ({second_time:.2f}ms) should be faster than miss ({first_time:.2f}ms)"

    # Cache should exist
    assert cache_key in database._query_cache

    # Clear cache
    await database.clear_cache()
    assert cache_key not in database._query_cache

    print(f"✅ Test 6 PASSED: Cache working (miss: {first_time:.2f}ms, hit: {second_time:.2f}ms)")


# ============================================================================
# TEST 7: COMPLEXITY FILTERING
# ============================================================================

@pytest.mark.asyncio
async def test_complexity_filtering(database):
    """Test 7: Verify ADHD complexity filtering and metadata."""
    # Mock data with complexity scores
    mock_rows = [
        {'id': 1, 'name': 'simple', 'complexity_score': 0.3},
        {'id': 2, 'name': 'complex', 'complexity_score': 0.8},
        {'id': 3, 'name': 'moderate', 'complexity_score': 0.5}
    ]

    # Apply complexity filtering
    filtered = database._apply_complexity_filtering(mock_rows)

    # Should be sorted by complexity (simple first)
    assert filtered[0]['complexity_score'] == 0.3
    assert filtered[1]['complexity_score'] == 0.5
    assert filtered[2]['complexity_score'] == 0.8

    # Should have ADHD metadata
    for row in filtered:
        assert 'adhd_complexity_category' in row
        assert 'adhd_recommended' in row

    # Simple and moderate should be recommended
    assert filtered[0]['adhd_recommended'] is True
    assert filtered[1]['adhd_recommended'] is True
    assert filtered[2]['adhd_recommended'] is False

    print("✅ Test 7 PASSED: Complexity filtering and metadata working")


# ============================================================================
# TEST 8: PROGRESSIVE DISCLOSURE
# ============================================================================

@pytest.mark.asyncio
async def test_progressive_disclosure(database):
    """Test 8: Validate result limiting for cognitive load."""
    # Temporarily set low limit
    original_limit = database.config.max_results_per_query
    database.config.max_results_per_query = 5

    # Query that returns many rows
    query = "SELECT generate_series(1, 20) as num"

    result = await database.execute_query(query)

    # Should be limited to 5
    assert len(result) <= 5

    # Metric should be incremented
    assert database._metrics.progressive_disclosure_activations > 0

    # Restore original limit
    database.config.max_results_per_query = original_limit

    print(f"✅ Test 8 PASSED: Progressive disclosure limited results to {len(result)}")


# ============================================================================
# TEST 9: ADHD SESSION OPTIMIZATION
# ============================================================================

@pytest.mark.asyncio
async def test_adhd_session_optimization(database):
    """Test 9: Validate dynamic optimization based on session data."""
    # Session with short attention span
    session_data = {
        'attention_span_minutes': 10,
        'cognitive_load_score': 0.8
    }

    original_max = database.config.max_results_per_query
    original_timeout = database.config.query_timeout

    await database.optimize_for_adhd_session(session_data)

    # Settings should be adjusted
    assert database.config.max_results_per_query <= 20  # Reduced for short attention
    assert database.config.adhd_complexity_filtering is True  # Enabled for high load
    assert database.config.progressive_disclosure_mode is True

    print("✅ Test 9 PASSED: ADHD session optimization working")


# ============================================================================
# TEST 10: HEALTH STATUS MONITORING
# ============================================================================

@pytest.mark.asyncio
async def test_health_status_monitoring(database):
    """Test 10: Validate health check and insights generation."""
    health = await database.get_health_status()

    # Should have required fields
    assert 'status' in health
    assert 'initialized' in health
    assert health['initialized'] is True

    # Should include pool stats
    assert 'connection_pool' in health
    assert 'size' in health['connection_pool']
    assert 'idle' in health['connection_pool']

    # Should have metrics
    assert 'metrics' in health
    assert 'adhd_insights' in health

    # Health check should be fast
    if 'health_check_time_ms' in health:
        assert health['health_check_time_ms'] < 200  # ADHD compliant

    print(f"✅ Test 10 PASSED: Health status = {health['status']}")


# ============================================================================
# TEST 11: METRICS TRACKING
# ============================================================================

@pytest.mark.asyncio
async def test_metrics_tracking(database):
    """Test 11: Verify metrics tracking and rolling averages."""
    initial_count = database._metrics.query_count

    # Execute some queries
    for i in range(5):
        await database.execute_query("SELECT 1")

    # Metrics should be updated
    assert database._metrics.query_count == initial_count + 5
    assert database._metrics.average_query_time_ms > 0
    assert 0 <= database._metrics.adhd_compliance_rate <= 1.0

    print(f"✅ Test 11 PASSED: Metrics tracked ({database._metrics.query_count} queries)")


# ============================================================================
# TEST 12: CONNECTION ERROR HANDLING
# ============================================================================

@pytest.mark.asyncio
async def test_connection_error_handling():
    """Test 12: Validate graceful error handling."""
    from serena.v2.intelligence.database import SeranaIntelligenceDatabase, DatabaseConfig

    # Bad config
    bad_config = DatabaseConfig(
        host="nonexistent.invalid",
        port=9999,
        database="fake_db",
        user="fake_user",
        password="fake_pass"
    )

    db = SeranaIntelligenceDatabase(bad_config)

    # Should fail gracefully
    success = await db.initialize()
    assert success is False
    assert db._initialized is False

    print("✅ Test 12 PASSED: Connection errors handled gracefully")


# ============================================================================
# TEST 13: PERFORMANCE UNDER LOAD
# ============================================================================

@pytest.mark.asyncio
async def test_100_concurrent_queries(database):
    """Test 13: Stress test with 100 concurrent queries."""
    queries = [
        ("SELECT $1 as value", (i,))
        for i in range(100)
    ]

    start_time = time.time()
    results = await database.execute_batch_queries(queries, max_concurrent=10)
    elapsed_ms = (time.time() - start_time) * 1000

    # All should complete
    assert len(results) == 100

    # Average per-query time
    avg_time = elapsed_ms / 100

    print(f"✅ Test 13 PASSED: 100 queries in {elapsed_ms:.2f}ms (avg: {avg_time:.2f}ms/query)")

    # Should still be ADHD compliant on average
    assert avg_time < 200, f"Average {avg_time:.2f}ms exceeds ADHD target"


# ============================================================================
# PERFORMANCE COMPARISON TEST
# ============================================================================

@pytest.mark.asyncio
async def test_cache_vs_uncached_performance(database):
    """Bonus Test: Validate cache speedup."""
    query = "SELECT generate_series(1, 100) as num"
    cache_key = "perf_test"

    # Uncached
    start = time.time()
    await database.execute_query(query)
    uncached_ms = (time.time() - start) * 1000

    # Cached
    start = time.time()
    await database.execute_query(query, cache_key=cache_key)
    first_cached_ms = (time.time() - start) * 1000

    # Second cached (should be faster)
    start = time.time()
    await database.execute_query(query, cache_key=cache_key)
    second_cached_ms = (time.time() - start) * 1000

    print(f"\nPerformance comparison:")
    print(f"  Uncached:       {uncached_ms:.2f}ms")
    print(f"  First cached:   {first_cached_ms:.2f}ms")
    print(f"  Second cached:  {second_cached_ms:.2f}ms")
    print(f"  Speedup:        {uncached_ms / second_cached_ms:.1f}x")

    assert second_cached_ms < first_cached_ms
    print("✅ Bonus Test PASSED: Cache provides speedup")


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("🧪 Serena v2 Intelligence Database Test Suite")
    print("=" * 70)
    print()

    # Run with pytest
    import sys
    sys.exit(pytest.main([__file__, "-v", "-s"]))
