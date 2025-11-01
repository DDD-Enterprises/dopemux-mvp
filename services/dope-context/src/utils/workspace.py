"""
Workspace Detection and Collection Naming
Ensures proper multi-project isolation.
"""

import hashlib
import sys
from pathlib import Path
from typing import Optional, Tuple

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
from src.dopemux.workspace_detection import get_workspace_root as _get_workspace_root


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

    Args:
        workspace_path: Absolute workspace path

    Returns:
        8-character hex hash
    """
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
    print(f"Workspace root: {workspace}")

    workspace_hash = workspace_to_hash(workspace)
    print(f"Workspace hash: {workspace_hash}")

    code_coll, docs_coll = get_collection_names(workspace)
    print(f"Code collection: {code_coll}")
    print(f"Docs collection: {docs_coll}")

    snapshot_dir = get_snapshot_dir(workspace)
    print(f"Snapshot dir: {snapshot_dir}")
