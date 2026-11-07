"""MCP surface: omitted ids, binding, auth (in-process and over HTTP)."""

from __future__ import annotations

import json
import sqlite3

import httpx
import pytest

from .helpers import fake_token, load_dope_memory_auth_identity, write_hash_file

pytest.importorskip("fastmcp")
auth_identity = load_dope_memory_auth_identity()

from fastmcp import Client  # noqa: E402
from fastmcp.client.transports import StreamableHttpTransport  # noqa: E402
from fastmcp.exceptions import ToolError  # noqa: E402
from starlette.applications import Starlette  # noqa: E402
from starlette.routing import Mount  # noqa: E402

import mcp_http  # noqa: E402

BOUND = "ws-bound"
IDS = {"workspace_id": BOUND, "instance_id": "inst-1"}

WRITE_ARGS = {
    "memory_store": {"category": "implementation", "entry_type": "decision", "summary": "s"},
    "memory_correct": {"entry_id": "missing", "correction_type": "summary"},
    "memory_link_resolution": {"issue_entry_id": "a", "resolution_entry_id": "b"},
    "memory_generate_reflection": {},
    "memory_mark_issue": {"issue_entry_id": "a", "description": "d"},
}


@pytest.fixture()
def backend(ledger_path):
    from dope_memory_main import DopeMemoryMCPServer

    return DopeMemoryMCPServer(workspace_id=BOUND, instance_id="A")


def _server(backend, mode="log", tokens=None, tmp_path=None, bound=BOUND):
    auth_dir = tmp_path / "auth" if tmp_path else None
    if tokens is not None:
        write_hash_file(auth_dir, tokens)
    gate = auth_identity.AuthGate(mode=mode, auth_dir=auth_dir)
    server = mcp_http.build_mcp_server(
        lambda: backend,
        bound_workspace_id=bound,
        read_default_instance_id="A",
        gate=gate,
    )
    return server, gate


def _principals(ledger_path):
    conn = sqlite3.connect(str(ledger_path))
    try:
        return [r[0] for r in conn.execute("SELECT write_principal FROM work_log_entries")]
    finally:
        conn.close()


# --- in-process (no HTTP request) -------------------------------------------


@pytest.mark.parametrize("missing", ["workspace_id", "instance_id"])
async def test_should_fill_a_tool_call_missing_an_id_from_the_binding(backend, ledger_path, missing):
    # Amendment 04 (W12): an omitted id is filled from the server's binding.
    server, _ = _server(backend)
    args = {**WRITE_ARGS["memory_store"], **{k: v for k, v in IDS.items() if k != missing}}
    async with Client(server) as client:
        stored = await client.call_tool("memory_store", args)
    assert stored.data["created"] is True
    assert _principals(ledger_path) == ["unverified"]


@pytest.mark.parametrize("tool", sorted(WRITE_ARGS))
async def test_should_reject_a_binding_mismatch(backend, tool):
    server, _ = _server(backend)
    async with Client(server) as client:
        with pytest.raises(ToolError, match="bound"):
            await client.call_tool(
                tool, {**WRITE_ARGS[tool], "workspace_id": "other", "instance_id": "i"}
            )


async def test_should_reject_writes_when_server_unbound(backend):
    server, _ = _server(backend, bound=None)
    async with Client(server) as client:
        with pytest.raises(ToolError, match="DOPE_MEMORY_WORKSPACE_ID"):
            await client.call_tool("memory_store", {**WRITE_ARGS["memory_store"], **IDS})


async def test_should_advertise_ids_as_optional_on_every_tool(backend):
    server, _ = _server(backend)
    async with Client(server) as client:
        tools = {t.name: t for t in await client.list_tools()}
    for name in WRITE_ARGS:
        required = set(tools[name].inputSchema.get("required", []))
        assert not ({"workspace_id", "instance_id"} & required), name
    for name in ("memory_search", "memory_recap", "memory_trajectory", "memory_reflections"):
        required = set(tools[name].inputSchema.get("required", []))
        assert not ({"workspace_id", "instance_id"} & required), name


async def test_should_keep_reads_working_without_ids(backend):
    server, _ = _server(backend, mode="enforce")
    async with Client(server) as client:
        assert (await client.call_tool("memory_search", {"query": "x"})).data["items"] == []
        await client.call_tool("memory_recap", {})
        await client.call_tool("memory_trajectory", {})


async def test_should_round_trip_write_with_unverified_principal_in_process(backend, ledger_path):
    server, gate = _server(backend, mode="log")
    async with Client(server) as client:
        stored = await client.call_tool("memory_store", {**WRITE_ARGS["memory_store"], **IDS})
        assert stored.data["created"] is True
        found = await client.call_tool("memory_search", {"query": "s", **IDS})
        assert [i["summary"] for i in found.data["items"]] == ["s"]
    assert _principals(ledger_path) == ["unverified"]
    assert gate.health_fields()["auth_unverified_calls"] == {"in-process": 1}


async def test_should_refuse_unauthenticated_in_process_write_in_enforce(backend, ledger_path):
    server, _ = _server(backend, mode="enforce")
    async with Client(server) as client:
        with pytest.raises(ToolError, match="401|unauthori"):
            await client.call_tool("memory_store", {**WRITE_ARGS["memory_store"], **IDS})
    assert not ledger_path.exists() or _principals(ledger_path) == []


async def test_should_unwrap_dict_shaped_backend_results():
    class DictBackend:
        def memory_trajectory(self, workspace_id, instance_id):
            return {"success": True, "current_stream": "idle", "boost_factor": 1.0}

        def memory_recap(self, **kwargs):
            return {"success": False, "error": "dict backend failure"}

    server = mcp_http.build_mcp_server(
        lambda: DictBackend(),
        bound_workspace_id="x",
        read_default_instance_id="A",
        gate=auth_identity.AuthGate(mode="log", auth_dir=None),
    )
    async with Client(server) as client:
        ok = await client.call_tool("memory_trajectory", {})
        assert ok.data["current_stream"] == "idle"
        with pytest.raises(ToolError, match="dict backend failure"):
            await client.call_tool("memory_recap", {})


# --- over HTTP ---------------------------------------------------------------


def _http_app(server, gate):
    mcp_app = mcp_http.build_mcp_http_app(server)
    app = Starlette(routes=[Mount("", mcp_app)], lifespan=mcp_app.lifespan)
    app.add_middleware(auth_identity.WriteAuthMiddleware, get_gate=lambda: gate)
    return app


def _client(app, token=None, user_agent="w01-test"):
    headers = {"User-Agent": user_agent}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    def factory(headers=None, timeout=None, auth=None, **kwargs):
        return httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            headers=headers,
            timeout=timeout,
            auth=auth,
            follow_redirects=True,
        )

    return Client(
        StreamableHttpTransport("http://test/mcp", headers=headers, httpx_client_factory=factory)
    )


@pytest.mark.parametrize(
    "mode,kind,principal",
    [
        ("log", "valid", "runner:codex"),
        ("log", "invalid", "unverified"),
        ("log", "missing", "unverified"),
        ("enforce", "valid", "runner:codex"),
    ],
)
async def test_should_store_verified_principal_over_http(
    backend, ledger_path, tmp_path, mode, kind, principal
):
    token = fake_token()
    server, gate = _server(backend, mode, {token: "runner:codex"}, tmp_path)
    app = _http_app(server, gate)
    sent = {"valid": token, "invalid": fake_token("bad"), "missing": None}[kind]
    async with app.router.lifespan_context(app):
        async with _client(app, sent) as client:
            stored = await client.call_tool("memory_store", {**WRITE_ARGS["memory_store"], **IDS})
            assert stored.data["created"] is True
    assert _principals(ledger_path) == [principal]


async def test_should_answer_401_over_http_for_unverified_write_in_enforce(
    backend, ledger_path, tmp_path
):
    token = fake_token()
    server, gate = _server(backend, "enforce", {token: "runner:codex"}, tmp_path)
    app = _http_app(server, gate)
    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": "memory_store", "arguments": {**WRITE_ARGS["memory_store"], **IDS}},
    }
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as raw:
            headers = {"Accept": "application/json, text/event-stream", "User-Agent": "raw/1"}
            resp = await raw.post("/mcp", json=body, headers=headers)
            assert resp.status_code == 401
            assert resp.headers["www-authenticate"].lower().startswith("bearer")
            bad = await raw.post(
                "/mcp", json=body, headers={**headers, "Authorization": f"Bearer {fake_token('bad')}"}
            )
            assert bad.status_code == 401
            # A batch containing one write is rejected as a whole.
            batch = await raw.post("/mcp", json=[{**body, "method": "tools/list"}, body], headers=headers)
            assert batch.status_code == 401
            # Non-write JSON-RPC traffic is not gated by the middleware.
            listing = await raw.post(
                "/mcp", json={"jsonrpc": "2.0", "id": 2, "method": "tools/list"}, headers=headers
            )
            assert listing.status_code != 401
    assert gate.health_fields()["auth_unverified_calls"]["raw/1"] == 3
    assert not ledger_path.exists() or _principals(ledger_path) == []


async def test_should_allow_reads_over_http_without_token_in_enforce(backend, tmp_path):
    server, gate = _server(backend, "enforce", {fake_token(): "runner:codex"}, tmp_path)
    app = _http_app(server, gate)
    async with app.router.lifespan_context(app):
        async with _client(app) as client:
            found = await client.call_tool("memory_search", {"query": "none"})
            assert found.data["items"] == []


# --- middleware mechanics ------------------------------------------------------


async def _run_asgi(app, method, path, body: bytes, headers=None):
    sent: list[dict] = []
    received = [{"type": "http.request", "body": body, "more_body": False}]

    async def receive():
        if received:
            return received.pop(0)
        return {"type": "http.disconnect"}

    async def send(message):
        sent.append(message)

    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "headers": [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()],
        "client": ("10.1.2.3", 5555),
    }
    await app(scope, receive, send)
    status = next(m["status"] for m in sent if m["type"] == "http.response.start")
    return status, sent


def _echo_app():
    seen = {}

    async def app(scope, receive, send):
        chunks = []
        while True:
            message = await receive()
            chunks.append(message.get("body", b""))
            if not message.get("more_body"):
                break
        seen["body"] = b"".join(chunks)
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})

    return app, seen


async def test_should_replay_request_body_to_inner_app_when_allowed(tmp_path):
    inner, seen = _echo_app()
    gate = auth_identity.AuthGate(mode="log", auth_dir=None)
    app = auth_identity.WriteAuthMiddleware(inner, get_gate=lambda: gate)
    body = json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "memory_store"}}
    ).encode()
    status, _ = await _run_asgi(app, "POST", "/mcp", body)
    assert status == 200
    assert seen["body"] == body


@pytest.mark.parametrize("body", [b"not json", b"123", b'"str"', b"[]", b"{}"])
async def test_should_pass_through_unparseable_or_non_call_bodies(body):
    inner, seen = _echo_app()
    gate = auth_identity.AuthGate(mode="enforce", auth_dir=None)
    app = auth_identity.WriteAuthMiddleware(inner, get_gate=lambda: gate)
    status, _ = await _run_asgi(app, "POST", "/mcp", body)
    assert status == 200 and seen["body"] == body


async def test_should_not_gate_other_paths_or_methods():
    inner, _ = _echo_app()
    gate = auth_identity.AuthGate(mode="enforce", auth_dir=None)
    app = auth_identity.WriteAuthMiddleware(inner, get_gate=lambda: gate)
    body = json.dumps({"method": "tools/call", "params": {"name": "memory_store"}}).encode()
    assert (await _run_asgi(app, "GET", "/mcp", b""))[0] == 200
    assert (await _run_asgi(app, "POST", "/health", body))[0] == 200


async def test_should_reject_oversized_mcp_bodies_with_413():
    inner, _ = _echo_app()
    gate = auth_identity.AuthGate(mode="enforce", auth_dir=None)
    app = auth_identity.WriteAuthMiddleware(inner, get_gate=lambda: gate, max_body_bytes=64)
    status, _ = await _run_asgi(app, "POST", "/mcp", b"x" * 65)
    assert status == 413
