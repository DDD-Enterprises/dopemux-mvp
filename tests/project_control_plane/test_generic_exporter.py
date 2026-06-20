"""
Tests for the generic PCP exporter (src/dopemux/pcp/exporter.py).

Exercises:
- A plain Git repo export validates against project_evidence_export.schema.json.
- generated_from_fixture is False; head_sha matches the real commit SHA.
- forbidden_action_confirmation flags are all False.
- active_packet.state is "ABSENT" (no named systems required).
- A dirty repo yields dirty_state.state == "DIRTY".
- A non-git directory raises ValueError.
"""

from __future__ import annotations

import json
import pathlib
import re
import shutil
import subprocess

import pytest
from jsonschema import Draft202012Validator

# ---------------------------------------------------------------------------
# Schema loading — CWD-independent, resolved relative to this file.
# Repository root: tests/project_control_plane/test_*.py → 3 levels up.
# ---------------------------------------------------------------------------
_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
_SCHEMA_PATH = _REPO_ROOT / "schemas" / "project_control_plane" / "project_evidence_export.schema.json"

with _SCHEMA_PATH.open() as _fh:
    _SCHEMA: dict = json.load(_fh)


def _schema_errors(instance: dict) -> list:
    return list(Draft202012Validator(_SCHEMA).iter_errors(instance))


# ---------------------------------------------------------------------------
# Skip guard — silently skip the whole module if git is unavailable.
# ---------------------------------------------------------------------------
_GIT_AVAILABLE = shutil.which("git") is not None
pytestmark = pytest.mark.skipif(
    not _GIT_AVAILABLE,
    reason="git executable not found; skipping generic exporter tests",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _git(args: list[str], cwd: str) -> str:
    """Run a git subcommand inside *cwd* and return stripped stdout."""
    return subprocess.check_output(
        ["git", "-C", cwd, *args],
        text=True,
        stderr=subprocess.DEVNULL,
    ).strip()


def _init_repo(path: pathlib.Path) -> str:
    """Initialise a minimal git repo with one commit; return the HEAD sha."""
    git = lambda *a: subprocess.check_call(  # noqa: E731
        ["git", "-C", str(path), *a],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    git("init")
    git("config", "user.email", "test@example.com")
    git("config", "user.name", "Test User")
    (path / "README.md").write_text("# test\n")
    git("add", "README.md")
    git("commit", "-m", "Initial commit")
    return _git(["rev-parse", "HEAD"], cwd=str(path))


# ---------------------------------------------------------------------------
# Import the module under test — after skip guard so pytest can collect the
# module even without git present.
# ---------------------------------------------------------------------------
from dopemux.pcp.exporter import export_evidence  # noqa: E402


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestExportEvidenceValidatesAgainstSchema:
    """The produced dict must have zero schema validation errors."""

    def test_clean_repo_validates(self, tmp_path: pathlib.Path) -> None:
        _init_repo(tmp_path)
        result = export_evidence(tmp_path)
        errs = _schema_errors(result)
        assert errs == [], f"Schema validation errors: {errs}"


class TestExportEvidenceRequiredFields:
    """Key field values must satisfy the contract."""

    def test_generated_from_fixture_is_false(self, tmp_path: pathlib.Path) -> None:
        _init_repo(tmp_path)
        result = export_evidence(tmp_path)
        assert result["generated_from_fixture"] is False

    def test_head_sha_matches_real_commit(self, tmp_path: pathlib.Path) -> None:
        expected_sha = _init_repo(tmp_path)
        result = export_evidence(tmp_path)
        assert result["repo_state"]["head_sha"] == expected_sha

    def test_head_sha_is_40_hex_chars(self, tmp_path: pathlib.Path) -> None:
        _init_repo(tmp_path)
        result = export_evidence(tmp_path)
        sha = result["repo_state"]["head_sha"]
        assert re.fullmatch(r"[0-9a-f]{40}", sha), f"head_sha not 40-hex: {sha!r}"

    def test_forbidden_action_confirmation_all_false(self, tmp_path: pathlib.Path) -> None:
        _init_repo(tmp_path)
        result = export_evidence(tmp_path)
        fac = result["forbidden_action_confirmation"]
        assert fac["external_runner_executed"] is False
        assert fac["external_workflow_written"] is False
        assert fac["github_mutated"] is False
        assert fac["runtime_written"] is False

    def test_active_packet_state_is_absent(self, tmp_path: pathlib.Path) -> None:
        """No named systems → active_packet must report ABSENT."""
        _init_repo(tmp_path)
        result = export_evidence(tmp_path)
        assert result["active_packet"]["state"] == "ABSENT"
        assert result["active_packet"]["packet_id"] is None
        assert result["active_packet"]["path"] is None

    def test_clean_repo_worktree_state_is_clean(self, tmp_path: pathlib.Path) -> None:
        _init_repo(tmp_path)
        result = export_evidence(tmp_path)
        assert result["repo_state"]["worktree_state"] == "CLEAN"
        assert result["dirty_state"]["state"] == "CLEAN"
        assert result["dirty_state"]["paths"] == []


class TestDirtyRepo:
    """An uncommitted change must surface as DIRTY."""

    def test_dirty_repo_yields_dirty_state(self, tmp_path: pathlib.Path) -> None:
        _init_repo(tmp_path)
        # Create an untracked / modified file after the commit.
        (tmp_path / "dirty.txt").write_text("uncommitted\n")
        result = export_evidence(tmp_path)
        assert result["dirty_state"]["state"] == "DIRTY"
        assert result["repo_state"]["worktree_state"] == "DIRTY"

    def test_dirty_repo_paths_list_nonempty(self, tmp_path: pathlib.Path) -> None:
        _init_repo(tmp_path)
        (tmp_path / "dirty2.txt").write_text("also uncommitted\n")
        result = export_evidence(tmp_path)
        assert len(result["dirty_state"]["paths"]) >= 1

    def test_dirty_repo_still_validates_against_schema(self, tmp_path: pathlib.Path) -> None:
        _init_repo(tmp_path)
        (tmp_path / "dirty3.txt").write_text("schema check\n")
        result = export_evidence(tmp_path)
        errs = _schema_errors(result)
        assert errs == [], f"Schema errors on dirty export: {errs}"


class TestNonGitDirectory:
    """A directory with no .git must raise ValueError."""

    def test_raises_value_error_for_non_git_dir(self, tmp_path: pathlib.Path) -> None:
        # tmp_path is a plain directory with no .git subdirectory.
        with pytest.raises(ValueError, match="Not a Git repository"):
            export_evidence(tmp_path)

    def test_raises_value_error_for_empty_non_git_dir(self, tmp_path: pathlib.Path) -> None:
        non_git = tmp_path / "plain_dir"
        non_git.mkdir()
        with pytest.raises(ValueError):
            export_evidence(non_git)
