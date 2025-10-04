"""
Tests for UncommittedChangeDetector.

Tests git status parsing, change detection, and main worktree protection logic.
"""

import pytest
from pathlib import Path
import tempfile
import subprocess

from src.dopemux.uncommitted_detector import (
    ChangesSummary,
    UncommittedChangeDetector,
    check_uncommitted_changes,
    should_protect_main,
)


@pytest.fixture
def git_repo():
    """Create a temporary git repository for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)

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

        # Create initial commit
        (repo_path / "README.md").write_text("# Test Repo")
        subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=repo_path,
            check=True,
            capture_output=True
        )

        yield repo_path


def test_changes_summary_is_clean():
    """Test ChangesSummary.is_clean() method."""
    # Clean state
    clean = ChangesSummary(
        has_changes=False,
        staged_count=0,
        unstaged_count=0,
        untracked_count=0,
        stashed_count=0,
        total_files=0
    )
    assert clean.is_clean() is True

    # Has changes
    with_changes = ChangesSummary(
        has_changes=True,
        staged_count=1,
        unstaged_count=0,
        untracked_count=0,
        stashed_count=0,
        total_files=1
    )
    assert with_changes.is_clean() is False

    # Has stash (even if no working tree changes)
    with_stash = ChangesSummary(
        has_changes=False,
        staged_count=0,
        unstaged_count=0,
        untracked_count=0,
        stashed_count=1,
        total_files=0
    )
    assert with_stash.is_clean() is False


def test_changes_summary_format_summary():
    """Test human-readable summary formatting."""
    # No changes
    summary1 = ChangesSummary(
        has_changes=False,
        staged_count=0,
        unstaged_count=0,
        untracked_count=0,
        stashed_count=0,
        total_files=0
    )
    assert summary1.format_summary() == "No changes"

    # Staged only
    summary2 = ChangesSummary(
        has_changes=True,
        staged_count=3,
        unstaged_count=0,
        untracked_count=0,
        stashed_count=0,
        total_files=3
    )
    assert summary2.format_summary() == "3 staged"

    # Mixed changes
    summary3 = ChangesSummary(
        has_changes=True,
        staged_count=2,
        unstaged_count=3,
        untracked_count=1,
        stashed_count=1,
        total_files=6
    )
    assert "2 staged" in summary3.format_summary()
    assert "3 unstaged" in summary3.format_summary()
    assert "1 untracked" in summary3.format_summary()
    assert "1 stashed" in summary3.format_summary()


def test_changes_summary_needs_worktree_suggestion():
    """Test worktree suggestion logic."""
    # Clean - no suggestion
    clean = ChangesSummary(
        has_changes=False,
        staged_count=0,
        unstaged_count=0,
        untracked_count=0,
        stashed_count=0,
        total_files=0
    )
    assert clean.needs_worktree_suggestion() is False

    # Has changes - suggest
    with_changes = ChangesSummary(
        has_changes=True,
        staged_count=1,
        unstaged_count=0,
        untracked_count=0,
        stashed_count=0,
        total_files=1
    )
    assert with_changes.needs_worktree_suggestion() is True

    # Has stash only - suggest
    with_stash = ChangesSummary(
        has_changes=False,
        staged_count=0,
        unstaged_count=0,
        untracked_count=0,
        stashed_count=1,
        total_files=0
    )
    assert with_stash.needs_worktree_suggestion() is True


def test_uncommitted_detector_initialization(git_repo):
    """Test UncommittedChangeDetector initialization."""
    detector = UncommittedChangeDetector(str(git_repo))
    assert detector.workspace_path == git_repo


def test_uncommitted_detector_non_git_repo():
    """Test initialization with non-git directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(ValueError, match="Not a git repository"):
            UncommittedChangeDetector(tmpdir)


def test_check_changes_clean_repo(git_repo):
    """Test detection on clean repository."""
    detector = UncommittedChangeDetector(str(git_repo))
    changes = detector.check_changes()

    assert changes.has_changes is False
    assert changes.staged_count == 0
    assert changes.unstaged_count == 0
    assert changes.untracked_count == 0
    assert changes.total_files == 0


def test_check_changes_unstaged_modifications(git_repo):
    """Test detection of unstaged modifications."""
    # Modify existing file
    (git_repo / "README.md").write_text("# Modified Content")

    detector = UncommittedChangeDetector(str(git_repo))
    changes = detector.check_changes()

    assert changes.has_changes is True
    assert changes.unstaged_count == 1
    assert changes.staged_count == 0
    assert changes.total_files == 1


def test_check_changes_staged_modifications(git_repo):
    """Test detection of staged modifications."""
    # Modify and stage file
    (git_repo / "README.md").write_text("# Staged Content")
    subprocess.run(["git", "add", "README.md"], cwd=git_repo, check=True, capture_output=True)

    detector = UncommittedChangeDetector(str(git_repo))
    changes = detector.check_changes()

    assert changes.has_changes is True
    assert changes.staged_count == 1
    assert changes.unstaged_count == 0
    assert changes.total_files == 1


def test_check_changes_untracked_files(git_repo):
    """Test detection of untracked files."""
    # Create untracked file
    (git_repo / "new_file.txt").write_text("New file content")

    detector = UncommittedChangeDetector(str(git_repo))
    changes = detector.check_changes()

    assert changes.has_changes is True
    assert changes.untracked_count == 1
    assert changes.staged_count == 0
    assert changes.unstaged_count == 0
    assert changes.total_files == 1


def test_check_changes_mixed_states(git_repo):
    """Test detection with mixed change states."""
    # Staged change
    (git_repo / "README.md").write_text("# Staged")
    subprocess.run(["git", "add", "README.md"], cwd=git_repo, check=True, capture_output=True)

    # Unstaged change
    (git_repo / "README.md").write_text("# Staged + Unstaged")

    # Untracked file
    (git_repo / "untracked.txt").write_text("Untracked")

    detector = UncommittedChangeDetector(str(git_repo))
    changes = detector.check_changes()

    assert changes.has_changes is True
    assert changes.staged_count == 1
    assert changes.unstaged_count == 1
    assert changes.untracked_count == 1
    assert changes.total_files == 3


def test_check_changes_with_stash(git_repo):
    """Test stash detection."""
    # Create and stash changes
    (git_repo / "README.md").write_text("# Stashed Content")
    subprocess.run(["git", "add", "README.md"], cwd=git_repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "stash", "push", "-m", "Test stash"],
        cwd=git_repo,
        check=True,
        capture_output=True
    )

    detector = UncommittedChangeDetector(str(git_repo))
    changes = detector.check_changes()

    # Working tree should be clean after stash
    assert changes.has_changes is False
    assert changes.total_files == 0

    # But stash should be detected
    assert changes.stashed_count == 1


def test_is_on_main_branch(git_repo):
    """Test main branch detection."""
    detector = UncommittedChangeDetector(str(git_repo))

    # Default branch should be main or master
    assert detector.is_on_main_branch() is True

    # Create and checkout feature branch
    subprocess.run(
        ["git", "checkout", "-b", "feature/test"],
        cwd=git_repo,
        check=True,
        capture_output=True
    )

    assert detector.is_on_main_branch() is False


def test_should_suggest_worktree_on_main_with_changes(git_repo):
    """Test worktree suggestion on main with uncommitted changes."""
    # Ensure on main branch
    detector = UncommittedChangeDetector(str(git_repo))
    assert detector.is_on_main_branch() is True

    # No changes - no suggestion
    assert detector.should_suggest_worktree() is False

    # Add changes
    (git_repo / "README.md").write_text("# Modified")

    assert detector.should_suggest_worktree() is True


def test_should_suggest_worktree_on_feature_branch(git_repo):
    """Test no worktree suggestion on feature branch."""
    # Create and checkout feature branch
    subprocess.run(
        ["git", "checkout", "-b", "feature/test"],
        cwd=git_repo,
        check=True,
        capture_output=True
    )

    detector = UncommittedChangeDetector(str(git_repo))

    # Add changes
    (git_repo / "README.md").write_text("# Modified on feature")

    # Should NOT suggest worktree (already on feature branch)
    assert detector.should_suggest_worktree() is False


def test_get_protection_message(git_repo):
    """Test protection message generation."""
    detector = UncommittedChangeDetector(str(git_repo))

    # No changes - no message
    assert detector.get_protection_message() is None

    # Add changes on main
    (git_repo / "README.md").write_text("# Modified")

    message = detector.get_protection_message()
    assert message is not None
    assert "Main Worktree Protection" in message
    assert "uncommitted changes" in message
    assert "1 unstaged" in message  # Should include change summary


def test_get_protection_message_on_feature_branch(git_repo):
    """Test no protection message on feature branch."""
    # Checkout feature branch
    subprocess.run(
        ["git", "checkout", "-b", "feature/test"],
        cwd=git_repo,
        check=True,
        capture_output=True
    )

    detector = UncommittedChangeDetector(str(git_repo))

    # Add changes
    (git_repo / "README.md").write_text("# Modified")

    # No protection message on feature branch
    assert detector.get_protection_message() is None


def test_check_uncommitted_changes_helper(git_repo):
    """Test synchronous helper function."""
    # Add changes
    (git_repo / "README.md").write_text("# Modified")

    changes = check_uncommitted_changes(str(git_repo))

    assert changes.has_changes is True
    assert changes.unstaged_count == 1


def test_should_protect_main_helper(git_repo):
    """Test should_protect_main helper function."""
    # Clean main - no protection
    assert should_protect_main(str(git_repo)) is False

    # Add changes on main
    (git_repo / "README.md").write_text("# Modified")

    assert should_protect_main(str(git_repo)) is True


def test_should_protect_main_non_git_repo():
    """Test should_protect_main with non-git directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Should not raise, just return False
        assert should_protect_main(tmpdir) is False
