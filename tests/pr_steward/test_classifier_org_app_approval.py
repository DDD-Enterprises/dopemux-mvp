"""Classifier integration for org-owned GitHub App security-release approvals."""

from __future__ import annotations

import json
from pathlib import Path

from tools.pr_steward.classifier import build_artifacts

HEAD = "ba8a78fa1ed09dc0d7cbb9f2b2680508c6fa13a3"
PR = 1126
REPO = "DDD-Enterprises/dopemux-mvp"
APP = "ddd-release-gate[bot]"


def _known(tmp_path: Path) -> Path:
    path = tmp_path / "known_reviewers.json"
    path.write_text(
        json.dumps(
            {
                "known_reviewers": ["hu3mann", APP],
                "trusted_author_associations": ["OWNER", "MEMBER", "COLLABORATOR"],
                "trusted_security_release_approvers": ["hu3mann"],
                "trusted_security_release_apps": [
                    {
                        "login": APP,
                        "owner": "DDD-Enterprises",
                        "installation_scope": REPO,
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _harvest(security_release_approval=None, checks=None) -> dict:
    return {
        "harvest_complete": True,
        "harvest_errors": [],
        "pr": {
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
            "headRefOid": HEAD,
            "author": {"login": "hu3mann", "authorAssociation": "OWNER"},
            "authorAssociation": "OWNER",
            "createdAt": "2026-07-26T01:00:00Z",
            "updatedAt": "2026-07-26T02:00:00Z",
        },
        "changed_files": [
            {"path": "schemas/mcp/fleet-catalog.schema.json", "additions": 1}
        ],
        "commits": [{"oid": HEAD, "messageHeadline": "test"}],
        "reviews": [],
        "review_comments": [],
        "review_threads": [],
        "issue_comments": [],
        "checks": checks
        or [
            {
                "name": "unit",
                "status": "COMPLETED",
                "conclusion": "success",
                "headSha": HEAD,
            }
        ],
        "proof": {
            "proof_path": "proof/PROOF.json",
            "proof_head_sha": HEAD,
            "matches_pr_head": True,
        },
        "embedded_audit": {
            "status": "PASS_WITH_RISKS",
            "report_path": "proof/AUDITOR_REPORT.md",
            "auditor_tool": "claude-code-cli",
            "auditor_model": "claude-sonnet-4.6",
        },
        "security_release_approval": security_release_approval,
    }


def _readiness(harvest: dict, known: Path) -> dict:
    return build_artifacts(
        harvest,
        repo=REPO,
        pr_number=PR,
        strict=True,
        allow_closed=False,
        known_reviewers_path=known,
    )["MERGE_READINESS.json"]


def test_org_app_exact_head_approval_ready(tmp_path: Path):
    known = _known(tmp_path)
    approval = {
        "state": "APPROVED",
        "repository": REPO,
        "pr_number": PR,
        "head_sha": HEAD,
        "approver": APP,
        "approver_association": "NONE",
        "approval_ref": "app-review-1",
        "approved_at": "2026-07-20T12:00:00Z",
    }
    readiness = _readiness(_harvest(security_release_approval=approval), known)
    assert readiness["security_release"]["required"] is True
    assert readiness["security_release"]["approved"] is True
    assert readiness["security_release"]["approval_kind"] == "github_app"
    assert "SECURITY_RELEASE_APPROVAL_REQUIRED" not in readiness["blockers"]
    assert readiness["readiness"] == "READY"


def test_org_app_does_not_waive_failed_ci(tmp_path: Path):
    known = _known(tmp_path)
    approval = {
        "state": "APPROVED",
        "repository": REPO,
        "pr_number": PR,
        "head_sha": HEAD,
        "approver": APP,
        "approver_association": "NONE",
        "approval_ref": "app-review-1",
        "approved_at": "2026-07-20T12:00:00Z",
    }
    harvest = _harvest(
        security_release_approval=approval,
        checks=[
            {
                "name": "unit",
                "status": "COMPLETED",
                "conclusion": "failure",
                "headSha": HEAD,
                "required": True,
            }
        ],
    )
    readiness = _readiness(harvest, known)
    assert "FAILED_CHECK" in readiness["blockers"]
    assert readiness["security_release"]["approved"] is False
    assert readiness["readiness"] != "READY"
