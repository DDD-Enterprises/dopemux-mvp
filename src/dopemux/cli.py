#!/usr/bin/env python3
"""
Dopemux CLI - ADHD-optimized development platform CLI.

Main entry point for all dopemux commands providing context preservation,
attention monitoring, and task decomposition for neurodivergent developers.
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

from . import __version__

# Load environment variables from .env file
load_dotenv()
from .adhd import AttentionMonitor, ContextManager
# TaskDecomposer removed - replaced by ConPort + SuperClaude /dx: commands
from .claude import ClaudeConfigurator, ClaudeLauncher
from .claude_code_router import (
    ClaudeCodeRouterError,
    ClaudeCodeRouterManager,
)
from .config import ConfigManager
from .health import HealthChecker
from .instance_manager import InstanceManager, detect_instances_sync, detect_orphaned_instances_sync
from .litellm_proxy import LiteLLMProxyError, LiteLLMProxyManager
from .profile_models import ProfileValidationError
from .profile_parser import ProfileParser
from .protection_interceptor import check_and_protect_main, consume_last_created_worktree
import subprocess
from subprocess import CalledProcessError
import yaml


if "-litellm" in sys.argv:
    sys.argv = ["--litellm" if arg == "-litellm" else arg for arg in sys.argv]

console = Console()


def show_version(ctx, param, value):
    """Show version and exit."""
    if not value or ctx.resilient_parsing:
        return
    click.echo(f"Dopemux {__version__}")
    ctx.exit()


@click.group()
@click.option(
    "--version", is_flag=True, expose_value=False, is_eager=True, callback=show_version
)
@click.option("--config", "-c", help="Configuration file path")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.pass_context
def cli(ctx, config: Optional[str], verbose: bool):
    """
    🧠 Dopemux - ADHD-optimized development platform

    Provides context preservation, attention monitoring, and task decomposition
    for enhanced productivity in software development.
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["config_manager"] = ConfigManager(config_path=config)


@cli.command()
@click.argument("directory", default=".")
@click.option("--force", "-f", is_flag=True, help="Overwrite existing configuration")
@click.option(
    "--template",
    "-t",
    default="python",
    help="Project template (python, js, rust, etc.)",
)
@click.pass_context
def init(ctx, directory: str, force: bool, template: str):
    """
    🚀 Initialize a new Dopemux project

    Sets up .claude/ configuration and .dopemux/ directory with ADHD-optimized
    settings for the specified project type.
    """
    config_manager = ctx.obj["config_manager"]
    project_path = Path(directory).resolve()

    if not project_path.exists():
        console.print(f"[red]Directory {project_path} does not exist[/red]")
        sys.exit(1)

    # Check if already initialized
    dopemux_dir = project_path / ".dopemux"
    claude_dir = project_path / ".claude"

    if (dopemux_dir.exists() or claude_dir.exists()) and not force:
        console.print(
            "[yellow]Project already initialized. Use --force to overwrite.[/yellow]"
        )
        sys.exit(1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Create directories
        task = progress.add_task("Creating project structure...", total=None)
        dopemux_dir.mkdir(exist_ok=True)
        claude_dir.mkdir(exist_ok=True)

        # Initialize configuration
        progress.update(task, description="Setting up configuration...")
        configurator = ClaudeConfigurator(config_manager)
        configurator.setup_project_config(project_path, template)

        # Setup ADHD features
        progress.update(task, description="Configuring ADHD features...")
        context_manager = ContextManager(project_path)
        context_manager.initialize()

        progress.update(task, description="Complete!", completed=True)

    console.print(
        Panel(
            f"✅ Dopemux initialized in {project_path}\n\n"
            f"📁 Configuration: {claude_dir}\n"
            f"🧠 ADHD features: {dopemux_dir}\n\n"
            f"Next steps:\n"
            f"• Run 'dopemux start' to launch Claude Code\n"
            f"• Use 'dopemux save' to preserve context\n"
            f"• Check 'dopemux status' for attention metrics",
            title="🎉 Project Initialized",
            border_style="green",
        )
    )


@cli.command()
@click.option("--session", "-s", help="Restore specific session ID")
@click.option("--background", "-b", is_flag=True, help="Launch in background")
@click.option("--debug", is_flag=True, help="Launch with debug output")
@click.option(
    "--dangerous",
    is_flag=True,
    help="⚠️  Enable dangerous mode (no approvals, all tools)",
)
@click.option(
    "--dangerously-skip-permissions",
    is_flag=True,
    help="⚠️  Skip all permission checks (same as --dangerous)",
)
@click.option(
    "--no-mcp",
    is_flag=True,
    help="Skip starting MCP servers (not recommended for ADHD experience)",
)
@click.option(
    "--litellm",
    "use_litellm",
    is_flag=True,
    help="Route Claude Code traffic through LiteLLM proxy",
)
@click.option(
    "--claude-router/--no-claude-router",
    "use_claude_router",
    default=True,
    help="Start Claude Code Router per instance (requires global `ccr`)",
)
@click.pass_context
def start(
    ctx,
    session: Optional[str],
    background: bool,
    debug: bool,
    dangerous: bool,
    dangerously_skip_permissions: bool,
    no_mcp: bool,
    use_litellm: bool,
    use_claude_router: bool,
    **legacy_kwargs,
):
    """
    🚀 Start Claude Code with ADHD-optimized configuration

    Launches Claude Code with custom MCP servers, restores previous context,
    and activates attention monitoring for the current project.

    Multi-Instance Support:
        Automatically detects running instances and creates isolated worktrees
        for parallel ADHD-optimized development workflows.
    """
    legacy_value = legacy_kwargs.get("claude_router")
    if legacy_value is not None:
        use_claude_router = legacy_value

    config_manager = ctx.obj["config_manager"]
    project_path = Path.cwd()

    # Check if project is initialized
    if not (project_path / ".dopemux").exists():
        console.print(
            "[yellow]Project not initialized. Run 'dopemux init' first.[/yellow]"
        )
        if click.confirm("Initialize now?"):
            ctx.invoke(init, directory=str(project_path))
        else:
            sys.exit(1)

    # Worktree Recovery Menu (ADHD-optimized session recovery)
    # Show menu if orphaned worktree sessions exist
    from .worktree_recovery import show_recovery_menu_sync
    import os

    try:
        selected_worktree = show_recovery_menu_sync(
            workspace_id=str(project_path),
            conport_port=3004  # Default ConPort port for instance A
        )

        if selected_worktree:
            # User selected a worktree to recover
            console.print(f"\n[blue]🔄 Recovering worktree session: {selected_worktree}[/blue]")

            # Change to the selected worktree
            os.chdir(selected_worktree)
            project_path = Path(selected_worktree)

            console.print(f"[green]✅ Switched to worktree: {project_path.name}[/green]")
            console.print(f"[dim]   Path: {project_path}[/dim]\n")
    except Exception as e:
        console.print(f"[yellow]⚠️ Recovery menu unavailable: {e}[/yellow]")
        # Continue with normal startup - recovery is optional

    # Main Worktree Protection (ADHD-optimized guidance)
    # Check if working in main with uncommitted changes
    try:
        should_exit = check_and_protect_main(
            workspace_path=str(project_path),
            enforce=False  # Warn only (gentle guidance, not blocking)
        )

        new_worktree = consume_last_created_worktree()
        if new_worktree:
            os.chdir(new_worktree)
            project_path = Path.cwd()
            console.print(f"[green]🔀 Switched to worktree: {project_path.name}")
            console.print(f"[dim]   Path: {project_path}[/dim]")

        if should_exit and not new_worktree:
            # User chose to exit (create worktree or clean up manually)
            sys.exit(0)
    except Exception as e:
        console.print(f"[yellow]⚠️ Protection check unavailable: {e}[/yellow]")
        # Continue with normal startup - protection is optional

    # Multi-instance detection and coordination
    instance_manager = InstanceManager(project_path)
    running_instances = detect_instances_sync(project_path)

    instance_id = None
    port_base = None
    worktree_path = None
    instance_env_vars = {}

    if running_instances:
        # Instances already running - offer to create new worktree
        console.print(f"\n[yellow]⚠️  Found {len(running_instances)} running instance(s):[/yellow]")

        table = Table(title="Running Instances")
        table.add_column("Instance", style="cyan")
        table.add_column("Port", style="magenta")
        table.add_column("Branch", style="green")
        table.add_column("Path", style="dim")

        for inst in running_instances:
            table.add_row(
                inst.instance_id,
                str(inst.port_base),
                inst.git_branch or "unknown",
                str(inst.worktree_path) if inst.worktree_path else "N/A"
            )

        console.print(table)

        try:
            instance_id, port_base = instance_manager.get_next_available_instance(running_instances)

            console.print(
                f"\n[blue]💡 Multi-instance mode: Creating new worktree for instance {instance_id}[/blue]"
            )

            if click.confirm(f"Create new worktree on port {port_base}?", default=True):
                # Get branch name from user
                suggested_branch = f"feature/instance-{instance_id}"
                branch_name = click.prompt(
                    "Branch name",
                    default=suggested_branch,
                    show_default=True
                )

                # Create worktree
                console.print(f"[blue]📁 Creating worktree for {branch_name}...[/blue]")
                worktree_path = instance_manager.create_worktree(instance_id, branch_name)

                console.print(f"[green]✅ Worktree created at {worktree_path}[/green]")

                # Get environment variables for this instance
                instance_env_vars = instance_manager.get_instance_env_vars(
                    instance_id,
                    port_base,
                    worktree_path
                )

                console.print(
                    f"\n[green]🎯 Starting instance {instance_id} on port {port_base}[/green]"
                )
                console.print(f"[dim]   Environment: DOPEMUX_INSTANCE_ID={instance_id}[/dim]")
                console.print(f"[dim]   Workspace: {project_path}[/dim]")
                console.print(f"[dim]   Worktree: {worktree_path}[/dim]")

            else:
                console.print("[yellow]Cancelled. Continuing with single instance.[/yellow]")

        except RuntimeError as e:
            console.print(f"[red]❌ {str(e)}[/red]")
            sys.exit(1)

    else:
        # No running instances - use main worktree (Instance A)
        instance_id = 'A'
        port_base = 3000
        worktree_path = project_path

        instance_env_vars = instance_manager.get_instance_env_vars(
            instance_id,
            port_base,
            worktree_path
        )

        console.print("[blue]🆕 Starting first instance (A) on port 3000[/blue]")

    if not instance_id:
        instance_id = 'A'
    if not port_base:
        port_base = 3000
    if not worktree_path:
        worktree_path = project_path

    # Inject instance environment variables
    if instance_env_vars:
        for key, value in instance_env_vars.items():
            os.environ[key] = value

        console.print("[dim]✅ Instance environment variables configured[/dim]")

    litellm_proxy_info = None
    litellm_enabled = use_litellm or use_claude_router

    if litellm_enabled:
        if not os.environ.get("OPENAI_API_KEY"):
            console.print(
                "[red]❌ OPENAI_API_KEY not set. Required for LiteLLM proxy configuration.[/red]"
            )
            sys.exit(1)

        try:
            litellm_manager = LiteLLMProxyManager(project_path, instance_id, port_base)
            litellm_proxy_info = litellm_manager.ensure_started()
            env_updates = litellm_manager.build_client_env(litellm_proxy_info)
            for key, value in env_updates.items():
                os.environ[key] = value

            if litellm_proxy_info.already_running:
                console.print(
                    f"[green]✅ Reusing LiteLLM proxy at {litellm_proxy_info.base_url}[/green]"
                )
            else:
                console.print(
                    f"[green]✅ LiteLLM proxy ready at {litellm_proxy_info.base_url}[/green]"
                )
                console.print(
                    f"[dim]   Config: {litellm_proxy_info.config_path}[/dim]"
                )
                console.print(
                    f"[dim]   Logs: {litellm_proxy_info.log_path}[/dim]"
                )

        except LiteLLMProxyError as exc:
            console.print(f"[red]❌ LiteLLM proxy failed: {exc}[/red]")
            sys.exit(1)

    router_info = None
    if use_claude_router:
        provider_url = None
        provider_models: List[str] = []
        provider_name = os.environ.get("CLAUDE_CODE_ROUTER_PROVIDER")
        provider_key_env = os.environ.get(
            "CLAUDE_CODE_ROUTER_UPSTREAM_KEY_VAR",
            "DOPEMUX_LITELLM_MASTER_KEY" if litellm_proxy_info else None,
        )
        provider_key: Optional[str] = None

        if litellm_proxy_info:
            provider_url = f"{litellm_proxy_info.base_url}/v1/chat/completions"
            provider_name = provider_name or "litellm"
            # Use Claude Pro Max as primary, fallback to others on rate limit
            provider_models = ["claude-sonnet-4.5", "openai-gpt-5", "xai-grok-4"]
        else:
            provider_url = os.environ.get("CLAUDE_CODE_ROUTER_UPSTREAM_URL")
            models_env = os.environ.get("CLAUDE_CODE_ROUTER_MODELS", "")
            provider_models = [m.strip() for m in models_env.split(",") if m.strip()]
            if not provider_name:
                provider_name = os.environ.get("CLAUDE_CODE_ROUTER_PROVIDER", "custom")
            provider_key = os.environ.get("CLAUDE_CODE_ROUTER_UPSTREAM_KEY")

        if not provider_url:
            console.print(
                "[red]❌ Claude Code Router upstream URL is not configured.[/red]"
            )
            console.print(
                "[dim]Set CLAUDE_CODE_ROUTER_UPSTREAM_URL or enable --litellm.[/dim]"
            )
            sys.exit(1)

        if not provider_models:
            console.print(
                "[red]❌ No models configured for Claude Code Router upstream.[/red]"
            )
            console.print(
                "[dim]Set CLAUDE_CODE_ROUTER_MODELS or rely on --litellm defaults.[/dim]"
            )
            sys.exit(1)

        router_manager = ClaudeCodeRouterManager(project_path, instance_id, port_base)

        try:
            router_info = router_manager.ensure_started(
                provider_url=provider_url,
                provider_models=provider_models,
                provider_name=provider_name or "litellm",
                provider_key=provider_key,
                provider_key_env_var=provider_key_env,
            )
        except ClaudeCodeRouterError as exc:
            console.print(f"[red]❌ Claude Code Router failed: {exc}[/red]")
            sys.exit(1)

        router_env = router_manager.build_client_env(router_info)

        # CRITICAL: Save original ANTHROPIC_API_KEY before router overwrites it
        # The router's API key is only for router's internal use, NOT for MCP servers
        original_anthropic_key = os.environ.get("ANTHROPIC_API_KEY")

        os.environ.update(router_env)

        # CRITICAL: Restore original ANTHROPIC_API_KEY for MCP servers and Claude Code
        # MCP servers need the REAL Anthropic API key, not the router's key
        if original_anthropic_key:
            os.environ["ANTHROPIC_API_KEY"] = original_anthropic_key

        if router_info.already_running:
            console.print(
                f"[green]✅ Reusing Claude Code Router at {router_info.base_url}[/green]"
            )
        else:
            console.print(
                f"[green]✅ Claude Code Router ready at {router_info.base_url}[/green]"
            )
            console.print(f"[dim]   Config: {router_info.config_path}[/dim]")
            console.print(f"[dim]   Logs: {router_info.log_path}[/dim]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Restore context
        task = progress.add_task("Restoring context...", total=None)

        # Use worktree path for context if in multi-instance mode
        context_path = worktree_path if worktree_path else project_path
        context_manager = ContextManager(context_path)

        if session:
            context = context_manager.restore_session(session)
        else:
            context = context_manager.restore_latest()

        if context:
            progress.update(
                task,
                description=f"Restored session from {context.get('timestamp', 'unknown')}",
            )
            console.print(
                f"[green]📍 Welcome back! You were working on: {context.get('current_goal', 'Unknown task')}[/green]"
            )
        else:
            progress.update(task, description="Starting fresh session")
            console.print("[blue]🆕 Starting new session[/blue]")

        # Check if dangerous mode has expired
        _check_dangerous_mode_expiry()

        # Handle dangerous mode activation
        is_dangerous_mode = dangerous or dangerously_skip_permissions
        if is_dangerous_mode:
            progress.update(task, description="⚠️  Activating dangerous mode...")
            _activate_dangerous_mode()

        # Start MCP servers by default (ADHD-optimized experience)
        if not no_mcp:
            _start_mcp_servers_with_progress(project_path)
        else:
            console.print("[yellow]⚠️  Skipping MCP servers (reduced ADHD experience)[/yellow]")

        # Launch Claude Code
        progress.update(task, description="Launching Claude Code...")
        launcher = ClaudeLauncher(config_manager)
        claude_process = launcher.launch(
            project_path=project_path,
            background=background,
            debug=debug,
            context=context,
        )

        # Start attention monitoring
        progress.update(task, description="Starting attention monitoring...")
        attention_monitor = AttentionMonitor(project_path)
        attention_monitor.start_monitoring()

        progress.update(task, description="Ready! 🎯", completed=True)

    # Save instance state to ConPort for crash recovery
    if instance_id and port_base:
        from .instance_state import save_instance_state_sync, InstanceState
        from datetime import datetime

        # Get current git branch
        try:
            git_branch = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=str(worktree_path or project_path),
                capture_output=True,
                text=True,
                check=True
            ).stdout.strip()
        except:
            git_branch = "unknown"

        state = InstanceState(
            instance_id=instance_id,
            port_base=port_base,
            worktree_path=str(worktree_path or project_path),
            git_branch=git_branch,
            created_at=datetime.now(),
            last_active=datetime.now(),
            status="active",
            last_working_directory=str(worktree_path or project_path),
            last_focus_context=context.get('current_goal', 'New session') if context else 'New session'
        )

        save_instance_state_sync(
            state,
            workspace_id=str(project_path.resolve()),
            conport_port=3004  # Always save via instance A's ConPort
        )
        console.print("[dim]✅ Instance state saved for crash recovery[/dim]")

    if not background:
        console.print(
            "[green]✨ Claude Code is running with ADHD optimizations[/green]"
        )
        console.print("Press Ctrl+C to stop monitoring and save context")

        try:
            claude_process.wait()
        except KeyboardInterrupt:
            console.print("\n[yellow]⏸️ Saving context and stopping...[/yellow]")

            # Mark instance as stopped in ConPort
            if instance_id:
                from .instance_state import load_instance_state_sync, save_instance_state_sync
                from datetime import datetime

                workspace_id = str(project_path.resolve())
                state = load_instance_state_sync(instance_id, workspace_id, conport_port=3004)
                if state:
                    state.status = 'stopped'
                    state.last_active = datetime.now()
                    save_instance_state_sync(state, workspace_id, conport_port=3004)
                    console.print("[dim]✅ Instance marked as stopped[/dim]")

            ctx.invoke(save)
            attention_monitor.stop_monitoring()


@cli.command()
@click.option("--message", "-m", help="Save message/note")
@click.option("--force", "-f", is_flag=True, help="Force save even if no changes")
@click.pass_context
def save(ctx, message: Optional[str], force: bool):
    """
    💾 Save current development context

    Captures open files, cursor positions, mental model, and recent decisions
    for seamless restoration later.
    """
    project_path = Path.cwd()

    if not (project_path / ".dopemux").exists():
        console.print("[red]No Dopemux project found in current directory[/red]")
        sys.exit(1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Saving context...", total=None)

        context_manager = ContextManager(project_path)
        session_id = context_manager.save_context(message=message, force=force)

        progress.update(task, description="Context saved!", completed=True)

    console.print(f"[green]✅ Context saved (session: {session_id[:8]})[/green]")
    if message:
        console.print(f"[dim]Note: {message}[/dim]")


@cli.command()
@click.option("--session", "-s", help="Specific session ID to restore")
@click.option(
    "--list", "-l", "list_sessions", is_flag=True, help="List available sessions"
)
@click.pass_context
def restore(ctx, session: Optional[str], list_sessions: bool):
    """
    🔄 Restore previous development context

    Restores files, cursor positions, and mental model from a previous session.
    """
    project_path = Path.cwd()

    if not (project_path / ".dopemux").exists():
        console.print("[red]No Dopemux project found in current directory[/red]")
        sys.exit(1)

    context_manager = ContextManager(project_path)

    if list_sessions:
        sessions = context_manager.list_sessions()
        if not sessions:
            console.print("[yellow]No saved sessions found[/yellow]")
            return

        table = Table(title="Available Sessions")
        table.add_column("ID", style="cyan")
        table.add_column("Timestamp", style="green")
        table.add_column("Goal", style="yellow")
        table.add_column("Files", justify="right", style="blue")

        for s in sessions:
            table.add_row(
                s["id"][:8],
                s["timestamp"],
                s.get("current_goal", "No goal set")[:50],
                str(len(s.get("open_files", []))),
            )

        console.print(table)
        return

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Restoring context...", total=None)

        if session:
            context = context_manager.restore_session(session)
        else:
            context = context_manager.restore_latest()

        progress.update(task, description="Context restored!", completed=True)

    if context:
        console.print(
            f"[green]✅ Restored session from {context.get('timestamp', 'unknown')}[/green]"
        )
        console.print(
            f"[blue]🎯 Goal: {context.get('current_goal', 'No goal set')}[/blue]"
        )
        console.print(
            f"[yellow]📁 Files: {len(context.get('open_files', []))} files restored[/yellow]"
        )
    else:
        console.print("[red]❌ No context found to restore[/red]")


@cli.group()
def instances():
    """
    🏗️  Manage multiple Dopemux instances and worktrees

    Commands for managing parallel ADHD-optimized development workflows
    with isolated worktrees and shared database.
    """
    pass


@instances.command("list")
@click.pass_context
def instances_list(ctx):
    """
    📋 List all running instances and worktrees

    Shows currently active instances with their ports, branches, and paths.
    Automatically detects and reports orphaned instances (crashed).
    """
    project_path = Path.cwd()
    workspace_id = str(project_path.resolve())

    instance_manager = InstanceManager(project_path)
    running_instances = detect_instances_sync(project_path)

    # Detect orphaned instances (automatic crash detection)
    orphaned_instances = detect_orphaned_instances_sync(
        project_path,
        workspace_id,
        conport_port=3004  # Always query via instance A's ConPort
    )

    # Show running instances
    if running_instances:
        console.print(f"\n[green]✅ Found {len(running_instances)} running instance(s)[/green]\n")

        table = Table(title="Running Instances")
        table.add_column("Instance", style="cyan", no_wrap=True)
        table.add_column("Port", style="magenta", no_wrap=True)
        table.add_column("Branch", style="green")
        table.add_column("Worktree Path", style="dim")
        table.add_column("Status", style="blue")

        for inst in running_instances:
            status = "✅ Healthy" if inst.is_healthy else "⚠️  Unknown"
            table.add_row(
                inst.instance_id,
                str(inst.port_base),
                inst.git_branch or "unknown",
                str(inst.worktree_path) if inst.worktree_path else "main",
                status
            )

        console.print(table)
    else:
        console.print("[yellow]No running instances found[/yellow]")

    # Show orphaned instances (automatic crash detection)
    if orphaned_instances:
        console.print(f"\n[red]⚠️  Found {len(orphaned_instances)} orphaned instance(s)[/red]")
        console.print("[dim]Orphaned instances have crashed but their worktrees still exist[/dim]\n")

        orphan_table = Table(title="Orphaned Instances (Crashed)")
        orphan_table.add_column("Instance", style="red", no_wrap=True)
        orphan_table.add_column("Branch", style="yellow")
        orphan_table.add_column("Last Active", style="dim")
        orphan_table.add_column("Last Focus", style="cyan")
        orphan_table.add_column("Action", style="green")

        from datetime import datetime
        for orphan in orphaned_instances:
            # Calculate time since last active
            if isinstance(orphan['last_active'], str):
                last_active = datetime.fromisoformat(orphan['last_active'])
            else:
                last_active = orphan['last_active']

            time_diff = datetime.now() - last_active
            if time_diff.days > 0:
                time_ago = f"{time_diff.days}d ago"
            elif time_diff.seconds > 3600:
                time_ago = f"{time_diff.seconds // 3600}h ago"
            else:
                time_ago = f"{time_diff.seconds // 60}m ago"

            orphan_table.add_row(
                orphan['instance_id'],
                orphan['git_branch'],
                time_ago,
                orphan.get('last_focus_context', 'N/A')[:40] or "N/A",
                f"dopemux instances resume {orphan['instance_id']}"
            )

        console.print(orphan_table)
        console.print("\n[dim]💡 Tip: Use 'dopemux instances resume <id>' to restart an orphaned instance[/dim]")
        console.print("[dim]     Or use 'dopemux instances cleanup <id>' to remove the worktree[/dim]")

    # Show git worktrees
    console.print("\n[bold]Git Worktrees:[/bold]")
    worktrees = instance_manager.list_worktrees()

    if worktrees:
        worktree_table = Table()
        worktree_table.add_column("ID", style="cyan")
        worktree_table.add_column("Path", style="dim")
        worktree_table.add_column("Branch", style="green")

        for wt_id, wt_path, wt_branch in worktrees:
            worktree_table.add_row(wt_id, str(wt_path), wt_branch)

        console.print(worktree_table)
    else:
        console.print("[dim]No worktrees found[/dim]")


@instances.command("resume")
@click.argument("instance_id")
@click.option("--restore-context", "-r", is_flag=True, help="Restore working directory and focus context")
@click.pass_context
def instances_resume(ctx, instance_id: str, restore_context: bool):
    """
    🔄 Resume an orphaned instance (one-click crash recovery)

    Restarts services for an orphaned instance, optionally restoring
    the last working directory and focus context.

    \b
    Examples:
        dopemux instances resume B              # Restart instance B
        dopemux instances resume B --restore-context  # Restart and restore context

    \b
    ADHD Benefit:
        Zero-friction recovery from crashes. Resume exactly where you left off
        with preserved mental model and context continuity.
    """
    project_path = Path.cwd()
    workspace_id = str(project_path.resolve())

    # Load orphaned instance state
    from .instance_state import load_instance_state_sync

    state = load_instance_state_sync(instance_id, workspace_id, conport_port=3004)

    if not state:
        console.print(f"[red]❌ No saved state found for instance {instance_id}[/red]")
        console.print("[dim]Tip: Use 'dopemux instances list' to see available instances[/dim]")
        sys.exit(1)

    if state.status != 'orphaned':
        console.print(f"[yellow]⚠️  Instance {instance_id} is not orphaned (status: {state.status})[/yellow]")
        if state.status == 'active':
            console.print(f"[dim]Instance is already running on port {state.port_base}[/dim]")
        sys.exit(1)

    # Check if worktree still exists
    worktree_path = Path(state.worktree_path)
    if not worktree_path.exists():
        console.print(f"[red]❌ Worktree not found at {worktree_path}[/red]")
        console.print("[dim]The worktree may have been deleted. Use 'dopemux instances cleanup' to remove state[/dim]")
        sys.exit(1)

    console.print(f"\n[cyan]🔄 Resuming instance {instance_id}...[/cyan]")
    console.print(f"   Branch: {state.git_branch}")
    console.print(f"   Worktree: {worktree_path}")
    console.print(f"   Port base: {state.port_base}")

    if state.last_focus_context:
        console.print(f"   Last focus: [dim]{state.last_focus_context}[/dim]")

    # Show context restoration info
    if restore_context and state.last_working_directory:
        console.print(f"\n[green]✨ Context restoration enabled:[/green]")
        console.print(f"   Working directory: {state.last_working_directory}")
        if state.last_focus_context:
            console.print(f"   Focus context: {state.last_focus_context}")

    # Start instance
    console.print(f"\n[yellow]💡 Starting instance {instance_id} on port {state.port_base}...[/yellow]")

    # Set environment variables for this process
    env = os.environ.copy()
    env.update({
        "DOPEMUX_INSTANCE_ID": instance_id,
        "DOPEMUX_WORKSPACE_ID": workspace_id,
        "DOPEMUX_PORT_BASE": str(state.port_base),
        "TASK_MASTER_PORT": str(state.port_base + 5),
        "SERENA_PORT": str(state.port_base + 6),
        "CONPORT_PORT": str(state.port_base + 7),
        "INTEGRATION_BRIDGE_PORT": str(state.port_base + 16),
    })

    # Change to worktree directory if restoring context
    original_cwd = os.getcwd()
    if restore_context and state.last_working_directory:
        try:
            os.chdir(state.last_working_directory)
            console.print(f"[green]✅ Changed to working directory: {state.last_working_directory}[/green]")
        except Exception as e:
            console.print(f"[yellow]⚠️  Could not change to working directory: {e}[/yellow]")
            console.print("[dim]Staying in current directory[/dim]")

    console.print(f"\n[green]✅ Instance {instance_id} resumed successfully![/green]")
    console.print(f"[dim]Services are starting on port {state.port_base}...[/dim]")

    if restore_context:
        console.print("\n[cyan]📍 Context Restored:[/cyan]")
        console.print(f"   You were working on: {state.last_focus_context or 'N/A'}")
        console.print(f"   In directory: {os.getcwd()}")

    console.print(f"\n[dim]💡 Tip: Instance will be marked as 'active' when dopemux start completes[/dim]")
    console.print(f"[dim]     Run: cd {worktree_path} && dopemux start[/dim]")

    # Mark as active (optimistic - actual start command will confirm)
    from .instance_state import save_instance_state_sync
    state.status = 'active'
    from datetime import datetime
    state.last_active = datetime.now()
    save_instance_state_sync(state, workspace_id, conport_port=3004)


@instances.command("cleanup")
@click.argument("instance_id", required=False)
@click.option("--all", "-a", is_flag=True, help="Clean up all stopped instances")
@click.option("--force", "-f", is_flag=True, help="Force cleanup without confirmation")
@click.pass_context
def instances_cleanup(ctx, instance_id: Optional[str], all: bool, force: bool):
    """
    🧹 Clean up stopped instance worktrees

    Removes git worktrees for stopped instances to free up disk space.

    \b
    Examples:
        dopemux instances cleanup B          # Remove instance B worktree
        dopemux instances cleanup --all      # Remove all stopped instances
    """
    project_path = Path.cwd()
    instance_manager = InstanceManager(project_path)

    if not instance_id and not all:
        console.print("[red]❌ Specify instance ID or use --all flag[/red]")
        console.print("[dim]Usage: dopemux instances cleanup <ID> or --all[/dim]")
        sys.exit(1)

    if all:
        # Get all worktrees
        worktrees = instance_manager.list_worktrees()
        running_instances = detect_instances_sync(project_path)
        running_ids = {inst.instance_id for inst in running_instances}

        # Find stopped instances
        stopped_instances = [
            (wt_id, wt_path) for wt_id, wt_path, _ in worktrees
            if wt_id not in running_ids and wt_id != 'A'
        ]

        if not stopped_instances:
            console.print("[green]✅ No stopped instances to clean up[/green]")
            return

        console.print(f"\n[yellow]⚠️  Found {len(stopped_instances)} stopped instance(s) to clean:[/yellow]")
        for wt_id, wt_path in stopped_instances:
            console.print(f"  • Instance {wt_id}: {wt_path}")

        if not force and not click.confirm("\nProceed with cleanup?"):
            console.print("[yellow]Cleanup cancelled[/yellow]")
            return

        # Clean up each stopped instance
        from .instance_state import cleanup_instance_state_sync
        workspace_id = str(project_path.resolve())

        for wt_id, _ in stopped_instances:
            if instance_manager.cleanup_worktree(wt_id):
                console.print(f"[green]✅ Removed worktree for instance {wt_id}[/green]")

                # Also remove instance state from ConPort
                if cleanup_instance_state_sync(wt_id, workspace_id, conport_port=3004):
                    console.print(f"[dim]✅ Removed instance state for {wt_id}[/dim]")
            else:
                console.print(f"[red]❌ Failed to remove worktree for instance {wt_id}[/red]")

    else:
        # Clean up specific instance
        if instance_id == 'A':
            console.print("[red]❌ Cannot clean up main worktree (instance A)[/red]")
            sys.exit(1)

        # Check if instance is running
        running_instances = detect_instances_sync(project_path)
        if any(inst.instance_id == instance_id for inst in running_instances):
            console.print(f"[red]❌ Instance {instance_id} is still running[/red]")
            console.print("[dim]Stop the instance before cleaning up its worktree[/dim]")
            sys.exit(1)

        worktree_path = instance_manager._get_worktree_path(instance_id)
        if not worktree_path or not worktree_path.exists():
            console.print(f"[yellow]⚠️  No worktree found for instance {instance_id}[/yellow]")
            return

        console.print(f"\n[yellow]⚠️  Removing worktree for instance {instance_id}[/yellow]")
        console.print(f"[dim]Path: {worktree_path}[/dim]")

        if not force and not click.confirm("Proceed?"):
            console.print("[yellow]Cleanup cancelled[/yellow]")
            return

        if instance_manager.cleanup_worktree(instance_id):
            console.print(f"[green]✅ Removed worktree for instance {instance_id}[/green]")

            # Also remove instance state from ConPort
            from .instance_state import cleanup_instance_state_sync
            workspace_id = str(project_path.resolve())

            if cleanup_instance_state_sync(instance_id, workspace_id, conport_port=3004):
                console.print(f"[dim]✅ Removed instance state from ConPort[/dim]")
        else:
            console.print(f"[red]❌ Failed to remove worktree for instance {instance_id}[/red]")


@cli.command()
@click.option("--attention", "-a", is_flag=True, help="Show attention metrics")
@click.option("--context", "-c", is_flag=True, help="Show context information")
@click.option("--tasks", "-t", is_flag=True, help="Show task progress")
@click.pass_context
def status(ctx, attention: bool, context: bool, tasks: bool):
    """
    📊 Show current session status and metrics

    Displays attention state, context information, task progress, and
    ADHD accommodation effectiveness.
    """
    project_path = Path.cwd()

    if not (project_path / ".dopemux").exists():
        console.print("[red]No Dopemux project found in current directory[/red]")
        sys.exit(1)

    # Show all by default if no specific flags
    if not any([attention, context, tasks]):
        attention = context = tasks = True

    if attention:
        monitor = AttentionMonitor(project_path)
        metrics = monitor.get_current_metrics()

        table = Table(title="🧠 Attention Metrics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        table.add_column("Status", style="yellow")

        table.add_row(
            "Current State",
            metrics.get("attention_state", "unknown"),
            _get_attention_emoji(metrics.get("attention_state")),
        )
        table.add_row(
            "Session Duration", f"{metrics.get('session_duration', 0):.1f} min", "⏱️"
        )
        table.add_row("Focus Score", f"{metrics.get('focus_score', 0):.1%}", "🎯")
        table.add_row("Context Switches", str(metrics.get("context_switches", 0)), "🔄")

        console.print(table)

    if context:
        context_manager = ContextManager(project_path)
        current_context = context_manager.get_current_context()

        table = Table(title="📍 Context Information")
        table.add_column("Item", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Current Goal", current_context.get("current_goal", "Not set"))
        table.add_row("Open Files", str(len(current_context.get("open_files", []))))
        table.add_row("Last Save", current_context.get("last_save", "Never"))
        table.add_row("Git Branch", current_context.get("git_branch", "unknown"))

        console.print(table)

    if tasks:
        decomposer = TaskDecomposer(project_path)
        progress_info = decomposer.get_progress()

        if progress_info:
            table = Table(title="📋 Task Progress")
            table.add_column("Task", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Progress", style="yellow")

            for task in progress_info.get("tasks", []):
                status_emoji = (
                    "✅" if task["completed"] else "🔄" if task["in_progress"] else "⏳"
                )
                table.add_row(
                    task["name"], status_emoji, f"{task.get('progress', 0):.0%}"
                )

            console.print(table)
        else:
            console.print("[yellow]No active tasks found[/yellow]")


@cli.command()
@click.argument("description", required=False)
@click.option("--duration", "-d", type=int, default=25, help="Task duration in minutes")
@click.option(
    "--priority", "-p", type=click.Choice(["low", "medium", "high"]), default="medium"
)
@click.option("--list", "-l", "list_tasks", is_flag=True, help="List current tasks")
@click.pass_context
def task(
    ctx, description: Optional[str], duration: int, priority: str, list_tasks: bool
):
    """
    📋 DEPRECATED - Use SuperClaude /dx: commands instead

    This command has been replaced by:
    - /dx:implement - Start ADHD-optimized implementation session
    - /dx:session start/end/break - Session management
    - /dx:load - Load tasks from ConPort
    - /dx:stats - View ADHD metrics and progress

    See: docs/90-adr/ADR-XXXX-path-c-migration.md
    """
    console.print("[yellow]" + "="*60 + "[/yellow]")
    console.print("[red]⚠️  DEPRECATED COMMAND[/red]")
    console.print("[yellow]" + "="*60 + "[/yellow]")
    console.print()
    console.print("The 'dopemux task' command has been replaced by SuperClaude /dx: commands:")
    console.print()
    console.print("  [cyan]/dx:implement[/cyan] - Start ADHD-optimized implementation session")
    console.print("  [cyan]/dx:session start[/cyan] - Begin work session")
    console.print("  [cyan]/dx:load[/cyan] - Load tasks from ConPort")
    console.print("  [cyan]/dx:stats[/cyan] - View ADHD metrics and progress")
    console.print()
    console.print("Migration completed: October 2025")
    console.print("See: [blue]docs/90-adr/ADR-XXXX-path-c-migration.md[/blue]")
    console.print()
    console.print("[yellow]" + "="*60 + "[/yellow]")
    sys.exit(0)

    if list_tasks:
        tasks = decomposer.list_tasks()
        if not tasks:
            console.print("[yellow]No tasks found[/yellow]")
            return

        table = Table(title="Current Tasks")
        table.add_column("Task", style="cyan")
        table.add_column("Priority", style="yellow")
        table.add_column("Duration", style="green")
        table.add_column("Status", style="blue")

        for task in tasks:
            status = (
                "✅ Complete"
                if task.get("status") == "completed"
                else (
                    "🔄 In Progress"
                    if task.get("status") == "in_progress"
                    else "⏳ Pending"
                )
            )
            table.add_row(
                task["description"],
                task["priority"],
                f"{task['estimated_duration']}m",
                status,
            )

        console.print(table)
        return

    # Check if description is provided for adding new task
    if not description:
        console.print("[red]Description required when not listing tasks[/red]")
        console.print("Use 'dopemux task --list' to list current tasks")
        sys.exit(1)

    # Add new task
    task_id = decomposer.add_task(
        description=description, duration=duration, priority=priority
    )

    console.print(f"[green]✅ Task added: {description}[/green]")
    console.print(f"[blue]🆔 ID: {task_id}[/blue]")
    console.print(f"[yellow]⏱️ Duration: {duration} minutes[/yellow]")
    console.print(f"[cyan]🎯 Priority: {priority}[/cyan]")


@cli.group()
@click.pass_context
def autoresponder(ctx):
    """
    🤖 Manage Claude Auto Responder integration

    Automatic confirmation responses for Claude Code prompts with
    ADHD-optimized controls and attention-aware features.
    """


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
    config_manager = ctx.obj["config_manager"]
    project_path = Path.cwd()

    if not (project_path / ".dopemux").exists():
        console.print("[red]No Dopemux project found in current directory[/red]")
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
            console.print("[green]✅ Claude Auto Responder is now active[/green]")
            console.print(
                "[blue]🎯 Monitoring for Claude Code confirmation prompts[/blue]"
            )

            config = config_manager.get_claude_autoresponder_config()
            console.print(f"[yellow]📡 Scope: {config.terminal_scope}[/yellow]")
            if config.response_delay > 0:
                console.print(f"[cyan]⏱️ Delay: {config.response_delay}s[/cyan]")
            console.print(
                f"[dim]💤 Auto-stop after {config.timeout_minutes} minutes of inactivity[/dim]"
            )
        else:
            progress.update(task, description="Failed to start", completed=True)
            console.print("[red]❌ Failed to start auto responder[/red]")
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
    config_manager = ctx.obj["config_manager"]
    project_path = Path.cwd()

    if not (project_path / ".dopemux").exists():
        console.print("[red]No Dopemux project found in current directory[/red]")
        sys.exit(1)

    from integrations.claude_autoresponder import create_autoresponder_manager

    autoresponder_manager = create_autoresponder_manager(config_manager, project_path)

    if not autoresponder_manager.is_running():
        console.print("[yellow]Auto responder is not running[/yellow]")
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
            console.print("[green]✅ Claude Auto Responder stopped[/green]")

            # Show session stats
            console.print(f"[blue]📊 Session Statistics:[/blue]")
            console.print(f"  ⏱️ Uptime: {status['uptime_minutes']:.1f} minutes")
            console.print(f"  ✅ Responses sent: {status['responses_sent']}")
            if status["responses_sent"] > 0:
                console.print(
                    f"  📈 Rate: {status['responses_per_minute']:.1f} responses/min"
                )
        else:
            progress.update(task, description="Error stopping", completed=True)
            console.print("[red]❌ Error stopping auto responder[/red]")


@autoresponder.command("status")
@click.pass_context
def autoresponder_status(ctx):
    """
    📊 Show auto responder status

    Displays current status, configuration, and performance metrics.
    """
    config_manager = ctx.obj["config_manager"]
    project_path = Path.cwd()

    if not (project_path / ".dopemux").exists():
        console.print("[red]No Dopemux project found in current directory[/red]")
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

    console.print(table)

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

    console.print(config_table)


@autoresponder.command("setup")
@click.pass_context
def autoresponder_setup(ctx):
    """
    🔧 Setup Claude Auto Responder

    Downloads and configures the ClaudeAutoResponder tool for use with Dopemux.
    """
    config_manager = ctx.obj["config_manager"]
    project_path = Path.cwd()

    if not (project_path / ".dopemux").exists():
        console.print("[red]No Dopemux project found in current directory[/red]")
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
            console.print("[green]✅ ClaudeAutoResponder setup complete[/green]")
            console.print("[blue]🚀 Run 'dopemux autoresponder start' to begin[/blue]")
        else:
            progress.update(task, description="Setup failed", completed=True)
            console.print("[red]❌ Setup failed[/red]")
            console.print("[yellow]Check logs for details[/yellow]")
            sys.exit(1)


@cli.group()
@click.pass_context
def extract(ctx):
    """
    📄 Document extraction with ADHD-optimized patterns

    Extract entities, configurations, and patterns from documentation
    using specialized extractors for markdown, YAML, and ADHD content.
    """
    pass


@extract.command("docs")
@click.argument("directory", default=".")
@click.option(
    "--mode", "-m",
    type=click.Choice(["basic", "detailed", "adhd"]),
    default="basic",
    help="Extraction mode: basic (key-value), detailed (all patterns), adhd (ADHD-specific)"
)
@click.option(
    "--format", "-f",
    type=click.Choice(["json", "csv", "markdown", "yaml"]),
    default="json",
    help="Output format for extracted entities"
)
@click.option("--output", "-o", help="Output file path (default: print to stdout)")
@click.option("--confidence", "-c", type=float, default=0.5, help="Minimum confidence threshold (0.0-1.0)")
@click.option("--extensions", help="File extensions to process (default: .md,.yaml,.yml)")
@click.option("--adhd-profile", "-p", is_flag=True, help="Extract ADHD accommodation profile")
@click.pass_context
def extract_docs(
    ctx,
    directory: str,
    mode: str,
    format: str,
    output: Optional[str],
    confidence: float,
    extensions: Optional[str],
    adhd_profile: bool
):
    """
    📄 Extract entities from documentation files

    Process markdown and YAML files to extract structured information
    using ADHD-optimized patterns and confidence scoring.
    """
    from pathlib import Path
    import sys
    import json
    import csv
    from io import StringIO

    # Add extraction package to path
    sys.path.append(str(Path(__file__).parent.parent.parent / "extraction"))

    try:
        from document_classifier import DocumentClassifier, extract_from_directory
    except ImportError as e:
        console.print(f"[red]❌ Could not import extraction modules: {e}[/red]")
        console.print("[yellow]💡 Make sure you're in the dopemux-mvp directory[/yellow]")
        sys.exit(1)

    source_path = Path(directory).resolve()
    if not source_path.exists():
        console.print(f"[red]❌ Directory does not exist: {source_path}[/red]")
        sys.exit(1)

    # Set default extensions if not provided
    if not extensions:
        extensions = ".md,.yaml,.yml,.json"

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Extracting entities in {mode} mode...", total=None)

        try:
            # Use the unified extraction function
            results = extract_from_directory(str(source_path))

            progress.update(task, description="Processing results...", total=None)

            # Filter by confidence
            filtered_entities = {}
            total_entities = 0
            filtered_count = 0

            for entity_type, entity_list in results.get('all_entities', {}).items():
                filtered_list = []
                for entity in entity_list:
                    total_entities += 1
                    entity_confidence = entity.get('confidence', 0.0)
                    if entity_confidence >= confidence:
                        filtered_list.append(entity)
                        filtered_count += 1

                if filtered_list:
                    filtered_entities[entity_type] = filtered_list

            # Apply mode filtering
            if mode == "basic":
                # Keep only essential patterns: headers, key-value pairs, basic settings
                basic_types = ['section_header', 'project_metadata', 'yaml_properties', 'markdown_headers']
                filtered_entities = {k: v for k, v in filtered_entities.items() if k in basic_types}
            elif mode == "adhd":
                # Keep only ADHD-related patterns
                adhd_keywords = ['adhd', 'focus', 'break', 'attention', 'cognitive', 'accommodation']
                adhd_types = [k for k in filtered_entities.keys()
                             if any(keyword in k.lower() for keyword in adhd_keywords)]
                filtered_entities = {k: v for k, v in filtered_entities.items() if k in adhd_types}
            # mode == "detailed" keeps everything

            progress.update(task, description="Formatting output...", total=None)

            # Format output
            output_data = {
                'extraction_summary': {
                    'mode': mode,
                    'source_directory': str(source_path),
                    'documents_processed': results.get('documents_processed', 0),
                    'total_entities_found': total_entities,
                    'entities_above_threshold': filtered_count,
                    'confidence_threshold': confidence,
                    'entity_types': list(filtered_entities.keys())
                },
                'entities': filtered_entities
            }

            # Add ADHD profile if requested
            if adhd_profile and results.get('metadata', {}).get('adhd_documents'):
                sys.path.append(str(Path(__file__).parent.parent.parent / "extraction"))
                from adhd_entities import ADHDEntityExtractor

                extractor = ADHDEntityExtractor()
                # Get content from first ADHD document for profile
                for doc_info in results.get('document_types', {}).get('markdown', []):
                    if doc_info['filename'] in results['metadata']['adhd_documents']:
                        # This is simplified - in a real implementation we'd need the content
                        output_data['adhd_profile'] = {
                            'accommodation_categories': ['attention_management', 'energy_management'],
                            'confidence_note': 'Profile extraction requires document content access'
                        }
                        break

            progress.update(task, description="Complete! ✅", completed=True)

        except Exception as e:
            progress.update(task, description="Error occurred", completed=True)
            console.print(f"[red]❌ Extraction failed: {e}[/red]")
            if ctx.obj.get("verbose"):
                import traceback
                traceback.print_exc()
            sys.exit(1)

    # Output results
    if format == "json":
        output_text = json.dumps(output_data, indent=2, ensure_ascii=False)
    elif format == "yaml":
        try:
            import yaml
            output_text = yaml.dump(output_data, default_flow_style=False, allow_unicode=True)
        except ImportError:
            console.print("[yellow]⚠️ PyYAML not available, falling back to JSON[/yellow]")
            output_text = json.dumps(output_data, indent=2, ensure_ascii=False)
    elif format == "csv":
        # Flatten entities for CSV
        output_buffer = StringIO()
        writer = csv.writer(output_buffer)
        writer.writerow(['entity_type', 'content', 'value', 'confidence', 'source_file'])

        for entity_type, entity_list in filtered_entities.items():
            for entity in entity_list:
                writer.writerow([
                    entity_type,
                    entity.get('content', ''),
                    entity.get('value', ''),
                    entity.get('confidence', 0.0),
                    entity.get('source_file', '')
                ])
        output_text = output_buffer.getvalue()
    elif format == "markdown":
        lines = [f"# Extraction Results - {mode.title()} Mode\n"]
        lines.append(f"**Source**: {source_path}")
        lines.append(f"**Documents**: {output_data['extraction_summary']['documents_processed']}")
        lines.append(f"**Entities**: {filtered_count}/{total_entities} (confidence ≥ {confidence})\n")

        for entity_type, entity_list in filtered_entities.items():
            lines.append(f"## {entity_type.replace('_', ' ').title()}\n")
            for entity in entity_list:
                lines.append(f"- **{entity.get('content', 'N/A')}**")
                if entity.get('value'):
                    lines.append(f": {entity['value']}")
                lines.append(f" _(confidence: {entity.get('confidence', 0.0):.2f})_")
                lines.append("")

        output_text = "\n".join(lines)

    # Write or print output
    if output:
        output_path = Path(output)
        output_path.write_text(output_text, encoding='utf-8')
        console.print(f"[green]✅ Results written to {output_path}[/green]")
    else:
        console.print(output_text)

    # Show summary
    console.print(
        Panel(
            f"🎯 Extraction Summary:\n\n"
            f"• Mode: {mode}\n"
            f"• Documents: {results.get('documents_processed', 0)}\n"
            f"• Entities: {filtered_count}/{total_entities}\n"
            f"• Entity types: {len(filtered_entities)}\n"
            f"• Format: {format}",
            title="📊 Results",
            border_style="green",
        )
    )


@extract.command("pipeline")
@click.argument("directory", default=".")
@click.option("--output", "-o", help="Output directory for pipeline results", default="./output")
@click.option(
    "--adhd/--no-adhd",
    default=True,
    help="Enable/disable ADHD-specific extraction patterns"
)
@click.option(
    "--multi-angle/--no-multi-angle",
    default=True,
    help="Enable/disable multi-angle entity extraction"
)
@click.option(
    "--embeddings/--no-embeddings",
    default=True,
    help="Enable/disable vector embedding generation"
)
@click.option(
    "--tsv/--no-tsv",
    default=True,
    help="Enable/disable TSV registry generation"
)
@click.option(
    "--confidence", "-c",
    type=float,
    default=0.5,
    help="Minimum confidence threshold for entities (0.0-1.0)"
)
@click.option(
    "--embedding-model", "-m",
    default="voyage-context-3",
    help="Embedding model to use"
)
@click.option("--milvus-uri", help="Milvus database URI for vector storage")
@click.option("--extensions", help="File extensions to process (default: .md,.yaml,.yml,.json,.txt)")
@click.option(
    "--format", "-f",
    type=click.Choice(["json", "csv", "markdown"]),
    default="json",
    help="Output format for extraction results"
)
@click.option(
    "--synthesis/--no-synthesis",
    default=True,
    help="Enable/disable document synthesis generation"
)
@click.option(
    "--synthesis-types",
    multiple=True,
    type=click.Choice(["executive", "adhd", "technical", "all"]),
    default=["executive", "adhd"],
    help="Types of synthesis to generate (can specify multiple)"
)
@click.option(
    "--synthesis-format",
    type=click.Choice(["markdown", "json", "both"]),
    default="markdown",
    help="Output format for synthesis results"
)
@click.pass_context
def extract_pipeline(
    ctx,
    directory: str,
    output: str,
    adhd: bool,
    multi_angle: bool,
    embeddings: bool,
    tsv: bool,
    confidence: float,
    embedding_model: str,
    milvus_uri: Optional[str],
    extensions: Optional[str],
    format: str,
    synthesis: bool,
    synthesis_types: tuple,
    synthesis_format: str
):
    """
    🚀 Complete document processing pipeline

    Run the full unified pipeline including multi-layer extraction,
    atomic unit normalization, TSV registry generation, and vector
    embeddings. Integrates all extraction systems into a single workflow.
    """
    from pathlib import Path
    import sys

    # Import the unified pipeline
    try:
        from .extraction import UnifiedDocumentPipeline, PipelineConfig
    except ImportError as e:
        console.print(f"[red]❌ Could not import pipeline modules: {e}[/red]")
        console.print("[yellow]💡 Make sure the extraction package is properly installed[/yellow]")
        sys.exit(1)

    source_path = Path(directory).resolve()
    output_path = Path(output).resolve()

    if not source_path.exists():
        console.print(f"[red]❌ Source directory does not exist: {source_path}[/red]")
        sys.exit(1)

    # Parse extensions
    file_extensions = None
    if extensions:
        file_extensions = [ext.strip() for ext in extensions.split(',')]
        if not all(ext.startswith('.') for ext in file_extensions):
            file_extensions = ['.' + ext.lstrip('.') for ext in file_extensions]

    # Process synthesis types
    synthesis_types_list = list(synthesis_types)
    if "all" in synthesis_types_list:
        synthesis_types_list = ["executive", "adhd", "technical"]

    # Create pipeline configuration
    config = PipelineConfig(
        source_directory=source_path,
        output_directory=output_path,
        enable_adhd_extraction=adhd,
        enable_multi_angle=multi_angle,
        file_extensions=file_extensions,
        confidence_threshold=confidence,
        generate_tsv_registries=tsv,
        generate_embeddings=embeddings,
        embedding_model=embedding_model,
        milvus_uri=milvus_uri,
        export_json=(format == "json"),
        export_csv=(format == "csv"),
        export_markdown=(format == "markdown"),
        enable_synthesis=synthesis,
        synthesis_types=synthesis_types_list,
        synthesis_format=synthesis_format
    )

    console.print(f"[blue]🚀 Starting unified document pipeline...[/blue]")
    console.print(f"[blue]📁 Source: {source_path}[/blue]")
    console.print(f"[blue]📤 Output: {output_path}[/blue]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Initializing pipeline...", total=None)

        try:
            # Create and run pipeline
            pipeline = UnifiedDocumentPipeline(config)
            result = pipeline.process_documents()

            if result.success:
                progress.update(task, description="Pipeline completed successfully! ✅", completed=True)

                # Show detailed results
                console.print(
                    Panel(
                        f"🎯 Pipeline Results:\n\n"
                        f"• Processing time: {result.processing_time:.2f}s\n"
                        f"• Documents processed: {result.document_count}\n"
                        f"• Total entities extracted: {result.total_entities}\n"
                        f"• TSV registries: {len(result.registry_files or {})}\n"
                        f"• Vector embeddings: {result.vector_count}\n"
                        f"• Output files: {len(result.output_files or [])}\n\n"
                        f"📊 Configuration:\n"
                        f"• ADHD extraction: {'✅' if adhd else '❌'}\n"
                        f"• Multi-angle extraction: {'✅' if multi_angle else '❌'}\n"
                        f"• TSV registries: {'✅' if tsv else '❌'}\n"
                        f"• Vector embeddings: {'✅' if embeddings else '❌'}\n"
                        f"• Confidence threshold: {confidence}",
                        title="🚀 Pipeline Complete",
                        border_style="green",
                    )
                )

                # Show output files
                if result.output_files:
                    console.print("\n[green]📤 Generated files:[/green]")
                    for file_path in result.output_files:
                        console.print(f"  • {file_path}")

                # Show registry files
                if result.registry_files:
                    console.print("\n[green]📊 TSV registries:[/green]")
                    for name, path in result.registry_files.items():
                        count = result.registry_counts.get(name, 0) if result.registry_counts else 0
                        console.print(f"  • {name}: {path} ({count} entries)")

                # Show embedding summary
                if result.embedding_summary:
                    console.print(f"\n[green]🔍 Embeddings:[/green]")
                    console.print(f"  • Model: {result.embedding_summary.get('model', 'N/A')}")
                    console.print(f"  • Vectors: {result.vector_count}")

            else:
                progress.update(task, description="Pipeline failed ❌", completed=True)
                console.print(f"[red]❌ Pipeline failed: {result.error_message}[/red]")
                sys.exit(1)

        except Exception as e:
            progress.update(task, description="Error occurred", completed=True)
            console.print(f"[red]❌ Pipeline execution failed: {e}[/red]")
            if ctx.obj.get("verbose"):
                import traceback
                traceback.print_exc()
            sys.exit(1)


@extract.command("cleanup")
@click.argument("directory", default=".")
@click.option(
    "--dry-run/--execute",
    default=True,
    help="Preview cleanup without removing files (default: dry-run)"
)
@click.option(
    "--cleanup-types",
    multiple=True,
    type=click.Choice(["temporary", "cache", "outputs", "interim", "all"]),
    default=["temporary", "cache", "interim"],
    help="Types of files to clean (can specify multiple)"
)
@click.option(
    "--include-outputs/--preserve-outputs",
    default=False,
    help="Include output files in cleanup (default: preserve)"
)
@click.option(
    "--report-format",
    type=click.Choice(["table", "json", "detailed"]),
    default="detailed",
    help="Format for cleanup report"
)
@click.option("--report-file", help="Save cleanup report to file")
@click.pass_context
def extract_cleanup(
    ctx,
    directory: str,
    dry_run: bool,
    cleanup_types: tuple,
    include_outputs: bool,
    report_format: str,
    report_file: Optional[str]
):
    """
    🧹 Clean pipeline files and generate activity report

    Remove temporary, cache, and interim files created during pipeline processing.
    Provides detailed reporting on files removed, created, changed, and output.

    Default behavior preserves output files and runs in dry-run mode for safety.
    """
    from pathlib import Path
    import sys
    import json
    from datetime import datetime

    # Import cleanup modules
    try:
        from .extraction.cleanup import PipelineCleanup, CleanupConfig
    except ImportError as e:
        console.print(f"[red]❌ Could not import cleanup modules: {e}[/red]")
        console.print("[yellow]💡 Make sure the extraction package is properly installed[/yellow]")
        sys.exit(1)

    target_path = Path(directory).resolve()

    if not target_path.exists():
        console.print(f"[red]❌ Target directory does not exist: {target_path}[/red]")
        sys.exit(1)

    # Configure cleanup
    cleanup_types_list = list(cleanup_types)
    if "all" in cleanup_types_list:
        cleanup_types_list = ["temporary", "cache", "outputs", "interim"]
    elif include_outputs and "outputs" not in cleanup_types_list:
        cleanup_types_list.append("outputs")

    config = CleanupConfig(
        cleanup_types=cleanup_types_list,
        dry_run=dry_run,
        preserve_recent_hours=0,  # Clean all matching files
        include_hidden=False,
        backup_before_delete=False  # For safety in dry-run mode
    )

    console.print(f"[blue]🧹 {'Previewing' if dry_run else 'Executing'} pipeline cleanup...[/blue]")
    console.print(f"[blue]📁 Target: {target_path}[/blue]")
    console.print(f"[blue]🎯 Cleanup types: {', '.join(cleanup_types_list)}[/blue]")

    if dry_run:
        console.print("[yellow]⚠️  DRY RUN: No files will actually be removed[/yellow]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Scanning for cleanup candidates...", total=None)

        try:
            # Create cleanup system and generate mock activity report
            cleanup = PipelineCleanup(config)

            # For cleanup command, we simulate an activity report for the target directory
            mock_activity_report = {
                "operation_summary": {
                    "start_time": datetime.now().isoformat(),
                    "end_time": datetime.now().isoformat(),
                    "total_operations": 0,
                    "directories_scanned": [str(target_path)]
                },
                "file_operations": {
                    "created": [],
                    "modified": [],
                    "deleted": [],
                    "moved": []
                },
                "size_tracking": {
                    "total_bytes_created": 0,
                    "total_bytes_modified": 0,
                    "total_bytes_deleted": 0
                },
                "categorization": {
                    "by_extension": {},
                    "by_operation": {},
                    "by_directory": {}
                }
            }

            progress.update(task, description="Performing cleanup analysis...")

            # Perform cleanup
            result = cleanup.cleanup_pipeline_files(mock_activity_report, target_path)

            if result.success:
                progress.update(task, description=f"Cleanup {'preview' if dry_run else 'execution'} completed! ✅", completed=True)

                # Generate detailed report
                if report_format == "detailed":
                    console.print(
                        Panel(
                            f"🧹 Cleanup Results:\n\n"
                            f"• Files removed: {result.files_removed}\n"
                            f"• Space freed: {result.space_freed / (1024*1024):.2f} MB\n"
                            f"• Processing time: {result.processing_time:.2f}s\n"
                            f"• Errors: {len(result.errors)}\n\n"
                            f"📊 File Types Cleaned:\n"
                            + "\n".join([f"• {category}: {count} files"
                                       for category, count in result.files_by_category.items()]),
                            title=f"🧹 Cleanup {'Preview' if dry_run else 'Complete'}",
                            border_style="green" if result.success else "red",
                        )
                    )

                    # Show detailed file lists
                    if result.removed_files:
                        console.print(f"\n[green]{'📋 Files to be removed:' if dry_run else '🗑️  Files removed:'}[/green]")
                        for file_path in result.removed_files[:20]:  # Show first 20
                            file_size = file_path.stat().st_size if file_path.exists() else 0
                            size_str = f"({file_size / 1024:.1f} KB)" if file_size > 0 else ""
                            console.print(f"  • {file_path.relative_to(target_path)} {size_str}")

                        if len(result.removed_files) > 20:
                            console.print(f"  ... and {len(result.removed_files) - 20} more files")

                    # Show errors if any
                    if result.errors:
                        console.print(f"\n[red]⚠️  Errors encountered:[/red]")
                        for error in result.errors[:5]:  # Show first 5 errors
                            console.print(f"  • {error}")
                        if len(result.errors) > 5:
                            console.print(f"  ... and {len(result.errors) - 5} more errors")

                elif report_format == "table":
                    # Create a summary table
                    from rich.table import Table

                    table = Table(title=f"Cleanup {'Preview' if dry_run else 'Results'}")
                    table.add_column("Category", style="cyan")
                    table.add_column("Files", justify="right", style="magenta")
                    table.add_column("Size", justify="right", style="green")

                    for category, count in result.files_by_category.items():
                        # Calculate size for this category
                        category_size = sum(
                            f.stat().st_size if f.exists() else 0
                            for f in result.removed_files
                            if category.lower() in str(f).lower()
                        )
                        size_mb = category_size / (1024 * 1024)
                        table.add_row(category, str(count), f"{size_mb:.2f} MB")

                    console.print(table)

                elif report_format == "json":
                    # JSON summary
                    json_result = {
                        "cleanup_summary": {
                            "dry_run": dry_run,
                            "success": result.success,
                            "files_removed": result.files_removed,
                            "space_freed_mb": result.space_freed / (1024*1024),
                            "processing_time": result.processing_time,
                            "target_directory": str(target_path),
                            "cleanup_types": cleanup_types_list
                        },
                        "file_categories": result.files_by_category,
                        "removed_files": [str(f) for f in result.removed_files],
                        "errors": result.errors,
                        "timestamp": datetime.now().isoformat()
                    }
                    console.print(json.dumps(json_result, indent=2))

                # Save report to file if requested
                if report_file:
                    report_path = Path(report_file)
                    report_data = {
                        "cleanup_summary": {
                            "dry_run": dry_run,
                            "success": result.success,
                            "files_removed": result.files_removed,
                            "space_freed_mb": result.space_freed / (1024*1024),
                            "processing_time": result.processing_time,
                            "target_directory": str(target_path),
                            "cleanup_types": cleanup_types_list,
                            "timestamp": datetime.now().isoformat()
                        },
                        "detailed_results": {
                            "file_categories": result.files_by_category,
                            "removed_files": [str(f) for f in result.removed_files],
                            "errors": result.errors
                        }
                    }

                    with open(report_path, 'w') as f:
                        json.dump(report_data, f, indent=2)

                    console.print(f"\n[green]📄 Report saved to: {report_path}[/green]")

            else:
                progress.update(task, description="Cleanup failed ❌", completed=True)
                console.print(f"[red]❌ Cleanup failed: {result.error_message}[/red]")
                sys.exit(1)

        except Exception as e:
            progress.update(task, description="Error occurred", completed=True)
            console.print(f"[red]❌ Cleanup execution failed: {e}[/red]")
            if ctx.obj.get("verbose"):
                import traceback
                traceback.print_exc()
            sys.exit(1)


@cli.command()
@click.argument("directory", default=".")
@click.option("--output", "-o", help="Output directory for analysis results")
@click.option(
    "--embedding-model", "-m", default="voyage-context-3", help="Embedding model to use"
)
@click.option("--milvus-uri", help="Milvus database URI (file path for Lite mode)")
@click.option("--max-files", type=int, help="Maximum number of files to process")
@click.option("--batch-size", type=int, default=10, help="Batch size for processing")
@click.option("--extensions", help="Comma-separated list of file extensions to include")
@click.option("--exclude", help="Comma-separated list of patterns to exclude")
@click.pass_context
def analyze(
    ctx,
    directory: str,
    output: Optional[str],
    embedding_model: str,
    milvus_uri: Optional[str],
    max_files: Optional[int],
    batch_size: int,
    extensions: Optional[str],
    exclude: Optional[str],
):
    """
    🔍 Analyze codebase with multi-angle document processing

    Processes documents in the specified directory, extracting features,
    components, subsystems, and research insights with semantic embeddings
    for intelligent code navigation and ADHD-friendly analysis.
    """
    from .analysis import DocumentProcessor, ProcessingConfig

    # Prepare configuration
    source_path = Path(directory).resolve()
    if not source_path.exists():
        console.print(f"[red]❌ Directory does not exist: {source_path}[/red]")
        sys.exit(1)

    # Set output directory
    if output:
        output_path = Path(output).resolve()
    else:
        output_path = source_path / ".dopemux" / "analysis"

    output_path.mkdir(parents=True, exist_ok=True)

    # Parse extensions
    file_extensions = None
    if extensions:
        file_extensions = [
            f".{ext.strip().lstrip('.')}" for ext in extensions.split(",")
        ]

    # Parse exclusion patterns
    exclude_patterns = None
    if exclude:
        exclude_patterns = [pattern.strip() for pattern in exclude.split(",")]

    # Create configuration
    config = ProcessingConfig(
        source_directory=source_path,
        output_directory=output_path,
        max_files=max_files,
        file_extensions=file_extensions,
        exclude_patterns=exclude_patterns,
        embedding_model=embedding_model,
        milvus_uri=milvus_uri,
        batch_size=batch_size,
        show_progress=True,
        gentle_feedback=True,
    )

    # Initialize and run processor
    console.print(f"[blue]🧠 Starting ADHD-optimized analysis of {source_path}[/blue]")
    console.print(f"[dim]Output: {output_path}[/dim]")

    try:
        processor = DocumentProcessor(config)
        results = processor.analyze_directory()

        if results["success"]:
            console.print(
                f"[green]✅ Analysis complete! Results saved to {output_path}[/green]"
            )
            console.print(
                f"[blue]📊 Processing time: {results['processing_time']:.1f}s[/blue]"
            )

            # Show usage suggestions
            console.print(
                Panel(
                    f"🎯 Next steps:\n\n"
                    f"• Browse results in {output_path}\n"
                    f"• Use semantic search with embeddings\n"
                    f"• Explore feature and component registries\n"
                    f"• Review evidence links for traceability",
                    title="🚀 Ready to Explore",
                    border_style="green",
                )
            )
        else:
            console.print("[red]❌ Analysis failed[/red]")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]❌ Analysis error: {e}[/red]")
        if ctx.obj.get("verbose"):
            import traceback

            traceback.print_exc()
        sys.exit(1)


@cli.group()
def mcp():
    """Manage MCP Docker servers (start/stop/status/logs)."""


@mcp.command("up")
@click.option("--all", "all_services", is_flag=True, help="Start all MCP servers")
@click.option("--services", "services", help="Comma-separated services to start")
def mcp_up_cmd(all_services: bool, services: str):
    """Start MCP servers via docker-compose."""
    try:
        cmd = "cd docker/mcp-servers && "
        if all_services or not services:
            cmd += "./start-all-mcp-servers.sh"
        else:
            svc_list = " ".join(s.strip() for s in services.split(",") if s.strip())
            cmd += f"docker-compose up -d --build {svc_list}"
        console.print(f"[blue]🔌 {cmd}[/blue]")
        subprocess.run(["bash","-lc", cmd], check=True)
        console.print("[green]✅ MCP servers started[/green]")
    except CalledProcessError:
        console.print("[red]❌ Failed to start MCP servers[/red]")
        sys.exit(1)


@mcp.command("down")
def mcp_down_cmd():
    """Stop all MCP servers."""
    try:
        subprocess.run(["bash","-lc","cd docker/mcp-servers && docker-compose down"], check=True)
        console.print("[green]✅ MCP servers stopped[/green]")
    except CalledProcessError:
        console.print("[red]❌ Failed to stop MCP servers[/red]")
        sys.exit(1)


@mcp.command("status")
def mcp_status_cmd():
    """Show docker-compose status for MCP servers."""
    try:
        subprocess.run(["bash","-lc","cd docker/mcp-servers && docker-compose ps"], check=False)
    except CalledProcessError:
        sys.exit(1)


@mcp.command("logs")
@click.option("--service", "service", help="Service to tail logs for")
def mcp_logs_cmd(service: str):
    """Tail logs for an MCP service or all."""
    try:
        if service:
            cmd = f"cd docker/mcp-servers && docker-compose logs -f {service}"
        else:
            cmd = "cd docker/mcp-servers && docker-compose logs -f"
        console.print(f"[blue]📄 {cmd}[/blue]")
        subprocess.run(["bash","-lc", cmd], check=False)
    except CalledProcessError:
        sys.exit(1)


@cli.group()
def servers():
    """Alias for 'dopemux mcp' commands."""


@servers.command("up")
@click.option("--all", "all_services", is_flag=True, help="Start all MCP servers")
@click.option("--services", "services", help="Comma-separated services to start")
def servers_up_cmd(all_services: bool, services: str):
    mcp_up_cmd(all_services, services)


@servers.command("down")
def servers_down_cmd():
    mcp_down_cmd()


@servers.command("status")
def servers_status_cmd():
    mcp_status_cmd()


@servers.command("logs")
@click.option("--service", "service", help="Service to tail logs for")
def servers_logs_cmd(service: str):
    mcp_logs_cmd(service)


@cli.command()
@click.option("--detailed", "-d", is_flag=True, help="Show detailed health information")
@click.option("--service", "-s", help="Check specific service only")
@click.option("--fix", "-f", is_flag=True, help="Attempt to fix unhealthy services")
@click.option("--watch", "-w", is_flag=True, help="Continuous monitoring mode")
@click.option(
    "--interval", "-i", type=int, default=30, help="Watch interval in seconds"
)
@click.pass_context
def health(
    ctx, detailed: bool, service: Optional[str], fix: bool, watch: bool, interval: int
):
    """
    🏥 Comprehensive health check for Dopemux ecosystem

    Monitors Dopemux core, Claude Code, MCP servers, Docker services,
    system resources, and ADHD feature effectiveness with ADHD-friendly reporting.
    """
    project_path = Path.cwd()
    health_checker = HealthChecker(project_path, console)

    if watch:
        console.print(
            f"[blue]👁️ Starting continuous health monitoring (interval: {interval}s)[/blue]"
        )
        console.print("[dim]Press Ctrl+C to stop[/dim]")

        try:
            while True:
                console.clear()
                console.print(
                    f"[dim]Last check: {datetime.now().strftime('%H:%M:%S')}[/dim]"
                )

                results = health_checker.check_all(detailed=detailed)
                health_checker.display_health_report(results, detailed=detailed)

                time.sleep(interval)
        except KeyboardInterrupt:
            console.print("\n[yellow]🛑 Health monitoring stopped[/yellow]")
            return

    # Single health check
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Running health checks...", total=None)

        if service:
            # Check specific service
            checker_method = getattr(health_checker, f"_check_{service}", None)
            if not checker_method:
                console.print(f"[red]❌ Unknown service: {service}[/red]")
                console.print(
                    f"[yellow]Available services: {', '.join(health_checker.checks.keys())}[/yellow]"
                )
                sys.exit(1)

            result = checker_method(detailed=detailed)
            results = {service: result}
        else:
            # Check all services
            results = health_checker.check_all(detailed=detailed)

        progress.update(task, description="Health checks complete!", completed=True)

    # Display results
    health_checker.display_health_report(results, detailed=detailed)

    # Fix unhealthy services if requested
    if fix:
        console.print("\n[blue]🔧 Attempting to fix unhealthy services...[/blue]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            fix_task = progress.add_task("Fixing services...", total=None)

            restarted = health_checker.restart_unhealthy_services()

            progress.update(
                fix_task, description="Fix attempts complete!", completed=True
            )

        if restarted:
            console.print(
                f"[green]✅ Restarted services: {', '.join(restarted)}[/green]"
            )
            console.print("[blue]💡 Run 'dopemux health' again to verify fixes[/blue]")
        else:
            console.print("[yellow]⚠️ No services could be automatically fixed[/yellow]")
            console.print("[dim]Manual intervention may be required[/dim]")

    # Exit with appropriate code for scripting
    critical_count = sum(1 for h in results.values() if h.status.value[0] == "critical")
    if critical_count > 0:
        sys.exit(1)


@autoresponder.command("config")
@click.option("--enabled/--disabled", help="Enable or disable auto responder")
@click.option(
    "--terminal-scope",
    type=click.Choice(["current", "all", "project"]),
    help="Terminal monitoring scope",
)
@click.option("--delay", type=float, help="Response delay in seconds (0-10)")
@click.option("--timeout", type=int, help="Auto-stop timeout in minutes")
@click.option("--whitelist/--no-whitelist", help="Enable/disable tool whitelisting")
@click.option("--debug/--no-debug", help="Enable/disable debug mode")
@click.pass_context
def autoresponder_config(
    ctx, enabled, terminal_scope, delay, timeout, whitelist, debug
):
    """
    ⚙️ Configure auto responder settings

    Update configuration options for Claude Auto Responder integration.
    """
    config_manager = ctx.obj["config_manager"]

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

        table = Table(title="🤖 Auto Responder Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Enabled", "Yes" if current_config.enabled else "No")
        table.add_row("Terminal Scope", current_config.terminal_scope)
        table.add_row("Response Delay", f"{current_config.response_delay}s")
        table.add_row("Timeout", f"{current_config.timeout_minutes} minutes")
        table.add_row(
            "Whitelist Tools", "Yes" if current_config.whitelist_tools else "No"
        )
        table.add_row("Debug Mode", "Yes" if current_config.debug_mode else "No")

        console.print(table)
        return

    # Apply updates
    try:
        config_manager.update_claude_autoresponder(**updates)
        console.print("[green]✅ Configuration updated[/green]")

        # Show what changed
        for key, value in updates.items():
            console.print(f"[blue]  {key}: {value}[/blue]")

        # Restart if running
        project_path = Path.cwd()
        if (project_path / ".dopemux").exists():
            from integrations.claude_autoresponder import create_autoresponder_manager

            autoresponder_manager = create_autoresponder_manager(
                config_manager, project_path
            )
            if autoresponder_manager.is_running():
                console.print(
                    "[yellow]🔄 Restarting auto responder with new settings...[/yellow]"
                )
                autoresponder_manager.restart()

    except ValueError as e:
        console.print(f"[red]❌ Configuration error: {e}[/red]")
        sys.exit(1)


def _get_attention_emoji(state: Optional[str]) -> str:
    """Get emoji for attention state."""
    emoji_map = {
        "focused": "🎯",
        "scattered": "🌪️",
        "hyperfocus": "🔥",
        "normal": "😊",
        "distracted": "😵‍💫",
    }
    return emoji_map.get(state, "❓")


def _start_mcp_servers_with_progress(project_path: Path):
    """
    Start MCP servers with real-time output streaming and health check waiting.

    ADHD-optimized:
    - Real-time visual feedback reduces anxiety
    - Clear status updates maintain engagement
    - Health check waiting ensures everything is ready
    """
    import requests

    mcp_dir = project_path / "docker" / "mcp-servers"

    # Critical servers to health check
    critical_servers = [
        ("Context7", "http://localhost:3002/health"),
        ("Zen", "http://localhost:3003/health"),
        ("LiteLLM", "http://localhost:4000/health"),
        ("Sequential", "http://localhost:3001/health"),
    ]

    console.print("\n[bold blue]🔌 Starting MCP Servers[/bold blue]")
    console.print("[dim]This may take 30-60 seconds for first-time setup...[/dim]\n")

    # Start docker-compose with real-time output
    status_text = Text()
    status_text.append("🚀 ", style="bold blue")
    status_text.append("Launching containers...")

    try:
        with Live(status_text, console=console, refresh_per_second=4) as live:
            # Start the containers
            process = subprocess.Popen(
                ["bash", "-c", f"cd {mcp_dir} && ./start-all-mcp-servers.sh"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            # Stream output line by line
            output_lines = []
            for line in process.stdout:
                line = line.rstrip()
                if line:
                    # Update status with last meaningful line
                    if "Starting" in line:
                        status_text = Text()
                        status_text.append("🔨 ", style="bold blue")
                        status_text.append(line)
                        live.update(status_text)
                    elif "✅" in line or "Healthy" in line:
                        status_text = Text()
                        status_text.append("✅ ", style="bold green")
                        status_text.append(line)
                        live.update(status_text)
                    elif "⚡" in line:
                        status_text = Text()
                        status_text.append("⚡ ", style="bold yellow")
                        status_text.append(line)
                        live.update(status_text)

                    output_lines.append(line)

            process.wait()

            if process.returncode != 0:
                console.print("\n[red]❌ MCP server startup failed[/red]")
                console.print("[dim]Last 10 lines of output:[/dim]")
                for line in output_lines[-10:]:
                    console.print(f"[dim]{line}[/dim]")
                raise CalledProcessError(process.returncode, process.args)

        # Wait for health checks
        console.print("\n[bold blue]🏥 Waiting for services to become healthy...[/bold blue]")

        max_wait = 45  # seconds
        start_time = time.time()
        all_healthy = False

        health_status = {name: False for name, _ in critical_servers}

        with Live(console=console, refresh_per_second=2) as live:
            while time.time() - start_time < max_wait:
                status_text = Text()
                all_healthy = True

                for name, url in critical_servers:
                    try:
                        response = requests.get(url, timeout=2)
                        is_healthy = response.status_code == 200
                        health_status[name] = is_healthy

                        if is_healthy:
                            status_text.append("✅ ", style="bold green")
                        else:
                            status_text.append("⏳ ", style="bold yellow")
                            all_healthy = False

                        status_text.append(f"{name}\n")
                    except requests.RequestException:
                        status_text.append("⏳ ", style="bold yellow")
                        status_text.append(f"{name}\n")
                        all_healthy = False
                        health_status[name] = False

                # Add elapsed time
                elapsed = int(time.time() - start_time)
                status_text.append(f"\n[dim]⏱️  {elapsed}s / {max_wait}s[/dim]")

                live.update(Panel(status_text, title="[bold]Health Check Status[/bold]", border_style="blue"))

                if all_healthy:
                    break

                time.sleep(2)

        if all_healthy:
            console.print("\n[bold green]✅ All MCP servers are healthy and ready![/bold green]\n")
        else:
            # Show which services failed
            console.print("\n[yellow]⚠️  Some services are not healthy (continuing anyway):[/yellow]")
            for name, is_healthy in health_status.items():
                if not is_healthy:
                    console.print(f"  [red]❌ {name}[/red]")
                else:
                    console.print(f"  [green]✅ {name}[/green]")
            console.print("[dim]Tip: Check docker logs with: docker-compose -f docker/mcp-servers/docker-compose.yml logs[/dim]\n")

    except CalledProcessError as e:
        console.print("[yellow]⚠️  Failed to start MCP servers (continuing with reduced functionality)[/yellow]")
        console.print("[dim]   Tip: Run 'dopemux start --no-mcp' to skip this step[/dim]")
    except Exception as e:
        console.print(f"[yellow]⚠️  Error during MCP startup: {e}[/yellow]")
        console.print("[dim]   Continuing with reduced functionality...[/dim]")


def _activate_dangerous_mode():
    """
    Activate dangerous mode with proper security safeguards.

    This temporarily overrides the default safe mode settings for the current
    session only. Changes are not persisted to the .env file.

    Security Features:
    - Time-limited session (1 hour max)
    - Explicit user confirmation required
    - Clear warnings about risks
    - Environment isolation
    """
    # Check if already in dangerous mode
    if os.getenv("DOPEMUX_DANGEROUS_MODE") == "true":
        expires_str = os.getenv("DOPEMUX_DANGEROUS_EXPIRES", "0")
        expires_timestamp = float(expires_str) if expires_str.isdigit() else 0

        if time.time() < expires_timestamp:
            console.print("[yellow]⚠️  Dangerous mode already active[/yellow]")
            remaining_minutes = int((expires_timestamp - time.time()) / 60)
            console.print(f"[dim]Expires in {remaining_minutes} minutes[/dim]")
            return
        else:
            # Expired, clear old settings
            _deactivate_dangerous_mode()

    # Show serious warning
    console.print(Panel(
        "[red bold]⚠️  DANGER: This will disable ALL security restrictions![/red bold]\n\n"
        "[yellow]This mode will:[/yellow]\n"
        "• Skip all permission checks\n"
        "• Disable role enforcement\n"
        "• Bypass budget limits\n"
        "• Allow unrestricted tool access\n\n"
        "[red]Use ONLY in isolated, trusted environments![/red]\n"
        "[yellow]Session will expire automatically in 1 hour.[/yellow]",
        title="🚨 Security Warning",
        border_style="red"
    ))

    # Require explicit confirmation
    if not click.confirm("\nDo you understand the risks and want to proceed?", default=False):
        console.print("[green]Dangerous mode cancelled. Staying in safe mode.[/green]")
        return

    if not click.confirm("Are you in an isolated, trusted environment?", default=False):
        console.print("[green]Dangerous mode cancelled for security.[/green]")
        return

    # Set time-limited dangerous mode (1 hour)
    expiry_time = time.time() + 3600  # 1 hour

    os.environ["DOPEMUX_DANGEROUS_MODE"] = "true"
    os.environ["DOPEMUX_DANGEROUS_EXPIRES"] = str(expiry_time)
    os.environ["DOPEMUX_DANGEROUS_PID"] = str(os.getpid())  # Track process

    # Set security bypass flags
    os.environ["HOOKS_ENABLE_ADAPTIVE_SECURITY"] = "0"
    os.environ["CLAUDE_CODE_SKIP_PERMISSIONS"] = "true"
    os.environ["METAMCP_ROLE_ENFORCEMENT"] = "false"
    os.environ["METAMCP_APPROVAL_REQUIRED"] = "false"
    os.environ["METAMCP_BUDGET_ENFORCEMENT"] = "false"

    # Traditional dangerous flags for compatibility
    os.environ["CLAUDE_DANGEROUS"] = "true"
    os.environ["SKIP_PERMISSIONS"] = "true"

    # Log for audit trail (but not sensitive info)
    expiry_str = datetime.fromtimestamp(expiry_time).strftime("%H:%M:%S")
    console.print(f"[red bold]⚠️  DANGEROUS MODE ACTIVE until {expiry_str}[/red bold]")


def _deactivate_dangerous_mode():
    """Deactivate dangerous mode and clean up environment."""
    dangerous_vars = [
        "DOPEMUX_DANGEROUS_MODE",
        "DOPEMUX_DANGEROUS_EXPIRES",
        "DOPEMUX_DANGEROUS_PID",
        "HOOKS_ENABLE_ADAPTIVE_SECURITY",
        "CLAUDE_CODE_SKIP_PERMISSIONS",
        "METAMCP_ROLE_ENFORCEMENT",
        "METAMCP_APPROVAL_REQUIRED",
        "METAMCP_BUDGET_ENFORCEMENT",
        "CLAUDE_DANGEROUS",
        "SKIP_PERMISSIONS"
    ]

    for var in dangerous_vars:
        os.environ.pop(var, None)

    console.print("[green]✅ Dangerous mode deactivated[/green]")


def _check_dangerous_mode_expiry():
    """Check if dangerous mode has expired and clean up if needed."""
    if os.getenv("DOPEMUX_DANGEROUS_MODE") == "true":
        expires_str = os.getenv("DOPEMUX_DANGEROUS_EXPIRES", "0")
        expires_timestamp = float(expires_str) if expires_str.isdigit() else 0

        if time.time() >= expires_timestamp:
            console.print("[yellow]⏰ Dangerous mode expired, returning to safe mode[/yellow]")
            _deactivate_dangerous_mode()
            return True
    return False


@cli.command("extract-chatlog")
@click.argument("directory", default=".")
@click.option("--output", "-o", help="Output directory for extraction results")
@click.option("--confidence", "-c", type=float, default=0.5, help="Minimum confidence threshold (0.0-1.0)")
@click.option("--batch-size", "-b", type=int, default=10, help="Number of files to process per batch")
@click.option("--max-workers", "-w", type=int, default=4, help="Maximum parallel workers")
@click.option("--archive", "-a", help="Archive directory for processed files")
@click.option("--workspace-id", help="ConPort workspace ID for persistence")
@click.pass_context
def extract_chatlog(
    ctx,
    directory: str,
    output: Optional[str],
    confidence: float,
    batch_size: int,
    max_workers: int,
    archive: Optional[str],
    workspace_id: Optional[str]
):
    """
    📄 Extract structured data from chatlog conversations (Basic Mode)

    Process chatlog files using core extractors (decisions, features, research)
    with adaptive document synthesis. Includes batch processing with phase
    synchronization and automatic archiving of processed files.

    Basic extractors:
    • Decision extraction (conclusions, agreements, next steps)
    • Feature extraction (requirements, user stories, acceptance criteria)
    • Research extraction (findings, references, methodologies)
    """
    import sys
    from pathlib import Path

    # Add the gpt-researcher backend to the path
    backend_path = Path(__file__).parent.parent.parent / "services" / "dopemux-gpt-researcher" / "backend"
    sys.path.insert(0, str(backend_path))

    try:
        from extraction_pipeline import ExtractionPipeline, PipelineConfig
    except ImportError as e:
        console.print(f"[red]❌ Could not import extraction pipeline: {e}[/red]")
        console.print("[yellow]💡 Make sure you're in the dopemux-mvp directory[/yellow]")
        sys.exit(1)

    source_path = Path(directory).resolve()
    if not source_path.exists():
        console.print(f"[red]❌ Directory does not exist: {source_path}[/red]")
        sys.exit(1)

    # Set output directory
    if output:
        output_path = Path(output).resolve()
    else:
        output_path = source_path / ".dopemux" / "extraction"

    # Set archive directory
    archive_path = None
    if archive:
        archive_path = Path(archive).resolve()

    # Set workspace ID for ConPort
    if not workspace_id:
        workspace_id = str(source_path)

    # Create configuration
    config = PipelineConfig(
        source_directory=source_path,
        output_directory=output_path,
        archive_directory=archive_path,
        batch_size=batch_size,
        max_workers=max_workers,
        confidence_threshold=confidence,
        include_basic_extractors=True,
        include_pro_extractors=False,  # Basic mode only
        enable_synthesis=True,
        max_documents=4,  # Fewer documents in basic mode
        verbose=ctx.obj.get("verbose", False),
        persist_to_conport=True,
        workspace_id=workspace_id
    )

    console.print("[blue]🚀 Starting Basic Chatlog Extraction Pipeline[/blue]")
    console.print(f"[blue]📁 Source: {source_path}[/blue]")
    console.print(f"[blue]📤 Output: {output_path}[/blue]")
    console.print(f"[blue]🎯 Extractors: Decision, Feature, Research[/blue]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Initializing extraction pipeline...", total=None)

        try:
            # Create and run pipeline
            pipeline = ExtractionPipeline(config)

            progress.update(task, description="Discovering files...")
            files = pipeline.discover_files()

            if not files:
                progress.update(task, description="No files found to process", completed=True)
                console.print("[yellow]⚠️ No unprocessed chatlog files found[/yellow]")
                return

            progress.update(task, description=f"Processing {len(files)} files...")
            result = pipeline.run_extraction()

            if result['success']:
                progress.update(task, description="Extraction completed successfully! ✅", completed=True)

                stats = result['statistics']
                console.print(
                    Panel(
                        f"🎯 Basic Extraction Results:\n\n"
                        f"• Files processed: {stats['files_processed']}/{stats['total_files']}\n"
                        f"• Total chunks: {stats['total_chunks']}\n"
                        f"• Fields extracted: {stats['total_fields']}\n"
                        f"• High confidence fields: {stats['high_confidence_fields']}\n"
                        f"• Documents generated: {stats['documents_generated']}\n"
                        f"• Processing time: {stats['processing_time']:.2f}s\n\n"
                        f"📊 Field Types:\n" +
                        "\n".join([f"• {field_type}: {count}"
                                 for field_type, count in stats['fields_by_type'].items()]),
                        title="🚀 Basic Extraction Complete",
                        border_style="green",
                    )
                )

                console.print(f"\n[green]📁 Results saved to: {output_path}[/green]")
                console.print(f"[green]📦 Processed files archived to: {result['archive_directory']}[/green]")

            else:
                progress.update(task, description="Extraction failed ❌", completed=True)
                console.print(f"[red]❌ Extraction failed[/red]")
                if result.get('errors'):
                    console.print(f"[red]Errors: {len(result['errors'])}[/red]")
                    for error in result['errors'][:3]:  # Show first 3 errors
                        console.print(f"[red]  • {error}[/red]")
                sys.exit(1)

        except Exception as e:
            progress.update(task, description="Error occurred", completed=True)
            console.print(f"[red]❌ Extraction pipeline failed: {e}[/red]")
            if ctx.obj.get("verbose"):
                import traceback
                traceback.print_exc()
            sys.exit(1)


@cli.command()
@click.argument("directory", default=".")
@click.option("--output", "-o", help="Output directory for extraction results")
@click.option("--confidence", "-c", type=float, default=0.4, help="Minimum confidence threshold (0.0-1.0)")
@click.option("--batch-size", "-b", type=int, default=15, help="Number of files to process per batch")
@click.option("--max-workers", "-w", type=int, default=6, help="Maximum parallel workers")
@click.option("--archive", "-a", help="Archive directory for processed files")
@click.option("--workspace-id", help="ConPort workspace ID for persistence")
@click.option("--max-documents", "-d", type=int, default=8, help="Maximum documents to generate")
@click.pass_context
def extractPro(
    ctx,
    directory: str,
    output: Optional[str],
    confidence: float,
    batch_size: int,
    max_workers: int,
    archive: Optional[str],
    workspace_id: Optional[str],
    max_documents: int
):
    """
    🔬 Extract comprehensive data from chatlog conversations (Pro Mode)

    Process chatlog files using ALL extractors with advanced analysis capabilities.
    Includes full synthesis suite, knowledge graph construction, and comprehensive
    reporting with pre-commit review integration.

    Pro extractors include ALL basic extractors PLUS:
    • Constraint extraction (technical/business limitations, dependencies)
    • Stakeholder extraction (roles, responsibilities, decision makers)
    • Risk extraction (threats, mitigations, impact assessments)
    • Security extraction (auth requirements, compliance, vulnerabilities)

    Pro features:
    • Lower confidence threshold for broader coverage
    • More parallel processing power
    • Advanced document synthesis (8+ document types)
    • Knowledge graph with relationship mapping
    • Comprehensive quality metrics and reporting
    """
    import sys
    from pathlib import Path

    # Add the gpt-researcher backend to the path
    backend_path = Path(__file__).parent.parent.parent / "services" / "dopemux-gpt-researcher" / "backend"
    sys.path.insert(0, str(backend_path))

    try:
        from extraction_pipeline import ExtractionPipeline, PipelineConfig
    except ImportError as e:
        console.print(f"[red]❌ Could not import extraction pipeline: {e}[/red]")
        console.print("[yellow]💡 Make sure you're in the dopemux-mvp directory[/yellow]")
        sys.exit(1)

    source_path = Path(directory).resolve()
    if not source_path.exists():
        console.print(f"[red]❌ Directory does not exist: {source_path}[/red]")
        sys.exit(1)

    # Set output directory
    if output:
        output_path = Path(output).resolve()
    else:
        output_path = source_path / ".dopemux" / "extraction-pro"

    # Set archive directory
    archive_path = None
    if archive:
        archive_path = Path(archive).resolve()

    # Set workspace ID for ConPort
    if not workspace_id:
        workspace_id = str(source_path)

    # Create configuration for Pro mode
    config = PipelineConfig(
        source_directory=source_path,
        output_directory=output_path,
        archive_directory=archive_path,
        batch_size=batch_size,
        max_workers=max_workers,
        confidence_threshold=confidence,
        include_basic_extractors=True,
        include_pro_extractors=True,  # Pro mode includes ALL extractors
        enable_synthesis=True,
        max_documents=max_documents,
        verbose=ctx.obj.get("verbose", False),
        persist_to_conport=True,
        workspace_id=workspace_id
    )

    console.print("[blue]🔬 Starting Pro Chatlog Extraction Pipeline[/blue]")
    console.print(f"[blue]📁 Source: {source_path}[/blue]")
    console.print(f"[blue]📤 Output: {output_path}[/blue]")
    console.print(f"[blue]🎯 Extractors: All 7 (Decision, Feature, Research, Constraint, Stakeholder, Risk, Security)[/blue]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Initializing Pro extraction pipeline...", total=None)

        try:
            # Create and run pipeline
            pipeline = ExtractionPipeline(config)

            progress.update(task, description="Discovering files...")
            files = pipeline.discover_files()

            if not files:
                progress.update(task, description="No files found to process", completed=True)
                console.print("[yellow]⚠️ No unprocessed chatlog files found[/yellow]")
                return

            progress.update(task, description=f"Processing {len(files)} files with ALL extractors...")
            result = pipeline.run_extraction()

            if result['success']:
                progress.update(task, description="Pro extraction completed successfully! ✅", completed=True)

                stats = result['statistics']
                console.print(
                    Panel(
                        f"🔬 Pro Extraction Results:\n\n"
                        f"• Files processed: {stats['files_processed']}/{stats['total_files']}\n"
                        f"• Total chunks: {stats['total_chunks']}\n"
                        f"• Fields extracted: {stats['total_fields']}\n"
                        f"• High confidence fields: {stats['high_confidence_fields']}\n"
                        f"• Documents generated: {stats['documents_generated']}\n"
                        f"• Processing time: {stats['processing_time']:.2f}s\n\n"
                        f"📊 Field Types:\n" +
                        "\n".join([f"• {field_type}: {count}"
                                 for field_type, count in stats['fields_by_type'].items()]) +
                        f"\n\n⏱️ Phase Times:\n" +
                        "\n".join([f"• {phase}: {time:.2f}s"
                                 for phase, time in stats['phase_times'].items()]),
                        title="🚀 Pro Extraction Complete",
                        border_style="green",
                    )
                )

                console.print(f"\n[green]📁 Results saved to: {output_path}[/green]")
                console.print(f"[green]📦 Processed files archived to: {result['archive_directory']}[/green]")
                console.print(f"[green]📊 Knowledge graph: {output_path}/knowledge_graph.json[/green]")
                console.print(f"[green]📋 Comprehensive report: {output_path}/reports/[/green]")

            else:
                progress.update(task, description="Pro extraction failed ❌", completed=True)
                console.print(f"[red]❌ Pro extraction failed[/red]")
                if result.get('errors'):
                    console.print(f"[red]Errors: {len(result['errors'])}[/red]")
                    for error in result['errors'][:3]:  # Show first 3 errors
                        console.print(f"[red]  • {error}[/red]")
                sys.exit(1)

        except Exception as e:
            progress.update(task, description="Error occurred", completed=True)
            console.print(f"[red]❌ Pro extraction pipeline failed: {e}[/red]")
            if ctx.obj.get("verbose"):
                import traceback
                traceback.print_exc()
            sys.exit(1)


@cli.group()
def update():
    """🔄 Update and upgrade dopemux system components."""
    pass


@update.command()
@click.option(
    "--check",
    is_flag=True,
    help="Check for updates without applying them (dry run)"
)
@click.option(
    "--minimal",
    is_flag=True,
    help="Skip Docker rebuilds if possible (faster update)"
)
@click.option(
    "--skip-backups",
    is_flag=True,
    help="Skip backup creation (not recommended)"
)
@click.option(
    "--skip-docker",
    is_flag=True,
    help="Skip Docker image updates"
)
@click.option(
    "--timeout",
    type=int,
    default=30,
    help="Timeout in minutes for update operations"
)
@click.pass_context
def run(ctx, check: bool, minimal: bool, skip_backups: bool, skip_docker: bool, timeout: int):
    """
    🚀 Run comprehensive system update

    Updates all dopemux components including:
    - Git repository (with local change preservation)
    - Docker containers and images
    - Python and Node.js dependencies
    - Database migrations
    - Configuration updates

    Includes automatic backup, rollback capability, and ADHD-friendly progress tracking.
    """
    import asyncio
    from .update import UpdateManager, UpdateConfig

    try:
        # Configure update
        config = UpdateConfig(
            dry_run=check,
            minimal=minimal,
            skip_backups=skip_backups,
            skip_docker=skip_docker,
            timeout_minutes=timeout
        )

        # Create update manager
        manager = UpdateManager(config=config, project_root=Path.cwd())

        if check:
            console.print("[cyan]🔍 Checking for available updates...[/cyan]")
            # Run dry run
            plan = asyncio.run(manager.dry_run())

            # Display update plan
            _show_update_plan(plan)

        else:
            # Run actual update
            console.print("[cyan]🚀 Starting dopemux update...[/cyan]")
            result = asyncio.run(manager.run_update())

            # Show result
            if result.value == "success":
                console.print("[green]✅ Update completed successfully![/green]")
            elif result.value == "rolled_back":
                console.print("[yellow]🔄 Update failed but rollback successful[/yellow]")
            elif result.value == "interrupted":
                console.print("[yellow]⏸️ Update interrupted - resume with 'dopemux update resume'[/yellow]")
            else:
                console.print("[red]❌ Update failed[/red]")
                sys.exit(1)

    except Exception as e:
        console.print(f"[red]❌ Update command failed: {e}[/red]")
        if ctx.obj and ctx.obj.get('verbose'):
            import traceback
            traceback.print_exc()
        sys.exit(1)


@update.command()
@click.pass_context
def resume(ctx):
    """
    ▶️ Resume interrupted update from last checkpoint

    Continues an update that was interrupted by user or system failure.
    Uses automatic checkpointing to resume from the exact point of interruption.
    """
    import asyncio
    from .update import UpdateManager, UpdateConfig

    try:
        # Create manager with resume configuration
        config = UpdateConfig(checkpoint_saves=True)
        manager = UpdateManager(config=config, project_root=Path.cwd())

        console.print("[cyan]🔄 Resuming interrupted update...[/cyan]")
        result = asyncio.run(manager.run_update())

        if result.value == "success":
            console.print("[green]✅ Update resumed and completed successfully![/green]")
        else:
            console.print(f"[red]❌ Update resume failed: {result.value}[/red]")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]❌ Resume command failed: {e}[/red]")
        if ctx.obj and ctx.obj.get('verbose'):
            import traceback
            traceback.print_exc()
        sys.exit(1)


@update.command()
@click.option(
    "--backup-name",
    help="Specific backup to rollback to (interactive selection if not provided)"
)
@click.option(
    "--list-backups",
    is_flag=True,
    help="List available backups and exit"
)
@click.pass_context
def rollback(ctx, backup_name: Optional[str], list_backups: bool):
    """
    ⏪ Rollback to previous system state

    Safely restore the system to a previous working state using automatic backups.
    Includes database restoration, configuration rollback, and service restart.
    """
    import asyncio
    from .update import RollbackManager

    try:
        manager = RollbackManager(project_root=Path.cwd())

        if list_backups:
            # List available backups
            backups = manager.list_available_backups()

            if not backups:
                console.print("[yellow]No backups available[/yellow]")
                return

            console.print("\n[bold]Available Backups:[/bold]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Name", style="cyan")
            table.add_column("Created", style="dim")
            table.add_column("Version", style="green")
            table.add_column("Size", style="blue")

            for backup in backups:
                backup_path = Path(backup['path'])
                created = backup['created_at'][:19].replace('T', ' ')
                version = backup.get('version_from', 'unknown')
                size = backup.get('size', 'unknown')

                table.add_row(backup_path.name, created, version, size)

            console.print(table)
            return

        # Perform rollback
        console.print("[yellow]🔄 Initiating system rollback...[/yellow]")
        success = asyncio.run(manager.manual_rollback(backup_name))

        if success:
            console.print("[green]✅ Rollback completed successfully![/green]")
        else:
            console.print("[red]❌ Rollback failed[/red]")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]❌ Rollback command failed: {e}[/red]")
        if ctx.obj and ctx.obj.get('verbose'):
            import traceback
            traceback.print_exc()
        sys.exit(1)


@update.command()
@click.pass_context
def status(ctx):
    """
    📊 Show system update status and health

    Displays current version, available updates, system health,
    and update history.
    """
    import asyncio
    from .update import UpdateManager
    from .update.health import HealthChecker

    try:
        manager = UpdateManager(project_root=Path.cwd())
        health_checker = HealthChecker(project_root=Path.cwd())

        console.print("[cyan]📊 Dopemux System Status[/cyan]\n")

        # Version information
        version_info = manager.check_for_updates()
        console.print(f"[bold]Current Version:[/bold] {version_info.current}")
        console.print(f"[bold]Latest Version:[/bold] {version_info.target}")

        if version_info.current != version_info.target:
            console.print(f"[yellow]📦 Update available: {version_info.current} → {version_info.target}[/yellow]")
        else:
            console.print("[green]✅ System is up to date[/green]")

        # Health status
        console.print("\n[bold]System Health:[/bold]")
        health_results = asyncio.run(health_checker.check_all_services())

        healthy_count = sum(health_results.values())
        total_count = len(health_results)

        if healthy_count == total_count:
            console.print(f"[green]✅ All services healthy ({healthy_count}/{total_count})[/green]")
        else:
            console.print(f"[yellow]⚠️ {total_count - healthy_count} services need attention ({healthy_count}/{total_count})[/yellow]")

            # Show unhealthy services
            unhealthy = [service for service, healthy in health_results.items() if not healthy]
            for service in unhealthy:
                console.print(f"  [red]❌ {service}[/red]")

    except Exception as e:
        console.print(f"[red]❌ Status command failed: {e}[/red]")
        if ctx.obj and ctx.obj.get('verbose'):
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _show_update_plan(plan):
    """Show update plan in user-friendly format."""
    version_info = plan['version_info']

    console.print(f"\n[bold]📋 Update Plan: v{version_info['current']} → v{version_info['target']}[/bold]")

    if version_info['current'] == version_info['target']:
        console.print("[green]✅ Already up to date![/green]")
        return

    # Show what will be updated
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Component", style="cyan")
    table.add_column("Action", style="yellow")
    table.add_column("Details")

    table.add_row("Code", "🔄 Update", "Pull latest changes from git")
    table.add_row("Dependencies", "📦 Update", "Python and Node.js packages")
    table.add_row("Docker", "🐳 Rebuild", "Update container images")
    table.add_row("Configuration", "⚙️ Merge", "Preserve local customizations")

    if version_info.get('requires_migration'):
        table.add_row("Database", "🔄 Migrate", "Apply schema changes")

    console.print(table)

    # Show estimates
    console.print(f"\n[dim]⏱️ Estimated time: {plan.get('estimated_time', '15-20 minutes')}[/dim]")
    console.print(f"[dim]💾 Backup size: {plan.get('backup_size', '~250 MB')}[/dim]")

    # Show phases
    phases = plan.get('phases', [])
    if phases:
        console.print(f"\n[bold]Phases:[/bold] {' → '.join(phases)}")


# =============================================================================
# Profile Management Commands (Epic 1)
# =============================================================================

@cli.group()
def profile():
    """📋 Manage MCP profiles for context-aware tool selection."""
    pass


@profile.command("list")
@click.option("--profile-dir", "-d", help="Profile directory path", type=click.Path(exists=True))
@click.pass_context
def profile_list_cmd(ctx, profile_dir: Optional[str]):
    """📋 List all available profiles."""
    try:
        parser = ProfileParser(Path(profile_dir) if profile_dir else None)
        profile_set = parser.load_all_profiles(fail_fast=False)

        if not profile_set.profiles:
            console.print("[yellow]No valid profiles found[/yellow]")
            console.print(f"\nProfile directory: {parser.profile_dir}")
            console.print("\nCreate profiles with the YAML schema documented in:")
            console.print("  docs/PROFILE-YAML-SCHEMA.md")
            sys.exit(1)

        # Display profiles in a rich table
        table = Table(title="📋 Available Profiles", show_header=True, header_style="bold cyan")
        table.add_column("Name", style="green")
        table.add_column("Display Name", style="cyan")
        table.add_column("MCPs", style="yellow")
        table.add_column("Description", style="white", no_wrap=False)

        for p in profile_set.profiles:
            mcp_count = len(p.mcps)
            table.add_row(
                p.name,
                p.display_name,
                f"{mcp_count} servers",
                p.description
            )

        console.print(table)
        console.print(f"\n[dim]Profile directory: {parser.profile_dir}[/dim]")
        console.print(f"[dim]Total profiles: {len(profile_set.profiles)}[/dim]")

        if profile_set.errors:
            console.print(f"\n[yellow]⚠️  {len(profile_set.errors)} profile(s) failed to load[/yellow]")
            for path, error in profile_set.errors:
                console.print(f"  [red]✗[/red] {path.name}: {error}")

    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        if ctx.obj.get("verbose"):
            raise
        sys.exit(1)


@profile.command("show")
@click.argument("profile_name")
@click.option("--profile-dir", "-d", help="Profile directory path", type=click.Path(exists=True))
@click.option("--raw", "-r", is_flag=True, help="Show raw YAML content")
@click.pass_context
def profile_show_cmd(ctx, profile_name: str, profile_dir: Optional[str], raw: bool):
    """📄 Show detailed profile information."""
    try:
        parser = ProfileParser(Path(profile_dir) if profile_dir else None)
        profile_paths = parser.discover_profiles()

        # Find matching profile
        profile_path = None
        for path in profile_paths:
            if path.stem == profile_name:
                profile_path = path
                break

        if not profile_path:
            console.print(f"[red]Profile '{profile_name}' not found[/red]")
            console.print(f"\nAvailable profiles in {parser.profile_dir}:")
            for path in profile_paths:
                console.print(f"  • {path.stem}")
            sys.exit(1)

        # Show raw YAML if requested
        if raw:
            console.print(f"\n[cyan]Profile: {profile_name}[/cyan]")
            console.print(f"[dim]Path: {profile_path}[/dim]\n")
            with open(profile_path, 'r') as f:
                console.print(f.read())
            return

        # Load and validate profile
        p = parser.load_profile(profile_path)

        # Display formatted profile info
        console.print(f"\n[bold cyan]Profile: {p.display_name}[/bold cyan]")
        console.print(f"[dim]Name: {p.name}[/dim]")
        console.print(f"[dim]File: {profile_path}[/dim]\n")

        console.print(f"[bold]Description:[/bold] {p.description}\n")

        # MCP Servers
        console.print("[bold]MCP Servers:[/bold]")
        for mcp in p.mcps:
            console.print(f"  • {mcp}")

        # ADHD Config (if present)
        if p.adhd_config:
            console.print("\n[bold]ADHD Configuration:[/bold]")
            console.print(f"  Energy preference: {p.adhd_config.energy_preference}")
            console.print(f"  Attention mode: {p.adhd_config.attention_mode}")
            console.print(f"  Session duration: {p.adhd_config.session_duration} minutes")

        # Auto-detection rules (if present)
        if p.auto_detection:
            console.print("\n[bold]Auto-Detection Rules:[/bold]")
            if p.auto_detection.git_branches:
                console.print("  Git branches:")
                for branch in p.auto_detection.git_branches:
                    console.print(f"    • {branch}")
            if p.auto_detection.directories:
                console.print("  Directories:")
                for dir in p.auto_detection.directories:
                    console.print(f"    • {dir}")
            if p.auto_detection.file_patterns:
                console.print("  File patterns:")
                for pattern in p.auto_detection.file_patterns:
                    console.print(f"    • {pattern}")
            if p.auto_detection.time_windows:
                console.print("  Time windows:")
                for window in p.auto_detection.time_windows:
                    console.print(f"    • {window}")

        console.print(f"\n[green]✓ Profile is valid[/green]")

    except ProfileValidationError as e:
        console.print(f"[red]Validation Error:[/red] {e.reason}")
        if e.fix_suggestion:
            console.print(f"[yellow]Suggestion:[/yellow] {e.fix_suggestion}")
        sys.exit(1)
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        if ctx.obj.get("verbose"):
            raise
        sys.exit(1)


@profile.command("validate")
@click.argument("profile_name", required=False)
@click.option("--profile-dir", "-d", help="Profile directory path", type=click.Path(exists=True))
@click.option("--all", "-a", is_flag=True, help="Validate all profiles")
@click.pass_context
def profile_validate_cmd(ctx, profile_name: Optional[str], profile_dir: Optional[str], all: bool):
    """✅ Validate profile YAML and configuration."""
    try:
        parser = ProfileParser(Path(profile_dir) if profile_dir else None)

        if all:
            # Validate all profiles
            console.print("[cyan]Validating all profiles...[/cyan]\n")
            profile_set = parser.load_all_profiles(fail_fast=False)

            # Show results
            table = Table(title="Validation Results", show_header=True, header_style="bold cyan")
            table.add_column("Profile", style="cyan")
            table.add_column("Status", style="white")
            table.add_column("Message", style="white", no_wrap=False)

            for p in profile_set.profiles:
                table.add_row(p.name, "[green]✓ Valid[/green]", f"{len(p.mcps)} MCP servers")

            for path, error in profile_set.errors:
                error_msg = str(error)
                if isinstance(error, ProfileValidationError):
                    error_msg = f"{error.reason}"
                table.add_row(path.stem, "[red]✗ Invalid[/red]", error_msg)

            console.print(table)

            # Summary
            total = len(profile_set.profiles) + len(profile_set.errors)
            valid = len(profile_set.profiles)
            console.print(f"\n[bold]Summary:[/bold] {valid}/{total} profiles valid")

            if profile_set.errors:
                sys.exit(1)

        else:
            # Validate single profile
            if not profile_name:
                console.print("[red]Error: Provide a profile name or use --all[/red]")
                console.print("Usage: dopemux profile validate <profile_name>")
                console.print("   or: dopemux profile validate --all")
                sys.exit(1)

            profile_paths = parser.discover_profiles()
            profile_path = None
            for path in profile_paths:
                if path.stem == profile_name:
                    profile_path = path
                    break

            if not profile_path:
                console.print(f"[red]Profile '{profile_name}' not found[/red]")
                sys.exit(1)

            console.print(f"[cyan]Validating profile: {profile_name}[/cyan]\n")

            # Load and validate
            p = parser.load_profile(profile_path)

            console.print(f"[green]✓ YAML syntax is valid[/green]")
            console.print(f"[green]✓ Profile schema is valid[/green]")
            console.print(f"[green]✓ All {len(p.mcps)} MCP servers are configured[/green]")
            if p.adhd_config:
                console.print(f"[green]✓ ADHD configuration is valid[/green]")
            if p.auto_detection:
                console.print(f"[green]✓ Auto-detection rules are valid[/green]")

            console.print(f"\n[bold green]Profile '{profile_name}' is valid ✓[/bold green]")

    except ProfileValidationError as e:
        console.print(f"[red]✗ Validation failed:[/red] {e.reason}")
        if e.fix_suggestion:
            console.print(f"[yellow]💡 Suggestion:[/yellow] {e.fix_suggestion}")
        sys.exit(1)
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        if ctx.obj.get("verbose"):
            raise
        sys.exit(1)


# Worktree Management Commands (Epic 3)
# =============================================================================

@cli.group()
def worktrees():
    """🌳 Manage git worktrees for parallel development."""
    pass


@worktrees.command("list")
@click.pass_context
def worktrees_list_cmd(ctx):
    """📋 List all git worktrees with status."""
    from .worktree_commands import list_worktrees
    list_worktrees()


@worktrees.command("switch")
@click.argument("branch")
@click.option("--no-fuzzy", is_flag=True, help="Disable fuzzy matching")
@click.pass_context
def worktrees_switch_cmd(ctx, branch: str, no_fuzzy: bool):
    """🔀 Switch to an existing worktree."""
    from .worktree_commands import switch_worktree
    workspace = Path.cwd()
    switch_worktree(workspace, branch, fuzzy_match=not no_fuzzy)


@worktrees.command("cleanup")
@click.option("--force", "-f", is_flag=True, help="Remove dirty worktrees")
@click.option("--dry-run", "-n", is_flag=True, help="Preview without removing")
@click.pass_context
def worktrees_cleanup_cmd(ctx, force: bool, dry_run: bool):
    """🧹 Clean up unused worktrees."""
    from .worktree_commands import cleanup_worktrees
    workspace = Path.cwd()
    cleanup_worktrees(workspace, force=force, dry_run=dry_run)


def main():
    """Main entry point."""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]⏸️ Interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        if "--debug" in sys.argv:
            raise
        sys.exit(1)


if __name__ == "__main__":
    main()
