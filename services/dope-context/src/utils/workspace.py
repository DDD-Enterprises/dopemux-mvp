"""
Workspace Detection and Collection Naming
Ensures proper multi-project isolation.
"""

import hashlib
import os
from pathlib import Path
from typing import Optional, Tuple


def get_workspace_root(cwd: Optional[Path] = None) -> Path:
    """
    Detect workspace root directory.

    Tries (in order):
    1. Git root (if in git repo)
    2. Directory with pyproject.toml or package.json
    3. Current working directory

    Args:
        cwd: Starting directory (defaults to os.getcwd())

    Returns:
        Workspace root path
    """
    if cwd is None:
        cwd = Path.cwd()

    current = cwd.resolve()

    # 1. Check for git root
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent

    # 2. Check for project markers
    current = cwd.resolve()
    markers = ["pyproject.toml", "package.json", "Cargo.toml", "go.mod"]

    while current != current.parent:
        for marker in markers:
            if (current / marker).exists():
                return current
        current = current.parent

    # 3. Fallback to cwd
    return cwd.resolve()


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
