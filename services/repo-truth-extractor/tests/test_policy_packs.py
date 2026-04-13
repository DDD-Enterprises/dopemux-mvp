from __future__ import annotations

import sys
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.policies.loader import load_policy_pack
from benchmarking.scoring.archetype_policies import policy_for_archetype
from benchmarking.synthesis.freshness import FreshnessPolicy
from benchmarking.synthesis.governance_blockers import RecommendationPolicy


def test_policy_packs_are_externalized_and_loaded_deterministically() -> None:
    archetype_pack = load_policy_pack("archetype_scoring_v1.json")
    recommendation_pack = load_policy_pack("recommendation_state_policy_v1.json")
    freshness_pack = load_policy_pack("freshness_policy_v1.json")
    control_pack = load_policy_pack("control_anchor_policy_v1.json")

    assert archetype_pack["policy_id"] == "archetype_scoring_policy_pack_v1"
    assert recommendation_pack["regression_floor"] == -0.05
    assert freshness_pack["max_age_hours"] == 24.0
    assert control_pack["comparison_fields"][-1] == "retry_policy_id"
    assert policy_for_archetype("tool_aware_repo_reasoning").policy_version == "1.0"
    assert RecommendationPolicy().policy_id == "recommendation_policy_v1"
    assert FreshnessPolicy().policy_id == "freshness_policy_v1"
