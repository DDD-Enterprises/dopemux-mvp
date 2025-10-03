"""
File Synchronizer - Incremental Update System
Ported from official claude-context TypeScript implementation.

Uses Merkle DAG and SHA256 snapshots for efficient change detection.
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Optional

from ..utils.workspace import get_snapshot_dir


logger = logging.getLogger(__name__)


@dataclass
class FileSnapshot:
    """Single file snapshot."""

    path: str  # Relative to workspace
    sha256: str
    size: int
    mtime: float


@dataclass
class WorkspaceSnapshot:
    """Complete workspace snapshot."""

    workspace_path: str
    files: Dict[str, FileSnapshot] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        """Convert to dict for JSON serialization."""
        return {
            "workspace_path": self.workspace_path,
            "files": {
                path: {
                    "sha256": f.sha256,
                    "size": f.size,
                    "mtime": f.mtime,
                }
                for path, f in self.files.items()
            },
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "WorkspaceSnapshot":
        """Load from dict."""
        snapshot = cls(workspace_path=data["workspace_path"])
        snapshot.created_at = data.get("created_at", "")

        for path, file_data in data.get("files", {}).items():
            snapshot.files[path] = FileSnapshot(
                path=path,
                sha256=file_data["sha256"],
                size=file_data["size"],
                mtime=file_data["mtime"],
            )

        return snapshot


@dataclass
class ChangeSet:
    """Detected file changes."""

    added: List[str] = field(default_factory=list)
    modified: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)

    def has_changes(self) -> bool:
        """Check if any changes detected."""
        return bool(self.added or self.modified or self.removed)

    def total_changes(self) -> int:
        """Total number of changed files."""
        return len(self.added) + len(self.modified) + len(self.removed)


class FileSynchronizer:
    """
    File synchronizer with Merkle DAG-based change detection.

    Tracks file changes efficiently using content hashing and snapshots.
    """

    def __init__(
        self,
        workspace_path: Path,
        include_patterns: List[str] = None,
        exclude_patterns: List[str] = None,
    ):
        """
        Initialize file synchronizer.

        Args:
            workspace_path: Absolute workspace path
            include_patterns: File patterns to include (e.g., ["*.py"])
            exclude_patterns: Patterns to exclude (e.g., ["__pycache__", "node_modules"])
        """
        self.workspace_path = workspace_path.resolve()
        self.include_patterns = include_patterns or [
            "*.py",
            "*.js",
            "*.ts",
            "*.tsx",
            "*.md",
        ]
        self.exclude_patterns = exclude_patterns or [
            "__pycache__",
            "*.pyc",
            "node_modules",
            ".git",
            "dist",
            "build",
        ]

        self.snapshot_dir = get_snapshot_dir(self.workspace_path)
        self.snapshot_file = self.snapshot_dir / "snapshot.json"

    def _should_ignore(self, rel_path: Path) -> bool:
        """Check if path should be ignored."""
        path_str = str(rel_path)

        # Check exclusions first
        for pattern in self.exclude_patterns:
            pattern_clean = pattern.replace("*", "")
            if pattern_clean in path_str:
                return True

        # Check if matches any include pattern
        if not self.include_patterns:
            return False  # No patterns = include everything

        for pattern in self.include_patterns:
            # Handle glob patterns
            if "*" in pattern:
                if rel_path.match(pattern):
                    return False
            else:
                # Exact extension match
                if path_str.endswith(pattern):
                    return False

        # Doesn't match any include pattern
        return True

    def _hash_file(self, file_path: Path) -> str:
        """Compute SHA256 hash of file."""
        hasher = hashlib.sha256()

        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                hasher.update(chunk)

        return hasher.hexdigest()

    def _scan_workspace(self) -> WorkspaceSnapshot:
        """
        Scan workspace and generate snapshot.

        Returns:
            WorkspaceSnapshot with all file hashes
        """
        snapshot = WorkspaceSnapshot(workspace_path=str(self.workspace_path))

        # Walk workspace
        for file_path in self.workspace_path.rglob("*"):
            if not file_path.is_file():
                continue

            # Get relative path
            rel_path = file_path.relative_to(self.workspace_path)

            # Check if should ignore
            if self._should_ignore(rel_path):
                continue

            try:
                # Compute hash
                file_hash = self._hash_file(file_path)
                stat = file_path.stat()

                snapshot.files[str(rel_path)] = FileSnapshot(
                    path=str(rel_path),
                    sha256=file_hash,
                    size=stat.st_size,
                    mtime=stat.st_mtime,
                )

            except Exception as e:
                logger.warning(f"Failed to hash {rel_path}: {e}")
                continue

        logger.info(
            f"Scanned {len(snapshot.files)} files in {self.workspace_path.name}"
        )
        return snapshot

    def load_snapshot(self) -> Optional[WorkspaceSnapshot]:
        """
        Load previous snapshot.

        Returns:
            WorkspaceSnapshot or None if no snapshot exists
        """
        if not self.snapshot_file.exists():
            logger.debug(f"No snapshot found at {self.snapshot_file}")
            return None

        try:
            data = json.loads(self.snapshot_file.read_text())
            snapshot = WorkspaceSnapshot.from_dict(data)
            logger.info(f"Loaded snapshot with {len(snapshot.files)} files")
            return snapshot

        except Exception as e:
            logger.error(f"Failed to load snapshot: {e}")
            return None

    def save_snapshot(self, snapshot: WorkspaceSnapshot):
        """
        Save snapshot atomically.

        Args:
            snapshot: Workspace snapshot to save
        """
        try:
            # Write to temp file first
            temp_file = self.snapshot_file.with_suffix(".tmp")
            temp_file.write_text(json.dumps(snapshot.to_dict(), indent=2))

            # Atomic rename
            temp_file.replace(self.snapshot_file)

            logger.info(f"Saved snapshot: {len(snapshot.files)} files")

        except Exception as e:
            logger.error(f"Failed to save snapshot: {e}")
            raise

    def check_changes(self) -> ChangeSet:
        """
        Check for file changes since last snapshot.

        Returns:
            ChangeSet with added, modified, removed files
        """
        # Load previous snapshot
        old_snapshot = self.load_snapshot()

        # Scan current state
        new_snapshot = self._scan_workspace()

        # Save new snapshot
        self.save_snapshot(new_snapshot)

        # If no previous snapshot, all files are "added"
        if old_snapshot is None:
            return ChangeSet(
                added=list(new_snapshot.files.keys()),
                modified=[],
                removed=[],
            )

        # Compare snapshots
        changes = ChangeSet()

        old_files = set(old_snapshot.files.keys())
        new_files = set(new_snapshot.files.keys())

        # Added files
        changes.added = list(new_files - old_files)

        # Removed files
        changes.removed = list(old_files - new_files)

        # Modified files (exist in both, but hash changed)
        for path in old_files & new_files:
            old_hash = old_snapshot.files[path].sha256
            new_hash = new_snapshot.files[path].sha256

            if old_hash != new_hash:
                changes.modified.append(path)

        logger.info(
            f"Changes detected: {len(changes.added)} added, "
            f"{len(changes.modified)} modified, {len(changes.removed)} removed"
        )

        return changes


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    sync = FileSynchronizer(
        workspace_path=Path.cwd(),
        include_patterns=["*.py", "*.md"],
    )

    changes = sync.check_changes()

    print(f"Changes: {changes.total_changes()} files")
    print(f"  Added: {len(changes.added)}")
    print(f"  Modified: {len(changes.modified)}")
    print(f"  Removed: {len(changes.removed)}")
