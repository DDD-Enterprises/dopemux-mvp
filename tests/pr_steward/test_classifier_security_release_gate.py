# tests/pr_steward/test_classifier_security_release_gate.py
from __future__ import annotations

from pathlib import Path

import pytest

from tools.pr_steward.classifier import build_artifacts

ROOT = Path(__file__).resolve().parents[2]
KNOWN_REVIEWERS_PATH = ROOT / "tools" / "pr_steward" / "known_reviewers.json"
TRUSTED_FIXTURE = ROOT / "tests" / "pr_steward" / "fixtures" / "known_reviewers_with_approver.json"

HEAD_SHA = "head000000000000000000000000000000000000"


def _base_harvest(changed_files=None, security_release_approval=None) -> dict:
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
            "headRefOid": HEAD_SHA,
            "author": {"login": "hu3mann"},
            "createdAt": "2026-05-26T01:00:00Z",
            "updatedAt": "2026-05-26T02:00:00Z",
        },
        "changed_files": [{"path": p, "additions": 1} for p in (changed_files or ["foo.py"])],
        "commits": [{"oid": HEAD_SHA, "messageHeadline": "test"}],
        "reviews": [],
        "review_comments": [],
        "review_threads": [],
        "issue_comments": [],
        "checks": [
            {"name": "unit", "status": "COMPLETED", "conclusion": "success", "headSha": HEAD_SHA}
        ],
        "proof": {
            "proof_path": "proof/PROOF.json",
            "proof_head_sha": HEAD_SHA,
            "matches_pr_head": True,
        },
        "embedded_audit": {"status": "PASS", "report_path": "proof/AUDITOR_REPORT.md"},
        "security_release_approval": security_release_approval,
    }


@pytest.fixture(autouse=True, scope="module")
def _fixture_dir(tmp_path_factory):
    global TRUSTED_FIXTURE
    TRUSTED_FIXTURE = (
        tmp_path_factory.mktemp("pr_steward") / "known_reviewers_with_approver.json"
    )
    TRUSTED_FIXTURE.write_text(
        """{
  \"known_reviewers\": [\"hu3mann\"],
  \"trusted_author_associations\": [\"OWNER\"],
  \"trusted_security_release_approvers\": [\"trusted-approver\"]
}"""
    )
    yield
    TRUSTED_FIXTURE.unlink(missing_ok=True)

def _artifacts(harvest: dict, known_reviewers_path=KNOWN_REVIEWERS_PATH) -> dict:
    return build_artifacts(
        harvest,
        repo="DDD-Enterprises/dopemux-mvp",
        pr_number=704,
        strict=True,
        allow_closed=False,
        known_reviewers_path=known_reviewers_path,
    )["MERGE_READINESS.json"]


def test_ordinary_pr_does_not_require_security_release():
    readiness = _artifacts(_base_harvest())
    assert readiness["security_release"]["required"] is False
    assert readiness["readiness"] == "READY"


def test_red_lane_pr_without_approval_cannot_be_ready():
    readiness = _artifacts(_base_harvest(changed_files=[".github/workflows/x.yml"]))
    assert readiness["security_release"]["required"] is True
    assert readiness["security_release"]["approved"] is False
    assert readiness["readiness"] != "READY"
    assert "SECURITY_RELEASE_APPROVAL_REQUIRED" in readiness["blockers"]


def test_red_lane_pr_with_valid_approval_is_ready():
    approval = {
        "state": "APPROVED",
        "repository": "DDD-Enterprises/dopemux-mvp",
        "pr_number": 704,
        "head_sha": HEAD_SHA,
        "approver": "trusted-approver",
        "approver_association": "COLLABORATOR",
        "approval_ref": "review-1",
        "approved_at": "2026-05-26T01:30:00Z",
    }
    readiness = _artifacts(
        _base_harvest(
            changed_files=[".github/workflows/x.yml"],
            security_release_approval=approval,
        ),
        known_reviewers_path=TRUSTED_FIXTURE,
    )
    assert readiness["security_release"]["required"] is True
    assert readiness["security_release"]["approved"] is True
    assert readiness["readiness"] == "READY"
    assert "SECURITY_RELEASE_APPROVAL_REQUIRED" not in readiness["blockers"]


def test_approval_does_not_override_other_blockers():
    approval = {
        "state": "APPROVED",
        "repository": "DDD-Enterprises/dopemux-mvp",
        "pr_number": 704,
        "head_sha": HEAD_SHA,
        "approver": "trusted-approver",
        "approver_association": "COLLABORATOR",
        "approval_ref": "review-1",
        "approved_at": "2026-05-26T01:30:00Z",
    }
    harvest = _base_harvest(
        changed_files=[".github/workflows/x.yml"],
        security_release_approval=approval,
    )
    harvest["checks"] = [
        {
            "name": "unit",
            "status": "COMPLETED",
            "conclusion": "failure",
            "headSha": HEAD_SHA,
            "required": True,
        }
    ]
    readiness = _artifacts(harvest, known_reviewers_path=TRUSTED_FIXTURE)
    assert readiness["security_release"]["approved"] is True
    assert readiness["readiness"] != "READY"
    assert "FAILED_CHECK" in readiness["blockers"]


def test_new_commit_invalidates_earlier_approval():
    approval = {
        "state": "APPROVED",
        "repository": "DDD-Enterprises/dopemux-mvp",
        "pr_number": 704,
        "head_sha": "stale0000000000000000000000000000000000",
        "approver": "trusted-approver",
        "approver_association": "COLLABORATOR",
        "approval_ref": "review-1",
        "approved_at": "2026-05-26T01:30:00Z",
    }
    readiness = _artifacts(
        _base_harvest(
            changed_files=[".github/workflows/x.yml"],
            security_release_approval=approval,
        ),
        known_reviewers_path=TRUSTED_FIXTURE,
    )
    assert readiness["security_release"]["approved"] is False
    assert "SECURITY_RELEASE_APPROVAL_HEAD_MISMATCH" in readiness["blockers"]


def test_unknown_approver_fails_closed():
    approval = {
        "state": "APPROVED",
        "repository": "DDD-Enterprises/dopemux-mvp",
        "pr_number": 704,
        "head_sha": HEAD_SHA,
        "approver": "random-user",
        "approval_ref": "review-1",
        "approved_at": "2026-05-26T01:30:00Z",
    }
    readiness = _artifacts(
        _base_harvest(
            changed_files=[".github/workflows/x.yml"],
            security_release_approval=approval,
        ),
        known_reviewers_path=TRUSTED_FIXTURE,
    )
    assert readiness["security_release"]["approved"] is False
    assert "SECURITY_RELEASE_APPROVER_UNKNOWN" in readiness["blockers"]


def test_empty_approver_roster_fails_closed_even_with_approval():
    approval = {
        "state": "APPROVED",
        "repository": "DDD-Enterprises/dopemux-mvp",
        "pr_number": 704,
        "head_sha": HEAD_SHA,
        "approver": "hu3mann",
        "approval_ref": "review-1",
        "approved_at": "2026-05-26T01:30:00Z",
    }
    readiness = _artifacts(
        _base_harvest(
            changed_files=[".github/workflows/x.yml"],
            security_release_approval=approval,
        ),
        known_reviewers_path=KNOWN_REVIEWERS_PATH,  # shipped roster is empty
    )
    assert readiness["security_release"]["approved"] is False
    assert "SECURITY_RELEASE_APPROVER_UNKNOWN" in readiness["blockers"]


def test_readiness_maps_security_release_blockers_to_needs_supervisor():
    readiness = _artifacts(_base_harvest(changed_files=["CODEOWNERS"]))
    assert readiness["readiness"] == "NEEDS_SUPERVISOR"
