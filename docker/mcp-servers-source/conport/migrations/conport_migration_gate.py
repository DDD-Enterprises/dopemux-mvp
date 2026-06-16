#!/usr/bin/env python3
"""Explicit ConPort migration gate with ledger/checksum verification.

This script is intentionally not invoked by normal ConPort startup. Mutation
requires both the `apply` subcommand and DPMX_CONPORT_MIGRATION_APPLY=1.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence
from urllib.parse import unquote, urlparse


APPLY_ENV = "DPMX_CONPORT_MIGRATION_APPLY"
DEFAULT_SCHEMA = "public"
LEDGER_TABLE = "conport_schema_migrations"
MIGRATION_RE = re.compile(r"^(?P<version>\d+)_.*\.sql$")
IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
REQUIRED_MIGRATIONS = {
    "001_enhanced_decision_model.sql",
    "002_decision_patterns_table.sql",
    "003_multi_tenancy_foundation.sql",
    "004_unified_query_indexes.sql",
    "007_worktree_support_simple.sql",
}

REQUIRED_TABLES = (
    "workspace_contexts",
    "decisions",
    "progress_entries",
    "custom_data",
    "entity_relationships",
    "decision_relationships",
    "adhd_metrics",
    "review_reminders",
    "decision_patterns",
    "users",
    "workspaces",
    "user_workspace_access",
)
REQUIRED_COLUMNS = (
    ("decisions", "impact_score"),
    ("decisions", "outcome_status"),
    ("decisions", "user_id"),
    ("decisions", "created_by_instance"),
    ("progress_entries", "user_id"),
    ("progress_entries", "instance_id"),
    ("workspace_contexts", "user_id"),
    ("workspace_contexts", "instance_id"),
    ("session_snapshots", "user_id"),
    ("custom_data", "user_id"),
)
REQUIRED_INDEXES = (
    "idx_decisions_user_fts",
    "idx_decisions_user_workspace_recent",
    "idx_decisions_user_workspace",
    "idx_progress_user_workspace_status",
    "idx_progress_user_recent",
    "idx_custom_data_user_category",
    "idx_progress_instance",
    "idx_progress_workspace_instance",
)


class GateError(RuntimeError):
    """Fail-closed migration gate error."""


@dataclass(frozen=True)
class Migration:
    version: int
    filename: str
    path: Path
    checksum: str


def _json_result(status: str, **fields: Any) -> str:
    payload = {"status": status, **fields}
    return json.dumps(payload, indent=2, sort_keys=True)


def validate_identifier(value: str, label: str = "identifier") -> str:
    if not IDENTIFIER_RE.fullmatch(value):
        raise GateError(f"invalid {label}: {value!r}")
    return value


def _checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def discover_migrations(migrations_dir: Path) -> list[Migration]:
    if not migrations_dir.exists() or not migrations_dir.is_dir():
        raise GateError(f"migrations directory not found: {migrations_dir}")

    migrations: list[Migration] = []
    for path in migrations_dir.iterdir():
        if not path.is_file():
            continue
        if path.name.endswith("_rollback.sql") or "rollback" in path.name:
            continue
        match = MIGRATION_RE.match(path.name)
        if not match:
            continue
        migrations.append(
            Migration(
                version=int(match.group("version")),
                filename=path.name,
                path=path,
                checksum=_checksum(path),
            )
        )

    by_name = {migration.filename for migration in migrations}
    missing = sorted(REQUIRED_MIGRATIONS - by_name)
    if missing:
        raise GateError(f"required migration files missing: {missing}")

    migrations.sort(key=lambda item: (item.version, item.filename))
    return migrations


def connect(database_url: str):
    try:
        import psycopg2
    except ImportError as exc:  # pragma: no cover - depends on runtime image deps.
        raise GateError("psycopg2 is required for ConPort migration gate") from exc

    conn = psycopg2.connect(normalize_database_url(database_url))
    conn.autocommit = True
    return conn


def normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql+asyncpg://"):
        return "postgresql://" + database_url.removeprefix("postgresql+asyncpg://")
    return database_url


def ensure_ledger(conn, schema: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {schema}.{LEDGER_TABLE} (
                version INTEGER PRIMARY KEY,
                filename TEXT NOT NULL UNIQUE,
                checksum_sha256 TEXT NOT NULL,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                execution_seconds NUMERIC(12, 3) NOT NULL DEFAULT 0,
                success BOOLEAN NOT NULL DEFAULT TRUE
            )
            """
        )


def ledger_exists(conn, schema: str) -> bool:
    with conn.cursor() as cur:
        cur.execute("SELECT to_regclass(%s) IS NOT NULL", (f"{schema}.{LEDGER_TABLE}",))
        return bool(cur.fetchone()[0])


def load_ledger(conn, schema: str) -> dict[int, dict[str, Any]]:
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT version, filename, checksum_sha256, success
            FROM {schema}.{LEDGER_TABLE}
            ORDER BY version, filename
            """
        )
        return {
            int(version): {
                "filename": filename,
                "checksum_sha256": checksum,
                "success": bool(success),
            }
            for version, filename, checksum, success in cur.fetchall()
        }


def validate_ledger_rows(
    migrations: Sequence[Migration], rows: dict[int, dict[str, Any]]
) -> list[str]:
    errors: list[str] = []
    for migration in migrations:
        row = rows.get(migration.version)
        if row is None:
            errors.append(f"missing ledger row for {migration.filename}")
            continue
        if row["filename"] != migration.filename:
            errors.append(
                f"ledger filename mismatch for version {migration.version}: "
                f"{row['filename']} != {migration.filename}"
            )
        if not row["success"]:
            errors.append(f"ledger marks {migration.filename} as failed")
        if row["checksum_sha256"] != migration.checksum:
            errors.append(f"checksum mismatch for {migration.filename}")
    return errors


def record_migration(
    conn,
    schema: str,
    migration: Migration,
    execution_seconds: float,
    success: bool,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            f"""
            INSERT INTO {schema}.{LEDGER_TABLE}
                (version, filename, checksum_sha256, execution_seconds, success)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (version) DO UPDATE SET
                filename = EXCLUDED.filename,
                checksum_sha256 = EXCLUDED.checksum_sha256,
                applied_at = NOW(),
                execution_seconds = EXCLUDED.execution_seconds,
                success = EXCLUDED.success
            """,
            (
                migration.version,
                migration.filename,
                migration.checksum,
                round(execution_seconds, 3),
                success,
            ),
        )


def build_psql_invocation(database_url: str, migration: Migration) -> tuple[list[str], dict[str, str]]:
    parsed = urlparse(normalize_database_url(database_url))
    if parsed.scheme not in {"postgresql", "postgres"}:
        raise GateError(f"unsupported PostgreSQL URL scheme: {parsed.scheme}")

    args = ["psql", "-v", "ON_ERROR_STOP=1"]
    if parsed.hostname:
        args.extend(["-h", parsed.hostname])
    if parsed.port:
        args.extend(["-p", str(parsed.port)])
    if parsed.username:
        args.extend(["-U", unquote(parsed.username)])
    db_name = (parsed.path or "").lstrip("/")
    if db_name:
        args.extend(["-d", unquote(db_name)])
    args.extend(["-f", str(migration.path)])

    env = os.environ.copy()
    if parsed.password:
        env["PGPASSWORD"] = unquote(parsed.password)
    return args, env


def run_psql(database_url: str, migration: Migration) -> None:
    args, env = build_psql_invocation(database_url, migration)
    proc = subprocess.run(
        args,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
    )
    if proc.returncode != 0:
        raise GateError(
            f"migration {migration.filename} failed with exit {proc.returncode}:\n"
            f"{proc.stdout}"
        )


def _exists_query(conn, query: str, args: tuple[Any, ...]) -> bool:
    with conn.cursor() as cur:
        cur.execute(query, args)
        return bool(cur.fetchone()[0])


def verify_schema_objects(conn, schema: str) -> list[str]:
    errors: list[str] = []

    for table in REQUIRED_TABLES:
        if not _exists_query(conn, "SELECT to_regclass(%s) IS NOT NULL", (f"{schema}.{table}",)):
            errors.append(f"missing table {schema}.{table}")

    for table, column in REQUIRED_COLUMNS:
        if not _exists_query(
            conn,
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = %s
                  AND table_name = %s
                  AND column_name = %s
            )
            """,
            (schema, table, column),
        ):
            errors.append(f"missing column {schema}.{table}.{column}")

    for index in REQUIRED_INDEXES:
        if not _exists_query(
            conn,
            """
            SELECT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = %s
                  AND indexname = %s
            )
            """,
            (schema, index),
        ):
            errors.append(f"missing index {schema}.{index}")

    return errors


def apply_migrations(database_url: str, migrations: Sequence[Migration], schema: str) -> dict[str, Any]:
    if os.environ.get(APPLY_ENV) != "1":
        raise GateError(f"refusing to mutate database without {APPLY_ENV}=1")

    applied: list[str] = []
    skipped: list[str] = []
    with connect(database_url) as conn:
        ensure_ledger(conn, schema)
        ledger = load_ledger(conn, schema)
        for migration in migrations:
            row = ledger.get(migration.version)
            if row:
                errors = validate_ledger_rows([migration], ledger)
                if errors:
                    raise GateError("; ".join(errors))
                skipped.append(migration.filename)
                continue

            started = time.monotonic()
            try:
                run_psql(database_url, migration)
            except Exception:
                record_migration(conn, schema, migration, time.monotonic() - started, False)
                raise
            record_migration(conn, schema, migration, time.monotonic() - started, True)
            applied.append(migration.filename)

        ledger_errors = validate_ledger_rows(migrations, load_ledger(conn, schema))
        schema_errors = verify_schema_objects(conn, schema)
        if ledger_errors or schema_errors:
            raise GateError("; ".join(ledger_errors + schema_errors))

    return {"applied": applied, "skipped": skipped}


def verify_migrations(database_url: str, migrations: Sequence[Migration], schema: str) -> dict[str, Any]:
    with connect(database_url) as conn:
        if not ledger_exists(conn, schema):
            raise GateError(f"missing migration ledger {schema}.{LEDGER_TABLE}")
        ledger_errors = validate_ledger_rows(migrations, load_ledger(conn, schema))
        schema_errors = verify_schema_objects(conn, schema)
        if ledger_errors or schema_errors:
            raise GateError("; ".join(ledger_errors + schema_errors))
    return {"verified": [migration.filename for migration in migrations]}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=("verify", "apply"),
        help="verify is read-only; apply mutates only with DPMX_CONPORT_MIGRATION_APPLY=1",
    )
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL"),
        help="PostgreSQL URL. Defaults to DATABASE_URL or POSTGRES_URL.",
    )
    parser.add_argument(
        "--migrations-dir",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Directory containing ConPort SQL migrations.",
    )
    parser.add_argument("--schema", default=DEFAULT_SCHEMA, help="Target schema name.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if not args.database_url:
            raise GateError("database URL is required")
        schema = validate_identifier(args.schema, "schema")
        migrations = discover_migrations(args.migrations_dir)
        if args.command == "apply":
            result = apply_migrations(args.database_url, migrations, schema)
        else:
            result = verify_migrations(args.database_url, migrations, schema)
    except GateError as exc:
        print(_json_result("fail-closed", error=str(exc)))
        return 2

    print(_json_result("pass", **result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
