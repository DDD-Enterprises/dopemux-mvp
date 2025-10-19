#!/usr/bin/env python3
"""Dev Mode CLI Commands for Dopemux"""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from .dev_mode import DevMode

console = Console()


@click.command("status")
def dev_status():
    """🔍 Show development mode status"""
    status = DevMode.get_status()

    # Build status display
    content = []
    content.append(f"[bold]Dev Mode:[/bold] {'✅ ACTIVE' if status['active'] else '❌ Inactive'}")
    content.append(f"[bold]Test Databases:[/bold] {'✅' if status['test_databases'] else '❌'}")
    content.append(f"[bold]Log Level:[/bold] {status['log_level']}")
    content.append(f"[bold]Database Dir:[/bold] [dim]{status['database_dir']}[/dim]\n")

    # Show dev component paths
    if status['dev_components']:
        content.append("[bold]Component Dev Paths:[/bold]")
        for name, path in status['dev_components'].items():
            if path:
                content.append(f"  {name}: [green]{path}[/green] ✅")
        content.append("")

    # Show skipped services
    if status['skip_services'] and status['skip_services'][0]:
        content.append(f"[bold]Skipped Services:[/bold] {', '.join(status['skip_services'])}")

    console.print(Panel(
        "\n".join(content),
        title="[bold]🔧 Development Mode Status[/bold]",
        border_style="yellow" if status['active'] else "dim"
    ))

    # Show recommendations
    if status['active']:
        console.print("\n[bold]💡 Dev Mode Tips:[/bold]")
        console.print("  • Edit code in detected paths - changes take effect")
        console.print("  • Use test databases (isolated from production)")
        console.print("  • Check logs with: dopemux health --verbose")
    else:
        console.print("\n[dim]Dev mode inactive. To enable:[/dim]")
        console.print("[dim]  export DOPEMUX_DEV_MODE=true[/dim]")
        console.print("[dim]  Or clone component to ~/code/{component-name}[/dim]")


@click.command("enable")
def dev_enable():
    """✅ Enable development mode"""
    import subprocess

    # Add to shell profile
    shell_config = None
    if Path.home() / ".bashrc":
        shell_config = Path.home() / ".bashrc"
    elif Path.home() / ".zshrc":
        shell_config = Path.home() / ".zshrc"

    if shell_config:
        with open(shell_config, "a") as f:
            f.write("\n# Dopemux dev mode\nexport DOPEMUX_DEV_MODE=true\n")
        console.print(f"\n✅ Dev mode enabled in {shell_config}")
        console.print("[dim]Restart shell or run: source {shell_config}[/dim]")
    else:
        console.print("\n[yellow]⚠️  Shell config not found[/yellow]")
        console.print("[dim]Manually add: export DOPEMUX_DEV_MODE=true[/dim]")


@click.command("paths")
def dev_paths():
    """📁 Show detected development paths"""
    components = DevMode.get_all_dev_components()

    if not components:
        console.print("\n[yellow]No development components detected[/yellow]")
        console.print("\n[dim]Clone to standard locations:[/dim]")
        console.print("[dim]  git clone <zen-repo> ~/code/zen-mcp-server[/dim]")
        console.print("[dim]  git clone <dopemux> ~/code/dopemux-mvp[/dim]")
        return

    table = Table(title="\n🔧 Development Component Paths", show_header=True, box=box.ROUNDED)
    table.add_column("Component", style="cyan")
    table.add_column("Local Path", style="green")
    table.add_column("Status", style="yellow")

    for name, path in components.items():
        status = "✅ Active" if path else "❌ Not found"
        table.add_row(name, str(path), status)

    console.print(table)
    console.print("\n[dim]Dopemux will use these paths instead of production versions[/dim]")
