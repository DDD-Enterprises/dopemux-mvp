"""Regression test for PR #1188 review finding: info_server.py advertised the
REST bind port (3004) as the MCP/SSE connection URL instead of the real SSE
listener port (3005), making /info service-discovery unusable.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

MODULE_DIR = Path(__file__).resolve().parents[1]


def _load_info_server(monkeypatch, mcp_server_port: str, advertised: str | None):
    monkeypatch.setenv("MCP_SERVER_PORT", mcp_server_port)
    if advertised is None:
        monkeypatch.delenv("CONPORT_ADVERTISED_MCP_PORT", raising=False)
    else:
        monkeypatch.setenv("CONPORT_ADVERTISED_MCP_PORT", advertised)
    sys.path.insert(0, str(MODULE_DIR))
    sys.modules.pop("info_server", None)
    try:
        return importlib.import_module("info_server")
    finally:
        sys.path.remove(str(MODULE_DIR))


def test_advertised_url_uses_real_sse_port_not_rest_bind_port(monkeypatch):
    """start_with_info.sh runs this process with MCP_SERVER_PORT=3004 (REST)
    but CONPORT_ADVERTISED_MCP_PORT=3005 (the real SSE child)."""
    from fastapi.testclient import TestClient

    info_server = _load_info_server(monkeypatch, "3004", "3005")
    client = TestClient(info_server.app)

    body = client.get("/info").json()
    assert body["mcp"]["connection"]["url"] == "http://localhost:3005/sse"
    assert body["metadata"]["mcp_port"] == 3005
    assert body["metadata"]["info_port"] == 4004


def test_advertised_port_defaults_to_bind_port_plus_one_when_unset(monkeypatch):
    """Standalone/legacy invocation without the new env var still works."""
    from fastapi.testclient import TestClient

    info_server = _load_info_server(monkeypatch, "3004", None)
    client = TestClient(info_server.app)

    body = client.get("/info").json()
    assert body["mcp"]["connection"]["url"] == "http://localhost:3005/sse"
