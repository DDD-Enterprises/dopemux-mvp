"""
Integration and end-to-end style tests for the Dope layout experience.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from click.testing import CliRunner

import dopemux.tmux.cli as tmux_cli
from dopemux.config.manager import DopemuxConfig, MCPServerConfig


class _FakeTmuxConfig:
    default_layout = "dope"
    default_session = "dopemux"
    orchestrator_window = "dopemux"
    monitor_commands: dict[str, str] = {}
    orchestrator_command = "dopemux start --role orchestrator --no-recovery"
    sandbox_command = None
    dual_agent_default = False
    secondary_agent_command = None
    agent_command = "dopemux start --role agent"


def _fake_pane(pane_id: str) -> tmux_cli.PaneInfo:
    return tmux_cli.PaneInfo(
        pane_id=pane_id,
        title="",
        command="zsh",
        window="0",
        session="dopemux",
        path=str(Path.cwd()),
        active=False,
    )


def test_start_tmux_dope_layout_invokes_setup(monkeypatch):
    """Ensure the tmux CLI wires through to the Dope layout builder."""

    runner = CliRunner()

    fake_cfg_manager = SimpleNamespace(get_tmux_config=lambda: _FakeTmuxConfig())
    monkeypatch.setattr(tmux_cli, "_resolve_config_manager", lambda ctx: fake_cfg_manager)

    mock_controller = Mock()
    mock_controller.backend = Mock()
    mock_controller.backend.list_panes.return_value = []
    mock_controller.resolve_pane.return_value = SimpleNamespace(
        pane_id="%agent",
        session="dopemux",
        window="dopemux",
    )
    monkeypatch.setattr(
        tmux_cli,
        "_get_controller",
        lambda ctx, force_cli_backend=False: mock_controller,
    )

    monkeypatch.setattr(
        tmux_cli,
        "_prepare_orchestrator_base",
        lambda controller, session, start_dir, window_name, created_new_session: tmux_cli.PaneInfo(
            pane_id="%base",
            title="",
            command="zsh",
            window="0",
            session=session,
            path=start_dir,
            active=True,
        ),
    )

    setup_calls: list[tuple] = []

    def _fake_setup(controller, session, base_pane, start_dir, config, dual_agent, bootstrap):
        setup_calls.append((controller, session, base_pane, start_dir, config, dual_agent, bootstrap))
        return tmux_cli.OrchestratorLayout(
            monitors=["%m1", "%m2"],
            orchestrator="%orc",
            agent="%agent",
            sandbox="%sand",
            secondary_agent=None,
            metrics_bar="%metrics",
        )

    monkeypatch.setattr(tmux_cli, "_setup_dope_layout", _fake_setup)

    session_exists_calls = {"count": 0}

    def _fake_session_exists(_session: str) -> bool:
        session_exists_calls["count"] += 1
        # First call treats the session as missing, second call verifies creation
        return session_exists_calls["count"] > 1

    monkeypatch.setattr(tmux_cli.tmux_utils, "session_exists", _fake_session_exists)
    monkeypatch.setattr(tmux_cli.tmux_utils, "create_session", lambda *args, **kwargs: None)
    monkeypatch.setattr(tmux_cli.tmux_utils, "enable_pane_titles", lambda *args, **kwargs: None)
    monkeypatch.setattr(tmux_cli.tmux_utils, "set_environment", lambda *args, **kwargs: None)
    monkeypatch.setattr(tmux_cli.tmux_utils, "attach_session", lambda *args, **kwargs: None)
    monkeypatch.setattr(tmux_cli.tmux_utils, "switch_client", lambda *args, **kwargs: None)

    result = runner.invoke(
        tmux_cli.tmux,
        ["start", "--layout", "dope", "--no-happy", "--no-attach"],
    )

    assert result.exit_code == 0, result.output
    assert setup_calls, "Dope layout setup was not invoked"
    controller_arg, session_arg, *_ = setup_calls[0]
    assert controller_arg is mock_controller
    assert session_arg == "dopemux"


@pytest.mark.asyncio
async def test_dashboard_state_store_persistence(tmp_path):
    """End-to-end exercise of the dashboard state persistence loop."""

    from scripts.ui.neon_dashboard.config.settings import DopeLayoutSettings
    from scripts.ui.neon_dashboard.core.state import DashboardStateStore

    state_path = tmp_path / "dashboard-state.json"
    settings = DopeLayoutSettings(default_mode="implementation", state_file=state_path)
    store = DashboardStateStore(settings)
    await store.load()
    assert store.state.mode == "implementation"

    await store.toggle_mode()
    assert store.state.mode == "pm"

    # A second store should hydrate from the saved state file
    other_store = DashboardStateStore(settings)
    await other_store.load()
    assert other_store.state.mode == "pm"

    await store.set_selected_task("task-123", "Code panes")
    await store.set_active_transient("alert-untracked")

    updated = await other_store.poll_external_updates()
    assert updated is not None
    assert other_store.state.selected_task_id == "task-123"
    assert other_store.state.active_transient_id == "alert-untracked"


def _build_config_with_servers(servers):
    cfg = DopemuxConfig()
    cfg.mcp_servers = {
        name: MCPServerConfig(enabled=True, command=name, args=[], env={})
        for name in servers
    }
    return cfg


def _dummy_controller_for_agent(pane_title="agent:primary", pane_id="%1"):
    class DummyController:
        def __init__(self):
            self.sent_keys = []
            self.sent_ctrl = []
            pane = tmux_cli.PaneInfo(
                pane_id=pane_id,
                title=pane_title,
                command="zsh",
                window="0",
                session="dopemux",
                path=str(Path.cwd()),
                active=False,
            )
            self.backend = SimpleNamespace(list_panes=lambda: [pane])

        def send_key(self, pane_id, key):
            self.sent_ctrl.append((pane_id, key))

        def send_keys(self, pane_id, text, **kwargs):
            self.sent_keys.append((pane_id, text, kwargs))

    return DummyController()


def test_agent_switch_role_primary(monkeypatch):
    runner = CliRunner()

    config = _build_config_with_servers(["conport", "serena", "pal", "zen"])

    class DummyManager:
        def __init__(self, cfg):
            self.cfg = cfg

        def get_tmux_config(self):
            return SimpleNamespace(default_session="dopemux")

        def load_config(self):
            return self.cfg

    dummy_manager = DummyManager(config)
    dummy_controller = _dummy_controller_for_agent()

    monkeypatch.setattr(tmux_cli, "_resolve_config_manager", lambda ctx: dummy_manager)
    monkeypatch.setattr(tmux_cli, "_get_controller", lambda ctx: dummy_controller)
    monkeypatch.setattr(tmux_cli.tmux_utils, "focus_pane", lambda pane_id: None)

    result = runner.invoke(tmux_cli.tmux, ["agent", "switch-role", "act"])

    assert result.exit_code == 0, result.output
    assert dummy_controller.sent_keys, "Command not sent to pane"
    assert "dopemux start --role act" in dummy_controller.sent_keys[0][1]


def test_agent_switch_role_unknown(monkeypatch):
    runner = CliRunner()

    config = _build_config_with_servers(["conport"])

    class DummyManager:
        def get_tmux_config(self):
            return SimpleNamespace(default_session="dopemux")

        def load_config(self):
            return config

    dummy_controller = _dummy_controller_for_agent()

    monkeypatch.setattr(tmux_cli, "_resolve_config_manager", lambda ctx: DummyManager())
    monkeypatch.setattr(tmux_cli, "_get_controller", lambda ctx: dummy_controller)
    monkeypatch.setattr(tmux_cli.tmux_utils, "focus_pane", lambda pane_id: None)

    result = runner.invoke(tmux_cli.tmux, ["agent", "switch-role", "unknown"])

    assert result.exit_code == 0
    assert "Unknown role" in result.output


def test_agent_switch_role_missing_services(monkeypatch):
    runner = CliRunner()

    config = _build_config_with_servers(["conport", "pal"])

    class DummyManager:
        def __init__(self, cfg):
            self.cfg = cfg

        def get_tmux_config(self):
            return SimpleNamespace(default_session="dopemux")

        def load_config(self):
            return self.cfg

    dummy_controller = _dummy_controller_for_agent()

    monkeypatch.setattr(tmux_cli, "_resolve_config_manager", lambda ctx: DummyManager(config))
    monkeypatch.setattr(tmux_cli, "_get_controller", lambda ctx: dummy_controller)
    monkeypatch.setattr(tmux_cli.tmux_utils, "focus_pane", lambda pane_id: None)

    result = runner.invoke(tmux_cli.tmux, ["agent", "switch-role", "act"])

    assert result.exit_code == 0
    assert "dopemux mcp up --services" in result.output
