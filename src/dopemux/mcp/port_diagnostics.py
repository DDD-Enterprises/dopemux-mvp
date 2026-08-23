"""Port allocation diagnostics for MCP doctor (read-only).

Recognizes the current sha1_abs_path_mod_100 allocator used by
`dopemux mcp init` (`_port_for` / `_allocate_ports`) and reports collision
risks without mutating allocation or rebinding ports.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple
from urllib.parse import urlparse


ALLOCATOR_NAME = "sha1_abs_path_mod_100"
BUCKET_COUNT = 100


@dataclass
class PortCollision:
    kind: str  # reserved | intra_config | cross_service
    port: int
    owners: List[str]
    message: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": self.kind,
            "port": self.port,
            "owners": list(self.owners),
            "message": self.message,
        }


@dataclass
class PortDiagnosticsReport:
    allocator: str
    offset: Optional[int]
    bucket_count: int
    reserved_ports_checked: List[int]
    expected_ports: Dict[str, int]  # var -> port
    collisions: List[PortCollision] = field(default_factory=list)
    risk_notes: List[str] = field(default_factory=list)
    findings: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allocator": self.allocator,
            "offset": self.offset,
            "bucket_count": self.bucket_count,
            "reserved_ports_checked": list(self.reserved_ports_checked),
            "collisions": [c.to_dict() for c in self.collisions],
            "risk_notes": list(self.risk_notes),
            "expected_ports": dict(self.expected_ports),
        }


def instance_id_for_path(worktree_path: str) -> str:
    """Match mcp_commands._instance_id: sha1(abspath)[:4]."""
    from pathlib import Path

    return hashlib.sha1(str(Path(worktree_path).resolve()).encode("utf-8")).hexdigest()[:4]


def offset_for_path(worktree_path: str) -> int:
    """Match mcp_commands._port_for offset: int(sha1[:4], 16) % 100."""
    return int(instance_id_for_path(worktree_path), 16) % BUCKET_COUNT


def port_for_base(worktree_path: str, base_port: int) -> int:
    """Match mcp_commands._port_for."""
    return base_port + offset_for_path(worktree_path)


def singleton_reserved_ports(catalog: Mapping[str, Any]) -> Dict[int, str]:
    """Mirror mcp_commands._singleton_reserved_ports without click/logging."""
    reserved: Dict[int, str] = {}
    for name, spec in (catalog.get("servers") or {}).items():
        if not isinstance(spec, dict):
            continue
        if spec.get("scope") != "singleton":
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
            except Exception:  # noqa: BLE001 — diagnostic only
                pass
    return reserved


def compute_expected_ports(
    worktree_path: str,
    service_names: Sequence[str],
    catalog: Mapping[str, Any],
    *,
    project_root: Optional[str] = None,
    env_ports: Optional[Mapping[str, int]] = None,
) -> Dict[str, int]:
    """
    Compute expected ports using the same rules as `_allocate_ports`.

    If env_ports is provided (from loaded .envrc), those values win for
    reporting "configured" ports; formula ports are still computed for
    collision analysis of the pure-hash path.
    """
    assignments: Dict[str, int] = {}
    for name in service_names:
        spec = (catalog.get("servers") or {}).get(name) or {}
        if not isinstance(spec, dict):
            continue
        if spec.get("scope") != "per-worktree":
            continue
        is_wrapper_singleton = spec.get("management_model") == "wrapper-singleton"
        key_path = (
            project_root
            if spec.get("state_scope") == "per-repo" and project_root
            else worktree_path
        )
        base = spec.get("default_port_base")
        port_var = spec.get("port_var")
        if base and port_var:
            port = int(base) if is_wrapper_singleton else port_for_base(str(key_path), int(base))
            assignments[port_var] = port
        if not is_wrapper_singleton:
            for extra in spec.get("extra_port_vars") or []:
                if not isinstance(extra, dict):
                    continue
                var = extra.get("var")
                ebase = extra.get("base")
                if var and ebase is not None:
                    assignments[str(var)] = port_for_base(str(key_path), int(ebase))

    if env_ports:
        # Overlay configured env ports for reporting
        for k, v in env_ports.items():
            assignments[k] = int(v)
    return assignments


def formula_ports_only(
    worktree_path: str,
    service_names: Sequence[str],
    catalog: Mapping[str, Any],
    *,
    project_root: Optional[str] = None,
) -> Dict[str, int]:
    """Pure formula ports (ignores env overrides)."""
    return compute_expected_ports(
        worktree_path,
        service_names,
        catalog,
        project_root=project_root,
        env_ports=None,
    )


def diagnose_ports(
    worktree_path: str,
    service_names: Sequence[str],
    catalog: Mapping[str, Any],
    *,
    project_root: Optional[str] = None,
    configured_ports: Optional[Mapping[str, int]] = None,
    has_lease_registry: bool = False,
    has_live_rebind: bool = False,
) -> PortDiagnosticsReport:
    """
    Produce port diagnostics and finding dicts for doctor.

    `configured_ports` = ports from envrc (if any). Formula collisions are
    always evaluated on pure-hash allocation for the path so reserved
    collisions are visible even when operators hand-picked safe ports.
    """
    offset = offset_for_path(worktree_path)
    reserved = singleton_reserved_ports(catalog)
    formula = formula_ports_only(
        worktree_path, service_names, catalog, project_root=project_root
    )
    configured = dict(configured_ports or formula)

    report = PortDiagnosticsReport(
        allocator=ALLOCATOR_NAME,
        offset=offset,
        bucket_count=BUCKET_COUNT,
        reserved_ports_checked=sorted(reserved.keys()),
        expected_ports=configured,
    )

    # --- Reserved singleton collisions (formula + configured) ---
    for source_label, port_map in (("formula", formula), ("configured", configured)):
        for var, port in port_map.items():
            if port in reserved:
                owner = reserved[port]
                col = PortCollision(
                    kind="reserved",
                    port=port,
                    owners=[f"{var}@{source_label}", f"singleton:{owner}"],
                    message=(
                        f"{var}={port} ({source_label}) collides with reserved "
                        f"singleton port for `{owner}`"
                    ),
                )
                # Dedupe by (kind, port, var)
                if not any(
                    c.kind == col.kind and c.port == col.port and var in c.owners[0]
                    for c in report.collisions
                ):
                    report.collisions.append(col)
                # Formula reserved ports are informational once envrc supplies a
                # different non-reserved value for the same var. Configured
                # reserved collisions stay FAIL. Pure-formula (no envrc) stays FAIL.
                neutralized = False
                if (
                    source_label == "formula"
                    and configured_ports is not None
                    and var in configured_ports
                    and int(configured_ports[var]) not in reserved
                ):
                    neutralized = True
                report.findings.append(
                    {
                        "code": "PORT_RESERVED_COLLISION",
                        "severity": "WARN" if neutralized else "FAIL",
                        "service": _service_for_var(var, catalog),
                        "message": col.message,
                        "evidence": [
                            f"port={port}",
                            f"var={var}",
                            f"singleton={owner}",
                            f"source={source_label}",
                            *(["neutralized=configured"] if neutralized else []),
                        ],
                        "recommendation": (
                            "Configured envrc ports already avoid this reserved singleton. "
                            "Formula collision is informational. Run `dopemux mcp start` "
                            "if services are down."
                            if neutralized
                            else (
                                "Adjust default_port_base spacing in mcp_catalog.yaml, "
                                "or implement preferred-port + lease allocation in a later packet. "
                                "Do not start services on reserved singleton ports."
                            )
                        ),
                    }
                )

    # --- Intra-config collisions (configured map) ---
    reverse: Dict[int, List[str]] = {}
    for var, port in configured.items():
        reverse.setdefault(port, []).append(var)
    for port, vars_ in reverse.items():
        if len(vars_) > 1:
            col = PortCollision(
                kind="intra_config",
                port=port,
                owners=vars_,
                message=f"Intra-config collision: {', '.join(vars_)} all map to :{port}",
            )
            report.collisions.append(col)
            report.findings.append(
                {
                    "code": "PORT_INTRA_CONFIG_COLLISION",
                    "severity": "FAIL",
                    "service": None,
                    "message": col.message,
                    "evidence": [f"port={port}", f"vars={vars_}"],
                    "recommendation": "Regenerate ports after fixing catalog base ports; do not share host ports across services.",
                }
            )

    # --- Cross-service formula collisions across different services ---
    # Same as intra but attributed when different services' formula ports collide
    # (already covered by reverse map if configured==formula). Explicitly check
    # formula-only map for distinct services.
    formula_reverse: Dict[int, List[str]] = {}
    for var, port in formula.items():
        formula_reverse.setdefault(port, []).append(var)
    for port, vars_ in formula_reverse.items():
        services = {_service_for_var(v, catalog) for v in vars_}
        services.discard(None)
        if len(vars_) > 1 and len(services) > 1:
            # Only emit if not already recorded as intra_config for same port
            if not any(c.kind == "intra_config" and c.port == port for c in report.collisions):
                col = PortCollision(
                    kind="cross_service",
                    port=port,
                    owners=vars_,
                    message=(
                        f"Cross-service formula collision: {', '.join(vars_)} "
                        f"({', '.join(sorted(s for s in services if s))}) → :{port}"
                    ),
                )
                report.collisions.append(col)
                report.findings.append(
                    {
                        "code": "PORT_CROSS_SERVICE_COLLISION",
                        "severity": "FAIL",
                        "service": None,
                        "message": col.message,
                        "evidence": [f"port={port}", f"vars={vars_}"],
                        "recommendation": "Adjust default_port_base values so hash offsets cannot alias across services.",
                    }
                )
            else:
                # Also tag as cross-service when multiple services share port
                report.findings.append(
                    {
                        "code": "PORT_CROSS_SERVICE_COLLISION",
                        "severity": "FAIL",
                        "service": None,
                        "message": (
                            f"Cross-service collision at :{port}: "
                            f"{', '.join(sorted(s for s in services if s))}"
                        ),
                        "evidence": [f"port={port}", f"vars={vars_}"],
                        "recommendation": "Adjust default_port_base values so hash offsets cannot alias across services.",
                    }
                )

    # --- Birthday-risk warning for %100 buckets ---
    if not has_lease_registry:
        note = (
            "Current hash allocator has only 100 offset buckets and no proven "
            "cross-worktree lease registry. Collision risk increases quickly as "
            "concurrent repos/worktrees grow. This is a warning in Packet 001 and "
            "must be fixed in a later lifecycle packet."
        )
        report.risk_notes.append(note)
        report.findings.append(
            {
                "code": "PORT_HASH_BUCKET_COLLISION_RISK",
                "severity": "WARN",
                "service": None,
                "message": note,
                "evidence": [
                    f"allocator={ALLOCATOR_NAME}",
                    f"bucket_count={BUCKET_COUNT}",
                    "lease_registry=absent",
                ],
                "recommendation": (
                    "Implement cross-worktree port lease registry and/or widen "
                    "hash modulus in a later lifecycle packet."
                ),
            }
        )

    # --- Live free-port rebind missing ---
    if not has_live_rebind:
        report.findings.append(
            {
                "code": "PORT_REBIND_MISSING",
                "severity": "WARN",
                "service": None,
                "message": (
                    "Allocator hard-fails on intra/reserved collisions or writes "
                    "config without live free-port rebind; no preferred-port + probe "
                    "+ lease path is wired into mcp init."
                ),
                "evidence": [
                    "live_rebind=false",
                    "init_allocator=_allocate_ports",
                ],
                "recommendation": (
                    "Implement preferred-port + probe + lease allocation in a later packet."
                ),
            }
        )

    # Expected ports as INFO-level findings for each configured port
    for var, port in sorted(configured.items()):
        report.findings.append(
            {
                "code": "PORT_EXPECTED",
                "severity": "INFO",
                "service": _service_for_var(var, catalog),
                "message": f"{var} expected/configured as {port}",
                "evidence": [f"var={var}", f"port={port}"],
                "recommendation": "",
            }
        )

    return report


def _service_for_var(var: str, catalog: Mapping[str, Any]) -> Optional[str]:
    for name, spec in (catalog.get("servers") or {}).items():
        if not isinstance(spec, dict):
            continue
        if spec.get("port_var") == var:
            return name
        for extra in spec.get("extra_port_vars") or []:
            if isinstance(extra, dict) and extra.get("var") == var:
                return name
    return None


def ports_listening_check(
    ports: Mapping[str, int],
    *,
    is_free_fn,
) -> List[Dict[str, Any]]:
    """
    Emit PORT_LISTENING / PORT_NOT_LISTENING findings.

    Ownership is NOT asserted here — listening alone is never PASS for ownership.
    """
    findings: List[Dict[str, Any]] = []
    for var, port in sorted(ports.items()):
        try:
            free = is_free_fn(port)
        except Exception as exc:  # noqa: BLE001
            findings.append(
                {
                    "code": "PORT_OWNERSHIP_UNKNOWN",
                    "severity": "UNKNOWN",
                    "service": None,
                    "message": f"Could not probe :{port} ({var}): {exc}",
                    "evidence": [f"var={var}", f"port={port}"],
                    "recommendation": "Retry doctor when network stack is available.",
                }
            )
            continue
        listening = not free
        if listening:
            findings.append(
                {
                    "code": "PORT_LISTENING",
                    "severity": "INFO",
                    "service": None,
                    "message": f"Port :{port} ({var}) is listening (ownership not proven)",
                    "evidence": [f"var={var}", f"port={port}", "ownership=UNKNOWN"],
                    "recommendation": (
                        "Confirm container labels/project identity before treating "
                        "this as healthy for this repo."
                    ),
                }
            )
            findings.append(
                {
                    "code": "PORT_OWNERSHIP_UNKNOWN",
                    "severity": "UNKNOWN",
                    "service": None,
                    "message": (
                        f"Listening port :{port} ({var}) has no proven project ownership"
                    ),
                    "evidence": [f"var={var}", f"port={port}"],
                    "recommendation": (
                        "Packet 002 should attach project labels and a runtime registry."
                    ),
                }
            )
        else:
            findings.append(
                {
                    "code": "PORT_NOT_LISTENING",
                    "severity": "WARN",
                    "service": None,
                    "message": f"Nothing listening on :{port} ({var})",
                    "evidence": [f"var={var}", f"port={port}"],
                    "recommendation": (
                        "Start the matching container only after repo-aware lifecycle "
                        "exists (Packet 002). Do not use cwd compose for foreign repos."
                    ),
                }
            )
    return findings
