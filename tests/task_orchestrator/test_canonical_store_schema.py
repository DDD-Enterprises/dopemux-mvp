from __future__ import annotations

import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = (
    ROOT
    / "services"
    / "task-orchestrator"
    / "app"
    / "storage"
    / "canonical_store_schema.sql"
)


def test_canonical_store_schema_loads_with_foreign_keys() -> None:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("PRAGMA foreign_keys = ON")

    conn.execute(
        """
        INSERT INTO source_databases (
            source_db_slug, source_database_path, source_schema_hash,
            source_schema_class, source_mtime_utc, source_row_id, archive_sha256,
            import_run_id, adjudication_class, canonical_treatment, imported_at_utc
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "dopemux-mvp-test",
            "/tmp/current-tasks.db",
            "abc123",
            "modern",
            "2026-06-22T00:00:00Z",
            "dopemux-mvp-test",
            "archive-sha",
            "run-1",
            "active_current_dopemux",
            "current test source",
            "2026-06-22T00:00:00Z",
        ),
    )
    conn.execute(
        """
        INSERT INTO source_work_items (
            source_db_slug, source_database_path, source_schema_hash, source_table,
            source_row_id, source_mtime_utc, import_run_id, archive_sha256, role,
            title
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "dopemux-mvp-test",
            "/tmp/current-tasks.db",
            "abc123",
            "COMBINED_WORK_ITEMS.csv",
            "item-1",
            "2026-06-22T00:00:00Z",
            "run-1",
            "archive-sha",
            "queue",
            "Example",
        ),
    )
    assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_canonical_store_rejects_missing_source_database() -> None:
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("PRAGMA foreign_keys = ON")

    try:
        conn.execute(
            """
            INSERT INTO source_work_items (
                source_db_slug, source_database_path, source_schema_hash,
                source_table, source_row_id, source_mtime_utc, import_run_id,
                archive_sha256, role, title
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "missing",
                "/tmp/current-tasks.db",
                "abc123",
                "COMBINED_WORK_ITEMS.csv",
                "item-1",
                "2026-06-22T00:00:00Z",
                "run-1",
                "archive-sha",
                "queue",
                "Example",
            ),
        )
    except sqlite3.IntegrityError:
        return
    raise AssertionError("foreign key should reject missing source database")
