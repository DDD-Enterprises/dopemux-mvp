from __future__ import annotations

from pathlib import Path

from dopemux_pr_merge_specialist import cli
from dopemux_pr_merge_specialist.schema import MergeDecision, ReviewThread, ThreadComment


def _thread(*, outdated: bool, body: str, author: str = "github-code-quality") -> ReviewThread:
    return ReviewThread(
        id="T1",
        is_resolved=False,
        is_outdated=outdated,
        viewer_can_resolve=True,
        path="src/example.py",
        line=10,
        original_line=10,
        original_start_line=10,
        comments=[
            ThreadComment(
                id="C1",
                author=author,
                body=body,
                created_at="2026-03-12T00:00:00Z",
                path="src/example.py",
                line=10,
                original_line=10,
            )
        ],
    )


def test_outdated_thread_auto_resolve_when_green_and_no_objection():
    thread = _thread(outdated=True, body="Looks good now")
    disposition = cli._decide_thread_disposition(thread, validation_green=True)
    assert disposition.disposition == "auto_resolve_outdated"


def test_addressed_and_acknowledged_thread_auto_resolves_even_if_not_outdated():
    thread = ReviewThread(
        id="T2",
        is_resolved=False,
        is_outdated=False,
        viewer_can_resolve=True,
        path="src/example.py",
        comments=[
            ThreadComment(
                id="C1",
                author="copilot-pull-request-reviewer",
                body="Please tighten this loop.",
                created_at="2026-03-12T00:00:00Z",
                path="src/example.py",
                line=10,
                original_line=10,
            ),
            ThreadComment(
                id="C2",
                author="hu3mann",
                body="Addressed in latest push.",
                created_at="2026-03-12T00:10:00Z",
                path="src/example.py",
                line=10,
                original_line=10,
            ),
            ThreadComment(
                id="C3",
                author="google-labs-jules",
                body="Acknowledged.",
                created_at="2026-03-12T00:11:00Z",
                path="src/example.py",
                line=10,
                original_line=10,
            ),
        ],
    )
    disposition = cli._decide_thread_disposition(thread, validation_green=True)
    assert disposition.disposition == "auto_resolve_outdated"


def test_implement_disposition_for_machine_applicable_pattern():
    thread = _thread(
        outdated=False,
        body="Please change <code>import os</code> to <code># removed</code>",
    )
    disposition = cli._decide_thread_disposition(thread, validation_green=True)
    assert disposition.disposition == "implement"


def test_implement_disposition_for_conflict_marker_resolution_comment():
    thread = _thread(
        outdated=False,
        body=(
            "Remove the Git conflict markers and keep the code already present "
            "between <code><<<<<<< HEAD</code> and <code>=======</code>."
        ),
    )
    disposition = cli._decide_thread_disposition(thread, validation_green=True)
    assert disposition.disposition == "implement"


def test_decline_disposition_for_non_machine_applicable_comment():
    thread = _thread(outdated=False, body="Can we rethink this architecture section?")
    disposition = cli._decide_thread_disposition(thread, validation_green=True)
    assert disposition.disposition == "decline_with_rationale"


def test_merge_fallback_to_auto_when_rebase_disallowed(monkeypatch, tmp_path: Path):
    calls = []

    def fake_execute(cmd, *, execute, cwd, commands_log):
        calls.append(cmd)
        if len(calls) == 1:
            return cli.CommandResult(command=list(cmd), returncode=1, stdout="", stderr="merge queue required")
        return cli.CommandResult(command=list(cmd), returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(cli, "_execute_or_dry_run", fake_execute)

    decision = MergeDecision(
        action="rebase_merge",
        command=["gh", "pr", "merge", "42", "--rebase", "--delete-branch"],
        reason="ready",
    )

    result = cli._run_merge_with_fallback(
        decision=decision,
        pr_id=42,
        execute=True,
        repo=None,
        commands_log=tmp_path / "commands.txt",
    )

    assert result.action == "auto_merge_fallback"
    assert "--auto" in result.command


def test_merge_treats_already_merged_cleanup_failure_as_success(monkeypatch, tmp_path: Path):
    calls = []

    def fake_execute(cmd, *, execute, cwd, commands_log):
        calls.append(cmd)
        return cli.CommandResult(
            command=list(cmd),
            returncode=1,
            stdout="",
            stderr="! Pull request was already merged\nfailed to delete local branch branch-used-by-worktree",
        )

    def fake_run(cmd, *, cwd=None):
        return cli.CommandResult(command=list(cmd), returncode=0, stdout="MERGED\n", stderr="")

    monkeypatch.setattr(cli, "_execute_or_dry_run", fake_execute)
    monkeypatch.setattr(cli, "_run_cmd", fake_run)

    decision = MergeDecision(
        action="rebase_merge",
        command=["gh", "pr", "merge", "203", "--rebase", "--delete-branch"],
        reason="ready",
    )

    result = cli._run_merge_with_fallback(
        decision=decision,
        pr_id=203,
        execute=True,
        repo=None,
        commands_log=tmp_path / "commands.txt",
    )

    assert result.action == "rebase_merge"
    assert "already merged" in result.reason.lower()


def test_conflict_analysis_explicitly_rejects_easy_defaults(tmp_path: Path):
    pr = cli.PRState(
        pr_id=77,
        title="Conflict PR",
        author="tester",
        state="OPEN",
        base_ref="main",
        head_ref="feature/conflict",
        ci_status="SUCCESS",
        mergeable="CONFLICTING",
        merge_state_status="DIRTY",
        review_decision="",
    )

    md = cli._build_conflict_analysis(
        pr=pr,
        worktree_path=None,
        rebase_error="conflict in src/example.py",
        strict_conflicts=True,
    )

    assert "Reject blanket `-X ours/-X theirs` strategies" in md


def test_conflict_analysis_includes_hunks_when_local_conflicts_exist(monkeypatch, tmp_path: Path):
    conflicted = tmp_path / "src" / "conflict.py"
    conflicted.parent.mkdir(parents=True)
    conflicted.write_text(
        "before\n<<<<<<< HEAD\nleft\n=======\nright\n>>>>>>> branch\nafter\n",
        encoding="utf-8",
    )
    pr = cli.PRState(
        pr_id=78,
        title="Conflict PR",
        author="tester",
        state="OPEN",
        base_ref="main",
        head_ref="feature/conflict",
        ci_status="SUCCESS",
        mergeable="CONFLICTING",
        merge_state_status="DIRTY",
        review_decision="",
    )
    monkeypatch.setattr(cli, "_conflict_files", lambda worktree_path: ["src/conflict.py"])
    monkeypatch.setattr(cli, "_recent_file_history", lambda worktree_path, rel_path, limit=5: ["abc1234 prior change"])

    md = cli._build_conflict_analysis(
        pr=pr,
        worktree_path=tmp_path,
        rebase_error="conflict in src/conflict.py",
        strict_conflicts=True,
    )

    assert "## Conflict Hunks" in md
    assert "src/conflict.py" in md
    assert "<<<<<<< HEAD" in md


def test_wait_for_green_checks_polls_until_success(monkeypatch):
    responses = iter(
        [
            (False, {"checks_total": 1, "checks_success": 0, "checks_failure": 0, "checks_pending": 1}),
            (True, {"checks_total": 1, "checks_success": 1, "checks_failure": 0, "checks_pending": 0}),
        ]
    )

    monkeypatch.setattr(cli, "_checks_green", lambda pr_id, repo: next(responses))
    monkeypatch.setattr(cli.time, "sleep", lambda _: None)

    green, payload, wait = cli._wait_for_green_checks(
        pr_id=42,
        repo=None,
        execute=True,
        max_wait_seconds=5,
        poll_interval_seconds=1,
    )

    assert green is True
    assert payload["checks_pending"] == 0
    assert wait["waited"] is True
    assert wait["attempts"] == 2


def test_attempt_rebase_reproduces_local_conflicts_for_analysis(monkeypatch, tmp_path: Path):
    commands = []

    def fake_execute(cmd, *, execute, cwd, commands_log):
        return cli.CommandResult(
            command=list(cmd),
            returncode=1,
            stdout="",
            stderr="GraphQL: rebase conflict between base and head (updatePullRequestBranch)",
        )

    def fake_run(cmd, *, cwd=None):
        commands.append(list(cmd))
        if cmd[:3] == ["git", "fetch", "origin"]:
            return cli.CommandResult(command=list(cmd), returncode=0, stdout="", stderr="")
        if cmd[:2] == ["git", "rebase"]:
            return cli.CommandResult(command=list(cmd), returncode=1, stdout="", stderr="conflict in docs/file.md")
        return cli.CommandResult(command=list(cmd), returncode=0, stdout="", stderr="")

    monkeypatch.setattr(cli, "_execute_or_dry_run", fake_execute)
    monkeypatch.setattr(cli, "_run_cmd", fake_run)

    ok, conflict, message = cli._attempt_rebase(
        pr_id=197,
        worktree_path=tmp_path,
        base_ref="main",
        head_ref="feature/conflict",
        commands_log=tmp_path / "commands.txt",
        execute=True,
    )

    assert ok is False
    assert conflict is True
    assert "Local conflict reproduction" in message
    assert ["git", "fetch", "origin", "main"] in commands
    assert ["git", "rebase", "origin/main"] in commands


def test_apply_suggestion_resolves_conflict_markers_using_head_side(tmp_path: Path):
    file_path = tmp_path / "src" / "example.py"
    file_path.parent.mkdir(parents=True)
    file_path.write_text(
        "<<<<<<< HEAD\nprint('head')\n=======\nprint('other')\n>>>>>>> branch\n",
        encoding="utf-8",
    )
    thread = ReviewThread(
        id="T3",
        is_resolved=False,
        is_outdated=False,
        viewer_can_resolve=True,
        path="src/example.py",
        line=1,
        original_line=1,
        original_start_line=1,
        comments=[
            ThreadComment(
                id="C1",
                author="github-code-quality",
                body=(
                    "Please remove the conflict markers and keep the code between "
                    "<code><<<<<<< HEAD</code> and <code>=======</code>."
                ),
                created_at="2026-03-12T00:00:00Z",
                path="src/example.py",
                line=1,
                original_line=1,
            )
        ],
    )

    ok, reason = cli._apply_suggestion_to_file(
        worktree_path=tmp_path,
        thread=thread,
        comment=thread.comments[0],
    )

    assert ok is True
    assert "Resolved conflict markers" in reason
    assert file_path.read_text(encoding="utf-8") == "print('head')\n"
