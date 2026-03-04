from __future__ import annotations

from types import SimpleNamespace

import pytest
from click.testing import CliRunner

import dopemux.cli as cli_module


@pytest.mark.parametrize(
    ("command", "extra_args", "expected"),
    [
        ("doctor", ["--timestamp-mode", "deterministic"], ["doctor", "--timestamp-mode", "deterministic"]),
        ("compile", ["--", "--mode", "mvp"], ["dopemux", "compile", "--mode", "mvp"]),
        ("run", ["--", "--task-id", "T001"], ["dopemux", "run", "--task-id", "T001"]),
        ("collect", [], ["dopemux", "collect"]),
        ("gate", [], ["dopemux", "gate"]),
        ("promote", [], ["dopemux", "promote"]),
        ("feedback", [], ["dopemux", "feedback"]),
        ("loop", [], ["dopemux", "loop"]),
    ],
)
def test_kernel_commands_delegate_to_taskx(monkeypatch, command: str, extra_args: list[str], expected: list[str]) -> None:
    captured: dict[str, object] = {}

    def _fake_run(cmd, cwd=None, check=False):
        captured["cmd"] = cmd
        captured["cwd"] = cwd
        captured["check"] = check
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(cli_module.subprocess, "run", _fake_run)

    runner = CliRunner()
    result = runner.invoke(cli_module.cli, ["kernel", command, *extra_args])

    assert result.exit_code == 0, result.output
    cmd = captured["cmd"]
    assert isinstance(cmd, list)
    assert cmd[1:] == expected


def test_kernel_group_help_includes_lifecycle_commands() -> None:
    runner = CliRunner()
    result = runner.invoke(cli_module.cli, ["kernel", "--help"])
    assert result.exit_code == 0, result.output
    for command_name in ["doctor", "compile", "run", "collect", "gate", "promote", "feedback", "loop"]:
        assert command_name in result.output


def test_kernel_command_propagates_nonzero_exit(monkeypatch) -> None:
    def _fake_run(cmd, cwd=None, check=False):
        return SimpleNamespace(returncode=23)

    monkeypatch.setattr(cli_module.subprocess, "run", _fake_run)

    runner = CliRunner()
    result = runner.invoke(cli_module.cli, ["kernel", "gate"])
    assert result.exit_code == 23
