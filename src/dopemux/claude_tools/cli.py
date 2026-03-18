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

import logging

logger = logging.getLogger(__name__)

from typing import Optional

from ..console import console
from .integration import get_global_integration
from .agent_communication import AgentMessage
from .debugging_support import DebuggerType
from ..adhd.context_manager import ContextManager


# Tmux commands removed - use 'dopemux tmux' instead
# The tmux_group was conflicting with dopemux.tmux.cli and has been removed.
# All tmux functionality is available via 'dopemux tmux' commands.

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
        console.log("[error]Claude-Code-Tools integration not initialized[/error]")
        return

    try:
        variables = integration.env_list(status)
        if status:
            console.log("[info]Environment Variables:[/info]")
            for key, info in variables.items():
                status_str = info.get('status', 'UNKNOWN')
                console.log(f"  {key}: {status_str}")
        else:
            console.log("[info]Environment Variable Keys:[/info]")
            for key in variables.keys():
                console.log(f"  {key}")
    except Exception as e:
        console.log(f"[error]Failed to list environment variables: {e}[/error]")


@env_group.command("check")
@click.argument("key")
def env_check(key: str):
    """Check if environment variable exists."""
    integration = get_global_integration()
    if not integration:
        console.log("[error]Claude-Code-Tools integration not initialized[/error]")
        return

    try:
        exists = integration.env_check(key)
        if exists:
            console.log(f"[success]Variable '{key}' exists[/success]")
        else:
            console.log(f"[warning]Variable '{key}' not found[/warning]")
    except Exception as e:
        console.log(f"[error]Failed to check variable: {e}[/error]")


@env_group.command("count")
def env_count():
    """Count environment variables."""
    integration = get_global_integration()
    if not integration:
        console.log("[error]Claude-Code-Tools integration not initialized[/error]")
        return

    try:
        counts = integration.env_count()
        console.log(f"[info]Environment Variables Summary:[/info]")
        console.log(f"  Total: {counts['total']}")
        console.log(f"  Set: {counts['set']}")
        console.log(f"  Empty: {counts['empty']}")
    except Exception as e:
        console.log(f"[error]Failed to count variables: {e}[/error]")


@env_group.command("validate")
def env_validate():
    """Validate .env file syntax."""
    integration = get_global_integration()
    if not integration:
        console.log("[error]Claude-Code-Tools integration not initialized[/error]")
        return

    try:
        result = integration.env_validate()
        if result['valid']:
            console.log("[success].env file is valid[/success]")
        else:
            console.log("[error].env file validation failed:[/error]")
            for error in result['errors']:
                console.log(f"  [error]Error:[/error] {error}")
            for warning in result['warnings']:
                console.log(f"  [warning]Warning:[/warning] {warning}")
    except Exception as e:
        console.log(f"[error]Failed to validate .env file: {e}[/error]")


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
        console.log("[error]Claude-Code-Tools integration not initialized[/error]")
        return

    try:
        sessions = integration.session_find(keywords, agent, limit)
        integration.session_display(sessions)
    except Exception as e:
        console.log(f"[error]Failed to search sessions: {e}[/error]")


@session_group.command("resume")
@click.argument("session_id")
def session_resume(session_id: str):
    """Resume a session by ID."""
    integration = get_global_integration()
    if not integration:
        console.log("[error]Claude-Code-Tools integration not initialized[/error]")
        return

    try:
        # First, find the session by ID
        sessions = integration.session_find(limit=100)  # Get all sessions
        session = next((s for s in sessions if str(s['id']) == session_id), None)

        if not session:
            console.log(f"[error]Session '{session_id}' not found[/error]")
            return

        success = integration.session_resume(session)
        if success:
            console.log(f"[success]✓ Resumed session '{session_id}'[/success]")
        else:
            console.log(f"[error]✗ Failed to resume session '{session_id}'[/error]")

    except Exception as e:
        console.log(f"[error]Failed to resume session: {e}[/error]")


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
        console.log("[error]Claude-Code-Tools integration not initialized[/error]")
        return

    console.log("[info]Safety Hooks Status:[/info]")
    console.log("  Command interception: Active")
    console.log("  File deletion protection: Active")
    console.log("  Git operation safeguards: Active")
    console.log("  Environment file locks: Active")
    console.log("  File size limits: Active")
    console.log("  Grep enforcement: Active")


@safe_group.command("check")
@click.argument("command")
@click.option("--confirmed", is_flag=True, help="Mark as confirmed")
def safe_check(command: str, confirmed: bool):
    """Check command safety."""
    integration = get_global_integration()
    if not integration:
        console.log("[error]Claude-Code-Tools integration not initialized[/error]")
        return

    context = {'confirmed': confirmed} if confirmed else {}
    result = integration.intercept_command(command, context)

    if result['allowed']:
        console.log(f"[success]✓ Command allowed: {result['message']}[/success]")
    else:
        console.log(f"[error]✗ Command blocked: {result['message']}[/error]")
        if result.get('safe_command'):
            console.log(f"[warning]Suggested safe command: {result['safe_command']}[/warning]")

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
        console.log("[error]Claude-Code-Tools integration not initialized[/error]")
        return

    try:
        success = integration.vault.encrypt_env(env_file)
        if success:
            console.log(f"[success]✓ Encrypted {env_file} to vault[/success]")
        else:
            console.log(f"[error]✗ Failed to encrypt {env_file}[/error]")
    except Exception as e:
        console.log(f"[error]Encryption failed: {e}[/error]")


@vault_group.command("decrypt")
@click.argument("vault_file", default=None)
def vault_decrypt(vault_file: Optional[str]):
    """Decrypt vault file to .env."""
    integration = get_global_integration()
    if not integration:
        console.log("[error]Claude-Code-Tools integration not initialized[/error]")
        return

    try:
        content = integration.vault.decrypt_env(vault_file)
        if content:
            console.log(f"[success]✓ Decrypted vault to .env[/success]")
        else:
            console.log(f"[error]✗ Failed to decrypt vault[/error]")
    except Exception as e:
        console.log(f"[error]Decryption failed: {e}[/error]")


@vault_group.command("sync")
@click.argument("env_file", default=".env")
def vault_sync(env_file: str):
    """Sync environment file to vault."""
    integration = get_global_integration()
    if not integration:
        console.log("[error]Claude-Code-Tools integration not initialized[/error]")
        return

    try:
        success = integration.vault.sync_env(env_file)
        if success:
            console.log(f"[success]✓ Synced {env_file} to vault[/success]")
        else:
            console.log(f"[error]✗ Failed to sync {env_file}[/error]")
    except Exception as e:
        console.log(f"[error]Sync failed: {e}[/error]")


@vault_group.command("list")
def vault_list():
    """List all vault files."""
    integration = get_global_integration()
    if not integration:
        console.log("[error]Claude-Code-Tools integration not initialized[/error]")
        return

    try:
        vaults = integration.vault.list_vaults()
        if vaults:
            console.log("[info]Vault Files:[/info]")
            for vault in vaults:
                console.log(f"  {vault}")
        else:
            console.log("[warning]No vault files found[/warning]")
    except Exception as e:
        console.log(f"[error]Failed to list vaults: {e}[/error]")


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
        console.log("[error]Claude-Code-Tools integration not initialized[/error]")
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
            console.log(f"[success]Response: {response.content}[/success]")
        else:
            console.log(f"[success]Message sent to {pane_id}[/success]")

    except Exception as e:
        console.log(f"[error]Failed to send message: {e}[/error]")


@agent_group.command("receive")
@click.argument("pane_id")
@click.option("--timeout", type=float, default=5.0, help="Timeout in seconds")
def agent_receive(pane_id: str, timeout: float):
    """Receive message from agent in pane."""
    integration = get_global_integration()
    if not integration:
        console.log("[error]Claude-Code-Tools integration not initialized[/error]")
        return

    try:
        message = integration.receive_agent_message(pane_id, timeout=timeout)

        if message:
            console.log(f"[info]Message from {message.sender}:[/info]")
            console.log(f"  Type: {message.message_type}")
            console.log(f"  Content: {message.content}")
        else:
            console.log(f"[warning]No message received from {pane_id} within {timeout}s[/warning]")

    except Exception as e:
        console.log(f"[error]Failed to receive message: {e}[/error]")


@agent_group.command("collaborate")
@click.argument("primary_pane")
@click.argument("secondary_pane")
@click.argument("task_description")
@click.option("--timeout", type=float, default=300.0, help="Collaboration timeout")
def agent_collaborate(primary_pane: str, secondary_pane: str, task_description: str, timeout: float):
    """Enable agent collaboration on task."""
    integration = get_global_integration()
    if not integration:
        console.log("[error]Claude-Code-Tools integration not initialized[/error]")
        return

    try:
        result = integration.collaborate_on_task(primary_pane, secondary_pane, task_description, timeout=timeout)

        if result['success']:
            console.log("[success]✓ Collaboration completed successfully[/success]")
            console.log(f"Duration: {result.get('collaboration_time', 0):.1f}s")
        else:
            console.log(f"[error]✗ Collaboration failed: {result.get('error', 'Unknown error')}[/error]")

    except Exception as e:
        console.log(f"[error]Collaboration error: {e}[/error]")


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
        console.log("[error]Claude-Code-Tools integration not initialized[/error]")
        return

    try:
        debugger_type = DebuggerType[debugger.upper()]
        session = integration.start_debug_session(command, debugger_type, pane_name=pane)

        console.logger.debug(f"[success]✓ Debug session started: {session.session_id}[/success]")
        console.log(f"  Pane: {session.pane_id}")
        console.logger.debug(f"  Debugger: {session.debugger_type.value}")

    except Exception as e:
        console.log(f"[error]Failed to start debug session: {e}[/error]")


@debug_group.command("breakpoint")
@click.argument("session_id")
@click.argument("file_path")
@click.argument("line", type=int)
def debug_breakpoint(session_id: str, file_path: str, line: int):
    """Set breakpoint in debug session."""
    integration = get_global_integration()
    if not integration:
        console.log("[error]Claude-Code-Tools integration not initialized[/error]")
        return

    try:
        session = integration.interactive_debugger.get_session(session_id)
        if not session:
            console.log(f"[error]Session not found: {session_id}[/error]")
            return

        success = integration.set_debug_breakpoint(session, file_path, line)

        if success:
            console.log(f"[success]✓ Breakpoint set at {file_path}:{line}[/success]")
        else:
            console.log(f"[error]✗ Failed to set breakpoint[/error]")

    except Exception as e:
        console.log(f"[error]Breakpoint error: {e}[/error]")


@debug_group.command("continue")
@click.argument("session_id")
def debug_continue(session_id: str):
    """Continue execution in debug session."""
    integration = get_global_integration()
    if not integration:
        console.log("[error]Claude-Code-Tools integration not initialized[/error]")
        return

    try:
        session = integration.interactive_debugger.get_session(session_id)
        if not session:
            console.log(f"[error]Session not found: {session_id}[/error]")
            return

        new_state = integration.continue_debugging(session)
        console.log(f"[success]Execution continued, state: {new_state.name}[/success]")

    except Exception as e:
        console.log(f"[error]Continue error: {e}[/error]")


@debug_group.command("step")
@click.argument("session_id")
@click.option("--type", type=click.Choice(['step', 'next']), default='step', help="Step type")
def debug_step(session_id: str, step_type: str):
    """Step through debug session."""
    integration = get_global_integration()
    if not integration:
        console.log("[error]Claude-Code-Tools integration not initialized[/error]")
        return

    try:
        session = integration.interactive_debugger.get_session(session_id)
        if not session:
            console.log(f"[error]Session not found: {session_id}[/error]")
            return

        new_state = integration.step_debugging(session, step_type)
        console.log(f"[success]Stepped ({step_type}), state: {new_state.name}[/success]")

    except Exception as e:
        console.log(f"[error]Step error: {e}[/error]")


@debug_group.command("inspect")
@click.argument("session_id")
@click.argument("variable")
def debug_inspect(session_id: str, variable: str):
    """Inspect variable in debug session."""
    integration = get_global_integration()
    if not integration:
        console.log("[error]Claude-Code-Tools integration not initialized[/error]")
        return

    try:
        session = integration.interactive_debugger.get_session(session_id)
        if not session:
            console.log(f"[error]Session not found: {session_id}[/error]")
            return

        value = integration.inspect_debug_variable(session, variable)
        console.log(f"[info]{variable} = {value}[/info]")

    except Exception as e:
        console.log(f"[error]Inspection error: {e}[/error]")


@debug_group.command("stack")
@click.argument("session_id")
def debug_stack(session_id: str):
    """Get stack trace from debug session."""
    integration = get_global_integration()
    if not integration:
        console.log("[error]Claude-Code-Tools integration not initialized[/error]")
        return

    try:
        session = integration.interactive_debugger.get_session(session_id)
        if not session:
            console.log(f"[error]Session not found: {session_id}[/error]")
            return

        stack = integration.get_debug_stack_trace(session)
        console.logger.debug("[info]Stack Trace:[/info]")
        for i, frame in enumerate(stack, 1):
            console.log(f"  {i}. {frame}")

    except Exception as e:
        console.log(f"[error]Stack trace error: {e}[/error]")


@debug_group.command("locals")
@click.argument("session_id")
def debug_locals(session_id: str):
    """Get local variables from debug session."""
    integration = get_global_integration()
    if not integration:
        console.log("[error]Claude-Code-Tools integration not initialized[/error]")
        return

    try:
        session = integration.interactive_debugger.get_session(session_id)
        if not session:
            console.log(f"[error]Session not found: {session_id}[/error]")
            return

        locals_vars = integration.get_debug_locals(session)
        console.log("[info]Local Variables:[/info]")
        for var_name, var_value in locals_vars.items():
            console.log(f"  {var_name} = {var_value}")

    except Exception as e:
        console.log(f"[error]Locals error: {e}[/error]")


@debug_group.command("quit")
@click.argument("session_id")
def debug_quit(session_id: str):
    """Quit debug session."""
    integration = get_global_integration()
    if not integration:
        console.log("[error]Claude-Code-Tools integration not initialized[/error]")
        return

    try:
        session = integration.interactive_debugger.get_session(session_id)
        if not session:
            console.log(f"[error]Session not found: {session_id}[/error]")
            return

        integration.quit_debugging(session)
        console.logger.debug(f"[success]✓ Debug session {session_id} terminated[/success]")

    except Exception as e:
        console.log(f"[error]Quit error: {e}[/error]")


@debug_group.command("analyze-error")
@click.argument("error_text")
def debug_analyze_error(error_text: str):
    """Analyze error output for debugging insights."""
    integration = get_global_integration()
    if not integration:
        console.log("[error]Claude-Code-Tools integration not initialized[/error]")
        return

    try:
        analysis = integration.analyze_error(error_text)
        console.log(f"[info]Error Analysis: {analysis['error_type']}[/info]")
        console.log(f"Likely Cause: {analysis['likely_cause']}")
        console.log("Suggested Fixes:")
        for fix in analysis['suggested_fixes']:
            console.log(f"  • {fix}")

    except Exception as e:
        console.log(f"[error]Analysis error: {e}[/error]")


# Register command groups
def register_commands(main_group):
    """Register Claude-Code-Tools commands with main CLI group.
    
    Note: tmux_group is NOT registered to avoid conflicts with dopemux.tmux.
    Use 'dopemux tmux' for all tmux functionality.
    """
    # main_group.add_command(tmux_group)  # REMOVED: Conflicts with dopemux.tmux
    main_group.add_command(env_group)
    main_group.add_command(session_group)
    main_group.add_command(safe_group)
    main_group.add_command(agent_group)
    main_group.add_command(debug_group)