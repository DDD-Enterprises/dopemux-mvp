"""
MCP Server Management Commands

Commands for starting, stopping, and monitoring MCP Docker servers.
The `servers` group is an alias for `mcp`.
"""

import sys
import subprocess
from pathlib import Path
from subprocess import CalledProcessError

import click
import yaml

from ..console import console


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

    if not isinstance(data, dict):
        raise click.ClickException(f"Invalid compose file {path}: root must be a mapping")

    services = data.get("services", {})
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
        result = subprocess.run(["docker", "compose", "-f", "compose.yml", "ps"], check=False)
        sys.exit(result.returncode)
    except FileNotFoundError:
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
        result = subprocess.run(cmd, check=False)
        sys.exit(result.returncode)
    except FileNotFoundError:
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
