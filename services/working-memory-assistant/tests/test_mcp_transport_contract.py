"""Actual Streamable HTTP messages against the mounted app, without a socket.

Only the MCP transport lifespan runs. The product lifespan (event bus, retention,
and background workers) is deliberately excluded; all writes use a temp ledger.
"""

import hashlib
import json
from contextlib import asynccontextmanager

import httpx
import pytest
from mcp.types import LATEST_PROTOCOL_VERSION

import dope_memory_main as main
from auth_identity import AuthGate


@asynccontextmanager
async def transport(tmp_path, monkeypatch):
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(tmp_path / "ledger.sqlite"))
    backend = main.DopeMemoryMCPServer("ws", "A")
    monkeypatch.setattr(main, "mcp_server", backend)
    token = "FAKE-TEST-TOKEN-contained-correction"
    auth_dir = tmp_path / "auth"
    auth_dir.mkdir()
    (auth_dir / "memory-token-hashes.json").write_text(
        json.dumps({hashlib.sha256(token.encode()).hexdigest(): "runner:codex"})
    )
    gate = AuthGate(mode="enforce", auth_dir=auth_dir)
    monkeypatch.setattr(main, "AUTH_GATE", gate)
    monkeypatch.setattr(main, "BOUND_WORKSPACE_ID", "ws")
    mcp_app = main.build_mcp_http_app(
        main.build_mcp_server(
            lambda: backend,
            bound_workspace_id="ws",
            read_default_instance_id="A",
            gate=gate,
        )
    )
    mounted = next(
        route for route in main.app.routes
        if getattr(route, "app", None) is main.mcp_http_app
    )
    monkeypatch.setattr(mounted, "app", mcp_app)
    monkeypatch.setattr(main, "mcp_http_app", mcp_app)
    headers = {"Accept": "application/json, text/event-stream"}
    request_id = 0
    try:
        async with main.mcp_http_app.lifespan(main.app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=main.app),
                base_url="http://testserver",
                headers={"Authorization": f"Bearer {token}"},
            ) as client:

                async def rpc(method, params):
                    nonlocal request_id
                    request_id += 1
                    response = await client.post(
                        "/mcp",
                        headers=headers,
                        json={
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "method": method,
                            "params": params,
                        },
                    )
                    assert response.status_code == 200, response.text
                    if response.headers.get("mcp-session-id"):
                        headers["mcp-session-id"] = response.headers["mcp-session-id"]
                    if "application/json" in response.headers["content-type"]:
                        messages = [response.json()]
                    else:
                        messages = [
                            json.loads(line[6:])
                            for line in response.text.splitlines()
                            if line.startswith("data: ")
                        ]
                    return next(
                        message
                        for message in messages
                        if message.get("id") == request_id
                    )

                initialized = await rpc(
                    "initialize",
                    {
                        "protocolVersion": LATEST_PROTOCOL_VERSION,
                        "capabilities": {},
                        "clientInfo": {
                            "name": "contained-contract-test",
                            "version": "1",
                        },
                    },
                )
                headers["MCP-Protocol-Version"] = initialized["result"][
                    "protocolVersion"
                ]
                notified = await client.post(
                    "/mcp",
                    headers=headers,
                    json={
                        "jsonrpc": "2.0",
                        "method": "notifications/initialized",
                    },
                )
                assert notified.status_code == 202
                yield backend, client, rpc
                terminated = await client.delete("/mcp", headers=headers)
                assert terminated.status_code == 200
    finally:
        for store in backend._stores.values():
            store.close()


async def seed(client):
    response = await client.post(
        "/tools/memory_store",
        json={
            "workspace_id": "ws",
            "instance_id": "A",
            "category": "planning",
            "entry_type": "decision",
            "summary": "Original transport evidence",
            "tags": ["old"],
            "details": {"keep": True},
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["entry_id"]


@pytest.mark.asyncio
async def test_rest_and_mcp_share_writer_and_stored_retry_receipt(
    tmp_path, monkeypatch
):
    async with transport(tmp_path, monkeypatch) as (backend, client, rpc):
        source = await seed(client)
        tools = await rpc("tools/list", {})
        correction = next(
            tool
            for tool in tools["result"]["tools"]
            if tool["name"] == "memory_correct"
        )
        assert "corrected_tags" in correction["inputSchema"]["properties"]
        arguments = {
            "workspace_id": "ws",
            "instance_id": "A",
            "entry_id": source,
            "correction_type": "tags",
            "corrected_tags": [],
            "idempotency_key": "http-retry",
        }
        first = (
            await rpc("tools/call", {"name": "memory_correct", "arguments": arguments})
        )["result"]
        assert not first.get("isError"), first
        stored = first["structuredContent"]
        arguments.pop("corrected_tags")
        arguments["correction_type"] = "retraction"
        retried = (
            await rpc("tools/call", {"name": "memory_correct", "arguments": arguments})
        )["result"]
        assert retried["structuredContent"] == stored
        assert stored["correction_type"] == "tags"
        store = backend._get_store("ws")
        row = store.get_entry_by_id("ws", "A", stored["new_entry_id"])
        assert row["summary"] == "Original transport evidence"
        assert json.loads(row["tags_json"]) == []
        assert json.loads(row["details_json"]) == {"keep": True}
        assert row["write_principal"] == "runner:codex"
        assert (
            store.connect()
            .execute("SELECT count(*) FROM work_log_entries")
            .fetchone()[0]
            == 2
        )
        found = await client.post(
            "/tools/memory_search",
            json={
                "workspace_id": "ws",
                "instance_id": "A",
                "query": "transport evidence",
            },
        )
        assert found.status_code == 200, found.text
        assert [entry["id"] for entry in found.json()["items"]] == [
            stored["new_entry_id"]
        ]


@pytest.mark.asyncio
async def test_transport_rejections_do_not_append_corrections(tmp_path, monkeypatch):
    async with transport(tmp_path, monkeypatch) as (backend, client, rpc):
        source = await seed(client)
        for kind in ["tags", "summary", "category", "outcome", "update", "typo"]:
            result = await rpc(
                "tools/call",
                {
                    "name": "memory_correct",
                    "arguments": {
                        "workspace_id": "ws",
                        "instance_id": "A",
                        "entry_id": source,
                        "correction_type": kind,
                    },
                },
            )
            assert result["result"]["isError"] is True, result
        rejected = await client.post(
            "/tools/memory_correct",
            json={
                "workspace_id": "ws",
                "instance_id": "A",
                "entry_id": source,
                "correction_type": "update",
                "corrected_details": {"unsupported": True},
            },
        )
        assert rejected.status_code == 422
        mismatched = await client.post(
            "/tools/memory_correct",
            json={
                "workspace_id": "other",
                "entry_id": source,
                "correction_type": "tags",
                "corrected_tags": [],
            },
        )
        assert mismatched.status_code == 400
        assert "bound" in mismatched.text
        unauthorized = await client.post(
            "/tools/memory_correct",
            headers={"Authorization": "Bearer FAKE-TEST-TOKEN-invalid"},
            json={"entry_id": source, "correction_type": "retraction"},
        )
        assert unauthorized.status_code == 401
        assert (
            backend._get_store("ws")
            .connect()
            .execute("SELECT count(*) FROM work_log_entries")
            .fetchone()[0]
            == 1
        )
