from __future__ import annotations

from collections import Counter
from typing import Any


def build_case_set_rollup(
    benchmark_run_id: str,
    case_set: dict[str, Any],
    attempts: list[dict[str, Any]],
) -> dict[str, Any]:
    total = len(attempts)
    gate_pass = sum(1 for attempt in attempts if bool(attempt.get("contract_gate_pass")))
    avg_task = round(sum(float(attempt.get("task_success_score", 0.0)) for attempt in attempts) / total, 6) if total else 0.0
    surface_counter = Counter(str(attempt.get("surface_class")) for attempt in attempts)
    archetype_counter = Counter(str(attempt.get("archetype_id")) for attempt in attempts)
    benchmark_modes = sorted({str(attempt.get("benchmark_mode") or "runtime_route") for attempt in attempts})
    candidate_types = sorted({str(attempt.get("candidate_type") or "route_candidate") for attempt in attempts})
    return {
        "benchmark_run_id": benchmark_run_id,
        "rollup_type": "case_set",
        "case_set_id": case_set["case_set_id"],
        "control_anchor_group_id": case_set["control_anchor_group_id"],
        "benchmark_modes": benchmark_modes,
        "candidate_types": candidate_types,
        "lane_isolation_preserved": len(benchmark_modes) <= 1,
        "attempt_total": total,
        "contract_pass_total": gate_pass,
        "contract_pass_rate": round(gate_pass / total, 6) if total else 0.0,
        "average_task_success_score": avg_task,
        "surface_class_breakdown": dict(sorted(surface_counter.items())),
        "archetype_breakdown": dict(sorted(archetype_counter.items())),
    }
