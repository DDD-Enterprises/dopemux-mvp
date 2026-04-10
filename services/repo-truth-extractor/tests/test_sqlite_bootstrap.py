from __future__ import annotations

import sqlite3
import sys
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.storage.paths import benchmark_paths
from benchmarking.storage.sqlite_bootstrap import bootstrap_catalog, inspect_tables
from benchmarking.storage.sqlite_schema import EXPECTED_TABLES, SCHEMA_USER_VERSION, SCHEMA_VERSION


def test_bootstrap_creates_catalog_and_expected_tables(tmp_path: Path) -> None:
    db_path = bootstrap_catalog(tmp_path)
    assert db_path.exists()
    assert EXPECTED_TABLES.issubset(inspect_tables(db_path))


def test_bootstrap_is_idempotent_and_records_schema_version(tmp_path: Path) -> None:
    db_path = bootstrap_catalog(tmp_path)
    first_size = db_path.stat().st_size
    db_path_second = bootstrap_catalog(tmp_path)
    assert db_path_second == db_path
    assert db_path_second.stat().st_size >= first_size

    with sqlite3.connect(str(db_path)) as conn:
        user_version = conn.execute("PRAGMA user_version").fetchone()[0]
        schema_version = conn.execute(
            "SELECT value FROM catalog_meta WHERE key = 'schema_version'"
        ).fetchone()[0]
        migration_rows = conn.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0]
    assert user_version == SCHEMA_USER_VERSION
    assert schema_version == SCHEMA_VERSION
    assert migration_rows == 1

