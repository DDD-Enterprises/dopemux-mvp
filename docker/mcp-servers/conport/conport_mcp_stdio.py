#!/usr/bin/env python3
"""
ConPort Admin MCP (stdio)

Tools for managing ConPort instances directly inside the ConPort container:
- fork_instance(workspace_id, source_instance, target_instance)
- promote(progress_id)
- promote_all(workspace_id)
- get_progress(workspace_id, status, limit)
- get_decisions(workspace_id, limit)
"""

import asyncio
import json
import os
from typing import Optional

import aiohttp
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import TextContent

CONPORT_URL = os.getenv("CONPORT_URL", "http://localhost:3004")

server = Server("conport-admin")


async def _get_json(session: aiohttp.ClientSession, url: str):
    async with session.get(url) as resp:
        resp.raise_for_status()
        return await resp.json()


async def _post_json(url: str, payload: dict):
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
        async with session.post(url, json=payload) as resp:
            resp.raise_for_status()
            return await resp.json()


@server.tool()
async def get_progress(workspace_id: str, status: Optional[str] = None, limit: int = 20) -> list[TextContent]:
    """Get progress entries for a workspace (optionally filter by status)."""
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
        url = f"{CONPORT_URL}/api/progress?workspace_id={workspace_id}&limit={limit}"
        if status:
            url += f"&status={status}"
        data = await _get_json(session, url)
        return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]


@server.tool()
async def get_decisions(workspace_id: Optional[str] = None, limit: int = 10) -> list[TextContent]:
    """Get recent decisions (optionally filter by workspace)."""
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
        url = f"{CONPORT_URL}/api/decisions?limit={limit}"
        if workspace_id:
            url += f"&workspace_id={workspace_id}"
        data = await _get_json(session, url)
        return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]


@server.tool()
async def fork_instance(workspace_id: str, source_instance: Optional[str] = None, target_instance: Optional[str] = None) -> list[TextContent]:
    """Fork PLANNED/IN_PROGRESS progress from shared/source into target instance."""
    data = await _post_json(f"{CONPORT_URL}/api/instance/fork", {
        "workspace_id": workspace_id,
        "source_instance": source_instance,
        "target_instance": target_instance,
    })
    return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]


@server.tool()
async def promote(progress_id: str) -> list[TextContent]:
    """Promote a progress entry to shared (clear instance_id)."""
    data = await _post_json(f"{CONPORT_URL}/api/progress/promote", {"progress_id": progress_id})
    return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]


@server.tool()
async def promote_all(workspace_id: str) -> list[TextContent]:
    """Promote all instance-local PLANNED/IN_PROGRESS entries in current instance to shared."""
    data = await _post_json(f"{CONPORT_URL}/api/progress/promote_all", {"workspace_id": workspace_id})
    return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]


async def main():
    await stdio_server(server, InitializationOptions(
        server_name="conport-admin",
        server_version="1.0.0",
    ))


if __name__ == "__main__":
    asyncio.run(main())

