"""
Incremental Indexer - Chunk-Level Change Tracking

Coordinates file-level changes with chunk-level vector updates.
Enables efficient reindexing by only updating changed chunks.
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

from ..utils.workspace import get_snapshot_dir

logger = logging.getLogger(__name__)


@dataclass
class ChunkMetadata:
    """Metadata for a single code chunk."""

    chunk_id: str  # UUID from vector database
    file_path: str  # Relative to workspace
    start_line: int
    end_line: int
    content_hash: str  # SHA256 of chunk content
    symbol_name: Optional[str] = None


@dataclass
class FileChunkMap:
    """Mapping of file to its chunks."""

    file_path: str
    file_hash: str  # SHA256 of entire file
    chunks: List[ChunkMetadata] = field(default_factory=list)


@dataclass
class ChunkSnapshot:
    """Workspace-level chunk tracking."""

    workspace_path: str
    files: Dict[str, FileChunkMap] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Serialize to JSON."""
        return {
            "workspace_path": self.workspace_path,
            "files": {
                file_path: {
                    "file_hash": fcm.file_hash,
                    "chunks": [
                        {
                            "chunk_id": c.chunk_id,
                            "file_path": c.file_path,
                            "start_line": c.start_line,
                            "end_line": c.end_line,
                            "content_hash": c.content_hash,
                            "symbol_name": c.symbol_name,
                        }
                        for c in fcm.chunks
                    ],
                }
                for file_path, fcm in self.files.items()
            },
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "ChunkSnapshot":
        """Deserialize from JSON."""
        snapshot = cls(workspace_path=data["workspace_path"])

        for file_path, file_data in data.get("files", {}).items():
            fcm = FileChunkMap(
                file_path=file_path,
                file_hash=file_data["file_hash"],
                chunks=[
                    ChunkMetadata(
                        chunk_id=c["chunk_id"],
                        file_path=c["file_path"],
                        start_line=c["start_line"],
                        end_line=c["end_line"],
                        content_hash=c["content_hash"],
                        symbol_name=c.get("symbol_name"),
                    )
                    for c in file_data.get("chunks", [])
                ],
            )
            snapshot.files[file_path] = fcm

        return snapshot


@dataclass
class ChunkChanges:
    """Detected chunk-level changes."""

    files_added: List[str] = field(default_factory=list)  # New files
    files_removed: List[str] = field(default_factory=list)  # Deleted files
    files_modified: Dict[str, "ModifiedFileChunks"] = field(default_factory=dict)

    def has_changes(self) -> bool:
        """Check if any changes detected."""
        return bool(self.files_added or self.files_removed or self.files_modified)

    def total_chunks_to_update(self) -> int:
        """Count total chunks needing updates."""
        total = 0

        # All chunks in added files
        # (count will be determined during indexing)

        # Chunks to remove from deleted files
        # (will be determined from snapshot)

        # Modified chunks
        for modified in self.files_modified.values():
            total += len(modified.chunks_to_delete)
            total += len(modified.chunks_to_add)

        return total


@dataclass
class ModifiedFileChunks:
    """Chunk changes within a modified file."""

    file_path: str
    chunks_to_delete: List[str] = field(default_factory=list)  # Chunk IDs
    chunks_to_add: List[ChunkMetadata] = field(default_factory=list)  # New chunks


class IncrementalIndexer:
    """
    Incremental indexing coordinator.

    Tracks chunk-level changes and coordinates vector updates.
    """

    def __init__(self, workspace_path: Path):
        """
        Initialize incremental indexer.

        Args:
            workspace_path: Absolute workspace path
        """
        self.workspace_path = workspace_path.resolve()
        self.snapshot_dir = get_snapshot_dir(self.workspace_path)
        self.chunk_snapshot_file = self.snapshot_dir / "chunk_snapshot.json"

    def _hash_content(self, content: str) -> str:
        """Compute SHA256 hash of content."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def load_chunk_snapshot(self) -> Optional[ChunkSnapshot]:
        """Load previous chunk snapshot."""
        if not self.chunk_snapshot_file.exists():
            logger.debug(f"No chunk snapshot found at {self.chunk_snapshot_file}")
            return None

        try:
            data = json.loads(self.chunk_snapshot_file.read_text())
            snapshot = ChunkSnapshot.from_dict(data)
            logger.info(
                f"Loaded chunk snapshot: {len(snapshot.files)} files, "
                f"{sum(len(f.chunks) for f in snapshot.files.values())} chunks"
            )
            return snapshot

        except Exception as e:
            logger.error(f"Failed to load chunk snapshot: {e}")
            return None

    def save_chunk_snapshot(self, snapshot: ChunkSnapshot):
        """Save chunk snapshot atomically."""
        try:
            # Ensure directory exists
            self.snapshot_dir.mkdir(parents=True, exist_ok=True)

            # Write to temp file first
            temp_file = self.chunk_snapshot_file.with_suffix(".tmp")
            temp_file.write_text(json.dumps(snapshot.to_dict(), indent=2))

            # Atomic rename
            temp_file.replace(self.chunk_snapshot_file)

            logger.info(
                f"Saved chunk snapshot: {len(snapshot.files)} files, "
                f"{sum(len(f.chunks) for f in snapshot.files.values())} chunks"
            )

        except Exception as e:
            logger.error(f"Failed to save chunk snapshot: {e}")
            raise

    def get_chunks_to_delete_for_file(
        self, file_path: str, old_snapshot: ChunkSnapshot
    ) -> List[str]:
        """
        Get chunk IDs to delete for a file.

        Args:
            file_path: Relative file path
            old_snapshot: Previous chunk snapshot

        Returns:
            List of chunk IDs to delete
        """
        if file_path not in old_snapshot.files:
            return []

        return [c.chunk_id for c in old_snapshot.files[file_path].chunks]

    def update_chunk_mapping(
        self,
        snapshot: ChunkSnapshot,
        file_path: str,
        file_hash: str,
        chunks: List[ChunkMetadata],
    ):
        """
        Update chunk mapping for a file.

        Args:
            snapshot: Chunk snapshot to update
            file_path: Relative file path
            file_hash: SHA256 of entire file
            chunks: New chunk metadata
        """
        snapshot.files[file_path] = FileChunkMap(
            file_path=file_path,
            file_hash=file_hash,
            chunks=chunks,
        )

    def remove_file_mapping(self, snapshot: ChunkSnapshot, file_path: str):
        """Remove file from chunk snapshot."""
        if file_path in snapshot.files:
            del snapshot.files[file_path]


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    indexer = IncrementalIndexer(workspace_path=Path.cwd())

    # Load snapshot
    snapshot = indexer.load_chunk_snapshot()
    if snapshot is None:
        snapshot = ChunkSnapshot(workspace_path=str(Path.cwd()))

    # Example: Add chunk mapping for a file
    example_chunks = [
        ChunkMetadata(
            chunk_id="uuid-1",
            file_path="src/example.py",
            start_line=1,
            end_line=10,
            content_hash=indexer._hash_content("def example(): pass"),
            symbol_name="example",
        )
    ]

    indexer.update_chunk_mapping(
        snapshot=snapshot,
        file_path="src/example.py",
        file_hash="file_hash_here",
        chunks=example_chunks,
    )

    # Save snapshot
    indexer.save_chunk_snapshot(snapshot)

    logger.info(f"Snapshot saved: {len(snapshot.files)} files")
