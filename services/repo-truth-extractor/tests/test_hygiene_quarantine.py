"""
T3: Apply-mode quarantine tests.
Verifies that apply mode archives/quarantines targeted junk and writes a manifest.
"""
import json
from pathlib import Path

import pytest

from services.repo_truth_extractor import extraction_hygiene as hyg


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
