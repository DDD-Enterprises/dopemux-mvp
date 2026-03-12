from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from dopemux_pr_merge_specialist import cli
from dopemux_pr_merge_specialist.schema import MergeDecision, ValidationReport


def _raw_pr(number: int, title: str) -> dict:
    return {
        "number": number,
        "title": title,
        "author": {"login": "tester"},
        "state": "OPEN",
        "statusCheckRollup": [{"status": "COMPLETED", "conclusion": "SUCCESS"}],
        "mergeable": "MERGEABLE",
        "mergeStateStatus": "CLEAN",
        "labels": [],
        "reviewDecision": "",
        "updatedAt": "2026-03-12T00:00:00Z",
        "baseRefName": "main",
        "headRefName": f"feature/{number}",
        "isDraft": False,
        "additions": 3,
        "deletions": 1,
        "changedFiles": 1,
        "url": f"https://example.com/pr/{number}",
    }


def test_queue_drain_dry_run_writes_contract_artifacts(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(cli, "_resolve_repo_slug", lambda repo: "DDD-Enterprises/dopemux-mvp")
    monkeypatch.setattr(cli, "_fetch_open_prs", lambda limit, repo: [_raw_pr(1, "one"), _raw_pr(2, "two")])
    monkeypatch.setattr(cli, "_fetch_review_threads", lambda repo, pr_id: [])
    monkeypatch.setattr(
        cli,
        "_checks_green",
        lambda pr_id, repo: (True, {"checks_total": 1, "checks_success": 1, "checks_failure": 0, "checks_pending": 0}),
    )

    # Avoid hitting gh in dry-run merge helper path.
    monkeypatch.setattr(
        cli,
        "_run_merge_with_fallback",
        lambda decision, pr_id, execute, repo, commands_log: MergeDecision(
            action="rebase_merge",
            command=["gh", "pr", "merge", str(pr_id), "--rebase", "--delete-branch"],
            reason="dry-run merge",
        ),
    )

    args = SimpleNamespace(
        repo=None,
        execute=False,
        max_prs=0,
        limit=20,
        max_passes=2,
        check_wait_seconds=0,
        check_poll_seconds=0,
        strategy="hybrid",
        strict_conflicts=True,
        out_dir=str(tmp_path),
    )

    rc = cli._queue_drain(args)
    assert rc == 0

    run_dirs = [p for p in tmp_path.iterdir() if p.is_dir()]
    assert len(run_dirs) == 1
    run_dir = run_dirs[0]

    assert (run_dir / "QUEUE_SNAPSHOT.json").exists()
    assert (run_dir / "ORDERING_PLAN.json").exists()
    assert (run_dir / "PASS_REPORTS.json").exists()
    assert (run_dir / "BASE_REBASE_UPDATES.json").exists()
    assert (run_dir / "QUEUE_REPORT.json").exists()

    pr1 = run_dir / "PR-1"
    assert (pr1 / "INTAKE.json").exists()
    assert (pr1 / "REVIEW_THREADS.json").exists()
    assert (pr1 / "THREAD_DISPOSITIONS.json").exists()
    assert (pr1 / "VALIDATION_REPORT.md").exists()
    assert (pr1 / "MERGE_DECISION.json").exists()
    assert (pr1 / "RESULT.json").exists()

    report = json.loads((run_dir / "QUEUE_REPORT.json").read_text(encoding="utf-8"))
    assert report["processed"] == 2


def test_queue_drain_revisits_when_checks_are_pending(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(cli, "_resolve_repo_slug", lambda repo: "DDD-Enterprises/dopemux-mvp")

    fetch_calls = {"count": 0}

    def fake_fetch_open_prs(limit, repo):
        fetch_calls["count"] += 1
        if fetch_calls["count"] <= 3:
            return [_raw_pr(7, "pending")]
        return []

    check_calls = {"count": 0}

    def fake_checks_green(pr_id, repo):
        check_calls["count"] += 1
        if check_calls["count"] == 1:
            return False, {"checks_total": 1, "checks_success": 0, "checks_failure": 0, "checks_pending": 1}
        return True, {"checks_total": 1, "checks_success": 1, "checks_failure": 0, "checks_pending": 0}

    worktree = tmp_path / "wt"
    worktree.mkdir()

    monkeypatch.setattr(cli, "_fetch_open_prs", fake_fetch_open_prs)
    monkeypatch.setattr(cli, "_fetch_review_threads", lambda repo, pr_id: [])
    monkeypatch.setattr(cli, "_checks_green", fake_checks_green)
    monkeypatch.setattr(cli, "_prepare_worktree", lambda **kwargs: (worktree, "branch", None))
    monkeypatch.setattr(cli, "_attempt_rebase", lambda **kwargs: (True, False, "ok"))
    monkeypatch.setattr(cli, "_stage_and_push_if_needed", lambda **kwargs: None)
    monkeypatch.setattr(cli, "_cleanup_worktree", lambda **kwargs: None)
    monkeypatch.setattr(cli, "_run_validation_steps", lambda **kwargs: ValidationReport(passed=True))
    monkeypatch.setattr(cli, "_update_remaining_pr_bases", lambda **kwargs: [])
    monkeypatch.setattr(cli.time, "sleep", lambda _: None)

    def fake_run_merge(decision, pr_id, execute, repo, commands_log):
        if decision.action == "blocked":
            return decision
        return MergeDecision(
            action="rebase_merge",
            command=["gh", "pr", "merge", str(pr_id), "--rebase", "--delete-branch"],
            reason="merged on second pass",
        )

    monkeypatch.setattr(cli, "_run_merge_with_fallback", fake_run_merge)

    args = SimpleNamespace(
        repo=None,
        execute=True,
        max_prs=0,
        limit=20,
        max_passes=3,
        check_wait_seconds=0,
        check_poll_seconds=0,
        strategy="hybrid",
        strict_conflicts=True,
        out_dir=str(tmp_path),
    )

    rc = cli._queue_drain(args)
    assert rc == 0

    run_dir = next(p for p in tmp_path.iterdir() if p.is_dir() and p.name != "wt")
    report = json.loads((run_dir / "QUEUE_REPORT.json").read_text(encoding="utf-8"))

    assert report["processed"] == 1
    assert report["merged"] == 1
    assert len(report["passes"]) >= 2
    assert report["passes"][0]["pending_checks_seen"] == 1
