"""Tests for proof freshness substates in PR Steward classifier."""
from __future__ import annotations

from pathlib import Path

from tools.pr_steward.classifier import _proof, build_artifacts

ROOT = Path(__file__).resolve().parents[2]


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


class TestProofFreshnessSubstates:
    def test_sha_set_and_matching_is_fresh(self) -> None:
        result = _proof({"proof": {
            "proof_path": "proof/PROOF.json",
            "proof_head_sha": "abc123",
            "matches_pr_head": True,
        }})
        assert result["proof_freshness"] == "FRESH"

    def test_sha_set_but_not_matching_is_stale(self) -> None:
        result = _proof({"proof": {
            "proof_path": "proof/PROOF.json",
            "proof_head_sha": "abc123",
            "matches_pr_head": False,
        }})
        assert result["proof_freshness"] == "STALE"

    def test_no_sha_and_no_path_is_missing(self) -> None:
        result = _proof({"proof": {}})
        assert result["proof_freshness"] == "MISSING"

    def test_proof_key_absent_from_harvest_is_missing(self) -> None:
        result = _proof({})
        assert result["proof_freshness"] == "MISSING"

    def test_path_set_but_no_sha_is_stale(self) -> None:
        result = _proof({"proof": {
            "proof_path": "proof/PROOF.json",
            "proof_head_sha": None,
            "matches_pr_head": False,
        }})
        assert result["proof_freshness"] == "STALE"

    def test_proof_freshness_field_present_in_returned_dict(self) -> None:
        result = _proof({"proof": {
            "proof_path": "proof/PROOF.json",
            "proof_head_sha": "abc",
            "matches_pr_head": True,
        }})
        assert "proof_freshness" in result
        assert result["proof_freshness"] in ("FRESH", "STALE", "MISSING")


class TestProofFreshnessInArtifacts:
    def test_fresh_proof_no_stale_blocker(self) -> None:
        artifacts = build_artifacts(
            _base_harvest(),
            repo="DDD-Enterprises/dopemux-mvp",
            pr_number=704,
            strict=True,
            allow_closed=False,
        )
        readiness = artifacts["MERGE_READINESS.json"]
        assert isinstance(readiness, dict)
        assert "PROOF_STALE_OR_MISSING" not in readiness["blockers"]
        assert readiness["proof"]["proof_freshness"] == "FRESH"
        assert readiness["readiness"] == "READY"

    def test_stale_proof_adds_proof_stale_or_missing_blocker(self) -> None:
        harvest = _base_harvest()
        harvest["proof"] = {
            "proof_path": "proof/PROOF.json",
            "proof_head_sha": "old000000000000000000000000000000000000",
            "matches_pr_head": False,
        }
        artifacts = build_artifacts(
            harvest,
            repo="DDD-Enterprises/dopemux-mvp",
            pr_number=704,
            strict=True,
            allow_closed=False,
        )
        readiness = artifacts["MERGE_READINESS.json"]
        assert "PROOF_STALE_OR_MISSING" in readiness["blockers"]
        assert readiness["proof"]["proof_freshness"] == "STALE"

    def test_missing_proof_adds_proof_stale_or_missing_blocker(self) -> None:
        harvest = _base_harvest()
        harvest["proof"] = {}
        artifacts = build_artifacts(
            harvest,
            repo="DDD-Enterprises/dopemux-mvp",
            pr_number=704,
            strict=True,
            allow_closed=False,
        )
        readiness = artifacts["MERGE_READINESS.json"]
        assert "PROOF_STALE_OR_MISSING" in readiness["blockers"]
        assert readiness["proof"]["proof_freshness"] == "MISSING"
        assert "Proof head SHA missing" in readiness["unknowns"]

    def test_proof_freshness_propagates_to_snapshot(self) -> None:
        artifacts = build_artifacts(
            _base_harvest(),
            repo="DDD-Enterprises/dopemux-mvp",
            pr_number=704,
            strict=True,
            allow_closed=False,
        )
        snapshot_proof = artifacts["PR_STATE_SNAPSHOT.json"]["proof"]
        assert "proof_freshness" in snapshot_proof
        assert snapshot_proof["proof_freshness"] == "FRESH"
