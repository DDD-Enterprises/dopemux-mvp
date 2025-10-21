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
import os
import shutil
import tempfile
from datetime import datetime
import sys
import logging

from .main_worktree_detector import MainWorktreeDetector, ProtectionTrigger
from .worktree_name_inferrer import WorktreeNameInferrer, suggest_worktree_name
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

logger = logging.getLogger(__name__)
console = Console()

_last_created_worktree: Optional[Path] = None
_COPY_DIRECTORIES = [
    ".dopemux",
    ".claude",
    ".claude-flow",
]

# Copy (not symlink) these single files into the new worktree
_COPY_FILES = [
    "litellm.config.yaml",
]


def consume_last_created_worktree() -> Optional[Path]:
    """Return and clear the most recently created worktree path."""
    global _last_created_worktree
    path = _last_created_worktree
    _last_created_worktree = None
    return path


def _record_last_created_worktree(path: Path) -> None:
    global _last_created_worktree
    _last_created_worktree = path


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
        # Remember for this run to suppress further warnings
        os.environ["DOPEMUX_ALLOW_MAIN"] = "1"
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

    # Ask about change migration
    console.print("\n[cyan]💭 Would you like to migrate your uncommitted changes to the new worktree?[/cyan]")
    console.print("  • [green]Yes (recommended)[/green] - Stash changes and apply in new worktree")
    console.print("  • [dim]No[/dim] - Create empty worktree (changes stay in main)\n")

    try:
        migrate_choice = console.input("[cyan]Migrate changes? [Y/n]: [/cyan]").strip().lower()
    except (KeyboardInterrupt, EOFError):
        console.print("\n[dim]Cancelled - staying in main[/dim]")
        return False

    migrate_changes = migrate_choice != "n"  # Default to Yes

    # Create the worktree with optional migration
    success = _execute_worktree_creation(workspace_path, worktree_name, migrate_changes=migrate_changes)

    if success:
        console.print(f"\n[green]✅ Worktree created: {worktree_name}[/green]")
        if migrate_changes:
            console.print("[green]✓ Changes migrated successfully[/green]")
        console.print("[green]🎯 Continuing in new worktree[/green]\n")
        return False
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


def _stash_changes(workspace_path: str) -> Optional[str]:
    """
    Stash uncommitted changes including untracked files.

    Returns:
        Stash name if successful, None otherwise
    """
    import subprocess

    try:
        stash_name = f"dopemux-migration-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        # Stash with untracked files
        result = subprocess.run(
            ["git", "stash", "push", "-u", "-m", stash_name],
            cwd=workspace_path,
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            logger.error(f"Git stash failed: {result.stderr}")
            console.print(f"[red]Failed to stash changes: {result.stderr.strip()}[/red]")
            return None

        console.print(f"[green]✓ Stashed changes: {stash_name}[/green]")
        return stash_name

    except subprocess.TimeoutExpired:
        logger.error("Git stash timed out")
        console.print("[red]Git stash timed out[/red]")
        return None
    except Exception as e:
        logger.error(f"Failed to stash changes: {e}")
        console.print(f"[red]Error stashing: {e}[/red]")
        return None


def _pop_stash(workspace_path: str, stash_name: str) -> bool:
    """
    Pop stashed changes in new worktree.

    Returns:
        True if successful, False otherwise
    """
    import subprocess

    try:
        # Find stash by name
        result = subprocess.run(
            ["git", "stash", "list"],
            cwd=workspace_path,
            capture_output=True,
            text=True,
            timeout=5
        )

        # Find stash index
        stash_index = None
        for line in result.stdout.splitlines():
            if stash_name in line:
                # Format: "stash@{0}: On main: dopemux-migration-..."
                stash_index = line.split(":")[0].strip()
                break

        if not stash_index:
            logger.warning(f"Stash not found: {stash_name}")
            console.print(f"[yellow]⚠️ Could not find stash: {stash_name}[/yellow]")
            return False

        # Pop the stash
        result = subprocess.run(
            ["git", "stash", "pop", stash_index],
            cwd=workspace_path,
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            # Check if it's a conflict
            if "CONFLICT" in result.stdout or "CONFLICT" in result.stderr:
                console.print("[yellow]⚠️ Merge conflicts detected - please resolve manually[/yellow]")
                console.print(f"[dim]Run 'git status' to see conflicts[/dim]")
                return True  # Partial success - stash applied but has conflicts
            else:
                logger.error(f"Git stash pop failed: {result.stderr}")
                console.print(f"[red]Failed to apply stash: {result.stderr.strip()}[/red]")
                return False

        console.print(f"[green]✓ Applied changes from stash[/green]")
        return True

    except subprocess.TimeoutExpired:
        logger.error("Git stash pop timed out")
        console.print("[red]Git stash pop timed out[/red]")
        return False
    except Exception as e:
        logger.error(f"Failed to pop stash: {e}")
        console.print(f"[red]Error applying stash: {e}[/red]")
        return False


def _execute_worktree_creation(
    workspace_path: str,
    worktree_name: str,
    migrate_changes: bool = False
) -> bool:
    """
    Execute git worktree creation with optional change migration.

    Args:
        workspace_path: Absolute path to workspace root
        worktree_name: Name for new worktree/branch
        migrate_changes: If True, stash changes and apply in new worktree

    Returns:
        True if successful, False otherwise
    """
    import subprocess
    import os
    from datetime import datetime

    workspace = Path(workspace_path)

    # Create worktree in sibling directory
    worktree_path = workspace.parent / worktree_name

    stash_name = None
    snapshot_path = _snapshot_scaffolding(workspace)

    try:
        # Step 1: Stash changes if migration requested
        if migrate_changes:
            console.print("\n[cyan]📦 Migrating changes to new worktree...[/cyan]")
            stash_name = _stash_changes(workspace_path)
            if not stash_name:
                console.print("[yellow]⚠️ Could not stash changes - creating empty worktree[/yellow]")
                migrate_changes = False  # Skip migration
            elif snapshot_path:
                _sync_project_scaffolding(snapshot_path, workspace)

        # Step 2: Create worktree with new branch
        console.print(f"[cyan]🌳 Creating worktree: {worktree_name}[/cyan]")
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

            # Rollback: Pop stash if we stashed
            if stash_name:
                console.print("[cyan]Rolling back stash...[/cyan]")
                subprocess.run(
                    ["git", "stash", "pop"],
                    cwd=workspace_path,
                    capture_output=True,
                    timeout=5
                )
            return False

        console.print(f"[green]✓ Created worktree at: {worktree_path}[/green]")

        # Step 3: Apply stash in new worktree if migration requested
        if migrate_changes and stash_name:
            console.print(f"[cyan]📥 Applying changes in new worktree...[/cyan]")

            # Switch to new worktree
            original_dir = os.getcwd()
            try:
                os.chdir(worktree_path)

                # Pop stash in new worktree
                success = _pop_stash(str(worktree_path), stash_name)

                # Switch back
                os.chdir(original_dir)

                if not success:
                    console.print("[yellow]⚠️ Changes not fully migrated - check stash manually[/yellow]")
                    _record_last_created_worktree(worktree_path)
                    return True  # Worktree created, but migration incomplete
                elif snapshot_path:
                    _sync_project_scaffolding(snapshot_path, worktree_path, symlink_root=workspace)

            except Exception as e:
                os.chdir(original_dir)  # Ensure we switch back
                logger.error(f"Failed during migration: {e}")
                console.print(f"[yellow]⚠️ Migration error: {e}[/yellow]")
                _record_last_created_worktree(worktree_path)
                return True  # Worktree created, but migration failed

        if snapshot_path:
            _sync_project_scaffolding(snapshot_path, worktree_path, symlink_root=workspace)

        _record_last_created_worktree(worktree_path)
        return True

    except subprocess.TimeoutExpired:
        logger.error("Git worktree add timed out")
        console.print("[red]Git command timed out[/red]")

        if stash_name:
            subprocess.run(
                ["git", "stash", "pop"],
                cwd=workspace_path,
                capture_output=True,
                timeout=5
            )
        return False

    except Exception as e:
        logger.error(f"Failed to create worktree: {e}")
        console.print(f"[red]Error: {e}[/red]")

        if stash_name:
            subprocess.run(
                ["git", "stash", "pop"],
                cwd=workspace_path,
                capture_output=True,
                timeout=5
            )
        return False

    finally:
        if snapshot_path:
            shutil.rmtree(snapshot_path, ignore_errors=True)


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


def _sync_project_scaffolding(source: Path, destination: Path, symlink_root: Optional[Path] = None) -> None:
    """Copy essential Dopemux scaffolding files into a new worktree."""
    for item in _COPY_DIRECTORIES:
        src_path = source / item
        if not src_path.exists():
            continue

        dest_path = destination / item
        try:
            if src_path.is_dir():
                dest_path.mkdir(parents=True, exist_ok=True)
                shutil.copytree(src_path, dest_path, dirs_exist_ok=True)
            else:
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_path, dest_path)
        except Exception as exc:  # pragma: no cover - best-effort copy
            logger.warning("Failed to copy %s: %s", item, exc)

    # Copy single-file scaffolding items
    for file_name in _COPY_FILES:
        src_file = source / file_name
        if not src_file.exists():
            continue
        dest_file = destination / file_name
        try:
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            if dest_file.exists() or dest_file.is_symlink():
                try:
                    dest_file.unlink()
                except Exception:
                    pass
            shutil.copy2(src_file, dest_file)
        except Exception as exc:  # pragma: no cover
            logger.warning("Failed to copy %s: %s", file_name, exc)


def _snapshot_scaffolding(source: Path) -> Optional[Path]:
    """Capture scaffolding into a temporary directory and return its path."""
    temp_dir = Path(tempfile.mkdtemp(prefix="dopemux-scaffold-"))
    copied = False

    for item in _COPY_DIRECTORIES:
        src_path = source / item
        if not src_path.exists():
            continue

        dest_path = temp_dir / item
        try:
            if src_path.is_dir():
                dest_path.mkdir(parents=True, exist_ok=True)
                shutil.copytree(src_path, dest_path, dirs_exist_ok=True)
            else:
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_path, dest_path)
            copied = True
        except Exception as exc:  # pragma: no cover - best-effort copy
            logger.warning("Failed to snapshot %s: %s", item, exc)

    for file_name in _COPY_FILES:
        src_file = source / file_name
        if not src_file.exists():
            continue
        dest_file = temp_dir / file_name
        try:
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dest_file)
            copied = True
        except Exception as exc:  # pragma: no cover
            logger.warning("Failed to snapshot %s: %s", file_name, exc)

    if not copied:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return None

    return temp_dir
