#!/usr/bin/env python3
"""
Dope Decision Graph MCP (stdio)

Exposes DDG tools for Claude via stdio MCP:
- related_decisions(decision_id, k)
- related_text(query, workspace_id, k)
- instance_diff(workspace_id, a, b, kind)
- recent_decisions(workspace_id, limit)
- search_decisions(q, workspace_id, limit)
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


BRIDGE_URL = os.getenv("BRIDGE_URL", "http://localhost:3016")

server = Server("ddg-mcp")


async def _get_json(session: aiohttp.ClientSession, url: str):
    async with session.get(url) as resp:
        resp.raise_for_status()
        return await resp.json()


@server.tool()
async def related_decisions(decision_id: str, k: int = 10) -> list[TextContent]:
    """Find decisions related to a given decision id (embedding + rerank)."""
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
        data = await _get_json(session, f"{BRIDGE_URL}/ddg/decisions/related?decision_id={decision_id}&k={k}")
        return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]


@server.tool()
async def related_text(query: str, workspace_id: Optional[str] = None, k: int = 10) -> list[TextContent]:
    """Find decisions related to an arbitrary text query (embedding + rerank)."""
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
        url = f"{BRIDGE_URL}/ddg/decisions/related-text?q={aiohttp.helpers.requote_uri(query)}&k={k}"
        if workspace_id:
            url += f"&workspace_id={workspace_id}"
        data = await _get_json(session, url)
        return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]


@server.tool()
async def instance_diff(workspace_id: str, a: str, b: str, kind: str = "decisions") -> list[TextContent]:
    """Compare items between two instances for a workspace (decisions or progress)."""
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
        data = await _get_json(session, f"{BRIDGE_URL}/ddg/instance-diff?workspace_id={workspace_id}&a={a}&b={b}&kind={kind}")
        return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]


@server.tool()
async def recent_decisions(workspace_id: Optional[str] = None, limit: int = 20) -> list[TextContent]:
    """List recent decisions, optionally filtered by workspace."""
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
        url = f"{BRIDGE_URL}/ddg/decisions/recent?limit={limit}"
        if workspace_id:
            url += f"&workspace_id={workspace_id}"
        data = await _get_json(session, url)
        return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]


@server.tool()
async def search_decisions(q: str, workspace_id: Optional[str] = None, limit: int = 20) -> list[TextContent]:
    """Search decisions by summary text."""
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
        url = f"{BRIDGE_URL}/ddg/decisions/search?q={aiohttp.helpers.requote_uri(q)}&limit={limit}"
        if workspace_id:
            url += f"&workspace_id={workspace_id}"
        data = await _get_json(session, url)
        return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]


# ConPort admin tools (HTTP)

async def _post_json(url: str, payload: dict):
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
        async with session.post(url, json=payload) as resp:
            resp.raise_for_status()
            return await resp.json()


@server.tool()
async def conport_fork_instance(workspace_id: str, source_instance: Optional[str] = None, target_instance: Optional[str] = None, conport_url: str = "http://localhost:3004") -> list[TextContent]:
    """Fork PLANNED/IN_PROGRESS progress from shared/source instance to target instance."""
    url = f"{conport_url}/api/instance/fork"
    data = await _post_json(url, {
        "workspace_id": workspace_id,
        "source_instance": source_instance,
        "target_instance": target_instance,
    })
    return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]


@server.tool()
async def conport_promote(progress_id: str, conport_url: str = "http://localhost:3004") -> list[TextContent]:
    """Promote an instance-local progress entry to shared (clears instance_id)."""
    url = f"{conport_url}/api/progress/promote"
    data = await _post_json(url, {"progress_id": progress_id})
    return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]


@server.tool()
async def conport_promote_all(workspace_id: str, conport_url: str = "http://localhost:3004") -> list[TextContent]:
    """Promote all instance-local PLANNED/IN_PROGRESS entries to shared for the current instance."""
    url = f"{conport_url}/api/progress/promote_all"
    data = await _post_json(url, {"workspace_id": workspace_id})
    return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]


async def main():
    await stdio_server(server, InitializationOptions(
        server_name="ddg-mcp",
        server_version="1.0.0",
    ))


if __name__ == "__main__":
    asyncio.run(main())
