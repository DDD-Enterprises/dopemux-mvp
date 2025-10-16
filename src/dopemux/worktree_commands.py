"""
Git Worktree Management Commands for ADHD-Optimized Workflows.

Provides simple, direct worktree operations:
- switch: Change to an existing worktree
- list: Show all worktrees with ADHD-friendly display
- cleanup: Remove unused worktrees safely

ADHD Optimization: Clear, predictable commands with gentle guidance.

This module now uses the enhanced worktree manager backend for improved
safety, conflict detection, and ADHD optimizations.
"""

from pathlib import Path
from typing import Optional, List, Tuple
import subprocess
import sys
import os

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Import enhanced backend functions
from .worktree_manager_enhanced import (
    list_worktrees_adhd,
    switch_worktree_safe,
    cleanup_worktrees_safe,
)

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

    This is a backward compatibility wrapper that calls the enhanced backend.
    """
    # Use the enhanced backend which has ADHD optimizations (shows 3 most recent by default)
    list_worktrees_adhd(show_all=True)  # Show all for backward compatibility


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

    This is a backward compatibility wrapper that calls the enhanced backend.
    """
    # Use the enhanced backend with safe switching
    return switch_worktree_safe(target_name)


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

    This is a backward compatibility wrapper that calls the enhanced backend.
    """
    # Use the enhanced backend with safe cleanup
    cleanup_worktrees_safe(dry_run=dry_run)
