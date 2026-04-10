from __future__ import annotations

from typing import Any

from .explainability import candidate_key


def build_governance_history(
    current_recommendation: dict[str, Any],
    all_recommendations: list[dict[str, Any]],
    all_decisions: list[dict[str, Any]],
) -> dict[str, Any]:
    key = candidate_key(current_recommendation)
    recommendation_history = sorted(
        [item for item in all_recommendations if candidate_key(item) == key],
        key=lambda item: str(item.get("created_at_utc", "")),
    )
    recommendation_ids = {item["recommendation_id"] for item in recommendation_history}
    decision_history = sorted(
        [item for item in all_decisions if item.get("recommendation_id") in recommendation_ids],
        key=lambda item: str(item.get("timestamp", "")),
    )
    superseded_ids = {item.get("supersedes_decision_id") for item in decision_history if item.get("supersedes_decision_id")}
    current_effective = None
    for item in reversed(decision_history):
        if item["decision_id"] not in superseded_ids:
            current_effective = item
            break
    return {
        "candidate_key": key,
        "current_recommendation_id": current_recommendation["recommendation_id"],
        "current_effective_decision": current_effective,
        "recommendation_history": recommendation_history,
        "decision_history": decision_history,
        "historical_decisions": [item for item in decision_history if current_effective is None or item["decision_id"] != current_effective["decision_id"]],
    }
