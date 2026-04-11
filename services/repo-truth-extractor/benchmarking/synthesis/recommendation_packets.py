from __future__ import annotations

from typing import Any


def build_governance_packet(
    recommendation: dict[str, Any],
    attempt: dict[str, Any],
    case: dict[str, Any],
    profile_fit: dict[str, Any],
    case_set_rollup: dict[str, Any],
    archetype_rollup: dict[str, Any],
    control_deltas: list[dict[str, Any]],
) -> dict[str, Any]:
    control_summary = {
        "delta_count": len(control_deltas),
        "states": sorted({str(delta.get("delta_state")) for delta in control_deltas}),
        "metrics": sorted({str(delta.get("metric_name")) for delta in control_deltas}),
    }
    return {
        "recommendation_id": recommendation["recommendation_id"],
        "benchmark_run_id": recommendation["benchmark_run_id"],
        "benchmark_mode": recommendation["benchmark_mode"],
        "candidate_type": recommendation["candidate_type"],
        "route_id": recommendation["route_id"],
        "surface_id": recommendation["surface_id"],
        "archetype_id": recommendation["archetype_id"],
        "profile_id": recommendation["profile_id"],
        "runtime_version": recommendation["runtime_version"],
        "contract_version": recommendation["contract_version"],
        "contract_snapshot_id": recommendation["contract_snapshot_id"],
        "recommendation_state": recommendation["recommendation_state"],
        "failed_gates": recommendation["failed_gates"],
        "freshness_state": recommendation["freshness_state"],
        "dispute_state": recommendation["dispute_state"],
        "required_action": recommendation["required_action"],
        "requires_review": recommendation["requires_review"],
        "evidence_bundle_ids": recommendation["evidence_bundle_ids"],
        "relevant_rollup_ids": recommendation["relevant_rollup_ids"],
        "control_delta_summary": control_summary,
        "subject": {
            "case_id": attempt["case_id"],
            "case_version": attempt["case_version"],
            "case_title": case.get("title"),
            "benchmark_mode": attempt["benchmark_mode"],
            "candidate_type": attempt["candidate_type"],
            "execution_family": attempt["execution_family"],
            "surface_class": attempt["surface_class"],
            "profile_id": attempt["profile_id"],
            "validator_suite_id": attempt["validator_suite_id"],
        },
        "rollup_summary": {
            "profile_fit": profile_fit,
            "case_set_rollup": case_set_rollup,
            "archetype_rollup": archetype_rollup,
        },
    }
