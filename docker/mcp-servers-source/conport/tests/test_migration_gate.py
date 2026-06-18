import asyncio
from pathlib import Path

import pytest

from conport_migration_gate import (
    FOUNDATION_MIGRATIONS,
    LEDGER_TABLE,
    MigrationFile,
    MigrationGateError,
    apply_gate,
    checksum_sql,
    discover_foundation_migrations,
    normalize_database_url,
    required_schema_checks,
    validate_ledger,
    verify_gate,
)


def test_normalize_database_url_accepts_asyncpg_scheme():
    raw = "postgresql+asyncpg://user:pass@db:5432/conport"

    assert normalize_database_url(raw) == "postgresql://user:pass@db:5432/conport"


def test_discover_foundation_migrations_is_ordered_and_scoped(tmp_path):
    for name in FOUNDATION_MIGRATIONS:
        (tmp_path / name).write_text(f"-- {name}\n", encoding="utf-8")
    (tmp_path / "004_unified_query_indexes.sql").write_text("-- excluded\n", encoding="utf-8")

    migrations = discover_foundation_migrations(tmp_path)

    assert [migration.name for migration in migrations] == list(FOUNDATION_MIGRATIONS)


def test_discover_foundation_migrations_fails_closed_when_missing(tmp_path):
    (tmp_path / FOUNDATION_MIGRATIONS[0]).write_text("-- present\n", encoding="utf-8")

    with pytest.raises(MigrationGateError, match="missing required migration files"):
        discover_foundation_migrations(tmp_path)


def test_checksum_sql_changes_when_file_content_changes():
    assert checksum_sql("SELECT 1;\n") != checksum_sql("SELECT 2;\n")


def test_required_schema_checks_include_downstream_foundation_objects():
    checks = required_schema_checks()

    assert "decision_relationships" in checks.tables
    assert "review_reminders" in checks.tables
    assert "adhd_metrics" in checks.tables
    assert "decision_patterns" in checks.tables
    assert "users" in checks.tables
    assert "workspaces" in checks.tables
    assert "user_workspace_access" in checks.tables
    assert "outcome_status" in checks.columns["decisions"]
    assert "user_id" in checks.columns["workspace_contexts"]


def test_verify_gate_fails_closed_when_ledger_shape_is_incompatible():
    class IncompatibleLedgerConnection:
        async def fetchval(self, *_args):
            return LEDGER_TABLE

        async def fetch(self, *_args):
            raise RuntimeError('column "name" does not exist')

    with pytest.raises(MigrationGateError, match="migration ledger validation failed"):
        asyncio.run(verify_gate(IncompatibleLedgerConnection(), []))


def test_validate_ledger_accepts_legacy_success_rows_with_matching_checksums():
    migrations = [
        MigrationFile(
            name="001_enhanced_decision_model.sql",
            path=Path("001_enhanced_decision_model.sql"),
            checksum="abc123",
            sql="SELECT 1;",
            rank=1,
        )
    ]

    class LegacyLedgerConnection:
        async def fetchval(self, *_args):
            return LEDGER_TABLE

        async def fetch(self, query, *_args):
            if "information_schema.columns" in query:
                return [
                    {"column_name": "version"},
                    {"column_name": "filename"},
                    {"column_name": "checksum_sha256"},
                    {"column_name": "success"},
                ]
            return [
                {
                    "version": 1,
                    "filename": "001_enhanced_decision_model.sql",
                    "checksum_sha256": "abc123",
                    "success": True,
                }
            ]

    assert asyncio.run(validate_ledger(LegacyLedgerConnection(), migrations)) == []


def test_validate_ledger_rejects_legacy_failed_rows():
    migrations = [
        MigrationFile(
            name="001_enhanced_decision_model.sql",
            path=Path("001_enhanced_decision_model.sql"),
            checksum="abc123",
            sql="SELECT 1;",
            rank=1,
        )
    ]

    class LegacyLedgerConnection:
        async def fetchval(self, *_args):
            return LEDGER_TABLE

        async def fetch(self, query, *_args):
            if "information_schema.columns" in query:
                return [
                    {"column_name": "version"},
                    {"column_name": "filename"},
                    {"column_name": "checksum_sha256"},
                    {"column_name": "success"},
                ]
            return [
                {
                    "version": 1,
                    "filename": "001_enhanced_decision_model.sql",
                    "checksum_sha256": "abc123",
                    "success": False,
                }
            ]

    errors = asyncio.run(validate_ledger(LegacyLedgerConnection(), migrations))

    assert errors == ["ledger row is not applied: 001_enhanced_decision_model.sql"]


def test_apply_gate_refuses_to_mutate_missing_rows_in_legacy_ledger():
    migrations = [
        MigrationFile(
            name="001_enhanced_decision_model.sql",
            path=Path("001_enhanced_decision_model.sql"),
            checksum="abc123",
            sql="SELECT 1;",
            rank=1,
        )
    ]

    class LegacyLedgerConnection:
        async def execute(self, *_args):
            return None

        async def fetch(self, query, *_args):
            if "information_schema.columns" in query:
                return [
                    {"column_name": "version"},
                    {"column_name": "filename"},
                    {"column_name": "checksum_sha256"},
                    {"column_name": "success"},
                ]
            return []

    with pytest.raises(MigrationGateError, match="legacy migration ledger"):
        asyncio.run(apply_gate(LegacyLedgerConnection(), migrations))
