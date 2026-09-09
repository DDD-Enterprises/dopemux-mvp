"""Regression tests for _embedded_audit() schema normalization.

Asserts that:
1. Unknown status values are normalized to "SKIPPED" so artifacts
   remain schema-valid.
2. The EMBEDDED_AUDIT_UNKNOWN blocker still fires when upstream
   supplies a non-canonical status.
3. The emitted MERGE_READINESS.json validates against
   schemas/pr_steward/merge_readiness.schema.json.
"""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from tools.pr_steward.classifier import build_artifacts


_REPO_ROOT = Path(__file__).resolve().parents[2]
_MERGE_READINESS_SCHEMA = (
    _REPO_ROOT / "schemas" / "pr_steward" / "merge_readiness.schema.json"
)
_PR_STATE_SNAPSHOT_SCHEMA = (
    _REPO_ROOT / "schemas" / "pr_steward" / "pr_state_snapshot.schema.json"
)
_NOT_REQUIRED_REASON = "AUDIT_NOT_REQUIRED_BY_TRUSTED_CHANGE_CONTRACT"


def _minimal_harvest(audit_status: str | None) -> dict:
    """Minimal harvest payload sufficient for build_artifacts() to run.

    Only the embedded_audit.status is parametrized; everything else is
    fixed so the test asserts on the audit normalization specifically.
    """
    return {
        "harvest_complete": True,
        "pr": {
            "number": 718,
            "url": "https://github.com/DDD-Enterprises/dopemux-mvp/pull/718",
            "state": "OPEN",
            "draft": False,
            "author": {"login": "test-author", "authorAssociation": "OWNER"},
            "baseRefName": "main",
            "headRefName": "test-branch",
            "headRefOid": "deadbeef",
        },
        "reviews": [],
        "review_comments": [],
        "review_threads": [],
        "issue_comments": [],
        "checks": [],
        "changed_files": [],
        "commits": [],
        "embedded_audit": (
            {"status": audit_status, "report_path": "proof/test/AUDITOR_REPORT.md"}
            if audit_status is not None
            else {}
        ),
        "proof": {
            "proof_path": "proof/test/PROOF.json",
            "proof_head_sha": "deadbeef",
            "matches_pr_head": True,
        },
    }


@pytest.fixture(scope="module")
def merge_readiness_schema():
    return json.loads(_MERGE_READINESS_SCHEMA.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def pr_state_snapshot_schema():
    return json.loads(_PR_STATE_SNAPSHOT_SCHEMA.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "raw_status,expected_normalized",
    [
        ("PASS", "PASS"),
        ("PASS_WITH_RISKS", "PASS_WITH_RISKS"),
        ("FAIL", "FAIL"),
        ("NEEDS_SUPERVISOR", "NEEDS_SUPERVISOR"),
        ("SKIPPED", "SKIPPED"),
        ("NOT_RUN", "SKIPPED"),       # Codex P2 case: non-canonical → SKIPPED
        ("UNKNOWN", "SKIPPED"),
        ("pass", "PASS"),              # case insensitive
        ("Fail", "FAIL"),
        ("", "SKIPPED"),
        (None, "SKIPPED"),
    ],
)
def test_embedded_audit_status_normalization(
    raw_status, expected_normalized, merge_readiness_schema, pr_state_snapshot_schema
):
    """Emitted embedded_audit.status is always in the schema enum."""
    harvest = _minimal_harvest(raw_status)
    artifacts = build_artifacts(
        harvest,
        repo="DDD-Enterprises/dopemux-mvp",
        pr_number=718,
        strict=False,
        allow_closed=False,
    )

    merge_readiness = artifacts["MERGE_READINESS.json"]
    snapshot = artifacts["PR_STATE_SNAPSHOT.json"]

    assert merge_readiness["embedded_audit"]["status"] == expected_normalized
    assert snapshot["embedded_audit"]["status"] == expected_normalized

    # Schema-validate both artifacts — this is the F1 regression assertion.
    jsonschema.Draft7Validator(merge_readiness_schema).validate(merge_readiness)
    jsonschema.Draft7Validator(pr_state_snapshot_schema).validate(snapshot)


@pytest.mark.parametrize("non_canonical_status", ["NOT_RUN", "UNKNOWN", "weird"])
def test_unknown_status_adds_embedded_audit_unknown_blocker(non_canonical_status):
    """Fail-closed: non-canonical upstream status still adds EMBEDDED_AUDIT_UNKNOWN blocker."""
    harvest = _minimal_harvest(non_canonical_status)
    artifacts = build_artifacts(
        harvest,
        repo="DDD-Enterprises/dopemux-mvp",
        pr_number=718,
        strict=False,
        allow_closed=False,
    )
    merge_readiness = artifacts["MERGE_READINESS.json"]
    assert "EMBEDDED_AUDIT_UNKNOWN" in merge_readiness["blockers"], (
        f"Blocker missing for raw status {non_canonical_status!r}; "
        f"got blockers={merge_readiness['blockers']!r}"
    )


def test_canonical_status_does_not_add_unknown_blocker():
    """Canonical status (PASS) must NOT trigger EMBEDDED_AUDIT_UNKNOWN."""
    harvest = _minimal_harvest("PASS")
    artifacts = build_artifacts(
        harvest,
        repo="DDD-Enterprises/dopemux-mvp",
        pr_number=718,
        strict=False,
        allow_closed=False,
    )
    merge_readiness = artifacts["MERGE_READINESS.json"]
    assert "EMBEDDED_AUDIT_UNKNOWN" not in merge_readiness["blockers"]


def _artifacts_for_audit(audit: dict) -> dict:
    harvest = _minimal_harvest("PASS")
    harvest["embedded_audit"] = audit
    return build_artifacts(
        harvest,
        repo="DDD-Enterprises/dopemux-mvp",
        pr_number=718,
        strict=False,
        allow_closed=False,
    )


def _ready_schema_candidate(audit: dict) -> dict:
    candidate = _artifacts_for_audit(
        {"status": "PASS", "report_path": "proof/test/AUDITOR_REPORT.md"}
    )["MERGE_READINESS.json"]
    candidate["readiness"] = "READY"
    candidate["risk_tier"] = "CLEAR"
    candidate["embedded_audit"] = audit
    candidate["blockers"] = []
    candidate["unknowns"] = []
    return candidate


def test_exact_trusted_not_required_is_nonblocking_and_preserves_fields(
    merge_readiness_schema, pr_state_snapshot_schema
):
    artifacts = _artifacts_for_audit(
        {
            "status": "SKIPPED",
            "required": False,
            "skip_reason": _NOT_REQUIRED_REASON,
            "report_path": "proof/test/AUDITOR_REPORT.md",
        }
    )

    merge_readiness = artifacts["MERGE_READINESS.json"]
    snapshot = artifacts["PR_STATE_SNAPSHOT.json"]
    assert merge_readiness["readiness"] == "READY"
    assert "EMBEDDED_AUDIT_SKIPPED" not in merge_readiness["blockers"]
    assert merge_readiness["embedded_audit"]["required"] is False
    assert merge_readiness["embedded_audit"]["skip_reason"] == _NOT_REQUIRED_REASON
    assert set(snapshot["embedded_audit"]) == {"status", "report_path"}
    jsonschema.Draft7Validator(merge_readiness_schema).validate(merge_readiness)
    jsonschema.Draft7Validator(pr_state_snapshot_schema).validate(snapshot)


@pytest.mark.parametrize(
    "audit",
    [
        {
            "status": "SKIPPED",
            "required": True,
            "skip_reason": _NOT_REQUIRED_REASON,
            "report_path": "proof/test/AUDITOR_REPORT.md",
        },
        {
            "status": "SKIPPED",
            "required": None,
            "skip_reason": _NOT_REQUIRED_REASON,
            "report_path": "proof/test/AUDITOR_REPORT.md",
        },
        {
            "status": "SKIPPED",
            "required": "false",
            "skip_reason": _NOT_REQUIRED_REASON,
            "report_path": "proof/test/AUDITOR_REPORT.md",
        },
        {
            "status": "SKIPPED",
            "skip_reason": _NOT_REQUIRED_REASON,
            "report_path": "proof/test/AUDITOR_REPORT.md",
        },
        {
            "status": "SKIPPED",
            "required": False,
            "skip_reason": "UNTRUSTED_REASON",
            "report_path": "proof/test/AUDITOR_REPORT.md",
        },
        {
            "status": "SKIPPED",
            "required": False,
            "report_path": "proof/test/AUDITOR_REPORT.md",
        },
        {
            "required": False,
            "skip_reason": _NOT_REQUIRED_REASON,
            "report_path": "proof/test/AUDITOR_REPORT.md",
        },
        {
            "status": "skipped",
            "required": False,
            "skip_reason": _NOT_REQUIRED_REASON,
            "report_path": "proof/test/AUDITOR_REPORT.md",
        },
    ],
    ids=[
        "required-true",
        "required-null",
        "required-string",
        "required-missing",
        "wrong-reason",
        "missing-reason",
        "missing-status",
        "noncanonical-status-case",
    ],
)
def test_nontrusted_skipped_audit_remains_blocking_and_schema_valid(
    audit, merge_readiness_schema
):
    merge_readiness = _artifacts_for_audit(audit)["MERGE_READINESS.json"]

    assert merge_readiness["readiness"] == "NEEDS_SUPERVISOR"
    assert "EMBEDDED_AUDIT_SKIPPED" in merge_readiness["blockers"]
    normalized = merge_readiness["embedded_audit"]
    raw_required = audit.get("required")
    raw_skip_reason = audit.get("skip_reason")
    assert normalized["required"] == (
        raw_required if isinstance(raw_required, bool) else None
    )
    assert normalized["skip_reason"] == (
        raw_skip_reason if isinstance(raw_skip_reason, str) else None
    )
    jsonschema.Draft7Validator(merge_readiness_schema).validate(merge_readiness)


@pytest.mark.parametrize("status", ["PASS", "PASS_WITH_RISKS"])
def test_passing_audit_statuses_remain_nonblocking(status):
    merge_readiness = _artifacts_for_audit(
        {
            "status": status,
            "required": True,
            "skip_reason": None,
            "report_path": "proof/test/AUDITOR_REPORT.md",
        }
    )["MERGE_READINESS.json"]

    assert merge_readiness["readiness"] == "READY"
    assert not any(
        blocker.startswith("EMBEDDED_AUDIT_")
        for blocker in merge_readiness["blockers"]
    )


@pytest.mark.parametrize("status", ["FAIL", "NEEDS_SUPERVISOR"])
def test_blocking_audit_statuses_remain_blocking(status):
    merge_readiness = _artifacts_for_audit(
        {
            "status": status,
            "required": True,
            "skip_reason": None,
            "report_path": "proof/test/AUDITOR_REPORT.md",
        }
    )["MERGE_READINESS.json"]

    assert f"EMBEDDED_AUDIT_{status}" in merge_readiness["blockers"]


def test_unknown_status_cannot_claim_trusted_not_required():
    merge_readiness = _artifacts_for_audit(
        {
            "status": "UNKNOWN",
            "required": False,
            "skip_reason": _NOT_REQUIRED_REASON,
            "report_path": "proof/test/AUDITOR_REPORT.md",
        }
    )["MERGE_READINESS.json"]

    assert merge_readiness["readiness"] == "NEEDS_SUPERVISOR"
    assert "EMBEDDED_AUDIT_UNKNOWN" in merge_readiness["blockers"]


def test_ready_schema_accepts_exact_trusted_not_required(merge_readiness_schema):
    candidate = _ready_schema_candidate(
        {
            "status": "SKIPPED",
            "required": False,
            "skip_reason": _NOT_REQUIRED_REASON,
            "report_path": "proof/test/AUDITOR_REPORT.md",
        }
    )

    jsonschema.Draft7Validator(merge_readiness_schema).validate(candidate)


@pytest.mark.parametrize(
    "audit",
    [
        {
            "status": "SKIPPED",
            "required": True,
            "skip_reason": _NOT_REQUIRED_REASON,
            "report_path": "proof/test/AUDITOR_REPORT.md",
        },
        {
            "status": "SKIPPED",
            "required": None,
            "skip_reason": _NOT_REQUIRED_REASON,
            "report_path": "proof/test/AUDITOR_REPORT.md",
        },
        {
            "status": "SKIPPED",
            "required": "false",
            "skip_reason": _NOT_REQUIRED_REASON,
            "report_path": "proof/test/AUDITOR_REPORT.md",
        },
        {
            "status": "SKIPPED",
            "skip_reason": _NOT_REQUIRED_REASON,
            "report_path": "proof/test/AUDITOR_REPORT.md",
        },
        {
            "status": "SKIPPED",
            "required": False,
            "skip_reason": "UNTRUSTED_REASON",
            "report_path": "proof/test/AUDITOR_REPORT.md",
        },
        {
            "status": "SKIPPED",
            "required": False,
            "report_path": "proof/test/AUDITOR_REPORT.md",
        },
        {
            "required": False,
            "skip_reason": _NOT_REQUIRED_REASON,
            "report_path": "proof/test/AUDITOR_REPORT.md",
        },
    ],
    ids=[
        "required-true",
        "required-null",
        "required-string",
        "required-missing",
        "wrong-reason",
        "missing-reason",
        "missing-status",
    ],
)
def test_ready_schema_rejects_nontrusted_skipped_audit(
    audit, merge_readiness_schema
):
    candidate = _ready_schema_candidate(audit)

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft7Validator(merge_readiness_schema).validate(candidate)
