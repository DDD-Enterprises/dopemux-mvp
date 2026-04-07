from __future__ import annotations

import pytest
from aiohttp import web
from fastapi import HTTPException

from dopecon_bridge.clients import ConPortClient


async def _start_test_server(handler, port: int):
    app = web.Application()
    app.router.add_get("/api/custom_data", handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", port)
    await site.start()
    return runner


@pytest.mark.asyncio
async def test_get_custom_data_normalizes_upstream_404_to_empty(unused_tcp_port):
    async def handler(_request):
        raise web.HTTPNotFound(text="category missing")

    runner = await _start_test_server(handler, unused_tcp_port)

    client = ConPortClient()
    client.base_url = f"http://127.0.0.1:{unused_tcp_port}"

    try:
        payload = await client.get_custom_data(
            {"workspace_id": "/workspace", "category": "workflow_ideas", "limit": 5}
        )
    finally:
        await client.close()
        await runner.cleanup()

    assert payload == {"count": 0, "items": []}


@pytest.mark.asyncio
async def test_get_custom_data_preserves_non_404_failures(unused_tcp_port):
    async def handler(_request):
        raise web.HTTPServiceUnavailable(text="conport unavailable")

    runner = await _start_test_server(handler, unused_tcp_port)

    client = ConPortClient()
    client.base_url = f"http://127.0.0.1:{unused_tcp_port}"

    try:
        with pytest.raises(HTTPException) as exc_info:
            await client.get_custom_data(
                {"workspace_id": "/workspace", "category": "workflow_ideas", "limit": 5}
            )
    finally:
        await client.close()
        await runner.cleanup()

    assert exc_info.value.status_code == 502
    assert "conport unavailable" in exc_info.value.detail
