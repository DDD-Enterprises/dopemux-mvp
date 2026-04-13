from __future__ import annotations

import sys
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.scoring.contract_gate import evaluate_contract_gate


def test_contract_gate_passes_and_preserves_strength() -> None:
    outcome = evaluate_contract_gate(
        attempt={"repair_invocations": 0, "sidefill_invocations": 0, "contract_gate_strength": "moderate"},
        validator_results=[{"passed": True}],
        validator_suite={"strength_class": "strong", "contract_rigor": "strict_runtime_v5_with_promptset_v4_split"},
    )
    assert outcome.contract_gate_pass is True
    assert outcome.contract_gate_strength == "strong"
    assert outcome.first_pass_valid is True


def test_contract_gate_fails_closed_with_family_specific_classification() -> None:
    outcome = evaluate_contract_gate(
        attempt={"repair_invocations": 1, "sidefill_invocations": 0, "strict_schema_expected": True},
        validator_results=[{"passed": False, "failure_reason": "missing_phase_s_artifact"}],
        validator_suite={"strength_class": "moderate", "contract_rigor": "phase_s_weaker_contract_caveat"},
    )
    assert outcome.contract_gate_pass is False
    assert outcome.contract_fail_reason == "missing_phase_s_artifact"
    assert outcome.structural_failure_classification == "artifact_missing"
    assert outcome.first_pass_valid is False
