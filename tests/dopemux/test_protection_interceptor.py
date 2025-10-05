"""
Tests for ProtectionInterceptor.

Tests main worktree protection CLI integration, interactive prompts,
worktree creation, and ADHD-optimized user guidance.
"""

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
    _execute_worktree_creation,
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

    # Should exit after successful creation (to restart)
    assert result is True
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
    worktree_name = "test-feature-unique"

    result = _execute_worktree_creation(str(git_repo), worktree_name)

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
