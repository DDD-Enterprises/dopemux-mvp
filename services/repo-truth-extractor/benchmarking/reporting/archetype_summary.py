from __future__ import annotations

from typing import Any

from ..models.enums import EvidenceClass
from .explainability import evidence_claim


def build_archetype_summaries(
    benchmark_run_id: str,
    archetype_rollups: list[dict[str, Any]],
    recommendations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for rollup in sorted(archetype_rollups, key=lambda item: str(item["archetype_id"])):
        archetype_id = str(rollup["archetype_id"])
        matching = [item for item in recommendations if str(item.get("archetype_id")) == archetype_id]
        summaries.append(
            {
                "benchmark_run_id": benchmark_run_id,
                "archetype_id": archetype_id,
                "surface_classes": rollup.get("surface_classes", []),
                "runtime_versions": rollup.get("runtime_versions", []),
                "contract_versions": rollup.get("contract_versions", []),
                "recommendation_states": sorted({str(item.get("recommendation_state")) for item in matching}),
                "claims": [
                    evidence_claim(
                        statement=f"Archetype {archetype_id} average task success score is {rollup.get('average_task_success_score')}.",
                        evidence_class=EvidenceClass.BENCHMARK_DERIVED.value,
                        refs=[f"ARCHETYPE_ROLLUP__{archetype_id}"],
                    ),
                    evidence_claim(
                        statement=f"Archetype {archetype_id} currently has {len(matching)} recommendations.",
                        evidence_class=EvidenceClass.GOVERNANCE_DERIVED.value,
                        refs=[f"ARCHETYPE_ROLLUP__{archetype_id}"],
                    ),
                ],
            }
        )
    return summaries
