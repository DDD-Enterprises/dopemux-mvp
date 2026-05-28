"""Tests for cross-artifact mixed-SHA hard fail in PR Steward classifier."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tools.pr_steward.classifier import build_artifacts

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures" / "pr_steward"


def _base_harvest(head_sha: str = "head000000000000000000000000000000000000") -> dict:
    return {
        "harvest_complete": True,
        "harvest_errors": [],
        "pr": {
            "number": 704,
            "url": "https://github.com/DDD-Enterprises/dopemux-mvp/pull/704",
            "state": "OPEN",
            "isDraft": False,
            "mergeable": "MERGEABLE",
            "mergeStateStatus": "CLEAN",
            "reviewDecision": "APPROVED",
            "baseRefName": "main",
            "baseRefOid": "base000000000000000000000000000000000000",
            "headRefName": "codex/test",
            "headRefOid": head_sha,
            "author": {"login": "hu3mann"},
            "createdAt": "2026-05-26T01:00:00Z",
            "updatedAt": "2026-05-26T02:00:00Z",
        },
        "changed_files": [{"path": "foo.py", "additions": 1}],
        "commits": [{"oid": head_sha, "messageHeadline": "test"}],
        "reviews": [],
        "review_comments": [],
        "review_threads": [],
        "issue_comments": [],
        "checks": [
            {
                "name": "unit",
                "status": "COMPLETED",
                "conclusion": "SUCCESS",
                "required": True,
                "headSha": head_sha,
            }
        ],
        "embedded_audit": {
            "status": "PASS",
            "report_path": "proof/TP-DMX-PR-STEWARD-001/AUDITOR_REPORT.md",
        },
        "proof": {
            "proof_path": "proof/TP-DMX-PR-STEWARD-001/PROOF.json",
            "proof_head_sha": head_sha,
            "matches_pr_head": True,
        },
    }


class TestMixedShaDetection:
    def test_all_checks_match_pr_head_no_blocker(self) -> None:
        artifacts = build_artifacts(
            _base_harvest(),
            repo="DDD-Enterprises/dopemux-mvp",
            pr_number=704,
            strict=True,
            allow_closed=False,
        )
        readiness = artifacts["MERGE_READINESS.json"]
        assert isinstance(readiness, dict)
        assert "MIXED_SHA_ARTIFACT_SET" not in readiness["blockers"]
        assert readiness["readiness"] == "READY"

    def test_one_check_with_stale_sha_hard_blocks(self) -> None:
        harvest = _base_harvest()
        harvest["checks"] = [
            {
                "name": "unit",
                "status": "COMPLETED",
                "conclusion": "SUCCESS",
                "required": True,
                "headSha": "stale00000000000000000000000000000000000",
            }
        ]
        artifacts = build_artifacts(
            harvest,
            repo="DDD-Enterprises/dopemux-mvp",
            pr_number=704,
            strict=True,
            allow_closed=False,
        )
        readiness = artifacts["MERGE_READINESS.json"]
        assert isinstance(readiness, dict)
        assert "MIXED_SHA_ARTIFACT_SET" in readiness["blockers"]
        assert readiness["readiness"] == "BLOCKED"
        assert readiness["mutation_performed"] is False

    def test_check_with_null_sha_not_treated_as_mismatch(self) -> None:
        harvest = _base_harvest()
        harvest["checks"] = [
            {
                "name": "unit",
                "status": "COMPLETED",
                "conclusion": "SUCCESS",
                "required": True,
                # headSha absent — treated as empty string, excluded from comparison
            }
        ]
        artifacts = build_artifacts(
            harvest,
            repo="DDD-Enterprises/dopemux-mvp",
            pr_number=704,
            strict=True,
            allow_closed=False,
        )
        readiness = artifacts["MERGE_READINESS.json"]
        assert "MIXED_SHA_ARTIFACT_SET" not in readiness["blockers"]

    def test_empty_checks_list_no_mixed_sha_blocker(self) -> None:
        harvest = _base_harvest()
        harvest["checks"] = []
        artifacts = build_artifacts(
            harvest,
            repo="DDD-Enterprises/dopemux-mvp",
            pr_number=704,
            strict=True,
            allow_closed=False,
        )
        readiness = artifacts["MERGE_READINESS.json"]
        assert "MIXED_SHA_ARTIFACT_SET" not in readiness["blockers"]

    def test_mixed_sha_overrides_all_ready_signals(self) -> None:
        """Proof FRESH, audit PASS, no other blockers — mixed SHA still hard-BLOCKs."""
        harvest = _base_harvest()
        harvest["checks"] = [
            {
                "name": "unit",
                "status": "COMPLETED",
                "conclusion": "SUCCESS",
                "required": True,
                "headSha": "differentsha000000000000000000000000000",
            }
        ]
        artifacts = build_artifacts(
            harvest,
            repo="DDD-Enterprises/dopemux-mvp",
            pr_number=704,
            strict=False,
            allow_closed=False,
        )
        readiness = artifacts["MERGE_READINESS.json"]
        assert readiness["readiness"] == "BLOCKED"
        assert "MIXED_SHA_ARTIFACT_SET" in readiness["blockers"]

    def test_explicit_null_headSha_not_treated_as_mismatch(self) -> None:
        harvest = _base_harvest()
        harvest["checks"] = [
            {
                "name": "unit",
                "status": "COMPLETED",
                "conclusion": "SUCCESS",
                "required": True,
                "headSha": None,
            }
        ]
        artifacts = build_artifacts(
            harvest,
            repo="DDD-Enterprises/dopemux-mvp",
            pr_number=704,
            strict=True,
            allow_closed=False,
        )
        readiness = artifacts["MERGE_READINESS.json"]
        assert "MIXED_SHA_ARTIFACT_SET" not in readiness["blockers"]

    def test_explicit_null_head_sha_rest_field_not_treated_as_mismatch(self) -> None:
        harvest = _base_harvest()
        harvest["checks"] = [
            {
                "name": "unit",
                "status": "COMPLETED",
                "conclusion": "SUCCESS",
                "required": True,
                "head_sha": None,
            }
        ]
        artifacts = build_artifacts(
            harvest,
            repo="DDD-Enterprises/dopemux-mvp",
            pr_number=704,
            strict=True,
            allow_closed=False,
        )
        readiness = artifacts["MERGE_READINESS.json"]
        assert "MIXED_SHA_ARTIFACT_SET" not in readiness["blockers"]

    def test_head_sha_rest_field_stale_blocks(self) -> None:
        """REST field head_sha (as opposed to GraphQL headSha) triggers mismatch detection."""
        harvest = _base_harvest()
        harvest["checks"] = [
            {
                "name": "unit",
                "status": "COMPLETED",
                "conclusion": "SUCCESS",
                "required": True,
                "head_sha": "stale00000000000000000000000000000000000",
            }
        ]
        artifacts = build_artifacts(
            harvest,
            repo="DDD-Enterprises/dopemux-mvp",
            pr_number=704,
            strict=True,
            allow_closed=False,
        )
        readiness = artifacts["MERGE_READINESS.json"]
        assert "MIXED_SHA_ARTIFACT_SET" in readiness["blockers"]
        assert readiness["readiness"] == "BLOCKED"

    def test_multiple_checks_one_stale_blocks(self) -> None:
        head_sha = "head000000000000000000000000000000000000"
        harvest = _base_harvest()
        harvest["checks"] = [
            {
                "name": "unit",
                "status": "COMPLETED",
                "conclusion": "SUCCESS",
                "required": True,
                "headSha": head_sha,
            },
            {
                "name": "lint",
                "status": "COMPLETED",
                "conclusion": "SUCCESS",
                "required": True,
                "headSha": "stale00000000000000000000000000000000000",
            },
        ]
        artifacts = build_artifacts(
            harvest,
            repo="DDD-Enterprises/dopemux-mvp",
            pr_number=704,
            strict=True,
            allow_closed=False,
        )
        readiness = artifacts["MERGE_READINESS.json"]
        assert "MIXED_SHA_ARTIFACT_SET" in readiness["blockers"]
        assert readiness["readiness"] == "BLOCKED"


def test_mixed_sha_fixture_produces_blocked_via_intake(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.pr_steward.intake",
            "--fixture-dir",
            str(FIXTURES / "mixed_sha_checks_block"),
            "--repo",
            "DDD-Enterprises/dopemux-mvp",
            "--pr",
            "704",
            "--out",
            str(tmp_path),
            "--strict",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 2, result.stderr
    readiness = json.loads((tmp_path / "MERGE_READINESS.json").read_text())
    assert readiness["readiness"] == "BLOCKED"
    assert "MIXED_SHA_ARTIFACT_SET" in readiness["blockers"]
    assert readiness["mutation_performed"] is False
