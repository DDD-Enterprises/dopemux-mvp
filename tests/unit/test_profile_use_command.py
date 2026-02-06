from pathlib import Path

from click.testing import CliRunner

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
    def __init__(self, profile: _DummyProfile, previous: str | None = "full"):
        self.profile = profile
        self.previous = previous
        self.set_calls = []

    def get_profile(self, name: str):
        return self.profile if name == self.profile.name else None

    def get_active_profile(self, workspace: Path):
        return self.previous

    def set_active_profile(self, workspace: Path, profile_name: str):
        self.set_calls.append((str(workspace), profile_name))


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
    monkeypatch.setattr("dopemux.claude_config.ClaudeConfig", lambda: claude_config)
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
