"""Behavior contracts for shared exact-head review settlement."""

from __future__ import annotations

import importlib.util
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "audit" / "review_settlement.py"
NOW = datetime(2026, 8, 27, 20, 0, tzinfo=timezone.utc)


def _module() -> ModuleType:
    assert MODULE_PATH.is_file(), "shared review settlement module must exist"
    spec = importlib.util.spec_from_file_location("review_settlement", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _snapshot() -> dict:
    return {
        "repository": "DDD-Enterprises/dopemux-mvp",
        "pr_number": 1287,
        "state": "OPEN",
        "is_draft": False,
        "merged": False,
        "created_at": "2026-08-27T19:45:00Z",
        "head_sha": "a" * 40,
        "review_decision": "REVIEW_REQUIRED",
        "ready_events_complete": True,
        "review_events_complete": True,
        "thread_events_complete": True,
        "review_comment_events_complete": True,
        "ready_events": ["2026-08-27T19:50:00Z"],
        "reviews": [
            {
                "author": "reviewer-a",
                "state": "COMMENTED",
                "submitted_at": "2026-08-27T19:53:00Z",
                "updated_at": "2026-08-27T19:53:00Z",
            }
        ],
        "threads": [
            {
                "id": "thread-1",
                "is_resolved": True,
                "comments": [
                    {
                        "created_at": "2026-08-27T19:54:00Z",
                        "updated_at": "2026-08-27T19:54:00Z",
                    }
                ],
            }
        ],
    }


def _trusted_invalidation(at: str) -> dict:
    return {
        "latest_trusted_invalidation_at": at,
        "latest_trusted_invalidation_source": {
            "repository": "DDD-Enterprises/dopemux-mvp",
            "workflow_run_id": 987,
            "workflow_name": "PR readiness invalidation writer",
            "workflow_path": ".github/workflows/pr-readiness-invalidation-writer.yml",
            "status_context": "PR Steward / final readiness",
            "status_state": "pending",
        },
    }


def _evaluate(snapshot: dict) -> dict:
    return _module().evaluate_snapshot(
        snapshot,
        expected_repo="DDD-Enterprises/dopemux-mvp",
        expected_pr=1287,
        expected_head="a" * 40,
        now=NOW,
        min_ready_age_seconds=300,
        min_activity_quiet_seconds=120,
    )


def test_settled_exact_head_is_success_eligible() -> None:
    result = _evaluate(_snapshot())

    assert result["status"] == "SETTLED"
    assert result["reasons"] == []
    assert len(result["fingerprint"]) == 64


def test_direct_ready_pr_uses_created_at_fallback() -> None:
    snapshot = _snapshot()
    snapshot["ready_events"] = []

    assert _evaluate(snapshot)["status"] == "SETTLED"


def test_active_changes_requested_forbids_success() -> None:
    snapshot = _snapshot()
    snapshot["reviews"][0]["state"] = "CHANGES_REQUESTED"

    assert "active_change_request_reviews" in _evaluate(snapshot)["reasons"]


def test_latest_effective_review_state_clears_old_change_request() -> None:
    snapshot = _snapshot()
    snapshot["reviews"] = [
        {
            "author": "reviewer-a",
            "state": "CHANGES_REQUESTED",
            "submitted_at": "2026-08-27T19:51:00Z",
            "updated_at": "2026-08-27T19:51:00Z",
        },
        {
            "author": "reviewer-a",
            "state": "APPROVED",
            "submitted_at": "2026-08-27T19:53:00Z",
            "updated_at": "2026-08-27T19:53:00Z",
        },
    ]

    assert _evaluate(snapshot)["status"] == "SETTLED"


def test_unresolved_thread_forbids_success() -> None:
    snapshot = _snapshot()
    snapshot["threads"][0]["is_resolved"] = False

    assert "unresolved_review_threads" in _evaluate(snapshot)["reasons"]


def test_head_drift_forbids_success() -> None:
    snapshot = _snapshot()
    snapshot["head_sha"] = "b" * 40

    assert "head_sha_mismatch" in _evaluate(snapshot)["reasons"]


def test_incomplete_pagination_forbids_success() -> None:
    snapshot = _snapshot()
    snapshot["thread_events_complete"] = False

    assert "review_threads_pagination_unknown" in _evaluate(snapshot)["reasons"]


def test_review_activity_changes_fingerprint_and_blocks_quiet_period() -> None:
    settled = _evaluate(_snapshot())
    changed_snapshot = _snapshot()
    changed_snapshot["reviews"][0]["updated_at"] = "2026-08-27T19:59:30Z"
    changed = _evaluate(changed_snapshot)

    assert changed["fingerprint"] != settled["fingerprint"]
    assert "review_activity_too_recent" in changed["reasons"]


def test_recent_thread_resolved_invalidation_blocks_quiet_period() -> None:
    snapshot = _snapshot()
    snapshot.update(_trusted_invalidation("2026-08-27T19:59:50Z"))
    result = _evaluate(snapshot)

    assert result["review_activity_age_seconds"] == 10
    assert "review_activity_too_recent" in result["reasons"]
    assert result["facts"]["latest_trusted_invalidation_at"] == "2026-08-27T19:59:50Z"


def test_recent_thread_unresolved_invalidation_blocks_quiet_period() -> None:
    snapshot = _snapshot()
    snapshot["threads"][0]["is_resolved"] = False
    snapshot.update(_trusted_invalidation("2026-08-27T19:59:50Z"))
    result = _evaluate(snapshot)

    assert "unresolved_review_threads" in result["reasons"]
    assert "review_activity_too_recent" in result["reasons"]


def test_trusted_invalidation_timestamp_changes_fingerprint() -> None:
    settled = _evaluate(_snapshot())
    changed_snapshot = _snapshot()
    changed_snapshot.update(_trusted_invalidation("2026-08-27T19:57:30Z"))
    changed = _evaluate(changed_snapshot)

    assert changed["status"] == "SETTLED"
    assert changed["fingerprint"] != settled["fingerprint"]


def test_forged_unbound_invalidation_timestamp_cannot_satisfy_settlement() -> None:
    snapshot = _snapshot()
    snapshot["latest_trusted_invalidation_at"] = "2026-08-27T19:57:30Z"
    result = _evaluate(snapshot)

    assert result["status"] == "BLOCKED"
    assert "trusted_invalidation_time_unknown" in result["reasons"]


def test_quiet_period_passes_after_trusted_invalidation_duration() -> None:
    snapshot = _snapshot()
    snapshot.update(_trusted_invalidation("2026-08-27T19:57:30Z"))
    result = _evaluate(snapshot)

    assert result["status"] == "SETTLED"
    assert result["review_activity_age_seconds"] == 150
