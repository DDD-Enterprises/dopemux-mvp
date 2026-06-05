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
from . import dope_memory as dope_memory_adapter
from . import envelope as E
from . import gitstate, proofs
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
        fetch = lambda: conport_adapter.search(c, base_url, ws_id, q, "decisions")
    else:
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
