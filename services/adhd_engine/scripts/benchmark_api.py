#!/usr/bin/env python3
\"\"\"Performance benchmarking script for ADHD Engine APIs.

import logging

logger = logging.getLogger(__name__)


Usage:
    python scripts/benchmark_api.py --endpoint /api/v1/energy-level/{user_id} --iterations 100 --concurrency 10

Measures:
- Average response time
- P95 latency
- Cache hit rate (if monitoring available)
- Error rate

Requirements:
- httpx for async HTTP
- rich for pretty output
- ADHD Engine running on localhost:8001

\"\"\"

import asyncio
import time
from typing import Optional
from dataclasses import dataclass
from statistics import mean, median
from collections import defaultdict

import click
import httpx
from rich.console import Console
from rich.table import Table
from rich import print as rprint

@dataclass
class BenchmarkResult:
    endpoint: str
    iterations: int
    concurrency: int
    avg_response_time: float
    p95_latency: float
    min_response_time: float
    max_response_time: float
    error_rate: float
    cache_hit_rate: Optional[float] = None

async def benchmark_endpoint(
    endpoint: str,
    iterations: int,
    concurrency: int,
    api_key: str,
    user_id: str = "test_user"
):
    \"\"\"Benchmark a single API endpoint with concurrency.\"\"\"
    console = Console()

    # Prepare URL
    base_url = "http://localhost:8001"
    url = f"{base_url}{endpoint.format(user_id=user_id)}"

    # HTTP client with connection pooling
    async with httpx.AsyncClient(
        limits=httpx.Limits(max_keepalive_connections=concurrency, max_connections=concurrency)
    ) as client:
        # Headers
        headers = {"X-API-Key": api_key}

        # Track results
        response_times = []
        errors = 0
        cache_hits = 0
        total_requests = 0

        # Run with concurrency
        semaphore = asyncio.Semaphore(concurrency)

        async def make_request():
            async with semaphore:
                start_time = time.time()
                try:
                    response = await client.get(url, headers=headers, timeout=5.0)
                    elapsed = time.time() - start_time

                    # Check for cache hit (heuristic: response time < 50ms)
                    if elapsed < 0.05:
                        cache_hits += 1

                    response_times.append(elapsed)
                    total_requests += 1

                    if response.status_code != 200:
                        errors += 1
                        console.logger.error(f"[red]ERROR[/red]: {response.status_code} - {response.text[:100]}")

                except Exception as e:
                    errors += 1
                    console.logger.error(f"[red]REQUEST FAILED[/red]: {str(e)}")

        # Execute concurrent requests
        tasks = [make_request() for _ in range(iterations)]
        await asyncio.gather(*tasks, return_exceptions=True)

        # Calculate statistics
        if response_times:
            avg_time = mean(response_times)
            p95_latency = sorted(response_times)[-int(len(response_times) * 0.05)]
            min_time = min(response_times)
            max_time = max(response_times)
            cache_hit_rate = (cache_hits / total_requests * 100) if total_requests > 0 else 0
            error_rate = (errors / total_requests * 100) if total_requests > 0 else 0
        else:
            avg_time = float('inf')
            p95_latency = float('inf')
            min_time = float('inf')
            max_time = 0
            cache_hit_rate = 0
            error_rate = 100

        return BenchmarkResult(
            endpoint=endpoint,
            iterations=iterations,
            concurrency=concurrency,
            avg_response_time=avg_time,
            p95_latency=p95_latency,
            min_response_time=min_time,
            max_response_time=max_time,
            error_rate=error_rate,
            cache_hit_rate=cache_hit_rate
        )

@click.command()
@click.option('--endpoint', '-e', required=True, help='API endpoint to benchmark')
@click.option('--iterations', '-i', type=int, default=100, help='Number of requests')
@click.option('--concurrency', '-c', type=int, default=10, help='Concurrent requests')
@click.option('--api-key', '-k', default='test', help='API key for authentication')
@click.option('--user-id', '-u', default='test_user', help='User ID for requests')
def main(endpoint, iterations, concurrency, api_key, user_id):
    \"\"\"Run API benchmark.\"\"\"
    console = Console()

    rlogger.info(f"[bold cyan]🚀 Benchmarking ADHD Engine API[/bold cyan]")
    rlogger.info(f"Endpoint: {endpoint}")
    rlogger.info(f"Iterations: {iterations}")
    rlogger.info(f"Concurrency: {concurrency}")
    rlogger.info(f"User ID: {user_id}")
    rlogger.info("=" * 60)

    start_time = time.time()
    result = asyncio.run(benchmark_endpoint(endpoint, iterations, concurrency, api_key, user_id))
    end_time = time.time()

    # Create results table
    table = Table(title=f"Benchmark Results - {result.endpoint}")
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")

    table.add_row("Iterations", str(result.iterations))
    table.add_row("Concurrency", str(result.concurrency))
    table.add_row("Avg Response Time", f"{result.avg_response_time:.2f}s")
    table.add_row("P95 Latency", f"{result.p95_latency:.2f}s")
    table.add_row("Min Response Time", f"{result.min_response_time:.2f}s")
    table.add_row("Max Response Time", f"{result.max_response_time:.2f}s")
    table.add_row("Cache Hit Rate", f"{result.cache_hit_rate:.1f}%")
    table.add_row("Error Rate", f"{result.error_rate:.1f}%")
    table.add_row("Total Duration", f"{end_time - start_time:.2f}s")

    console.logger.info(table)

    # Success indicators
    if result.avg_response_time < 0.1:
        rlogger.info("[bold green]✅ Performance target met (<100ms average)[/bold green]")
    else:
        rlogger.info("[bold yellow]⚠️ Performance target not met[/bold yellow]")

    if result.cache_hit_rate > 80:
        rlogger.info("[bold green]✅ Cache hit rate target met (>80%)[/bold green]")
    else:
        rlogger.info("[bold yellow]⚠️ Cache hit rate target not met[/bold yellow]")

    if result.error_rate == 0:
        rlogger.error("[bold green]✅ Zero errors - excellent![/bold green]")
    else:
        rlogger.error(f"[bold red]❌ Errors: {result.error_rate:.1f}%[/bold red]")

if __name__ == "__main__":
    main()