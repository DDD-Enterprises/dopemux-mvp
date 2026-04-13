from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class SynthesisProposal:
    proposal_id: str
    proposal_class: str
    subject_key: str
    subject_kind: str
    target_profile: str
    benchmark_mode: str
    candidate_type: str
    pricing_status: str
    caveated: bool
    auto_apply: bool = False
    blocked_reason_codes: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    evidence_classes: list[str] = field(default_factory=list)
    unresolved_unknowns: list[str] = field(default_factory=list)
    rationale: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RoutingDiffProposal:
    proposal_id: str
    target_profile: str
    status: str
    route_additions: list[str] = field(default_factory=list)
    route_removals: list[str] = field(default_factory=list)
    blocked_reason_codes: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReviewPacket:
    review_packet_id: str
    proposal_id: str
    proposal_class: str
    subject_key: str
    target_profile: str
    pricing_status: str
    blocked_reason_codes: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    unresolved_unknowns: list[str] = field(default_factory=list)
    review_checks: list[str] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
