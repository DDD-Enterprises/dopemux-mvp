"""Migration 008 (write principal): the SQL text, schema.sql and the gate.

No database is touched.  The migration is operator-run only (packet C10).
"""

from __future__ import annotations

import importlib.util
import re
import sys

import pytest

from .helpers import CONPORT_DIR, MIGRATIONS_DIR

TABLES = ("workspace_contexts", "decisions", "progress_entries", "custom_data")


@pytest.fixture(scope="module")
def gate():
    path = MIGRATIONS_DIR / "conport_migration_gate.py"
    spec = importlib.util.spec_from_file_location("conport_gate_w02", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(spec.name, None)
    return module


def _strip_comments(sql: str) -> str:
    return "\n".join(line.split("--", 1)[0] for line in sql.splitlines())


def test_should_add_a_nullable_defaulted_principal_column_to_each_written_table():
    sql = _strip_comments((MIGRATIONS_DIR / "008_write_principal.sql").read_text(encoding="utf-8"))
    for table in TABLES:
        assert re.search(
            rf"ALTER TABLE {table}\s+ADD COLUMN IF NOT EXISTS write_principal VARCHAR\(255\)\s+DEFAULT 'unverified'",
            sql,
        ), table
    assert "NOT NULL" not in sql
    assert "DROP" not in sql.upper().replace("DROP-", "")


def test_should_be_idempotent_and_transactional():
    sql = _strip_comments((MIGRATIONS_DIR / "008_write_principal.sql").read_text(encoding="utf-8")).upper()
    assert "BEGIN;" in sql and "COMMIT;" in sql
    assert sql.count("ADD COLUMN IF NOT EXISTS") == len(TABLES)
    assert "UPDATE " not in sql  # no existing row is rewritten


def test_should_verify_the_columns_inside_the_migration():
    sql = (MIGRATIONS_DIR / "008_write_principal.sql").read_text(encoding="utf-8")
    assert "RAISE EXCEPTION" in sql and "write_principal" in sql


def test_should_roll_back_by_dropping_exactly_those_columns():
    sql = _strip_comments((MIGRATIONS_DIR / "008_rollback.sql").read_text(encoding="utf-8"))
    for table in TABLES:
        assert re.search(rf"ALTER TABLE {table}\s+DROP COLUMN IF EXISTS write_principal", sql), table
    assert sql.upper().count("DROP COLUMN") == len(TABLES)
    assert "BEGIN;" in sql.upper() and "COMMIT;" in sql.upper()
    # a rollback may not touch the migration ledger of other versions or any other column
    assert "conport_schema_migrations" not in sql or "version = 8" in sql


def test_should_put_the_principal_in_the_canonical_schema():
    schema = (CONPORT_DIR / "schema.sql").read_text(encoding="utf-8")
    for table in TABLES:
        block = re.search(rf"CREATE TABLE {table} \((.*?)\n\);", schema, re.S)
        assert block, table
        assert "write_principal VARCHAR(255) DEFAULT 'unverified'" in block.group(1), table
    # no other table gains one
    assert schema.count("write_principal") == len(TABLES)


def test_should_name_the_migration_files_so_the_gate_discovers_only_the_up_file(gate):
    found = {m.filename for m in gate.discover_migrations(MIGRATIONS_DIR)}
    assert "008_write_principal.sql" in found
    assert "008_rollback.sql" not in found  # rollback files are never applied


def test_should_require_the_new_migration_and_columns(gate):
    assert "008_write_principal.sql" in gate.REQUIRED_MIGRATIONS
    for table in TABLES:
        assert (table, "write_principal") in gate.REQUIRED_COLUMNS
    # the five existing names are untouched
    assert {
        "001_enhanced_decision_model.sql",
        "002_decision_patterns_table.sql",
        "003_multi_tenancy_foundation.sql",
        "004_unified_query_indexes.sql",
        "007_worktree_support_simple.sql",
    } <= gate.REQUIRED_MIGRATIONS


def test_should_let_the_adopt_path_recognise_a_psql_applied_008(gate):
    """psql-then-adopt: ``apply`` must see 008 as already applied, not re-run it."""

    class Conn:
        def __init__(self, present):
            self.present = present

    calls = []

    def column_exists(conn, schema, table, column):
        calls.append((table, column))
        return (table, column) in conn.present

    gate.column_exists, original = column_exists, gate.column_exists
    try:
        present = Conn({(t, "write_principal") for t in TABLES})
        assert gate.migration_schema_errors(present, "public", 8) == []
        missing = Conn(set())
        errors = gate.migration_schema_errors(missing, "public", 8)
        assert len(errors) == len(TABLES) and all("write_principal" in e for e in errors)
    finally:
        gate.column_exists = original
    assert all(column == "write_principal" for _, column in calls)


def test_should_keep_the_existing_adoption_checks(gate):
    # version 7 keeps its own checks; unknown versions still fail closed
    seen = []
    original = (gate.column_exists, gate.index_exists)
    gate.column_exists = lambda conn, schema, table, column: seen.append((table, column)) or True
    gate.index_exists = lambda conn, schema, index: True
    try:
        assert gate.migration_schema_errors(object(), "public", 7) == []
    finally:
        gate.column_exists, gate.index_exists = original
    assert ("decisions", "created_by_instance") in seen
    assert gate.migration_schema_errors(object(), "public", 99) == [
        "missing schema adoption checks for migration version 099"
    ]
