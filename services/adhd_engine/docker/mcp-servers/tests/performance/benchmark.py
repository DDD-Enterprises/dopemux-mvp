"""
Performance Benchmarking Suite for ADHD Services

Comprehensive performance testing framework with ADHD-specific usage patterns,
load testing, and P95 latency validation against targets.
"""

import asyncio
import aiohttp
import time
import statistics
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
import json

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Container for benchmark results."""
    operation: str
    requests_made: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    response_times: List[float] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        return self.successful_requests / max(self.requests_made, 1)

    @property
    def avg_response_time(self) -> float:
        """Calculate average response time."""
        return statistics.mean(self.response_times) if self.response_times else 0

    @property
    def p95_response_time(self) -> float:
        """Calculate 95th percentile response time."""
        if not self.response_times:
            return 0
        return statistics.quantiles(self.response_times, n=20)[18]  # 95th percentile

    @property
    def min_response_time(self) -> float:
        """Get minimum response time."""
        return min(self.response_times) if self.response_times else 0

    @property
    def max_response_time(self) -> float:
        """Get maximum response time."""
        return max(self.response_times) if self.response_times else 0


class ADHDServiceBenchmark:
    """
    Comprehensive benchmarking suite for ADHD services.

    Tests realistic ADHD usage patterns with proper load simulation
    and performance validation against targets.
    """

    def __init__(self, base_url: str = "http://localhost", concurrency: int = 10):
        """
        Initialize benchmark suite.

        Args:
            base_url: Base URL for services
            concurrency: Number of concurrent requests
        """
        self.base_url = base_url.rstrip("/")
        self.concurrency = concurrency
        self.session: Optional[aiohttp.ClientSession] = None

        # ADHD-specific usage patterns
        self.usage_patterns = {
            "adhd_engine_assess_task": {
                "endpoint": "/api/v1/assess-task",
                "method": "POST",
                "headers": {"X-API-Key": "benchmark-key-123"},
                "payload": {
                    "task_description": "Implement user authentication with JWT tokens",
                    "user_id": "test-user"
                },
                "target_p95_ms": 200,  # Target: <200ms P95
                "expected_success_rate": 0.99
            },
            "adhd_engine_energy_level": {
                "endpoint": "/api/v1/energy-level/test-user",
                "method": "GET",
                "headers": {"X-API-Key": "benchmark-key-123"},
                "target_p95_ms": 100,  # Target: <100ms P95
                "expected_success_rate": 0.995
            },
            "adhd_dashboard_metrics": {
                "endpoint": "/api/metrics",
                "method": "GET",
                "headers": {"X-API-Key": "dashboard-key-456"},
                "target_p95_ms": 150,  # Target: <150ms P95
                "expected_success_rate": 0.99
            },
            "activity_capture_health": {
                "endpoint": ":8096/health",
                "method": "GET",
                "target_p95_ms": 50,   # Target: <50ms P95
                "expected_success_rate": 0.999
            }
        }

    async def initialize(self):
        """Initialize HTTP session."""
        self.session = aiohttp.ClientSession()

    async def close(self):
        """Close HTTP session."""
        if self.session:
            await self.session.close()

    async def run_single_benchmark(
        self,
        pattern_name: str,
        request_count: int = 100,
        duration_seconds: Optional[int] = None
    ) -> BenchmarkResult:
        """
        Run benchmark for a single endpoint.

        Args:
            pattern_name: Name of usage pattern to test
            request_count: Number of requests to make
            duration_seconds: Duration to run (alternative to request_count)

        Returns:
            BenchmarkResult with performance metrics
        """
        if pattern_name not in self.usage_patterns:
            raise ValueError(f"Unknown pattern: {pattern_name}")

        pattern = self.usage_patterns[pattern_name]
        result = BenchmarkResult(operation=pattern_name)

        # Prepare request details
        url = f"{self.base_url}{pattern['endpoint']}"
        method = pattern['method']
        headers = pattern.get('headers', {})
        payload = pattern.get('payload')

        logger.info(f"Starting benchmark: {pattern_name}")
        logger.info(f"Target: {url} ({method})")
        logger.info(f"Requests: {request_count}, Concurrency: {self.concurrency}")

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.concurrency)

        async def make_request():
            """Make a single request with timing."""
            async with semaphore:
                start_time = time.time()

                try:
                    if method == "GET":
                        async with self.session.get(url, headers=headers) as response:
                            await response.text()
                            success = response.status == 200
                    elif method == "POST":
                        async with self.session.post(
                            url,
                            headers=headers,
                            json=payload
                        ) as response:
                            await response.text()
                            success = response.status == 200
                    else:
                        success = False
                        result.errors.append(f"Unsupported method: {method}")

                    response_time = (time.time() - start_time) * 1000  # Convert to ms

                    if success:
                        result.successful_requests += 1
                        result.response_times.append(response_time)
                    else:
                        result.failed_requests += 1
                        result.errors.append(f"HTTP {response.status}")

                except Exception as e:
                    result.failed_requests += 1
                    result.errors.append(str(e))

                result.requests_made += 1

        # Run requests
        if duration_seconds:
            # Duration-based testing
            end_time = time.time() + duration_seconds
            tasks = []

            while time.time() < end_time:
                task = asyncio.create_task(make_request())
                tasks.append(task)

                # Limit concurrent tasks
                if len(tasks) >= self.concurrency * 10:
                    await asyncio.gather(*tasks)
                    tasks = []

            if tasks:
                await asyncio.gather(*tasks)

        else:
            # Request count-based testing
            tasks = [make_request() for _ in range(request_count)]
            await asyncio.gather(*tasks)

        logger.info(f"Benchmark complete: {pattern_name}")
        logger.info(f"Success rate: {result.success_rate:.1%}")
        logger.info(f"Avg response: {result.avg_response_time:.1f}ms")
        logger.info(f"P95 response: {result.p95_response_time:.1f}ms")

        return result

    async def run_full_suite(self) -> Dict[str, BenchmarkResult]:
        """
        Run complete benchmark suite against all ADHD services.

        Returns:
            Dict mapping pattern names to BenchmarkResult objects
        """
        results = {}

        logger.info("Starting full ADHD services benchmark suite")
        logger.info("=" * 60)

        for pattern_name in self.usage_patterns.keys():
            try:
                result = await self.run_single_benchmark(pattern_name, request_count=50)
                results[pattern_name] = result

                # Brief pause between tests
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Failed to run benchmark for {pattern_name}: {e}")
                results[pattern_name] = BenchmarkResult(
                    operation=pattern_name,
                    errors=[str(e)]
                )

        logger.info("Benchmark suite complete")
        return results

    def validate_targets(self, results: Dict[str, BenchmarkResult]) -> Dict[str, Dict[str, Any]]:
        """
        Validate benchmark results against performance targets.

        Args:
            results: Benchmark results from run_full_suite()

        Returns:
            Validation results with pass/fail status
        """
        validation_results = {}

        for pattern_name, result in results.items():
            pattern = self.usage_patterns[pattern_name]

            target_p95 = pattern["target_p95_ms"]
            expected_success_rate = pattern["expected_success_rate"]

            # Check P95 response time
            p95_pass = result.p95_response_time <= target_p95

            # Check success rate
            success_rate_pass = result.success_rate >= expected_success_rate

            # Overall pass/fail
            overall_pass = p95_pass and success_rate_pass

            validation_results[pattern_name] = {
                "overall_pass": overall_pass,
                "p95_target_ms": target_p95,
                "p95_actual_ms": result.p95_response_time,
                "p95_pass": p95_pass,
                "success_rate_target": expected_success_rate,
                "success_rate_actual": result.success_rate,
                "success_rate_pass": success_rate_pass,
                "requests_made": result.requests_made,
                "avg_response_time_ms": result.avg_response_time,
            }

        return validation_results

    async def run_adhd_simulation(self, duration_minutes: int = 5) -> Dict[str, Any]:
        """
        Run ADHD-specific usage simulation.

        Simulates realistic ADHD user behavior patterns over time.

        Args:
            duration_minutes: Duration to run simulation

        Returns:
            Simulation results and metrics
        """
        logger.info(f"Starting ADHD usage simulation ({duration_minutes} minutes)")

        simulation_results = {
            "duration_minutes": duration_minutes,
            "patterns_executed": [],
            "total_requests": 0,
            "successful_requests": 0,
            "avg_response_time_ms": 0,
            "p95_response_time_ms": 0,
        }

        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)

        # ADHD usage patterns (weighted by typical usage)
        pattern_weights = {
            "adhd_engine_energy_level": 0.4,  # Frequent energy checks
            "adhd_engine_assess_task": 0.3,   # Task assessments
            "adhd_dashboard_metrics": 0.2,    # Dashboard views
            "activity_capture_health": 0.1,   # Health checks
        }

        all_response_times = []

        while time.time() < end_time:
            # Select pattern based on weights
            import random
            pattern_name = random.choices(
                list(pattern_weights.keys()),
                weights=list(pattern_weights.values())
            )[0]

            # Run single request
            result = await self.run_single_benchmark(pattern_name, request_count=1)

            # Record results
            simulation_results["patterns_executed"].append(pattern_name)
            simulation_results["total_requests"] += result.requests_made
            simulation_results["successful_requests"] += result.successful_requests
            all_response_times.extend(result.response_times)

            # Random delay (ADHD users don't request at fixed intervals)
            await asyncio.sleep(random.uniform(0.5, 3.0))

        # Calculate final metrics
        if all_response_times:
            simulation_results["avg_response_time_ms"] = statistics.mean(all_response_times)
            simulation_results["p95_response_time_ms"] = statistics.quantiles(all_response_times, n=20)[18]

        simulation_results["success_rate"] = (
            simulation_results["successful_requests"] / max(simulation_results["total_requests"], 1)
        )

        logger.info("ADHD simulation complete")
        logger.info(f"Total requests: {simulation_results['total_requests']}")
        logger.info(f"Success rate: {simulation_results['success_rate']:.1%}")
        logger.info(f"Avg response: {simulation_results['avg_response_time_ms']:.1f}ms")
        logger.info(f"P95 response: {simulation_results['p95_response_time_ms']:.1f}ms")

        return simulation_results


async def run_performance_benchmarks():
    """Main function to run performance benchmarks."""
    # Initialize benchmark suite
    benchmark = ADHDServiceBenchmark(
        base_url="http://localhost",
        concurrency=5  # Conservative concurrency for accuracy
    )

    try:
        await benchmark.initialize()

        print("🧪 Starting ADHD Services Performance Benchmark Suite")
        print("=" * 60)

        # Run full benchmark suite
        results = await benchmark.run_full_suite()

        # Validate against targets
        validation = benchmark.validate_targets(results)

        # Run ADHD simulation
        simulation = await benchmark.run_adhd_simulation(duration_minutes=2)

        # Generate comprehensive report
        report = {
            "timestamp": time.time(),
            "benchmark_results": {
                pattern: {
                    "requests_made": result.requests_made,
                    "success_rate": result.success_rate,
                    "avg_response_time_ms": result.avg_response_time,
                    "p95_response_time_ms": result.p95_response_time,
                    "min_response_time_ms": result.min_response_time,
                    "max_response_time_ms": result.max_response_time,
                }
                for pattern, result in results.items()
            },
            "validation_results": validation,
            "simulation_results": simulation,
            "summary": {
                "overall_success_rate": statistics.mean([
                    r.success_rate for r in results.values()
                ]),
                "overall_avg_response_time": statistics.mean([
                    r.avg_response_time for r in results.values()
                ]),
                "targets_met": sum(1 for v in validation.values() if v["overall_pass"]),
                "total_targets": len(validation),
                "target_success_rate": sum(1 for v in validation.values() if v["overall_pass"]) / len(validation)
            }
        }

        # Save report to file
        with open("performance_report.json", "w") as f:
            json.dump(report, f, indent=2)

        # Print summary
        print("\n📊 PERFORMANCE BENCHMARK SUMMARY")
        print("-" * 40)
        print(".1%")
        print(".1f")
        print(".1%")
        print(f"Targets Met: {report['summary']['targets_met']}/{report['summary']['total_targets']}")

        if report['summary']['target_success_rate'] >= 0.8:
            print("✅ PERFORMANCE TARGETS ACHIEVED")
        else:
            print("⚠️ PERFORMANCE TARGETS NOT MET - OPTIMIZATION NEEDED")

        print(f"\n📄 Detailed report saved to: performance_report.json")

        return report

    finally:
        await benchmark.close()


if __name__ == "__main__":
    asyncio.run(run_performance_benchmarks())