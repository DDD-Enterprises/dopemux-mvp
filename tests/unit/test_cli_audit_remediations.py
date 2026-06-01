from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from click.testing import CliRunner

from dopemux.cli import cli
from dopemux.commands import mcp_commands
from dopemux.routing_cli import _set_routing_mode
from dopemux.routing_config import RoutingConfigError


def test_mcp_up_uses_argv_and_validates_services(monkeypatch):
    runner = CliRunner()
    recorded = []

    monkeypatch.setattr(mcp_commands, "_compose_services", lambda *_: {"conport", "pal"})

    def fake_run(cmd, *, check):
        recorded.append((list(cmd), check))
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(mcp_commands.subprocess, "run", fake_run)

    result = runner.invoke(mcp_commands.mcp, ["up", "--services", "conport,pal"])

    assert result.exit_code == 0, result.output
    assert recorded == [
        (
            [
                "docker",
                "compose",
                "-f",
                "compose.yml",
                "up",
                "-d",
                "--build",
                "conport",
                "pal",
            ],
            True,
        )
    ]


def test_mcp_rejects_invalid_service_before_subprocess(monkeypatch):
    runner = CliRunner()

    monkeypatch.setattr(mcp_commands, "_compose_services", lambda *_: {"conport"})
    monkeypatch.setattr(
        mcp_commands.subprocess,
        "run",
        lambda *args, **kwargs: pytest.fail("subprocess must not run"),
    )

    result = runner.invoke(mcp_commands.mcp, ["logs", "--service", "conport;rm -rf /"])

    assert result.exit_code != 0
    assert "Unknown compose service" in result.output


def test_mcp_status_propagates_docker_failure(monkeypatch):
    runner = CliRunner()

    def fake_run(cmd, *, check):
        raise subprocess.CalledProcessError(2, cmd)

    monkeypatch.setattr(mcp_commands.subprocess, "run", fake_run)

    result = runner.invoke(mcp_commands.mcp, ["status"])

    assert result.exit_code == 1


def test_routing_mode_update_preserves_config_fields(tmp_path: Path):
    config_path = tmp_path / "routing.yaml"
    config_path.write_text(
        "mode: subscription\nports:\n  litellm: 4010\nproviders:\n  - name: openrouter\n",
        encoding="utf-8",
    )

    _set_routing_mode(config_path, "api")

    content = config_path.read_text(encoding="utf-8")
    assert "mode: api" in content
    assert "litellm: 4010" in content
    assert "name: openrouter" in content


def test_routing_mode_update_fails_closed_on_invalid_yaml(tmp_path: Path):
    config_path = tmp_path / "routing.yaml"
    original = "mode: [\n"
    config_path.write_text(original, encoding="utf-8")

    with pytest.raises(RoutingConfigError):
        _set_routing_mode(config_path, "api")

    assert config_path.read_text(encoding="utf-8") == original


def test_decisions_subcommands_are_registered():
    decisions = cli.commands["decisions"]

    assert set(decisions.commands) == {
        "energy",
        "patterns",
        "list",
        "show",
        "query",
        "review",
        "update-outcome",
    }


def test_removed_genetic_code_commands_are_not_registered():
    assert "genetic" not in cli.commands
    assert "code" not in cli.commands


def test_operator_status_aliases_are_public_and_legacy_names_hidden():
    update_group = cli.commands["update"]

    assert "status" in update_group.commands
    assert "update-status-cmd" in update_group.commands
    assert update_group.commands["update-status-cmd"].hidden is True

    runner = CliRunner()
    update_help = runner.invoke(cli, ["update", "--help"])

    assert update_help.exit_code == 0
    assert "status" in update_help.output
    assert "update-status-cmd" not in update_help.output


def test_profile_lifecycle_commands_are_real_callbacks():
    profile_group = cli.commands["profile"]

    assert profile_group.commands["copy"].callback.__name__ == "copy_profile"
    assert profile_group.commands["edit"].callback.__name__ == "edit_profile"
    assert profile_group.commands["delete"].callback.__name__ == "delete_profile"
    assert profile_group.commands["current"].callback.__name__ == "show_profile"


def test_native_hooks_register_refuses_invalid_settings_json():
    runner = CliRunner()

    with runner.isolated_filesystem():
        settings_path = Path(".claude") / "settings.json"
        settings_path.parent.mkdir()
        settings_path.write_text("{not-json", encoding="utf-8")

        result = runner.invoke(cli, ["native-hooks", "register"])

        assert result.exit_code != 0
        assert "Invalid JSON" in result.output
        assert settings_path.read_text(encoding="utf-8") == "{not-json"
