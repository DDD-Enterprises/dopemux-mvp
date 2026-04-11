from __future__ import annotations

from collections import defaultdict
from typing import Any

from ..models.ids import synthetic_id
from .proposal_models import RoutingDiffProposal, SynthesisProposal


def build_routing_diff_proposals(proposals: list[SynthesisProposal]) -> list[RoutingDiffProposal]:
    grouped: dict[str, list[SynthesisProposal]] = defaultdict(list)
    for proposal in proposals:
        grouped[proposal.target_profile].append(proposal)

    diffs: list[RoutingDiffProposal] = []
    for target_profile, rows in sorted(grouped.items()):
        routable = [row for row in rows if row.subject_kind == "route" and row.proposal_class == "candidate_for_balanced_profile"]
        blocked = [row for row in rows if row.proposal_class in {"blocked_lane", "insufficient_evidence"}]
        direct_only = [row for row in rows if row.subject_kind == "model"]
        diff = RoutingDiffProposal(
            proposal_id=synthetic_id("routing_diff", target_profile),
            target_profile=target_profile,
            status="proposed" if routable and not blocked else "blocked",
            route_additions=sorted({row.subject_key for row in routable}),
            blocked_reason_codes=sorted({code for row in blocked for code in row.blocked_reason_codes}),
            evidence_refs=sorted({ref for row in rows for ref in row.evidence_refs}),
            notes=[],
        )
        if direct_only:
            diff.notes.append("Direct-model candidates are upstream admission inputs and are not auto-added to runtime routing.")
        if blocked:
            diff.notes.append("Blocked or insufficient-evidence candidates prevent a clean routing diff for this profile.")
        diffs.append(diff)
    return diffs
