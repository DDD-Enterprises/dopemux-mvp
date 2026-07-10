"""
MCP Server Management Commands

Commands for starting, stopping, and monitoring MCP Docker servers
(``up``/``down``/``status``/``logs``/``start-all``), plus MCP config
scaffolding driven by repo-local or bundled ``mcp_catalog.yaml`` data
(``init``/``add``/``remove``/``list``/``doctor``/``sync-globals``).

The ``servers`` group is an alias for ``mcp`` for backward compatibility.
"""

import asyncio
import hashlib
import importlib.resources
import json
import os
import re
import shutil
import socket
import sys
import subprocess
from datetime import datetime
from pathlib import Path
from subprocess import CalledProcessError
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import click
import yaml

from ..console import console
from ..mcp.project_identity import ProjectIdentityError, resolve_project_identity
from ..worktree_commands import get_repo_root


# desktop-commander and exa are quarantined (lifecycle: decision-required)
# and excluded from the default set; start them explicitly via --services.
DEFAULT_MCP_SERVICES = {
    "adhd-engine",
    "conport",
    "dope-context",
    "dope-memory",
    "dopecon-bridge",
    "gptr-mcp",
    "leantime-bridge",
    "litellm",
    "pal",
    "serena",
    "task-orchestrator",
}


def _compose_path() -> Path:
    return Path.cwd() / "compose.yml"


def _compose_services(compose_path: Path | None = None) -> set[str]:
    """Return service names declared by the active compose file."""
    path = compose_path or _compose_path()
    if not path.exists():
        return set(DEFAULT_MCP_SERVICES)

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise click.ClickException(f"Invalid compose file {path}: {exc}") from exc

    services = data.get("services", {}) if isinstance(data, dict) else {}
    if not isinstance(services, dict):
        raise click.ClickException(f"Invalid compose file {path}: services must be a mapping")
    return {str(name) for name in services}


def _parse_services(services: str | None, *, allowed: set[str] | None = None) -> list[str]:
    parsed = [svc.strip() for svc in (services or "").split(",") if svc.strip()]
    if not parsed:
        return []

    allowed_services = allowed or _compose_services()
    invalid = sorted(set(parsed) - allowed_services)
    if invalid:
        valid_hint = ", ".join(sorted(allowed_services))
        raise click.ClickException(
            f"Unknown compose service(s): {', '.join(invalid)}. Valid services: {valid_hint}"
        )
    return parsed


@click.group()
def mcp():
    """
    🔬 Neural Architecture: Command the MCP infrastructure

    Manages the Docker-based Model Context Protocol servers. These daemons 
    (ConPort, PAL, Serena, etc.) provide the underlying neural architecture 
    for the cockpit's tool capabilities and semantic context management.
    """


def _lifecycle_repo_option():
    return click.option(
        "--repo",
        "repo_arg",
        type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
        default=None,
        help="Target repo/worktree (default: cwd). Works without compose.yml in the target.",
    )


def _lifecycle_services_option():
    return click.option(
        "--services",
        "services",
        default=None,
        help="Comma-separated project-scoped services (conport,dope-memory,task-orchestrator).",
    )


def _run_lifecycle_cli(
    operation: str,
    *,
    repo_arg: Optional[Path],
    services: Optional[str],
    dry_run: bool,
    json_output: bool,
) -> None:
    """Shared entry for start/stop/restart/status reconciler."""
    from dopemux.mcp.lifecycle import format_lifecycle_human, run_lifecycle

    catalog = _load_catalog()
    svc_list = [s.strip() for s in (services or "").split(",") if s.strip()] or None
    result = run_lifecycle(
        operation,
        repo=repo_arg,
        services=svc_list,
        catalog=catalog,
        dry_run=dry_run,
        process_env=dict(os.environ),
    )
    if json_output:
        sys.stdout.write(result.to_json())
    else:
        text = format_lifecycle_human(result)
        if result.status in {"PASS", "PLANNED"}:
            console.logger.info(f"[success]{text.rstrip()}[/success]")
        elif result.status in {"PASS_WITH_WARNINGS"}:
            console.logger.info(f"[warning]{text.rstrip()}[/warning]")
        elif result.status in {"FAIL", "BLOCKED"}:
            console.logger.info(f"[error]{text.rstrip()}[/error]")
        else:
            console.logger.info(f"[info]{text.rstrip()}[/info]")
    if result.exit_code:
        sys.exit(result.exit_code)


@mcp.command("start")
@_lifecycle_repo_option()
@_lifecycle_services_option()
@click.option("--dry-run", is_flag=True, help="Plan only; no Docker mutations, no registry writes.")
@click.option("--json", "json_output", is_flag=True, help="Emit lifecycle JSON report.")
def mcp_start_cmd(repo_arg: Optional[Path], services: Optional[str], dry_run: bool, json_output: bool):
    """
    🚀 Start project-scoped MCP sidecars (repo-aware reconciler)

    Starts conport / dope-memory / task-orchestrator for the target repo with
    unique names, labels, absolute memory volumes, and runtime registry updates.
    Does not use the unsafe env-injection compose pattern.
    """
    _run_lifecycle_cli(
        "start",
        repo_arg=repo_arg,
        services=services,
        dry_run=dry_run,
        json_output=json_output,
    )


@mcp.command("stop")
@_lifecycle_repo_option()
@_lifecycle_services_option()
@click.option("--dry-run", is_flag=True, help="Plan only; do not stop containers.")
@click.option("--json", "json_output", is_flag=True, help="Emit lifecycle JSON report.")
def mcp_stop_cmd(repo_arg: Optional[Path], services: Optional[str], dry_run: bool, json_output: bool):
    """
    🛑 Stop Dopemux-managed MCP sidecars for a target repo

    Stops only containers with dopemux.managed=true and matching project labels
    (or registry-known task-orchestrator wrappers). Never stops unlabeled strangers.
    """
    _run_lifecycle_cli(
        "stop",
        repo_arg=repo_arg,
        services=services,
        dry_run=dry_run,
        json_output=json_output,
    )


@mcp.command("restart")
@_lifecycle_repo_option()
@_lifecycle_services_option()
@click.option("--dry-run", is_flag=True, help="Plan stop+start without mutations.")
@click.option("--json", "json_output", is_flag=True, help="Emit lifecycle JSON report.")
def mcp_restart_cmd(repo_arg: Optional[Path], services: Optional[str], dry_run: bool, json_output: bool):
    """♻️ Restart project-scoped MCP sidecars (safe stop then start)."""
    _run_lifecycle_cli(
        "restart",
        repo_arg=repo_arg,
        services=services,
        dry_run=dry_run,
        json_output=json_output,
    )


@mcp.command("up")
@click.option("--all", "all_services", is_flag=True, help="🚀 Boot Fleet: Start every configured MCP service simultaneously.")
@click.option("--services", "services", help="🎯 Targeted Ignition: Comma-separated list of specific MCP services to ignite.")
@_lifecycle_repo_option()
@click.option("--dry-run", is_flag=True, help="When --repo is set: plan-only reconciler start.")
@click.option("--json", "json_output", is_flag=True, help="When --repo is set: JSON lifecycle report.")
def mcp_up_cmd(
    all_services: bool,
    services: str,
    repo_arg: Optional[Path],
    dry_run: bool,
    json_output: bool,
):
    """
    ⚡ Ignite Engine: Deploy MCP servers

    With ``--repo``: compatibility alias for ``dopemux mcp start --repo``.
    Without ``--repo``: legacy cwd compose / start-all-mcp-servers.sh behavior.
    ``--dry-run`` / ``--json`` only apply with ``--repo`` (ignored otherwise).
    """
    if repo_arg is not None:
        _run_lifecycle_cli(
            "start",
            repo_arg=repo_arg,
            services=services,
            dry_run=dry_run,
            json_output=json_output,
        )
        return
    try:
        script_dir = Path(__file__).parent.parent.parent.parent / "scripts"
        script_path = script_dir / "start-all-mcp-servers.sh"

        if all_services or not services:
            cmd = ["bash", str(script_path)]
        else:
            svc_list = _parse_services(services)
            cmd = ["docker", "compose", "-f", "compose.yml", "up", "-d", "--build"] + svc_list
        console.logger.info(f"[info]{' '.join(cmd)}[/info]")
        subprocess.run(cmd, check=True)
        console.logger.info("[success]MCP servers started[/success]")
    except (CalledProcessError, FileNotFoundError) as exc:
        console.logger.error(f"[error]Failed to start MCP servers: {exc}[/error]")
        sys.exit(1)


@mcp.command("down")
@_lifecycle_repo_option()
@_lifecycle_services_option()
@click.option("--dry-run", is_flag=True, help="When --repo is set: plan-only stop.")
@click.option("--json", "json_output", is_flag=True, help="When --repo is set: JSON lifecycle report.")
def mcp_down_cmd(
    repo_arg: Optional[Path],
    services: Optional[str],
    dry_run: bool,
    json_output: bool,
):
    """
    💧 Cool Down Cores: Terminate MCP containers

    With ``--repo``: compatibility alias for ``dopemux mcp stop --repo``.
    Without ``--repo``: legacy cwd compose rm behavior.
    ``--dry-run`` / ``--json`` only apply with ``--repo`` (ignored otherwise).
    """
    if repo_arg is not None:
        _run_lifecycle_cli(
            "stop",
            repo_arg=repo_arg,
            services=services,
            dry_run=dry_run,
            json_output=json_output,
        )
        return
    try:
        # Derive from the default set so `down` stays symmetric with `up`
        # (previously a hardcoded list that omitted several running services).
        mcp_services = sorted(DEFAULT_MCP_SERVICES & _compose_services())
        if not mcp_services:
            mcp_services = sorted(DEFAULT_MCP_SERVICES)
        subprocess.run(
            ["docker", "compose", "-f", "compose.yml", "rm", "-f", "-s", "-v"] + mcp_services,
            check=True,
        )
        console.logger.info("[success]MCP servers stopped[/success]")
    except (CalledProcessError, FileNotFoundError) as exc:
        console.logger.error(f"[error]Failed to stop MCP servers: {exc}[/error]")
        sys.exit(1)


@mcp.command("status")
@_lifecycle_repo_option()
@click.option("--json", "json_output", is_flag=True, help="Emit repo-aware status JSON (registry+docker+probes).")
@click.option(
    "--legacy-compose",
    is_flag=True,
    help="Force legacy `docker compose ps` from cwd (ignores --repo).",
)
def mcp_status_cmd(repo_arg: Optional[Path], json_output: bool, legacy_compose: bool):
    """
    📊 Diagnostic HUD: Interrogate MCP service health

    Default / with ``--repo`` / ``--json``: repo-aware status (registry + Docker + probes).
    ``--legacy-compose``: previous cwd `docker compose ps` behavior.
    """
    if legacy_compose:
        try:
            subprocess.run(["docker", "compose", "-f", "compose.yml", "ps"], check=True)
        except (CalledProcessError, FileNotFoundError):
            sys.exit(1)
        return

    # Prefer reconciler status when --repo/--json or target has .mcp.json
    use_reconciler = (
        repo_arg is not None
        or json_output
        or (Path.cwd() / PROJECT_MCP_FILENAME).exists()
        or (Path.cwd() / ENVRC_FILENAME).exists()
    )
    if use_reconciler:
        _run_lifecycle_cli(
            "status",
            repo_arg=repo_arg,
            services=None,
            dry_run=False,
            json_output=json_output,
        )
        return
    try:
        subprocess.run(["docker", "compose", "-f", "compose.yml", "ps"], check=True)
    except (CalledProcessError, FileNotFoundError):
        sys.exit(1)


@mcp.command("logs")
@click.option("--service", "service", help="📊 Telemetry Filter: Focus the log stream on a specific MCP daemon.")
def mcp_logs_cmd(service: str):
    """
    🧠 Tap Telemetry: Stream real-time log data from MCP services

    Enables direct observation of the signal exchange between the cockpit 
    and its distributed toolset for granular ritual debugging.
    """
    try:
        if service:
            svc_list = _parse_services(service)
            cmd = ["docker", "compose", "-f", "compose.yml", "logs", "-f"] + svc_list
        else:
            cmd = ["docker", "compose", "-f", "compose.yml", "logs", "-f"]
        console.logger.info(f"[info]{' '.join(cmd)}[/info]")
        subprocess.run(cmd, check=True)
    except (CalledProcessError, FileNotFoundError):
        sys.exit(1)


@mcp.command("start-all")
@click.option("--verify", "-v", is_flag=True, help="✅ Verify Pulse: Execute high-fidelity health checks after ignition.")
def mcp_start_all_cmd(verify: bool):
    """
    🧙 Summon Ecosystem: Ignite the complete DØPEMÜX stack

    Initiates the full ritual environment: MCP servers, Integration Bridge, 
    Task Orchestrator, and application services. Primes the cockpit for 
    intensive work log sessions.
    """
    try:
        script_path = Path(__file__).parent.parent.parent.parent / "scripts" / "start-all.sh"

        if not script_path.exists():
            console.logger.info(f"[error]start-all.sh not found at {script_path}[/error]")
            console.logger.info("[warning]Falling back to manual startup...[/warning]")

            console.logger.info("[info]Starting MCP servers...[/info]")
            subprocess.run(["docker", "compose", "-f", "compose.yml", "up", "-d"], check=True)

            # NOTE: the legacy docker/conport-kg integration-bridge is dead
            # code (kill-list per the MCP fleet audit) and must not be
            # resurrected here.

            console.logger.info("[info]Starting Task Orchestrator...[/info]")
            subprocess.run(
                ["docker", "compose", "-f", "compose.yml", "--profile", "manual", "up", "-d", "task-orchestrator"],
                check=True,
            )

            console.logger.info("[success]All services started[/success]")
        else:
            cmd = ["bash", str(script_path)]
            if verify:
                cmd.append("--verify")
            subprocess.run(cmd, check=True)

    except CalledProcessError:
        console.logger.error("[error]Failed to start all services[/error]")
        console.logger.info("[warning]Try: docker ps to see running containers[/warning]")
        sys.exit(1)


# ---------------------------------------------------------------------------
# `servers` group — alias for `mcp`
# ---------------------------------------------------------------------------

@click.group()
def servers():
    """
    🔬 Cockpit Alias: Alternative entry point for MCP operations

    Inherits all Model Context Protocol management capabilities. Provides 
    a secondary routing path for managing the neural server fleet.
    """


@servers.command("up")
@click.option("--all", "all_services", is_flag=True, help="🚀 Boot Fleet: Start every configured MCP service simultaneously.")
@click.option("--services", "services", help="🎯 Targeted Ignition: Comma-separated list of specific MCP services to ignite.")
@click.option("--repo", "repo_arg", type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path), default=None)
@click.option("--dry-run", is_flag=True)
@click.option("--json", "json_output", is_flag=True)
def servers_up_cmd(
    all_services: bool,
    services: str,
    repo_arg: Optional[Path],
    dry_run: bool,
    json_output: bool,
):
    """
    ⚡ Ignite Engine (Alias): Deploy MCP servers via Docker Compose
    """
    mcp_up_cmd.callback(all_services, services, repo_arg, dry_run, json_output)


@servers.command("down")
@click.option("--repo", "repo_arg", type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path), default=None)
@click.option("--services", "services", default=None)
@click.option("--dry-run", is_flag=True)
@click.option("--json", "json_output", is_flag=True)
def servers_down_cmd(
    repo_arg: Optional[Path],
    services: Optional[str],
    dry_run: bool,
    json_output: bool,
):
    """
    💧 Cool Down Cores (Alias): Terminate MCP containers and volumes
    """
    mcp_down_cmd.callback(repo_arg, services, dry_run, json_output)


@servers.command("status")
@click.option("--repo", "repo_arg", type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path), default=None)
@click.option("--json", "json_output", is_flag=True)
@click.option("--legacy-compose", is_flag=True)
def servers_status_cmd(repo_arg: Optional[Path], json_output: bool, legacy_compose: bool):
    """
    📊 Diagnostic HUD (Alias): Interrogate MCP service health
    """
    mcp_status_cmd.callback(repo_arg, json_output, legacy_compose)


@servers.command("logs")
@click.option("--service", "service", help="📊 Telemetry Filter: Focus the log stream on a specific MCP daemon.")
def servers_logs_cmd(service: str):
    """
    🧠 Tap Telemetry (Alias): Stream real-time log data
    """
    mcp_logs_cmd.callback(service)


# ---------------------------------------------------------------------------
# Catalog-driven config management
# ---------------------------------------------------------------------------
#
# These subcommands read ``mcp_catalog.yaml`` at the repo root and use it to
# manage two distinct surfaces:
#
#   ~/.claude.json mcpServers   — singletons shared across all worktrees
#   <worktree>/.mcp.json        — per-worktree servers with env-var ports
#
# Per-worktree port allocation is deterministic:
#     port = base + (sha1(worktree_abspath)[:4]_hex % 100)
# giving each worktree a stable port offset in a 100-port window per service.

CATALOG_FILENAME = "mcp_catalog.yaml"
CATALOG_ENV_VAR = "DOPEMUX_MCP_CATALOG"
DEFAULT_CATALOG_RESOURCE = "default_catalog.yaml"
PROJECT_MCP_FILENAME = ".mcp.json"
ENVRC_FILENAME = ".envrc.dopemux-mcp"   # sourced from .envrc; keeps generated content separate


def _catalog_path() -> Optional[Path]:
    """Locate an explicit or repo-local MCP catalog path, if present."""
    explicit = os.environ.get(CATALOG_ENV_VAR)
    if explicit:
        path = Path(explicit).expanduser().resolve()
        if not path.is_file():
            raise click.ClickException(
                f"{CATALOG_ENV_VAR} points to a missing catalog: {path}"
            )
        return path

    repo = get_repo_root(fallback_cwd=False)
    if repo:
        candidate = Path(repo) / CATALOG_FILENAME
        if candidate.exists():
            return candidate
    return None


def _load_catalog() -> Dict[str, Any]:
    catalog_path = _catalog_path()
    if catalog_path:
        with catalog_path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
    else:
        try:
            resource = importlib.resources.files("dopemux.mcp").joinpath(
                DEFAULT_CATALOG_RESOURCE
            )
            with resource.open("r", encoding="utf-8") as fh:
                data = yaml.safe_load(fh) or {}
        except FileNotFoundError as exc:
            raise click.ClickException(
                f"Bundled MCP catalog `{DEFAULT_CATALOG_RESOURCE}` is missing."
            ) from exc

    if data.get("version") != 1:
        raise click.ClickException(
            f"Unsupported catalog version: {data.get('version')!r}. Expected 1."
        )
    if "servers" not in data:
        raise click.ClickException("Catalog missing required `servers` block.")
    return data


def _instance_id(worktree_path: str) -> str:
    """Short stable hash of the worktree absolute path (4 hex chars)."""
    return hashlib.sha1(str(Path(worktree_path).resolve()).encode("utf-8")).hexdigest()[:4]


def _port_for(worktree_path: str, base_port: int) -> int:
    """Deterministic port within `[base, base+99]` keyed by worktree path.

    The 100-slot ceiling means inter-worktree port collisions become probable
    by birthday-paradox math past ~12 active worktrees and likely past ~50.
    `_allocate_ports` only catches *intra*-worktree collisions; cross-worktree
    collisions surface at runtime (port already in use). Widen the modulus
    here and bump `default_port_base` spacing in mcp_catalog.yaml if you need
    more headroom.
    """
    offset = int(_instance_id(worktree_path), 16) % 100
    return base_port + offset


def _port_is_free(port: int, host: str = "127.0.0.1") -> bool:
    """True if nothing is currently bound on (host, port).

    Note: `doctor` inverts this (`not _port_is_free(port)`) because a *listening*
    port means the worktree's MCP server is actually running — the opposite of
    what `init`/`list` want, which is to confirm a port is *available* before
    claiming it.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.5)
    try:
        return sock.connect_ex((host, port)) != 0
    finally:
        sock.close()


def _render_local_entry(name: str, spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Render a per-worktree catalog entry as a Claude Code .mcp.json mcpServers value.
    Uses ${VAR} placeholders so Claude Code expands them at session start.
    """
    transport = spec.get("transport", "http")
    entry: Dict[str, Any] = {"type": transport}

    if transport in {"http", "sse"}:
        url = spec.get("url_template") or spec.get("url")
        if not url:
            raise click.ClickException(f"Server `{name}` missing `url`/`url_template`.")
        entry["url"] = url
    elif transport == "stdio":
        entry["command"] = spec.get("command_template") or spec.get("command")
        if not entry["command"]:
            raise click.ClickException(f"Server `{name}` missing `command`/`command_template`.")
        args = spec.get("args_template") or spec.get("args") or []
        entry["args"] = list(args)
    else:
        raise click.ClickException(f"Unsupported transport `{transport}` for `{name}`.")

    env_template = spec.get("env_template") or {}
    env_keys = list(spec.get("requires_env", []) or []) + list(spec.get("optional_env", []) or [])
    env: Dict[str, str] = {k: f"${{{k}:-}}" for k in env_keys}
    env.update(env_template)   # explicit templates win over default `${VAR:-}` shape
    if env:
        entry["env"] = env

    if spec.get("description"):
        entry["description"] = spec["description"]

    return entry


def _render_global_entry(name: str, spec: Dict[str, Any]) -> Dict[str, Any]:
    """Render a singleton catalog entry as a ~/.claude.json mcpServers value."""
    transport = spec.get("transport", "http")
    entry: Dict[str, Any] = {"type": transport}

    if transport in {"http", "sse"}:
        if not spec.get("url"):
            raise click.ClickException(f"Singleton `{name}` requires `url`.")
        entry["url"] = spec["url"]
    elif transport == "stdio":
        if not spec.get("command"):
            raise click.ClickException(f"Singleton `{name}` requires `command`.")
        entry["command"] = spec["command"]
        if spec.get("args"):
            entry["args"] = list(spec["args"])
    else:
        raise click.ClickException(f"Unsupported transport `{transport}` for `{name}`.")

    env_keys = list(spec.get("requires_env", []) or []) + list(spec.get("optional_env", []) or [])
    if env_keys:
        entry["env"] = {k: f"${{{k}:-}}" for k in env_keys}

    if spec.get("description"):
        entry["description"] = spec["description"]
    return entry


def _is_startable_global_entry(spec: Dict[str, Any]) -> bool:
    return spec.get("lifecycle") != "decision-required"


def _build_global_mcp_servers(catalog: Dict[str, Any]) -> Dict[str, Any]:
    """Construct startable singleton MCP entries for global client config."""

    return {
        name: _render_global_entry(name, spec)
        for name, spec in catalog["servers"].items()
        if spec.get("scope") == "singleton" and _is_startable_global_entry(spec)
    }


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r") as fh:
        return json.load(fh)


def _atomic_write_json(path: Path, data: Dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")
    tmp.replace(path)


def _claude_global_path() -> Path:
    return Path.home() / ".claude.json"


def _backup_path(path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    return path.with_suffix(path.suffix + f".backup-{stamp}")


def _singleton_reserved_ports(catalog: Dict[str, Any]) -> Dict[int, str]:
    """
    Return a map of {port: server_name} for all singleton servers that have a
    statically-declared port in the catalog.  These ports must never be assigned
    to per-worktree services regardless of what hash offset `_port_for` produces.

    Two sources of port reservation are recognised:

    1. ``url`` field — parsed via urllib (e.g. ``http://localhost:3009/mcp``).
    2. ``reserved_port`` field — an explicit integer for singletons whose MCP
       transport is ``stdio`` (e.g. ``gpt-researcher``) but whose Docker service
       still binds a host port that per-worktree services must not shadow.
    """
    from urllib.parse import urlparse as _urlparse

    reserved: Dict[int, str] = {}
    for name, spec in catalog.get("servers", {}).items():
        if spec.get("scope") != "singleton":
            continue

        # Source 1: explicit reserved_port (stdio singletons that still bind a host port)
        explicit = spec.get("reserved_port")
        if explicit is not None:
            try:
                reserved[int(explicit)] = name
            except (TypeError, ValueError):
                console.logger.warning(
                    f"[warning]mcp_catalog: singleton '{name}' has a non-integer "
                    f"reserved_port value ({explicit!r}); skipping port reservation.[/warning]"
                )

        # Source 2: url field (HTTP/SSE singletons)
        raw_url = spec.get("url")
        if raw_url:
            try:
                port = _urlparse(str(raw_url)).port
                if port:
                    reserved[port] = name
            except Exception as exc:  # noqa: BLE001
                console.logger.warning(
                    f"[warning]mcp_catalog: singleton '{name}' has an unparseable "
                    f"url ({raw_url!r}); skipping port reservation. ({exc})[/warning]"
                )
    return reserved


def _allocate_ports(
    worktree: str,
    names: List[str],
    catalog: Dict[str, Any],
    *,
    project_root: str | None = None,
) -> Dict[str, int]:
    """
    Compute ports for each per-worktree server, including any `extra_port_vars`
    declared by the spec (e.g. conport exposes three host ports for one service).
    Same hash offset is reused across a single server's primary + extras.

    Safety rules:
    - ``wrapper-singleton`` services (one global instance, fixed port) are
      assigned their ``default_port_base`` directly without any hash offset.
    - All singleton-catalog reserved ports are pre-seeded into the collision
      map so per-worktree hash offsets cannot land on them.
    """
    assignments: Dict[str, int] = {}
    # Pre-seed with singleton reserved ports so per-worktree allocations
    # cannot collide with statically-assigned singleton ports (e.g. gptr-mcp).
    seen_ports: Dict[int, str] = {
        port: f"singleton:{name}"
        for port, name in _singleton_reserved_ports(catalog).items()
    }

    def _claim(
        var: str, base: int, owner: str, key_path: str, *, fixed: bool = False
    ) -> None:
        port = base if fixed else _port_for(key_path, base)
        if port in seen_ports:
            raise click.ClickException(
                f"Internal port collision: {owner}.{var} and "
                f"{seen_ports[port]} both map to :{port}. "
                f"Adjust the `default_port_base` for one of them in {CATALOG_FILENAME}."
            )
        seen_ports[port] = f"{owner}.{var}"
        assignments[var] = port

    for name in names:
        spec = catalog["servers"].get(name)
        if not spec or spec.get("scope") != "per-worktree":
            continue
        # wrapper-singleton: one global instance at a fixed port — no hash offset.
        is_wrapper_singleton = spec.get("management_model") == "wrapper-singleton"
        key_path = (
            project_root
            if spec.get("state_scope") == "per-repo" and project_root
            else worktree
        )
        base = spec.get("default_port_base")
        if base:
            _claim(spec["port_var"], base, name, key_path, fixed=is_wrapper_singleton)
        if not is_wrapper_singleton:
            for extra in spec.get("extra_port_vars", []) or []:
                _claim(extra["var"], extra["base"], name, key_path)
    return assignments


def _project_env_exports(worktree: str, project_root: str) -> Dict[str, str]:
    return {
        "DOPEMUX_WORKSPACE_ID": worktree,
        "DOPEMUX_WORKSPACE_ROOT": worktree,
        "DOPEMUX_PROJECT_ROOT": project_root,
        "TASK_ORCHESTRATOR_PROJECT_ROOT": project_root,
        "DOPEMUX_INSTANCE_ID": _instance_id(worktree),
        "DOPE_MEMORY_WORKSPACE_ID": Path(worktree).name,
        "DOPE_MEMORY_INSTANCE_ID": _instance_id(worktree),
        "WORKSPACE_ID": worktree,
    }


def _write_envrc(
    envrc_path: Path,
    port_vars: Dict[str, int],
    worktree: str,
    project_root: str,
) -> None:
    """Write the per-worktree env file (sourced by direnv `.envrc` or `.env.mcp` consumers)."""
    env_exports = _project_env_exports(worktree, project_root)
    lines = [
        "# Generated by `dopemux mcp init`. Do not edit by hand — re-run init to regenerate.",
        f"# Worktree: {worktree}",
        f"# Project:  {project_root}",
        f"# Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
    ]
    for var, value in env_exports.items():
        lines.append(f"export {var}={shlex_quote(str(value))}")
    lines.append("")
    for var, port in sorted(port_vars.items()):
        lines.append(f"export {var}={port}")
    envrc_path.write_text("\n".join(lines) + "\n")


def _append_missing_env_exports(envrc_path: Path, exports: Dict[str, Any]) -> List[str]:
    """Append missing port exports to an existing env file without rewriting user content."""
    existing = envrc_path.read_text() if envrc_path.exists() else ""
    missing = [
        (var, value)
        for var, value in sorted(exports.items())
        if f"export {var}=" not in existing
    ]
    if not missing:
        return []

    prefix = "" if not existing or existing.endswith("\n") else "\n"
    with envrc_path.open("a") as fh:
        fh.write(prefix)
        for var, value in missing:
            fh.write(f"export {var}={shlex_quote(str(value))}\n")
    return [var for var, _ in missing]


def shlex_quote(value: str) -> str:
    """Local shlex.quote shim (avoid importing shlex into top-of-module namespace)."""
    import shlex
    return shlex.quote(value)


def _build_local_mcp_json(server_names: List[str], catalog: Dict[str, Any]) -> Dict[str, Any]:
    """Construct the .mcp.json contents for the given per-worktree server names."""
    servers: Dict[str, Any] = {}
    for name in server_names:
        spec = catalog["servers"].get(name)
        if not spec:
            raise click.ClickException(f"Unknown server `{name}` (not in {CATALOG_FILENAME}).")
        if spec.get("scope") != "per-worktree":
            raise click.ClickException(
                f"`{name}` is a singleton — declare it once in `~/.claude.json` via "
                f"`dopemux mcp sync-globals`, not per-worktree."
            )
        servers[name] = _render_local_entry(name, spec)
    return {"mcpServers": servers}


# ---------------------------------------------------------------------------
# `mcp generate` / `ensure` / `init` / `add` / `remove` / `list` / `doctor` / `sync-globals`
# ---------------------------------------------------------------------------


@mcp.command("generate")
@click.option("--apply", is_flag=True, help="Write generated outputs. Default is dry-run.")
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path, file_okay=False, dir_okay=True),
    help="Directory for generated output files when --apply is set.",
)
def mcp_generate_cmd(apply: bool, output_dir: Optional[Path]):
    """
    🧾 Project Fleet: Render catalog-backed MCP config fragments

    Generates reviewable projections for local .mcp.json, Claude globals,
    Codex config, health probes, and MCP doctrine docs. Dry-run is the default;
    writes require both --apply and --output-dir.
    """
    from dopemux.mcp import fleet_catalog

    catalog = _load_catalog()
    outputs = fleet_catalog.generate_fleet_output_files(catalog)

    if not apply:
        console.logger.info("[info]Dry-run only. No files were written.[/info]")
        for relative_path, content in outputs.items():
            line_count = len(content.splitlines())
            console.logger.info(f"[info]Would write {relative_path} ({line_count} lines)[/info]")
        return

    if output_dir is None:
        raise click.ClickException("--apply requires --output-dir to bound generated writes.")

    for relative_path, content in outputs.items():
        target = output_dir / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        console.logger.info(f"[success]Wrote {target}[/success]")


def _ensure_context() -> tuple[Path, Any]:
    repo = get_repo_root(fallback_cwd=False)
    if not repo:
        raise click.ClickException("Not inside a git repository.")
    repo_path = Path(repo)
    identity_env = dict(os.environ)
    identity_env["DOPEMUX_WORKSPACE_ROOT"] = repo
    try:
        identity = resolve_project_identity(cwd=repo_path, env=identity_env)
    except ProjectIdentityError as exc:
        raise click.ClickException(f"Could not resolve project identity: {exc}") from exc
    return repo_path, identity


def _ensure_fast_context() -> tuple[Path, Path]:
    env_repo = os.environ.get("DOPEMUX_WORKSPACE_ROOT") or os.environ.get("DOPEMUX_PROJECT_ROOT")
    if env_repo:
        repo_path = Path(env_repo).expanduser().resolve()
        if not repo_path.is_dir():
            raise click.ClickException(f"MCP workspace root does not point to a directory: {repo_path}")
    else:
        start = Path.cwd().resolve()
        repo_path = next(
            (
                candidate
                for candidate in (start, *start.parents)
                if (candidate / PROJECT_MCP_FILENAME).exists() or (candidate / ".git").exists()
            ),
            None,
        )
        if repo_path is None:
            raise click.ClickException(
                "Could not determine MCP workspace root without subprocess; "
                "set DOPEMUX_WORKSPACE_ROOT or run from the repository root."
            )

    project_override = os.environ.get("TASK_ORCHESTRATOR_PROJECT_ROOT") or os.environ.get("DOPEMUX_PROJECT_ROOT")
    if project_override:
        project_root = Path(project_override).expanduser().resolve()
        if not project_root.is_dir():
            raise click.ClickException(f"MCP project root does not point to a directory: {project_root}")
    else:
        project_root = repo_path
    return repo_path, project_root


def _ensure_fast_problems(catalog: Dict[str, Any], repo_path: Path, project_root: Path) -> List[str]:
    problems: List[str] = []
    mcp_json_path = repo_path / PROJECT_MCP_FILENAME
    envrc_path = repo_path / ENVRC_FILENAME

    if not mcp_json_path.exists():
        problems.append(
            f"Missing {PROJECT_MCP_FILENAME} at {mcp_json_path} — run `dopemux mcp init`."
        )
    else:
        defaults = catalog.get("defaults", {}).get("per_worktree", []) or []
        try:
            expected = _build_local_mcp_json(list(defaults), catalog)
            actual = _read_json(mcp_json_path)
        except (json.JSONDecodeError, click.ClickException) as exc:
            problems.append(f"{mcp_json_path} is not a valid catalog-backed MCP config: {exc}")
        else:
            if actual != expected:
                problems.append(f"{mcp_json_path} does not match catalog defaults.")

    if not envrc_path.exists():
        problems.append(f"Missing {ENVRC_FILENAME} at {envrc_path} — run `dopemux mcp init`.")

    local_env = {
        **os.environ,
        **_project_env_exports(str(repo_path), str(project_root)),
    }
    for name in catalog.get("defaults", {}).get("per_worktree", []) or []:
        spec = catalog.get("servers", {}).get(name) or {}
        for env_key in spec.get("requires_env", []) or []:
            if not local_env.get(env_key):
                problems.append(f"`{name}`: required env `{env_key}` is unavailable.")
    return problems


DEFAULT_ENSURE_TIMEOUT_SECONDS = 120
DEFAULT_COMPOSE_WAIT_TIMEOUT_SECONDS = 90
# `docker compose up` also BUILDS any missing local images before the health
# wait begins, and a cold multi-image build easily exceeds the health-wait
# budget. Give the compose step its own generous (but still bounded) subprocess
# budget so a first-run build isn't killed, while --wait-timeout still bounds
# the post-build health wait.
DEFAULT_COMPOSE_UP_TIMEOUT_SECONDS = 900


def _catalog_compose_services(catalog: Dict[str, Any]) -> List[str]:
    """Compose services that `ensure --full` may auto-start.

    Includes ``lifecycle: active`` and ``lifecycle: operator-managed`` servers —
    both are consumed by clients (e.g. ``pal-stdio`` is the ``mcp-pal-stdio``
    container that Claude/Codex configs exec into), so ensure must bring them up
    or it would report green while a configured server is down. Only
    ``decision-required`` servers (e.g. desktop-commander) — quarantined
    out of generated startable config pending an operator decision — are
    excluded, along with any server missing a lifecycle field.
    """
    services = {
        str(spec["docker_compose_service"])
        for spec in catalog.get("servers", {}).values()
        if spec.get("docker_compose_service")
        and spec.get("lifecycle") in ("active", "operator-managed")
    }
    return sorted(services)


def _run_checked(
    cmd: List[str],
    *,
    cwd: Path,
    label: str,
    timeout: int = DEFAULT_ENSURE_TIMEOUT_SECONDS,
) -> None:
    console.logger.info(f"[info]{label}: {' '.join(cmd)}[/info]")
    try:
        subprocess.run(cmd, cwd=cwd, check=True, timeout=timeout)
    except FileNotFoundError as exc:
        raise click.ClickException(f"{label}: command not found: {cmd[0]}") from exc
    except CalledProcessError as exc:
        raise click.ClickException(f"{label} failed with exit code {exc.returncode}.") from exc
    except subprocess.TimeoutExpired as exc:
        raise click.ClickException(
            f"{label} timed out after {exc.timeout}s (command: {' '.join(cmd)})."
        ) from exc


_ENV_TEMPLATE_RE = re.compile(r"\$\{([A-Z][A-Z0-9_]*)(?::-([^}]*))?\}")


def _resolve_env_template(value: str, env: Dict[str, str]) -> str:
    def repl(match: re.Match[str]) -> str:
        name = match.group(1)
        default = match.group(2) or ""
        return env.get(name) or default

    return _ENV_TEMPLATE_RE.sub(repl, value)


def _probeable_http_servers(catalog: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    env = dict(os.environ)
    servers: Dict[str, Dict[str, Any]] = {}
    for name, spec in sorted(catalog.get("servers", {}).items()):
        if spec.get("transport") != "http":
            continue
        raw_url = spec.get("url") or spec.get("url_template")
        if not raw_url:
            continue
        url = _resolve_env_template(str(raw_url), env)
        parsed = urlparse(url)
        if parsed.hostname not in {"localhost", "127.0.0.1"}:
            continue
        servers[name] = {"url": url}
    return servers


def _run_mcp_tools_list_probes(catalog: Dict[str, Any]) -> List[str]:
    servers = _probeable_http_servers(catalog)
    if not servers:
        return []
    try:
        from dopemux.mcp.discovery import ToolDiscoveryClient
    except ModuleNotFoundError as exc:
        return [f"MCP probe client unavailable: missing dependency `{exc.name}`."]

    report = asyncio.run(ToolDiscoveryClient(timeout=2.0).discover(servers))
    return [
        f"`{server['name']}`: MCP tools-list probe failed ({server.get('status', 'unknown')})."
        for server in report.get("servers", [])
        if not server.get("reachable")
    ]


def _report_ensure_problems(problems: List[str]) -> None:
    console.logger.info(f"[warning]{len(problems)} ensure issue(s) found:[/warning]")
    for problem in problems:
        console.logger.info(f"  • {problem}")
    sys.exit(1)


@mcp.command("ensure")
@click.option(
    "--fast",
    is_flag=True,
    help="Static prerequisite checks only (config/env presence) — no daemon probes, no health checks.",
)
@click.option("--full", "full_mode", is_flag=True, help="Run local checks plus bounded service remediation/probes.")
def mcp_ensure_cmd(fast: bool, full_mode: bool):
    """
    🛠️ Stabilize Fleet: Check or remediate catalog-backed MCP prerequisites

    `--fast` performs static prerequisite checks only: it verifies `.mcp.json`
    matches catalog defaults, `.envrc.dopemux-mcp` exists, and required env
    vars are present. It does not probe any daemon, container, or HTTP
    endpoint, live or cached. `--full` additionally starts catalog compose
    services (lifecycle: active only), ensures PAL and the Task Orchestrator
    singleton, then runs bounded local HTTP MCP tools-list probes.
    """
    if fast and full_mode:
        raise click.ClickException("Choose exactly one of --fast or --full.")
    if not fast and not full_mode:
        fast = True

    catalog = _load_catalog()
    if fast:
        repo_path, project_root = _ensure_fast_context()
    else:
        repo_path, identity = _ensure_context()
        project_root = identity.project_root
    problems = _ensure_fast_problems(catalog, repo_path, project_root)
    if problems:
        _report_ensure_problems(problems)

    if fast:
        console.logger.info("[success]Fast MCP ensure checks green.[/success]")
        return

    if shutil.which("docker") is None:
        raise click.ClickException("docker is required for `dopemux mcp ensure --full`.")
    if not (repo_path / "compose.yml").exists():
        raise click.ClickException(f"Missing {repo_path / 'compose.yml'} for compose remediation.")

    compose_services = _catalog_compose_services(catalog)
    if compose_services:
        # --wait blocks until dependent services report healthy (bounded by
        # --wait-timeout). The Python-side timeout= is a backstop against a
        # hung CLI and must cover BOTH a cold first-run image build AND the
        # health wait, so it uses the generous compose-up budget rather than
        # the short health-wait one.
        _run_checked(
            [
                "docker", "compose", "-f", "compose.yml", "up", "-d",
                "--wait", "--wait-timeout", str(DEFAULT_COMPOSE_WAIT_TIMEOUT_SECONDS),
                *compose_services,
            ],
            cwd=repo_path,
            label="compose",
            timeout=DEFAULT_COMPOSE_UP_TIMEOUT_SECONDS,
        )

    # ensure-pal.sh owns the off-compose Codex pal-mcp-server container only;
    # the compose step above already (re)started the compose `pal` service
    # that Claude Code talks to, so there is no overlap between the two.
    _run_checked(["bash", "scripts/mcp-wrappers/ensure-pal.sh"], cwd=repo_path, label="pal")
    _run_checked(
        ["bash", "scripts/mcp-wrappers/task-orchestrator-http-singleton.sh"],
        cwd=repo_path,
        label="task-orchestrator",
    )

    probe_problems = _run_mcp_tools_list_probes(catalog)
    if probe_problems:
        _report_ensure_problems(probe_problems)
    console.logger.info("[success]Full MCP ensure checks green.[/success]")


@mcp.command("init")
@click.option("--force", is_flag=True, help="Overwrite existing .mcp.json and env file without prompting.")
@click.option("--with", "extra", multiple=True, help="Additional server name beyond catalog defaults (repeatable).")
def mcp_init_cmd(force: bool, extra: Tuple[str, ...]):
    """
    🌱 Bootstrap Worktree: Scaffold .mcp.json + per-worktree env file

    Generates the per-worktree MCP config from the catalog defaults plus any
    `--with NAME` extras. Allocates ports deterministically from the worktree
    path so two worktrees never collide on the same host port.
    """
    repo = get_repo_root(fallback_cwd=False)
    if not repo:
        raise click.ClickException("Not inside a git repository.")
    repo_path = Path(repo)
    identity_env = dict(os.environ)
    identity_env["DOPEMUX_WORKSPACE_ROOT"] = repo
    try:
        identity = resolve_project_identity(cwd=repo_path, env=identity_env)
    except ProjectIdentityError as exc:
        raise click.ClickException(f"Could not resolve project identity: {exc}") from exc

    catalog = _load_catalog()

    server_names = list(catalog.get("defaults", {}).get("per_worktree", [])) + list(extra)
    # de-dup while preserving order
    seen, ordered = set(), []
    for n in server_names:
        if n not in seen:
            seen.add(n)
            ordered.append(n)

    mcp_json_path = repo_path / PROJECT_MCP_FILENAME
    envrc_path = repo_path / ENVRC_FILENAME

    port_vars = _allocate_ports(repo, ordered, catalog, project_root=str(identity.project_root))
    config = _build_local_mcp_json(ordered, catalog)

    if envrc_path.exists() and not force:
        raise click.ClickException(
            f"{envrc_path.name} already exists. Use --force to overwrite."
        )

    wrote_mcp_json = True
    if mcp_json_path.exists() and not force:
        existing_config = _read_json(mcp_json_path)
        if existing_config != config:
            raise click.ClickException(
                f"{mcp_json_path.name} already exists and does not match the catalog template. "
                "Use --force to overwrite."
            )
        wrote_mcp_json = False
    else:
        _atomic_write_json(mcp_json_path, config)

    _write_envrc(envrc_path, port_vars, repo, str(identity.project_root))

    if wrote_mcp_json:
        console.logger.info(f"[success]Wrote {mcp_json_path}[/success]")
    else:
        console.logger.info(f"[info]Kept existing catalog-matching {mcp_json_path}[/info]")
    console.logger.info(f"[success]Wrote {envrc_path}[/success]")
    console.logger.info(f"[info]Worktree:   {repo}[/info]")
    console.logger.info(f"[info]Project:    {identity.project_root}[/info]")
    console.logger.info(f"[info]Instance:   {_instance_id(repo)}[/info]")
    if port_vars:
        for var, port in sorted(port_vars.items()):
            free = "[success]free[/success]" if _port_is_free(port) else "[warning]in use[/warning]"
            console.logger.info(f"[info]  {var}={port} ({free})[/info]")
    console.logger.info("")
    console.logger.info("[info]Next:[/info]")
    console.logger.info("[info]  1. Add `source ./.envrc.dopemux-mcp` to your .envrc, or `direnv allow`.[/info]")
    console.logger.info("[info]  2. Start containers: `dopemux mcp up` (or compose with the new ports).[/info]")
    console.logger.info("[info]  3. Verify: `dopemux mcp doctor`.[/info]")


@mcp.command("add")
@click.argument("name")
def mcp_add_cmd(name: str):
    """
    ➕ Append Server: Add a per-worktree MCP from the catalog to .mcp.json

    The server must be present in `mcp_catalog.yaml` with `scope: per-worktree`.
    Singletons are added via `dopemux mcp sync-globals` instead.
    """
    repo = get_repo_root(fallback_cwd=False)
    if not repo:
        raise click.ClickException("Not inside a git repository.")
    identity_env = dict(os.environ)
    identity_env["DOPEMUX_WORKSPACE_ROOT"] = repo
    try:
        identity = resolve_project_identity(cwd=repo, env=identity_env)
    except ProjectIdentityError as exc:
        raise click.ClickException(f"Could not resolve project identity: {exc}") from exc

    catalog = _load_catalog()
    if name not in catalog["servers"]:
        raise click.ClickException(f"Unknown server `{name}`. See `dopemux mcp list`.")
    if catalog["servers"][name].get("scope") != "per-worktree":
        raise click.ClickException(
            f"`{name}` is a singleton. Add via `dopemux mcp sync-globals`, not `mcp add`."
        )

    mcp_json_path = Path(repo) / PROJECT_MCP_FILENAME
    if not mcp_json_path.exists():
        raise click.ClickException(
            f"{PROJECT_MCP_FILENAME} not found. Run `dopemux mcp init` first."
        )

    data = _read_json(mcp_json_path)
    servers = data.setdefault("mcpServers", {})
    if name in servers:
        console.logger.info(f"[warning]`{name}` already in {PROJECT_MCP_FILENAME}; nothing to do.[/warning]")
        return

    servers[name] = _render_local_entry(name, catalog["servers"][name])
    _atomic_write_json(mcp_json_path, data)

    envrc_path = Path(repo) / ENVRC_FILENAME
    env_exports: Dict[str, Any] = {
        **_project_env_exports(repo, str(identity.project_root)),
        **_allocate_ports(repo, [name], catalog, project_root=str(identity.project_root)),
    }
    appended = _append_missing_env_exports(envrc_path, env_exports)
    for var in appended:
        console.logger.info(f"[info]Appended {var}={env_exports[var]} to {envrc_path.name}.[/info]")

    console.logger.info(f"[success]Added `{name}` to {mcp_json_path}.[/success]")


@mcp.command("remove")
@click.argument("name")
def mcp_remove_cmd(name: str):
    """
    ➖ Drop Server: Remove a per-worktree MCP from .mcp.json
    """
    repo = get_repo_root(fallback_cwd=False)
    if not repo:
        raise click.ClickException("Not inside a git repository.")
    mcp_json_path = Path(repo) / PROJECT_MCP_FILENAME
    if not mcp_json_path.exists():
        raise click.ClickException(f"{PROJECT_MCP_FILENAME} not found.")

    data = _read_json(mcp_json_path)
    servers = data.get("mcpServers", {})
    if name not in servers:
        console.logger.info(f"[warning]`{name}` not in {PROJECT_MCP_FILENAME}; nothing to remove.[/warning]")
        return

    del servers[name]
    _atomic_write_json(mcp_json_path, data)
    console.logger.info(f"[success]Removed `{name}` from {mcp_json_path}.[/success]")
    console.logger.info(
        "[info]The corresponding env-var entry in .envrc.dopemux-mcp is left intact "
        "(re-run `dopemux mcp init --force` to regenerate cleanly).[/info]"
    )


@mcp.command("list")
def mcp_list_cmd():
    """
    📋 Survey Fleet: Show globals, locals, catalog availability

    Lists what the catalog knows, what `~/.claude.json` declares globally,
    and what the current worktree's `.mcp.json` declares locally. Flags
    duplicates or drift between catalog and declared configs.
    """
    catalog = _load_catalog()
    repo = get_repo_root(fallback_cwd=False)
    global_path = _claude_global_path()
    global_data = _read_json(global_path)
    global_servers = (global_data.get("mcpServers") or {})

    local_data: Dict[str, Any] = {}
    if repo:
        local_path = Path(repo) / PROJECT_MCP_FILENAME
        local_data = _read_json(local_path)
    local_servers = (local_data.get("mcpServers") or {})

    console.logger.info("[info]== Catalog ==[/info]")
    for name, spec in catalog["servers"].items():
        scope = spec.get("scope", "?")
        transport = spec.get("transport", "?")
        console.logger.info(f"  {name}  ({scope}, {transport})  — {spec.get('description', '')}")

    console.logger.info("")
    console.logger.info(f"[info]== Global (~/.claude.json mcpServers) ==[/info]")
    for name in sorted(global_servers):
        marker = "" if name in catalog["servers"] else "  [warning](not in catalog)[/warning]"
        console.logger.info(f"  {name}{marker}")

    console.logger.info("")
    if repo:
        console.logger.info(f"[info]== Local ({repo}/{PROJECT_MCP_FILENAME}) ==[/info]")
        if not local_servers:
            console.logger.info("  (none — run `dopemux mcp init`)")
        for name in sorted(local_servers):
            marker = ""
            if name in global_servers:
                marker = "  [warning](DUPLICATE — also in global)[/warning]"
            elif name not in catalog["servers"]:
                marker = "  [warning](not in catalog)[/warning]"
            console.logger.info(f"  {name}{marker}")


def _run_stdio_doctor(name: str, spec: Dict[str, Any], env: Dict[str, str], cwd: Path) -> List[str]:
    """Run a stdio server's configured non-mutating doctor command."""
    doctor_args = list(spec.get("doctor_args") or [])
    if not doctor_args:
        return []

    command = spec.get("command_template") or spec.get("command")
    if not command:
        return [f"`{name}`: stdio server missing command for doctor check."]

    try:
        result = subprocess.run(
            [command, *doctor_args],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
            env=env,
            cwd=cwd,
        )
    except FileNotFoundError:
        return [f"`{name}`: doctor command not found: {command}"]
    except subprocess.TimeoutExpired:
        return [f"`{name}`: doctor command timed out."]

    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        suffix = f" {detail}" if detail else ""
        return [f"`{name}`: doctor command failed.{suffix}"]

    if result.stdout.strip():
        for line in result.stdout.strip().splitlines():
            console.logger.info(f"[info]`{name}`: {line}[/info]")
    return []


@mcp.command("doctor")
@click.option(
    "--repo",
    "repo_arg",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=None,
    help="Target repo/worktree to diagnose (defaults to current git root). Works from any cwd.",
)
@click.option(
    "--json",
    "json_output",
    is_flag=True,
    help="Emit the full doctor JSON report (schema_version 1.0) to stdout.",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Include more findings in the human summary.",
)
@click.option(
    "--skip-docker",
    is_flag=True,
    help="Skip Docker inspection (still reports DOCKER_UNAVAILABLE).",
)
@click.option(
    "--legacy",
    is_flag=True,
    help="Use the pre-Packet-001 problem-list doctor (cwd git root only).",
)
def mcp_doctor_cmd(
    repo_arg: Optional[Path],
    json_output: bool,
    verbose: bool,
    skip_docker: bool,
    legacy: bool,
):
    """
    🩺 Health Sweep: Repo-aware MCP truth gate (read-only)

    Loads the target repo's `.envrc.dopemux-mcp`, validates catalog transports,
    detects port collision risks, compose lifecycle drift, and Docker ownership
    where labels exist. Does not start or stop containers.

    Examples:
      dopemux mcp doctor
      dopemux mcp doctor --repo ~/code/other-project
      dopemux mcp doctor --repo ~/code/other-project --json
    """
    if legacy:
        if repo_arg is not None:
            raise click.ClickException(
                "--legacy does not support --repo; omit --legacy for repo-aware doctor."
            )
        _mcp_doctor_legacy()
        return

    catalog = _load_catalog()
    catalog_path = _catalog_path()
    catalog_paths = [str(catalog_path)] if catalog_path else ["bundled:default_catalog.yaml"]

    if repo_arg is not None:
        repo = str(repo_arg.resolve())
    else:
        repo = get_repo_root(fallback_cwd=False)
        if not repo:
            raise click.ClickException(
                "Not inside a git repository. Pass --repo <path> to diagnose another project."
            )

    from dopemux.mcp.doctor import format_human_summary, run_mcp_doctor

    # Prefer compose hazards from dopemux product compose when target has none.
    compose_candidate = Path(repo) / "compose.yml"
    if not compose_candidate.is_file():
        # Read-only: may use current cwd compose for hazard text only
        cwd_compose = Path.cwd() / "compose.yml"
        compose_candidate = cwd_compose if cwd_compose.is_file() else None

    report = run_mcp_doctor(
        repo,
        catalog=catalog,
        catalog_paths_checked=catalog_paths,
        compose_path=compose_candidate,
        skip_docker=skip_docker,
        process_env=dict(os.environ),
    )

    if json_output:
        # Deterministic JSON to stdout (not through rich logger)
        sys.stdout.write(report.to_json())
    else:
        summary = format_human_summary(report, verbose=verbose)
        # Color the status line lightly via console, keep body plain for copy/paste
        status = report.status
        if status == "PASS":
            console.logger.info(f"[success]{summary.rstrip()}[/success]")
        elif status == "PASS_WITH_WARNINGS":
            console.logger.info(f"[warning]{summary.rstrip()}[/warning]")
        elif status == "FAIL":
            console.logger.info(f"[error]{summary.rstrip()}[/error]")
        else:
            console.logger.info(f"[info]{summary.rstrip()}[/info]")

    if report.exit_code:
        sys.exit(report.exit_code)


def _mcp_doctor_legacy() -> None:
    """Pre-Packet-001 doctor: problem list for cwd git root (compat)."""
    catalog = _load_catalog()
    repo = get_repo_root(fallback_cwd=False)
    if not repo:
        raise click.ClickException("Not inside a git repository.")

    envrc_path = Path(repo) / ENVRC_FILENAME
    mcp_json_path = Path(repo) / PROJECT_MCP_FILENAME
    problems: List[str] = []
    try:
        identity_env = dict(os.environ)
        identity_env["DOPEMUX_WORKSPACE_ROOT"] = repo
        identity = resolve_project_identity(cwd=repo, env=identity_env)
    except ProjectIdentityError as exc:
        raise click.ClickException(f"Could not resolve project identity: {exc}") from exc

    # Load envrc when present so legacy path no longer false-fails on unset ports.
    doctor_env = dict(os.environ)
    doctor_env.update(_project_env_exports(repo, str(identity.project_root)))
    if envrc_path.is_file():
        from dopemux.mcp.envrc import load_envrc, merge_envrc_into_environ

        parsed = load_envrc(envrc_path)
        doctor_env = merge_envrc_into_environ(doctor_env, parsed, override=True)

    if not mcp_json_path.exists():
        problems.append(f"Missing {mcp_json_path} — run `dopemux mcp init`.")
    if not envrc_path.exists():
        problems.append(f"Missing {envrc_path} — run `dopemux mcp init`.")

    local_data = _read_json(mcp_json_path) if mcp_json_path.exists() else {}
    declared = list((local_data.get("mcpServers") or {}).keys())

    for name in declared:
        spec = catalog["servers"].get(name)
        if not spec:
            problems.append(f"Server `{name}` declared locally but not in catalog.")
            continue
        is_stdio = spec.get("transport") == "stdio"
        env_source = doctor_env if is_stdio else doctor_env
        for env_key in spec.get("requires_env", []) or []:
            if not env_source.get(env_key):
                problems.append(f"`{name}`: required env `{env_key}` is unset.")
        if is_stdio:
            problems.extend(_run_stdio_doctor(name, spec, doctor_env, Path(repo)))
            continue
        if spec.get("port_var"):
            port_str = doctor_env.get(spec["port_var"])
            if not port_str:
                problems.append(f"`{name}`: env `{spec['port_var']}` is unset (source the .envrc?).")
                continue
            port = int(port_str)
            reachable = not _port_is_free(port)   # something listening => good
            if not reachable:
                problems.append(f"`{name}`: nothing listening on :{port} (start the container?).")

    if not problems:
        console.logger.info("[success]All checks green.[/success]")
        return
    console.logger.info(f"[warning]{len(problems)} issue(s) found:[/warning]")
    for p in problems:
        console.logger.info(f"  • {p}")
    sys.exit(1)


def _functional_subset(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Strip advisory fields (description) for diff purposes — they're documentation, not config."""
    return {k: v for k, v in entry.items() if k != "description"}


@mcp.command("sync-globals")
@click.option("--apply", is_flag=True, help="Actually write ~/.claude.json (default: dry-run with diff).")
@click.option("--prune", is_flag=True, help="Remove singletons that exist in ~/.claude.json but not the catalog (default: keep them).")
def mcp_sync_globals_cmd(apply: bool, prune: bool):
    """
    🌐 Promote Singletons: Reconcile ~/.claude.json mcpServers with the catalog

    Defaults to dry-run: prints the functional diff between `~/.claude.json`
    `mcpServers` and the catalog's singletons. User-set descriptions are
    preserved on apply; only functional fields (type, url, command, args, env)
    are changed. Pass --apply to write (after a timestamped backup).
    Pass --prune to remove existing globals that aren't in the catalog.
    """
    catalog = _load_catalog()
    desired = _build_global_mcp_servers(catalog)

    global_path = _claude_global_path()
    global_data = _read_json(global_path) if global_path.exists() else {}
    current = global_data.get("mcpServers", {}) or {}

    additions = sorted(set(desired) - set(current))
    removals = sorted(set(current) - set(desired))
    changed = sorted(
        n for n in (set(desired) & set(current))
        if _functional_subset(current[n]) != _functional_subset(desired[n])
    )

    if not (additions or (prune and removals) or changed):
        console.logger.info("[success]~/.claude.json mcpServers already matches the catalog (functionally).[/success]")
        if removals and not prune:
            console.logger.info(
                f"[info]Note: {len(removals)} extra entries in global config (not in catalog): "
                f"{', '.join(removals)}. Pass --prune to remove them.[/info]"
            )
        return

    console.logger.info("[info]Planned changes to ~/.claude.json mcpServers:[/info]")
    for n in additions:
        console.logger.info(f"  [success]+ {n}[/success]")
    if prune:
        for n in removals:
            console.logger.info(f"  [warning]- {n} (in ~/.claude.json but not catalog)[/warning]")
    else:
        for n in removals:
            console.logger.info(f"  [info]· {n} (kept; pass --prune to remove)[/info]")
    for n in changed:
        console.logger.info(f"  [info]~ {n} (functional drift)[/info]")

    if not apply:
        console.logger.info("")
        console.logger.info("[info]Dry-run only. Re-run with --apply to write.[/info]")
        return

    # Build the merged result: catalog defines functional fields,
    # but preserve any user-set descriptions on existing entries.
    merged: Dict[str, Any] = {}
    for name, new_entry in desired.items():
        existing = current.get(name) or {}
        merged_entry = dict(new_entry)
        if "description" in existing and "description" not in merged_entry:
            merged_entry["description"] = existing["description"]
        merged[name] = merged_entry
    if not prune:
        # Keep entries that are in current but not in catalog.
        for name, entry in current.items():
            if name not in merged:
                merged[name] = entry

    backup = _backup_path(global_path)
    if global_path.exists():
        backup.write_bytes(global_path.read_bytes())
        console.logger.info(f"[info]Backup: {backup}[/info]")

    new_data = dict(global_data)
    new_data["mcpServers"] = merged
    _atomic_write_json(global_path, new_data)
    console.logger.info(f"[success]Wrote {global_path}.[/success]")
