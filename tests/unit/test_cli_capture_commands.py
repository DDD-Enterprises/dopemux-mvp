from pathlib import Path
from types import SimpleNamespace

from click.testing import CliRunner

import dopemux.commands.capture_group_commands as capture_module
import dopemux.commands.trigger_group_commands as trigger_module
from dopemux.cli import cli
from dopemux.memory import CaptureError


def _capture_result(event_type: str, mode: str = "auto") -> SimpleNamespace:
    return SimpleNamespace(
        event_id="evt-123",
        inserted=True,
        ledger_path=Path("/tmp/chronicle.sqlite"),
        repo_root=Path("/tmp"),
        mode=mode,
        source="cli",
        event_type=event_type,
    )


def test_capture_emit_invokes_capture_client(monkeypatch):
    calls = {}

    def _fake_emit(event, *, mode="auto", repo_root=None, emit_event_bus=None):
        calls["event"] = event
        calls["mode"] = mode
        calls["repo_root"] = repo_root
        calls["emit_event_bus"] = emit_event_bus
        return _capture_result(event_type=event.get("event_type", "unknown"), mode=mode)

    monkeypatch.setattr(capture_module, "emit_capture_event", _fake_emit)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "capture",
            "emit",
            "--mode",
            "plugin",
            "--event",
            '{"event_type":"shell.command","payload":{"command":"pytest -q"}}',
        ],
    )

    assert result.exit_code == 0, result.output
    assert calls["mode"] == "plugin"
    assert calls["emit_event_bus"] is False
    assert calls["event"]["event_type"] == "shell.command"
    assert calls["event"]["payload"]["command"] == "pytest -q"


def test_capture_emit_rejects_non_object_json():
    runner = CliRunner()
    result = runner.invoke(cli, ["capture", "emit", "--event", '["not","object"]'])
    assert result.exit_code != 0
    assert "must decode to an object" in result.output


def test_capture_note_builds_manual_note_payload(monkeypatch):
    calls = {}

    def _fake_emit(event, *, mode="auto", repo_root=None, emit_event_bus=None):
        calls["event"] = event
        calls["mode"] = mode
        calls["emit_event_bus"] = emit_event_bus
        return _capture_result(event_type=event.get("event_type", "unknown"), mode=mode)

    monkeypatch.setattr(capture_module, "emit_capture_event", _fake_emit)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "capture",
            "note",
            "Investigated regression",
        ],
    )

    assert result.exit_code == 0, result.output
    assert calls["mode"] == "auto"
    assert calls["event"]["event_type"] == "manual.note"
    assert calls["event"]["source"] == "cli"
    assert calls["event"]["payload"]["summary"] == "Investigated regression"
    assert calls["event"]["payload"]["tags"] == []


def test_trigger_shell_command_parses_invalid_json_as_raw_context(monkeypatch):
    calls = {}

    def _fake_emit(event, *, mode="auto", repo_root=None, emit_event_bus=None):
        calls["event"] = event
        calls["mode"] = mode
        return _capture_result(event_type=event.get("event_type", "unknown"), mode=mode)

    monkeypatch.setattr(trigger_module, "emit_capture_event", _fake_emit)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "trigger",
            "shell-command",
            "--context",
            '{"command":"echo "oops""}',
            "--quiet",
        ],
    )

    assert result.exit_code == 0, result.output
    assert calls["mode"] == "auto"
    assert calls["event"]["event_type"] == "shell.command"
    assert calls["event"]["payload"] == {"raw_context": '{"command":"echo "oops""}'}


def test_trigger_command_done_returns_nonzero_on_capture_failure(monkeypatch):
    def _raise_capture_error(*args, **kwargs):
        raise CaptureError("boom")

    monkeypatch.setattr(trigger_module, "emit_capture_event", _raise_capture_error)

    runner = CliRunner()
    result = runner.invoke(cli, ["trigger", "command-done", "--quiet"])

    assert result.exit_code == 1
