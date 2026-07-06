"""Tests for the lite untracked-work probe (src/dopemux/untracked_work.py)."""

import subprocess
import tempfile
from pathlib import Path

import pytest

import src.dopemux.untracked_work as uw
from src.dopemux.untracked_work import (
    check_untracked_work,
    current_branch,
    format_advisory,
    probe_untracked_work,
)


@pytest.fixture
def git_repo():
    """Temporary git repository with one commit."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        subprocess.run(
            ["git", "init", "-b", "feature/test"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        (repo_path / "README.md").write_text("# Test Repo")
        subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        yield repo_path


def test_clean_repo_returns_none(git_repo):
    assert check_untracked_work(str(git_repo)) is None


def test_non_git_dir_returns_none():
    with tempfile.TemporaryDirectory() as tmpdir:
        assert check_untracked_work(tmpdir) is None


def test_dirty_repo_returns_summary(git_repo):
    (git_repo / "README.md").write_text("# Modified")
    (git_repo / "new.py").write_text("x = 1")

    changes = check_untracked_work(str(git_repo))

    assert changes is not None
    assert changes.unstaged_count == 1
    assert changes.untracked_count == 1


def test_current_branch(git_repo):
    assert current_branch(str(git_repo)) == "feature/test"


def test_format_advisory_mentions_branch_and_counts():
    from src.dopemux.uncommitted_detector import ChangesSummary

    changes = ChangesSummary(
        has_changes=True,
        staged_count=1,
        unstaged_count=2,
        untracked_count=3,
        stashed_count=0,
        total_files=6,
    )
    advisory = format_advisory(changes, "feature/test")

    assert "feature/test" in advisory
    assert "1 staged" in advisory
    assert "2 unstaged" in advisory
    assert "3 untracked" in advisory


def test_probe_emits_capture_event_and_returns_advisory(git_repo, monkeypatch):
    (git_repo / "new.py").write_text("x = 1")

    emitted = []
    monkeypatch.setattr(
        uw,
        "emit_untracked_detected",
        lambda path, changes, branch, **kw: emitted.append((path, changes, branch, kw)) or True,
    )

    advisory = probe_untracked_work(str(git_repo), source_probe="test_probe")

    assert advisory is not None
    assert "feature/test" in advisory
    assert len(emitted) == 1
    assert emitted[0][3]["source_probe"] == "test_probe"


def test_probe_silent_on_clean_repo(git_repo, monkeypatch):
    emitted = []
    monkeypatch.setattr(
        uw,
        "emit_untracked_detected",
        lambda *a, **kw: emitted.append(1) or True,
    )

    assert probe_untracked_work(str(git_repo), source_probe="test_probe") is None
    assert emitted == []


def test_emit_uses_promotable_event_type(git_repo, monkeypatch):
    """The probe's event type must be in the capture allowlist."""
    (git_repo / "new.py").write_text("x = 1")

    captured = {}

    def fake_emit(event_type, payload, **kwargs):
        captured["event_type"] = event_type
        captured["payload"] = payload
        return object()

    import src.dopemux.memory.capture_client as cc

    monkeypatch.setattr(cc, "try_emit_promotable_capture_event", fake_emit)
    # The module imports lazily inside the function, so patch the source.
    advisory = probe_untracked_work(str(git_repo), source_probe="test_probe")

    assert advisory is not None
    assert captured["event_type"] == "work.untracked_detected"
    assert captured["event_type"] in cc.PROMOTABLE_CAPTURE_EVENT_TYPES
    assert captured["payload"]["untracked_count"] == 1
