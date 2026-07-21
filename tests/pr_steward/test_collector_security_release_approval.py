from __future__ import annotations

from tools.pr_steward.collector import _select_security_release_approval


def _review(**overrides):
    base = {
        "id": "R_1",
        "state": "APPROVED",
        "author": {"login": "trusted-approver"},
        "authorAssociation": "COLLABORATOR",
        "submittedAt": "2026-07-20T10:00:00Z",
        "commit": {"oid": "a" * 40},
    }
    base.update(overrides)
    return base


def test_no_reviews_returns_none():
    assert _select_security_release_approval([], repo="o/r", pr_number=1) is None


def test_single_approved_review_is_selected():
    result = _select_security_release_approval(
        [_review()], repo="owner/repo", pr_number=42
    )
    assert result is not None
    assert result["state"] == "APPROVED"
    assert result["approver"] == "trusted-approver"
    assert result["head_sha"] == "a" * 40
    assert result["approval_ref"] == "R_1"
    assert result["repository"] == "owner/repo"
    assert result["pr_number"] == 42
    assert result["approved_at"] == "2026-07-20T10:00:00Z"


def test_most_recent_approved_review_wins():
    older = _review(id="R_1", submittedAt="2026-07-20T09:00:00Z")
    newer = _review(id="R_2", submittedAt="2026-07-20T11:00:00Z")
    result = _select_security_release_approval([older, newer], repo="o/r", pr_number=1)
    assert result["approval_ref"] == "R_2"


def test_changes_requested_after_approval_is_not_selected_as_approved():
    approved = _review(id="R_1", state="APPROVED", submittedAt="2026-07-20T09:00:00Z")
    later_changes = _review(
        id="R_2", state="CHANGES_REQUESTED", author={"login": "trusted-approver"},
        submittedAt="2026-07-20T11:00:00Z",
    )
    result = _select_security_release_approval([approved, later_changes], repo="o/r", pr_number=1)
    assert result is None


def test_review_without_commit_oid_is_skipped():
    result = _select_security_release_approval(
        [_review(commit=None)], repo="o/r", pr_number=1
    )
    assert result is None
