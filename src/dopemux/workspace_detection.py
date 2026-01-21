"""Unified workspace detection for all Dopemux components.

This module provides consistent workspace detection across:
- Main repository
- Git worktrees (critical: worktrees have .git as FILE, not directory!)
- Non-git projects
- All MCP servers (ConPort, Serena, Dope-Context)

Priority order:
1. DOPEMUX_WORKSPACE_ROOT env var (explicit override)
2. git rev-parse --show-toplevel (works for worktrees AND main repo!)
3. Project markers (pyproject.toml, package.json, .git file/dir)
4. Current directory (fallback)

ADHD Benefits:
- Zero manual configuration (auto-detection)
- Works identically in main repo and worktrees
- Clear error messages with actionable fixes
- Consistent behavior across all components
"""

from pathlib import Path
import subprocess
import os
from typing import Optional
import logging

from .global_config import get_default_workspace, set_default_workspace

logger = logging.getLogger(__name__)

DEFAULT_WORKSPACE_FILE = Path.home() / ".dopemux" / "default_workspace"


def _load_persisted_default_workspace() -> Optional[Path]:
    """
    Load the last known Dopemux workspace recorded on disk.

    Returns:
        Path if the persisted location exists, otherwise None.
    """
    # Prefer the new global config (supports multi-workspace concurrency)
    default_from_config = get_default_workspace()
    if default_from_config:
        return default_from_config

    try:
        if not DEFAULT_WORKSPACE_FILE.exists():
            return None
        value = DEFAULT_WORKSPACE_FILE.read_text(encoding="utf-8").strip()
        if not value:
            return None
        candidate = Path(value).expanduser().resolve()
        if candidate.exists() and candidate.is_dir():
            return candidate
    except OSError as exc:
        logger.debug(f"Unable to read default workspace file: {exc}")
    return None


def persist_workspace_root(workspace_path: Path) -> None:
    """
    Persist a workspace path so Dopemux can be launched from any directory.

    Args:
        workspace_path: Project root to persist.
    """
    try:
        workspace_path = workspace_path.expanduser().resolve()
        if not workspace_path.exists():
            logger.debug("Skipping workspace persistence (missing path: %s)", workspace_path)
            return
        # Update the global config first so scripts and other repos can source
        # their environment from ~/.dopemux/workspaces/<slug>.
        set_default_workspace(workspace_path)
        DEFAULT_WORKSPACE_FILE.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_WORKSPACE_FILE.write_text(str(workspace_path), encoding="utf-8")
    except OSError as exc:
        logger.debug(f"Unable to persist workspace root: {exc}")


def get_workspace_root(start_path: Optional[Path] = None) -> Path:
    """
    Detect workspace root with full git worktree support.

    This is the SINGLE SOURCE OF TRUTH for workspace detection.
    All Dopemux components MUST use this function.

    Args:
        start_path: Starting directory for detection (default: cwd)

    Returns:
        Path: Absolute path to workspace root

    Raises:
        Never raises - always returns valid Path (falls back to cwd if needed)

    Examples:
        >>> # In main repo
        >>> get_workspace_root()
        Path('/Users/hue/code/dopemux-mvp')

        >>> # In worktree
        >>> get_workspace_root()
        Path('/Users/hue/code/ui-build')  # NOT main repo!

        >>> # With explicit override
        >>> os.environ['DOPEMUX_WORKSPACE_ROOT'] = '/custom/path'
        >>> get_workspace_root()
        Path('/custom/path')
    """
    current = Path(start_path or os.getcwd()).resolve()

    # Priority 1: Explicit environment variable override
    env_workspace = os.getenv("DOPEMUX_WORKSPACE_ROOT")
    if env_workspace:
        workspace_path = Path(env_workspace).resolve()
        if workspace_path.exists() and workspace_path.is_dir():
            logger.debug(f"Workspace detected via DOPEMUX_WORKSPACE_ROOT: {workspace_path}")
            return workspace_path
        else:
            logger.warning(
                f"DOPEMUX_WORKSPACE_ROOT set to invalid path: {env_workspace}. "
                f"Falling back to auto-detection."
            )

    # Priority 2: Git detection (PRIMARY - supports worktrees!)
    # This is THE CORRECT WAY to detect worktrees
    # git rev-parse --show-toplevel returns:
    #   - Worktree root for worktrees
    #   - Main repo root for main repo
    # This is exactly what we need!
    try:
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
            logger.debug(f"Workspace detected via git: {git_root}")
            return git_root.resolve()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
        logger.debug(f"Git detection failed: {e}. Trying project markers.")
        persisted = _load_persisted_default_workspace()
        if persisted:
            logger.debug(f"Workspace detected via persisted default: {persisted}")
            return persisted

    # Priority 3: Project marker detection (fallback for non-git projects)
    # Walk up directory tree looking for common project markers
    project_markers = [
        "pyproject.toml",
        "package.json",
        ".git",  # Could be file (worktree) or directory (main repo)
        "Cargo.toml",
        "go.mod",
        "composer.json",
    ]

    search_path = current
    for _ in range(10):  # Limit depth to prevent infinite loops
        for marker in project_markers:
            if (search_path / marker).exists():
                logger.debug(f"Workspace detected via marker '{marker}': {search_path}")
                return search_path

        parent = search_path.parent
        if parent == search_path:  # Reached filesystem root
            break
        search_path = parent

    # Priority 4: Fallback to current directory
    logger.warning(
        f"No workspace root detected. Falling back to current directory: {current}. "
        f"Consider setting DOPEMUX_WORKSPACE_ROOT or ensuring you're in a git repository."
    )
    return current


def export_workspace_env(workspace_path: Optional[Path] = None) -> dict[str, str]:
    """
    Generate environment variables for MCP server propagation.

    Use this in MCP wrapper scripts to ensure consistent workspace
    detection across all servers.

    Args:
        workspace_path: Explicit workspace path (default: auto-detect)

    Returns:
        Dict of environment variables to export

    Example:
        >>> env_vars = export_workspace_env()
        >>> logger.info(env_vars)
        {
            'DOPEMUX_WORKSPACE_ROOT': '/Users/hue/code/dopemux-mvp',
            'DOPEMUX_WORKSPACE_ID': '/Users/hue/code/dopemux-mvp'
        }

    Shell usage:
        ```bash
        # In MCP wrapper script:
        eval "$(python3 -c 'from dopemux.workspace_detection import export_workspace_env; import json; logger.info(\"\\n\".join(f\"export {k}={v}\" for k,v in export_workspace_env().items()))')"
        ```
    """
    if workspace_path is None:
        workspace_path = get_workspace_root()

    workspace_str = str(workspace_path.resolve())

    return {
        "DOPEMUX_WORKSPACE_ROOT": workspace_str,
        "DOPEMUX_WORKSPACE_ID": workspace_str,  # Alias for compatibility
    }


def validate_workspace(workspace_path: Path) -> tuple[bool, Optional[str]]:
    """
    Validate that a path is a valid Dopemux workspace.

    Args:
        workspace_path: Path to validate

    Returns:
        (is_valid, error_message)

    Example:
        >>> valid, error = validate_workspace(Path('/Users/hue/code/dopemux-mvp'))
        >>> if not valid:
        ...     logger.error(f"Invalid workspace: {error}")
    """
    if not workspace_path.exists():
        return False, f"Path does not exist: {workspace_path}"

    if not workspace_path.is_dir():
        return False, f"Path is not a directory: {workspace_path}"

    # Check for git repository (main repo or worktree)
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=str(workspace_path),
            capture_output=True,
            text=True,
            check=True,
            timeout=2
        )
        git_dir = result.stdout.strip()
        if git_dir:
            # Valid git workspace
            return True, None
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Check for project markers (non-git projects)
    project_markers = ["pyproject.toml", "package.json", "Cargo.toml", "go.mod"]
    if any((workspace_path / marker).exists() for marker in project_markers):
        return True, None

    # No clear project indicators
    return False, (
        f"Path does not appear to be a valid workspace: {workspace_path}\n"
        f"Expected: git repository OR project marker (pyproject.toml, package.json, etc.)"
    )


def get_workspace_info(workspace_path: Optional[Path] = None) -> dict[str, any]:
    """
    Get comprehensive workspace information for diagnostics.

    Args:
        workspace_path: Explicit workspace path (default: auto-detect)

    Returns:
        Dict with workspace metadata

    Example:
        >>> info = get_workspace_info()
        >>> logger.info(json.dumps(info, indent=2))
        {
          "workspace_root": "/Users/hue/code/dopemux-mvp",
          "is_git_repo": true,
          "is_worktree": false,
          "git_branch": "main",
          "detection_method": "git"
        }
    """
    if workspace_path is None:
        workspace_path = get_workspace_root()

    info = {
        "workspace_root": str(workspace_path),
        "is_git_repo": False,
        "is_worktree": False,
        "git_branch": None,
        "detection_method": "fallback",
    }

    # Check git status
    try:
        # Check if it's a git repo
        subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=str(workspace_path),
            capture_output=True,
            check=True,
            timeout=2
        )
        info["is_git_repo"] = True
        info["detection_method"] = "git"

        # Check if it's a worktree
        git_dir_path = workspace_path / ".git"
        if git_dir_path.exists() and git_dir_path.is_file():
            # .git as file = worktree
            info["is_worktree"] = True

        # Get current branch
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(workspace_path),
            capture_output=True,
            text=True,
            check=True,
            timeout=2
        )
        info["git_branch"] = result.stdout.strip()

    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Check for env var override
    if os.getenv("DOPEMUX_WORKSPACE_ROOT"):
        info["detection_method"] = "env_override"

    return info


if __name__ == "__main__":
    # CLI usage for diagnostics
    import json
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--info":
        # Print workspace info
        info = get_workspace_info()
        logger.info(json.dumps(info, indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "--env":
        # Print environment variables (for sourcing in shell)
        env_vars = export_workspace_env()
        for key, value in env_vars.items():
            logger.info(f"export {key}={value}")
    else:
        # Print workspace root
        workspace = get_workspace_root()
        logger.info(workspace)
