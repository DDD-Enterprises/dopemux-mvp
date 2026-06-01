"""Tests for TP-DMX-PR-STEWARD-HARDEN-010 hardening items:
  - PROOF_STALE / PROOF_MISSING split (no more PROOF_STALE_OR_MISSING)
  - UNKNOWN_PR_AUTHOR blocker
  - risk_tier field in MERGE_READINESS.json
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from tools.pr_steward.classifier import _readiness, _risk_tier, build_artifacts

ROOT = Path(__file__).resolve().parents[2]
KNOWN_REVIEWERS_PATH = ROOT / "tools" / "pr_steward" / "known_reviewers.json"


def _base_harvest(
    head_sha: str = "head000000000000000000000000000000000000",
    author_login: str = "hu3mann",
) -> dict:
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
            "author": {"login": author_login},
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
                "conclusion": "success",
                "headSha": head_sha,
            }
        ],
        "proof": {
            "proof_path": "proof/PROOF.json",
            "proof_head_sha": head_sha,
            "matches_pr_head": True,
        },
        "embedded_audit": {
            "status": "PASS",
            "report_path": "proof/AUDITOR_REPORT.md",
        },
    }


def _artifacts(harvest: dict) -> dict:
    return build_artifacts(
        harvest,
        repo="DDD-Enterprises/dopemux-mvp",
        pr_number=704,
        strict=True,
        allow_closed=False,
        known_reviewers_path=KNOWN_REVIEWERS_PATH,
    )["MERGE_READINESS.json"]


# ---------------------------------------------------------------------------
# PROOF_STALE / PROOF_MISSING split
# ---------------------------------------------------------------------------


class TestProofBlockerSplit:
    def test_stale_proof_emits_proof_stale_not_combined(self) -> None:
        harvest = _base_harvest()
        harvest["proof"] = {
            "proof_path": "proof/PROOF.json",
            "proof_head_sha": "old000000000000000000000000000000000000",
            "matches_pr_head": False,
        }
        readiness = _artifacts(harvest)
        assert "PROOF_STALE" in readiness["blockers"]
        assert "PROOF_MISSING" not in readiness["blockers"]
        assert "PROOF_STALE_OR_MISSING" not in readiness["blockers"]

    def test_stale_proof_recomputed_even_when_harvest_claims_current(self) -> None:
        harvest = _base_harvest()
        harvest["proof"] = {
            "proof_path": "proof/PROOF.json",
            "proof_head_sha": "old000000000000000000000000000000000000",
            "matches_pr_head": True,
            "proof_freshness": {
                "status": "CURRENT",
                "matches_pr_head": True,
                "proof_recorded_sha": "old000000000000000000000000000000000000",
                "pr_head_sha": harvest["pr"]["headRefOid"],
            },
        }

        readiness = _artifacts(harvest)

        assert "PROOF_STALE" in readiness["blockers"]
        assert readiness["proof"]["matches_pr_head"] is False
        assert readiness["proof"]["proof_freshness"]["status"] == "STALE"

    def test_missing_proof_emits_proof_missing_not_combined(self) -> None:
        harvest = _base_harvest()
        harvest["proof"] = {}
        readiness = _artifacts(harvest)
        assert "PROOF_MISSING" in readiness["blockers"]
        assert "PROOF_STALE" not in readiness["blockers"]
        assert "PROOF_STALE_OR_MISSING" not in readiness["blockers"]

    def test_fresh_proof_emits_neither_proof_blocker(self) -> None:
        readiness = _artifacts(_base_harvest())
        assert "PROOF_STALE" not in readiness["blockers"]
        assert "PROOF_MISSING" not in readiness["blockers"]
        assert "PROOF_STALE_OR_MISSING" not in readiness["blockers"]

    def test_stale_proof_maps_to_needs_supervisor(self) -> None:
        harvest = _base_harvest()
        harvest["proof"] = {
            "proof_path": "proof/PROOF.json",
            "proof_head_sha": "old000000000000000000000000000000000000",
            "matches_pr_head": False,
        }
        readiness = _artifacts(harvest)
        assert readiness["readiness"] == "NEEDS_SUPERVISOR"

    def test_missing_proof_maps_to_needs_supervisor(self) -> None:
        harvest = _base_harvest()
        harvest["proof"] = {}
        readiness = _artifacts(harvest)
        assert readiness["readiness"] == "NEEDS_SUPERVISOR"

    def test_readiness_function_handles_proof_stale(self) -> None:
        assert _readiness(["PROOF_STALE"]) == "NEEDS_SUPERVISOR"

    def test_readiness_function_handles_proof_missing(self) -> None:
        assert _readiness(["PROOF_MISSING"]) == "NEEDS_SUPERVISOR"


# ---------------------------------------------------------------------------
# UNKNOWN_PR_AUTHOR blocker
# ---------------------------------------------------------------------------


class TestUnknownPrAuthor:
    def test_known_author_no_blocker(self) -> None:
        readiness = _artifacts(_base_harvest(author_login="hu3mann"))
        assert "UNKNOWN_PR_AUTHOR" not in readiness["blockers"]

    def test_unknown_author_adds_blocker(self) -> None:
        readiness = _artifacts(_base_harvest(author_login="external-bot"))
        assert "UNKNOWN_PR_AUTHOR" in readiness["blockers"]

    def test_unknown_author_adds_unknown_entry(self) -> None:
        readiness = _artifacts(_base_harvest(author_login="external-bot"))
        assert any("external-bot" in u for u in readiness["unknowns"])

    def test_unknown_author_maps_to_needs_supervisor(self) -> None:
        readiness = _artifacts(_base_harvest(author_login="external-bot"))
        assert readiness["readiness"] == "NEEDS_SUPERVISOR"

    def test_readiness_function_handles_unknown_pr_author(self) -> None:
        assert _readiness(["UNKNOWN_PR_AUTHOR"]) == "NEEDS_SUPERVISOR"

    def test_known_reviewers_file_used(self) -> None:
        harvest = _base_harvest(author_login="chatgpt-codex-connector")
        readiness = _artifacts(harvest)
        assert "UNKNOWN_PR_AUTHOR" not in readiness["blockers"]

    def test_nested_author_association_owner_trusted(self) -> None:
        harvest = _base_harvest(author_login="external-bot")
        harvest["pr"]["author"] = {"login": "external-bot", "authorAssociation": "OWNER"}
        readiness = _artifacts(harvest)
        assert "UNKNOWN_PR_AUTHOR" not in readiness["blockers"]

    def test_nested_author_association_none_treated_as_unknown(self) -> None:
        harvest = _base_harvest(author_login="external-bot")
        harvest["pr"]["author"] = {"login": "external-bot"}
        readiness = _artifacts(harvest)
        assert "UNKNOWN_PR_AUTHOR" in readiness["blockers"]


# ---------------------------------------------------------------------------
# risk_tier field
# ---------------------------------------------------------------------------


class TestRiskTier:
    def test_ready_has_clear_risk_tier(self) -> None:
        readiness = _artifacts(_base_harvest())
        assert readiness["risk_tier"] == "CLEAR"

    def test_needs_supervisor_has_high_risk_tier(self) -> None:
        harvest = _base_harvest()
        harvest["proof"] = {}
        readiness = _artifacts(harvest)
        assert readiness["risk_tier"] == "HIGH"

    def test_blocked_pr_has_critical_risk_tier(self) -> None:
        harvest = _base_harvest()
        harvest["pr"]["isDraft"] = True
        readiness = _artifacts(harvest)
        assert readiness["risk_tier"] == "CRITICAL"

    def test_risk_tier_present_in_output(self) -> None:
        readiness = _artifacts(_base_harvest())
        assert "risk_tier" in readiness

    def test_risk_tier_mapping_blocked(self) -> None:
        assert _risk_tier("BLOCKED") == "CRITICAL"

    def test_risk_tier_mapping_needs_supervisor(self) -> None:
        assert _risk_tier("NEEDS_SUPERVISOR") == "HIGH"

    def test_risk_tier_mapping_needs_implementer(self) -> None:
        assert _risk_tier("NEEDS_IMPLEMENTER") == "MEDIUM"

    def test_risk_tier_mapping_not_ready(self) -> None:
        assert _risk_tier("NOT_READY") == "LOW"

    def test_risk_tier_mapping_ready(self) -> None:
        assert _risk_tier("READY") == "CLEAR"

    def test_risk_tier_in_summary(self) -> None:
        artifacts = build_artifacts(
            _base_harvest(),
            repo="DDD-Enterprises/dopemux-mvp",
            pr_number=704,
            strict=True,
            allow_closed=False,
            known_reviewers_path=KNOWN_REVIEWERS_PATH,
        )
        summary = artifacts["PR_STEWARD_SUMMARY.md"]
        assert "risk_tier: CLEAR" in summary
