"""The SSE and the new streamable-HTTP surface of ``server.py``.

Both are served by one uvicorn listener (as in the image) in front of a fake
REST port, and driven with the real MCP client.  Covered: the streamable
handshake, 17 tools on both surfaces, auth in each mode, token forwarding to
REST and the ids on the write tools.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from urllib.parse import quote

import pytest

pytest.importorskip("mcp.server.fastmcp")
pytest.importorskip("uvicorn")
pytest.importorskip("httpx")

import httpx  # noqa: E402
from aiohttp import web  # noqa: E402
from aiohttp.test_utils import TestServer  # noqa: E402

from .conftest import load_conport_module  # noqa: E402
from .helpers import BOUND_WORKSPACE, INSTANCE, SSE_TOOL_NAMES, fake_token, write_hash_file  # noqa: E402

WS = BOUND_WORKSPACE
PID = "22222222-2222-2222-2222-222222222222"
ACCEPT = "application/json, text/event-stream"

WRITE_CALLS = {
    "update_progress": (
        {"progress_id": PID, "workspace_id": WS, "instance_id": INSTANCE, "updates": {"status": "COMPLETED"}},
        "PUT", f"/api/progress/{PID}",
    ),
    "log_decision": (
        {"workspace_id": WS, "topic": "t", "decision": "d", "rationale": "r"}, "POST", "/api/decisions",
    ),
    "fork_instance": (
        {"workspace_id": WS, "target_instance": INSTANCE}, "POST", "/api/instance/fork",
    ),
    "promote": (
        {"progress_id": PID, "workspace_id": WS, "instance_id": INSTANCE}, "POST", "/api/progress/promote",
    ),
    "promote_all": ({"workspace_id": WS, "instance_id": INSTANCE}, "POST", "/api/progress/promote_all"),
    "update_context": (
        {"workspace_id": WS, "instance_id": INSTANCE, "context_data": {"active_context": "x"}},
        "POST", f"/api/context/{quote(WS, safe='')}",
    ),
    "log_progress": (
        {"workspace_id": WS, "instance_id": INSTANCE, "description": "d"}, "POST", "/api/progress",
    ),
    "save_custom_data": (
        {"workspace_id": WS, "category": "c", "key": "k", "value": {"a": 1}}, "POST", "/api/custom_data",
    ),
    "delete_custom_data": (
        {"workspace_id": WS, "category": "c", "key": "k"}, "DELETE", "/api/custom_data",
    ),
}


@contextlib.asynccontextmanager
async def fake_rest():
    calls: list[dict] = []

    async def handler(request: web.Request) -> web.Response:
        body = await request.read()
        calls.append(
            {
                "method": request.method,
                "path": request.raw_path.split("?", 1)[0],
                "headers": {k.lower(): v for k, v in request.headers.items()},
                "json": json.loads(body) if body else None,
            }
        )
        return web.json_response({"ok": True})

    app = web.Application()
    app.router.add_route("*", "/{tail:.*}", handler)
    server = TestServer(app)
    await server.start_server()
    try:
        yield f"http://127.0.0.1:{server.port}", calls
    finally:
        await server.close()


@contextlib.asynccontextmanager
async def serve(app):
    import uvicorn

    config = uvicorn.Config(app, host="127.0.0.1", port=0, log_level="warning", lifespan="on")
    server = uvicorn.Server(config)
    task = asyncio.create_task(server.serve())
    for _ in range(500):
        if server.started:
            break
        await asyncio.sleep(0.01)
    else:  # pragma: no cover
        raise RuntimeError("uvicorn did not start")
    port = server.servers[0].sockets[0].getsockname()[1]
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.should_exit = True
        await task


@pytest.fixture()
def load_server(monkeypatch, tmp_path):
    def factory(mode="log", tokens=None, proxy_token=None, rest_url=None):
        monkeypatch.setenv("CONPORT_AUTH_MODE", mode)
        write_hash_file(tmp_path / "auth", tokens or {})
        monkeypatch.setenv("CONPORT_AUTH_DIR", str(tmp_path / "auth"))
        module = load_conport_module("server", monkeypatch)
        module.PROXY_TOKEN_PROVIDER = lambda: proxy_token
        if rest_url:
            module.CONPORT_URL = rest_url
        return module

    return factory


@contextlib.asynccontextmanager
async def mcp_session(transport: str, base: str, headers=None):
    from mcp import ClientSession

    headers = headers or {}
    if transport == "sse":
        from mcp.client.sse import sse_client

        async with sse_client(f"{base}/sse", headers=headers) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session
    else:
        from mcp.client import streamable_http as sh

        client = httpx.AsyncClient(headers=headers, timeout=30)
        async with client:
            async with sh.streamable_http_client(f"{base}/mcp", http_client=client) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    yield session


def _sse_data(text: str) -> dict:
    for line in text.splitlines():
        if line.startswith("data:"):
            return json.loads(line[5:].strip())
    return json.loads(text)


def _rpc(method, params=None, rid=1):
    return {"jsonrpc": "2.0", "id": rid, "method": method, **({"params": params} if params else {})}


INIT = _rpc(
    "initialize",
    {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "w02-test", "version": "0"}},
)


# -- transport ------------------------------------------------------------------------------


async def test_should_complete_the_streamable_handshake_with_a_session_id(load_server):
    module = load_server("log")
    async with serve(module.build_http_app()) as base:
        async with httpx.AsyncClient(base_url=base, timeout=30) as client:
            init = await client.post("/mcp", json=INIT, headers={"Accept": ACCEPT})
            assert init.status_code == 200
            session = init.headers["mcp-session-id"]
            assert session
            assert _sse_data(init.text)["result"]["serverInfo"]["name"] == "conport"
            headers = {"Accept": ACCEPT, "Mcp-Session-Id": session}
            done = await client.post("/mcp", json={"jsonrpc": "2.0", "method": "notifications/initialized"},
                                     headers=headers)
            assert done.status_code == 202
            listing = await client.post("/mcp", json=_rpc("tools/list", rid=2), headers=headers)
            names = {tool["name"] for tool in _sse_data(listing.text)["result"]["tools"]}
            assert names == SSE_TOOL_NAMES and len(names) == 17
            no_session = await client.post("/mcp", json=_rpc("tools/list", rid=3), headers={"Accept": ACCEPT})
            assert no_session.status_code == 400


async def test_should_keep_serving_sse_beside_the_streamable_path(load_server):
    module = load_server("log")
    paths = {getattr(route, "path", None) for route in module.build_http_app().app.routes}
    assert {"/mcp", "/sse", "/messages"} <= paths  # Starlette's Mount drops the trailing slash
    assert module.mcp.settings.streamable_http_path == "/mcp"


@pytest.mark.parametrize("transport", ["sse", "streamable"])
async def test_should_expose_the_same_17_tools_on_both_surfaces(load_server, transport):
    module = load_server("log")
    async with serve(module.build_http_app()) as base:
        async with mcp_session(transport, base) as session:
            tools = (await session.list_tools()).tools
    assert {tool.name for tool in tools} == SSE_TOOL_NAMES
    assert len(tools) == 17


@pytest.mark.parametrize("transport", ["sse", "streamable"])
async def test_should_require_the_ids_on_the_write_tools(load_server, transport):
    module = load_server("log")
    async with serve(module.build_http_app()) as base:
        async with mcp_session(transport, base) as session:
            tools = {tool.name: tool.inputSchema for tool in (await session.list_tools()).tools}
    for name in ("update_progress", "promote", "promote_all", "update_context", "log_progress"):
        assert {"workspace_id", "instance_id"} <= set(tools[name]["required"]), name
    assert {"workspace_id", "target_instance"} <= set(tools["fork_instance"]["required"])
    for name in ("log_decision", "save_custom_data", "delete_custom_data"):
        assert "workspace_id" in tools[name]["required"], name
        assert "ctx" not in tools[name]["properties"]  # the request context is not a tool argument
    assert "instance_id" not in tools["save_custom_data"]["properties"]  # custom_data has no instance column


# -- token forwarding ------------------------------------------------------------------------------


@pytest.mark.parametrize("transport", ["sse", "streamable"])
@pytest.mark.parametrize("tool", list(WRITE_CALLS))
async def test_should_forward_the_callers_token_and_ids_to_rest(load_server, transport, tool):
    token = fake_token()
    arguments, method, path = WRITE_CALLS[tool]
    async with fake_rest() as (rest_url, calls):
        module = load_server("enforce", {token: "runner:codex"}, rest_url=rest_url)
        async with serve(module.build_http_app()) as base:
            async with mcp_session(transport, base, {"Authorization": f"Bearer {token}"}) as session:
                result = await session.call_tool(tool, arguments)
                assert not result.isError, result
    (call,) = calls
    assert (call["method"], call["path"]) == (method, path)
    assert call["headers"]["authorization"] == f"Bearer {token}"
    assert "x-dopemux-unverified-caller" not in call["headers"]
    if call["json"] is not None and tool != "update_context":
        assert call["json"]["workspace_id"] == WS or tool == "update_progress"
    if tool in ("log_progress", "promote_all"):
        assert call["json"]["instance_id"] == INSTANCE
    if tool == "update_progress":
        assert call["json"] == {"status": "COMPLETED", "workspace_id": WS, "instance_id": INSTANCE}
    if tool == "update_context":
        assert call["json"] == {"active_context": "x", "instance_id": INSTANCE, "workspace_id": WS}
    if tool == "delete_custom_data":
        assert call["json"] is None


@pytest.mark.parametrize("transport", ["sse", "streamable"])
async def test_should_not_send_credentials_with_reads(load_server, transport):
    token = fake_token()
    async with fake_rest() as (rest_url, calls):
        module = load_server("enforce", {token: "runner:codex"}, rest_url=rest_url)
        async with serve(module.build_http_app()) as base:
            async with mcp_session(transport, base, {"Authorization": f"Bearer {token}"}) as session:
                await session.call_tool("get_context", {"workspace_id": WS})
    (call,) = calls
    assert call["method"] == "GET" and "authorization" not in call["headers"]


# -- modes ------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("path", ["/mcp", "/messages/?session_id=deadbeef"])
async def test_should_answer_401_to_unverified_writes_in_enforce_mode(load_server, path):
    async with fake_rest() as (rest_url, calls):
        module = load_server("enforce", {fake_token(): "runner:codex"}, rest_url=rest_url)
        async with serve(module.build_http_app()) as base:
            async with httpx.AsyncClient(base_url=base, timeout=30) as client:
                call = _rpc("tools/call", {"name": "log_progress", "arguments": WRITE_CALLS["log_progress"][0]})
                for headers in ({}, {"Authorization": "Bearer FAKE-not-a-token"}):
                    response = await client.post(path, json=call, headers={"Accept": ACCEPT, **headers})
                    assert response.status_code == 401, (path, headers)
                    assert response.headers["www-authenticate"] == "Bearer"
                read = await client.post(
                    path, json=_rpc("tools/call", {"name": "get_context", "arguments": {"workspace_id": WS}}),
                    headers={"Accept": ACCEPT},
                )
                assert read.status_code != 401
    assert calls == []


async def test_should_let_a_verified_caller_through_the_http_gate_in_enforce_mode(load_server):
    token = fake_token()
    module = load_server("enforce", {token: "runner:codex"})
    async with serve(module.build_http_app()) as base:
        async with httpx.AsyncClient(base_url=base, timeout=30) as client:
            call = _rpc("tools/call", {"name": "log_progress", "arguments": WRITE_CALLS["log_progress"][0]})
            response = await client.post(
                "/messages/?session_id=deadbeef", json=call,
                headers={"Accept": ACCEPT, "Authorization": f"Bearer {token}"},
            )
    assert response.status_code != 401  # the SSE transport itself says "no such session"


async def test_should_use_the_proxy_principal_only_in_log_mode_without_a_caller_token(load_server):
    proxy = fake_token("proxy")
    arguments = WRITE_CALLS["log_progress"][0]
    async with fake_rest() as (rest_url, calls):
        module = load_server("log", {proxy: "internal:bridge-proxy"}, proxy_token=proxy, rest_url=rest_url)
        async with serve(module.build_http_app()) as base:
            async with mcp_session("streamable", base, {"User-Agent": "agent-x/2"}) as session:
                await session.call_tool("log_progress", arguments)
    (call,) = calls
    assert call["headers"]["authorization"] == f"Bearer {proxy}"
    assert call["headers"]["x-dopemux-unverified-caller"] == "agent-x/2"


async def test_should_send_no_credentials_when_no_proxy_token_exists_yet(load_server):
    async with fake_rest() as (rest_url, calls):
        module = load_server("log", {}, proxy_token=None, rest_url=rest_url)
        async with serve(module.build_http_app()) as base:
            async with mcp_session("sse", base, {"User-Agent": "agent-x/2"}) as session:
                await session.call_tool("log_progress", WRITE_CALLS["log_progress"][0])
    (call,) = calls
    assert "authorization" not in call["headers"]
    assert call["headers"]["x-dopemux-unverified-caller"] == "agent-x/2"


async def test_should_not_replace_a_bad_caller_token_with_the_proxy_token(load_server):
    proxy = fake_token("proxy")
    async with fake_rest() as (rest_url, calls):
        module = load_server("log", {proxy: "internal:bridge-proxy"}, proxy_token=proxy, rest_url=rest_url)
        async with serve(module.build_http_app()) as base:
            async with mcp_session("streamable", base, {"Authorization": "Bearer FAKE-bad"}) as session:
                await session.call_tool("log_progress", WRITE_CALLS["log_progress"][0])
    assert calls[0]["headers"]["authorization"] == "Bearer FAKE-bad"


async def test_should_forward_nothing_special_in_off_mode(load_server):
    async with fake_rest() as (rest_url, calls):
        module = load_server("off", {}, proxy_token=fake_token("proxy"), rest_url=rest_url)
        async with serve(module.build_http_app()) as base:
            async with mcp_session("streamable", base) as session:
                await session.call_tool("log_progress", WRITE_CALLS["log_progress"][0])
    assert "authorization" not in calls[0]["headers"]
    assert "x-dopemux-unverified-caller" not in calls[0]["headers"]


async def test_should_never_log_tokens(load_server, caplog):
    token = fake_token()
    async with fake_rest() as (rest_url, calls):
        module = load_server("enforce", {token: "runner:codex"}, rest_url=rest_url)
        with caplog.at_level(logging.DEBUG):
            async with serve(module.build_http_app()) as base:
                async with mcp_session("streamable", base, {"Authorization": f"Bearer {token}"}) as session:
                    await session.call_tool("log_progress", WRITE_CALLS["log_progress"][0])
                async with httpx.AsyncClient(base_url=base) as client:
                    await client.post(
                        "/mcp",
                        json=_rpc("tools/call", {"name": "log_progress", "arguments": {}}),
                        headers={"Accept": ACCEPT, "Authorization": f"Bearer {token}-wrong"},
                    )
    assert token not in caplog.text
