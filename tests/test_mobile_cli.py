from click.testing import CliRunner
from types import SimpleNamespace

from dopemux.cli import cli
import dopemux.mobile.cli as mobile_cli
import dopemux.mobile.hooks as mobile_hooks
import dopemux.mobile.runtime as mobile_runtime
from dopemux.tmux.common import PaneInfo
from dopemux.mobile.runtime import MobileStatus
from dopemux.config.manager import MobileConfig
from dopemux.tmux.controller import TmuxController
from unittest.mock import MagicMock


class DummyConfigManager:
    def __init__(self, enabled: bool = True):
        self._mobile = MobileConfig(enabled=enabled)

    def get_mobile_config(self):
        return self._mobile


def _runner():
    return CliRunner()


def test_mobile_status_lists_sessions(monkeypatch):
    dummy_cm = DummyConfigManager()
    snapshot = MobileStatus(
        enabled=True,
        happy_ok=True,
        claude_ok=True,
        sessions=[
            PaneInfo(
                pane_id="%1",
                title="mobile:reviewer",
                command="happy",
                window="mobile",
                session="session0",
                active=True,
                path="/tmp",
            )
        ],
        tmux_error=None,
    )

    monkeypatch.setattr(mobile_cli, "_get_config_manager", lambda ctx: dummy_cm)
    monkeypatch.setattr(mobile_cli, "get_mobile_status", lambda cm, ctrl=None: snapshot)
    monkeypatch.setattr(mobile_cli, "update_tmux_mobile_indicator", lambda cm, ctrl=None: None)
    controller = MagicMock(spec=TmuxController)
    controller.list_panes.return_value = [] # existing labels empty
    controller.backend = MagicMock()
    
    # Mock window creation sequence
    monkeypatch.setattr(mobile_cli, "_get_controller", lambda ctx: controller)
    
    result = _runner().invoke(mobile_cli.mobile, ["status"])

    assert result.exit_code == 0
    assert "Active sessions" in result.output
    assert "mobile:reviewer" in result.output


def test_mobile_status_json_monkeypatch(monkeypatch):
    dummy_cm = DummyConfigManager(enabled=False)
    snapshot = MobileStatus(
        enabled=False,
        happy_ok=False,
        claude_ok=False,
        sessions=[],
        tmux_error=None,
    )

    monkeypatch.setattr(mobile_cli, "_get_config_manager", lambda ctx: dummy_cm)
    monkeypatch.setattr(mobile_cli, "get_mobile_status", lambda cm, ctrl=None: snapshot)
    monkeypatch.setattr(mobile_cli, "update_tmux_mobile_indicator", lambda cm, ctrl=None: None)
    monkeypatch.setattr(mobile_cli, "_get_controller", lambda ctx: MagicMock(spec=TmuxController))

    result = _runner().invoke(mobile_cli.mobile, ["status", "--json"])

    assert result.exit_code == 0
    assert '"mobile_enabled": false' in result.output.lower()


def test_mobile_status_watch_json_conflict(monkeypatch):
    dummy_cm = DummyConfigManager()
    snapshot = MobileStatus(
        enabled=True,
        happy_ok=True,
        claude_ok=True,
        sessions=[],
        tmux_error=None,
    )

    monkeypatch.setattr(mobile_cli, "_get_config_manager", lambda ctx: dummy_cm)
    monkeypatch.setattr(mobile_cli, "get_mobile_status", lambda cm, ctrl=None: snapshot)
    monkeypatch.setattr(mobile_cli, "update_tmux_mobile_indicator", lambda cm, ctrl=None: None)
    monkeypatch.setattr(mobile_cli, "_get_controller", lambda ctx: MagicMock(spec=TmuxController))

    result = _runner().invoke(mobile_cli.mobile, ["status", "--json", "--watch"], catch_exceptions=False)

    assert result.exit_code == 1
    assert "cannot be combined" in result.output


def test_run_tests_default(monkeypatch):
    recorded = {}

    monkeypatch.setattr(
        mobile_hooks, "notify_mobile_event", lambda cfg, msg: recorded.setdefault("messages", []).append(msg)
    )
    monkeypatch.setattr(mobile_runtime, "update_tmux_mobile_indicator", lambda cfg, ctrl=None: None)

    def fake_run(args, cwd=None, check=False):
        recorded["args"] = list(args)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("subprocess.run", fake_run)

    result = CliRunner().invoke(cli, ["run-tests"])

    assert result.exit_code == 0
    assert recorded["args"] == ["pytest"]
    assert any("complete" in msg for msg in recorded["messages"])


def test_run_build_failure(monkeypatch):
    messages = []

    monkeypatch.setattr(mobile_hooks, "notify_mobile_event", lambda cfg, msg: messages.append(msg))
    monkeypatch.setattr(mobile_runtime, "update_tmux_mobile_indicator", lambda cfg, ctrl=None: None)

    def fake_run(args, cwd=None, check=False):
        return SimpleNamespace(returncode=2)

    monkeypatch.setattr("subprocess.run", fake_run)

    result = CliRunner().invoke(cli, ["run-build", "npm", "run", "build"], catch_exceptions=False)

    assert result.exit_code == 2
