"""`dopemux native-hooks register` must write Claude Code's event-keyed hooks schema.

Claude Code expects ``hooks.<EventName>: [{hooks: [{type: "command", command: ...}]}]``;
the older ``hooks.command: [{events: [...], command: ...}]`` shape is ignored.
"""

from __future__ import annotations

import json
import shlex
import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

from dopemux.cli import cli

EXPECTED_EVENTS = [
    "SessionStart",
    "SubagentStart",
    "UserPromptSubmit",
    "PreToolUse",
    "PermissionRequest",
    "PostToolUse",
    "PostToolUseFailure",
    "Stop",
    "SubagentStop",
    "PreCompact",
    "SessionEnd",
]


def _register(*args: str):
    return CliRunner().invoke(cli, ["native-hooks", "register", *args])


def _dopemux_commands(settings: dict, event: str) -> list[str]:
    return [
        hook["command"]
        for group in settings["hooks"][event]
        for hook in group["hooks"]
        if "native_hooks.py" in hook["command"] or "run_native_hooks.sh" in hook["command"]
    ]


@pytest.fixture
def project_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_register_global_writes_event_keyed_schema(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))

    result = _register("--global")

    assert result.exit_code == 0, result.output
    hooks = json.loads((tmp_path / ".claude" / "settings.json").read_text())["hooks"]
    assert "command" not in hooks
    assert sorted(hooks) == sorted(EXPECTED_EVENTS)
    for event in EXPECTED_EVENTS:
        groups = hooks[event]
        assert len(groups) == 1
        assert len(groups[0]["hooks"]) == 1
        hook = groups[0]["hooks"][0]
        assert hook["type"] == "command"
        argv = shlex.split(hook["command"])
        assert argv[0] == sys.executable
        assert argv[1].endswith("/dopemux/claude/native_hooks.py")
        assert Path(argv[1]).is_file()


def test_register_project_without_repo_dispatcher_pins_interpreter(
    project_dir: Path,
) -> None:
    # run_native_hooks.sh only exists in dopemux-mvp; elsewhere the repo-relative
    # command would fail, so project mode must fall back to the pinned command.
    result = _register()

    assert result.exit_code == 0, result.output
    settings = json.loads((project_dir / ".claude" / "settings.json").read_text())
    assert sorted(settings["hooks"]) == sorted(EXPECTED_EVENTS)
    for event in EXPECTED_EVENTS:
        (command,) = _dopemux_commands(settings, event)
        assert shlex.split(command)[0] == sys.executable
        assert "run_native_hooks.sh" not in command


def test_register_project_with_repo_dispatcher_uses_it(project_dir: Path) -> None:
    dispatcher = project_dir / ".claude" / "hooks" / "run_native_hooks.sh"
    dispatcher.parent.mkdir(parents=True)
    dispatcher.write_text("#!/usr/bin/env sh\n", encoding="utf-8")

    result = _register()

    assert result.exit_code == 0, result.output
    settings = json.loads((project_dir / ".claude" / "settings.json").read_text())
    for event in EXPECTED_EVENTS:
        assert _dopemux_commands(settings, event) == [
            'sh "${CLAUDE_PROJECT_DIR:-.}/.claude/hooks/run_native_hooks.sh"'
        ]


def test_register_includes_subagent_start(project_dir: Path) -> None:
    result = _register()

    assert result.exit_code == 0, result.output
    settings = json.loads((project_dir / ".claude" / "settings.json").read_text())
    assert "SubagentStart" in settings["hooks"]


def test_register_is_idempotent(project_dir: Path) -> None:
    first = _register()
    settings_path = project_dir / ".claude" / "settings.json"
    after_first = settings_path.read_text()

    second = _register()

    assert first.exit_code == 0 and second.exit_code == 0, second.output
    assert "already registered" in second.output
    assert settings_path.read_text() == after_first
    settings = json.loads(after_first)
    for event in EXPECTED_EVENTS:
        assert len(settings["hooks"][event]) == 1


def test_register_refuses_invalid_json_without_touching_file(project_dir: Path) -> None:
    settings_path = project_dir / ".claude" / "settings.json"
    settings_path.parent.mkdir()
    settings_path.write_text("{not-json", encoding="utf-8")

    result = _register()

    assert result.exit_code != 0
    assert "Invalid JSON" in result.output
    assert settings_path.read_text(encoding="utf-8") == "{not-json"
    assert not settings_path.with_suffix(".json.bak").exists()


def test_register_refuses_non_list_event_entry(project_dir: Path) -> None:
    settings_path = project_dir / ".claude" / "settings.json"
    settings_path.parent.mkdir()
    original = json.dumps({"hooks": {"Stop": {"oops": 1}}})
    settings_path.write_text(original, encoding="utf-8")

    result = _register()

    assert result.exit_code != 0
    assert "hooks.Stop" in result.output
    assert settings_path.read_text(encoding="utf-8") == original


def test_register_preserves_existing_hooks_and_inserts_dopemux_first(
    project_dir: Path,
) -> None:
    settings_path = project_dir / ".claude" / "settings.json"
    settings_path.parent.mkdir()
    user_group = {"matcher": "Bash", "hooks": [{"type": "command", "command": "echo mine"}]}
    original = {
        "permissions": {"allow": ["Bash(ls:*)"]},
        "hooks": {
            "PreToolUse": [user_group],
            "Notification": [{"hooks": [{"type": "command", "command": "echo note"}]}],
        },
    }
    settings_path.write_text(json.dumps(original), encoding="utf-8")

    result = _register()

    assert result.exit_code == 0, result.output
    settings = json.loads(settings_path.read_text())
    assert settings["permissions"] == original["permissions"]
    assert settings["hooks"]["Notification"] == original["hooks"]["Notification"]
    pre_tool = settings["hooks"]["PreToolUse"]
    assert len(pre_tool) == 2
    assert pre_tool[1] == user_group
    assert "native_hooks.py" in pre_tool[0]["hooks"][0]["command"]
    # A .bak of the pre-registration file is kept.
    backup = settings_path.with_suffix(".json.bak")
    assert json.loads(backup.read_text()) == original


def test_register_adds_only_missing_events_when_partially_registered(
    project_dir: Path,
) -> None:
    first = _register()
    assert first.exit_code == 0, first.output
    settings_path = project_dir / ".claude" / "settings.json"
    settings = json.loads(settings_path.read_text())
    del settings["hooks"]["SubagentStart"]
    settings_path.write_text(json.dumps(settings), encoding="utf-8")

    result = _register()

    assert result.exit_code == 0, result.output
    settings = json.loads(settings_path.read_text())
    for event in EXPECTED_EVENTS:
        assert len(settings["hooks"][event]) == 1
