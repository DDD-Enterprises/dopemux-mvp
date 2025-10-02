#!/usr/bin/env python3
"""
CONPORT-KG-2025 Performance Benchmarking
Part of Phase 7 (Decision #117)

Validates performance targets:
- Tier 1 (Overview): p95 < 50ms
- Tier 2 (Exploration): p95 < 150ms
- Tier 3 (Deep Context): p95 < 500ms

Uses 100 iterations to measure p50, p95, p99 latencies.
"""

import time
import statistics
import sys
import os
from typing import Dict, List

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from queries.overview import OverviewQueries
from queries.exploration import ExplorationQueries
from queries.deep_context import DeepContextQueries


class PerformanceBenchmark:
    """
    Performance validation framework

    Runs 100 iterations of representative queries for each tier.
    Measures p50, p95, p99 latencies.
    """

    def __init__(self, iterations: int = 100, test_decision_id: int = 85):
        self.iterations = iterations
        self.test_id = test_decision_id

    def benchmark_tier1(self) -> Dict:
        """
        Tier 1: Overview Queries
        Target: p95 < 50ms
        """
        print(f"\nBenchmarking Tier 1 (Overview) - {self.iterations} iterations...")

        queries = OverviewQueries()
        times = []

        for i in range(self.iterations):
            start = time.perf_counter()
            result = queries.get_recent_decisions(3)
            elapsed = (time.perf_counter() - start) * 1000  # ms
            times.append(elapsed)

            if i == 0:
                print(f"   First query: {elapsed:.2f}ms (includes connection setup)")

        return self._calculate_stats("Tier 1 (Overview)", times, 50.0)

    def benchmark_tier2(self) -> Dict:
        """
        Tier 2: Exploration Queries
        Target: p95 < 150ms
        """
        print(f"\nBenchmarking Tier 2 (Exploration) - {self.iterations} iterations...")

        queries = ExplorationQueries()
        times = []

        for i in range(self.iterations):
            start = time.perf_counter()
            result = queries.get_decision_neighborhood(self.test_id, max_hops=2)
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

            if i == 0:
                print(f"   First query: {elapsed:.2f}ms (2-hop neighborhood)")

        return self._calculate_stats("Tier 2 (Exploration)", times, 150.0)

    def benchmark_tier3(self) -> Dict:
        """
        Tier 3: Deep Context Queries
        Target: p95 < 500ms
        """
        print(f"\nBenchmarking Tier 3 (Deep Context) - {self.iterations} iterations...")

        queries = DeepContextQueries()
        times = []

        for i in range(self.iterations):
            start = time.perf_counter()
            result = queries.get_full_decision_context(self.test_id)
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

            if i == 0:
                print(f"   First query: {elapsed:.2f}ms (full 3-hop context)")

        return self._calculate_stats("Tier 3 (Deep Context)", times, 500.0)

    def _calculate_stats(self, tier_name: str, times: List[float], target: float) -> Dict:
        """Calculate percentile statistics"""

        p50 = statistics.median(times)
        p95 = statistics.quantiles(times, n=20)[18]  # 95th percentile
        p99 = statistics.quantiles(times, n=100)[98] if len(times) >= 100 else max(times)

        passes = p95 < target

        result = {
            'tier': tier_name,
            'target_ms': target,
            'p50_ms': round(p50, 2),
            'p95_ms': round(p95, 2),
            'p99_ms': round(p99, 2),
            'min_ms': round(min(times), 2),
            'max_ms': round(max(times), 2),
            'passes': passes,
            'iterations': len(times)
        }

        print(f"\n   Results for {tier_name}:")
        print(f"      p50: {result['p50_ms']:.2f}ms")
        print(f"      p95: {result['p95_ms']:.2f}ms (target: <{target}ms)")
        print(f"      p99: {result['p99_ms']:.2f}ms")
        print(f"      Range: {result['min_ms']:.2f}ms - {result['max_ms']:.2f}ms")
        print(f"      {'✅ PASS' if passes else '❌ FAIL'}")

        return result

    def run_all_benchmarks(self) -> Dict:
        """Run complete benchmark suite"""

        print("=" * 70)
        print("CONPORT-KG-2025 Performance Benchmark Suite")
        print(f"Iterations: {self.iterations} per tier")
        print(f"Test decision: #{self.test_id}")
        print("=" * 70)

        results = {
            'tier1': self.benchmark_tier1(),
            'tier2': self.benchmark_tier2(),
            'tier3': self.benchmark_tier3()
        }

        # Summary
        print("\n" + "=" * 70)
        print("BENCHMARK SUMMARY")
        print("=" * 70)

        all_pass = all(r['passes'] for r in results.values())

        for tier_key, stats in results.items():
            status = "✅ PASS" if stats['passes'] else "❌ FAIL"
            print(f"{stats['tier']:25s} p95: {stats['p95_ms']:6.2f}ms  {status}")

        print("\n" + "=" * 70)
        if all_pass:
            print("✅ ALL TIERS PASSED - Performance targets met!")
            print("   No Redis caching needed.")
        else:
            print("⚠️  SOME TIERS FAILED - Optimization needed")
            failed_tiers = [s['tier'] for s in results.values() if not s['passes']]
            print(f"   Failed: {', '.join(failed_tiers)}")
            print("   Recommendation: Add Redis caching for failed tiers")

        print("=" * 70)

        return results


if __name__ == "__main__":
    # Run benchmark suite
    benchmark = PerformanceBenchmark(iterations=100, test_decision_id=85)
    results = benchmark.run_all_benchmarks()

    # Exit with status code
    all_pass = all(r['passes'] for r in results.values())
    sys.exit(0 if all_pass else 1)
