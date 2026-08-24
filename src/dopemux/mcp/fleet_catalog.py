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
_MCP_TOOL_SURFACE_RE = re.compile(r"\bmcp__([A-Za-z0-9_-]+)__([A-Za-z0-9_-]+|\*)")
_CODEX_SERVER_HEADING_RE = re.compile(r'^\[mcp_servers\."([^"]+)"\]$', re.MULTILINE)

# Snapshot of the ConPort JSON-RPC dispatch map in
# docker/mcp-servers-source/conport/enhanced_server.py. Keep this static gate
# offline and deterministic; updating the runtime surface requires updating the
# snapshot deliberately in the same change.
_CONPORT_TOOL_SNAPSHOT = frozenset(
    {
        "conport_get_context",
        "conport_update_context",
        "conport_log_decision",
        "conport_get_decisions",
        "conport_log_progress",
        "conport_get_progress",
        "conport_update_progress",
        "conport_get_recent_activity",
        "conport_get_active_work",
        "conport_get_custom_data",
        "conport_save_custom_data",
        "conport_delete_custom_data",
        "conport_search_content",
        "conport_fork_instance",
        "conport_promote",
        "conport_promote_all",
    }
)
_MCP_TOOL_SNAPSHOTS = {"conport": _CONPORT_TOOL_SNAPSHOT}

# Managed-section markers for merge-style apply targets (MCPINT-FND-CODEGEN-005).
# Everything between BEGIN and END (inclusive) is generator-owned; content outside
# the markers is user-owned and preserved verbatim by the merge renderers.
OPENCODE_MANAGED_BEGIN = "// BEGIN dopemux-managed mcp"
OPENCODE_MANAGED_END = "// END dopemux-managed mcp"
CODEX_MANAGED_BEGIN = "# BEGIN dopemux-managed mcp_servers"
CODEX_MANAGED_END = "# END dopemux-managed mcp_servers"

# Planes whose full tool surface is read-safe (no repo/authority mutation), so a
# `read-plane` agents-matrix row may be honored by DIRECT client config while the
# universal read plane (dcp-readonly-facade) is still planned-active with no
# endpoint (ADR-MCPINT-002: read-plane = "facade projection and/or read-safe
# direct config"). Everything else waits for MCPINT-IMP-FACADE-001.
_READ_SAFE_DIRECT_PLANES = frozenset({"reasoning"})

# Codex renders `full` / `full-sequenced` rows; a missing `agents:` field
# (legacy or synthetic catalogs) records no restriction and stays renderable.
_CODEX_RENDERABLE_EXPOSURES = (None, "full", "full-sequenced")


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
        # Transport truth (P0 claim 11): pal-http is a health/lifecycle shim with
        # no MCP endpoint; quarantined until PAL-HTTP-RETROFIT is decided.
        "plane": "reasoning",
        "authority_role": "reasoning-infrastructure",
        "lifecycle": "decision-required",
        "management_model": "compose-service",
        "identity_scope": "singleton",
        "follow_on_decision": "wire-or-retire",
    },
    "pal-stdio": {
        "plane": "reasoning",
        "authority_role": "reasoning-infrastructure",
        "lifecycle": "operator-managed",
        "management_model": "docker-exec",
        "identity_scope": "singleton",
        "follow_on_decision": "none",
    },
    "desktop-commander": {
        "plane": "automation",
        "authority_role": "desktop-automation",
        "lifecycle": "decision-required",
        "management_model": "compose-service",
        "identity_scope": "host-session",
        "follow_on_decision": "delete-or-host-run",
    },
    "leantime-bridge": {
        # PM-sync plane (P0 claim 13): live compose service, no agent matrix row.
        "plane": "pm",
        "authority_role": "pm-adapter",
        "lifecycle": "active",
        "management_model": "compose-service",
        "identity_scope": "singleton",
        "follow_on_decision": "none",
    },
    "dcp-readonly-facade": {
        # Universal read plane (ADR-MCPINT-002): built, deploy owned by
        # MCPINT-IMP-FACADE-001 — planned-active until a listener exists.
        "plane": "dcp-read",
        "authority_role": "read-plane-projection",
        "lifecycle": "planned-active",
        "management_model": "compose-service",
        "identity_scope": "per-repo",
        "follow_on_decision": "none",
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


def _agent_exposure(spec: dict[str, Any], agent: str) -> str | None:
    """Exposure value for `agent` from this server's `agents:` matrix.

    Returns None when the spec carries no `agents:` field at all (legacy or
    synthetic catalogs — no restriction recorded). The sentinel string "none"
    (whole-server or per-agent) means explicitly no exposure; a matrix dict
    without a row for `agent` is treated as no exposure (the matrix is explicit).
    """
    agents = spec.get("agents")
    if agents is None:
        return None
    if agents == "none":
        return "none"
    if isinstance(agents, dict):
        return agents.get(agent, "none")
    return "none"


def _codex_server_lines(catalog: dict[str, Any]) -> list[str]:
    """Codex `[mcp_servers.*]` table lines for every codex-renderable server.

    Codex currently supports stdio and streamable HTTP MCP servers. SSE-only
    singleton entries stay represented in Claude/global and health outputs.
    Only `full` / `full-sequenced` codex agents-matrix rows render
    (ADR-MCPINT-001 §2 / ADR-MCPINT-002 §1).
    """
    lines: list[str] = []
    for name, spec in sorted(catalog.get("servers", {}).items()):
        if spec.get("scope") != "singleton":
            continue
        if not mcp_commands._is_startable_global_entry(spec):
            continue
        if _agent_exposure(spec, "codex") not in _CODEX_RENDERABLE_EXPOSURES:
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

    return lines


def render_codex_config_fragment(catalog: dict[str, Any]) -> str:
    """Render codex-renderable MCP servers in Codex `config.toml` syntax.

    This is the preview/projection output. The in-repo `.codex/config.toml`
    write is gated: codex exposure is `full-sequenced` (ADR-MCPINT-002 G1), so
    `dopemux mcp generate --apply` refuses it without `--allow-sequenced`.
    """

    lines = [
        "# Generated from mcp_catalog.yaml by `dopemux mcp generate`.",
        "# Dry-run is the default; review before copying into .codex/config.toml.",
        "# In-repo apply is sequenced (ADR-MCPINT-002 G1): `--apply --allow-sequenced`",
        "# writes .codex/config.toml only after DMX-MEMSPINE-IDENTITY-005 and",
        "# task-orchestrator actor_authentication.enabled have landed.",
        *_codex_server_lines(catalog),
    ]
    return "\n".join(lines) + "\n"


def render_codex_managed_region(catalog: dict[str, Any]) -> str:
    """The generator-owned `[mcp_servers.*]` region for in-repo .codex/config.toml."""
    lines = [
        CODEX_MANAGED_BEGIN
        + " — generated from mcp_catalog.yaml by `dopemux mcp generate --apply"
        + " --allow-sequenced`. Do not hand-edit this section.",
        *_codex_server_lines(catalog),
        "",
        CODEX_MANAGED_END,
    ]
    return "\n".join(lines)


def _extract_marked_region(text: str, begin: str, end: str) -> str | None:
    """Return the inclusive begin→end marked block of `text`, or None."""
    lines = text.splitlines()
    start = next(
        (index for index, line in enumerate(lines) if line.strip().startswith(begin)),
        None,
    )
    if start is None:
        return None
    stop = next(
        (
            index
            for index, line in enumerate(lines[start + 1 :], start=start + 1)
            if line.strip().startswith(end)
        ),
        None,
    )
    if stop is None:
        return None
    return "\n".join(lines[start : stop + 1])


def merge_codex_config_toml(existing_text: str | None, catalog: dict[str, Any]) -> str:
    """Merge the managed `mcp_servers` region into an existing .codex/config.toml.

    Additive and marker-delimited: user keys (model, [agents], approval_policy,
    …) are preserved verbatim; only the marked region is replaced (or appended
    when absent). Hand-authored `[mcp_servers.*]` tables outside the markers are
    a contract violation (generated files are never hand-edited — ADR-MCPINT-001)
    and abort the merge.
    """
    region = render_codex_managed_region(catalog)
    text = existing_text or ""
    existing_region = _extract_marked_region(text, CODEX_MANAGED_BEGIN, CODEX_MANAGED_END)
    if existing_region is not None:
        remainder = text.replace(existing_region, "", 1)
        if "[mcp_servers." in remainder:
            raise MCPFleetCatalogError(
                ".codex/config.toml declares [mcp_servers.*] outside the dopemux-managed "
                "markers; remove the hand-authored tables before `--allow-sequenced` apply."
            )
        merged = text.replace(existing_region, region, 1)
        return merged if merged.endswith("\n") else merged + "\n"
    if "[mcp_servers." in text:
        raise MCPFleetCatalogError(
            ".codex/config.toml declares [mcp_servers.*] outside the dopemux-managed "
            "markers; remove the hand-authored tables before `--allow-sequenced` apply."
        )
    base = text.rstrip("\n")
    prefix = base + "\n\n" if base else ""
    return prefix + region + "\n"


# ---------------------------------------------------------------------------
# OpenCode (opencode.jsonc) — managed-merge renderer (MCPINT-FND-CODEGEN-005)
# ---------------------------------------------------------------------------


def _strip_jsonc_comments(text: str) -> str:
    """Strip // and /* */ comments from JSONC while preserving string contents."""
    out: list[str] = []
    index = 0
    length = len(text)
    in_string = False
    while index < length:
        char = text[index]
        if in_string:
            out.append(char)
            if char == "\\" and index + 1 < length:
                out.append(text[index + 1])
                index += 2
                continue
            if char == '"':
                in_string = False
            index += 1
            continue
        if char == '"':
            in_string = True
            out.append(char)
            index += 1
            continue
        if char == "/" and index + 1 < length and text[index + 1] == "/":
            while index < length and text[index] != "\n":
                index += 1
            continue
        if char == "/" and index + 1 < length and text[index + 1] == "*":
            index += 2
            while index + 1 < length and not (text[index] == "*" and text[index + 1] == "/"):
                index += 1
            index += 2
            continue
        out.append(char)
        index += 1
    return "".join(out)


def _opencode_entry(spec: dict[str, Any]) -> dict[str, Any] | None:
    """Render one catalog spec as an OpenCode `mcp` entry, or None if not renderable."""
    transport = spec.get("transport", "http")
    if transport == "stdio":
        command = spec.get("command")
        if not command:
            return None
        entry: dict[str, Any] = {
            "type": "local",
            "command": [command, *list(spec.get("args") or [])],
            "enabled": True,
        }
        env_vars = _codex_env_vars(spec)
        if env_vars:
            entry["environment"] = {key: f"{{env:{key}}}" for key in env_vars}
        return entry
    if transport == "http":
        url = spec.get("url")
        if not url:
            return None
        return {"type": "remote", "url": url, "enabled": True}
    return None


def render_opencode_mcp_servers(catalog: dict[str, Any]) -> dict[str, Any]:
    """OpenCode `mcp` mapping rendered truthfully from the catalog.

    `read-plane` rows (ADR-MCPINT-002) are honored by DIRECT config only for
    read-safe planes (see `_READ_SAFE_DIRECT_PLANES`); everything else joins via
    the dcp-readonly-facade once MCPINT-IMP-FACADE-001 deploys a real listener.
    No endpoint is ever invented for planned-active/url-less entries.
    """
    servers: dict[str, Any] = {}
    for name, spec in sorted(catalog.get("servers", {}).items()):
        exposure = _agent_exposure(spec, "opencode")
        if exposure not in {"full", "read-plane"}:
            continue
        if not mcp_commands._is_startable_global_entry(spec):
            continue
        if exposure == "read-plane" and spec.get("plane") not in _READ_SAFE_DIRECT_PLANES:
            continue
        entry = _opencode_entry(spec)
        if entry is None:
            continue
        servers[name] = entry
    return servers


def _opencode_deferred_servers(catalog: dict[str, Any]) -> list[str]:
    """Servers with an opencode exposure row that cannot render truthfully today."""
    rendered = set(render_opencode_mcp_servers(catalog))
    return [
        name
        for name, spec in sorted(catalog.get("servers", {}).items())
        if _agent_exposure(spec, "opencode") in {"full", "read-plane"} and name not in rendered
    ]


def render_opencode_managed_section_lines(catalog: dict[str, Any]) -> list[str]:
    """The generator-owned opencode.jsonc lines (comments + `"mcp": {...}`), 2-space indented."""
    lines = [
        f"  {OPENCODE_MANAGED_BEGIN} — generated from mcp_catalog.yaml by"
        " `dopemux mcp generate --apply`. Do not hand-edit this section.",
        "  // Read-plane rows (ADR-MCPINT-002) render here only where a read-safe DIRECT",
        "  // config exists today; the universal read plane (dcp-readonly-facade) is",
        "  // planned-active with no endpoint until MCPINT-IMP-FACADE-001 deploys it.",
    ]
    deferred = _opencode_deferred_servers(catalog)
    if deferred:
        lines.append("  // Deferred to the facade: " + ", ".join(deferred))
    payload = json.dumps({"mcp": render_opencode_mcp_servers(catalog)}, indent=2, sort_keys=True)
    lines.extend(payload.splitlines()[1:-1])
    lines.append(f"  {OPENCODE_MANAGED_END}")
    return lines


def render_opencode_managed_preview(catalog: dict[str, Any]) -> str:
    """Standalone JSONC preview of the managed opencode section (output-dir projection)."""
    return "{\n" + "\n".join(render_opencode_managed_section_lines(catalog)) + "\n}\n"


def render_opencode_jsonc(existing_text: str | None, catalog: dict[str, Any]) -> str:
    """Merge the managed `mcp` section into opencode.jsonc, preserving user keys.

    Only the marker-delimited managed section (the `mcp` key) is generator-owned;
    every other top-level key (`$schema`, `instructions`, `permission`, …) is
    preserved with its original relative order. The managed section replaces the
    existing `mcp` key in place, or is inserted before `permission` (or appended)
    when no `mcp` key exists yet.
    """
    if existing_text and existing_text.strip():
        try:
            data = json.loads(_strip_jsonc_comments(existing_text))
        except json.JSONDecodeError as exc:
            raise MCPFleetCatalogError(f"opencode.jsonc is not parseable JSONC: {exc}") from exc
        if not isinstance(data, dict):
            raise MCPFleetCatalogError("opencode.jsonc must contain a top-level object.")
    else:
        data = {}

    managed = object()
    slots: list[Any] = [managed if key == "mcp" else key for key in data]
    if managed not in slots:
        if "permission" in slots:
            slots.insert(slots.index("permission"), managed)
        else:
            slots.append(managed)

    section = render_opencode_managed_section_lines(catalog)
    lines: list[str] = ["{"]
    for index, slot in enumerate(slots):
        is_last = index == len(slots) - 1
        if slot is managed:
            block = list(section)
            if not is_last:
                # The trailing comma goes on the last JSON line, not the END comment.
                for position in range(len(block) - 1, -1, -1):
                    if not block[position].lstrip().startswith("//"):
                        block[position] += ","
                        break
            lines.extend(block)
        else:
            chunk = json.dumps({slot: data[slot]}, indent=2).splitlines()[1:-1]
            if not is_last:
                chunk[-1] += ","
            lines.extend(chunk)
    lines.append("}")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Copilot proxy (mcp-proxy-config.copilot.yaml) renderer (MCPINT-FND-CODEGEN-005)
# ---------------------------------------------------------------------------


def render_copilot_proxy_config(catalog: dict[str, Any]) -> str:
    """Regenerate mcp-proxy-config.copilot.yaml from the catalog.

    Includes only catalog servers whose `agents.copilot` row grants exposure
    (`full` / `full-sequenced` / `read-plane`), with their contractual catalog
    transports. Planned-active entries (no truthful endpoint yet) are named in a
    header comment instead of being invented.
    """
    servers: dict[str, Any] = {}
    deferred: list[str] = []
    for name, spec in sorted(catalog.get("servers", {}).items()):
        exposure = _agent_exposure(spec, "copilot")
        if exposure not in {"full", "full-sequenced", "read-plane"}:
            continue
        if not mcp_commands._is_startable_global_entry(spec):
            if spec.get("lifecycle") == "planned-active":
                deferred.append(name)
            continue
        transport = spec.get("transport", "http")
        if transport == "stdio":
            command = spec.get("command")
            if not command:
                raise MCPFleetCatalogError(
                    f"`{name}` requires `command` for the Copilot proxy config."
                )
            entry: dict[str, Any] = {
                "type": "stdio",
                "command": command,
                "args": list(spec.get("args") or []),
            }
            env_vars = _codex_env_vars(spec)
            if env_vars:
                entry["env"] = {key: f"${{{key}}}" for key in env_vars}
        elif transport in {"http", "sse"}:
            url = spec.get("url") or spec.get("url_template")
            if not url:
                raise MCPFleetCatalogError(
                    f"`{name}` requires `url`/`url_template` for the Copilot proxy config."
                )
            entry = {"type": transport, "url": url}
        else:
            continue
        servers[name] = entry

    lines = [
        "# Generated from mcp_catalog.yaml by `dopemux mcp generate`. Do not hand-edit.",
        "# Copilot proxy MCP servers — catalog entries whose `agents.copilot` row grants",
        "# exposure (ADR-MCPINT-001 §2 / ADR-MCPINT-002; renderer: MCPINT-FND-CODEGEN-005).",
    ]
    if deferred:
        lines.append(
            "# Deferred (planned-active, no endpoint yet — deployed by MCPINT-IMP-FACADE-001): "
            + ", ".join(deferred)
        )
    payload = yaml.safe_dump({"mcpServers": servers}, sort_keys=True, default_flow_style=False)
    return "\n".join(lines) + "\n" + payload


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
    """Agent-matrix fleet projection (ADR-MCPINT-001). Not an implicit profile=all.

    Profile-selected generation uses :func:`generate_profile_output_files`.
    """
    defaults = catalog.get("defaults", {}).get("per_worktree") or []
    return {
        "local/.mcp.json": _json_dumps(render_per_worktree_mcp_json(defaults, catalog)),
        "claude/mcpServers.json": _json_dumps(
            {"mcpServers": render_singleton_mcp_servers(catalog)}
        ),
        "codex/config.toml": render_codex_config_fragment(catalog),
        "opencode/opencode.managed.jsonc": render_opencode_managed_preview(catalog),
        "copilot/mcp-proxy-config.copilot.yaml": render_copilot_proxy_config(catalog),
        "health/mcp-health-probes.json": _json_dumps(render_health_probe_list(catalog)),
        "docs/mcp-fleet.md": render_mcp_doctrine_doc(catalog),
    }


def generate_profile_output_files(
    catalog: dict[str, Any],
    profile_name: str,
    *,
    repo_root: Path | None = None,
) -> dict[str, str]:
    """Deterministic profile-selected projection (ADR-DMX-MCPPROF-001).

    Emits inventory + filtered local mcpServers for the named profile only.
    Never expands to all catalog servers.
    """
    from dopemux.mcp import profile_policy

    inventory = profile_policy.resolve_profile(
        catalog,
        profile_name,
        repo_root=repo_root,
        check_inventory_baseline=True,
    )
    selected = list(inventory.selected_servers)
    servers_map = catalog.get("servers") or {}
    per_worktree = [
        name
        for name in selected
        if isinstance(servers_map.get(name), dict)
        and servers_map[name].get("scope") == "per-worktree"
    ]
    # Local .mcp.json: per-worktree members of the profile (may be empty).
    local_payload = render_per_worktree_mcp_json(per_worktree, catalog)
    # Profile mcpServers: startable selected servers only (skip external/managed false
    # for executable config; still listed in inventory JSON).
    profile_servers: dict[str, Any] = {}
    for name in selected:
        spec = servers_map.get(name)
        if not isinstance(spec, dict):
            continue
        if spec.get("transport") == "external" or spec.get("managed") is False:
            continue
        if spec.get("lifecycle") in {"decision-required", "planned-active"}:
            continue
        if spec.get("scope") == "per-worktree":
            profile_servers[name] = mcp_commands._render_local_entry(name, spec)
        else:
            profile_servers[name] = mcp_commands._render_global_entry(name, spec)

    return {
        f"profiles/{inventory.profile}/inventory.json": _json_dumps(inventory.to_dict()),
        f"profiles/{inventory.profile}/.mcp.json": _json_dumps(local_payload),
        f"profiles/{inventory.profile}/mcpServers.json": _json_dumps(
            {
                "profile": inventory.profile,
                "profile_digest": inventory.profile_digest,
                "tool_schema_digest": inventory.tool_schema_digest,
                "mcpServers": profile_servers,
            }
        ),
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

    opencode_payload = rendered.get("opencode/opencode.managed.jsonc")
    if opencode_payload:
        try:
            opencode_data = json.loads(_strip_jsonc_comments(opencode_payload))
        except json.JSONDecodeError:
            errors.append("opencode/opencode.managed.jsonc is not parseable JSONC")
        else:
            startable_outputs["opencode/opencode.managed.jsonc"] = set(
                opencode_data.get("mcp") or {}
            )

    copilot_payload = rendered.get("copilot/mcp-proxy-config.copilot.yaml")
    if copilot_payload:
        copilot_data = yaml.safe_load(copilot_payload) or {}
        startable_outputs["copilot/mcp-proxy-config.copilot.yaml"] = set(
            copilot_data.get("mcpServers") or {}
        )

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


def extract_mcp_tool_references(text: str) -> list[tuple[str, str]]:
    return [match.groups() for match in _MCP_TOOL_SURFACE_RE.finditer(text)]


def find_unknown_command_tool_surfaces(
    command_dir: Path,
    catalog: dict[str, Any],
) -> list[str]:
    known = known_tool_surfaces(catalog)
    unknown: list[str] = []
    for path in sorted(command_dir.rglob("*.md")):
        for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            for surface, tool_name in extract_mcp_tool_references(line):
                if surface not in known:
                    unknown.append(f"{path}:{index}:{surface}")
                    continue
                known_tools = _MCP_TOOL_SNAPSHOTS.get(surface)
                if known_tools is not None and tool_name != "*" and tool_name not in known_tools:
                    unknown.append(f"{path}:{index}:{surface}:{tool_name}")
    return unknown


_REQUIRED_PERSONALITY_FIELDS = (
    "authority_role",
    "lifecycle",
    "management_model",
    "identity_scope",
)


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
        if not isinstance(spec, dict):
            continue
        missing_fields = [
            field for field in _REQUIRED_PERSONALITY_FIELDS if spec.get(field) is None
        ]
        if missing_fields:
            errors.append(
                f"{name}: missing required personality field(s) {missing_fields} "
                "(every catalog server must carry authority_role, lifecycle, "
                "management_model, identity_scope)"
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


def validate_opencode_jsonc_parity(repo_root: Path) -> list[str]:
    """Parity gate for the opencode.jsonc apply target (MCPINT-FND-CODEGEN-005).

    Parity holds over the managed section only: the committed file must carry
    the managed markers and its `mcp` mapping must equal the fresh catalog
    render. User-owned keys (`permission`, `instructions`, …) are not checked.
    """
    path = repo_root / "opencode.jsonc"
    if not path.exists():
        return ["opencode.jsonc is missing — run `dopemux mcp generate --apply`"]
    text = path.read_text(encoding="utf-8")
    if OPENCODE_MANAGED_BEGIN not in text or OPENCODE_MANAGED_END not in text:
        return [
            "opencode.jsonc is missing the dopemux-managed mcp section markers — "
            "run `dopemux mcp generate --apply`"
        ]
    try:
        data = json.loads(_strip_jsonc_comments(text))
    except json.JSONDecodeError as exc:
        return [f"opencode.jsonc is not parseable JSONC: {exc}"]
    expected = render_opencode_mcp_servers(load_root_catalog(repo_root))
    if data.get("mcp") != expected:
        return [
            "opencode.jsonc managed `mcp` section does not match the catalog renderer — "
            "re-run `dopemux mcp generate --apply`"
        ]
    return []


def validate_copilot_proxy_config_parity(repo_root: Path) -> list[str]:
    """Parity gate for the fully-generated mcp-proxy-config.copilot.yaml target."""
    path = repo_root / "mcp-proxy-config.copilot.yaml"
    if not path.exists():
        return ["mcp-proxy-config.copilot.yaml is missing — run `dopemux mcp generate --apply`"]
    expected = render_copilot_proxy_config(load_root_catalog(repo_root))
    if path.read_text(encoding="utf-8") != expected:
        return [
            "mcp-proxy-config.copilot.yaml does not match the catalog renderer — "
            "re-run `dopemux mcp generate --apply`"
        ]
    return []


def validate_codex_config_toml_parity(repo_root: Path) -> list[str]:
    """Parity gate for the sequenced .codex/config.toml target (ADR-MCPINT-002 G1).

    Until `--allow-sequenced` apply lands the managed region (sequencing
    prerequisites DMX-MEMSPINE-IDENTITY-005 + actor_authentication.enabled are
    unmet), the gate only enforces that no `[mcp_servers.*]` tables drift into
    the file outside generator ownership. Once the managed region exists it must
    equal the fresh catalog render, and nothing outside it may declare servers.
    """
    path = repo_root / ".codex/config.toml"
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    region = _extract_marked_region(text, CODEX_MANAGED_BEGIN, CODEX_MANAGED_END)
    if region is None:
        if CODEX_MANAGED_BEGIN in text or CODEX_MANAGED_END in text:
            return [".codex/config.toml has malformed dopemux-managed mcp_servers markers"]
        if "[mcp_servers." in text:
            return [
                ".codex/config.toml declares [mcp_servers.*] outside the dopemux-managed "
                "region — codex configs are produced only by `dopemux mcp generate --apply "
                "--allow-sequenced` (ADR-MCPINT-001 §2 / ADR-MCPINT-002 §1)"
            ]
        return []
    errors: list[str] = []
    if region != render_codex_managed_region(load_root_catalog(repo_root)):
        errors.append(
            ".codex/config.toml dopemux-managed mcp_servers region does not match the "
            "catalog renderer — re-run `dopemux mcp generate --apply --allow-sequenced`"
        )
    if "[mcp_servers." in text.replace(region, "", 1):
        errors.append(
            ".codex/config.toml declares [mcp_servers.*] outside the dopemux-managed region"
        )
    return errors
