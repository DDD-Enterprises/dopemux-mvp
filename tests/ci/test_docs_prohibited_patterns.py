"""Regression tests for scripts/ci/docs_prohibited_patterns.sh.

Covers the docs-prohibited-patterns pre-commit hook regression where
`*temp*.md` substring-matched legitimate `template-*.md` filenames (the
filename "template" contains "temp"), first surfaced against
docs/pr_prep/adapters/vibe/template-agent.md (commit 139944337a renamed
agent-template.md -> template-agent.md specifically to escape this glob,
without a matching hook-pattern fix).
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "ci" / "docs_prohibited_patterns.sh"

ALLOWED_FILES = [
    "docs/pr_prep/adapters/vibe/template-agent.md",
    "docs/03-reference/governance/template-task.md",
    "docs/03-reference/governance/template-canonical-pr.md",
    "docs/03-reference/governance/task-packet-template.md",
    "docs/03-reference/governance/TEMPLATE-AGENT.md",
]

FORBIDDEN_FILES = [
    "docs/scratch/temp.md",
    "docs/scratch/temp-foo.md",
    "docs/scratch/my-temp-file.md",
    "docs/scratch/temporary.md",
    "docs/scratch/notes.md",
    "docs/scratch/notes-foo.md",
    "docs/scratch/todo.md",
    "docs/scratch/scratch.md",
    "docs/scratch/foo-scratch-bar.md",
    "task-packets/temp-draft.md",
    # A filename combining "template" with a genuinely prohibited token must
    # still be blocked -- the template exemption may not swallow the
    # notes/todo/scratch/temp prohibition wholesale.
    "docs/scratch/todo-template.md",
    "docs/scratch/notes-template.md",
    "docs/scratch/temp-template.md",
    "docs/scratch/scratch-template.md",
]


def _run(*files: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(SCRIPT), *files],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.parametrize("path", ALLOWED_FILES)
def test_allows_legitimate_template_filenames(path: str) -> None:
    result = _run(path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "❌" not in result.stdout


@pytest.mark.parametrize("path", FORBIDDEN_FILES)
def test_rejects_prohibited_filenames(path: str) -> None:
    result = _run(path)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "❌" in result.stdout


def test_mixed_batch_flags_only_the_forbidden_file() -> None:
    result = _run(
        "docs/pr_prep/adapters/vibe/template-agent.md",
        "docs/scratch/temp.md",
    )
    assert result.returncode == 1
    assert "template-agent.md" not in result.stdout.split("temp.md")[0]
    assert "docs/scratch/temp.md" in result.stdout


def test_quarantined_history_source_files_are_skipped() -> None:
    result = _run("docs/04-explanation/history/sourceFiles/temp-old-notes.md")
    assert result.returncode == 0
    assert "❌" not in result.stdout


def test_non_docs_paths_are_ignored() -> None:
    result = _run("src/dopemux/temp_module.md")
    assert result.returncode == 0
    assert "❌" not in result.stdout
