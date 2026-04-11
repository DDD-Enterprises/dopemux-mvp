from __future__ import annotations

from typing import Any

from ..models.enums import EvidenceClass
from .explainability import evidence_claim


def build_profile_summaries(
    benchmark_run_id: str,
    profile_fit_rows: list[dict[str, Any]],
    recommendations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for row in sorted(profile_fit_rows, key=lambda item: str(item["profile_id"])):
        profile_id = str(row["profile_id"])
        matching = [item for item in recommendations if str(item.get("profile_id")) == profile_id]
        summaries.append(
            {
                "benchmark_run_id": benchmark_run_id,
                "profile_id": profile_id,
                "benchmark_modes": row.get("benchmark_modes", []),
                "candidate_types": row.get("candidate_types", []),
                "lane_isolation_preserved": row.get("lane_isolation_preserved", True),
                "allowed_surfaces": row.get("allowed_surfaces", []),
                "recommendation_state_counts": row.get("recommendation_state_counts", {}),
                "recommendation_ids": row.get("recommendation_ids", []),
                "contract_pass_rate": row.get("contract_pass_rate"),
                "average_task_success_score": row.get("average_task_success_score"),
                "operational_risk_flags": row.get("operational_risk_flags", []),
                "claims": [
                    evidence_claim(
                        statement=f"Profile {profile_id} has {len(matching)} active recommendations.",
                        evidence_class=EvidenceClass.GOVERNANCE_DERIVED.value,
                        refs=[f"PROFILE_FIT__{profile_id}"],
                    ),
                    evidence_claim(
                        statement=f"Profile {profile_id} contract pass rate is {row.get('contract_pass_rate')}.",
                        evidence_class=EvidenceClass.BENCHMARK_DERIVED.value,
                        refs=[f"PROFILE_FIT__{profile_id}"],
                    ),
                    evidence_claim(
                        statement=f"Profile {profile_id} remains a downstream consumer of runtime_route evidence rather than a raw execution lane.",
                        evidence_class=EvidenceClass.GOVERNANCE_DERIVED.value,
                        refs=[f"PROFILE_FIT__{profile_id}"],
                    ),
                ],
            }
        )
    return summaries
