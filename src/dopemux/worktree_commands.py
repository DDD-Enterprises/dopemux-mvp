"""
Git Worktree Management Commands for ADHD-Optimized Workflows.

Provides simple, direct worktree operations:
- current: Get current worktree path with caching (MCP-optimized)
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
import tempfile
import time
import threading

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

# Cache for current worktree detection (30 second TTL)
_WORKTREE_CACHE = {
    "path": None,
    "timestamp": 0,
    "ttl": 30  # seconds
}

# Thread safety: Lock for atomic cache updates
# Important for Serena container which is persistent across requests
_CACHE_LOCK = threading.Lock()


def get_repo_root(fallback_cwd: bool = True) -> Optional[str]:
    """
    Get canonical repository root using git rev-parse with environment override.

    This is the authoritative way to determine the repository root,
    eliminating Path.cwd() dependency issues in worktree contexts.

    Args:
        fallback_cwd: If True and git fails, return Path.cwd() (default: True)

    Returns:
        Absolute path to repo root, or None if not in a git repo

    Environment:
        DOPEMUX_WORKSPACE_ROOT: Current worktree (PRIORITY - set by dopemux start)
        DOPEMUX_PROJECT_ROOT: Main repo root override (for testing)

    Performance:
        - With env var: 0ms (instant)
        - Without: 10-50ms (git subprocess)

    Example:
        # With dopemux start (instant):
        export DOPEMUX_WORKSPACE_ROOT="/Users/hue/code/ui-build"
        repo_root = get_repo_root()  # Returns /Users/hue/code/ui-build (0ms!)

        # Without (slower):
        repo_root = get_repo_root()  # Runs git rev-parse (10-50ms)
    """
    # 0. Check shared workspace first (FASTEST - instant!)
    env_workspace = os.environ.get('DOPEMUX_WORKSPACE_ROOT')
    if env_workspace:
        return str(Path(env_workspace).resolve())

    # 1. Check legacy override
    env_root = os.environ.get('DOPEMUX_PROJECT_ROOT')
    if env_root:
        return str(Path(env_root).resolve())

    # 2. Use git to get canonical repo root
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            return result.stdout.strip()

        # Git failed - fallback to cwd if requested
        if fallback_cwd:
            return str(Path.cwd().resolve())

        return None

    except Exception:
        # Exception - fallback to cwd if requested
        if fallback_cwd:
            return str(Path.cwd().resolve())
        return None


def get_current_worktree(use_cache: bool = True, quiet: bool = False) -> Optional[str]:
    """
    Get the current worktree path with intelligent caching.

    Optimized for MCP wrappers - reduces repeated git calls by caching
    the result for 30 seconds. Perfect for preventing memory bloat from
    spawning hundreds of git processes during MCP operations.

    Args:
        use_cache: Use cached value if available (default: True)
        quiet: Suppress console output (default: False for CLI, True for wrappers)

    Returns:
        Absolute path to current worktree, or None if not in a git repo

    Example:
        # From MCP wrapper (cached, quiet):
        workspace = get_current_worktree(quiet=True)

        # From CLI (fresh, with output):
        workspace = get_current_worktree(use_cache=False)
    """
    global _WORKTREE_CACHE

    # Check cache if enabled (thread-safe read)
    if use_cache:
        cached_path = None
        with _CACHE_LOCK:
            now = time.time()
            if (_WORKTREE_CACHE["path"] and
                now - _WORKTREE_CACHE["timestamp"] < _WORKTREE_CACHE["ttl"]):
                cached_path = _WORKTREE_CACHE["path"]

        # Print outside lock to avoid holding lock during I/O
        if cached_path:
            if not quiet:
                console.print(f"[dim]📍 Current worktree (cached): {cached_path}[/dim]")
            return cached_path

    # Detect worktree using git
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            worktree_path = result.stdout.strip()

            # Update cache (thread-safe write)
            with _CACHE_LOCK:
                _WORKTREE_CACHE["path"] = worktree_path
                _WORKTREE_CACHE["timestamp"] = time.time()

            if not quiet:
                console.print(f"[green]📍 Current worktree: {worktree_path}[/green]")

            return worktree_path
        else:
            if not quiet:
                console.print("[yellow]⚠️  Not in a git repository[/yellow]")
            return None

    except subprocess.TimeoutExpired:
        if not quiet:
            console.print("[red]❌ Git command timed out[/red]")
        return None
    except Exception as e:
        if not quiet:
            console.print(f"[red]❌ Error detecting worktree: {e}[/red]")
        return None


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

        # Get current repo root to determine which worktree we're in
        # Use git rev-parse instead of Path.cwd() for reliability
        current_dir = get_repo_root(fallback_cwd=True)

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
    list_worktrees_adhd(show_all=True, workspace_path=workspace_path)  # Show all for backward compatibility


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
    return switch_worktree_safe(target_name, workspace_path=workspace_path)


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
    cleanup_worktrees_safe(dry_run=dry_run, force=force, workspace_path=workspace_path)


def get_worktree_path(
    branch_name: str,
    workspace_path: Optional[Path] = None
) -> Optional[str]:
    """
    Get worktree path for shell integration (no directory change).

    This function is designed for shell integration where the shell function
    will execute cd. It provides the same fuzzy matching as switch_worktree
    but only returns the path.

    Args:
        branch_name: Exact or partial branch name to find
        workspace_path: Path to git repository (default: current directory)

    Returns:
        Absolute path to worktree if found, None otherwise
    """
    from .worktree_manager_enhanced import EnhancedWorktreeManager

    manager = EnhancedWorktreeManager(workspace_path)
    return manager.get_worktree_path_for_switch(branch_name)
