"""Repo-aware MCP lifecycle reconciler: plan, preflight, start/stop/status.

Uses Packet 001 doctor for preflight. Never adopts unlabeled containers.
"""

from __future__ import annotations

import json
import re
import socket
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence

from . import docker_inspect as di
from . import docker_runtime as dr
from .doctor import DoctorReport, run_mcp_doctor
from .envrc import load_envrc, merge_envrc_into_environ, safe_port_int
from .port_diagnostics import instance_id_for_path
from .runtime_registry import (
    RegistryError,
    RuntimeRegistry,
    build_instance_record,
    default_registry_path,
)
from .runtime_state import (
    ENVRC_FILENAME,
    PROJECT_MCP_FILENAME,
    load_mcp_json,
    resolve_identity_view,
)

SCHEMA_VERSION = "1.0"

PROJECT_SCOPED_DEFAULT = ("conport", "dope-memory", "task-orchestrator")

# Doctor finding codes that block start mutations
BLOCKING_FINDING_CODES = frozenset(
    {
        "PROJECT_IDENTITY_UNKNOWN",
        "WORKTREE_ROOT_UNKNOWN",
        "PROJECT_ROOT_UNKNOWN",
        "MCP_JSON_PARSE_ERROR",
        "ENVRC_PARSE_ERROR",
        "ENVRC_MISSING",
        "MCP_JSON_MISSING",
        "TRANSPORT_MISMATCH",
        "PORT_RESERVED_COLLISION",
        "PORT_INTRA_CONFIG_COLLISION",
        "PORT_OWNED_BY_OTHER_PROJECT",
        "DOCKER_UNAVAILABLE",
        "DOCKER_CONTAINER_WRONG_PROJECT",
        "DOCKER_CONTAINER_UNLABELED_UNKNOWN",
        "DOCKER_CONTAINER_PORT_COLLISION",
        "TASK_ORCHESTRATOR_WRONG_PROJECT_RUNTIME",
    }
)

# Informational doctor codes that should not block (lifecycle neutralizes compose hazards)
NON_BLOCKING_EVEN_IF_IN_SET = frozenset(
    {
        # These become non-blocking when we use generated override (not raw compose)
        "COMPOSE_REQUIRED_IN_CWD",
        "COMPOSE_CONTAINER_NAME_DEFAULT_COLLISION_RISK",
        "COMPOSE_MEMORY_VOLUME_RELATIVE_CWD_RISK",
        "COMPOSE_WORKSPACE_ID_MISSING_RISK",
        "COMPOSE_INSTANCE_ID_ONLY_INSUFFICIENT",
        "DUAL_ALLOCATION_BRAINS",
        "INSTANCE_OVERLAY_NOT_WIRED_TO_INIT",
        "PORT_HASH_BUCKET_COLLISION_RISK",
        "PORT_REBIND_MISSING",
        "PORT_NOT_LISTENING",
        "PORT_LISTENING",
        "PORT_OWNERSHIP_UNKNOWN",
        "PORT_EXPECTED",
        "DOCKER_CONTAINER_NOT_FOUND",
        "GLOBAL_SERVICE_DEAD",
        "GLOBAL_LOCAL_DUPLICATE",
        "TASK_ORCHESTRATOR_PROJECT_IDENTITY_UNKNOWN",
    }
)


def _port_is_free(port: int, host: str = "127.0.0.1") -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.5)
    try:
        return sock.connect_ex((host, port)) != 0
    finally:
        sock.close()


def _service_instance_id(slug: str, worktree_hash: str, service: str) -> str:
    return f"{slug}-{worktree_hash}-{service}"


@dataclass
class LifecycleResult:
    schema_version: str
    operation: str
    dry_run: bool
    status: str
    project_identity: Dict[str, Any]
    services: List[Dict[str, Any]]
    blocking_findings: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    registry_path: str = ""
    runtime_artifacts: List[str] = field(default_factory=list)
    recommended_next_actions: List[str] = field(default_factory=list)
    exit_code: int = 0
    registry: Optional[Dict[str, Any]] = None
    docker: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "schema_version": self.schema_version,
            "operation": self.operation,
            "dry_run": self.dry_run,
            "status": self.status,
            "project_identity": self.project_identity,
            "services": self.services,
            "blocking_findings": self.blocking_findings,
            "warnings": self.warnings,
            "registry_path": self.registry_path,
            "runtime_artifacts": self.runtime_artifacts,
            "recommended_next_actions": self.recommended_next_actions,
        }
        if self.registry is not None:
            d["registry"] = self.registry
        if self.docker is not None:
            d["docker"] = self.docker
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"


def resolve_target_repo(repo: Optional[str | Path]) -> Path:
    if repo is not None:
        path = Path(repo).expanduser().resolve()
    else:
        path = Path.cwd().resolve()
    if not path.is_dir():
        raise FileNotFoundError(f"Target path not found: {path}")
    return path


def select_services(
    requested: Optional[Sequence[str]],
    mcp_servers: Mapping[str, Any],
    catalog: Mapping[str, Any],
) -> List[str]:
    if requested:
        return [s.strip() for s in requested if s.strip()]
    # Prefer local .mcp.json project-scoped entries
    names = []
    for name in mcp_servers.keys():
        spec = (catalog.get("servers") or {}).get(name) or {}
        if isinstance(spec, dict) and spec.get("scope") == "per-worktree":
            names.append(name)
        elif name in PROJECT_SCOPED_DEFAULT:
            names.append(name)
    if not names:
        names = list(PROJECT_SCOPED_DEFAULT)
    return names


def _doctor_blocking_findings(
    doctor: DoctorReport,
    *,
    services: Sequence[str],
    strategy_neutralizes_compose: bool = True,
) -> List[Dict[str, Any]]:
    blocking = []
    for f in doctor.findings:
        code = f.get("code") or ""
        if code in NON_BLOCKING_EVEN_IF_IN_SET and strategy_neutralizes_compose:
            continue
        # Only block PORT_RESERVED_COLLISION for formula when configured ports differ —
        # filter: block if service is requested and finding mentions reserved for configured
        if code == "PORT_RESERVED_COLLISION":
            evidence = " ".join(f.get("evidence") or [])
            # Block configured collisions always; formula-only is warn if envrc has safe ports
            if "source=formula" in evidence and "source=configured" not in evidence:
                # Downgrade pure-formula reserved collision if we have configured ports from envrc
                continue
        if code in BLOCKING_FINDING_CODES:
            # Scope transport mismatch etc. to requested services when service field set
            svc = f.get("service")
            if svc and svc not in services and code == "TRANSPORT_MISMATCH":
                continue
            if svc and svc not in services and code.startswith("DOCKER_CONTAINER"):
                continue
            blocking.append(f)
        elif f.get("severity") == "FAIL" and code not in NON_BLOCKING_EVEN_IF_IN_SET:
            # Extra hard FAILs
            if code.startswith("MCP_DOCTOR"):
                continue
            svc = f.get("service")
            if svc and svc not in services:
                continue
            if code in BLOCKING_FINDING_CODES:
                blocking.append(f)
    return blocking


def _extract_ports(env: Mapping[str, str], services: Sequence[str], catalog: Mapping[str, Any]) -> Dict[str, int]:
    ports: Dict[str, int] = {}
    for name in services:
        spec = (catalog.get("servers") or {}).get(name) or {}
        if not isinstance(spec, dict):
            continue
        for key in [spec.get("port_var")] + [
            e.get("var") for e in (spec.get("extra_port_vars") or []) if isinstance(e, dict)
        ]:
            if not key:
                continue
            p = safe_port_int(env, str(key))
            if p is not None:
                ports[str(key)] = p
    return ports


def _port_to_expected_service(
    port: int,
    *,
    services: Sequence[str],
    ports: Mapping[str, int],
    catalog: Mapping[str, Any],
) -> Optional[str]:
    """Map a host port back to the requested MCP service that owns it."""
    for svc in services:
        svc_ports = _ports_for_service(svc, ports, catalog)
        if any(int(p) == int(port) for p in svc_ports.values()):
            return svc
    # Fallback: port env-var naming conventions
    for var, p in ports.items():
        if int(p) != int(port):
            continue
        key = str(var).upper()
        if key.startswith("CONPORT"):
            return "conport"
        if key.startswith("DOPE_MEMORY") or key.startswith("DOPEMEMORY"):
            return "dope-memory"
        if key.startswith("TASK_ORCHESTRATOR"):
            return "task-orchestrator"
    return None


def _collision_checks(
    *,
    services: Sequence[str],
    ports: Mapping[str, int],
    container_names: Mapping[str, str],
    docker: di.DockerInspectResult,
    project_id: str,
    worktree_root: str,
    catalog: Optional[Mapping[str, Any]] = None,
) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    catalog = catalog or {}
    if not docker.available:
        findings.append(
            {
                "code": "DOCKER_UNAVAILABLE",
                "severity": "FAIL",
                "message": docker.error or "Docker unavailable",
                "service": None,
            }
        )
        return findings

    by_name = {c.name: c for c in docker.containers}
    port_owners: Dict[int, di.DockerContainerInfo] = {}
    for c in docker.containers:
        for p in c.published_ports:
            port_owners[p] = c

    for svc, cname in container_names.items():
        if svc not in services:
            continue
        existing = by_name.get(cname)
        if not existing:
            # also match prefix
            for c in docker.containers:
                if c.name == cname or c.name.endswith(cname):
                    existing = c
                    break
        if existing:
            labels = existing.labels or {}
            managed = labels.get(dr.LABEL_MANAGED) == "true"
            if not managed:
                findings.append(
                    {
                        "code": "DOCKER_CONTAINER_UNLABELED_UNKNOWN",
                        "severity": "FAIL",
                        "service": svc,
                        "message": (
                            f"Container {existing.name} exists without dopemux.managed=true; "
                            "refusing to adopt"
                        ),
                    }
                )
            elif labels.get("dopemux.project_id") and labels.get("dopemux.project_id") != project_id:
                findings.append(
                    {
                        "code": "DOCKER_CONTAINER_WRONG_PROJECT",
                        "severity": "FAIL",
                        "service": svc,
                        "message": f"Container {existing.name} belongs to another project",
                    }
                )
            elif labels.get("dopemux.service") and labels.get("dopemux.service") != svc:
                findings.append(
                    {
                        "code": "DOCKER_CONTAINER_WRONG_PROJECT",
                        "severity": "FAIL",
                        "service": svc,
                        "message": f"Container {existing.name} labels service mismatch",
                    }
                )

    for var, port in ports.items():
        owner = port_owners.get(port)
        if not owner:
            continue
        labels = owner.labels or {}
        managed = labels.get(dr.LABEL_MANAGED) == "true"
        expected_svc = _port_to_expected_service(
            int(port), services=services, ports=ports, catalog=catalog
        )
        expected_spec = (catalog.get("servers") or {}).get(expected_svc or "") or {}
        if (
            expected_svc == "task-orchestrator"
            and expected_spec.get("state_scope") == "multi_project_singleton"
        ):
            # Fixed-port TO ownership is verified by MCP handshake below, not labels.
            continue
        expected_cname = container_names.get(expected_svc or "", "")
        # Only treat as "ours" when name matches the *expected* MCP service/container —
        # never the owner's own name fragment (avoids accepting <repo>_db on MCP ports).
        expected_name_substrings = [
            s
            for s in (
                expected_svc or "",
                expected_cname,
                "task-orchestrator" if expected_svc == "task-orchestrator" else "",
            )
            if s
        ]
        ownership = di.classify_container_ownership(
            owner,
            project_root=worktree_root,
            workspace_id=worktree_root,
            project_id=project_id,
            expected_ports=[int(port)],
            expected_name_substrings=expected_name_substrings,
            project_slug_hints=[project_id, Path(worktree_root).name if worktree_root else ""],
        )
        owner_svc_label = labels.get("dopemux.service") or ""
        # Explicit service-label mismatch on our port → always collision
        if (
            managed
            and expected_svc
            and owner_svc_label
            and owner_svc_label != expected_svc
            and labels.get("dopemux.project_id") == project_id
        ):
            findings.append(
                {
                    "code": "DOCKER_CONTAINER_PORT_COLLISION",
                    "severity": "FAIL",
                    "service": expected_svc,
                    "message": (
                        f"Port :{port} ({var}) held by same-project container "
                        f"{owner.name} labeled service={owner_svc_label} "
                        f"(expected {expected_svc})"
                    ),
                }
            )
            continue
        if ownership in {"MATCH", "COMPOSE_MATCH"}:
            # Require that COMPOSE_MATCH is not just port+slug with wrong service name
            if ownership == "COMPOSE_MATCH" and expected_name_substrings:
                name_l = (owner.name or "").lower()
                if not any(s.lower() in name_l for s in expected_name_substrings if s):
                    findings.append(
                        {
                            "code": "DOCKER_CONTAINER_PORT_COLLISION",
                            "severity": "FAIL",
                            "service": expected_svc,
                            "message": (
                                f"Port :{port} ({var}) occupied by same-project container "
                                f"{owner.name} that is not the expected MCP service "
                                f"{expected_svc or var}"
                            ),
                        }
                    )
                    continue
            # Owned by this project (explicit labels or compose secondary) — not a foreign collision
            continue
        if not managed:
            findings.append(
                {
                    "code": "DOCKER_CONTAINER_PORT_COLLISION",
                    "severity": "FAIL",
                    "service": expected_svc,
                    "message": (
                        f"Port :{port} ({var}) occupied by unlabeled container {owner.name}"
                    ),
                }
            )
        elif labels.get("dopemux.project_id") and labels.get("dopemux.project_id") != project_id:
            findings.append(
                {
                    "code": "PORT_OWNED_BY_OTHER_PROJECT",
                    "severity": "FAIL",
                    "service": labels.get("dopemux.service") or expected_svc,
                    "message": (
                        f"Port :{port} owned by project {labels.get('dopemux.project_id')} "
                        f"via {owner.name}"
                    ),
                }
            )
        # Same project + managed + matching service → OK (already_running path)
    return findings


def run_lifecycle(
    operation: str,
    *,
    repo: Optional[str | Path] = None,
    services: Optional[Sequence[str]] = None,
    catalog: Mapping[str, Any],
    dry_run: bool = False,
    registry_path: Optional[Path] = None,
    docker_runner: Optional[Callable[..., Any]] = None,
    cmd_runner: Optional[Callable[..., Any]] = None,
    skip_doctor: bool = False,
    process_env: Optional[Mapping[str, str]] = None,
    port_is_free_fn: Optional[Callable[[int], bool]] = None,
    product_root: Optional[Path] = None,
) -> LifecycleResult:
    """Execute start|stop|restart|status for project-scoped MCP sidecars."""
    op = operation.lower().strip()
    if op not in {"start", "stop", "restart", "status"}:
        raise ValueError(f"unsupported operation: {operation}")

    target = resolve_target_repo(repo)
    is_free = port_is_free_fn or _port_is_free
    envrc = load_envrc(target / ENVRC_FILENAME)
    doctor_env = merge_envrc_into_environ(dict(process_env or {}), envrc, override=True)
    mcp_json = load_mcp_json(target / PROJECT_MCP_FILENAME)
    mcp_servers = mcp_json.get("servers") or {}
    identity = resolve_identity_view(target, envrc_values=doctor_env)

    selected = select_services(services, mcp_servers, catalog)
    reg_path = registry_path or default_registry_path()

    # Doctor preflight (read-only; never creates registry)
    doctor: Optional[DoctorReport] = None
    if not skip_doctor and op != "status":
        doctor = run_mcp_doctor(
            target,
            catalog=catalog,
            skip_docker=False,
            skip_port_probe=True,
            process_env=doctor_env,
            docker_runner=docker_runner,
        )
    elif op == "status":
        doctor = run_mcp_doctor(
            target,
            catalog=catalog,
            skip_docker=False,
            skip_port_probe=False,
            process_env=doctor_env,
            docker_runner=docker_runner,
            port_is_free_fn=is_free,
        )

    blocking: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []

    # Identity blockers
    if not identity.project_id or identity.identity_confidence == "UNKNOWN":
        blocking.append(
            {
                "code": "PROJECT_IDENTITY_UNKNOWN",
                "severity": "FAIL",
                "message": "project identity unknown",
                "service": None,
            }
        )
    if not identity.worktree_root:
        blocking.append(
            {
                "code": "WORKTREE_ROOT_UNKNOWN",
                "severity": "FAIL",
                "message": "worktree root unknown",
                "service": None,
            }
        )
    if not identity.project_root:
        blocking.append(
            {
                "code": "PROJECT_ROOT_UNKNOWN",
                "severity": "FAIL",
                "message": "project root unknown",
                "service": None,
            }
        )
    if not envrc.present or envrc.parse_status == "MISSING":
        blocking.append(
            {
                "code": "ENVRC_MISSING",
                "severity": "FAIL",
                "message": f"Missing {ENVRC_FILENAME}",
                "service": None,
            }
        )
    elif envrc.parse_status == "ERROR":
        blocking.append(
            {
                "code": "ENVRC_PARSE_ERROR",
                "severity": "FAIL",
                "message": "envrc parse error",
                "service": None,
            }
        )
    elif envrc.parse_status == "PARTIAL":
        warnings.append(
            {
                "code": "ENVRC_PARTIAL_PARSE",
                "severity": "WARN",
                "message": (
                    f"envrc partial parse: {len(envrc.values)} keys loaded, "
                    f"{len(envrc.errors)} malformed line(s)"
                ),
                "service": None,
            }
        )
    if not mcp_json.get("present"):
        blocking.append(
            {
                "code": "MCP_JSON_MISSING",
                "severity": "FAIL",
                "message": f"Missing {PROJECT_MCP_FILENAME}",
                "service": None,
            }
        )
    elif mcp_json.get("parse_status") == "ERROR":
        blocking.append(
            {
                "code": "MCP_JSON_PARSE_ERROR",
                "severity": "FAIL",
                "message": "mcp.json parse error",
                "service": None,
            }
        )

    if doctor:
        blocking.extend(
            _doctor_blocking_findings(doctor, services=selected, strategy_neutralizes_compose=True)
        )
        for f in doctor.findings:
            if f.get("severity") == "WARN":
                warnings.append(f)

    # Load registry
    if op == "status":
        registry = RuntimeRegistry.load(reg_path, create_missing=False)
    else:
        registry = RuntimeRegistry.load(reg_path, create_missing=False)
        if registry.parse_status == "ERROR" and op in {"start", "stop", "restart"}:
            blocking.append(
                {
                    "code": "REGISTRY_PARSE_ERROR",
                    "severity": "FAIL",
                    "message": f"Registry unreadable: {registry.error}",
                    "service": None,
                }
            )

    docker = di.inspect_running_containers(runner=docker_runner)

    worktree_root = identity.worktree_root or str(target)
    project_root = identity.project_root or str(target)
    project_id = identity.project_id or Path(project_root).name
    worktree_hash = identity.worktree_hash or instance_id_for_path(worktree_root)
    project_hash = identity.project_hash or ""
    slug = dr.project_slug(Path(project_root).name)
    compose_proj = dr.compose_project_name(slug, worktree_hash)

    ports = _extract_ports(doctor_env, selected, catalog)

    # Task Orchestrator fixed-port identity gate (Packet 005)
    if op in {"start", "restart"} and "task-orchestrator" in selected:
        try:
            from .task_orchestrator_identity import (
                evaluate_fixed_port_state,
                identity_from_docker_labels,
            )

            to_spec = (catalog.get("servers") or {}).get("task-orchestrator") or {}
            to_port = ports.get(
                str(to_spec.get("port_var") or "TASK_ORCHESTRATOR_HTTP_PORT")
            ) or int(to_spec.get("default_port_base") or 7890)
            docker_identity = None
            if docker.available:
                from .task_orchestrator_identity import identity_from_container_heuristics

                matches = di.find_containers_for_service(
                    docker,
                    service_name="task-orchestrator",
                    expected_ports=[int(to_port)],
                    name_hints=["task-orchestrator", "orchestrator"],
                )
                for c in matches:
                    st = di.classify_container_ownership(
                        c,
                        project_root=identity.project_root,
                        workspace_id=identity.workspace_id,
                        project_id=identity.project_id,
                        expected_ports=[int(to_port)],
                        expected_name_substrings=["task-orchestrator"],
                        project_slug_hints=[
                            identity.project_id or "",
                            Path(identity.project_root or "").name,
                        ],
                    )
                    if st in {"MATCH", "WRONG_PROJECT"}:
                        docker_identity = identity_from_docker_labels(
                            c.labels or {},
                            port=int(to_port),
                            container_name=c.name,
                        )
                        break
                    if st in {"COMPOSE_MATCH", "UNLABELED"} and docker_identity is None:
                        docker_identity = identity_from_container_heuristics(
                            container_name=c.name,
                            labels=c.labels or {},
                            port=int(to_port),
                            target_project_root=identity.project_root,
                            target_project_id=identity.project_id,
                        )
                        if st == "COMPOSE_MATCH" or docker_identity.has_project_proof():
                            break
            to_eval = evaluate_fixed_port_state(
                port=int(to_port),
                target_project_id=identity.project_id,
                target_project_root=identity.project_root,
                target_workspace_id=identity.workspace_id,
                target_instance_id=identity.instance_id,
                target_worktree_hash=identity.worktree_hash,
                is_free_fn=is_free,
                docker_identity=docker_identity,
                multi_project_singleton=(
                    to_spec.get("state_scope") == "multi_project_singleton"
                ),
                skip_http=True,  # upstream jar has no /info|/health (006R)
                for_start=True,
            )
            for f in to_eval.findings:
                if f.get("severity") == "FAIL" or f.get("code", "").startswith(
                    "TASK_ORCHESTRATOR_START_BLOCKED"
                ):
                    blocking.append(
                        {
                            "code": f.get("code")
                            or to_eval.start_block_code
                            or "TASK_ORCHESTRATOR_START_BLOCKED_UNKNOWN_OWNER",
                            "severity": "FAIL",
                            "message": f.get("message") or "TO start blocked",
                            "service": "task-orchestrator",
                        }
                    )
                elif f.get("severity") in {"WARN", "UNKNOWN"}:
                    warnings.append(
                        {
                            "code": f.get("code"),
                            "severity": f.get("severity"),
                            "message": f.get("message"),
                            "service": "task-orchestrator",
                        }
                    )
            if not to_eval.start_allowed and to_eval.start_block_code:
                if not any(
                    b.get("code") == to_eval.start_block_code for b in blocking
                ):
                    blocking.append(
                        {
                            "code": to_eval.start_block_code,
                            "severity": "FAIL",
                            "message": (
                                f"task-orchestrator start blocked "
                                f"(match={to_eval.match} port={to_port})"
                            ),
                            "service": "task-orchestrator",
                        }
                    )
            elif to_eval.start_allowed and to_eval.match in {"OK", "SHARED"}:
                warnings.append(
                    {
                        "code": "TASK_ORCHESTRATOR_START_ALLOWED",
                        "severity": "INFO",
                        "message": (
                            "task-orchestrator shared singleton already running"
                            if to_eval.match == "SHARED"
                            else "task-orchestrator already running for target project"
                        ),
                        "service": "task-orchestrator",
                    }
                )
            elif to_eval.start_allowed and to_eval.match == "FREE":
                warnings.append(
                    {
                        "code": "TASK_ORCHESTRATOR_START_ALLOWED",
                        "severity": "INFO",
                        "message": f"task-orchestrator fixed port :{to_port} free; start allowed",
                        "service": "task-orchestrator",
                    }
                )
        except Exception as exc:  # noqa: BLE001
            blocking.append(
                {
                    "code": "TASK_ORCHESTRATOR_START_BLOCKED_UNKNOWN_OWNER",
                    "severity": "FAIL",
                    "message": f"TO identity preflight failed: {exc}",
                    "service": "task-orchestrator",
                }
            )

    # Lease registry consistency (start only — recommend repair-config on mismatch)
    if op == "start":
        try:
            from .port_leases import PortLeaseRegistry

            lease_reg = PortLeaseRegistry.load()
            if lease_reg.parse_status == "ERROR":
                blocking.append(
                    {
                        "code": "LEASE_REGISTRY_PARSE_ERROR",
                        "severity": "FAIL",
                        "message": f"Lease registry unreadable: {lease_reg.error}",
                        "service": None,
                    }
                )
            elif lease_reg.parse_status == "OK":
                # Reserved singleton ports (TO:7890) are never project-leased (006R)
                from .port_allocator import singleton_reserved_ports

                reserved = singleton_reserved_ports(catalog)
                reserved.setdefault(7890, "task-orchestrator")
                for var, port in ports.items():
                    if int(port) in reserved:
                        # Ignore invalid foreign leases on reserved ports; do not block start.
                        warnings.append(
                            {
                                "code": "ALLOCATOR_RESERVED_SINGLETON_PORT",
                                "severity": "INFO",
                                "message": (
                                    f"{var}={port} is reserved singleton "
                                    f"({reserved[int(port)]}); not lease-gated"
                                ),
                                "service": reserved.get(int(port)),
                            }
                        )
                        continue
                    ours = [
                        L
                        for L in lease_reg.active_leases()
                        if L.get("port_var") == var
                        and (
                            L.get("worktree_root") == (identity.worktree_root or str(target))
                            or L.get("worktree_hash") == identity.worktree_hash
                        )
                    ]
                    foreign = lease_reg.find_active_by_port(int(port))
                    if foreign and not lease_reg.identity_matches(
                        foreign,
                        worktree_root=identity.worktree_root or str(target),
                        project_root=identity.project_root,
                        worktree_hash=identity.worktree_hash,
                    ):
                        blocking.append(
                            {
                                "code": "LEASE_BELONGS_TO_OTHER_PROJECT",
                                "severity": "FAIL",
                                "message": f"Port {port} ({var}) leased to another project",
                                "service": None,
                            }
                        )
                    elif ours and int(ours[0].get("port") or 0) != int(port):
                        blocking.append(
                            {
                                "code": "LEASE_ENVRC_MISMATCH",
                                "severity": "FAIL",
                                "message": (
                                    f"Envrc {var}={port} != lease {ours[0].get('port')}; "
                                    "run `dopemux mcp repair-config --apply`"
                                ),
                                "service": None,
                            }
                        )
                    elif not ours:
                        warnings.append(
                            {
                                "code": "LEGACY_ENVRC_WITHOUT_LEASE",
                                "severity": "WARN",
                                "message": f"No lease for envrc {var}={port}",
                                "service": None,
                            }
                        )
                    else:
                        if not is_free(int(port)):
                            pass
        except Exception as exc:  # noqa: BLE001
            warnings.append(
                {
                    "code": "LEASE_UNKNOWN_OWNER",
                    "severity": "WARN",
                    "message": f"Lease check skipped: {exc}",
                    "service": None,
                }
            )

    # Missing required ports for selected services
    for name in selected:
        spec = (catalog.get("servers") or {}).get(name) or {}
        if not isinstance(spec, dict):
            blocking.append(
                {
                    "code": "CATALOG_SERVICE_UNKNOWN",
                    "severity": "FAIL",
                    "message": f"Service `{name}` not in catalog",
                    "service": name,
                }
            )
            continue
        pvar = spec.get("port_var")
        if pvar and pvar not in ports and name != "task-orchestrator":
            # TO has fixed default 7890
            if name == "task-orchestrator":
                ports.setdefault(str(pvar), int(spec.get("default_port_base") or 7890))
            else:
                blocking.append(
                    {
                        "code": "PORT_UNSET",
                        "severity": "FAIL",
                        "message": f"Required port env {pvar} unset for {name}",
                        "service": name,
                    }
                )
        if name == "task-orchestrator" and pvar:
            ports.setdefault(str(pvar), int(spec.get("default_port_base") or 7890))

    container_names = {
        svc: dr.container_name_for(slug, worktree_hash, svc) for svc in selected
    }
    # Match wrapper scripts/mcp-wrappers/task-orchestrator-*-{stdio,http}:
    # state_id = <project-slug>-<sha256(project_root)[:16]> (== ProjectIdentity.project_id)
    # container_name = task-orchestrator-${state_id}
    if "task-orchestrator" in selected:
        to_state_id = identity.project_id
        if not to_state_id and project_hash:
            # Fallback: identity-style slug (keeps . _ - like the wrapper), not docker slug.
            to_slug = re.sub(
                r"[^a-z0-9._-]+", "-", Path(project_root).name.lower()
            ).strip("-") or "workspace"
            to_state_id = f"{to_slug}-{project_hash}"
        if to_state_id:
            container_names["task-orchestrator"] = f"task-orchestrator-{to_state_id}"

    labels_by_service: Dict[str, Dict[str, str]] = {}
    for svc in selected:
        spec = (catalog.get("servers") or {}).get(svc) or {}
        transport = str(spec.get("transport") or "unknown") if isinstance(spec, dict) else "unknown"
        scope = "worktree"
        if isinstance(spec, dict) and spec.get("state_scope") == "per-repo":
            scope = "project"
        elif isinstance(spec, dict) and spec.get("scope") == "singleton":
            scope = "singleton"
        iid = _service_instance_id(slug, worktree_hash, svc)
        labels_by_service[svc] = dr.build_labels(
            project_id=project_id,
            workspace_id=identity.workspace_id or worktree_root,
            project_root=project_root,
            worktree_root=worktree_root,
            project_hash=project_hash,
            worktree_hash=worktree_hash,
            instance_id=iid,
            service=svc,
            scope=scope,
            transport=transport,
        )

    collision_findings = _collision_checks(
        services=selected,
        ports=ports,
        container_names=container_names,
        docker=docker,
        project_id=project_id,
        worktree_root=worktree_root,
        catalog=catalog,
    )
    if op in {"start", "restart"}:
        blocking.extend(collision_findings)

    # Deduplicate blocking by code+service+message
    seen_b = set()
    uniq_blocking = []
    for f in blocking:
        key = (f.get("code"), f.get("service"), f.get("message"))
        if key in seen_b:
            continue
        seen_b.add(key)
        uniq_blocking.append(f)
    blocking = uniq_blocking

    identity_dict = identity.to_dict()

    if op == "status":
        return _status_result(
            identity_dict=identity_dict,
            selected=selected,
            registry=registry,
            docker=docker,
            doctor=doctor,
            container_names=container_names,
            ports=ports,
            labels_by_service=labels_by_service,
            project_id=project_id,
            worktree_root=worktree_root,
            catalog=catalog,
            is_free=is_free,
            reg_path=reg_path,
            warnings=warnings,
        )

    if blocking and op in {"start", "stop", "restart"}:
        # stop can proceed only for managed matching; but still block on registry error
        if op == "stop" and not any(
            f.get("code") == "REGISTRY_PARSE_ERROR" for f in blocking
        ):
            # For stop, filter blocking to only hard safety (don't require envrc for stop if registry has entries)
            hard = [
                f
                for f in blocking
                if f.get("code")
                in {
                    "REGISTRY_PARSE_ERROR",
                    "PROJECT_IDENTITY_UNKNOWN",
                    "DOCKER_UNAVAILABLE",
                }
            ]
            if not hard:
                blocking = []
        if blocking:
            svc_plans = [
                {
                    "service": s,
                    "action": "blocked",
                    "reason": "preflight blocked",
                    "container_name": container_names.get(s),
                    "ports": {k: v for k, v in ports.items() if s.split("-")[0] in k.lower() or True},
                    "labels": labels_by_service.get(s, {}),
                    "runtime_files": [],
                    "commands": [],
                    "preflight_findings": [f for f in blocking if f.get("service") in (None, s)],
                }
                for s in selected
            ]
            # simplify ports in plan
            for plan in svc_plans:
                plan["ports"] = _ports_for_service(plan["service"], ports, catalog)
            return LifecycleResult(
                schema_version=SCHEMA_VERSION,
                operation=op,
                dry_run=dry_run,
                status="BLOCKED" if dry_run else "FAIL",
                project_identity=identity_dict,
                services=svc_plans,
                blocking_findings=blocking,
                warnings=warnings,
                registry_path=str(reg_path),
                exit_code=1,
                recommended_next_actions=[
                    "Fix blocking preflight findings (doctor --json), then retry.",
                    "Do not start via cwd compose env injection.",
                ],
            )

    try:
        product = product_root or dr.product_root()
    except FileNotFoundError as exc:
        return LifecycleResult(
            schema_version=SCHEMA_VERSION,
            operation=op,
            dry_run=dry_run,
            status="FAIL",
            project_identity=identity_dict,
            services=[],
            blocking_findings=[
                {
                    "code": "PRODUCT_ROOT_UNKNOWN",
                    "severity": "FAIL",
                    "message": str(exc),
                    "service": None,
                }
            ],
            registry_path=str(reg_path),
            exit_code=2,
        )

    if op == "stop":
        return _stop_services(
            selected=selected,
            identity_dict=identity_dict,
            project_id=project_id,
            worktree_root=worktree_root,
            container_names=container_names,
            labels_by_service=labels_by_service,
            registry=registry,
            docker=docker,
            dry_run=dry_run,
            reg_path=reg_path,
            product=product,
            compose_proj=compose_proj,
            cmd_runner=cmd_runner,
            ports=ports,
            catalog=catalog,
            slug=slug,
            worktree_hash=worktree_hash,
        )

    if op == "restart":
        stop_res = _stop_services(
            selected=selected,
            identity_dict=identity_dict,
            project_id=project_id,
            worktree_root=worktree_root,
            container_names=container_names,
            labels_by_service=labels_by_service,
            registry=registry,
            docker=docker,
            dry_run=dry_run,
            reg_path=reg_path,
            product=product,
            compose_proj=compose_proj,
            cmd_runner=cmd_runner,
            ports=ports,
            catalog=catalog,
            slug=slug,
            worktree_hash=worktree_hash,
        )
        if stop_res.status == "FAIL" and not dry_run:
            stop_res.operation = "restart"
            return stop_res
        start_res = _start_services(
            selected=selected,
            identity=identity,
            identity_dict=identity_dict,
            project_id=project_id,
            project_root=project_root,
            worktree_root=worktree_root,
            project_hash=project_hash,
            worktree_hash=worktree_hash,
            slug=slug,
            compose_proj=compose_proj,
            container_names=container_names,
            labels_by_service=labels_by_service,
            ports=ports,
            doctor_env=doctor_env,
            registry=registry,
            docker=docker,
            dry_run=dry_run,
            reg_path=reg_path,
            product=product,
            catalog=catalog,
            cmd_runner=cmd_runner,
            is_free=is_free,
            target=target,
        )
        start_res.operation = "restart"
        if dry_run:
            start_res.services = [
                {
                    **s,
                    "restart_plan": {
                        "stop": next(
                            (x for x in stop_res.services if x.get("service") == s.get("service")),
                            {},
                        ),
                        "start": s,
                    },
                }
                for s in start_res.services
            ]
        return start_res

    # start
    return _start_services(
        selected=selected,
        identity=identity,
        identity_dict=identity_dict,
        project_id=project_id,
        project_root=project_root,
        worktree_root=worktree_root,
        project_hash=project_hash,
        worktree_hash=worktree_hash,
        slug=slug,
        compose_proj=compose_proj,
        container_names=container_names,
        labels_by_service=labels_by_service,
        ports=ports,
        doctor_env=doctor_env,
        registry=registry,
        docker=docker,
        dry_run=dry_run,
        reg_path=reg_path,
        product=product,
        catalog=catalog,
        cmd_runner=cmd_runner,
        is_free=is_free,
        target=target,
    )


def _ports_for_service(service: str, ports: Mapping[str, int], catalog: Mapping[str, Any]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    spec = (catalog.get("servers") or {}).get(service) or {}
    if not isinstance(spec, dict):
        return out
    if spec.get("port_var") and spec["port_var"] in ports:
        out[str(spec["port_var"])] = ports[str(spec["port_var"])]
    for extra in spec.get("extra_port_vars") or []:
        if isinstance(extra, dict) and extra.get("var") in ports:
            out[str(extra["var"])] = ports[str(extra["var"])]
    # Friendly aliases for registry
    if service == "conport":
        if "CONPORT_HTTP_PORT" in ports:
            out["http"] = ports["CONPORT_HTTP_PORT"]
        if "CONPORT_MCP_PORT" in ports:
            out["sse"] = ports["CONPORT_MCP_PORT"]
        if "CONPORT_INFO_PORT" in ports:
            out["info"] = ports["CONPORT_INFO_PORT"]
    if service == "dope-memory" and "DOPE_MEMORY_PORT" in ports:
        out["http"] = ports["DOPE_MEMORY_PORT"]
    if service == "task-orchestrator" and "TASK_ORCHESTRATOR_HTTP_PORT" in ports:
        out["http"] = ports["TASK_ORCHESTRATOR_HTTP_PORT"]
    return out


def _urls_for_service(service: str, ports: Mapping[str, int]) -> Dict[str, str]:
    urls: Dict[str, str] = {}
    if service == "conport":
        if "CONPORT_HTTP_PORT" in ports:
            urls["http"] = f"http://localhost:{ports['CONPORT_HTTP_PORT']}"
        if "CONPORT_MCP_PORT" in ports:
            urls["sse"] = f"http://localhost:{ports['CONPORT_MCP_PORT']}/sse"
    if service == "dope-memory" and "DOPE_MEMORY_PORT" in ports:
        urls["http"] = f"http://localhost:{ports['DOPE_MEMORY_PORT']}/mcp"
        urls["health"] = f"http://localhost:{ports['DOPE_MEMORY_PORT']}/health"
    if service == "task-orchestrator" and "TASK_ORCHESTRATOR_HTTP_PORT" in ports:
        p = ports["TASK_ORCHESTRATOR_HTTP_PORT"]
        urls["http"] = f"http://127.0.0.1:{p}/mcp"
        urls["health"] = f"http://127.0.0.1:{p}/health"
    return urls


def _already_running_managed(
    docker: di.DockerInspectResult,
    cname: str,
    project_id: str,
    service: str,
) -> Optional[di.DockerContainerInfo]:
    if not docker.available:
        return None
    for c in docker.containers:
        if c.name != cname and not c.name.endswith(cname):
            continue
        labels = c.labels or {}
        if labels.get(dr.LABEL_MANAGED) != "true":
            return None
        if labels.get("dopemux.project_id") == project_id and labels.get("dopemux.service") == service:
            return c
        # name match but wrong labels handled by collision
        return None
    return None


def _start_services(**kw: Any) -> LifecycleResult:
    selected: List[str] = kw["selected"]
    identity = kw["identity"]
    identity_dict = kw["identity_dict"]
    project_id = kw["project_id"]
    project_root = kw["project_root"]
    worktree_root = kw["worktree_root"]
    project_hash = kw["project_hash"]
    worktree_hash = kw["worktree_hash"]
    slug = kw["slug"]
    compose_proj = kw["compose_proj"]
    container_names = kw["container_names"]
    labels_by_service = kw["labels_by_service"]
    ports: Dict[str, int] = kw["ports"]
    doctor_env = kw["doctor_env"]
    registry: RuntimeRegistry = kw["registry"]
    docker: di.DockerInspectResult = kw["docker"]
    dry_run: bool = kw["dry_run"]
    reg_path: Path = kw["reg_path"]
    product: Path = kw["product"]
    catalog = kw["catalog"]
    cmd_runner = kw["cmd_runner"]
    is_free = kw["is_free"]
    target: Path = kw["target"]

    compose_services = [s for s in selected if s in {"conport", "dope-memory"}]
    to_selected = "task-orchestrator" in selected

    runtime_base = reg_path.parent / f"{slug}-{worktree_hash}"
    memory_data = Path(worktree_root) / ".dopemux"
    # Project identity used for TO container naming (must match wrapper).
    to_state_id = ""
    if "task-orchestrator" in selected:
        to_cname = container_names.get("task-orchestrator") or ""
        if to_cname.startswith("task-orchestrator-"):
            to_state_id = to_cname[len("task-orchestrator-") :]
        else:
            to_state_id = identity.project_id or project_id or ""

    identity_env = {
        "DOPEMUX_INSTANCE_ID": identity.instance_id or worktree_hash,
        "DOPEMUX_PROJECT_ID": identity.project_id or project_id,
        "DOPEMUX_WORKSPACE_ID": identity.workspace_id or worktree_root,
        "DOPEMUX_PROJECT_ROOT": project_root,
        "DOPEMUX_WORKTREE_ROOT": worktree_root,
        "DOPEMUX_WORKSPACE_ROOT": worktree_root,
        "DOPE_MEMORY_WORKSPACE_ID": doctor_env.get("DOPE_MEMORY_WORKSPACE_ID")
        or Path(worktree_root).name,
        "DOPE_MEMORY_INSTANCE_ID": doctor_env.get("DOPE_MEMORY_INSTANCE_ID")
        or (identity.instance_id or worktree_hash),
        "TASK_ORCHESTRATOR_PROJECT_ROOT": project_root,
        "CONPORT_CONTAINER_NAME": container_names.get("conport", ""),
        **{k: str(v) for k, v in ports.items()},
    }
    if to_state_id:
        # Prefer project identity for TO naming; do not leak worktree instance id.
        identity_env["DOPEMUX_PROJECT_ID"] = to_state_id


    override_text = ""
    env_text = dr.generate_mcp_env(identity_env)
    if compose_services:
        override_text = dr.generate_compose_override(
            services=compose_services,
            identity=identity_env,
            ports=ports,
            container_names=container_names,
            labels_by_service=labels_by_service,
            memory_data_path=memory_data,
        )

    plan_doc = {
        "services": selected,
        "compose_project": compose_proj,
        "container_names": container_names,
        "ports": ports,
        "strategy": "compose_override+no_deps" if compose_services else "none",
        "task_orchestrator_strategy": "wrapper_singleton" if to_selected else None,
        "product_root": str(product),
        "memory_data_path": str(memory_data),
    }

    artifact_paths = dr.write_runtime_artifacts(
        runtime_base,
        env_text=env_text,
        override_text=override_text or "# no compose services\n",
        plan=plan_doc,
        dry_run=dry_run,
    )

    service_results: List[Dict[str, Any]] = []
    overall_fail = False
    overall_unknown = False

    # Plan/start compose services
    for svc in selected:
        cname = container_names[svc]
        svc_ports = _ports_for_service(svc, ports, catalog)
        labels = labels_by_service[svc]
        existing = _already_running_managed(docker, cname, project_id, svc)
        # TO: also check wrapper name
        if svc == "task-orchestrator" and not existing:
            existing = _already_running_managed(
                docker, cname, project_id, svc
            )
            # unlabeled TO on fixed port is already blocked in collision

        to_spec = (catalog.get("servers") or {}).get("task-orchestrator") or {}
        if (
            svc == "task-orchestrator"
            and not existing
            and to_spec.get("state_scope") == "multi_project_singleton"
            and not is_free(int(ports.get("TASK_ORCHESTRATOR_HTTP_PORT", 7890)))
        ):
            from .task_orchestrator_identity import (
                is_task_orchestrator_server_name,
                probe_mcp_server_name,
            )

            server_name = probe_mcp_server_name(
                int(ports.get("TASK_ORCHESTRATOR_HTTP_PORT", 7890))
            )
            if is_task_orchestrator_server_name(server_name):
                service_results.append(
                    {
                        "service": svc,
                        "action": "shared_singleton",
                        "reason": "verified existing shared Task Orchestrator MCP endpoint",
                        "container_name": None,
                        "container_names": [],
                        "ports": svc_ports,
                        "labels": labels,
                        "commands": [],
                        "probe_status": "PASS",
                        "registry_updated": False,
                        "findings": [
                            {
                                "code": "TASK_ORCHESTRATOR_SHARED_SINGLETON_OK",
                                "severity": "INFO",
                                "message": (
                                    "shared singleton verified via "
                                    f"serverInfo.name={server_name}"
                                ),
                            }
                        ],
                    }
                )
                continue

        if existing:
            service_results.append(
                {
                    "service": svc,
                    "action": "already_running" if not dry_run else "already_running",
                    "reason": "managed container already running with matching labels",
                    "container_name": existing.name,
                    "container_names": [existing.name],
                    "ports": svc_ports,
                    "labels": labels,
                    "commands": [],
                    "probe_status": "UNKNOWN",
                    "registry_updated": False,
                    "findings": [],
                }
            )
            if not dry_run:
                _registry_upsert(
                    registry,
                    svc=svc,
                    project_id=project_id,
                    identity=identity,
                    project_root=project_root,
                    worktree_root=worktree_root,
                    project_hash=project_hash,
                    worktree_hash=worktree_hash,
                    slug=slug,
                    compose_proj=compose_proj,
                    container_names=[existing.name],
                    ports=svc_ports,
                    labels=labels,
                    status="running",
                    last_start={"command": ["already_running"], "exit_code": 0},
                )
            continue

        commands: List[List[str]] = []
        if svc in {"conport", "dope-memory"}:
            cmd = dr.compose_up_command(
                product=product,
                override_path=Path(artifact_paths["compose.override.yml"]),
                env_file=Path(artifact_paths["mcp.env"]),
                project_name=compose_proj,
                services=[svc],
                no_deps=True,
            )
            commands.append(cmd)
        elif svc == "task-orchestrator":
            # Wrapper uses project resolution from env; set identity env
            cmd = dr.task_orchestrator_start_command(product, dry_run=False)
            commands.append(cmd)
        else:
            service_results.append(
                {
                    "service": svc,
                    "action": "blocked",
                    "reason": "service not supported by lifecycle reconciler",
                    "container_name": cname,
                    "ports": svc_ports,
                    "labels": labels,
                    "commands": [],
                    "findings": [],
                }
            )
            overall_fail = True
            continue

        if dry_run:
            service_results.append(
                {
                    "service": svc,
                    "action": "start",
                    "reason": "planned",
                    "container_name": cname,
                    "ports": svc_ports,
                    "labels": labels,
                    "runtime_files": list(artifact_paths.values()),
                    "commands": [dr.redact_command(c) for c in commands],
                    "preflight_findings": [],
                }
            )
            continue

        # Apply
        if svc in {"conport", "dope-memory"}:
            # Ensure data dir for memory
            if svc == "dope-memory":
                memory_data.mkdir(parents=True, exist_ok=True)
            result = dr.run_cmd(
                commands[0],
                runner=cmd_runner,
                cwd=product,
                dry_run=False,
            )
            action = "started" if result.exit_code == 0 else "failed"
            if result.exit_code != 0:
                overall_fail = True
            probe = _probe_service(svc, ports, is_free)
            if not dry_run and result.exit_code == 0:
                _registry_upsert(
                    registry,
                    svc=svc,
                    project_id=project_id,
                    identity=identity,
                    project_root=project_root,
                    worktree_root=worktree_root,
                    project_hash=project_hash,
                    worktree_hash=worktree_hash,
                    slug=slug,
                    compose_proj=compose_proj,
                    container_names=[cname],
                    ports=svc_ports,
                    labels=labels,
                    status="running" if probe != "FAIL" else "unhealthy",
                    last_start={
                        "command": [dr.redact_command(commands[0])],
                        "exit_code": result.exit_code,
                    },
                    last_probe={"status": probe},
                )
            service_results.append(
                {
                    "service": svc,
                    "action": action,
                    "container_names": [cname],
                    "ports": svc_ports,
                    "probe_status": probe,
                    "registry_updated": result.exit_code == 0,
                    "findings": [],
                    "commands": [dr.redact_command(commands[0])],
                    "result": result.to_dict(),
                }
            )
        elif svc == "task-orchestrator":
            # Run wrapper with project identity env so container name matches registry.
            env = dict(os_environ_safe(doctor_env))
            env["TASK_ORCHESTRATOR_PROJECT_ROOT"] = project_root
            env["DOPEMUX_PROJECT_ROOT"] = project_root
            env["DOPEMUX_WORKTREE_ROOT"] = worktree_root
            env["DOPEMUX_WORKSPACE_ROOT"] = worktree_root
            # Use lifecycle project identity (slug-hash), not envrc worktree instance id.
            to_id = project_id
            cname_expected = container_names.get("task-orchestrator") or ""
            if cname_expected.startswith("task-orchestrator-"):
                to_id = cname_expected[len("task-orchestrator-") :]
            env["DOPEMUX_PROJECT_ID"] = to_id
            # Wrapper prefers DOPEMUX_PROJECT_ID for naming; clear stale instance id override path
            env["DOPEMUX_INSTANCE_ID"] = to_id
            env["TASK_ORCHESTRATOR_HTTP_PORT"] = str(
                ports.get("TASK_ORCHESTRATOR_HTTP_PORT", 7890)
            )
            result = dr.run_cmd(
                commands[0],
                runner=cmd_runner,
                env=env,
                cwd=Path(worktree_root),
                dry_run=False,
            )
            action = "started" if result.exit_code == 0 else "failed"
            if result.exit_code != 0:
                overall_fail = True
            probe = _probe_service(svc, ports, is_free)
            # Identity may be unproven for TO wrapper (labels not applied by wrapper)
            if result.exit_code == 0 and probe != "FAIL":
                overall_unknown = True  # labels not guaranteed
            actual_name = cname
            if result.exit_code == 0:
                _registry_upsert(
                    registry,
                    svc=svc,
                    project_id=project_id,
                    identity=identity,
                    project_root=project_root,
                    worktree_root=worktree_root,
                    project_hash=project_hash,
                    worktree_hash=worktree_hash,
                    slug=slug,
                    compose_proj=compose_proj,
                    container_names=[actual_name],
                    ports=svc_ports,
                    labels=labels,
                    status="running",
                    last_start={
                        "command": [dr.redact_command(commands[0])],
                        "exit_code": result.exit_code,
                        "note": dr.apply_labels_via_docker_run_note(),
                    },
                    last_probe={"status": probe},
                )
            service_results.append(
                {
                    "service": svc,
                    "action": action,
                    "container_names": [actual_name],
                    "ports": svc_ports,
                    "probe_status": "UNKNOWN" if result.exit_code == 0 else "FAIL",
                    "registry_updated": result.exit_code == 0,
                    "findings": [
                        {
                            "code": "TASK_ORCHESTRATOR_PROJECT_IDENTITY_UNKNOWN",
                            "severity": "UNKNOWN",
                            "message": (
                                "Wrapper-singleton start does not apply dopemux labels; "
                                "ownership proof is limited"
                            ),
                        }
                    ]
                    if result.exit_code == 0
                    else [],
                    "commands": [dr.redact_command(commands[0])],
                    "result": result.to_dict(),
                }
            )

    if not dry_run and registry.parse_status != "ERROR":
        try:
            registry.path = reg_path
            if not registry.present and registry.parse_status == "MISSING":
                registry.data = registry.data or {}
                from .runtime_registry import empty_registry

                if not registry.data.get("instances"):
                    registry.data = empty_registry()
                registry.parse_status = "OK"
            registry.save()
        except RegistryError:
            overall_fail = True

    if dry_run:
        status = "PLANNED"
        exit_code = 0
    elif overall_fail:
        status = "FAIL"
        exit_code = 1
    elif overall_unknown:
        status = "PASS_WITH_WARNINGS"
        exit_code = 0
    else:
        status = "PASS"
        exit_code = 0

    return LifecycleResult(
        schema_version=SCHEMA_VERSION,
        operation="start",
        dry_run=dry_run,
        status=status,
        project_identity=identity_dict,
        services=service_results,
        blocking_findings=[],
        warnings=[],
        registry_path=str(reg_path),
        runtime_artifacts=list(artifact_paths.values()),
        exit_code=exit_code,
        recommended_next_actions=[
            "source .envrc.dopemux-mcp && claude",
            "dopemux mcp doctor --repo " + str(target),
        ],
    )


def os_environ_safe(base: Mapping[str, str]) -> Dict[str, str]:
    import os

    env = dict(os.environ)
    env.update({k: str(v) for k, v in base.items()})
    return env


def _registry_upsert(registry: RuntimeRegistry, **kw: Any) -> None:
    svc = kw["svc"]
    slug = kw["slug"]
    worktree_hash = kw["worktree_hash"]
    iid = _service_instance_id(slug, worktree_hash, svc)
    identity = kw["identity"]
    ports = kw["ports"]
    # Prefer friendly port map
    port_map = {k: v for k, v in ports.items() if not str(k).isupper() or True}
    urls = _urls_for_service(
        svc,
        {
            **(
                {
                    "CONPORT_HTTP_PORT": ports.get("http") or ports.get("CONPORT_HTTP_PORT"),
                    "CONPORT_MCP_PORT": ports.get("sse") or ports.get("CONPORT_MCP_PORT"),
                    "CONPORT_INFO_PORT": ports.get("info") or ports.get("CONPORT_INFO_PORT"),
                    "DOPE_MEMORY_PORT": ports.get("http") or ports.get("DOPE_MEMORY_PORT"),
                    "TASK_ORCHESTRATOR_HTTP_PORT": ports.get("http")
                    or ports.get("TASK_ORCHESTRATOR_HTTP_PORT"),
                }
            ),
            **{k: v for k, v in ports.items() if isinstance(v, int)},
        },
    )
    # Clean None from port helper
    clean_ports = {
        k: int(v)
        for k, v in ports.items()
        if v is not None and (isinstance(v, int) or str(v).isdigit())
    }
    rec = build_instance_record(
        instance_id=iid,
        project_id=kw["project_id"],
        workspace_id=identity.workspace_id or kw["worktree_root"],
        project_root=kw["project_root"],
        worktree_root=kw["worktree_root"],
        worktree_hash=worktree_hash,
        project_hash=kw["project_hash"],
        service=svc,
        scope=kw["labels"].get("dopemux.scope", "worktree"),
        status=kw["status"],
        ports=clean_ports,
        urls=urls,
        container_names=kw["container_names"],
        compose_project_name=kw["compose_proj"],
        labels=kw["labels"],
        last_start=kw.get("last_start"),
        last_probe=kw.get("last_probe"),
    )
    if registry.parse_status == "MISSING":
        from .runtime_registry import empty_registry

        registry.data = empty_registry()
        registry.parse_status = "OK"
    registry.upsert_instance(rec)


def _probe_service(service: str, ports: Mapping[str, int], is_free: Callable[[int], bool]) -> str:
    try:
        if service == "conport":
            p = ports.get("CONPORT_HTTP_PORT") or ports.get("http")
            if p is None:
                return "UNKNOWN"
            return "OK" if not is_free(int(p)) else "FAIL"
        if service == "dope-memory":
            p = ports.get("DOPE_MEMORY_PORT") or ports.get("http")
            if p is None:
                return "UNKNOWN"
            return "OK" if not is_free(int(p)) else "FAIL"
        if service == "task-orchestrator":
            p = ports.get("TASK_ORCHESTRATOR_HTTP_PORT") or ports.get("http")
            if p is None:
                return "UNKNOWN"
            return "OK" if not is_free(int(p)) else "FAIL"
    except Exception:  # noqa: BLE001
        return "UNKNOWN"
    return "UNKNOWN"


def _stop_services(**kw: Any) -> LifecycleResult:
    selected = kw["selected"]
    identity_dict = kw["identity_dict"]
    project_id = kw["project_id"]
    worktree_root = kw["worktree_root"]
    container_names = kw["container_names"]
    registry: RuntimeRegistry = kw["registry"]
    docker: di.DockerInspectResult = kw["docker"]
    dry_run = kw["dry_run"]
    reg_path = kw["reg_path"]
    cmd_runner = kw["cmd_runner"]
    catalog = kw["catalog"]
    ports = kw["ports"]

    results = []
    fail = False

    for svc in selected:
        cname = container_names[svc]
        # Prefer registry names
        reg_hits = registry.find(
            project_id=project_id, worktree_root=worktree_root, service=svc
        )
        names = []
        for hit in reg_hits:
            names.extend(hit.get("container_names") or [])
        if cname not in names:
            names.append(cname)

        targets_to_stop = []
        for name in names:
            match = None
            for c in docker.containers if docker.available else []:
                if c.name == name:
                    match = c
                    break
            if not match:
                results.append(
                    {
                        "service": svc,
                        "action": "skip" if dry_run else "already_stopped",
                        "reason": f"container {name} not running",
                        "container_name": name,
                        "commands": [],
                    }
                )
                continue
            labels = match.labels or {}
            if labels.get(dr.LABEL_MANAGED) != "true":
                # TO wrapper containers lack labels — allow stop only if registry knows them
                if svc == "task-orchestrator" and reg_hits:
                    targets_to_stop.append(match)
                    continue
                results.append(
                    {
                        "service": svc,
                        "action": "blocked",
                        "reason": f"refusing to stop unlabeled container {match.name}",
                        "container_name": match.name,
                        "commands": [],
                    }
                )
                fail = True
                continue
            if labels.get("dopemux.project_id") != project_id:
                results.append(
                    {
                        "service": svc,
                        "action": "blocked",
                        "reason": f"wrong project labels on {match.name}",
                        "container_name": match.name,
                        "commands": [],
                    }
                )
                fail = True
                continue
            targets_to_stop.append(match)

        for match in targets_to_stop:
            cmd = dr.docker_stop_command(match.name)
            if dry_run:
                results.append(
                    {
                        "service": svc,
                        "action": "stop",
                        "reason": "planned",
                        "container_name": match.name,
                        "commands": [dr.redact_command(cmd)],
                    }
                )
            else:
                res = dr.run_cmd(cmd, runner=cmd_runner)
                if res.exit_code != 0:
                    fail = True
                results.append(
                    {
                        "service": svc,
                        "action": "stopped" if res.exit_code == 0 else "failed",
                        "container_name": match.name,
                        "commands": [dr.redact_command(cmd)],
                        "result": res.to_dict(),
                    }
                )
                if res.exit_code == 0:
                    registry.mark_stopped(
                        project_id=project_id,
                        service=svc,
                        worktree_root=worktree_root,
                    )

    if not dry_run and registry.parse_status == "OK":
        try:
            registry.save()
        except RegistryError:
            fail = True

    return LifecycleResult(
        schema_version=SCHEMA_VERSION,
        operation="stop",
        dry_run=dry_run,
        status="PLANNED" if dry_run else ("FAIL" if fail else "PASS"),
        project_identity=identity_dict,
        services=results,
        registry_path=str(reg_path),
        exit_code=1 if fail and not dry_run else 0,
    )


def _status_result(**kw: Any) -> LifecycleResult:
    selected = kw["selected"]
    identity_dict = kw["identity_dict"]
    registry: RuntimeRegistry = kw["registry"]
    docker: di.DockerInspectResult = kw["docker"]
    doctor = kw["doctor"]
    container_names = kw["container_names"]
    ports = kw["ports"]
    project_id = kw["project_id"]
    worktree_root = kw["worktree_root"]
    catalog = kw["catalog"]
    is_free = kw["is_free"]
    reg_path = kw["reg_path"]
    warnings = kw["warnings"]

    services_out = []
    overall = "PASS"
    for svc in selected:
        reg_hits = registry.find(
            project_id=project_id, worktree_root=worktree_root, service=svc
        )
        reg_state = "missing"
        if reg_hits:
            statuses = {h.get("status") for h in reg_hits}
            if "running" in statuses:
                reg_state = "running"
            elif "stopped" in statuses:
                reg_state = "stopped"
            else:
                reg_state = str(next(iter(statuses)) or "unknown")

        cname = container_names.get(svc)
        docker_state = "missing"
        findings = []
        if docker.available and cname:
            for c in docker.containers:
                if c.name == cname or cname in c.name:
                    labels = c.labels or {}
                    if labels.get(dr.LABEL_MANAGED) != "true":
                        docker_state = "unlabeled_unknown"
                        findings.append(
                            {
                                "code": "DOCKER_CONTAINER_UNLABELED_UNKNOWN",
                                "severity": "UNKNOWN",
                                "message": f"{c.name} unlabeled",
                            }
                        )
                    elif labels.get("dopemux.project_id") != project_id:
                        docker_state = "wrong_project"
                        findings.append(
                            {
                                "code": "DOCKER_CONTAINER_WRONG_PROJECT",
                                "severity": "FAIL",
                                "message": f"{c.name} wrong project",
                            }
                        )
                    else:
                        docker_state = "running"
                    break
        elif not docker.available:
            docker_state = "unknown"

        svc_ports = _ports_for_service(svc, ports, catalog)
        probe_state = "skipped"
        listen_port = None
        if svc == "conport":
            listen_port = ports.get("CONPORT_HTTP_PORT")
        elif svc == "dope-memory":
            listen_port = ports.get("DOPE_MEMORY_PORT")
        elif svc == "task-orchestrator":
            listen_port = ports.get("TASK_ORCHESTRATOR_HTTP_PORT")
        if listen_port is not None:
            try:
                if is_free(int(listen_port)):
                    probe_state = "not_listening"
                else:
                    probe_state = "healthy" if docker_state == "running" else "unknown"
            except Exception:  # noqa: BLE001
                probe_state = "unknown"

        # overall per service
        if docker_state == "wrong_project":
            svc_overall = "FAIL"
            overall = "FAIL"
        elif docker_state == "unlabeled_unknown":
            svc_overall = "UNKNOWN"
            if overall == "PASS":
                overall = "UNKNOWN"
        elif reg_state == "running" and docker_state == "missing":
            svc_overall = "WARN"
            reg_state = "stale"
            if overall == "PASS":
                overall = "PASS_WITH_WARNINGS"
        elif docker_state == "running" and probe_state == "not_listening":
            svc_overall = "WARN"
            if overall == "PASS":
                overall = "PASS_WITH_WARNINGS"
        elif docker_state == "running":
            svc_overall = "PASS"
        else:
            svc_overall = "UNKNOWN" if docker_state == "unknown" else "WARN"
            if svc_overall == "UNKNOWN" and overall == "PASS":
                overall = "UNKNOWN"
            elif svc_overall == "WARN" and overall == "PASS":
                overall = "PASS_WITH_WARNINGS"

        services_out.append(
            {
                "service": svc,
                "desired": {
                    "container_name": cname,
                    "ports": svc_ports,
                    "urls": _urls_for_service(svc, ports),
                },
                "registry_state": reg_state,
                "docker_state": docker_state,
                "probe_state": probe_state,
                "overall": svc_overall,
                "findings": findings,
            }
        )

    exit_code = 0
    if overall == "FAIL":
        exit_code = 1
    elif overall == "UNKNOWN":
        exit_code = 2

    return LifecycleResult(
        schema_version=SCHEMA_VERSION,
        operation="status",
        dry_run=False,
        status=overall,
        project_identity=identity_dict,
        services=services_out,
        warnings=warnings,
        registry_path=str(reg_path),
        registry=registry.to_report_dict(),
        docker=docker.to_dict(),
        exit_code=exit_code,
        recommended_next_actions=[
            "dopemux mcp start --repo <path>" if overall != "PASS" else "No action required",
        ],
    )


def format_lifecycle_human(result: LifecycleResult) -> str:
    lines = [
        f"MCP {result.operation}: {result.status}"
        + (" (dry-run)" if result.dry_run else "")
    ]
    pid = result.project_identity.get("project_id") or "?"
    lines.append(f"Project: {pid}")
    for s in result.services[:10]:
        svc = s.get("service")
        action = s.get("action") or s.get("overall") or s.get("docker_state")
        lines.append(f"  • {svc}: {action}")
    if result.blocking_findings:
        lines.append(f"Blocking: {len(result.blocking_findings)}")
        for f in result.blocking_findings[:5]:
            lines.append(f"  - {f.get('code')}: {f.get('message')}")
    if result.recommended_next_actions:
        lines.append(f"Next: {result.recommended_next_actions[0]}")
    return "\n".join(lines) + "\n"
