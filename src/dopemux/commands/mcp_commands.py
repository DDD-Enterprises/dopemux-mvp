"""
MCP Server Management Commands

Commands for starting, stopping, and monitoring MCP Docker servers
(``up``/``down``/``status``/``logs``/``start-all``), plus MCP config
scaffolding driven by repo-local or bundled ``mcp_catalog.yaml`` data
(``init``/``add``/``remove``/``list``/``doctor``/``sync-globals``).

The ``servers`` group is an alias for ``mcp`` for backward compatibility.
"""

import hashlib
import importlib.resources
import json
import os
import socket
import sys
import subprocess
from datetime import datetime
from pathlib import Path
from subprocess import CalledProcessError
from typing import Any, Dict, List, Optional, Tuple

import click
import yaml

from ..console import console
from ..mcp.project_identity import ProjectIdentityError, resolve_project_identity
from ..worktree_commands import get_repo_root


DEFAULT_MCP_SERVICES = {
    "conport",
    "desktop-commander",
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


@mcp.command("up")
@click.option("--all", "all_services", is_flag=True, help="🚀 Boot Fleet: Start every configured MCP service simultaneously.")
@click.option("--services", "services", help="🎯 Targeted Ignition: Comma-separated list of specific MCP services to ignite.")
def mcp_up_cmd(all_services: bool, services: str):
    """
    ⚡ Ignite Engine: Deploy MCP servers via Docker Compose

    Materializes the Model Context Protocol environment, initializing the 
    distributed tool architecture required for high-fidelity focus-tracking 
    and codebase interrogation.
    """
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
def mcp_down_cmd():
    """
    💧 Cool Down Cores: Terminate MCP containers and volumes

    Safely deactivates the neural infrastructure, releasing system resources 
    and preserving ritual state in the Docker volume ledgers.
    """
    try:
        mcp_services = [
            "conport", "pal", "litellm", "dope-context",
            "serena", "gptr-mcp", "desktop-commander", "leantime-bridge",
        ]
        subprocess.run(
            ["docker", "compose", "-f", "compose.yml", "rm", "-f", "-s", "-v"] + mcp_services,
            check=True,
        )
        console.logger.info("[success]MCP servers stopped[/success]")
    except (CalledProcessError, FileNotFoundError) as exc:
        console.logger.error(f"[error]Failed to stop MCP servers: {exc}[/error]")
        sys.exit(1)


@mcp.command("status")
def mcp_status_cmd():
    """
    📊 Diagnostic HUD: Interrogate MCP service health

    Displays the current operational state, port mappings, and uptime for 
    all registered MCP daemons. Essential for diagnosing sensor disconnects.
    """
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

            console.logger.info("[info]Starting Integration Bridge...[/info]")
            subprocess.run(
                ["bash", "-lc", "cd docker/conport-kg && docker-compose up -d --no-deps integration-bridge"],
                check=True,
            )

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
def servers_up_cmd(all_services: bool, services: str):
    """
    ⚡ Ignite Engine (Alias): Deploy MCP servers via Docker Compose
    """
    mcp_up_cmd.callback(all_services, services)


@servers.command("down")
def servers_down_cmd():
    """
    💧 Cool Down Cores (Alias): Terminate MCP containers and volumes
    """
    mcp_down_cmd.callback()


@servers.command("status")
def servers_status_cmd():
    """
    📊 Diagnostic HUD (Alias): Interrogate MCP service health
    """
    mcp_status_cmd.callback()


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


def _allocate_ports(worktree: str, names: List[str], catalog: Dict[str, Any]) -> Dict[str, int]:
    """
    Compute ports for each per-worktree server, including any `extra_port_vars`
    declared by the spec (e.g. conport exposes three host ports for one service).
    Same hash offset is reused across a single server's primary + extras.
    """
    assignments: Dict[str, int] = {}
    seen_ports: Dict[int, str] = {}

    def _claim(var: str, base: int, owner: str) -> None:
        port = _port_for(worktree, base)
        if port in seen_ports:
            raise click.ClickException(
                f"Internal port collision: {owner}.{var} and {seen_ports[port]} both hashed to :{port}. "
                f"Adjust the `default_port_base` for one of them in {CATALOG_FILENAME}."
            )
        seen_ports[port] = f"{owner}.{var}"
        assignments[var] = port

    for name in names:
        spec = catalog["servers"].get(name)
        if not spec or spec.get("scope") != "per-worktree":
            continue
        base = spec.get("default_port_base")
        if base:
            _claim(spec["port_var"], base, name)
        for extra in spec.get("extra_port_vars", []) or []:
            _claim(extra["var"], extra["base"], name)
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
# `mcp init` / `add` / `remove` / `list` / `doctor` / `sync-globals`
# ---------------------------------------------------------------------------

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

    port_vars = _allocate_ports(repo, ordered, catalog)
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
        **_allocate_ports(repo, [name], catalog),
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


def _run_stdio_doctor(name: str, spec: Dict[str, Any], env: Dict[str, str]) -> List[str]:
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
def mcp_doctor_cmd():
    """
    🩺 Health Sweep: Verify env vars, port reachability, container health
    """
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

    doctor_env = dict(os.environ)
    doctor_env.update(_project_env_exports(repo, str(identity.project_root)))

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
        env_source = doctor_env if is_stdio else os.environ
        for env_key in spec.get("requires_env", []) or []:
            if not env_source.get(env_key):
                problems.append(f"`{name}`: required env `{env_key}` is unset.")
        if is_stdio:
            problems.extend(_run_stdio_doctor(name, spec, doctor_env))
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
    desired = {
        name: _render_global_entry(name, spec)
        for name, spec in catalog["servers"].items()
        if spec.get("scope") == "singleton"
    }

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
