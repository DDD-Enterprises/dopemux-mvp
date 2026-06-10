"""Tests for the /mcp streamable-HTTP endpoint (mcp_http module).

Verifies:
- The FastMCP server exposes the full memory_* tool surface.
- Tools delegate to DopeMemoryMCPServer (store -> search round trip).
- Tool failures surface as MCP tool errors, not silent successes.
- dope_memory_main mounts the MCP app so /mcp resolves on the FastAPI app.

Requires fastmcp (installed in the service image via dopemux[services]);
skipped automatically where fastmcp is unavailable.
"""

import pytest

fastmcp = pytest.importorskip("fastmcp")

from fastmcp import Client  # noqa: E402
from fastmcp.exceptions import ToolError  # noqa: E402

import mcp_http  # noqa: E402

EXPECTED_TOOLS = {
    "memory_search",
    "memory_store",
    "memory_recap",
    "memory_mark_issue",
    "memory_link_resolution",
    "memory_replay_session",
    "memory_correct",
    "memory_generate_reflection",
    "memory_reflections",
    "memory_trajectory",
}


@pytest.fixture()
def backend(tmp_path, monkeypatch):
    """DopeMemoryMCPServer against a temp canonical ledger."""
    monkeypatch.setenv(
        "DOPEMUX_CAPTURE_LEDGER_PATH", str(tmp_path / "chronicle.sqlite")
    )
    from dope_memory_main import DopeMemoryMCPServer

    return DopeMemoryMCPServer(workspace_id="test-ws", instance_id="A")


@pytest.fixture()
def mcp_server(backend):
    return mcp_http.build_mcp_server(
        lambda: backend,
        default_workspace_id="test-ws",
        default_instance_id="A",
    )


@pytest.mark.asyncio
async def test_should_expose_all_memory_tools(mcp_server):
    async with Client(mcp_server) as client:
        tools = await client.list_tools()
    assert {t.name for t in tools} == EXPECTED_TOOLS


@pytest.mark.asyncio
async def test_should_round_trip_store_and_search(mcp_server):
    async with Client(mcp_server) as client:
        stored = await client.call_tool(
            "memory_store",
            {
                "category": "implementation",
                "entry_type": "decision",
                "summary": "MCP endpoint round-trip entry",
                "importance_score": 8,
            },
        )
        assert stored.data["created"] is True
        assert stored.data["entry_id"]

        found = await client.call_tool(
            "memory_search", {"query": "round-trip"}
        )
        summaries = [item["summary"] for item in found.data["items"]]
        assert "MCP endpoint round-trip entry" in summaries


@pytest.mark.asyncio
async def test_should_raise_tool_error_when_backend_fails(mcp_server):
    async with Client(mcp_server) as client:
        with pytest.raises(ToolError):
            # Nonexistent entry id -> backend returns success=False.
            await client.call_tool(
                "memory_mark_issue",
                {"issue_entry_id": "missing-entry", "description": "nope"},
            )


@pytest.mark.asyncio
async def test_should_error_when_backend_not_initialized():
    mcp_server = mcp_http.build_mcp_server(
        lambda: None, default_workspace_id="x", default_instance_id="A"
    )
    async with Client(mcp_server) as client:
        with pytest.raises(ToolError, match="not initialized"):
            await client.call_tool("memory_trajectory", {})


def test_should_mount_mcp_app_on_fastapi(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "DOPEMUX_CAPTURE_LEDGER_PATH", str(tmp_path / "chronicle.sqlite")
    )
    import dope_memory_main

    assert dope_memory_main.FASTMCP_AVAILABLE
    assert dope_memory_main.mcp_http_app is not None
    # The catch-all mount must come after the REST routes.
    mounts = [
        r
        for r in dope_memory_main.app.routes
        if getattr(r, "app", None) is dope_memory_main.mcp_http_app
    ]
    assert len(mounts) == 1
    rest_paths = {getattr(r, "path", None) for r in dope_memory_main.app.routes}
    assert "/health" in rest_paths
    assert "/tools/memory_search" in rest_paths
