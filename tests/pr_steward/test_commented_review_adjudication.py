"""TP-DMX-PR-STEWARD-COMMENTED-REVIEW-ADJUDICATION-001.

A trusted security-release approver may post a top-level issue comment
formatted as a PR_STEWARD_REVIEW_ADJUDICATION_V1 receipt to reclassify one
exact COMMENTED review, at one exact PR head, as REJECTED_WITH_REASON /
nonblocking. Every other review state (CHANGES_REQUESTED above all),
unresolved threads, CI, audit, and security-release blockers are untouched.
"""

from __future__ import annotations

from pathlib import Path

from tools.pr_steward.classifier import build_artifacts

REPO = "DDD-Enterprises/dopemux-mvp"
PR_NUMBER = 1287
HEAD_SHA = "b69bf6cb1e47e8db9d071c5548d14462c0092a31"
OTHER_HEAD_SHA = "0123456789abcdef0123456789abcdef01234567"
REVIEW_ID = "PRR_kwDOPyIw988AAAABLPwIjQ"
TRUSTED_APPROVER = "hu3mann"
UNTRUSTED_APPROVER = "copilot-pull-request-reviewer"
ROOT = Path(__file__).resolve().parents[2]
REAL_KNOWN_REVIEWERS_PATH = ROOT / "tools" / "pr_steward" / "known_reviewers.json"


def _receipt_body(
    *,
    review_id: str = REVIEW_ID,
    head_sha: str = HEAD_SHA,
    disposition: str = "REJECTED_WITH_REASON",
    reason: str = "Historical P2 finding already resolved by later commits.",
) -> str:
    return (
        "PR_STEWARD_REVIEW_ADJUDICATION_V1\n"
        f"review_id={review_id}\n"
        f"head_sha={head_sha}\n"
        f"disposition={disposition}\n"
        f"reason={reason}\n"
    )


def _base_harvest(
    *,
    review_state: str = "COMMENTED",
    review_body: str = "P2: flagging this for follow-up before merge.",
    reviews: list[dict] | None = None,
    issue_comments: list[dict] | None = None,
) -> dict:
    if reviews is None:
        reviews = [
            {
                "id": REVIEW_ID,
                "state": review_state,
                "body": review_body,
                "author": {"login": "chatgpt-codex-connector"},
                "authorAssociation": None,
                "submittedAt": "2026-08-28T09:15:45Z",
                "commit": {"oid": "08395a7d17c2f66bf34794e6d01ea6b91074ecef"},
            }
        ]
    return {
        "harvest_complete": True,
        "harvest_errors": [],
        "pr": {
            "number": PR_NUMBER,
            "url": f"https://github.com/{REPO}/pull/{PR_NUMBER}",
            "state": "OPEN",
            "isDraft": True,
            "mergeable": "MERGEABLE",
            "mergeStateStatus": "BLOCKED",
            "reviewDecision": "COMMENTED",
            "baseRefName": "main",
            "baseRefOid": "base000000000000000000000000000000000000",
            "headRefName": "codex/pr-steward-followup",
            "headRefOid": HEAD_SHA,
            "author": {"login": "hu3mann", "authorAssociation": "OWNER"},
            "createdAt": "2026-08-20T01:00:00Z",
            "updatedAt": "2026-09-01T02:00:00Z",
        },
        "changed_files": [{"path": "tools/pr_steward/intake.py", "additions": 1}],
        "commits": [{"oid": HEAD_SHA, "messageHeadline": "test"}],
        "reviews": reviews,
        "review_comments": [],
        "review_threads": [],
        "issue_comments": issue_comments or [],
        "checks": [
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
            "status": "PASS",
            "report_path": "proof/AUDITOR_REPORT.md",
        },
    }


def _artifacts(
    harvest: dict, known_reviewers_path: Path = REAL_KNOWN_REVIEWERS_PATH
) -> dict:
    return build_artifacts(
        harvest,
        repo=REPO,
        pr_number=PR_NUMBER,
        strict=True,
        allow_closed=True,
        known_reviewers_path=known_reviewers_path,
    )


def _review_item(ledger: dict, item_id: str = REVIEW_ID) -> dict:
    matches = [item for item in ledger["items"] if item["id"] == item_id]
    assert len(matches) == 1, f"expected exactly one ledger item for {item_id}"
    return matches[0]


class TestNoReceipt:
    def test_commented_p2_review_with_no_receipt_is_must_fix(self) -> None:
        harvest = _base_harvest()
        artifacts = _artifacts(harvest)
        item = _review_item(artifacts["REVIEW_ITEM_LEDGER.json"])
        assert item["disposition"] == "MUST_FIX"
        assert item["blocking"] is True
        assert "REVIEW_ITEM_MUST_FIX" in artifacts["MERGE_READINESS.json"]["blockers"]


class TestValidReceipt:
    def test_valid_trusted_exact_head_receipt_clears_the_review(self) -> None:
        harvest = _base_harvest(
            issue_comments=[
                {
                    "id": "ic-1",
                    "body": _receipt_body(),
                    "author": {"login": TRUSTED_APPROVER},
                    "authorAssociation": "OWNER",
                }
            ]
        )
        artifacts = _artifacts(harvest)
        ledger = artifacts["REVIEW_ITEM_LEDGER.json"]
        item = _review_item(ledger, REVIEW_ID)
        # Original review preserved: same id, unchanged body.
        assert item["body"] == "P2: flagging this for follow-up before merge."
        assert item["disposition"] == "REJECTED_WITH_REASON"
        assert item["blocking"] is False
        assert (
            "REVIEW_ITEM_MUST_FIX" not in artifacts["MERGE_READINESS.json"]["blockers"]
        )


class TestWrongHead:
    def test_receipt_bound_to_stale_head_does_not_clear(self) -> None:
        harvest = _base_harvest(
            issue_comments=[
                {
                    "id": "ic-1",
                    "body": _receipt_body(head_sha=OTHER_HEAD_SHA),
                    "author": {"login": TRUSTED_APPROVER},
                }
            ]
        )
        artifacts = _artifacts(harvest)
        item = _review_item(artifacts["REVIEW_ITEM_LEDGER.json"])
        assert item["disposition"] == "MUST_FIX"
        assert item["blocking"] is True


class TestWrongReviewId:
    def test_receipt_for_a_different_review_does_not_clear(self) -> None:
        harvest = _base_harvest(
            issue_comments=[
                {
                    "id": "ic-1",
                    "body": _receipt_body(review_id="PRR_someOtherReviewNodeId"),
                    "author": {"login": TRUSTED_APPROVER},
                }
            ]
        )
        artifacts = _artifacts(harvest)
        item = _review_item(artifacts["REVIEW_ITEM_LEDGER.json"])
        assert item["disposition"] == "MUST_FIX"
        assert item["blocking"] is True


class TestUntrustedAuthor:
    def test_receipt_from_untrusted_author_does_not_clear(self) -> None:
        harvest = _base_harvest(
            issue_comments=[
                {
                    "id": "ic-1",
                    "body": _receipt_body(),
                    "author": {"login": UNTRUSTED_APPROVER},
                }
            ]
        )
        artifacts = _artifacts(harvest)
        item = _review_item(artifacts["REVIEW_ITEM_LEDGER.json"])
        assert item["disposition"] == "MUST_FIX"
        assert item["blocking"] is True


class TestMalformedReceipt:
    def test_malformed_receipt_does_not_clear(self) -> None:
        malformed = (
            "PR_STEWARD_REVIEW_ADJUDICATION_V1\n"
            f"review_id={REVIEW_ID}\n"
            f"head_sha={HEAD_SHA}\n"
            "disposition=REJECTED_WITH_REASON\n"
            # reason= line omitted entirely -> malformed
        )
        harvest = _base_harvest(
            issue_comments=[
                {"id": "ic-1", "body": malformed, "author": {"login": TRUSTED_APPROVER}}
            ]
        )
        artifacts = _artifacts(harvest)
        item = _review_item(artifacts["REVIEW_ITEM_LEDGER.json"])
        assert item["disposition"] == "MUST_FIX"
        assert item["blocking"] is True

    def test_short_head_sha_does_not_clear(self) -> None:
        malformed = _receipt_body(head_sha="b69bf6c")
        harvest = _base_harvest(
            issue_comments=[
                {"id": "ic-1", "body": malformed, "author": {"login": TRUSTED_APPROVER}}
            ]
        )
        artifacts = _artifacts(harvest)
        item = _review_item(artifacts["REVIEW_ITEM_LEDGER.json"])
        assert item["disposition"] == "MUST_FIX"
        assert item["blocking"] is True


class TestConflictingReceipts:
    def test_two_conflicting_eligible_receipts_do_not_clear(self) -> None:
        harvest = _base_harvest(
            issue_comments=[
                {
                    "id": "ic-1",
                    "body": _receipt_body(reason="First adjudication reason."),
                    "author": {"login": TRUSTED_APPROVER},
                },
                {
                    "id": "ic-2",
                    "body": _receipt_body(reason="Second, conflicting reason."),
                    "author": {"login": TRUSTED_APPROVER},
                },
            ]
        )
        artifacts = _artifacts(harvest)
        item = _review_item(artifacts["REVIEW_ITEM_LEDGER.json"])
        assert item["disposition"] == "MUST_FIX"
        assert item["blocking"] is True

    def test_duplicate_identical_receipts_are_not_a_conflict(self) -> None:
        body = _receipt_body()
        harvest = _base_harvest(
            issue_comments=[
                {"id": "ic-1", "body": body, "author": {"login": TRUSTED_APPROVER}},
                {"id": "ic-2", "body": body, "author": {"login": TRUSTED_APPROVER}},
            ]
        )
        artifacts = _artifacts(harvest)
        item = _review_item(artifacts["REVIEW_ITEM_LEDGER.json"])
        assert item["disposition"] == "REJECTED_WITH_REASON"
        assert item["blocking"] is False


class TestChangesRequestedNeverOverridable:
    def test_changes_requested_stays_blocking_despite_valid_receipt(self) -> None:
        harvest = _base_harvest(
            review_state="CHANGES_REQUESTED",
            issue_comments=[
                {
                    "id": "ic-1",
                    "body": _receipt_body(),
                    "author": {"login": TRUSTED_APPROVER},
                }
            ],
        )
        artifacts = _artifacts(harvest)
        item = _review_item(artifacts["REVIEW_ITEM_LEDGER.json"])
        assert item["disposition"] == "MUST_FIX"
        assert item["blocking"] is True
        assert "REQUEST_CHANGES" in artifacts["MERGE_READINESS.json"]["blockers"]


class TestUnresolvedThreadUnaffected:
    def test_unresolved_thread_remains_blocking_alongside_a_cleared_review(
        self,
    ) -> None:
        harvest = _base_harvest(
            issue_comments=[
                {
                    "id": "ic-1",
                    "body": _receipt_body(),
                    "author": {"login": TRUSTED_APPROVER},
                }
            ],
        )
        harvest["review_threads"] = [
            {
                "id": "thread-1",
                "isResolved": False,
                "isOutdated": False,
                "comments": {
                    "nodes": [
                        {
                            "id": "rc-1",
                            "body": "P1: unresolved concern.",
                            "author": {"login": "chatgpt-codex-connector"},
                        }
                    ]
                },
            }
        ]
        artifacts = _artifacts(harvest)
        merge_readiness = artifacts["MERGE_READINESS.json"]
        review_item = _review_item(artifacts["REVIEW_ITEM_LEDGER.json"])
        assert review_item["disposition"] == "REJECTED_WITH_REASON"
        assert review_item["blocking"] is False
        assert merge_readiness["readiness"] != "READY"


class TestReceiptCommentItselfIsNonblocking:
    def test_receipt_comment_is_nonblocking_even_when_reason_quotes_p2(self) -> None:
        harvest = _base_harvest(
            issue_comments=[
                {
                    "id": "ic-1",
                    "body": _receipt_body(
                        reason="The historical P2 finding no longer applies."
                    ),
                    "author": {"login": TRUSTED_APPROVER},
                }
            ]
        )
        artifacts = _artifacts(harvest)
        comment_item = _review_item(artifacts["REVIEW_ITEM_LEDGER.json"], "ic-1")
        assert comment_item["disposition"] == "REJECTED_WITH_REASON"
        assert comment_item["blocking"] is False


class TestLedgerConservation:
    def test_ledger_item_count_matches_harvest_after_clearance(self) -> None:
        harvest = _base_harvest(
            issue_comments=[
                {
                    "id": "ic-1",
                    "body": _receipt_body(),
                    "author": {"login": TRUSTED_APPROVER},
                }
            ]
        )
        artifacts = _artifacts(harvest)
        ledger = artifacts["REVIEW_ITEM_LEDGER.json"]
        assert len(ledger["items"]) == len(harvest["reviews"]) + len(
            harvest["issue_comments"]
        )
        assert ledger["unclassified_count"] == 0
        assert "HARVEST_INCOMPLETE" not in artifacts["MERGE_READINESS.json"]["blockers"]
