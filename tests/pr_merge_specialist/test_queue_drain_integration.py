from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace

from dopemux_pr_merge_specialist import closed_loop_engine
from dopemux_pr_merge_specialist import engine
from dopemux_pr_merge_specialist import queue_drain as queue_drain_module
from dopemux_pr_merge_specialist.plan_builder import build_plan_result, write_pr_state_artifact
from dopemux_pr_merge_specialist.preflight import build_run_paths, pr_dir_for
from dopemux_pr_merge_specialist.schema import MergeActionType, MergeDecision, PRResult, PRState, PullRequestState, ValidationReport, ValidationStatus, ValidationStepResult
from dopemux_pr_merge_specialist import cli as pr_merge_cli


class FakeGitHubClient:
    def __init__(self, *, repo, repo_root, policy):
        self.repo = repo
        self.repo_root = repo_root
        self.policy = policy
        self.invalidations = []

    def cache_summary(self) -> dict:
        return {"hits": 0, "misses": 0, "invalidations": len(self.invalidations), "keys": []}

    def invalidate(self, prefix: str) -> None:
        self.invalidations.append(prefix)

    def resolve_repo_slug(self) -> str:
        return "DDD-Enterprises/dopemux-mvp"

    def fetch_open_prs(self, limit: int) -> list[dict]:
        return [
            {
                "number": 190,
                "title": "target",
                "author": {"login": "tester"},
                "state": "OPEN",
                "statusCheckRollup": [{"status": "COMPLETED", "conclusion": "SUCCESS", "isRequired": True}],
                "mergeable": "MERGEABLE",
                "mergeStateStatus": "CLEAN",
                "labels": [],
                "reviewDecision": "APPROVED",
                "updatedAt": "2026-03-12T00:00:00Z",
                "baseRefName": "main",
                "headRefName": "feature/190",
                "headRefOid": "head-190",
                "baseRefOid": "base-main",
                "isDraft": False,
                "additions": 3,
                "deletions": 1,
                "changedFiles": 1,
                "url": "https://example.com/pr/190",
            }
        ]

    def fetch_pr(self, pr_id: int) -> dict:
        return self.fetch_open_prs(1)[0]

    def fetch_pr_head_oid(self, pr_id: int):
        return "head-190", None

    def fetch_review_threads(self, pr_id: int):
        return []

    def query_checks(self, pr_id: int, pr_payload=None) -> dict:
        return {
            "summary": engine.summarize_checks([{"status": "COMPLETED", "conclusion": "SUCCESS", "isRequired": True}]),
            "review_decision": "APPROVED",
            "mergeable": "MERGEABLE",
            "merge_state_status": "CLEAN",
            "blocker_types": [],
            "warning_types": [],
        }

    def rate_limit_snapshot(self) -> dict:
        return {"available": True, "resources": {}}

    def find_global_fix_prs(self) -> list[dict]:
        return []


def _make_result(
    *,
    pr_id: int,
    lifecycle_state: str,
    ci_status: str,
    merge_decision: MergeDecision | None = None,
    auto_merge_enabled: bool = False,
    artifacts: dict[str, str] | None = None,
    validation_status: ValidationStatus = ValidationStatus.PASSED,
) -> PRResult:
    return PRResult(
        run_id="testrun",
        pr_state=PullRequestState(
            pr_id=pr_id,
            title=f"PR {pr_id}",
            author="tester",
            state="OPEN",
            base_ref="main",
            head_ref=f"feature/{pr_id}",
            ci_status=ci_status,
            mergeable="MERGEABLE",
            merge_state_status="CLEAN",
            review_decision="APPROVED",
            auto_merge_enabled=auto_merge_enabled,
            additions=3,
            deletions=1,
            changed_files=1,
            lifecycle_state=PRState(lifecycle_state),
            head_sha=f"head-{pr_id}",
            base_sha="base-main",
        ),
        lifecycle_state=lifecycle_state,
        apply_actions=[],
        merge_decision=merge_decision,
        findings=[],
        truth_sources=[],
        precedence_order=[],
        decision_basis={},
        validation_report=ValidationReport(
            status=validation_status,
            required_for_merge_ready=True,
            steps=[],
            attempts=1,
            remediation_applied=False,
        ),
        thread_dispositions=[],
        fingerprint=None,
        artifacts=artifacts or {},
    )


def test_queue_scan_writes_v3_artifacts(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(engine, "GitHubClient", FakeGitHubClient)
    args = SimpleNamespace(
        repo=None,
        out_dir=str(tmp_path),
        policy=None,
        limit=20,
        strategy="hybrid",
        prioritize=[],
        only=[],
        run_id="scanrun",
    )

    rc = engine.queue_scan(args)
    assert rc == 0
    run_dir = tmp_path / "run_scanrun"
    assert (run_dir / "queue" / "QUEUE_SNAPSHOT.json").exists()
    assert (run_dir / "queue" / "ORDERING_PLAN.json").exists()
    assert (run_dir / "RUN_MANIFEST.json").exists()
    assert (run_dir / "POLICY_EFFECTIVE.json").exists()
    assert (run_dir / "RUN_SUMMARY.md").exists()


def test_queue_scan_reuses_matching_prior_validation_state(tmp_path: Path):
    client = FakeGitHubClient(repo=None, repo_root=tmp_path, policy={})
    args = SimpleNamespace(
        repo=None,
        out_dir=str(tmp_path),
        policy=None,
        limit=20,
        strategy="hybrid",
        prioritize=[],
        only=[],
        run_id="scanrun",
    )
    policy = {
        "validation": {"require_local_validation_for_merge_ready": True},
        "conflict_rules": {"strict": True},
        "thread_rules": {"resolution_markers": [], "objection_markers": []},
    }

    _, threads, pr, check_payload = queue_drain_module._load_pr_context(
        client=client,
        pr_id=190,
    )
    previous_result = build_plan_result(
        active_run_id="previous",
        pr=pr,
        threads=threads,
        check_payload=check_payload,
        validation_report=ValidationReport(
            status=ValidationStatus.PASSED,
            required_for_merge_ready=True,
            steps=[],
            attempts=1,
            remediation_applied=False,
        ),
        policy=policy,
    )
    _, _, previous_pr_root = build_run_paths(str(tmp_path), "previous")
    write_pr_state_artifact(pr_dir_for(previous_pr_root, 190), previous_result)

    results = queue_drain_module.queue_scan_internal(
        args,
        client,
        policy,
        "scanrun",
    )

    assert len(results) == 1
    assert results[0].validation_report is not None
    assert results[0].validation_report.status == ValidationStatus.PASSED
    assert results[0].lifecycle_state == "merge_ready"


def test_queue_drain_hands_off_post_apply_passive_queued_result(
    monkeypatch, tmp_path: Path
):
    initial_result = _make_result(
        pr_id=190,
        lifecycle_state=PRState.APPLY_BLOCKED.value,
        ci_status="FAILURE",
    )
    prepared_result = _make_result(
        pr_id=190,
        lifecycle_state=PRState.QUEUED_FOR_MERGE.value,
        ci_status="SUCCESS",
        auto_merge_enabled=True,
        merge_decision=MergeDecision(
            action=MergeActionType.REBASE_MERGE,
            command=["gh", "pr", "merge", "190", "--rebase", "--delete-branch"],
            reason="ready",
            reason_code="rebase_merge_ready",
        ),
        artifacts={"operator_state": "queued_for_merge"},
    )

    merge_handoffs: list[int] = []

    class FakeClosedLoopEngine:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def run_cycle(self, _case_id: str, _report: dict) -> SimpleNamespace:
            return SimpleNamespace(next_tactic="APPLY_FIX")

        def emit_trace_artifacts(self, _trace: object, _path: Path) -> None:
            return None

    monkeypatch.setattr(closed_loop_engine, "ClosedLoopEngine", FakeClosedLoopEngine)
    monkeypatch.setattr(queue_drain_module, "GitHubClient", FakeGitHubClient)
    monkeypatch.setattr(
        queue_drain_module,
        "load_effective_policy",
        lambda *_args, **_kwargs: {},
    )
    monkeypatch.setattr(queue_drain_module, "_get_ops_engine", lambda _run_dir: object())
    monkeypatch.setattr(
        queue_drain_module,
        "queue_scan_internal",
        lambda *_args, **_kwargs: [initial_result],
    )
    monkeypatch.setattr(
        queue_drain_module,
        "_handle_global_ci_blockers",
        lambda *_args, **_kwargs: {},
    )
    monkeypatch.setattr(
        queue_drain_module,
        "_ignite_speculative_train",
        lambda *_args, **_kwargs: ([], []),
    )
    monkeypatch.setattr(
        queue_drain_module,
        "acquire_queue_lock",
        lambda **_kwargs: (True, tmp_path / "queue.lock", None),
    )
    monkeypatch.setattr(
        queue_drain_module,
        "release_queue_lock",
        lambda _lock_path: None,
    )
    monkeypatch.setattr(queue_drain_module, "pr_apply", lambda _args, **_kw: prepared_result)

    def fake_merge_prepared_result(**kwargs):
        merge_handoffs.append(kwargs["prepared_result"].pr_state.pr_id)
        return kwargs["prepared_result"]

    monkeypatch.setattr(
        queue_drain_module,
        "_merge_prepared_result",
        fake_merge_prepared_result,
    )

    rc = queue_drain_module.queue_drain(
        SimpleNamespace(
            repo=None,
            out_dir=str(tmp_path),
            policy=None,
            execute=True,
            allow_dirty=True,
            limit=20,
            max_prs=1,
            max_passes=1,
            strategy="hybrid",
            prioritize=[],
            only=[],
            run_id="queuedhandoff",
        )
    )

    assert rc == 0
    assert merge_handoffs == [190]


def test_queue_drain_orchestrates_phase_functions(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(engine, "GitHubClient", FakeGitHubClient)

    apply_calls = []
    merge_calls = []

    def fake_apply(args):
        apply_calls.append(args.id)
        pr_dir = Path(args.out_dir) / f"run_{args.run_id}" / "pr" / str(args.id)
        pr_dir.mkdir(parents=True, exist_ok=True)
        (pr_dir / "APPLY.json").write_text(
            json.dumps(
                {
                    "run_id": args.run_id,
                    "pr_state": FakeGitHubClient(repo=None, repo_root=Path.cwd(), policy={}).fetch_pr(args.id) | {"headRefName": "feature/190"},
                    "lifecycle_state": "applied",
                    "apply_actions": [],
                    "merge_decision": None,
                    "blockers": [],
                    "warnings": [],
                    "observations": [],
                    "truth_sources": [],
                    "precedence_order": [],
                    "decision_basis": {},
                    "validation_report": ValidationReport(
                        status=ValidationStatus.PASSED,
                        required_for_merge_ready=True,
                        steps=[],
                        attempts=1,
                        remediation_applied=False,
                    ).to_dict(),
                    "thread_dispositions": [],
                    "fingerprint": None,
                    "artifacts": {},
                }
            ),
            encoding="utf-8",
        )
        return 0

    def fake_merge(args):
        merge_calls.append(args.id)
        pr_dir = Path(args.out_dir) / f"run_{args.run_id}" / "pr" / str(args.id)
        pr_dir.mkdir(parents=True, exist_ok=True)
        (pr_dir / "MERGE.json").write_text(
            json.dumps(
                {
                    "run_id": args.run_id,
                    "pr_state": {
                        "pr_id": args.id,
                        "title": "target",
                        "author": "tester",
                        "state": "OPEN",
                        "base_ref": "main",
                        "head_ref": "feature/190",
                        "ci_status": "SUCCESS",
                        "mergeable": "MERGEABLE",
                        "merge_state_status": "CLEAN",
                        "review_decision": "APPROVED",
                        "labels": [],
                        "updated_at": "2026-03-12T00:00:00Z",
                        "is_draft": False,
                        "additions": 3,
                        "deletions": 1,
                        "changed_files": 1,
                        "unresolved_threads": 0,
                        "active_unresolved_threads": 0,
                        "outdated_unresolved_threads": 0,
                        "pr_class": "READY",
                        "risk_score": 1.0,
                        "check_summary": None,
                        "lifecycle_state": "merged",
                        "head_sha": "head-190",
                        "base_sha": "base-main",
                    },
                    "lifecycle_state": "merged",
                    "apply_actions": [],
                    "merge_decision": {
                        "action": "rebase_merge",
                        "command": ["gh", "pr", "merge", "190", "--rebase", "--delete-branch"],
                        "reason": "ready",
                        "reason_code": "rebase_merge_ready",
                    },
                    "blockers": [],
                    "warnings": [],
                    "observations": [],
                    "truth_sources": [],
                    "precedence_order": [],
                    "decision_basis": {},
                    "validation_report": ValidationReport(
                        status=ValidationStatus.PASSED,
                        required_for_merge_ready=True,
                        steps=[],
                        attempts=1,
                        remediation_applied=False,
                    ).to_dict(),
                    "thread_dispositions": [],
                    "fingerprint": None,
                    "artifacts": {},
                }
            ),
            encoding="utf-8",
        )
        return 0

    monkeypatch.setattr(engine, "pr_apply", fake_apply)
    monkeypatch.setattr(engine, "pr_merge", fake_merge)
    monkeypatch.setattr(engine, "update_remaining_pr_bases", lambda **kwargs: [])

    args = SimpleNamespace(
        repo=None,
        out_dir=str(tmp_path),
        policy=None,
        execute=False,
        allow_dirty=True,
        limit=20,
        max_prs=0,
        max_passes=1,
        strategy="hybrid",
        prioritize=[],
        only=[],
        run_id="drainrun",
    )

    rc = engine.queue_drain(args)
    assert rc == 0
    assert apply_calls == []
    assert merge_calls == []
    run_dir = tmp_path / "run_drainrun"
    assert run_dir.exists()


def test_cmd_flight_deck_routes_to_dashboard(monkeypatch):
    captured = {}

    def fake_cmd_flight(args):
        captured.update(vars(args))
        return 17

    monkeypatch.setattr(pr_merge_cli, "cmd_flight", fake_cmd_flight)

    rc = pr_merge_cli.cmd_flight_deck(
        Namespace(
            pr_id=218,
            auto_pilot=True,
            repo=None,
            out_dir="proof/pr_merge",
            policy=None,
            execute=False,
            allow_dirty=True,
        )
    )

    assert rc == 17
    assert captured["only"] == ["218"]
    assert captured["auto_pilot"] is True
    assert captured["limit"] == 50
    assert captured["strategy"] == "hybrid"


def test_remediate_ci_failure_uses_prompt_only_gemini_command(monkeypatch, tmp_path: Path):
    captured: dict[str, object] = {}

    class FakeStdout:
        def __init__(self) -> None:
            self._lines = iter(["gemini failed\n", ""])

        def readline(self) -> str:
            return next(self._lines)

    class FakeProcess:
        def __init__(self) -> None:
            self.stdout = FakeStdout()
            self.returncode = 2

        def wait(self, timeout=None) -> None:
            return None

    def fake_popen(cmd, **kwargs):
        captured["cmd"] = cmd
        captured["cwd"] = kwargs.get("cwd")
        return FakeProcess()

    monkeypatch.setattr(queue_drain_module.subprocess, "Popen", fake_popen)

    validation = ValidationReport(
        status=ValidationStatus.FAILED,
        required_for_merge_ready=True,
        steps=[
            ValidationStepResult(
                name="pre-commit",
                command="pre-commit run --all-files",
                status="failed",
                stderr="boom",
            )
        ],
        attempts=1,
        remediation_applied=False,
    )
    messages: list[str] = []

    remediated = queue_drain_module.remediate_ci_failure(
        tmp_path,
        validation,
        lambda message, *_: messages.append(message),
    )

    assert remediated is False
    assert captured["cwd"] == tmp_path
    assert captured["cmd"][0] == "gemini"
    assert "--prompt" in captured["cmd"]
    assert "--yolo" in captured["cmd"]
    assert "--skill" not in captured["cmd"]
    assert any("non-zero exit code" in message for message in messages)


def test_handle_global_ci_blockers_ignores_failed_global_fix_creation(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(
        queue_drain_module,
        "allowed_actions_for_result",
        lambda _result: ["APPLY_FIX"],
    )
    monkeypatch.setattr(
        queue_drain_module,
        "_create_global_fix_pr",
        lambda fingerprint, failed_step, client, repo_root: -1,
    )

    failed_validation = ValidationReport(
        status=ValidationStatus.FAILED,
        required_for_merge_ready=True,
        steps=[
            ValidationStepResult(
                name="pre-commit",
                command="pre-commit run --all-files",
                status="failed",
                stderr="boom",
            )
        ],
        attempts=1,
        remediation_applied=False,
    )
    results = [
        SimpleNamespace(
            pr_state=SimpleNamespace(pr_id=101),
            validation_report=failed_validation,
        ),
        SimpleNamespace(
            pr_state=SimpleNamespace(pr_id=102),
            validation_report=failed_validation,
        ),
    ]

    blocked_map = queue_drain_module._handle_global_ci_blockers(
        results,
        FakeGitHubClient(repo=None, repo_root=tmp_path, policy={}),
        tmp_path,
    )

    # Creation failed (-1), so no PRs should be in the blocked map
    assert blocked_map == {}


def test_global_fix_blocking_persists_across_passes(monkeypatch, tmp_path: Path):
    """
    When pass 1 detects a global CI blocker for 2+ PRs, the blocked dict persists
    so that pass 2 skips those PRs without re-running remediation.
    """
    initial_result_101 = _make_result(
        pr_id=101,
        lifecycle_state=PRState.APPLY_BLOCKED.value,
        ci_status="FAILURE",
    )
    initial_result_102 = _make_result(
        pr_id=102,
        lifecycle_state=PRState.APPLY_BLOCKED.value,
        ci_status="FAILURE",
    )

    run_cycle_calls: list[str] = []

    class FakeClosedLoopEngine:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def run_cycle(self, case_id: str, _report: dict) -> SimpleNamespace:
            run_cycle_calls.append(case_id)
            return SimpleNamespace(next_tactic="APPLY_FIX")

        def emit_trace_artifacts(self, _trace: object, _path: Path) -> None:
            return None

    pass_counter = [0]

    def fake_handle_global_ci_blockers(_results, _client, _worktree_dir):
        pass_counter[0] += 1
        if pass_counter[0] == 1:
            # Pass 1: both PRs are globally blocked by fix PR #999
            return {101: 999, 102: 999}
        # Pass 2+: no new blockers (already persisted in global_fix_blocked)
        return {}

    monkeypatch.setattr(closed_loop_engine, "ClosedLoopEngine", FakeClosedLoopEngine)
    monkeypatch.setattr(queue_drain_module, "GitHubClient", FakeGitHubClient)
    monkeypatch.setattr(
        queue_drain_module,
        "load_effective_policy",
        lambda *_args, **_kwargs: {},
    )
    monkeypatch.setattr(queue_drain_module, "_get_ops_engine", lambda _run_dir: object())
    monkeypatch.setattr(
        queue_drain_module,
        "queue_scan_internal",
        lambda *_args, **_kwargs: [initial_result_101, initial_result_102],
    )
    monkeypatch.setattr(
        queue_drain_module,
        "_handle_global_ci_blockers",
        fake_handle_global_ci_blockers,
    )
    monkeypatch.setattr(
        queue_drain_module,
        "_ignite_speculative_train",
        lambda *_args, **_kwargs: ([], []),
    )
    monkeypatch.setattr(
        queue_drain_module,
        "acquire_queue_lock",
        lambda **_kwargs: (True, tmp_path / "queue.lock", None),
    )
    monkeypatch.setattr(queue_drain_module, "release_queue_lock", lambda _lock_path: None)

    rc = queue_drain_module.queue_drain(
        SimpleNamespace(
            repo=None,
            out_dir=str(tmp_path),
            policy=None,
            execute=True,
            allow_dirty=True,
            limit=20,
            max_prs=0,
            max_passes=2,
            strategy="hybrid",
            prioritize=[],
            only=[],
            run_id="globalfixtest",
        )
    )

    assert rc == 0
    # PRs 101 and 102 are blocked by the global fix dict; run_cycle should never be called
    assert run_cycle_calls == []


def test_failed_remediation_excluded_from_active_results(monkeypatch, tmp_path: Path):
    """
    A PR that raises RuntimeError during APPLY_FIX in pass 1 must be excluded from
    active_results in pass 2 (failed_remediation_ids accumulates across passes).
    """
    failing_result = _make_result(
        pr_id=201,
        lifecycle_state=PRState.APPLY_BLOCKED.value,
        ci_status="FAILURE",
    )

    apply_call_count = [0]

    class FakeClosedLoopEngine:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def run_cycle(self, _case_id: str, _report: dict) -> SimpleNamespace:
            return SimpleNamespace(next_tactic="APPLY_FIX")

        def emit_trace_artifacts(self, _trace: object, _path: Path) -> None:
            return None

    def fake_pr_apply(_args, **_kw):
        apply_call_count[0] += 1
        raise RuntimeError("apply failed")

    monkeypatch.setattr(closed_loop_engine, "ClosedLoopEngine", FakeClosedLoopEngine)
    monkeypatch.setattr(queue_drain_module, "GitHubClient", FakeGitHubClient)
    monkeypatch.setattr(
        queue_drain_module,
        "load_effective_policy",
        lambda *_args, **_kwargs: {},
    )
    monkeypatch.setattr(queue_drain_module, "_get_ops_engine", lambda _run_dir: object())
    monkeypatch.setattr(
        queue_drain_module,
        "queue_scan_internal",
        lambda *_args, **_kwargs: [failing_result],
    )
    monkeypatch.setattr(
        queue_drain_module,
        "_handle_global_ci_blockers",
        lambda *_args, **_kwargs: {},
    )
    monkeypatch.setattr(
        queue_drain_module,
        "_ignite_speculative_train",
        lambda *_args, **_kwargs: ([], []),
    )
    monkeypatch.setattr(
        queue_drain_module,
        "acquire_queue_lock",
        lambda **_kwargs: (True, tmp_path / "queue.lock", None),
    )
    monkeypatch.setattr(queue_drain_module, "release_queue_lock", lambda _lock_path: None)
    monkeypatch.setattr(queue_drain_module, "pr_apply", fake_pr_apply)

    rc = queue_drain_module.queue_drain(
        SimpleNamespace(
            repo=None,
            out_dir=str(tmp_path),
            policy=None,
            execute=True,
            allow_dirty=True,
            limit=20,
            max_prs=0,
            max_passes=2,
            strategy="hybrid",
            prioritize=[],
            only=[],
            run_id="failedremedtest",
        )
    )

    assert rc == 0
    # pr_apply should be called exactly once (pass 1). Pass 2 should skip PR 201.
    assert apply_call_count[0] == 1


def test_speculative_train_single_candidate_skipped():
    """
    When only 1 PR is MERGE_READY with green CI, _ignite_speculative_train returns
    empty lists -- documents that single-candidate trains are intentionally skipped.
    """
    single_result = _make_result(
        pr_id=300,
        lifecycle_state=PRState.MERGE_READY.value,
        ci_status="SUCCESS",
    )

    merged, queued = queue_drain_module._ignite_speculative_train(
        results=[single_result],
        client=FakeGitHubClient(repo=None, repo_root=Path("."), policy={}),
        repo_root=Path("."),
        active_run_id="traintest",
        commands_log=Path("/dev/null"),
        policy={},
        execute=False,
    )

    assert merged == []
    assert queued == []


# --------------------------------------------------------------------------- #
# Strategy selection tests
# --------------------------------------------------------------------------- #

from dopemux_pr_merge_specialist.strategy_library import (
    select_strategy,
    StrategyAssignment,
    TRAIN_ELIGIBLE_STRATEGIES,
    STRATEGY_EXECUTION_ORDER,
)
from dopemux_pr_merge_specialist.closed_loop_engine import ClosedLoopTrace


def test_select_strategy_clean_merge_ready_pr():
    """MERGE_READY + green CI -> DIRECT_REBASE_MERGE."""
    result = _make_result(
        pr_id=400,
        lifecycle_state=PRState.MERGE_READY.value,
        ci_status="SUCCESS",
    )
    assignment = select_strategy(result, {})
    assert assignment.strategy_id == "DIRECT_REBASE_MERGE"
    assert assignment.priority_boost == 30.0


def test_select_strategy_ci_failure_pr():
    """CI_ONLY class -> PATCH_ISOLATION_PLAN."""
    result = PRResult(
        run_id="testrun",
        pr_state=PullRequestState(
            pr_id=401,
            title="PR 401",
            author="tester",
            state="OPEN",
            base_ref="main",
            head_ref="feature/401",
            ci_status="FAILURE",
            mergeable="MERGEABLE",
            merge_state_status="CLEAN",
            review_decision="APPROVED",
            auto_merge_enabled=False,
            additions=3,
            deletions=1,
            changed_files=1,
            lifecycle_state=PRState.APPLY_BLOCKED,
            head_sha="head-401",
            base_sha="base-main",
            pr_class="CI_ONLY",
        ),
        lifecycle_state=PRState.APPLY_BLOCKED.value,
        apply_actions=[],
        merge_decision=None,
        findings=[],
        truth_sources=[],
        precedence_order=[],
        decision_basis={},
        validation_report=ValidationReport(
            status=ValidationStatus.FAILED,
            required_for_merge_ready=True,
            steps=[],
            attempts=1,
            remediation_applied=False,
        ),
        thread_dispositions=[],
        fingerprint=None,
        artifacts={},
    )
    assignment = select_strategy(result, {})
    assert assignment.strategy_id == "PATCH_ISOLATION_PLAN"
    assert assignment.priority_boost == 50.0


def test_select_strategy_mixed_blockers_pr():
    """MIXED class (non-conflicting) -> STAGED_SEQUENCE_MERGE."""
    result = PRResult(
        run_id="testrun",
        pr_state=PullRequestState(
            pr_id=402,
            title="PR 402",
            author="tester",
            state="OPEN",
            base_ref="main",
            head_ref="feature/402",
            ci_status="FAILURE",
            mergeable="MERGEABLE",
            merge_state_status="BEHIND",
            review_decision="CHANGES_REQUESTED",
            auto_merge_enabled=False,
            additions=10,
            deletions=5,
            changed_files=3,
            lifecycle_state=PRState.APPLY_BLOCKED,
            head_sha="head-402",
            base_sha="base-main",
            pr_class="MIXED",
        ),
        lifecycle_state=PRState.APPLY_BLOCKED.value,
        apply_actions=[],
        merge_decision=None,
        findings=[],
        truth_sources=[],
        precedence_order=[],
        decision_basis={},
        validation_report=None,
        thread_dispositions=[],
        fingerprint=None,
        artifacts={},
    )
    assignment = select_strategy(result, {})
    assert assignment.strategy_id == "STAGED_SEQUENCE_MERGE"
    assert assignment.priority_boost == 5.0


def test_select_strategy_conflicting_eligible_pr():
    """Conflicting PR with eligible recovery -> delegates to recommend_conflict_strategy."""
    result = PRResult(
        run_id="testrun",
        pr_state=PullRequestState(
            pr_id=403,
            title="PR 403",
            author="tester",
            state="OPEN",
            base_ref="main",
            head_ref="feature/403",
            ci_status="SUCCESS",
            mergeable="CONFLICTING",
            merge_state_status="DIRTY",
            review_decision="APPROVED",
            auto_merge_enabled=False,
            additions=3,
            deletions=1,
            changed_files=1,
            lifecycle_state=PRState.APPLY_BLOCKED,
            head_sha="head-403",
            base_sha="base-main",
            pr_class="CONFLICTS_ONLY",
            # No conflict-blocking labels -> eligible for recovery
        ),
        lifecycle_state=PRState.APPLY_BLOCKED.value,
        apply_actions=[],
        merge_decision=None,
        findings=[],
        truth_sources=[],
        precedence_order=[],
        decision_basis={},
        validation_report=None,
        thread_dispositions=[],
        fingerprint=None,
        artifacts={},
    )
    policy = {"conflict_rules": {"auto_recovery": {"require_opt_in_label": False}}}
    assignment = select_strategy(result, policy)
    # Default conflict strategy (no file paths) -> OURS_THEN_PORT_SELECTIVE
    assert assignment.strategy_id == "OURS_THEN_PORT_SELECTIVE"
    assert assignment.priority_boost == 10.0


def test_train_filters_ineligible_strategies():
    """
    Train should skip PRs whose strategy is not in TRAIN_ELIGIBLE_STRATEGIES.
    If filtering leaves < 2 eligible candidates, train returns empty.
    """
    # PR 501: MERGE_READY -> DIRECT_REBASE_MERGE (eligible)
    eligible_result = _make_result(
        pr_id=501,
        lifecycle_state=PRState.MERGE_READY.value,
        ci_status="SUCCESS",
    )
    # PR 502: MIXED class -> STAGED_SEQUENCE_MERGE (NOT eligible for train)
    ineligible_result = PRResult(
        run_id="testrun",
        pr_state=PullRequestState(
            pr_id=502,
            title="PR 502",
            author="tester",
            state="OPEN",
            base_ref="main",
            head_ref="feature/502",
            ci_status="SUCCESS",
            mergeable="MERGEABLE",
            merge_state_status="CLEAN",
            review_decision="APPROVED",
            auto_merge_enabled=False,
            additions=10,
            deletions=5,
            changed_files=3,
            lifecycle_state=PRState.MERGE_READY,
            head_sha="head-502",
            base_sha="base-main",
            pr_class="MIXED",
            active_unresolved_threads=0,
        ),
        lifecycle_state=PRState.MERGE_READY.value,
        apply_actions=[],
        merge_decision=None,
        findings=[],
        truth_sources=[],
        precedence_order=[],
        decision_basis={},
        validation_report=ValidationReport(
            status=ValidationStatus.PASSED,
            required_for_merge_ready=True,
            steps=[],
            attempts=1,
            remediation_applied=False,
        ),
        thread_dispositions=[],
        fingerprint=None,
        artifacts={},
    )

    merged, queued = queue_drain_module._ignite_speculative_train(
        results=[eligible_result, ineligible_result],
        client=FakeGitHubClient(repo=None, repo_root=Path("."), policy={}),
        repo_root=Path("."),
        active_run_id="trainfilter",
        commands_log=Path("/dev/null"),
        policy={},
        execute=False,
    )

    # Only 1 eligible PR after filtering -> train skipped
    assert merged == []
    assert queued == []


def test_train_orders_by_strategy():
    """DIRECT_REBASE_MERGE (order 0) should be processed before PATCH_ISOLATION_PLAN (order 1)."""
    assert STRATEGY_EXECUTION_ORDER["DIRECT_REBASE_MERGE"] < STRATEGY_EXECUTION_ORDER["PATCH_ISOLATION_PLAN"]
    assert STRATEGY_EXECUTION_ORDER["PATCH_ISOLATION_PLAN"] < STRATEGY_EXECUTION_ORDER["STAGED_SEQUENCE_MERGE"]
    # Verify all train-eligible strategies have defined order
    for s in TRAIN_ELIGIBLE_STRATEGIES:
        assert s in STRATEGY_EXECUTION_ORDER


def test_closed_loop_trace_includes_strategy():
    """ClosedLoopTrace should carry strategy_id for observability."""
    trace = ClosedLoopTrace(
        pr_id="100",
        cycle_id="abc",
        implicit_actions=[],
        state_before={},
        state_after={},
        next_tactic="MERGE",
        posture="GO_SUPERVISED_ONLY",
        computed_at=0.0,
        strategy_id="DIRECT_REBASE_MERGE",
    )
    assert trace.strategy_id == "DIRECT_REBASE_MERGE"

    # Default should be empty string
    trace_default = ClosedLoopTrace(
        pr_id="100",
        cycle_id="abc",
        implicit_actions=[],
        state_before={},
        state_after={},
        next_tactic="MERGE",
        posture="GO_SUPERVISED_ONLY",
        computed_at=0.0,
    )
    assert trace_default.strategy_id == ""


def test_closed_loop_engine_populates_strategy_in_trace():
    """run_cycle should populate strategy_id based on PR state signals."""
    from dopemux_pr_merge_specialist.closed_loop_engine import ClosedLoopEngine

    engine = ClosedLoopEngine(ops_engine=object(), strategy_library={})
    report = {
        "lifecycle_state": "merge_ready",
        "pr_state": {
            "pr_class": "READY",
            "ci_status": "SUCCESS",
            "mergeable": "MERGEABLE",
            "merge_state_status": "CLEAN",
        },
        "allowed_actions": ["MERGE"],
    }

    trace = engine.run_cycle("100", report)
    assert trace.next_tactic == "MERGE"
    assert trace.strategy_id == "DIRECT_REBASE_MERGE"
