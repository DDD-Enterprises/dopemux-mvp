from __future__ import annotations

from typing import Any


def build_profile_fit_rows(
    benchmark_run_id: str,
    profiles: list[dict[str, Any]],
    attempts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for profile in sorted(profiles, key=lambda item: str(item["profile_id"])):
        matching = [attempt for attempt in attempts if str(attempt.get("profile_id")) == str(profile["profile_id"])]
        total = len(matching)
        average_score = round(sum(float(item.get("task_success_score", 0.0)) for item in matching) / total, 6) if total else 0.0
        policy_bounds = dict(profile.get("policy_bounds", {}))
        flags = {
            "local_or_open_weight_not_production_eligible"
            for item in matching
            if str(item.get("surface_class")) == "local_or_open_weight"
        }
        if str(policy_bounds.get("governance_posture") or "") == "unresolved":
            flags.add("governance_posture_unresolved")
        rows.append(
            {
                "benchmark_run_id": benchmark_run_id,
                "profile_id": profile["profile_id"],
                "is_production_profile": bool(profile.get("is_production_profile")),
                "allowed_surfaces": profile.get("allowed_surfaces", []),
                "allowed_archetypes": profile.get("allowed_archetypes", []),
                "attempt_total": total,
                "contract_pass_rate": round(sum(1 for item in matching if bool(item.get("contract_gate_pass"))) / total, 6) if total else 0.0,
                "average_task_success_score": average_score,
                "operational_risk_flags": sorted(flags),
            }
        )
    return rows
