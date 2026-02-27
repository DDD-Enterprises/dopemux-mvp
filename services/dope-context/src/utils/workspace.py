"""
Workspace Detection and Collection Naming
Ensures proper multi-project isolation.
"""

import hashlib
import logging
import sys
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Add project root to path for imports
# Detect if running in Docker (different path structure)
is_docker = Path("/.dockerenv").exists() or Path("/app").exists()
if is_docker:
    # In Docker: /app/src/utils/workspace.py -> /app (2 levels up)
    project_root = Path(__file__).resolve().parents[2]
else:
    # Local development: services/dope-context/src/utils -> root (4 levels up)
    project_root = Path(__file__).resolve().parents[4]

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import shared workspace detection (SINGLE SOURCE OF TRUTH)
# This fixes the worktree bug: git worktrees have .git as FILE, not directory!
try:
    from src.dopemux.workspace_detection import get_workspace_root as _get_workspace_root
except ModuleNotFoundError:
    # Fallback implementation for Docker images where the shared dopemux package
    # is not available. Keeps workspace detection consistent with the main repo.
    import logging
    import os
    import subprocess

    _logger = logging.getLogger(__name__)

    def _get_workspace_root(start_path: Optional[Path] = None) -> Path:
        current = Path(start_path or os.getcwd()).resolve()

        # Check for dynamic relative path from Docker environment
        host_relative_path = os.getenv("HOST_PROJECT_RELATIVE_PATH")
        if host_relative_path:
            # If we are in docker and have this var, we expect code at /workspaces/<name>
            candidate = Path(f"/workspaces/{host_relative_path}")
            if candidate.exists():
                _logger.debug(
                    "Workspace detected via HOST_PROJECT_RELATIVE_PATH: %s", candidate
                )
                return candidate

        env_workspace = os.getenv("DOPEMUX_WORKSPACE_ROOT")
        if env_workspace:
            workspace_path = Path(env_workspace).resolve()
            if workspace_path.exists() and workspace_path.is_dir():
                _logger.debug(
                    "Workspace detected via DOPEMUX_WORKSPACE_ROOT: %s", workspace_path
                )
                return workspace_path
            _logger.warning(
                "DOPEMUX_WORKSPACE_ROOT set to invalid path: %s. Falling back to auto-detection.",
                env_workspace,
            )

        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=str(current),
                capture_output=True,
                text=True,
                check=True,
                timeout=2,
            )
            git_root = Path(result.stdout.strip())
            if git_root.exists():
                _logger.debug("Workspace detected via git: %s", git_root)
                return git_root.resolve()
        except (
            subprocess.CalledProcessError,
            subprocess.TimeoutExpired,
            FileNotFoundError,
        ) as exc:
            _logger.debug("Git detection failed (%s). Trying project markers.", exc)

        project_markers = [
            "pyproject.toml",
            "package.json",
            ".git",
            "Cargo.toml",
            "go.mod",
            "composer.json",
        ]

        search_path = current
        for _ in range(10):
            for marker in project_markers:
                if (search_path / marker).exists():
                    _logger.debug(
                        "Workspace detected via marker '%s': %s", marker, search_path
                    )
                    return search_path

            parent = search_path.parent
            if parent == search_path:
                break
            search_path = parent

        _logger.warning(
            "No workspace root detected. Falling back to current directory: %s", current
        )
        return current


# Compatibility wrapper for existing dope-context code
def get_workspace_root(cwd: Optional[Path] = None) -> Path:
    """
    Detect workspace root (dope-context compatibility wrapper).

    Delegates to shared workspace detection module.

    Args:
        cwd: Starting directory (defaults to os.getcwd())

    Returns:
        Workspace root path
    """
    return _get_workspace_root(start_path=cwd)


def workspace_to_hash(workspace_path: Path) -> str:
    """
    Generate stable hash from workspace path.

    Uses MD5 of absolute normalized path (same as official claude-context).
    Supports WORKSPACE_HASH_OVERRIDE env var for Docker compatibility.

    Args:
        workspace_path: Absolute workspace path

    Returns:
        8-character hex hash
    """
    import os
    
    # Check for hash override (for Docker where mount path differs from host)
    override = os.getenv("WORKSPACE_HASH_OVERRIDE")
    if override:
        import logging
        logging.getLogger(__name__).info(
            f"Using WORKSPACE_HASH_OVERRIDE={override} (workspace: {workspace_path})"
        )
        return override
    
    normalized = str(workspace_path.resolve())
    hash_full = hashlib.md5(normalized.encode()).hexdigest()
    return hash_full[:8]


def get_collection_names(workspace_path: Optional[Path] = None) -> Tuple[str, str]:
    """
    Get collection names for workspace.

    Args:
        workspace_path: Workspace path (auto-detects if None)

    Returns:
        Tuple of (code_collection_name, docs_collection_name)
    """
    if workspace_path is None:
        workspace_path = get_workspace_root()

    workspace_hash = workspace_to_hash(workspace_path)

    return (
        f"code_{workspace_hash}",
        f"docs_{workspace_hash}",
    )


def get_snapshot_dir(workspace_path: Optional[Path] = None) -> Path:
    """
    Get snapshot directory for workspace.

    Stores in: ~/.dope-context/snapshots/{workspace_hash}/

    Args:
        workspace_path: Workspace path (auto-detects if None)

    Returns:
        Snapshot directory path
    """
    if workspace_path is None:
        workspace_path = get_workspace_root()

    workspace_hash = workspace_to_hash(workspace_path)

    home = Path.home()
    snapshot_dir = home / ".dope-context" / "snapshots" / workspace_hash

    # Create if doesn't exist
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    return snapshot_dir


# Example usage
if __name__ == "__main__":
    workspace = get_workspace_root()
    logger.info(f"Workspace root: {workspace}")

    workspace_hash = workspace_to_hash(workspace)
    logger.info(f"Workspace hash: {workspace_hash}")

    code_coll, docs_coll = get_collection_names(workspace)
    logger.info(f"Code collection: {code_coll}")
    logger.info(f"Docs collection: {docs_coll}")

    snapshot_dir = get_snapshot_dir(workspace)
    logger.info(f"Snapshot dir: {snapshot_dir}")
