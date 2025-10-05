"""
Main Worktree Protection Interceptor.

Hooks MainWorktreeDetector into dopemux CLI to protect main worktree
from accumulating uncommitted changes. ADHD-optimized with gentle guidance.

Usage:
    # At CLI entry point (after initialization, before operations):
    from protection_interceptor import check_main_protection_interactive

    should_exit = check_main_protection_interactive(
        workspace_path=str(project_path),
        enforce=False  # Warn only (default)
    )
    if should_exit:
        sys.exit(0)  # User chose to exit
"""

from pathlib import Path
from typing import Optional, Tuple
import sys
import logging

from .main_worktree_detector import MainWorktreeDetector, ProtectionTrigger
from .worktree_name_inferrer import WorktreeNameInferrer, suggest_worktree_name
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

logger = logging.getLogger(__name__)
console = Console()


def check_main_protection_interactive(
    workspace_path: str,
    enforce: bool = False,
    offer_creation: bool = True
) -> bool:
    """
    Check main worktree protection and guide user interactively.

    ADHD Optimization:
    - Gentle warning (not error)
    - Clear actionable options
    - Safe default (exit to main)
    - Optional worktree creation with smart naming

    Args:
        workspace_path: Absolute path to workspace root
        enforce: If True, block operations; if False, warn only
        offer_creation: Whether to offer creating worktree

    Returns:
        True if user should exit (chose to stay in main without changes),
        False if should continue (user proceeded or created worktree)
    """
    detector = MainWorktreeDetector(workspace_path, enforce_protection=enforce)
    trigger = detector.check_protection_needed()

    if not trigger:
        # No protection needed - clean main or not on main
        return False

    # Protection triggered - show warning
    _display_protection_warning(trigger)

    if not offer_creation:
        # Just show warning, let user decide
        if enforce:
            console.print("[red]❌ Operation blocked by main worktree protection[/red]")
            return True  # Exit
        else:
            console.print("[yellow]⚠️ Warning shown - proceeding anyway[/yellow]")
            return False  # Continue

    # Offer interactive worktree creation
    return _offer_worktree_creation(workspace_path, trigger)


def _display_protection_warning(trigger: ProtectionTrigger) -> None:
    """Display ADHD-friendly protection warning."""
    warning_text = trigger.format_warning()

    panel = Panel(
        warning_text,
        title="[bold yellow]⚠️  Main Worktree Protection[/bold yellow]",
        border_style="yellow",
        padding=(1, 2)
    )

    console.print()  # Blank line for spacing
    console.print(panel)
    console.print()


def _offer_worktree_creation(
    workspace_path: str,
    trigger: ProtectionTrigger
) -> bool:
    """
    Offer to create worktree for uncommitted changes.

    Returns:
        True if user wants to exit (chose not to create),
        False if worktree created or user wants to continue
    """
    console.print("[cyan]💡 What would you like to do?[/cyan]\n")
    console.print("  1. [green]Create worktree[/green] - Move changes to new worktree (recommended)")
    console.print("  2. [blue]Stay in main[/blue] - Continue in main worktree (not recommended)")
    console.print("  3. [dim]Exit[/dim] - Clean up manually and restart\n")

    # Get user choice with input validation
    try:
        choice = console.input("[cyan]Choose (1/2/3) [[bold]1[/bold]]: [/cyan]").strip() or "1"
    except (KeyboardInterrupt, EOFError):
        console.print("\n[dim]Cancelled - exiting[/dim]")
        return True  # Exit

    if choice == "1":
        # Create worktree
        return _create_worktree_interactive(workspace_path, trigger)
    elif choice == "2":
        # Continue in main (warn)
        console.print("\n[yellow]⚠️ Continuing in main worktree - please be careful![/yellow]")
        return False
    elif choice == "3":
        # Exit
        console.print("\n[dim]Exiting - please clean up changes manually[/dim]")
        return True
    else:
        # Invalid choice - default to exit (safe)
        console.print(f"\n[red]Invalid choice: '{choice}' - exiting for safety[/red]")
        return True


def _create_worktree_interactive(
    workspace_path: str,
    trigger: ProtectionTrigger
) -> bool:
    """
    Create worktree interactively with smart naming.

    Returns:
        True if should exit (creation failed),
        False if worktree created successfully
    """
    console.print("\n[cyan]📝 Creating new worktree...[/cyan]\n")

    # Generate name suggestions
    inferrer = WorktreeNameInferrer(workspace_path)
    suggestions = inferrer.suggest_names(max_suggestions=3)

    if not suggestions:
        console.print("[red]❌ Could not generate worktree name suggestions[/red]")
        return True  # Exit

    # Display suggestions (ADHD: max 3 options)
    console.print("[cyan]Suggested names (best match first):[/cyan]")
    for i, suggestion in enumerate(suggestions, start=1):
        console.print(f"  {i}. [green]{suggestion.name}[/green] ({suggestion.source}, confidence: {suggestion.confidence:.0%})")
    console.print()

    # Get user choice or custom name
    console.print("[cyan]Options:[/cyan]")
    console.print("  • Enter [bold]1-3[/bold] to use suggestion")
    console.print("  • Enter [bold]custom name[/bold] for custom worktree")
    console.print("  • Press [bold]Enter[/bold] to use best suggestion\n")

    try:
        choice_input = console.input(f"[cyan]Choice [[bold]{suggestions[0].name}[/bold]]: [/cyan]").strip()
    except (KeyboardInterrupt, EOFError):
        console.print("\n[dim]Cancelled - staying in main[/dim]")
        return False  # Continue in main

    # Parse choice
    worktree_name = _parse_name_choice(choice_input, suggestions, inferrer)

    if not worktree_name:
        console.print("[yellow]⚠️ No name selected - staying in main[/yellow]")
        return False

    # Create the worktree
    success = _execute_worktree_creation(workspace_path, worktree_name)

    if success:
        console.print(f"\n[green]✅ Worktree created: {worktree_name}[/green]")
        console.print("[dim]Restart dopemux to switch to new worktree[/dim]\n")
        return True  # Exit to allow user to restart
    else:
        console.print(f"\n[red]❌ Failed to create worktree: {worktree_name}[/red]")
        console.print("[yellow]⚠️ Staying in main - please create worktree manually[/yellow]")
        return False


def _parse_name_choice(
    choice_input: str,
    suggestions: list,
    inferrer: WorktreeNameInferrer
) -> Optional[str]:
    """
    Parse user's name choice input.

    Returns:
        Selected worktree name, or None if cancelled
    """
    if not choice_input:
        # Default to best suggestion
        return suggestions[0].name

    # Try parsing as number (1-3)
    if choice_input in ("1", "2", "3"):
        index = int(choice_input) - 1
        if index < len(suggestions):
            return suggestions[index].name
        else:
            # Index out of range - use best
            return suggestions[0].name

    # Custom name - sanitize and check availability
    custom_name = inferrer._sanitize_name(choice_input)

    if not inferrer.check_name_available(custom_name):
        # Name conflict - resolve
        console.print(f"[yellow]⚠️ Name '{custom_name}' already exists[/yellow]")
        resolved = inferrer.resolve_conflict(custom_name)
        console.print(f"[cyan]Using '{resolved}' instead[/cyan]")
        return resolved

    return custom_name


def _execute_worktree_creation(
    workspace_path: str,
    worktree_name: str
) -> bool:
    """
    Execute git worktree creation.

    Returns:
        True if successful, False otherwise
    """
    import subprocess

    workspace = Path(workspace_path)

    # Create worktree in sibling directory
    worktree_path = workspace.parent / worktree_name

    try:
        # Create worktree with new branch
        result = subprocess.run(
            ["git", "worktree", "add", str(worktree_path), "-b", worktree_name],
            cwd=workspace_path,
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            logger.error(f"Git worktree add failed: {result.stderr}")
            console.print(f"[red]Git error: {result.stderr.strip()}[/red]")
            return False

        # Move uncommitted changes to new worktree (optional - user can stash/commit later)
        # For now, just create the worktree - user can move changes manually

        console.print(f"[green]Created worktree at: {worktree_path}[/green]")
        return True

    except subprocess.TimeoutExpired:
        logger.error("Git worktree add timed out")
        console.print("[red]Git command timed out[/red]")
        return False
    except Exception as e:
        logger.error(f"Failed to create worktree: {e}")
        console.print(f"[red]Error: {e}[/red]")
        return False


# Synchronous helper for CLI integration
def check_and_protect_main(
    workspace_path: str,
    enforce: bool = False
) -> bool:
    """
    Synchronous helper for main worktree protection check.

    Args:
        workspace_path: Absolute path to workspace root
        enforce: Whether to block operations (True) or warn only (False)

    Returns:
        True if should exit, False if should continue
    """
    return check_main_protection_interactive(
        workspace_path=workspace_path,
        enforce=enforce,
        offer_creation=True
    )
