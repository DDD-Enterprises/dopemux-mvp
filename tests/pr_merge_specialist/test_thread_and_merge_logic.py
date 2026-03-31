from __future__ import annotations

from pathlib import Path

from dopemux_pr_merge_specialist import engine
from dopemux_pr_merge_specialist.schema import (
    BlockerType,
    Finding,
    FindingSeverity,
    MergeActionType,
    MergeDecision,
    PRState,
    PullRequestState,
    ReviewThread,
    ThreadComment,
    ValidationReport,
    ValidationStatus,
)


class DummyClient:
    def fetch_pr(self, pr_id: int) -> dict:
        return {"state": "MERGED"}

    def invalidate(self, prefix: str) -> None:
        return None


def _policy() -> dict:
    return {
        "thread_rules": {
            "auto_resolve_outdated": True,
            "auto_resolve_resolution_signals": True,
            "resolution_markers": ["addressed", "acknowledged"],
            "objection_markers": ["not fixed", "still"],
            "implementable_patterns": ["```suggestion", "change <code>", "conflict marker", "<<<<<<< head"],
        },
        "conflict_rules": {
            "strict": True,
            "canonical_head_markers": ["keep the current version"],
        },
        "timeouts": {"subprocess_seconds": 5, "gh_seconds": 5},
    }


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
    disposition = engine.decide_thread_disposition(thread, validation_green=True, policy=_policy())
    assert disposition.disposition == "auto_resolve_outdated"


def test_addressed_thread_auto_resolves_even_if_not_outdated():
    thread = ReviewThread(
        id="T2",
        is_resolved=False,
        is_outdated=False,
        viewer_can_resolve=True,
        path="src/example.py",
        comments=[
            ThreadComment(id="C1", author="copilot-pull-request-reviewer", body="Please tighten this loop.", created_at="2026-03-12T00:00:00Z", path="src/example.py", line=10, original_line=10),
            ThreadComment(id="C2", author="hu3mann", body="Addressed in latest push.", created_at="2026-03-12T00:10:00Z", path="src/example.py", line=10, original_line=10),
            ThreadComment(id="C3", author="google-labs-jules", body="Acknowledged.", created_at="2026-03-12T00:11:00Z", path="src/example.py", line=10, original_line=10),
        ],
    )
    disposition = engine.decide_thread_disposition(thread, validation_green=True, policy=_policy())
    assert disposition.disposition == "auto_resolve_outdated"


def test_implement_disposition_for_conflict_marker_resolution_comment():
    thread = _thread(
        outdated=False,
        body="Remove the Git conflict markers and keep the code already present between <code><<<<<<< HEAD</code> and <code>=======</code>.",
    )
    disposition = engine.decide_thread_disposition(thread, validation_green=True, policy=_policy())
    assert disposition.disposition == "implement"


def test_merge_fallback_to_auto_when_policy_requires_queue(monkeypatch, tmp_path: Path):
    calls = []

    def fake_execute(cmd, *, execute, cwd, commands_log, timeout_seconds=600):
        calls.append(cmd)
        if len(calls) == 1:
            return engine.CommandResult(command=list(cmd), returncode=1, stdout="", stderr="merge queue required")
        return engine.CommandResult(command=list(cmd), returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(engine, "execute_or_dry_run", fake_execute)

    decision = MergeDecision(
        action=MergeActionType.REBASE_MERGE,
        command=["gh", "pr", "merge", "42", "--rebase", "--delete-branch"],
        reason="ready",
        reason_code="rebase_merge_ready",
    )

    result = engine.run_merge_with_fallback(
        decision=decision,
        pr_id=42,
        execute=True,
        repo=None,
        commands_log=tmp_path / "commands.txt",
        repo_root=tmp_path,
        policy={"timeouts": {"subprocess_seconds": 5}},
        client=DummyClient(),
    )

    assert result.action == MergeActionType.AUTO_MERGE_FALLBACK
    assert "--auto" in result.command
    assert result.reason_code == "merge_queue_required"


def test_conflict_analysis_explicitly_rejects_easy_defaults(tmp_path: Path):
    pr = PullRequestState(
        pr_id=77,
        title="Conflict PR",
        author="tester",
        state="OPEN",
        base_ref="main",
        head_ref="feature/conflict",
        ci_status="SUCCESS",
        mergeable="CONFLICTING",
        merge_state_status="DIRTY",
        review_decision="APPROVED",
        lifecycle_state=PRState.DISCOVERED,
    )

    md = engine.build_conflict_analysis(pr=pr, worktree_path=None, rebase_error="conflict in src/example.py", policy={"conflict_rules": {"strict": True}})
    assert "Reject blanket `-X ours/-X theirs` strategies" in md


def test_truth_sources_include_validation_status():
    report = ValidationReport(
        status=ValidationStatus.NOT_EXECUTED,
        required_for_merge_ready=True,
        steps=[],
        attempts=0,
        remediation_applied=False,
    )
    sources = engine.truth_sources_for(
        {
            "summary": engine.summarize_checks([]),
            "review_decision": "APPROVED",
            "mergeable": "MERGEABLE",
            "merge_state_status": "CLEAN",
            "blocker_types": [],
            "warning_types": [],
        },
        report,
        {"_meta": {"fingerprint": "abc"}},
    )
    assert sources[2].status == ValidationStatus.NOT_EXECUTED.value


def test_decide_merge_action_returns_rebase_command_when_green():
    pr = PullRequestState(
        pr_id=42,
        title="Ready PR",
        author="tester",
        state="OPEN",
        base_ref="main",
        head_ref="feature/ready",
        ci_status="SUCCESS",
        mergeable="MERGEABLE",
        merge_state_status="CLEAN",
        review_decision="APPROVED",
        lifecycle_state=PRState.MERGE_READY,
    )
    report = ValidationReport(
        status=ValidationStatus.PASSED,
        required_for_merge_ready=True,
        steps=[],
        attempts=1,
        remediation_applied=False,
    )

    result = engine.decide_merge_action(pr=pr, findings=[], validation_report=report)

    assert result.action == MergeActionType.REBASE_MERGE
    assert result.command == ["gh", "pr", "merge", "42", "--rebase", "--delete-branch"]


def test_decide_merge_action_returns_auto_merge_command_for_pending_checks():
    pr = PullRequestState(
        pr_id=43,
        title="Pending checks PR",
        author="tester",
        state="OPEN",
        base_ref="main",
        head_ref="feature/pending",
        ci_status="PENDING",
        mergeable="MERGEABLE",
        merge_state_status="BLOCKED",
        review_decision="APPROVED",
        lifecycle_state=PRState.MERGE_BLOCKED,
    )
    report = ValidationReport(
        status=ValidationStatus.PASSED,
        required_for_merge_ready=True,
        steps=[],
        attempts=1,
        remediation_applied=False,
    )
    findings = [
        Finding(
            kind=FindingSeverity.BLOCKER,
            finding_type=BlockerType.REQUIRED_CHECK_PENDING.value,
            message="Required checks pending",
        )
    ]

    result = engine.decide_merge_action(pr=pr, findings=findings, validation_report=report)

    assert result.action == MergeActionType.AUTO_MERGE_FALLBACK
    assert result.command == ["gh", "pr", "merge", "43", "--auto", "--rebase", "--delete-branch"]
