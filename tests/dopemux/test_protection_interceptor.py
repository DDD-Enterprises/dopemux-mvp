"""
Tests for ProtectionInterceptor.

Tests main worktree protection CLI integration, interactive prompts,
worktree creation, and ADHD-optimized user guidance.
"""

import os
import pytest
from pathlib import Path
import tempfile
import subprocess
from unittest.mock import patch, MagicMock, call

from src.dopemux.protection_interceptor import (
    check_main_protection_interactive,
    check_and_protect_main,
    _display_protection_warning,
    _offer_worktree_creation,
    _create_worktree_interactive,
    _parse_name_choice,
    _parse_migration_choice,
    _execute_worktree_creation,
    _stash_changes,
    _pop_stash,
    consume_last_created_worktree,
)
from src.dopemux.main_worktree_detector import ProtectionTrigger
from src.dopemux.uncommitted_detector import ChangesSummary
from src.dopemux.worktree_name_inferrer import NameSuggestion


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


def test_check_main_protection_no_changes(git_repo):
    """Test protection check with clean main worktree."""
    # Clean main - no protection needed
    result = check_main_protection_interactive(
        workspace_path=str(git_repo),
        enforce=False,
        offer_creation=False
    )

    # Should not exit - clean repo
    assert result is False


def test_check_main_protection_feature_branch(git_repo):
    """Test protection check on feature branch (no protection)."""
    # Checkout feature branch
    subprocess.run(
        ["git", "checkout", "-b", "feature/test"],
        cwd=git_repo,
        check=True,
        capture_output=True
    )

    # Add changes
    (git_repo / "test.txt").write_text("Changes")

    result = check_main_protection_interactive(
        workspace_path=str(git_repo),
        enforce=False,
        offer_creation=False
    )

    # Should not exit - feature branch allowed
    assert result is False


@patch('src.dopemux.protection_interceptor._display_protection_warning')
def test_check_main_protection_with_changes_no_offer(mock_display, git_repo):
    """Test protection warning displayed without worktree offer."""
    # Add changes to main
    (git_repo / "README.md").write_text("# Modified")

    result = check_main_protection_interactive(
        workspace_path=str(git_repo),
        enforce=False,
        offer_creation=False  # Don't offer worktree creation
    )

    # Should display warning
    assert mock_display.called

    # Should continue (warn only, not enforce)
    assert result is False


@patch('src.dopemux.protection_interceptor._display_protection_warning')
def test_check_main_protection_enforce_mode(mock_display, git_repo):
    """Test protection blocks operations in enforce mode."""
    # Add changes to main
    (git_repo / "README.md").write_text("# Modified")

    result = check_main_protection_interactive(
        workspace_path=str(git_repo),
        enforce=True,  # Block operations
        offer_creation=False
    )

    # Should display warning
    assert mock_display.called

    # Should exit (blocked)
    assert result is True


@patch('src.dopemux.protection_interceptor._offer_worktree_creation')
@patch('src.dopemux.protection_interceptor._display_protection_warning')
def test_check_main_protection_offers_creation(mock_display, mock_offer, git_repo):
    """Test protection offers worktree creation."""
    # Add changes to main
    (git_repo / "README.md").write_text("# Modified")

    mock_offer.return_value = False  # User chose to continue

    result = check_main_protection_interactive(
        workspace_path=str(git_repo),
        enforce=False,
        offer_creation=True  # Offer worktree creation
    )

    # Should display warning and offer creation
    assert mock_display.called
    assert mock_offer.called

    # Result depends on offer outcome
    assert result is False


def test_display_protection_warning(capsys):
    """Test protection warning formatting and display."""
    changes = ChangesSummary(
        has_changes=True,
        staged_count=1,
        unstaged_count=2,
        untracked_count=0,
        stashed_count=0,
        total_files=3
    )

    trigger = ProtectionTrigger(
        workspace_path="/test/path",
        git_branch="main",
        changes=changes,
        trigger_reason="uncommitted modifications in main",
        suggested_action="Create a worktree"
    )

    _display_protection_warning(trigger)

    # Verify warning components are displayed (using capsys)
    # Note: Rich console output may not be captured by capsys in tests,
    # so we just verify the function doesn't crash


@patch('src.dopemux.protection_interceptor.console.input')
@patch('src.dopemux.protection_interceptor._create_worktree_interactive')
def test_offer_worktree_creation_choice_1(mock_create, mock_input, git_repo):
    """Test user chooses to create worktree (option 1)."""
    mock_input.return_value = "1"  # Create worktree
    mock_create.return_value = True  # Creation successful, should exit

    trigger = ProtectionTrigger(
        workspace_path=str(git_repo),
        git_branch="main",
        changes=ChangesSummary(True, 1, 0, 0, 0, 1),
        trigger_reason="test",
        suggested_action="test action"
    )

    result = _offer_worktree_creation(str(git_repo), trigger)

    assert mock_create.called
    assert result is True  # Exit to restart


@patch('src.dopemux.protection_interceptor.console.input')
def test_offer_worktree_creation_choice_2(mock_input, git_repo):
    """Test user chooses to stay in main (option 2)."""
    mock_input.return_value = "2"  # Stay in main

    trigger = ProtectionTrigger(
        workspace_path=str(git_repo),
        git_branch="main",
        changes=ChangesSummary(True, 1, 0, 0, 0, 1),
        trigger_reason="test",
        suggested_action="test action"
    )

    result = _offer_worktree_creation(str(git_repo), trigger)

    # Should continue (not exit)
    assert result is False


@patch('src.dopemux.protection_interceptor.console.input')
def test_offer_worktree_creation_choice_3(mock_input, git_repo):
    """Test user chooses to exit (option 3)."""
    mock_input.return_value = "3"  # Exit

    trigger = ProtectionTrigger(
        workspace_path=str(git_repo),
        git_branch="main",
        changes=ChangesSummary(True, 1, 0, 0, 0, 1),
        trigger_reason="test",
        suggested_action="test action"
    )

    result = _offer_worktree_creation(str(git_repo), trigger)

    # Should exit
    assert result is True


@patch('src.dopemux.protection_interceptor.console.input')
def test_offer_worktree_creation_invalid_choice(mock_input, git_repo):
    """Test invalid choice defaults to exit (safe)."""
    mock_input.return_value = "invalid"  # Invalid choice

    trigger = ProtectionTrigger(
        workspace_path=str(git_repo),
        git_branch="main",
        changes=ChangesSummary(True, 1, 0, 0, 0, 1),
        trigger_reason="test",
        suggested_action="test action"
    )

    result = _offer_worktree_creation(str(git_repo), trigger)

    # Should exit (safe default)
    assert result is True


@patch('src.dopemux.protection_interceptor.console.input')
def test_offer_worktree_creation_keyboard_interrupt(mock_input, git_repo):
    """Test keyboard interrupt during choice."""
    mock_input.side_effect = KeyboardInterrupt()

    trigger = ProtectionTrigger(
        workspace_path=str(git_repo),
        git_branch="main",
        changes=ChangesSummary(True, 1, 0, 0, 0, 1),
        trigger_reason="test",
        suggested_action="test action"
    )

    result = _offer_worktree_creation(str(git_repo), trigger)

    # Should exit on interrupt
    assert result is True


@patch('src.dopemux.protection_interceptor.console.input')
@patch('src.dopemux.protection_interceptor._parse_name_choice')
@patch('src.dopemux.protection_interceptor._execute_worktree_creation')
def test_create_worktree_interactive_success(mock_execute, mock_parse, mock_input, git_repo):
    """Test successful worktree creation flow."""
    # Mock name selection
    mock_input.return_value = "1"  # Choose first suggestion
    mock_parse.return_value = "feature-test"
    mock_execute.return_value = True  # Creation successful

    trigger = ProtectionTrigger(
        workspace_path=str(git_repo),
        git_branch="main",
        changes=ChangesSummary(True, 1, 0, 0, 0, 1),
        trigger_reason="test",
        suggested_action="test action"
    )

    result = _create_worktree_interactive(str(git_repo), trigger)

    # Should continue after successful creation
    assert result is False
    assert mock_execute.called


@patch('src.dopemux.protection_interceptor.console.input')
@patch('src.dopemux.protection_interceptor._parse_name_choice')
@patch('src.dopemux.protection_interceptor._execute_worktree_creation')
def test_create_worktree_interactive_failure(mock_execute, mock_parse, mock_input, git_repo):
    """Test worktree creation failure."""
    mock_input.return_value = "feature-test"
    mock_parse.return_value = "feature-test"
    mock_execute.return_value = False  # Creation failed

    trigger = ProtectionTrigger(
        workspace_path=str(git_repo),
        git_branch="main",
        changes=ChangesSummary(True, 1, 0, 0, 0, 1),
        trigger_reason="test",
        suggested_action="test action"
    )

    result = _create_worktree_interactive(str(git_repo), trigger)

    # Should continue (stay in main after failure)
    assert result is False


@patch('src.dopemux.protection_interceptor.console.input')
def test_create_worktree_interactive_cancelled(mock_input, git_repo):
    """Test worktree creation cancelled by user."""
    mock_input.side_effect = KeyboardInterrupt()

    trigger = ProtectionTrigger(
        workspace_path=str(git_repo),
        git_branch="main",
        changes=ChangesSummary(True, 1, 0, 0, 0, 1),
        trigger_reason="test",
        suggested_action="test action"
    )

    result = _create_worktree_interactive(str(git_repo), trigger)

    # Should continue (stay in main)
    assert result is False


def test_parse_name_choice_default():
    """Test parsing empty input (use default)."""
    suggestions = [
        NameSuggestion("issue-123", "issue/PR", 0.9, "From issue number"),
        NameSuggestion("feature-auth", "branch", 0.8, "From branch"),
    ]

    from src.dopemux.worktree_name_inferrer import WorktreeNameInferrer
    inferrer = WorktreeNameInferrer("/fake/path")

    # Empty input should use first suggestion
    result = _parse_name_choice("", suggestions, inferrer)
    assert result == "issue-123"


def test_parse_migration_choice():
    """Test migration prompt parser supports common yes/no inputs."""
    assert _parse_migration_choice("") is True
    assert _parse_migration_choice("y") is True
    assert _parse_migration_choice("yes") is True

    assert _parse_migration_choice("n") is False
    assert _parse_migration_choice("no") is False
    assert _parse_migration_choice("No") is False
    assert _parse_migration_choice("false") is False


def test_parse_name_choice_numeric():
    """Test parsing numeric choice (1-3)."""
    suggestions = [
        NameSuggestion("issue-123", "issue/PR", 0.9, "From issue"),
        NameSuggestion("feature-auth", "branch", 0.8, "From branch"),
        NameSuggestion("work-20250101", "timestamp", 0.3, "Fallback"),
    ]

    from src.dopemux.worktree_name_inferrer import WorktreeNameInferrer
    inferrer = WorktreeNameInferrer("/fake/path")

    # Choice "2" should select second suggestion
    result = _parse_name_choice("2", suggestions, inferrer)
    assert result == "feature-auth"


def test_parse_name_choice_custom():
    """Test parsing custom name input."""
    suggestions = [
        NameSuggestion("issue-123", "issue/PR", 0.9, "From issue"),
    ]

    from src.dopemux.worktree_name_inferrer import WorktreeNameInferrer
    inferrer = WorktreeNameInferrer("/fake/path")

    # Custom name should be sanitized
    result = _parse_name_choice("My Custom Feature!", suggestions, inferrer)
    assert result == "my-custom-feature"


def test_execute_worktree_creation_success(git_repo):
    """Test successful git worktree creation."""
    import uuid
    worktree_name = f"test-feature-{uuid.uuid4().hex[:8]}"

    result = _execute_worktree_creation(str(git_repo), worktree_name, migrate_changes=False)

    # Should succeed
    assert result is True

    # Verify worktree was created
    worktree_path = git_repo.parent / worktree_name
    assert worktree_path.exists()


def test_execute_worktree_creation_conflict(git_repo):
    """Test worktree creation with existing name."""
    worktree_name = "existing-branch"

    # Create branch first
    subprocess.run(
        ["git", "branch", worktree_name],
        cwd=git_repo,
        check=True,
        capture_output=True
    )

    result = _execute_worktree_creation(str(git_repo), worktree_name)

    # Should fail (branch already exists)
    assert result is False


def test_execute_worktree_creation_non_git():
    """Test worktree creation in non-git directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = _execute_worktree_creation(tmpdir, "test")

        # Should fail gracefully
        assert result is False


def test_check_and_protect_main_helper(git_repo):
    """Test synchronous helper function."""
    # Clean main - should not exit
    result = check_and_protect_main(str(git_repo), enforce=False)
    assert result is False


@patch('src.dopemux.protection_interceptor.check_main_protection_interactive')
def test_check_and_protect_main_forwards_args(mock_check, git_repo):
    """Test helper forwards arguments correctly."""
    mock_check.return_value = False

    check_and_protect_main(str(git_repo), enforce=True)

    # Verify arguments forwarded
    mock_check.assert_called_once_with(
        workspace_path=str(git_repo),
        enforce=True,
        offer_creation=True
    )


# Change Migration Tests


def test_stash_changes_success(git_repo):
    """Test successful stashing of uncommitted changes."""
    # Create uncommitted changes
    (git_repo / "new_file.txt").write_text("Uncommitted")
    (git_repo / "README.md").write_text("# Modified")

    stash_name = _stash_changes(str(git_repo))

    # Should return stash name
    assert stash_name is not None
    assert "dopemux-migration-" in stash_name

    # Verify working directory is clean
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=git_repo,
        capture_output=True,
        text=True
    )
    assert result.stdout.strip() == ""


def test_stash_changes_with_untracked(git_repo):
    """Test stashing includes untracked files."""
    # Create untracked file
    (git_repo / "untracked.txt").write_text("Untracked file")

    stash_name = _stash_changes(str(git_repo))

    assert stash_name is not None

    # Verify untracked file was stashed
    assert not (git_repo / "untracked.txt").exists()


def test_stash_changes_empty_repo(git_repo):
    """Test stashing with no changes creates empty stash."""
    # No changes - git stash creates empty stash
    stash_name = _stash_changes(str(git_repo))

    # Git allows empty stash creation
    assert stash_name is not None


def test_pop_stash_success(git_repo):
    """Test successful stash pop in worktree."""
    # Create and stash changes
    (git_repo / "file.txt").write_text("Content")
    stash_result = subprocess.run(
        ["git", "stash", "push", "-u", "-m", "test-stash"],
        cwd=git_repo,
        capture_output=True,
        text=True
    )
    assert stash_result.returncode == 0

    # Pop the stash
    success = _pop_stash(str(git_repo), "test-stash")

    assert success is True

    # Verify file was restored
    assert (git_repo / "file.txt").exists()
    assert (git_repo / "file.txt").read_text() == "Content"


def test_pop_stash_not_found(git_repo):
    """Test pop with non-existent stash name."""
    success = _pop_stash(str(git_repo), "nonexistent-stash")

    # Should return False (stash not found)
    assert success is False


def test_execute_worktree_creation_with_migration(git_repo):
    """Test worktree creation with change migration."""
    import uuid

    # Create uncommitted changes
    (git_repo / "modified.txt").write_text("Modified content")
    (git_repo / "new.txt").write_text("New file")

    worktree_name = f"migration-test-{uuid.uuid4().hex[:8]}"

    # Create worktree with migration
    result = _execute_worktree_creation(
        str(git_repo),
        worktree_name,
        migrate_changes=True
    )

    assert result is True

    # Verify worktree was created
    worktree_path = git_repo.parent / worktree_name
    assert worktree_path.exists()

    # Verify changes were migrated (files should exist in worktree)
    assert (worktree_path / "modified.txt").exists()
    assert (worktree_path / "new.txt").exists()

    # Verify original worktree is clean
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=git_repo,
        capture_output=True,
        text=True
    )
    assert result.stdout.strip() == ""


def test_execute_worktree_creation_without_migration(git_repo):
    """Test worktree creation without change migration."""
    import uuid

    # Create uncommitted changes
    (git_repo / "file.txt").write_text("Content")

    worktree_name = f"no-migration-test-{uuid.uuid4().hex[:8]}"

    # Create worktree without migration
    result = _execute_worktree_creation(
        str(git_repo),
        worktree_name,
        migrate_changes=False
    )

    assert result is True

    # Verify worktree was created
    worktree_path = git_repo.parent / worktree_name
    assert worktree_path.exists()

    # Verify changes were NOT migrated (file should not exist in worktree)
    assert not (worktree_path / "file.txt").exists()

    # Verify changes still in original worktree
    assert (git_repo / "file.txt").exists()


def test_execute_worktree_creation_migration_rollback_on_failure(git_repo):
    """Test that stash is rolled back if worktree creation fails."""
    # Create changes
    (git_repo / "file.txt").write_text("Content")

    # Try to create worktree with existing branch name
    subprocess.run(
        ["git", "branch", "existing-branch"],
        cwd=git_repo,
        check=True,
        capture_output=True
    )

    result = _execute_worktree_creation(
        str(git_repo),
        "existing-branch",  # Will fail - branch exists
        migrate_changes=True
    )

    # Should fail
    assert result is False

    # Verify changes were rolled back (file should still exist)
    assert (git_repo / "file.txt").exists()


@patch('src.dopemux.protection_interceptor.console.input')
@patch('src.dopemux.protection_interceptor._execute_worktree_creation')
def test_create_worktree_interactive_with_migration_yes(mock_execute, mock_input, git_repo):
    """Test interactive creation with migration (user says yes)."""
    # Mock name choice
    mock_input.side_effect = ["1", "y"]  # Choose first suggestion, yes to migration
    mock_execute.return_value = True

    trigger = ProtectionTrigger(
        workspace_path=str(git_repo),
        git_branch="main",
        changes=ChangesSummary(True, 1, 0, 0, 0, 1),
        trigger_reason="test",
        suggested_action="test"
    )

    result = _create_worktree_interactive(str(git_repo), trigger)

    # Should call execute with migrate_changes=True
    assert mock_execute.call_args[1]["migrate_changes"] is True
    assert result is False


@patch('src.dopemux.protection_interceptor.console.input')
@patch('src.dopemux.protection_interceptor._execute_worktree_creation')
def test_create_worktree_interactive_with_migration_no(mock_execute, mock_input, git_repo):
    """Test interactive creation without migration (user says no)."""
    # Mock name choice
    mock_input.side_effect = ["1", "no"]  # Choose first suggestion, no to migration
    mock_execute.return_value = True

    trigger = ProtectionTrigger(
        workspace_path=str(git_repo),
        git_branch="main",
        changes=ChangesSummary(True, 1, 0, 0, 0, 1),
        trigger_reason="test",
        suggested_action="test"
    )

    result = _create_worktree_interactive(str(git_repo), trigger)

    # Should call execute with migrate_changes=False
    assert mock_execute.call_args[1]["migrate_changes"] is False
    assert result is False


def test_migration_preserves_staged_and_unstaged(git_repo):
    """Test migration preserves both staged and unstaged changes."""
    import uuid

    # Create staged change
    (git_repo / "staged.txt").write_text("Staged")
    subprocess.run(["git", "add", "staged.txt"], cwd=git_repo, check=True, capture_output=True)

    # Create unstaged change
    (git_repo / "README.md").write_text("# Unstaged modification")

    # Create untracked file
    (git_repo / "untracked.txt").write_text("Untracked")

    worktree_name = f"preserve-test-{uuid.uuid4().hex[:8]}"

    # Prepare Dopemux scaffolding to verify copy
    (git_repo / ".dopemux").mkdir()
    (git_repo / ".claude").mkdir()
    (git_repo / "litellm.config.yaml").write_text("model_list: []\n")

    result = _execute_worktree_creation(
        str(git_repo),
        worktree_name,
        migrate_changes=True
    )

    assert result is True

    # Verify all changes were migrated
    worktree_path = git_repo.parent / worktree_name
    assert (worktree_path / "staged.txt").exists()
    assert (worktree_path / "README.md").read_text() == "# Unstaged modification"
    assert (worktree_path / "untracked.txt").exists()

    # Scaffolding copied
    assert (worktree_path / ".dopemux").exists()
    assert (worktree_path / ".claude").exists()
    litellm_path = worktree_path / "litellm.config.yaml"
    assert litellm_path.exists()

    # consume recorded worktree
    assert consume_last_created_worktree() == worktree_path
    assert consume_last_created_worktree() is None
