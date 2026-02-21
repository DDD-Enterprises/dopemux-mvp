#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sqlite3
from pathlib import Path
from typing import Dict, Iterable, List

ROOT = Path(__file__).resolve().parents[1]
LEDGER_ROOT = ROOT / "services" / "webhook_receiver"


def _parse_db_url(db_url: str) -> Dict[str, str]:
    """
    Delegate DB URL parsing to the canonical implementation used by the webhook ledger.

    This avoids duplicating logic and keeps supported schemes in sync with
    services/webhook_receiver/ledger/interface.py.
    """
    # Import lazily and ensure the project root is on sys.path so the
    # services package is importable when this script is run directly.
    import sys

    root_str = str(ROOT)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)

    from services.webhook_receiver.ledger.interface import parse_db_url as ledger_parse_db_url

    return ledger_parse_db_url(db_url)


def _migration_files(backend: str) -> List[Path]:
    migration_dir = LEDGER_ROOT / "migrations" / backend
    if not migration_dir.exists():
        raise FileNotFoundError(f"Missing migration dir: {migration_dir}")
    return sorted(migration_dir.glob("*.sql"), key=lambda p: p.name)


def _apply_sqlite(db_path: str, migrations: Iterable[Path]) -> None:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
              version TEXT PRIMARY KEY,
              applied_at_utc TEXT NOT NULL
            )
            """
        )
        for migration in migrations:
            version = migration.name
            row = conn.execute("SELECT version FROM schema_migrations WHERE version = ?", (version,)).fetchone()
            if row:
                continue
            conn.executescript(migration.read_text(encoding="utf-8"))
            conn.execute(
                "INSERT INTO schema_migrations(version, applied_at_utc) VALUES(?, strftime('%Y-%m-%dT%H:%M:%fZ','now'))",
                (version,),
            )
        conn.commit()


def _apply_postgres(db_url: str, migrations: Iterable[Path]) -> None:
    try:
        import psycopg2
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("psycopg2 is required for postgres migrations") from exc

    with psycopg2.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                  version TEXT PRIMARY KEY,
                  applied_at_utc TIMESTAMPTZ NOT NULL DEFAULT (now() at time zone 'utc')
                )
                """
            )
            for migration in migrations:
                version = migration.name
                cur.execute("SELECT version FROM schema_migrations WHERE version = %s", (version,))
                if cur.fetchone() is not None:
                    continue
                cur.execute(migration.read_text(encoding="utf-8"))
                cur.execute("INSERT INTO schema_migrations(version) VALUES(%s)", (version,))


def main() -> None:
    parser = argparse.ArgumentParser("webhook ledger migrations")
    parser.add_argument("--db", dest="db_url", default=os.getenv("WEBHOOK_DB_URL", ""))
    args = parser.parse_args()

    if not str(args.db_url).strip():
        raise SystemExit("Missing --db or WEBHOOK_DB_URL")

    parsed = _parse_db_url(str(args.db_url))
    migrations = _migration_files(parsed["backend"])
    if parsed["backend"] == "sqlite":
        _apply_sqlite(parsed["path"], migrations)
    else:
        _apply_postgres(parsed["url"], migrations)


if __name__ == "__main__":
    main()
