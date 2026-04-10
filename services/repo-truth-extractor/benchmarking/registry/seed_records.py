from __future__ import annotations

from pathlib import Path

from ..models.entities import (
    Archetype,
    BenchmarkCase,
    BenchmarkCaseAttempt,
    BenchmarkCaseSet,
    BenchmarkRun,
    ContractSnapshot,
    ControlAnchorGroup,
    ControlDelta,
    GovernanceDecision,
    ModelRecord,
    Profile,
    PromotionRecommendation,
    ProviderSurface,
    RetryPolicy,
    RouteRecord,
    ValidatorResult,
    ValidatorSuite,
)
from ..models.ids import synthetic_id, synthetic_run_id, utc_now_iso
from ..storage.hashing import hash_json


def synthetic_fixture_records(git_commit: str) -> dict[str, object]:
    now = utc_now_iso()
    surface = ProviderSurface(
        surface_id="surface_openrouter_api_v1",
        surface_class="openrouter_routed",
        provider_name="openrouter",
        transport_kind="https_json",
        endpoint_ref="https://openrouter.ai/api/v1",
        logging_posture="operator_visible",
        residency_posture="unknown",
        surface_hash=hash_json({"surface": "openrouter_v1"}),
        source_ref="prompt4_benchmark_architecture",
    )
    model = ModelRecord(
        model_key="openai/gpt-5.4",
        display_name="GPT-5.4",
        family="gpt-5",
        source_registry_ref="prompt1_model_registry",
        registry_class="current_state_authority",
        lifecycle_status="candidate",
        content_hash=hash_json({"model_key": "openai/gpt-5.4"}),
    )
    route = RouteRecord(
        route_id="route_openrouter_openai_gpt_5_4_v1",
        surface_id=surface.surface_id,
        model_key=model.model_key,
        provider_model_id="openai/gpt-5.4",
        api_key_ref="OPENROUTER_API_KEY",
        route_pin="openai/gpt-5.4",
        strict_json_schema_declared=True,
        strict_passthrough_verified=False,
        route_hash=hash_json({"route": "openrouter/gpt-5.4"}),
        content_hash=hash_json({"route_id": "route_openrouter_openai_gpt_5_4_v1"}),
    )
    contract_snapshot = ContractSnapshot(
        contract_snapshot_id="contract_promptset_v4_runtime_v5_smoke",
        runtime_version="v5",
        contract_version="promptsets/v4",
        source_files=[
            "services/repo-truth-extractor/run_extraction_v5.py",
            "services/repo-truth-extractor/promptsets/v4/promptset.yaml",
        ],
        content_hashes={
            "runtime": hash_json({"runtime_version": "v5"}),
            "contract": hash_json({"contract_version": "promptsets/v4"}),
        },
        strict_schema_expected=True,
        snapshot_hash=hash_json({"runtime_version": "v5", "contract_version": "promptsets/v4"}),
        content_hash=hash_json({"snapshot_id": "contract_promptset_v4_runtime_v5_smoke"}),
    )
    validator_suite = ValidatorSuite(
        validator_suite_id="validators_runtime_strict_json_v1",
        surface_scope=[surface.surface_class.value],
        validators=["json_schema_shape", "artifact_presence"],
        strength_class="strong",
        version_hash=hash_json({"validator_suite_id": "validators_runtime_strict_json_v1"}),
        content_hash=hash_json({"validator_suite_id": "validators_runtime_strict_json_v1"}),
    )
    archetype = Archetype(
        archetype_id="strict_evidence_extraction",
        description="Synthetic strict evidence extraction smoke archetype",
        phase_families=["D_C_G_X"],
        success_rubric_id="rubric_strict_v1",
        promotion_policy_id="policy_manual_review_only",
        content_hash=hash_json({"archetype_id": "strict_evidence_extraction"}),
    )
    control_anchor_group = ControlAnchorGroup(
        anchor_group_id="anchor_openrouter_strict_v1",
        surface_class=surface.surface_class,
        archetype_id=archetype.archetype_id,
        route_ids=[route.route_id],
        required=True,
        content_hash=hash_json({"anchor_group_id": "anchor_openrouter_strict_v1"}),
    )
    profile = Profile(
        profile_id="balanced_production",
        allowed_surfaces=[surface.surface_class.value],
        allowed_archetypes=[archetype.archetype_id],
        policy_bounds={"local_or_open_weight": "not_production_eligible"},
        is_production_profile=True,
        content_hash=hash_json({"profile_id": "balanced_production"}),
    )
    retry_policy = RetryPolicy(
        retry_policy_id="retry_ladder_structural_fail_closed_v1",
        same_route_rules=["same_surface_only", "fail_closed"],
        escalation_rules=["no_live_calls_in_m0"],
        max_hops=1,
        policy_hash=hash_json({"retry_policy_id": "retry_ladder_structural_fail_closed_v1"}),
        content_hash=hash_json({"retry_policy_id": "retry_ladder_structural_fail_closed_v1"}),
    )
    benchmark_case = BenchmarkCase(
        case_id="strict_extract_conflicting_evidence_v1",
        case_version=1,
        archetype_id=archetype.archetype_id,
        phase_or_step_family="D_C_G_X",
        prompt_inventory_refs=["promptsets/v4/promptset.yaml"],
        surface_scope=[surface.surface_class.value],
        executor_kind="synthetic_fixture",
        validator_suite_id=validator_suite.validator_suite_id,
        golden_evaluator_id="task_eval_smoke_v1",
        input_bundle_id="input_bundle_smoke_v1",
        contract_snapshot_id=contract_snapshot.contract_snapshot_id,
        content_hash=hash_json({"case_id": "strict_extract_conflicting_evidence_v1"}),
    )
    case_set = BenchmarkCaseSet(
        case_set_id="strict_extract_weekly_v1",
        case_set_version=1,
        archetype_id=archetype.archetype_id,
        benchmark_stage="admission_smoke",
        case_ids=[benchmark_case.case_id],
        control_anchor_group_id=control_anchor_group.anchor_group_id,
        schedule_class="manual_smoke",
        content_hash=hash_json({"case_set_id": "strict_extract_weekly_v1"}),
    )
    benchmark_run = BenchmarkRun(
        benchmark_run_id=synthetic_run_id("m0_smoke"),
        run_type="synthetic_smoke",
        trigger_type="manual",
        trigger_ref="TP-RTE-BENCH-M0",
        git_commit=git_commit,
        runtime_version="v5",
        contract_snapshot_ids=[contract_snapshot.contract_snapshot_id],
        status="READY_FOR_REVIEW",
        started_at=now,
        finished_at=now,
        content_hash=hash_json({"trigger_ref": "TP-RTE-BENCH-M0", "git_commit": git_commit}),
    )
    attempt = BenchmarkCaseAttempt(
        case_attempt_id=synthetic_id("bca", benchmark_run.benchmark_run_id),
        benchmark_run_id=benchmark_run.benchmark_run_id,
        case_id=benchmark_case.case_id,
        case_version=benchmark_case.case_version,
        case_set_id=case_set.case_set_id,
        archetype_id=archetype.archetype_id,
        phase_or_step_family=benchmark_case.phase_or_step_family,
        surface_class=surface.surface_class,
        surface_id=surface.surface_id,
        profile_id=profile.profile_id,
        route_id=route.route_id,
        control_anchor_group_id=control_anchor_group.anchor_group_id,
        runtime_version="v5",
        contract_version="promptsets/v4",
        contract_snapshot_id=contract_snapshot.contract_snapshot_id,
        schema_id="REPO_ENTITY_LIST@v1",
        strict_schema_expected=True,
        validator_suite_id=validator_suite.validator_suite_id,
        attempt_number=1,
        retry_policy_id=retry_policy.retry_policy_id,
        temperature_or_equivalent=0.0,
        max_tokens_or_budget=4096,
        tool_mode="disabled",
        batch_mode="sync",
        contract_gate_pass=True,
        contract_gate_strength="strong",
        contract_fail_reason=None,
        validator_pass=True,
        task_success_score=1.0,
        task_score_breakdown={
            "completeness_score": 1.0,
            "evidence_score": 1.0,
            "stability_score": 1.0,
        },
        operational_metrics={
            "latency_ms": 1,
            "tokens_input": 0,
            "tokens_output": 0,
            "cost_estimate_usd": 0.0,
            "route_hop_total": 1,
            "repair_invocations": 0,
            "request_error_rate": 0.0,
        },
        unknowns_open=["metadata_is_not_suitability_proof"],
        output_artifact_ref="outputs/REPO_ENTITY_LIST.json",
        golden_eval_ref="TASK_EVAL.json",
        control_delta_ref="CONTROL_DELTA.json",
        evidence_bundle_id=synthetic_id("bundle", benchmark_run.benchmark_run_id),
        timestamp_utc=now,
    )
    validator_result = ValidatorResult(
        validator_result_id=synthetic_id("validator_result", attempt.case_attempt_id),
        case_attempt_id=attempt.case_attempt_id,
        validator_suite_id=validator_suite.validator_suite_id,
        validator_name="artifact_presence",
        passed=True,
        strength_class="strong",
        failure_reason=None,
        details_ref="VALIDATOR_RESULTS.json",
        content_hash=hash_json({"validator_result_id": synthetic_id("validator_result", attempt.case_attempt_id)}),
    )
    control_delta = ControlDelta(
        control_delta_id=synthetic_id("control_delta", attempt.case_attempt_id),
        candidate_attempt_id=attempt.case_attempt_id,
        anchor_attempt_id=attempt.case_attempt_id,
        metric_name="task_success_score",
        candidate_value=1.0,
        anchor_value=1.0,
        delta_value=0.0,
        delta_state="parity",
        content_hash=hash_json({"control_delta_id": synthetic_id("control_delta", attempt.case_attempt_id)}),
    )
    recommendation = PromotionRecommendation(
        recommendation_id=synthetic_id("recommendation", attempt.case_attempt_id),
        route_id=route.route_id,
        surface_id=surface.surface_id,
        archetype_id=archetype.archetype_id,
        profile_id=profile.profile_id,
        recommendation_state="not_evaluated",
        failed_gates=[],
        evidence_bundle_ids=[attempt.evidence_bundle_id],
        requires_review=True,
        content_hash=hash_json({"recommendation_id": synthetic_id("recommendation", attempt.case_attempt_id)}),
    )
    decision = GovernanceDecision(
        decision_id=synthetic_id("decision", attempt.case_attempt_id),
        recommendation_id=recommendation.recommendation_id,
        decision_type="defer",
        decision_outcome="recorded",
        actor="operator_pending",
        timestamp=now,
        reason="M0 intentionally does not implement governance workflows.",
        content_hash=hash_json({"decision_id": synthetic_id("decision", attempt.case_attempt_id)}),
    )
    registry_snapshot_files = [
        "promptset.yaml",
        "artifacts.yaml",
        "model_map.yaml",
        "prompt_inventory_manifest.md",
        "phase_s_registry.json",
        "phase_fl_int_registry.json",
        "scoring_policy.json",
        "profile_policy.json",
    ]
    return {
        "provider_surface": surface,
        "model": model,
        "route": route,
        "contract_snapshot": contract_snapshot,
        "validator_suite": validator_suite,
        "control_anchor_group": control_anchor_group,
        "archetype": archetype,
        "profile": profile,
        "retry_policy": retry_policy,
        "benchmark_case": benchmark_case,
        "benchmark_case_set": case_set,
        "benchmark_run": benchmark_run,
        "benchmark_case_attempt": attempt,
        "validator_result": validator_result,
        "control_delta": control_delta,
        "promotion_recommendation": recommendation,
        "governance_decision": decision,
        "registry_snapshot_files": registry_snapshot_files,
        "route_trace": {
            "route_id": route.route_id,
            "surface_class": surface.surface_class.value,
            "runtime_version": "v5",
            "contract_version": "promptsets/v4",
            "hops": [{"hop_index": 0, "route_id": route.route_id, "ok": True}],
        },
        "validator_results_payload": {
            "validator_suite_id": validator_suite.validator_suite_id,
            "results": [{"validator_name": "artifact_presence", "pass": True}],
        },
        "task_eval_payload": {
            "task_success_score": 1.0,
            "breakdown": {
                "completeness_score": 1.0,
                "evidence_score": 1.0,
                "stability_score": 1.0,
            },
        },
        "control_delta_payload": {
            "metric_name": control_delta.metric_name,
            "candidate_value": control_delta.candidate_value,
            "anchor_value": control_delta.anchor_value,
            "delta_value": control_delta.delta_value,
            "delta_state": control_delta.delta_state,
        },
        "executor_links_payload": {
            "executor_kind": "synthetic_fixture",
            "live_provider_calls": False,
            "runtime_script": "services/repo-truth-extractor/run_extraction_v5.py",
            "contract_source": "services/repo-truth-extractor/promptsets/v4",
        },
        "outputs": {
            "REPO_ENTITY_LIST.json": {
                "entities": [
                    {"id": benchmark_case.case_id, "class": "benchmark_case"},
                    {"id": attempt.case_attempt_id, "class": "benchmark_case_attempt"},
                ]
            }
        },
    }
