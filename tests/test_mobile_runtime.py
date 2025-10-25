"""Unit tests for Dopemux mobile runtime helpers."""

from dopemux.config.manager import MobileConfig
from dopemux.mobile.runtime import resolve_targets
from dopemux.mobile.tmux_utils import TmuxPane


def _pane(pane_id: str, title: str, command: str, window: str, active: bool = False) -> TmuxPane:
    return TmuxPane(
        pane_id=pane_id,
        title=title,
        command=command,
        window=window,
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
