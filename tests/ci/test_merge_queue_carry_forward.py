"""Merge-queue audit carry-forward refuses anything except a proven merge."""

from __future__ import annotations

import json

import pytest

from scripts.ci.merge_queue_carry_forward import (
    AUDIT_CHECK,
    STEWARD_CONTEXT,
    CarryForwardError,
    evaluate,
    parse_queue_pr_numbers,
)

BASE = "b" * 40
PR_HEAD = "a" * 40
QUEUE = "c" * 40
OTHER = "d" * 40


class FakeGitHub:
    def __init__(self) -> None:
        self.pulls = {
            PR_HEAD: [
                {
                    "number": 1466,
                    "state": "open",
                    "base": {"ref": "main"},
                    "head": {"sha": PR_HEAD},
                }
            ]
        }
        self.checks = {PR_HEAD: {AUDIT_CHECK: "success"}}
        self.statuses = {PR_HEAD: {STEWARD_CONTEXT: "success"}}

    def pulls_for_commit(self, sha: str):
        return self.pulls.get(sha, [])

    def check_conclusion(self, sha: str, name: str):
        return self.checks.get(sha, {}).get(name)

    def status_state(self, sha: str, context: str):
        return self.statuses.get(sha, {}).get(context)


def test_parse_queue_ref_numbers():
    assert parse_queue_pr_numbers(
        "refs/heads/gh-readonly-queue/main/pr-1466-abcdef0"
    ) == (1466,)
    assert parse_queue_pr_numbers("gh-readonly-queue/main/pr-1466-1440-abcdef0") == (
        1466,
        1440,
    )
    assert parse_queue_pr_numbers(
        "gh-readonly-queue/main/pr-1466-pr-1440-deadbeef"
    ) == (1466, 1440)
    assert parse_queue_pr_numbers("refs/heads/feature") is None


def test_single_pr_merge_carries_forward_when_both_gates_passed():
    parents = {QUEUE: (BASE, PR_HEAD)}
    result = evaluate(
        head_sha=QUEUE,
        base_sha=BASE,
        head_ref="gh-readonly-queue/main/pr-1466-abcdef0",
        base_ref="main",
        parents_of=parents.get,
        github=FakeGitHub(),
    )
    assert result.pull_requests == (1466,)
    assert result.pull_request_heads == (PR_HEAD,)


def test_missing_audit_or_steward_is_refused():
    parents = {QUEUE: (BASE, PR_HEAD)}
    github = FakeGitHub()
    github.checks[PR_HEAD][AUDIT_CHECK] = "failure"
    with pytest.raises(CarryForwardError, match="independent embedded audit"):
        evaluate(
            head_sha=QUEUE,
            base_sha=BASE,
            head_ref="gh-readonly-queue/main/pr-1466-abcdef0",
            base_ref="main",
            parents_of=parents.get,
            github=github,
        )


def test_non_merge_queue_commit_is_refused():
    with pytest.raises(CarryForwardError, match="not a merge commit"):
        evaluate(
            head_sha=QUEUE,
            base_sha=BASE,
            head_ref="gh-readonly-queue/main/pr-1466-abcdef0",
            base_ref="main",
            parents_of=lambda _sha: (BASE,),
            github=FakeGitHub(),
        )


def test_ref_names_must_match_merge_parents():
    parents = {QUEUE: (BASE, PR_HEAD), OTHER: (QUEUE, "e" * 40)}
    github = FakeGitHub()
    github.pulls["e" * 40] = [
        {
            "number": 1440,
            "state": "open",
            "base": {"ref": "main"},
            "head": {"sha": "e" * 40},
        }
    ]
    github.checks["e" * 40] = {AUDIT_CHECK: "success"}
    github.statuses["e" * 40] = {STEWARD_CONTEXT: "success"}
    with pytest.raises(CarryForwardError, match="queue ref names"):
        evaluate(
            head_sha=OTHER,
            base_sha=BASE,
            head_ref="gh-readonly-queue/main/pr-1466-abcdef0",
            base_ref="main",
            parents_of=parents.get,
            github=github,
        )


def test_newer_in_progress_check_is_not_a_success():
    from scripts.ci.merge_queue_carry_forward import GhApi

    pages = {
        1: {
            "check_runs": [
                {
                    "name": AUDIT_CHECK,
                    "status": "completed",
                    "conclusion": "success",
                    "started_at": "2026-11-07T00:00:00Z",
                    "completed_at": "2026-11-07T00:01:00Z",
                },
                {
                    "name": AUDIT_CHECK,
                    "status": "in_progress",
                    "conclusion": None,
                    "started_at": "2026-11-07T00:02:00Z",
                    "completed_at": None,
                },
            ]
        }
    }
    github = GhApi("DDD-Enterprises/dopemux-mvp")
    github._api = lambda path: pages[1]  # type: ignore[method-assign]
    assert github.check_conclusion(PR_HEAD, AUDIT_CHECK) is None


def test_cli_writes_a_refusal(tmp_path, monkeypatch):
    from scripts.ci.merge_queue_carry_forward import main

    out = tmp_path / "carry.json"
    monkeypatch.setattr(
        "scripts.ci.merge_queue_carry_forward.git_parents",
        lambda _repo, _sha: (BASE,),
    )
    code = main(
        [
            "--repo",
            "DDD-Enterprises/dopemux-mvp",
            "--head-sha",
            QUEUE,
            "--base-sha",
            BASE,
            "--head-ref",
            "gh-readonly-queue/main/pr-1466-abcdef0",
            "--out",
            str(out),
        ]
    )
    assert code == 1
    assert json.loads(out.read_text(encoding="utf-8"))["ok"] is False
