#!/usr/bin/env python3
"""
Validate PostgreSQL/AGE compatibility and concurrent query behavior.

This script is read-only against ConPort runtime tables and outputs a JSON report
that can be attached to strict-closure evidence artifacts.
"""

import argparse
import asyncio
import json
import random
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import asyncpg
except ModuleNotFoundError as exc:  # pragma: no cover - runtime dependency
    raise SystemExit(
        "asyncpg is required for validate_age_pg_compat_stress.py. "
        "Run in an environment/container where asyncpg is installed."
    ) from exc


DEFAULT_DB_URL = "postgresql://dopemux_age:dopemux_age_dev_password@localhost:5456/dopemux_knowledge_graph"
DEFAULT_WORKSPACE_ID = "/Users/hue/code/dopemux-mvp"


async def detect_schema(conn: asyncpg.Connection) -> str:
    for schema in ("ag_catalog", "public"):
        exists = await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = $1
                AND table_name = 'decisions'
            )
            """,
            schema,
        )
        if exists:
            return schema
    raise RuntimeError("Unable to detect schema containing decisions table.")


def percentile(sorted_values: List[float], p: float) -> float:
    if not sorted_values:
        return 0.0
    idx = min(len(sorted_values) - 1, max(0, int(round(p * (len(sorted_values) - 1)))))
    return sorted_values[idx]


async def run_compatibility_checks(conn: asyncpg.Connection, schema: str, workspace_id: str) -> Dict[str, Any]:
    checks: Dict[str, Any] = {}

    postgres_version = await conn.fetchval("SELECT version();")
    checks["postgres_version"] = postgres_version

    age_extension = await conn.fetchrow(
        """
        SELECT extname, extversion
        FROM pg_extension
        WHERE extname = 'age'
        """
    )
    checks["age_extension"] = (
        {"installed": True, "name": age_extension["extname"], "version": age_extension["extversion"]}
        if age_extension
        else {"installed": False}
    )

    age_load_ok = False
    age_load_error: Optional[str] = None
    try:
        await conn.execute("LOAD 'age';")
        age_load_ok = True
    except Exception as exc:  # pragma: no cover - environment-dependent
        age_load_error = str(exc)
    checks["age_load"] = {"ok": age_load_ok, "error": age_load_error}

    required_tables = [
        "decisions",
        "progress_entries",
        "custom_data",
        "entity_relationships",
        "workspace_contexts",
    ]
    table_exists = {}
    for table in required_tables:
        exists = await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = $1
                AND table_name = $2
            )
            """,
            schema,
            table,
        )
        table_exists[table] = bool(exists)
    checks["required_tables"] = table_exists

    counts = await conn.fetchrow(
        f"""
        SELECT
            (SELECT COUNT(*) FROM "{schema}"."decisions" WHERE workspace_id = $1) AS decisions,
            (SELECT COUNT(*) FROM "{schema}"."progress_entries" WHERE workspace_id = $1) AS progress_entries,
            (SELECT COUNT(*) FROM "{schema}"."custom_data" WHERE workspace_id = $1) AS custom_data,
            (SELECT COUNT(*) FROM "{schema}"."entity_relationships" WHERE workspace_id = $1) AS entity_relationships,
            (SELECT COUNT(*) FROM "{schema}"."workspace_contexts" WHERE workspace_id = $1) AS workspace_contexts
        """,
        workspace_id,
    )
    checks["workspace_row_counts"] = dict(counts)

    joins = await conn.fetchrow(
        f"""
        SELECT
            COUNT(*) FILTER (WHERE p.linked_decision_id IS NOT NULL) AS linked_progress_rows,
            COUNT(*) FILTER (WHERE p.linked_decision_id IS NOT NULL AND d.id IS NOT NULL) AS resolvable_links
        FROM "{schema}"."progress_entries" p
        LEFT JOIN "{schema}"."decisions" d ON p.linked_decision_id = d.id
        WHERE p.workspace_id = $1
        """,
        workspace_id,
    )
    checks["linked_decision_integrity"] = dict(joins)

    age_graphs: List[Dict[str, Any]] = []
    if age_extension:
        try:
            rows = await conn.fetch(
                "SELECT graphid, name, namespace FROM ag_catalog.ag_graph ORDER BY graphid;"
            )
            age_graphs = [dict(row) for row in rows]
        except Exception as exc:  # pragma: no cover - environment-dependent
            checks["age_graph_catalog_error"] = str(exc)
    checks["age_graphs"] = age_graphs

    cypher_test = {"executed": False, "ok": False, "error": None}
    if age_graphs:
        graph_name = age_graphs[0]["name"]
        try:
            await conn.fetchval(
                f"SELECT * FROM ag_catalog.cypher('{graph_name}', $$ RETURN 1 $$) AS (n agtype);"
            )
            cypher_test = {"executed": True, "ok": True, "error": None, "graph": graph_name}
        except Exception as exc:  # pragma: no cover - environment-dependent
            cypher_test = {"executed": True, "ok": False, "error": str(exc), "graph": graph_name}
    checks["age_cypher_smoke"] = cypher_test

    return checks


async def run_concurrency_stress(
    pool: asyncpg.Pool,
    schema: str,
    workspace_id: str,
    concurrency: int,
    iterations_per_worker: int,
) -> Dict[str, Any]:
    latency_ms: List[float] = []
    errors = 0
    total_queries = concurrency * iterations_per_worker

    query_fns = [
        lambda conn: conn.fetchval(
            f'SELECT COUNT(*) FROM "{schema}"."decisions" WHERE workspace_id = $1', workspace_id
        ),
        lambda conn: conn.fetchval(
            f'SELECT COUNT(*) FROM "{schema}"."progress_entries" WHERE workspace_id = $1 AND status = $2',
            workspace_id,
            "COMPLETED",
        ),
        lambda conn: conn.fetchval(
            f'SELECT COUNT(*) FROM "{schema}"."entity_relationships" WHERE workspace_id = $1',
            workspace_id,
        ),
        lambda conn: conn.fetch(
            f"""
            SELECT id, summary
            FROM "{schema}"."decisions"
            WHERE workspace_id = $1
            ORDER BY updated_at DESC NULLS LAST
            LIMIT 20
            """,
            workspace_id,
        ),
        lambda conn: conn.fetchval(
            f"""
            SELECT COUNT(*) FROM "{schema}"."progress_entries" p
            JOIN "{schema}"."decisions" d ON p.linked_decision_id = d.id
            WHERE p.workspace_id = $1
            """,
            workspace_id,
        ),
    ]

    async def worker() -> None:
        nonlocal errors
        async with pool.acquire() as conn:
            for _ in range(iterations_per_worker):
                q = random.choice(query_fns)
                started = time.perf_counter()
                try:
                    await q(conn)
                    latency_ms.append((time.perf_counter() - started) * 1000.0)
                except Exception:
                    errors += 1

    started = time.perf_counter()
    await asyncio.gather(*(worker() for _ in range(concurrency)))
    elapsed = time.perf_counter() - started

    lat_sorted = sorted(latency_ms)
    success_queries = len(latency_ms)
    qps = success_queries / elapsed if elapsed > 0 else 0.0

    return {
        "concurrency": concurrency,
        "iterations_per_worker": iterations_per_worker,
        "total_queries_planned": total_queries,
        "total_queries_successful": success_queries,
        "total_queries_failed": errors,
        "error_rate_percent": (errors / total_queries * 100.0) if total_queries else 0.0,
        "elapsed_seconds": elapsed,
        "throughput_qps": qps,
        "latency_ms": {
            "min": min(lat_sorted) if lat_sorted else 0.0,
            "avg": (statistics.mean(lat_sorted) if lat_sorted else 0.0),
            "median": (statistics.median(lat_sorted) if lat_sorted else 0.0),
            "p95": percentile(lat_sorted, 0.95),
            "p99": percentile(lat_sorted, 0.99),
            "max": max(lat_sorted) if lat_sorted else 0.0,
        },
    }


async def main_async(args: argparse.Namespace) -> Dict[str, Any]:
    compat_conn = await asyncpg.connect(args.db_url)
    try:
        schema = await detect_schema(compat_conn)
        compat = await run_compatibility_checks(compat_conn, schema, args.workspace_id)
    finally:
        await compat_conn.close()

    pool = await asyncpg.create_pool(
        dsn=args.db_url,
        min_size=min(2, max(1, max(args.concurrency_levels))),
        max_size=max(2, max(args.concurrency_levels)),
    )
    try:
        stress_runs = []
        for concurrency in args.concurrency_levels:
            run = await run_concurrency_stress(
                pool=pool,
                schema=schema,
                workspace_id=args.workspace_id,
                concurrency=concurrency,
                iterations_per_worker=args.iterations_per_worker,
            )
            stress_runs.append(run)
    finally:
        await pool.close()

    pass_fail = {
        "required_tables_present": all(compat["required_tables"].values()),
        "age_extension_installed": bool(compat["age_extension"].get("installed")),
        "age_load_ok": bool(compat["age_load"].get("ok")),
        "stress_zero_errors": all(r["total_queries_failed"] == 0 for r in stress_runs),
        "stress_p95_under_50ms": all(r["latency_ms"]["p95"] < 50.0 for r in stress_runs),
    }

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "target_db_url": args.db_url,
        "workspace_id": args.workspace_id,
        "detected_schema": schema,
        "compatibility": compat,
        "stress": {
            "iterations_per_worker": args.iterations_per_worker,
            "concurrency_levels": args.concurrency_levels,
            "runs": stress_runs,
        },
        "pass_fail": pass_fail,
        "overall_ok": all(pass_fail.values()),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate AGE/PG compatibility and run concurrent query stress checks."
    )
    parser.add_argument("--db-url", default=DEFAULT_DB_URL, help="PostgreSQL connection URL.")
    parser.add_argument("--workspace-id", default=DEFAULT_WORKSPACE_ID, help="Workspace ID filter.")
    parser.add_argument(
        "--iterations-per-worker",
        type=int,
        default=80,
        help="Number of query iterations per concurrent worker.",
    )
    parser.add_argument(
        "--concurrency-levels",
        type=int,
        nargs="+",
        default=[1, 5, 10, 20],
        help="Concurrency levels to test.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output report path (JSON).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = asyncio.run(main_async(args))
    payload = json.dumps(report, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
