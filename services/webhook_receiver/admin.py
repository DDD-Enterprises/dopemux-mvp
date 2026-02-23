#!/usr/bin/env python3
"""Webhook Ledger Admin CLI.

First-class DB introspection and proof commands for the webhook receiver.
Supports SQLite out of the box. Postgres support requires psycopg2/psycopg.
"""

import argparse
import sys
from typing import Any, Dict, List

from ledger.interface import parse_db_url
from storage import resolve_webhook_db_url


def _get_connection(db_url: str) -> Any:
    parsed = parse_db_url(db_url)
    if parsed["backend"] == "sqlite":
        import sqlite3

        conn = sqlite3.connect(parsed["path"])
        conn.row_factory = sqlite3.Row
        return conn, "sqlite"
    elif parsed["backend"] == "postgres":
        try:
            import psycopg2
            import psycopg2.extras

            conn = psycopg2.connect(
                parsed["url"],
                cursor_factory=psycopg2.extras.DictCursor
            )
            return conn, "postgres"
        except ImportError:
            try:
                import psycopg
                from psycopg.rows import dict_row

                conn = psycopg.connect(parsed["url"], row_factory=dict_row)
                return conn, "postgres"
            except ImportError:
                msg = (
                    "Postgres backend requires 'psycopg2' or 'psycopg' module."
                )
                print(f"Error: {msg}")
                sys.exit(1)
    else:
        msg = f"Unsupported backend '{parsed['backend']}'"
        print(f"Error: {msg}")
        sys.exit(1)


def _execute(
    conn: Any, backend: str, query: str, params: tuple = ()
) -> List[Dict[str, Any]]:
    cursor = conn.cursor()
    if backend == "postgres":
        # simple replacement of ? with %s for queries
        query = query.replace("?", "%s")

    cursor.execute(query, params)

    # Check if the query returns rows
    if cursor.description is None:
        conn.commit()
        return []

    if backend == "sqlite":
        return [dict(row) for row in cursor.fetchall()]
    else:
        # For psycopg2 with DictCursor or psycopg with dict_row
        return [dict(row) for row in cursor.fetchall()]


def _table_exists(conn: Any, backend: str, table_name: str) -> bool:
    if backend == "sqlite":
        query = (
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        )
        rows = _execute(conn, backend, query, (table_name,))
        return len(rows) > 0
    else:
        query = (
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='public' AND table_name=?"
        )
        rows = _execute(conn, backend, query, (table_name,))
        return len(rows) > 0


def cmd_stats(conn: Any, backend: str, db_url: str) -> None:
    print(f"db_url: {db_url}")

    # Provider events (webhook_events)
    if _table_exists(conn, backend, "webhook_events"):
        rows = _execute(conn, backend, "SELECT COUNT(*) as c FROM webhook_events")
        print(f"count(*) provider_events: {rows[0]['c']}")
    else:
        print("count(*) provider_events: 0 (table missing)")

    # Legacy webhook events (same as above but spec asks for it)
    print("count(*) webhook_events (legacy): (see provider_events)")

    # Run events
    if _table_exists(conn, backend, "run_events"):
        rows = _execute(conn, backend, "SELECT COUNT(*) as c FROM run_events")
        print(f"count(*) run_events: {rows[0]['c']}")
    else:
        print("count(*) run_events: 0 (table missing)")

    # Async jobs
    if _table_exists(conn, backend, "async_jobs"):
        rows = _execute(conn, backend, "SELECT COUNT(*) as c FROM async_jobs")
        print(f"count(*) async_jobs: {rows[0]['c']}")

        status_query = (
            "SELECT status, COUNT(*) as c FROM async_jobs GROUP BY status"
        )
        status_rows = _execute(conn, backend, status_query)
        if status_rows:
            print("async_jobs by status:")
            for row in status_rows:
                print(f"  {row['status']}: {row['c']}")
    else:
        print("count(*) async_jobs: 0 (table missing)")


def cmd_tail(conn: Any, backend: str, table: str, limit: int) -> None:
    target_table = "webhook_events" if table == "provider_events" else table

    if not _table_exists(conn, backend, target_table):
        print(f"Error: Table '{target_table}' does not exist.")
        sys.exit(1)

    if table == "provider_events":
        query = (
            "SELECT received_at_utc, provider, idempotency_key as delivery_id, "
            "event_type, event_id FROM webhook_events ORDER BY id DESC LIMIT ?"
        )
        rows = _execute(conn, backend, query, (limit,))

        if not rows:
            print("No provider events found.")
            return

        # Print header
        keys = [
            "received_at_utc", "provider", "delivery_id", "event_type",
            "event_id"
        ]
        print("\t".join(keys))
        for row in rows:
            print("\t".join(str(row.get(k, "")) for k in keys))

    elif table == "run_events":
        query = (
            "SELECT created_at_utc, run_id, phase, step_id, partition_id, "
            "provider, event_type, event_id, orphaned FROM run_events "
            "ORDER BY id DESC LIMIT ?"
        )
        rows = _execute(conn, backend, query, (limit,))

        if not rows:
            print("No run events found.")
            return

        keys = [
            "created_at_utc", "run_id", "phase", "step_id", "partition_id",
            "provider", "event_type", "event_id", "orphaned"
        ]
        print("\t".join(keys))
        for row in rows:
            print("\t".join(str(row.get(k, "")) for k in keys))

    else:
        query = f"SELECT * FROM {target_table} ORDER BY id DESC LIMIT ?"
        rows = _execute(conn, backend, query, (limit,))

        if not rows:
            print(f"No rows found in {target_table}.")
            return

        keys = list(rows[0].keys())
        print("\t".join(keys))
        for row in rows:
            print("\t".join(str(row.get(k, "")) for k in keys))


def cmd_dedupe_check(conn: Any, backend: str, delivery_id: str) -> None:
    if not _table_exists(conn, backend, "webhook_events"):
        print("Error: Table 'webhook_events' does not exist.")
        sys.exit(1)

    query = (
        "SELECT id, received_at_utc, provider, event_type, event_id "
        "FROM webhook_events WHERE idempotency_key = ?"
    )
    rows = _execute(conn, backend, query, (delivery_id,))

    if rows:
        print(f"Delivery ID '{delivery_id}' EXISTS. Matching rows: {len(rows)}")
        for i, row in enumerate(rows, 1):
            details = (
                f"id={row.get('id')}, provider={row.get('provider')}, "
                f"event_type={row.get('event_type')}, "
                f"event_id={row.get('event_id')}, "
                f"received_at_utc={row.get('received_at_utc')}"
            )
            print(f"  Row {i}: {details}")
    else:
        print(f"Delivery ID '{delivery_id}' does NOT exist.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Webhook Ledger Admin CLI")
    subparsers = parser.add_subparsers(dest="noun", required=True)

    db_parser = subparsers.add_parser("db", help="Database operations")
    db_sub = db_parser.add_subparsers(dest="verb", required=True)

    # db stats
    db_sub.add_parser("stats", help="Show database table statistics")

    # db tail
    tail_parser = db_sub.add_parser("tail", help="Tail rows from a table")
    tail_parser.add_argument(
        "--table", required=True,
        help="Table to tail (e.g. provider_events, run_events)"
    )
    tail_parser.add_argument(
        "--limit", type=int, default=20,
        help="Number of rows to fetch (default: 20)"
    )

    # db dedupe-check
    dedupe_parser = db_sub.add_parser("dedupe-check", help="Check if a delivery exists")
    dedupe_parser.add_argument(
        "--delivery-id", required=True,
        help="The delivery idempotency key to check"
    )

    args = parser.parse_args()

    db_url = resolve_webhook_db_url()
    conn, backend = _get_connection(db_url)

    try:
        if args.noun == "db":
            if args.verb == "stats":
                cmd_stats(conn, backend, db_url)
            elif args.verb == "tail":
                cmd_tail(conn, backend, args.table, args.limit)
            elif args.verb == "dedupe-check":
                cmd_dedupe_check(conn, backend, args.delivery_id)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
