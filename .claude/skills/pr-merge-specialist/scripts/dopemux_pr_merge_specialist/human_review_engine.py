import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .schema import (
    ArbitrationEvidenceBundle,
    AutonomyGateReport,
    ChallengeReport,
    ConsensusDecision,
    HumanEscalationPacket,
)


class HumanReviewEngine:
    """Synthesizes arbitration results into a concise human-review surface."""

    def compose_packet(
        self,
        bundle: ArbitrationEvidenceBundle,
        consensus: ConsensusDecision,
        gate: AutonomyGateReport,
        challenge: ChallengeReport,
    ) -> HumanEscalationPacket:
        """Create an evidence-backed handoff packet for the operator."""

        # 1. Defer Reasons
        defer_reasons = []
        if gate.decision == "DEFER_TO_HUMAN":
            defer_reasons.append("HIGH_RISK_POLICY_GATE")
        if consensus.confidence == "LOW":
            defer_reasons.append("LOW_CONFIDENCE")
        if challenge and challenge.objections:
            defer_reasons.append("UNRESOLVED_REVIEWER_INTENT")

        # 2. Decision Point Extraction
        decision_points = []
        if challenge:
            for obj in challenge.objections:
                decision_points.append(
                    f"Resolve Objection: {obj.get('desc', 'Unknown')}"
                )
        if not consensus.preferred_candidate:
            decision_points.append("Select valid merge end-state from candidates.")

        return HumanEscalationPacket(
            case_id=consensus.case_id,
            defer_reasons=defer_reasons or ["POLICY_MANDATED_REVIEW"],
            ours_summary=bundle.enforcement_state.get("title", "Ours"),
            theirs_summary="Theirs (PR)",
            overlap_summary=f"{len(bundle.overlap_files)} files overlapping.",
            manual_decision_points=decision_points,
            recommended_process="Review candidate matrix and approve synthesis plan.",
            evidence_refs=consensus.evidence_refs,
        )

    def emit_artifacts(self, packet: HumanEscalationPacket, out_dir: Path):
        """Emit human review surface artifacts."""
        (out_dir / "HUMAN_ESCALATION_PACKET.json").write_text(
            json.dumps(packet.__dict__, indent=2, default=str)
        )

        summary = {
            "status": "ESCALATED",
            "defer_reasons": packet.defer_reasons,
            "required_decisions": len(packet.manual_decision_points),
            "handoff_summary": f"Arbitration deferred: {packet.recommended_process}",
        }
        (out_dir / "OPERATOR_REVIEW_SUMMARY.json").write_text(
            json.dumps(summary, indent=2)
        )
