"""
Git Worktree Management Commands for ADHD-Optimized Workflows.

Provides simple, direct worktree operations:
- switch: Change to an existing worktree
- list: Show all worktrees with ADHD-friendly display
- cleanup: Remove unused worktrees safely

ADHD Optimization: Clear, predictable commands with gentle guidance.
"""

from pathlib import Path
from typing import Optional, List, Tuple
import subprocess
import sys
import os

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def get_worktrees(workspace_path: Path) -> List[Tuple[str, str, str]]:
    """
    Get list of all git worktrees.

    Args:
        workspace_path: Path to git repository

    Returns:
        List of (path, branch, is_current) tuples
    """
    try:
        result = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=workspace_path,
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            return []

        worktrees = []
        current_wt = {}

        # Get current directory to determine which worktree we're in
        current_dir = str(Path.cwd().resolve())

        for line in result.stdout.splitlines():
            if line.startswith("worktree "):
                if current_wt:
                    # Check if this worktree path matches current directory
                    wt_path = current_wt["path"]
                    is_current = str(Path(wt_path).resolve()) == current_dir

                    worktrees.append((
                        wt_path,
                        current_wt.get("branch", ""),
                        is_current
                    ))
                current_wt = {"path": line.split(" ", 1)[1]}

            elif line.startswith("branch "):
                branch_ref = line.split(" ", 1)[1]
                branch_name = branch_ref.replace("refs/heads/", "")
                current_wt["branch"] = branch_name

        # Add last worktree
        if current_wt:
            wt_path = current_wt["path"]
            is_current = str(Path(wt_path).resolve()) == current_dir

            worktrees.append((
                wt_path,
                current_wt.get("branch", ""),
                is_current
            ))

        return worktrees

    except Exception as e:
        console.print(f"[red]Failed to list worktrees: {e}[/red]")
        return []


def get_worktree_status(worktree_path: str) -> str:
    """
    Get git status for a worktree (clean/dirty).

    Args:
        worktree_path: Path to worktree

    Returns:
        Status string: "clean", "dirty", "unknown"
    """
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=worktree_path,
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            return "unknown"

        return "clean" if not result.stdout.strip() else "dirty"

    except Exception:
        return "unknown"


def list_worktrees(workspace_path: Optional[Path] = None) -> None:
    """
    List all git worktrees with ADHD-friendly display.

    Args:
        workspace_path: Path to git repository (default: current directory)
    """
    workspace = workspace_path or Path.cwd()

    # Get worktrees
    worktrees = get_worktrees(workspace)

    if not worktrees:
        console.print("[yellow]No worktrees found[/yellow]")
        console.print("[dim]💡 Tip: Use 'git worktree add' or the protection interceptor to create worktrees[/dim]")
        return

    # Create ADHD-friendly table
    table = Table(title="🌳 Git Worktrees", show_header=True)
    table.add_column("Branch", style="green", no_wrap=True)
    table.add_column("Path", style="cyan")
    table.add_column("Status", style="dim")
    table.add_column("Current", style="bold yellow")

    for path, branch, is_current in worktrees:
        status = get_worktree_status(path)

        # Color-code status
        if status == "clean":
            status_display = "[green]✓ clean[/green]"
        elif status == "dirty":
            status_display = "[yellow]● dirty[/yellow]"
        else:
            status_display = "[dim]? unknown[/dim]"

        # Mark current worktree
        current_marker = "→" if is_current else ""

        # Shorten path for readability
        try:
            short_path = Path(path).name if Path(path).parent == workspace.parent else path
        except Exception:
            short_path = path

        table.add_row(branch, short_path, status_display, current_marker)

    console.print(table)
    console.print(f"\n[dim]💡 Tip: Use 'dopemux switch <branch>' to switch worktrees[/dim]")


def switch_worktree(
    workspace_path: Path,
    target_name: str,
    fuzzy_match: bool = True
) -> bool:
    """
    Switch to an existing worktree.

    Args:
        workspace_path: Path to git repository
        target_name: Branch name or partial name to switch to
        fuzzy_match: Allow fuzzy matching if exact match not found

    Returns:
        True if successful, False otherwise
    """
    # Get all worktrees
    worktrees = get_worktrees(workspace_path)

    if not worktrees:
        console.print("[red]No worktrees found[/red]")
        return False

    # Find matching worktree
    exact_match = None
    fuzzy_matches = []

    for path, branch, is_current in worktrees:
        if branch == target_name:
            exact_match = (path, branch, is_current)
            break
        elif fuzzy_match and target_name.lower() in branch.lower():
            fuzzy_matches.append((path, branch, is_current))

    # Determine target
    target = None

    if exact_match:
        target = exact_match
    elif len(fuzzy_matches) == 1:
        target = fuzzy_matches[0]
        console.print(f"[dim]Fuzzy matched '{target_name}' → '{target[1]}'[/dim]")
    elif len(fuzzy_matches) > 1:
        console.print(f"[yellow]Multiple matches found for '{target_name}':[/yellow]")
        for i, (_, branch, _) in enumerate(fuzzy_matches, 1):
            console.print(f"  {i}. {branch}")
        console.print("\n[dim]Please specify the exact branch name[/dim]")
        return False
    else:
        console.print(f"[red]No worktree found matching '{target_name}'[/red]")
        console.print("\n[dim]Available worktrees:[/dim]")
        for _, branch, _ in worktrees:
            console.print(f"  • {branch}")
        return False

    # Check if already on target
    if target[2]:  # is_current
        console.print(f"[yellow]Already on worktree '{target[1]}'[/yellow]")
        return True

    # Switch to worktree
    console.print(f"[cyan]Switching to worktree '{target[1]}'...[/cyan]")

    try:
        # Git doesn't have a "switch worktree" command, so we guide the user
        console.print(f"\n[green]✓ Worktree path: {target[0]}[/green]")
        console.print("\n[bold]To switch to this worktree:[/bold]")
        console.print(f"  cd {target[0]}")
        console.print("\n[dim]💡 Tip: Dopemux will automatically detect the worktree change[/dim]")

        # Note: We can't actually change the shell's directory from Python
        # The user needs to run `cd` themselves
        return True

    except Exception as e:
        console.print(f"[red]Failed to switch: {e}[/red]")
        return False


def cleanup_worktrees(
    workspace_path: Path,
    force: bool = False,
    dry_run: bool = False
) -> None:
    """
    Clean up unused worktrees safely.

    Args:
        workspace_path: Path to git repository
        force: Skip confirmation prompts
        dry_run: Show what would be removed without removing
    """
    console.print("[cyan]🧹 Scanning for unused worktrees...[/cyan]\n")

    # Get all worktrees
    worktrees = get_worktrees(workspace_path)

    if not worktrees:
        console.print("[yellow]No worktrees found[/yellow]")
        return

    # Get current worktree
    current_wt = None
    for path, branch, is_current in worktrees:
        if is_current:
            current_wt = branch
            break

    # Find candidates for cleanup
    cleanup_candidates = []

    for path, branch, is_current in worktrees:
        # Skip current worktree
        if is_current:
            continue

        # Skip main/master
        if branch in ("main", "master"):
            console.print(f"[dim]Skipping main worktree: {branch}[/dim]")
            continue

        # Check if worktree is clean
        status = get_worktree_status(path)

        if status == "clean":
            cleanup_candidates.append((path, branch, "clean"))
        elif status == "dirty":
            console.print(f"[yellow]⚠️  Worktree has uncommitted changes: {branch}[/yellow]")
            console.print(f"[dim]   Path: {path}[/dim]")

            if force:
                console.print(f"[red]   Force mode: Will remove anyway[/red]")
                cleanup_candidates.append((path, branch, "dirty"))
            else:
                console.print(f"[dim]   Skipping (use --force to remove anyway)[/dim]")

    # Display cleanup candidates
    if not cleanup_candidates:
        console.print("[green]✓ No worktrees need cleanup[/green]")
        return

    console.print(f"\n[yellow]Found {len(cleanup_candidates)} worktree(s) to remove:[/yellow]\n")

    table = Table()
    table.add_column("Branch", style="cyan")
    table.add_column("Path", style="dim")
    table.add_column("Status", style="yellow")

    for path, branch, status in cleanup_candidates:
        try:
            short_path = Path(path).name
        except Exception:
            short_path = path

        status_display = "clean" if status == "clean" else "[red]dirty (forced)[/red]"
        table.add_row(branch, short_path, status_display)

    console.print(table)

    # Dry run mode
    if dry_run:
        console.print("\n[dim]Dry run - no changes made[/dim]")
        return

    # Confirmation
    if not force:
        console.print("\n[yellow]⚠️  This will permanently remove these worktrees[/yellow]")

        from rich.prompt import Confirm
        if not Confirm.ask("Proceed with cleanup?", default=False):
            console.print("[yellow]Cleanup cancelled[/yellow]")
            return

    # Remove worktrees
    console.print("\n[cyan]Removing worktrees...[/cyan]")

    for path, branch, status in cleanup_candidates:
        try:
            result = subprocess.run(
                ["git", "worktree", "remove", path, "--force" if force else ""],
                cwd=workspace_path,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                console.print(f"[green]✓ Removed worktree: {branch}[/green]")
            else:
                console.print(f"[red]✗ Failed to remove {branch}: {result.stderr.strip()}[/red]")

        except Exception as e:
            console.print(f"[red]✗ Error removing {branch}: {e}[/red]")

    console.print("\n[green]✓ Cleanup complete[/green]")
