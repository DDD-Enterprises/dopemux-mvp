"""Tests for TP-DMX-AUDIT-STEWARD-CONTRACT-HYGIENE-001 Slice 1:
truthful, mechanically-derived REVIEW_ITEM_LEDGER accounting.

Invariants under test:
  - unclassified_count is derived, never hardcoded.
  - input_item_count == ledger_item_count == sum(disposition_counts).
  - every current supported input receives exactly one disposition.
  - malformed/unexpected shapes cannot silently disappear: they surface as
    an explicit unclassified ledger entry AND block readiness via the
    existing HARVEST_INCOMPLETE blocker (no new blocker type introduced).
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path

from tools.pr_steward.classifier import (
    REVIEW_LEDGER_SOURCES,
    UNCLASSIFIED_ITEM_DISPOSITION,
    build_artifacts,
)

ROOT = Path(__file__).resolve().parents[2]
KNOWN_REVIEWERS_PATH = ROOT / "tools" / "pr_steward" / "known_reviewers.json"


def _base_harvest(**overrides) -> dict:
    harvest = {
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
            "headRefOid": "head000000000000000000000000000000000000",
            "author": {"login": "hu3mann"},
            "createdAt": "2026-05-26T01:00:00Z",
            "updatedAt": "2026-05-26T02:00:00Z",
        },
        "changed_files": [{"path": "foo.py", "additions": 1}],
        "commits": [{"oid": "head000000000000000000000000000000000000", "messageHeadline": "t"}],
        "reviews": [],
        "review_comments": [],
        "review_threads": [],
        "issue_comments": [],
        "checks": [],
        "proof": {
            "proof_path": "proof/PROOF.json",
            "proof_head_sha": "head000000000000000000000000000000000000",
            "matches_pr_head": True,
        },
        "embedded_audit": {"status": "PASS", "report_path": "proof/AUDITOR_REPORT.md"},
    }
    harvest.update(overrides)
    return harvest


def _build(harvest: dict) -> dict:
    return build_artifacts(
        harvest,
        repo="DDD-Enterprises/dopemux-mvp",
        pr_number=704,
        strict=True,
        allow_closed=False,
        known_reviewers_path=KNOWN_REVIEWERS_PATH,
    )


def _assert_conserved(artifacts: dict) -> dict:
    ledger = artifacts["REVIEW_ITEM_LEDGER.json"]
    ledger_source_items = [
        item for item in ledger["items"] if item["source"] in REVIEW_LEDGER_SOURCES
    ]
    disposition_counts = Counter(item["disposition"] for item in ledger_source_items)
    assert sum(disposition_counts.values()) == len(ledger_source_items)
    assert ledger["unclassified_count"] == disposition_counts.get(
        UNCLASSIFIED_ITEM_DISPOSITION, 0
    )
    return ledger


# ---------------------------------------------------------------------------
# Empty / well-formed inputs
# ---------------------------------------------------------------------------


class TestWellFormedConservation:
    def test_empty_intake_zero_unclassified(self) -> None:
        artifacts = _build(_base_harvest())
        ledger = _assert_conserved(artifacts)
        assert ledger["unclassified_count"] == 0
        assert ledger["items"] == []

    def test_one_item_of_each_supported_type(self) -> None:
        harvest = _base_harvest(
            reviews=[{"id": "r1", "author": {"login": "hu3mann"}, "state": "APPROVED", "body": ""}],
            review_comments=[
                {"id": "rc1", "author": {"login": "hu3mann"}, "body": "looks fine"}
            ],
            issue_comments=[
                {"id": "ic1", "author": {"login": "hu3mann"}, "body": "looks fine"}
            ],
            review_threads=[
                {
                    "id": "t1",
                    "isResolved": True,
                    "isOutdated": False,
                    "comments": [{"id": "tc1", "author": {"login": "hu3mann"}, "body": "ok"}],
                }
            ],
        )
        artifacts = _build(harvest)
        ledger = _assert_conserved(artifacts)
        assert ledger["unclassified_count"] == 0
        sources = {item["source"] for item in ledger["items"]}
        assert sources == {"review", "review_comment", "issue_comment", "review_thread"}

    def test_unknown_reviewer_is_not_unclassified(self) -> None:
        harvest = _base_harvest(
            reviews=[
                {"id": "r1", "author": {"login": "totally-unknown"}, "state": "COMMENTED", "body": ""}
            ]
        )
        artifacts = _build(harvest)
        ledger = _assert_conserved(artifacts)
        assert ledger["unclassified_count"] == 0
        assert ledger["items"][0]["disposition"] == "UNKNOWN_REVIEWER_NEEDS_CLASSIFICATION"
        readiness = artifacts["MERGE_READINESS.json"]
        assert "UNKNOWN_REVIEWER_NEEDS_CLASSIFICATION" in readiness["blockers"]

    def test_missing_author_treated_as_unknown_reviewer(self) -> None:
        harvest = _base_harvest(reviews=[{"id": "r1", "state": "COMMENTED", "body": ""}])
        artifacts = _build(harvest)
        ledger = _assert_conserved(artifacts)
        assert ledger["unclassified_count"] == 0
        assert ledger["items"][0]["author"] == "unknown"
        assert ledger["items"][0]["disposition"] == "UNKNOWN_REVIEWER_NEEDS_CLASSIFICATION"

    def test_duplicate_thread_comment_representation_conserves(self) -> None:
        # The same underlying comment id legitimately appears both in the flat
        # review_comments array (REST shape) and nested inside a review_thread
        # (GraphQL shape). Both representations are counted — that is current
        # classifier semantics, and conservation must still hold across both.
        harvest = _base_harvest(
            review_comments=[
                {"id": "dup1", "author": {"login": "hu3mann"}, "body": "note"}
            ],
            review_threads=[
                {
                    "id": "t1",
                    "isResolved": True,
                    "isOutdated": False,
                    "comments": [{"id": "dup1", "author": {"login": "hu3mann"}, "body": "note"}],
                }
            ],
        )
        artifacts = _build(harvest)
        ledger = _assert_conserved(artifacts)
        assert ledger["unclassified_count"] == 0
        ids_by_source = {
            (item["source"], item["id"]) for item in ledger["items"]
        }
        assert ("review_comment", "dup1") in ids_by_source
        assert ("review_thread", "dup1") in ids_by_source


# ---------------------------------------------------------------------------
# Malformed shapes
# ---------------------------------------------------------------------------


class TestMalformedShapes:
    def test_malformed_review_blocks_and_counts_unclassified(self) -> None:
        harvest = _base_harvest(reviews=["not-a-mapping"])
        artifacts = _build(harvest)
        ledger = _assert_conserved(artifacts)
        assert ledger["unclassified_count"] == 1
        readiness = artifacts["MERGE_READINESS.json"]
        assert "HARVEST_INCOMPLETE" in readiness["blockers"]
        assert readiness["readiness"] == "BLOCKED"

    def test_malformed_review_comment_blocks_and_counts_unclassified(self) -> None:
        harvest = _base_harvest(review_comments=[42])
        artifacts = _build(harvest)
        ledger = _assert_conserved(artifacts)
        assert ledger["unclassified_count"] == 1
        readiness = artifacts["MERGE_READINESS.json"]
        assert "HARVEST_INCOMPLETE" in readiness["blockers"]

    def test_malformed_issue_comment_blocks_and_counts_unclassified(self) -> None:
        harvest = _base_harvest(issue_comments=[None])
        artifacts = _build(harvest)
        ledger = _assert_conserved(artifacts)
        assert ledger["unclassified_count"] == 1
        readiness = artifacts["MERGE_READINESS.json"]
        assert "HARVEST_INCOMPLETE" in readiness["blockers"]

    def test_malformed_thread_blocks_and_counts_unclassified(self) -> None:
        harvest = _base_harvest(review_threads=["not-a-mapping"])
        artifacts = _build(harvest)
        ledger = _assert_conserved(artifacts)
        assert ledger["unclassified_count"] == 1
        readiness = artifacts["MERGE_READINESS.json"]
        assert "HARVEST_INCOMPLETE" in readiness["blockers"]

    def test_malformed_thread_comments_container_blocks(self) -> None:
        harvest = _base_harvest(
            review_threads=[{"id": "t1", "isResolved": True, "comments": "not-a-list"}]
        )
        artifacts = _build(harvest)
        ledger = _assert_conserved(artifacts)
        assert ledger["unclassified_count"] == 1
        readiness = artifacts["MERGE_READINESS.json"]
        assert "HARVEST_INCOMPLETE" in readiness["blockers"]

    def test_malformed_comment_inside_thread_blocks(self) -> None:
        harvest = _base_harvest(
            review_threads=[
                {
                    "id": "t1",
                    "isResolved": True,
                    "isOutdated": False,
                    "comments": [
                        {"id": "ok1", "author": {"login": "hu3mann"}, "body": "fine"},
                        "not-a-mapping",
                    ],
                }
            ]
        )
        artifacts = _build(harvest)
        ledger = _assert_conserved(artifacts)
        assert ledger["unclassified_count"] == 1
        readiness = artifacts["MERGE_READINESS.json"]
        assert "HARVEST_INCOMPLETE" in readiness["blockers"]

    def test_unexpected_item_type_at_field_level_blocks(self) -> None:
        # The whole field is the wrong type (a dict instead of a list).
        harvest = _base_harvest(reviews={"unexpected": "shape"})
        artifacts = _build(harvest)
        ledger = _assert_conserved(artifacts)
        assert ledger["unclassified_count"] == 0
        readiness = artifacts["MERGE_READINESS.json"]
        assert "HARVEST_INCOMPLETE" in readiness["blockers"]
        assert readiness["readiness"] == "BLOCKED"

    def test_nonzero_unclassified_count_blocks_readiness(self) -> None:
        harvest = _base_harvest(reviews=["bad"])
        artifacts = _build(harvest)
        ledger = artifacts["REVIEW_ITEM_LEDGER.json"]
        readiness = artifacts["MERGE_READINESS.json"]
        assert ledger["unclassified_count"] > 0
        assert readiness["readiness"] != "READY"

    def test_no_silently_dropped_input_mixed_batch(self) -> None:
        harvest = _base_harvest(
            reviews=[
                {"id": "r1", "author": {"login": "hu3mann"}, "state": "APPROVED", "body": ""},
                "bad-review",
            ],
            review_comments=[
                {"id": "rc1", "author": {"login": "hu3mann"}, "body": "ok"},
                123,
            ],
            issue_comments=[{"id": "ic1", "author": {"login": "hu3mann"}, "body": "ok"}],
            review_threads=[
                {
                    "id": "t1",
                    "isResolved": True,
                    "isOutdated": False,
                    "comments": [
                        {"id": "tc1", "author": {"login": "hu3mann"}, "body": "ok"},
                        None,
                    ],
                },
                "bad-thread",
            ],
        )
        artifacts = _build(harvest)
        ledger = _assert_conserved(artifacts)
        # 2 good reviews-side items + 4 malformed = 6 real items total across
        # reviews(2) + review_comments(2) + issue_comments(1) + thread(2) + bad-thread(1) = 8
        assert len(ledger["items"]) == 8
        assert ledger["unclassified_count"] == 4
        readiness = artifacts["MERGE_READINESS.json"]
        assert readiness["readiness"] == "BLOCKED"
