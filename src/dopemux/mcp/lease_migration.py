"""Migrate legacy hash-only envrc ports into the lease registry when safe."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

from .envrc import load_envrc, safe_port_int
from .port_allocator import (
    AllocatorIdentity,
    allocate_ports,
    instance_id_for_path,
    preferred_port_for_path,
)
from .port_leases import PortLeaseRegistry, default_lease_registry_path


def migrate_envrc_to_leases(
    repo: Path | str,
    catalog: Mapping[str, Any],
    *,
    service_names: Optional[Sequence[str]] = None,
    project_root: Optional[str] = None,
    registry_path: Optional[Path] = None,
    persist: bool = True,
    dry_run: bool = False,
    is_free_fn=None,
) -> Dict[str, Any]:
    """Import envrc ports as preferred values and acquire leases.

    Returns a report dict with status, ports, warnings, rebinds.
    """
    repo_path = Path(repo).expanduser().resolve()
    envrc = load_envrc(repo_path / ".envrc.dopemux-mcp")
    env_values = dict(envrc.values) if envrc.present else {}

    names = list(
        service_names
        or (catalog.get("defaults") or {}).get("per_worktree")
        or []
    )
    proj = str(Path(project_root or repo_path).expanduser().resolve())
    wt = str(repo_path)
    wt_hash = instance_id_for_path(wt)

    identity = AllocatorIdentity(
        project_id=Path(proj).name,
        workspace_id=env_values.get("DOPEMUX_WORKSPACE_ID") or wt,
        project_root=proj,
        worktree_root=wt,
        project_hash=None,
        worktree_hash=env_values.get("DOPEMUX_INSTANCE_ID") or wt_hash,
        instance_id=env_values.get("DOPEMUX_INSTANCE_ID") or wt_hash,
    )

    warnings: List[Dict[str, Any]] = []
    if not envrc.present:
        warnings.append(
            {
                "code": "LEGACY_ENVRC_WITHOUT_LEASE",
                "message": "No .envrc.dopemux-mcp; allocator will create fresh leases.",
            }
        )
    else:
        warnings.append(
            {
                "code": "LEGACY_HASH_ALLOCATOR_MIGRATED",
                "message": "Migrating envrc ports through lease allocator.",
            }
        )

    result = allocate_ports(
        names,
        catalog,
        worktree=wt,
        project_root=proj,
        identity=identity,
        existing_envrc=env_values,
        registry_path=registry_path or default_lease_registry_path(),
        persist=persist and not dry_run,
        dry_run=dry_run,
        source="dopemux mcp migration",
        is_free_fn=is_free_fn,
    )
    report = result.to_dict()
    report["warnings"] = warnings + list(result.warnings)
    report["envrc_present"] = envrc.present
    report["legacy_ports"] = {
        k: safe_port_int(env_values, k)
        for k in env_values
        if k.endswith("_PORT") or k.endswith("_PORTS")
    }
    return report


def formula_preferred_ports(
    worktree: str,
    service_names: Sequence[str],
    catalog: Mapping[str, Any],
    *,
    project_root: Optional[str] = None,
) -> Dict[str, int]:
    """Compute pure preferred formula ports (no lease, no rebind)."""
    from .port_allocator import build_role_requests

    reqs = build_role_requests(
        service_names,
        catalog,
        worktree=worktree,
        project_root=project_root,
    )
    return {r.port_var: int(r.preferred or r.base) for r in reqs}
