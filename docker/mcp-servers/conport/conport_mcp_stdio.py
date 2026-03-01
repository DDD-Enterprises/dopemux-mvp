import asyncio
import json
import os
from typing import Optional

import aiohttp
from mcp.server.fastmcp import FastMCP
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server

CONPORT_URL = os.getenv("CONPORT_URL", "http://localhost:3004")

mcp = FastMCP("conport-admin")


async def _get_json(session: aiohttp.ClientSession, url: str):
    async with session.get(url) as resp:
        resp.raise_for_status()
        return await resp.json()


async def _post_json(url: str, payload: dict):
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
        async with session.post(url, json=payload) as resp:
            resp.raise_for_status()
            return await resp.json()


@mcp.tool()
async def get_progress(workspace_id: str, status: Optional[str] = None, limit: int = 20) -> str:
    """Get progress entries for a workspace (optionally filter by status)."""
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
        url = f"{CONPORT_URL}/api/progress?workspace_id={workspace_id}&limit={limit}"
        if status:
            url += f"&status={status}"
        data = await _get_json(session, url)
        return json.dumps(data, ensure_ascii=False, indent=2)


@mcp.tool()
async def get_decisions(workspace_id: Optional[str] = None, limit: int = 10) -> str:
    """Get recent decisions (optionally filter by workspace)."""
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
        url = f"{CONPORT_URL}/api/decisions?limit={limit}"
        if workspace_id:
            url += f"&workspace_id={workspace_id}"
        data = await _get_json(session, url)
        return json.dumps(data, ensure_ascii=False, indent=2)


@mcp.tool()
async def fork_instance(workspace_id: str, source_instance: Optional[str] = None, target_instance: Optional[str] = None) -> str:
    """Fork PLANNED/IN_PROGRESS progress from shared/source into target instance."""
    data = await _post_json(f"{CONPORT_URL}/api/instance/fork", {
        "workspace_id": workspace_id,
        "source_instance": source_instance,
        "target_instance": target_instance,
    })
    return json.dumps(data, ensure_ascii=False, indent=2)


@mcp.tool()
async def promote(progress_id: str) -> str:
    """Promote a progress entry to shared (clear instance_id)."""
    data = await _post_json(f"{CONPORT_URL}/api/progress/promote", {"progress_id": progress_id})
    return json.dumps(data, ensure_ascii=False, indent=2)


@mcp.tool()
async def promote_all(workspace_id: str) -> str:
    """Promote all instance-local PLANNED/IN_PROGRESS entries in current instance to shared."""
    data = await _post_json(f"{CONPORT_URL}/api/progress/promote_all", {"workspace_id": workspace_id})
    return json.dumps(data, ensure_ascii=False, indent=2)


async def main():
    # Use FastMCP's native async stdio runner
    await mcp.run_stdio_async()


if __name__ == "__main__":
    # Ensure no extra print statements occur before JSON-RPC starts
    asyncio.run(main())

