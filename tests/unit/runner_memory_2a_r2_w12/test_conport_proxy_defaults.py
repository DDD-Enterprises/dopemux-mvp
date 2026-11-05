"""ConPort SSE / streamable-HTTP tools (server.py): the ids on the write tools are
optional and are not invented by the proxy; the REST port fills them.

Driven with the real MCP client in front of a fake REST port (W02 harness).
"""

from __future__ import annotations

import pytest

pytest.importorskip("mcp.server.fastmcp")
pytest.importorskip("uvicorn")
pytest.importorskip("httpx")

from ..runner_memory_2a_r2_w02.helpers import BOUND_WORKSPACE as WS  # noqa: E402
from ..runner_memory_2a_r2_w02.test_mcp_surfaces import (  # noqa: E402,F401
    fake_rest,
    load_server,
    mcp_session,
    serve,
)

PID = "22222222-2222-2222-2222-222222222222"

# tool -> (arguments with NO identity fields, method, path)
OMITTING = {
    "update_progress": ({"progress_id": PID, "updates": {"status": "COMPLETED"}}, "PUT", f"/api/progress/{PID}"),
    "log_decision": ({"topic": "t", "decision": "d", "rationale": "r"}, "POST", "/api/decisions"),
    "fork_instance": ({"target_instance": "inst-a"}, "POST", "/api/instance/fork"),
    "promote": ({"progress_id": PID}, "POST", "/api/progress/promote"),
    "promote_all": ({}, "POST", "/api/progress/promote_all"),
    "log_progress": ({"description": "d"}, "POST", "/api/progress"),
    "save_custom_data": ({"category": "c", "key": "k", "value": {"a": 1}}, "POST", "/api/custom_data"),
    "delete_custom_data": ({"category": "c", "key": "k"}, "DELETE", "/api/custom_data"),
}


@pytest.mark.parametrize("transport", ["sse", "streamable"])
async def test_should_mark_the_ids_optional_on_every_write_tool(load_server, transport):
    module = load_server("log")
    async with serve(module.build_http_app()) as base:
        async with mcp_session(transport, base) as session:
            tools = {tool.name: tool.inputSchema for tool in (await session.list_tools()).tools}
    for name in ("update_progress", "promote", "promote_all", "update_context", "log_progress",
                 "log_decision", "save_custom_data", "delete_custom_data", "fork_instance"):
        schema = tools[name]
        assert "workspace_id" not in schema.get("required", []), name
        assert "binding" in schema["properties"]["workspace_id"].get("description", ""), name
    for name in ("update_progress", "promote", "promote_all", "update_context", "log_progress", "log_decision"):
        assert "instance_id" not in tools[name].get("required", []), name
        assert "binding" in tools[name]["properties"]["instance_id"].get("description", ""), name
    assert "target_instance" in tools["fork_instance"]["required"]  # names the target, not the caller
    assert "instance_id" not in tools["save_custom_data"]["properties"]  # custom_data has no instance column
    for name in ("get_context", "get_progress", "search_content"):
        assert "workspace_id" in tools[name]["required"], name  # reads are unchanged


@pytest.mark.parametrize("transport", ["sse", "streamable"])
@pytest.mark.parametrize("tool", list(OMITTING))
async def test_should_call_rest_without_inventing_ids(load_server, transport, tool):
    arguments, method, path = OMITTING[tool]
    async with fake_rest() as (rest_url, calls):
        module = load_server("off", rest_url=rest_url)
        async with serve(module.build_http_app()) as base:
            async with mcp_session(transport, base) as session:
                result = await session.call_tool(tool, arguments)
                assert not result.isError, result
    (call,) = calls
    assert (call["method"], call["path"]) == (method, path)
    sent = call["json"] or {}
    assert not sent.get("workspace_id"), sent
    assert not sent.get("instance_id"), sent
    if tool == "delete_custom_data":
        assert call["path"] == "/api/custom_data"


async def test_should_send_the_bound_workspace_in_the_context_path_when_omitted(load_server, monkeypatch):
    monkeypatch.setenv("DOPEMUX_WORKSPACE_ID", WS)
    async with fake_rest() as (rest_url, calls):
        module = load_server("off", rest_url=rest_url)
        async with serve(module.build_http_app()) as base:
            async with mcp_session("streamable", base) as session:
                result = await session.call_tool("update_context", {"context_data": {"active_context": "x"}})
                assert not result.isError, result
    (call,) = calls
    assert call["path"] == "/api/context/" + WS.replace("/", "%2F")


async def test_should_refuse_an_omitted_context_workspace_on_an_unbound_server(load_server, monkeypatch):
    monkeypatch.delenv("DOPEMUX_WORKSPACE_ID", raising=False)
    async with fake_rest() as (rest_url, calls):
        module = load_server("off", rest_url=rest_url)
        async with serve(module.build_http_app()) as base:
            async with mcp_session("streamable", base) as session:
                result = await session.call_tool("update_context", {"context_data": {"active_context": "x"}})
                assert result.isError
    assert calls == []


async def test_should_pass_supplied_ids_through_unchanged(load_server):
    async with fake_rest() as (rest_url, calls):
        module = load_server("off", rest_url=rest_url)
        async with serve(module.build_http_app()) as base:
            async with mcp_session("streamable", base) as session:
                await session.call_tool("log_progress", {"workspace_id": WS, "instance_id": "inst-x", "description": "d"})
    (call,) = calls
    assert call["json"]["workspace_id"] == WS and call["json"]["instance_id"] == "inst-x"
