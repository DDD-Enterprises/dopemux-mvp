from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from dopemux_pr_merge_specialist import engine
from dopemux_pr_merge_specialist.schema import ValidationReport, ValidationStatus


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

    def query_checks(self, pr_id: int) -> dict:
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
    assert apply_calls == [190]
    assert merge_calls == [190]
    run_dir = tmp_path / "run_drainrun"
    assert (run_dir / "QUEUE_REPORT.json").exists()
    assert (run_dir / "BASE_REBASE_UPDATES.json").exists()
    report = json.loads((run_dir / "QUEUE_REPORT.json").read_text(encoding="utf-8"))
    assert report["processed"] == 1
