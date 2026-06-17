#!/usr/bin/env python3
"""Operator-run ConPort migration verifier/apply gate."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


FOUNDATION_MIGRATIONS = (
    "001_enhanced_decision_model.sql",
    "002_decision_patterns_table.sql",
    "003_multi_tenancy_foundation.sql",
)

LEDGER_TABLE = "conport_schema_migrations"
LOCK_KEY = 2_001_003


class MigrationGateError(RuntimeError):
    """Raised when the migration gate must fail closed."""


@dataclass(frozen=True)
class MigrationFile:
    name: str
    path: Path
    checksum: str
    sql: str
    rank: int


@dataclass(frozen=True)
class SchemaChecks:
    tables: tuple[str, ...]
    columns: dict[str, tuple[str, ...]]
    views: tuple[str, ...]


def normalize_database_url(raw_url: str) -> str:
    if raw_url.startswith("postgresql+asyncpg://"):
        return "postgresql://" + raw_url.removeprefix("postgresql+asyncpg://")
    return raw_url


def checksum_sql(sql: str) -> str:
    return hashlib.sha256(sql.encode("utf-8")).hexdigest()


def discover_foundation_migrations(migrations_dir: Path) -> list[MigrationFile]:
    missing = [
        name for name in FOUNDATION_MIGRATIONS if not (migrations_dir / name).is_file()
    ]
    if missing:
        raise MigrationGateError(
            "missing required migration files: " + ", ".join(sorted(missing))
        )

    migrations: list[MigrationFile] = []
    for rank, name in enumerate(FOUNDATION_MIGRATIONS, start=1):
        path = migrations_dir / name
        sql = path.read_text(encoding="utf-8")
        migrations.append(
            MigrationFile(
                name=name,
                path=path,
                checksum=checksum_sql(sql),
                sql=sql,
                rank=rank,
            )
        )
    return migrations


def required_schema_checks() -> SchemaChecks:
    return SchemaChecks(
        tables=(
            "decision_relationships",
            "adhd_metrics",
            "review_reminders",
            "decision_patterns",
            "users",
            "workspaces",
            "user_workspace_access",
        ),
        columns={
            "decisions": (
                "impact_score",
                "reversibility",
                "alternatives_considered",
                "success_criteria",
                "review_date",
                "outcome_status",
                "outcome_notes",
                "outcome_date",
                "lessons_learned",
                "cognitive_load",
                "decision_time_minutes",
                "energy_level",
                "requires_followup",
                "user_id",
            ),
            "progress_entries": ("user_id",),
            "workspace_contexts": ("user_id",),
            "session_snapshots": ("user_id",),
            "custom_data": ("user_id",),
        },
        views=("recent_activity", "decisions_needing_review", "pattern_statistics"),
    )


def database_url_from_env() -> str:
    raw_url = os.environ.get("POSTGRES_URL") or os.environ.get("DATABASE_URL")
    if not raw_url:
        raise MigrationGateError("POSTGRES_URL or DATABASE_URL is required")
    return normalize_database_url(raw_url)


async def connect(database_url: str):
    try:
        import asyncpg
    except ImportError as exc:
        raise MigrationGateError("asyncpg is required to run the migration gate") from exc
    try:
        return await asyncpg.connect(database_url)
    except Exception as exc:
        raise MigrationGateError("database connection failed") from exc


async def ledger_exists(conn) -> bool:
    result = await conn.fetchval("SELECT to_regclass($1)", LEDGER_TABLE)
    return result == LEDGER_TABLE


async def ensure_ledger(conn) -> None:
    await conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {LEDGER_TABLE} (
            name TEXT PRIMARY KEY,
            rank INTEGER NOT NULL UNIQUE,
            checksum TEXT NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('applied', 'failed')),
            applied_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            error TEXT
        )
        """
    )


async def fetch_ledger(conn) -> dict[str, dict]:
    rows = await conn.fetch(
        f"""
        SELECT name, rank, checksum, status, error
        FROM {LEDGER_TABLE}
        ORDER BY rank
        """
    )
    return {row["name"]: dict(row) for row in rows}


async def validate_ledger(conn, migrations: Iterable[MigrationFile]) -> list[str]:
    if not await ledger_exists(conn):
        return [f"migration ledger missing: {LEDGER_TABLE}"]

    rows = await fetch_ledger(conn)
    errors: list[str] = []
    for migration in migrations:
        row = rows.get(migration.name)
        if not row:
            errors.append(f"missing ledger row: {migration.name}")
            continue
        if row["status"] != "applied":
            errors.append(f"ledger row is not applied: {migration.name}")
        if row["rank"] != migration.rank:
            errors.append(f"ledger rank mismatch: {migration.name}")
        if row["checksum"] != migration.checksum:
            errors.append(f"checksum mismatch: {migration.name}")
    return errors


async def validate_schema(conn) -> list[str]:
    checks = required_schema_checks()
    errors: list[str] = []

    for table in checks.tables:
        exists = await conn.fetchval("SELECT to_regclass($1)", table)
        if exists != table:
            errors.append(f"missing table: {table}")

    for table, columns in checks.columns.items():
        existing = {
            row["column_name"]
            for row in await conn.fetch(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = $1
                """,
                table,
            )
        }
        for column in columns:
            if column not in existing:
                errors.append(f"missing column: {table}.{column}")

    for view in checks.views:
        exists = await conn.fetchval("SELECT to_regclass($1)", view)
        if exists != view:
            errors.append(f"missing view: {view}")

    return errors


async def verify_gate(conn, migrations: list[MigrationFile]) -> None:
    errors = []
    errors.extend(await validate_ledger(conn, migrations))
    errors.extend(await validate_schema(conn))
    if errors:
        raise MigrationGateError("migration verification failed: " + "; ".join(errors))


async def apply_gate(conn, migrations: list[MigrationFile]) -> None:
    await conn.execute("SELECT pg_advisory_lock($1)", LOCK_KEY)
    try:
        await ensure_ledger(conn)
        rows = await fetch_ledger(conn)
        for migration in migrations:
            row = rows.get(migration.name)
            if row:
                if row["checksum"] != migration.checksum:
                    raise MigrationGateError(f"checksum mismatch: {migration.name}")
                if row["rank"] != migration.rank:
                    raise MigrationGateError(f"ledger rank mismatch: {migration.name}")
                if row["status"] != "applied":
                    raise MigrationGateError(f"ledger row is not applied: {migration.name}")
                continue

            try:
                await conn.execute(migration.sql)
            except Exception as exc:  # pragma: no cover - exercised against live DB
                await conn.execute(
                    f"""
                    INSERT INTO {LEDGER_TABLE} (name, rank, checksum, status, error)
                    VALUES ($1, $2, $3, 'failed', $4)
                    ON CONFLICT (name) DO UPDATE
                    SET status = 'failed', error = EXCLUDED.error
                    """,
                    migration.name,
                    migration.rank,
                    migration.checksum,
                    str(exc),
                )
                raise MigrationGateError(f"migration apply failed: {migration.name}") from exc

            await conn.execute(
                f"""
                INSERT INTO {LEDGER_TABLE} (name, rank, checksum, status)
                VALUES ($1, $2, $3, 'applied')
                """,
                migration.name,
                migration.rank,
                migration.checksum,
            )
            rows[migration.name] = {
                "name": migration.name,
                "rank": migration.rank,
                "checksum": migration.checksum,
                "status": "applied",
                "error": None,
            }

        await verify_gate(conn, migrations)
    finally:
        await conn.execute("SELECT pg_advisory_unlock($1)", LOCK_KEY)


async def run(args: argparse.Namespace) -> dict:
    migrations = discover_foundation_migrations(args.migrations_dir)
    database_url = (
        normalize_database_url(args.database_url)
        if args.database_url
        else database_url_from_env()
    )
    conn = await connect(database_url)
    try:
        if args.apply:
            await apply_gate(conn, migrations)
            return {"status": "applied_verified", "migrations": [m.name for m in migrations]}
        await verify_gate(conn, migrations)
        return {"status": "verified", "migrations": [m.name for m in migrations]}
    finally:
        await conn.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify or explicitly apply the ConPort foundation migration gate."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Mutate the database by applying foundation migrations and recording ledger rows.",
    )
    parser.add_argument(
        "--database-url",
        help="PostgreSQL URL. Defaults to POSTGRES_URL or DATABASE_URL.",
    )
    parser.add_argument(
        "--migrations-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "migrations",
        help="Directory containing ConPort migration SQL files.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON status.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = asyncio.run(run(args))
    except MigrationGateError as exc:
        if args.json:
            print(json.dumps({"status": "failed", "error": str(exc)}, sort_keys=True))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        print(result["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
