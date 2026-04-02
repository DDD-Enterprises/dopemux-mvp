"""
T3: Apply-mode quarantine tests.
Verifies that apply mode archives/quarantines targeted junk and writes a manifest.
"""
import json
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


class TestApplyModeQuarantine:
    """Apply mode must move (not delete) artifacts and write a manifest."""

    def _make_stale_failed(self, run_dir: Path, step: str = "A0", part: str = "A_P0001") -> Path:
        raw = run_dir / "A_repo_control_plane" / "raw"
        raw.mkdir(parents=True, exist_ok=True)
        failed = raw / f"{step}__{part}.FAILED.json"
        failed.write_text('{"failure_type": "schema"}')
        return failed

    def _make_success(self, run_dir: Path, step: str = "A0", part: str = "A_P0001") -> Path:
        raw = run_dir / "A_repo_control_plane" / "raw"
        raw.mkdir(parents=True, exist_ok=True)
        success = raw / f"{step}__{part}.json"
        success.write_text('{"surfaces": []}')
        # Make success newer than failed (ensure mtime ordering)
        import time; time.sleep(0.01)
        success.touch()
        return success

    def test_stale_failed_is_quarantined(self, tmp_path):
        """Stale FAILED markers (older than success) are moved to quarantine."""
        runs = tmp_path / "extraction/repo-truth-extractor/v3/runs/old_run"
        failed = self._make_stale_failed(runs)
        self._make_success(runs)  # success is newer → failed is stale

        plan = hyg.run_apply(repo_root=tmp_path, dry_run=False)

        quarantine = tmp_path / "extraction/repo-truth-extractor/quarantine"
        assert not failed.exists(), "stale FAILED file must be moved out of original location"
        # Should be somewhere under quarantine
        moved_files = list(quarantine.rglob("*.FAILED.json")) if quarantine.exists() else []
        assert len(moved_files) >= 1, "stale FAILED file must appear in quarantine"

    def test_manifest_is_written(self, tmp_path):
        """Apply mode writes ARCHIVE_MANIFEST.json in the quarantine directory."""
        runs = tmp_path / "extraction/repo-truth-extractor/v3/runs/old_run"
        self._make_stale_failed(runs)
        self._make_success(runs)

        plan = hyg.run_apply(repo_root=tmp_path, dry_run=False)

        quarantine = tmp_path / "extraction/repo-truth-extractor/quarantine"
        manifests = list(quarantine.rglob("ARCHIVE_MANIFEST.json")) if quarantine.exists() else []
        assert len(manifests) >= 1, "ARCHIVE_MANIFEST.json must be written by apply mode"

    def test_manifest_content_is_valid_json(self, tmp_path):
        """ARCHIVE_MANIFEST.json must be valid JSON with required fields."""
        runs = tmp_path / "extraction/repo-truth-extractor/v3/runs/old_run"
        self._make_stale_failed(runs)
        self._make_success(runs)

        hyg.run_apply(repo_root=tmp_path, dry_run=False)

        quarantine = tmp_path / "extraction/repo-truth-extractor/quarantine"
        manifests = list(quarantine.rglob("ARCHIVE_MANIFEST.json")) if quarantine.exists() else []
        assert manifests, "manifest must exist"
        data = json.loads(manifests[0].read_text())
        assert "timestamp" in data
        assert "moved_items" in data
        assert isinstance(data["moved_items"], list)

    def test_ds_store_in_extraction_tree_is_quarantined(self, tmp_path):
        """DS_Store files in the extraction tree are quarantined."""
        runs = tmp_path / "extraction/repo-truth-extractor/v3/runs/old_run"
        runs.mkdir(parents=True)
        ds = runs / ".DS_Store"
        ds.write_bytes(b"\x00\x01")

        hyg.run_apply(repo_root=tmp_path, dry_run=False)

        assert not ds.exists(), ".DS_Store must be moved to quarantine"

    def test_apply_returns_plan_with_actions(self, tmp_path):
        """run_apply returns an ApplyPlan listing what was done."""
        runs = tmp_path / "extraction/repo-truth-extractor/v3/runs/old_run"
        self._make_stale_failed(runs)
        self._make_success(runs)

        plan = hyg.run_apply(repo_root=tmp_path, dry_run=False)

        assert hasattr(plan, "applied_actions")
        assert len(plan.applied_actions) >= 1

    def test_apply_mode_is_reversible(self, tmp_path):
        """Content of quarantined files is preserved (not corrupted or truncated)."""
        runs = tmp_path / "extraction/repo-truth-extractor/v3/runs/old_run"
        failed = self._make_stale_failed(runs)
        original_content = failed.read_text()
        self._make_success(runs)

        hyg.run_apply(repo_root=tmp_path, dry_run=False)

        quarantine = tmp_path / "extraction/repo-truth-extractor/quarantine"
        moved = list(quarantine.rglob("*.FAILED.json")) if quarantine.exists() else []
        assert moved, "file must be in quarantine"
        assert moved[0].read_text() == original_content, "quarantined file must retain original content"

    def test_blocked_promptset_run_is_not_quarantined(self, tmp_path):
        """Apply mode must preserve stale sidecars in runs marked blocked_promptset=true."""
        runs = tmp_path / "extraction/repo-truth-extractor/v3/runs/blocked_run"
        failed = self._make_stale_failed(runs)
        self._make_success(runs)
        (runs / "RESUME_PROOF.json").write_text(json.dumps({
            "resume_status": "blocked",
            "blocked_promptset": True,
        }))

        plan = hyg.run_apply(repo_root=tmp_path, dry_run=False)

        assert failed.exists(), "blocked promptset run should be preserved for review"
        assert not plan.applied_actions, "blocked promptset run should not produce quarantine actions"
        assert plan.summary["skipped_blocked_promptset"] == 1

    def test_top_level_runs_zip_is_not_quarantined(self, tmp_path):
        """Top-level runs/*.zip is not inside a run directory and must not be auto-quarantined."""
        runs_root = tmp_path / "extraction/repo-truth-extractor/v3/runs"
        runs_root.mkdir(parents=True, exist_ok=True)
        archive = runs_root / "fullrepo_20260304T024932Z.zip"
        archive.write_bytes(b"zip-bytes")

        plan = hyg.run_apply(repo_root=tmp_path, dry_run=False)

        assert archive.exists(), "top-level runs zip should not be auto-quarantined"
        assert all(action.source != archive for action in plan.applied_actions)
        assert plan.summary["skipped_top_level_zip"] == 1

    def test_ambiguous_top_level_failed_marker_is_counted(self, tmp_path):
        """FAILED markers not nested in a run directory are counted as ambiguous and skipped."""
        runs_root = tmp_path / "extraction/repo-truth-extractor/v3/runs"
        runs_root.mkdir(parents=True, exist_ok=True)
        failed = runs_root / "A0__A_P0001.FAILED.json"
        failed.write_text('{"failure_type": "schema"}')
        success = runs_root / "A0__A_P0001.json"
        success.write_text('{"surfaces": []}')

        plan = hyg.run_apply(repo_root=tmp_path, dry_run=False)

        assert failed.exists(), "ambiguous top-level FAILED marker should be preserved"
        assert plan.summary["skipped_ambiguous"] == 1

    def test_bucket_limit_selects_only_stale_resume_state_actions(self, tmp_path):
        """Bucket filtering and limit must bound apply without cross-bucket leakage."""
        run_one = tmp_path / "extraction/repo-truth-extractor/v3/runs/old_run_1"
        run_two = tmp_path / "extraction/repo-truth-extractor/v3/runs/old_run_2"
        self._make_stale_failed(run_one, part="A_P0001")
        self._make_success(run_one, part="A_P0001")
        self._make_stale_failed(run_two, part="A_P0002")
        self._make_success(run_two, part="A_P0002")
        ds = tmp_path / "extraction/repo-truth-extractor/v3/runs/old_run_2/.DS_Store"
        ds.write_bytes(b"\x00\x01")

        plan = hyg.run_apply(
            repo_root=tmp_path,
            dry_run=True,
            bucket="stale_resume_state",
            limit=1,
        )

        assert plan.bucket == "stale_resume_state"
        assert plan.limit == 1
        assert plan.summary["eligible_actions"] == 2
        assert len(plan.planned_actions) == 1
        assert all(action.bucket == "stale_resume_state" for action in plan.planned_actions)
