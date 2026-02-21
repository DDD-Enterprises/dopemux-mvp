#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sqlite3
from pathlib import Path
from typing import Iterable, List

ROOT = Path(__file__).resolve().parents[1]
LEDGER_ROOT = ROOT / "services" / "webhook_receiver"


def _parse_db_url(db_url: str) -> dict:
    token = db_url.strip()
    if token.startswith("sqlite:///"):
        path = token.removeprefix("sqlite:///")
        if not path:
            raise ValueError("Invalid sqlite URL")
        return {"backend": "sqlite", "path": "/" + path if not path.startswith("/") else path}
    if token.startswith("postgresql://") or token.startswith("postgresql+psycopg://"):
        return {"backend": "postgres", "url": token}
    raise ValueError(f"Unsupported DB URL: {token}")


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
        import psycopg
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("psycopg is required for postgres migrations") from exc

    with psycopg.connect(db_url) as conn:
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
