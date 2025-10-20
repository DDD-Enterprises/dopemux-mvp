"""
Workspace Detection Utilities for Dopemux

Ensures consistent workspace root detection across CLI, MCP servers, and multi-instance support.
Critical for ADHD context preservation - wrong workspace = wrong context, decisions, and history.
"""

import subprocess
from pathlib import Path
from typing import Optional


def get_workspace_root(start_path: Optional[Path] = None) -> Path:
    """
    Detect workspace root directory with git-aware detection.

    This is CRITICAL for ADHD optimization:
    - Context manager needs correct path to restore sessions
    - ConPort needs correct workspace_id to log decisions
    - Worktree detection needs git root for multi-instance isolation

    Detection order (matches dope-context pattern):
    1. Git root (if in git repo) - PRIMARY for worktree support
    2. Directory with pyproject.toml or package.json - Project markers
    3. Current working directory - Fallback only

    Args:
        start_path: Starting directory (defaults to cwd)

    Returns:
        Workspace root path (always absolute, resolved)

    Examples:
        >>> # From subdirectory
        >>> os.chdir("/Users/hue/code/dopemux-mvp/src/dopemux")
        >>> get_workspace_root()
        Path("/Users/hue/code/dopemux-mvp")  # ✅ Git root, not cwd

        >>> # From worktree
        >>> os.chdir("/Users/hue/code/dopemux-mvp-feature")
        >>> get_workspace_root()
        Path("/Users/hue/code/dopemux-mvp-feature")  # ✅ Worktree root
    """
    if start_path is None:
        start_path = Path.cwd()

    current = start_path.resolve()

    # 1. Try git root detection (PRIMARY - supports worktrees!)
    try:
        # git rev-parse --show-toplevel returns worktree root for worktrees
        # and main repo root for main repo - exactly what we need!
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(current),
            capture_output=True,
            text=True,
            check=True,
            timeout=2
        )
        git_root = Path(result.stdout.strip())
        if git_root.exists():
            return git_root.resolve()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        # Not in git repo or git not available
        pass

    # 2. Try project markers (pyproject.toml, package.json, etc.)
    markers = ["pyproject.toml", "package.json", "Cargo.toml", "go.mod", ".dopemux"]

    current = start_path.resolve()
    while current != current.parent:
        for marker in markers:
            if (current / marker).exists():
                return current
        current = current.parent

    # 3. Fallback to start_path (better than failing)
    return start_path.resolve()


def is_worktree(workspace_path: Path) -> bool:
    """
    Check if workspace is a git worktree (not main repo).

    Useful for multi-instance logic:
    - Main repo (instance A): is_worktree() = False
    - Worktrees (instance B-E): is_worktree() = True

    Args:
        workspace_path: Path to check

    Returns:
        True if workspace is a git worktree, False otherwise
    """
    try:
        # Worktrees have .git as a file (not directory)
        git_path = workspace_path / ".git"
        if git_path.is_file():
            return True

        # Double-check with git command
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=str(workspace_path),
            capture_output=True,
            text=True,
            timeout=2
        )

        if result.returncode == 0:
            # In a work tree, check if it's a worktree
            worktree_result = subprocess.run(
                ["git", "worktree", "list"],
                cwd=str(workspace_path),
                capture_output=True,
                text=True,
                timeout=2
            )

            if worktree_result.returncode == 0:
                # Check if current path is listed as a worktree (not main)
                lines = worktree_result.stdout.strip().split("\n")
                if len(lines) > 1:  # More than just main worktree
                    # Current path in worktree list but not first (main)?
                    current_str = str(workspace_path.resolve())
                    for line in lines[1:]:  # Skip first (main)
                        if current_str in line:
                            return True

        return False

    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return False


def get_git_branch(workspace_path: Path) -> Optional[str]:
    """
    Get current git branch for workspace.

    Args:
        workspace_path: Workspace to check

    Returns:
        Branch name or None if not in git repo
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(workspace_path),
            capture_output=True,
            text=True,
            check=True,
            timeout=2
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return None
