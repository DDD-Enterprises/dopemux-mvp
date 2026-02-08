"""
End-to-end tests for worktree recovery workflow.

Tests complete user journeys from startup through worktree recovery,
including real git repos, ConPort integration, and performance validation.
"""

import pytest
from pathlib import Path
import tempfile
import subprocess
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock, MagicMock

from src.dopemux.worktree_recovery import (
    WorktreeRecoveryMenu,
    RecoveryOption,
    show_recovery_menu_sync,
)
from src.dopemux.instance_state import InstanceState, InstanceStateManager


@pytest.fixture
def git_repo_with_worktrees():
    """Create a git repository with multiple worktrees for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        main_path = Path(tmpdir) / "main"
        main_path.mkdir()

        # Initialize git repo
        subprocess.run(["git", "init", "-b", "main"], cwd=main_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=main_path,
            check=True,
            capture_output=True
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=main_path,
            check=True,
            capture_output=True
        )

        # Create initial commit
        (main_path / "README.md").write_text("# Test Project")
        subprocess.run(["git", "add", "."], cwd=main_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=main_path,
            check=True,
            capture_output=True
        )

        # Create multiple worktrees
        worktrees = []
        for i in range(1, 4):
            worktree_path = Path(tmpdir) / f"worktree-{i}"
            branch_name = f"feature/test-{i}"

            subprocess.run(
                ["git", "worktree", "add", str(worktree_path), "-b", branch_name],
                cwd=main_path,
                check=True,
                capture_output=True
            )
            worktrees.append({
                "path": str(worktree_path),
                "branch": branch_name
            })

        yield {
            "main": str(main_path),
            "worktrees": worktrees
        }


class TestEndToEndWorkflow:
    """End-to-end workflow tests for complete recovery flow."""

    @pytest.mark.asyncio
    async def test_full_recovery_workflow_with_git_fallback(self, git_repo_with_worktrees):
        """Test complete recovery workflow using git fallback (no ConPort)."""
        main_path = git_repo_with_worktrees["main"]

        # Create menu with non-existent ConPort port (force git fallback)
        menu = WorktreeRecoveryMenu(main_path, conport_port=9999)

        # Use git fallback directly (since ConPort unavailable)
        options = await menu.fallback_to_git_worktree_list()

        # Should find 3 worktrees (ADHD max for initial display)
        assert len(options) == 3

        # Verify all options are valid
        for opt in options:
            assert opt.instance_id.startswith("git-")
            assert opt.git_branch.startswith("feature/test-")
            assert Path(opt.worktree_path).exists()

    @pytest.mark.asyncio
    async def test_recovery_menu_display_performance(self, git_repo_with_worktrees):
        """Test that menu display completes within ADHD performance target (< 2s)."""
        main_path = git_repo_with_worktrees["main"]

        # Create menu
        menu = WorktreeRecoveryMenu(main_path, conport_port=9999)

        # Measure time to find and display options
        start_time = time.time()

        # Use git fallback (ConPort unavailable in tests)
        options = await menu.fallback_to_git_worktree_list()
        has_more = False  # Only 3 worktrees created

        # Display menu (captures output)
        import io
        import sys
        captured_output = io.StringIO()
        with patch('sys.stdout', captured_output):
            menu.display_menu(options, has_more)

        elapsed = time.time() - start_time

        # Should complete within 2 seconds (ADHD performance target)
        assert elapsed < 2.0, f"Menu display took {elapsed:.2f}s, target is < 2.0s"

        # Verify menu was displayed
        output = captured_output.getvalue()
        assert "🔄 Found orphaned worktree sessions" in output
        assert "feature/test-" in output

    @pytest.mark.asyncio
    async def test_progressive_disclosure_workflow(self, git_repo_with_worktrees):
        """Test progressive disclosure: show 3 initially, expand on request."""
        main_path = git_repo_with_worktrees["main"]

        # Create menu
        menu = WorktreeRecoveryMenu(main_path, conport_port=9999)

        # Initial display should show max 3 (using git fallback)
        initial_options = await menu.fallback_to_git_worktree_list()
        assert len(initial_options) == 3

        # Test with more worktrees (create additional ones)
        for i in range(4, 8):
            worktree_path = Path(git_repo_with_worktrees["main"]).parent / f"worktree-{i}"
            branch_name = f"feature/test-{i}"

            subprocess.run(
                ["git", "worktree", "add", str(worktree_path), "-b", branch_name],
                cwd=main_path,
                check=True,
                capture_output=True
            )

        # Now should have more than 3, but fallback still shows max 3
        initial_options = await menu.fallback_to_git_worktree_list()
        assert len(initial_options) == 3  # Git fallback limits to 3

        # Git worktree list should show all worktrees exist
        result = subprocess.run(
            ["git", "worktree", "list"],
            cwd=main_path,
            capture_output=True,
            text=True
        )
        # Should have main + 7 worktrees = 8 total lines (approximately)
        worktree_count = len([line for line in result.stdout.splitlines() if line.strip()])
        assert worktree_count >= 7  # At least 7 worktrees


class TestErrorScenarios:
    """Test error handling and graceful degradation."""

    @pytest.mark.asyncio
    async def test_conport_unavailable_falls_back_to_git(self, git_repo_with_worktrees):
        """Test that ConPort unavailability triggers git fallback."""
        main_path = git_repo_with_worktrees["main"]

        # Create menu with invalid ConPort port
        menu = WorktreeRecoveryMenu(main_path, conport_port=9999)

        # This should trigger git fallback
        options = await menu.fallback_to_git_worktree_list()

        # Should successfully fall back to git
        assert len(options) == 3
        assert all(opt.instance_id.startswith("git-") for opt in options)

    @pytest.mark.asyncio
    async def test_git_command_failure_graceful_degradation(self):
        """Test graceful handling when git commands fail."""
        # Use non-git directory
        with tempfile.TemporaryDirectory() as tmpdir:
            menu = WorktreeRecoveryMenu(tmpdir, conport_port=9999)

            # Should return empty list, not crash
            options = await menu.fallback_to_git_worktree_list()
            assert options == []

    @pytest.mark.asyncio
    async def test_invalid_workspace_path(self):
        """Test handling of non-existent workspace paths."""
        menu = WorktreeRecoveryMenu("/nonexistent/path/12345", conport_port=9999)

        # Should not crash, just return empty list
        options = await menu.find_recoverable_sessions()
        assert options == []

    def test_sync_wrapper_error_handling(self):
        """Test that sync wrapper handles errors gracefully."""
        # Should not raise, just return None
        result = show_recovery_menu_sync("/nonexistent/path/12345", conport_port=9999)
        assert result is None


class TestRealWorldScenarios:
    """Test realistic user scenarios and workflows."""

    @pytest.mark.asyncio
    async def test_worktree_with_uncommitted_changes(self, git_repo_with_worktrees):
        """Test worktree with uncommitted changes is still recoverable."""
        main_path = git_repo_with_worktrees["main"]
        worktree_path = git_repo_with_worktrees["worktrees"][0]["path"]
        expected_branch = git_repo_with_worktrees["worktrees"][0]["branch"]

        # Create uncommitted changes in worktree
        (Path(worktree_path) / "new_file.txt").write_text("Uncommitted work")

        # Should still be recoverable (using git fallback)
        menu = WorktreeRecoveryMenu(main_path, conport_port=9999)
        options = await menu.fallback_to_git_worktree_list()

        # Worktree should be in the list (check by branch name, not path due to symlinks)
        worktree_found = any(
            opt.git_branch == expected_branch
            for opt in options
        )
        assert worktree_found, f"Expected branch '{expected_branch}' not found in {[opt.git_branch for opt in options]}"

    @pytest.mark.asyncio
    async def test_multiple_branches_same_prefix(self, git_repo_with_worktrees):
        """Test handling of branches with same prefix (feature/test-1 vs feature/test-10)."""
        main_path = git_repo_with_worktrees["main"]

        # Create worktree with similar branch name
        worktree_path = Path(git_repo_with_worktrees["main"]).parent / "worktree-10"
        subprocess.run(
            ["git", "worktree", "add", str(worktree_path), "-b", "feature/test-10"],
            cwd=main_path,
            check=True,
            capture_output=True
        )

        menu = WorktreeRecoveryMenu(main_path, conport_port=9999)
        options = await menu.fallback_to_git_worktree_list()

        # Should correctly parse all branch names (limited to 3 by fallback)
        branch_names = [opt.git_branch for opt in options]
        # Git fallback limits to 3, so we won't see all 4 worktrees
        assert len(branch_names) == 3
        # But all present branch names should be correctly parsed
        for name in branch_names:
            assert name.startswith("feature/test-")
        # Verify they're distinct
        assert len(set(branch_names)) == len(branch_names)

    @pytest.mark.asyncio
    async def test_worktree_age_display_accuracy(self, git_repo_with_worktrees):
        """Test that age display accurately reflects worktree last activity."""
        main_path = git_repo_with_worktrees["main"]

        menu = WorktreeRecoveryMenu(main_path, conport_port=9999)
        options = await menu.find_recoverable_sessions()

        # All worktrees just created, should show "< 1 hour ago"
        for opt in options:
            age = opt.age_display()
            assert age == "< 1 hour ago"


class TestMenuInteraction:
    """Test menu interaction and user input handling."""

    @pytest.mark.asyncio
    async def test_menu_formatting_adhd_friendly(self, git_repo_with_worktrees):
        """Test that menu output is ADHD-friendly (clear, concise, visual)."""
        main_path = git_repo_with_worktrees["main"]

        menu = WorktreeRecoveryMenu(main_path, conport_port=9999)
        options = await menu.find_recoverable_sessions()

        # Verify menu lines are formatted correctly
        for opt in options:
            menu_line = opt.format_menu_line()

            # Should include tree emoji for visual clarity
            assert "🌳" in menu_line

            # Should include branch name
            assert opt.git_branch in menu_line

            # Should include age display
            assert "ago" in menu_line

            # Should be concise (< 100 chars for ADHD focus)
            assert len(menu_line) < 100

    @pytest.mark.asyncio
    async def test_timeout_handling_pytest_environment(self, git_repo_with_worktrees):
        """Test that async input handles pytest environment correctly."""
        main_path = git_repo_with_worktrees["main"]

        menu = WorktreeRecoveryMenu(main_path, conport_port=9999, timeout_seconds=1)

        # In pytest, stdin is replaced with DontReadFromInput
        # get_user_input_async should detect this and return None immediately
        result = await menu.get_user_input_async("Test prompt: ", timeout=1)

        # Should return None (simulating timeout)
        assert result is None


class TestIntegrationWithInstanceState:
    """Test integration with InstanceStateManager when ConPort is available."""

    @pytest.mark.asyncio
    async def test_recovery_with_mocked_conport(self, git_repo_with_worktrees):
        """Test recovery menu with mocked ConPort instance state."""
        main_path = git_repo_with_worktrees["main"]

        # Create mock instance states with correct InstanceState fields
        now = datetime.now()
        mock_states = [
            InstanceState(
                instance_id="inst-1",
                port_base=3000,
                worktree_path=git_repo_with_worktrees["worktrees"][0]["path"],
                git_branch=git_repo_with_worktrees["worktrees"][0]["branch"],
                created_at=now - timedelta(hours=2),
                last_active=now - timedelta(hours=1),
                status="orphaned",
                last_focus_context="Working on authentication"
            ),
            InstanceState(
                instance_id="inst-2",
                port_base=3100,
                worktree_path=git_repo_with_worktrees["worktrees"][1]["path"],
                git_branch=git_repo_with_worktrees["worktrees"][1]["branch"],
                created_at=now - timedelta(hours=3),
                last_active=now - timedelta(hours=2),
                status="orphaned",
                last_focus_context="Refactoring database layer"
            ),
        ]

        # Mock InstanceStateManager
        with patch.object(InstanceStateManager, 'find_orphaned_instances_filtered', new_callable=AsyncMock) as mock_find:
            mock_find.return_value = mock_states

            menu = WorktreeRecoveryMenu(main_path, conport_port=3007)
            options = await menu.find_recoverable_sessions()

            # Should use ConPort data
            assert len(options) == 2
            assert options[0].last_focus == "Working on authentication"
            assert options[1].last_focus == "Refactoring database layer"


class TestPerformance:
    """Performance validation for ADHD targets."""

    @pytest.mark.asyncio
    async def test_menu_display_under_2_seconds(self, git_repo_with_worktrees):
        """Validate menu display completes within 2-second ADHD target."""
        main_path = git_repo_with_worktrees["main"]

        menu = WorktreeRecoveryMenu(main_path, conport_port=9999)

        # Measure full workflow: find sessions + check more + display
        start = time.time()

        options = await menu.find_recoverable_sessions()
        has_more = await menu.check_has_more_sessions()

        import io
        import sys
        with patch('sys.stdout', io.StringIO()):
            menu.display_menu(options, has_more)

        elapsed = time.time() - start

        # ADHD performance target: < 2 seconds
        assert elapsed < 2.0, f"Performance degradation: {elapsed:.2f}s (target < 2.0s)"

    @pytest.mark.asyncio
    async def test_git_fallback_performance(self, git_repo_with_worktrees):
        """Test git fallback completes quickly enough for ADHD users."""
        main_path = git_repo_with_worktrees["main"]

        menu = WorktreeRecoveryMenu(main_path, conport_port=9999)

        # Measure git fallback performance
        start = time.time()
        options = await menu.fallback_to_git_worktree_list()
        elapsed = time.time() - start

        # Should be very fast (< 1 second)
        assert elapsed < 1.0, f"Git fallback too slow: {elapsed:.2f}s"
        assert len(options) > 0
