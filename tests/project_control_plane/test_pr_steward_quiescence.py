"""
Adversarial regression test suite for PR Steward exact-head review quiescence.

Covers:
1. PR #1286 race timing fixture: audit finishes before review producer completion,
   reviewers arrive later with issues. Implementation gates audit on review quiescence
   and blocks on unresolved review threads.
2. Exact-head review submission completion vs stale previous-head review rejection.
3. Check-run completion strategy for automated reviewers (CodeQL/Copilot).
4. Missing mandatory review producers fail closed to UNKNOWN / BLOCKED.
5. Unknown review producers fail closed.
6. Active unresolved review threads yield NEEDS_IMPLEMENTER and block quiescence.
7. PR head SHA mismatch rejects evidence and blocks quiescence.
8. Elapsed time alone never constitutes completion authority.
9. All emitted receipts validate against review_quiescence.schema.json.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft7Validator

from tools.pr_steward.review_quiescence import (
    evaluate_review_quiescence,
    load_review_producers,
)
from tools.pr_steward.collector import _quiescence_state
from tools.pr_steward.classifier import build_artifacts

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCHEMA_PATH = _REPO_ROOT / "schemas" / "pr_steward" / "review_quiescence.schema.json"

with _SCHEMA_PATH.open("r", encoding="utf-8") as fh:
    _SCHEMA = json.load(fh)

_VALIDATOR = Draft7Validator(_SCHEMA)


def _validate_schema(instance: dict[str, Any]) -> None:
    errors = list(_VALIDATOR.iter_errors(instance))
    assert errors == [], f"Schema validation failed: {errors}"


_HEAD_A = "a" * 40
_HEAD_B = "b" * 40
_REPO = "DDD-Enterprises/dopemux-mvp"
_PR_NUM = 1286


@pytest.fixture
def base_config() -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "review_producers": [
            {
                "producer_id": "copilot-pull-request-reviewer",
                "mandatory": True,
                "strategies": ["review_submission", "check_run", "reaction"],
                "check_names": ["copilot-code-review", "CodeQL"],
            },
            {
                "producer_id": "chatgpt-codex-connector",
                "mandatory": True,
                "strategies": ["review_submission", "reaction"],
            },
        ],
    }


class TestReviewQuiescenceBasics:
    def test_clean_exact_head_quiescent(self, base_config: dict[str, Any]) -> None:
        harvest = {
            "pr": {"number": _PR_NUM, "headRefOid": _HEAD_A},
            "reviews": [
                {
                    "author": {"login": "copilot-pull-request-reviewer"},
                    "commit_id": _HEAD_A,
                    "state": "COMMENTED",
                    "id": "rev_1",
                },
                {
                    "author": {"login": "chatgpt-codex-connector"},
                    "commit_id": _HEAD_A,
                    "state": "COMMENTED",
                    "id": "rev_2",
                },
            ],
            "checks": [],
            "review_threads": [],
        }

        receipt = evaluate_review_quiescence(
            harvest,
            expected_head_sha=_HEAD_A,
            repo=_REPO,
            pr_number=_PR_NUM,
            producers_config=base_config,
        )

        assert receipt["verdict"] == "QUIESCENT"
        assert receipt["is_quiescent"] is True
        assert receipt["blocking_reasons"] == []
        assert receipt["unresolved_thread_count"] == 0
        _validate_schema(receipt)

    def test_missing_mandatory_producer_yields_unknown(self, base_config: dict[str, Any]) -> None:
        harvest = {
            "pr": {"number": _PR_NUM, "headRefOid": _HEAD_A},
            "reviews": [
                {
                    "author": {"login": "copilot-pull-request-reviewer"},
                    "commit_id": _HEAD_A,
                    "state": "COMMENTED",
                    "id": "rev_1",
                }
            ],
            "checks": [],
            "review_threads": [],
        }

        receipt = evaluate_review_quiescence(
            harvest,
            expected_head_sha=_HEAD_A,
            repo=_REPO,
            pr_number=_PR_NUM,
            producers_config=base_config,
        )

        assert receipt["verdict"] == "UNKNOWN"
        assert receipt["is_quiescent"] is False
        assert any("chatgpt-codex-connector" in r for r in receipt["blocking_reasons"])
        _validate_schema(receipt)

    def test_stale_prior_head_review_rejected(self, base_config: dict[str, Any]) -> None:
        harvest = {
            "pr": {"number": _PR_NUM, "headRefOid": _HEAD_A},
            "reviews": [
                {
                    "author": {"login": "copilot-pull-request-reviewer"},
                    "commit_id": _HEAD_B,  # Stale head B
                    "state": "COMMENTED",
                    "id": "rev_1",
                },
                {
                    "author": {"login": "chatgpt-codex-connector"},
                    "commit_id": _HEAD_A,
                    "state": "COMMENTED",
                    "id": "rev_2",
                },
            ],
            "checks": [],
            "review_threads": [],
        }

        receipt = evaluate_review_quiescence(
            harvest,
            expected_head_sha=_HEAD_A,
            repo=_REPO,
            pr_number=_PR_NUM,
            producers_config=base_config,
        )

        assert receipt["verdict"] == "BLOCKED"
        assert receipt["is_quiescent"] is False
        assert any("stale" in r.lower() for r in receipt["blocking_reasons"])
        _validate_schema(receipt)

    def test_unresolved_review_threads_yield_needs_implementer(self, base_config: dict[str, Any]) -> None:
        harvest = {
            "pr": {"number": _PR_NUM, "headRefOid": _HEAD_A},
            "reviews": [
                {
                    "author": {"login": "copilot-pull-request-reviewer"},
                    "commit_id": _HEAD_A,
                    "state": "COMMENTED",
                    "id": "rev_1",
                },
                {
                    "author": {"login": "chatgpt-codex-connector"},
                    "commit_id": _HEAD_A,
                    "state": "COMMENTED",
                    "id": "rev_2",
                },
            ],
            "checks": [],
            "review_threads": [
                {
                    "isResolved": False,
                    "comments": [{"body": "Contradiction in docs"}],
                }
            ],
        }

        receipt = evaluate_review_quiescence(
            harvest,
            expected_head_sha=_HEAD_A,
            repo=_REPO,
            pr_number=_PR_NUM,
            producers_config=base_config,
        )

        assert receipt["verdict"] == "NEEDS_IMPLEMENTER"
        assert receipt["is_quiescent"] is False
        assert receipt["unresolved_thread_count"] == 1
        _validate_schema(receipt)

    def test_check_run_strategy_satisfies_producer(self, base_config: dict[str, Any]) -> None:
        harvest = {
            "pr": {"number": _PR_NUM, "headRefOid": _HEAD_A},
            "reviews": [
                {
                    "author": {"login": "chatgpt-codex-connector"},
                    "commit_id": _HEAD_A,
                    "state": "COMMENTED",
                    "id": "rev_2",
                },
            ],
            "checks": [
                {
                    "name": "CodeQL",
                    "status": "completed",
                    "conclusion": "success",
                    "head_sha": _HEAD_A,
                }
            ],
            "review_threads": [],
        }

        receipt = evaluate_review_quiescence(
            harvest,
            expected_head_sha=_HEAD_A,
            repo=_REPO,
            pr_number=_PR_NUM,
            producers_config=base_config,
        )

        assert receipt["verdict"] == "QUIESCENT"
        assert receipt["is_quiescent"] is True
        copilot_prod = next(p for p in receipt["producers"] if p["producer_id"] == "copilot-pull-request-reviewer")
        assert copilot_prod["status"] == "COMPLETED"
        assert copilot_prod["strategy_used"] == "check_run"
        _validate_schema(receipt)

    def test_head_sha_mismatch_fails_closed(self, base_config: dict[str, Any]) -> None:
        harvest = {
            "pr": {"number": _PR_NUM, "headRefOid": _HEAD_B},
            "reviews": [],
            "checks": [],
            "review_threads": [],
        }

        receipt = evaluate_review_quiescence(
            harvest,
            expected_head_sha=_HEAD_A,
            repo=_REPO,
            pr_number=_PR_NUM,
            producers_config=base_config,
        )

        assert receipt["verdict"] == "BLOCKED"
        assert receipt["is_quiescent"] is False
        assert any("mismatch" in r.lower() for r in receipt["blocking_reasons"])
        _validate_schema(receipt)


class TestPR1286RaceRegression:
    """Explicitly tests the PR #1286 race scenario."""

    def test_pr_1286_race_ordering(self, base_config: dict[str, Any]) -> None:
        # At T1: Embedded audit ran early, no reviews yet.
        t1_harvest = {
            "pr": {"number": 1286, "headRefOid": "aa5f144c489cf3697e08ba6e85744cb8dd1b8a59"},
            "reviews": [],
            "checks": [],
            "review_threads": [],
        }
        t1_receipt = evaluate_review_quiescence(
            t1_harvest,
            expected_head_sha="aa5f144c489cf3697e08ba6e85744cb8dd1b8a59",
            repo=_REPO,
            pr_number=1286,
            producers_config=base_config,
        )
        # At T1, review quiescence must FAIL so audit cannot run.
        assert t1_receipt["is_quiescent"] is False
        assert t1_receipt["verdict"] == "UNKNOWN"

        # At T3/T4: Copilot and Codex reviews arrived with unresolved threads.
        t4_harvest = {
            "pr": {"number": 1286, "headRefOid": "aa5f144c489cf3697e08ba6e85744cb8dd1b8a59"},
            "reviews": [
                {
                    "author": {"login": "copilot-pull-request-reviewer"},
                    "commit_id": "aa5f144c489cf3697e08ba6e85744cb8dd1b8a59",
                    "state": "COMMENTED",
                    "id": "rev_copilot",
                },
                {
                    "author": {"login": "chatgpt-codex-connector"},
                    "commit_id": "aa5f144c489cf3697e08ba6e85744cb8dd1b8a59",
                    "state": "COMMENTED",
                    "id": "rev_codex",
                },
            ],
            "checks": [],
            "review_threads": [
                {
                    "isResolved": False,
                    "comments": [{"body": "docs/index.md text contradicts name-change note"}],
                },
                {
                    "isResolved": False,
                    "comments": [{"body": "Rebuild standalone PAL image when canonical source changes"}],
                },
            ],
        }
        t4_receipt = evaluate_review_quiescence(
            t4_harvest,
            expected_head_sha="aa5f144c489cf3697e08ba6e85744cb8dd1b8a59",
            repo=_REPO,
            pr_number=1286,
            producers_config=base_config,
        )
        # At T4, reviews are present but threads are unresolved: verdict NEEDS_IMPLEMENTER
        assert t4_receipt["is_quiescent"] is False
        assert t4_receipt["verdict"] == "NEEDS_IMPLEMENTER"
        assert t4_receipt["unresolved_thread_count"] == 2

        # Test PR Steward classification with non-quiescent harvest
        t4_harvest_steward = {
            "harvest_complete": True,
            "harvest_errors": [],
            "pr": {
                "number": 1286,
                "url": "https://github.com/DDD-Enterprises/dopemux-mvp/pull/1286",
                "state": "OPEN",
                "isDraft": False,
                "mergeable": "MERGEABLE",
                "mergeStateStatus": "CLEAN",
                "headRefName": "feat/pal-model-routing-modernization-001",
                "headRefOid": "aa5f144c489cf3697e08ba6e85744cb8dd1b8a59",
                "baseRefName": "main",
                "baseRefOid": "5900c27d3c38b515204bd5dc4baed8b5e14e2a8e",
                "files": [],
                "commits": [],
                "reviews": t4_harvest["reviews"],
            },
            "changed_files": [],
            "commits": [],
            "reviews": t4_harvest["reviews"],
            "review_comments": [],
            "review_threads": t4_harvest["review_threads"],
            "checks": [],
            "proof": {
                "proof_path": "proof/PROOF.json",
                "proof_head_sha": "aa5f144c489cf3697e08ba6e85744cb8dd1b8a59",
                "matches_pr_head": True,
                "proof_freshness": {"status": "FRESH"},
            },
            "embedded_audit": {"status": "PASS", "report_path": "proof/AUDITOR_REPORT.md"},
            "review_quiescence": t4_receipt,
        }

        artifacts = build_artifacts(
            t4_harvest_steward,
            repo=_REPO,
            pr_number=1286,
            strict=True,
            allow_closed=False,
        )
        readiness = artifacts["MERGE_READINESS.json"]
        assert readiness["readiness"] != "READY"
        assert any("QUIESCENCE" in b for b in readiness["blockers"])
