"""
Claude Auto Responder Commands

Commands for managing the Claude Auto Responder integration with ADHD-optimized controls.
"""

import sys
from pathlib import Path

import click
from dopemux.ui.progress import branded_progress
from dopemux.ui.progress import branded_progress
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..console import console
from ..config import ConfigManager
from ..ui.theme import styled_panel, styled_table, error_panel, Glyphs, StatusChip


@click.group()
@click.pass_context
def autoresponder(ctx):
    """
    🤖 Auto-Response Ritual: Manage Claude Auto Responder integration

    Orchestrates the automatic confirmation response system for Claude Code. 
    This system synchronizes ADHD-optimized attention patterns with CLI 
    prompts, providing a seamless, automated feedback loop within the cockpit.
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
    help="📡 Monitoring Scope: Terminal boundaries for signal detection.",
)
@click.option("--delay", "-d", type=float, help="⏱️ Ritual Delay: Response latency in seconds (0-10).")
@click.option("--timeout", type=int, help="⏳ Auto-Stop: Duration in minutes before halting the ritual.")
@click.option(
    "--whitelist/--no-whitelist", default=None, help="🛡️  Tool Validation: Enable high-fidelity whitelisting for responses."
)
@click.option("--debug/--no-debug", default=None, help="📜 Deep Telemetry: Toggle debug mode for internal signals.")
@click.pass_context
def autoresponder_start(ctx, terminal_scope, delay, timeout, whitelist, debug):
    """
    🚀 Ignite Responder: Start Claude Auto Responder

    Activates the automatic confirmation sequence, synchronizing 
    ADHD-optimized heuristics with the active Claude Code session.
    """
    project_path = Path.cwd()
    config_manager = _get_autoresponder_config_manager(ctx, project_path)

    if not (project_path / ".dopemux").exists():
        console.logger.info("[error]No Dopemux project found in current directory[/error]")
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

    with branded_progress(
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
            console.logger.info("[success]✅ Claude Auto Responder is now active[/success]")
            console.print(
                "[info]🎯 Monitoring for Claude Code confirmation prompts[/info]"
            )

            config = config_manager.get_claude_autoresponder_config()
            console.logger.info(f"[warning]📡 Scope: {config.terminal_scope}[/warning]")
            if config.response_delay > 0:
                console.logger.info(f"[info]⏱️ Delay: {config.response_delay}s[/info]")
            console.print(
                f"[text.dim]💤 Auto-stop after {config.timeout_minutes} minutes of inactivity[/text.dim]"
            )
        else:
            progress.update(task, description="Failed to start", completed=True)
            console.logger.error("[error]❌ Failed to start auto responder[/error]")
            console.print(
                "[warning]💡 Try running 'dopemux autoresponder setup' first[/warning]"
            )
            sys.exit(1)


@autoresponder.command("stop")
@click.pass_context
def autoresponder_stop(ctx):
    """
    ⏹️ Halt Ritual: Stop Claude Auto Responder

    Deactivates the automatic confirmation sequence and renders a 
    diagnostic summary of the session telemetry.
    """
    project_path = Path.cwd()
    config_manager = _get_autoresponder_config_manager(ctx, project_path)

    if not (project_path / ".dopemux").exists():
        console.logger.info("[error]No Dopemux project found in current directory[/error]")
        sys.exit(1)

    from integrations.claude_autoresponder import create_autoresponder_manager

    autoresponder_manager = create_autoresponder_manager(config_manager, project_path)

    if not autoresponder_manager.is_running():
        console.logger.info("[warning]Auto responder is not running[/warning]")
        return

    with branded_progress(
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
            console.logger.info("[success]✅ Claude Auto Responder stopped[/success]")

            # Show session stats
            console.logger.info(f"[info]📊 Session Statistics:[/info]")
            console.logger.info(f"  ⏱️ Uptime: {status['uptime_minutes']:.1f} minutes")
            console.logger.info(f"  ✅ Responses sent: {status['responses_sent']}")
            if status["responses_sent"] > 0:
                console.print(
                    f"  📈 Rate: {status['responses_per_minute']:.1f} responses/min"
                )
        else:
            progress.update(task, description="Error stopping", completed=True)
            console.logger.error("[error]❌ Error stopping auto responder[/error]")


@autoresponder.command("status")
@click.pass_context
def autoresponder_status(ctx):
    """
    📊 Monitoring HUD: Show auto responder status

    Displays the current operational coordinates, cognitive configuration, 
    and performance metrics of the responder daemon.
    """
    project_path = Path.cwd()
    config_manager = _get_autoresponder_config_manager(ctx, project_path)

    if not (project_path / ".dopemux").exists():
        console.logger.info("[error]No Dopemux project found in current directory[/error]")
        sys.exit(1)

    from integrations.claude_autoresponder import create_autoresponder_manager

    autoresponder_manager = create_autoresponder_manager(config_manager, project_path)
    status = autoresponder_manager.get_status()

    status_emoji = "🟢" if status["running"] else "🟡"
    click.echo("Claude Auto Responder Status")
    click.echo(f"Status: {status_emoji} {status['status'].title()}")
    click.echo(f"Running: {'Yes' if status['running'] else 'No'}")
    if status["running"]:
        click.echo(f"Uptime: {status['uptime_minutes']:.1f} minutes")
        click.echo(f"Responses Sent: {status['responses_sent']}")
        click.echo(f"Response Rate: {status['responses_per_minute']:.1f}/min")
        click.echo(f"Attention State: {status['attention_state']}")

        if status["last_response"]:
            click.echo(f"Last Response: {status['last_response']}")

    config = status["config"]
    click.echo("Configuration")
    click.echo(f"Enabled: {'Yes' if config['enabled'] else 'No'}")
    click.echo(f"Terminal Scope: {config['terminal_scope']}")
    click.echo(f"Response Delay: {config['response_delay']}s")
    click.echo(f"Timeout: {config['timeout_minutes']} minutes")
    click.echo(f"Whitelist Tools: {'Yes' if config['whitelist_tools'] else 'No'}")
    click.echo(f"Debug Mode: {'Yes' if config['debug_mode'] else 'No'}")


@autoresponder.command("setup")
@click.pass_context
def autoresponder_setup(ctx):
    """
    🔧 Ritual Preparation: Setup Claude Auto Responder

    Downloads and calibrates the ClaudeAutoResponder tool for high-fidelity 
    integration with the DØPEMÜX cockpit.
    """
    project_path = Path.cwd()
    config_manager = _get_autoresponder_config_manager(ctx, project_path)

    if not (project_path / ".dopemux").exists():
        console.logger.info("[error]No Dopemux project found in current directory[/error]")
        sys.exit(1)

    from integrations.claude_autoresponder import create_autoresponder_manager

    autoresponder_manager = create_autoresponder_manager(config_manager, project_path)

    with branded_progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Setting up ClaudeAutoResponder...", total=None)

        success = autoresponder_manager.setup_autoresponder()

        if success:
            progress.update(task, description="Setup complete! 🎉", completed=True)
            console.logger.info("[success]✅ ClaudeAutoResponder setup complete[/success]")
            console.logger.info("[info]🚀 Run 'dopemux autoresponder start' to begin[/info]")
        else:
            progress.update(task, description="Setup failed", completed=True)
            console.logger.error("[error]❌ Setup failed[/error]")
            console.logger.info("[warning]Check logs for details[/warning]")
            sys.exit(1)


@autoresponder.command("config")
@click.option(
    "--enabled/--disabled",
    default=None,
    help="⚡ Toggle Ritual: Enable or disable the auto responder daemon.",
)
@click.option(
    "--terminal-scope",
    type=click.Choice(["current", "all", "project"]),
    help="📡 Monitoring Scope: Terminal boundaries for signal detection.",
)
@click.option("--delay", type=float, help="⏱️ Ritual Delay: Response latency in seconds (0-10).")
@click.option("--timeout", type=int, help="⏳ Auto-Stop: Duration in minutes before halting the ritual.")
@click.option(
    "--whitelist/--no-whitelist",
    default=None,
    help="🛡️  Tool Validation: Enable high-fidelity whitelisting for responses.",
)
@click.option(
    "--debug/--no-debug",
    default=None,
    help="📜 Deep Telemetry: Toggle debug mode for internal signals.",
)
@click.pass_context
def autoresponder_config(
    ctx, enabled, terminal_scope, delay, timeout, whitelist, debug
):
    """
    ⚙️ Cognitive Tuning: Configure auto responder settings

    Updates the internal heuristics and operational parameters for 
    the Claude Auto Responder integration.
    """
    project_path = Path.cwd()
    config_manager = _get_autoresponder_config_manager(ctx, project_path)

    updates = {}
    if enabled is not None:
        updates["enabled"] = enabled
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

    if not updates:
        # Show current config
        current_config = config_manager.get_claude_autoresponder_config()
        click.echo("Auto Responder Configuration")
        click.echo(f"Enabled: {'Yes' if current_config.enabled else 'No'}")
        click.echo(f"Terminal Scope: {current_config.terminal_scope}")
        click.echo(f"Response Delay: {current_config.response_delay}s")
        click.echo(f"Timeout: {current_config.timeout_minutes} minutes")
        click.echo(
            f"Whitelist Tools: {'Yes' if current_config.whitelist_tools else 'No'}"
        )
        click.echo(f"Debug Mode: {'Yes' if current_config.debug_mode else 'No'}")
        return

    # Apply updates
    try:
        config_manager.update_claude_autoresponder(**updates)
        console.logger.info("[success]✅ Configuration updated[/success]")

        for key, value in updates.items():
            console.logger.info(f"[info]  {key}: {value}[/info]")

        # Restart if running
        if (project_path / ".dopemux").exists():
            from integrations.claude_autoresponder import create_autoresponder_manager

            autoresponder_manager = create_autoresponder_manager(
                config_manager, project_path
            )
            if autoresponder_manager.is_running():
                console.print(
                    "[warning]🔄 Restarting auto responder with new settings...[/warning]"
                )
                autoresponder_manager.restart()

    except ValueError as e:
        console.logger.error(f"[error]❌ Configuration error: {e}[/error]")
        sys.exit(1)
