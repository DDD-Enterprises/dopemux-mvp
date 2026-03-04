"""
End-to-End Tests for Epic 2: Main Worktree Protection & Interactive Worktree Creation.

Tests complete user workflows that span multiple components:
- MainWorktreeDetector: Change detection and protection triggering
- WorktreeNameInferrer: Smart name suggestions from context
- ProtectionInterceptor: Interactive CLI flow with worktree creation
- Change Migration: Automated stash→create→pop flow

ADHD Context: E2E tests validate realistic user journeys, ensuring
the system supports interrupted workflows and context preservation.
"""

import pytest
from pathlib import Path
import tempfile
import subprocess
import uuid
from unittest.mock import patch

from src.dopemux.main_worktree_detector import MainWorktreeDetector
from src.dopemux.worktree_name_inferrer import WorktreeNameInferrer
from src.dopemux.protection_interceptor import (
    check_main_protection_interactive,
    _create_worktree_interactive,
    _execute_worktree_creation,
)


@pytest.fixture(scope="session", autouse=True)
def cleanup_temp_worktrees():
    """Clean up any leftover worktrees from previous test runs."""
    import shutil

    temp_base = Path(tempfile.gettempdir())

    # Common worktree names that tests might create
    common_names = [
        "initial-commit",
        "feature-x",
        "no-migration-test",
        "preserve-test",
        "all-changes-test",
    ]

    for name in common_names:
        potential_path = temp_base / name
        if potential_path.exists() and potential_path.is_dir():
            try:
                shutil.rmtree(potential_path)
            except Exception:
                pass

    yield

    # Cleanup after all tests
    for name in common_names:
        potential_path = temp_base / name
        if potential_path.exists() and potential_path.is_dir():
            try:
                shutil.rmtree(potential_path)
            except Exception:
                pass


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

        # Cleanup: Remove any created worktrees
        try:
            result = subprocess.run(
                ["git", "worktree", "list", "--porcelain"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )

            # Parse worktree paths and remove them
            worktree_paths = []
            for line in result.stdout.splitlines():
                if line.startswith("worktree "):
                    path = line.split(" ", 1)[1]
                    # Don't remove the main worktree (repo_path itself)
                    if Path(path) != repo_path:
                        worktree_paths.append(path)

            # Remove each worktree
            for wt_path in worktree_paths:
                subprocess.run(
                    ["git", "worktree", "remove", "-f", wt_path],
                    cwd=repo_path,
                    capture_output=True,
                    timeout=5
                )
        except Exception:
            pass  # Ignore cleanup errors


# ============================================================================
# E2E Scenario 1: Happy Path - Create Worktree with Migration
# ============================================================================

@patch('src.dopemux.protection_interceptor.console.input')
def test_e2e_happy_path_create_with_migration(mock_input, git_repo):
    """
    E2E: User on main with changes → chooses to create worktree → migrates changes.

    Flow:
    1. User has uncommitted changes on main
    2. Protection triggers
    3. User chooses option 1 (create worktree)
    4. User accepts first suggested name
    5. User chooses to migrate changes
    6. Worktree created with changes migrated
    7. Main is clean
    """
    worktree_name = f"e2e-migrate-{uuid.uuid4().hex[:8]}"

    # Setup: Create uncommitted changes on main
    (git_repo / "modified.txt").write_text("Modified content")
    (git_repo / "new_file.txt").write_text("New file")
    subprocess.run(["git", "add", "modified.txt"], cwd=git_repo, check=True, capture_output=True)

    # Mock user input: choose option 1, accept suggestion, migrate changes
    mock_input.side_effect = [
        "1",  # Create worktree
        worktree_name,  # Use a unique name to avoid stale worktree lock collisions
        "y"   # Migrate changes (default)
    ]

    # Execute: Check protection interactively
    result = check_main_protection_interactive(
        workspace_path=str(git_repo),
        enforce=False,
        offer_creation=True
    )

    # User chose to create worktree and exit
    assert result is True

    # Verify: Main worktree is now clean
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=git_repo,
        capture_output=True,
        text=True
    )
    assert status.stdout.strip() == ""

    # Verify: Worktree was created (check git worktree list)
    worktrees = subprocess.run(
        ["git", "worktree", "list"],
        cwd=git_repo,
        capture_output=True,
        text=True
    )
    assert len(worktrees.stdout.splitlines()) == 2  # main + new worktree


# ============================================================================
# E2E Scenario 2: User Declines Migration
# ============================================================================

@patch('src.dopemux.protection_interceptor.console.input')
def test_e2e_create_worktree_without_migration(mock_input, git_repo):
    """
    E2E: User creates worktree but declines change migration.

    Flow:
    1. User has changes on main
    2. Protection triggers
    3. User creates worktree
    4. User declines migration
    5. Worktree created empty
    6. Changes remain in main
    """
    worktree_name = f"e2e-nomigrate-{uuid.uuid4().hex[:8]}"

    # Setup
    (git_repo / "file.txt").write_text("Content")

    # Mock: create worktree, decline migration
    mock_input.side_effect = [
        "1",  # Create worktree
        worktree_name,  # Use a unique name to avoid stale worktree lock collisions
        "n"   # No migration
    ]

    result = check_main_protection_interactive(str(git_repo))

    # Worktree created, user should exit to restart
    assert result is True

    # Changes should still be in main (not migrated)
    assert (git_repo / "file.txt").exists()
    assert (git_repo / "file.txt").read_text() == "Content"


# ============================================================================
# E2E Scenario 3: User Stays in Main
# ============================================================================

@patch('src.dopemux.protection_interceptor.console.input')
def test_e2e_user_chooses_to_stay_in_main(mock_input, git_repo):
    """
    E2E: User chooses to continue working in main despite warning.

    Flow:
    1. User has changes on main
    2. Protection triggers
    3. User chooses option 2 (stay in main)
    4. No worktree created
    5. User continues in main
    """
    # Setup
    (git_repo / "file.txt").write_text("Content")

    # Mock: choose to stay in main
    mock_input.side_effect = ["2"]  # Stay in main

    result = check_main_protection_interactive(str(git_repo))

    # User chose to continue (not exit)
    assert result is False

    # Changes still present
    assert (git_repo / "file.txt").exists()

    # No new worktree created
    worktrees = subprocess.run(
        ["git", "worktree", "list"],
        cwd=git_repo,
        capture_output=True,
        text=True
    )
    assert len(worktrees.stdout.splitlines()) == 1  # Only main


# ============================================================================
# E2E Scenario 4: User Exits
# ============================================================================

@patch('src.dopemux.protection_interceptor.console.input')
def test_e2e_user_chooses_to_exit(mock_input, git_repo):
    """
    E2E: User chooses to exit and clean up manually.

    Flow:
    1. User has changes on main
    2. Protection triggers
    3. User chooses option 3 (exit)
    4. No changes made
    5. User exits cleanly
    """
    # Setup
    (git_repo / "file.txt").write_text("Content")

    # Mock: choose to exit
    mock_input.side_effect = ["3"]  # Exit

    result = check_main_protection_interactive(str(git_repo))

    # User chose to exit
    assert result is True

    # No worktree created
    worktrees = subprocess.run(
        ["git", "worktree", "list"],
        cwd=git_repo,
        capture_output=True,
        text=True
    )
    assert len(worktrees.stdout.splitlines()) == 1


# ============================================================================
# E2E Scenario 5: Custom Name with Conflict Resolution
# ============================================================================

@patch('src.dopemux.protection_interceptor.console.input')
def test_e2e_custom_name_with_conflict_resolution(mock_input, git_repo):
    """
    E2E: User enters custom name that conflicts, system resolves automatically.

    Flow:
    1. User has changes on main
    2. Create existing worktree/branch
    3. User tries to use same name
    4. System auto-resolves with suffix
    5. Worktree created successfully
    """
    base_name = f"feature-x-{uuid.uuid4().hex[:8]}"
    resolved_name = f"{base_name}-2"

    # Setup: Create existing branch
    subprocess.run(
        ["git", "branch", base_name],
        cwd=git_repo,
        check=True,
        capture_output=True
    )

    # Create changes
    (git_repo / "file.txt").write_text("Content")

    # Mock: create worktree, enter conflicting name, no migration
    mock_input.side_effect = [
        "1",          # Create worktree
        base_name,    # Custom name (conflicts!)
        "n"           # No migration
    ]

    result = check_main_protection_interactive(str(git_repo))

    # Should succeed with resolved name
    assert result is True

    # Verify worktree created with resolved name
    worktrees = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        cwd=git_repo,
        capture_output=True,
        text=True
    )

    # Should have resolved name in branches
    branches = subprocess.run(
        ["git", "branch"],
        cwd=git_repo,
        capture_output=True,
        text=True
    )
    assert resolved_name in branches.stdout


# ============================================================================
# E2E Scenario 6: All Change Types Migration
# ============================================================================

def test_e2e_migrate_all_change_types(git_repo):
    """
    E2E: Migrate staged + unstaged + untracked files together.

    Flow:
    1. User has all three change types
    2. All changes stashed together
    3. Worktree created
    4. All changes popped in new worktree
    5. All file states preserved
    """
    # Setup: Create all change types
    # Staged
    (git_repo / "staged.txt").write_text("Staged content")
    subprocess.run(["git", "add", "staged.txt"], cwd=git_repo, check=True, capture_output=True)

    # Unstaged
    (git_repo / "README.md").write_text("# Modified README")

    # Untracked
    (git_repo / "untracked.txt").write_text("Untracked file")

    # Execute migration
    worktree_name = f"all-changes-test-{uuid.uuid4().hex[:8]}"
    result = _execute_worktree_creation(
        str(git_repo),
        worktree_name,
        migrate_changes=True
    )

    assert result is True

    # Verify all changes migrated
    worktree_path = git_repo.parent / worktree_name
    assert (worktree_path / "staged.txt").exists()
    assert (worktree_path / "README.md").read_text() == "# Modified README"
    assert (worktree_path / "untracked.txt").exists()

    # Verify main is clean
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=git_repo,
        capture_output=True,
        text=True
    )
    assert status.stdout.strip() == ""


# ============================================================================
# E2E Scenario 7: Issue Number Extraction from Context
# ============================================================================

def test_e2e_issue_number_extraction_workflow(git_repo):
    """
    E2E: System extracts issue number from branch and suggests good name.

    Flow:
    1. User on branch with issue pattern (e.g., fix-issue-123)
    2. System detects issue number
    3. Suggested name includes issue reference
    4. High confidence score
    """
    # Setup: Create branch with issue pattern
    subprocess.run(
        ["git", "checkout", "-b", "fix-issue-456"],
        cwd=git_repo,
        check=True,
        capture_output=True
    )

    # Add changes to trigger protection on main
    (git_repo / "file.txt").write_text("Fix content")

    # Get name suggestions
    inferrer = WorktreeNameInferrer(str(git_repo))
    suggestions = inferrer.suggest_names(max_suggestions=3)

    # Should have issue number in suggestions
    assert len(suggestions) > 0

    # Best suggestion should include issue reference
    best = suggestions[0]
    assert "issue-456" in best.name or "fix-issue-456" in best.name
    assert best.confidence >= 0.8  # High confidence for issue extraction


# ============================================================================
# E2E Scenario 8: Name Suggestions from Multiple Sources
# ============================================================================

def test_e2e_multiple_context_sources_ranking(git_repo):
    """
    E2E: Multiple context sources available, system ranks them properly.

    Flow:
    1. Branch name has issue pattern
    2. Commit message has feature description
    3. Modified files suggest area
    4. All suggestions returned, ranked by confidence
    5. Issue pattern ranks highest
    """
    # Setup: Branch with issue pattern (highest confidence)
    subprocess.run(
        ["git", "checkout", "-b", "feat-issue-789"],
        cwd=git_repo,
        check=True,
        capture_output=True
    )

    # Commit with description
    (git_repo / "auth/login.py").parent.mkdir(exist_ok=True)
    (git_repo / "auth/login.py").write_text("def login(): pass")
    subprocess.run(["git", "add", "."], cwd=git_repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Add authentication system"],
        cwd=git_repo,
        check=True,
        capture_output=True
    )

    # Modified files (lower confidence)
    (git_repo / "auth/session.py").write_text("def session(): pass")

    # Get suggestions
    inferrer = WorktreeNameInferrer(str(git_repo))
    suggestions = inferrer.suggest_names(max_suggestions=3)

    # Should have multiple suggestions
    assert len(suggestions) >= 2

    # Sorted by confidence (descending)
    for i in range(len(suggestions) - 1):
        assert suggestions[i].confidence >= suggestions[i + 1].confidence

    # Issue pattern should be first (highest confidence)
    assert "issue-789" in suggestions[0].name or "feat-issue-789" in suggestions[0].name


# ============================================================================
# E2E Scenario 9: Enforcement Mode Blocks Operations
# ============================================================================

def test_e2e_enforcement_mode_blocks_operations(git_repo):
    """
    E2E: With enforcement enabled, operations blocked on main with changes.

    Flow:
    1. Enforcement enabled
    2. User on main with changes
    3. Protection triggers
    4. System blocks risky operations
    5. User must create worktree or clean up
    """
    # Setup
    (git_repo / "file.txt").write_text("Content")

    # Enforcement enabled
    detector = MainWorktreeDetector(str(git_repo), enforce_protection=True)

    # Should block risky operations
    assert detector.should_block_operation("commit") is True
    assert detector.should_block_operation("push") is True
    assert detector.should_block_operation("merge") is True

    # Safe operations not blocked
    assert detector.should_block_operation("status") is False
    assert detector.should_block_operation("diff") is False


# ============================================================================
# E2E Scenario 10: Clean Repo Has No Protection
# ============================================================================

def test_e2e_clean_repo_no_protection_workflow(git_repo):
    """
    E2E: Clean main branch triggers no protection.

    Flow:
    1. User on main with no changes
    2. No protection triggered
    3. Normal operations proceed
    """
    # Clean repo - no changes
    result = check_main_protection_interactive(
        workspace_path=str(git_repo),
        enforce=False
    )

    # No protection needed
    assert result is False

    # Detector confirms no trigger
    detector = MainWorktreeDetector(str(git_repo))
    trigger = detector.check_protection_needed()
    assert trigger is None


# ============================================================================
# E2E Scenario 11: Feature Branch Has No Protection
# ============================================================================

def test_e2e_feature_branch_no_protection(git_repo):
    """
    E2E: Feature branch with changes has no protection.

    Flow:
    1. User on feature branch
    2. User has uncommitted changes
    3. No protection triggered (not on main)
    4. Normal workflow continues
    """
    # Setup: Create and checkout feature branch
    subprocess.run(
        ["git", "checkout", "-b", "feature/test"],
        cwd=git_repo,
        check=True,
        capture_output=True
    )

    # Add changes
    (git_repo / "file.txt").write_text("Changes on feature branch")

    # No protection on feature branch
    result = check_main_protection_interactive(str(git_repo))
    assert result is False

    detector = MainWorktreeDetector(str(git_repo))
    trigger = detector.check_protection_needed()
    assert trigger is None


# ============================================================================
# E2E Scenario 12: Keyboard Interrupt Handling
# ============================================================================

@patch('src.dopemux.protection_interceptor.console.input')
def test_e2e_keyboard_interrupt_graceful_exit(mock_input, git_repo):
    """
    E2E: User presses Ctrl+C during prompts, system exits gracefully.

    Flow:
    1. User has changes on main
    2. Protection triggers
    3. User presses Ctrl+C
    4. System exits gracefully without errors
    5. No partial state created
    """
    # Setup
    (git_repo / "file.txt").write_text("Content")

    # Mock keyboard interrupt
    mock_input.side_effect = KeyboardInterrupt()

    result = check_main_protection_interactive(str(git_repo))

    # Should exit cleanly
    assert result is True

    # No worktree created
    worktrees = subprocess.run(
        ["git", "worktree", "list"],
        cwd=git_repo,
        capture_output=True,
        text=True
    )
    assert len(worktrees.stdout.splitlines()) == 1


# ============================================================================
# E2E Scenario 13: Stashed Changes Detection
# ============================================================================

def test_e2e_stashed_changes_trigger_protection(git_repo):
    """
    E2E: Stashed changes on main trigger protection.

    Flow:
    1. User stashes changes on main
    2. Protection still triggers (stash detected)
    3. User warned about stashed work
    """
    # Setup: Create and stash changes
    (git_repo / "file.txt").write_text("Content")
    subprocess.run(["git", "add", "."], cwd=git_repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "stash", "push", "-m", "Test stash"],
        cwd=git_repo,
        check=True,
        capture_output=True
    )

    # Protection should trigger for stashed changes
    detector = MainWorktreeDetector(str(git_repo))
    trigger = detector.check_protection_needed()

    assert trigger is not None
    assert trigger.changes.stashed_count == 1
    assert "stashed changes" in trigger.trigger_reason
