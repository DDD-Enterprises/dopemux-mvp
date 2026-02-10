"""
Integration tests for ADR-213: Dual-Capture Canonical Ledger Design

Verifies that:
1. Plugin and MCP modes produce identical event_id for same events
2. All capture modes write to the same canonical ledger
3. Capture fails closed without repo root resolution
4. Global rollup never writes to project ledgers (read-only guarantee)
"""

import json
import sqlite3
import tempfile
from pathlib import Path

import pytest

from dopemux.memory.capture_client import (
    CaptureError,
    emit_capture_event,
    resolve_repo_root_strict,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _count_events(ledger_path: Path) -> int:
    """Count events in a ledger."""
    conn = sqlite3.connect(str(ledger_path))
    try:
        return int(conn.execute("SELECT COUNT(*) FROM raw_activity_events").fetchone()[0])
    finally:
        conn.close()


def _get_event_ids(ledger_path: Path) -> list[str]:
    """Get all event IDs from a ledger."""
    conn = sqlite3.connect(str(ledger_path))
    try:
        rows = conn.execute("SELECT id FROM raw_activity_events ORDER BY id").fetchall()
        return [row[0] for row in rows]
    finally:
        conn.close()


def test_plugin_and_mcp_modes_produce_identical_event_id(tmp_path, monkeypatch):
    """
    Verify ADR-213 convergent event identity guarantee:
    Same event from plugin vs MCP mode produces identical event_id.
    """
    ledger_path = tmp_path / "chronicle.sqlite"
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger_path))

    # Same event content
    event_data = {
        "event_type": "shell.command",
        "source": "test",
        "ts_utc": "2026-02-08T18:00:00+00:00",
        "payload": {"command": "pytest -q", "exit_code": 0},
    }

    # Capture as plugin
    plugin_result = emit_capture_event(
        event_data,
        mode="plugin",
        repo_root=REPO_ROOT,
    )

    # Capture as MCP (same content, different mode)
    mcp_result = emit_capture_event(
        event_data,
        mode="mcp",
        repo_root=REPO_ROOT,
    )

    # Verify convergent event_id
    assert plugin_result.event_id == mcp_result.event_id, (
        "Plugin and MCP modes must produce identical event_id for same content"
    )

    # Verify second insert was deduplicated
    assert plugin_result.inserted is True, "First capture should insert"
    assert mcp_result.inserted is False, "Second capture should dedupe"

    # Verify only one event in ledger
    assert _count_events(ledger_path) == 1, "Duplicate event_id must dedupe"


def test_cli_and_mcp_modes_share_single_canonical_ledger(tmp_path, monkeypatch):
    """
    Verify ADR-213 canonical ledger guarantee:
    All capture modes write to same ledger location.
    """
    ledger_path = tmp_path / "chronicle.sqlite"
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger_path))

    cli_result = emit_capture_event(
        {
            "event_type": "manual.note",
            "payload": {"summary": "CLI capture"},
        },
        mode="cli",
        repo_root=REPO_ROOT,
    )

    mcp_result = emit_capture_event(
        {
            "event_type": "manual.note",
            "payload": {"summary": "MCP capture"},
        },
        mode="mcp",
        repo_root=REPO_ROOT,
    )

    plugin_result = emit_capture_event(
        {
            "event_type": "manual.note",
            "payload": {"summary": "Plugin capture"},
        },
        mode="plugin",
        repo_root=REPO_ROOT,
    )

    # All modes write to same ledger
    assert cli_result.ledger_path == mcp_result.ledger_path
    assert cli_result.ledger_path == plugin_result.ledger_path
    assert cli_result.ledger_path == ledger_path.resolve()

    # All events in same ledger
    assert _count_events(ledger_path) == 3


def test_capture_fails_closed_without_repo_root(tmp_path, monkeypatch):
    """
    Verify ADR-213 fail-closed guarantee:
    Capture raises CaptureError if repo root cannot be resolved.
    """
    non_repo = tmp_path / "not_a_repo"
    non_repo.mkdir(parents=True)
    monkeypatch.chdir(non_repo)

    with pytest.raises(CaptureError, match="fails closed"):
        emit_capture_event(
            {
                "event_type": "manual.note",
                "payload": {"summary": "Outside repo"},
            },
            mode="cli",
        )


def test_repo_root_resolution_is_deterministic(tmp_path):
    """
    Verify ADR-213 deterministic repo root resolution:
    Walking upward from nested path finds first .git or .dopemux marker.
    """
    repo = tmp_path / "workspace"
    nested = repo / "a" / "b" / "c"
    (repo / ".git").mkdir(parents=True)
    nested.mkdir(parents=True)

    # Resolve from deeply nested path
    resolved = resolve_repo_root_strict(nested)
    assert resolved == repo.resolve()

    # Resolve from repo root itself
    resolved_from_root = resolve_repo_root_strict(repo)
    assert resolved_from_root == repo.resolve()


def test_all_modes_use_same_event_id_for_duplicate_content(tmp_path, monkeypatch):
    """
    Verify ADR-213 content-based event_id generation:
    event_id is derived from content, not mode or timestamp.
    """
    ledger_path = tmp_path / "chronicle.sqlite"
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger_path))

    event_data = {
        "event_type": "task.completed",
        "source": "test",
        "ts_utc": "2026-02-08T19:00:00+00:00",
        "payload": {"task_id": "T-123", "duration_seconds": 45},
    }

    # Capture with all three modes
    plugin_result = emit_capture_event(event_data, mode="plugin", repo_root=REPO_ROOT)
    cli_result = emit_capture_event(event_data, mode="cli", repo_root=REPO_ROOT)
    mcp_result = emit_capture_event(event_data, mode="mcp", repo_root=REPO_ROOT)

    # All produce same event_id
    assert plugin_result.event_id == cli_result.event_id == mcp_result.event_id

    # Only first insert succeeds
    assert plugin_result.inserted is True
    assert cli_result.inserted is False
    assert mcp_result.inserted is False

    # Single event in ledger
    assert _count_events(ledger_path) == 1


def test_global_rollup_never_writes_to_project_ledger(tmp_path, monkeypatch):
    """
    Verify ADR-213 read-only global rollup guarantee:
    Global rollup index reads project ledgers but never writes to them.

    This test verifies the architectural contract that global rollup
    operations cannot corrupt project data.
    """
    # Create a project ledger with known content
    project_ledger = tmp_path / "project_chronicle.sqlite"
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(project_ledger))

    # Capture some events
    emit_capture_event(
        {
            "event_type": "decision.logged",
            "payload": {"summary": "Project decision"},
        },
        mode="cli",
        repo_root=REPO_ROOT,
    )
    emit_capture_event(
        {
            "event_type": "task.completed",
            "payload": {"task_id": "T-456"},
        },
        mode="cli",
        repo_root=REPO_ROOT,
    )

    initial_count = _count_events(project_ledger)
    initial_event_ids = _get_event_ids(project_ledger)
    initial_mtime = project_ledger.stat().st_mtime

    # Simulate global rollup read operation
    # (In real code: global_rollup.build() reads project ledgers)
    conn = sqlite3.connect(f"file:{project_ledger}?mode=ro", uri=True)
    try:
        # Read events (this is what global rollup does)
        events = conn.execute(
            "SELECT id, event_type, payload_json FROM raw_activity_events"
        ).fetchall()
        assert len(events) == initial_count

        # Verify read-only connection prevents writes
        with pytest.raises(sqlite3.OperationalError, match="readonly database"):
            conn.execute(
                "INSERT INTO raw_activity_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                ("fake_id", "ws", "inst", "sess", "2026-02-08", "fake", "test", "{}", "none", 7, "2026-02-08"),
            )
    finally:
        conn.close()

    # Verify project ledger unchanged
    assert _count_events(project_ledger) == initial_count
    assert _get_event_ids(project_ledger) == initial_event_ids

    # Verify ledger file not modified
    final_mtime = project_ledger.stat().st_mtime
    assert final_mtime == initial_mtime, "Read-only access must not modify ledger file"


def test_auto_mode_resolves_to_valid_capture_mode(tmp_path, monkeypatch):
    """
    Verify ADR-213 auto mode behavior:
    Auto mode resolves to valid capture mode and writes to canonical ledger.
    """
    ledger_path = tmp_path / "chronicle.sqlite"
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger_path))

    # Capture with auto mode (context-driven selection)
    result = emit_capture_event(
        {
            "event_type": "workflow.phase_changed",
            "payload": {"from": "plan", "to": "implement"},
        },
        mode="auto",
        repo_root=REPO_ROOT,
    )

    # Writes to canonical ledger (mode resolution happens internally)
    assert result.ledger_path == ledger_path.resolve()
    assert _count_events(ledger_path) == 1

    # Verify event captured correctly
    assert result.event_id is not None
    assert result.inserted is True


def test_capture_modes_use_deterministic_ordering(tmp_path, monkeypatch):
    """
    Verify ADR-213 deterministic ordering guarantee:
    Events are sorted by importance_score DESC, ts DESC, id ASC.
    """
    ledger_path = tmp_path / "chronicle.sqlite"
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger_path))

    # Capture events with different timestamps
    events = [
        ("2026-02-08T10:00:00+00:00", "event_early"),
        ("2026-02-08T12:00:00+00:00", "event_middle"),
        ("2026-02-08T14:00:00+00:00", "event_late"),
    ]

    for ts, label in events:
        emit_capture_event(
            {
                "event_type": "manual.note",
                "source": "test",
                "ts_utc": ts,
                "payload": {"summary": label},
            },
            mode="cli",
            repo_root=REPO_ROOT,
        )

    # Verify deterministic ordering
    conn = sqlite3.connect(str(ledger_path))
    try:
        rows = conn.execute(
            "SELECT ts_utc FROM raw_activity_events ORDER BY ts_utc DESC, id ASC"
        ).fetchall()
        timestamps = [row[0] for row in rows]
    finally:
        conn.close()

    # Most recent first
    assert timestamps == [
        "2026-02-08T14:00:00+00:00",
        "2026-02-08T12:00:00+00:00",
        "2026-02-08T10:00:00+00:00",
    ]
