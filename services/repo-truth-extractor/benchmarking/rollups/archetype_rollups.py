from __future__ import annotations

from collections import defaultdict
from typing import Any


def build_archetype_rollups(benchmark_run_id: str, attempts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for attempt in attempts:
        grouped[str(attempt["archetype_id"])].append(attempt)
    payloads: list[dict[str, Any]] = []
    for archetype_id, rows in sorted(grouped.items()):
        total = len(rows)
        task_average = round(sum(float(row.get("task_success_score", 0.0)) for row in rows) / total, 6) if total else 0.0
        benchmark_modes = sorted({str(row.get("benchmark_mode") or "runtime_route") for row in rows})
        candidate_types = sorted({str(row.get("candidate_type") or "route_candidate") for row in rows})
        payloads.append(
            {
                "benchmark_run_id": benchmark_run_id,
                "rollup_type": "archetype",
                "archetype_id": archetype_id,
                "benchmark_modes": benchmark_modes,
                "candidate_types": candidate_types,
                "lane_isolation_preserved": len(benchmark_modes) <= 1,
                "attempt_total": total,
                "contract_pass_rate": round(sum(1 for row in rows if bool(row.get("contract_gate_pass"))) / total, 6) if total else 0.0,
                "average_task_success_score": task_average,
                "surface_classes": sorted({str(row.get("surface_class")) for row in rows}),
                "runtime_versions": sorted({str(row.get("runtime_version")) for row in rows}),
                "contract_versions": sorted({str(row.get("contract_version")) for row in rows}),
            }
        )
    return payloads
