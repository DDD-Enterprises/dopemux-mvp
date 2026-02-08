import json
import sqlite3
from pathlib import Path

import pytest

from dopemux.memory.capture_client import (
    CaptureError,
    emit_capture_event,
    resolve_repo_root_strict,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _count_events(ledger_path: Path) -> int:
    conn = sqlite3.connect(str(ledger_path))
    try:
        return int(conn.execute("SELECT COUNT(*) FROM raw_activity_events").fetchone()[0])
    finally:
        conn.close()


def test_plugin_and_cli_modes_share_single_ledger(tmp_path, monkeypatch):
    ledger_path = tmp_path / "chronicle.sqlite"
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger_path))

    plugin = emit_capture_event(
        {
            "event_type": "shell.command",
            "payload": {"command": "echo plugin"},
        },
        mode="plugin",
        repo_root=REPO_ROOT,
    )
    cli = emit_capture_event(
        {
            "event_type": "shell.command",
            "payload": {"command": "echo cli"},
        },
        mode="cli",
        repo_root=REPO_ROOT,
    )

    assert plugin.ledger_path == cli.ledger_path
    assert plugin.ledger_path == ledger_path.resolve()
    assert _count_events(plugin.ledger_path) == 2


def test_redaction_is_applied_consistently(tmp_path, monkeypatch):
    ledger_path = tmp_path / "chronicle.sqlite"
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger_path))

    result = emit_capture_event(
        {
            "event_type": "manual.note",
            "payload": {
                "summary": "test",
                "password": "super-secret",
                "token_line": "Bearer abcdef123456",
            },
        },
        mode="cli",
        repo_root=REPO_ROOT,
    )

    conn = sqlite3.connect(str(result.ledger_path))
    try:
        payload_json = conn.execute(
            "SELECT payload_json FROM raw_activity_events WHERE id = ?", (result.event_id,)
        ).fetchone()[0]
    finally:
        conn.close()

    payload = json.loads(payload_json)
    assert "password" not in payload
    assert payload["token_line"].startswith("[REDACTED")


def test_duplicate_retry_is_ignored(tmp_path, monkeypatch):
    ledger_path = tmp_path / "chronicle.sqlite"
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger_path))

    event = {
        "event_type": "shell.command",
        "source": "cli",
        "ts_utc": "2026-02-08T18:00:00+00:00",
        "payload": {"command": "pytest -q"},
    }

    first = emit_capture_event(event, mode="cli", repo_root=REPO_ROOT)
    second = emit_capture_event(event, mode="cli", repo_root=REPO_ROOT)

    assert first.event_id == second.event_id
    assert first.inserted is True
    assert second.inserted is False
    assert _count_events(first.ledger_path) == 1


def test_repo_root_resolution_is_stable(tmp_path):
    repo = tmp_path / "workspace"
    nested = repo / "a" / "b"
    (repo / ".git").mkdir(parents=True)
    nested.mkdir(parents=True)

    resolved = resolve_repo_root_strict(nested)
    assert resolved == repo.resolve()


def test_capture_fails_closed_outside_repo(tmp_path, monkeypatch):
    non_repo = tmp_path / "outside"
    non_repo.mkdir(parents=True)
    monkeypatch.chdir(non_repo)

    with pytest.raises(CaptureError, match="fails closed"):
        emit_capture_event(
            {
                "event_type": "manual.note",
                "payload": {"summary": "outside repo"},
            },
            mode="cli",
        )
