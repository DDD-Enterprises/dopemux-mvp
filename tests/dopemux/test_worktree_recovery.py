"""
Tests for WorktreeRecoveryMenu.

Tests ADHD-optimized recovery menu: async input, progressive disclosure, graceful degradation.
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

from src.dopemux.worktree_recovery import (
    RecoveryOption,
    WorktreeRecoveryMenu,
)
from src.dopemux.instance_state import InstanceState


@pytest.fixture
def temp_workspace():
    """Create temporary workspace directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_recovery_options():
    """Create sample recovery options."""
    now = datetime.now()

    return [
        RecoveryOption(
            instance_id="inst-1",
            worktree_path="/workspace/worktrees/feature-auth",
            git_branch="feature/auth",
            last_active=now - timedelta(hours=1),
            last_focus="Implementing JWT tokens",
            display_index=1
        ),
        RecoveryOption(
            instance_id="inst-2",
            worktree_path="/workspace/worktrees/feature-api",
            git_branch="feature/api",
            last_active=now - timedelta(hours=6),
            last_focus="Building REST endpoints",
            display_index=2
        ),
        RecoveryOption(
            instance_id="inst-3",
            worktree_path="/workspace/worktrees/bugfix-memory",
            git_branch="bugfix/memory-leak",
            last_active=now - timedelta(days=2),
            last_focus="Debugging memory issues",
            display_index=3
        ),
    ]


def test_recovery_option_age_display():
    """Test human-readable age display."""
    now = datetime.now()

    # Less than 1 hour
    opt1 = RecoveryOption(
        instance_id="test",
        worktree_path="/path",
        git_branch="main",
        last_active=now - timedelta(minutes=30),
        display_index=1
    )
    assert opt1.age_display() == "< 1 hour ago"

    # 5 hours ago
    opt2 = RecoveryOption(
        instance_id="test",
        worktree_path="/path",
        git_branch="main",
        last_active=now - timedelta(hours=5),
        display_index=1
    )
    assert opt2.age_display() == "5 hours ago"

    # 2 days ago
    opt3 = RecoveryOption(
        instance_id="test",
        worktree_path="/path",
        git_branch="main",
        last_active=now - timedelta(days=2),
        display_index=1
    )
    assert opt3.age_display() == "2 days ago"


def test_recovery_option_format_menu_line(sample_recovery_options):
    """Test menu line formatting."""
    opt = sample_recovery_options[0]
    line = opt.format_menu_line()

    assert "1." in line
    assert "🌳" in line
    assert "feature/auth" in line
    assert "Implementing JWT tokens" in line


def test_recovery_option_format_without_focus():
    """Test menu line formatting without focus context."""
    opt = RecoveryOption(
        instance_id="test",
        worktree_path="/path",
        git_branch="feature/test",
        last_active=datetime.now(),
        last_focus=None,
        display_index=2
    )

    line = opt.format_menu_line()
    assert "2." in line
    assert "feature/test" in line
    # Should not crash with None focus


@pytest.mark.asyncio
async def test_worktree_recovery_menu_initialization(temp_workspace):
    """Test WorktreeRecoveryMenu initialization."""
    menu = WorktreeRecoveryMenu(
        workspace_id=str(temp_workspace),
        conport_port=3007,
        max_age_days=7,
        timeout_seconds=30
    )

    assert menu.workspace_id == str(temp_workspace)
    assert menu.max_age_days == 7
    assert menu.timeout_seconds == 30


@pytest.mark.asyncio
async def test_find_recoverable_sessions(temp_workspace):
    """Test finding recoverable sessions."""
    menu = WorktreeRecoveryMenu(workspace_id=str(temp_workspace))

    # Mock the manager's method
    now = datetime.now()
    mock_states = [
        InstanceState(
            instance_id="inst-1",
            port_base=3000,
            worktree_path="/worktree-1",
            git_branch="feature/auth",
            created_at=now - timedelta(hours=2),
            last_active=now - timedelta(hours=1),
            status="orphaned",
            last_focus_context="Testing auth"
        ),
    ]

    menu.manager.find_orphaned_instances_filtered = AsyncMock(return_value=mock_states)

    options = await menu.find_recoverable_sessions()

    assert len(options) == 1
    assert options[0].instance_id == "inst-1"
    assert options[0].git_branch == "feature/auth"
    assert options[0].display_index == 1


@pytest.mark.asyncio
async def test_check_has_more_sessions(temp_workspace):
    """Test checking for additional sessions."""
    menu = WorktreeRecoveryMenu(workspace_id=str(temp_workspace))

    # Mock with 5 orphaned instances
    mock_states = [MagicMock() for _ in range(5)]
    menu.manager.find_orphaned_instances_filtered = AsyncMock(return_value=mock_states)

    has_more = await menu.check_has_more_sessions()

    assert has_more is True  # 5 > 3

    # Mock with only 2
    mock_states = [MagicMock() for _ in range(2)]
    menu.manager.find_orphaned_instances_filtered = AsyncMock(return_value=mock_states)

    has_more = await menu.check_has_more_sessions()

    assert has_more is False  # 2 <= 3


@pytest.mark.asyncio
async def test_display_menu(temp_workspace, sample_recovery_options, capsys):
    """Test menu display output."""
    menu = WorktreeRecoveryMenu(workspace_id=str(temp_workspace))

    menu.display_menu(sample_recovery_options[:2], has_more=False)

    captured = capsys.readouterr()

    # Check for key elements
    assert "orphaned worktree sessions" in captured.out
    assert "feature/auth" in captured.out
    assert "feature/api" in captured.out
    assert "Stay in main worktree" in captured.out
    assert "30s" in captured.out  # Timeout display


@pytest.mark.asyncio
async def test_display_menu_with_show_all(temp_workspace, sample_recovery_options, capsys):
    """Test menu display with 'show all' option."""
    menu = WorktreeRecoveryMenu(workspace_id=str(temp_workspace))

    menu.display_menu(sample_recovery_options[:3], has_more=True)

    captured = capsys.readouterr()

    # Should show "show all" option
    assert "Show all recoverable sessions" in captured.out
    assert "a." in captured.out


@pytest.mark.asyncio
async def test_fallback_to_git_worktree_list(temp_workspace):
    """Test git worktree fallback when ConPort unavailable."""
    # Create a real git repo with worktrees for testing
    import subprocess

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=temp_workspace, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=temp_workspace, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=temp_workspace, check=True, capture_output=True)

    # Create initial commit
    (temp_workspace / "README.md").write_text("Test")
    subprocess.run(["git", "add", "."], cwd=temp_workspace, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial"], cwd=temp_workspace, check=True, capture_output=True)

    # Create a worktree
    worktree_path = temp_workspace / "worktree-feature"
    subprocess.run(
        ["git", "worktree", "add", str(worktree_path), "-b", "feature/test"],
        cwd=temp_workspace,
        check=True,
        capture_output=True
    )

    menu = WorktreeRecoveryMenu(workspace_id=str(temp_workspace))
    options = await menu.fallback_to_git_worktree_list()

    # Should find the worktree (excluding main)
    assert len(options) >= 1
    assert any("feature" in opt.git_branch for opt in options)


@pytest.mark.asyncio
async def test_find_all_recoverable_sessions(temp_workspace):
    """Test finding all recoverable sessions (progressive disclosure)."""
    menu = WorktreeRecoveryMenu(workspace_id=str(temp_workspace))

    # Mock with 7 instances
    mock_states = [
        MagicMock(
            instance_id=f"inst-{i}",
            worktree_path=f"/worktree-{i}",
            git_branch=f"feature/{i}",
            last_active=datetime.now() - timedelta(hours=i),
            last_focus_context=f"Work {i}"
        )
        for i in range(7)
    ]

    menu.manager.find_orphaned_instances_filtered = AsyncMock(return_value=mock_states)

    options = await menu.find_all_recoverable_sessions()

    # Should return all 7 (under limit of 10)
    assert len(options) == 7


@pytest.mark.asyncio
async def test_show_recovery_menu_no_options(temp_workspace):
    """Test recovery menu with no orphaned sessions."""
    menu = WorktreeRecoveryMenu(workspace_id=str(temp_workspace))

    menu.manager.find_orphaned_instances_filtered = AsyncMock(return_value=[])

    # Mock git fallback to also return empty
    with patch.object(menu, 'fallback_to_git_worktree_list', AsyncMock(return_value=[])):
        result = await menu.show_recovery_menu()

    assert result is None  # Should return None (stay in main)


@pytest.mark.asyncio
async def test_create_option_from_git(temp_workspace):
    """Test creating RecoveryOption from git worktree data."""
    menu = WorktreeRecoveryMenu(workspace_id=str(temp_workspace))

    git_data = {
        "path": "/workspace/worktrees/feature-auth",
        "branch": "feature/auth"
    }

    option = menu._create_option_from_git(git_data, index=1)

    assert option.instance_id == "git-1"
    assert option.worktree_path == "/workspace/worktrees/feature-auth"
    assert option.git_branch == "feature/auth"
    assert option.display_index == 1
    assert option.last_focus is None  # Git doesn't provide this


@pytest.mark.asyncio
async def test_adhd_optimization_max_3_initial(temp_workspace):
    """Test ADHD optimization: max 3 options initially."""
    menu = WorktreeRecoveryMenu(workspace_id=str(temp_workspace))

    # Create 5 mock instances
    mock_states = [MagicMock() for _ in range(5)]
    menu.manager.find_orphaned_instances_filtered = AsyncMock(return_value=mock_states[:3])

    options = await menu.find_recoverable_sessions()

    # Should only return 3 (ADHD max for initial display)
    assert len(options) == 3
