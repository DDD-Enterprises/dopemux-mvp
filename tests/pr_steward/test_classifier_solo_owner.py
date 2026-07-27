"""Classifier integration for solo-owner security-release override."""

from __future__ import annotations

from pathlib import Path

from tools.pr_steward.classifier import build_artifacts
from tools.pr_steward.solo_owner_security_release import (
    RECEIPT_CODE,
    build_solo_owner_phrase,
)

HEAD_SHA = "e41d134b5b0f32b5475ab5f094274bfac2259601"
PR = 1128
REPO = "DDD-Enterprises/dopemux-mvp"


def _known_reviewers(tmp_path: Path, approvers: list[str]) -> Path:
    path = tmp_path / "known_reviewers.json"
    import json

    path.write_text(
        json.dumps(
            {
                "known_reviewers": ["hu3mann", *approvers],
                "trusted_author_associations": ["OWNER", "MEMBER", "COLLABORATOR"],
                "trusted_security_release_approvers": approvers,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _harvest(
    *,
    issue_comments=None,
    security_release_approval=None,
    checks=None,
    audit_status="PASS_WITH_RISKS",
    author_association=None,
) -> dict:
    pr = {
        "number": PR,
        "url": f"https://github.com/{REPO}/pull/{PR}",
        "state": "OPEN",
        "isDraft": False,
        "mergeable": "MERGEABLE",
        "mergeStateStatus": "CLEAN",
        "reviewDecision": None,
        "baseRefName": "main",
        "baseRefOid": "base000000000000000000000000000000000000",
        "headRefName": "feat/test",
        "headRefOid": HEAD_SHA,
        "author": {"login": "hu3mann"},
        "createdAt": "2026-07-26T01:00:00Z",
        "updatedAt": "2026-07-26T02:00:00Z",
    }
    if author_association:
        pr["authorAssociation"] = author_association
        pr["author"] = {"login": "hu3mann", "authorAssociation": author_association}
    return {
        "harvest_complete": True,
        "harvest_errors": [],
        "pr": pr,
        "changed_files": [
            {"path": "schemas/mcp/fleet-catalog.schema.json", "additions": 1}
        ],
        "commits": [{"oid": HEAD_SHA, "messageHeadline": "test"}],
        "reviews": [],
        "review_comments": [],
        "review_threads": [],
        "issue_comments": issue_comments or [],
        "checks": checks
        or [
            {
                "name": "unit",
                "status": "COMPLETED",
                "conclusion": "success",
                "headSha": HEAD_SHA,
            }
        ],
        "proof": {
            "proof_path": "proof/PROOF.json",
            "proof_head_sha": HEAD_SHA,
            "matches_pr_head": True,
        },
        "embedded_audit": {
            "status": audit_status,
            "report_path": "proof/AUDITOR_REPORT.md",
            "auditor_tool": "claude-code-cli",
            "auditor_model": "claude-sonnet-4.6",
            "auditor_provider": "local-signed-attestation",
            "auditor_runner": "supervisor-session",
            "auditor_session": "bootstrap-001",
            "invocation": "test-audit",
        },
        "security_release_approval": security_release_approval,
    }


def _readiness(harvest: dict, known_path: Path) -> dict:
    return build_artifacts(
        harvest,
        repo=REPO,
        pr_number=PR,
        strict=True,
        allow_closed=False,
        known_reviewers_path=known_path,
    )["MERGE_READINESS.json"]


def test_solo_owner_phrase_clears_security_gate(tmp_path: Path):
    known = _known_reviewers(tmp_path, ["hu3mann"])
    phrase = build_solo_owner_phrase(pr_number=PR, head_sha=HEAD_SHA)
    harvest = _harvest(
        issue_comments=[
            {
                "id": "ic-auth",
                "body": phrase,
                "author": {"login": "hu3mann"},
                "authorAssociation": "OWNER",
                "createdAt": "2026-07-27T12:00:00Z",
            }
        ],
        author_association="OWNER",
    )
    readiness = _readiness(harvest, known)
    assert readiness["security_release"]["required"] is True
    assert readiness["security_release"]["approved"] is True
    assert readiness["security_release"]["solo_owner_override"]["receipt_code"] == RECEIPT_CODE
    assert readiness["security_release"]["approval"] is None
    assert "SECURITY_RELEASE_APPROVAL_REQUIRED" not in readiness["blockers"]
    assert readiness["readiness"] == "READY"


def test_solo_owner_does_not_activate_with_second_trusted_approver(tmp_path: Path):
    known = _known_reviewers(tmp_path, ["hu3mann", "second-human"])
    phrase = build_solo_owner_phrase(pr_number=PR, head_sha=HEAD_SHA)
    harvest = _harvest(
        issue_comments=[
            {
                "id": "ic-auth",
                "body": phrase,
                "author": {"login": "hu3mann"},
                "authorAssociation": "OWNER",
                "createdAt": "2026-07-27T12:00:00Z",
            }
        ],
        author_association="OWNER",
    )
    readiness = _readiness(harvest, known)
    assert readiness["security_release"]["approved"] is False
    assert readiness["security_release"]["solo_owner_override"] is None
    assert "SECURITY_RELEASE_APPROVAL_REQUIRED" in readiness["blockers"]
    assert readiness["readiness"] != "READY"


def test_ordinary_non_author_approval_still_works(tmp_path: Path):
    known = _known_reviewers(tmp_path, ["trusted-approver"])
    approval = {
        "state": "APPROVED",
        "repository": REPO,
        "pr_number": PR,
        "head_sha": HEAD_SHA,
        "approver": "trusted-approver",
        "approver_association": "COLLABORATOR",
        "approval_ref": "review-1",
        "approved_at": "2026-07-20T12:00:00Z",
    }
    readiness = _readiness(
        _harvest(security_release_approval=approval),
        known,
    )
    assert readiness["security_release"]["approved"] is True
    assert readiness["security_release"]["solo_owner_override"] is None
    assert readiness["security_release"]["approval"]["approver"] == "trusted-approver"
    assert readiness["readiness"] == "READY"


def test_solo_owner_does_not_waive_failed_ci(tmp_path: Path):
    known = _known_reviewers(tmp_path, ["hu3mann"])
    phrase = build_solo_owner_phrase(pr_number=PR, head_sha=HEAD_SHA)
    harvest = _harvest(
        issue_comments=[
            {
                "id": "ic-auth",
                "body": phrase,
                "author": {"login": "hu3mann"},
                "authorAssociation": "OWNER",
                "createdAt": "2026-07-27T12:00:00Z",
            }
        ],
        author_association="OWNER",
        checks=[
            {
                "name": "unit",
                "status": "COMPLETED",
                "conclusion": "failure",
                "headSha": HEAD_SHA,
                "required": True,
            }
        ],
    )
    readiness = _readiness(harvest, known)
    # Solo cannot activate while FAILED_CHECK is present.
    assert "FAILED_CHECK" in readiness["blockers"]
    assert readiness["security_release"]["solo_owner_override"] is None
    assert readiness["readiness"] != "READY"


def test_stale_head_phrase_does_not_approve(tmp_path: Path):
    known = _known_reviewers(tmp_path, ["hu3mann"])
    stale = build_solo_owner_phrase(pr_number=PR, head_sha="a" * 40)
    harvest = _harvest(
        issue_comments=[
            {
                "id": "ic-auth",
                "body": stale,
                "author": {"login": "hu3mann"},
                "authorAssociation": "OWNER",
                "createdAt": "2026-07-27T12:00:00Z",
            }
        ],
        author_association="OWNER",
    )
    readiness = _readiness(harvest, known)
    assert readiness["security_release"]["approved"] is False
    assert "SECURITY_RELEASE_APPROVAL_REQUIRED" in readiness["blockers"]
