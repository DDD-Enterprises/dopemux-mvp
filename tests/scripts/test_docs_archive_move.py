"""Tests for scripts/docs_archive_move.py using a throwaway git repo."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import List

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "docs_archive_move.py"
MANIFEST = "docs/archive/MANIFEST.jsonl"
KEYS = [
    "original_path",
    "archive_path",
    "sha256",
    "source_commit",
    "wave",
    "reason",
    "disposition_candidate",
    "recorded_at",
]


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


def commit_files(repo: Path, files: dict) -> None:
    for rel, text in files.items():
        target = repo / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "fixture")


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.name", "Test")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "commit.gpgsign", "false")
    commit_files(
        tmp_path,
        {
            "docs/a.md": "alpha\n",
            "docs/sub/b.md": "beta\n",
            "docs/sub/c.md": "gamma\n",
        },
    )
    return tmp_path


def run(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--repo-root", str(repo), *args],
        capture_output=True,
        text=True,
    )


def rows(repo: Path) -> List[dict]:
    text = (repo / MANIFEST).read_text()
    return [json.loads(line) for line in text.splitlines()]


def test_move_file_preserves_original_path(repo: Path) -> None:
    result = run(repo, "--wave", "w1", "--reason", "stale", "docs/a.md")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().splitlines()[-1] == "moved=1 recorded=1"
    assert not (repo / "docs/a.md").exists()
    assert (repo / "docs/archive/w1/docs/a.md").read_text() == "alpha\n"
    assert "docs/archive/w1/docs/a.md" in git(repo, "ls-files")


def test_move_directory_and_manifest_rows(repo: Path) -> None:
    head = git(repo, "rev-parse", "HEAD")
    result = run(
        repo,
        "--wave",
        "w1",
        "--reason",
        "old",
        "--disposition",
        "export-later",
        "docs/sub",
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().splitlines()[-1] == "moved=2 recorded=2"
    out = rows(repo)
    assert [list(r) for r in out] == [KEYS, KEYS]
    assert [r["original_path"] for r in out] == ["docs/sub/b.md", "docs/sub/c.md"]
    first = out[0]
    assert first["archive_path"] == "docs/archive/w1/docs/sub/b.md"
    assert first["sha256"] == hashlib.sha256(b"beta\n").hexdigest()
    assert first["source_commit"] == head
    assert (first["wave"], first["reason"]) == ("w1", "old")
    assert first["disposition_candidate"] == "export-later"
    assert first["recorded_at"].endswith("+00:00")
    assert (repo / "docs/archive/w1/docs/sub/c.md").exists()


def test_refuse_when_destination_exists(repo: Path) -> None:
    commit_files(repo, {"docs/archive/w1/docs/a.md": "other\n"})
    result = run(repo, "--wave", "w1", "--reason", "x", "docs/a.md", "docs/sub/b.md")
    assert result.returncode == 1
    assert (repo / "docs/a.md").exists() and (repo / "docs/sub/b.md").exists()
    assert not (repo / MANIFEST).exists()


def test_refuse_source_already_archived(repo: Path) -> None:
    commit_files(repo, {"docs/archive/old/x.md": "x\n"})
    result = run(repo, "--wave", "w2", "--reason", "x", "docs/archive/old/x.md")
    assert result.returncode == 1
    assert (repo / "docs/archive/old/x.md").exists()
    assert not (repo / MANIFEST).exists()


def test_refuse_untracked_input_without_partial_moves(repo: Path) -> None:
    (repo / "docs/new.md").write_text("new\n")
    result = run(repo, "--wave", "w1", "--reason", "x", "docs/a.md", "docs/new.md")
    assert result.returncode == 1
    assert (repo / "docs/a.md").exists() and (repo / "docs/new.md").exists()
    assert not (repo / MANIFEST).exists()


def test_refuse_destination_outside_repo(repo: Path) -> None:
    result = run(repo, "--wave", "../../evil", "--reason", "x", "docs/a.md")
    assert result.returncode == 1
    assert (repo / "docs/a.md").exists()


def test_usage_error_exit_code(repo: Path) -> None:
    assert run(repo, "--reason", "x", "docs/a.md").returncode == 2
    assert run(repo, "--wave", "w1", "--reason", "x").returncode == 2


def test_dry_run_writes_nothing(repo: Path) -> None:
    result = run(repo, "--dry-run", "--wave", "w1", "--reason", "x", "docs/sub")
    assert result.returncode == 0, result.stderr
    assert "docs/archive/w1/docs/sub/b.md" in result.stdout
    assert (repo / "docs/sub/b.md").exists()
    assert not (repo / "docs/archive").exists()
    assert git(repo, "status", "--porcelain") == ""


def test_seed_marks_duplicates_and_is_idempotent(repo: Path) -> None:
    commit_files(
        repo,
        {
            "docs/archive/w0/z.md": "same\n",
            "docs/archive/w0/a.md": "same\n",
            "docs/archive/w0/u.md": "unique\n",
        },
    )
    args = ("--seed", "--wave", "w0", "--reason", "baseline")
    result = run(repo, *args)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().splitlines()[-1] == "moved=0 recorded=3"
    by_path = {r["archive_path"]: r for r in rows(repo)}
    assert set(by_path) == {
        "docs/archive/w0/a.md",
        "docs/archive/w0/u.md",
        "docs/archive/w0/z.md",
    }
    assert by_path["docs/archive/w0/a.md"]["disposition_candidate"] == "keep"
    z = by_path["docs/archive/w0/z.md"]
    assert z["disposition_candidate"] == "delete-later"
    assert z["reason"] == "exact-duplicate-of:docs/archive/w0/a.md"
    assert by_path["docs/archive/w0/u.md"]["reason"] == "baseline"
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "manifest")
    again = run(repo, *args)
    assert again.returncode == 0, again.stderr
    assert again.stdout.strip().splitlines()[-1] == "moved=0 recorded=0"
    assert len(rows(repo)) == 3
