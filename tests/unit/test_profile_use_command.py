from pathlib import Path

from click.testing import CliRunner

import dopemux.claude_config as claude_config_module
from dopemux import profile_commands


class _DummyConsole:
    def __init__(self):
        self.messages = []
        self.logger = self

    def info(self, message):
        self.messages.append(str(message))


class _DummyProfile:
    def __init__(self, name: str):
        self.name = name
        self.description = f"{name} profile"
        self.mcp_servers = {"required": ["conport"], "enabled": ["zen"]}
        self.mcps = ["conport", "zen"]


class _DummyManager:
    def __init__(self, profile: _DummyProfile | None = None, previous: str | None = "full", profiles=None):
        if profiles is not None:
            self.profiles = {p.name: p for p in profiles}
        elif profile is not None:
            self.profiles = {profile.name: profile}
        else:
            self.profiles = {}
        self.previous = previous
        self.set_calls = []

    def get_profile(self, name: str):
        return self.profiles.get(name)

    def get_active_profile(self, workspace: Path):
        return self.previous

    def set_active_profile(self, workspace: Path, profile_name: str):
        self.set_calls.append((str(workspace), profile_name))
        self.previous = profile_name


class _DummyClaudeConfig:
    def __init__(self, apply_exc: Exception | None = None):
        self.apply_exc = apply_exc
        self.apply_calls = []
        self.rollback_calls = []

    def apply_profile(self, profile, create_backup=True, dry_run=False, return_backup_path=False):
        if self.apply_exc:
            raise self.apply_exc
        self.apply_calls.append(
            {
                "profile": profile.name,
                "create_backup": create_backup,
                "dry_run": dry_run,
                "return_backup_path": return_backup_path,
            }
        )
        backup = Path("/tmp/settings_backup.json")
        if return_backup_path:
            return {"mcpServers": {"conport": {}}}, backup
        return {"mcpServers": {"conport": {}}}

    def rollback_to_backup(self, backup_path: Path):
        self.rollback_calls.append(str(backup_path))


def _patch_runtime(monkeypatch, tmp_path: Path, manager, claude_config):
    monkeypatch.setattr(profile_commands, "detect_workspace", lambda: tmp_path)
    monkeypatch.setattr(profile_commands, "ProfileManager", lambda: manager)
    monkeypatch.setattr(claude_config_module, "ClaudeConfig", lambda: claude_config)
    fake_console = _DummyConsole()
    monkeypatch.setattr(profile_commands, "console", fake_console)
    return fake_console


def test_use_profile_applies_config_and_sets_active(monkeypatch, tmp_path: Path):
    runner = CliRunner()
    profile = _DummyProfile("developer")
    manager = _DummyManager(profile=profile, previous="full")
    claude_config = _DummyClaudeConfig()

    fake_console = _patch_runtime(monkeypatch, tmp_path, manager, claude_config)

    result = runner.invoke(profile_commands.use_profile, ["developer"])

    assert result.exit_code == 0, result.output
    assert manager.set_calls == [(str(tmp_path), "developer")]
    assert claude_config.apply_calls
    assert claude_config.rollback_calls == []
    assert any("Claude settings updated" in msg for msg in fake_console.messages)


def test_use_profile_apply_failure_keeps_previous_active(monkeypatch, tmp_path: Path):
    runner = CliRunner()
    profile = _DummyProfile("developer")
    manager = _DummyManager(profile=profile, previous="full")
    claude_config = _DummyClaudeConfig(apply_exc=RuntimeError("config write failed"))

    fake_console = _patch_runtime(monkeypatch, tmp_path, manager, claude_config)

    result = runner.invoke(profile_commands.use_profile, ["developer"])

    assert result.exit_code == 0, result.output
    assert manager.set_calls == []
    assert any("Failed to apply Claude config" in msg for msg in fake_console.messages)
    assert any("Active profile remains: full" in msg for msg in fake_console.messages)


def test_use_profile_rolls_back_config_when_marker_write_fails(monkeypatch, tmp_path: Path):
    runner = CliRunner()
    profile = _DummyProfile("developer")
    manager = _DummyManager(profile=profile, previous="full")
    claude_config = _DummyClaudeConfig()

    def _raise_set_active(_workspace: Path, _profile_name: str):
        raise OSError("marker write failed")

    manager.set_active_profile = _raise_set_active

    fake_console = _patch_runtime(monkeypatch, tmp_path, manager, claude_config)

    result = runner.invoke(profile_commands.use_profile, ["developer"])

    assert result.exit_code == 0, result.output
    assert claude_config.apply_calls
    assert claude_config.rollback_calls == ["/tmp/settings_backup.json"]
    assert any("Configuration rolled back from backup" in msg for msg in fake_console.messages)
    assert any("Failed to set active profile" in msg for msg in fake_console.messages)


def test_use_profile_no_apply_config_skips_claude_updates(monkeypatch, tmp_path: Path):
    runner = CliRunner()
    profile = _DummyProfile("developer")
    manager = _DummyManager(profile=profile, previous=None)
    claude_config = _DummyClaudeConfig()

    _patch_runtime(monkeypatch, tmp_path, manager, claude_config)

    result = runner.invoke(profile_commands.use_profile, ["developer", "--no-apply-config"])

    assert result.exit_code == 0, result.output
    assert manager.set_calls == [(str(tmp_path), "developer")]
    assert claude_config.apply_calls == []


def test_use_profile_restart_flag_runs_dopemux_start(monkeypatch, tmp_path: Path):
    runner = CliRunner()
    profile = _DummyProfile("developer")
    manager = _DummyManager(profile=profile, previous="full")
    claude_config = _DummyClaudeConfig()
    fake_console = _patch_runtime(monkeypatch, tmp_path, manager, claude_config)

    calls = []

    def _fake_run(cmd, check):
        calls.append({"cmd": cmd, "check": check})
        return 0

    monkeypatch.setattr(profile_commands.subprocess, "run", _fake_run)

    result = runner.invoke(
        profile_commands.use_profile,
        ["developer", "--no-apply-config", "--restart-claude"],
    )

    assert result.exit_code == 0, result.output
    assert calls == [{"cmd": ["dopemux", "start", "--profile", "developer"], "check": True}]
    assert any("Claude restart command completed successfully" in msg for msg in fake_console.messages)


def test_switch_full_to_developer_to_full_flow_with_context(monkeypatch, tmp_path: Path):
    runner = CliRunner()
    full = _DummyProfile("full")
    developer = _DummyProfile("developer")
    manager = _DummyManager(profiles=[full, developer], previous="full")
    claude_config = _DummyClaudeConfig()
    fake_console = _patch_runtime(monkeypatch, tmp_path, manager, claude_config)

    save_calls = []
    restore_calls = []

    monkeypatch.setattr(
        profile_commands,
        "_save_context_for_switch",
        lambda workspace, previous, target: (
            save_calls.append((str(workspace), previous, target)) or f"{target}-session-id"
        ),
    )
    monkeypatch.setattr(
        profile_commands,
        "_restore_context_for_switch",
        lambda workspace: (restore_calls.append(str(workspace)) or {"restored": True}),
    )

    result_one = runner.invoke(
        profile_commands.use_profile,
        ["developer", "--no-apply-config"],
    )
    result_two = runner.invoke(
        profile_commands.use_profile,
        ["full", "--no-apply-config"],
    )

    assert result_one.exit_code == 0, result_one.output
    assert result_two.exit_code == 0, result_two.output
    assert manager.set_calls == [(str(tmp_path), "developer"), (str(tmp_path), "full")]
    assert save_calls == [
        (str(tmp_path), "full", "developer"),
        (str(tmp_path), "developer", "full"),
    ]
    assert restore_calls == [str(tmp_path), str(tmp_path)]
    assert any("Switch timing:" in msg for msg in fake_console.messages)
    assert any("Context saved" in msg for msg in fake_console.messages)
    assert any("Context restored after switch" in msg for msg in fake_console.messages)


def test_use_profile_warns_when_switch_exceeds_target(monkeypatch, tmp_path: Path):
    runner = CliRunner()
    profile = _DummyProfile("developer")
    manager = _DummyManager(profile=profile, previous="full")
    claude_config = _DummyClaudeConfig()
    fake_console = _patch_runtime(monkeypatch, tmp_path, manager, claude_config)

    result = runner.invoke(
        profile_commands.use_profile,
        ["developer", "--no-apply-config", "--target-seconds", "0.0"],
    )

    assert result.exit_code == 0, result.output
    assert any("exceeded target" in msg for msg in fake_console.messages)


def test_use_profile_logs_switch_duration_and_mcp_count(monkeypatch, tmp_path: Path):
    runner = CliRunner()
    profile = _DummyProfile("developer")
    manager = _DummyManager(profile=profile, previous="full")
    claude_config = _DummyClaudeConfig()
    _patch_runtime(monkeypatch, tmp_path, manager, claude_config)

    captured = {}
    monkeypatch.setattr(
        "dopemux.profile_analytics.log_switch_sync",
        lambda **kwargs: captured.update(kwargs) or True,
    )

    result = runner.invoke(
        profile_commands.use_profile,
        ["developer", "--no-apply-config", "--no-save-session", "--no-restore-context"],
    )

    assert result.exit_code == 0, result.output
    assert captured["to_profile"] == "developer"
    assert captured["from_profile"] == "full"
    assert captured["mcp_count"] == 2
    assert captured["switch_duration_seconds"] >= 0.0
