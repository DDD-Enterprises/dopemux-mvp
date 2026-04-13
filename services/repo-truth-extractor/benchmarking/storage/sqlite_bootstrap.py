from __future__ import annotations

import sqlite3
from pathlib import Path

from ..models.ids import utc_now_iso
from .paths import benchmark_paths
from .sqlite_schema import DDL_STATEMENTS, EXPECTED_TABLES, REQUIRED_COLUMNS, SCHEMA_USER_VERSION, SCHEMA_VERSION


def connect_catalog(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _ensure_required_columns(conn: sqlite3.Connection) -> None:
    for table_name, column_specs in REQUIRED_COLUMNS.items():
        rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
        existing = {str(row["name"]) for row in rows}
        for column_name, column_sql in column_specs:
            if column_name in existing:
                continue
            conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql}")


def bootstrap_catalog(root: Path | None = None) -> Path:
    paths = benchmark_paths(root)
    paths.index_dir.mkdir(parents=True, exist_ok=True)
    paths.runs_dir.mkdir(parents=True, exist_ok=True)
    with connect_catalog(paths.catalog_db) as conn:
        for statement in DDL_STATEMENTS:
            conn.executescript(statement)
        _ensure_required_columns(conn)
        conn.execute(f"PRAGMA user_version = {SCHEMA_USER_VERSION}")
        conn.execute(
            "INSERT OR IGNORE INTO schema_migrations(version, applied_at_utc) VALUES(?, ?)",
            (SCHEMA_VERSION, utc_now_iso()),
        )
        conn.execute(
            """
            INSERT INTO catalog_meta(key, value) VALUES(?, ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value
            """,
            ("schema_version", SCHEMA_VERSION),
        )
        conn.commit()
    return paths.catalog_db


def inspect_tables(db_path: Path) -> set[str]:
    with connect_catalog(db_path) as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
    return {str(row["name"]) for row in rows}


def verify_catalog(db_path: Path) -> None:
    actual = inspect_tables(db_path)
    missing = EXPECTED_TABLES - actual
    if missing:
        raise RuntimeError(f"benchmark catalog missing tables: {sorted(missing)}")
