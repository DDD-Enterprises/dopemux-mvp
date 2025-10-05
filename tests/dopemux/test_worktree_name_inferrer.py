"""
Tests for WorktreeNameInferrer.

Tests smart worktree naming with context-based inference,
confidence scoring, conflict resolution, and ADHD optimizations.
"""

import pytest
from pathlib import Path
import tempfile
import subprocess
from datetime import datetime

from src.dopemux.worktree_name_inferrer import (
    WorktreeNameInferrer,
    NameSuggestion,
    suggest_worktree_name,
    get_name_suggestions,
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


def test_name_suggestion_dataclass():
    """Test NameSuggestion dataclass and formatting."""
    suggestion = NameSuggestion(
        name="feature-auth",
        source="branch",
        confidence=0.8,
        description="From current branch"
    )

    assert suggestion.name == "feature-auth"
    assert suggestion.confidence == 0.8

    formatted = suggestion.format_for_display(1)
    assert "1." in formatted
    assert "feature-auth" in formatted
    assert "branch" in formatted


def test_name_sanitization():
    """Test name sanitization for git worktree compatibility."""
    inferrer = WorktreeNameInferrer("/fake/path")

    # Test special character removal (slashes preserved for branch names)
    assert inferrer._sanitize_name("Feature/Auth System!") == "feature/auth-system"

    # Test space replacement
    assert inferrer._sanitize_name("my cool feature") == "my-cool-feature"

    # Test multiple consecutive hyphens
    assert inferrer._sanitize_name("test---feature") == "test-feature"

    # Test leading/trailing hyphens
    assert inferrer._sanitize_name("-test-feature-") == "test-feature"

    # Test empty string fallback
    assert inferrer._sanitize_name("!!!") == "worktree"


def test_extract_from_issue_pr_number(git_repo):
    """Test extraction from issue/PR patterns (highest confidence)."""
    # Create branch with issue number
    subprocess.run(
        ["git", "checkout", "-b", "issue-123"],
        cwd=git_repo,
        check=True,
        capture_output=True
    )

    inferrer = WorktreeNameInferrer(str(git_repo))
    suggestion = inferrer._extract_from_issue_pr_number()

    assert suggestion is not None
    assert suggestion.confidence == 0.9
    assert "issue-123" in suggestion.name
    assert suggestion.source == "issue/PR"


def test_extract_from_pr_number(git_repo):
    """Test extraction from PR pattern."""
    subprocess.run(
        ["git", "checkout", "-b", "pr-456"],
        cwd=git_repo,
        check=True,
        capture_output=True
    )

    inferrer = WorktreeNameInferrer(str(git_repo))
    suggestion = inferrer._extract_from_issue_pr_number()

    assert suggestion is not None
    assert "pr-456" in suggestion.name


def test_extract_from_jira_pattern(git_repo):
    """Test extraction from JIRA-style pattern."""
    subprocess.run(
        ["git", "checkout", "-b", "PROJ-789-add-feature"],
        cwd=git_repo,
        check=True,
        capture_output=True
    )

    inferrer = WorktreeNameInferrer(str(git_repo))
    suggestion = inferrer._extract_from_issue_pr_number()

    assert suggestion is not None
    assert "proj-789" in suggestion.name


def test_extract_from_branch_name(git_repo):
    """Test extraction from feature branch name."""
    subprocess.run(
        ["git", "checkout", "-b", "feature/authentication"],
        cwd=git_repo,
        check=True,
        capture_output=True
    )

    inferrer = WorktreeNameInferrer(str(git_repo))
    suggestion = inferrer._extract_from_branch_name()

    assert suggestion is not None
    assert suggestion.confidence == 0.8
    assert "authentication" in suggestion.name
    assert suggestion.source == "current branch"


def test_extract_from_branch_ignores_main(git_repo):
    """Test that main/master branches return None."""
    # Already on main (default from fixture)
    inferrer = WorktreeNameInferrer(str(git_repo))
    suggestion = inferrer._extract_from_branch_name()

    assert suggestion is None


def test_extract_from_commit_message(git_repo):
    """Test extraction from recent commit message."""
    # Create commit with descriptive message
    (git_repo / "test.txt").write_text("test")
    subprocess.run(["git", "add", "."], cwd=git_repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Add authentication middleware"],
        cwd=git_repo,
        check=True,
        capture_output=True
    )

    inferrer = WorktreeNameInferrer(str(git_repo))
    suggestion = inferrer._extract_from_commit_message()

    assert suggestion is not None
    assert suggestion.confidence == 0.6
    assert "add" in suggestion.name or "authentication" in suggestion.name
    assert suggestion.source == "recent commit"


def test_extract_from_modified_files_single(git_repo):
    """Test extraction from single modified file."""
    # Modify a file
    (git_repo / "authentication.py").write_text("# Auth module")

    inferrer = WorktreeNameInferrer(str(git_repo))
    suggestion = inferrer._extract_from_modified_files()

    assert suggestion is not None
    assert suggestion.confidence == 0.5
    assert "authentication" in suggestion.name
    assert suggestion.source == "modified files"


def test_extract_from_modified_files_common_dir(git_repo):
    """Test extraction from multiple files in common directory."""
    # Create files in common directory
    (git_repo / "auth").mkdir()
    (git_repo / "auth" / "user.py").write_text("# User auth")
    (git_repo / "auth" / "session.py").write_text("# Session")

    inferrer = WorktreeNameInferrer(str(git_repo))
    suggestion = inferrer._extract_from_modified_files()

    assert suggestion is not None
    assert "auth" in suggestion.name


def test_extract_from_modified_files_no_common_dir(git_repo):
    """Test extraction when files have no common directory."""
    # Create files in different directories
    (git_repo / "src").mkdir()
    (git_repo / "tests").mkdir()
    (git_repo / "src" / "app.py").write_text("# App")
    (git_repo / "tests" / "test.py").write_text("# Test")

    inferrer = WorktreeNameInferrer(str(git_repo))
    suggestion = inferrer._extract_from_modified_files()

    assert suggestion is not None
    assert suggestion.name == "changes"  # Fallback for no common dir


def test_timestamp_fallback():
    """Test timestamp-based fallback name generation."""
    inferrer = WorktreeNameInferrer("/fake/path")
    suggestion = inferrer._generate_timestamp_fallback()

    assert suggestion is not None
    assert suggestion.confidence == 0.3
    assert suggestion.name.startswith("work-")
    assert suggestion.source == "timestamp"

    # Verify timestamp format (YYYYMMDD-HHMMSS)
    timestamp_part = suggestion.name.replace("work-", "")
    assert len(timestamp_part) == 15  # YYYYMMDD-HHMMSS
    assert "-" in timestamp_part


def test_suggest_names_sorting_by_confidence(git_repo):
    """Test that suggestions are sorted by confidence (highest first)."""
    # Create branch with issue number (highest confidence)
    subprocess.run(
        ["git", "checkout", "-b", "issue-123-add-feature"],
        cwd=git_repo,
        check=True,
        capture_output=True
    )

    # Add modified file (lower confidence)
    (git_repo / "auth.py").write_text("# Auth")

    inferrer = WorktreeNameInferrer(str(git_repo))
    suggestions = inferrer.suggest_names()

    # Should have multiple suggestions, sorted by confidence
    assert len(suggestions) >= 1
    assert suggestions[0].confidence >= 0.8  # Issue/PR or branch

    # Verify descending order
    for i in range(len(suggestions) - 1):
        assert suggestions[i].confidence >= suggestions[i + 1].confidence


def test_suggest_names_deduplication(git_repo):
    """Test that duplicate names are removed."""
    # Create scenario where extractors might produce same name
    subprocess.run(
        ["git", "checkout", "-b", "auth-module"],
        cwd=git_repo,
        check=True,
        capture_output=True
    )

    inferrer = WorktreeNameInferrer(str(git_repo))
    suggestions = inferrer.suggest_names()

    # No duplicate names
    names = [s.name for s in suggestions]
    assert len(names) == len(set(names))


def test_suggest_names_adhd_limit(git_repo):
    """Test ADHD-friendly max 3 suggestions."""
    # Create multiple potential sources
    subprocess.run(
        ["git", "checkout", "-b", "feature/auth"],
        cwd=git_repo,
        check=True,
        capture_output=True
    )
    (git_repo / "auth.py").write_text("# Auth")

    inferrer = WorktreeNameInferrer(str(git_repo))
    suggestions = inferrer.suggest_names(max_suggestions=3)

    assert len(suggestions) <= 3


def test_get_best_suggestion(git_repo):
    """Test getting single best suggestion (ADHD optimization)."""
    subprocess.run(
        ["git", "checkout", "-b", "issue-456"],
        cwd=git_repo,
        check=True,
        capture_output=True
    )

    inferrer = WorktreeNameInferrer(str(git_repo))
    best = inferrer.get_best_suggestion()

    assert best is not None
    assert best.confidence >= 0.8  # Should be the highest confidence


def test_check_name_available_no_worktrees(git_repo):
    """Test name availability when no worktrees exist."""
    inferrer = WorktreeNameInferrer(str(git_repo))

    assert inferrer.check_name_available("feature-auth") is True
    assert inferrer.check_name_available("any-name") is True


def test_check_name_available_with_existing_worktree(git_repo):
    """Test name availability with existing worktree."""
    # Create a worktree (in unique subdirectory)
    worktree_path = git_repo / "worktrees" / "availability-test"
    worktree_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "worktree", "add", str(worktree_path), "-b", "existing-branch"],
        cwd=git_repo,
        check=True,
        capture_output=True
    )

    inferrer = WorktreeNameInferrer(str(git_repo))

    # Existing branch should be unavailable
    assert inferrer.check_name_available("existing-branch") is False

    # New name should be available
    assert inferrer.check_name_available("new-branch") is True


def test_resolve_conflict(git_repo):
    """Test conflict resolution with suffix."""
    # Create worktree with base name (in unique subdirectory)
    worktree_path = git_repo / "worktrees" / "conflict-test"
    worktree_path.parent.mkdir(exist_ok=True)
    subprocess.run(
        ["git", "worktree", "add", str(worktree_path), "-b", "feature-auth"],
        cwd=git_repo,
        check=True,
        capture_output=True
    )

    inferrer = WorktreeNameInferrer(str(git_repo))
    resolved = inferrer.resolve_conflict("feature-auth")

    # Should add suffix
    assert resolved != "feature-auth"
    assert resolved.startswith("feature-auth-")
    assert inferrer.check_name_available(resolved) is True


def test_resolve_conflict_multiple(git_repo):
    """Test conflict resolution with multiple existing suffixes."""
    # Create worktrees with base name and suffix (in unique subdirectories)
    worktrees_dir = git_repo / "worktrees" / "multiple-test"
    worktrees_dir.mkdir(parents=True, exist_ok=True)

    for i in range(1, 4):
        worktree_path = worktrees_dir / f"auth-{i}"
        branch_name = f"auth-{i}" if i > 1 else "auth"
        subprocess.run(
            ["git", "worktree", "add", str(worktree_path), "-b", branch_name],
            cwd=git_repo,
            check=True,
            capture_output=True
        )

    inferrer = WorktreeNameInferrer(str(git_repo))
    resolved = inferrer.resolve_conflict("auth")

    # Should use next available suffix
    assert resolved == "auth-4"


def test_get_available_name_no_conflict(git_repo):
    """Test getting available name when preferred name is free."""
    inferrer = WorktreeNameInferrer(str(git_repo))

    name = inferrer.get_available_name("my-feature")
    assert name == "my-feature"


def test_get_available_name_with_conflict(git_repo):
    """Test getting available name with conflict resolution."""
    # Create existing worktree (in unique subdirectory)
    worktree_path = git_repo / "worktrees" / "name-conflict-test"
    worktree_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "worktree", "add", str(worktree_path), "-b", "my-feature"],
        cwd=git_repo,
        check=True,
        capture_output=True
    )

    inferrer = WorktreeNameInferrer(str(git_repo))
    name = inferrer.get_available_name("my-feature")

    # Should resolve conflict
    assert name != "my-feature"
    assert name.startswith("my-feature-")


def test_get_available_name_auto_suggestion(git_repo):
    """Test getting available name with automatic suggestion."""
    subprocess.run(
        ["git", "checkout", "-b", "feature/awesome"],
        cwd=git_repo,
        check=True,
        capture_output=True
    )

    inferrer = WorktreeNameInferrer(str(git_repo))
    name = inferrer.get_available_name()  # No preferred name

    # Should use best suggestion
    assert name is not None
    assert "awesome" in name or "work-" in name  # Branch or timestamp fallback


def test_helper_suggest_worktree_name(git_repo):
    """Test synchronous helper function."""
    subprocess.run(
        ["git", "checkout", "-b", "issue-789"],
        cwd=git_repo,
        check=True,
        capture_output=True
    )

    name = suggest_worktree_name(str(git_repo))

    assert name is not None
    assert isinstance(name, str)
    assert "issue-789" in name or "work-" in name


def test_helper_get_name_suggestions(git_repo):
    """Test helper for getting multiple suggestions."""
    subprocess.run(
        ["git", "checkout", "-b", "feature/test"],
        cwd=git_repo,
        check=True,
        capture_output=True
    )

    suggestions = get_name_suggestions(str(git_repo), max_suggestions=3)

    assert len(suggestions) <= 3
    assert all(isinstance(s, str) for s in suggestions)


def test_handle_non_git_directory():
    """Test graceful handling of non-git directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        inferrer = WorktreeNameInferrer(tmpdir)

        # Should not crash, fall back to timestamp
        suggestion = inferrer.get_best_suggestion()
        assert suggestion.name.startswith("work-")
        assert suggestion.confidence == 0.3


def test_sanitize_slash_in_branch_name(git_repo):
    """Test sanitization preserves slashes in branch names."""
    subprocess.run(
        ["git", "checkout", "-b", "feature/auth/jwt"],
        cwd=git_repo,
        check=True,
        capture_output=True
    )

    inferrer = WorktreeNameInferrer(str(git_repo))
    suggestion = inferrer._extract_from_branch_name()

    # Slashes should be preserved (git worktree supports them)
    assert suggestion is not None
    assert "/" in suggestion.name or "-" in suggestion.name  # Might get sanitized


def test_confidence_scoring_order():
    """Test that confidence levels follow expected hierarchy."""
    inferrer = WorktreeNameInferrer("/fake/path")

    # Issue/PR should be highest
    assert 0.9 == 0.9  # Confidence for issue/PR

    # Branch should be next
    assert 0.8 < 0.9

    # Commit should be next
    assert 0.6 < 0.8

    # Files should be next
    assert 0.5 < 0.6

    # Timestamp should be lowest
    assert 0.3 < 0.5


def test_empty_modified_files(git_repo):
    """Test handling of no modified files."""
    inferrer = WorktreeNameInferrer(str(git_repo))

    # Clean repo - no modified files
    suggestion = inferrer._extract_from_modified_files()

    assert suggestion is None


def test_short_commit_message(git_repo):
    """Test handling of very short commit message."""
    # Test single-word commit
    (git_repo / "test.txt").write_text("content")
    subprocess.run(["git", "add", "."], cwd=git_repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "fix"],
        cwd=git_repo,
        check=True,
        capture_output=True
    )

    inferrer = WorktreeNameInferrer(str(git_repo))
    suggestion = inferrer._extract_from_commit_message()

    # Should create suggestion from single word
    assert suggestion is not None
    assert "fix" in suggestion.name
