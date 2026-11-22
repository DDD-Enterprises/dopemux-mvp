"""The cockpit's Start / Finish write path to the Task Orchestrator MCP on port 7890.

Operator ruling 2026-11-22: "Yes, Start/Finish only". This module is the only place in the
dashboard backend that writes to the orchestrator; ``orchestrator_tasks`` stays read-only.

What it may send, and nothing else:
- ``query_items`` ``get`` for one item, to read its current role;
- ``advance_item`` with trigger ``start`` (only when the item is in ``queue``) or ``complete``
  (only when the item is in ``work``), one item per call, with the fixed actor
  ``{id: "operator:cockpit", kind: "user"}`` and the caller's ``requestId``.

The actor is recorded by the orchestrator but not verified (its verifier is a no-op until
Wave 2C), so a cockpit write is attributed, not authenticated.

Before every write the backend proves which project owns port 7890 (Docker labels, the same check
as the read path), reads the item's role, re-proves ownership, and requires the same container id
both times. All of that and the write run under one process-wide lock, so two clicks cannot both
see ``queue``. A writer outside this backend (a runner) can still move the item between the read
and the write; the response then reports the move the orchestrator actually made.

Shapes follow the orchestrator's source at tag v3.8.0, whose ``advance_item`` description equals
the live tools/list capture of 2026-11-16. A refused transition carries ``applied: false``,
``error`` and, for a gate refusal, ``missingNotes``.
"""

from __future__ import annotations

import asyncio
import hmac
import json
import logging
import re
import uuid
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

import aiohttp

from dopemux.mcp.task_orchestrator_identity import DEFAULT_TO_PORT
from dopemux.mcp.tool_snapshot import parse_mcp_response_body
from orchestrator_tasks import (
    MCP_PROTOCOL_VERSION,
    MCP_TIMEOUT_S,
    MCP_URL,
    SOURCE,
    ExpectedProject,
    McpReadError,
    OwnerCheck,
    _display_name,
    _post,
    _project_ref,
    check_port_owner,
    extract_tool_payload,
    resolve_expected_project,
)

logger = logging.getLogger(__name__)

WRITE_TOOL = "advance_item"
READ_TOOL = "query_items"
# trigger -> the only role the item may be in when the cockpit sends it
ALLOWED_TRIGGERS: Dict[str, str] = {"start": "queue", "complete": "work"}
EXPECTED_MOVE: Dict[str, Tuple[str, str]] = {"start": ("queue", "work"), "complete": ("work", "terminal")}
ACTOR: Dict[str, str] = {"id": "operator:cockpit", "kind": "user"}
ACTOR_VERIFICATION = "unverified: recorded by the orchestrator but not checked until Wave 2C"
ROLES = ("queue", "work", "review", "blocked", "terminal")
REASON_MAX = 300

_UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
_WRITE_LOCK = asyncio.Lock()

HTTP_STATUS = {"applied": 200, "refused": 409, "wrong_project": 409, "unavailable": 503}
NOT_WRITTEN = "nothing was written"
OUTCOME_UNKNOWN = "the write outcome is unknown; refresh the queue to see the item's role"


class TransitionOutcomeUnknown(McpReadError):
    """The write call was sent (or may have been), so whether it applied cannot be known."""


# --- response -----------------------------------------------------------------------------


def build_response(
    status: str,
    *,
    item_id: Optional[str] = None,
    trigger: Optional[str] = None,
    request_id: Optional[str] = None,
    reason: Optional[str] = None,
    previous_role: Optional[str] = None,
    new_role: Optional[str] = None,
    missing_notes: Optional[List[Dict[str, Optional[str]]]] = None,
    expected: Optional[ExpectedProject] = None,
    owner: Optional[OwnerCheck] = None,
) -> Dict[str, Any]:
    return {
        "source": SOURCE,
        "endpoint": MCP_URL,
        "status": status,
        "reason": reason,
        "item_id": item_id,
        "trigger": trigger,
        "request_id": request_id,
        "actor": {**ACTOR, "verification": ACTOR_VERIFICATION},
        "previous_role": previous_role,
        "new_role": new_role,
        "missing_notes": missing_notes,
        "project": {
            "expected": _project_ref(expected.project_id, _display_name(expected.project_root)) if expected else None,
            "owner": _project_ref(owner.project_id, owner.name) if owner else None,
            "verdict": owner.verdict if owner else "NOT_CHECKED",
        },
    }


def _owner_refusal(base: Dict[str, Any], owner: OwnerCheck, *, stage: str) -> Dict[str, Any]:
    port = DEFAULT_TO_PORT
    if owner.verdict == "WRONG_PROJECT":
        who = owner.name or owner.project_id or owner.detail
        reason = f"port {port} {stage} is serving project {who} ({owner.detail}), not this one; {NOT_WRITTEN}"
        return build_response("wrong_project", reason=reason, owner=owner, **base)
    reason = f"port {port} owner {stage} could not be proven ({owner.verdict}): {owner.detail}; {NOT_WRITTEN}"
    return build_response("unavailable", reason=reason, owner=owner, **base)


# --- the MCP client -----------------------------------------------------------------------


def _check_call(tool: str, arguments: Dict[str, Any]) -> None:
    """The send-site allow-list: one read and one write tool, and only the two triggers."""
    if tool == READ_TOOL:
        if arguments.get("operation") != "get":
            raise ValueError("only query_items get is sent from the write path")
        return
    if tool != WRITE_TOOL:
        raise ValueError(f"tool {tool!r} is not sent by the cockpit")
    transitions = arguments.get("transitions")
    if not isinstance(transitions, list) or len(transitions) != 1:
        raise ValueError("exactly one transition per call")
    if transitions[0].get("trigger") not in ALLOWED_TRIGGERS:
        raise ValueError(f"trigger {transitions[0].get('trigger')!r} is not exposed by the cockpit")


async def _call_tool(
    tool: str,
    arguments: Dict[str, Any],
    *,
    session_factory: Callable[..., Any] = aiohttp.ClientSession,
) -> Dict[str, Any]:
    """Handshake, then one tools/call. Returns ``structuredContent``.

    Raises McpReadError when the call was never sent, and, for the write tool,
    TransitionOutcomeUnknown once the tools/call request may have reached the orchestrator.
    Messages are fixed text; server text goes to ``detail``, which is logged, never returned.
    """
    _check_call(tool, arguments)
    after_send = TransitionOutcomeUnknown if tool == WRITE_TOOL else McpReadError

    initialize = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {"name": "dopemux-cockpit-transitions", "version": "1"},
        },
    }
    call = {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": tool, "arguments": arguments}}

    sent = False
    try:
        timeout = aiohttp.ClientTimeout(total=MCP_TIMEOUT_S)
        async with session_factory(timeout=timeout) as session:
            status, _body, session_id = await _post(session, initialize, None)
            if status != 200:
                raise McpReadError(f"initialize returned HTTP {status}")
            await _post(session, {"jsonrpc": "2.0", "method": "notifications/initialized"}, session_id)
            sent = True
            status, body, _ = await _post(session, call, session_id)
            if status != 200:
                raise after_send(f"tools/call returned HTTP {status}")
    except McpReadError:
        raise
    except asyncio.TimeoutError as exc:
        cls = after_send if sent else McpReadError
        raise cls(f"timed out after {MCP_TIMEOUT_S:g} s") from exc
    except (aiohttp.ClientError, OSError) as exc:
        cls = after_send if sent else McpReadError
        raise cls(f"connection failed ({type(exc).__name__})", detail=str(exc)[:500]) from exc

    try:
        return extract_tool_payload(parse_mcp_response_body(body))
    except McpReadError as exc:
        raise after_send(str(exc), detail=exc.detail) from exc
    except (ValueError, TypeError) as exc:
        raise after_send("the reply was not a JSON-RPC message", detail=str(exc)[:500]) from exc


async def read_item_role(item_id: str, *, session_factory: Callable[..., Any] = aiohttp.ClientSession) -> str:
    payload = await _call_tool(READ_TOOL, {"operation": "get", "itemId": item_id}, session_factory=session_factory)
    if payload.get("id") != item_id:
        raise McpReadError("the orchestrator returned another item", detail=str(payload.get("id"))[:100])
    role = payload.get("role")
    if role not in ROLES:
        raise McpReadError("the item's role was missing or unknown", detail=str(role)[:100])
    return role


async def send_transition(
    item_id: str,
    trigger: str,
    request_id: str,
    *,
    session_factory: Callable[..., Any] = aiohttp.ClientSession,
) -> Dict[str, Any]:
    if trigger not in ALLOWED_TRIGGERS:
        raise ValueError(f"trigger {trigger!r} is not exposed by the cockpit")
    arguments = {
        "transitions": [{"itemId": item_id, "trigger": trigger, "actor": dict(ACTOR)}],
        "requestId": request_id,
    }
    return await _call_tool(WRITE_TOOL, arguments, session_factory=session_factory)


# --- parsing the write result -------------------------------------------------------------


def _bounded(text: str) -> str:
    return " ".join(text.split())[:REASON_MAX]


def _missing_notes(result: Dict[str, Any]) -> Optional[List[Dict[str, Optional[str]]]]:
    def entry(note: Dict[str, Any]) -> Dict[str, Optional[str]]:
        description = note.get("description")
        return {"key": _bounded(note["key"]), "description": _bounded(description) if isinstance(description, str) else None}

    missing = result.get("missingNotes")
    if isinstance(missing, list):
        notes = [entry(n) for n in missing if isinstance(n, dict) and isinstance(n.get("key"), str)]
        return notes or None
    expected = result.get("expectedNotes")
    if isinstance(expected, list):
        notes = [
            entry(n)
            for n in expected
            if isinstance(n, dict) and isinstance(n.get("key"), str) and n.get("required") is True and n.get("exists") is False
        ]
        return notes or None
    return None


def parse_transition_result(payload: Any, item_id: str, trigger: str) -> Dict[str, Any]:
    """Map the orchestrator's reply to a status. Anything not clearly applied or refused is unknown."""
    unknown = {"status": "unavailable", "reason": f"the orchestrator's reply could not be read; {OUTCOME_UNKNOWN}"}
    results = payload.get("results") if isinstance(payload, dict) else None
    if not isinstance(results, list) or len(results) != 1 or not isinstance(results[0], dict):
        return unknown
    result = results[0]
    if result.get("itemId") != item_id:
        return unknown

    applied = result.get("applied")
    if applied is True:
        previous, new = result.get("previousRole"), result.get("newRole")
        if previous not in ROLES or new not in ROLES:
            return unknown
        reason = None
        want_from, want_to = EXPECTED_MOVE[trigger]
        if (previous, new) != (want_from, want_to):
            reason = (
                f"applied, but the orchestrator moved the item from {previous} to {new}, "
                f"not {want_from} to {want_to}; another writer may have changed it first"
            )
        return {"status": "applied", "reason": reason, "previous_role": previous, "new_role": new}
    if applied is False:
        error = result.get("error")
        text = _bounded(error) if isinstance(error, str) and error.strip() else "no reason given"
        return {"status": "refused", "reason": f"orchestrator refused: {text}", "missing_notes": _missing_notes(result)}
    return unknown


# --- the gate -----------------------------------------------------------------------------


async def transition_item(
    checkout: Path,
    item_id: Any,
    trigger: Any,
    request_id: Any,
    *,
    resolve_expected: Callable[[Path], Optional[ExpectedProject]] = resolve_expected_project,
    check_owner: Callable[[ExpectedProject], OwnerCheck] = check_port_owner,
    get_role: Callable[[str], Awaitable[str]] = read_item_role,
    advance: Callable[[str, str, str], Awaitable[Dict[str, Any]]] = send_transition,
) -> Dict[str, Any]:
    """Start or Finish one item. Returns the response body; status applied | refused | unavailable | wrong_project."""
    base: Dict[str, Any] = {
        "item_id": item_id if isinstance(item_id, str) else None,
        "trigger": trigger if isinstance(trigger, str) else None,
        "request_id": request_id if isinstance(request_id, str) else None,
    }

    if trigger not in ALLOWED_TRIGGERS:
        return build_response("refused", reason="trigger must be start or complete; " + NOT_WRITTEN, **base)
    if not isinstance(item_id, str) or not _UUID.match(item_id):
        return build_response("refused", reason="item id must be a full lowercase UUID; " + NOT_WRITTEN, **base)
    if not isinstance(request_id, str) or not _UUID.match(request_id.lower()):
        return build_response("refused", reason="request_id must be a UUID; " + NOT_WRITTEN, **base)

    expected = await asyncio.to_thread(resolve_expected, checkout)
    base["expected"] = expected
    if expected is None:
        reason = "this backend is not running from a git checkout with a provable project identity; " + NOT_WRITTEN
        return build_response("unavailable", reason=reason, **base)

    async with _WRITE_LOCK:
        owner = await asyncio.to_thread(check_owner, expected)
        if owner.verdict != "OK":
            return _owner_refusal(base, owner, stage="owner")
        if not owner.container_id:
            reason = f"port {DEFAULT_TO_PORT} owner has no container id, so a replaced container could not be noticed; {NOT_WRITTEN}"
            return build_response("unavailable", reason=reason, owner=owner, **base)

        try:
            role = await get_role(item_id)
        except McpReadError as exc:
            logger.warning("role read failed: %s (%s)", exc, exc.detail)
            return build_response("unavailable", reason=f"{MCP_URL} role read failed: {exc}; {NOT_WRITTEN}", owner=owner, **base)

        required = ALLOWED_TRIGGERS[trigger]
        if role != required:
            label = "Start" if trigger == "start" else "Finish"
            reason = f"{label} needs the item in {required}; it is in {role}; {NOT_WRITTEN}"
            return build_response("refused", reason=reason, previous_role=role, owner=owner, **base)

        owner_now = await asyncio.to_thread(check_owner, expected)
        if owner_now.verdict != "OK":
            return _owner_refusal(base, owner_now, stage="owner changed after the role read and")
        if owner_now.container_id != owner.container_id:
            reason = f"port {DEFAULT_TO_PORT} owner was replaced after the role read; {NOT_WRITTEN}"
            return build_response("unavailable", reason=reason, owner=owner_now, **base)

        try:
            payload = await advance(item_id, trigger, request_id)
        except TransitionOutcomeUnknown as exc:
            logger.warning("transition write failed after sending: %s (%s)", exc, exc.detail)
            reason = f"{MCP_URL} write failed: {exc}; {OUTCOME_UNKNOWN}"
            return build_response("unavailable", reason=reason, previous_role=role, owner=owner_now, **base)
        except McpReadError as exc:
            logger.warning("transition write failed before sending: %s (%s)", exc, exc.detail)
            reason = f"{MCP_URL} write failed before sending: {exc}; {NOT_WRITTEN}"
            return build_response("unavailable", reason=reason, previous_role=role, owner=owner_now, **base)

    parsed = parse_transition_result(payload, item_id, trigger)
    if parsed["status"] != "applied":
        # The role this backend read just before the write.
        parsed.setdefault("previous_role", role)
    return build_response(owner=owner_now, **base, **parsed)


# --- the HTTP request ---------------------------------------------------------------------


async def handle_transition_request(
    *,
    item_id: str,
    api_key: Optional[str],
    configured_key: Optional[str],
    body: bytes,
    checkout: Path,
    transition: Callable[..., Awaitable[Dict[str, Any]]] = transition_item,
) -> Tuple[int, Dict[str, Any]]:
    """Auth, then the body, then the transition. Every outcome is (HTTP status, contract body)."""
    base: Dict[str, Any] = {"item_id": item_id}
    if not configured_key:
        reason = "writes are disabled: DASHBOARD_API_KEY is not set on this backend"
        return 403, build_response("refused", reason=reason, **base)
    if not isinstance(api_key, str) or not hmac.compare_digest(api_key.encode(), configured_key.encode()):
        return 401, build_response("refused", reason="X-API-Key is missing or wrong", **base)

    try:
        data = json.loads(body.decode("utf-8")) if body else None
    except (UnicodeDecodeError, ValueError):
        data = None
    if not isinstance(data, dict) or not isinstance(data.get("trigger"), str) or not isinstance(data.get("request_id"), str):
        reason = 'body must be JSON {"trigger": "start" | "complete", "request_id": "<uuid>"}; ' + NOT_WRITTEN
        return 400, build_response("refused", reason=reason, **base)

    try:
        payload = await transition(checkout, item_id, data["trigger"], data["request_id"])
    except Exception:  # noqa: BLE001 - the route promises a contract body, never a bare 500
        logger.exception("transition handler failed")
        reason = f"the backend failed while handling this request; {OUTCOME_UNKNOWN}"
        return 500, build_response(
            "unavailable", reason=reason, trigger=data["trigger"], request_id=data["request_id"], **base
        )
    return HTTP_STATUS.get(str(payload.get("status")), 500), payload


def new_request_id() -> str:
    return str(uuid.uuid4())


__all__ = [
    "ACTOR",
    "ALLOWED_TRIGGERS",
    "READ_TOOL",
    "TransitionOutcomeUnknown",
    "WRITE_TOOL",
    "build_response",
    "handle_transition_request",
    "parse_transition_result",
    "read_item_role",
    "send_transition",
    "transition_item",
]
