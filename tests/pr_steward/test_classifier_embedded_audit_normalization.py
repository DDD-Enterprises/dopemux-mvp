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
