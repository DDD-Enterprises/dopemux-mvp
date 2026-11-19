"""Read-only view of the Task Orchestrator work queue for the cockpit.

The orchestrator MCP listens on one reserved host port and serves whichever project's
container currently publishes it. A plain client therefore reads another repository's tasks
whenever that repository owns the port. This module serves items only after proving, from the
container's dopemux labels, that the owner is the project this backend was started from. It
proves it again after the read and discards the items if the owner changed.

It reads only. It never starts, stops or switches the orchestrator, and it sends one tool:
``query_items`` in list mode.

Deployment: the proof needs ``docker ps`` and a git checkout. A host-run backend has both.
The compose container has neither, so there every answer is ``unavailable``.
"""

from __future__ import annotations

import asyncio
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

import aiohttp

from dopemux.mcp.docker_inspect import inspect_running_containers
from dopemux.mcp.runtime_state import resolve_identity_view
from dopemux.mcp.task_orchestrator_identity import (
    DEFAULT_TO_PORT,
    identity_from_docker_labels,
    match_target,
)
from dopemux.mcp.tool_snapshot import parse_mcp_response_body

SOURCE = "task-orchestrator-mcp"
MCP_URL = f"http://127.0.0.1:{DEFAULT_TO_PORT}/mcp"
# Roles the cockpit lists, in display order. review, blocked and terminal are not listed.
LISTED_ROLES: Tuple[str, ...] = ("work", "queue")
ROLE_LIMIT = 20
OWNER_CHECK_TIMEOUT_S = 5.0
MCP_TIMEOUT_S = 5.0
MCP_PROTOCOL_VERSION = "2024-11-05"

_JSON_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}


class McpReadError(Exception):
    """The orchestrator could not be read, or answered in a shape this reader does not know."""


@dataclass(frozen=True)
class ExpectedProject:
    project_id: str
    project_root: str


@dataclass(frozen=True)
class OwnerCheck:
    verdict: str  # OK | WRONG_PROJECT | UNKNOWN | CONFLICT
    project_id: Optional[str]
    name: Optional[str]
    detail: str


def _display_name(project_root: Optional[str]) -> Optional[str]:
    """Directory name only: host paths never leave this module."""
    if not project_root:
        return None
    return PurePosixPath(str(project_root).rstrip("/")).name or None


# --- identity ------------------------------------------------------------------------------


def resolve_expected_project(checkout: Path) -> Optional[ExpectedProject]:
    """The project this backend runs from, by git only. None when it cannot be proven."""
    try:
        view = resolve_identity_view(Path(checkout), trust_env=False)
    except (OSError, subprocess.SubprocessError):
        # The resolver runs git and only handles git's own refusals. No git binary (the slim
        # service image has none) or a git that hangs means the identity cannot be proven.
        return None
    if not view.project_id or not view.project_root or view.identity_confidence == "UNKNOWN":
        return None
    return ExpectedProject(project_id=view.project_id, project_root=view.project_root)


def check_port_owner(
    expected: ExpectedProject,
    *,
    inspect: Callable[..., Any] = inspect_running_containers,
) -> OwnerCheck:
    """Who publishes the orchestrator port right now, judged against ``expected``.

    Mirrors the launcher's owner verdict: exactly one publishing container, identified by its
    dopemux labels and matched with ``match_target``. Blocking; run it off the event loop.
    """
    state = inspect(timeout=OWNER_CHECK_TIMEOUT_S)
    if not state.available:
        return OwnerCheck("UNKNOWN", None, None, f"docker ps unavailable: {state.error or 'no detail'}")

    owners = [c for c in state.containers if DEFAULT_TO_PORT in (c.published_ports or [])]
    if not owners:
        return OwnerCheck("UNKNOWN", None, None, f"no container publishes port {DEFAULT_TO_PORT}")
    if len(owners) > 1:
        names = ", ".join(sorted(c.name for c in owners))
        return OwnerCheck("UNKNOWN", None, None, f"more than one container publishes port {DEFAULT_TO_PORT}: {names}")

    owner = owners[0]
    observed = identity_from_docker_labels(owner.labels or {}, port=DEFAULT_TO_PORT, container_name=owner.name)
    verdict = match_target(observed, project_id=expected.project_id, project_root=expected.project_root)
    if not observed.has_project_proof():
        detail = f"container {owner.name} publishes port {DEFAULT_TO_PORT} without dopemux project labels"
    else:
        detail = f"container {owner.name}"
    return OwnerCheck(verdict, observed.project_id, _display_name(observed.project_root), detail)


# --- parsing -------------------------------------------------------------------------------


def extract_tool_payload(rpc: Any) -> Dict[str, Any]:
    """The ``structuredContent`` object of a tools/call reply, or McpReadError."""
    if not isinstance(rpc, dict):
        raise McpReadError("reply is not a JSON-RPC object")
    if rpc.get("error") is not None:
        error = rpc["error"]
        message = error.get("message") if isinstance(error, dict) else error
        raise McpReadError(f"JSON-RPC error: {str(message)[:200]}")
    result = rpc.get("result")
    if not isinstance(result, dict):
        raise McpReadError("reply has no result object")
    if result.get("isError"):
        raise McpReadError(f"tool reported an error: {_first_text(result)[:200]}")
    payload = result.get("structuredContent")
    if not isinstance(payload, dict):
        raise McpReadError("reply has no structuredContent object")
    return payload


def _first_text(result: Dict[str, Any]) -> str:
    content = result.get("content")
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and isinstance(block.get("text"), str):
                return block["text"]
    return "no detail"


def _optional_str(value: Any) -> Optional[str]:
    return value if isinstance(value, str) and value else None


def _optional_int(value: Any) -> Optional[int]:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _tags(value: Any) -> Optional[List[str]]:
    if isinstance(value, str):
        return [tag.strip() for tag in value.split(",") if tag.strip()]
    if isinstance(value, list) and all(isinstance(tag, str) for tag in value):
        return list(value)
    return None


def parse_item_list(payload: Dict[str, Any], role: str) -> Tuple[List[Dict[str, Any]], Optional[int]]:
    """Map a list-mode result to cockpit items. Unknown optional fields become None.

    An item without an id or title, or in a role other than the one asked for, is not
    something this reader understands: the whole result is refused.
    """
    raw_items = payload.get("items") if isinstance(payload, dict) else None
    if not isinstance(raw_items, list):
        raise McpReadError("result has no items array")

    items: List[Dict[str, Any]] = []
    for raw in raw_items:
        if not isinstance(raw, dict):
            raise McpReadError("an item is not an object")
        item_id = _optional_str(raw.get("id"))
        title = _optional_str(raw.get("title"))
        if item_id is None or title is None:
            raise McpReadError("an item has no id or no title")
        item_role = raw.get("role", role)
        if item_role != role:
            raise McpReadError(f"asked for role {role}, got an item in role {str(item_role)[:40]}")
        items.append(
            {
                "id": item_id,
                "title": title,
                "role": role,
                "priority": _optional_str(raw.get("priority")),
                "parent_id": _optional_str(raw.get("parentId")),
                "depth": _optional_int(raw.get("depth")),
                "tags": _tags(raw.get("tags")),
                "complexity": _optional_int(raw.get("complexity")),
            }
        )
    return items, _optional_int(payload.get("total"))


# --- MCP client ----------------------------------------------------------------------------


async def _post(session: Any, payload: Dict[str, Any], session_id: Optional[str]) -> Tuple[int, str, Optional[str]]:
    headers = dict(_JSON_HEADERS)
    if session_id:
        headers["Mcp-Session-Id"] = session_id
    async with session.post(MCP_URL, json=payload, headers=headers) as response:
        body = await response.text()
        return response.status, body, response.headers.get("Mcp-Session-Id")


async def list_role_items(
    role: str,
    *,
    session_factory: Callable[..., Any] = aiohttp.ClientSession,
) -> Tuple[List[Dict[str, Any]], Optional[int]]:
    """List up to ROLE_LIMIT items in ``role`` from the orchestrator. Raises McpReadError."""
    if role not in LISTED_ROLES:
        raise ValueError(f"role {role!r} is not listed by the cockpit")

    initialize = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {"name": "dopemux-cockpit-queue-reader", "version": "1"},
        },
    }
    call = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "query_items",
            "arguments": {"operation": "search", "role": role, "limit": ROLE_LIMIT},
        },
    }

    try:
        timeout = aiohttp.ClientTimeout(total=MCP_TIMEOUT_S)
        async with session_factory(timeout=timeout) as session:
            status, _body, session_id = await _post(session, initialize, None)
            if status != 200:
                raise McpReadError(f"initialize returned HTTP {status}")
            # Best effort, as in dopemux.mcp.tool_snapshot: the reply to a notification is not used.
            await _post(session, {"jsonrpc": "2.0", "method": "notifications/initialized"}, session_id)
            status, body, _ = await _post(session, call, session_id)
            if status != 200:
                raise McpReadError(f"tools/call returned HTTP {status}")
    except McpReadError:
        raise
    except asyncio.TimeoutError as exc:
        raise McpReadError(f"timed out after {MCP_TIMEOUT_S:g} s") from exc
    except (aiohttp.ClientError, OSError) as exc:
        raise McpReadError(str(exc)[:200] or type(exc).__name__) from exc

    return parse_item_list(extract_tool_payload(parse_mcp_response_body(body)), role)


# --- the gate ------------------------------------------------------------------------------


def _project_ref(project_id: Optional[str], name: Optional[str]) -> Optional[Dict[str, Optional[str]]]:
    if project_id is None and name is None:
        return None
    return {"project_id": project_id, "name": name}


def _response(
    status: str,
    *,
    reason: Optional[str],
    expected: Optional[ExpectedProject],
    owner: Optional[OwnerCheck],
    items: Optional[List[Dict[str, Any]]] = None,
    total: Optional[int] = None,
) -> Dict[str, Any]:
    return {
        "source": SOURCE,
        "endpoint": MCP_URL,
        "status": status,
        "reason": reason,
        "project": {
            "expected": _project_ref(expected.project_id, _display_name(expected.project_root)) if expected else None,
            "owner": _project_ref(owner.project_id, owner.name) if owner else None,
            "verdict": owner.verdict if owner else "NOT_CHECKED",
        },
        "roles": list(LISTED_ROLES),
        "items": items or [],
        "total": total,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def _refusal(expected: ExpectedProject, owner: OwnerCheck, *, changed: bool = False) -> Dict[str, Any]:
    """The response for any owner verdict other than OK. Never carries items."""
    port = DEFAULT_TO_PORT
    if owner.verdict == "WRONG_PROJECT":
        who = owner.name or owner.project_id or owner.detail
        lead = f"port {port} owner changed during the read: it" if changed else f"port {port}"
        reason = f"{lead} is serving project {who} ({owner.detail}), not this one"
        return _response("wrong_project", reason=reason, expected=expected, owner=owner)
    lead = f"port {port} owner changed during the read and" if changed else f"port {port} owner"
    reason = f"{lead} could not be proven ({owner.verdict}): {owner.detail}"
    return _response("unavailable", reason=reason, expected=expected, owner=owner)


async def read_task_queue(
    checkout: Path,
    *,
    resolve_expected: Callable[[Path], Optional[ExpectedProject]] = resolve_expected_project,
    check_owner: Callable[[ExpectedProject], OwnerCheck] = check_port_owner,
    list_role: Callable[[str], Awaitable[Tuple[List[Dict[str, Any]], Optional[int]]]] = list_role_items,
) -> Dict[str, Any]:
    """The cockpit's task queue, or a status that says exactly why there is none.

    status: ok | empty | unavailable | wrong_project. Items are returned only for ok.
    """
    expected = await asyncio.to_thread(resolve_expected, checkout)
    if expected is None:
        return _response(
            "unavailable",
            reason="this backend is not running from a git checkout with a provable project identity",
            expected=None,
            owner=None,
        )

    owner = await asyncio.to_thread(check_owner, expected)
    if owner.verdict != "OK":
        return _refusal(expected, owner)

    items: List[Dict[str, Any]] = []
    totals: List[Optional[int]] = []
    try:
        for role in LISTED_ROLES:
            role_items, role_total = await list_role(role)
            items.extend(role_items)
            totals.append(role_total)
    except McpReadError as exc:
        return _response("unavailable", reason=f"{MCP_URL} read failed: {exc}", expected=expected, owner=owner)

    # The port can change hands between the proof and the read; never serve what may be another
    # project's items.
    owner_after = await asyncio.to_thread(check_owner, expected)
    if owner_after.verdict != "OK":
        return _refusal(expected, owner_after, changed=True)

    total = sum(t for t in totals if t is not None) if all(t is not None for t in totals) else None
    return _response("ok" if items else "empty", reason=None, expected=expected, owner=owner_after, items=items, total=total)


__all__ = [
    "ExpectedProject",
    "LISTED_ROLES",
    "MCP_URL",
    "McpReadError",
    "OwnerCheck",
    "check_port_owner",
    "extract_tool_payload",
    "list_role_items",
    "parse_item_list",
    "read_task_queue",
    "resolve_expected_project",
]
