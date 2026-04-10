from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..policies.loader import load_policy_pack
from .freshness import FreshnessOutcome


_POLICY = load_policy_pack("recommendation_state_policy_v1.json")


@dataclass(frozen=True)
class RecommendationPolicy:
    policy_id: str = str(_POLICY["policy_id"])
    policy_version: str = str(_POLICY["policy_version"])
    regression_floor: float = float(_POLICY["regression_floor"])
    min_sample_size_for_recommended: int = int(_POLICY["min_sample_size_for_recommended"])


def collect_blockers(
    attempt: dict[str, Any],
    case: dict[str, Any],
    profile_fit: dict[str, Any],
    freshness: FreshnessOutcome,
    control_deltas: list[dict[str, Any]],
    policy: RecommendationPolicy | None = None,
) -> list[str]:
    active_policy = policy or RecommendationPolicy()
    blockers = list(freshness.blockers)
    if not bool(attempt.get("contract_gate_pass")):
        blockers.append("contract_gate_failure")
    if str(attempt.get("surface_class")) == "local_or_open_weight":
        blockers.append("local_open_weight_promotion_forbidden")
    if "local_or_open_weight_not_production_eligible" in set(profile_fit.get("operational_risk_flags", [])):
        blockers.append("surface_policy_exclusion")
    if "governance_posture_unresolved" in set(profile_fit.get("operational_risk_flags", [])):
        blockers.append("governance_posture_unresolved")
    if str(case.get("validator_suite_id")) == "validators_phase_s_advisory_v1":
        blockers.append("phase_s_stricter_review_requirement")
    computed_deltas = [
        delta
        for delta in control_deltas
        if str(delta.get("delta_state", "")).startswith("computed")
    ]
    if not control_deltas:
        blockers.append("missing_comparable_control_anchor")
    elif any(str(delta.get("delta_state", "")).startswith("not_comparable") for delta in control_deltas):
        blockers.append("missing_comparable_control_anchor")
    elif not computed_deltas:
        blockers.append("missing_comparable_control_anchor")
    else:
        task_deltas = [delta for delta in computed_deltas if delta.get("metric_name") == "task_success"]
        if task_deltas and float(task_deltas[0].get("delta_value", 0.0)) < active_policy.regression_floor:
            blockers.append("regression_delta_below_policy_floor")
    if int(profile_fit.get("attempt_total", 0)) < active_policy.min_sample_size_for_recommended:
        blockers.append("insufficient_sample_size")
    return sorted(set(blockers))
