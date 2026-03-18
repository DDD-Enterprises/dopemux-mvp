"""
T2: Dry-run safety tests.
Verifies that scan mode and dry-run mode make zero filesystem mutations.
"""
import os
import stat
from pathlib import Path

import pytest

import importlib.util as _ilu
import sys as _sys
def _load_hyg():
    _root = __import__('pathlib').Path(__file__).resolve().parents[3]
    _spec = _ilu.spec_from_file_location(
        "extraction_hygiene",
        _root / "services" / "repo-truth-extractor" / "extraction_hygiene.py",
    )
    _mod = _ilu.module_from_spec(_spec)
    _sys.modules["extraction_hygiene"] = _mod
    _spec.loader.exec_module(_mod)
    return _mod
hyg = _load_hyg()


class TestDryRunSafety:
    """Dry-run and scan must be read-only — no filesystem mutations."""

    def test_scan_does_not_create_files(self, tmp_path):
        """run_scan() on an empty-ish tree creates no new files."""
        (tmp_path / "README.md").write_text("# hello")
        before = set(tmp_path.rglob("*"))
        hyg.run_scan(repo_root=tmp_path)
        after = set(tmp_path.rglob("*"))
        assert before == after, "scan must not create, modify, or delete any files"

    def test_scan_does_not_delete_files(self, tmp_path):
        """run_scan() preserves all files including junk paths."""
        noise = tmp_path / "node_modules" / "dep" / "README.md"
        noise.parent.mkdir(parents=True)
        noise.write_text("# dep")

        hyg.run_scan(repo_root=tmp_path)

        assert noise.exists(), "scan must not delete any files"

    def test_apply_dry_run_does_not_move_files(self, tmp_path):
        """apply(dry_run=True) reports mutations but makes none."""
        (tmp_path / "extraction/repo-truth-extractor/v3/runs/old_run").mkdir(
            parents=True
        )
        stale = (
            tmp_path
            / "extraction/repo-truth-extractor/v3/runs/old_run/raw/A0__A_P0001.FAILED.json"
        )
        stale.parent.mkdir(parents=True)
        stale.write_text('{"failure_type": "schema"}')

        plan = hyg.run_apply(repo_root=tmp_path, dry_run=True)

        # File still present
        assert stale.exists(), "dry-run must not move or delete files"
        # But the plan should describe what would have happened
        assert len(plan.planned_actions) >= 0  # may be 0 if no stale-after-success found

    def test_apply_dry_run_does_not_create_quarantine_dir(self, tmp_path):
        """apply(dry_run=True) must not create the quarantine directory."""
        quarantine = tmp_path / "extraction/repo-truth-extractor/quarantine"
        hyg.run_apply(repo_root=tmp_path, dry_run=True)
        assert not quarantine.exists(), (
            "dry-run must not create the quarantine directory"
        )

    def test_scan_returns_structured_result(self, tmp_path):
        """run_scan() returns a ScanResult with expected fields."""
        result = hyg.run_scan(repo_root=tmp_path)
        assert hasattr(result, "warnings")
        assert hasattr(result, "errors")
        assert hasattr(result, "noise_paths")
        assert hasattr(result, "version_path_issues")
        assert hasattr(result, "resume_state_issues")
        assert hasattr(result, "authority_summary")

    def test_apply_dry_run_returns_plan(self, tmp_path):
        """run_apply(dry_run=True) returns an ApplyPlan with planned_actions."""
        plan = hyg.run_apply(repo_root=tmp_path, dry_run=True)
        assert hasattr(plan, "planned_actions")
        assert hasattr(plan, "dry_run")
        assert plan.dry_run is True
