from __future__ import annotations

import sys
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.synthesis.freshness import FreshnessPolicy, evaluate_freshness
from benchmarking.synthesis.governance_blockers import RecommendationPolicy, collect_blockers
from benchmarking.synthesis.recommendation_states import determine_recommendation_state


def test_stale_and_disputed_evidence_downgrades_state() -> None:
    freshness = evaluate_freshness(
        benchmark_run={"finished_at": "2026-04-01T00:00:00Z"},
        attempt={"timestamp_utc": "2026-04-01T00:00:00Z", "unknowns_open": ["needs_manual_check"]},
        policy=FreshnessPolicy(max_age_hours=1.0),
    )
    state = determine_recommendation_state(
        attempt={"surface_class": "openrouter_routed"},
        freshness=freshness,
        blockers=freshness.blockers,
    )
    assert freshness.freshness_state == "stale"
    assert freshness.dispute_state == "disputed"
    assert state.recommendation_state == "stale_disputed"


def test_unresolved_unknowns_and_local_surface_block_production_recommendation() -> None:
    freshness = evaluate_freshness(
        benchmark_run={"finished_at": "2026-04-10T00:00:00Z"},
        attempt={"timestamp_utc": "2026-04-10T00:00:00Z", "unknowns_open": []},
    )
    blockers = collect_blockers(
        attempt={"contract_gate_pass": True, "surface_class": "local_or_open_weight"},
        case={"validator_suite_id": "validators_prescan_repo_reasoning_v1"},
        profile_fit={"operational_risk_flags": ["local_or_open_weight_not_production_eligible"], "attempt_total": 1},
        freshness=freshness,
        control_deltas=[],
        policy=RecommendationPolicy(min_sample_size_for_recommended=1),
    )
    assert "local_open_weight_promotion_forbidden" in blockers
    assert "missing_comparable_control_anchor" in blockers
