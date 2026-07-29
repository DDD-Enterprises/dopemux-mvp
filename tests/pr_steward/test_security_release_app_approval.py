"""Tests for organization-owned GitHub App security-release approvals."""

from __future__ import annotations

from tools.pr_steward.security_release_approval import (
    compute_app_gate_ok,
    evaluate_security_release_approval,
    load_trusted_security_apps,
)

HEAD = "ba8a78fa1ed09dc0d7cbb9f2b2680508c6fa13a3"
REPO = "DDD-Enterprises/dopemux-mvp"
PR = 1126
APP = "ddd-release-gate[bot]"
APPS = [
    {
        "login": APP,
        "owner": "DDD-Enterprises",
        "installation_scope": "DDD-Enterprises/dopemux-mvp",
    }
]


def _app_approval(**overrides):
    base = {
        "state": "APPROVED",
        "repository": REPO,
        "pr_number": PR,
        "head_sha": HEAD,
        "approver": APP,
        "approver_association": "NONE",
        "approval_ref": "app-review-1",
        "approved_at": "2026-07-20T10:00:00Z",
    }
    base.update(overrides)
    return base


def _human_approval(**overrides):
    base = {
        "state": "APPROVED",
        "repository": REPO,
        "pr_number": PR,
        "head_sha": HEAD,
        "approver": "trusted-human",
        "approver_association": "MEMBER",
        "approval_ref": "human-review-1",
        "approved_at": "2026-07-20T10:00:00Z",
    }
    base.update(overrides)
    return base


def test_load_trusted_security_apps():
    apps = load_trusted_security_apps(
        {"trusted_security_release_apps": APPS, "trusted_security_release_approvers": []}
    )
    assert apps[0]["login"] == APP
    assert apps[0]["owner"] == "DDD-Enterprises"


def test_app_approval_accepted_when_gates_ok():
    errors = evaluate_security_release_approval(
        _app_approval(),
        required=True,
        expected_repo=REPO,
        expected_pr=PR,
        expected_head_sha=HEAD,
        trusted_approvers=["hu3mann"],
        trusted_apps=APPS,
        app_gate_ok=True,
    )
    assert errors == []


def test_app_approval_rejected_when_gates_not_met():
    errors = evaluate_security_release_approval(
        _app_approval(),
        required=True,
        expected_repo=REPO,
        expected_pr=PR,
        expected_head_sha=HEAD,
        trusted_approvers=["hu3mann"],
        trusted_apps=APPS,
        app_gate_ok=False,
    )
    assert "SECURITY_RELEASE_APP_GATES_NOT_MET" in errors


def test_github_actions_bot_forbidden_even_if_listed():
    apps = [
        {
            "login": "github-actions[bot]",
            "owner": "DDD-Enterprises",
            "installation_scope": REPO,
        }
    ]
    errors = evaluate_security_release_approval(
        _app_approval(approver="github-actions[bot]"),
        required=True,
        expected_repo=REPO,
        expected_pr=PR,
        expected_head_sha=HEAD,
        trusted_approvers=[],
        trusted_apps=apps,
        app_gate_ok=True,
    )
    assert "SECURITY_RELEASE_APP_FORBIDDEN" in errors


def test_unknown_app_rejected():
    errors = evaluate_security_release_approval(
        _app_approval(approver="random-bot[bot]"),
        required=True,
        expected_repo=REPO,
        expected_pr=PR,
        expected_head_sha=HEAD,
        trusted_approvers=[],
        trusted_apps=APPS,
        app_gate_ok=True,
    )
    assert "SECURITY_RELEASE_APP_UNKNOWN" in errors


def test_app_stale_head_rejected():
    errors = evaluate_security_release_approval(
        _app_approval(head_sha="a" * 40),
        required=True,
        expected_repo=REPO,
        expected_pr=PR,
        expected_head_sha=HEAD,
        trusted_approvers=[],
        trusted_apps=APPS,
        app_gate_ok=True,
    )
    assert "SECURITY_RELEASE_APPROVAL_HEAD_MISMATCH" in errors


def test_human_path_unchanged():
    errors = evaluate_security_release_approval(
        _human_approval(),
        required=True,
        expected_repo=REPO,
        expected_pr=PR,
        expected_head_sha=HEAD,
        trusted_approvers=["trusted-human"],
        trusted_apps=APPS,
        app_gate_ok=False,
    )
    assert errors == []


def test_compute_app_gate_ok_positive():
    assert (
        compute_app_gate_ok(
            audit_status="PASS_WITH_RISKS",
            proof_status="CURRENT",
            blockers=["SECURITY_RELEASE_APPROVAL_REQUIRED"],
            unclassified_review_item_count=0,
        )
        is True
    )


def test_compute_app_gate_ok_blocks_failed_ci():
    assert (
        compute_app_gate_ok(
            audit_status="PASS",
            proof_status="CURRENT",
            blockers=["FAILED_CHECK", "SECURITY_RELEASE_APPROVAL_REQUIRED"],
            unclassified_review_item_count=0,
        )
        is False
    )


def test_scope_mismatch():
    apps = [
        {
            "login": APP,
            "owner": "DDD-Enterprises",
            "installation_scope": "DDD-Enterprises/other-repo",
        }
    ]
    errors = evaluate_security_release_approval(
        _app_approval(),
        required=True,
        expected_repo=REPO,
        expected_pr=PR,
        expected_head_sha=HEAD,
        trusted_approvers=[],
        trusted_apps=apps,
        app_gate_ok=True,
    )
    assert "SECURITY_RELEASE_APP_UNKNOWN" in errors or "SECURITY_RELEASE_APP_SCOPE_MISMATCH" in errors
