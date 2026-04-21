from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from ..campaigns.selection import CampaignAssignment, CampaignCandidate
from ..executors.base import ExecutorAdapter
from ..executors.extraction_v5_adapter import ExtractionV5Adapter
from ..executors.fl_int_adapter import FLIntAdapter
from ..executors.phase_s_adapter import PhaseSAdapter
from ..executors.prescan_adapter import PrescanAdapter
from ..models.entities import BenchmarkCaseAttempt, BenchmarkRun, ControlDelta, ValidatorResult
from ..models.enums import BenchmarkMode
from ..models.ids import synthetic_id, synthetic_run_id, utc_now_iso
from ..models.lane_contracts import build_runtime_route_attempt_payload
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
    route_identity_rows: list[dict[str, Any]]
    route_collapse: dict[str, Any] | None = None


def _step_route_signature(route_trace: dict[str, Any]) -> str:
    payload = route_trace.get("step_route_counts")
    if not isinstance(payload, dict):
        return ""
    normalized = {
        str(step): [str(item) for item in value]
        for step, value in sorted(payload.items())
        if isinstance(value, list)
    }
    return json.dumps(normalized, sort_keys=True, separators=(",", ":"))


def _step_route_signature_payload(route_trace: dict[str, Any]) -> dict[str, list[str]]:
    payload = route_trace.get("step_route_counts")
    if not isinstance(payload, dict):
        return {}
    return {
        str(step): [str(item) for item in value]
        for step, value in sorted(payload.items())
        if isinstance(value, list) and value
    }


def _execution_signature_payload(
    *,
    route_trace: dict[str, Any],
    outputs: dict[str, Any],
    selected_route_identity: dict[str, Any],
    surface_transport_kind: str,
) -> dict[str, Any]:
    routing_fingerprint = outputs.get("RUN_ROUTING_FINGERPRINT.json", {})
    effective_model_routing = {}
    if isinstance(routing_fingerprint, dict):
        payload = routing_fingerprint.get("effective_model_routing", {})
        if isinstance(payload, dict):
            effective_model_routing = payload
    phase = str(route_trace.get("phase") or "A")
    representative_route = effective_model_routing.get(phase) or effective_model_routing.get("A") or {}
    if not isinstance(representative_route, dict):
        representative_route = {}
    provider_name = str(
        representative_route.get("provider")
        or selected_route_identity.get("provider_name")
        or route_trace.get("provider_name")
        or ""
    )
    provider_model_id = str(
        representative_route.get("model_id")
        or selected_route_identity.get("provider_model_id")
        or ""
    )
    transport_kind = str(
        representative_route.get("transport")
        or selected_route_identity.get("transport_kind")
        or surface_transport_kind
    )
    return {
        "provider_name": provider_name,
        "provider_model_id": provider_model_id,
        "transport_kind": transport_kind,
        "effective_routing_signature": _step_route_signature_payload(route_trace),
        "representative_phase_route": {
            "provider": provider_name,
            "model_id": provider_model_id,
            "transport": transport_kind,
            "scope": str(representative_route.get("scope") or ""),
            "reason": str(representative_route.get("reason") or ""),
        },
        "route_ownership_mode": str(route_trace.get("route_ownership_mode") or ""),
    }


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

    def _insert_attempt_artifacts(
        self,
        attempt: BenchmarkCaseAttempt,
        execution: Any,
        validation: Any,
    ) -> None:
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

    def execute_assignments(
        self,
        *,
        assignments: list[CampaignAssignment],
        case_set_id: str,
        run_type: str,
        trigger_ref: str,
        benchmark_run_prefix: str,
    ) -> AttemptExecutionReport:
        self._ensure_registry()
        benchmark_run_id = synthetic_run_id(benchmark_run_prefix)
        run = BenchmarkRun(
            benchmark_run_id=benchmark_run_id,
            run_type=run_type,
            trigger_type="manual",
            trigger_ref=trigger_ref,
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

        case_set = self.repo.fetch_benchmark_case_set(case_set_id)
        if case_set is None:
            raise RuntimeError(f"missing benchmark case set {case_set_id}")
        first_case = self.repo.fetch_benchmark_case(assignments[0].case_id)
        if first_case is None:
            raise RuntimeError(f"missing benchmark case {assignments[0].case_id}")
        contract_snapshot = self.repo.fetch_contract_snapshot(str(first_case["contract_snapshot_id"]))
        if contract_snapshot is None:
            raise RuntimeError(f"missing contract snapshot for case {assignments[0].case_id}")
        case_ids = sorted({assignment.case_id for assignment in assignments})
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
        live_route_signatures: dict[str, dict[str, dict[str, Any]]] = {}
        route_identity_rows: list[dict[str, Any]] = []
        route_collapse: dict[str, Any] | None = None

        for index, assignment in enumerate(assignments, start=1):
            case = self.repo.fetch_benchmark_case(assignment.case_id)
            if case is None:
                raise RuntimeError(f"missing benchmark case {assignment.case_id}")
            if str(case.get("benchmark_mode") or BenchmarkMode.RUNTIME_ROUTE.value) != BenchmarkMode.RUNTIME_ROUTE.value:
                raise RuntimeError(
                    f"AttemptExecutor only supports runtime_route cases; {assignment.case_id} is "
                    f"{case.get('benchmark_mode')}"
                )
            route_record = self.repo.fetch_route(assignment.candidate.route_id)
            if route_record is None:
                raise RuntimeError(f"missing route record {assignment.candidate.route_id}")
            surface_record = self.repo.fetch_provider_surface(assignment.candidate.surface_id) or {}
            executor = _executor_for_case(case)
            validator = _validator_for_case(case)
            case_attempt_id = synthetic_id(
                "bca",
                f"{benchmark_run_id}_{assignment.case_id}_{assignment.candidate.route_id}",
            )
            execution_case = dict(case)
            execution_case["campaign_execution"] = {
                "run_id": f"{benchmark_run_id}_{assignment.case_id}_{assignment.candidate.route_id}",
                "phase": assignment.phase,
                "output_root": str(benchmark_paths(self.root).root / "work" / benchmark_run_id / assignment.case_id / assignment.candidate.route_id),
                "repo_root": str(assignment.repo_root),
                "live_execution": assignment.live_execution,
                "routing_override_model": assignment.routing_override_model,
                "route_id": assignment.candidate.route_id,
                "surface_id": assignment.candidate.surface_id,
                "surface_class": assignment.candidate.surface_class,
                "provider_name": assignment.candidate.provider_name,
                "model_key": assignment.candidate.model_key,
                "provider_model_id": assignment.candidate.provider_model_id,
                "route_pin": str(route_record.get("route_pin") or ""),
                "api_key_env": str(route_record.get("api_key_ref") or ""),
                "benchmark_route_ownership_mode": str(assignment.benchmark_route_ownership_mode or ""),
                "benchmark_route_ownership_scope": str(assignment.benchmark_route_ownership_scope or ""),
            }
            execution = executor.execute(
                execution_case,
                benchmark_paths(self.root).root / "work" / benchmark_run_id / assignment.case_id / assignment.candidate.route_id,
            )
            validation = validator.validate(execution, case)
            runtime_route_attempt = build_runtime_route_attempt_payload(
                declared_route_id=assignment.candidate.route_id,
                route_trace=execution.route_trace,
                route_telemetry_refs=[
                    "ROUTE_TRACE.json",
                    *(
                        ref
                        for ref in (
                            "outputs/STEP_METRICS.json" if "STEP_METRICS.json" in execution.outputs else "",
                            "outputs/RUN_ROUTING_FINGERPRINT.json" if "RUN_ROUTING_FINGERPRINT.json" in execution.outputs else "",
                            "outputs/ROUTING_LOG.json" if "ROUTING_LOG.json" in execution.outputs else "",
                        )
                        if ref
                    ),
                ],
                admissibility_status="not_evaluated",
            )

            attempt = BenchmarkCaseAttempt(
                case_attempt_id=case_attempt_id,
                benchmark_run_id=benchmark_run_id,
                case_id=assignment.case_id,
                case_version=int(case["case_version"]),
                case_set_id=str(case_set["case_set_id"]),
                benchmark_mode=str(case["benchmark_mode"]),
                candidate_type=str(case["candidate_type"]),
                execution_family=str(case["execution_family"]),
                archetype_id=assignment.archetype_id,
                phase_or_step_family=str(case["phase_or_step_family"]),
                surface_class=assignment.candidate.surface_class,
                surface_id=assignment.candidate.surface_id,
                profile_id=assignment.profile_id,
                route_id=assignment.candidate.route_id,
                control_anchor_group_id=assignment.control_anchor_group_id,
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
                route_distinctness_required=bool(case.get("route_distinctness_required", False)),
                pricing_relevant=bool(case.get("pricing_relevant", False)),
                governance_relevant=bool(case.get("governance_relevant", True)),
                governance_blockers_apply_directly=bool(case.get("governance_blockers_apply_directly", True)),
                runtime_route_attempt=runtime_route_attempt,
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
                evidence_bundle_id=synthetic_id(
                    "bundle",
                    f"{benchmark_run_id}_{assignment.case_id}_{assignment.candidate.route_id}",
                ),
                timestamp_utc=utc_now_iso(),
                source_ref="m2_attempt_executor",
                notes=[assignment.operator_note] if assignment.operator_note else [],
            )
            self._insert_attempt_artifacts(attempt, execution, validation)
            if assignment.live_execution:
                selected_route_identity = dict(execution.route_trace.get("selected_route_identity") or {})
                selected_route_identity.setdefault("transport_kind", str(surface_record.get("transport_kind") or ""))
                signature_payload = _execution_signature_payload(
                    route_trace=execution.route_trace,
                    outputs=execution.outputs,
                    selected_route_identity=selected_route_identity,
                    surface_transport_kind=str(surface_record.get("transport_kind") or ""),
                )
                signature_hash = hash_json(signature_payload)
                route_identity_row = {
                    "benchmark_run_id": benchmark_run_id,
                    "case_id": assignment.case_id,
                    "case_attempt_id": attempt.case_attempt_id,
                    "route_id": assignment.candidate.route_id,
                    "cohort": assignment.candidate.cohort,
                    "surface_class": assignment.candidate.surface_class,
                    "planned_route_identity": {
                        "provider_name": assignment.candidate.provider_name,
                        "model_key": assignment.candidate.model_key,
                        "provider_model_id": assignment.candidate.provider_model_id,
                        "surface_id": assignment.candidate.surface_id,
                        "transport_kind": str(surface_record.get("transport_kind") or ""),
                    },
                    "selected_route_identity": selected_route_identity,
                    "effective_execution_signature": signature_payload,
                    "effective_execution_signature_hash": signature_hash,
                    "route_signature_source_refs": [
                        "ROUTE_TRACE.json",
                        "outputs/STEP_METRICS.json",
                        "outputs/RUN_ROUTING_FINGERPRINT.json",
                        "outputs/ROUTING_LOG.json",
                    ],
                    "contract_fail_reason": execution.contract_fail_reason,
                    "validator_pass": validation.passed,
                }
                route_identity_rows.append(route_identity_row)
                prior_routes = live_route_signatures.setdefault(assignment.case_id, {})
                for prior_route_id, prior_row in prior_routes.items():
                    if (
                        prior_route_id != assignment.candidate.route_id
                        and str(prior_row.get("effective_execution_signature_hash") or "") == signature_hash
                    ):
                        route_collapse = {
                            "status": "blocked",
                            "benchmark_run_id": benchmark_run_id,
                            "case_id": assignment.case_id,
                            "blocked_route_id": assignment.candidate.route_id,
                            "conflicting_route_id": prior_route_id,
                            "effective_execution_signature_hash": signature_hash,
                            "blocked_route_signature": route_identity_row,
                            "conflicting_route_signature": prior_row,
                            "message": (
                                "campaign route collapse detected: live routes resolved to the same execution-time "
                                "provider/model/transport/signature tuple"
                            ),
                        }
                        break
                prior_routes[assignment.candidate.route_id] = route_identity_row
            case_attempt_ids.append(attempt.case_attempt_id)
            bundle_ids.append(attempt.evidence_bundle_id)
            if first_attempt_payload is None:
                first_attempt_payload = self.repo.fetch_attempt(attempt.case_attempt_id)
                first_validator_payload = validation.details_payload
                first_route_trace = execution.route_trace
                first_executor_links = execution.executor_links
            if route_collapse is not None:
                break

        return AttemptExecutionReport(
            benchmark_run_id=benchmark_run_id,
            case_attempt_ids=case_attempt_ids,
            bundle_ids=bundle_ids,
            db_row_counts=self.repo.count_rows(),
            sample_attempt=first_attempt_payload or {},
            sample_validator_results=first_validator_payload or {},
            sample_route_trace=first_route_trace or {},
            sample_executor_links=first_executor_links or {},
            route_identity_rows=route_identity_rows,
            route_collapse=route_collapse,
        )

    def execute_starter_set(self, case_ids: list[str]) -> AttemptExecutionReport:
        self._ensure_registry()
        assignments: list[CampaignAssignment] = []
        fixture_repo = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "golden_repo_min"
        for case_id in case_ids:
            case = self.repo.fetch_benchmark_case(case_id)
            if case is None:
                raise RuntimeError(f"missing benchmark case {case_id}")
            surface_class = str((case.get("surface_scope") or ["local_or_open_weight"])[0])
            route_context = _attempt_route_context(surface_class)
            assignments.append(
                CampaignAssignment(
                    candidate=CampaignCandidate(
                        route_id=route_context["route_id"],
                        cohort="smoke",
                        surface_id=route_context["surface_id"],
                        surface_class=surface_class,
                        provider_name=route_context["surface_id"].replace("surface_", "").replace("_api_v1", "").replace("_fixture_v1", ""),
                        model_key=route_context["route_id"],
                        provider_model_id=route_context["route_id"],
                        admission_reason="Synthetic smoke coverage.",
                        policy_note="Synthetic smoke route.",
                    ),
                    case_id=case_id,
                    archetype_id=str(case["archetype_id"]),
                    profile_id=route_context["profile_id"],
                    control_anchor_group_id=route_context["control_anchor_group_id"],
                    live_execution=False,
                    phase="A" if str(case.get("executor_kind")) == "runtime_v5_adapter" else str(case.get("phase_or_step_family") or "synthetic"),
                    repo_root=fixture_repo,
                    routing_override_model=None,
                )
            )
        return self.execute_assignments(
            assignments=assignments,
            case_set_id="benchmark_registry_starter_v1",
            run_type="benchmark_execution_smoke",
            trigger_ref="TP-RTE-BENCH-M2",
            benchmark_run_prefix="m2_exec",
        )
