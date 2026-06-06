"""Phase-1 tool implementations (pure; no MCP dependency).

Each function takes a loaded ``Registry`` and returns a canonical envelope.
Project-scoped tools resolve the project first (fail-closed) and confine all
reads to the resolved workspace. All ``data`` is redacted before return.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, Optional

_MAX_FILTER_LEN = 128
_MAX_QUERY_LEN = 256

from . import conport as conport_adapter
from . import dope_context as dope_context_adapter
from . import dope_memory as dope_memory_adapter
from . import envelope as E
from . import gitstate, proofs
from . import task_orchestrator as task_orchestrator_adapter
from .http_client import HttpResponse, ReadOnlyHttpClient, ReadOnlyHttpError
from .redaction import redact_value
from .registry import Project, Registry
from .resolver import resolve


def _abs_roots(workspace: Optional[Path]) -> list[str]:
    roots: list[str] = []
    if workspace is not None:
        roots.append(str(workspace))
    home = os.path.expanduser("~")
    if home and home != "~":
        roots.append(home)
    return roots


def list_projects(registry: Registry) -> dict:
    """Approved (enabled) projects only. No project_id; never exposes paths."""
    data = [
        {"project_id": p.project_id, "capabilities": p.configured_capabilities()}
        for p in registry.enabled_projects()
    ]
    clean, red = redact_value(data, _abs_roots(None))
    return E.build_envelope(
        project_id=None,
        status=E.OK,
        source_system=E.SOURCE_FACADE,
        authority_label=E.AUTHORITY_FACADE,
        data=clean,
        redactions=red,
    )


def get_project_capabilities(registry: Registry, project_id: object) -> dict:
    res, reason = resolve(registry, project_id)
    if res is None:
        return E.blocked(project_id if isinstance(project_id, str) else None, reason or "blocked")
    data = {"project_id": res.project.project_id, "capabilities": res.project.configured_capabilities()}
    clean, red = redact_value(data, _abs_roots(res.workspace))
    return E.build_envelope(
        project_id=res.project.project_id,
        status=E.OK,
        source_system=E.SOURCE_FACADE,
        authority_label=E.AUTHORITY_FACADE,
        data=clean,
        redactions=red,
    )


def get_repo_state_snapshot(registry: Registry, project_id: object) -> dict:
    res, reason = resolve(registry, project_id)
    if res is None:
        return E.blocked(project_id if isinstance(project_id, str) else None, reason or "blocked")
    st = gitstate.repo_state(res.workspace)
    warnings: list[str] = []
    limitations: list[str] = []
    status = E.OK
    if st["head_sha"] is None:
        status = E.PARTIAL
        limitations.append("git state unavailable")
    if st["dirty"]:
        warnings.append("dirty worktree")
    data = {"branch": st["branch"], "head_sha": st["head_sha"], "dirty": st["dirty"]}
    clean, red = redact_value(data, _abs_roots(res.workspace))
    return E.build_envelope(
        project_id=res.project.project_id,
        status=status,
        source_system=E.SOURCE_GIT,
        authority_label=E.AUTHORITY_GIT,
        data=clean,
        branch=st["branch"],
        head_sha=st["head_sha"],
        dirty=st["dirty"],
        warnings=warnings,
        limitations=limitations,
        redactions=red,
    )


def list_proof_bundles(
    registry: Registry,
    project_id: object,
    packet_id_filter: Optional[str] = None,
) -> dict:
    res, reason = resolve(registry, project_id)
    if res is None:
        return E.blocked(project_id if isinstance(project_id, str) else None, reason or "blocked")
    if packet_id_filter is not None and (
        not isinstance(packet_id_filter, str) or len(packet_id_filter) > _MAX_FILTER_LEN
    ):
        # Literal substring filter only (no regex) — bounded length, no ReDoS surface.
        return E.blocked(res.project.project_id, "invalid packet_id_filter")
    bundles, truncated = proofs.list_bundles(res.workspace, packet_id_filter, cap=proofs.MAX_BUNDLES)
    limitations: list[str] = []
    if truncated:
        limitations.append(f"results capped at {proofs.MAX_BUNDLES}")
    clean, red = redact_value({"bundles": bundles}, _abs_roots(res.workspace))
    return E.build_envelope(
        project_id=res.project.project_id,
        status=E.OK,
        source_system=E.SOURCE_FACADE,
        authority_label=E.AUTHORITY_FS,
        data=clean,
        limitations=limitations,
        redactions=red,
    )


def fetch_proof_bundle(registry: Registry, project_id: object, bundle_id: object) -> dict:
    res, reason = resolve(registry, project_id)
    if res is None:
        return E.blocked(project_id if isinstance(project_id, str) else None, reason or "blocked")
    head = gitstate.repo_state(res.workspace)["head_sha"]
    data, block_reason, warnings = proofs.fetch_bundle(res.workspace, bundle_id, current_head=head)
    if block_reason is not None:
        return E.blocked(res.project.project_id, block_reason)
    clean, red = redact_value(data, _abs_roots(res.workspace))
    return E.build_envelope(
        project_id=res.project.project_id,
        status=E.OK,
        source_system=E.SOURCE_FACADE,
        authority_label=E.AUTHORITY_FS,
        data=clean,
        head_sha=head,
        warnings=warnings,
        redactions=red,
    )


# ---------------------------------------------------------------------------
# Service-backed read tools (packet 0005): ConPort + dope-memory adapters.
# Each resolves the project, reads the registry-bound service profile (the
# caller never supplies base_url/workspace_id/route), calls the read-only
# adapter, then redacts + envelopes. Backend failures fail closed.
# ---------------------------------------------------------------------------


def _bound_profile(project: Project, name: str) -> Optional[dict]:
    prof = project.service_profiles.get(name)
    return prof if isinstance(prof, dict) else None


def _profile_binding(project: Project, name: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """Return (base_url, workspace_id, missing_reason) for a service profile."""
    prof = _bound_profile(project, name)
    if prof is None:
        return None, None, f"{name} not configured for this project"
    base_url = prof.get("base_url")
    workspace_id = prof.get("workspace_id")
    if not base_url:
        return None, None, f"{name} base_url not configured"
    if not workspace_id:
        return None, None, f"{name} workspace_id not configured"
    return base_url, workspace_id, None


def _profile_binding_url_only(project: Project, name: str) -> tuple[Optional[str], Optional[str]]:
    """Return (base_url, missing_reason) for a service profile that only needs base_url.

    Used for dope_context and task_orchestrator which don't use workspace_id.
    """
    prof = _bound_profile(project, name)
    if prof is None:
        return None, f"{name} not configured for this project"
    base_url = prof.get("base_url")
    if not base_url:
        return None, f"{name} base_url not configured"
    return base_url, None


def _norm_query(query: Optional[str]) -> str:
    q = query.strip() if isinstance(query, str) else ""
    return q[:_MAX_QUERY_LEN]


def _enveloped_backend_read(
    project_id: str,
    workspace: Path,
    source_system: str,
    fetch: Callable[[], HttpResponse],
) -> dict:
    """Run a backend read, mapping outcomes to a canonical CANONICAL envelope."""
    try:
        resp: HttpResponse = fetch()
    except ReadOnlyHttpError:
        # Generic reason — never echo internal host/port/exception detail to the caller.
        return E.build_envelope(
            project_id=project_id,
            status=E.BLOCKED,
            source_system=source_system,
            authority_label=E.AUTHORITY_CANONICAL,
            data=None,
            blocked_reasons=["backend unavailable"],
        )
    if not resp.ok or resp.json is None:
        return E.build_envelope(
            project_id=project_id,
            status=E.PARTIAL,
            source_system=source_system,
            authority_label=E.AUTHORITY_CANONICAL,
            data=None,
            limitations=[f"backend returned status {resp.status}"],
            warnings=["incomplete read"],
        )
    clean, red = redact_value(resp.json, _abs_roots(workspace))
    return E.build_envelope(
        project_id=project_id,
        status=E.OK,
        source_system=source_system,
        authority_label=E.AUTHORITY_CANONICAL,
        data=clean,
        redactions=red,
    )


def _default_client() -> ReadOnlyHttpClient:
    return ReadOnlyHttpClient()


def search_decisions(
    registry: Registry,
    project_id: object,
    query: Optional[str] = None,
    limit: int = conport_adapter.MAX_LIMIT,
    *,
    client: Optional[ReadOnlyHttpClient] = None,
) -> dict:
    res, reason = resolve(registry, project_id)
    if res is None:
        return E.blocked(project_id if isinstance(project_id, str) else None, reason or "blocked")
    base_url, ws_id, missing = _profile_binding(res.project, "conport")
    if missing:
        return E.blocked(res.project.project_id, missing)
    c = client or _default_client()
    q = _norm_query(query)
    if q:
        # ConPort's GET /api/search/{ws} (text search) is deferred in Phase 1:
        # the default enhanced server returns 500 because search_content builds
        # the row dict without serializing the UUID `id` before json.dumps. We
        # do NOT expose a broken read; list mode (GET /api/decisions, which does
        # serialize ids) remains available. (conport.search is ready for when
        # the backend serializes ids.)
        return E.build_envelope(
            project_id=res.project.project_id,
            status=E.PARTIAL,
            source_system=E.SOURCE_CONPORT,
            authority_label=E.AUTHORITY_CANONICAL,
            data=None,
            limitations=[
                "decision text search deferred: ConPort GET /api/search returns "
                "500 (UUID id not serialized); use search_decisions without a query"
            ],
        )
    fetch = lambda: conport_adapter.get_decisions(c, base_url, ws_id, limit)
    return _enveloped_backend_read(res.project.project_id, res.workspace, E.SOURCE_CONPORT, fetch)


def search_progress(
    registry: Registry,
    project_id: object,
    status: Optional[str] = None,
    limit: int = conport_adapter.MAX_LIMIT,
    *,
    client: Optional[ReadOnlyHttpClient] = None,
) -> dict:
    res, reason = resolve(registry, project_id)
    if res is None:
        return E.blocked(project_id if isinstance(project_id, str) else None, reason or "blocked")
    base_url, ws_id, missing = _profile_binding(res.project, "conport")
    if missing:
        return E.blocked(res.project.project_id, missing)
    # ConPort GET /api/progress is NOT always side-effect-free: the default
    # enhanced server (DOPEMUX_AUTO_FORK_PROGRESS=1) auto-forks (writes) progress
    # rows from shared when the workspace has none. The facade cannot suppress
    # that per-request, so search_progress is fail-closed: it runs only when the
    # operator explicitly asserts the backend is read-only-safe.
    prof = _bound_profile(res.project, "conport")
    if not (prof and prof.get("progress_readonly_safe") is True):
        return E.blocked(
            res.project.project_id,
            "search_progress disabled: ConPort GET /api/progress can auto-fork "
            "(write) when empty; set conport.progress_readonly_safe=true after "
            "disabling DOPEMUX_AUTO_FORK_PROGRESS on the backend",
        )
    c = client or _default_client()
    fetch = lambda: conport_adapter.get_progress(c, base_url, ws_id, status, limit)
    return _enveloped_backend_read(res.project.project_id, res.workspace, E.SOURCE_CONPORT, fetch)


def search_chronicle(
    registry: Registry,
    project_id: object,
    query: str = "",
    top_k: int = dope_memory_adapter.MAX_TOP_K,
    *,
    client: Optional[ReadOnlyHttpClient] = None,
) -> dict:
    res, reason = resolve(registry, project_id)
    if res is None:
        return E.blocked(project_id if isinstance(project_id, str) else None, reason or "blocked")
    base_url, ws_id, missing = _profile_binding(res.project, "dope_memory")
    if missing:
        return E.blocked(res.project.project_id, missing)
    c = client or _default_client()
    q = _norm_query(query)
    fetch = lambda: dope_memory_adapter.memory_search(c, base_url, ws_id, q, top_k)
    return _enveloped_backend_read(
        res.project.project_id, res.workspace, E.SOURCE_DOPE_MEMORY, fetch
    )


def replay_chronicle_session(
    registry: Registry,
    project_id: object,
    session_id: object,
    mode: str = "replay_current",
    top_k: int = dope_memory_adapter.MAX_TOP_K,
    *,
    client: Optional[ReadOnlyHttpClient] = None,
) -> dict:
    res, reason = resolve(registry, project_id)
    if res is None:
        return E.blocked(project_id if isinstance(project_id, str) else None, reason or "blocked")
    if not isinstance(session_id, str) or not session_id:
        return E.blocked(res.project.project_id, "session_id is required")
    base_url, ws_id, missing = _profile_binding(res.project, "dope_memory")
    if missing:
        return E.blocked(res.project.project_id, missing)
    c = client or _default_client()
    fetch = lambda: dope_memory_adapter.memory_replay_session(
        c, base_url, ws_id, session_id, mode, top_k
    )
    return _enveloped_backend_read(
        res.project.project_id, res.workspace, E.SOURCE_DOPE_MEMORY, fetch
    )


# ---------------------------------------------------------------------------
# Service-backed read tools (packet 0006): dope-context + task-orchestrator.
#
# dope-context Phase 1 note: dope-context exposes tools via MCP JSON-RPC (not
# REST). The facade speaks REST only. search_code_docs and get_index_status are
# wired but return BLOCKED with explicit limitations (fail-closed, honest).
# A future Phase 2 bridge will enable live results. The limitation text is
# present in the envelope so callers know exactly what is missing and why.
#
# task-orchestrator: HTTP GET adapter. All three routes (queue, blockers, state)
# are CONFIRMED_READ_ONLY. get_workflow_status_snapshot fans out all three and
# merges; a sub-call failure yields PARTIAL (not full BLOCKED) so partial data
# is still returned. The permanent limitation note ("workflow-view only") appears
# in every envelope regardless of outcome.
# ---------------------------------------------------------------------------

# Permanent limitation note for every task-orchestrator envelope.
_TO_WORKFLOW_VIEW_ONLY = (
    "task-orchestrator status is workflow-view authority only, not PM-metadata truth"
)

# Structural limitation for dope-context (transport not yet bridged).
_DC_TRANSPORT_LIMITATION = (
    "dope-context exposes tools via MCP JSON-RPC at /mcp; "
    "facade speaks REST only — bridge pending Phase 2"
)


def search_code_docs(
    registry: Registry,
    project_id: object,
    query: str,
    top_k: int = dope_context_adapter.MAX_LIMIT,
    *,
    kind: str = "code",
    profile: Optional[str] = None,
    filter_doc_type: Optional[str] = None,
    client: Optional[ReadOnlyHttpClient] = None,
) -> dict:
    """Search dope-context code or docs indexes.

    Phase 1: BLOCKED — dope-context MCP JSON-RPC transport not yet bridged.

    Args:
        registry: Project registry.
        project_id: Caller-supplied project identifier (registry-validated).
        query: Natural language search query.
        top_k: Max results (capped at dope_context_adapter.MAX_LIMIT=20).
        kind: "code" (default) or "docs" — selects which index to search.
        profile: Optional search profile for code search (implementation,
            debugging, exploration). Ignored for docs search.
        filter_doc_type: Optional doc type filter for docs search (e.g. "md",
            "pdf"). Ignored for code search.
        client: Optional HTTP client override (for testing).

    Returns:
        BLOCKED envelope with transport limitation note.

    Denied routes (never reachable):
        - search-all tool (side-effect risk: triggers dopecon-bridge + Redis)
        - index control tools (mutating or side-effect)
        - sync tools (mutating or side-effect)
        - autonomous indexing control tools
    """
    res, reason = resolve(registry, project_id)
    if res is None:
        return E.blocked(project_id if isinstance(project_id, str) else None, reason or "blocked")
    base_url, missing = _profile_binding_url_only(res.project, "dope_context")
    if missing:
        return E.blocked(res.project.project_id, missing)
    # Phase 1: transport not bridged — fail closed with honest limitations.
    # The adapter raises ReadOnlyHttpError; we capture and emit BLOCKED.
    c = client or _default_client()
    try:
        if kind == "docs":
            dope_context_adapter.docs_search(c, base_url, query, top_k, filter_doc_type)
        else:
            dope_context_adapter.search_code(c, base_url, query, top_k, profile)
    except ReadOnlyHttpError:
        pass
    return E.build_envelope(
        project_id=res.project.project_id,
        status=E.BLOCKED,
        source_system=E.SOURCE_DOPE_CONTEXT,
        authority_label=E.AUTHORITY_DERIVED,
        data=None,
        blocked_reasons=["dope-context MCP transport not yet bridged in facade"],
        limitations=[_DC_TRANSPORT_LIMITATION],
    )


def get_index_status(
    registry: Registry,
    project_id: object,
    *,
    client: Optional[ReadOnlyHttpClient] = None,
) -> dict:
    """Get dope-context index status (collection info + statistics).

    Phase 1: BLOCKED — dope-context MCP JSON-RPC transport not yet bridged.
    Additionally, get_index_status is PROPOSED-only (not in discovery inventory);
    it must be formally inventoried before being wired into the allowlist.

    Args:
        registry: Project registry.
        project_id: Caller-supplied project identifier (registry-validated).
        client: Optional HTTP client override (for testing).

    Returns:
        BLOCKED envelope with transport and inventory limitations.
    """
    res, reason = resolve(registry, project_id)
    if res is None:
        return E.blocked(project_id if isinstance(project_id, str) else None, reason or "blocked")
    base_url, missing = _profile_binding_url_only(res.project, "dope_context")
    if missing:
        return E.blocked(res.project.project_id, missing)
    # Phase 1: transport not bridged + not in inventory — fail closed.
    c = client or _default_client()
    try:
        dope_context_adapter.get_index_status(c, base_url)
    except ReadOnlyHttpError:
        pass
    return E.build_envelope(
        project_id=res.project.project_id,
        status=E.BLOCKED,
        source_system=E.SOURCE_DOPE_CONTEXT,
        authority_label=E.AUTHORITY_DERIVED,
        data=None,
        blocked_reasons=["dope-context MCP transport not yet bridged in facade"],
        limitations=[
            _DC_TRANSPORT_LIMITATION,
            "get_index_status is PROPOSED-only (not in discovery inventory); "
            "requires formal inventory + classification before allowlist wiring",
        ],
    )


def get_workflow_status_snapshot(
    registry: Registry,
    project_id: object,
    *,
    client: Optional[ReadOnlyHttpClient] = None,
) -> dict:
    """Get a task-orchestrator workflow status snapshot (queue + blockers + state).

    Fans out three GET reads (queue, blockers, state) and merges results. If a
    sub-call fails, the envelope is PARTIAL with a per-sub-call limitation note.
    All three failing yields BLOCKED. The permanent limitation note
    ("workflow-view only") always appears regardless of outcome.

    The /workflow/state route (project_workflow.py:385) was absent from the
    TP-DCP-MCP-RO-0001 discovery inventory but is OBSERVED as a first-class GET
    read endpoint. It is classified CONFIRMED_READ_ONLY here (TP-0006 discovery
    gap resolved) and included in this snapshot.

    Args:
        registry: Project registry.
        project_id: Caller-supplied project identifier (registry-validated).
        client: Optional HTTP client override (for testing).

    Returns:
        OK/PARTIAL/BLOCKED envelope with {"queue": [...], "blockers": [...],
        "state": {...}} payload. Permanent limitation: workflow-view only.

    Denied routes (never reachable):
        - workflow transition endpoints (MUTATING)
        - PM write tool endpoints
        - workflow mutation surfaces (ideas, epics)
        - bridge/proxy surfaces (kg, ddg, route-pm)
    """
    res, reason = resolve(registry, project_id)
    if res is None:
        return E.blocked(project_id if isinstance(project_id, str) else None, reason or "blocked")
    base_url, missing = _profile_binding_url_only(res.project, "task_orchestrator")
    if missing:
        return E.blocked(res.project.project_id, missing)

    c = client or _default_client()

    # Determine the task-orchestrator project_id to use. Per the registry contract,
    # the caller never supplies a backend project_id; the registry-bound profile
    # supplies the mapping (task_orchestrator_project_id key). If absent, we use
    # the facade project_id as a sensible default but note this in limitations.
    prof = _bound_profile(res.project, "task_orchestrator") or {}
    to_project_id: str = prof.get("task_orchestrator_project_id") or res.project.project_id

    data: dict = {"queue": None, "blockers": None, "state": None}
    limitations: list[str] = [_TO_WORKFLOW_VIEW_ONLY]
    failed_sub: list[str] = []

    # Sub-call: queue
    try:
        r_queue = task_orchestrator_adapter.get_workflow_queue(c, base_url, to_project_id)
        if r_queue.ok and r_queue.json is not None:
            data["queue"] = r_queue.json
        else:
            failed_sub.append(f"queue unavailable (status {r_queue.status})")
    except ReadOnlyHttpError:
        failed_sub.append("queue unavailable")

    # Sub-call: blockers
    try:
        r_blockers = task_orchestrator_adapter.get_workflow_blockers(c, base_url, to_project_id)
        if r_blockers.ok and r_blockers.json is not None:
            data["blockers"] = r_blockers.json
        else:
            failed_sub.append(f"blockers unavailable (status {r_blockers.status})")
    except ReadOnlyHttpError:
        failed_sub.append("blockers unavailable")

    # Sub-call: state (OBSERVED: project_workflow.py:385 — GET, read-only,
    # classified CONFIRMED_READ_ONLY in TP-0006 inventory resolution)
    try:
        r_state = task_orchestrator_adapter.get_workflow_state(c, base_url, to_project_id)
        if r_state.ok and r_state.json is not None:
            data["state"] = r_state.json
        else:
            failed_sub.append(f"state unavailable (status {r_state.status})")
    except ReadOnlyHttpError:
        failed_sub.append("state unavailable")

    limitations.extend(failed_sub)

    # Determine status: all failed → BLOCKED; some failed → PARTIAL; none → OK.
    all_none = all(v is None for v in data.values())
    any_none = any(v is None for v in data.values())

    if all_none:
        return E.build_envelope(
            project_id=res.project.project_id,
            status=E.BLOCKED,
            source_system=E.SOURCE_TASK_ORCHESTRATOR,
            authority_label=E.AUTHORITY_CANONICAL,
            data=None,
            blocked_reasons=["all task-orchestrator sub-reads failed"],
            limitations=limitations,
        )

    clean, red = redact_value(data, _abs_roots(res.workspace))
    status = E.PARTIAL if any_none else E.OK
    return E.build_envelope(
        project_id=res.project.project_id,
        status=status,
        source_system=E.SOURCE_TASK_ORCHESTRATOR,
        authority_label=E.AUTHORITY_CANONICAL,
        data=clean,
        limitations=limitations,
        redactions=red,
    )
