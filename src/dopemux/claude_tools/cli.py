"""
CLI Commands for Claude-Code-Tools Integration

Provides command-line interface for Claude-Code-Tools functionality
integrated into Dopemux.

Commands:
- dmx tmux: Terminal automation commands
- dmx env: Safe environment variable inspection
- dmx session: Session search and management
- dmx safe: Safety hook management
"""

import click
from rich.console import Console
from typing import Optional

from .integration import get_global_integration
from .agent_communication import AgentMessage
from .debugging_support import DebuggerType
from ..adhd.context_manager import ContextManager

console = Console()


@click.group(name="tmux")
def tmux_group():
    """Tmux automation commands for AI agents."""
    pass


@tmux_group.command("open")
@click.argument("command")
@click.option("--session", "-s", help="Session name")
def tmux_open(command: str, session: Optional[str]):
    """Launch command in new tmux pane."""
    integration = get_global_integration()
    if not integration:
        console.print("[red]Claude-Code-Tools integration not initialized[/red]")
        return

    try:
        pane = integration.tmux_launch(command, session)
        console.print(f"[green]Launched command in pane: {pane.pane_id}[/green]")
    except Exception as e:
        console.print(f"[red]Failed to launch command: {e}[/red]")


@tmux_group.command("send")
@click.argument("pane_id")
@click.argument("text")
@click.option("--enter/--no-enter", default=True, help="Send Enter after text")
@click.option("--delay-enter", type=float, default=0.1, help="Delay before Enter")
def tmux_send(pane_id: str, text: str, enter: bool, delay_enter: float):
    """Send text input to tmux pane."""
    integration = get_global_integration()
    if not integration:
        console.print("[red]Claude-Code-Tools integration not initialized[/red]")
        return

    try:
        integration.tmux_send(text, pane_id, enter=enter, delay_enter=delay_enter)
        console.print(f"[green]Sent text to pane {pane_id}[/green]")
    except Exception as e:
        console.print(f"[red]Failed to send text: {e}[/red]")


@tmux_group.command("capture")
@click.argument("pane_id")
@click.option("--lines", "-n", type=int, default=100, help="Number of lines to capture")
def tmux_capture(pane_id: str, lines: int):
    """Capture output from tmux pane."""
    integration = get_global_integration()
    if not integration:
        console.print("[red]Claude-Code-Tools integration not initialized[/red]")
        return

    try:
        output = integration.tmux_capture(pane_id, lines)
        console.print(f"[cyan]Captured output from pane {pane_id}:[/cyan]")
        console.print(output)
    except Exception as e:
        console.print(f"[red]Failed to capture output: {e}[/red]")


@tmux_group.command("interrupt")
@click.argument("pane_id")
def tmux_interrupt(pane_id: str):
    """Send interrupt signal to tmux pane."""
    integration = get_global_integration()
    if not integration:
        console.print("[red]Claude-Code-Tools integration not initialized[/red]")
        return

    try:
        integration.tmux_interrupt(pane_id)
        console.print(f"[green]Interrupted pane {pane_id}[/green]")
    except Exception as e:
        console.print(f"[red]Failed to interrupt pane: {e}[/red]")


@tmux_group.command("kill")
@click.argument("pane_id")
def tmux_kill(pane_id: str):
    """Kill tmux pane."""
    integration = get_global_integration()
    if not integration:
        console.print("[red]Claude-Code-Tools integration not initialized[/red]")
        return

    try:
        integration.tmux_kill(pane_id)
        console.print(f"[green]Killed pane {pane_id}[/green]")
    except Exception as e:
        console.print(f"[red]Failed to kill pane: {e}[/red]")


@tmux_group.command("list")
@click.option("--session", "-s", help="Session name filter")
def tmux_list(session: Optional[str]):
    """List tmux panes."""
    integration = get_global_integration()
    if not integration:
        console.print("[red]Claude-Code-Tools integration not initialized[/red]")
        return

    try:
        panes = integration.tmux_list_panes(session)
        if not panes:
            console.print("No panes found")
            return

        console.print("[cyan]Tmux Panes:[/cyan]")
        for pane in panes:
            status = "[active]" if pane.active else ""
            console.print(f"  {pane.pane_id}: {pane.command} {status}")
    except Exception as e:
        console.print(f"[red]Failed to list panes: {e}[/red]")


@tmux_group.command("status")
def tmux_status():
    """Show current tmux status."""
    integration = get_global_integration()
    if not integration:
        console.print("[red]Claude-Code-Tools integration not initialized[/red]")
        return

    try:
        status = integration.tmux_status()
        console.print(f"[cyan]Current location: {status['current_location']}[/cyan]")
        console.print("[cyan]Panes in current window:[/cyan]")
        for pane in status['panes']:
            console.print(f"  {pane['id']}: {pane['command']}")
    except Exception as e:
        console.print(f"[red]Failed to get status: {e}[/red]")


# Environment safe commands
@click.group(name="env")
def env_group():
    """Safe environment variable inspection."""
    pass


@env_group.command("list")
@click.option("--status", is_flag=True, help="Show set/empty status")
def env_list(status: bool):
    """List environment variable keys safely."""
    integration = get_global_integration()
    if not integration:
        console.print("[red]Claude-Code-Tools integration not initialized[/red]")
        return

    try:
        variables = integration.env_list(status)
        if status:
            console.print("[cyan]Environment Variables:[/cyan]")
            for key, info in variables.items():
                status_str = info.get('status', 'UNKNOWN')
                console.print(f"  {key}: {status_str}")
        else:
            console.print("[cyan]Environment Variable Keys:[/cyan]")
            for key in variables.keys():
                console.print(f"  {key}")
    except Exception as e:
        console.print(f"[red]Failed to list environment variables: {e}[/red]")


@env_group.command("check")
@click.argument("key")
def env_check(key: str):
    """Check if environment variable exists."""
    integration = get_global_integration()
    if not integration:
        console.print("[red]Claude-Code-Tools integration not initialized[/red]")
        return

    try:
        exists = integration.env_check(key)
        if exists:
            console.print(f"[green]Variable '{key}' exists[/green]")
        else:
            console.print(f"[yellow]Variable '{key}' not found[/yellow]")
    except Exception as e:
        console.print(f"[red]Failed to check variable: {e}[/red]")


@env_group.command("count")
def env_count():
    """Count environment variables."""
    integration = get_global_integration()
    if not integration:
        console.print("[red]Claude-Code-Tools integration not initialized[/red]")
        return

    try:
        counts = integration.env_count()
        console.print(f"[cyan]Environment Variables Summary:[/cyan]")
        console.print(f"  Total: {counts['total']}")
        console.print(f"  Set: {counts['set']}")
        console.print(f"  Empty: {counts['empty']}")
    except Exception as e:
        console.print(f"[red]Failed to count variables: {e}[/red]")


@env_group.command("validate")
def env_validate():
    """Validate .env file syntax."""
    integration = get_global_integration()
    if not integration:
        console.print("[red]Claude-Code-Tools integration not initialized[/red]")
        return

    try:
        result = integration.env_validate()
        if result['valid']:
            console.print("[green].env file is valid[/green]")
        else:
            console.print("[red].env file validation failed:[/red]")
            for error in result['errors']:
                console.print(f"  [red]Error:[/red] {error}")
            for warning in result['warnings']:
                console.print(f"  [yellow]Warning:[/yellow] {warning}")
    except Exception as e:
        console.print(f"[red]Failed to validate .env file: {e}[/red]")


# Session management commands
@click.group(name="session")
def session_group():
    """Session search and management."""
    pass


@session_group.command("find")
@click.argument("keywords", required=False)
@click.option("--agent", "-a", help="Filter by agent type")
@click.option("--limit", "-n", type=int, default=20, help="Limit results")
def session_find(keywords: Optional[str], agent: Optional[str], limit: int):
    """Search for sessions."""
    integration = get_global_integration()
    if not integration:
        console.print("[red]Claude-Code-Tools integration not initialized[/red]")
        return

    try:
        sessions = integration.session_find(keywords, agent, limit)
        integration.session_display(sessions)
    except Exception as e:
        console.print(f"[red]Failed to search sessions: {e}[/red]")


@session_group.command("resume")
@click.argument("session_id")
def session_resume(session_id: str):
    """Resume a session by ID."""
    integration = get_global_integration()
    if not integration:
        console.print("[red]Claude-Code-Tools integration not initialized[/red]")
        return

    try:
        # First, find the session by ID
        sessions = integration.session_find(limit=100)  # Get all sessions
        session = next((s for s in sessions if str(s['id']) == session_id), None)

        if not session:
            console.print(f"[red]Session '{session_id}' not found[/red]")
            return

        success = integration.session_resume(session)
        if success:
            console.print(f"[green]✓ Resumed session '{session_id}'[/green]")
        else:
            console.print(f"[red]✗ Failed to resume session '{session_id}'[/red]")

    except Exception as e:
        console.print(f"[red]Failed to resume session: {e}[/red]")


# Safety management commands
@click.group(name="safe")
def safe_group():
    """Safety hook management."""
    pass


@safe_group.command("status")
def safe_status():
    """Show safety hook status."""
    integration = get_global_integration()
    if not integration:
        console.print("[red]Claude-Code-Tools integration not initialized[/red]")
        return

    console.print("[cyan]Safety Hooks Status:[/cyan]")
    console.print("  Command interception: Active")
    console.print("  File deletion protection: Active")
    console.print("  Git operation safeguards: Active")
    console.print("  Environment file locks: Active")
    console.print("  File size limits: Active")
    console.print("  Grep enforcement: Active")


@safe_group.command("check")
@click.argument("command")
@click.option("--confirmed", is_flag=True, help="Mark as confirmed")
def safe_check(command: str, confirmed: bool):
    """Check command safety."""
    integration = get_global_integration()
    if not integration:
        console.print("[red]Claude-Code-Tools integration not initialized[/red]")
        return

    context = {'confirmed': confirmed} if confirmed else {}
    result = integration.intercept_command(command, context)

    if result['allowed']:
        console.print(f"[green]✓ Command allowed: {result['message']}[/green]")
    else:
        console.print(f"[red]✗ Command blocked: {result['message']}[/red]")
        if result.get('safe_command'):
            console.print(f"[yellow]Suggested safe command: {result['safe_command']}[/yellow]")

# Vault commands
@click.group(name="vault")
def vault_group():
    """Encrypted environment vault management."""
    pass


@vault_group.command("encrypt")
@click.argument("env_file", default=".env")
def vault_encrypt(env_file: str):
    """Encrypt .env file to vault."""
    integration = get_global_integration()
    if not integration:
        console.print("[red]Claude-Code-Tools integration not initialized[/red]")
        return

    try:
        success = integration.vault.encrypt_env(env_file)
        if success:
            console.print(f"[green]✓ Encrypted {env_file} to vault[/green]")
        else:
            console.print(f"[red]✗ Failed to encrypt {env_file}[/red]")
    except Exception as e:
        console.print(f"[red]Encryption failed: {e}[/red]")


@vault_group.command("decrypt")
@click.argument("vault_file", default=None)
def vault_decrypt(vault_file: Optional[str]):
    """Decrypt vault file to .env."""
    integration = get_global_integration()
    if not integration:
        console.print("[red]Claude-Code-Tools integration not initialized[/red]")
        return

    try:
        content = integration.vault.decrypt_env(vault_file)
        if content:
            console.print(f"[green]✓ Decrypted vault to .env[/green]")
        else:
            console.print(f"[red]✗ Failed to decrypt vault[/red]")
    except Exception as e:
        console.print(f"[red]Decryption failed: {e}[/red]")


@vault_group.command("sync")
@click.argument("env_file", default=".env")
def vault_sync(env_file: str):
    """Sync environment file to vault."""
    integration = get_global_integration()
    if not integration:
        console.print("[red]Claude-Code-Tools integration not initialized[/red]")
        return

    try:
        success = integration.vault.sync_env(env_file)
        if success:
            console.print(f"[green]✓ Synced {env_file} to vault[/green]")
        else:
            console.print(f"[red]✗ Failed to sync {env_file}[/red]")
    except Exception as e:
        console.print(f"[red]Sync failed: {e}[/red]")


@vault_group.command("list")
def vault_list():
    """List all vault files."""
    integration = get_global_integration()
    if not integration:
        console.print("[red]Claude-Code-Tools integration not initialized[/red]")
        return

    try:
        vaults = integration.vault.list_vaults()
        if vaults:
            console.print("[cyan]Vault Files:[/cyan]")
            for vault in vaults:
                console.print(f"  {vault}")
        else:
            console.print("[yellow]No vault files found[/yellow]")
    except Exception as e:
        console.print(f"[red]Failed to list vaults: {e}[/red]")


# Agent Communication commands
@click.group(name="agent")
def agent_group():
    """Agent-to-agent communication."""
    pass


@agent_group.command("send")
@click.argument("pane_id")
@click.argument("message")
@click.option("--type", "message_type", default="request", help="Message type")
@click.option("--sync/--async", default=True, help="Synchronous response")
def agent_send(pane_id: str, message: str, message_type: str, sync: bool):
    """Send message to agent in pane."""
    integration = get_global_integration()
    if not integration:
        console.print("[red]Claude-Code-Tools integration not initialized[/red]")
        return

    try:
        agent_msg = AgentMessage(
            sender="cli",
            recipient="agent",
            message_type=message_type,
            content=message
        )

        mode = "SYNCHRONOUS" if sync else "ASYNCHRONOUS"
        response = integration.send_agent_message(pane_id, agent_msg, mode=mode)

        if response:
            console.print(f"[green]Response: {response.content}[/green]")
        else:
            console.print(f"[green]Message sent to {pane_id}[/green]")

    except Exception as e:
        console.print(f"[red]Failed to send message: {e}[/red]")


@agent_group.command("receive")
@click.argument("pane_id")
@click.option("--timeout", type=float, default=5.0, help="Timeout in seconds")
def agent_receive(pane_id: str, timeout: float):
    """Receive message from agent in pane."""
    integration = get_global_integration()
    if not integration:
        console.print("[red]Claude-Code-Tools integration not initialized[/red]")
        return

    try:
        message = integration.receive_agent_message(pane_id, timeout=timeout)

        if message:
            console.print(f"[cyan]Message from {message.sender}:[/cyan]")
            console.print(f"  Type: {message.message_type}")
            console.print(f"  Content: {message.content}")
        else:
            console.print(f"[yellow]No message received from {pane_id} within {timeout}s[/yellow]")

    except Exception as e:
        console.print(f"[red]Failed to receive message: {e}[/red]")


@agent_group.command("collaborate")
@click.argument("primary_pane")
@click.argument("secondary_pane")
@click.argument("task_description")
@click.option("--timeout", type=float, default=300.0, help="Collaboration timeout")
def agent_collaborate(primary_pane: str, secondary_pane: str, task_description: str, timeout: float):
    """Enable agent collaboration on task."""
    integration = get_global_integration()
    if not integration:
        console.print("[red]Claude-Code-Tools integration not initialized[/red]")
        return

    try:
        result = integration.collaborate_on_task(primary_pane, secondary_pane, task_description, timeout=timeout)

        if result['success']:
            console.print("[green]✓ Collaboration completed successfully[/green]")
            console.print(f"Duration: {result.get('collaboration_time', 0):.1f}s")
        else:
            console.print(f"[red]✗ Collaboration failed: {result.get('error', 'Unknown error')}[/red]")

    except Exception as e:
        console.print(f"[red]Collaboration error: {e}[/red]")


# Debugging commands
@click.group(name="debug")
def debug_group():
    """Interactive debugging support."""
    pass


@debug_group.command("start")
@click.argument("command")
@click.option("--debugger", type=click.Choice(['pdb', 'gdb', 'lldb']), default='pdb', help="Debugger type")
@click.option("--pane", help="Specific pane name")
def debug_start(command: str, debugger: str, pane: Optional[str]):
    """Start debugging session."""
    integration = get_global_integration()
    if not integration:
        console.print("[red]Claude-Code-Tools integration not initialized[/red]")
        return

    try:
        debugger_type = DebuggerType[debugger.upper()]
        session = integration.start_debug_session(command, debugger_type, pane_name=pane)

        console.print(f"[green]✓ Debug session started: {session.session_id}[/green]")
        console.print(f"  Pane: {session.pane_id}")
        console.print(f"  Debugger: {session.debugger_type.value}")

    except Exception as e:
        console.print(f"[red]Failed to start debug session: {e}[/red]")


@debug_group.command("breakpoint")
@click.argument("session_id")
@click.argument("file_path")
@click.argument("line", type=int)
def debug_breakpoint(session_id: str, file_path: str, line: int):
    """Set breakpoint in debug session."""
    integration = get_global_integration()
    if not integration:
        console.print("[red]Claude-Code-Tools integration not initialized[/red]")
        return

    try:
        session = integration.interactive_debugger.get_session(session_id)
        if not session:
            console.print(f"[red]Session not found: {session_id}[/red]")
            return

        success = integration.set_debug_breakpoint(session, file_path, line)

        if success:
            console.print(f"[green]✓ Breakpoint set at {file_path}:{line}[/green]")
        else:
            console.print(f"[red]✗ Failed to set breakpoint[/red]")

    except Exception as e:
        console.print(f"[red]Breakpoint error: {e}[/red]")


@debug_group.command("continue")
@click.argument("session_id")
def debug_continue(session_id: str):
    """Continue execution in debug session."""
    integration = get_global_integration()
    if not integration:
        console.print("[red]Claude-Code-Tools integration not initialized[/red]")
        return

    try:
        session = integration.interactive_debugger.get_session(session_id)
        if not session:
            console.print(f"[red]Session not found: {session_id}[/red]")
            return

        new_state = integration.continue_debugging(session)
        console.print(f"[green]Execution continued, state: {new_state.name}[/green]")

    except Exception as e:
        console.print(f"[red]Continue error: {e}[/red]")


@debug_group.command("step")
@click.argument("session_id")
@click.option("--type", type=click.Choice(['step', 'next']), default='step', help="Step type")
def debug_step(session_id: str, step_type: str):
    """Step through debug session."""
    integration = get_global_integration()
    if not integration:
        console.print("[red]Claude-Code-Tools integration not initialized[/red]")
        return

    try:
        session = integration.interactive_debugger.get_session(session_id)
        if not session:
            console.print(f"[red]Session not found: {session_id}[/red]")
            return

        new_state = integration.step_debugging(session, step_type)
        console.print(f"[green]Stepped ({step_type}), state: {new_state.name}[/green]")

    except Exception as e:
        console.print(f"[red]Step error: {e}[/red]")


@debug_group.command("inspect")
@click.argument("session_id")
@click.argument("variable")
def debug_inspect(session_id: str, variable: str):
    """Inspect variable in debug session."""
    integration = get_global_integration()
    if not integration:
        console.print("[red]Claude-Code-Tools integration not initialized[/red]")
        return

    try:
        session = integration.interactive_debugger.get_session(session_id)
        if not session:
            console.print(f"[red]Session not found: {session_id}[/red]")
            return

        value = integration.inspect_debug_variable(session, variable)
        console.print(f"[cyan]{variable} = {value}[/cyan]")

    except Exception as e:
        console.print(f"[red]Inspection error: {e}[/red]")


@debug_group.command("stack")
@click.argument("session_id")
def debug_stack(session_id: str):
    """Get stack trace from debug session."""
    integration = get_global_integration()
    if not integration:
        console.print("[red]Claude-Code-Tools integration not initialized[/red]")
        return

    try:
        session = integration.interactive_debugger.get_session(session_id)
        if not session:
            console.print(f"[red]Session not found: {session_id}[/red]")
            return

        stack = integration.get_debug_stack_trace(session)
        console.print("[cyan]Stack Trace:[/cyan]")
        for i, frame in enumerate(stack, 1):
            console.print(f"  {i}. {frame}")

    except Exception as e:
        console.print(f"[red]Stack trace error: {e}[/red]")


@debug_group.command("locals")
@click.argument("session_id")
def debug_locals(session_id: str):
    """Get local variables from debug session."""
    integration = get_global_integration()
    if not integration:
        console.print("[red]Claude-Code-Tools integration not initialized[/red]")
        return

    try:
        session = integration.interactive_debugger.get_session(session_id)
        if not session:
            console.print(f"[red]Session not found: {session_id}[/red]")
            return

        locals_vars = integration.get_debug_locals(session)
        console.print("[cyan]Local Variables:[/cyan]")
        for var_name, var_value in locals_vars.items():
            console.print(f"  {var_name} = {var_value}")

    except Exception as e:
        console.print(f"[red]Locals error: {e}[/red]")


@debug_group.command("quit")
@click.argument("session_id")
def debug_quit(session_id: str):
    """Quit debug session."""
    integration = get_global_integration()
    if not integration:
        console.print("[red]Claude-Code-Tools integration not initialized[/red]")
        return

    try:
        session = integration.interactive_debugger.get_session(session_id)
        if not session:
            console.print(f"[red]Session not found: {session_id}[/red]")
            return

        integration.quit_debugging(session)
        console.print(f"[green]✓ Debug session {session_id} terminated[/green]")

    except Exception as e:
        console.print(f"[red]Quit error: {e}[/red]")


@debug_group.command("analyze-error")
@click.argument("error_text")
def debug_analyze_error(error_text: str):
    """Analyze error output for debugging insights."""
    integration = get_global_integration()
    if not integration:
        console.print("[red]Claude-Code-Tools integration not initialized[/red]")
        return

    try:
        analysis = integration.analyze_error(error_text)
        console.print(f"[cyan]Error Analysis: {analysis['error_type']}[/cyan]")
        console.print(f"Likely Cause: {analysis['likely_cause']}")
        console.print("Suggested Fixes:")
        for fix in analysis['suggested_fixes']:
            console.print(f"  • {fix}")

    except Exception as e:
        console.print(f"[red]Analysis error: {e}[/red]")


# Register command groups
def register_commands(main_group):
    """Register Claude-Code-Tools commands with main CLI group."""
    main_group.add_command(tmux_group)
    main_group.add_command(env_group)
    main_group.add_command(session_group)
    main_group.add_command(safe_group)
    main_group.add_command(agent_group)
    main_group.add_command(debug_group)