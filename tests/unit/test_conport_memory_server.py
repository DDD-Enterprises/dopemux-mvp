import ssl
from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from conport.memory_server import AiohttpMcpSseTransport, MemoryConfig
from mcp import types
from mcp.shared.message import SessionMessage


class _FakeMcpServer:
    def create_initialization_options(self):
        return None

    async def run(self, read_stream, write_stream, initialization_options):
        async with read_stream, write_stream:
            async for incoming in read_stream:
                request_id = incoming.message.root.id
                response = types.JSONRPCResponse(
                    jsonrpc="2.0",
                    id=request_id,
                    result={"ok": True},
                )
                await write_stream.send(
                    SessionMessage(message=types.JSONRPCMessage(response))
                )
                break


@pytest.mark.asyncio
async def test_aiohttp_mcp_sse_transport_round_trips_jsonrpc_message():
    transport = AiohttpMcpSseTransport(_FakeMcpServer(), heartbeat_seconds=60)
    app = web.Application()
    app.router.add_get("/sse", transport.handle_sse)
    app.router.add_post("/messages", transport.handle_post_message)

    server = TestServer(app)
    await server.start_server()
    client = TestClient(server)
    await client.start_server()

    try:
        response = await client.get("/sse")
        assert response.status == 200

        event_line = await response.content.readline()
        data_line = await response.content.readline()
        await response.content.readline()

        assert event_line.decode().strip() == "event: endpoint"
        endpoint_data = data_line.decode().strip().removeprefix("data: ")
        assert endpoint_data.startswith("/messages?session_id=")

        post_response = await client.post(
            endpoint_data,
            json={"jsonrpc": "2.0", "id": 7, "method": "ping"},
            headers={"Content-Type": "application/json"},
        )
        assert post_response.status == 202

        message_event = await response.content.readline()
        message_data = await response.content.readline()
        await response.content.readline()

        assert message_event.decode().strip() == "event: message"
        payload = types.JSONRPCMessage.model_validate_json(
            message_data.decode().strip().removeprefix("data: ")
        )
        assert payload.root.id == 7
        assert payload.root.result == {"ok": True}

        response.close()
    finally:
        await client.close()
        await server.close()


def test_memory_config_builds_tls_connection_kwargs(monkeypatch, tmp_path: Path):
    cert_path = tmp_path / "ca.pem"
    cert_path.write_text("placeholder")

    monkeypatch.setenv("POSTGRES_SSL_MODE", "require")
    monkeypatch.setenv("MILVUS_SECURE", "true")
    monkeypatch.setenv("MILVUS_TLS_SERVER_NAME", "milvus.internal")
    monkeypatch.setenv("MILVUS_TLS_CA_PEM_PATH", str(cert_path))

    config = MemoryConfig()

    postgres_kwargs = config.build_postgres_connect_kwargs()
    assert "ssl" in postgres_kwargs
    assert isinstance(postgres_kwargs["ssl"], ssl.SSLContext)
    assert postgres_kwargs["ssl"].verify_mode == ssl.CERT_NONE
    assert postgres_kwargs["ssl"].check_hostname is False

    milvus_kwargs = config.build_milvus_client_kwargs()
    assert milvus_kwargs["uri"].startswith("https://")
    assert milvus_kwargs["secure"] is True
    assert milvus_kwargs["server_name"] == "milvus.internal"
    assert milvus_kwargs["ca_pem_path"] == str(cert_path)
