"""dope-context read adapter — Phase 1 FAIL-CLOSED stub.

# Transport decision (Phase A investigation — TP-DCP-MCP-RO-0006)
#
# OBSERVED: dope-context (services/dope-context/src/mcp/server.py) exposes its
# tools exclusively via FastMCP with @mcp.tool() decorators. When MCP_SERVER_PORT
# is set (as in the container), the FastMCP server binds HTTP but serves MCP
# JSON-RPC at /mcp — NOT REST routes. The custom-route decorators for /health
# and /info are commented out in the source. There are NO REST endpoints at
# /search/code, /search/docs, or /index/status.
#
# The facade's ReadOnlyHttpClient speaks REST (GET/POST to REST paths). It cannot
# speak MCP JSON-RPC. Implementing an MCP JSON-RPC client is materially out of
# scope for Phase 1 ("minimal correct change").
#
# DECISION: Path 2 — fail-closed. The three adapter functions have correct
# signatures but raise ReadOnlyHttpError("dope-context MCP transport not yet
# bridged in facade") immediately. The tools.py layer intercepts this and emits
# an honest BLOCKED envelope with explicit limitations. This is consistent with
# the architecture's fail-closed posture (§16) and the TP invariant
# "Unavailable backend returns PARTIAL/BLOCKED."
#
# A future Path 1 implementation will replace the raise with a real MCP
# JSON-RPC client once the transport bridge exists.

Phase 1 Phase-1 dope-context hits are labelled DERIVED (not CANONICAL) until
exact-source fetch is implemented. search_all is DENIED (side-effect risk:
triggers dopecon-bridge call + Redis operations).

DENIED routes (never reachable from this adapter):
  - search_all (side-effect: calls dopecon-bridge + Redis)
  - index_workspace, index_docs, clear_index (mutating)
  - sync_workspace, sync_docs (mutating/side-effect)
  - start_autonomous_indexing, stop_autonomous_indexing (control)
  - start_autonomous_docs_indexing, stop_autonomous_docs_indexing (control)
"""

from __future__ import annotations

from typing import Optional

from .http_client import HttpResponse, ReadOnlyHttpClient, ReadOnlyHttpError

MAX_LIMIT = 20

_TRANSPORT_NOT_BRIDGED = (
    "dope-context MCP transport not yet bridged in facade: "
    "dope-context serves MCP JSON-RPC at /mcp (not REST); "
    "facade speaks REST only — bridge pending Phase 2"
)


def _cap(limit: Optional[int]) -> int:
    if not isinstance(limit, int) or limit <= 0:
        return MAX_LIMIT
    return min(limit, MAX_LIMIT)


def _validate_query(query: object) -> str:
    if not isinstance(query, str) or len(query.strip()) == 0:
        raise ReadOnlyHttpError("query must be a non-empty string")
    return query.strip()


def _validate_profile(profile: Optional[str]) -> Optional[str]:
    """Validate search profile enum (if provided)."""
    if profile is None:
        return None
    valid_profiles = ("implementation", "debugging", "exploration")
    if not isinstance(profile, str) or profile not in valid_profiles:
        raise ReadOnlyHttpError(f"profile must be one of {valid_profiles}")
    return profile


def _validate_filter(filter_str: Optional[str], filter_name: str) -> Optional[str]:
    """Validate optional filter string (e.g., filter_doc_type, filter_language)."""
    if filter_str is None:
        return None
    if not isinstance(filter_str, str) or len(filter_str.strip()) == 0:
        raise ReadOnlyHttpError(f"{filter_name} must be a non-empty string or None")
    return filter_str.strip()


def search_code(
    client: ReadOnlyHttpClient,
    base_url: str,
    query: str,
    top_k: Optional[int] = MAX_LIMIT,
    profile: Optional[str] = None,
) -> HttpResponse:
    """Search indexed code with hybrid dense + sparse search.

    Phase 1 FAIL-CLOSED: raises ReadOnlyHttpError because dope-context exposes
    tools via MCP JSON-RPC (not REST). The tools.py layer maps this to a BLOCKED
    envelope with explicit limitations.

    Args:
        client: Read-only HTTP client (unused in Phase 1 — fail-closed).
        base_url: dope-context service base URL (registry-owned).
        query: Natural language search query.
        top_k: Max results (capped at MAX_LIMIT=20).
        profile: Optional search profile (implementation, debugging, exploration).

    Raises:
        ReadOnlyHttpError: Always in Phase 1 (transport not yet bridged).
    """
    # Validate parameters first (so callers get useful errors even in Phase 1).
    _validate_query(query)
    _validate_profile(profile)
    _cap(top_k)
    # Fail closed: MCP JSON-RPC transport not yet bridged.
    raise ReadOnlyHttpError(_TRANSPORT_NOT_BRIDGED)


def docs_search(
    client: ReadOnlyHttpClient,
    base_url: str,
    query: str,
    top_k: Optional[int] = MAX_LIMIT,
    filter_doc_type: Optional[str] = None,
) -> HttpResponse:
    """Search indexed documents (PDF, Markdown, HTML, text).

    Phase 1 FAIL-CLOSED: raises ReadOnlyHttpError because dope-context exposes
    tools via MCP JSON-RPC (not REST). The tools.py layer maps this to a BLOCKED
    envelope with explicit limitations.

    Args:
        client: Read-only HTTP client (unused in Phase 1 — fail-closed).
        base_url: dope-context service base URL (registry-owned).
        query: Natural language search query.
        top_k: Max results (capped at MAX_LIMIT=20).
        filter_doc_type: Optional filter (e.g., "md", "pdf", "html").

    Raises:
        ReadOnlyHttpError: Always in Phase 1 (transport not yet bridged).
    """
    _validate_query(query)
    _validate_filter(filter_doc_type, "filter_doc_type")
    _cap(top_k)
    raise ReadOnlyHttpError(_TRANSPORT_NOT_BRIDGED)


def get_index_status(
    client: ReadOnlyHttpClient,
    base_url: str,
) -> HttpResponse:
    """Get status of code/doc indexes (health snapshot).

    Phase 1 FAIL-CLOSED: raises ReadOnlyHttpError because dope-context exposes
    tools via MCP JSON-RPC (not REST). The tools.py layer maps this to a BLOCKED
    envelope with explicit limitations.

    NOTE: get_index_status is also PROPOSED-only in the tool contract (not in the
    discovery inventory); it must be formally inventoried before being wired into
    the allowlist (TOOL_CONTRACT.md §1c warning).

    Args:
        client: Read-only HTTP client (unused in Phase 1 — fail-closed).
        base_url: dope-context service base URL (registry-owned).

    Raises:
        ReadOnlyHttpError: Always in Phase 1 (transport not yet bridged).
    """
    raise ReadOnlyHttpError(_TRANSPORT_NOT_BRIDGED)
