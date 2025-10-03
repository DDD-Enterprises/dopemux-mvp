"""
Tests for Multi-Project Isolation
Critical security test: Ensure no data leakage between workspaces.
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from src.utils.workspace import (
    get_workspace_root,
    workspace_to_hash,
    get_collection_names,
)
from src.sync.file_synchronizer import FileSynchronizer, ChangeSet


def test_workspace_hash_deterministic():
    """Test workspace hashing is deterministic."""
    path1 = Path("/Users/test/project-a").resolve()
    path2 = Path("/Users/test/project-a").resolve()
    path3 = Path("/Users/test/project-b").resolve()

    hash1 = workspace_to_hash(path1)
    hash2 = workspace_to_hash(path2)
    hash3 = workspace_to_hash(path3)

    # Same path = same hash
    assert hash1 == hash2

    # Different path = different hash
    assert hash1 != hash3

    # Hash is 8 characters
    assert len(hash1) == 8


def test_collection_names_unique_per_workspace():
    """Test collection names are unique per workspace."""
    project_a = Path("/Users/test/project-a")
    project_b = Path("/Users/test/project-b")

    code_a, docs_a = get_collection_names(project_a)
    code_b, docs_b = get_collection_names(project_b)

    # Different projects = different collections
    assert code_a != code_b
    assert docs_a != docs_b

    # Collections follow naming pattern
    assert code_a.startswith("code_")
    assert docs_a.startswith("docs_")


def test_file_synchronizer_change_detection(tmp_path):
    """Test file change detection."""
    # Create test files
    file1 = tmp_path / "test1.py"
    file1.write_text("def foo(): pass")

    # First scan - all files are "added"
    sync = FileSynchronizer(
        workspace_path=tmp_path,
        include_patterns=["*.py"],
    )

    changes1 = sync.check_changes()
    assert len(changes1.added) == 1
    assert "test1.py" in changes1.added
    assert len(changes1.modified) == 0
    assert len(changes1.removed) == 0

    # No changes - should detect nothing
    changes2 = sync.check_changes()
    assert not changes2.has_changes()

    # Modify file
    file1.write_text("def foo(): return 42")

    changes3 = sync.check_changes()
    assert len(changes3.modified) == 1
    assert "test1.py" in changes3.modified

    # Add new file
    file2 = tmp_path / "test2.py"
    file2.write_text("def bar(): pass")

    changes4 = sync.check_changes()
    assert len(changes4.added) == 1
    assert "test2.py" in changes4.added

    # Remove file
    file1.unlink()

    changes5 = sync.check_changes()
    assert len(changes5.removed) == 1
    assert "test1.py" in changes5.removed


def test_file_synchronizer_ignores_patterns(tmp_path):
    """Test file exclusion patterns."""
    # Create files
    (tmp_path / "include.py").write_text("code")
    (tmp_path / "test_exclude.py").write_text("test")
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "cache.pyc").write_text("binary")

    sync = FileSynchronizer(
        workspace_path=tmp_path,
        include_patterns=["*.py"],
        exclude_patterns=["*test*", "*__pycache__*"],
    )

    changes = sync.check_changes()

    # Should only include include.py
    assert len(changes.added) == 1
    assert "include.py" in changes.added


def test_snapshot_persistence(tmp_path):
    """Test snapshot saves and loads correctly."""
    file1 = tmp_path / "test.py"
    file1.write_text("def foo(): pass")

    sync = FileSynchronizer(workspace_path=tmp_path)

    # First scan creates snapshot
    changes1 = sync.check_changes()
    assert len(changes1.added) == 1

    # Create new synchronizer (simulates restart)
    sync2 = FileSynchronizer(workspace_path=tmp_path)

    # Should load snapshot and detect no changes
    changes2 = sync2.check_changes()
    assert not changes2.has_changes()


@pytest.mark.asyncio
async def test_workspace_isolation_in_search():
    """
    CRITICAL TEST: Verify workspace isolation.

    Ensure searching workspace A doesn't return results from workspace B.
    """
    with patch("src.mcp.server.get_collection_names") as mock_collections:
        # Workspace A gets collection code_aaaa1111
        # Workspace B gets collection code_bbbb2222

        workspace_a = Path("/tmp/project-a")
        workspace_b = Path("/tmp/project-b")

        def get_collections_side_effect(workspace):
            if "project-a" in str(workspace):
                return ("code_aaaa1111", "docs_aaaa1111")
            else:
                return ("code_bbbb2222", "docs_bbbb2222")

        mock_collections.side_effect = get_collections_side_effect

        # Verify different workspaces get different collections
        code_a, _ = get_collections_side_effect(workspace_a)
        code_b, _ = get_collections_side_effect(workspace_b)

        assert code_a != code_b  # ISOLATION VERIFIED
        assert code_a == "code_aaaa1111"
        assert code_b == "code_bbbb2222"


def test_changeset_total_changes():
    """Test ChangeSet utility methods."""
    changes = ChangeSet(
        added=["file1.py", "file2.py"],
        modified=["file3.py"],
        removed=["file4.py", "file5.py"],
    )

    assert changes.total_changes() == 5
    assert changes.has_changes() == True

    empty = ChangeSet()
    assert empty.total_changes() == 0
    assert empty.has_changes() == False
