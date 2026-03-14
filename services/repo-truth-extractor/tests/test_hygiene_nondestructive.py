"""
T7: Non-destructive behavior tests.
Verifies that canonical source docs are never mutated by cleanup operations.
"""
import hashlib
from pathlib import Path

import pytest

from services.repo_truth_extractor import extraction_hygiene as hyg


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _populate_canonical_sources(root: Path) -> dict:
    """Create a set of canonical source files and return their sha256s."""
    files = {
        root / "compose.yml": "version: '3'\nservices:\n  app:\n    image: test\n",
        root / "README.md": "# Project\n",
        root / "src/dopemux/cli.py": "def main(): pass\n",
        root / ".claude/CLAUDE.md": "# Instructions\n",
        root / "config/settings.yaml": "key: value\n",
        root / "AGENTS.md": "# Agents\n",
    }
    checksums = {}
    for path, content in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        checksums[path] = _sha256(path)
    return checksums


class TestNonDestructiveBehavior:
    """No cleanup operation must ever touch canonical source files."""

    def test_scan_does_not_mutate_canonical_files(self, tmp_path):
        checksums_before = _populate_canonical_sources(tmp_path)

        hyg.run_scan(repo_root=tmp_path)

        for path, expected_sha in checksums_before.items():
            assert path.exists(), f"{path} was deleted by scan"
            assert _sha256(path) == expected_sha, f"{path} was modified by scan"

    def test_apply_dry_run_does_not_mutate_canonical_files(self, tmp_path):
        checksums_before = _populate_canonical_sources(tmp_path)

        hyg.run_apply(repo_root=tmp_path, dry_run=True)

        for path, expected_sha in checksums_before.items():
            assert path.exists(), f"{path} was deleted by apply dry-run"
            assert _sha256(path) == expected_sha, f"{path} was modified by apply dry-run"

    def test_apply_does_not_mutate_canonical_files(self, tmp_path):
        """Even in live apply mode, canonical sources are untouched."""
        checksums_before = _populate_canonical_sources(tmp_path)

        # Also add some junk to quarantine
        noise = tmp_path / "extraction/repo-truth-extractor/v3/runs/junk_run/.DS_Store"
        noise.parent.mkdir(parents=True)
        noise.write_bytes(b"\x00")

        hyg.run_apply(repo_root=tmp_path, dry_run=False)

        for path, expected_sha in checksums_before.items():
            assert path.exists(), f"{path} was deleted by apply"
            assert _sha256(path) == expected_sha, f"{path} was modified by apply"

    def test_apply_does_not_quarantine_canonical_files(self, tmp_path):
        """Canonical source files must not appear in the quarantine directory."""
        _populate_canonical_sources(tmp_path)

        hyg.run_apply(repo_root=tmp_path, dry_run=False)

        quarantine = tmp_path / "extraction/repo-truth-extractor/quarantine"
        if quarantine.exists():
            quarantined = list(quarantine.rglob("*"))
            canonical_names = {"compose.yml", "README.md", "cli.py", "CLAUDE.md",
                               "settings.yaml", "AGENTS.md"}
            for q in quarantined:
                assert q.name not in canonical_names, (
                    f"Canonical file {q.name!r} appeared in quarantine"
                )

    def test_apply_result_indicates_no_canonical_touched(self, tmp_path):
        """ApplyPlan must report canonical_sources_mutated=False."""
        _populate_canonical_sources(tmp_path)

        plan = hyg.run_apply(repo_root=tmp_path, dry_run=False)

        assert hasattr(plan, "canonical_sources_mutated")
        assert plan.canonical_sources_mutated is False
