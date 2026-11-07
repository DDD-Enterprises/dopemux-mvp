"""Streamable-HTTP MCP endpoint for the dope-memory service.

Builds a FastMCP server exposing the existing ``memory_*`` tools and an ASGI
app serving the MCP streamable-HTTP transport at ``/mcp``.  Mounted onto the
FastAPI app in ``dope_memory_main`` so REST (``/tools/*``) and MCP share one
process and one ``DopeMemoryMCPServer`` instance.

The pip-installed ``mcp`` SDK (a fastmcp dependency) must not be shadowed by
a local package named ``mcp`` — the service-local tool implementations live
in ``wma_mcp/`` for that reason.
"""

from __future__ import annotations

import logging
from typing import Annotated, Any, Callable, Optional

from pydantic import Field

from auth_identity import (
    AuthGate,
    Unauthorized,
    WriteIdentityError,
    caller_label,
    validate_write_ids,
)

logger = logging.getLogger(__name__)

FASTMCP_AVAILABLE = True
try:
    from fastmcp import FastMCP
    from fastmcp.exceptions import ToolError
    from fastmcp.server.dependencies import get_http_request
except ImportError:  # pragma: no cover - container image always has fastmcp
    FASTMCP_AVAILABLE = False
    FastMCP = None  # type: ignore[assignment]
    get_http_request = None  # type: ignore[assignment]

    class ToolError(RuntimeError):  # type: ignore[no-redef]
        """Fallback so type references stay valid without fastmcp."""


# ``get_server`` indirection: the DopeMemoryMCPServer is created in the
# FastAPI lifespan, after this module builds the tool definitions.
ServerGetter = Callable[[], Any]

# Write tools take both ids as optional (Amendment 04): the server fills an
# omitted one from its own binding and rejects a workspace that is not its own.
WorkspaceIdParam = Annotated[
    Optional[str],
    Field(
        description="Workspace to write to. Optional: the server fills it from "
        "its own binding; a value that differs from the binding is rejected."
    ),
]
InstanceIdParam = Annotated[
    Optional[str],
    Field(
        description="Instance to write as. Optional: the server fills it from "
        "its own binding (its configured instance)."
    ),
]


def build_mcp_server(
    get_server: ServerGetter,
    *,
    bound_workspace_id: Optional[str],
    gate: AuthGate,
    read_default_instance_id: str = "A",
) -> Any:
    """Create a FastMCP server whose tools delegate to DopeMemoryMCPServer.

    Writes (``auth_identity.WRITE_TOOLS``) take ``workspace_id`` and
    ``instance_id`` as optional: an omitted one is filled from
    ``bound_workspace_id`` / ``read_default_instance_id`` (the server's own
    instance). A ``workspace_id`` that differs from ``bound_workspace_id`` is
    rejected, and so is every write when the server has no binding. Writes carry
    the principal ``gate`` verifies from the request's bearer token. Reads keep a
    default workspace/instance so existing read-only clients continue to work.
    """
    if not FASTMCP_AVAILABLE:
        raise RuntimeError("fastmcp is not installed; MCP endpoint unavailable")

    mcp = FastMCP(name="dope-memory")
    read_workspace_id = bound_workspace_id or "default"

    def _server() -> Any:
        server = get_server()
        if server is None:
            raise ToolError("dope-memory backend not initialized yet")
        return server

    def _authorize_write(
        workspace_id: Optional[str], instance_id: Optional[str]
    ) -> tuple[str, str, str]:
        """Verify the caller and resolve the ids of a write.

        Returns ``(principal, workspace_id, instance_id)`` with omitted ids
        filled from the server's binding.
        """
        try:
            request = get_http_request()
            headers = request.headers
            authorization = headers.get("authorization")
            caller = caller_label(
                headers.get("user-agent"), request.client.host if request.client else None
            )
        except RuntimeError:  # no HTTP request: in-process call, nothing to verify
            authorization, caller = None, "in-process"
        try:
            identity = gate.authorize_write(authorization, caller)
            workspace_id, instance_id = validate_write_ids(
                workspace_id, instance_id, bound_workspace_id, read_default_instance_id
            )
        except (Unauthorized, WriteIdentityError) as exc:
            raise ToolError(str(exc)) from None
        return identity.principal, workspace_id, instance_id

    def _unwrap(result: Any) -> dict[str, Any]:
        """Convert a backend result into MCP output (raise on failure).

        Supports both backend shapes: the inline DopeMemoryMCPServer in
        dope_memory_main returns a ToolResponse dataclass; the library class
        in wma_mcp/server.py returns plain dicts with a "success" key.
        """
        if isinstance(result, dict):
            if not result.get("success", True):
                raise ToolError(result.get("error") or "tool call failed")
            return {k: v for k, v in result.items() if k != "success"}
        if not result.success:
            raise ToolError(result.error or "tool call failed")
        return result.data

    @mcp.tool(name="memory_search")
    def memory_search(
        query: str = "",
        workspace_id: str = read_workspace_id,
        instance_id: str = read_default_instance_id,
        session_id: Optional[str] = None,
        category: Optional[str] = None,
        entry_type: Optional[str] = None,
        workflow_phase: Optional[str] = None,
        tags_any: Optional[list[str]] = None,
        time_range: Optional[str] = None,
        top_k: int = 3,
        cursor: Optional[str] = None,
        include_superseded: bool = False,
    ) -> dict[str, Any]:
        """Search work log entries (Top-3 default, trajectory-boosted ranking,
        cursor pagination)."""
        filters = {
            k: v
            for k, v in {
                "category": category,
                "entry_type": entry_type,
                "workflow_phase": workflow_phase,
                "tags_any": tags_any,
                "time_range": time_range,
            }.items()
            if v is not None
        }
        return _unwrap(
            _server().memory_search(
                query=query,
                workspace_id=workspace_id,
                instance_id=instance_id,
                session_id=session_id,
                filters=filters or None,
                top_k=top_k,
                cursor=cursor,
                include_superseded=include_superseded,
            )
        )

    @mcp.tool(name="memory_store")
    def memory_store(
        category: str,
        entry_type: str,
        summary: str,
        workspace_id: WorkspaceIdParam = None,
        instance_id: InstanceIdParam = None,
        session_id: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
        reasoning: Optional[str] = None,
        outcome: str = "in_progress",
        importance_score: int = 6,
        tags: Optional[list[str]] = None,
        links: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Store a manual work log entry (secrets are redacted before write).

        workspace_id and instance_id are optional; the server fills them from
        its binding."""
        principal, workspace_id, instance_id = _authorize_write(workspace_id, instance_id)
        return _unwrap(
            _server().memory_store(
                workspace_id=workspace_id,
                instance_id=instance_id,
                category=category,
                entry_type=entry_type,
                summary=summary,
                session_id=session_id,
                details=details,
                reasoning=reasoning,
                outcome=outcome,
                importance_score=importance_score,
                tags=tags,
                links=links,
                write_principal=principal,
            )
        )

    @mcp.tool(name="memory_recap")
    def memory_recap(
        workspace_id: str = read_workspace_id,
        instance_id: str = read_default_instance_id,
        scope: str = "session",
        session_id: Optional[str] = None,
        top_k: int = 3,
    ) -> dict[str, Any]:
        """Get a recap of recent work (scope: session | today | last_2_hours)."""
        return _unwrap(
            _server().memory_recap(
                workspace_id=workspace_id,
                instance_id=instance_id,
                scope=scope,
                session_id=session_id,
                top_k=top_k,
            )
        )

    @mcp.tool(name="memory_mark_issue")
    def memory_mark_issue(
        issue_entry_id: str,
        description: str,
        workspace_id: WorkspaceIdParam = None,
        instance_id: InstanceIdParam = None,
        confidence: float = 0.7,
        evidence_window_min: int = 30,
        tags: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Mark an existing work log entry as an issue source.

        workspace_id and instance_id are optional; the server fills them from
        its binding."""
        _, workspace_id, instance_id = _authorize_write(workspace_id, instance_id)
        return _unwrap(
            _server().memory_mark_issue(
                workspace_id=workspace_id,
                instance_id=instance_id,
                issue_entry_id=issue_entry_id,
                description=description,
                confidence=confidence,
                evidence_window_min=evidence_window_min,
                tags=tags,
            )
        )

    @mcp.tool(name="memory_link_resolution")
    def memory_link_resolution(
        issue_entry_id: str,
        resolution_entry_id: str,
        workspace_id: WorkspaceIdParam = None,
        instance_id: InstanceIdParam = None,
        confidence: float = 0.8,
        evidence_window_min: int = 30,
    ) -> dict[str, Any]:
        """Link an issue entry to the entry that resolved it.

        workspace_id and instance_id are optional; the server fills them from
        its binding."""
        principal, workspace_id, instance_id = _authorize_write(workspace_id, instance_id)
        return _unwrap(
            _server().memory_link_resolution(
                workspace_id=workspace_id,
                instance_id=instance_id,
                issue_entry_id=issue_entry_id,
                resolution_entry_id=resolution_entry_id,
                confidence=confidence,
                evidence_window_min=evidence_window_min,
                write_principal=principal,
            )
        )

    @mcp.tool(name="memory_replay_session")
    def memory_replay_session(
        session_id: str,
        workspace_id: str = read_workspace_id,
        instance_id: str = read_default_instance_id,
        top_k: int = 3,
        cursor: Optional[str] = None,
        mode: str = "replay_current",
    ) -> dict[str, Any]:
        """Replay session entries chronologically (mode: replay_current |
        replay_full)."""
        return _unwrap(
            _server().memory_replay_session(
                workspace_id=workspace_id,
                instance_id=instance_id,
                session_id=session_id,
                top_k=top_k,
                cursor=cursor,
                mode=mode,
            )
        )

    @mcp.tool(name="memory_correct")
    def memory_correct(
        entry_id: str,
        correction_type: str,
        workspace_id: WorkspaceIdParam = None,
        instance_id: InstanceIdParam = None,
        corrected_summary: Optional[str] = None,
        corrected_tags: Optional[list[str]] = None,
        corrected_category: Optional[str] = None,
        corrected_entry_type: Optional[str] = None,
        corrected_outcome: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> dict[str, Any]:
        """Supersede an entry with a corrected version (correction_type:
        summary | tags | category | outcome | retraction). The original is
        preserved immutably. workspace_id and instance_id are optional; the
        server fills them from its binding."""
        principal, workspace_id, instance_id = _authorize_write(workspace_id, instance_id)
        return _unwrap(
            _server().memory_correct(
                workspace_id=workspace_id,
                instance_id=instance_id,
                entry_id=entry_id,
                correction_type=correction_type,
                corrected_summary=corrected_summary,
                corrected_tags=corrected_tags,
                corrected_category=corrected_category,
                corrected_entry_type=corrected_entry_type,
                corrected_outcome=corrected_outcome,
                idempotency_key=idempotency_key,
                write_principal=principal,
            )
        )

    @mcp.tool(name="memory_generate_reflection")
    def memory_generate_reflection(
        workspace_id: WorkspaceIdParam = None,
        instance_id: InstanceIdParam = None,
        session_id: Optional[str] = None,
        window_hours: int = 2,
    ) -> dict[str, Any]:
        """Generate a deterministic reflection card from recent work.

        workspace_id and instance_id are optional; the server fills them from
        its binding."""
        principal, workspace_id, instance_id = _authorize_write(workspace_id, instance_id)
        return _unwrap(
            _server().memory_generate_reflection(
                workspace_id=workspace_id,
                instance_id=instance_id,
                session_id=session_id,
                window_hours=window_hours,
                write_principal=principal,
            )
        )

    @mcp.tool(name="memory_reflections")
    def memory_reflections(
        workspace_id: str = read_workspace_id,
        instance_id: str = read_default_instance_id,
        session_id: Optional[str] = None,
        limit: int = 3,
    ) -> dict[str, Any]:
        """Fetch recent reflection cards."""
        return _unwrap(
            _server().memory_reflections(
                workspace_id=workspace_id,
                instance_id=instance_id,
                session_id=session_id,
                limit=limit,
            )
        )

    @mcp.tool(name="memory_trajectory")
    def memory_trajectory(
        workspace_id: str = read_workspace_id,
        instance_id: str = read_default_instance_id,
    ) -> dict[str, Any]:
        """Get the current trajectory state (stream, goal, recent steps,
        boost factor)."""
        return _unwrap(
            _server().memory_trajectory(
                workspace_id=workspace_id,
                instance_id=instance_id,
            )
        )

    return mcp


def build_mcp_http_app(mcp: Any):
    """Build the streamable-HTTP ASGI app with its endpoint at ``/mcp``.

    Mount at the FastAPI root (``app.mount("", ...)``) so clients reach the
    endpoint at exactly ``/mcp`` with no trailing-slash redirect.
    """
    return mcp.http_app(path="/mcp")
