#!/usr/bin/env python3
"""
SQLite WAL Performance Test for Multi-Instance Architecture

Tests SQLite WAL mode performance with multiple concurrent instances
to validate whether PostgreSQL migration is necessary.

Based on O3 expert analysis recommendations.

Usage:
    python scripts/test_sqlite_wal_performance.py --instances 10 --duration 25

Success criteria: P99 checkpoint latency ≤ 30ms
"""

import asyncio
import sqlite3
import time
import argparse
import statistics
import os
import tempfile
import numpy as np
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import List, Dict, Any
import json


@dataclass
class PerformanceResult:
    """Performance test results"""
    instance_count: int
    total_operations: int
    duration_seconds: float
    checkpoint_latencies: List[float]
    write_latencies: List[float]
    p99_checkpoint: float
    p95_checkpoint: float
    avg_checkpoint: float
    p99_write: float
    p95_write: float
    avg_write: float
    operations_per_second: float
    success: bool


def configure_sqlite_wal(db_path: str) -> sqlite3.Connection:
    """Configure SQLite with O3 recommended WAL optimizations"""

    db = sqlite3.connect(db_path, timeout=10.0)

    # O3 recommended WAL configuration
    db.execute('PRAGMA journal_mode = WAL')
    db.execute('PRAGMA busy_timeout = 5000')              # 5 second timeout
    db.execute('PRAGMA journal_size_limit = 67110000')    # ~64MB before checkpoint
    db.execute('PRAGMA wal_autocheckpoint = 1000')        # Checkpoint every 1000 pages
    db.execute('PRAGMA synchronous = NORMAL')             # Balance safety/performance
    db.execute('PRAGMA cache_size = -2000')               # 2MB cache
    db.execute('PRAGMA temp_store = MEMORY')              # Store temp tables in memory
    db.execute('PRAGMA mmap_size = 268435456')            # 256MB memory map

    # Verify WAL mode is enabled
    result = db.execute('PRAGMA journal_mode').fetchone()
    if result[0].lower() != 'wal':
        raise RuntimeError(f"Failed to enable WAL mode, got: {result[0]}")

    # Create test table matching ConPort schema
    db.execute('''
        CREATE TABLE IF NOT EXISTS test_decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            instance_id TEXT NOT NULL,
            summary TEXT NOT NULL,
            rationale TEXT,
            implementation_details TEXT,
            tags TEXT,
            timestamp REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create index for better performance
    db.execute('''
        CREATE INDEX IF NOT EXISTS idx_test_decisions_instance
        ON test_decisions(instance_id)
    ''')

    db.commit()
    return db


async def writer_instance(
    instance_id: int,
    db_path: str,
    write_interval_ms: int,
    duration_seconds: int,
    results_queue: asyncio.Queue
):
    """Simulate a Claude Code instance writing to ConPort database"""

    # Each instance gets its own connection
    db = configure_sqlite_wal(db_path)

    write_latencies = []
    checkpoint_latencies = []
    operations = 0

    start_time = time.time()
    end_time = start_time + duration_seconds

    try:
        while time.time() < end_time:
            # Simulate ConPort decision logging
            write_start = time.time()

            db.execute('''
                INSERT INTO test_decisions
                (instance_id, summary, rationale, implementation_details, tags, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                f'instance_{instance_id}',
                f'Architecture decision {operations}',
                f'Rationale for decision {operations} from instance {instance_id}',
                f'Implementation details for operation {operations}',
                f'["tag{operations}", "instance{instance_id}"]',
                time.time()
            ))

            db.commit()
            write_latency = (time.time() - write_start) * 1000  # milliseconds
            write_latencies.append(write_latency)

            # Measure checkpoint latency (critical for O3 validation)
            checkpoint_start = time.time()
            db.execute('PRAGMA wal_checkpoint(PASSIVE)')
            checkpoint_latency = (time.time() - checkpoint_start) * 1000
            checkpoint_latencies.append(checkpoint_latency)

            operations += 1

            # Wait for next write interval
            await asyncio.sleep(write_interval_ms / 1000.0)

    except Exception as e:
        print(f"Instance {instance_id} error: {e}")
    finally:
        db.close()

        # Send results back
        await results_queue.put({
            'instance_id': instance_id,
            'operations': operations,
            'write_latencies': write_latencies,
            'checkpoint_latencies': checkpoint_latencies
        })


async def run_performance_test(
    instance_count: int,
    write_interval_ms: int,
    duration_seconds: int,
    db_path: str = None
) -> PerformanceResult:
    """Run multi-instance SQLite performance test"""

    if db_path is None:
        # Create temporary database
        db_dir = Path("/tmp/dopemux")
        db_dir.mkdir(exist_ok=True)
        db_path = str(db_dir / "test_conport.db")

    # Clean up any existing test database
    if os.path.exists(db_path):
        os.remove(db_path)

    # Initialize database
    db = configure_sqlite_wal(db_path)
    db.close()

    print(f"Starting performance test:")
    print(f"  Instances: {instance_count}")
    print(f"  Write interval: {write_interval_ms}ms")
    print(f"  Duration: {duration_seconds}s")
    print(f"  Database: {db_path}")
    print()

    # Create queue for collecting results
    results_queue = asyncio.Queue()

    # Start all writer instances
    start_time = time.time()
    tasks = [
        writer_instance(i, db_path, write_interval_ms, duration_seconds, results_queue)
        for i in range(instance_count)
    ]

    # Wait for all instances to complete
    await asyncio.gather(*tasks)
    actual_duration = time.time() - start_time

    # Collect results from all instances
    all_write_latencies = []
    all_checkpoint_latencies = []
    total_operations = 0

    for _ in range(instance_count):
        result = await results_queue.get()
        all_write_latencies.extend(result['write_latencies'])
        all_checkpoint_latencies.extend(result['checkpoint_latencies'])
        total_operations += result['operations']

    # Calculate statistics
    if not all_checkpoint_latencies:
        raise RuntimeError("No checkpoint latencies recorded")

    p99_checkpoint = np.percentile(all_checkpoint_latencies, 99)
    p95_checkpoint = np.percentile(all_checkpoint_latencies, 95)
    avg_checkpoint = np.mean(all_checkpoint_latencies)

    p99_write = np.percentile(all_write_latencies, 99)
    p95_write = np.percentile(all_write_latencies, 95)
    avg_write = np.mean(all_write_latencies)

    ops_per_second = total_operations / actual_duration

    # O3 success criteria: P99 checkpoint latency ≤ 30ms
    success = p99_checkpoint <= 30.0

    return PerformanceResult(
        instance_count=instance_count,
        total_operations=total_operations,
        duration_seconds=actual_duration,
        checkpoint_latencies=all_checkpoint_latencies,
        write_latencies=all_write_latencies,
        p99_checkpoint=p99_checkpoint,
        p95_checkpoint=p95_checkpoint,
        avg_checkpoint=avg_checkpoint,
        p99_write=p99_write,
        p95_write=p95_write,
        avg_write=avg_write,
        operations_per_second=ops_per_second,
        success=success
    )


def print_results(result: PerformanceResult):
    """Print formatted test results"""

    print("=" * 60)
    print("SQLite WAL Performance Test Results")
    print("=" * 60)
    print()

    print(f"Test Configuration:")
    print(f"  Instances: {result.instance_count}")
    print(f"  Duration: {result.duration_seconds:.1f}s")
    print(f"  Total Operations: {result.total_operations}")
    print(f"  Operations/sec: {result.operations_per_second:.1f}")
    print()

    print(f"Checkpoint Latency (CRITICAL):")
    print(f"  P99: {result.p99_checkpoint:.2f}ms")
    print(f"  P95: {result.p95_checkpoint:.2f}ms")
    print(f"  Average: {result.avg_checkpoint:.2f}ms")
    print()

    print(f"Write Latency:")
    print(f"  P99: {result.p99_write:.2f}ms")
    print(f"  P95: {result.p95_write:.2f}ms")
    print(f"  Average: {result.avg_write:.2f}ms")
    print()

    # O3 validation criteria
    print(f"O3 Validation Criteria:")
    print(f"  P99 Checkpoint ≤ 30ms: {'✅ PASS' if result.success else '❌ FAIL'}")
    print(f"  Actual P99: {result.p99_checkpoint:.2f}ms")
    print()

    if result.success:
        print("🎉 SQLite WAL performance is ACCEPTABLE for multi-instance use!")
        print("   Recommendation: Proceed with SQLite, no PostgreSQL migration needed")
    else:
        print("⚠️  SQLite WAL performance is INSUFFICIENT for multi-instance use")
        print("   Recommendation: Implement PostgreSQL repository layer")

    print()


def save_results(result: PerformanceResult, output_file: str = None):
    """Save results to JSON file for analysis"""

    if output_file is None:
        timestamp = int(time.time())
        output_file = f"/tmp/dopemux/sqlite_test_results_{timestamp}.json"

    # Convert result to JSON-serializable format
    result_data = {
        'test_metadata': {
            'timestamp': time.time(),
            'test_type': 'sqlite_wal_performance',
            'o3_validated': True
        },
        'configuration': {
            'instance_count': result.instance_count,
            'duration_seconds': result.duration_seconds,
            'total_operations': result.total_operations
        },
        'performance_metrics': {
            'operations_per_second': result.operations_per_second,
            'checkpoint_latency': {
                'p99': result.p99_checkpoint,
                'p95': result.p95_checkpoint,
                'average': result.avg_checkpoint
            },
            'write_latency': {
                'p99': result.p99_write,
                'p95': result.p95_write,
                'average': result.avg_write
            }
        },
        'validation': {
            'o3_criteria_met': result.success,
            'p99_threshold_ms': 30.0,
            'recommendation': 'keep_sqlite' if result.success else 'migrate_postgresql'
        }
    }

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(result_data, f, indent=2)

    print(f"Results saved to: {output_file}")


async def main():
    """Main test runner"""

    parser = argparse.ArgumentParser(description='SQLite WAL Performance Test for Multi-Instance')
    parser.add_argument('--instances', type=int, default=10,
                       help='Number of concurrent instances (default: 10)')
    parser.add_argument('--write-interval', type=int, default=250,
                       help='Write interval in milliseconds (default: 250)')
    parser.add_argument('--duration', type=int, default=25,
                       help='Test duration in seconds (default: 25)')
    parser.add_argument('--database', type=str, default=None,
                       help='Database path (default: /tmp/dopemux/test_conport.db)')
    parser.add_argument('--output', type=str, default=None,
                       help='Output file for results (default: auto-generated)')
    parser.add_argument('--quiet', action='store_true',
                       help='Quiet mode - minimal output')

    args = parser.parse_args()

    if not args.quiet:
        print("SQLite WAL Multi-Instance Performance Test")
        print("Based on O3 Expert Analysis Recommendations")
        print("=" * 60)
        print()

    try:
        # Run performance test
        result = await run_performance_test(
            instance_count=args.instances,
            write_interval_ms=args.write_interval,
            duration_seconds=args.duration,
            db_path=args.database
        )

        # Print results
        if not args.quiet:
            print_results(result)

        # Save results
        save_results(result, args.output)

        # Exit with appropriate code
        exit_code = 0 if result.success else 1
        exit(exit_code)

    except Exception as e:
        print(f"Error running performance test: {e}")
        exit(2)


if __name__ == '__main__':
    asyncio.run(main())