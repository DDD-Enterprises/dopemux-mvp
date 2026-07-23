from __future__ import annotations

from tools.pr_steward.security_release_approval import evaluate_security_release_approval


HEAD = "a" * 40
REPO = "DDD-Enterprises/dopemux-mvp"
PR = 1234


def _approval(**overrides):
    base = {
        "state": "APPROVED",
        "repository": REPO,
        "pr_number": PR,
        "head_sha": HEAD,
        "approver": "trusted-approver",
        "approver_association": "MEMBER",
        "approval_ref": "review-node-id-123",
        "approved_at": "2026-07-20T10:00:00Z",
    }
    base.update(overrides)
    return base


def test_not_required_returns_no_errors_even_without_approval():
    errors = evaluate_security_release_approval(
        None,
        required=False,
        expected_repo=REPO,
        expected_pr=PR,
        expected_head_sha=HEAD,
        trusted_approvers=[],
    )
    assert errors == []


def test_required_with_no_approval_is_required_error():
    errors = evaluate_security_release_approval(
        None,
        required=True,
        expected_repo=REPO,
        expected_pr=PR,
        expected_head_sha=HEAD,
        trusted_approvers=["trusted-approver"],
    )
    assert errors == ["SECURITY_RELEASE_APPROVAL_REQUIRED"]


def test_required_with_empty_trusted_approvers_is_approver_unknown():
    errors = evaluate_security_release_approval(
        _approval(),
        required=True,
        expected_repo=REPO,
        expected_pr=PR,
        expected_head_sha=HEAD,
        trusted_approvers=[],
    )
    assert "SECURITY_RELEASE_APPROVER_UNKNOWN" in errors


def test_valid_approval_at_exact_head_has_no_errors():
    errors = evaluate_security_release_approval(
        _approval(),
        required=True,
        expected_repo=REPO,
        expected_pr=PR,
        expected_head_sha=HEAD,
        trusted_approvers=["trusted-approver"],
    )
    assert errors == []


def test_wrong_repo_is_rejected():
    errors = evaluate_security_release_approval(
        _approval(repository="someone-else/other-repo"),
        required=True,
        expected_repo=REPO,
        expected_pr=PR,
        expected_head_sha=HEAD,
        trusted_approvers=["trusted-approver"],
    )
    assert "SECURITY_RELEASE_APPROVAL_INVALID" in errors


def test_wrong_pr_is_rejected():
    errors = evaluate_security_release_approval(
        _approval(pr_number=9999),
        required=True,
        expected_repo=REPO,
        expected_pr=PR,
        expected_head_sha=HEAD,
        trusted_approvers=["trusted-approver"],
    )
    assert "SECURITY_RELEASE_APPROVAL_INVALID" in errors


def test_wrong_head_is_head_mismatch():
    errors = evaluate_security_release_approval(
        _approval(head_sha="b" * 40),
        required=True,
        expected_repo=REPO,
        expected_pr=PR,
        expected_head_sha=HEAD,
        trusted_approvers=["trusted-approver"],
    )
    assert "SECURITY_RELEASE_APPROVAL_HEAD_MISMATCH" in errors


def test_future_dated_approval_is_stale():
    errors = evaluate_security_release_approval(
        _approval(approved_at="2099-01-01T00:00:00Z"),
        required=True,
        expected_repo=REPO,
        expected_pr=PR,
        expected_head_sha=HEAD,
        trusted_approvers=["trusted-approver"],
    )
    assert "SECURITY_RELEASE_APPROVAL_STALE" in errors


def test_unparseable_timestamp_is_invalid():
    errors = evaluate_security_release_approval(
        _approval(approved_at="not-a-timestamp"),
        required=True,
        expected_repo=REPO,
        expected_pr=PR,
        expected_head_sha=HEAD,
        trusted_approvers=["trusted-approver"],
    )
    assert "SECURITY_RELEASE_APPROVAL_INVALID" in errors


def test_non_approved_state_is_invalid():
    errors = evaluate_security_release_approval(
        _approval(state="CHANGES_REQUESTED"),
        required=True,
        expected_repo=REPO,
        expected_pr=PR,
        expected_head_sha=HEAD,
        trusted_approvers=["trusted-approver"],
    )
    assert "SECURITY_RELEASE_APPROVAL_INVALID" in errors


def test_unknown_approver_is_approver_unknown():
    errors = evaluate_security_release_approval(
        _approval(approver="random-user"),
        required=True,
        expected_repo=REPO,
        expected_pr=PR,
        expected_head_sha=HEAD,
        trusted_approvers=["trusted-approver"],
    )
    assert "SECURITY_RELEASE_APPROVER_UNKNOWN" in errors


def test_untrusted_association_is_approver_unknown_even_if_login_trusted():
    errors = evaluate_security_release_approval(
        _approval(approver_association="NONE"),
        required=True,
        expected_repo=REPO,
        expected_pr=PR,
        expected_head_sha=HEAD,
        trusted_approvers=["trusted-approver"],
    )
    assert "SECURITY_RELEASE_APPROVER_UNKNOWN" in errors


def test_missing_association_is_approver_unknown():
    errors = evaluate_security_release_approval(
        _approval(approver_association=None),
        required=True,
        expected_repo=REPO,
        expected_pr=PR,
        expected_head_sha=HEAD,
        trusted_approvers=["trusted-approver"],
    )
    assert "SECURITY_RELEASE_APPROVER_UNKNOWN" in errors


def test_empty_approval_ref_is_invalid():
    errors = evaluate_security_release_approval(
        _approval(approval_ref=""),
        required=True,
        expected_repo=REPO,
        expected_pr=PR,
        expected_head_sha=HEAD,
        trusted_approvers=["trusted-approver"],
    )
    assert "SECURITY_RELEASE_APPROVAL_INVALID" in errors


def test_non_boolean_truthy_state_does_not_bypass():
    # integer 1 / string "true" must not be treated as APPROVED via loose equality
    errors = evaluate_security_release_approval(
        _approval(state=1),
        required=True,
        expected_repo=REPO,
        expected_pr=PR,
        expected_head_sha=HEAD,
        trusted_approvers=["trusted-approver"],
    )
    assert "SECURITY_RELEASE_APPROVAL_INVALID" in errors


def test_malformed_payload_is_invalid():
    errors = evaluate_security_release_approval(
        "not-a-dict",  # type: ignore[arg-type]
        required=True,
        expected_repo=REPO,
        expected_pr=PR,
        expected_head_sha=HEAD,
        trusted_approvers=["trusted-approver"],
    )
    assert errors == ["SECURITY_RELEASE_APPROVAL_INVALID"]
