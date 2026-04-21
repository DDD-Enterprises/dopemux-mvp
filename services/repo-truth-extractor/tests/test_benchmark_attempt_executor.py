from __future__ import annotations

import sys
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.campaigns.selection import build_r1_campaign_plan, ensure_r1_campaign_records
from benchmarking.executors.base import ExecutionResult
from benchmarking.orchestration import attempt_executor as attempt_executor_module
from benchmarking.registry.registry_loader import seed_registry
from benchmarking.storage.sqlite_repo import BenchmarkCatalogRepo


class _FakeValidator:
    validator_suite_id = "validators_runtime_strict_json_v1"
    wrapper_name = "fake_validator"

    def validate(self, execution, case):  # type: ignore[no-untyped-def]
        class _Result:
            validator_suite_id = "validators_runtime_strict_json_v1"
            wrapper_name = "fake_validator"
            passed = True
            strength_class = "strong"
            failure_reason = None
            details_payload = {"status": "ok"}

        return _Result()


class _QueuedExecutor:
    def __init__(self, results: list[ExecutionResult]) -> None:
        self._results = list(results)

    def execute(self, case, work_root):  # type: ignore[no-untyped-def]
        return self._results.pop(0)


def _execution_result(route_id: str, provider: str, model_id: str, transport: str) -> ExecutionResult:
    return ExecutionResult(
        adapter_name="runtime_v5_extraction",
        case_id="strict_extract_conflicting_evidence_v1",
        succeeded=True,
        contract_gate_pass=True,
        contract_gate_strength="strong",
        contract_fail_reason=None,
        output_artifact_ref="outputs/REPOCTRL_INVENTORY.json",
        outputs={
            "REPOCTRL_INVENTORY.json": {},
            "STEP_METRICS.json": {"steps": {"A:A0": {"final_route_counts": {"openrouter/openai/gpt-5.4": 1}}}},
            "RUN_ROUTING_FINGERPRINT.json": {
                "effective_model_routing": {
                    "A": {
                        "provider": provider,
                        "model_id": model_id,
                        "transport": transport,
                        "scope": "representative_phase_default_not_step_authoritative",
                        "reason": "benchmark_route_ownership_primary",
                    }
                }
            },
            "ROUTING_LOG.json": {"entries": []},
        },
        route_trace={
            "declared_route_id": route_id,
            "surface_class": "direct_provider_api",
            "execution_mode": "live_execute",
            "phase": "A",
            "logical_route_id": route_id,
            "provider_name": provider,
            "selected_route_identity": {
                "declared_route_id": route_id,
                "provider_name": provider,
                "provider_model_id": model_id,
            },
            "route_hops": [f"{provider}/{model_id}"],
            "step_route_counts": {"A:A0": ["openrouter/openai/gpt-5.4"]},
            "route_ownership_mode": "strict_extraction_lane_owned_v1",
            "route_ownership_source": "benchmark_route_ownership_env",
            "run_root": "/tmp/fake-run",
        },
        task_eval={"status": "captured"},
        executor_links={"script": "fake"},
        validator_inputs={},
        route_hop_total=1,
        work_root="/tmp/fake-run",
    )


def test_execute_assignments_records_route_collapse_instead_of_raising(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = BenchmarkCatalogRepo.from_root(tmp_path)
    seed_registry(repo)
    ensure_r1_campaign_records(repo)
    plan = build_r1_campaign_plan(repo)
    assignments = [
        assignment
        for assignment in plan.campaign_assignments
        if assignment.live_execution and assignment.case_id == "strict_extract_conflicting_evidence_v1"
    ][:2]
    fake_executor = _QueuedExecutor(
        [
            _execution_result(assignments[0].candidate.route_id, "openrouter", "openai/gpt-5.4", "openai_sdk"),
            _execution_result(assignments[1].candidate.route_id, "openrouter", "openai/gpt-5.4", "openai_sdk"),
        ]
    )

    monkeypatch.setattr(attempt_executor_module, "_executor_for_case", lambda case: fake_executor)
    monkeypatch.setattr(attempt_executor_module, "_validator_for_case", lambda case: _FakeValidator())

    report = attempt_executor_module.AttemptExecutor(tmp_path).execute_assignments(
        assignments=assignments,
        case_set_id=plan.case_set_id,
        run_type="benchmark_campaign_candidate",
        trigger_ref=plan.campaign_id,
        benchmark_run_prefix="test_collapse",
    )

    assert report.route_collapse is not None
    assert report.route_collapse["blocked_route_id"] == assignments[1].candidate.route_id
    assert len(report.case_attempt_ids) == 2
    assert len(report.route_identity_rows) == 2
