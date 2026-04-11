from __future__ import annotations

from ..models.ids import synthetic_id
from .proposal_models import ReviewPacket, SynthesisProposal


def build_review_packet(proposal: SynthesisProposal) -> ReviewPacket:
    checks = [
        "Confirm evidence refs point to the expected lane-specific artifacts.",
        "Confirm pricing status is acceptable for the intended profile posture.",
        "Confirm no auto-application path is triggered by this proposal.",
    ]
    if proposal.proposal_class == "candidate_for_low_cost_profile":
        checks.append("Confirm pricing caveats are acceptable before any low-cost profile action.")
    if proposal.proposal_class in {"blocked_lane", "insufficient_evidence"}:
        checks.append("Confirm blocker codes are resolved before reconsidering this candidate.")
    return ReviewPacket(
        review_packet_id=synthetic_id("profile_review_packet", proposal.proposal_id),
        proposal_id=proposal.proposal_id,
        proposal_class=proposal.proposal_class,
        subject_key=proposal.subject_key,
        target_profile=proposal.target_profile,
        pricing_status=proposal.pricing_status,
        blocked_reason_codes=list(proposal.blocked_reason_codes),
        evidence_refs=list(proposal.evidence_refs),
        unresolved_unknowns=list(proposal.unresolved_unknowns),
        review_checks=checks,
        summary="Review-first synthesis packet. Proposal is advisory only and must not auto-apply runtime changes.",
    )
