"""ConPort stdio tools (conport_mcp_stdio.py): the ids on the write tools are
optional and are not invented by the proxy; the REST port fills them (Amendment 04).

Uses W02's stdio loader and fake REST port.
"""

from __future__ import annotations

import pytest

pytest.importorskip("mcp.server.fastmcp")

from ..runner_memory_2a_r2_w02.helpers import BOUND_WORKSPACE as WS  # noqa: E402
from ..runner_memory_2a_r2_w02.test_mcp_surfaces import fake_rest  # noqa: E402
from ..runner_memory_2a_r2_w02.test_stdio_proxy import load_stdio  # noqa: E402,F401

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
WRITE_TOOLS = set(OMITTING) | {"update_context"}


async def test_should_advertise_the_ids_as_not_required_on_every_stdio_write_tool(load_stdio):
    module = load_stdio()
    tools = {tool.name: tool.inputSchema for tool in await module.mcp.list_tools()}
    for name in WRITE_TOOLS:
        schema = tools[name]
        assert "workspace_id" not in schema.get("required", []), name
        assert "binding" in schema["properties"]["workspace_id"].get("description", ""), name
        assert "ctx" not in schema["properties"], name
    for name in ("update_progress", "promote", "promote_all", "update_context", "log_progress", "log_decision"):
        assert "instance_id" not in tools[name].get("required", []), name
        assert "binding" in tools[name]["properties"]["instance_id"].get("description", ""), name
    assert "target_instance" in tools["fork_instance"]["required"]  # names the target, not the caller
    assert "instance_id" not in tools["save_custom_data"]["properties"]  # custom_data has no instance column
    for name in ("get_context", "get_progress", "search_content"):
        assert "workspace_id" in tools[name]["required"], name  # reads are unchanged


@pytest.mark.parametrize("tool", list(OMITTING))
async def test_should_call_rest_without_inventing_ids(load_stdio, tool):
    arguments, method, path = OMITTING[tool]
    async with fake_rest() as (rest_url, calls):
        module = load_stdio("off", rest_url=rest_url)
        await module.mcp.call_tool(tool, arguments)
    (call,) = calls
    assert (call["method"], call["path"]) == (method, path)
    sent = call["json"] or {}
    assert not sent.get("workspace_id"), sent
    assert not sent.get("instance_id"), sent


async def test_should_never_send_a_literal_none_in_the_delete_query(load_stdio):
    async with fake_rest() as (rest_url, calls):
        module = load_stdio("off", rest_url=rest_url)
        await module.mcp.call_tool("delete_custom_data", {"category": "c", "key": "k"})
    (call,) = calls
    assert "None" not in call["path"] and "workspace_id" not in call["path"]


async def test_should_send_the_bound_workspace_in_the_context_path_when_omitted(load_stdio, monkeypatch):
    monkeypatch.setenv("DOPEMUX_WORKSPACE_ID", WS)
    async with fake_rest() as (rest_url, calls):
        module = load_stdio("off", rest_url=rest_url)
        await module.mcp.call_tool("update_context", {"context_data": {"active_context": "x"}})
    (call,) = calls
    assert call["path"] == "/api/context/" + WS.replace("/", "%2F")
    assert not (call["json"] or {}).get("workspace_id")


async def test_should_refuse_an_omitted_context_workspace_on_an_unbound_server(load_stdio, monkeypatch):
    monkeypatch.delenv("DOPEMUX_WORKSPACE_ID", raising=False)
    async with fake_rest() as (rest_url, calls):
        module = load_stdio("off", rest_url=rest_url)
        with pytest.raises(Exception, match="no workspace binding"):
            await module.mcp.call_tool("update_context", {"context_data": {"active_context": "x"}})
    assert calls == []


async def test_should_pass_supplied_ids_through_unchanged(load_stdio):
    async with fake_rest() as (rest_url, calls):
        module = load_stdio("off", rest_url=rest_url)
        await module.mcp.call_tool(
            "log_progress", {"workspace_id": WS, "instance_id": "inst-x", "description": "d"})
    (call,) = calls
    assert call["json"]["workspace_id"] == WS and call["json"]["instance_id"] == "inst-x"
