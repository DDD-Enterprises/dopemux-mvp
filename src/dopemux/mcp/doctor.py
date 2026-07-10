"""Repo-aware MCP doctor — read-only truth and safety gate.

Loads target-repo `.envrc.dopemux-mcp`, validates catalog transport truth,
detects port collision risks, compose lifecycle drift, and Docker ownership
where labels exist. Never starts/stops containers or mutates config.
"""

from __future__ import annotations

import json
import socket
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence
from urllib.parse import urlparse

from . import docker_inspect as di
from . import port_diagnostics as pd
from .envrc import (
    load_envrc,
    merge_envrc_into_environ,
    redact_value,
    safe_port_int,
)
from .runtime_state import (
    ENVRC_FILENAME,
    PROJECT_MCP_FILENAME,
    build_desired_services,
    catalog_service_summary,
    compose_lifecycle_diagnostics,
    load_global_claude,
    load_mcp_json,
    resolve_identity_view,
)

# Re-export for callers
__all__ = ["DoctorReport", "run_mcp_doctor", "format_human_summary", "SCHEMA_VERSION"]

SCHEMA_VERSION = "1.0"

Severity = str  # INFO | WARN | FAIL | UNKNOWN


@dataclass
class Finding:
    code: str
    severity: Severity
    service: Optional[str]
    message: str
    evidence: List[str] = field(default_factory=list)
    recommendation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity,
            "service": self.service,
            "message": self.message,
            "evidence": list(self.evidence),
            "recommendation": self.recommendation,
        }


@dataclass
class DoctorReport:
    schema_version: str
    status: str
    repo_arg: str
    project_identity: Dict[str, Any]
    config_sources: Dict[str, Any]
    desired_services: List[Dict[str, Any]]
    actual_services: List[Dict[str, Any]]
    port_diagnostics: Dict[str, Any]
    compose_lifecycle_diagnostics: Dict[str, Any]
    findings: List[Dict[str, Any]]
    unknowns: List[str]
    recommended_next_actions: List[str]
    exit_code: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "repo_arg": self.repo_arg,
            "project_identity": self.project_identity,
            "config_sources": self.config_sources,
            "desired_services": self.desired_services,
            "actual_services": self.actual_services,
            "port_diagnostics": self.port_diagnostics,
            "compose_lifecycle_diagnostics": self.compose_lifecycle_diagnostics,
            "findings": self.findings,
            "unknowns": self.unknowns,
            "recommended_next_actions": self.recommended_next_actions,
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True) + "\n"


def _port_is_free(port: int, host: str = "127.0.0.1") -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.5)
    try:
        return sock.connect_ex((host, port)) != 0
    finally:
        sock.close()


def _add(
    findings: List[Finding],
    code: str,
    severity: Severity,
    message: str,
    *,
    service: Optional[str] = None,
    evidence: Optional[Sequence[str]] = None,
    recommendation: str = "",
) -> None:
    findings.append(
        Finding(
            code=code,
            severity=severity,
            service=service,
            message=message,
            evidence=list(evidence or []),
            recommendation=recommendation,
        )
    )


def _summarize_status(findings: List[Finding]) -> tuple[str, int]:
    """Return (status, exit_code)."""
    sevs = {f.severity for f in findings}
    if "FAIL" in sevs:
        return "FAIL", 1
    # UNKNOWN without FAIL → exit 2 if identity/tool failure class codes present
    unknown_blocking = {
        "PROJECT_IDENTITY_UNKNOWN",
        "DOCKER_UNAVAILABLE",
        "MCP_DOCTOR_UNKNOWN",
        "WORKTREE_ROOT_UNKNOWN",
        "PROJECT_ROOT_UNKNOWN",
        "TASK_ORCHESTRATOR_PROJECT_IDENTITY_UNKNOWN",
        "TASK_ORCHESTRATOR_FIXED_PORT_OCCUPIED_UNKNOWN",
        "TASK_ORCHESTRATOR_STATUS_UNKNOWN",
    }
    has_blocking_unknown = any(
        f.severity == "UNKNOWN" and f.code in unknown_blocking for f in findings
    )
    has_any_unknown = any(f.severity == "UNKNOWN" for f in findings)
    if "WARN" in sevs and not has_blocking_unknown:
        # PASS_WITH_WARNINGS even if ownership UNKNOWN INFO-level codes exist
        if has_any_unknown and not any(f.severity == "FAIL" for f in findings):
            # ownership unknowns alone → still PASS_WITH_WARNINGS if only WARN+UNKNOWN
            return "PASS_WITH_WARNINGS", 0
        return "PASS_WITH_WARNINGS", 0
    if has_blocking_unknown:
        return "UNKNOWN", 2
    if has_any_unknown and "WARN" not in sevs and "FAIL" not in sevs:
        # Listening ports with ownership unknown → not a green pass
        return "UNKNOWN", 2
    if "WARN" in sevs:
        return "PASS_WITH_WARNINGS", 0
    return "PASS", 0


def run_mcp_doctor(
    repo: str | Path,
    *,
    catalog: Mapping[str, Any],
    catalog_paths_checked: Optional[Sequence[str]] = None,
    compose_path: Optional[Path] = None,
    global_claude_path: Optional[Path] = None,
    docker_runner: Optional[Callable[..., Any]] = None,
    port_is_free_fn: Optional[Callable[[int], bool]] = None,
    skip_docker: bool = False,
    skip_port_probe: bool = False,
    process_env: Optional[Mapping[str, str]] = None,
) -> DoctorReport:
    """
    Run the full read-only doctor against ``repo``.

    Parameters allow injection of catalog/docker/port probes for unit tests.
    """
    repo_path = Path(repo).expanduser().resolve()
    repo_arg = str(repo)
    findings: List[Finding] = []
    unknowns: List[str] = []
    next_actions: List[str] = []
    is_free = port_is_free_fn or _port_is_free

    # --- Config sources ---
    envrc_path = repo_path / ENVRC_FILENAME
    mcp_path = repo_path / PROJECT_MCP_FILENAME
    envrc = load_envrc(envrc_path)
    mcp_json = load_mcp_json(mcp_path)
    global_claude = load_global_claude(global_claude_path)

    if envrc.present and envrc.parse_status in {"OK", "PARTIAL"}:
        _add(findings, "ENVRC_FOUND", "INFO", f"Found {ENVRC_FILENAME}", evidence=[str(envrc_path)])
        if envrc.parse_status == "PARTIAL":
            _add(
                findings,
                "ENVRC_PARTIAL_PARSE",
                "WARN",
                (
                    f"Partial parse of {ENVRC_FILENAME}: "
                    f"{len(envrc.values)} keys loaded, {len(envrc.errors)} malformed line(s)"
                ),
                evidence=envrc.errors,
                recommendation="Fix malformed lines or regenerate .envrc.dopemux-mcp.",
            )
    elif not envrc.present:
        # Severity depends on whether mcp.json expects env-derived ports
        mcp_needs_env = False
        for svc in mcp_json.get("services") or []:
            url = svc.get("url") or ""
            if "${" in str(url):
                mcp_needs_env = True
                break
        sev: Severity = "FAIL" if mcp_needs_env or mcp_json.get("present") else "WARN"
        _add(
            findings,
            "ENVRC_MISSING",
            sev,
            f"Missing {ENVRC_FILENAME}",
            evidence=[str(envrc_path)],
            recommendation="Run `dopemux mcp init` in the target repo (after port allocator is safe).",
        )
    else:
        _add(
            findings,
            "ENVRC_PARSE_ERROR",
            "FAIL",
            f"Failed to parse {ENVRC_FILENAME}: {'; '.join(envrc.errors) or 'unknown error'}",
            evidence=envrc.errors,
            recommendation="Fix or regenerate .envrc.dopemux-mcp.",
        )

    if mcp_json["present"] and mcp_json["parse_status"] == "OK":
        _add(findings, "MCP_JSON_FOUND", "INFO", f"Found {PROJECT_MCP_FILENAME}", evidence=[str(mcp_path)])
    elif not mcp_json["present"]:
        _add(
            findings,
            "MCP_JSON_MISSING",
            "FAIL",
            f"Missing {PROJECT_MCP_FILENAME}",
            evidence=[str(mcp_path)],
            recommendation="Run `dopemux mcp init` in the target repo.",
        )
    else:
        _add(
            findings,
            "MCP_JSON_PARSE_ERROR",
            "FAIL",
            f"Failed to parse {PROJECT_MCP_FILENAME}: {mcp_json.get('error')}",
            evidence=[str(mcp_json.get("error"))],
            recommendation="Fix JSON syntax in .mcp.json.",
        )

    # Merge env: process env + envrc (envrc wins for doctor inspection)
    base_env = dict(process_env if process_env is not None else {})
    doctor_env = merge_envrc_into_environ(base_env, envrc, override=True)

    # --- Identity ---
    identity = resolve_identity_view(repo_path, envrc_values=doctor_env)
    if identity.identity_confidence in {"HIGH", "MEDIUM"} and identity.project_id:
        _add(
            findings,
            "PROJECT_IDENTITY_RESOLVED",
            "INFO",
            f"Resolved project identity {identity.project_id}",
            evidence=identity.evidence,
        )
    else:
        _add(
            findings,
            "PROJECT_IDENTITY_UNKNOWN",
            "UNKNOWN",
            "Could not fully resolve project identity",
            evidence=identity.evidence,
            recommendation="Ensure target path is a git repo or set DOPEMUX_PROJECT_ROOT.",
        )
        unknowns.append("project_identity incomplete")

    if not identity.worktree_root:
        _add(findings, "WORKTREE_ROOT_UNKNOWN", "UNKNOWN", "Worktree root unknown")
        unknowns.append("worktree_root")
    if not identity.project_root:
        _add(findings, "PROJECT_ROOT_UNKNOWN", "UNKNOWN", "Project root unknown")
        unknowns.append("project_root")
    elif identity.worktree_root and identity.project_root != identity.worktree_root:
        _add(
            findings,
            "PROJECT_ROOT_DIFFERS_FROM_WORKTREE",
            "INFO",
            f"Project root {identity.project_root} differs from worktree {identity.worktree_root}",
            evidence=identity.evidence,
        )

    # --- Desired services ---
    mcp_servers = mcp_json.get("servers") or {}
    service_names = list(mcp_servers.keys()) if mcp_servers else list(
        (catalog.get("defaults") or {}).get("per_worktree") or []
    )

    # Configured ports from envrc
    configured_ports: Dict[str, int] = {}
    for name in service_names:
        spec = (catalog.get("servers") or {}).get(name) or {}
        if not isinstance(spec, dict):
            continue
        for key in [spec.get("port_var")] + [
            e.get("var") for e in (spec.get("extra_port_vars") or []) if isinstance(e, dict)
        ]:
            if not key:
                continue
            port = safe_port_int(doctor_env, str(key))
            if port is not None:
                configured_ports[str(key)] = port
            elif envrc.present and envrc.parse_status in {"OK", "PARTIAL"}:
                _add(
                    findings,
                    "PORT_UNSET",
                    "WARN",
                    f"Port env {key} unset in envrc/process for service `{name}`",
                    service=name,
                    evidence=[str(key)],
                    recommendation=f"Source {ENVRC_FILENAME} or re-run init.",
                )

    desired = build_desired_services(
        catalog, mcp_servers, doctor_env, configured_ports=configured_ports
    )

    # --- Transport validation ---
    for svc in desired:
        cat_t = (svc.catalog_transport or "unknown").lower()
        mcp_t = (svc.mcp_json_transport or "").lower() if svc.mcp_json_transport else None
        catalog_has = svc.name in (catalog.get("servers") or {})
        if not catalog_has:
            _add(
                findings,
                "CATALOG_SERVICE_UNKNOWN",
                "WARN",
                f"Service `{svc.name}` in .mcp.json is not in catalog",
                service=svc.name,
                evidence=[svc.name],
            )
            continue
        if cat_t in {"", "unknown", "none"}:
            _add(
                findings,
                "CATALOG_TRANSPORT_UNKNOWN",
                "UNKNOWN",
                f"Catalog transport unknown for `{svc.name}`",
                service=svc.name,
            )
            unknowns.append(f"transport:{svc.name}")
            continue
        if mcp_t is None:
            continue
        if mcp_t == cat_t:
            _add(
                findings,
                "TRANSPORT_MATCH",
                "INFO",
                f"`{svc.name}` transport matches catalog ({cat_t})",
                service=svc.name,
                evidence=[f"catalog={cat_t}", f"mcp_json={mcp_t}"],
            )
        else:
            _add(
                findings,
                "TRANSPORT_MISMATCH",
                "FAIL",
                f"`{svc.name}` expected transport {cat_t}, found {mcp_t} in .mcp.json",
                service=svc.name,
                evidence=[f"catalog={cat_t}", f"mcp_json={mcp_t}"],
                recommendation=(
                    "Fix .mcp.json type to match mcp_catalog.yaml. "
                    "Streamable HTTP must remain type=http; SSE must remain type=sse."
                ),
            )

    # --- Port diagnostics + lease registry ---
    worktree_for_ports = identity.worktree_root or str(repo_path)
    project_root_for_ports = identity.project_root

    lease_registry_present = False
    lease_allocator_healthy = False
    try:
        from .port_leases import PortLeaseRegistry

        lease_reg = PortLeaseRegistry.load()
        if lease_reg.parse_status == "ERROR":
            _add(
                findings,
                "LEASE_REGISTRY_PARSE_ERROR",
                "FAIL",
                f"Lease registry unreadable: {lease_reg.error}",
                evidence=[str(lease_reg.path)],
                recommendation="Inspect ~/.dopemux/mcp/runtime/port-leases.json or set DOPEMUX_MCP_PORT_LEASE_REGISTRY.",
            )
        elif lease_reg.parse_status == "MISSING":
            _add(
                findings,
                "LEASE_REGISTRY_MISSING",
                "WARN",
                f"No lease registry at {lease_reg.path}",
                evidence=[str(lease_reg.path)],
                recommendation="Run `dopemux mcp init` or `dopemux mcp repair-config --apply` to create leases.",
            )
            if envrc.present and configured_ports:
                _add(
                    findings,
                    "LEGACY_ENVRC_WITHOUT_LEASE",
                    "WARN",
                    "Envrc ports present without lease registry entries",
                    recommendation="Run `dopemux mcp repair-config --apply` to migrate ports into leases.",
                )
        else:
            lease_registry_present = True
            _add(
                findings,
                "LEASE_REGISTRY_FOUND",
                "INFO",
                f"Lease registry OK ({len(lease_reg.active_leases())} active)",
                evidence=[str(lease_reg.path)],
            )
            # Envrc vs lease mismatch
            for var, port in (configured_ports or {}).items():
                matched = False
                foreign = False
                for L in lease_reg.active_leases():
                    if int(L.get("port") or 0) != int(port):
                        continue
                    if L.get("worktree_root") in {worktree_for_ports, str(repo_path)} or (
                        L.get("worktree_hash") and L.get("worktree_hash") == identity.worktree_hash
                    ):
                        matched = True
                    else:
                        foreign = True
                if foreign and not matched:
                    _add(
                        findings,
                        "LEASE_BELONGS_TO_OTHER_PROJECT",
                        "FAIL",
                        f"Envrc {var}={port} is leased to another project/worktree",
                        evidence=[f"{var}={port}"],
                        recommendation="Run `dopemux mcp repair-config --apply` to rebind.",
                    )
                elif not matched:
                    # no lease for this envrc port
                    ours = [
                        L
                        for L in lease_reg.active_leases()
                        if L.get("port_var") == var
                        and (
                            L.get("worktree_root") in {worktree_for_ports, str(repo_path)}
                            or L.get("worktree_hash") == identity.worktree_hash
                        )
                    ]
                    if ours and int(ours[0].get("port") or 0) != int(port):
                        _add(
                            findings,
                            "LEASE_ENVRC_MISMATCH",
                            "FAIL",
                            f"Envrc {var}={port} != lease {ours[0].get('port')}",
                            evidence=[f"envrc={port}", f"lease={ours[0].get('port')}"],
                            recommendation="Run `dopemux mcp repair-config --apply`.",
                        )
                    elif not ours:
                        _add(
                            findings,
                            "LEGACY_ENVRC_WITHOUT_LEASE",
                            "WARN",
                            f"Envrc {var}={port} has no active lease for this worktree",
                            recommendation="Run `dopemux mcp repair-config --apply`.",
                        )
                else:
                    lease_allocator_healthy = True
                    if not is_free(int(port)):
                        _add(
                            findings,
                            "LEASE_PORT_OCCUPIED",
                            "INFO",
                            f"Leased port {port} ({var}) is listening (expected if services are up)",
                            evidence=[f"{var}={port}"],
                        )
                    else:
                        _add(
                            findings,
                            "LEASE_PORT_FREE",
                            "INFO",
                            f"Leased port {port} ({var}) is free (services may be stopped)",
                            evidence=[f"{var}={port}"],
                        )
            # Stale leases for this worktree (active but free + no configured use)
            for L in lease_reg.active_leases():
                if L.get("worktree_root") not in {worktree_for_ports, str(repo_path)}:
                    continue
                lp = int(L.get("port") or 0)
                if not lp:
                    continue
                if is_free(lp) and (
                    not configured_ports
                    or L.get("port_var") not in configured_ports
                    or configured_ports.get(str(L.get("port_var"))) != lp
                ):
                    # only mark stale-ish when no envrc owns it
                    if not configured_ports or str(L.get("port_var")) not in configured_ports:
                        _add(
                            findings,
                            "LEASE_STALE",
                            "WARN",
                            f"Active lease {L.get('lease_id')} port {lp} looks unused",
                            service=L.get("service"),
                            evidence=[str(L.get("lease_id")), f"port={lp}"],
                            recommendation="Explicit prune is not auto-run; re-init/repair if needed.",
                        )
    except Exception as exc:  # noqa: BLE001 — doctor remains best-effort
        unknowns.append(f"lease registry inspection failed: {exc}")

    port_report = pd.diagnose_ports(
        worktree_for_ports,
        service_names,
        catalog,
        project_root=project_root_for_ports,
        configured_ports=configured_ports or None,
        has_lease_registry=lease_registry_present,
        has_live_rebind=lease_allocator_healthy or lease_registry_present,
    )
    for fdict in port_report.findings:
        # Downgrade legacy hash bucket noise when lease allocator is active
        code = fdict.get("code") or ""
        sev = fdict.get("severity") or "INFO"
        if lease_registry_present and code in {
            "PORT_HASH_BUCKET_COLLISION_RISK",
            "PORT_REBIND_MISSING",
        }:
            sev = "INFO"
            fdict = dict(fdict)
            fdict["message"] = (
                f"{fdict.get('message', '')} (lease allocator active — preferred formula only)"
            )
            fdict["severity"] = sev
        findings.append(
            Finding(
                code=fdict["code"],
                severity=fdict["severity"],
                service=fdict.get("service"),
                message=fdict["message"],
                evidence=list(fdict.get("evidence") or []),
                recommendation=fdict.get("recommendation") or "",
            )
        )

    # Port listening probes
    if not skip_port_probe and configured_ports:
        for fdict in pd.ports_listening_check(configured_ports, is_free_fn=is_free):
            findings.append(
                Finding(
                    code=fdict["code"],
                    severity=fdict["severity"],
                    service=fdict.get("service"),
                    message=fdict["message"],
                    evidence=list(fdict.get("evidence") or []),
                    recommendation=fdict.get("recommendation") or "",
                )
            )

    # mcp.json vs envrc port mismatch (expanded default vs configured)
    if envrc.present and mcp_json.get("parse_status") == "OK":
        for name, entry in (mcp_servers or {}).items():
            if not isinstance(entry, dict):
                continue
            url = entry.get("url") or ""
            # Extract ${VAR:-default} defaults and compare to envrc
            import re as _re

            for match in _re.finditer(
                r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([0-9]+))?\}", str(url)
            ):
                var, default = match.group(1), match.group(2)
                env_port = safe_port_int(doctor_env, var)
                if env_port is not None and default is not None and int(default) != env_port:
                    # Not necessarily a mismatch error — templates use defaults when unset.
                    # Flag only when URL hardcodes a different literal after expansion would differ.
                    pass
            # If both envrc and formula disagree with a literal port in url without placeholder
            if url and "${" not in str(url):
                try:
                    parsed = urlparse(str(url))
                    if parsed.port and configured_ports:
                        expected = next(iter(configured_ports.values()), None)
                        # Compare service-specific
                        spec = (catalog.get("servers") or {}).get(name) or {}
                        pvar = spec.get("port_var")
                        if pvar and pvar in configured_ports and configured_ports[pvar] != parsed.port:
                            _add(
                                findings,
                                "MCP_JSON_ENVRC_PORT_MISMATCH",
                                "FAIL",
                                (
                                    f"`{name}` .mcp.json URL port {parsed.port} != "
                                    f"envrc {pvar}={configured_ports[pvar]}"
                                ),
                                service=name,
                                evidence=[str(url), f"{pvar}={configured_ports[pvar]}"],
                                recommendation="Align .mcp.json URL with .envrc.dopemux-mcp ports.",
                            )
                except Exception:  # noqa: BLE001
                    pass

    # --- Compose lifecycle ---
    # Prefer explicit compose_path; else try dopemux-mvp-style only if present under repo
    effective_compose = compose_path
    if effective_compose is None:
        candidate = repo_path / "compose.yml"
        if candidate.is_file():
            effective_compose = candidate
        else:
            # Also check cwd (lifecycle hazard: up uses cwd) without requiring it
            cwd_compose = Path.cwd() / "compose.yml"
            if cwd_compose.is_file():
                effective_compose = cwd_compose

    compose_diag = compose_lifecycle_diagnostics(
        effective_compose,
        compose_required_in_cwd=True,
        instance_overlay_wired_to_init=False,
    )
    for fdict in compose_diag.get("findings") or []:
        findings.append(
            Finding(
                code=fdict["code"],
                severity=fdict["severity"],
                service=fdict.get("service"),
                message=fdict["message"],
                evidence=list(fdict.get("evidence") or []),
                recommendation=fdict.get("recommendation") or "",
            )
        )
    # Drop nested findings from compose dict for report contract
    compose_out = {
        k: v for k, v in compose_diag.items() if k != "findings"
    }

    # --- Docker inspection ---
    actual_services: List[Dict[str, Any]] = []
    if skip_docker:
        docker_result = di.DockerInspectResult(available=False, error="skipped")
        _add(
            findings,
            "DOCKER_UNAVAILABLE",
            "UNKNOWN",
            "Docker inspection skipped",
            evidence=["skip_docker=true"],
        )
        unknowns.append("docker skipped")
    else:
        docker_result = di.inspect_running_containers(runner=docker_runner)
        if not docker_result.available:
            _add(
                findings,
                "DOCKER_UNAVAILABLE",
                "UNKNOWN",
                f"Docker unavailable: {docker_result.error or 'unknown'}",
                evidence=[docker_result.error or ""],
                recommendation="Doctor continues without Docker; start Docker for ownership checks.",
            )
            unknowns.append("docker unavailable")

    for svc in desired:
        ports = list(svc.expected_ports.values())
        endpoint = svc.expected_urls[0] if svc.expected_urls else None
        containers = di.find_containers_for_service(
            docker_result,
            service_name=svc.name,
            expected_ports=ports,
            name_hints=[svc.name, f"mcp-{svc.name}", svc.name.replace("-", "_")],
        )
        label_status = "SKIPPED"
        if not docker_result.available:
            label_status = "SKIPPED"
            if not containers:
                _add(
                    findings,
                    "DOCKER_CONTAINER_NOT_FOUND",
                    "INFO",
                    f"No docker match for `{svc.name}` (docker unavailable or not running)",
                    service=svc.name,
                )
        elif not containers:
            label_status = "UNKNOWN"
            _add(
                findings,
                "DOCKER_CONTAINER_NOT_FOUND",
                "WARN",
                f"No running container matched `{svc.name}` by name/port",
                service=svc.name,
                evidence=[f"ports={ports}"],
            )
        else:
            for c in containers:
                label_status = di.classify_container_ownership(
                    c,
                    project_root=identity.project_root,
                    workspace_id=identity.workspace_id,
                    project_id=identity.project_id,
                    expected_ports=ports,
                    expected_name_substrings=[svc.name],
                )
                if label_status == "MATCH":
                    _add(
                        findings,
                        "DOCKER_CONTAINER_MATCH",
                        "INFO",
                        f"Container {c.name} labels match project for `{svc.name}`",
                        service=svc.name,
                        evidence=[c.name, f"labels={sorted(c.labels.keys())}"],
                    )
                elif label_status == "WRONG_PROJECT":
                    _add(
                        findings,
                        "DOCKER_CONTAINER_WRONG_PROJECT",
                        "FAIL",
                        f"Container {c.name} labels belong to another project for `{svc.name}`",
                        service=svc.name,
                        evidence=[c.name, f"labels={di._redact_labels(c.labels)}"],
                        recommendation="Do not treat this container as this repo's MCP service.",
                    )
                elif label_status == "UNLABELED":
                    _add(
                        findings,
                        "DOCKER_CONTAINER_UNLABELED_UNKNOWN",
                        "UNKNOWN",
                        (
                            f"Container {c.name} matches `{svc.name}` by name/port but has no "
                            "project labels — ownership UNKNOWN"
                        ),
                        service=svc.name,
                        evidence=[c.name, f"ports={c.published_ports}"],
                        recommendation="Packet 002 should attach dopemux project labels.",
                    )
                    unknowns.append(f"docker ownership unlabeled: {c.name}")
                # Port collision: container publishes port assigned to us but wrong name
                if set(c.published_ports) & set(ports) and svc.name.replace("-", "") not in c.name.replace("-", "").lower():
                    # only if name totally unrelated
                    pass

        # Cross-container port collision: another container holds our port
        if docker_result.available and ports:
            for c in docker_result.containers:
                overlap = set(c.published_ports) & set(ports)
                if not overlap:
                    continue
                if c in containers:
                    continue
                _add(
                    findings,
                    "DOCKER_CONTAINER_PORT_COLLISION",
                    "FAIL",
                    (
                        f"Container {c.name} publishes port(s) {sorted(overlap)} "
                        f"expected by `{svc.name}`"
                    ),
                    service=svc.name,
                    evidence=[c.name, f"ports={sorted(overlap)}"],
                    recommendation="Stop the conflicting container or reallocate ports.",
                )

        probe_status = "SKIPPED"
        http_status = None
        if endpoint and not skip_port_probe and ports:
            # Listening alone is not health; leave probe as SKIPPED for ownership safety
            # unless we only check TCP
            try:
                listening = not is_free(ports[0])
                probe_status = "UNKNOWN" if listening else "FAIL"
            except Exception:  # noqa: BLE001
                probe_status = "UNKNOWN"

        actual_services.append(
            {
                "name": svc.name,
                "endpoint": endpoint,
                "probe_status": probe_status,
                "http_status": http_status,
                "docker": {
                    "available": docker_result.available,
                    "containers": [c.to_dict() for c in containers],
                    "label_status": label_status,
                },
            }
        )

    # --- Global / local duplicates ---
    global_servers = global_claude.get("servers") or {}
    local_servers = mcp_servers or {}
    if global_claude.get("parse_status") == "ERROR":
        _add(
            findings,
            "GLOBAL_SERVICE_CONFLICTS_WITH_LOCAL",
            "WARN",
            f"Malformed global config: {global_claude.get('error')}",
            evidence=[str(global_claude.get("path"))],
        )
    for name in sorted(set(global_servers) & set(local_servers)):
        g = global_servers[name] if isinstance(global_servers.get(name), dict) else {}
        loc = local_servers[name] if isinstance(local_servers.get(name), dict) else {}
        g_url = g.get("url") or ""
        l_url = loc.get("url") or ""
        # Always redact URLs in evidence (credentials / non-localhost hostnames).
        safe_g_url = redact_value("URL", str(g_url)) if g_url else None
        safe_l_url = redact_value("URL", str(l_url)) if l_url else None
        _add(
            findings,
            "GLOBAL_LOCAL_DUPLICATE",
            "WARN",
            f"`{name}` exists in both ~/.claude.json and local .mcp.json",
            service=name,
            evidence=[
                f"global_type={g.get('type')}",
                f"local_type={loc.get('type')}",
                f"global_url={safe_g_url}",
                f"local_url={safe_l_url}",
            ],
            recommendation="Prefer local per-worktree entry; remove or rename global duplicate.",
        )
        if g.get("type") != loc.get("type") or (
            g_url and l_url and g_url != l_url and "${" not in g_url and "${" not in l_url
        ):
            # Never dump full mcpServers entry (may contain env secrets).
            g_env_keys = sorted((g.get("env") or {}).keys()) if isinstance(g.get("env"), dict) else []
            _add(
                findings,
                "GLOBAL_SERVICE_CONFLICTS_WITH_LOCAL",
                "FAIL",
                f"`{name}` global and local disagree on type/url",
                service=name,
                evidence=[
                    f"global_type={g.get('type')}",
                    f"local_type={loc.get('type')}",
                    f"global_url={safe_g_url}",
                    f"local_url={safe_l_url}",
                    f"global_env_keys={g_env_keys}",
                ],
            )
        # Dead global probe
        if g_url and "${" not in str(g_url) and not skip_port_probe:
            try:
                parsed = urlparse(str(g_url))
                if parsed.port and ("localhost" in str(g_url) or "127.0.0.1" in str(g_url)):
                    if is_free(parsed.port):
                        _add(
                            findings,
                            "GLOBAL_SERVICE_DEAD",
                            "WARN",
                            f"Global `{name}` points at :{parsed.port} which is not listening",
                            service=name,
                            evidence=[str(g_url)],
                            recommendation="Start the global singleton or remove the dead global entry.",
                        )
                    else:
                        # listening but may still be wrong project
                        pass
            except Exception:  # noqa: BLE001
                pass

    # Global singletons that are only global
    for name, entry in global_servers.items():
        if name in local_servers:
            continue
        spec = (catalog.get("servers") or {}).get(name) or {}
        if isinstance(spec, dict) and spec.get("scope") == "singleton":
            _add(
                findings,
                "GLOBAL_SINGLETON_OK",
                "INFO",
                f"Global singleton `{name}` present in ~/.claude.json",
                service=name,
            )

    for name in local_servers:
        if name not in global_servers:
            _add(
                findings,
                "LOCAL_SERVICE_OK",
                "INFO",
                f"Local service `{name}` not duplicated in global config",
                service=name,
            )

    # --- Stdio doctor_args (non-mutating; same as legacy doctor) ---
    for name in service_names:
        spec = (catalog.get("servers") or {}).get(name) or {}
        if not isinstance(spec, dict):
            continue
        if str(spec.get("transport") or "").lower() != "stdio":
            continue
        doctor_args = list(spec.get("doctor_args") or [])
        if not doctor_args:
            continue
        command = spec.get("command_template") or spec.get("command")
        if not command:
            _add(
                findings,
                "CATALOG_SERVICE_UNKNOWN",
                "WARN",
                f"`{name}`: stdio server missing command for doctor check",
                service=name,
            )
            continue
        try:
            import subprocess as _sp

            result = _sp.run(
                [command, *doctor_args],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
                env=doctor_env,
                cwd=str(repo_path),
            )
        except FileNotFoundError:
            _add(
                findings,
                "PORT_NOT_LISTENING",
                "WARN",
                f"`{name}`: doctor command not found: {command}",
                service=name,
                evidence=[str(command)],
            )
            continue
        except Exception as exc:  # noqa: BLE001
            _add(
                findings,
                "MCP_DOCTOR_UNKNOWN",
                "UNKNOWN",
                f"`{name}`: doctor command failed: {exc}",
                service=name,
            )
            continue
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip()
            _add(
                findings,
                "TASK_ORCHESTRATOR_PROJECT_IDENTITY_UNKNOWN"
                if name == "task-orchestrator"
                else "MCP_DOCTOR_UNKNOWN",
                "WARN",
                f"`{name}`: doctor command failed" + (f" {detail}" if detail else ""),
                service=name,
            )
        elif result.stdout.strip():
            # Surface stdout as INFO evidence (e.g. state_id=...)
            for line in result.stdout.strip().splitlines():
                _add(
                    findings,
                    "LOCAL_SERVICE_OK",
                    "INFO",
                    f"`{name}`: {line}",
                    service=name,
                    evidence=[line],
                )

    # --- Task orchestrator specials (Packet 005 multi-source identity) ---
    to_spec = (catalog.get("servers") or {}).get("task-orchestrator") or {}
    if "task-orchestrator" in service_names or "task-orchestrator" in local_servers:
        if isinstance(to_spec, dict) and to_spec.get("management_model") == "wrapper-singleton":
            _add(
                findings,
                "TASK_ORCHESTRATOR_WRAPPER_SINGLETON_COMPAT",
                "INFO",
                "task-orchestrator is wrapper-singleton (fixed port, per-repo state)",
                service="task-orchestrator",
            )
            base = to_spec.get("default_port_base") or 7890
            _add(
                findings,
                "TASK_ORCHESTRATOR_FIXED_PORT",
                "INFO",
                f"task-orchestrator uses fixed port {base}",
                service="task-orchestrator",
                evidence=[f"port={base}"],
            )
            to_port = configured_ports.get(
                str(to_spec.get("port_var") or "TASK_ORCHESTRATOR_HTTP_PORT")
            )
            if to_port is None:
                to_port = int(base)

            docker_identity = None
            if docker_result.available:
                matches = di.find_containers_for_service(
                    docker_result,
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
                    )
                    if st == "WRONG_PROJECT":
                        from .task_orchestrator_identity import identity_from_docker_labels

                        docker_identity = identity_from_docker_labels(
                            c.labels or {},
                            port=int(to_port),
                            container_name=c.name,
                        )
                    elif st == "MATCH":
                        from .task_orchestrator_identity import identity_from_docker_labels

                        docker_identity = identity_from_docker_labels(
                            c.labels or {},
                            port=int(to_port),
                            container_name=c.name,
                        )
                        break
                    elif st in {"UNLABELED", "UNKNOWN"} and docker_identity is None:
                        from .task_orchestrator_identity import TOIdentity

                        docker_identity = TOIdentity(
                            port=int(to_port),
                            source="docker_labels",
                            confidence="UNKNOWN",
                            evidence=[c.name, f"ownership={st}"],
                        )

            try:
                from .task_orchestrator_identity import evaluate_fixed_port_state

                eval_result = evaluate_fixed_port_state(
                    port=int(to_port),
                    target_project_id=identity.project_id,
                    target_project_root=identity.project_root,
                    target_workspace_id=identity.workspace_id,
                    target_instance_id=identity.instance_id,
                    target_worktree_hash=identity.worktree_hash,
                    is_free_fn=is_free if not skip_port_probe else (lambda _p: True),
                    docker_identity=docker_identity,
                    skip_http=skip_port_probe,
                    for_start=False,
                )
                for fdict in eval_result.findings:
                    sev = fdict.get("severity") or "INFO"
                    # Map UNKNOWN severity string to Finding severity
                    if sev == "UNKNOWN":
                        sev = "UNKNOWN"
                    _add(
                        findings,
                        fdict.get("code") or "TASK_ORCHESTRATOR_STATUS_UNKNOWN",
                        sev,  # type: ignore[arg-type]
                        fdict.get("message") or "",
                        service="task-orchestrator",
                        evidence=list(fdict.get("evidence") or []),
                        recommendation=fdict.get("recommendation") or "",
                    )
                    if fdict.get("code") in {
                        "TASK_ORCHESTRATOR_PROJECT_IDENTITY_UNKNOWN",
                        "TASK_ORCHESTRATOR_FIXED_PORT_OCCUPIED_UNKNOWN",
                    }:
                        unknowns.append("task-orchestrator ownership")
            except Exception as exc:  # noqa: BLE001
                unknowns.append(f"task-orchestrator identity probe failed: {exc}")
                _add(
                    findings,
                    "TASK_ORCHESTRATOR_STATUS_UNKNOWN",
                    "UNKNOWN",
                    f"TO identity evaluation failed: {exc}",
                    service="task-orchestrator",
                )

    # --- Status summary findings ---
    status, exit_code = _summarize_status(findings)
    if status == "PASS":
        _add(findings, "MCP_DOCTOR_PASS", "INFO", "MCP doctor checks passed")
    elif status == "PASS_WITH_WARNINGS":
        _add(findings, "MCP_DOCTOR_PASS_WITH_WARNINGS", "WARN", "MCP doctor passed with warnings")
    elif status == "FAIL":
        _add(findings, "MCP_DOCTOR_FAIL", "FAIL", "MCP doctor found blocking failures")
    else:
        _add(findings, "MCP_DOCTOR_UNKNOWN", "UNKNOWN", "MCP doctor could not fully determine health")

    # Next actions from top FAIL/WARN
    for f in findings:
        if f.severity in {"FAIL", "WARN"} and f.recommendation:
            if f.recommendation not in next_actions:
                next_actions.append(f.recommendation)
    if not next_actions:
        next_actions.append("No blocking actions. Proceed to Packet 002 only if lifecycle start is required.")

    config_sources = {
        "mcp_json": {
            "path": mcp_json.get("path"),
            "present": mcp_json.get("present"),
            "parse_status": mcp_json.get("parse_status"),
            "services": mcp_json.get("services") or [],
        },
        "envrc": envrc.to_report_dict(),
        "catalog": {
            "paths_checked": list(catalog_paths_checked or []),
            "services": catalog_service_summary(catalog),
        },
        "global_claude": {
            "path": global_claude.get("path"),
            "present": global_claude.get("present"),
            "parse_status": global_claude.get("parse_status"),
            "services": global_claude.get("services") or [],
        },
    }

    return DoctorReport(
        schema_version=SCHEMA_VERSION,
        status=status,
        repo_arg=repo_arg,
        project_identity=identity.to_dict(),
        config_sources=config_sources,
        desired_services=[s.to_dict() for s in desired],
        actual_services=actual_services,
        port_diagnostics=port_report.to_dict(),
        compose_lifecycle_diagnostics=compose_out,
        findings=[f.to_dict() for f in findings],
        unknowns=unknowns,
        recommended_next_actions=next_actions[:12],
        exit_code=exit_code,
    )


def format_human_summary(report: DoctorReport, *, verbose: bool = False, max_findings: int = 5) -> str:
    """Compact human-readable doctor summary."""
    repo_name = Path(report.repo_arg).name or report.repo_arg
    lines = [f"MCP Doctor for {repo_name}: {report.status}"]
    # Prioritize FAIL then WARN then UNKNOWN
    priority = {"FAIL": 0, "WARN": 1, "UNKNOWN": 2, "INFO": 3}
    sorted_findings = sorted(
        report.findings,
        key=lambda f: (priority.get(f.get("severity", "INFO"), 9), f.get("code", "")),
    )
    # Skip pure INFO noise for top findings
    top = [
        f
        for f in sorted_findings
        if f.get("severity") in {"FAIL", "WARN", "UNKNOWN"}
        and f.get("code")
        not in {
            "MCP_DOCTOR_PASS",
            "MCP_DOCTOR_PASS_WITH_WARNINGS",
            "MCP_DOCTOR_FAIL",
            "MCP_DOCTOR_UNKNOWN",
            "PORT_EXPECTED",
            "ENVRC_FOUND",
            "MCP_JSON_FOUND",
            "TRANSPORT_MATCH",
            "LOCAL_SERVICE_OK",
            "GLOBAL_SINGLETON_OK",
            "PROJECT_IDENTITY_RESOLVED",
            "TASK_ORCHESTRATOR_FIXED_PORT",
            "TASK_ORCHESTRATOR_WRAPPER_SINGLETON_COMPAT",
        }
    ]
    if not verbose:
        top = top[:max_findings]
    if top:
        lines.append("Top findings:")
        for i, f in enumerate(top, 1):
            svc = f" {f['service']}" if f.get("service") else ""
            lines.append(f"{i}. {f['severity']} {f['code']}{svc} {f['message']}")
    else:
        lines.append("Top findings: (none)")
    if report.recommended_next_actions:
        lines.append("Next action:")
        lines.append(report.recommended_next_actions[0])
    return "\n".join(lines) + "\n"
