from __future__ import annotations

import sys
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.campaigns.route_identity import RouteIdentityRecord
from benchmarking.campaigns.route_separation import (
    CASE_FAMILY_SPECIFIC_CONVERGENCE,
    SELECTION_LAYER_OVERRIDE,
    TELEMETRY_UNDER_RESOLUTION,
    build_corrected_control_strategy,
    build_route_identity_truth_table,
    classify_route_collapse,
)


def _record(route_id: str, provider_name: str, provider_model_id: str, signature_hash: str) -> RouteIdentityRecord:
    return RouteIdentityRecord(
        benchmark_run_id="run",
        case_attempt_id=f"{route_id}_attempt",
        case_id="strict_extract_conflicting_evidence_v1",
        phase_or_step_family="A",
        surface_class="direct_provider_api" if provider_name != "openrouter" else "openrouter_routed",
        runtime_version="v5",
        contract_version="v4",
        contract_snapshot_id="snapshot",
        evidence_bundle_id=f"{route_id}_bundle",
        declared_route_id=route_id,
        selected_route_identity={
            "declared_route_id": route_id,
            "provider_name": provider_name,
            "provider_model_id": provider_model_id,
            "route_pin": f"{provider_name}/{provider_model_id}",
            "representative_phase_route": {
                "provider": "openrouter",
                "model_id": "openai/gpt-5.3-codex",
            },
        },
        effective_route_signature={"A:A0": ["openrouter/openai/gpt-5.3-codex"]},
        effective_route_signature_hash=signature_hash,
        route_signature_source_refs=["outputs/STEP_METRICS.json"],
        admissibility_status="derived",
        admissibility_blocker_codes=[],
        admissibility_notes=[],
    )


def test_route_separation_truth_table_classifies_override_and_convergence() -> None:
    intended_routes = [
        {
            "route_id": "route_openrouter_openai_gpt_5_4_v1",
            "cohort": "control",
            "case_id": "strict_extract_conflicting_evidence_v1",
            "surface_class": "openrouter_routed",
            "provider_name": "openrouter",
            "model_key": "openai/gpt-5.4",
            "provider_model_id": "openai/gpt-5.4",
        },
        {
            "route_id": "route_openai_gpt_5_4_v1",
            "cohort": "control",
            "case_id": "strict_extract_conflicting_evidence_v1",
            "surface_class": "direct_provider_api",
            "provider_name": "openai",
            "model_key": "openai/gpt-5.4",
            "provider_model_id": "gpt-5.4",
        },
    ]
    admissibility = {
        "comparisons": [
            {
                "comparison_type": "control_pair",
                "case_id": "strict_extract_conflicting_evidence_v1",
                "left_route_id": "route_openrouter_openai_gpt_5_4_v1",
                "right_route_id": "route_openai_gpt_5_4_v1",
                "left_signature_hashes": ["same_hash"],
                "right_signature_hashes": ["same_hash"],
                "signatures_equal": True,
            }
        ]
    }
    table = build_route_identity_truth_table(
        intended_routes=intended_routes,
        route_identities=[
            _record("route_openrouter_openai_gpt_5_4_v1", "openrouter", "openai/gpt-5.4", "same_hash"),
            _record("route_openai_gpt_5_4_v1", "openai", "gpt-5.4", "same_hash"),
        ],
        route_errors={},
        admissibility=admissibility,
    )
    assert len(table) == 2
    for row in table:
        assert row["meaningfully_distinct_for_case_family"] is False
        assert SELECTION_LAYER_OVERRIDE in row["collapse_cause_codes"]
        assert CASE_FAMILY_SPECIFIC_CONVERGENCE in row["collapse_cause_codes"]


def test_route_separation_truth_table_classifies_missing_telemetry() -> None:
    table = build_route_identity_truth_table(
        intended_routes=[
            {
                "route_id": "route_local_fixture_v1",
                "cohort": "experimental",
                "case_id": "tool_aware_repo_reasoning_v1",
                "surface_class": "local_or_open_weight",
                "provider_name": "local-fixture",
                "model_key": "local/benchmark-fixture",
                "provider_model_id": "local/benchmark-fixture",
            }
        ],
        route_identities=[],
        route_errors={
            ("tool_aware_repo_reasoning_v1", "route_local_fixture_v1"): [
                {"blocker_code": "MISSING_ROUTE_TELEMETRY", "message": "missing telemetry"}
            ]
        },
        admissibility={"comparisons": []},
    )
    assert table[0]["meaningfully_distinct_for_case_family"] is False
    assert TELEMETRY_UNDER_RESOLUTION in table[0]["collapse_cause_codes"]


def test_blocked_lane_strategy_is_emitted_when_live_routes_converge() -> None:
    truth_table = [
        {
            "route_id": "route_openrouter_openai_gpt_5_4_v1",
            "case_id": "strict_extract_conflicting_evidence_v1",
            "surface_class": "openrouter_routed",
            "meaningfully_distinct_for_case_family": False,
        },
        {
            "route_id": "route_openai_gpt_5_4_v1",
            "case_id": "strict_extract_conflicting_evidence_v1",
            "surface_class": "direct_provider_api",
            "meaningfully_distinct_for_case_family": False,
        },
    ]
    strategy = build_corrected_control_strategy(
        manifest={"campaign_id": "TP-RTE-BENCH-R1"},
        truth_table=truth_table,
        admissibility={"admissibility_blocker_codes": ["IDENTICAL_CONTROL_SIGNATURE"]},
    )
    assert strategy["status"] == "blocked_lane_verdict"
    assert strategy["r1_restart_truthful"] is False


def test_classify_route_collapse_counts_causes() -> None:
    payload = classify_route_collapse(
        [
            {
                "route_id": "a",
                "meaningfully_distinct_for_case_family": False,
                "collapse_cause_codes": [SELECTION_LAYER_OVERRIDE, CASE_FAMILY_SPECIFIC_CONVERGENCE],
            },
            {
                "route_id": "b",
                "meaningfully_distinct_for_case_family": True,
                "collapse_cause_codes": [],
            },
        ]
    )
    assert payload["status"] == "collapse_observed"
    assert payload["cause_counts"][SELECTION_LAYER_OVERRIDE] == 1
