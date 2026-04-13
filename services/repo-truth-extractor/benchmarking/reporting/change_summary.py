from __future__ import annotations

from typing import Any

from ..models.enums import EvidenceClass
from .explainability import evidence_claim


def build_change_summary(
    current_recommendation: dict[str, Any],
    previous_recommendation: dict[str, Any] | None,
    current_history: dict[str, Any],
    previous_history: dict[str, Any] | None,
) -> dict[str, Any]:
    previous_state = previous_recommendation.get("recommendation_state") if previous_recommendation else None
    current_state = current_recommendation.get("recommendation_state")
    previous_blockers = set(previous_recommendation.get("failed_gates", [])) if previous_recommendation else set()
    current_blockers = set(current_recommendation.get("failed_gates", []))
    previous_decision = previous_history.get("current_effective_decision") if previous_history else None
    current_decision = current_history.get("current_effective_decision")
    return {
        "recommendation_id": current_recommendation["recommendation_id"],
        "candidate_key": current_history["candidate_key"],
        "recommendation_state_change": {
            "previous": previous_state,
            "current": current_state,
            "changed": previous_state != current_state,
        },
        "blocker_delta": {
            "added": sorted(current_blockers - previous_blockers),
            "removed": sorted(previous_blockers - current_blockers),
        },
        "freshness_change": {
            "previous": previous_recommendation.get("freshness_state") if previous_recommendation else None,
            "current": current_recommendation.get("freshness_state"),
        },
        "governance_state_change": {
            "previous": previous_decision.get("decision_type") if previous_decision else None,
            "current": current_decision.get("decision_type") if current_decision else None,
        },
        "claims": [
            evidence_claim(
                statement=f"Recommendation state changed from {previous_state} to {current_state}.",
                evidence_class=EvidenceClass.GOVERNANCE_DERIVED.value,
                refs=[current_recommendation["recommendation_id"]],
            ),
            evidence_claim(
                statement=f"Blocker delta added {sorted(current_blockers - previous_blockers)} and removed {sorted(previous_blockers - current_blockers)}.",
                evidence_class=EvidenceClass.GOVERNANCE_DERIVED.value,
                refs=[current_recommendation["recommendation_id"]],
            ),
        ],
    }
