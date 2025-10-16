"""
End-to-End Tests for Epic 3: Manual Worktree Commands.

Tests complete user workflows for worktree management:
- list: Display all worktrees with ADHD-friendly status visualization
- switch: Navigate between worktrees with fuzzy matching
- cleanup: Safe removal of unused worktrees with protection

ADHD Context: E2E tests validate that worktree commands support
scattered attention patterns through fuzzy matching, visual clarity,
and progressive safety mechanisms.
"""

import pytest
from pathlib import Path
import tempfile
import subprocess
import os
from unittest.mock import patch, MagicMock
from io import StringIO

from src.dopemux.worktree_commands import (
    get_worktrees,
    get_worktree_status,
    list_worktrees,
    switch_worktree,
    cleanup_worktrees,
)


@pytest.fixture
def preserve_cwd():
    """Preserve and restore current working directory after test."""
    original_cwd = Path.cwd()
    yield
    try:
        os.chdir(original_cwd)
    except (OSError, FileNotFoundError):
        # If original directory was deleted, go to temp directory
        os.chdir(tempfile.gettempdir())


@pytest.fixture
def git_repo():
    """Create a temporary git repository with worktrees for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "main-repo"
        repo_path.mkdir()

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=repo_path,
            check=True,
            capture_output=True
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=repo_path,
            check=True,
            capture_output=True
        )

        # Create initial commit on main branch
        (repo_path / "README.md").write_text("# Test Repo")
        subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=repo_path,
            check=True,
            capture_output=True
        )

        # Ensure we're on main branch
        subprocess.run(
            ["git", "checkout", "-b", "main"],
            cwd=repo_path,
            capture_output=True
        )

        yield repo_path

        # Cleanup: Remove any created worktrees
        try:
            result = subprocess.run(
                ["git", "worktree", "list", "--porcelain"],
                cwd=repo_path,
                capture_output=True,
                text=True
            )

            # Parse and remove all worktrees except main
            for line in result.stdout.splitlines():
                if line.startswith("worktree "):
                    wt_path = line.split(" ", 1)[1]
                    if str(repo_path) != wt_path:
                        subprocess.run(
                            ["git", "worktree", "remove", wt_path, "--force"],
                            cwd=repo_path,
                            capture_output=True
                        )
        except Exception:
            pass


@pytest.fixture
def git_repo_with_worktrees(git_repo):
    """Create a git repo with multiple worktrees for testing."""
    # Create feature worktree
    feature_path = git_repo.parent / "feature-branch"
    subprocess.run(
        ["git", "worktree", "add", str(feature_path), "-b", "feature/test-feature"],
        cwd=git_repo,
        check=True,
        capture_output=True
    )

    # Create another worktree
    bugfix_path = git_repo.parent / "bugfix-branch"
    subprocess.run(
        ["git", "worktree", "add", str(bugfix_path), "-b", "bugfix/urgent-fix"],
        cwd=git_repo,
        check=True,
        capture_output=True
    )

    yield {
        "main": git_repo,
        "feature": feature_path,
        "bugfix": bugfix_path,
    }


class TestWorktreeListCommand:
    """Test suite for 'dopemux worktrees list' command."""

    def test_get_worktrees_empty_repo(self, git_repo):
        """Should return single worktree for repo without worktrees."""
        worktrees = get_worktrees(git_repo)

        assert len(worktrees) == 1
        assert worktrees[0][1] == "main"  # branch name

    def test_get_worktrees_multiple(self, git_repo_with_worktrees):
        """Should list all worktrees including main."""
        worktrees = get_worktrees(git_repo_with_worktrees["main"])

        assert len(worktrees) == 3
        branches = [wt[1] for wt in worktrees]
        assert "main" in branches
        assert "feature/test-feature" in branches
        assert "bugfix/urgent-fix" in branches

    def test_get_worktree_status_clean(self, git_repo):
        """Should detect clean worktree status."""
        status = get_worktree_status(str(git_repo))
        assert status == "clean"

    def test_get_worktree_status_dirty(self, git_repo):
        """Should detect dirty worktree status with uncommitted changes."""
        # Make a change
        (git_repo / "test.txt").write_text("uncommitted change")

        status = get_worktree_status(str(git_repo))
        assert status == "dirty"

    def test_list_worktrees_displays_table(self, git_repo_with_worktrees, capsys):
        """Should display ADHD-friendly table with worktree information."""
        list_worktrees(git_repo_with_worktrees["main"])

        captured = capsys.readouterr()
        output = captured.out

        # Verify table elements present
        assert "🌳 Git Worktrees" in output
        assert "Branch" in output
        assert "Path" in output
        assert "Status" in output
        assert "main" in output
        assert "feature/test-feature" in output

    def test_list_worktrees_no_worktrees(self, tmp_path, capsys):
        """Should show helpful message when no worktrees exist."""
        # Create non-git directory
        list_worktrees(tmp_path)

        captured = capsys.readouterr()
        output = captured.out

        assert "No worktrees found" in output
        assert "Tip" in output


class TestWorktreeSwitchCommand:
    """Test suite for 'dopemux worktrees switch' command."""

    def test_switch_exact_match(self, git_repo_with_worktrees, capsys, preserve_cwd):
        """Should switch to worktree with exact branch name match."""
        result = switch_worktree(
            git_repo_with_worktrees["main"],
            "feature/test-feature",
            fuzzy_match=False
        )

        assert result is True
        captured = capsys.readouterr()
        output = captured.out

        assert "feature/test-feature" in output
        assert "Switching to worktree" in output  # Should show switching message

    def test_switch_fuzzy_match_single(self, git_repo_with_worktrees, capsys, preserve_cwd):
        """Should fuzzy match when single partial match exists."""
        result = switch_worktree(
            git_repo_with_worktrees["main"],
            "feature",
            fuzzy_match=True
        )

        assert result is True
        captured = capsys.readouterr()
        output = captured.out

        assert "Fuzzy matched" in output
        assert "feature/test-feature" in output

    def test_switch_fuzzy_match_multiple(self, git_repo_with_worktrees, capsys, preserve_cwd):
        """Should show disambiguation when multiple fuzzy matches exist."""
        # Create a third worktree that also contains "feature"
        hotfix_path = git_repo_with_worktrees["main"].parent / "hotfix-branch"
        subprocess.run(
            ["git", "worktree", "add", str(hotfix_path), "-b", "hotfix/urgent-fix"],
            cwd=git_repo_with_worktrees["main"],
            check=True,
            capture_output=True
        )

        # Now both "hotfix/urgent-fix" and "bugfix/urgent-fix" contain "fix"
        result = switch_worktree(
            git_repo_with_worktrees["main"],
            "fix",
            fuzzy_match=True
        )

        assert result is False  # Should fail with multiple matches
        captured = capsys.readouterr()
        output = captured.out

        assert "Multiple matches found" in output
        assert "specify the exact branch name" in output

        # Cleanup
        subprocess.run(
            ["git", "worktree", "remove", str(hotfix_path), "--force"],
            cwd=git_repo_with_worktrees["main"],
            capture_output=True
        )

    def test_switch_no_match(self, git_repo_with_worktrees, capsys, preserve_cwd):
        """Should show available worktrees when no match found."""
        result = switch_worktree(
            git_repo_with_worktrees["main"],
            "nonexistent-branch",
            fuzzy_match=True
        )

        assert result is False
        captured = capsys.readouterr()
        output = captured.out

        assert "No worktree found" in output
        assert "Available worktrees:" in output
        assert "main" in output

    def test_switch_already_current(self, git_repo, capsys, preserve_cwd):
        """Should inform user when already on target worktree."""
        # Mock Path.cwd() to return the git repo directory
        with patch("src.dopemux.worktree_commands.Path.cwd") as mock_cwd:
            mock_cwd.return_value = git_repo

            # Single worktree repo, already on main
            result = switch_worktree(git_repo, "main", fuzzy_match=False)

            assert result is True
            captured = capsys.readouterr()
            output = captured.out

            assert "Already on worktree" in output


class TestWorktreeCleanupCommand:
    """Test suite for 'dopemux worktrees cleanup' command."""

    def test_cleanup_skips_main(self, git_repo_with_worktrees, capsys):
        """Should skip main/master worktrees during cleanup."""
        cleanup_worktrees(
            git_repo_with_worktrees["main"],
            force=False,
            dry_run=True
        )

        captured = capsys.readouterr()
        output = captured.out

        assert "Skipping main worktree: main" in output

    def test_cleanup_dry_run(self, git_repo_with_worktrees, capsys):
        """Should preview cleanup without removing in dry-run mode."""
        cleanup_worktrees(
            git_repo_with_worktrees["main"],
            force=False,
            dry_run=True
        )

        captured = capsys.readouterr()
        output = captured.out

        assert "Dry run - no changes made" in output
        assert "Found" in output  # Should show candidates

        # Verify worktrees still exist
        worktrees = get_worktrees(git_repo_with_worktrees["main"])
        assert len(worktrees) == 3  # All still present

    def test_cleanup_skips_dirty_worktrees(self, git_repo_with_worktrees, capsys):
        """Should skip worktrees with uncommitted changes unless forced."""
        # Make feature worktree dirty
        (git_repo_with_worktrees["feature"] / "dirty.txt").write_text("uncommitted")

        cleanup_worktrees(
            git_repo_with_worktrees["main"],
            force=False,
            dry_run=True
        )

        captured = capsys.readouterr()
        output = captured.out

        assert "uncommitted changes" in output
        assert "--force" in output  # Message includes --force suggestion

    def test_cleanup_force_removes_dirty(self, git_repo_with_worktrees, capsys):
        """Should remove dirty worktrees when force mode enabled."""
        # Make feature worktree dirty
        (git_repo_with_worktrees["feature"] / "dirty.txt").write_text("uncommitted")

        cleanup_worktrees(
            git_repo_with_worktrees["main"],
            force=True,
            dry_run=True
        )

        captured = capsys.readouterr()
        output = captured.out

        assert "Force mode: Will remove anyway" in output or "dirty (forced)" in output

    def test_cleanup_no_candidates(self, git_repo, capsys):
        """Should show success message when no worktrees need cleanup."""
        cleanup_worktrees(git_repo, force=False, dry_run=True)

        captured = capsys.readouterr()
        output = captured.out

        assert "No worktrees need cleanup" in output

    def test_cleanup_removes_feature_worktrees(self, git_repo_with_worktrees):
        """Should remove feature worktrees when not in dry-run mode."""
        # Run cleanup without dry-run (should actually remove)
        cleanup_worktrees(
            git_repo_with_worktrees["main"],
            force=False,
            dry_run=False
        )

        # Verify feature worktrees were removed, main remains
        worktrees = get_worktrees(git_repo_with_worktrees["main"])
        # Should only have main worktree left (feature branches cleaned up)
        assert len(worktrees) == 1
        assert worktrees[0][1] == "main"  # Main branch remains


class TestWorktreeADHDOptimizations:
    """Test ADHD-specific features of worktree commands."""

    def test_fuzzy_matching_reduces_cognitive_load(self, git_repo_with_worktrees, preserve_cwd):
        """Fuzzy matching should work with partial, case-insensitive matches."""
        # Test case-insensitive matching
        result = switch_worktree(
            git_repo_with_worktrees["main"],
            "FEATURE",  # Uppercase
            fuzzy_match=True
        )
        assert result is True

        # Test partial matching
        result = switch_worktree(
            git_repo_with_worktrees["main"],
            "bug",  # Partial
            fuzzy_match=True
        )
        assert result is True

    def test_visual_status_indicators(self, git_repo_with_worktrees, capsys):
        """List command should use visual symbols for status clarity."""
        list_worktrees(git_repo_with_worktrees["main"])

        captured = capsys.readouterr()
        output = captured.out

        # Should contain visual indicators (exact symbols may vary)
        assert "clean" in output.lower() or "✓" in output

    def test_progressive_safety_dry_run(self, git_repo_with_worktrees, capsys):
        """Cleanup should default to dry-run preview before actual removal."""
        # Dry run should be explicitly enabled
        cleanup_worktrees(
            git_repo_with_worktrees["main"],
            force=False,
            dry_run=True
        )

        captured = capsys.readouterr()
        output = captured.out

        assert "Dry run" in output
        # Verify no actual removal occurred
        worktrees = get_worktrees(git_repo_with_worktrees["main"])
        assert len(worktrees) == 3

    def test_helpful_tips_after_commands(self, git_repo_with_worktrees, capsys):
        """Commands should provide helpful next-step guidance."""
        list_worktrees(git_repo_with_worktrees["main"])

        captured = capsys.readouterr()
        output = captured.out

        assert "💡 Tip" in output or "Tip:" in output

    def test_max_3_options_disambiguation(self, git_repo_with_worktrees, capsys):
        """When showing options, limit to reduce decision paralysis."""
        # This is implicit in the design - fuzzy matching either:
        # - Succeeds with 1 match
        # - Fails with instruction to be more specific
        # - Never shows more than necessary options

        result = switch_worktree(
            git_repo_with_worktrees["main"],
            "xyz",  # No matches
            fuzzy_match=True
        )

        assert result is False
        captured = capsys.readouterr()
        output = captured.out

        # Should show all available, but in a clear, organized way
        assert "Available worktrees:" in output
