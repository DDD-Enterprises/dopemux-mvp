import subprocess
from pathlib import Path

from click.testing import CliRunner

from dopemux import profile_commands
from dopemux.profile_manager import ProfileManager


class _DummyConsole:
    def __init__(self):
        self.messages = []
        self.logger = self

    def info(self, message):
        self.messages.append(str(message))


class _DummyProfile:
    def __init__(self, name: str, description: str = "test profile"):
        self.name = name
        self.description = description
        self.mcp_servers = {"required": ["conport"], "enabled": ["zen"]}


class _DummyManager:
    def __init__(self):
        self.profiles_dir = Path("/tmp/profiles")
        self.create_calls = []

    def get_profile(self, name: str):
        if name == "source":
            return _DummyProfile("source", "source description")
        if name == "developer":
            return _DummyProfile("developer", "developer profile")
        return None

    def create_profile(self, name: str, description: str, based_on: str | None = None):
        self.create_calls.append(
            {"name": name, "description": description, "based_on": based_on}
        )
        return _DummyProfile(name=name, description=description)

    def get_active_profile(self, workspace: Path):
        return None

    def detect_profile_from_claude_config(self, workspace: Path, cache_result: bool = True):
        return "developer"


def _patch_console(monkeypatch):
    fake_console = _DummyConsole()
    monkeypatch.setattr(profile_commands, "console", fake_console)
    return fake_console


def test_create_profile_interactive_uses_wizard(monkeypatch):
    runner = CliRunner()
    manager = _DummyManager()
    fake_console = _patch_console(monkeypatch)

    class _DummyWizard:
        def run(self, profile_name, output_dir):
            assert profile_name == "custom"
            assert output_dir == manager.profiles_dir
            return output_dir / "custom.yaml"

    monkeypatch.setattr(profile_commands, "ProfileManager", lambda: manager)
    monkeypatch.setattr("dopemux.profile_wizard.ProfileWizard", _DummyWizard)

    result = runner.invoke(profile_commands.create_profile, ["custom", "--interactive"])

    assert result.exit_code == 0, result.output
    assert any("Profile created" in msg for msg in fake_console.messages)
    assert any("Wizard output" in msg for msg in fake_console.messages)


def test_copy_profile_creates_new_profile_from_source(monkeypatch):
    runner = CliRunner()
    manager = _DummyManager()
    fake_console = _patch_console(monkeypatch)

    monkeypatch.setattr(profile_commands, "ProfileManager", lambda: manager)
    monkeypatch.setattr(profile_commands.Path, "exists", lambda p: False)

    result = runner.invoke(profile_commands.copy_profile, ["source", "target"])

    assert result.exit_code == 0, result.output
    assert manager.create_calls == [
        {
            "name": "target",
            "description": "Copy of source: source description",
            "based_on": "source",
        }
    ]
    assert any("Profile copied" in msg for msg in fake_console.messages)


def test_edit_profile_rolls_back_on_editor_failure(monkeypatch, tmp_path: Path):
    runner = CliRunner()
    fake_console = _patch_console(monkeypatch)

    manager = ProfileManager(dopemux_home=tmp_path / ".dopemux-home")
    profile_file = manager.profiles_dir / "developer.yaml"
    original_content = "name: developer\ndescription: test\nmcp_servers:\n  required: [conport]\n"
    profile_file.write_text(original_content, encoding="utf-8")

    monkeypatch.setattr(profile_commands, "ProfileManager", lambda: manager)
    monkeypatch.setattr(
        profile_commands.subprocess,
        "run",
        lambda *a, **k: (_ for _ in ()).throw(subprocess.CalledProcessError(1, "editor")),
    )

    result = runner.invoke(
        profile_commands.edit_profile,
        ["developer", "--editor", "fake-editor"],
    )

    assert result.exit_code == 0, result.output
    assert profile_file.read_text(encoding="utf-8") == original_content
    assert any("rolled back" in msg for msg in fake_console.messages)


def test_delete_profile_archives_and_clears_active_marker(monkeypatch, tmp_path: Path):
    runner = CliRunner()
    fake_console = _patch_console(monkeypatch)

    manager = ProfileManager(dopemux_home=tmp_path / ".dopemux-home")
    profile_file = manager.profiles_dir / "scratch.yaml"
    profile_file.write_text(
        "name: scratch\ndescription: scratch\nmcp_servers:\n  required: [conport]\n",
        encoding="utf-8",
    )

    workspace = tmp_path / "workspace"
    marker = workspace / ".dopemux" / "active_profile"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("scratch", encoding="utf-8")

    monkeypatch.setattr(profile_commands, "ProfileManager", lambda: manager)
    monkeypatch.setattr(profile_commands, "detect_workspace", lambda: workspace)

    result = runner.invoke(profile_commands.delete_profile, ["scratch"])

    assert result.exit_code == 0, result.output
    assert not profile_file.exists()
    archived = list((manager.profiles_dir / "archive").glob("scratch.*.yaml"))
    assert archived
    assert not marker.exists()
    assert any("Profile archived" in msg for msg in fake_console.messages)


def test_show_profile_detects_when_marker_missing(monkeypatch, tmp_path: Path):
    runner = CliRunner()
    manager = _DummyManager()
    fake_console = _patch_console(monkeypatch)

    monkeypatch.setattr(profile_commands, "ProfileManager", lambda: manager)
    monkeypatch.setattr(profile_commands, "detect_workspace", lambda: tmp_path)

    result = runner.invoke(profile_commands.show_profile, [])

    assert result.exit_code == 0, result.output
    assert any("Detected active profile from Claude config" in msg for msg in fake_console.messages)
