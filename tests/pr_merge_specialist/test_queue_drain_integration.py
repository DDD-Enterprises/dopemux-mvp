from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace

from dopemux_pr_merge_specialist import engine
from dopemux_pr_merge_specialist import queue_drain as queue_drain_module
from dopemux_pr_merge_specialist.plan_builder import build_plan_result, write_pr_state_artifact
from dopemux_pr_merge_specialist.preflight import build_run_paths, pr_dir_for
from dopemux_pr_merge_specialist.schema import ValidationReport, ValidationStatus
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
