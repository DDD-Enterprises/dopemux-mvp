from __future__ import annotations

import sys
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.models.entities import BenchmarkCaseAttempt, ProfileSynthesisInput
from benchmarking.models.lane_contracts import (
    build_direct_model_attempt_payload,
    build_profile_synthesis_input_payload,
)


def test_direct_model_attempt_shape_is_structurally_distinct_from_runtime_route() -> None:
    attempt = BenchmarkCaseAttempt(
        case_attempt_id="bca_direct_model_demo",
        benchmark_run_id="run_direct_model_demo",
        case_id="direct_model_json_contract_v1",
        case_version=1,
        case_set_id="direct_model_mvp_set_v1",
        benchmark_mode="direct_model",
        candidate_type="model_candidate",
        execution_family="direct_api_execution",
        archetype_id="strict_evidence_extraction",
        phase_or_step_family="D_C_G_X",
        surface_class="direct_provider_api",
        surface_id="surface_openai_api_v1",
        runtime_version="v5",
        contract_version="promptsets/v4",
        contract_snapshot_id="contract_promptset_v4_runtime_v5_smoke",
        schema_id="REPO_ENTITY_LIST@v1",
        strict_schema_expected=True,
        validator_suite_id="validators_runtime_strict_json_v1",
        attempt_number=1,
        retry_policy_id="retry_ladder_structural_fail_closed_v1",
        temperature_or_equivalent=0.0,
        max_tokens_or_budget=2048,
        tool_mode="disabled",
        batch_mode="sync",
        pricing_relevant=True,
        governance_relevant=False,
        governance_blockers_apply_directly=False,
        direct_model_attempt=build_direct_model_attempt_payload(
            declared_provider_name="openrouter",
            declared_model_key="openrouter/openai/gpt-5.4-mini",
            selected_provider_name="openrouter",
            selected_model_key="openrouter/openai/gpt-5.4-mini",
            direct_request_ref="DIRECT_REQUEST.json",
            direct_response_ref="DIRECT_RESPONSE.json",
            pricing_metrics={"cost_estimate_usd": 0.01},
            latency_metrics={"latency_ms": 123.0},
            validator_results_ref="VALIDATOR_RESULTS.json",
        ),
        contract_gate_pass=True,
        contract_gate_strength="strong",
        validator_pass=True,
        task_success_score=1.0,
        output_artifact_ref="outputs/DIRECT_MODEL_OUTPUT.json",
        golden_eval_ref="TASK_EVAL.json",
        control_delta_ref="CONTROL_DELTA.json",
        evidence_bundle_id="bundle_direct_model_demo",
    )

    assert attempt.benchmark_mode.value == "direct_model"
    assert attempt.direct_model_attempt is not None
    assert attempt.runtime_route_attempt is None


def test_profile_synthesis_input_remains_downstream_only() -> None:
    synthesis = ProfileSynthesisInput(
        synthesis_input_id="profile_synthesis_demo",
        profile_id="balanced_production",
        source_attempt_ids=["attempt_runtime_a", "attempt_direct_b"],
        source_rollup_ids=["PROFILE_FIT__balanced_production", "PORTFOLIO_VIEW"],
        pricing_source_refs=["DIRECT_MODEL_COMPARISON.json"],
        governance_source_refs=["PROMOTION_RECOMMENDATIONS.json"],
        notes=["Downstream-only synthesis input; not a raw execution attempt."],
    )
    payload = build_profile_synthesis_input_payload(
        profile_id=synthesis.profile_id,
        source_attempt_ids=synthesis.source_attempt_ids,
        source_rollup_ids=synthesis.source_rollup_ids,
        pricing_source_refs=synthesis.pricing_source_refs,
        governance_source_refs=synthesis.governance_source_refs,
    )

    assert synthesis.benchmark_mode.value == "profile_synthesis_input"
    assert synthesis.execution_family.value == "downstream_synthesis"
    assert payload["source_attempt_ids"] == ["attempt_runtime_a", "attempt_direct_b"]
