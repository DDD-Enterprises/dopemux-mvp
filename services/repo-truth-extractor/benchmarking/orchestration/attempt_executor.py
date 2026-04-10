from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..executors.base import ExecutorAdapter
from ..executors.extraction_v5_adapter import ExtractionV5Adapter
from ..executors.fl_int_adapter import FLIntAdapter
from ..executors.phase_s_adapter import PhaseSAdapter
from ..executors.prescan_adapter import PrescanAdapter
from ..models.entities import BenchmarkCaseAttempt, BenchmarkRun, ControlDelta, ValidatorResult
from ..models.ids import synthetic_id, synthetic_run_id, utc_now_iso
from ..registry.registry_loader import seed_registry
from ..storage.bundle_writer import EvidenceBundleWriter
from ..storage.hashing import hash_json
from ..storage.paths import benchmark_paths
from ..storage.sqlite_repo import BenchmarkCatalogRepo
from ..validators.base import ValidatorWrapper
from ..validators.fl_int_validator_wrapper import FLIntValidatorWrapper
from ..validators.phase_s_validator_wrapper import PhaseSValidatorWrapper
from ..validators.prescan_validator_wrapper import PrescanValidatorWrapper
from ..validators.runtime_validator_wrapper import RuntimeValidatorWrapper


def _executor_for_case(case: dict[str, Any]) -> ExecutorAdapter:
    kind = str(case.get("executor_kind") or "")
    mapping: dict[str, ExecutorAdapter] = {
        "prescan_adapter": PrescanAdapter(),
        "runtime_v5_adapter": ExtractionV5Adapter(),
        "phase_s_adapter": PhaseSAdapter(),
        "fl_int_adapter": FLIntAdapter(),
    }
    if kind not in mapping:
        raise ValueError(f"unsupported executor kind: {kind}")
    return mapping[kind]


def _validator_for_case(case: dict[str, Any]) -> ValidatorWrapper:
    suite = str(case.get("validator_suite_id") or "")
    if suite == "validators_prescan_repo_reasoning_v1":
        return PrescanValidatorWrapper()
    if suite == "validators_runtime_strict_json_v1":
        return RuntimeValidatorWrapper()
    if suite == "validators_phase_s_advisory_v1":
        return PhaseSValidatorWrapper()
    if suite == "validators_fl_int_schema_v1":
        return FLIntValidatorWrapper()
    raise ValueError(f"unsupported validator suite: {suite}")


def _attempt_route_context(surface_class: str) -> dict[str, str]:
    mapping = {
        "local_or_open_weight": {
            "surface_id": "surface_local_fixture_v1",
            "route_id": "route_local_fixture_v1",
            "profile_id": "benchmark_local_validation",
            "control_anchor_group_id": "anchor_local_fixture_v1",
        },
        "openrouter_routed": {
            "surface_id": "surface_openrouter_api_v1",
            "route_id": "route_openrouter_openai_gpt_5_4_v1",
            "profile_id": "balanced_production",
            "control_anchor_group_id": "anchor_openrouter_strict_v1",
        },
        "direct_provider_api": {
            "surface_id": "surface_openai_api_v1",
            "route_id": "route_openai_gpt_5_4_v1",
            "profile_id": "balanced_production",
            "control_anchor_group_id": "anchor_openai_general_v1",
        },
    }
    if surface_class not in mapping:
        raise ValueError(f"unsupported surface class: {surface_class}")
    return mapping[surface_class]


@dataclass(frozen=True)
class AttemptExecutionReport:
    benchmark_run_id: str
    case_attempt_ids: list[str]
    bundle_ids: list[str]
    db_row_counts: dict[str, int]
    sample_attempt: dict[str, Any]
    sample_validator_results: dict[str, Any]
    sample_route_trace: dict[str, Any]
    sample_executor_links: dict[str, Any]


class AttemptExecutor:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root
        self.repo = BenchmarkCatalogRepo.from_root(root)
        self.writer = EvidenceBundleWriter(root)

    def _ensure_registry(self) -> None:
        required_records_missing = any(
            [
                self.repo.fetch_benchmark_case("prescan_route_inventory_v1") is None,
                self.repo.fetch_provider_surface("surface_local_fixture_v1") is None,
                self.repo.fetch_route("route_local_fixture_v1") is None,
                self.repo.fetch_profile("benchmark_local_validation") is None,
                self.repo.fetch_control_anchor_group("anchor_local_fixture_v1") is None,
            ]
        )
        if required_records_missing:
            seed_registry(self.repo)

    def execute_starter_set(self, case_ids: list[str]) -> AttemptExecutionReport:
        self._ensure_registry()
        benchmark_run_id = synthetic_run_id("m2_exec")
        run = BenchmarkRun(
            benchmark_run_id=benchmark_run_id,
            run_type="benchmark_execution_smoke",
            trigger_type="manual",
            trigger_ref="TP-RTE-BENCH-M2",
            git_commit="workspace",
            runtime_version="v5",
            contract_snapshot_ids=[],
            status="READY_FOR_REVIEW",
            started_at=utc_now_iso(),
            finished_at=utc_now_iso(),
            content_hash=hash_json({"benchmark_run_id": benchmark_run_id}),
            source_ref="m2_attempt_executor",
        )
        self.repo.insert_benchmark_run(run)

        case_set = self.repo.fetch_benchmark_case_set("benchmark_registry_starter_v1")
        assert case_set is not None
        contract_snapshot = self.repo.fetch_contract_snapshot(
            self.repo.fetch_benchmark_case(case_ids[0])["contract_snapshot_id"]  # type: ignore[index]
        )
        assert contract_snapshot is not None
        self.writer.write_run_layout(
            benchmark_run=run,
            case_set_id=case_set["case_set_id"],
            contract_version=contract_snapshot["contract_version"],
            contract_snapshot_id=contract_snapshot["contract_snapshot_id"],
            registry_snapshot_files=[
                "promptset.yaml",
                "artifacts.yaml",
                "model_map.yaml",
                "phase_s_registry.json",
                "fl_int_schema_input.json",
            ],
        )
        self.writer.write_case_set_layout(
            benchmark_run_id=benchmark_run_id,
            case_set_id=case_set["case_set_id"],
            case_ids=case_ids,
            control_anchor_group_id=str(case_set["control_anchor_group_id"]),
        )

        case_attempt_ids: list[str] = []
        bundle_ids: list[str] = []
        first_attempt_payload: dict[str, Any] | None = None
        first_validator_payload: dict[str, Any] | None = None
        first_route_trace: dict[str, Any] | None = None
        first_executor_links: dict[str, Any] | None = None

        for index, case_id in enumerate(case_ids, start=1):
            case = self.repo.fetch_benchmark_case(case_id)
            if case is None:
                raise RuntimeError(f"missing benchmark case {case_id}")
            surface_class = str((case.get("surface_scope") or ["local_or_open_weight"])[0])
            route_context = _attempt_route_context(surface_class)
            executor = _executor_for_case(case)
            validator = _validator_for_case(case)
            execution = executor.execute(case, benchmark_paths(self.root).root / "work" / case_id)
            validation = validator.validate(execution, case)
            if not validation.passed:
                raise RuntimeError(f"structural validation failed for {case_id}: {validation.failure_reason}")

            attempt = BenchmarkCaseAttempt(
                case_attempt_id=synthetic_id("bca", f"{benchmark_run_id}_{case_id}"),
                benchmark_run_id=benchmark_run_id,
                case_id=case_id,
                case_version=int(case["case_version"]),
                case_set_id=str(case_set["case_set_id"]),
                archetype_id=str(case["archetype_id"]),
                phase_or_step_family=str(case["phase_or_step_family"]),
                surface_class=surface_class,
                surface_id=route_context["surface_id"],
                profile_id=route_context["profile_id"],
                route_id=route_context["route_id"],
                control_anchor_group_id=route_context["control_anchor_group_id"],
                runtime_version="v5",
                contract_version=str(contract_snapshot["contract_version"]),
                contract_snapshot_id=str(contract_snapshot["contract_snapshot_id"]),
                schema_id="REPO_ENTITY_LIST@v1",
                strict_schema_expected=True,
                validator_suite_id=str(case["validator_suite_id"]),
                attempt_number=index,
                retry_policy_id="retry_ladder_structural_fail_closed_v1",
                temperature_or_equivalent=0.0,
                max_tokens_or_budget=4096,
                tool_mode="disabled",
                batch_mode="sync",
                contract_gate_pass=execution.contract_gate_pass,
                contract_gate_strength=execution.contract_gate_strength,
                contract_fail_reason=execution.contract_fail_reason,
                validator_pass=validation.passed,
                task_success_score=1.0,
                task_score_breakdown={"structural_score": 1.0},
                operational_metrics={"route_hop_total": execution.route_hop_total},
                repair_invocations=execution.repair_invocations,
                sidefill_invocations=execution.sidefill_invocations,
                route_hop_total=execution.route_hop_total,
                unknowns_open=[],
                output_artifact_ref=execution.output_artifact_ref,
                golden_eval_ref="TASK_EVAL.json",
                control_delta_ref="CONTROL_DELTA.json",
                evidence_bundle_id=synthetic_id("bundle", f"{benchmark_run_id}_{case_id}"),
                timestamp_utc=utc_now_iso(),
                source_ref="m2_attempt_executor",
            )
            written = self.writer.write_attempt_bundle(
                attempt=attempt,
                route_trace=execution.route_trace,
                validator_results=validation.details_payload,
                task_eval=execution.task_eval,
                control_delta={"status": "not_implemented_in_m2"},
                executor_links=execution.executor_links,
                output_payloads=execution.outputs,
            )
            validator_result = ValidatorResult(
                validator_result_id=synthetic_id("validator", attempt.case_attempt_id),
                case_attempt_id=attempt.case_attempt_id,
                validator_suite_id=validation.validator_suite_id,
                validator_name=validation.wrapper_name,
                passed=validation.passed,
                strength_class=validation.strength_class,
                failure_reason=validation.failure_reason,
                details_ref="VALIDATOR_RESULTS.json",
                content_hash=hash_json(validation.details_payload),
                source_ref="m2_attempt_executor",
            )
            self.repo.insert_evidence_bundle(written.bundle)
            self.repo.insert_benchmark_case_attempt(attempt)
            self.repo.insert_validator_result(validator_result)
            self.repo.insert_control_delta(
                ControlDelta(
                    control_delta_id=synthetic_id("control_delta", attempt.case_attempt_id),
                    candidate_attempt_id=attempt.case_attempt_id,
                    anchor_attempt_id=attempt.case_attempt_id,
                    metric_name="not_implemented_in_m2",
                    candidate_value=0.0,
                    anchor_value=0.0,
                    delta_value=0.0,
                    delta_state="not_computed",
                    content_hash=hash_json({"case_attempt_id": attempt.case_attempt_id}),
                    source_ref="m2_attempt_executor",
                )
            )
            case_attempt_ids.append(attempt.case_attempt_id)
            bundle_ids.append(written.bundle.bundle_id)
            if first_attempt_payload is None:
                first_attempt_payload = self.repo.fetch_attempt(attempt.case_attempt_id)
                first_validator_payload = validation.details_payload
                first_route_trace = execution.route_trace
                first_executor_links = execution.executor_links

        return AttemptExecutionReport(
            benchmark_run_id=benchmark_run_id,
            case_attempt_ids=case_attempt_ids,
            bundle_ids=bundle_ids,
            db_row_counts=self.repo.count_rows(),
            sample_attempt=first_attempt_payload or {},
            sample_validator_results=first_validator_payload or {},
            sample_route_trace=first_route_trace or {},
            sample_executor_links=first_executor_links or {},
        )
