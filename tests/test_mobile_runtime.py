"""Unit tests for Dopemux mobile runtime helpers."""

from dopemux.config.manager import MobileConfig
import dopemux.mobile.runtime as mobile_runtime
from dopemux.mobile.runtime import (
    LaunchOutcome,
    MobileStatus,
    launch_happy_sessions,
    resolve_targets,
    update_tmux_mobile_indicator,
)
from dopemux.tmux.common import PaneInfo, TmuxError
from dopemux.tmux.controller import TmuxController
from unittest.mock import MagicMock
import pytest


def _pane(
    pane_id: str,
    title: str,
    command: str,
    window: str,
    active: bool = False,
    session: str = "session-0",

) -> PaneInfo:
    return PaneInfo(
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

    controller = MagicMock(spec=TmuxController)
    controller.list_panes.return_value = panes
    
    mobile_cfg = MobileConfig(default_panes="primary")
    result = resolve_targets(False, [], mobile_cfg, controller=controller)

    assert result == [panes[1]]


def test_resolve_all_with_flag(monkeypatch):
    panes = [
        _pane("%1", "agent-a", "claude", "workspace"),
        _pane("%2", "agent-b", "claude", "workspace"),
    ]
    controller = MagicMock(spec=TmuxController)
    controller.list_panes.return_value = panes

    result = resolve_targets(True, [], MobileConfig(), controller=controller)

    assert result == panes


def test_resolve_explicit_match(monkeypatch):
    panes = [
        _pane("%1", "agent-c", "claude", "workspace"),
        _pane("%2", "builder", "claude", "workspace"),
    ]
    controller = MagicMock(spec=TmuxController)
    controller.list_panes.return_value = panes

    mobile_cfg = MobileConfig()
    result = resolve_targets(False, ["builder"], mobile_cfg, controller=controller)

    assert result == [panes[1]]


def test_resolve_map_agents_returns_all(monkeypatch):
    panes = [
        _pane("%1", "agent-a", "claude", "workspace"),
        _pane("%2", "agent-b", "claude", "workspace"),
    ]
    controller = MagicMock(spec=TmuxController)
    controller.list_panes.return_value = panes
    
    mobile_cfg = MobileConfig(default_panes="primary")
    result = resolve_targets(False, [], mobile_cfg, mapping_strategy="agents", controller=controller)

    assert result == panes


def test_launch_happy_sessions_applies_labels(monkeypatch):
    panes = [
        _pane("%1", "agent-a", "claude", "workspace"),
        _pane("%2", "agent-b", "claude", "workspace"),
    ]

    controller = MagicMock(spec=TmuxController)
    controller.list_panes.return_value = [] # existing labels empty
    controller.backend = MagicMock()
    
    # Mock window creation sequence
    # First iteration: new_window("mobile"). Returns pane-1.
    # Second iteration: backend.split_window(target="mobile"). Returns pane-2.
    
    controller.new_window.return_value = "pane-1"
    controller.backend.split_window.return_value = "pane-2"
    
    titles = {}
    def fake_set_pane_title(pane_id, title):
        titles[pane_id] = title
    controller.set_pane_title.side_effect = fake_set_pane_title
    
    outcome = launch_happy_sessions(
        panes,
        env={},
        mobile_config=MobileConfig(),
        labels=["Reviewer", "Navigator"],
        controller=controller,
    )

    assert isinstance(outcome, LaunchOutcome)
    assert outcome.started == ["Reviewer", "Navigator"]
    assert outcome.skipped_existing == []
    assert titles == {"pane-1": "mobile:Reviewer", "pane-2": "mobile:Navigator"}
    assert controller.new_window.called


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

    controller = MagicMock(spec=TmuxController)
    
    # get_mobile_status calls list_mobile_panes -> controller.list_panes
    # We need list_panes to return something or empty? 
    # Actually get_mobile_status catches errors.
    # The existing test mocks get_mobile_status directly to return snapshot.
    # We can keep doing that if get_mobile_status accepts controller?
    # No, get_mobile_status is what calls controller.
    # But here the test *mocks* get_mobile_status entirely.
    # Does get_mobile_status accept controller now? Yes.
    
    # If we mock d.m.r.get_mobile_status, we bypass internal controller usage there.
    # BUT update_tmux_mobile_indicator calls controller.set_global_option.
    
    # So we need to ensure update_tmux_mobile_indicator uses our mock controller.
    # It accepts controller argument.
    
    monkeypatch.setattr(mobile_runtime, "get_mobile_status", lambda cfg, ctrl: snapshot)
    monkeypatch.setattr(mobile_runtime, "_persist_mobile_status", lambda cfg, status: None)

    update_tmux_mobile_indicator(DummyCM(), controller=controller)
    
    
    # Check call args manually since color codes make exact match brittle
    assert controller.set_global_option.called
    args = controller.set_global_option.call_args
    assert args[0][0] == "@dopemux_mobile_indicator"
    assert "📱" in args[0][1]
