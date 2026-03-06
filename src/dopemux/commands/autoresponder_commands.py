"""
Claude Auto Responder Commands

Commands for managing the Claude Auto Responder integration with ADHD-optimized controls.
"""

import sys
from pathlib import Path

import click
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ..console import console
from ..config import ConfigManager


@click.group()
@click.pass_context
def autoresponder(ctx):
    """
    🤖 Manage Claude Auto Responder integration

    Automatic confirmation responses for Claude Code prompts with
    ADHD-optimized controls and attention-aware features.
    """


def _get_autoresponder_config_manager(ctx, project_path: Path) -> ConfigManager:
    """Use project-local config for autoresponder commands when inside a Dopemux project."""
    if (project_path / ".dopemux").exists():
        return ConfigManager(config_path=str(project_path / ".dopemux" / "config.yaml"))

    return ctx.obj["config_manager"]


@autoresponder.command("start")
@click.option(
    "--terminal-scope",
    "-t",
    type=click.Choice(["current", "all", "project"]),
    help="Terminal scope for monitoring",
)
@click.option("--delay", "-d", type=float, help="Response delay in seconds (0-10)")
@click.option("--timeout", type=int, help="Auto-stop timeout in minutes")
@click.option(
    "--whitelist/--no-whitelist", default=None, help="Enable/disable tool whitelisting"
)
@click.option("--debug/--no-debug", default=None, help="Enable/disable debug mode")
@click.pass_context
def autoresponder_start(ctx, terminal_scope, delay, timeout, whitelist, debug):
    """
    🚀 Start Claude Auto Responder

    Begins automatic confirmation of Claude Code prompts with current
    configuration settings and ADHD optimizations.
    """
    project_path = Path.cwd()
    config_manager = _get_autoresponder_config_manager(ctx, project_path)

    if not (project_path / ".dopemux").exists():
        console.logger.info("[red]No Dopemux project found in current directory[/red]")
        sys.exit(1)

    # Update configuration if options provided
    updates = {}
    if terminal_scope:
        updates["terminal_scope"] = terminal_scope
    if delay is not None:
        updates["response_delay"] = delay
    if timeout:
        updates["timeout_minutes"] = timeout
    if whitelist is not None:
        updates["whitelist_tools"] = whitelist
    if debug is not None:
        updates["debug_mode"] = debug

    if updates:
        config_manager.update_claude_autoresponder(**updates)

    from integrations.claude_autoresponder import create_autoresponder_manager

    autoresponder_manager = create_autoresponder_manager(config_manager, project_path)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Starting auto responder...", total=None)

        success = autoresponder_manager.start()

        if success:
            progress.update(
                task, description="Auto responder started! 🤖", completed=True
            )
            console.logger.info("[green]✅ Claude Auto Responder is now active[/green]")
            console.print(
                "[blue]🎯 Monitoring for Claude Code confirmation prompts[/blue]"
            )

            config = config_manager.get_claude_autoresponder_config()
            console.logger.info(f"[yellow]📡 Scope: {config.terminal_scope}[/yellow]")
            if config.response_delay > 0:
                console.logger.info(f"[cyan]⏱️ Delay: {config.response_delay}s[/cyan]")
            console.print(
                f"[dim]💤 Auto-stop after {config.timeout_minutes} minutes of inactivity[/dim]"
            )
        else:
            progress.update(task, description="Failed to start", completed=True)
            console.logger.error("[red]❌ Failed to start auto responder[/red]")
            console.print(
                "[yellow]💡 Try running 'dopemux autoresponder setup' first[/yellow]"
            )
            sys.exit(1)


@autoresponder.command("stop")
@click.pass_context
def autoresponder_stop(ctx):
    """
    ⏹️ Stop Claude Auto Responder

    Stops automatic confirmation and displays session statistics.
    """
    project_path = Path.cwd()
    config_manager = _get_autoresponder_config_manager(ctx, project_path)

    if not (project_path / ".dopemux").exists():
        console.logger.info("[red]No Dopemux project found in current directory[/red]")
        sys.exit(1)

    from integrations.claude_autoresponder import create_autoresponder_manager

    autoresponder_manager = create_autoresponder_manager(config_manager, project_path)

    if not autoresponder_manager.is_running():
        console.logger.info("[yellow]Auto responder is not running[/yellow]")
        return

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Stopping auto responder...", total=None)

        # Get stats before stopping
        status = autoresponder_manager.get_status()

        success = autoresponder_manager.stop()

        if success:
            progress.update(task, description="Auto responder stopped", completed=True)
            console.logger.info("[green]✅ Claude Auto Responder stopped[/green]")

            # Show session stats
            console.logger.info(f"[blue]📊 Session Statistics:[/blue]")
            console.logger.info(f"  ⏱️ Uptime: {status['uptime_minutes']:.1f} minutes")
            console.logger.info(f"  ✅ Responses sent: {status['responses_sent']}")
            if status["responses_sent"] > 0:
                console.print(
                    f"  📈 Rate: {status['responses_per_minute']:.1f} responses/min"
                )
        else:
            progress.update(task, description="Error stopping", completed=True)
            console.logger.error("[red]❌ Error stopping auto responder[/red]")


@autoresponder.command("status")
@click.pass_context
def autoresponder_status(ctx):
    """
    📊 Show auto responder status

    Displays current status, configuration, and performance metrics.
    """
    project_path = Path.cwd()
    config_manager = _get_autoresponder_config_manager(ctx, project_path)

    if not (project_path / ".dopemux").exists():
        console.logger.info("[red]No Dopemux project found in current directory[/red]")
        sys.exit(1)

    from integrations.claude_autoresponder import create_autoresponder_manager

    autoresponder_manager = create_autoresponder_manager(config_manager, project_path)
    status = autoresponder_manager.get_status()

    # Status overview
    status_color = "green" if status["running"] else "yellow"
    status_emoji = "🟢" if status["running"] else "🟡"

    table = Table(title="🤖 Claude Auto Responder Status")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style=status_color)

    table.add_row("Status", f"{status_emoji} {status['status'].title()}")
    table.add_row("Running", "Yes" if status["running"] else "No")

    if status["running"]:
        table.add_row("Uptime", f"{status['uptime_minutes']:.1f} minutes")
        table.add_row("Responses Sent", str(status["responses_sent"]))
        table.add_row("Response Rate", f"{status['responses_per_minute']:.1f}/min")
        table.add_row("Attention State", status["attention_state"])

        if status["last_response"]:
            table.add_row("Last Response", status["last_response"])

    console.logger.info(table)

    # Configuration table
    config_table = Table(title="⚙️ Configuration")
    config_table.add_column("Setting", style="cyan")
    config_table.add_column("Value", style="green")

    config = status["config"]
    config_table.add_row("Enabled", "Yes" if config["enabled"] else "No")
    config_table.add_row("Terminal Scope", config["terminal_scope"])
    config_table.add_row("Response Delay", f"{config['response_delay']}s")
    config_table.add_row("Timeout", f"{config['timeout_minutes']} minutes")
    config_table.add_row(
        "Whitelist Tools", "Yes" if config["whitelist_tools"] else "No"
    )
    config_table.add_row("Debug Mode", "Yes" if config["debug_mode"] else "No")

    console.logger.info(config_table)


@autoresponder.command("setup")
@click.pass_context
def autoresponder_setup(ctx):
    """
    🔧 Setup Claude Auto Responder

    Downloads and configures the ClaudeAutoResponder tool for use with Dopemux.
    """
    project_path = Path.cwd()
    config_manager = _get_autoresponder_config_manager(ctx, project_path)

    if not (project_path / ".dopemux").exists():
        console.logger.info("[red]No Dopemux project found in current directory[/red]")
        sys.exit(1)

    from integrations.claude_autoresponder import create_autoresponder_manager

    autoresponder_manager = create_autoresponder_manager(config_manager, project_path)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Setting up ClaudeAutoResponder...", total=None)

        success = autoresponder_manager.setup_autoresponder()

        if success:
            progress.update(task, description="Setup complete! 🎉", completed=True)
            console.logger.info("[green]✅ ClaudeAutoResponder setup complete[/green]")
            console.logger.info("[blue]🚀 Run 'dopemux autoresponder start' to begin[/blue]")
        else:
            progress.update(task, description="Setup failed", completed=True)
            console.logger.error("[red]❌ Setup failed[/red]")
            console.logger.info("[yellow]Check logs for details[/yellow]")
            sys.exit(1)
