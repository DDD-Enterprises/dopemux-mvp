"""
Tests for the generic PCP-Core PR Steward readiness intake.

Covers:
- Clean intake (all gates clear) → READY, blocked_reasons == [], schema-valid.
- One test per blocking condition: READY withheld, correct blocked_reason, status != READY,
  schema still valid.
- Advisory / no-merge proof: module source has no write/merge calls; advisory is True.
- harvest_pr_intake with a fake runner → schema-valid result; no real subprocess ran.
- Schema self-consistency: merge_readiness.schema.json is a valid Draft 2020-12 schema.
"""

from __future__ import annotations

import inspect
import json
import pathlib
from datetime import datetime, timezone
from typing import Any

import pytest
from jsonschema import Draft202012Validator

# ---------------------------------------------------------------------------
# Schema loading
# ---------------------------------------------------------------------------
_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
_SCHEMA_PATH = (
    _REPO_ROOT
    / "schemas"
    / "project_control_plane"
    / "merge_readiness.schema.json"
)

with _SCHEMA_PATH.open() as _fh:
    _SCHEMA: dict = json.load(_fh)


def _schema_errors(instance: dict) -> list:
    return list(Draft202012Validator(_SCHEMA).iter_errors(instance))


# ---------------------------------------------------------------------------
# Module under test
# ---------------------------------------------------------------------------
from dopemux.pcp.pr_steward import assess_merge_readiness, harvest_pr_intake  # noqa: E402

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_NOW = datetime.now(tz=timezone.utc).isoformat()

_CLEAN_PR_REF = {
    "repo": "owner/repo",
    "number": 42,
    "head_ref": "feature/foo",
    "base_ref": "main",
}
_HEAD_SHA = "a" * 40


def _clean_intake(**overrides: Any) -> dict:
    """Return a clean (all-gates-clear) intake dict, with optional field overrides."""
    base: dict[str, Any] = {
        "changed_files": ["src/foo.py"],
        "commits": ["deadbeef" * 5],
        "checks": [
            {"name": "ci/test", "conclusion": "SUCCESS", "stale_to_head": False}
        ],
        "reviews": [],
        "review_threads": [],
        "reviewer_classifications": [{"actor": "alice", "kind": "HUMAN"}],
        "unclassified_review_items": [],
        "proof_refs": [{"path": "proof/PROOF.json", "head_sha": _HEAD_SHA}],
        "proof_freshness": "FRESH",
        "diff_escapes_allowlist": False,
        "security_release_required": False,
        "security_release_approved": False,
    }
    base.update(overrides)
    return base


def _assess(intake: dict | None = None, **kwargs: Any) -> dict:
    """Shorthand: call assess_merge_readiness with defaults for pr_ref/head_sha/created_at."""
    return assess_merge_readiness(
        intake if intake is not None else _clean_intake(),
        pr_ref=kwargs.get("pr_ref", _CLEAN_PR_REF),
        head_sha=kwargs.get("head_sha", _HEAD_SHA),
        created_at=kwargs.get("created_at", _NOW),
    )


# ---------------------------------------------------------------------------
# 1. Clean intake → READY, blocked_reasons == [], schema-valid
# ---------------------------------------------------------------------------

class TestCleanIntakeReady:
    def test_status_is_ready(self) -> None:
        result = _assess()
        assert result["status"] == "READY"

    def test_blocked_reasons_empty(self) -> None:
        result = _assess()
        assert result["blocked_reasons"] == []

    def test_advisory_true(self) -> None:
        result = _assess()
        assert result["advisory"] is True

    def test_schema_valid(self) -> None:
        result = _assess()
        errors = _schema_errors(result)
        assert errors == [], f"Schema validation errors: {errors}"

    def test_schema_version_sentinel(self) -> None:
        result = _assess()
        assert result["schema_version"] == "pcp.merge_readiness.v0"


# ---------------------------------------------------------------------------
# 2. Blocking condition tests — one per blocked_reason
# ---------------------------------------------------------------------------

class TestStaleProof:
    @pytest.mark.parametrize("freshness", ["STALE", "MISSING", "UNKNOWN"])
    def test_stale_proof_withholds_ready(self, freshness: str) -> None:
        intake = _clean_intake(proof_freshness=freshness)
        result = _assess(intake)
        assert result["status"] != "READY"
        assert "STALE_PROOF" in result["blocked_reasons"]

    def test_schema_still_valid(self) -> None:
        intake = _clean_intake(proof_freshness="STALE")
        result = _assess(intake)
        assert _schema_errors(result) == []


class TestFailedCheck:
    def test_failed_check_withholds_ready(self) -> None:
        intake = _clean_intake(
            proof_freshness="FRESH",
            checks=[
                {"name": "ci/test", "conclusion": "FAILURE", "stale_to_head": False}
            ],
        )
        result = _assess(intake)
        assert result["status"] != "READY"
        assert "FAILED_CHECK" in result["blocked_reasons"]

    def test_schema_still_valid(self) -> None:
        intake = _clean_intake(
            proof_freshness="FRESH",
            checks=[
                {"name": "ci/test", "conclusion": "FAILURE", "stale_to_head": False}
            ],
        )
        result = _assess(intake)
        assert _schema_errors(result) == []


class TestStaleCheck:
    @pytest.mark.parametrize("conclusion", ["STALE", "PENDING", "UNKNOWN"])
    def test_stale_check_conclusion_withholds_ready(self, conclusion: str) -> None:
        intake = _clean_intake(
            proof_freshness="FRESH",
            checks=[
                {"name": "ci/test", "conclusion": conclusion, "stale_to_head": False}
            ],
        )
        result = _assess(intake)
        assert result["status"] != "READY"
        assert "STALE_CHECK" in result["blocked_reasons"]

    def test_stale_to_head_true_withholds_ready(self) -> None:
        intake = _clean_intake(
            proof_freshness="FRESH",
            checks=[
                {"name": "ci/test", "conclusion": "SUCCESS", "stale_to_head": True}
            ],
        )
        result = _assess(intake)
        assert result["status"] != "READY"
        assert "STALE_CHECK" in result["blocked_reasons"]

    def test_schema_still_valid(self) -> None:
        intake = _clean_intake(
            proof_freshness="FRESH",
            checks=[
                {"name": "ci/test", "conclusion": "PENDING", "stale_to_head": False}
            ],
        )
        result = _assess(intake)
        assert _schema_errors(result) == []


class TestUnknownReviewerOrBot:
    def test_unknown_reviewer_withholds_ready(self) -> None:
        intake = _clean_intake(
            reviewer_classifications=[{"actor": "mystery-user", "kind": "UNKNOWN"}]
        )
        result = _assess(intake)
        assert result["status"] != "READY"
        assert "UNKNOWN_REVIEWER_OR_BOT" in result["blocked_reasons"]

    def test_schema_still_valid(self) -> None:
        intake = _clean_intake(
            reviewer_classifications=[{"actor": "mystery-user", "kind": "UNKNOWN"}]
        )
        result = _assess(intake)
        assert _schema_errors(result) == []


class TestUnclassifiedReviewItem:
    def test_unclassified_items_withholds_ready(self) -> None:
        intake = _clean_intake(
            unclassified_review_items=["item-id-abc123"]
        )
        result = _assess(intake)
        assert result["status"] != "READY"
        assert "UNCLASSIFIED_REVIEW_ITEM" in result["blocked_reasons"]

    def test_schema_still_valid(self) -> None:
        intake = _clean_intake(
            unclassified_review_items=["item-id-abc123"]
        )
        result = _assess(intake)
        assert _schema_errors(result) == []


class TestUnresolvedBlockingThread:
    def test_unresolved_blocking_thread_withholds_ready(self) -> None:
        intake = _clean_intake(
            review_threads=[{"resolved": False, "blocking": True}]
        )
        result = _assess(intake)
        assert result["status"] != "READY"
        assert "UNRESOLVED_BLOCKING_THREAD" in result["blocked_reasons"]

    def test_resolved_blocking_thread_does_not_block(self) -> None:
        intake = _clean_intake(
            review_threads=[{"resolved": True, "blocking": True}]
        )
        result = _assess(intake)
        assert "UNRESOLVED_BLOCKING_THREAD" not in result["blocked_reasons"]

    def test_schema_still_valid(self) -> None:
        intake = _clean_intake(
            review_threads=[{"resolved": False, "blocking": True}]
        )
        result = _assess(intake)
        assert _schema_errors(result) == []


class TestDiffOutsideAllowlist:
    def test_diff_escape_withholds_ready(self) -> None:
        intake = _clean_intake(diff_escapes_allowlist=True)
        result = _assess(intake)
        assert result["status"] != "READY"
        assert "DIFF_OUTSIDE_ALLOWLIST" in result["blocked_reasons"]

    def test_schema_still_valid(self) -> None:
        intake = _clean_intake(diff_escapes_allowlist=True)
        result = _assess(intake)
        assert _schema_errors(result) == []


class TestMissingSecurityReleaseApproval:
    def test_missing_security_approval_withholds_ready(self) -> None:
        intake = _clean_intake(
            security_release_required=True,
            security_release_approved=False,
        )
        result = _assess(intake)
        assert result["status"] != "READY"
        assert "MISSING_SECURITY_RELEASE_APPROVAL" in result["blocked_reasons"]

    def test_approved_security_gate_does_not_block(self) -> None:
        intake = _clean_intake(
            security_release_required=True,
            security_release_approved=True,
        )
        result = _assess(intake)
        assert "MISSING_SECURITY_RELEASE_APPROVAL" not in result["blocked_reasons"]

    def test_schema_still_valid(self) -> None:
        intake = _clean_intake(
            security_release_required=True,
            security_release_approved=False,
        )
        result = _assess(intake)
        assert _schema_errors(result) == []


class TestMissingRequiredIntake:
    def test_none_intake_withholds_ready(self) -> None:
        result = assess_merge_readiness(
            None,
            pr_ref=_CLEAN_PR_REF,
            head_sha=_HEAD_SHA,
            created_at=_NOW,
        )
        assert result["status"] != "READY"
        assert "MISSING_REQUIRED_INTAKE" in result["blocked_reasons"]

    def test_empty_head_sha_withholds_ready(self) -> None:
        result = assess_merge_readiness(
            _clean_intake(),
            pr_ref=_CLEAN_PR_REF,
            head_sha="",
            created_at=_NOW,
        )
        assert result["status"] != "READY"
        assert "MISSING_REQUIRED_INTAKE" in result["blocked_reasons"]

    def test_schema_still_valid_with_none_intake(self) -> None:
        result = assess_merge_readiness(
            None,
            pr_ref=_CLEAN_PR_REF,
            head_sha=_HEAD_SHA,
            created_at=_NOW,
        )
        assert _schema_errors(result) == []


# ---------------------------------------------------------------------------
# 3. Advisory / no-merge proof
# ---------------------------------------------------------------------------

class TestAdvisoryAndNoMerge:
    def test_advisory_field_always_true(self) -> None:
        result = _assess()
        assert result["advisory"] is True

    def test_blocked_result_advisory_true(self) -> None:
        result = _assess(_clean_intake(proof_freshness="STALE"))
        assert result["advisory"] is True

    def test_module_source_has_no_merge_calls(self) -> None:
        """Assert the module source contains no write/merge/push commands."""
        import dopemux.pcp.pr_steward as _mod
        source = inspect.getsource(_mod)
        forbidden_patterns = [
            "gh pr merge",
            "gh pr ready",
            "git push",
            "git commit",
            "git merge",
        ]
        for pattern in forbidden_patterns:
            assert pattern not in source, (
                f"Module source contains forbidden pattern: {pattern!r}"
            )


# ---------------------------------------------------------------------------
# 4. harvest_pr_intake with a fake runner
# ---------------------------------------------------------------------------

class TestHarvestPrIntakeWithFakeRunner:
    """harvest_pr_intake must use the injected runner and produce a schema-valid result."""

    _GH_PR_JSON = json.dumps({
        "number": 99,
        "headRefName": "feature/bar",
        "baseRefName": "main",
        "headRefOid": "b" * 40,
        "files": [
            {"path": "src/bar.py", "additions": 10, "deletions": 2, "changeType": "MODIFIED"}
        ],
        "commits": [
            {"oid": "c" * 40, "messageHeadline": "feat: bar"}
        ],
        "reviews": [
            {"author": {"login": "bob"}, "state": "APPROVED", "body": "lgtm"}
        ],
        "statusCheckRollup": [
            {"name": "ci/lint", "conclusion": "SUCCESS", "state": "COMPLETED"}
        ],
        "reviewThreads": [
            {"isResolved": True, "comments": {"nodes": []}}
        ],
    })

    def _make_runner(self) -> tuple[list, object]:
        calls: list[list[str]] = []

        def fake_runner(args: list[str]) -> str:
            calls.append(list(args))
            return self._GH_PR_JSON

        return calls, fake_runner

    def test_no_real_subprocess_called(self) -> None:
        calls, fake_runner = self._make_runner()
        harvest_pr_intake(99, repo="owner/repo", runner=fake_runner)
        assert len(calls) >= 1, "fake runner was never called"
        # All calls must go through the fake, not subprocess
        for call in calls:
            assert call[0] == "gh", f"Unexpected command prefix: {call[0]}"

    def test_returns_pr_ref(self) -> None:
        _, fake_runner = self._make_runner()
        result = harvest_pr_intake(99, repo="owner/repo", runner=fake_runner)
        assert result["pr_ref"]["number"] == 99
        assert result["pr_ref"]["repo"] == "owner/repo"
        assert result["pr_ref"]["head_ref"] == "feature/bar"
        assert result["pr_ref"]["base_ref"] == "main"

    def test_returns_head_sha(self) -> None:
        _, fake_runner = self._make_runner()
        result = harvest_pr_intake(99, repo="owner/repo", runner=fake_runner)
        assert result["head_sha"] == "b" * 40

    def test_produce_schema_valid_signal(self) -> None:
        """Full pipeline: harvest → assess → schema validate."""
        _, fake_runner = self._make_runner()
        harvest = harvest_pr_intake(99, repo="owner/repo", runner=fake_runner)
        signal = assess_merge_readiness(
            harvest["intake"],
            pr_ref=harvest["pr_ref"],
            head_sha=harvest["head_sha"],
            created_at=_NOW,
        )
        errors = _schema_errors(signal)
        assert errors == [], f"Schema errors: {errors}"

    def test_invalid_pr_number_raises(self) -> None:
        _, fake_runner = self._make_runner()
        with pytest.raises(ValueError, match="pr_number"):
            harvest_pr_intake(0, repo="owner/repo", runner=fake_runner)

    def test_empty_repo_raises(self) -> None:
        _, fake_runner = self._make_runner()
        with pytest.raises(ValueError, match="repo"):
            harvest_pr_intake(1, repo="", runner=fake_runner)

    def test_malformed_json_raises(self) -> None:
        def bad_runner(args: list[str]) -> str:
            return "not json {"

        with pytest.raises(ValueError, match="non-JSON"):
            harvest_pr_intake(1, repo="owner/repo", runner=bad_runner)


# ---------------------------------------------------------------------------
# 6. Security gate — new tests (fail-open fix + schema gate e)
# ---------------------------------------------------------------------------

class TestSecurityGateYiedsNeedsSupervisor:
    def test_security_gate_yields_needs_supervisor(self) -> None:
        """Clean intake with security_release_required=True, approved=False → NEEDS_SUPERVISOR."""
        intake = _clean_intake(
            security_release_required=True,
            security_release_approved=False,
        )
        result = _assess(intake)
        assert result["status"] == "NEEDS_SUPERVISOR"
        assert "MISSING_SECURITY_RELEASE_APPROVAL" in result["blocked_reasons"]
        assert _schema_errors(result) == []


class TestSecurityRequiredTruthyNonBoolStillBlocks:
    def test_security_required_truthy_non_bool_still_blocks(self) -> None:
        """Truthy integer 1 for security_release_required must still trigger the block.

        This locks the fail-open fix: bool() coercion, not `is True` identity,
        is required so that non-True truthy values (e.g. integer 1) are caught.
        """
        intake = _clean_intake(
            security_release_required=1,   # integer truthy, not the bool True
            security_release_approved=0,   # integer falsy, not the bool False
        )
        result = _assess(intake)
        assert result["status"] != "READY"
        assert "MISSING_SECURITY_RELEASE_APPROVAL" in result["blocked_reasons"]


class TestSchemaRejectsReadyWithUnapprovedSecurityGate:
    def test_schema_rejects_ready_with_unapproved_security_gate(self) -> None:
        """Schema gate (e) must reject a hand-crafted READY signal with unapproved security gate.

        The code path never produces this combination, but the schema must also
        independently reject it as defense-in-depth.
        """
        bad_signal: dict[str, Any] = {
            "schema_version": "pcp.merge_readiness.v0",
            "pr_ref": _CLEAN_PR_REF,
            "head_sha": _HEAD_SHA,
            "status": "READY",
            "blocked_reasons": [],
            "advisory": True,
            "created_at": _NOW,
            "intake": {
                "changed_files": ["src/foo.py"],
                "commits": ["deadbeef" * 5],
                "checks": [
                    {"name": "ci/test", "conclusion": "SUCCESS", "stale_to_head": False}
                ],
                "reviews": [],
                "review_threads": [],
                "reviewer_classifications": [{"actor": "alice", "kind": "HUMAN"}],
                "unclassified_review_items": [],
                "proof_refs": [{"path": "proof/PROOF.json", "head_sha": _HEAD_SHA}],
                "proof_freshness": "FRESH",
                "diff_escapes_allowlist": False,
                # Unapproved security gate — should be rejected by schema gate (e)
                "security_release_required": True,
                "security_release_approved": False,
            },
        }
        errors = _schema_errors(bad_signal)
        assert len(errors) >= 1, (
            "Schema gate (e) should reject READY with unapproved security gate, "
            f"but no errors were found. Signal: {bad_signal}"
        )


# ---------------------------------------------------------------------------
# 5. Schema self-consistency
# ---------------------------------------------------------------------------

class TestSchemaSelfConsistency:
    def test_schema_is_valid_draft_2020_12(self) -> None:
        """merge_readiness.schema.json must be a valid Draft 2020-12 schema."""
        with _SCHEMA_PATH.open() as fh:
            schema = json.load(fh)
        # Check schema raises nothing if meta-schema validation passes
        Draft202012Validator.check_schema(schema)

    def test_schema_has_required_id(self) -> None:
        with _SCHEMA_PATH.open() as fh:
            schema = json.load(fh)
        assert schema.get("$id") == (
            "https://dopemux.dev/schemas/project_control_plane/merge_readiness.schema.json"
        )

    def test_schema_version_is_correct(self) -> None:
        with _SCHEMA_PATH.open() as fh:
            schema = json.load(fh)
        assert schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema"
