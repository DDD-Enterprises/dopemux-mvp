"""Static MCP fleet catalog contract helpers.

This module intentionally performs no Docker, provider, or MCP network work.
It validates catalog shape and static drift between committed config surfaces.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml

from dopemux.commands import mcp_commands


class MCPFleetCatalogError(ValueError):
    """Base error for static MCP fleet catalog validation."""


class DuplicateKeyError(MCPFleetCatalogError):
    """Raised when a YAML mapping repeats a key."""


_ENV_DEFAULT_RE = re.compile(r"\$\{[^:}]+:-([0-9]+)\}")
_ENV_RE = re.compile(r"\$\{[^}]+\}")
_MCP_TOOL_SURFACE_RE = re.compile(r"\bmcp__([A-Za-z0-9_-]+)__(?:[A-Za-z0-9_-]+|\*)")
_CODEX_SERVER_HEADING_RE = re.compile(r'^\[mcp_servers\."([^"]+)"\]$', re.MULTILINE)


REQUIRED_SERVER_PERSONALITIES: dict[str, dict[str, str]] = {
    "conport": {
        "plane": "memory",
        "authority_role": "structured-context-authority",
        "lifecycle": "active",
        "management_model": "compose-service",
        "identity_scope": "per-worktree",
        "follow_on_decision": "none",
    },
    "dope-memory": {
        "plane": "memory",
        "authority_role": "chronicle-authority",
        "lifecycle": "active",
        "management_model": "compose-service",
        "identity_scope": "per-worktree",
        "follow_on_decision": "none",
    },
    "dope-context": {
        "plane": "retrieval",
        "authority_role": "retrieval-projection",
        "lifecycle": "active",
        "management_model": "compose-service",
        "identity_scope": "per-call-workspace",
        "follow_on_decision": "none",
    },
    "task-orchestrator": {
        "plane": "workflow",
        "authority_role": "workflow-authority",
        "lifecycle": "active",
        "management_model": "wrapper-singleton",
        "identity_scope": "per-repo",
        "follow_on_decision": "none",
    },
    "pal": {
        "plane": "reasoning",
        "authority_role": "reasoning-infrastructure",
        "lifecycle": "active",
        "management_model": "compose-service",
        "identity_scope": "singleton",
        "follow_on_decision": "none",
    },
    "pal-stdio": {
        "plane": "reasoning",
        "authority_role": "reasoning-infrastructure",
        "lifecycle": "operator-managed",
        "management_model": "docker-exec",
        "identity_scope": "singleton",
        "follow_on_decision": "none",
    },
    # exa retired 2026-07-04 (wire-or-retire → retire).
    "desktop-commander": {
        "plane": "automation",
        "authority_role": "desktop-automation",
        "lifecycle": "decision-required",
        "management_model": "compose-service",
        "identity_scope": "host-session",
        "follow_on_decision": "delete-or-host-run",
    },
}


def load_yaml_no_duplicate_keys(path: Path) -> Any:
    """Load YAML while rejecting duplicate mapping keys at any depth."""

    class Loader(yaml.SafeLoader):
        source_name = str(path)

    def construct_mapping(loader: yaml.SafeLoader, node: yaml.MappingNode, deep: bool = False):
        mapping: dict[Any, Any] = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node, deep=deep)
            if key in mapping:
                line = key_node.start_mark.line + 1
                raise DuplicateKeyError(
                    f"{Loader.source_name}: duplicate YAML key {key!r} at line {line}"
                )
            mapping[key] = loader.construct_object(value_node, deep=deep)
        return mapping

    Loader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping,
    )

    with path.open("r", encoding="utf-8") as fh:
        return yaml.load(fh, Loader=Loader)


def load_json_schema(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def load_root_catalog(repo_root: Path) -> dict[str, Any]:
    data = load_yaml_no_duplicate_keys(repo_root / "mcp_catalog.yaml") or {}
    if data.get("version") != 1:
        raise MCPFleetCatalogError(f"Unsupported MCP catalog version: {data.get('version')!r}")
    if not isinstance(data.get("servers"), dict):
        raise MCPFleetCatalogError("MCP catalog missing required `servers` mapping.")
    return data


def render_per_worktree_mcp_json(
    server_names: list[str],
    catalog: dict[str, Any],
) -> dict[str, Any]:
    return mcp_commands._build_local_mcp_json(server_names, catalog)


def _is_decision_required(spec: dict[str, Any]) -> bool:
    return spec.get("lifecycle") == "decision-required"


def render_singleton_mcp_servers(catalog: dict[str, Any]) -> dict[str, Any]:
    return mcp_commands._build_global_mcp_servers(catalog)


def _json_dumps(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def _toml_string(value: Any) -> str:
    return json.dumps(str(value))


def _toml_string_array(values: list[Any]) -> str:
    return "[" + ", ".join(_toml_string(value) for value in values) + "]"


def _codex_env_vars(spec: dict[str, Any]) -> list[str]:
    env_keys = list(spec.get("requires_env", []) or []) + list(spec.get("optional_env", []) or [])
    return sorted(set(env_keys))


def render_codex_config_fragment(catalog: dict[str, Any]) -> str:
    """Render singleton MCP servers in Codex `config.toml` syntax.

    Codex currently supports stdio and streamable HTTP MCP servers. SSE-only
    singleton entries stay represented in Claude/global and health outputs.
    """

    lines = [
        "# Generated from mcp_catalog.yaml by `dopemux mcp generate`.",
        "# Dry-run is the default; review before copying into .codex/config.toml.",
    ]
    for name, spec in sorted(catalog.get("servers", {}).items()):
        if spec.get("scope") != "singleton":
            continue
        if _is_decision_required(spec):
            continue
        transport = spec.get("transport", "http")
        if transport not in {"stdio", "http"}:
            continue

        lines.extend(["", f"[mcp_servers.{_toml_string(name)}]"])
        if transport == "stdio":
            command = spec.get("command")
            if not command:
                raise MCPFleetCatalogError(f"Singleton `{name}` requires `command` for Codex stdio.")
            lines.append(f"command = {_toml_string(command)}")
            if spec.get("args"):
                lines.append(f"args = {_toml_string_array(list(spec['args']))}")
            env_vars = _codex_env_vars(spec)
            if env_vars:
                lines.append(f"env_vars = {_toml_string_array(env_vars)}")
        else:
            url = spec.get("url")
            if not url:
                raise MCPFleetCatalogError(f"Singleton `{name}` requires `url` for Codex HTTP.")
            lines.append(f"url = {_toml_string(url)}")

    return "\n".join(lines) + "\n"


def render_health_probe_list(catalog: dict[str, Any]) -> list[dict[str, Any]]:
    probes: list[dict[str, Any]] = []
    for name, spec in sorted(catalog.get("servers", {}).items()):
        url = spec.get("url") or spec.get("url_template")
        if not url:
            continue
        probes.append(
            {
                "authority_role": spec.get("authority_role"),
                "docker_compose_service": spec.get("docker_compose_service"),
                "follow_on_decision": spec.get("follow_on_decision"),
                "identity_scope": spec.get("identity_scope"),
                "lifecycle": spec.get("lifecycle"),
                "management_model": spec.get("management_model"),
                "name": name,
                "plane": spec.get("plane"),
                "scope": spec.get("scope"),
                "transport": spec.get("transport", "http"),
                "url": url,
            }
        )
    return probes


def render_mcp_doctrine_doc(catalog: dict[str, Any]) -> str:
    lines = [
        "# MCP Fleet Catalog Outputs",
        "",
        "<!-- Generated from mcp_catalog.yaml by `dopemux mcp generate`. -->",
        "",
        "## Contract",
        "",
        "- `mcp_catalog.yaml` is the source for generated MCP config fragments.",
        "- Dry-run is the default; writes require `dopemux mcp generate --apply --output-dir <dir>`.",
        "- Generated outputs are projections, not user-global authority.",
        "- Unknown external config entries are preserved by sync flows unless pruning is explicit.",
        "- `decision-required` servers stay visible in audit outputs but are excluded from startable generated configs.",
        "",
        "## Default Per-Worktree Servers",
        "",
    ]
    defaults = catalog.get("defaults", {}).get("per_worktree") or []
    if defaults:
        for name in defaults:
            lines.append(f"- `{name}`")
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Servers",
            "",
            "| Server | Plane | Authority Role | Lifecycle | Identity | Follow-on | Scope | Transport | Health URL | Compose Service |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for name, spec in sorted(catalog.get("servers", {}).items()):
        health_url = spec.get("url") or spec.get("url_template") or ""
        compose_service = spec.get("docker_compose_service") or ""
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{name}`",
                    str(spec.get("plane", "")),
                    str(spec.get("authority_role", "")),
                    str(spec.get("lifecycle", "")),
                    str(spec.get("identity_scope", "")),
                    str(spec.get("follow_on_decision", "")),
                    str(spec.get("scope", "")),
                    str(spec.get("transport", "")),
                    f"`{health_url}`" if health_url else "",
                    f"`{compose_service}`" if compose_service else "",
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def generate_fleet_output_files(catalog: dict[str, Any]) -> dict[str, str]:
    defaults = catalog.get("defaults", {}).get("per_worktree") or []
    return {
        "local/.mcp.json": _json_dumps(render_per_worktree_mcp_json(defaults, catalog)),
        "claude/mcpServers.json": _json_dumps(
            {"mcpServers": render_singleton_mcp_servers(catalog)}
        ),
        "codex/config.toml": render_codex_config_fragment(catalog),
        "health/mcp-health-probes.json": _json_dumps(render_health_probe_list(catalog)),
        "docs/mcp-fleet.md": render_mcp_doctrine_doc(catalog),
    }


def _json_mcp_server_names(payload: str) -> set[str]:
    data = json.loads(payload)
    servers = data.get("mcpServers") or {}
    if isinstance(servers, dict):
        return set(servers)
    if isinstance(servers, list):
        names: set[str] = set()
        for server in servers:
            if isinstance(server, str):
                names.add(server)
            elif isinstance(server, dict) and isinstance(server.get("name"), str):
                names.add(server["name"])
        return names
    return set()


def validate_decision_required_generated_config_quarantine(
    catalog: dict[str, Any],
    outputs: dict[str, str] | None = None,
) -> list[str]:
    """Ensure unresolved MCP surfaces cannot be started from generated configs."""

    errors: list[str] = []
    servers = catalog.get("servers") or {}
    decision_required = {
        name
        for name, spec in servers.items()
        if isinstance(spec, dict) and _is_decision_required(spec)
    }

    for name in catalog.get("defaults", {}).get("per_worktree") or []:
        if name in decision_required:
            errors.append(f"defaults.per_worktree includes decision-required server `{name}`")

    rendered = outputs if outputs is not None else generate_fleet_output_files(catalog)
    startable_outputs = {
        "local/.mcp.json": _json_mcp_server_names(rendered.get("local/.mcp.json", "{}")),
        "claude/mcpServers.json": _json_mcp_server_names(
            rendered.get("claude/mcpServers.json", "{}")
        ),
        "codex/config.toml": set(
            _CODEX_SERVER_HEADING_RE.findall(rendered.get("codex/config.toml", ""))
        ),
    }
    for output_path, names in startable_outputs.items():
        for name in sorted(names & decision_required):
            errors.append(f"{output_path} includes decision-required server `{name}`")

    return errors


def known_tool_surfaces(catalog: dict[str, Any]) -> set[str]:
    surfaces: set[str] = set(catalog.get("servers", {}))
    for spec in catalog.get("servers", {}).values():
        surfaces.update(spec.get("tool_aliases") or [])
    return surfaces


def extract_mcp_tool_surfaces(text: str) -> list[str]:
    return [match.group(1) for match in _MCP_TOOL_SURFACE_RE.finditer(text)]


def find_unknown_command_tool_surfaces(
    command_dir: Path,
    catalog: dict[str, Any],
) -> list[str]:
    known = known_tool_surfaces(catalog)
    unknown: list[str] = []
    for path in sorted(command_dir.rglob("*.md")):
        for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            for surface in extract_mcp_tool_surfaces(line):
                if surface not in known:
                    unknown.append(f"{path}:{index}:{surface}")
    return unknown


def validate_catalog_personality_contract(catalog: dict[str, Any]) -> list[str]:
    """Validate high-risk MCP server role and lifecycle metadata.

    This is a static gate. It does not prove the runtime is healthy; it prevents
    authority and lifecycle semantics from drifting out of the catalog.
    """

    errors: list[str] = []
    servers = catalog.get("servers") or {}
    for name, expected in REQUIRED_SERVER_PERSONALITIES.items():
        spec = servers.get(name)
        if not spec:
            errors.append(f"{name}: required server missing from catalog")
            continue
        for field, expected_value in expected.items():
            actual = spec.get(field)
            if actual != expected_value:
                errors.append(
                    f"{name}: {field} must be `{expected_value}` for MCP personality contract "
                    f"(found `{actual}`)"
                )

    for name, spec in sorted(servers.items()):
        follow_on_decision = spec.get("follow_on_decision")
        if spec.get("lifecycle") == "decision-required" and follow_on_decision in {None, "none"}:
            errors.append(f"{name}: decision-required lifecycle must name a follow_on_decision")
        if follow_on_decision not in {None, "none"} and spec.get("lifecycle") != "decision-required":
            errors.append(f"{name}: follow_on_decision requires lifecycle `decision-required`")

    return errors


def load_compose(repo_root: Path) -> dict[str, Any]:
    return load_yaml_no_duplicate_keys(repo_root / "compose.yml") or {}


def _defaulted(value: str) -> str:
    value = _ENV_DEFAULT_RE.sub(r"\1", value)
    return _ENV_RE.sub("", value)


def _parse_port_mapping(value: Any) -> tuple[int, int] | None:
    if not isinstance(value, str):
        return None
    cleaned = _defaulted(value)
    parts = cleaned.split(":")
    if len(parts) == 3:
        host, container = parts[1], parts[2]
    elif len(parts) == 2:
        host, container = parts[0], parts[1]
    else:
        return None
    try:
        return int(host), int(container)
    except ValueError:
        return None


def _compose_host_ports(service: dict[str, Any]) -> set[int]:
    ports: set[int] = set()
    for value in service.get("ports") or []:
        parsed = _parse_port_mapping(value)
        if parsed:
            ports.add(parsed[0])
    return ports


def _container_name(service_name: str, service: dict[str, Any]) -> str:
    value = str(service.get("container_name") or service_name)
    return _defaulted(value)


def _url_port(value: str | None) -> int | None:
    if not value:
        return None
    parsed = urlparse(_defaulted(value))
    return parsed.port


_DOCKER_EXEC_VALUE_FLAGS = {
    "--detach-keys",
    "--env",
    "--env-file",
    "--user",
    "--workdir",
    "-e",
    "-u",
    "-w",
}


def _docker_exec_target(args: list[str]) -> str | None:
    if not args or args[0] != "exec":
        return None
    skip_next = False
    for token in args[1:]:
        if skip_next:
            skip_next = False
            continue
        if token in _DOCKER_EXEC_VALUE_FLAGS:
            skip_next = True
            continue
        if token.startswith("--"):
            if "=" in token:
                continue
            continue
        if token.startswith("-"):
            # Short Docker exec flags that take attached values, e.g. -u1000 or -eKEY=VAL.
            if len(token) > 2 and token[1] in {"e", "u", "w"}:
                continue
            continue
        return token
    return None


def validate_catalog_compose_alignment(repo_root: Path) -> list[str]:
    return validate_catalog_compose_alignment_data(
        load_root_catalog(repo_root),
        load_compose(repo_root),
    )


def validate_catalog_compose_alignment_data(
    catalog: dict[str, Any],
    compose: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    compose_services = compose.get("services") or {}

    for name, spec in sorted((catalog.get("servers") or {}).items()):
        service_name = spec.get("docker_compose_service")
        if not service_name:
            continue
        service = compose_services.get(service_name)
        if not service:
            errors.append(f"{name}: docker_compose_service `{service_name}` missing from compose.yml")
            continue

        host_ports = _compose_host_ports(service)
        expected_ports = {
            port
            for port in (
                _url_port(spec.get("url")),
                _url_port(spec.get("url_template")),
                spec.get("default_port_base"),
                *[extra.get("base") for extra in spec.get("extra_port_vars") or []],
            )
            if port
        }
        missing_ports = sorted(expected_ports - host_ports)
        if missing_ports:
            errors.append(
                f"{name}: catalog ports {missing_ports} missing from compose service `{service_name}` ports"
            )

        if spec.get("command") == "docker":
            target = _docker_exec_target(list(spec.get("args") or []))
            if target:
                allowed_targets = {service_name, _container_name(service_name, service)}
                if target not in allowed_targets:
                    errors.append(
                        f"{name}: docker exec target `{target}` does not match compose service "
                        f"`{service_name}` container `{_container_name(service_name, service)}`"
                    )

    return errors


def validate_legacy_registry_contract(repo_root: Path) -> list[str]:
    registry_path = repo_root / "src/dopemux/mcp/registry.yaml"
    try:
        registry = load_yaml_no_duplicate_keys(registry_path) or {}
    except DuplicateKeyError as exc:
        return [str(exc)]

    compose_services = load_compose(repo_root).get("services") or {}
    errors: list[str] = []
    for name, spec in sorted((registry.get("servers") or {}).items()):
        docker = spec.get("docker") or {}
        service_name = docker.get("service")
        if not service_name:
            continue
        service = compose_services.get(service_name)
        if not service:
            errors.append(f"{name}: docker.service `{service_name}` missing from compose.yml")
            continue
        health_url = docker.get("health_url")
        port = _url_port(health_url)
        if not health_url or port is None:
            errors.append(f"{name}: docker.health_url must include an absolute URL with a port")
        elif port not in _compose_host_ports(service):
            errors.append(
                f"{name}: health_url port {port} missing from compose service `{service_name}` ports"
            )
        if "healthcheck" not in service:
            errors.append(f"{name}: compose service `{service_name}` missing healthcheck")
    return errors


def validate_generated_mcp_json_parity(repo_root: Path) -> list[str]:
    catalog = load_root_catalog(repo_root)
    defaults = catalog.get("defaults", {}).get("per_worktree") or []
    expected = render_per_worktree_mcp_json(defaults, catalog)
    actual_path = repo_root / ".mcp.json"
    if not actual_path.exists():
        return [".mcp.json is missing"]
    actual = json.loads(actual_path.read_text(encoding="utf-8"))
    if actual != expected:
        return [".mcp.json does not match catalog defaults renderer"]
    return []
