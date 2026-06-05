"""Phase-1 tool implementations (pure; no MCP dependency).

Each function takes a loaded ``Registry`` and returns a canonical envelope.
Project-scoped tools resolve the project first (fail-closed) and confine all
reads to the resolved workspace. All ``data`` is redacted before return.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

_MAX_FILTER_LEN = 128

from . import envelope as E
from . import gitstate, proofs
from .redaction import redact_value
from .registry import Registry
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
