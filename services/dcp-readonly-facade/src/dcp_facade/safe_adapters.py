"""Release-one safe adapter gate (TP-DCP-MCP-RO-0015).

Only ConPort decision list/read and dope-memory search/replay may run, and only
after ownership is VERIFIED. Progress, broad query, writes, and non-release
families are structurally denied. Callers inject HTTP clients — this module
does not open sockets by itself.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from . import conport as conport_adapter
from . import dope_memory as dope_memory_adapter
from .http_client import HttpResponse, ReadOnlyHttpClient, ReadOnlyHttpError
from .ownership import OwnershipVerdict
from .route_manifest import (
    CONPORT,
    DOPE_MEMORY,
    RELEASE_ONE_OPERATIONS,
    is_release_one_operation,
)


@dataclass(frozen=True)
class SafeAdapterResult:
    allowed: bool
    operation: str
    family: str
    reason: str
    response: Optional[HttpResponse] = None

    def to_public_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "allowed": self.allowed,
            "operation": self.operation,
            "family": self.family,
            "reason": self.reason,
            "callable": False,
        }
        if self.allowed and self.response is not None:
            out["status_code"] = self.response.status
            out["ok"] = self.response.ok
            # Body remains for tool layer redaction; never invent data on deny.
            out["data"] = self.response.json if self.response.ok else None
        else:
            out["data"] = None
        return out


def _deny(operation: str, family: str, reason: str) -> SafeAdapterResult:
    return SafeAdapterResult(
        allowed=False, operation=operation, family=family, reason=reason, response=None
    )


def require_verified_ownership(verdict: OwnershipVerdict, family: str) -> Optional[str]:
    """Return a block reason or None when ownership permits adapter use."""
    if verdict.family != family:
        return "ownership family mismatch"
    if not verdict.verified:
        return verdict.reason or "ownership not verified"
    return None


def list_decisions(
    *,
    ownership: OwnershipVerdict,
    client: ReadOnlyHttpClient,
    base_url: str,
    workspace_id: str,
    limit: Optional[int] = None,
) -> SafeAdapterResult:
    op = "list_decisions"
    if not is_release_one_operation(CONPORT, op):
        return _deny(op, CONPORT, "operation not in release-one allowlist")
    blocked = require_verified_ownership(ownership, CONPORT)
    if blocked:
        return _deny(op, CONPORT, blocked)
    try:
        resp = conport_adapter.get_decisions(client, base_url, workspace_id, limit=limit)
    except ReadOnlyHttpError as exc:
        return _deny(op, CONPORT, f"adapter error: {exc}")
    return SafeAdapterResult(
        allowed=True, operation=op, family=CONPORT, reason="ok", response=resp
    )


def get_decision(
    *,
    ownership: OwnershipVerdict,
    client: ReadOnlyHttpClient,
    base_url: str,
    workspace_id: str,
    decision_id: str,
) -> SafeAdapterResult:
    op = "get_decision"
    if not is_release_one_operation(CONPORT, op):
        return _deny(op, CONPORT, "operation not in release-one allowlist")
    blocked = require_verified_ownership(ownership, CONPORT)
    if blocked:
        return _deny(op, CONPORT, blocked)
    try:
        resp = conport_adapter.get_decision(client, base_url, workspace_id, decision_id)
    except ReadOnlyHttpError as exc:
        return _deny(op, CONPORT, f"adapter error: {exc}")
    return SafeAdapterResult(
        allowed=True, operation=op, family=CONPORT, reason="ok", response=resp
    )


def memory_search(
    *,
    ownership: OwnershipVerdict,
    client: ReadOnlyHttpClient,
    base_url: str,
    workspace_id: str,
    query: str = "",
    top_k: int = 3,
) -> SafeAdapterResult:
    op = "memory_search"
    if not is_release_one_operation(DOPE_MEMORY, op):
        return _deny(op, DOPE_MEMORY, "operation not in release-one allowlist")
    blocked = require_verified_ownership(ownership, DOPE_MEMORY)
    if blocked:
        return _deny(op, DOPE_MEMORY, blocked)
    try:
        resp = dope_memory_adapter.memory_search(
            client, base_url, workspace_id, query=query, top_k=top_k
        )
    except ReadOnlyHttpError as exc:
        return _deny(op, DOPE_MEMORY, f"adapter error: {exc}")
    return SafeAdapterResult(
        allowed=True, operation=op, family=DOPE_MEMORY, reason="ok", response=resp
    )


def memory_replay_session(
    *,
    ownership: OwnershipVerdict,
    client: ReadOnlyHttpClient,
    base_url: str,
    workspace_id: str,
    session_id: str,
    mode: str = "replay_current",
    top_k: int = 3,
) -> SafeAdapterResult:
    op = "memory_replay_session"
    if not is_release_one_operation(DOPE_MEMORY, op):
        return _deny(op, DOPE_MEMORY, "operation not in release-one allowlist")
    blocked = require_verified_ownership(ownership, DOPE_MEMORY)
    if blocked:
        return _deny(op, DOPE_MEMORY, blocked)
    try:
        resp = dope_memory_adapter.memory_replay_session(
            client, base_url, workspace_id, session_id, mode=mode, top_k=top_k
        )
    except ReadOnlyHttpError as exc:
        return _deny(op, DOPE_MEMORY, f"adapter error: {exc}")
    return SafeAdapterResult(
        allowed=True, operation=op, family=DOPE_MEMORY, reason="ok", response=resp
    )


def deny_blocked_operation(operation: str, family: str) -> SafeAdapterResult:
    """Explicit deny for progress/query/writes and other non-release ops."""
    if is_release_one_operation(family, operation):
        return _deny(operation, family, "use the typed release-one entrypoint")
    return _deny(operation, family, "operation blocked for release-one")


def release_one_operations() -> dict[str, tuple[str, ...]]:
    return {family: tuple(ops) for family, ops in RELEASE_ONE_OPERATIONS.items()}
