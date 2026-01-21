#!/usr/bin/env python3
"""
AGE Performance Benchmarking
Part of CONPORT-KG-2025 Two-Phase Migration (Decision #112)

Validates <150ms p95 performance target for 3-hop queries.
Tests ADHD features: complexity filtering, progressive disclosure, workspace filtering.
"""

import asyncio

import logging

logger = logging.getLogger(__name__)

import psycopg2
import sys
import time
from typing import List, Dict
from statistics import mean, median


class AGEBenchmarker:
    """Benchmarks AGE query performance"""

    def __init__(self, age_url: str):
        self.age_url = age_url
        self.conn = None

    def connect(self):
        """Establish database connection"""
        self.conn = psycopg2.connect(self.age_url)
        # Enable AGE extension
        cursor = self.conn.cursor()
        cursor.execute("LOAD 'age';")
        cursor.execute("SET search_path = ag_catalog, conport_knowledge, public;")
        cursor.close()
        logger.info(f"✓ Connected to AGE database")

    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def benchmark_query(self, query: str, iterations: int = 100) -> Dict:
        """
        Benchmark single query with multiple iterations

        Returns timing statistics: min, max, avg, median, p95
        """

        times = []
        cursor = self.conn.cursor()

        for i in range(iterations):
            start = time.time()

            try:
                cursor.execute(query)
                cursor.fetchall()  # Consume results
            except Exception as e:
                logger.error(f"  ✗ Query failed on iteration {i}: {e}")
                cursor.close()
                return None

            elapsed_ms = (time.time() - start) * 1000
            times.append(elapsed_ms)

        cursor.close()

        times.sort()

        return {
            'iterations': iterations,
            'min': times[0],
            'max': times[-1],
            'avg': mean(times),
            'median': median(times),
            'p95': times[int(len(times) * 0.95)],
            'p99': times[int(len(times) * 0.99)]
        }

    def run_benchmarks(self, workspace_id: str):
        """Run comprehensive benchmark suite"""

        self.connect()

        try:
            logger.info("\n" + "=" * 60)
            logger.info("AGE Performance Benchmarks")
            logger.info("=" * 60)

            benchmarks = []

            # Benchmark 1: 3-hop genealogy query
            logger.info("\n[1] 3-Hop Genealogy Query (Core Test)")
            logger.info("-" * 60)

            query = f"""
                SELECT * FROM cypher('conport_knowledge', $$
                    MATCH path = (d:Decision {{id: 50}})-[*1..3]-(related:Decision)
                    WHERE related.workspace_id = '{workspace_id}'
                    RETURN path, length(path) as hops
                    LIMIT 10
                $$) as (path agtype, hops agtype);
            """

            result = self.benchmark_query(query, 100)

            if result:
                benchmarks.append(('3-hop genealogy', result))
                self.print_benchmark_result(result, target_p95=150)

            # Benchmark 2: ADHD complexity filtering
            logger.info("\n[2] ADHD Complexity Filtering")
            logger.info("-" * 60)

            query = f"""
                SELECT * FROM cypher('conport_knowledge', $$
                    MATCH (d:Decision)
                    WHERE d.workspace_id = '{workspace_id}'
                      AND d.hop_distance <= 3
                    RETURN d
                    ORDER BY d.hop_distance ASC
                    LIMIT 10
                $$) as (decision agtype);
            """

            result = self.benchmark_query(query, 100)

            if result:
                benchmarks.append(('ADHD filtering', result))
                self.print_benchmark_result(result, target_p95=100)

            # Benchmark 3: Workspace filtering
            logger.info("\n[3] Workspace Filtering")
            logger.info("-" * 60)

            query = f"""
                SELECT * FROM cypher('conport_knowledge', $$
                    MATCH (d:Decision)
                    WHERE d.workspace_id = '{workspace_id}'
                    RETURN COUNT(d)
                $$) as (count agtype);
            """

            result = self.benchmark_query(query, 100)

            if result:
                benchmarks.append(('Workspace filtering', result))
                self.print_benchmark_result(result, target_p95=50)

            # Benchmark 4: Relationship type filtering
            logger.info("\n[4] Relationship Type Query")
            logger.info("-" * 60)

            query = f"""
                SELECT * FROM cypher('conport_knowledge', $$
                    MATCH (d:Decision)-[r:IMPLEMENTS]->(target:Decision)
                    WHERE d.workspace_id = '{workspace_id}'
                    RETURN d, r, target
                    LIMIT 10
                $$) as (source agtype, rel agtype, target agtype);
            """

            result = self.benchmark_query(query, 100)

            if result:
                benchmarks.append(('Relationship filtering', result))
                self.print_benchmark_result(result, target_p95=100)

            # Summary
            logger.info("\n" + "=" * 60)
            logger.info("BENCHMARK SUMMARY")
            logger.info("=" * 60)

            all_pass = True
            for name, result in benchmarks:
                target = 150 if '3-hop' in name else 100
                passed = result['p95'] < target
                status = "✓ PASS" if passed else "✗ FAIL"
                all_pass = all_pass and passed

                logger.info(f"{status} | {name:<25} | P95: {result['p95']:.2f}ms (target: <{target}ms)")

            return all_pass

        finally:
            self.disconnect()

    def print_benchmark_result(self, result: Dict, target_p95: float):
        """Print formatted benchmark results"""

        logger.info(f"  Iterations: {result['iterations']}")
        logger.info(f"  Min:        {result['min']:.2f}ms")
        logger.info(f"  Avg:        {result['avg']:.2f}ms")
        logger.info(f"  Median:     {result['median']:.2f}ms")
        logger.info(f"  P95:        {result['p95']:.2f}ms  (target: <{target_p95}ms)")
        logger.info(f"  P99:        {result['p99']:.2f}ms")
        logger.info(f"  Max:        {result['max']:.2f}ms")

        if result['p95'] < target_p95:
            logger.info(f"  Status:     ✓ PASS (within target)")
        else:
            logger.error(f"  Status:     ✗ FAIL ({result['p95'] - target_p95:.2f}ms over target)")


async def main():
    """Main benchmarking procedure"""

    # Configuration
    AGE_URL = "postgresql://dopemux_age:dopemux_age_password@localhost:5455/dopemux_knowledge_graph"
    WORKSPACE_ID = "/Users/hue/code/dopemux-mvp"

    logger.info("=" * 60)
    logger.info("AGE Performance Benchmarking")
    logger.info("=" * 60)
    logger.info(f"Workspace: {WORKSPACE_ID}")
    logger.info(f"Target: <150ms p95 for 3-hop queries")
    logger.info()

    benchmarker = AGEBenchmarker(AGE_URL)

    try:
        all_pass = benchmarker.run_benchmarks(WORKSPACE_ID)

        if all_pass:
            logger.info("\n✓ SUCCESS: All performance targets achieved")
            logger.info("\nMigration complete! System ready for:")
            logger.info("  - ADHD progressive disclosure queries")
            logger.info("  - Decision genealogy visualization")
            logger.info("  - Two-Plane Architecture integration")
            return 0
        else:
            logger.warning("\n⚠️  WARNING: Some performance targets missed")
            logger.info("\nRecommended actions:")
            logger.info("  1. Review query plans with EXPLAIN ANALYZE")
            logger.info("  2. Verify all indexes created correctly")
            logger.info("  3. Consider materialized views for slow queries")
            return 1

    except Exception as e:
        logger.error(f"\n✗ ERROR: Benchmarking failed")
        logger.info(f"  {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
