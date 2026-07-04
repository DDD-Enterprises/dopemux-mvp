"""DCP read-only MCP server wiring tests.

These tests replace the optional FastMCP dependency with a recording stub before
importing ``mcp.server``. That keeps the assertions focused on stdio facade tool
registration and delegation without opening network or MCP transports.
"""

from __future__ import annotations

import asyncio
import importlib
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
    monkeypatch.setenv("DCP_FACADE_REGISTRY", str(tmp_path / "missing-registry.yaml"))
    monkeypatch.setitem(sys.modules, "fastmcp", types.SimpleNamespace(FastMCP=RecordingFastMCP))
    sys.modules.pop("mcp.server", None)
    module = importlib.import_module("mcp.server")
    assert RecordingFastMCP.instances, "mcp.server import did not instantiate FastMCP"
    yield module, RecordingFastMCP.instances[-1]
    sys.modules.pop("mcp.server", None)


def test_mcp_server_registers_packet_0006_tools(server_module):
    _, mcp = server_module
    assert mcp.name == "dcp-readonly-facade"
    assert set(mcp.tools) == {
        "list_projects",
        "get_project_capabilities",
        "get_repo_state_snapshot",
        "list_proof_bundles",
        "fetch_proof_bundle",
        "search_decisions",
        "search_progress",
        "search_chronicle",
        "replay_chronicle_session",
        "search_code_docs",
        "get_index_status",
        "get_workflow_status_snapshot",
    }


def test_search_code_docs_delegates_to_pure_facade_function(server_module, monkeypatch):
    server, _ = server_module
    captured = {}
    sentinel = {"status": "BLOCKED", "data": None}

    def fake_search_code_docs(
        registry,
        project_id,
        query,
        top_k,
        *,
        kind,
        profile,
        filter_doc_type,
    ):
        captured.update(
            {
                "registry": registry,
                "project_id": project_id,
                "query": query,
                "top_k": top_k,
                "kind": kind,
                "profile": profile,
                "filter_doc_type": filter_doc_type,
            }
        )
        return sentinel

    monkeypatch.setattr(server.tools, "search_code_docs", fake_search_code_docs)
    result = asyncio.run(
        server.search_code_docs(
            "dopemux",
            "catalog contract",
            top_k=7,
            kind="docs",
            profile="implementation",
            filter_doc_type="md",
        )
    )

    assert result is sentinel
    assert captured == {
        "registry": server._REGISTRY,
        "project_id": "dopemux",
        "query": "catalog contract",
        "top_k": 7,
        "kind": "docs",
        "profile": "implementation",
        "filter_doc_type": "md",
    }


def test_status_wrappers_delegate_to_pure_facade_functions(server_module, monkeypatch):
    server, _ = server_module
    captured = []

    def fake_index_status(registry, project_id):
        captured.append(("index", registry, project_id))
        return {"status": "BLOCKED"}

    def fake_workflow_snapshot(registry, project_id):
        captured.append(("workflow", registry, project_id))
        return {"status": "OK"}

    monkeypatch.setattr(server.tools, "get_index_status", fake_index_status)
    monkeypatch.setattr(server.tools, "get_workflow_status_snapshot", fake_workflow_snapshot)

    assert asyncio.run(server.get_index_status("dopemux")) == {"status": "BLOCKED"}
    assert asyncio.run(server.get_workflow_status_snapshot("dopemux")) == {"status": "OK"}
    assert captured == [
        ("index", server._REGISTRY, "dopemux"),
        ("workflow", server._REGISTRY, "dopemux"),
    ]
