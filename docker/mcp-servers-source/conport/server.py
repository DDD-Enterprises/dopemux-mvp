import asyncio
import json
import os
from typing import Any, Callable, Optional, List
from urllib.parse import quote, quote_plus, urlencode

import aiohttp
from mcp.server.fastmcp import Context, FastMCP

from auth_identity import (
    PROXY_WRITE_TOOLS,
    AuthGate,
    WriteAuthMiddleware,
    rest_write_headers_for_call,
)

CONPORT_URL = os.getenv("CONPORT_URL", "http://localhost:3004")
MCP_PORT = int(os.getenv("MCP_SERVER_PORT", 3005))

mcp = FastMCP("conport")

# Wave 2A R2: write identity. Mode from CONPORT_AUTH_MODE, hashes from CONPORT_AUTH_DIR.
# The SSE and streamable surfaces forward the caller's bearer token to the REST
# port, which verifies it again and stores the principal.
AUTH_GATE = AuthGate.from_env()

# Token for ``internal:bridge-proxy``, used only in ``log`` mode for a caller that
# sent none. The shared keychain/hash helper (W03) is not available inside the
# image yet, so there is no production source: the default is "no token", and
# the REST side then records the caller as ``unverified``. Tests inject one.
PROXY_TOKEN_PROVIDER: Callable[[], Optional[str]] = lambda: None


def _write_headers(ctx: Optional[Context]) -> dict:
    """Headers for a REST write: the caller's token, or the proxy's in log mode."""
    return rest_write_headers_for_call(AUTH_GATE, ctx, fallback_token=lambda: PROXY_TOKEN_PROVIDER())


async def _get_json(session: aiohttp.ClientSession, url: str):
    async with session.get(url) as resp:
        resp.raise_for_status()
        return await resp.json()


async def _post_json(url: str, payload: dict, headers: Optional[dict] = None):
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
        async with session.post(url, json=payload, headers=headers) as resp:
            resp.raise_for_status()
            return await resp.json()


async def _put_json(url: str, payload: dict, headers: Optional[dict] = None):
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
        async with session.put(url, json=payload, headers=headers) as resp:
            resp.raise_for_status()
            return await resp.json()


async def _delete_json(url: str, headers: Optional[dict] = None):
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
        async with session.delete(url, headers=headers) as resp:
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
async def update_progress(
    progress_id: str,
    workspace_id: str,
    instance_id: str,
    updates: dict,
    ctx: Context = None,
) -> str:
    """Update an existing progress entry. Pass a dict with fields like status (e.g. COMPLETED), percentage, etc.

    workspace_id must be the entry's workspace; instance_id is the writing instance ("shared" for the shared scope).
    """
    url = f"{CONPORT_URL}/api/progress/{progress_id}"
    payload = {**updates, "workspace_id": workspace_id, "instance_id": instance_id}
    data = await _put_json(url, payload, _write_headers(ctx))
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
async def log_decision(
    workspace_id: str,
    topic: str,
    decision: str,
    rationale: str,
    tags: Optional[List[str]] = None,
    instance_id: Optional[str] = None,
    ctx: Context = None,
) -> str:
    """Log an architectural or technical decision to the workspace graph."""
    payload = {
        "workspace_id": workspace_id,
        "summary": f"[{topic}] {decision}",
        "topic": topic,
        "decision": decision,
        "rationale": rationale,
        "tags": tags or [],
    }
    if instance_id:
        payload["instance_id"] = instance_id
    url = f"{CONPORT_URL}/api/decisions"
    data = await _post_json(url, payload, _write_headers(ctx))
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
async def fork_instance(
    workspace_id: str,
    target_instance: str,
    source_instance: Optional[str] = None,
    ctx: Context = None,
) -> str:
    """Fork PLANNED/IN_PROGRESS progress from shared/source into target instance."""
    data = await _post_json(f"{CONPORT_URL}/api/instance/fork", {
        "workspace_id": workspace_id,
        "source_instance": source_instance,
        "target_instance": target_instance,
    }, _write_headers(ctx))
    return json.dumps(data, ensure_ascii=False, indent=2)


@mcp.tool()
async def promote(progress_id: str, workspace_id: str, instance_id: str, ctx: Context = None) -> str:
    """Promote a progress entry to shared (clear instance_id)."""
    data = await _post_json(
        f"{CONPORT_URL}/api/progress/promote",
        {"progress_id": progress_id, "workspace_id": workspace_id, "instance_id": instance_id},
        _write_headers(ctx),
    )
    return json.dumps(data, ensure_ascii=False, indent=2)


@mcp.tool()
async def promote_all(workspace_id: str, instance_id: str, ctx: Context = None) -> str:
    """Promote all instance-local PLANNED/IN_PROGRESS entries of the given instance to shared."""
    data = await _post_json(
        f"{CONPORT_URL}/api/progress/promote_all",
        {"workspace_id": workspace_id, "instance_id": instance_id},
        _write_headers(ctx),
    )
    return json.dumps(data, ensure_ascii=False, indent=2)


@mcp.tool()
async def get_context(workspace_id: str) -> str:
    """Get active context for a workspace, including instance-specific data."""
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
        url = f"{CONPORT_URL}/api/context/{workspace_id}"
        data = await _get_json(session, url)
        return json.dumps(data, ensure_ascii=False, indent=2)


@mcp.tool()
async def update_context(
    workspace_id: str,
    instance_id: str,
    context_data: dict,
    ctx: Context = None,
) -> str:
    """Update active context for a workspace (instance_id is the writing instance; "shared" for the shared scope)."""
    url = f"{CONPORT_URL}/api/context/{quote(workspace_id, safe='')}"
    payload = {**context_data, "workspace_id": workspace_id, "instance_id": instance_id}
    data = await _post_json(url, payload, _write_headers(ctx))
    return json.dumps(data, ensure_ascii=False, indent=2)


@mcp.tool()
async def log_progress(
    workspace_id: str,
    instance_id: str,
    description: str,
    status: str = "IN_PROGRESS",
    priority: str = "medium",
    linked_decision_id: Optional[str] = None,
    ctx: Context = None,
) -> str:
    """Log a new progress item or task in the workspace (instance_id is the writing instance; "shared" for the shared scope)."""
    payload = {
        "workspace_id": workspace_id,
        "instance_id": instance_id,
        "description": description,
        "status": status,
        "priority": priority
    }
    if linked_decision_id:
        payload["linked_decision_id"] = linked_decision_id

    url = f"{CONPORT_URL}/api/progress"
    data = await _post_json(url, payload, _write_headers(ctx))
    return json.dumps(data, ensure_ascii=False, indent=2)


@mcp.tool()
async def get_custom_data(workspace_id: str, category: Optional[str] = None, key: Optional[str] = None) -> str:
    """Retrieve custom data for a workspace, optionally filtered by category and key."""
    query = {"workspace_id": workspace_id}
    if category is not None:
        query["category"] = category
    if key is not None:
        query["key"] = key
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
        data = await _get_json(session, f"{CONPORT_URL}/api/custom_data?{urlencode(query)}")
        return json.dumps(data, ensure_ascii=False, indent=2)


@mcp.tool()
async def save_custom_data(workspace_id: str, category: str, key: str, value: Any, ctx: Context = None) -> str:
    """Save or update custom data for a workspace."""
    payload = {
        "workspace_id": workspace_id,
        "category": category,
        "key": key,
        "value": value,
    }
    data = await _post_json(f"{CONPORT_URL}/api/custom_data", payload, _write_headers(ctx))
    return json.dumps(data, ensure_ascii=False, indent=2)


@mcp.tool()
async def delete_custom_data(workspace_id: str, category: str, key: str, ctx: Context = None) -> str:
    """Delete custom data for a workspace."""
    query = urlencode({"workspace_id": workspace_id, "category": category, "key": key})
    data = await _delete_json(f"{CONPORT_URL}/api/custom_data?{query}", _write_headers(ctx))
    return json.dumps(data, ensure_ascii=False, indent=2)


@mcp.tool()
async def search_content(workspace_id: str, query: str) -> str:
    """Search decisions and progress entries in a workspace."""
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
        url = f"{CONPORT_URL}/api/search/{quote(workspace_id, safe='')}?q={quote_plus(query)}"
        data = await _get_json(session, url)
        return json.dumps(data, ensure_ascii=False, indent=2)


def build_http_app():
    """One ASGI app for the MCP listener: SSE (``/sse``, ``/messages/``) and the
    streamable-HTTP surface (``/mcp``), both behind the write-auth gate.

    The streamable app's lifespan runs the session manager, so it becomes the
    lifespan of the combined app.
    """
    from starlette.applications import Starlette

    sse = mcp.sse_app()
    streamable = mcp.streamable_http_app()
    combined = Starlette(
        routes=[*streamable.routes, *sse.routes],
        lifespan=streamable.router.lifespan_context,
    )
    return WriteAuthMiddleware(
        combined,
        lambda: AUTH_GATE,
        write_paths={mcp.settings.streamable_http_path, mcp.settings.message_path},
        write_tools=PROXY_WRITE_TOOLS,
    )


if __name__ == "__main__":
    import sys
    import uvicorn
    transport = "stdio"
    if len(sys.argv) > 1:
        transport = sys.argv[1]

    if transport == "sse":
        uvicorn.run(build_http_app(), host="0.0.0.0", port=MCP_PORT)
    else:
        mcp.run(transport="stdio")
