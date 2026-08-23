"""FastMCP v2 public-surface registration tests."""

from __future__ import annotations

import asyncio
import importlib
import inspect
import sys
import types

import pytest


class RecordingFastMCP:
    instances: list["RecordingFastMCP"] = []

    def __init__(self, name: str):
        self.name = name
        self.tools: dict[str, object] = {}
        RecordingFastMCP.instances.append(self)

    def tool(self, *args, **kwargs):
        def decorator(func):
            self.tools[func.__name__] = func
            return func

        return decorator

    def run(self, *args, **kwargs):  # pragma: no cover - main() is not exercised here
        self.run_args = (args, kwargs)


@pytest.fixture()
def server_module(monkeypatch, tmp_path):
    RecordingFastMCP.instances = []
    monkeypatch.setenv("DCP_FACADE_REGISTRY_V2", str(tmp_path / "missing-registry-v2.yaml"))
    monkeypatch.delenv("DCP_FACADE_REGISTRY", raising=False)
    monkeypatch.setitem(sys.modules, "fastmcp", types.SimpleNamespace(FastMCP=RecordingFastMCP))
    sys.modules.pop("mcp.server", None)
    module = importlib.import_module("mcp.server")
    assert RecordingFastMCP.instances, "mcp.server import did not instantiate FastMCP"
    yield module, RecordingFastMCP.instances[-1]
    sys.modules.pop("mcp.server", None)


def test_mcp_server_registers_v2_target_tools_only(server_module):
    server, mcp = server_module

    assert mcp.name == "dcp-readonly-facade"
    assert set(mcp.tools) == {
        "list_targets",
        "get_target_capabilities",
        "get_target_repo_state_snapshot",
        "list_target_proof_bundles",
        "fetch_target_proof_bundle",
        "get_target_runtime_receipt",
    }
    assert type(server._REGISTRY).__name__ == "RegistryV2"
    for name, tool in mcp.tools.items():
        if name != "list_targets":
            assert "target_id" in inspect.signature(tool).parameters


def test_v2_server_delegates_target_id_to_pure_facade_function(server_module, monkeypatch):
    server, _ = server_module
    captured = {}
    sentinel = {"status": "OK", "target_id": "target-main"}

    def fake_snapshot(registry, target_id):
        captured.update({"registry": registry, "target_id": target_id})
        return sentinel

    monkeypatch.setattr(server.tools_v2, "get_target_repo_state_snapshot", fake_snapshot)

    result = asyncio.run(server.get_target_repo_state_snapshot("target-main"))

    assert result is sentinel
    assert captured == {"registry": server._REGISTRY, "target_id": "target-main"}
