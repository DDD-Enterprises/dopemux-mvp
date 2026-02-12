"""Packet H hardening tests for supersession migration and MCP envelope."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from chronicle.store import ChronicleStore
from mcp import DopeMemoryMCPServer


def _insert_raw_worklog_row(
    conn: sqlite3.Connection,
    *,
    row_id: str,
    workspace_id: str,
    instance_id: str,
    supersedes_entry_id: str | None,
) -> None:
    """Insert a minimal valid row for index-level tests."""
    conn.execute(
        """
        INSERT INTO work_log_entries (
            id, workspace_id, instance_id, session_id, ts_utc, duration_sec,
            category, entry_type, workflow_phase, summary, details_json, reasoning,
            outcome, importance_score, tags_json, linked_decisions_json, linked_files_json,
            linked_commits_json, linked_chat_range_json, parent_entry_id, source_event_id,
            source_event_type, source_adapter, source_event_ts_utc, promotion_rule,
            promotion_ts_utc, supersedes_entry_id, created_at_utc, updated_at_utc
        ) VALUES (
            ?, ?, ?, NULL, '2026-02-11T12:00:00Z', NULL,
            'planning', 'decision', NULL, 'test', NULL, NULL,
            'in_progress', 5, '[]', NULL, NULL,
            NULL, NULL, NULL, ?, 'test.event', 'test_adapter', '2026-02-11T12:00:00Z',
            'test.rule', '2026-02-11T12:00:00Z', ?, '2026-02-11T12:00:00Z', '2026-02-11T12:00:00Z'
        )
        """,
        (row_id, workspace_id, instance_id, f"evt-{row_id}", supersedes_entry_id),
    )


def test_scoped_supersession_unique_index_allows_cross_scope_reuse(tmp_path: Path) -> None:
    """Same supersedes target is allowed across different workspace/instance scopes."""
    db_path = tmp_path / "scoped_index.db"
    store = ChronicleStore(db_path)
    store.initialize_schema()
    conn = store.connect()

    target_id = "same-target-id"
    _insert_raw_worklog_row(
        conn,
        row_id="corr-ws1",
        workspace_id="ws-1",
        instance_id="A",
        supersedes_entry_id=target_id,
    )
    _insert_raw_worklog_row(
        conn,
        row_id="corr-ws2",
        workspace_id="ws-2",
        instance_id="B",
        supersedes_entry_id=target_id,
    )
    conn.commit()

    with pytest.raises(sqlite3.IntegrityError):
        _insert_raw_worklog_row(
            conn,
            row_id="corr-ws1-dup",
            workspace_id="ws-1",
            instance_id="A",
            supersedes_entry_id=target_id,
        )


def test_v1_2_1_migration_converts_unscoped_index_to_scoped(tmp_path: Path) -> None:
    """Migration upgrades legacy unscoped unique index to scoped partial index."""
    db_path = tmp_path / "migrate_index.db"
    conn = sqlite3.connect(str(db_path))

    conn.executescript(
        """
        CREATE TABLE work_log_entries (
          id TEXT PRIMARY KEY,
          workspace_id TEXT NOT NULL,
          instance_id TEXT NOT NULL,
          supersedes_entry_id TEXT
        );
        CREATE TABLE schema_migrations (
          version TEXT PRIMARY KEY,
          applied_at_utc TEXT NOT NULL
        );
        CREATE UNIQUE INDEX idx_worklog_supersedes_unique
          ON work_log_entries(supersedes_entry_id)
          WHERE supersedes_entry_id IS NOT NULL;
        """
    )

    migration_sql = (
        Path(__file__).resolve().parents[2]
        / "chronicle"
        / "migrations"
        / "v1_2_1_scope_supersession_unique_index.sql"
    ).read_text(encoding="utf-8")

    conn.executescript(migration_sql)
    conn.executescript(migration_sql)  # idempotency check

    index_rows = conn.execute(
        """
        SELECT name, sql
        FROM sqlite_master
        WHERE type = 'index' AND tbl_name = 'work_log_entries'
        """
    ).fetchall()
    index_sql_by_name = {name: (sql or "") for name, sql in index_rows}

    assert "idx_worklog_supersedes_unique" not in index_sql_by_name
    assert "idx_worklog_supersedes_unique_scoped" in index_sql_by_name
    scoped_sql = index_sql_by_name["idx_worklog_supersedes_unique_scoped"].lower()
    assert "(workspace_id, instance_id, supersedes_entry_id)" in scoped_sql
    assert "where supersedes_entry_id is not null" in scoped_sql

    version = conn.execute(
        "SELECT version FROM schema_migrations WHERE version = 'v1.2.1'"
    ).fetchone()
    assert version is not None


def test_memory_correct_response_envelope_is_stable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """memory_correct returns explicit success on both success and failure paths."""
    ledger_path = tmp_path / "mcp_contract.sqlite"
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger_path))
    server = DopeMemoryMCPServer()

    stored = server.memory_store(
        workspace_id="ws-1",
        instance_id="A",
        category="planning",
        entry_type="decision",
        summary="original",
    )
    original_id = stored["entry_id"]

    success = server.memory_correct(
        workspace_id="ws-1",
        instance_id="A",
        entry_id=original_id,
        correction_type="update",
        summary="corrected",
    )
    assert success["success"] is True
    assert success["created"] is True
    assert isinstance(success["entry_id"], str) and success["entry_id"]

    failure = server.memory_correct(
        workspace_id="ws-1",
        instance_id="A",
        entry_id="does-not-exist",
        correction_type="update",
        summary="should fail",
    )
    assert failure["success"] is False
    assert isinstance(failure.get("error"), str) and failure["error"]


def test_memory_correct_idempotency(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """memory_correct with same idempotency_key yields same entry_id (idempotent)."""
    ledger_path = tmp_path / "idempotent.sqlite"
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger_path))
    server = DopeMemoryMCPServer()

    stored = server.memory_store(
        workspace_id="ws-1",
        instance_id="A",
        category="planning",
        entry_type="decision",
        summary="original",
    )
    original_id = stored["entry_id"]

    idemp_key = "fix-123"
    
    # 1. First correction
    resp1 = server.memory_correct(
        workspace_id="ws-1",
        instance_id="A",
        entry_id=original_id,
        correction_type="update",
        summary="corrected once",
        idempotency_key=idemp_key,
    )
    assert resp1["success"] is True
    id1 = resp1["entry_id"]

    # 2. Second correction (retry with same key)
    resp2 = server.memory_correct(
        workspace_id="ws-1",
        instance_id="A",
        entry_id=original_id,
        correction_type="update",
        summary="corrected twice", # summary is different but key is same
        idempotency_key=idemp_key,
    )
    assert resp2["success"] is True
    id2 = resp2["entry_id"]

    # Entry IDs must be identical
    assert id1 == id2
    
    # Verify only one correction entry exists in DB
    from chronicle.store import ChronicleStore
    store = ChronicleStore(ledger_path)
    conn = store.connect()
    count = conn.execute(
        "SELECT COUNT(*) FROM work_log_entries WHERE supersedes_entry_id = ?",
        (original_id,)
    ).fetchone()[0]
    assert count == 1


def test_all_mcp_tools_return_success_field(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """All MCP tools must return the success field."""
    ledger_path = tmp_path / "global_success.sqlite"
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger_path))
    server = DopeMemoryMCPServer()

    # 1. memory_store
    resp = server.memory_store(
        workspace_id="ws-1",
        instance_id="A",
        category="planning",
        entry_type="decision",
        summary="test",
    )
    assert resp.get("success") is True

    # 2. memory_search
    resp = server.memory_search(query="test", workspace_id="ws-1", instance_id="A")
    assert resp.get("success") is True

    # 3. memory_recap
    resp = server.memory_recap(workspace_id="ws-1", instance_id="A")
    assert resp.get("success") is True

    # 4. memory_mark_issue
    # Will fail because entry doesn't exist, but should have success field
    resp = server.memory_mark_issue(
        workspace_id="ws-1", instance_id="A", issue_entry_id="any", description="test"
    )
    assert "success" in resp
    assert resp["success"] is False

    # 5. memory_link_resolution
    # Link will fail because entry doesn't exist, but it should return success: False envelope
    resp = server.memory_link_resolution(
        workspace_id="ws-1", instance_id="A", issue_entry_id="a", resolution_entry_id="b"
    )
    assert resp.get("success") is False
    assert "error" in resp

    # 6. memory_replay_session
    resp = server.memory_replay_session(
        workspace_id="ws-1", instance_id="A", session_id="sess-1"
    )
    assert resp.get("success") is True
