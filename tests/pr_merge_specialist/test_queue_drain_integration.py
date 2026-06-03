from __future__ import annotations

import json
import shutil
from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace

from dopemux_pr_merge_specialist import closed_loop_engine
from dopemux_pr_merge_specialist import engine
from dopemux_pr_merge_specialist.github_api import GitHubClient, RemoteCheckLogEvidence
from dopemux_pr_merge_specialist import queue_drain as queue_drain_module
from dopemux_pr_merge_specialist.plan_builder import build_plan_result, write_pr_state_artifact
from dopemux_pr_merge_specialist.preflight import build_run_paths, pr_dir_for
from dopemux_pr_merge_specialist.runtime import CommandResult
from dopemux_pr_merge_specialist.schema import BlockerType, Finding, FindingSeverity, MergeActionType, MergeDecision, PRResult, PRState, PullRequestState, ValidationReport, ValidationStatus, ValidationStepResult
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

    def fetch_remote_check_log_evidence(self, check_entry: dict) -> RemoteCheckLogEvidence:
        return RemoteCheckLogEvidence(
            check_name=str(check_entry.get("check_name") or ""),
            details_url=str(check_entry.get("details_url") or ""),
            fetch_status="unsupported",
            error="not configured in FakeGitHubClient",
        )


def _make_result(
    *,
    pr_id: int,
    lifecycle_state: str,
    ci_status: str,
    merge_decision: MergeDecision | None = None,
    auto_merge_enabled: bool = False,
    artifacts: dict[str, str] | None = None,
    validation_status: ValidationStatus = ValidationStatus.PASSED,
    findings: list[Finding] | None = None,
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
        findings=findings or [],
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


def test_merge_prepared_result_logs_auto_merge_handoff_truthfully(
    monkeypatch, tmp_path: Path
):
    messages: list[tuple[str, str]] = []
    merge_expected_heads: list[str | None] = []

    def fake_run_merge_with_fallback(**kwargs):
        merge_expected_heads.append(kwargs.get("expected_head_oid"))
        return MergeDecision(
            action=MergeActionType.AUTO_MERGE_FALLBACK,
            command=["gh", "pr", "merge", "190", "--auto"],
            reason="pending checks",
            reason_code="auto_merge_pending_checks",
        )

    monkeypatch.setattr(
        queue_drain_module,
        "run_merge_with_fallback",
        fake_run_merge_with_fallback,
    )
    monkeypatch.setattr(queue_drain_module, "_refresh_client_state", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        queue_drain_module,
        "_load_pr_context",
        lambda **_kwargs: (
            {},
            [],
            PullRequestState(
                pr_id=190,
                title="Queued PR",
                author="tester",
                state="OPEN",
                base_ref="main",
                head_ref="feature/queued",
                ci_status="PENDING",
                mergeable="MERGEABLE",
                merge_state_status="BLOCKED",
                review_decision="",
                labels=[],
                is_draft=False,
                active_unresolved_threads=0,
                head_sha="headsha",
                base_sha="basesha",
            ),
            {},
        ),
    )
    monkeypatch.setattr(
        queue_drain_module,
        "build_plan_result",
        lambda **_kwargs: _make_result(
            pr_id=190,
            lifecycle_state=PRState.QUEUED_FOR_MERGE.value,
            ci_status="PENDING",
            merge_decision=MergeDecision(
                action=MergeActionType.AUTO_MERGE_FALLBACK,
                command=["gh", "pr", "merge", "190", "--auto"],
                reason="pending checks",
                reason_code="auto_merge_pending_checks",
            ),
            artifacts={"operator_state": "queued_for_merge"},
        ),
    )
    monkeypatch.setattr(queue_drain_module, "write_pr_state_artifact", lambda *_args, **_kwargs: None)

    client = FakeGitHubClient(repo=None, repo_root=tmp_path, policy={})
    prepared_result = _make_result(
        pr_id=190,
        lifecycle_state=PRState.QUEUED_FOR_MERGE.value,
        ci_status="SUCCESS",
        merge_decision=MergeDecision(
            action=MergeActionType.REBASE_MERGE,
            command=["gh", "pr", "merge", "190", "--rebase", "--delete-branch"],
            reason="ready",
            reason_code="rebase_merge_ready",
        ),
        artifacts={"operator_state": "queued_for_merge"},
    )
    pr_dir = pr_dir_for(tmp_path, 190)
    steward_dir = tmp_path / "pr-steward" / "pr-190"
    audit_dir = tmp_path / "embedded-audit" / "pr-190"
    steward_dir.mkdir(parents=True)
    audit_dir.mkdir(parents=True)
    (steward_dir / "MERGE_READINESS.json").write_text(
        json.dumps(
            {
                "generated_at": "2026-05-31T12:00:00Z",
                "readiness": "READY",
                "blockers": [],
                "pr": {"number": 190, "head_sha": "head-190"},
                "proof": {"proof_head_sha": "head-190"},
                "embedded_audit": {"status": "PASS"},
            }
        ),
        encoding="utf-8",
    )
    (audit_dir / "PROOF.json").write_text(
        json.dumps(
            {
                "generated_at": "2026-05-31T12:00:00Z",
                "head_sha": "head-190",
                "embedded_audit": {"status": "PASS"},
            }
        ),
        encoding="utf-8",
    )

    result = queue_drain_module._merge_prepared_result(
        args=Namespace(id=190, out_dir=str(tmp_path), repo=None, execute=True),
        client=client,
        repo_root=tmp_path,
        policy={
            "steward_gate": {
                "artifact_ttl_seconds": 10_000_000,
                "merge_readiness_path": "{out_dir}/pr-steward/pr-{pr_id}/MERGE_READINESS.json",
                "audit_proof_path": "{out_dir}/embedded-audit/pr-{pr_id}/PROOF.json",
            }
        },
        pr_root=tmp_path,
        active_run_id="truthfulhandoff",
        prepared_result=prepared_result,
        progress_callback=lambda msg, level="INFO": messages.append((level, msg)),
    )

    assert result.lifecycle_state == PRState.QUEUED_FOR_MERGE.value
    assert ("SUCCESS", "Auto-merge handoff successful") in messages
    assert ("SUCCESS", "Merge successful") not in messages
    assert merge_expected_heads == ["head-190"]


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


def test_self_check_json_suppresses_preflight_banner(monkeypatch, capsys):
    def fake_preflight(args):
        assert getattr(args, "_suppress_output", False) is True
        if not getattr(args, "_suppress_output", False):
            print("Preflight artifacts: noisy")
        return 0

    monkeypatch.setattr(pr_merge_cli, "preflight", fake_preflight)

    rc = pr_merge_cli._self_check(
        Namespace(
            json=True,
            out_dir="proof/pr_merge",
            repo=None,
            policy=None,
            allow_dirty=True,
            run_id="selfcheck",
        )
    )

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["checks"][-1] == {"name": "preflight", "status": "PASS"}


def test_self_check_allow_dirty_warn_renders_warning_icon(monkeypatch, capsys):
    def fake_preflight(args):
        return 1

    monkeypatch.setattr(pr_merge_cli, "preflight", fake_preflight)

    rc = pr_merge_cli._self_check(
        Namespace(
            json=False,
            out_dir="proof/pr_merge",
            repo=None,
            policy=None,
            allow_dirty=True,
            run_id="selfcheck",
        )
    )

    assert rc == 0
    output = capsys.readouterr().out
    assert "[WARN] preflight" in output
    assert "nonfatal under --allow-dirty" in output
    assert "[FAIL] preflight" not in output


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


def test_queue_drain_propagates_resolved_run_id_to_subcommands(
    monkeypatch, tmp_path: Path
):
    initial_result = _make_result(
        pr_id=191,
        lifecycle_state=PRState.APPLY_BLOCKED.value,
        ci_status="FAILURE",
    )
    seen_run_ids: list[str | None] = []

    class FakeClosedLoopEngine:
        def __init__(self, *_args, **_kwargs):
            pass

        def run_cycle(self, _case_id, _report):
            return SimpleNamespace(next_tactic="APPLY_FIX")

        def emit_trace_artifacts(self, _trace, _path):
            return None

    def fake_apply(args, **_kw):
        seen_run_ids.append(getattr(args, "run_id", None))
        return initial_result

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
    monkeypatch.setattr(queue_drain_module, "pr_apply", fake_apply)
    monkeypatch.setattr(
        queue_drain_module, "_should_handoff_prepared_result", lambda *a, **kw: False
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
            run_id=None,
        )
    )

    assert rc == 0
    assert len(seen_run_ids) == 1
    assert seen_run_ids[0]


def test_query_checks_reports_exact_failed_required_check_names(tmp_path: Path):
    client = GitHubClient(
        repo="DDD-Enterprises/dopemux-mvp",
        repo_root=tmp_path,
        policy={"retry": {}, "timeouts": {}},
    )
    client.fetch_branch_protection = lambda _branch: {  # type: ignore[method-assign]
        "approval_required": False,
        "required_status_checks": ["🧪 Unit Tests", "identity-check"],
    }
    payload = {
        "baseRefName": "main",
        "reviewDecision": "",
        "mergeable": "MERGEABLE",
        "mergeStateStatus": "BLOCKED",
        "statusCheckRollup": [
            {"name": "🧪 Unit Tests", "status": "COMPLETED", "conclusion": "FAILURE"},
            {"name": "identity-check", "status": "COMPLETED", "conclusion": "SUCCESS"},
            {"name": "📚 Documentation Check", "status": "COMPLETED", "conclusion": "FAILURE"},
        ],
    }

    result = client.query_checks(323, pr_payload=payload)

    assert result["failed_required_checks"] == ["🧪 Unit Tests"]
    assert result["pending_required_checks"] == []


def test_reproduce_remote_required_check_failure_runs_mapped_command(monkeypatch, tmp_path: Path):
    recorded_commands: list[list[str]] = []
    messages: list[tuple[str, str]] = []

    def fake_execute_or_dry_run(cmd, *, execute, cwd, commands_log, timeout_seconds=600):
        recorded_commands.append(list(cmd))
        return CommandResult(list(cmd), 1, "", "test failure")

    monkeypatch.setattr(queue_drain_module, "execute_or_dry_run", fake_execute_or_dry_run)

    check_name, report = queue_drain_module.reproduce_remote_required_check_failure(
        worktree_path=tmp_path,
        commands_log=tmp_path / "commands.txt",
        policy={
            "timeouts": {"subprocess_seconds": 30},
            "remote_check_repro": {
                "steps": [
                    {
                        "check_name": "🧪 Unit Tests",
                        "command": ["pytest", "tests/", "--maxfail=1"],
                        "scope": "repo",
                    }
                ]
            },
        },
        check_payload={"failed_required_checks": ["🧪 Unit Tests"]},
        log=lambda message, level="INFO": messages.append((message, level)),
    )

    assert check_name == "🧪 Unit Tests"
    assert report is not None
    assert report.status == ValidationStatus.FAILED
    assert report.steps[0].name == "🧪 Unit Tests"
    assert recorded_commands == [["pytest", "tests/", "--maxfail=1"]]
    assert any("reproduced locally" in message for message, _level in messages)


def test_handle_global_ci_blockers_ignores_failed_global_fix_creation(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(
        queue_drain_module,
        "allowed_actions_for_result",
        lambda _result: ["APPLY_FIX"],
    )
    monkeypatch.setattr(
        queue_drain_module,
        "_create_global_fix_pr",
        lambda fingerprint, failed_step, client, repo_root, **kwargs: -1,
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


def test_fetch_remote_check_log_evidence_parses_github_actions_job_url(tmp_path: Path):
    client = GitHubClient(
        repo="DDD-Enterprises/dopemux-mvp",
        repo_root=tmp_path,
        policy={"retry": {}, "timeouts": {}},
    )
    seen_commands: list[list[str]] = []

    def fake_run(cmd):
        seen_commands.append(list(cmd))
        return CommandResult(list(cmd), 0, "pytest log output", "")

    client._run = fake_run  # type: ignore[method-assign]
    evidence = client.fetch_remote_check_log_evidence(
        {
            "check_name": "🧪 Unit Tests",
            "details_url": "https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/23701466608/job/69045799064",
        }
    )

    assert evidence.fetch_status == "ok"
    assert evidence.run_id == "23701466608"
    assert evidence.job_id == "69045799064"
    assert evidence.log_text == "pytest log output"
    assert seen_commands == [
        [
            "gh",
            "run",
            "view",
            "23701466608",
            "--job",
            "69045799064",
            "--log",
            "--repo",
            "DDD-Enterprises/dopemux-mvp",
        ]
    ]


def test_fetch_remote_check_log_evidence_rejects_non_actions_url(tmp_path: Path):
    client = GitHubClient(
        repo="DDD-Enterprises/dopemux-mvp",
        repo_root=tmp_path,
        policy={"retry": {}, "timeouts": {}},
    )

    evidence = client.fetch_remote_check_log_evidence(
        {
            "check_name": "🔍 Docker Scout",
            "details_url": "https://scout.docker.com/v/CVE-123",
        }
    )

    assert evidence.fetch_status == "unsupported"
    assert evidence.run_id is None
    assert evidence.job_id is None


def test_extract_remote_failure_signature_prefers_pytest_node_id():
    signature = queue_drain_module._extract_remote_failure_signature(
        """
=========================== short test summary info ============================
FAILED tests/test_cli.py::TestCLI::test_start_command_role_dry_run - UnboundLocalError: cannot access local variable 'project_path'
        """.strip()
    )

    assert signature == (
        "pytest_node",
        "tests/test_cli.py::TestCLI::test_start_command_role_dry_run",
        "pytest failure tests/test_cli.py::TestCLI::test_start_command_role_dry_run",
    )


def test_extract_remote_failure_signature_falls_back_to_exception_header():
    signature = queue_drain_module._extract_remote_failure_signature(
        """
Traceback (most recent call last):
E   AssertionError: template/runtime parity mismatch
        """.strip()
    )

    assert signature == (
        "exception_header",
        "AssertionError: template/runtime parity mismatch",
        "failure header AssertionError: template/runtime parity mismatch",
    )


def test_extract_remote_failure_signature_returns_none_for_ambiguous_log():
    assert (
        queue_drain_module._extract_remote_failure_signature(
            "Build failed after 12.3s with no test summary available."
        )
        is None
    )


def test_queue_drain_progress_writes_live_log(tmp_path: Path):
    live_log_path = tmp_path / "LIVE_LOG.txt"

    cb = queue_drain_module._queue_drain_progress(
        42,
        live_log_path=live_log_path,
    )
    cb("Running validation suite...", "START")

    lines = live_log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert lines[0].endswith("[START] pr:42: Running validation suite...")


def test_create_global_fix_pr_logs_no_changes_outcome(monkeypatch, tmp_path: Path):
    log_events: list[tuple[str, str, str]] = []
    popen_env: dict[str, str] = {}

    def logger(level: str, scope: str, message: str) -> None:
        log_events.append((level, scope, message))

    class FakeStdout:
        def __init__(self, lines: list[str]) -> None:
            self._lines = iter(lines)

        def readline(self) -> str:
            return next(self._lines, "")

    class FakePopen:
        def __init__(self, cmd, stdout, stderr, text, cwd, env, bufsize, universal_newlines):
            self.cmd = cmd
            popen_env.update(env)
            self.stdout = FakeStdout(["working\n"])
            self.returncode = 0

        def wait(self, timeout=None):
            return 0

    seen_commands: list[list[str]] = []
    focused_precheck_calls = 0

    def fake_run(cmd, cwd=None, check=False, stderr=None, stdout=None, capture_output=False, text=False, timeout=None):
        nonlocal focused_precheck_calls
        command = list(cmd)
        seen_commands.append(command)
        if command[:4] == ["pytest", "tests/test_cli.py::TestCLI::test_start_command_role_dry_run", "-q"]:
            focused_precheck_calls += 1
            if focused_precheck_calls == 1:
                return SimpleNamespace(returncode=1, stdout="", stderr="FAILED tests/test_cli.py::TestCLI::test_start_command_role_dry_run")
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        if command and command[0] == "pytest":
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        if command[:3] == ["git", "status", "--porcelain"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("subprocess.run", fake_run)
    monkeypatch.setattr("subprocess.Popen", FakePopen)

    pr_num = queue_drain_module._create_global_fix_pr(
        "abc12345deadbeef",
        ValidationStepResult(
            name="🧪 Unit Tests",
            command="pytest tests/ --maxfail=1",
            status="failed",
            stderr="FAILED tests/test_cli.py::TestCLI::test_start_command_role_dry_run",
        ),
        FakeGitHubClient(repo=None, repo_root=tmp_path, policy={}),
        tmp_path,
        logger=logger,
        verification_command="pytest tests/ --maxfail=1",
        targeted_nodeid="tests/test_cli.py::TestCLI::test_start_command_role_dry_run",
    )

    assert pr_num == -1
    messages = [message for _level, _scope, message in log_events]
    assert any("Creating global fix PR" in message for message in messages)
    assert any("Launching Gemini CLI agent for GLOBAL FIX" in message for message in messages)
    assert any("Gemini global-fix process exited with code 0" in message for message in messages)
    assert any("Global fix agent made no changes." in message for message in messages)
    assert ["pytest", "tests/test_cli.py::TestCLI::test_start_command_role_dry_run", "-q"] in seen_commands
    assert ["pytest", "tests/test_cli.py", "-q"] in seen_commands
    assert popen_env["HOME"] != str(Path.home())
    assert popen_env["XDG_CONFIG_HOME"].endswith("/.config")


def test_create_global_fix_pr_skips_stale_remote_fingerprint_when_precheck_is_green(
    monkeypatch, tmp_path: Path
):
    log_events: list[tuple[str, str, str]] = []

    def logger(level: str, scope: str, message: str) -> None:
        log_events.append((level, scope, message))

    def fake_popen(*args, **kwargs):
        raise AssertionError("Gemini should not launch when precheck is already green")

    def fake_run(
        cmd,
        cwd=None,
        check=False,
        stderr=None,
        stdout=None,
        capture_output=False,
        text=False,
        timeout=None,
    ):
        command = list(cmd)
        if command[:2] == ["git", "fetch"] or command[:2] == ["git", "branch"] or command[:2] == ["git", "worktree"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        if command[:4] == ["pytest", "tests/test_cli.py::TestCLI::test_start_command_role_dry_run", "-q"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        if command[:3] == ["pytest", "tests/test_cli.py", "-q"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("subprocess.run", fake_run)
    monkeypatch.setattr("subprocess.Popen", fake_popen)

    pr_num = queue_drain_module._create_global_fix_pr(
        "abc12345deadbeef",
        ValidationStepResult(
            name="🧪 Unit Tests",
            command="pytest tests/ --maxfail=1",
            status="failed",
            stderr="FAILED tests/test_cli.py::TestCLI::test_start_command_role_dry_run",
        ),
        FakeGitHubClient(repo=None, repo_root=tmp_path, policy={}),
        tmp_path,
        logger=logger,
        verification_command="pytest tests/ --maxfail=1",
        targeted_nodeid="tests/test_cli.py::TestCLI::test_start_command_role_dry_run",
    )

    assert pr_num == -2  # Stale fingerprint returns -2 (distinct from -1 failure)
    messages = [message for _level, _scope, message in log_events]
    assert any("Pre-checking focused remediation command before launching Gemini" in message for message in messages)
    assert any("Focused remediation command already passes on current main." in message for message in messages)
    assert any("Pre-checking fingerprint lane command before launching Gemini" in message for message in messages)
    assert any("treating the remote fingerprint as stale and skipping shared remediation" in message for message in messages)
    assert not any("Launching Gemini CLI agent for GLOBAL FIX" in message for message in messages)


def test_create_global_fix_pr_removes_stale_non_worktree_path(monkeypatch, tmp_path: Path):
    log_events: list[tuple[str, str, str]] = []
    stale_path = Path("/tmp") / "dopemux-global-fix-deadbeef"
    if stale_path.exists():
        if stale_path.is_dir():
            shutil.rmtree(stale_path)
        else:
            stale_path.unlink()
    stale_path.mkdir(parents=True)
    (stale_path / "leftover.txt").write_text("stale", encoding="utf-8")

    def logger(level: str, scope: str, message: str) -> None:
        log_events.append((level, scope, message))

    def fake_popen(*args, **kwargs):
        raise AssertionError("Gemini should not launch for a stale-green fingerprint")

    def fake_run(
        cmd,
        cwd=None,
        check=False,
        stderr=None,
        stdout=None,
        capture_output=False,
        text=False,
        timeout=None,
    ):
        command = list(cmd)
        if command[:4] == ["git", "worktree", "remove", "--force"]:
            return SimpleNamespace(returncode=128, stdout="", stderr="fatal: not a working tree")
        if command[:2] == ["git", "fetch"] or command[:2] == ["git", "branch"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        if command[:3] == ["git", "worktree", "add"]:
            assert not stale_path.exists()
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        if command[:4] == ["pytest", "tests/test_cli.py::TestCLI::test_start_command_role_dry_run", "-q"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        if command[:3] == ["pytest", "tests/test_cli.py", "-q"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("subprocess.run", fake_run)
    monkeypatch.setattr("subprocess.Popen", fake_popen)

    pr_num = queue_drain_module._create_global_fix_pr(
        "deadbeefcafebabe",
        ValidationStepResult(
            name="🧪 Unit Tests",
            command="pytest tests/ --maxfail=1",
            status="failed",
            stderr="FAILED tests/test_cli.py::TestCLI::test_start_command_role_dry_run",
        ),
        FakeGitHubClient(repo=None, repo_root=tmp_path, policy={}),
        tmp_path,
        logger=logger,
        verification_command="pytest tests/ --maxfail=1",
        targeted_nodeid="tests/test_cli.py::TestCLI::test_start_command_role_dry_run",
    )

    assert pr_num == -2  # Stale fingerprint returns -2 (distinct from -1 failure)
    assert not stale_path.exists()
    messages = [message for _level, _scope, message in log_events]
    assert any("Removed stale global-fix path that was not an active git worktree" in message for message in messages)


def test_create_global_fix_pr_aborts_when_post_verify_fails(monkeypatch, tmp_path: Path):
    log_events: list[tuple[str, str, str]] = []

    def logger(level: str, scope: str, message: str) -> None:
        log_events.append((level, scope, message))

    class FakeStdout:
        def __init__(self, lines: list[str]) -> None:
            self._lines = iter(lines)

        def readline(self) -> str:
            return next(self._lines, "")

    class FakePopen:
        def __init__(self, cmd, stdout, stderr, text, cwd, env, bufsize, universal_newlines):
            self.stdout = FakeStdout(["working\n"])
            self.returncode = 0

        def wait(self, timeout=None):
            return 0

    def fake_run(cmd, cwd=None, check=False, stderr=None, stdout=None, capture_output=False, text=False, timeout=None):
        command = list(cmd)
        if command[:3] == ["git", "status", "--porcelain"]:
            return SimpleNamespace(returncode=0, stdout=" M changed.py\n", stderr="")
        if command[:2] == ["git", "fetch"] or command[:2] == ["git", "branch"] or command[:2] == ["git", "worktree"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        if command[:4] == ["pytest", "tests/test_cli.py::TestCLI::test_start_command_role_dry_run", "-q"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        if command[:3] == ["pytest", "tests/test_cli.py", "-q"]:
            return SimpleNamespace(returncode=1, stdout="", stderr="FAILED tests/test_cli.py::TestCLI::test_start_command_role_dry_run")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("subprocess.run", fake_run)
    monkeypatch.setattr("subprocess.Popen", FakePopen)

    pr_num = queue_drain_module._create_global_fix_pr(
        "abc12345deadbeef",
        ValidationStepResult(
            name="🧪 Unit Tests",
            command="pytest tests/ --maxfail=1",
            status="failed",
            stderr="FAILED tests/test_cli.py::TestCLI::test_start_command_role_dry_run",
        ),
        FakeGitHubClient(repo=None, repo_root=tmp_path, policy={}),
        tmp_path,
        logger=logger,
        verification_command="pytest tests/ --maxfail=1",
        targeted_nodeid="tests/test_cli.py::TestCLI::test_start_command_role_dry_run",
    )

    assert pr_num == -1
    messages = [message for _level, _scope, message in log_events]
    assert any("Verifying focused remediation command" in message for message in messages)
    assert any("Verifying fingerprint lane command" in message for message in messages)
    assert any("aborting shared remediation without commit." in message for message in messages)
    assert not any("Creating global fix PR on GitHub." in message for message in messages)


def test_isolated_gemini_home_env_strips_creds_and_forwards_allowlist(monkeypatch, tmp_path: Path):
    """Constrained env: an empty temp HOME, an XDG_CONFIG_HOME under it, and a
    tight allowlist of Gemini auth/config env vars forwarded from the caller.
    Repository / per-user creds (OAuth files, gcloud config, PYTHONPATH, etc.)
    must NOT cross into the subprocess env.
    """
    monkeypatch.setenv("GEMINI_API_KEY", "test-api-key")
    monkeypatch.setenv("GOOGLE_GENAI_USE_VERTEXAI", "false")
    monkeypatch.setenv("PYTHONPATH", "/should/not/leak")
    monkeypatch.setenv("VIRTUAL_ENV", "/should/not/leak")

    with queue_drain_module._isolated_gemini_home_env() as env:
        isolated_home = Path(env["HOME"])
        isolated_gemini = isolated_home / ".gemini"

        assert env["GEMINI_API_KEY"] == "test-api-key"
        assert env["GOOGLE_GENAI_USE_VERTEXAI"] == "false"
        assert "PYTHONPATH" not in env
        assert "VIRTUAL_ENV" not in env

        assert env["XDG_CONFIG_HOME"] == str(isolated_home / ".config")
        assert not isolated_gemini.exists() or not any(isolated_gemini.iterdir())


def test_handle_global_ci_blockers_groups_remote_fingerprints(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(
        queue_drain_module,
        "allowed_actions_for_result",
        lambda _result: ["APPLY_FIX"],
    )

    created: list[tuple[str, str]] = []

    def fake_create_global_fix_pr(
        fingerprint,
        failed_step,
        client,
        repo_root,
        logger=None,
        verification_command=None,
        targeted_nodeid=None,
    ):
        created.append((fingerprint, failed_step.command))
        assert verification_command == "pytest tests/ --maxfail=1"
        assert targeted_nodeid == "tests/test_cli.py::TestCLI::test_start_command_role_dry_run"
        return 777

    monkeypatch.setattr(
        queue_drain_module,
        "_create_global_fix_pr",
        fake_create_global_fix_pr,
    )

    remote_details = {
        "blocker_types": ["required_check_failed"],
        "failed_required_checks": ["🧪 Unit Tests"],
        "failed_required_check_entries": [
            {
                "check_name": "🧪 Unit Tests",
                "details_url": "https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/23701466608/job/69045799064",
            }
        ],
    }
    findings = [
        Finding(
            kind=FindingSeverity.BLOCKER,
            finding_type=BlockerType.REQUIRED_CHECK_FAILED.value,
            message="Required checks are failing.",
            details=remote_details,
            source="github_protection_review",
        )
    ]
    results = [
        _make_result(
            pr_id=401,
            lifecycle_state=PRState.APPLY_BLOCKED.value,
            ci_status="FAILURE",
            findings=findings,
        ),
        _make_result(
            pr_id=402,
            lifecycle_state=PRState.APPLY_BLOCKED.value,
            ci_status="FAILURE",
            findings=findings,
        ),
    ]

    client = FakeGitHubClient(
        repo=None,
        repo_root=tmp_path,
        policy={
            "remote_check_repro": {
                "steps": [
                    {
                        "check_name": "🧪 Unit Tests",
                        "command": ["pytest", "tests/", "--maxfail=1"],
                        "scope": "repo",
                    }
                ]
            }
        },
    )
    client.fetch_remote_check_log_evidence = lambda _entry: RemoteCheckLogEvidence(  # type: ignore[method-assign]
        check_name="🧪 Unit Tests",
        details_url="https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/23701466608/job/69045799064",
        run_id="23701466608",
        job_id="69045799064",
        log_text="FAILED tests/test_cli.py::TestCLI::test_start_command_role_dry_run - UnboundLocalError",
        fetch_status="ok",
    )

    blocked_map = queue_drain_module._handle_global_ci_blockers(
        results,
        client,
        tmp_path,
    )

    assert blocked_map == {401: 777, 402: 777}
    assert len(created) == 1
    assert created[0][1] == "pytest tests/ --maxfail=1"


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

    def fake_handle_global_ci_blockers(_results, _client, _worktree_dir, seen_stale_fingerprints=None, logger=None):
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


def test_queue_drain_skips_no_progress_prs_in_subsequent_passes(
    monkeypatch, tmp_path: Path
):
    """PRs that pass local validation but remain apply_blocked should not be reprocessed."""
    apply_blocked_result = _make_result(
        pr_id=200,
        lifecycle_state=PRState.APPLY_BLOCKED.value,
        ci_status="FAILURE",
        validation_status=ValidationStatus.PASSED,
    )

    scan_call_count = [0]
    apply_call_count = [0]

    def fake_scan(*_args, **_kwargs):
        scan_call_count[0] += 1
        return [apply_blocked_result]

    class FakeClosedLoopEngine:
        def __init__(self, *_args, **_kwargs):
            pass

        def run_cycle(self, _case_id, _report):
            return SimpleNamespace(next_tactic="APPLY_FIX")

        def emit_trace_artifacts(self, _trace, _path):
            return None

    def fake_apply(_args, **_kw):
        apply_call_count[0] += 1
        return apply_blocked_result

    monkeypatch.setattr(closed_loop_engine, "ClosedLoopEngine", FakeClosedLoopEngine)
    monkeypatch.setattr(queue_drain_module, "GitHubClient", FakeGitHubClient)
    monkeypatch.setattr(queue_drain_module, "load_effective_policy", lambda *a, **kw: {})
    monkeypatch.setattr(queue_drain_module, "_get_ops_engine", lambda _: object())
    monkeypatch.setattr(queue_drain_module, "queue_scan_internal", fake_scan)
    monkeypatch.setattr(queue_drain_module, "_handle_global_ci_blockers", lambda *a, **kw: {})
    monkeypatch.setattr(queue_drain_module, "_ignite_speculative_train", lambda *a, **kw: ([], []))
    monkeypatch.setattr(queue_drain_module, "acquire_queue_lock", lambda **kw: (True, tmp_path / "q.lock", None))
    monkeypatch.setattr(queue_drain_module, "release_queue_lock", lambda _: None)
    monkeypatch.setattr(queue_drain_module, "pr_apply", fake_apply)
    monkeypatch.setattr(queue_drain_module, "_should_handoff_prepared_result", lambda *a, **kw: False)

    rc = queue_drain_module.queue_drain(
        SimpleNamespace(
            repo=None,
            out_dir=str(tmp_path),
            policy=None,
            execute=True,
            allow_dirty=True,
            limit=20,
            max_prs=0,
            max_passes=3,
            strategy="hybrid",
            prioritize=[],
            only=[],
            run_id="noprogress",
        )
    )

    assert rc == 0
    # Scanned 2 passes (pass 1 processes, pass 2 finds nothing active), but applied only once
    assert scan_call_count[0] == 2
    assert apply_call_count[0] == 1


def test_queue_drain_dry_run_processes_actionable_prs_in_all_passes(
    monkeypatch, tmp_path: Path
):
    """In dry-run mode, actionable tactics should NOT be skipped in subsequent passes."""
    result = _make_result(
        pr_id=201,
        lifecycle_state=PRState.APPLY_BLOCKED.value,
        ci_status="FAILURE",
    )

    scan_call_count = [0]

    def fake_scan(*_args, **_kwargs):
        scan_call_count[0] += 1
        return [result]

    class FakeClosedLoopEngine:
        def __init__(self, *_args, **_kwargs):
            pass

        def run_cycle(self, _case_id, _report):
            return SimpleNamespace(next_tactic="APPLY_FIX")

        def emit_trace_artifacts(self, _trace, _path):
            return None

    monkeypatch.setattr(closed_loop_engine, "ClosedLoopEngine", FakeClosedLoopEngine)
    monkeypatch.setattr(queue_drain_module, "GitHubClient", FakeGitHubClient)
    monkeypatch.setattr(queue_drain_module, "load_effective_policy", lambda *a, **kw: {})
    monkeypatch.setattr(queue_drain_module, "_get_ops_engine", lambda _: object())
    monkeypatch.setattr(queue_drain_module, "queue_scan_internal", fake_scan)
    monkeypatch.setattr(queue_drain_module, "_handle_global_ci_blockers", lambda *a, **kw: {})
    monkeypatch.setattr(queue_drain_module, "_ignite_speculative_train", lambda *a, **kw: ([], []))

    rc = queue_drain_module.queue_drain(
        SimpleNamespace(
            repo=None,
            out_dir=str(tmp_path),
            policy=None,
            execute=False,
            allow_dirty=True,
            limit=20,
            max_prs=0,
            max_passes=3,
            strategy="hybrid",
            prioritize=[],
            only=[],
            run_id="dryrun",
        )
    )

    assert rc == 0
    assert scan_call_count[0] == 3  # all 3 passes execute


def test_stale_fingerprint_cached_between_passes(monkeypatch, tmp_path: Path):
    """When a fingerprint is marked stale (-2), it is cached and skipped in subsequent passes."""
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
    
    fingerprint = failed_validation.failure_fingerprint
    results = [
        SimpleNamespace(
            pr_state=SimpleNamespace(pr_id=101),
            validation_report=failed_validation,
            apply_actions=[],
        ),
        SimpleNamespace(
            pr_state=SimpleNamespace(pr_id=102),
            validation_report=failed_validation,
            apply_actions=[],
        ),
    ]

    def fake_allowed_actions(result):
        return ["APPLY_FIX"]
    monkeypatch.setattr(queue_drain_module, "allowed_actions_for_result", fake_allowed_actions)

    call_count = [0]
    def fake_create_global_fix_pr(*args, **kwargs):
        call_count[0] += 1
        return -2  # simulate stale fingerprint

    monkeypatch.setattr(queue_drain_module, "_create_global_fix_pr", fake_create_global_fix_pr)

    client = FakeGitHubClient(repo=None, repo_root=tmp_path, policy={})

    # Pass 1
    seen_stale_fingerprints = set()
    queue_drain_module._handle_global_ci_blockers(results, client, tmp_path, seen_stale_fingerprints=seen_stale_fingerprints)
    assert call_count[0] == 1
    assert fingerprint in seen_stale_fingerprints

    # Pass 2
    queue_drain_module._handle_global_ci_blockers(results, client, tmp_path, seen_stale_fingerprints=seen_stale_fingerprints)
    assert call_count[0] == 1  # Should not be called again
