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
import logging
import os
from typing import Dict, Optional

import aiohttp
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import TextContent


BRIDGE_URL = os.getenv("BRIDGE_URL", "http://localhost:3016")

logger = logging.getLogger(__name__)

# Wave 2A R2 W05: ConPort writes carry this principal's token (design 5.3). This
# script runs through `docker exec` in the bridge container (scripts/mcp/wire_claude_mcp.py),
# where the macOS keychain does not exist, so get_token fails there and the write
# goes out unauthenticated (unverified in log mode). Moving a token into the
# container is a design decision, not made here.
_PRINCIPAL = "internal:dopecon"


def _bearer_headers() -> Dict[str, str]:
    """Authorization header for this caller's principal, or {} when no token is available.

    A missing token never fails a write: in log mode the server records it as
    unverified. Only the principal name is logged, never a token.
    """
    try:
        from dopemux.auth import AuthError, get_token
    except ImportError:
        logger.info("dopemux.auth is unavailable; sending %s writes without a token", _PRINCIPAL)
        return {}
    try:
        return {"Authorization": f"Bearer {get_token(_PRINCIPAL)}"}
    except AuthError:
        logger.info("no token for %s; sending the write without Authorization", _PRINCIPAL)
        return {}


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
    headers = await asyncio.to_thread(_bearer_headers)
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
        async with session.post(url, json=payload, headers=headers) as resp:
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
async def conport_promote(
    progress_id: str,
    conport_url: str = "http://localhost:3004",
    workspace_id: Optional[str] = None,
    instance_id: Optional[str] = None,
) -> list[TextContent]:
    """Promote an instance-local progress entry to shared (clears instance_id).

    ConPort requires workspace_id and instance_id on this write; when omitted they
    default to DOPEMUX_WORKSPACE_ID and DOPEMUX_INSTANCE_ID if the environment sets them.
    """
    url = f"{conport_url}/api/progress/promote"
    payload = {"progress_id": progress_id}
    for key, value, env_name in (
        ("workspace_id", workspace_id, "DOPEMUX_WORKSPACE_ID"),
        ("instance_id", instance_id, "DOPEMUX_INSTANCE_ID"),
    ):
        if value or os.getenv(env_name):
            payload[key] = value or os.environ[env_name]
    data = await _post_json(url, payload)
    return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]


@server.tool()
async def conport_promote_all(
    workspace_id: str,
    conport_url: str = "http://localhost:3004",
    instance_id: Optional[str] = None,
) -> list[TextContent]:
    """Promote all instance-local PLANNED/IN_PROGRESS entries to shared for the given instance.

    ConPort requires instance_id on this write; when omitted it defaults to DOPEMUX_INSTANCE_ID if set.
    """
    url = f"{conport_url}/api/progress/promote_all"
    payload = {"workspace_id": workspace_id}
    if instance_id or os.getenv("DOPEMUX_INSTANCE_ID"):
        payload["instance_id"] = instance_id or os.environ["DOPEMUX_INSTANCE_ID"]
    data = await _post_json(url, payload)
    return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]


async def main():
    await stdio_server(server, InitializationOptions(
        server_name="ddg-mcp",
        server_version="1.0.0",
    ))


if __name__ == "__main__":
    asyncio.run(main())
