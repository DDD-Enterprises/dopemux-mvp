
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from src.dopemux.instance_manager import InstanceManager

@patch("src.dopemux.instance_manager.InstanceManager._ensure_cache_dir")
def test_get_instance_env_vars_host_paths(mock_ensure_cache):
    """Verify that HOST_CODE_PARENT_DIR and HOST_PROJECT_RELATIVE_PATH are calculated correctly."""

    # Setup mock workspace
    # We use a path that looks like the user's setup
    workspace_root = Path("/Users/hue/code/dopemux-mvp")

    # Initialize manager (mock _ensure_cache_dir prevents fs access)
    manager = InstanceManager(workspace_root)

    # Test case 1: Main instance (A)
    # instance_id='A', worktree_path=None
    env_vars = manager.get_instance_env_vars('A', 3000, None)

    assert "HOST_CODE_PARENT_DIR" in env_vars
    assert "HOST_PROJECT_RELATIVE_PATH" in env_vars

    # For main instance, actual_workspace is workspace_root
    assert env_vars["HOST_CODE_PARENT_DIR"] == "/Users/hue/code"
    assert env_vars["HOST_PROJECT_RELATIVE_PATH"] == "dopemux-mvp"

    # Test case 2: Worktree instance (B)
    # instance_id='B', worktree_path is inside worktrees dir
    worktree_path = workspace_root / "worktrees" / "B"
    env_vars_b = manager.get_instance_env_vars('B', 3030, worktree_path)

    assert env_vars_b["HOST_CODE_PARENT_DIR"] == "/Users/hue/code/dopemux-mvp/worktrees"
    assert env_vars_b["HOST_PROJECT_RELATIVE_PATH"] == "B"

if __name__ == "__main__":
    pytest.main([__file__])
