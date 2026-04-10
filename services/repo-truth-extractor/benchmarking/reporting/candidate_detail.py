from __future__ import annotations

from typing import Any

from .explainability import build_explanation_chain


def build_candidate_detail(
    recommendation: dict[str, Any],
    governance_packet: dict[str, Any],
    attempt: dict[str, Any],
    bundle: dict[str, Any],
    case: dict[str, Any],
    case_set_rollup: dict[str, Any],
    archetype_rollup: dict[str, Any],
    profile_fit: dict[str, Any],
    control_deltas: list[dict[str, Any]],
    latest_governance_decision: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "recommendation_id": recommendation["recommendation_id"],
        "case_id": attempt["case_id"],
        "route_id": recommendation["route_id"],
        "surface_id": recommendation["surface_id"],
        "surface_class": attempt["surface_class"],
        "archetype_id": recommendation["archetype_id"],
        "profile_id": recommendation["profile_id"],
        "runtime_version": recommendation["runtime_version"],
        "contract_version": recommendation["contract_version"],
        "contract_snapshot_id": recommendation["contract_snapshot_id"],
        "current_recommendation_state": recommendation["recommendation_state"],
        "failed_gates": recommendation["failed_gates"],
        "freshness_state": recommendation["freshness_state"],
        "dispute_state": recommendation["dispute_state"],
        "required_action": recommendation["required_action"],
        "requires_review": recommendation["requires_review"],
        "control_deltas": control_deltas,
        "supporting_attempt_ref": attempt["case_attempt_id"],
        "evidence_bundle_ref": bundle["bundle_id"],
        "latest_governance_decision": latest_governance_decision,
        "unresolved_unknowns": attempt.get("unknowns_open", []),
        "phase_caveat": "phase_s_policy_sensitive" if case.get("validator_suite_id") == "validators_phase_s_advisory_v1" else None,
        "explanation_chain": build_explanation_chain(
            recommendation=recommendation,
            governance_packet=governance_packet,
            attempt=attempt,
            bundle=bundle,
            case_set_rollup=case_set_rollup,
            archetype_rollup=archetype_rollup,
            profile_fit=profile_fit,
            control_deltas=control_deltas,
            latest_governance_decision=latest_governance_decision,
        ),
    }
