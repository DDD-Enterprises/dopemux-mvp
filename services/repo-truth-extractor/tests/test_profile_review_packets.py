from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = ROOT / "services" / "repo-truth-extractor"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.synthesis.proposal_models import SynthesisProposal
from benchmarking.synthesis.review_packets import build_review_packet


def test_review_packet_preserves_evidence_and_blockers() -> None:
    proposal = SynthesisProposal(
        proposal_id="proposal_demo",
        proposal_class="candidate_for_low_cost_profile",
        subject_key="openrouter/x-ai/grok-4.1-fast",
        subject_kind="model",
        target_profile="low_cost_profile",
        benchmark_mode="profile_synthesis_input",
        candidate_type="profile_candidate",
        pricing_status="PRICED_WITH_CAVEAT",
        caveated=True,
        blocked_reason_codes=["pricing_caveated"],
        evidence_refs=["DIRECT_MODEL_COMPARISON.json", "pricing_coverage_report.json"],
        evidence_classes=["direct_model", "pricing"],
        unresolved_unknowns=["pricing_caveated"],
    )

    packet = build_review_packet(proposal)

    assert packet.proposal_id == "proposal_demo"
    assert "pricing_coverage_report.json" in packet.evidence_refs
    assert "pricing_caveated" in packet.blocked_reason_codes
    assert any("low-cost" in check or "low-cost" in check.lower() for check in packet.review_checks)
