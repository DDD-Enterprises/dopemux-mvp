"""
Tests for MainWorktreeDetector.

Tests protection trigger logic, warning messages, and operation blocking.
"""

import pytest
from pathlib import Path
import tempfile
import subprocess

from src.dopemux.main_worktree_detector import (
    MainWorktreeDetector,
    ProtectionTrigger,
    check_main_protection,
    should_warn_user,
)
from src.dopemux.uncommitted_detector import ChangesSummary


@pytest.fixture
def git_repo():
    """Create a temporary git repository for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)

        # Initialize git repo
        subprocess.run(["git", "init", "-b", "main"], cwd=repo_path, check=True, capture_output=True)
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


def test_protection_trigger_format_warning():
    """Test ProtectionTrigger warning message formatting."""
    changes = ChangesSummary(
        has_changes=True,
        staged_count=2,
        unstaged_count=1,
        untracked_count=0,
        stashed_count=0,
        total_files=3
    )

    trigger = ProtectionTrigger(
        workspace_path="/test/path",
        git_branch="main",
        changes=changes,
        trigger_reason="staged changes in main",
        suggested_action="Create a worktree"
    )

    warning = trigger.format_warning()

    # Should include all key information
    assert "Main Worktree Protection" in warning
    assert "main" in warning  # Branch name
    assert "2 staged" in warning  # Change summary
    assert "Create a worktree" in warning  # Suggested action


def test_main_worktree_detector_initialization(git_repo):
    """Test MainWorktreeDetector initialization."""
    detector = MainWorktreeDetector(str(git_repo))

    assert detector.workspace_path == git_repo
    assert detector.enforce_protection is False  # Default
    assert detector.detector is not None


def test_main_worktree_detector_enforce_mode(git_repo):
    """Test initialization with enforcement enabled."""
    detector = MainWorktreeDetector(str(git_repo), enforce_protection=True)

    assert detector.enforce_protection is True


def test_check_protection_not_needed_clean_repo(git_repo):
    """Test no protection needed on clean main branch."""
    detector = MainWorktreeDetector(str(git_repo))

    trigger = detector.check_protection_needed()

    # Clean repo - no protection needed
    assert trigger is None


def test_check_protection_not_needed_feature_branch(git_repo):
    """Test no protection needed on feature branch (even with changes)."""
    # Create and checkout feature branch
    subprocess.run(
        ["git", "checkout", "-b", "feature/test"],
        cwd=git_repo,
        check=True,
        capture_output=True
    )

    # Add changes
    (git_repo / "test.txt").write_text("Changes")

    detector = MainWorktreeDetector(str(git_repo))
    trigger = detector.check_protection_needed()

    # Feature branch - no protection needed
    assert trigger is None


def test_check_protection_needed_unstaged_changes(git_repo):
    """Test protection triggers on main with unstaged changes."""
    # Modify file
    (git_repo / "README.md").write_text("# Modified")

    detector = MainWorktreeDetector(str(git_repo))
    trigger = detector.check_protection_needed()

    # Should trigger protection
    assert trigger is not None
    assert trigger.git_branch == "main"
    assert trigger.changes.unstaged_count == 1
    assert "uncommitted modifications" in trigger.trigger_reason


def test_check_protection_needed_staged_changes(git_repo):
    """Test protection triggers on main with staged changes."""
    # Modify and stage file
    (git_repo / "README.md").write_text("# Staged")
    subprocess.run(["git", "add", "README.md"], cwd=git_repo, check=True, capture_output=True)

    detector = MainWorktreeDetector(str(git_repo))
    trigger = detector.check_protection_needed()

    # Should trigger protection
    assert trigger is not None
    assert trigger.changes.staged_count == 1
    assert "staged changes" in trigger.trigger_reason


def test_check_protection_needed_untracked_files(git_repo):
    """Test protection triggers on main with untracked files."""
    # Create untracked file
    (git_repo / "new_file.txt").write_text("New file")

    detector = MainWorktreeDetector(str(git_repo))
    trigger = detector.check_protection_needed()

    # Should trigger protection
    assert trigger is not None
    assert trigger.changes.untracked_count == 1
    assert "untracked files" in trigger.trigger_reason


def test_check_protection_needed_stashed_changes(git_repo):
    """Test protection triggers on main with stashed changes."""
    # Create and stash changes
    (git_repo / "README.md").write_text("# Stashed")
    subprocess.run(["git", "add", "README.md"], cwd=git_repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "stash", "push", "-m", "Test stash"],
        cwd=git_repo,
        check=True,
        capture_output=True
    )

    detector = MainWorktreeDetector(str(git_repo))
    trigger = detector.check_protection_needed()

    # Should trigger protection
    assert trigger is not None
    assert trigger.changes.stashed_count == 1
    assert "stashed changes" in trigger.trigger_reason


def test_should_block_operation_no_enforcement(git_repo):
    """Test operations not blocked without enforcement."""
    # Add changes
    (git_repo / "README.md").write_text("# Modified")

    # Enforcement disabled
    detector = MainWorktreeDetector(str(git_repo), enforce_protection=False)

    # Should NOT block (warn only)
    assert detector.should_block_operation("commit") is False
    assert detector.should_block_operation("push") is False


def test_should_block_operation_with_enforcement(git_repo):
    """Test operations blocked with enforcement enabled."""
    # Add changes
    (git_repo / "README.md").write_text("# Modified")

    # Enforcement enabled
    detector = MainWorktreeDetector(str(git_repo), enforce_protection=True)

    # Should block risky operations
    assert detector.should_block_operation("commit") is True
    assert detector.should_block_operation("push") is True
    assert detector.should_block_operation("merge") is True


def test_should_not_block_safe_operations(git_repo):
    """Test safe operations not blocked even with enforcement."""
    # Add changes
    (git_repo / "README.md").write_text("# Modified")

    # Enforcement enabled
    detector = MainWorktreeDetector(str(git_repo), enforce_protection=True)

    # Safe operations should not block
    assert detector.should_block_operation("status") is False
    assert detector.should_block_operation("diff") is False
    assert detector.should_block_operation("log") is False


def test_should_not_block_on_clean_repo(git_repo):
    """Test no blocking on clean repo even with enforcement."""
    # Enforcement enabled
    detector = MainWorktreeDetector(str(git_repo), enforce_protection=True)

    # Clean repo - should not block anything
    assert detector.should_block_operation("commit") is False


def test_get_interactive_prompt_with_changes(git_repo):
    """Test interactive prompt generation with changes."""
    # Add changes
    (git_repo / "README.md").write_text("# Modified")

    detector = MainWorktreeDetector(str(git_repo))
    prompt = detector.get_interactive_prompt()

    # Should generate prompt
    assert prompt is not None
    assert "Main Worktree Protection" in prompt
    assert "Would you like to create a worktree now?" in prompt
    assert "[y/N]" in prompt  # Safe default


def test_get_interactive_prompt_without_changes(git_repo):
    """Test no prompt on clean repo."""
    detector = MainWorktreeDetector(str(git_repo))
    prompt = detector.get_interactive_prompt()

    # No changes - no prompt
    assert prompt is None


def test_check_main_protection_helper(git_repo):
    """Test synchronous helper function."""
    # Add changes
    (git_repo / "README.md").write_text("# Modified")

    trigger = check_main_protection(str(git_repo))

    # Should return trigger
    assert trigger is not None
    assert trigger.changes.unstaged_count == 1


def test_check_main_protection_helper_clean(git_repo):
    """Test helper returns None for clean repo."""
    trigger = check_main_protection(str(git_repo))

    # Clean - no trigger
    assert trigger is None


def test_should_warn_user_helper(git_repo):
    """Test should_warn_user helper function."""
    # Clean repo - no warning
    assert should_warn_user(str(git_repo)) is False

    # Add changes - should warn
    (git_repo / "README.md").write_text("# Modified")
    assert should_warn_user(str(git_repo)) is True


def test_protection_trigger_suggested_action():
    """Test suggested action includes actionable guidance."""
    changes = ChangesSummary(
        has_changes=True,
        staged_count=1,
        unstaged_count=0,
        untracked_count=0,
        stashed_count=0,
        total_files=1
    )

    trigger = ProtectionTrigger(
        workspace_path="/test",
        git_branch="main",
        changes=changes,
        trigger_reason="test",
        suggested_action="Create a worktree to keep main clean. Run 'dopemux start' to create a new worktree automatically."
    )

    # Should include specific command
    assert "dopemux start" in trigger.suggested_action
    assert "worktree" in trigger.suggested_action


def test_case_insensitive_operation_blocking(git_repo):
    """Test operation blocking is case-insensitive."""
    # Add changes
    (git_repo / "README.md").write_text("# Modified")

    detector = MainWorktreeDetector(str(git_repo), enforce_protection=True)

    # Case variations should all block
    assert detector.should_block_operation("COMMIT") is True
    assert detector.should_block_operation("Commit") is True
    assert detector.should_block_operation("commit") is True


def test_protection_on_master_branch(git_repo):
    """Test protection works on 'master' branch too."""
    # Rename main to master
    subprocess.run(
        ["git", "branch", "-m", "master"],
        cwd=git_repo,
        check=True,
        capture_output=True
    )

    # Add changes
    (git_repo / "README.md").write_text("# Modified")

    detector = MainWorktreeDetector(str(git_repo))
    trigger = detector.check_protection_needed()

    # Should trigger on master too
    assert trigger is not None
    assert trigger.git_branch == "master"


def test_helper_handles_non_git_directory():
    """Test helpers handle non-git directories gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Should not crash, just return None/False
        assert check_main_protection(tmpdir) is None
        assert should_warn_user(tmpdir) is False
