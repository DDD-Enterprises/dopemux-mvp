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
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from . import __version__
from .adhd import AttentionMonitor, ContextManager, TaskDecomposer
from .claude import ClaudeConfigurator, ClaudeLauncher
from .config import ConfigManager
from .health import HealthChecker

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
@click.pass_context
def start(
    ctx,
    session: Optional[str],
    background: bool,
    debug: bool,
    dangerous: bool,
    dangerously_skip_permissions: bool,
):
    """
    🚀 Start Claude Code with ADHD-optimized configuration

    Launches Claude Code with custom MCP servers, restores previous context,
    and activates attention monitoring for the current project.
    """
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

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Restore context
        task = progress.add_task("Restoring context...", total=None)
        context_manager = ContextManager(project_path)

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

        # Handle dangerous mode activation
        is_dangerous_mode = dangerous or dangerously_skip_permissions
        if is_dangerous_mode:
            progress.update(task, description="⚠️  Activating dangerous mode...")
            _activate_dangerous_mode()
            console.print("[red bold]⚠️  DANGEROUS MODE ACTIVE[/red bold]")
            console.print(
                "[red]All safety restrictions disabled - USE ONLY IN ISOLATED ENVIRONMENTS[/red]"
            )

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

    if not background:
        console.print(
            "[green]✨ Claude Code is running with ADHD optimizations[/green]"
        )
        console.print("Press Ctrl+C to stop monitoring and save context")

        try:
            claude_process.wait()
        except KeyboardInterrupt:
            console.print("\n[yellow]⏸️ Saving context and stopping...[/yellow]")
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
    📋 Manage tasks with ADHD-friendly decomposition

    Break down complex tasks into manageable 25-minute chunks with
    progress tracking and attention-aware scheduling.
    """
    project_path = Path.cwd()

    if not (project_path / ".dopemux").exists():
        console.print("[red]No Dopemux project found in current directory[/red]")
        sys.exit(1)

    decomposer = TaskDecomposer(project_path)

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


def _activate_dangerous_mode():
    """
    Activate dangerous mode by setting environment variables.

    This temporarily overrides the default safe mode settings for the current
    session only. Changes are not persisted to the .env file.
    """
    # Set dangerous mode environment variables
    os.environ["DOPEMUX_DANGEROUS_MODE"] = "true"
    os.environ["HOOKS_ENABLE_ADAPTIVE_SECURITY"] = "0"
    os.environ["CLAUDE_CODE_SKIP_PERMISSIONS"] = "true"
    os.environ["METAMCP_ROLE_ENFORCEMENT"] = "false"
    os.environ["METAMCP_APPROVAL_REQUIRED"] = "false"
    os.environ["METAMCP_BUDGET_ENFORCEMENT"] = "false"

    # Also set traditional dangerous flags for compatibility
    os.environ["CLAUDE_DANGEROUS"] = "true"
    os.environ["SKIP_PERMISSIONS"] = "true"


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
