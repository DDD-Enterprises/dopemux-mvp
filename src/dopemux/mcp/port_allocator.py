"""Unified MCP port allocator with lease registry + live rebind.

Replaces hash-only policy as the runtime assignment authority while still
using hash-derived ports as *preferred* candidates when safe.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple
from urllib.parse import urlparse

from .port_leases import (
    PortLease,
    PortLeaseRegistry,
    default_lease_registry_path,
    make_lease_id,
)
from .socket_probe import port_is_free

# Default search window beyond base when rebinding
DEFAULT_SEARCH_SPAN = 100


def preferred_port_for_path(worktree_path: str, base_port: int) -> int:
    """Legacy preferred formula: base + sha1(abspath)[:4] % 100."""
    offset = int(
        hashlib.sha1(str(Path(worktree_path).resolve()).encode("utf-8")).hexdigest()[:4],
        16,
    ) % 100
    return int(base_port) + offset


def instance_id_for_path(worktree_path: str) -> str:
    return hashlib.sha1(str(Path(worktree_path).resolve()).encode("utf-8")).hexdigest()[:4]


def singleton_reserved_ports(catalog: Mapping[str, Any]) -> Dict[int, str]:
    reserved: Dict[int, str] = {}
    for name, spec in (catalog.get("servers") or {}).items():
        if not isinstance(spec, dict) or spec.get("scope") != "singleton":
            continue
        explicit = spec.get("reserved_port")
        if explicit is not None:
            try:
                reserved[int(explicit)] = name
            except (TypeError, ValueError):
                pass
        raw_url = spec.get("url")
        if raw_url:
            try:
                port = urlparse(str(raw_url)).port
                if port:
                    reserved[port] = name
            except Exception:  # noqa: BLE001
                pass
    return reserved


@dataclass
class PortRoleRequest:
    service: str
    port_role: str
    port_var: str
    base: int
    fixed: bool = False
    scope: str = "worktree"  # worktree | project | singleton
    preferred: Optional[int] = None


@dataclass
class AllocationResult:
    status: str  # ASSIGNED|REUSED|REBIND|BLOCKED|UNKNOWN
    ports: Dict[str, int] = field(default_factory=dict)  # port_var -> port
    leases: List[Dict[str, Any]] = field(default_factory=list)
    rebinds: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    blocking_findings: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "ports": dict(self.ports),
            "leases": list(self.leases),
            "rebinds": list(self.rebinds),
            "warnings": list(self.warnings),
            "blocking_findings": list(self.blocking_findings),
        }


def _role_from_var(port_var: str, service: str) -> str:
    upper = port_var.upper()
    if "INFO" in upper:
        return "info"
    if "HTTP" in upper and "MCP" not in upper:
        return "http"
    if "MCP" in upper or upper.endswith("_PORT"):
        # primary MCP port: sse for conport-ish, http otherwise
        if service == "conport" and "HTTP" not in upper:
            return "sse"
        return "http"
    return "http"


def build_role_requests(
    service_names: Sequence[str],
    catalog: Mapping[str, Any],
    *,
    worktree: str,
    project_root: Optional[str] = None,
    existing_envrc: Optional[Mapping[str, str]] = None,
) -> List[PortRoleRequest]:
    """Expand catalog services into port-role allocation requests."""
    reqs: List[PortRoleRequest] = []
    env = existing_envrc or {}
    for name in service_names:
        spec = (catalog.get("servers") or {}).get(name) or {}
        if not isinstance(spec, dict) or spec.get("scope") != "per-worktree":
            continue
        is_fixed = spec.get("management_model") == "wrapper-singleton"
        key_path = (
            project_root
            if spec.get("state_scope") == "per-repo" and project_root
            else worktree
        )
        scope = "project" if spec.get("state_scope") == "per-repo" else "worktree"
        base = spec.get("default_port_base")
        port_var = spec.get("port_var")
        if base and port_var:
            pref = preferred_port_for_path(str(key_path), int(base)) if not is_fixed else int(base)
            if str(port_var) in env:
                try:
                    pref = int(str(env[str(port_var)]).strip())
                except ValueError:
                    pass
            reqs.append(
                PortRoleRequest(
                    service=str(name),
                    port_role=_role_from_var(str(port_var), str(name)),
                    port_var=str(port_var),
                    base=int(base),
                    fixed=is_fixed,
                    scope=scope,
                    preferred=pref,
                )
            )
        if not is_fixed:
            for extra in spec.get("extra_port_vars") or []:
                if not isinstance(extra, dict):
                    continue
                var = extra.get("var")
                ebase = extra.get("base")
                if not var or ebase is None:
                    continue
                pref = preferred_port_for_path(str(key_path), int(ebase))
                if str(var) in env:
                    try:
                        pref = int(str(env[str(var)]).strip())
                    except ValueError:
                        pass
                reqs.append(
                    PortRoleRequest(
                        service=str(name),
                        port_role=_role_from_var(str(var), str(name)),
                        port_var=str(var),
                        base=int(ebase),
                        fixed=False,
                        scope=scope,
                        preferred=pref,
                    )
                )
    return reqs


def _candidate_ports(preferred: int, base: int, *, span: int = DEFAULT_SEARCH_SPAN) -> List[int]:
    """Deterministic search order: preferred, then base..base+span, then preferred±."""
    seen = set()
    out: List[int] = []

    def add(p: int) -> None:
        if 1 <= p <= 65535 and p not in seen:
            seen.add(p)
            out.append(p)

    add(int(preferred))
    for p in range(int(base), int(base) + span + 1):
        add(p)
    # widen slightly around preferred if base range exhausted
    for delta in range(1, span + 1):
        add(int(preferred) + delta)
        add(int(preferred) - delta)
    return out


@dataclass
class AllocatorIdentity:
    project_id: Optional[str]
    workspace_id: Optional[str]
    project_root: str
    worktree_root: str
    project_hash: Optional[str]
    worktree_hash: str
    instance_id: str


def allocate_ports(
    service_names: Sequence[str],
    catalog: Mapping[str, Any],
    *,
    worktree: str,
    project_root: Optional[str] = None,
    identity: Optional[AllocatorIdentity] = None,
    existing_envrc: Optional[Mapping[str, str]] = None,
    registry: Optional[PortLeaseRegistry] = None,
    registry_path: Optional[Path] = None,
    persist: bool = True,
    dry_run: bool = False,
    source: str = "dopemux mcp init",
    is_free_fn: Optional[Callable[[int], bool]] = None,
    extra_blocked_ports: Optional[Mapping[int, str]] = None,
) -> AllocationResult:
    """Allocate ports for services with lease + live socket safety.

    ``persist=False`` or ``dry_run=True`` skips registry writes.
    """
    is_free = is_free_fn or (lambda p: port_is_free(p))
    wt = str(Path(worktree).expanduser().resolve())
    proj = str(Path(project_root or worktree).expanduser().resolve())
    wt_hash = instance_id_for_path(wt)
    if identity is None:
        identity = AllocatorIdentity(
            project_id=Path(proj).name,
            workspace_id=wt,
            project_root=proj,
            worktree_root=wt,
            project_hash=None,
            worktree_hash=wt_hash,
            instance_id=wt_hash,
        )

    result = AllocationResult(status="ASSIGNED")

    # Load registry
    if registry is None:
        path = registry_path or default_lease_registry_path()
        registry = PortLeaseRegistry.load(path)
    if registry.parse_status == "ERROR":
        result.status = "BLOCKED"
        result.blocking_findings.append(
            {
                "code": "LEASE_REGISTRY_PARSE_ERROR",
                "message": f"Lease registry unreadable: {registry.error}",
                "path": str(registry.path),
            }
        )
        return result

    if registry.parse_status == "MISSING":
        result.warnings.append(
            {
                "code": "LEASE_REGISTRY_MISSING",
                "message": f"No lease registry yet at {registry.path}; will create on first write.",
            }
        )
    else:
        result.warnings.append(
            {
                "code": "LEASE_REGISTRY_FOUND",
                "message": f"Using lease registry {registry.path}",
            }
        )

    reserved = singleton_reserved_ports(catalog)
    registry.set_reserved_from_catalog(reserved)

    blocked: Dict[int, str] = {p: f"singleton:{n}" for p, n in reserved.items()}
    if extra_blocked_ports:
        blocked.update({int(k): str(v) for k, v in extra_blocked_ports.items()})

    # Seed blocked with other projects' active leases
    for L in registry.active_leases():
        port = int(L.get("port") or 0)
        if not port:
            continue
        same = registry.identity_matches(
            L,
            worktree_root=identity.worktree_root,
            project_root=identity.project_root,
            worktree_hash=identity.worktree_hash,
            project_id=identity.project_id,
        )
        if not same:
            blocked[port] = (
                f"lease:{L.get('service')}:{L.get('worktree_root') or L.get('project_root')}"
            )

    plan_ports: Dict[int, str] = {}  # port -> owner key in this allocation
    reqs = build_role_requests(
        service_names,
        catalog,
        worktree=wt,
        project_root=proj,
        existing_envrc=existing_envrc,
    )

    for req in reqs:
        preferred = int(req.preferred if req.preferred is not None else req.base)
        assigned: Optional[int] = None
        status_local = "ASSIGNED"
        rebind_reason: Optional[str] = None

        # 1) Existing valid lease for this identity/service/role
        existing = registry.find_active_for_identity(
            service=req.service,
            port_role=req.port_role,
            worktree_root=identity.worktree_root if req.scope == "worktree" else None,
            project_root=identity.project_root if req.scope == "project" else identity.project_root,
            worktree_hash=identity.worktree_hash,
        )
        if existing:
            ep = int(existing["port"])
            if ep in plan_ports and plan_ports[ep] != f"{req.service}.{req.port_var}":
                # conflict within plan — fall through to rebind
                pass
            elif ep in blocked and not registry.identity_matches(
                existing,
                worktree_root=identity.worktree_root,
                project_root=identity.project_root,
                worktree_hash=identity.worktree_hash,
            ):
                pass
            elif is_free(ep) or registry.identity_matches(
                existing,
                worktree_root=identity.worktree_root,
                project_root=identity.project_root,
                worktree_hash=identity.worktree_hash,
            ):
                # Reuse lease if free OR still ours (may be running)
                other = registry.find_active_by_port(ep)
                if other and not registry.identity_matches(
                    other,
                    worktree_root=identity.worktree_root,
                    project_root=identity.project_root,
                    worktree_hash=identity.worktree_hash,
                ):
                    pass
                else:
                    assigned = ep
                    status_local = "REUSED"
                    result.warnings.append(
                        {
                            "code": "LEASE_REUSED",
                            "service": req.service,
                            "port_role": req.port_role,
                            "port": ep,
                        }
                    )

        if assigned is None and req.fixed:
            # Fixed-port services: never rebind
            cand = preferred
            conflict = blocked.get(cand) or plan_ports.get(cand)
            other = registry.find_active_by_port(cand)
            other_ok = True
            if other and not registry.identity_matches(
                other,
                worktree_root=identity.worktree_root,
                project_root=identity.project_root,
                worktree_hash=identity.worktree_hash,
            ):
                other_ok = False
            free = is_free(cand)
            if conflict or not other_ok:
                result.status = "BLOCKED"
                result.blocking_findings.append(
                    {
                        "code": "ALLOCATOR_FIXED_PORT_BLOCKED",
                        "service": req.service,
                        "port": cand,
                        "message": (
                            f"Fixed port {cand} for {req.service} is blocked "
                            f"({conflict or 'foreign lease'})."
                        ),
                    }
                )
                return result
            if not free and not other_ok:
                result.status = "BLOCKED"
                result.blocking_findings.append(
                    {
                        "code": "LEASE_PORT_OCCUPIED",
                        "service": req.service,
                        "port": cand,
                        "message": f"Fixed port {cand} occupied by unknown process.",
                    }
                )
                return result
            assigned = cand
            status_local = "REUSED" if other else "ASSIGNED"
            result.warnings.append(
                {
                    "code": "ALLOCATOR_FIXED_PORT_REUSED" if other else "ALLOCATOR_ASSIGNED_PREFERRED",
                    "service": req.service,
                    "port": cand,
                }
            )
        elif assigned is None:
            # Search candidates
            for cand in _candidate_ports(preferred, req.base):
                if cand in reserved:
                    if cand == preferred:
                        rebind_reason = rebind_reason or "PORT_RESERVED_COLLISION"
                    continue
                if cand in blocked:
                    if cand == preferred:
                        rebind_reason = rebind_reason or "LEASE_BELONGS_TO_OTHER_PROJECT"
                    continue
                if cand in plan_ports:
                    if cand == preferred:
                        rebind_reason = rebind_reason or "ALLOCATOR_CROSS_SERVICE_COLLISION_AVOIDED"
                    continue
                other = registry.find_active_by_port(cand)
                if other and not registry.identity_matches(
                    other,
                    worktree_root=identity.worktree_root,
                    project_root=identity.project_root,
                    worktree_hash=identity.worktree_hash,
                ):
                    if cand == preferred:
                        rebind_reason = rebind_reason or "LEASE_BELONGS_TO_OTHER_WORKTREE"
                    continue
                if not is_free(cand):
                    # occupied — only ok if our lease
                    if other and registry.identity_matches(
                        other,
                        worktree_root=identity.worktree_root,
                        project_root=identity.project_root,
                        worktree_hash=identity.worktree_hash,
                    ):
                        assigned = cand
                        status_local = "REUSED"
                        break
                    if cand == preferred:
                        rebind_reason = rebind_reason or "LEASE_PORT_OCCUPIED"
                    continue
                assigned = cand
                if cand == preferred:
                    status_local = "ASSIGNED"
                    result.warnings.append(
                        {
                            "code": "ALLOCATOR_ASSIGNED_PREFERRED",
                            "service": req.service,
                            "port_role": req.port_role,
                            "port": cand,
                        }
                    )
                else:
                    status_local = "REBIND"
                    rebind_reason = rebind_reason or "ALLOCATOR_REBOUND_FROM_PREFERRED"
                break

        if assigned is None:
            result.status = "BLOCKED"
            result.blocking_findings.append(
                {
                    "code": "ALLOCATOR_NO_SAFE_PORT",
                    "service": req.service,
                    "port_role": req.port_role,
                    "port_var": req.port_var,
                    "preferred": preferred,
                    "message": f"No safe port for {req.service}.{req.port_var} near base {req.base}.",
                }
            )
            return result

        if status_local == "REBIND" or (assigned != preferred and not req.fixed):
            result.rebinds.append(
                {
                    "role": req.port_role,
                    "service": req.service,
                    "port_var": req.port_var,
                    "preferred": preferred,
                    "assigned": assigned,
                    "reason": rebind_reason or "ALLOCATOR_REBOUND_FROM_PREFERRED",
                }
            )
            result.warnings.append(
                {
                    "code": "LEASE_REBOUND",
                    "service": req.service,
                    "preferred": preferred,
                    "assigned": assigned,
                    "reason": rebind_reason,
                }
            )
            if result.status not in {"BLOCKED"}:
                result.status = "REBIND"

        plan_ports[assigned] = f"{req.service}.{req.port_var}"
        result.ports[req.port_var] = assigned

        lease = PortLease(
            lease_id=make_lease_id(
                project_slug=str(identity.project_id or Path(identity.project_root).name),
                worktree_hash=identity.worktree_hash,
                service=req.service,
                port_role=req.port_role,
                port=assigned,
            ),
            port=assigned,
            service=req.service,
            port_role=req.port_role,
            port_var=req.port_var,
            project_id=identity.project_id,
            workspace_id=identity.workspace_id,
            project_root=identity.project_root,
            worktree_root=identity.worktree_root,
            project_hash=identity.project_hash,
            worktree_hash=identity.worktree_hash,
            instance_id=identity.instance_id,
            scope=req.scope,
            source=source,
            status="active",
            preferred=(assigned == preferred),
            reserved=False,
            notes=[] if assigned == preferred else [f"rebound from {preferred}"],
        )
        entry = lease.to_dict()
        result.leases.append(entry)
        if not dry_run and persist:
            registry.upsert_lease(lease)

        if status_local == "ASSIGNED" and assigned == preferred:
            result.warnings.append(
                {
                    "code": "LEASE_CREATED",
                    "service": req.service,
                    "port": assigned,
                }
            )

    # Cross-worktree collision avoided summary
    if any(r.get("reason") == "LEASE_BELONGS_TO_OTHER_WORKTREE" for r in result.rebinds):
        result.warnings.append(
            {
                "code": "ALLOCATOR_CROSS_WORKTREE_COLLISION_AVOIDED",
                "message": "Rebound at least one port to avoid another worktree's lease.",
            }
        )
    if any(r.get("reason") == "ALLOCATOR_CROSS_SERVICE_COLLISION_AVOIDED" for r in result.rebinds):
        result.warnings.append(
            {
                "code": "ALLOCATOR_CROSS_SERVICE_COLLISION_AVOIDED",
                "message": "Rebound to avoid intra-plan cross-service collision.",
            }
        )

    if not dry_run and persist and result.leases:
        try:
            registry.save()
        except OSError as exc:
            result.status = "BLOCKED"
            result.blocking_findings.append(
                {
                    "code": "LEASE_REGISTRY_PARSE_ERROR",
                    "message": f"Failed to write lease registry: {exc}",
                }
            )
            return result

    if result.status not in {"BLOCKED", "REBIND"} and all(
        w.get("code") == "LEASE_REUSED" for w in result.warnings if w.get("code", "").startswith("LEASE_")
    ):
        # purely reused
        if any(w.get("code") == "LEASE_REUSED" for w in result.warnings):
            result.status = "REUSED"

    if not result.ports and not result.blocking_findings:
        result.status = "UNKNOWN"

    return result


def allocate_ports_map(
    worktree: str,
    names: Sequence[str],
    catalog: Mapping[str, Any],
    *,
    project_root: str | None = None,
    existing_envrc: Optional[Mapping[str, str]] = None,
    persist: bool = True,
    dry_run: bool = False,
    source: str = "dopemux mcp init",
    registry_path: Optional[Path] = None,
    is_free_fn: Optional[Callable[[int], bool]] = None,
) -> Dict[str, int]:
    """Drop-in replacement shape for ``_allocate_ports`` → {port_var: port}.

    Raises RuntimeError on BLOCKED (callers may convert to ClickException).
    """
    result = allocate_ports(
        names,
        catalog,
        worktree=worktree,
        project_root=project_root,
        existing_envrc=existing_envrc,
        persist=persist and not dry_run,
        dry_run=dry_run,
        source=source,
        registry_path=registry_path,
        is_free_fn=is_free_fn,
    )
    if result.status == "BLOCKED":
        msgs = "; ".join(f["message"] for f in result.blocking_findings if f.get("message"))
        raise RuntimeError(msgs or "Port allocation blocked")
    return dict(result.ports)
