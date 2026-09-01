"""Behavior contracts for shared exact-head review settlement."""

from __future__ import annotations

import importlib
import json
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType

import pytest


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "audit" / "review_settlement.py"
PACKAGED_MODULE_PATH = ROOT / "src" / "dopemux_pr_steward" / "review_settlement.py"
NOW = datetime(2026, 8, 27, 20, 0, tzinfo=timezone.utc)


def _module() -> ModuleType:
    return importlib.import_module("dopemux_pr_steward.review_settlement")


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
        "issue_comment_events_complete": True,
        "issue_comments": [],
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
            "workflow_event": "workflow_run",
            "run_conclusion": "success",
            "publisher_kind": "invalidation_writer",
            "status_context": "PR Steward / final readiness",
            "status_state": "pending",
            "status_sha": "a" * 40,
            "status_description": "review activity invalidated final readiness",
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


def test_incomplete_issue_comment_pagination_forbids_success() -> None:
    """TP-DMX-...-A15-R1 S3: pagination must fail closed for issue comments
    the same way it already does for reviews/threads/review comments."""
    snapshot = _snapshot()
    snapshot["issue_comment_events_complete"] = False

    assert "issue_comments_pagination_unknown" in _evaluate(snapshot)["reasons"]


def test_issue_comment_changes_fingerprint_and_blocks_quiet_period() -> None:
    """TP-DMX-...-A15-R1 S3: a new PR conversation comment must reset the
    quiet clock and change the settlement fingerprint, mirroring review
    activity and review-thread comment activity."""
    settled = _evaluate(_snapshot())

    with_comment = _snapshot()
    with_comment["issue_comments"] = [
        {
            "id": "IC_1",
            "created_at": "2026-08-27T19:59:00Z",
            "updated_at": "2026-08-27T19:59:00Z",
        }
    ]
    result = _evaluate(with_comment)

    assert result["fingerprint"] != settled["fingerprint"]
    assert result["status"] == "BLOCKED"
    assert "review_activity_too_recent" in result["reasons"]


def test_old_issue_comment_does_not_block_quiet_period() -> None:
    snapshot = _snapshot()
    snapshot["issue_comments"] = [
        {
            "id": "IC_1",
            "created_at": "2026-08-27T19:00:00Z",
            "updated_at": "2026-08-27T19:00:00Z",
        }
    ]

    assert _evaluate(snapshot)["status"] == "SETTLED"


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


def _pending_status(*, run_id: int, created_at: str, sha: str = "a" * 40) -> dict:
    return {
        "context": "PR Steward / final readiness",
        "state": "pending",
        "sha": sha,
        "created_at": created_at,
        "description": "live head or review settlement changed after readiness publication",
        "target_url": (
            f"https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/{run_id}"
        ),
    }


def _workflow_run(
    *,
    run_id: int,
    name: str,
    path: str,
    event: str,
    conclusion: str,
) -> dict:
    return {
        "id": run_id,
        "repository": {"full_name": "DDD-Enterprises/dopemux-mvp"},
        "name": name,
        "path": path,
        "status": "completed",
        "conclusion": conclusion,
        "event": event,
    }


@pytest.mark.parametrize("event", ["workflow_run", "workflow_dispatch"])
def test_latest_steward_fail_closed_pending_is_trusted(monkeypatch, event: str) -> None:
    module = _module()
    status = _pending_status(run_id=222, created_at="2026-08-27T19:59:50Z")
    run = _workflow_run(
        run_id=222,
        name="PR Steward",
        path=".github/workflows/pr-steward.yml",
        event=event,
        conclusion="failure",
    )
    monkeypatch.setattr(module, "_status_history", lambda _repo, _head: [status])
    monkeypatch.setattr(module, "_gh_api_json", lambda *_args: run)

    created_at, source = module.fetch_latest_trusted_invalidation(
        "DDD-Enterprises/dopemux-mvp", "a" * 40
    )

    assert created_at == "2026-08-27T19:59:50Z"
    assert source == {
        "repository": "DDD-Enterprises/dopemux-mvp",
        "workflow_run_id": 222,
        "workflow_name": "PR Steward",
        "workflow_path": ".github/workflows/pr-steward.yml",
        "workflow_event": event,
        "run_conclusion": "failure",
        "publisher_kind": "pr_steward",
        "status_context": "PR Steward / final readiness",
        "status_state": "pending",
        "status_sha": "a" * 40,
        "status_description": (
            "live head or review settlement changed after readiness publication"
        ),
    }


def test_newer_untrusted_pending_is_not_skipped(monkeypatch) -> None:
    module = _module()
    statuses = [
        _pending_status(run_id=111, created_at="2026-08-27T19:58:00Z"),
        _pending_status(run_id=222, created_at="2026-08-27T19:59:00Z"),
    ]
    untrusted_run = _workflow_run(
        run_id=222,
        name="Untrusted workflow",
        path=".github/workflows/untrusted.yml",
        event="workflow_dispatch",
        conclusion="success",
    )
    monkeypatch.setattr(module, "_status_history", lambda _repo, _head: statuses)
    monkeypatch.setattr(module, "_gh_api_json", lambda *_args: untrusted_run)

    with pytest.raises(RuntimeError, match="TRUSTED_INVALIDATION_TIME_UNKNOWN"):
        module.fetch_latest_trusted_invalidation(
            "DDD-Enterprises/dopemux-mvp", "a" * 40
        )


def test_trusted_pending_status_must_match_exact_head(monkeypatch) -> None:
    module = _module()
    status = _pending_status(
        run_id=111,
        created_at="2026-08-27T19:58:00Z",
        sha="b" * 40,
    )
    run = _workflow_run(
        run_id=111,
        name="PR readiness invalidation writer",
        path=".github/workflows/pr-readiness-invalidation-writer.yml",
        event="workflow_run",
        conclusion="success",
    )
    monkeypatch.setattr(module, "_status_history", lambda _repo, _head: [status])
    monkeypatch.setattr(module, "_gh_api_json", lambda *_args: run)

    with pytest.raises(RuntimeError, match="status_head_sha_mismatch"):
        module.fetch_latest_trusted_invalidation(
            "DDD-Enterprises/dopemux-mvp", "a" * 40
        )


def test_repository_settlement_script_is_thin_package_wrapper() -> None:
    assert PACKAGED_MODULE_PATH.is_file()
    wrapper = MODULE_PATH.read_text(encoding="utf-8")

    assert "from dopemux_pr_steward.review_settlement import main" in wrapper
    assert "def evaluate_snapshot" not in wrapper
    assert "def fetch_snapshot" not in wrapper


def test_packaged_cli_settlement_fetch(monkeypatch, tmp_path: Path, capsys) -> None:
    from dopemux_pr_steward.cli import main as steward_main

    module = _module()
    monkeypatch.setattr(module, "fetch_snapshot", lambda _repo, _pr: _snapshot())
    output = tmp_path / "settlement.json"

    rc = steward_main(
        [
            "settlement",
            "fetch",
            "--repo",
            "DDD-Enterprises/dopemux-mvp",
            "--pr",
            "1287",
            "--head",
            "a" * 40,
            "--output",
            str(output),
            "--now",
            "2026-08-27T20:00:00Z",
        ]
    )

    captured = capsys.readouterr()
    assert rc == 0, captured.err
    assert json.loads(output.read_text(encoding="utf-8"))["status"] == "SETTLED"


def test_packaged_cli_settlement_compare(tmp_path: Path, capsys) -> None:
    from dopemux_pr_steward.cli import main as steward_main

    result = _evaluate(_snapshot())
    before = tmp_path / "before.json"
    after = tmp_path / "after.json"
    before.write_text(json.dumps(result), encoding="utf-8")
    after.write_text(json.dumps(result), encoding="utf-8")

    rc = steward_main(
        [
            "settlement",
            "compare",
            "--before",
            str(before),
            "--after",
            str(after),
        ]
    )

    captured = capsys.readouterr()
    assert rc == 0, captured.err
    assert json.loads(captured.out)["status"] == "MATCH"
