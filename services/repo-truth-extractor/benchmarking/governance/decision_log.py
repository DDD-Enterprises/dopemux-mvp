from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..models.entities import GovernanceDecision
from ..models.ids import synthetic_id
from ..storage.hashing import hash_json
from ..storage.sqlite_repo import BenchmarkCatalogRepo


@dataclass(frozen=True)
class GovernanceDecisionLog:
    repo: BenchmarkCatalogRepo

    def append_decision(
        self,
        recommendation: dict[str, Any],
        decision_type: str,
        actor: str,
        reason: str,
        evidence_bundle_ids: list[str],
        governance_packet_ref: str,
        required_action: str,
        supersedes_decision_id: str | None = None,
    ) -> GovernanceDecision:
        existing_count = len(self.repo.list_governance_decisions(str(recommendation["recommendation_id"])))
        decision = GovernanceDecision(
            decision_id=synthetic_id(
                "gov_decision",
                f"{recommendation['recommendation_id']}_{decision_type}_{actor}_{existing_count + 1}",
            ),
            recommendation_id=str(recommendation["recommendation_id"]),
            decision_type=decision_type,
            decision_outcome="recorded",
            actor=actor,
            reason=reason,
            evidence_bundle_ids=evidence_bundle_ids,
            governance_packet_ref=governance_packet_ref,
            required_action=required_action,
            supersedes_decision_id=supersedes_decision_id,
            content_hash=hash_json(
                {
                    "recommendation_id": recommendation["recommendation_id"],
                    "decision_type": decision_type,
                    "actor": actor,
                    "reason": reason,
                    "supersedes_decision_id": supersedes_decision_id,
                }
            ),
            source_ref="m4_governance_decision_log",
        )
        self.repo.insert_governance_decision(decision)
        return decision
