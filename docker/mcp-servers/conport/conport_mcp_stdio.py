import asyncio
import json
import os
from typing import Optional, List

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


async def _put_json(url: str, payload: dict):
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
        async with session.put(url, json=payload) as resp:
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
async def update_progress(progress_id: str, updates: dict) -> str:
    """Update an existing progress entry. Pass a dict with fields like status (e.g. COMPLETED), percentage, etc."""
    url = f"{CONPORT_URL}/api/progress/{progress_id}"
    data = await _put_json(url, updates)
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
async def log_decision(workspace_id: str, topic: str, decision: str, rationale: str, tags: Optional[List[str]] = None) -> str:
    """Log an architectural or technical decision to the workspace graph."""
    payload = {
        "workspace_id": workspace_id,
        "summary": f"[{topic}] {decision}",
        "decision": decision,
        "rationale": rationale,
        "tags": tags or []
    }
    url = f"{CONPORT_URL}/api/decisions"
    data = await _post_json(url, payload)
    return json.dumps(data, ensure_ascii=False, indent=2)


@mcp.tool()
async def get_recent_activity(workspace_id: str, hours: int = 24) -> str:
    """Get recent activity to rebuild context."""
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
        url = f"{CONPORT_URL}/api/recent-activity/{workspace_id}?hours={hours}"
        data = await _get_json(session, url)
        return json.dumps(data, ensure_ascii=False, indent=2)


@mcp.tool()
async def get_active_work(workspace_id: str) -> str:
    """Get currently active work items to maintain focus."""
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
        url = f"{CONPORT_URL}/api/active-work/{workspace_id}"
        data = await _get_json(session, url)
        return json.dumps(data, ensure_ascii=False, indent=2)


@mcp.tool()
async def workspace_summary(user_id: str) -> str:
    """Get an aggregated summary across all workspaces for a user."""
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
        url = f"{CONPORT_URL}/api/workspace-summary?user_id={user_id}"
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


@mcp.tool()
async def get_context(workspace_id: str) -> str:
    """Get active context for a workspace, including instance-specific data."""
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
        url = f"{CONPORT_URL}/api/context/{workspace_id}"
        data = await _get_json(session, url)
        return json.dumps(data, ensure_ascii=False, indent=2)


@mcp.tool()
async def update_context(workspace_id: str, context_data: dict) -> str:
    """Update active context for a workspace."""
    url = f"{CONPORT_URL}/api/context/{workspace_id}"
    data = await _post_json(url, context_data)
    return json.dumps(data, ensure_ascii=False, indent=2)


@mcp.tool()
async def log_progress(workspace_id: str, description: str, status: str = "PLANNED", priority: str = "medium", linked_decision_id: Optional[str] = None) -> str:
    """Log a new progress item or task in the workspace."""
    payload = {
        "workspace_id": workspace_id,
        "description": description,
        "status": status,
        "priority": priority
    }
    if linked_decision_id:
        payload["linked_decision_id"] = linked_decision_id
        
    url = f"{CONPORT_URL}/api/progress"
    data = await _post_json(url, payload)
    return json.dumps(data, ensure_ascii=False, indent=2)


async def main():
    # Use FastMCP's native async stdio runner
    await mcp.run_stdio_async()


if __name__ == "__main__":
    # Ensure no extra print statements occur before JSON-RPC starts
    asyncio.run(main())

