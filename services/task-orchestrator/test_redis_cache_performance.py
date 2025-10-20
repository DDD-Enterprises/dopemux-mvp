#!/usr/bin/env python3
"""
Redis Cache Performance Validation
===================================

Validates Redis caching layer performance for Component 5 with ADHD targets.

**Validation Goals**:
- Cache hit latency: < 5ms (target: 1.76ms from Serena benchmarks)
- Cache hit rate: > 80%
- Latency reduction: > 90% (1.76ms vs 100ms = 98%)
- ADHD-safe: All operations < 200ms

**Test Coverage**:
- Cache hit vs miss performance
- Cache invalidation timing
- TTL verification
- Workspace isolation
- Performance metrics accuracy
"""

import asyncio
import time
import statistics
from typing import List, Dict, Any
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from redis_cache import RedisCache, CacheInvalidator

# Test configuration
WARMUP_ITERATIONS = 10
TEST_ITERATIONS = 100
CACHE_HIT_TARGET_MS = 5.0  # Target: < 5ms (Serena achieved 1.76ms)
CACHE_MISS_SIMULATION_MS = 100  # Simulate ConPort MCP call time
LATENCY_REDUCTION_TARGET = 90  # Target: > 90% reduction


async def simulate_slow_query(duration_ms: float = 100) -> Dict[str, Any]:
    """Simulate slow ConPort MCP query."""
    await asyncio.sleep(duration_ms / 1000)
    return {
        "energy_level": "medium",
        "attention_level": "focused",
        "time_since_break": 45,
        "break_recommended": False,
        "current_session_duration": 45
    }


async def measure_operation(operation, label: str) -> float:
    """Measure operation latency in milliseconds."""
    start = time.time()
    result = await operation()
    latency = (time.time() - start) * 1000
    return latency


async def test_cache_hit_performance(cache: RedisCache) -> Dict[str, Any]:
    """Test cache hit latency."""
    print("\n" + "="*70)
    print("Test 1: Cache Hit Performance")
    print("="*70)

    # Pre-populate cache
    test_data = {"test": "data", "timestamp": time.time()}
    await cache.set("test_key", test_data, ttl=60)

    # Warmup
    print(f"  🔥 Warming up ({WARMUP_ITERATIONS} iterations)...")
    for _ in range(WARMUP_ITERATIONS):
        await cache.get("test_key")

    # Performance test
    print(f"  📊 Testing cache hits ({TEST_ITERATIONS} iterations)...")
    latencies = []

    for _ in range(TEST_ITERATIONS):
        latency = await measure_operation(
            lambda: cache.get("test_key"),
            "cache_hit"
        )
        latencies.append(latency)

    # Calculate statistics
    avg_latency = statistics.mean(latencies)
    min_latency = min(latencies)
    max_latency = max(latencies)
    p50_latency = statistics.median(latencies)
    p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
    p99_latency = sorted(latencies)[int(len(latencies) * 0.99)]

    # Validate against target
    passed = avg_latency < CACHE_HIT_TARGET_MS

    print(f"\n  Results:")
    print(f"    Average: {avg_latency:.2f}ms")
    print(f"    Min: {min_latency:.2f}ms")
    print(f"    Max: {max_latency:.2f}ms")
    print(f"    P50: {p50_latency:.2f}ms")
    print(f"    P95: {p95_latency:.2f}ms")
    print(f"    P99: {p99_latency:.2f}ms")
    print(f"    Target: < {CACHE_HIT_TARGET_MS:.0f}ms")
    print(f"    Status: {'✅ PASS' if passed else '❌ FAIL'}")

    return {
        "test": "cache_hit_performance",
        "passed": passed,
        "avg_latency_ms": avg_latency,
        "p95_latency_ms": p95_latency,
        "target_ms": CACHE_HIT_TARGET_MS
    }


async def test_cache_miss_vs_hit(cache: RedisCache) -> Dict[str, Any]:
    """Test cache miss vs hit latency difference."""
    print("\n" + "="*70)
    print("Test 2: Cache Miss vs Hit Comparison")
    print("="*70)

    # Test cache miss (with simulated slow query)
    print(f"  📊 Testing cache miss (simulated {CACHE_MISS_SIMULATION_MS}ms query)...")
    miss_latencies = []

    for i in range(20):
        start = time.time()

        # Check cache (miss)
        cached = await cache.get(f"miss_key_{i}")

        # Simulate slow query on miss
        if not cached:
            result = await simulate_slow_query(CACHE_MISS_SIMULATION_MS)
            await cache.set(f"miss_key_{i}", result, ttl=60)

        latency = (time.time() - start) * 1000
        miss_latencies.append(latency)

    # Test cache hit (from previous test)
    print(f"  📊 Testing cache hit...")
    await cache.set("hit_key", {"test": "data"}, ttl=60)

    hit_latencies = []
    for _ in range(20):
        latency = await measure_operation(
            lambda: cache.get("hit_key"),
            "cache_hit"
        )
        hit_latencies.append(latency)

    # Calculate statistics
    avg_miss = statistics.mean(miss_latencies)
    avg_hit = statistics.mean(hit_latencies)
    latency_reduction = ((avg_miss - avg_hit) / avg_miss) * 100

    # Validate against target
    passed = latency_reduction > LATENCY_REDUCTION_TARGET

    print(f"\n  Results:")
    print(f"    Cache miss avg: {avg_miss:.2f}ms")
    print(f"    Cache hit avg: {avg_hit:.2f}ms")
    print(f"    Latency reduction: {latency_reduction:.1f}%")
    print(f"    Target: > {LATENCY_REDUCTION_TARGET}%")
    print(f"    Status: {'✅ PASS' if passed else '❌ FAIL'}")

    return {
        "test": "cache_miss_vs_hit",
        "passed": passed,
        "miss_latency_ms": avg_miss,
        "hit_latency_ms": avg_hit,
        "latency_reduction_pct": latency_reduction,
        "target_pct": LATENCY_REDUCTION_TARGET
    }


async def test_cache_hit_rate(cache: RedisCache) -> Dict[str, Any]:
    """Test cache hit rate over multiple queries."""
    print("\n" + "="*70)
    print("Test 3: Cache Hit Rate")
    print("="*70)

    # Pre-populate cache with 80 keys (simulate 80% hit rate)
    print(f"  📦 Pre-populating cache (80 keys)...")
    for i in range(80):
        await cache.set(f"popular_key_{i}", {"data": i}, ttl=60)

    # Reset metrics
    cache.hits = 0
    cache.misses = 0

    # Perform 100 queries (80 cached, 20 uncached)
    print(f"  📊 Performing 100 queries (80 cached, 20 uncached)...")
    for i in range(100):
        await cache.get(f"popular_key_{i}")

    # Check hit rate
    metrics = await cache.get_metrics()
    hit_rate = (cache.hits / (cache.hits + cache.misses)) * 100

    # Validate against 80% target
    passed = hit_rate >= 80.0

    print(f"\n  Results:")
    print(f"    Hits: {cache.hits}")
    print(f"    Misses: {cache.misses}")
    print(f"    Hit rate: {hit_rate:.1f}%")
    print(f"    Target: ≥ 80%")
    print(f"    Status: {'✅ PASS' if passed else '❌ FAIL'}")

    return {
        "test": "cache_hit_rate",
        "passed": passed,
        "hit_rate_pct": hit_rate,
        "target_pct": 80.0
    }


async def test_cache_invalidation(cache: RedisCache) -> Dict[str, Any]:
    """Test cache invalidation performance."""
    print("\n" + "="*70)
    print("Test 4: Cache Invalidation")
    print("="*70)

    invalidator = CacheInvalidator(cache)

    # Set test data
    await cache.set("adhd_state", {"energy": "high"}, ttl=60)
    await cache.set("task_detail", "123", {"task_id": "123"}, ttl=60)

    # Test invalidation latency
    print(f"  📊 Testing invalidation latency...")

    invalidate_latency = await measure_operation(
        lambda: invalidator.on_adhd_state_change(),
        "invalidate_adhd_state"
    )

    # Verify cache was cleared
    cached_adhd = await cache.get("adhd_state")
    cached_recs = await cache.get("recommendations")

    # Validate
    passed = (
        cached_adhd is None and
        cached_recs is None and
        invalidate_latency < 10.0  # < 10ms invalidation
    )

    print(f"\n  Results:")
    print(f"    Invalidation latency: {invalidate_latency:.2f}ms")
    print(f"    ADHD state cleared: {'✅' if cached_adhd is None else '❌'}")
    print(f"    Recommendations cleared: {'✅' if cached_recs is None else '❌'}")
    print(f"    Status: {'✅ PASS' if passed else '❌ FAIL'}")

    return {
        "test": "cache_invalidation",
        "passed": passed,
        "invalidation_latency_ms": invalidate_latency
    }


async def test_adhd_safe_performance(cache: RedisCache) -> Dict[str, Any]:
    """Test ADHD-safe performance (< 200ms)."""
    print("\n" + "="*70)
    print("Test 5: ADHD-Safe Performance (< 200ms)")
    print("="*70)

    # Pre-populate cache
    await cache.set("adhd_state", {"energy": "medium"}, ttl=30)
    await cache.set("session", {"active": True}, ttl=60)
    await cache.set("sprint", {"sprint_id": "S-2025.10"}, ttl=300)

    # Simulate dashboard query (3 cached endpoints)
    print(f"  📊 Simulating dashboard query (3 cached endpoints)...")

    start = time.time()

    # Parallel queries
    results = await asyncio.gather(
        cache.get("adhd_state"),
        cache.get("session"),
        cache.get("sprint")
    )

    total_latency = (time.time() - start) * 1000

    # Validate ADHD-safe
    passed = total_latency < 200.0

    print(f"\n  Results:")
    print(f"    Total latency (3 parallel queries): {total_latency:.2f}ms")
    print(f"    Average per query: {total_latency / 3:.2f}ms")
    print(f"    ADHD threshold: < 200ms")
    print(f"    Status: {'✅ PASS' if passed else '❌ FAIL'}")

    return {
        "test": "adhd_safe_performance",
        "passed": passed,
        "total_latency_ms": total_latency,
        "avg_per_query_ms": total_latency / 3,
        "adhd_threshold_ms": 200.0
    }


async def main():
    """Run complete Redis cache performance test suite."""
    print("🚀 Redis Cache Performance Validation Suite")
    print(f"📍 Workspace: /test/workspace")
    print(f"🎯 Target: < {CACHE_HIT_TARGET_MS}ms cache hits, > {LATENCY_REDUCTION_TARGET}% reduction")

    # Initialize cache
    cache = RedisCache(workspace_id="/test/workspace")
    await cache.connect()

    if not cache.enabled:
        print("\n❌ Redis cache not available - cannot run performance tests")
        print("   Please ensure Redis is running on localhost:6379")
        return

    try:
        # Run all tests
        results = []

        results.append(await test_cache_hit_performance(cache))
        results.append(await test_cache_miss_vs_hit(cache))
        results.append(await test_cache_hit_rate(cache))
        results.append(await test_cache_invalidation(cache))
        results.append(await test_adhd_safe_performance(cache))

        # Summary report
        print("\n" + "="*70)
        print("Performance Validation Summary")
        print("="*70)

        all_passed = all(r["passed"] for r in results)
        passed_count = sum(1 for r in results if r["passed"])

        print(f"\n  Tests passed: {passed_count}/{len(results)}")

        for result in results:
            status = "✅ PASS" if result["passed"] else "❌ FAIL"
            print(f"    {status} - {result['test']}")

        # Final metrics
        cache_metrics = await cache.get_metrics()
        print(f"\n  Cache Metrics:")
        print(f"    Total requests: {cache_metrics['total_requests']}")
        print(f"    Hit rate: {cache_metrics['hit_rate']}")
        print(f"    Errors: {cache_metrics['errors']}")

        print("\n" + "="*70)
        if all_passed:
            print("✅ All performance tests PASSED!")
        else:
            print("⚠️  Some performance tests FAILED - review results above")
        print("="*70)

        # Cleanup
        await cache.flush_workspace()

    finally:
        await cache.close()


if __name__ == "__main__":
    asyncio.run(main())
