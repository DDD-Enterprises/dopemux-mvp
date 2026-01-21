#!/usr/bin/env python3
"""
Profile Management CLI Commands for Dopemux

Provides user-facing commands for managing configuration profiles.
"""

import click

import logging

logger = logging.getLogger(__name__)

from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from .profile_manager import ProfileManager

console = Console()

def detect_workspace() -> Path:
    """Detect current workspace (git root or cwd)."""
    import subprocess
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True
        )
        return Path(result.stdout.strip())
    except Exception as e:
        return Path.cwd()


        logger.error(f"Error: {e}")
@click.command("list")
def list_profiles():
    """📋 List all available profiles"""
    manager = ProfileManager()
    profiles = manager.list_profiles()

    if not profiles:
        console.logger.info("\n[yellow]No profiles found[/yellow]")
        return

    table = Table(title=f"\n📋 Profiles ({len(profiles)})", show_header=True, box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="white")

    workspace = detect_workspace()
    active = manager.get_active_profile(workspace)

    for p in profiles:
        name = f"[bold]{p.name} ✅[/bold]" if p.name == active else p.name
        table.add_row(name, p.description[:60])

    console.logger.info(table)


@click.command("use")
@click.argument("profile_name")
def use_profile(profile_name: str):
    """✅ Set active profile"""
    workspace = detect_workspace()
    manager = ProfileManager()
    
    profile = manager.get_profile(profile_name)
    if not profile:
        console.logger.info(f"\n[red]❌ Profile not found: {profile_name}[/red]")
        return

    manager.set_active_profile(workspace, profile_name)
    console.logger.info(f"\n✅ Active profile: [cyan]{profile_name}[/cyan]")


@click.command("show")
@click.option("--verbose", "-v", is_flag=True)
def show_profile(verbose: bool):
    """🔍 Show active profile"""
    workspace = detect_workspace()
    manager = ProfileManager()
    active_name = manager.get_active_profile(workspace)

    if not active_name:
        console.logger.info(f"\n[yellow]No active profile[/yellow]")
        return

    profile = manager.get_profile(active_name)
    if not profile:
        return

    content = [
        f"[bold cyan]Profile:[/bold cyan] {profile.name}",
        f"{profile.description}\n",
        f"[bold]MCP Servers:[/bold]",
        f"  Required: {', '.join(profile.mcp_servers.get('required', []))}",
    ]

    console.logger.info(Panel("\n".join(content), border_style="cyan"))

    if verbose:
        merged = manager.load_merged_config(workspace, active_name)
        import yaml
        console.logger.info(f"\n[dim]{yaml.dump(merged, default_flow_style=False)}[/dim]")


@click.command("create")
@click.argument("name")
@click.option("--description", "-d")
@click.option("--based-on", "-b")
def create_profile(name: str, description: str, based_on: str):
    """➕ Create custom profile"""
    manager = ProfileManager()
    
    try:
        desc = description or f"Custom: {name}"
        profile = manager.create_profile(name, desc, based_on)
        console.logger.info(f"\n✅ Profile created: [cyan]{name}[/cyan]")
        console.logger.info(f"[dim]Edit: ~/.dopemux/profiles/{name}.yaml[/dim]")
    except ValueError as e:
        console.logger.info(f"\n[red]❌ {e}[/red]")
