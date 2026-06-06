"""ConPort read adapter (HTTP, :3004) — GET-only.

Maps to the inventory's CONFIRMED_READ_ONLY ConPort surfaces. The caller never
supplies base_url/workspace_id/route — those come from the registry-bound
``conport`` service profile. All reads are GET; this module never constructs a
ConPort write route. Results are returned raw (the tool layer redacts +
envelopes); a backend error raises ReadOnlyHttpError (fail closed).
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


def get_decisions(
    client: ReadOnlyHttpClient, base_url: str, workspace_id: str, limit: Optional[int] = MAX_LIMIT
) -> HttpResponse:
    return client.get(
        base_url, "/api/decisions", {"workspace_id": workspace_id, "limit": _cap(limit)}
    )


def get_progress(
    client: ReadOnlyHttpClient,
    base_url: str,
    workspace_id: str,
    status: Optional[str] = None,
    limit: Optional[int] = MAX_LIMIT,
) -> HttpResponse:
    params: dict = {"workspace_id": workspace_id, "limit": _cap(limit)}
    if status:
        params["status"] = status
    return client.get(base_url, "/api/progress", params)


def search(
    client: ReadOnlyHttpClient,
    base_url: str,
    workspace_id: str,
    query: str,
    search_type: str = "decisions",
) -> HttpResponse:
    # workspace_id is a single path segment. Although registry-owned, encode it
    # and reject path-bearing values (fail closed) so it can never alter the route.
    if "/" in workspace_id or ".." in workspace_id:
        raise ReadOnlyHttpError("invalid workspace_id (must be a single segment)")
    safe_ws = quote(workspace_id, safe="")
    return client.get(
        base_url,
        f"/api/search/{safe_ws}",
        {"q": query, "type": search_type},
    )
