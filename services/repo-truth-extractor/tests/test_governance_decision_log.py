from __future__ import annotations

import sys
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.governance.decision_log import GovernanceDecisionLog
from benchmarking.models.entities import PromotionRecommendation
from benchmarking.registry.registry_loader import seed_registry
from benchmarking.storage.hashing import hash_json
from benchmarking.storage.sqlite_repo import BenchmarkCatalogRepo


def test_governance_decision_log_is_append_only_and_supports_supersession(tmp_path: Path) -> None:
    repo = BenchmarkCatalogRepo.from_root(tmp_path)
    seed_registry(repo)
    recommendation = PromotionRecommendation(
        recommendation_id="recommendation_demo_v1",
        benchmark_run_id="run_demo_v1",
        route_id="route_openrouter_openai_gpt_5_4_v1",
        surface_id="surface_openrouter_api_v1",
        archetype_id="strict_evidence_extraction",
        profile_id="balanced_production",
        runtime_version="v5",
        contract_version="promptsets/v4",
        contract_snapshot_id=repo.list_benchmark_cases()[0]["contract_snapshot_id"],
        freshness_state="fresh",
        dispute_state="clear",
        recommendation_state="recommended_for_review",
        failed_gates=[],
        evidence_bundle_ids=["bundle_demo_v1"],
        relevant_rollup_ids=["CASESET_ROLLUP__demo"],
        control_delta_summary={"task_success": 0.1},
        required_action="manual_promotion_review",
        requires_review=True,
        content_hash=hash_json({"recommendation_id": "recommendation_demo_v1"}),
        source_ref="test",
    )
    repo.insert_promotion_recommendation(recommendation)
    log = GovernanceDecisionLog(repo)
    first = log.append_decision(
        recommendation=repo.fetch_promotion_recommendation("recommendation_demo_v1"),
        decision_type="defer",
        actor="tester",
        reason="Need more evidence.",
        evidence_bundle_ids=["bundle_demo_v1"],
        governance_packet_ref="GOVERNANCE_PACKET__recommendation_demo_v1.json",
        required_action="manual_promotion_review",
    )
    second = log.append_decision(
        recommendation=repo.fetch_promotion_recommendation("recommendation_demo_v1"),
        decision_type="clear_dispute",
        actor="tester",
        reason="Dispute cleared.",
        evidence_bundle_ids=["bundle_demo_v1"],
        governance_packet_ref="GOVERNANCE_PACKET__recommendation_demo_v1.json",
        required_action="manual_promotion_review",
        supersedes_decision_id=first.decision_id,
    )
    decisions = repo.list_governance_decisions("recommendation_demo_v1")
    assert len(decisions) == 2
    assert decisions[-1]["supersedes_decision_id"] == first.decision_id
    assert decisions[0]["decision_id"] != decisions[1]["decision_id"]
    assert second.decision_outcome.value == "recorded"
