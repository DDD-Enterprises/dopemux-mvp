"""SQLite chronicle migration applicator tests."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from chronicle.sqlite_migrations import apply_chronicle_migrations


def _chronicle_schema_path() -> Path:
    return Path(__file__).resolve().parents[2] / "chronicle" / "schema.sql"


def _chronicle_migrations_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "chronicle" / "migrations"


def _create_v1_0_0_baseline(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE work_log_entries (
          id TEXT PRIMARY KEY,
          workspace_id TEXT NOT NULL,
          instance_id TEXT NOT NULL,
          session_id TEXT,
          ts_utc TEXT NOT NULL,
          duration_sec INTEGER,
          category TEXT NOT NULL,
          entry_type TEXT NOT NULL,
          workflow_phase TEXT,
          summary TEXT NOT NULL,
          details_json TEXT,
          reasoning TEXT,
          outcome TEXT NOT NULL DEFAULT 'in_progress',
          importance_score INTEGER NOT NULL DEFAULT 5,
          tags_json TEXT NOT NULL DEFAULT '[]',
          linked_decisions_json TEXT,
          linked_files_json TEXT,
          linked_commits_json TEXT,
          linked_chat_range_json TEXT,
          parent_entry_id TEXT,
          created_at_utc TEXT NOT NULL,
          updated_at_utc TEXT NOT NULL
        );

        CREATE TABLE reflection_cards (
          id TEXT PRIMARY KEY,
          workspace_id TEXT NOT NULL,
          instance_id TEXT NOT NULL,
          session_id TEXT,
          ts_utc TEXT NOT NULL,
          window_start_utc TEXT NOT NULL,
          window_end_utc TEXT NOT NULL,
          trajectory TEXT NOT NULL,
          top_decisions_json TEXT NOT NULL DEFAULT '[]',
          top_blockers_json TEXT NOT NULL DEFAULT '[]',
          progress_json TEXT NOT NULL DEFAULT '{}',
          next_suggested_json TEXT NOT NULL DEFAULT '[]',
          promotion_candidates_json TEXT NOT NULL DEFAULT '[]',
          created_at_utc TEXT NOT NULL
        );

        CREATE TABLE schema_migrations (
          version TEXT PRIMARY KEY,
          applied_at_utc TEXT NOT NULL
        );

        INSERT INTO schema_migrations(version, applied_at_utc)
        VALUES ('v1.0.0', datetime('now'));
        """
    )
    conn.commit()


def test_apply_chronicle_migrations_upgrades_v1_0_0_schema(tmp_path: Path) -> None:
    db_path = tmp_path / "chronicle_v1_0_0.db"
    conn = sqlite3.connect(str(db_path))
    _create_v1_0_0_baseline(conn)

    applied = apply_chronicle_migrations(
        conn,
        schema_path=_chronicle_schema_path(),
        migrations_dir=_chronicle_migrations_dir(),
    )
    assert applied

    versions = {
        row[0]
        for row in conn.execute("SELECT version FROM schema_migrations").fetchall()
    }
    assert {"v1.1.0", "v1.1.1", "v1.2.0", "v1.2.1"}.issubset(versions)

    columns = {
        row[1]
        for row in conn.execute("PRAGMA table_info(work_log_entries)").fetchall()
    }
    assert "source_event_id" in columns
    assert "source_event_type" in columns
    assert "source_adapter" in columns
    assert "source_event_ts_utc" in columns
    assert "promotion_rule" in columns
    assert "promotion_ts_utc" in columns
    assert "supersedes_entry_id" in columns

    supersedes_indexes = conn.execute(
        """
        SELECT name, sql
        FROM sqlite_master
        WHERE type='index' AND tbl_name='work_log_entries' AND sql LIKE '%supersed%'
        """
    ).fetchall()
    assert supersedes_indexes
    assert any(
        (sql or "").lower().find("workspace_id, instance_id, supersedes_entry_id") >= 0
        for _, sql in supersedes_indexes
    )

    reapplied = apply_chronicle_migrations(
        conn,
        schema_path=_chronicle_schema_path(),
        migrations_dir=_chronicle_migrations_dir(),
    )
    assert reapplied == []


def test_apply_chronicle_migrations_bootstraps_empty_db(tmp_path: Path) -> None:
    db_path = tmp_path / "chronicle_empty.db"
    conn = sqlite3.connect(str(db_path))

    apply_chronicle_migrations(
        conn,
        schema_path=_chronicle_schema_path(),
        migrations_dir=_chronicle_migrations_dir(),
    )

    assert conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='raw_activity_events'"
    ).fetchone()

    versions = {
        row[0]
        for row in conn.execute("SELECT version FROM schema_migrations").fetchall()
    }
    assert "v1.2.1" in versions
