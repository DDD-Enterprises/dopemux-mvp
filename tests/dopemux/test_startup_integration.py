"""
Tests for worktree recovery menu startup integration.

Tests that the recovery menu is properly integrated into the dopemux startup flow.
"""

import pytest
from pathlib import Path
import tempfile
import subprocess
from unittest.mock import patch, MagicMock, AsyncMock


def test_startup_integration_imports():
    """Test that recovery menu can be imported in cli module."""
    # This tests that the import statement in cli.py will work
    from src.dopemux.worktree_recovery import show_recovery_menu_sync

    assert show_recovery_menu_sync is not None
    assert callable(show_recovery_menu_sync)


def test_recovery_menu_sync_function_exists():
    """Test that the synchronous wrapper function exists."""
    from src.dopemux.worktree_recovery import show_recovery_menu_sync

    # Should be a callable function
    assert callable(show_recovery_menu_sync)


def test_recovery_menu_with_no_orphaned_sessions():
    """Test recovery menu when no orphaned sessions exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)

        # Initialize git repo
        subprocess.run(["git", "init", "-b", "main"], cwd=workspace, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=workspace,
            check=True,
            capture_output=True
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=workspace,
            check=True,
            capture_output=True
        )

        # Create initial commit
        (workspace / "README.md").write_text("Test")
        subprocess.run(["git", "add", "."], cwd=workspace, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial"],
            cwd=workspace,
            check=True,
            capture_output=True
        )

        from src.dopemux.worktree_recovery import show_recovery_menu_sync

        # Should return None (no worktrees to recover)
        result = show_recovery_menu_sync(str(workspace))

        assert result is None


def test_recovery_menu_graceful_degradation_non_git():
    """Test recovery menu gracefully handles non-git directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        from src.dopemux.worktree_recovery import show_recovery_menu_sync

        # Should handle non-git directory without crashing
        result = show_recovery_menu_sync(tmpdir)

        # Should return None (no git = no worktrees)
        assert result is None


@patch('src.dopemux.worktree_recovery.WorktreeRecoveryMenu')
def test_startup_flow_calls_recovery_menu(mock_menu_class):
    """Test that startup flow would call recovery menu correctly."""
    # Mock the recovery menu to avoid actual user interaction
    mock_instance = MagicMock()
    # Use AsyncMock for async method
    mock_instance.show_recovery_menu = AsyncMock(return_value=None)
    mock_menu_class.return_value = mock_instance

    from src.dopemux.worktree_recovery import show_recovery_menu_sync

    # Call the sync wrapper
    result = show_recovery_menu_sync("/fake/path")

    # Verify menu was created with correct parameters
    mock_menu_class.assert_called_once()
    call_args = mock_menu_class.call_args

    # Arguments are positional: WorktreeRecoveryMenu(workspace_id, conport_port)
    assert call_args[0][0] == "/fake/path"  # workspace_id
    assert call_args[0][1] == 3004  # conport_port


def test_recovery_menu_integration_error_handling():
    """Test that recovery menu errors don't crash startup."""
    from src.dopemux.worktree_recovery import show_recovery_menu_sync

    # Pass invalid workspace - should not raise, just return None
    result = show_recovery_menu_sync("/nonexistent/path/12345")

    # Should return None (graceful degradation)
    assert result is None


def test_cli_imports_work():
    """Test that all required imports for CLI integration work."""
    # Test imports that cli.py uses
    from src.dopemux.worktree_recovery import show_recovery_menu_sync
    import os
    from pathlib import Path

    # All imports should succeed
    assert show_recovery_menu_sync is not None
    assert os is not None
    assert Path is not None


def test_recovery_menu_conport_unavailable():
    """Test recovery menu when ConPort is unavailable (uses git fallback)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)

        # Initialize git repo
        subprocess.run(["git", "init", "-b", "main"], cwd=workspace, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=workspace,
            check=True,
            capture_output=True
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=workspace,
            check=True,
            capture_output=True
        )

        # Create initial commit
        (workspace / "README.md").write_text("Test")
        subprocess.run(["git", "add", "."], cwd=workspace, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial"],
            cwd=workspace,
            check=True,
            capture_output=True
        )

        # Create a worktree
        worktree_path = workspace / "worktree-test"
        subprocess.run(
            ["git", "worktree", "add", str(worktree_path), "-b", "feature/test"],
            cwd=workspace,
            check=True,
            capture_output=True
        )

        from src.dopemux.worktree_recovery import show_recovery_menu_sync

        # ConPort on port 9999 won't exist, should fall back to git worktree list
        # Since we can't test interactive input, this will return None (no selection)
        # But it should NOT crash - that's what we're testing
        result = show_recovery_menu_sync(str(workspace), conport_port=9999)

        # Should return None (no user input in test) but NOT crash
        assert result is None


def test_workspace_path_handling():
    """Test that workspace paths are handled correctly."""
    from src.dopemux.worktree_recovery import show_recovery_menu_sync

    # Test with absolute path
    result = show_recovery_menu_sync("/absolute/path/test")
    assert result is None  # No worktrees, but shouldn't crash

    # Test with relative path (will be non-existent)
    result = show_recovery_menu_sync("./relative/path")
    assert result is None  # No worktrees, but shouldn't crash
