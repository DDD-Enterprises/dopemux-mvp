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
from urllib.parse import unquote, urlparse, urlsplit, urlunsplit


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

BASE_SCHEMA_TABLES = (
    "workspace_contexts",
    "decisions",
    "progress_entries",
    "session_snapshots",
    "custom_data",
    "entity_relationships",
    "search_cache",
)
BASE_SCHEMA_FUNCTIONS = ("update_modified_column",)
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
REQUIRED_VIEWS = (
    "decisions_needing_review",
    "pattern_statistics",
)
MIGRATION_MARKERS = {
    1: "001_enhanced_decision_model",
    2: "002_decision_patterns_table",
}


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


def validate_supported_schema(schema: str) -> str:
    if schema != DEFAULT_SCHEMA:
        raise GateError(
            "unsupported schema: ConPort migrations contain public-qualified and "
            f"unqualified SQL; only {DEFAULT_SCHEMA!r} is supported"
        )
    return schema


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
    normalized_url = normalize_database_url(database_url)
    parsed = urlparse(normalized_url)
    if parsed.scheme not in {"postgresql", "postgres"}:
        raise GateError(f"unsupported PostgreSQL URL scheme: {parsed.scheme}")

    env = os.environ.copy()
    if parsed.password:
        env["PGPASSWORD"] = unquote(parsed.password)

    split_url = urlsplit(normalized_url)
    safe_netloc = split_url.netloc
    if "@" in safe_netloc:
        userinfo, hostinfo = safe_netloc.rsplit("@", 1)
        username = userinfo.split(":", 1)[0]
        safe_netloc = f"{username}@{hostinfo}" if username else hostinfo
    safe_url = urlunsplit(
        (split_url.scheme, safe_netloc, split_url.path, split_url.query, split_url.fragment)
    )

    args = ["psql", "-v", "ON_ERROR_STOP=1", "-d", safe_url, "-f", str(migration.path)]
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


def table_exists(conn, schema: str, table: str) -> bool:
    return _exists_query(
        conn,
        "SELECT to_regclass(%s) IS NOT NULL",
        (f"{schema}.{table}",),
    )


def column_exists(conn, schema: str, table: str, column: str) -> bool:
    return _exists_query(
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
    )


def index_exists(conn, schema: str, index: str) -> bool:
    return _exists_query(
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
    )


def view_exists(conn, schema: str, view: str) -> bool:
    return _exists_query(
        conn,
        """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.views
            WHERE table_schema = %s
              AND table_name = %s
        )
        """,
        (schema, view),
    )


def function_exists(conn, schema: str, function: str) -> bool:
    return _exists_query(
        conn,
        """
        SELECT EXISTS (
            SELECT 1
            FROM pg_proc p
            JOIN pg_namespace n ON n.oid = p.pronamespace
            WHERE n.nspname = %s
              AND p.proname = %s
        )
        """,
        (schema, function),
    )


def migration_marker_exists(conn, schema: str, marker: str) -> bool:
    if not table_exists(conn, schema, "custom_data"):
        return False
    return _exists_query(
        conn,
        f"""
        SELECT EXISTS (
            SELECT 1
            FROM {schema}.custom_data
            WHERE workspace_id = '_system'
              AND category = 'migrations'
              AND key = %s
        )
        """,
        (marker,),
    )


def preflight_base_schema(conn, schema: str) -> list[str]:
    errors: list[str] = []
    for table in BASE_SCHEMA_TABLES:
        if not table_exists(conn, schema, table):
            errors.append(
                f"missing base table {schema}.{table}; run schema.sql before gated migrations"
            )
    for function in BASE_SCHEMA_FUNCTIONS:
        if not function_exists(conn, schema, function):
            errors.append(
                f"missing base function {schema}.{function}; "
                "run schema.sql before gated migrations"
            )
    return errors


def migration_schema_errors(conn, schema: str, version: int) -> list[str]:
    checks: dict[int, tuple[str, ...]] = {
        1: (
            "column:decisions:impact_score",
            "column:decisions:outcome_status",
            "table:decision_relationships",
            "table:adhd_metrics",
            "table:review_reminders",
            "view:decisions_needing_review",
        ),
        2: ("table:decision_patterns", "view:pattern_statistics"),
        3: (
            "column:decisions:user_id",
            "column:progress_entries:user_id",
            "column:workspace_contexts:user_id",
            "column:session_snapshots:user_id",
            "column:custom_data:user_id",
            "table:users",
            "table:workspaces",
            "table:user_workspace_access",
        ),
        4: (
            "index:idx_decisions_user_fts",
            "index:idx_decisions_user_workspace_recent",
            "index:idx_decisions_user_workspace",
            "index:idx_progress_user_workspace_status",
            "index:idx_progress_user_recent",
            "index:idx_custom_data_user_category",
        ),
        7: (
            "column:progress_entries:instance_id",
            "column:decisions:created_by_instance",
            "column:workspace_contexts:instance_id",
            "index:idx_progress_instance",
            "index:idx_progress_workspace_instance",
        ),
    }
    errors: list[str] = []
    for check in checks.get(version, ()):
        kind, *parts = check.split(":")
        if kind == "table" and not table_exists(conn, schema, parts[0]):
            errors.append(f"missing table {schema}.{parts[0]}")
        elif kind == "column" and not column_exists(conn, schema, parts[0], parts[1]):
            errors.append(f"missing column {schema}.{parts[0]}.{parts[1]}")
        elif kind == "index" and not index_exists(conn, schema, parts[0]):
            errors.append(f"missing index {schema}.{parts[0]}")
        elif kind == "view" and not view_exists(conn, schema, parts[0]):
            errors.append(f"missing view {schema}.{parts[0]}")
    return errors


def migration_already_applied(conn, schema: str, migration: Migration) -> bool:
    marker = MIGRATION_MARKERS.get(migration.version)
    marker_exists = bool(marker and migration_marker_exists(conn, schema, marker))
    schema_errors = migration_schema_errors(conn, schema, migration.version)
    return not schema_errors or marker_exists


def adopt_existing_migrations(
    conn,
    schema: str,
    migrations: Sequence[Migration],
    rows: dict[int, dict[str, Any]],
) -> list[str]:
    adopted: list[str] = []
    for migration in migrations:
        if migration.version in rows:
            continue
        if migration_already_applied(conn, schema, migration):
            record_migration(conn, schema, migration, 0, True)
            rows[migration.version] = {
                "filename": migration.filename,
                "checksum_sha256": migration.checksum,
                "success": True,
            }
            adopted.append(migration.filename)
    return adopted


def verify_schema_objects(conn, schema: str) -> list[str]:
    errors: list[str] = []

    for table in REQUIRED_TABLES:
        if not table_exists(conn, schema, table):
            errors.append(f"missing table {schema}.{table}")

    for table, column in REQUIRED_COLUMNS:
        if not column_exists(conn, schema, table, column):
            errors.append(f"missing column {schema}.{table}.{column}")

    for index in REQUIRED_INDEXES:
        if not index_exists(conn, schema, index):
            errors.append(f"missing index {schema}.{index}")

    for view in REQUIRED_VIEWS:
        if not view_exists(conn, schema, view):
            errors.append(f"missing view {schema}.{view}")

    return errors


def apply_migrations(database_url: str, migrations: Sequence[Migration], schema: str) -> dict[str, Any]:
    if os.environ.get(APPLY_ENV) != "1":
        raise GateError(f"refusing to mutate database without {APPLY_ENV}=1")

    applied: list[str] = []
    adopted: list[str] = []
    skipped: list[str] = []
    with connect(database_url) as conn:
        base_errors = preflight_base_schema(conn, schema)
        if base_errors:
            raise GateError("; ".join(base_errors))
        ensure_ledger(conn, schema)
        ledger = load_ledger(conn, schema)
        adopted = adopt_existing_migrations(conn, schema, migrations, ledger)
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

    return {"adopted": adopted, "applied": applied, "skipped": skipped}


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
    parser.add_argument(
        "--schema",
        default=DEFAULT_SCHEMA,
        help="Target schema name. Only public is supported by current ConPort SQL migrations.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if not args.database_url:
            raise GateError("database URL is required")
        schema = validate_supported_schema(validate_identifier(args.schema, "schema"))
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
