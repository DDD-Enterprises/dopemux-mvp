"""
Hooks Integration Commands

Manages Claude Code integration hooks for activity signal monitoring and
shell hook installation. Orchestrates high-fidelity monitoring of Claude
Code activity signals into per-project Chronicle ledger.
"""

import logging
import sys

import click

from ..console import console

logger = logging.getLogger(__name__)


@click.command("hooks")
@click.option("--setup", is_flag=True, help="🚀 Ignite Sensors: Start monitoring Claude Code activity signals.")
@click.option("--teardown", is_flag=True, help="⏹️ Halt Sensors: Stop monitoring Claude Code activity.")
@click.option("--status", is_flag=True, help="📊 Sensor HUD: Show current hook operational status.")
@click.option(
    "--enable",
    help="⚡ Engage Sensor: Enable specific hook type (session-start, file-change, shell-command, git-commit).",
)
@click.option(
    "--disable",
    help="⏸️  Silence Sensor: Disable specific hook type.",
)
@click.option("--shell-scripts", is_flag=True, help="🐚 Generate Rituals: Generate shell hook scripts for manual uplink.")
@click.option(
    "--install-shell-hooks", is_flag=True, help="⚡ Commit Uplink: Install shell hooks into system shell configuration."
)
@click.option(
    "--uninstall-shell-hooks",
    is_flag=True,
    help="🔌 Sever Uplink: Uninstall shell hooks from shell configuration.",
)
@click.option(
    "--workspace",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="🔬 Ritual Chamber: Target workspace for hook synchronization.",
)
@click.option("--force", is_flag=True, help="⚡ Force Extraction: Overwrite safety interlocks for hook operations.")
@click.pass_context
def hooks_cmd(
    ctx,
    setup,
    teardown,
    status,
    enable,
    disable,
    shell_scripts,
    install_shell_hooks,
    uninstall_shell_hooks,
    workspace,
    force,
):
    """
    🔗 Event Synchronization: Manage Claude Code integration hooks

    Orchestrates the high-fidelity monitoring of Claude Code activity signals.
    This system synchronizes shell rituals, file system modifications, and
    git telemetry into the per-project Chronicle ledger.
    """
    try:
        from ..hooks.claude_code_hooks import claude_hooks, get_shell_hook_scripts

        if setup:
            claude_hooks.start_monitoring(workspace)
            console.logger.info("[success]✅ Claude Code hooks started[/success]")
            console.logger.info(
                f"   Monitoring paths: {[str(p) for p in claude_hooks.watched_paths]}"
            )

        elif teardown:
            claude_hooks.stop_monitoring()
            console.logger.info("[success]✅ Claude Code hooks stopped[/success]")

        elif status:
            hook_status = claude_hooks.get_status()
            console.logger.info("[bold]Claude Code Hook Status:[/bold]")
            console.logger.info(
                f"   Monitoring active: {hook_status['monitoring_active']}"
            )
            console.logger.info(f"   Quiet mode: {hook_status['quiet_mode']}")
            console.logger.info(f"   Watched paths: {hook_status['watched_paths']}")
            console.logger.info("\n[bold]Hook Types:[/bold]")
            for hook_type, enabled in hook_status["active_hooks"].items():
                status_icon = "[success]✓[/success]" if enabled else "[error]✗[/error]"
                console.logger.info(f"   {status_icon} {hook_type}")

        elif enable:
            claude_hooks.enable_hook(enable)
            console.logger.info(f"[success]✅ Hook enabled: {enable}[/success]")

        elif disable:
            claude_hooks.disable_hook(disable)
            console.logger.info(f"[success]✅ Hook disabled: {disable}[/success]")

        elif shell_scripts:
            scripts = get_shell_hook_scripts()
            console.logger.info("[bold]Shell Hook Scripts:[/bold]")
            console.logger.info(
                "\n[text.dim]Add these to your ~/.bashrc or ~/.zshrc:[/text.dim]\n"
            )

            console.logger.info("[mint]For Bash:[/mint]")
            console.logger.info(scripts["bash_preexec"])
            console.logger.info(scripts["bash_precmd"])

            console.logger.info("\n[mint]For Zsh:[/mint]")
            console.logger.info(scripts["zsh_hooks"])

        elif install_shell_hooks:
            from ..hooks.shell_hook_installer import install_shell_hooks as installer

            success, message = installer(force=force)
            if success:
                console.logger.info(f"[success]{message}[/success]")
            else:
                console.logger.info(f"[error]{message}[/error]")
                sys.exit(1)

        elif uninstall_shell_hooks:
            from ..hooks.shell_hook_installer import uninstall_shell_hooks as uninstaller

            success, message = uninstaller()
            if success:
                console.logger.info(f"[success]{message}[/success]")
            else:
                console.logger.info(f"[error]{message}[/error]")
                sys.exit(1)

        else:
            # Default: show help
            console.logger.info("[bold]Dopemux Hook System[/bold]")
            console.logger.info("Manage external hooks for Claude Code integration.\n")
            console.logger.info("[bold]Commands:[/bold]")
            console.logger.info(
                "   --setup               Start monitoring Claude Code activity"
            )
            console.logger.info("   --teardown            Stop monitoring")
            console.logger.info("   --status              Show current hook status")
            console.logger.info("   --enable HOOK         Enable specific hook type")
            console.logger.info("   --disable HOOK        Disable specific hook type")
            console.logger.info("   --shell-scripts       Generate shell hook scripts")
            console.logger.info(
                "   --install-shell-hooks Install shell hooks in shell config"
            )
            console.logger.info(
                "   --uninstall-shell-hooks Remove shell hooks from shell config"
            )
            console.logger.info("   --workspace PATH      Set workspace to monitor")
            console.logger.info(
                "   --force               Force operations (e.g., reinstall)\n"
            )
            console.logger.info("[bold]Hook Types:[/bold]")
            console.logger.info("   session-start    Monitor Claude Code process start")
            console.logger.info("   file-change      Monitor file modifications")
            console.logger.info("   shell-command    Monitor shell commands")
            console.logger.info(
                "   git-commit       Monitor git operations (disabled by default)"
            )

    except Exception as e:
        console.logger.error(f"[error]❌ Hook command failed: {e}[/error]")
        if (ctx.obj or {}).get("verbose"):
            raise
        sys.exit(1)
