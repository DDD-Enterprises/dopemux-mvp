#!/usr/bin/env python3
"""
Component 5 Performance Validation
==================================

Tests HTTP communication latency and throughput for cross-plane queries.

**ADHD Performance Targets**:
- Query latency: < 200ms (attention-safe)
- Batch operations: < 500ms
- Connection overhead: < 50ms
- Total request cycle: < 300ms

**Architecture**:
ConPort/UI → DopeconBridge (3016) → Orchestrator (3017) → ConPort MCP
"""

import asyncio
import aiohttp
import time
import statistics
from typing import List, Dict, Any
from datetime import datetime

# Test configuration
BRIDGE_URL = "http://localhost:3016"
ORCHESTRATOR_URL = "http://localhost:3017"
WARMUP_REQUESTS = 5
TEST_REQUESTS = 20

# ADHD performance thresholds
LATENCY_TARGET = 0.200  # 200ms - attention-safe
BATCH_TARGET = 0.500    # 500ms - acceptable for batch
CONNECTION_TARGET = 0.050  # 50ms - connection overhead

class PerformanceMetrics:
    """Track performance metrics with ADHD awareness."""

    def __init__(self, operation: str):
        self.operation = operation
        self.latencies: List[float] = []
        self.start_time = time.time()

    def record(self, latency: float):
        """Record single operation latency."""
        self.latencies.append(latency)

    def summary(self) -> Dict[str, Any]:
        """Generate performance summary."""
        if not self.latencies:
            return {"operation": self.operation, "status": "no data"}

        return {
            "operation": self.operation,
            "count": len(self.latencies),
            "min_ms": min(self.latencies) * 1000,
            "max_ms": max(self.latencies) * 1000,
            "avg_ms": statistics.mean(self.latencies) * 1000,
            "p50_ms": statistics.median(self.latencies) * 1000,
            "p95_ms": sorted(self.latencies)[int(len(self.latencies) * 0.95)] * 1000,
            "p99_ms": sorted(self.latencies)[int(len(self.latencies) * 0.99)] * 1000,
            "adhd_safe": statistics.mean(self.latencies) < LATENCY_TARGET,
            "target_ms": LATENCY_TARGET * 1000
        }


async def test_endpoint(session: aiohttp.ClientSession, url: str, metrics: PerformanceMetrics):
    """Test single endpoint performance."""
    start = time.time()
    try:
        async with session.get(url) as resp:
            await resp.json()
            latency = time.time() - start
            metrics.record(latency)
            return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


async def warmup(session: aiohttp.ClientSession, url: str):
    """Warmup endpoint to eliminate cold-start effects."""
    print(f"  🔥 Warming up endpoint...")
    for _ in range(WARMUP_REQUESTS):
        try:
            async with session.get(url) as resp:
                await resp.json()
        except Exception as e:
            pass


            logger.error(f"Error: {e}")
async def test_dopecon_bridge_endpoints():
    """Test DopeconBridge → Orchestrator latency."""
    print("\n" + "="*70)
    print("Component 5 Performance Validation")
    print("="*70)

    endpoints = [
        ("/orchestrator/tasks", "List Tasks"),
        ("/orchestrator/adhd-state", "ADHD State"),
        ("/orchestrator/recommendations", "Task Recommendations"),
        ("/orchestrator/session", "Session Status"),
        ("/orchestrator/active-sprint", "Active Sprint")
    ]

    results = []

    async with aiohttp.ClientSession() as session:
        for path, name in endpoints:
            print(f"\n📊 Testing: {name}")
            url = f"{BRIDGE_URL}{path}"

            # Warmup
            await warmup(session, url)

            # Performance test
            metrics = PerformanceMetrics(name)
            successes = 0

            for i in range(TEST_REQUESTS):
                if await test_endpoint(session, url, metrics):
                    successes += 1
                await asyncio.sleep(0.05)  # 50ms between requests

            summary = metrics.summary()
            results.append(summary)

            # Print results
            adhd_status = "✅ ADHD-Safe" if summary["adhd_safe"] else "⚠️  Needs optimization"
            print(f"  Requests: {successes}/{TEST_REQUESTS}")
            print(f"  Latency (avg): {summary['avg_ms']:.1f}ms")
            print(f"  Latency (p95): {summary['p95_ms']:.1f}ms")
            print(f"  Target: {summary['target_ms']:.0f}ms {adhd_status}")

    return results


async def test_direct_orchestrator():
    """Test direct orchestrator access (baseline)."""
    print("\n" + "="*70)
    print("Direct Orchestrator Performance (Baseline)")
    print("="*70)

    url = f"{ORCHESTRATOR_URL}/tasks"
    metrics = PerformanceMetrics("Direct Orchestrator")

    async with aiohttp.ClientSession() as session:
        print(f"\n📊 Testing: Direct Access")
        await warmup(session, url)

        for _ in range(TEST_REQUESTS):
            await test_endpoint(session, url, metrics)
            await asyncio.sleep(0.05)

        summary = metrics.summary()
        print(f"  Latency (avg): {summary['avg_ms']:.1f}ms")
        print(f"  Latency (p95): {summary['p95_ms']:.1f}ms")

        return summary


async def test_connection_overhead():
    """Measure DopeconBridge connection overhead."""
    print("\n" + "="*70)
    print("Connection Overhead Analysis")
    print("="*70)

    # Test direct orchestrator
    direct_summary = await test_direct_orchestrator()

    # Test via bridge
    url = f"{BRIDGE_URL}/orchestrator/tasks"
    bridge_metrics = PerformanceMetrics("Via Bridge")

    async with aiohttp.ClientSession() as session:
        await warmup(session, url)

        for _ in range(TEST_REQUESTS):
            await test_endpoint(session, url, bridge_metrics)
            await asyncio.sleep(0.05)

    bridge_summary = bridge_metrics.summary()

    # Calculate overhead
    overhead_ms = bridge_summary["avg_ms"] - direct_summary["avg_ms"]
    overhead_pct = (overhead_ms / direct_summary["avg_ms"]) * 100

    print(f"\n📈 Overhead Analysis:")
    print(f"  Direct: {direct_summary['avg_ms']:.1f}ms")
    print(f"  Via Bridge: {bridge_summary['avg_ms']:.1f}ms")
    print(f"  Overhead: {overhead_ms:.1f}ms ({overhead_pct:.1f}%)")

    overhead_safe = overhead_ms < (CONNECTION_TARGET * 1000)
    print(f"  Target: {CONNECTION_TARGET * 1000:.0f}ms {'✅ Acceptable' if overhead_safe else '⚠️  High'}")

    return {
        "direct_ms": direct_summary["avg_ms"],
        "bridge_ms": bridge_summary["avg_ms"],
        "overhead_ms": overhead_ms,
        "overhead_pct": overhead_pct,
        "overhead_safe": overhead_safe
    }


async def test_concurrent_queries():
    """Test concurrent query performance."""
    print("\n" + "="*70)
    print("Concurrent Query Performance")
    print("="*70)

    endpoints = [
        f"{BRIDGE_URL}/orchestrator/tasks",
        f"{BRIDGE_URL}/orchestrator/adhd-state",
        f"{BRIDGE_URL}/orchestrator/session"
    ]

    async with aiohttp.ClientSession() as session:
        for concurrency in [1, 5, 10]:
            print(f"\n📊 Testing: {concurrency} concurrent requests")

            start = time.time()
            tasks = []

            for _ in range(concurrency):
                for url in endpoints:
                    task = session.get(url)
                    tasks.append(task)

            responses = await asyncio.gather(*tasks, return_exceptions=True)
            duration = time.time() - start

            successes = sum(1 for r in responses if not isinstance(r, Exception))
            total_requests = len(tasks)

            print(f"  Total requests: {total_requests}")
            print(f"  Successes: {successes}")
            print(f"  Duration: {duration * 1000:.1f}ms")
            print(f"  Throughput: {total_requests / duration:.1f} req/s")


def print_summary_report(results: List[Dict[str, Any]], overhead: Dict[str, Any]):
    """Print comprehensive performance summary."""
    print("\n" + "="*70)
    print("Performance Summary Report")
    print("="*70)

    print("\n📊 ADHD Performance Validation:")
    all_safe = all(r.get("adhd_safe", False) for r in results)
    print(f"  Status: {'✅ All endpoints ADHD-safe' if all_safe else '⚠️  Some endpoints need optimization'}")
    print(f"  Target: < {LATENCY_TARGET * 1000:.0f}ms average latency")

    print("\n📈 Endpoint Performance:")
    for result in results:
        status = "✅" if result.get("adhd_safe", False) else "⚠️ "
        print(f"  {status} {result['operation']}: {result['avg_ms']:.1f}ms avg, {result['p95_ms']:.1f}ms p95")

    print("\n🔗 Connection Overhead:")
    status = "✅" if overhead["overhead_safe"] else "⚠️ "
    print(f"  {status} Bridge overhead: {overhead['overhead_ms']:.1f}ms ({overhead['overhead_pct']:.1f}%)")
    print(f"  Target: < {CONNECTION_TARGET * 1000:.0f}ms")

    print("\n💡 Architecture Performance:")
    avg_latency = statistics.mean([r["avg_ms"] for r in results])
    print(f"  Average query latency: {avg_latency:.1f}ms")
    print(f"  Round-trip (Bridge→Orchestrator→ConPort): ~{avg_latency * 2:.1f}ms")
    print(f"  ADHD attention budget: {(LATENCY_TARGET * 1000) - avg_latency:.1f}ms remaining")

    print("\n" + "="*70)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("="*70)


async def main():
    """Run complete performance validation suite."""
    print("🚀 Starting Component 5 Performance Validation...")
    print(f"📍 DopeconBridge: {BRIDGE_URL}")
    print(f"📍 Orchestrator: {ORCHESTRATOR_URL}")
    print(f"🎯 ADHD Target: < {LATENCY_TARGET * 1000:.0f}ms per query")

    try:
        # Test all endpoints
        results = await test_dopecon_bridge_endpoints()

        # Measure overhead
        overhead = await test_connection_overhead()

        # Test concurrent load
        await test_concurrent_queries()

        # Summary report
        print_summary_report(results, overhead)

        print("\n✅ Performance validation complete!")

    except Exception as e:
        print(f"\n❌ Performance validation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
