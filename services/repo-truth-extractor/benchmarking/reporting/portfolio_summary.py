from __future__ import annotations

from collections import Counter
from typing import Any

from ..models.enums import EvidenceClass
from .explainability import evidence_claim


def build_portfolio_summary(
    benchmark_run_id: str,
    portfolio_view: dict[str, Any],
    recommendations: list[dict[str, Any]],
) -> dict[str, Any]:
    state_counts = Counter(str(item.get("recommendation_state")) for item in recommendations)
    profile_matrix: dict[str, dict[str, int]] = {}
    for recommendation in recommendations:
        profile_id = str(recommendation["profile_id"])
        state = str(recommendation["recommendation_state"])
        profile_matrix.setdefault(profile_id, {})
        profile_matrix[profile_id][state] = profile_matrix[profile_id].get(state, 0) + 1
    return {
        "benchmark_run_id": benchmark_run_id,
        "view_type": "portfolio_summary",
        "benchmark_modes": portfolio_view.get("benchmark_modes", []),
        "lane_isolation_preserved": bool(portfolio_view.get("lane_isolation_preserved", True)),
        "matrix_preserved": True,
        "recommendation_state_counts": dict(sorted(state_counts.items())),
        "profile_state_matrix": {key: dict(sorted(value.items())) for key, value in sorted(profile_matrix.items())},
        "portfolio_view_ref": "PORTFOLIO_VIEW",
        "claims": [
            evidence_claim(
                statement="Portfolio summary preserves a matrix structure and does not create a universal leaderboard.",
                evidence_class=EvidenceClass.GOVERNANCE_DERIVED.value,
                refs=["PORTFOLIO_VIEW"],
            ),
            evidence_claim(
                statement="Portfolio summary is runtime-route scoped and must not collapse direct_model evidence into route-profile truth.",
                evidence_class=EvidenceClass.GOVERNANCE_DERIVED.value,
                refs=["PORTFOLIO_VIEW"],
            ),
            evidence_claim(
                statement=f"Portfolio view contains {len(portfolio_view.get('recommendation_state_matrix', []))} recommendation-state entries.",
                evidence_class=EvidenceClass.GOVERNANCE_DERIVED.value,
                refs=["PORTFOLIO_VIEW"],
            ),
        ],
    }
