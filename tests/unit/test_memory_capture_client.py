import json
import sqlite3
from pathlib import Path

import pytest

from dopemux.memory import capture_client as capture_client_module
from dopemux.memory.capture_client import (
    CaptureError,
    emit_capture_event,
    resolve_capture_mode,
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


def test_schema_bootstrap_runs_once_per_ledger(tmp_path, monkeypatch):
    ledger_path = tmp_path / "chronicle.sqlite"
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger_path))

    init_calls = {"count": 0}
    real_initialize_schema = capture_client_module._initialize_schema

    def _counting_initialize_schema(conn, schema_path):
        init_calls["count"] += 1
        return real_initialize_schema(conn, schema_path)

    monkeypatch.setattr(
        capture_client_module,
        "_initialize_schema",
        _counting_initialize_schema,
    )

    emit_capture_event(
        {
            "event_type": "shell.command",
            "payload": {"command": "echo first"},
        },
        mode="cli",
        repo_root=REPO_ROOT,
    )
    emit_capture_event(
        {
            "event_type": "shell.command",
            "payload": {"command": "echo second"},
        },
        mode="cli",
        repo_root=REPO_ROOT,
    )

    assert init_calls["count"] == 1


def test_schema_bootstrap_runs_for_each_distinct_ledger(tmp_path, monkeypatch):
    first_ledger = tmp_path / "a.sqlite"
    second_ledger = tmp_path / "b.sqlite"

    init_calls = {"count": 0}
    real_initialize_schema = capture_client_module._initialize_schema

    def _counting_initialize_schema(conn, schema_path):
        init_calls["count"] += 1
        return real_initialize_schema(conn, schema_path)

    monkeypatch.setattr(
        capture_client_module,
        "_initialize_schema",
        _counting_initialize_schema,
    )

    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(first_ledger))
    emit_capture_event(
        {
            "event_type": "shell.command",
            "payload": {"command": "echo one"},
        },
        mode="cli",
        repo_root=REPO_ROOT,
    )

    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(second_ledger))
    emit_capture_event(
        {
            "event_type": "shell.command",
            "payload": {"command": "echo two"},
        },
        mode="cli",
        repo_root=REPO_ROOT,
    )

    assert init_calls["count"] == 2


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


def test_capture_fails_when_schema_dependency_errors(tmp_path, monkeypatch):
    ledger_path = tmp_path / "chronicle.sqlite"
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger_path))

    def _raise_missing_schema(_repo_root):
        raise CaptureError("WMA schema not found: forced test path")

    monkeypatch.setattr(
        capture_client_module,
        "_resolve_wma_schema_path",
        _raise_missing_schema,
    )

    with pytest.raises(CaptureError, match="WMA schema not found"):
        emit_capture_event(
            {
                "event_type": "manual.note",
                "payload": {"summary": "schema failure"},
            },
            mode="cli",
            repo_root=REPO_ROOT,
        )


def test_capture_fails_when_redactor_dependency_errors(tmp_path, monkeypatch):
    ledger_path = tmp_path / "chronicle.sqlite"
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger_path))

    def _raise_missing_redactor(_repo_root):
        raise CaptureError("WMA redactor not found: forced test path")

    monkeypatch.setattr(
        capture_client_module,
        "_load_wma_redactor",
        _raise_missing_redactor,
    )

    with pytest.raises(CaptureError, match="WMA redactor not found"):
        emit_capture_event(
            {
                "event_type": "manual.note",
                "payload": {"summary": "redactor failure"},
            },
            mode="cli",
            repo_root=REPO_ROOT,
        )


def test_event_bus_toggle_paths(tmp_path, monkeypatch):
    ledger_path = tmp_path / "chronicle.sqlite"
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger_path))

    emitted_events: list[dict] = []

    def _record_event(event):
        emitted_events.append(event)

    monkeypatch.setattr(capture_client_module, "_emit_to_event_stream", _record_event)

    # Default false path: env unset and no explicit flag
    monkeypatch.delenv("DOPEMUX_CAPTURE_EMIT_EVENTBUS", raising=False)
    emit_capture_event(
        {
            "event_type": "manual.note",
            "payload": {"summary": "default false"},
        },
        mode="cli",
        repo_root=REPO_ROOT,
    )
    assert emitted_events == []

    # Env-driven true path
    monkeypatch.setenv("DOPEMUX_CAPTURE_EMIT_EVENTBUS", "true")
    emit_capture_event(
        {
            "event_type": "manual.note",
            "payload": {"summary": "env true"},
        },
        mode="cli",
        repo_root=REPO_ROOT,
    )
    assert len(emitted_events) == 1

    # Explicit false overrides env true
    emit_capture_event(
        {
            "event_type": "manual.note",
            "payload": {"summary": "explicit false"},
        },
        mode="cli",
        repo_root=REPO_ROOT,
        emit_event_bus=False,
    )
    assert len(emitted_events) == 1


def test_mode_resolution_explicit_overrides_all(monkeypatch):
    monkeypatch.setenv("DOPEMUX_CAPTURE_MODE", "mcp")
    monkeypatch.setenv("DOPEMUX_CAPTURE_CONTEXT", "plugin")
    monkeypatch.setenv("CLAUDE_SESSION_ID", "session-1")

    assert resolve_capture_mode("cli", repo_root=REPO_ROOT) == "cli"


def test_mode_resolution_env_overrides_config_and_context(monkeypatch):
    monkeypatch.setenv("DOPEMUX_CAPTURE_MODE", "mcp")
    monkeypatch.setenv("DOPEMUX_CAPTURE_CONTEXT", "plugin")

    monkeypatch.setattr(
        capture_client_module,
        "_read_capture_mode_from_project_config",
        lambda _repo_root: "cli",
    )

    assert resolve_capture_mode("auto", repo_root=REPO_ROOT) == "mcp"


def test_mode_resolution_config_overrides_context_and_heuristics(monkeypatch):
    monkeypatch.delenv("DOPEMUX_CAPTURE_MODE", raising=False)
    monkeypatch.setenv("DOPEMUX_CAPTURE_CONTEXT", "plugin")
    monkeypatch.setenv("CLAUDE_SESSION_ID", "session-2")

    monkeypatch.setattr(
        capture_client_module,
        "_read_capture_mode_from_project_config",
        lambda _repo_root: "mcp",
    )

    assert resolve_capture_mode("auto", repo_root=REPO_ROOT) == "mcp"
