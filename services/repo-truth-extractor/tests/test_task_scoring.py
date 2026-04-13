from __future__ import annotations

import sys
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.scoring.contract_gate import ContractGateOutcome
from benchmarking.scoring.task_scoring import score_attempt


def test_task_scores_only_when_contract_gate_passes() -> None:
    blocked = score_attempt(
        case={"archetype_id": "strict_evidence_extraction"},
        attempt={"runtime_version": "v5", "contract_version": "promptsets/v4"},
        contract_gate=ContractGateOutcome(False, "strong", "validator_failed", False, "validator_failed"),
        task_eval={"status": "captured"},
        route_trace={"execution_mode": "dry_run", "surface_class": "openrouter_routed"},
        validator_results=[{"passed": False}],
        executor_links={"script": "run_extraction_v5.py"},
    )
    assert blocked.task_success_score == 0.0
    assert blocked.task_score_breakdown == {"blocked_by_contract_gate": 1.0}


def test_task_scoring_is_archetype_specific_not_global() -> None:
    outcome = score_attempt(
        case={"archetype_id": "prescan_routing_assessment"},
        attempt={"surface_class": "local_or_open_weight", "surface_id": "surface_local_fixture_v1"},
        contract_gate=ContractGateOutcome(True, "moderate", None, True, None),
        task_eval={"status": "captured"},
        route_trace={"execution_mode": "local_dry_run", "surface_class": "local_or_open_weight"},
        validator_results=[{"passed": True}],
        executor_links={"script": "run_prescan.py"},
    )
    assert outcome.scoring_policy_id == "routing_classification_v1"
    assert "surface_explicitness" in outcome.task_score_breakdown
    assert "contract_separation" not in outcome.task_score_breakdown
