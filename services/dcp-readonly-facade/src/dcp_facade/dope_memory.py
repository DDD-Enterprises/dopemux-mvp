"""dope-memory read adapter (HTTP, :3020) — POST-read allowlist only.

The two read routes here use POST but are side-effect-free (per the inventory).
The adapter issues them ONLY via ``client.post_read(..., DOPE_MEMORY_READ_PATHS)``,
which rejects any other path — so the mutating correction route (and the
reflection / store / link routes) are structurally unreachable. ``top_k`` is
hard-capped at 3. The denied route literals live only in route_manifest + tests.
"""

from __future__ import annotations

from .http_client import HttpResponse, ReadOnlyHttpClient
from .route_manifest import DOPE_MEMORY_READ_PATHS

MAX_TOP_K = 3
_VALID_MODES = ("replay_current", "replay_full")


def _cap_top_k(top_k: object) -> int:
    if not isinstance(top_k, int) or top_k <= 0:
        return MAX_TOP_K
    return min(top_k, MAX_TOP_K)


def memory_search(
    client: ReadOnlyHttpClient,
    base_url: str,
    workspace_id: str,
    query: str = "",
    top_k: int = MAX_TOP_K,
) -> HttpResponse:
    body = {
        "query": query or "",
        "workspace_id": workspace_id,
        "top_k": _cap_top_k(top_k),
    }
    return client.post_read(base_url, "/tools/memory_search", body, DOPE_MEMORY_READ_PATHS)


def memory_replay_session(
    client: ReadOnlyHttpClient,
    base_url: str,
    workspace_id: str,
    session_id: str,
    mode: str = "replay_current",
    top_k: int = MAX_TOP_K,
) -> HttpResponse:
    safe_mode = mode if mode in _VALID_MODES else "replay_current"
    body = {
        "workspace_id": workspace_id,
        "session_id": session_id,
        "mode": safe_mode,
        "top_k": _cap_top_k(top_k),
    }
    return client.post_read(
        base_url, "/tools/memory_replay_session", body, DOPE_MEMORY_READ_PATHS
    )
