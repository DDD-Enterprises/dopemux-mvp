from __future__ import annotations

import sys
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.synthesis.freshness import FreshnessOutcome
from benchmarking.synthesis.recommendation_states import determine_recommendation_state


def test_recommendation_state_is_deterministic_and_reviewable_when_unblocked() -> None:
    outcome = determine_recommendation_state(
        attempt={"surface_class": "openrouter_routed"},
        freshness=FreshnessOutcome("fresh", "clear", 0.1, []),
        blockers=[],
    )
    assert outcome.recommendation_state == "recommended_for_review"
    assert outcome.required_action == "manual_promotion_review"


def test_missing_control_anchor_blocks_promotion() -> None:
    outcome = determine_recommendation_state(
        attempt={"surface_class": "openrouter_routed"},
        freshness=FreshnessOutcome("fresh", "clear", 0.1, []),
        blockers=["missing_comparable_control_anchor"],
    )
    assert outcome.recommendation_state == "ineligible"
    assert "missing_comparable_control_anchor" in outcome.failed_gates


def test_contract_failure_quarantines_candidate() -> None:
    outcome = determine_recommendation_state(
        attempt={"surface_class": "openrouter_routed"},
        freshness=FreshnessOutcome("fresh", "clear", 0.1, []),
        blockers=["contract_gate_failure"],
    )
    assert outcome.recommendation_state == "quarantined"
