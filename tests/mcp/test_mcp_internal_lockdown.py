"""TP-2 (MCP-internal lockdown) regression tests.

Covers the audit fixes:
- MCP1-04: spawned child MCP processes must not inherit undeclared host secrets.
- MCP1-05: session_id must be sanitized before it is used in a filesystem path.
"""
from __future__ import annotations

import pytest

from dopemux.mcp.session_manager import SessionManager


def _load_build_child_env():
    # server_manager imports `websockets` at module top; skip (NOT_RUN) where it isn't
    # installed rather than failing collection.
    pytest.importorskip("websockets")
    from dopemux.mcp.server_manager import _build_child_env

    return _build_child_env


def test_build_child_env_does_not_leak_undeclared_secrets(monkeypatch):
    # MCP1-04: only base operational vars + declared secrets + per-server env reach a child.
    build_child_env = _load_build_child_env()
    monkeypatch.setenv("PATH", "/usr/bin")
    monkeypatch.setenv("FOO_DECLARED_KEY", "declared-secret")
    monkeypatch.setenv("UNDECLARED_SECRET_KEY", "should-not-leak")
    config = {"requires_env": ["FOO_DECLARED_KEY"], "environment": {"EXTRA": "x"}}

    env = build_child_env(config)

    assert env.get("PATH") == "/usr/bin"                     # base operational var
    assert env.get("FOO_DECLARED_KEY") == "declared-secret"  # declared secret forwarded
    assert env.get("EXTRA") == "x"                           # per-server env forwarded
    assert "UNDECLARED_SECRET_KEY" not in env                # undeclared secret NOT leaked


def test_build_child_env_per_server_env_overrides_host(monkeypatch):
    build_child_env = _load_build_child_env()
    monkeypatch.setenv("FOO_DECLARED_KEY", "host-value")
    config = {
        "requires_env": ["FOO_DECLARED_KEY"],
        "environment": {"FOO_DECLARED_KEY": "override"},
    }
    assert build_child_env(config)["FOO_DECLARED_KEY"] == "override"


def test_safe_session_filename_accepts_valid():
    assert SessionManager._safe_session_filename("abc-123_X") == "abc-123_X.json"


@pytest.mark.parametrize(
    "bad",
    ["../etc/passwd", "a/b", "..", "", "a.b", "a b", "a/../b", "/abs"],
)
def test_safe_session_filename_rejects_traversal(bad):
    # MCP1-05: reject path separators / parent refs / unexpected chars.
    with pytest.raises(ValueError):
        SessionManager._safe_session_filename(bad)
