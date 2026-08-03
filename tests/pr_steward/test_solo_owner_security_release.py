"""Unit tests for solo-owner security-release authorization."""

from __future__ import annotations

from tools.pr_steward.solo_owner_security_release import (
    RECEIPT_CODE,
    build_solo_owner_phrase,
    evaluate_solo_owner_security_release,
    harvest_solo_owner_authorization,
    parse_solo_owner_phrase,
    solo_owner_roster_eligible,
)

HEAD = "e41d134b5b0f32b5475ab5f094274bfac2259601"
REPO = "DDD-Enterprises/dopemux-mvp"
PR = 1128
AUTHOR = "hu3mann"


def _phrase(pr: int = PR, head: str = HEAD) -> str:
    return build_solo_owner_phrase(pr_number=pr, head_sha=head)


def _comment(
    body: str,
    *,
    login: str = AUTHOR,
    association: str = "OWNER",
    created: str = "2026-07-27T01:00:00Z",
    cid: str = "c1",
) -> dict:
    return {
        "id": cid,
        "body": body,
        "author": {"login": login},
        "authorAssociation": association,
        "createdAt": created,
    }


def _eval(**overrides):
    base = dict(
        required=True,
        trusted_approvers=[AUTHOR],
        pr_author=AUTHOR,
        pr_author_association="OWNER",
        expected_repo=REPO,
        expected_pr=PR,
        expected_head_sha=HEAD,
        issue_comments=[_comment(_phrase())],
        blockers=["SECURITY_RELEASE_APPROVAL_REQUIRED"],
        unclassified_review_item_count=0,
        audit_status="PASS_WITH_RISKS",
        audit_meta={
            "auditor_tool": "claude-code-cli",
            "auditor_model": "claude-sonnet-4.6",
            "auditor_provider": "local-signed-attestation",
            "auditor_runner": "supervisor-embedded-audit-session",
            "auditor_session": "TP-DMX-PR-STEWARD-SOLO-OWNER-BOOTSTRAP-001",
            "invocation": "test",
            "report_path": "proof/x/AUDITOR_REPORT.md",
        },
        proof_status="CURRENT",
    )
    base.update(overrides)
    return evaluate_solo_owner_security_release(**base)


def test_phrase_roundtrip():
    phrase = _phrase()
    assert parse_solo_owner_phrase(phrase) == (PR, HEAD)
    assert parse_solo_owner_phrase(f"prefix\n{phrase}\nsuffix") == (PR, HEAD)


def test_phrase_rejects_partial_sha():
    bad = f"AUTHORIZE SOLO-OWNER SECURITY RELEASE FOR PR #{PR} AT HEAD abc123"
    assert parse_solo_owner_phrase(bad) is None


def test_roster_eligible_only_for_single_author_approver():
    assert solo_owner_roster_eligible([AUTHOR], pr_author=AUTHOR) is True
    assert solo_owner_roster_eligible([AUTHOR, "other"], pr_author=AUTHOR) is False
    assert solo_owner_roster_eligible(["other"], pr_author=AUTHOR) is False
    assert solo_owner_roster_eligible([], pr_author=AUTHOR) is False


def test_activate_happy_path():
    result = _eval()
    assert result.activated is True
    assert result.receipt is not None
    assert result.receipt["receipt_code"] == RECEIPT_CODE
    assert result.receipt["does_not_count_as_github_approved_review"] is True
    assert result.receipt["auto_merge_enabled"] is False
    assert result.receipt["head_sha"] == HEAD
    assert result.receipt["pr_number"] == PR


def test_activate_with_member_association_org_repo():
    """Org-owned repos emit MEMBER for the sole trusted operator, not OWNER."""
    result = _eval(
        pr_author_association="MEMBER",
        issue_comments=[_comment(_phrase(), association="MEMBER")],
    )
    assert result.activated is True
    assert result.receipt is not None
    assert result.receipt["operator_association"] == "MEMBER"


def test_activate_with_collaborator_association_org_repo():
    """Steward harvest may report COLLABORATOR for the same org operator."""
    result = _eval(
        pr_author_association="COLLABORATOR",
        issue_comments=[_comment(_phrase(), association="COLLABORATOR")],
    )
    assert result.activated is True
    assert result.receipt is not None
    assert result.receipt["operator_association"] == "COLLABORATOR"


def test_activate_when_author_assoc_missing_but_comment_is_member():
    result = _eval(
        pr_author_association=None,
        issue_comments=[_comment(_phrase(), association="MEMBER")],
    )
    assert result.activated is True
    assert result.receipt is not None
    assert result.receipt["operator_association"] == "MEMBER"


def test_reject_contributor_association():
    result = _eval(
        pr_author_association="CONTRIBUTOR",
        issue_comments=[_comment(_phrase(), association="CONTRIBUTOR")],
    )
    assert result.activated is False
    assert "SOLO_OWNER_AUTHOR_ASSOCIATION_UNTRUSTED" in result.diagnostic_errors


def test_reject_none_comment_association_when_author_also_untrusted():
    result = _eval(
        pr_author_association=None,
        issue_comments=[_comment(_phrase(), association="NONE")],
    )
    assert result.activated is False
    assert (
        "SOLO_OWNER_PHRASE_OPERATOR_ASSOCIATION_UNTRUSTED" in result.diagnostic_errors
    )


def test_reject_untrusted_comment_even_if_author_is_member():
    result = _eval(
        pr_author_association="MEMBER",
        issue_comments=[_comment(_phrase(), association="CONTRIBUTOR")],
    )
    assert result.activated is False
    assert (
        "SOLO_OWNER_PHRASE_OPERATOR_ASSOCIATION_UNTRUSTED" in result.diagnostic_errors
    )


def test_cannot_activate_when_non_author_trusted_approver_exists():
    result = _eval(trusted_approvers=[AUTHOR, "second-human"])
    assert result.activated is False
    assert "SOLO_OWNER_INELIGIBLE_ROSTER" in result.diagnostic_errors


def test_cannot_activate_when_trusted_approver_is_not_author():
    result = _eval(trusted_approvers=["second-human"], pr_author=AUTHOR)
    assert result.activated is False
    assert "SOLO_OWNER_INELIGIBLE_ROSTER" in result.diagnostic_errors


def test_stale_head_phrase_rejected():
    other = "a" * 40
    result = _eval(issue_comments=[_comment(_phrase(head=other))])
    assert result.activated is False
    assert "SOLO_OWNER_PHRASE_MISSING_OR_MISMATCH" in result.diagnostic_errors


def test_wrong_pr_number_phrase_rejected():
    result = _eval(issue_comments=[_comment(_phrase(pr=9999))])
    assert result.activated is False
    assert "SOLO_OWNER_PHRASE_MISSING_OR_MISMATCH" in result.diagnostic_errors


def test_author_phrase_mismatch_rejected():
    result = _eval(
        issue_comments=[_comment(_phrase(), login="not-the-author", association="OWNER")]
    )
    assert result.activated is False
    assert "SOLO_OWNER_PHRASE_MISSING_OR_MISMATCH" in result.diagnostic_errors


def test_missing_phrase_rejected():
    result = _eval(issue_comments=[_comment("LGTM")])
    assert result.activated is False
    assert "SOLO_OWNER_PHRASE_MISSING_OR_MISMATCH" in result.diagnostic_errors


def test_failed_audit_blocks_activation():
    result = _eval(audit_status="FAIL")
    assert result.activated is False
    assert "SOLO_OWNER_AUDIT_NOT_PASSING" in result.diagnostic_errors


def test_stale_proof_blocks_activation():
    result = _eval(proof_status="STALE")
    assert result.activated is False
    assert "SOLO_OWNER_PROOF_NOT_CURRENT" in result.diagnostic_errors


def test_failed_check_blocks_activation():
    result = _eval(
        blockers=["SECURITY_RELEASE_APPROVAL_REQUIRED", "FAILED_CHECK"]
    )
    assert result.activated is False
    assert "SOLO_OWNER_OTHER_GATES_BLOCKING" in result.diagnostic_errors


def test_unresolved_thread_blocks_activation():
    result = _eval(
        blockers=["SECURITY_RELEASE_APPROVAL_REQUIRED", "UNRESOLVED_REVIEW_THREAD"]
    )
    assert result.activated is False
    assert "SOLO_OWNER_OTHER_GATES_BLOCKING" in result.diagnostic_errors


def test_unknown_reviewer_blocks_activation():
    result = _eval(
        blockers=[
            "SECURITY_RELEASE_APPROVAL_REQUIRED",
            "UNKNOWN_REVIEWER_NEEDS_CLASSIFICATION",
        ]
    )
    assert result.activated is False
    assert "SOLO_OWNER_OTHER_GATES_BLOCKING" in result.diagnostic_errors


def test_unclassified_items_block_activation():
    result = _eval(unclassified_review_item_count=1)
    assert result.activated is False
    assert "SOLO_OWNER_UNCLASSIFIED_REVIEW_ITEMS" in result.diagnostic_errors


def test_not_required_does_not_activate():
    result = _eval(required=False)
    assert result.activated is False


def test_harvest_picks_newest_matching_phrase():
    comments = [
        _comment(_phrase(), created="2026-07-27T01:00:00Z", cid="old"),
        _comment(_phrase(), created="2026-07-27T02:00:00Z", cid="new"),
        _comment(_phrase(head="b" * 40), created="2026-07-27T03:00:00Z", cid="stale"),
    ]
    auth = harvest_solo_owner_authorization(
        comments,
        expected_pr=PR,
        expected_head_sha=HEAD,
        expected_operator=AUTHOR,
    )
    assert auth is not None
    assert auth["authorization_ref"] == "new"
