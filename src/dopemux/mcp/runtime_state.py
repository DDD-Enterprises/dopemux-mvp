"""Desired MCP runtime state models for doctor (read-only).

Assembles catalog + .mcp.json + envrc + project identity into a desired-state
view without claiming that running processes belong to the project.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence
from urllib.parse import urlparse

from .envrc import EnvrcParseResult, load_envrc, safe_port_int
from .project_identity import ProjectIdentity, ProjectIdentityError, resolve_project_identity


ENVRC_FILENAME = ".envrc.dopemux-mcp"
PROJECT_MCP_FILENAME = ".mcp.json"


@dataclass
class ProjectIdentityView:
    project_id: Optional[str]
    workspace_id: Optional[str]
    project_root: Optional[str]
    worktree_root: Optional[str]
    project_hash: Optional[str]
    worktree_hash: Optional[str]
    instance_id: Optional[str]
    identity_confidence: str
    evidence: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "workspace_id": self.workspace_id,
            "project_root": self.project_root,
            "worktree_root": self.worktree_root,
            "project_hash": self.project_hash,
            "worktree_hash": self.worktree_hash,
            "instance_id": self.instance_id,
            "identity_confidence": self.identity_confidence,
            "evidence": list(self.evidence),
        }


@dataclass
class DesiredService:
    name: str
    scope: str
    catalog_transport: str
    mcp_json_transport: Optional[str]
    expected_urls: List[str]
    expected_ports: Dict[str, int]
    env_keys: List[str]
    identity_requirements: List[str]
    management_model: Optional[str] = None
    state_scope: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "scope": self.scope,
            "catalog_transport": self.catalog_transport,
            "mcp_json_transport": self.mcp_json_transport,
            "expected_urls": list(self.expected_urls),
            "expected_ports": dict(self.expected_ports),
            "env_keys": list(self.env_keys),
            "identity_requirements": list(self.identity_requirements),
            "management_model": self.management_model,
            "state_scope": self.state_scope,
        }


def resolve_identity_view(
    repo_path: Path,
    *,
    envrc_values: Optional[Mapping[str, str]] = None,
) -> ProjectIdentityView:
    """Resolve project identity for doctor; never raises — degrades to UNKNOWN."""
    evidence: List[str] = []
    env_map = dict(envrc_values or {})
    env_map.setdefault("DOPEMUX_WORKSPACE_ROOT", str(repo_path))

    try:
        identity: ProjectIdentity = resolve_project_identity(cwd=repo_path, env=env_map)
    except ProjectIdentityError as exc:
        return ProjectIdentityView(
            project_id=None,
            workspace_id=env_map.get("DOPEMUX_WORKSPACE_ID") or str(repo_path),
            project_root=env_map.get("DOPEMUX_PROJECT_ROOT"),
            worktree_root=str(repo_path),
            project_hash=None,
            worktree_hash=None,
            instance_id=env_map.get("DOPEMUX_INSTANCE_ID"),
            identity_confidence="UNKNOWN",
            evidence=[f"resolve_project_identity failed: {exc}"],
        )

    from .port_diagnostics import instance_id_for_path

    worktree = str(identity.worktree_root)
    project_root = str(identity.project_root)
    instance_id = env_map.get("DOPEMUX_INSTANCE_ID") or instance_id_for_path(worktree)
    confidence = "HIGH"
    evidence.append(f"worktree_root={worktree}")
    evidence.append(f"project_root={project_root}")
    if worktree != project_root:
        evidence.append("worktree_differs_from_project_root")
        confidence = "MEDIUM"
    if identity.git_common_dir is None and (
        env_map.get("DOPEMUX_PROJECT_ROOT") or env_map.get("TASK_ORCHESTRATOR_PROJECT_ROOT")
    ):
        evidence.append("project_root_from_env_override")
        confidence = "MEDIUM"

    return ProjectIdentityView(
        project_id=identity.project_id,
        workspace_id=env_map.get("DOPEMUX_WORKSPACE_ID") or worktree,
        project_root=project_root,
        worktree_root=worktree,
        project_hash=identity.project_hash,
        worktree_hash=instance_id_for_path(worktree),
        instance_id=instance_id,
        identity_confidence=confidence,
        evidence=evidence,
    )


def load_mcp_json(path: Path) -> Dict[str, Any]:
    """Load .mcp.json; return {present, parse_status, services, error, raw_servers}."""
    if not path.exists():
        return {
            "path": str(path),
            "present": False,
            "parse_status": "MISSING",
            "services": [],
            "servers": {},
            "error": None,
        }
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "path": str(path),
            "present": True,
            "parse_status": "ERROR",
            "services": [],
            "servers": {},
            "error": str(exc),
        }
    servers = data.get("mcpServers") or {}
    if not isinstance(servers, dict):
        return {
            "path": str(path),
            "present": True,
            "parse_status": "ERROR",
            "services": [],
            "servers": {},
            "error": "mcpServers is not a mapping",
        }
    service_summaries = []
    for name, entry in servers.items():
        if not isinstance(entry, dict):
            service_summaries.append({"name": name, "type": "unknown", "url": None})
            continue
        service_summaries.append(
            {
                "name": name,
                "type": entry.get("type"),
                "url": entry.get("url"),
                "command": entry.get("command"),
            }
        )
    return {
        "path": str(path),
        "present": True,
        "parse_status": "OK",
        "services": service_summaries,
        "servers": servers,
        "error": None,
    }


def load_global_claude(path: Optional[Path] = None) -> Dict[str, Any]:
    """Load ~/.claude.json mcpServers (read-only)."""
    global_path = path or (Path.home() / ".claude.json")
    if not global_path.exists():
        return {
            "path": str(global_path),
            "present": False,
            "parse_status": "MISSING",
            "services": [],
            "servers": {},
            "error": None,
        }
    try:
        data = json.loads(global_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "path": str(global_path),
            "present": True,
            "parse_status": "ERROR",
            "services": [],
            "servers": {},
            "error": str(exc),
        }
    servers = data.get("mcpServers") or {}
    if not isinstance(servers, dict):
        servers = {}
    services = []
    for name, entry in servers.items():
        if not isinstance(entry, dict):
            services.append({"name": name, "type": "unknown", "url": None})
            continue
        services.append(
            {
                "name": name,
                "type": entry.get("type"),
                "url": entry.get("url"),
                "command": entry.get("command"),
            }
        )
    return {
        "path": str(global_path),
        "present": True,
        "parse_status": "OK",
        "services": services,
        "servers": servers,
        "error": None,
    }


_ENV_PLACEHOLDER = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}")


def expand_url_template(template: str, env: Mapping[str, str]) -> str:
    """Expand ${VAR:-default} placeholders using env mapping (for doctor expected URLs)."""

    def repl(match: re.Match[str]) -> str:
        key = match.group(1)
        default = match.group(2) if match.group(2) is not None else ""
        return env.get(key, default)

    return _ENV_PLACEHOLDER.sub(repl, template)


def extract_ports_from_url(url: str) -> List[int]:
    try:
        parsed = urlparse(url)
        if parsed.port:
            return [parsed.port]
    except Exception:  # noqa: BLE001
        pass
    return []


def build_desired_services(
    catalog: Mapping[str, Any],
    mcp_servers: Mapping[str, Any],
    env_values: Mapping[str, str],
    *,
    configured_ports: Optional[Mapping[str, int]] = None,
) -> List[DesiredService]:
    """Build desired service list from catalog + local mcp.json + env."""
    desired: List[DesiredService] = []
    names = list(mcp_servers.keys()) if mcp_servers else list(
        (catalog.get("defaults") or {}).get("per_worktree") or []
    )
    # Also include any catalog per-worktree defaults not in mcp.json for diagnosis
    for name in names:
        catalog_spec = (catalog.get("servers") or {}).get(name) or {}
        local_entry = mcp_servers.get(name) if isinstance(mcp_servers.get(name), dict) else {}
        if not catalog_spec and not local_entry:
            continue

        catalog_transport = str(catalog_spec.get("transport") or "unknown")
        mcp_transport = local_entry.get("type") if local_entry else None
        if mcp_transport is not None:
            mcp_transport = str(mcp_transport)

        scope = str(catalog_spec.get("scope") or "unknown")
        expected_ports: Dict[str, int] = {}
        port_var = catalog_spec.get("port_var")
        if port_var:
            if configured_ports and port_var in configured_ports:
                expected_ports[port_var] = int(configured_ports[port_var])
            else:
                port = safe_port_int(env_values, str(port_var))
                if port is not None:
                    expected_ports[str(port_var)] = port
        for extra in catalog_spec.get("extra_port_vars") or []:
            if not isinstance(extra, dict):
                continue
            var = extra.get("var")
            if not var:
                continue
            if configured_ports and var in configured_ports:
                expected_ports[str(var)] = int(configured_ports[str(var)])
            else:
                port = safe_port_int(env_values, str(var))
                if port is not None:
                    expected_ports[str(var)] = port

        urls: List[str] = []
        template = catalog_spec.get("url_template") or catalog_spec.get("url") or local_entry.get("url")
        if template:
            expanded = expand_url_template(str(template), env_values)
            # Only keep localhost-ish URLs in report
            if "localhost" in expanded or "127.0.0.1" in expanded:
                urls.append(expanded)

        env_keys = list(catalog_spec.get("requires_env") or []) + list(
            catalog_spec.get("optional_env") or []
        )
        identity_reqs = [
            k
            for k in (
                "DOPEMUX_WORKSPACE_ID",
                "DOPEMUX_PROJECT_ROOT",
                "TASK_ORCHESTRATOR_PROJECT_ROOT",
                "DOPE_MEMORY_WORKSPACE_ID",
                "DOPE_MEMORY_INSTANCE_ID",
            )
            if k in env_keys or k in (catalog_spec.get("requires_env") or [])
        ]

        desired.append(
            DesiredService(
                name=name,
                scope=scope,
                catalog_transport=catalog_transport if catalog_spec else "unknown",
                mcp_json_transport=mcp_transport,
                expected_urls=urls,
                expected_ports=expected_ports,
                env_keys=env_keys,
                identity_requirements=identity_reqs,
                management_model=catalog_spec.get("management_model"),
                state_scope=catalog_spec.get("state_scope"),
            )
        )
    return desired


def catalog_service_summary(catalog: Mapping[str, Any]) -> List[Dict[str, Any]]:
    out = []
    for name, spec in (catalog.get("servers") or {}).items():
        if not isinstance(spec, dict):
            continue
        out.append(
            {
                "name": name,
                "scope": spec.get("scope"),
                "transport": spec.get("transport"),
                "management_model": spec.get("management_model"),
                "port_var": spec.get("port_var"),
                "default_port_base": spec.get("default_port_base"),
            }
        )
    return out


def compose_lifecycle_diagnostics(
    compose_path: Optional[Path],
    *,
    compose_required_in_cwd: bool = True,
    instance_overlay_wired_to_init: bool = False,
) -> Dict[str, Any]:
    """
    Read-only compose hazard scan.

    If compose_path is None or missing, still report architectural risks that
    are known from dopemux-mvp compose conventions (from code paths), but
    mark file-specific evidence as unavailable.
    """
    fixed_name_risks: List[str] = []
    relative_volume_risks: List[str] = []
    identity_env_risks: List[str] = []
    dual_allocator_risks: List[str] = []
    findings_seed: List[Dict[str, Any]] = []

    text = ""
    if compose_path and compose_path.is_file():
        try:
            text = compose_path.read_text(encoding="utf-8")
        except OSError as exc:
            findings_seed.append(
                {
                    "code": "COMPOSE_REQUIRED_IN_CWD",
                    "severity": "WARN",
                    "service": None,
                    "message": f"Could not read compose file {compose_path}: {exc}",
                    "evidence": [str(compose_path)],
                    "recommendation": "Doctor does not require compose for config checks; compose is only for lifecycle hazard detection.",
                }
            )

    # Fixed container name default for conport
    if text:
        if "CONPORT_CONTAINER_NAME:-mcp-conport" in text or re.search(
            r"container_name:\s*\$\{CONPORT_CONTAINER_NAME:-\s*mcp-conport\s*\}", text
        ):
            fixed_name_risks.append(
                "conport defaults to container_name mcp-conport; foreign-repo up can replace primary"
            )
        if re.search(r"\./\.dopemux\s*:\s*/data", text) or "./.dopemux:/data" in text:
            relative_volume_risks.append(
                "dope-memory volume ./.dopemux:/data is relative to compose cwd"
            )
        # Identity env on conport
        if "DOPEMUX_INSTANCE_ID" in text and "DOPEMUX_WORKSPACE_ID" not in text.split("conport:")[1].split("\n  ")[0] if "conport:" in text else True:
            # Broader check: conport service block lacks WORKSPACE_ID
            conport_block = _extract_service_block(text, "conport")
            if conport_block:
                if "DOPEMUX_INSTANCE_ID" in conport_block and "DOPEMUX_WORKSPACE_ID" not in conport_block:
                    identity_env_risks.append(
                        "conport receives DOPEMUX_INSTANCE_ID but not DOPEMUX_WORKSPACE_ID"
                    )
        memory_block = _extract_service_block(text, "dope-memory")
        if memory_block and "DOPE_MEMORY_WORKSPACE_ID" in memory_block:
            # workspace id is present for memory — still relative volume is the main risk
            pass
    else:
        # Without compose file still emit known architectural risks as WARN
        # so doctor works without target-repo compose.yml
        fixed_name_risks.append(
            "compose convention (dopemux-mvp): conport container_name defaults to mcp-conport"
        )
        relative_volume_risks.append(
            "compose convention (dopemux-mvp): dope-memory binds ./.dopemux:/data relative to compose cwd"
        )
        identity_env_risks.append(
            "compose convention: project-scoped services may receive instance id without full workspace identity"
        )

    if compose_required_in_cwd:
        findings_seed.append(
            {
                "code": "COMPOSE_REQUIRED_IN_CWD",
                "severity": "WARN",
                "service": None,
                "message": (
                    "mcp up/status/ensure --full paths require compose.yml in cwd "
                    "(or current repo), so init-for-target + up-from-dopemux-mvp is split and unsafe."
                ),
                "evidence": ["mcp_commands._compose_path uses Path.cwd()/compose.yml"],
                "recommendation": (
                    "Packet 002 must implement repo-aware start/up/down that does not "
                    "depend on operator cwd for identity."
                ),
            }
        )

    if fixed_name_risks:
        findings_seed.append(
            {
                "code": "COMPOSE_CONTAINER_NAME_DEFAULT_COLLISION_RISK",
                "severity": "FAIL",
                "service": "conport",
                "message": (
                    "Fixed/default mcp-conport container name risks replacing the primary "
                    "ConPort container when starting another project's stack."
                ),
                "evidence": fixed_name_risks,
                "recommendation": (
                    "Always set unique CONPORT_CONTAINER_NAME per project/worktree; "
                    "Packet 002 should enforce labels + unique names."
                ),
            }
        )

    if relative_volume_risks:
        findings_seed.append(
            {
                "code": "COMPOSE_MEMORY_VOLUME_RELATIVE_CWD_RISK",
                "severity": "FAIL",
                "service": "dope-memory",
                "message": (
                    "Starting dope-memory for another repo from dopemux-mvp compose can bind "
                    "dopemux-mvp/.dopemux instead of the target repo .dopemux, causing memory-state bleed."
                ),
                "evidence": relative_volume_risks,
                "recommendation": (
                    "Do not start foreign-repo dope-memory via dopemux-mvp cwd compose until "
                    "Packet 002 binds absolute target-repo data paths."
                ),
            }
        )

    if identity_env_risks:
        findings_seed.append(
            {
                "code": "COMPOSE_WORKSPACE_ID_MISSING_RISK",
                "severity": "WARN",
                "service": "conport",
                "message": "; ".join(identity_env_risks),
                "evidence": identity_env_risks,
                "recommendation": "Pass DOPEMUX_WORKSPACE_ID / project identity into project-scoped containers.",
            }
        )
        findings_seed.append(
            {
                "code": "COMPOSE_INSTANCE_ID_ONLY_INSUFFICIENT",
                "severity": "WARN",
                "service": "conport",
                "message": (
                    "DOPEMUX_INSTANCE_ID alone is insufficient to prove workspace/project ownership."
                ),
                "evidence": identity_env_risks,
                "recommendation": "Require workspace/project labels and env before treating a container as owned.",
            }
        )

    if not instance_overlay_wired_to_init:
        dual_allocator_risks.append(
            "InstanceOverlayManager uses a separate port map (letter/md5 base) not wired into mcp init"
        )
        dual_allocator_risks.append(
            "mcp init uses _allocate_ports (sha1_abs_path_mod_100) independently"
        )
        findings_seed.append(
            {
                "code": "DUAL_ALLOCATION_BRAINS",
                "severity": "WARN",
                "service": None,
                "message": (
                    "Two allocation brains exist: mcp init `_allocate_ports` and "
                    "`InstanceOverlayManager`; they are not unified."
                ),
                "evidence": dual_allocator_risks,
                "recommendation": (
                    "Unify allocation in a later packet; doctor only reports the drift."
                ),
            }
        )
        findings_seed.append(
            {
                "code": "INSTANCE_OVERLAY_NOT_WIRED_TO_INIT",
                "severity": "WARN",
                "service": None,
                "message": "InstanceOverlayManager is not wired into `dopemux mcp init`.",
                "evidence": [
                    "instance_overlay.InstanceOverlayManager",
                    "mcp_commands._allocate_ports",
                ],
                "recommendation": "Wire a single allocator before multi-repo start automation.",
            }
        )

    return {
        "compose_required_in_cwd": compose_required_in_cwd,
        "compose_path": str(compose_path) if compose_path else None,
        "compose_present": bool(compose_path and compose_path.is_file()),
        "fixed_container_name_risks": fixed_name_risks,
        "relative_volume_risks": relative_volume_risks,
        "identity_env_risks": identity_env_risks,
        "dual_allocator_risks": dual_allocator_risks,
        "findings": findings_seed,
    }


def _extract_service_block(compose_text: str, service: str) -> str:
    """Best-effort extract of a top-level compose service block by name."""
    pattern = re.compile(
        rf"^  {re.escape(service)}:\n(.*?)(?=^  [A-Za-z0-9_.-]+:|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(compose_text)
    return match.group(0) if match else ""
