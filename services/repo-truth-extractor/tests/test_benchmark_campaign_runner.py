from __future__ import annotations

import sys
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.campaigns.selection import build_r1_campaign_plan, ensure_r1_campaign_records
from benchmarking.cli import benchmark_campaign_runner as runner_module
from benchmarking.orchestration.attempt_executor import AttemptExecutionReport
from benchmarking.registry.registry_loader import seed_registry
from benchmarking.storage.sqlite_repo import BenchmarkCatalogRepo


class _FakeExecutor:
    def __init__(self, root: Path | None = None, report: AttemptExecutionReport | None = None) -> None:
        self.root = root
        self.report = report
        self.seen_assignments = []

    def execute_assignments(self, **kwargs):  # type: ignore[no-untyped-def]
        self.seen_assignments = list(kwargs["assignments"])
        assert self.report is not None
        return self.report


class _FakeScoring:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root

    def score_run(self, benchmark_run_id: str) -> dict[str, object]:
        return {}


class _FakeGovernance:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root

    def synthesize_run(self, benchmark_run_id: str) -> dict[str, object]:
        return {
            "governance_packets": [],
            "recommendations": [],
            "sample_recommendation": {},
            "sample_governance_packet": {},
        }


class _FakeReporting:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root

    def build_reports(self, benchmark_run_id: str) -> dict[str, object]:
        return {"candidate_details": [], "portfolio_summary": {}, "profile_summaries": []}


def _prepare_plan(tmp_path: Path):
    repo = BenchmarkCatalogRepo.from_root(tmp_path)
    seed_registry(repo)
    ensure_r1_campaign_records(repo)
    return build_r1_campaign_plan(repo)


def test_run_campaign_filters_quota_blocked_openai_routes_from_live_execution(
    tmp_path: Path,
    monkeypatch,
) -> None:
    plan = _prepare_plan(tmp_path)
    fake_report = AttemptExecutionReport(
        benchmark_run_id="r1_campaign_test",
        case_attempt_ids=["attempt_a"],
        bundle_ids=["bundle_a"],
        db_row_counts={"benchmark_runs": 1},
        sample_attempt={},
        sample_validator_results={},
        sample_route_trace={},
        sample_executor_links={},
        route_identity_rows=[
            {
                "route_id": "route_openrouter_openai_gpt_5_4_v1",
                "case_id": "strict_extract_conflicting_evidence_v1",
                "cohort": "control",
                "planned_route_identity": {},
                "selected_route_identity": {},
                "effective_execution_signature": {},
                "effective_execution_signature_hash": "sig_a",
            }
        ],
        route_collapse=None,
    )
    fake_executor = _FakeExecutor(report=fake_report)

    monkeypatch.setattr(runner_module, "build_r1_campaign_plan", lambda repo: plan)
    monkeypatch.setattr(runner_module, "_preflight_output", lambda: "exit_code=0\n")
    monkeypatch.setattr(runner_module, "_load_admissibility_gate", lambda root, run_id: {"status": "admissible"})
    monkeypatch.setattr(runner_module, "AttemptExecutor", lambda root=None: fake_executor)
    monkeypatch.setattr(runner_module, "BenchmarkScoringPipeline", _FakeScoring)
    monkeypatch.setattr(runner_module, "GovernanceSynthesisPipeline", _FakeGovernance)
    monkeypatch.setattr(runner_module, "BenchmarkReportingPipeline", _FakeReporting)

    from benchmarking.cli import benchmark_live_route_readiness_smoke as readiness_module

    monkeypatch.setattr(
        readiness_module,
        "_provider_readiness",
        lambda repo, assignments: {
            "routes": [
                {
                    "route_id": "route_openrouter_openai_gpt_5_4_v1",
                    "ready": True,
                    "provider_probe": {"readiness_blocker": {}},
                },
                {
                    "route_id": "route_openrouter_openai_gpt_5_3_codex_v1",
                    "ready": True,
                    "provider_probe": {"readiness_blocker": {}},
                },
                {
                    "route_id": "route_openai_gpt_5_4_v1",
                    "ready": False,
                    "provider_probe": {"readiness_blocker": {"blocker_code": "QUOTA_OR_BILLING_BLOCK"}},
                },
                {
                    "route_id": "route_openai_gpt_5_4_mini_v1",
                    "ready": False,
                    "provider_probe": {"readiness_blocker": {"blocker_code": "QUOTA_OR_BILLING_BLOCK"}},
                },
            ]
        },
    )

    payload = runner_module.run_campaign(tmp_path, tmp_path / "proof", admissibility_run_id="admissible_run")

    executed_route_ids = [assignment.candidate.route_id for assignment in fake_executor.seen_assignments if assignment.live_execution]
    assert executed_route_ids == [
        "route_openrouter_openai_gpt_5_4_v1",
        "route_openrouter_openai_gpt_5_3_codex_v1",
    ]
    assert payload["live_cohort_decision"]["quota_blocked_openai_route_ids"] == [
        "route_openai_gpt_5_4_mini_v1",
        "route_openai_gpt_5_4_v1",
    ]


def test_run_campaign_writes_route_collapse_evidence_without_crashing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    plan = _prepare_plan(tmp_path)
    fake_report = AttemptExecutionReport(
        benchmark_run_id="r1_campaign_collapse",
        case_attempt_ids=["attempt_a", "attempt_b"],
        bundle_ids=["bundle_a", "bundle_b"],
        db_row_counts={"benchmark_runs": 1},
        sample_attempt={},
        sample_validator_results={},
        sample_route_trace={},
        sample_executor_links={},
        route_identity_rows=[
            {
                "route_id": "route_openrouter_openai_gpt_5_4_v1",
                "case_id": "strict_extract_conflicting_evidence_v1",
                "cohort": "control",
                "planned_route_identity": {},
                "selected_route_identity": {},
                "effective_execution_signature": {},
                "effective_execution_signature_hash": "sig_same",
            },
            {
                "route_id": "route_openrouter_openai_gpt_5_3_codex_v1",
                "case_id": "strict_extract_conflicting_evidence_v1",
                "cohort": "premium",
                "planned_route_identity": {},
                "selected_route_identity": {},
                "effective_execution_signature": {},
                "effective_execution_signature_hash": "sig_same",
            },
        ],
        route_collapse={
            "status": "blocked",
            "message": "campaign route collapse detected",
            "blocked_route_id": "route_openrouter_openai_gpt_5_3_codex_v1",
            "conflicting_route_id": "route_openrouter_openai_gpt_5_4_v1",
        },
    )
    fake_executor = _FakeExecutor(report=fake_report)

    monkeypatch.setattr(runner_module, "build_r1_campaign_plan", lambda repo: plan)
    monkeypatch.setattr(runner_module, "_preflight_output", lambda: "exit_code=0\n")
    monkeypatch.setattr(runner_module, "_load_admissibility_gate", lambda root, run_id: {"status": "admissible"})
    monkeypatch.setattr(runner_module, "AttemptExecutor", lambda root=None: fake_executor)
    monkeypatch.setattr(runner_module, "BenchmarkScoringPipeline", _FakeScoring)
    monkeypatch.setattr(runner_module, "GovernanceSynthesisPipeline", _FakeGovernance)
    monkeypatch.setattr(runner_module, "BenchmarkReportingPipeline", _FakeReporting)

    from benchmarking.cli import benchmark_live_route_readiness_smoke as readiness_module

    monkeypatch.setattr(
        readiness_module,
        "_provider_readiness",
        lambda repo, assignments: {
            "routes": [
                {
                    "route_id": "route_openrouter_openai_gpt_5_4_v1",
                    "ready": True,
                    "provider_probe": {"readiness_blocker": {}},
                },
                {
                    "route_id": "route_openrouter_openai_gpt_5_3_codex_v1",
                    "ready": True,
                    "provider_probe": {"readiness_blocker": {}},
                },
            ]
        },
    )

    payload = runner_module.run_campaign(tmp_path, tmp_path / "proof", admissibility_run_id="admissible_run")

    assert payload["campaign_state"] == "blocked_route_signature_collapse"
    assert (tmp_path / "proof" / "route_collapse_evidence.json").exists()
