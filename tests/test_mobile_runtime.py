"""Unit tests for Dopemux mobile runtime helpers."""

from dopemux.config.manager import MobileConfig
from dopemux.mobile.runtime import (
    LaunchOutcome,
    MobileStatus,
    launch_happy_sessions,
    resolve_targets,
    update_tmux_mobile_indicator,
)
from dopemux.tmux.utils import TmuxPane


def _pane(
    pane_id: str,
    title: str,
    command: str,
    window: str,
    active: bool = False,
    session: str = "session-0",
) -> TmuxPane:
    return TmuxPane(
        pane_id=pane_id,
        title=title,
        command=command,
        window=window,
        session=session,
        active=active,
        path="/tmp",
    )


def test_resolve_primary_prefers_active(monkeypatch):
    panes = [
        _pane("%1", "agent-primary", "claude", "workspace", active=False),
        _pane("%2", "agent-secondary", "claude", "workspace", active=True),
    ]

    monkeypatch.setattr("dopemux.mobile.runtime.list_claude_panes", lambda: panes)

    mobile_cfg = MobileConfig(default_panes="primary")
    result = resolve_targets(False, [], mobile_cfg)

    assert result == [panes[1]]


def test_resolve_all_with_flag(monkeypatch):
    panes = [
        _pane("%1", "agent-a", "claude", "workspace"),
        _pane("%2", "agent-b", "claude", "workspace"),
    ]
    monkeypatch.setattr("dopemux.mobile.runtime.list_claude_panes", lambda: panes)

    result = resolve_targets(True, [], MobileConfig())

    assert result == panes


def test_resolve_explicit_match(monkeypatch):
    panes = [
        _pane("%1", "agent-c", "claude", "workspace"),
        _pane("%2", "builder", "claude", "workspace"),
    ]
    monkeypatch.setattr("dopemux.mobile.runtime.list_claude_panes", lambda: panes)

    mobile_cfg = MobileConfig()
    result = resolve_targets(False, ["builder"], mobile_cfg)

    assert result == [panes[1]]


def test_resolve_map_agents_returns_all(monkeypatch):
    panes = [
        _pane("%1", "agent-a", "claude", "workspace"),
        _pane("%2", "agent-b", "claude", "workspace"),
    ]
    monkeypatch.setattr("dopemux.mobile.runtime.list_claude_panes", lambda: panes)

    mobile_cfg = MobileConfig(default_panes="primary")
    result = resolve_targets(False, [], mobile_cfg, mapping_strategy="agents")

    assert result == panes


def test_launch_happy_sessions_applies_labels(monkeypatch):
    panes = [
        _pane("%1", "agent-a", "claude", "workspace"),
        _pane("%2", "agent-b", "claude", "workspace"),
    ]

    monkeypatch.setattr("dopemux.mobile.runtime._existing_mobile_labels", lambda: [])
    monkeypatch.setattr("dopemux.mobile.runtime.list_windows", lambda: [])

    created_commands = []

    def fake_new_window(window_name, command):
        created_commands.append(("new", window_name, command))
        return "pane-1"

    def fake_split_window(target, command, vertical=False):
        created_commands.append(("split", target, command, vertical))
        return "pane-2"

    titles = {}

    def fake_set_pane_title(pane_id, title):
        titles[pane_id] = title

    monkeypatch.setattr("dopemux.mobile.runtime.new_window", fake_new_window)
    monkeypatch.setattr("dopemux.mobile.runtime.split_window", fake_split_window)
    monkeypatch.setattr("dopemux.mobile.runtime.set_pane_title", fake_set_pane_title)
    monkeypatch.setattr("dopemux.mobile.runtime.set_layout", lambda *args, **kwargs: None)

    outcome = launch_happy_sessions(
        panes,
        env={},
        mobile_config=MobileConfig(),
        labels=["Reviewer", "Navigator"],
    )

    assert isinstance(outcome, LaunchOutcome)
    assert outcome.started == ["Reviewer", "Navigator"]
    assert outcome.skipped_existing == []
    assert titles == {"pane-1": "mobile:Reviewer", "pane-2": "mobile:Navigator"}
    assert created_commands[0][0] == "new"


def test_update_tmux_mobile_indicator_sets_option(monkeypatch):
    class DummyCM:
        def get_mobile_config(self):
            return MobileConfig()

    snapshot = MobileStatus(
        enabled=True,
        happy_ok=True,
        claude_ok=True,
        sessions=[],
        tmux_error=None,
    )

    monkeypatch.setattr("dopemux.mobile.runtime.get_mobile_status", lambda cfg: snapshot)

    captured = {}

    def fake_set_global_option(option, value):
        captured["option"] = option
        captured["value"] = value

    monkeypatch.setattr("dopemux.mobile.runtime.set_global_option", fake_set_global_option)
    monkeypatch.setattr("dopemux.mobile.runtime._persist_mobile_status", lambda cfg, status: captured.setdefault("persist", True))

    update_tmux_mobile_indicator(DummyCM())

    assert captured["option"] == "@dopemux_mobile_indicator"
    assert "📱" in captured["value"]
