import asyncio
import json
import os
from typing import Annotated, Any, Callable, Optional, List
from urllib.parse import quote, quote_plus, urlencode

import aiohttp
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from pydantic import Field

from auth_identity import AuthGate, rest_write_headers_for_call
from instance_detector import get_bound_workspace_id

CONPORT_URL = os.getenv("CONPORT_URL", "http://localhost:3004")

mcp = FastMCP("conport-admin")

# Wave 2A R2: write identity. A stdio process has no HTTP headers, so the caller's
# bearer token is read from CONPORT_STDIO_TOKEN (set by whatever spawns this
# process) and forwarded to the REST port, which verifies it and stores the
# principal. Mode from CONPORT_AUTH_MODE, hashes from CONPORT_AUTH_DIR.
AUTH_GATE = AuthGate.from_env()

# Token for ``internal:bridge-proxy``, used only in ``log`` mode when the caller
# has no token. The shared keychain/hash helper (W03) is not available inside the
# image yet, so there is no production source: the default is "no token", and
# the REST side then records the caller as ``unverified``. Tests inject one.
PROXY_TOKEN_PROVIDER: Callable[[], Optional[str]] = lambda: None


# Write tools take the ids as optional (Amendment 04): the REST port fills an
# omitted one from its own binding and rejects a workspace that is not its own.
WorkspaceIdParam = Annotated[
    Optional[str],
    Field(
        description="Workspace to write to. Optional: the server fills it from its own "
        "binding; a workspace that differs from the binding is rejected."
    ),
]
InstanceIdParam = Annotated[
    Optional[str],
    Field(
        description="Instance to write as. Optional: the server fills it from its own "
        "binding (its instance, else \"shared\")."
    ),
]


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
    updates: dict,
    workspace_id: WorkspaceIdParam = None,
    instance_id: InstanceIdParam = None,
    ctx: Context = None,
) -> str:
    """Update an existing progress entry. Pass a dict with fields like status (e.g. COMPLETED), percentage, etc.

    workspace_id and instance_id are optional: the server fills them from its binding. A workspace_id must be
    the entry's workspace; instance_id is the writing instance ("shared" for the shared scope).
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
    topic: str,
    decision: str,
    rationale: str,
    workspace_id: WorkspaceIdParam = None,
    tags: Optional[List[str]] = None,
    instance_id: InstanceIdParam = None,
    ctx: Context = None,
) -> str:
    """Log an architectural or technical decision to the workspace graph.

    workspace_id and instance_id are optional: the server fills them from its binding."""
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
    target_instance: str,
    workspace_id: WorkspaceIdParam = None,
    source_instance: Optional[str] = None,
    ctx: Context = None,
) -> str:
    """Fork PLANNED/IN_PROGRESS progress from shared/source into target instance.

    workspace_id is optional (filled from the server's binding); target_instance is required."""
    data = await _post_json(f"{CONPORT_URL}/api/instance/fork", {
        "workspace_id": workspace_id,
        "source_instance": source_instance,
        "target_instance": target_instance,
    }, _write_headers(ctx))
    return json.dumps(data, ensure_ascii=False, indent=2)


@mcp.tool()
async def promote(
    progress_id: str,
    workspace_id: WorkspaceIdParam = None,
    instance_id: InstanceIdParam = None,
    ctx: Context = None,
) -> str:
    """Promote a progress entry to shared (clear instance_id).

    workspace_id and instance_id are optional: the server fills them from its binding."""
    data = await _post_json(
        f"{CONPORT_URL}/api/progress/promote",
        {"progress_id": progress_id, "workspace_id": workspace_id, "instance_id": instance_id},
        _write_headers(ctx),
    )
    return json.dumps(data, ensure_ascii=False, indent=2)


@mcp.tool()
async def promote_all(
    workspace_id: WorkspaceIdParam = None,
    instance_id: InstanceIdParam = None,
    ctx: Context = None,
) -> str:
    """Promote all instance-local PLANNED/IN_PROGRESS entries of the given instance to shared.

    workspace_id and instance_id are optional: the server fills them from its binding."""
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
    context_data: dict,
    workspace_id: WorkspaceIdParam = None,
    instance_id: InstanceIdParam = None,
    ctx: Context = None,
) -> str:
    """Update active context for a workspace (instance_id is the writing instance; "shared" for the shared scope).

    workspace_id and instance_id are optional: the server fills them from its binding."""
    # The REST route carries the workspace in its path, so an omitted one is the binding.
    path_workspace = workspace_id if workspace_id and workspace_id.strip() else get_bound_workspace_id()
    if not path_workspace:
        raise ValueError(
            "workspace_id was omitted and this ConPort server has no workspace binding "
            "(DOPEMUX_WORKSPACE_ID is unset); writes are rejected"
        )
    url = f"{CONPORT_URL}/api/context/{quote(path_workspace, safe='')}"
    payload = {**context_data, "workspace_id": workspace_id, "instance_id": instance_id}
    data = await _post_json(url, payload, _write_headers(ctx))
    return json.dumps(data, ensure_ascii=False, indent=2)


@mcp.tool()
async def log_progress(
    description: str,
    workspace_id: WorkspaceIdParam = None,
    instance_id: InstanceIdParam = None,
    status: str = "IN_PROGRESS",
    priority: str = "medium",
    linked_decision_id: Optional[str] = None,
    ctx: Context = None,
) -> str:
    """Log a new progress item or task in the workspace (instance_id is the writing instance; "shared" for the shared scope).

    workspace_id and instance_id are optional: the server fills them from its binding."""
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
async def save_custom_data(
    category: str,
    key: str,
    value: Any,
    workspace_id: WorkspaceIdParam = None,
    ctx: Context = None,
) -> str:
    """Save or update custom data for a workspace.

    workspace_id is optional: the server fills it from its binding."""
    payload = {
        "workspace_id": workspace_id,
        "category": category,
        "key": key,
        "value": value,
    }
    data = await _post_json(f"{CONPORT_URL}/api/custom_data", payload, _write_headers(ctx))
    return json.dumps(data, ensure_ascii=False, indent=2)


@mcp.tool()
async def delete_custom_data(
    category: str,
    key: str,
    workspace_id: WorkspaceIdParam = None,
    ctx: Context = None,
) -> str:
    """Delete custom data for a workspace.

    workspace_id is optional: the server fills it from its binding."""
    params = {"category": category, "key": key}
    if workspace_id:
        params["workspace_id"] = workspace_id
    query = urlencode(params)
    data = await _delete_json(f"{CONPORT_URL}/api/custom_data?{query}", _write_headers(ctx))
    return json.dumps(data, ensure_ascii=False, indent=2)


@mcp.tool()
async def search_content(workspace_id: str, query: str) -> str:
    """Search decisions and progress entries in a workspace."""
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
        url = f"{CONPORT_URL}/api/search/{quote(workspace_id, safe='')}?q={quote_plus(query)}"
        data = await _get_json(session, url)
        return json.dumps(data, ensure_ascii=False, indent=2)


async def main():
    # Use FastMCP's native async stdio runner
    await mcp.run_stdio_async()


if __name__ == "__main__":
    # Ensure no extra print statements occur before JSON-RPC starts
    asyncio.run(main())
