"""task-orchestrator read adapter (HTTP, :8000) — GET-only.

Maps to the inventory's CONFIRMED_READ_ONLY task-orchestrator surfaces. The
caller never supplies base_url/project_id/route — those come from the
registry-bound ``task-orchestrator`` service profile. All reads are GET; this
module never constructs a task-orchestrator write route.

Results are returned raw (the tool layer redacts + envelopes); a backend error
raises ReadOnlyHttpError (fail closed).

NOTE: The `/workflow/state` route is inventory-classified as UNCLASSIFIED in the
discovery gap (TP-DCP-MCP-RO-0001 missed it), but it exists in the runtime
(project_workflow.py:385) as a first-class GET read. This adapter implements it
as a GET; formal inventory + classification is deferred to downstream documentation.
"""

from __future__ import annotations

from typing import Optional
from urllib.parse import quote

from .http_client import HttpResponse, ReadOnlyHttpClient, ReadOnlyHttpError

MAX_LIMIT = 20


def _cap(limit: Optional[int]) -> int:
    if not isinstance(limit, int) or limit <= 0:
        return MAX_LIMIT
    return min(limit, MAX_LIMIT)


def _validate_project_id(project_id: str) -> str:
    """Validate and encode project_id (single path segment, fail closed)."""
    if "/" in project_id or ".." in project_id:
        raise ReadOnlyHttpError("invalid project_id (must be a single segment)")
    return quote(project_id, safe="")


def get_workflow_queue(
    client: ReadOnlyHttpClient,
    base_url: str,
    project_id: str,
    limit: Optional[int] = MAX_LIMIT,
) -> HttpResponse:
    """GET /api/projects/{project_id}/workflow/queue

    Retrieve the workflow queue (pending, in-progress items).

    Args:
        client: ReadOnlyHttpClient
        base_url: Service base URL (registry-owned)
        project_id: Project identifier (single path segment)
        limit: Max queue items to return (capped at MAX_LIMIT)

    Returns:
        HttpResponse with queue items; identity fields (e.g. claimedBy) are
        returned raw and may be redacted by the tool layer.

    Raises:
        ReadOnlyHttpError: Invalid project_id or backend failure
    """
    safe_pid = _validate_project_id(project_id)
    return client.get(
        base_url,
        f"/api/projects/{safe_pid}/workflow/queue",
        {"limit": _cap(limit)},
    )


def get_workflow_blockers(
    client: ReadOnlyHttpClient,
    base_url: str,
    project_id: str,
) -> HttpResponse:
    """GET /api/projects/{project_id}/workflow/blockers

    Retrieve blocked workflow items and their blocking dependencies.

    Args:
        client: ReadOnlyHttpClient
        base_url: Service base URL (registry-owned)
        project_id: Project identifier (single path segment)

    Returns:
        HttpResponse with blocked items; raw response.

    Raises:
        ReadOnlyHttpError: Invalid project_id or backend failure
    """
    safe_pid = _validate_project_id(project_id)
    return client.get(
        base_url,
        f"/api/projects/{safe_pid}/workflow/blockers",
    )


def get_workflow_state(
    client: ReadOnlyHttpClient,
    base_url: str,
    project_id: str,
) -> HttpResponse:
    """GET /api/projects/{project_id}/workflow/state

    Retrieve workflow state snapshot: phases, stages, allowed transitions, and
    linked item IDs.

    NOTE: This route exists in the runtime (project_workflow.py:385) but was
    absent from the TP-DCP-MCP-RO-0001 inventory. It is classified as GET
    (read-only) and included in this adapter; formal inventory + classification
    is deferred to downstream documentation.

    Args:
        client: ReadOnlyHttpClient
        base_url: Service base URL (registry-owned)
        project_id: Project identifier (single path segment)

    Returns:
        HttpResponse with workflow state snapshot; raw response.

    Raises:
        ReadOnlyHttpError: Invalid project_id or backend failure
    """
    safe_pid = _validate_project_id(project_id)
    return client.get(
        base_url,
        f"/api/projects/{safe_pid}/workflow/state",
    )
