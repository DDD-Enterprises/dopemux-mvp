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

from ..console import console


@click.group()
def mcp():
    """Manage MCP Docker servers (start/stop/status/logs)."""


@mcp.command("up")
@click.option("--all", "all_services", is_flag=True, help="Start all MCP servers")
@click.option("--services", "services", help="Comma-separated services to start")
def mcp_up_cmd(all_services: bool, services: str):
    """Start MCP servers via docker-compose."""
    try:
        script_dir = Path(__file__).parent.parent.parent.parent / "scripts"
        script_path = script_dir / "start-all-mcp-servers.sh"

        if all_services or not services:
            cmd = f"bash {script_path}"
        else:
            svc_list = " ".join(s.strip() for s in services.split(",") if s.strip())
            cmd = f"docker compose -f compose.yml up -d --build {svc_list}"
        console.logger.info(f"[info]{cmd}[/info]")
        subprocess.run(["bash", "-lc", cmd], check=True)
        console.logger.info("[success]MCP servers started[/success]")
    except CalledProcessError:
        console.logger.error("[error]Failed to start MCP servers[/error]")
        sys.exit(1)


@mcp.command("down")
def mcp_down_cmd():
    """Stop all MCP servers."""
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
    except CalledProcessError:
        console.logger.error("[error]Failed to stop MCP servers[/error]")
        sys.exit(1)


@mcp.command("status")
def mcp_status_cmd():
    """Show docker-compose status for MCP servers."""
    try:
        subprocess.run(["docker", "compose", "-f", "compose.yml", "ps"], check=False)
    except CalledProcessError:
        sys.exit(1)


@mcp.command("logs")
@click.option("--service", "service", help="Service to tail logs for")
def mcp_logs_cmd(service: str):
    """Tail logs for an MCP service or all."""
    try:
        if service:
            cmd = f"docker compose -f compose.yml logs -f {service}"
        else:
            cmd = "docker compose -f compose.yml logs -f"
        console.logger.info(f"[info]{cmd}[/info]")
        subprocess.run(["bash", "-lc", cmd], check=False)
    except CalledProcessError:
        sys.exit(1)


@mcp.command("start-all")
@click.option("--verify", "-v", is_flag=True, help="Verify service health after starting")
def mcp_start_all_cmd(verify: bool):
    """
    Start complete Dopemux stack (MCP servers + application services)

    Starts all services including MCP servers (ConPort, Zen, Serena, etc.),
    Integration Bridge, Task Orchestrator, and all infrastructure.

    \b
    Examples:
        dopemux mcp start-all           # Start everything
        dopemux mcp start-all --verify  # Start + verify health
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
    """Alias for 'dopemux mcp' commands."""


@servers.command("up")
@click.option("--all", "all_services", is_flag=True, help="Start all MCP servers")
@click.option("--services", "services", help="Comma-separated services to start")
def servers_up_cmd(all_services: bool, services: str):
    mcp_up_cmd.callback(all_services, services)


@servers.command("down")
def servers_down_cmd():
    mcp_down_cmd.callback()


@servers.command("status")
def servers_status_cmd():
    mcp_status_cmd.callback()


@servers.command("logs")
@click.option("--service", "service", help="Service to tail logs for")
def servers_logs_cmd(service: str):
    mcp_logs_cmd.callback(service)
