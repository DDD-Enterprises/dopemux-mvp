from pathlib import Path

import pytest

from conport_migration_gate import (
    FOUNDATION_MIGRATIONS,
    MigrationGateError,
    checksum_sql,
    discover_foundation_migrations,
    normalize_database_url,
    required_schema_checks,
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
