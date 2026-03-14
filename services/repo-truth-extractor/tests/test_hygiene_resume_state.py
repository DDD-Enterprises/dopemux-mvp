"""
T6: Resume-state hygiene tests.
Verifies that stale/conflicting run-state artifacts are detected and reported.
"""
import json
import time
from pathlib import Path

import pytest

from services.repo_truth_extractor import extraction_hygiene as hyg


def _write_failed(raw_dir: Path, step: str, part: str) -> Path:
    raw_dir.mkdir(parents=True, exist_ok=True)
    p = raw_dir / f"{step}__{part}.FAILED.json"
    p.write_text(json.dumps({"failure_type": "schema", "step_id": step, "partition_id": part}))
    return p


def _write_success(raw_dir: Path, step: str, part: str, delay: float = 0.02) -> Path:
    raw_dir.mkdir(parents=True, exist_ok=True)
    p = raw_dir / f"{step}__{part}.json"
    time.sleep(delay)
    p.write_text(json.dumps({"surfaces": [], "step_id": step}))
    p.touch()
    return p


class TestResumeStateHygiene:
    """Resume state hazards must be detected before rerun."""

    def test_stale_failed_detected(self, tmp_path):
        """FAILED files older than success files are reported as stale."""
        run_dir = tmp_path / "extraction/repo-truth-extractor/v3/runs/old_run"
        raw = run_dir / "A_repo_control_plane" / "raw"
        failed = _write_failed(raw, "A0", "A_P0001")
        _write_success(raw, "A0", "A_P0001")

        issues = hyg.scan_resume_state(run_dirs=[run_dir])

        stale = [i for i in issues if i.issue_type == "stale_failed"]
        assert len(stale) >= 1
        assert str(failed) in str(stale[0].path)

    def test_orphan_failed_without_success_detected(self, tmp_path):
        """FAILED files with no corresponding success are reported as orphan_failed."""
        run_dir = tmp_path / "extraction/repo-truth-extractor/v3/runs/incomplete_run"
        raw = run_dir / "A_repo_control_plane" / "raw"
        _write_failed(raw, "A2", "A_P0003")  # no success file

        issues = hyg.scan_resume_state(run_dirs=[run_dir])

        orphans = [i for i in issues if i.issue_type == "orphan_failed"]
        assert len(orphans) >= 1

    def test_blocked_resume_proof_detected(self, tmp_path):
        """RESUME_PROOF.json with blocked_promptset=true is flagged."""
        run_dir = tmp_path / "extraction/repo-truth-extractor/v3/runs/blocked_run"
        run_dir.mkdir(parents=True)
        proof = run_dir / "RESUME_PROOF.json"
        proof.write_text(json.dumps({
            "resume_status": "ready",
            "blocked_promptset": True,
            "totals": {"recomputed_partitions": 0, "resume_skipped_partitions": 0},
        }))

        issues = hyg.scan_resume_state(run_dirs=[run_dir])

        blocked = [i for i in issues if i.issue_type == "blocked_promptset"]
        assert len(blocked) >= 1

    def test_clean_run_has_no_issues(self, tmp_path):
        """A run with all successes and no FAILED files has no resume issues."""
        run_dir = tmp_path / "extraction/repo-truth-extractor/v3/runs/clean_run"
        raw = run_dir / "A_repo_control_plane" / "raw"
        _write_success(raw, "A0", "A_P0001", delay=0)
        _write_success(raw, "A1", "A_P0001", delay=0)
        proof = run_dir / "RESUME_PROOF.json"
        proof.write_text(json.dumps({
            "resume_status": "ready",
            "blocked_promptset": False,
            "totals": {"recomputed_partitions": 2, "resume_skipped_partitions": 0},
        }))

        issues = hyg.scan_resume_state(run_dirs=[run_dir])

        assert len(issues) == 0, f"clean run should have no issues, got: {issues}"

    def test_resume_issues_appear_in_scan_result(self, tmp_path):
        """run_scan() includes resume_state_issues in its result."""
        run_dir = tmp_path / "extraction/repo-truth-extractor/v3/runs/bad_run"
        raw = run_dir / "A_repo_control_plane" / "raw"
        _write_failed(raw, "A0", "A_P0001")

        result = hyg.run_scan(
            repo_root=tmp_path,
            run_dirs=[run_dir],
        )

        assert isinstance(result.resume_state_issues, list)

    def test_resume_issue_has_required_fields(self, tmp_path):
        """ResumeIssue objects have the required fields for reporting."""
        run_dir = tmp_path / "extraction/repo-truth-extractor/v3/runs/bad_run"
        raw = run_dir / "A_repo_control_plane" / "raw"
        _write_failed(raw, "A0", "A_P0001")

        issues = hyg.scan_resume_state(run_dirs=[run_dir])

        assert issues
        issue = issues[0]
        assert hasattr(issue, "issue_type")
        assert hasattr(issue, "path")
        assert hasattr(issue, "severity")
        assert hasattr(issue, "message")
