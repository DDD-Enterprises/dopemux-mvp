from __future__ import annotations

import sys
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.scoring.control_deltas import comparable_attempts, compute_control_deltas


def test_only_comparable_attempts_generate_computed_deltas() -> None:
    baseline = {
        "case_attempt_id": "anchor_a",
        "case_id": "case_a",
        "surface_class": "local_or_open_weight",
        "runtime_version": "v5",
        "contract_snapshot_id": "snap_a",
        "validator_suite_id": "suite_a",
        "retry_policy_id": "retry_a",
        "contract_gate_pass": True,
        "task_success_score": 0.8,
        "operational_metrics": {"latency_ms": 10.0, "cost_estimate_usd": 0.0, "stability_score": 1.0},
    }
    candidate = dict(baseline, case_attempt_id="candidate_a", task_success_score=0.9)
    assert comparable_attempts(candidate, baseline) is True
    outcome = compute_control_deltas(candidate, baseline)
    assert outcome.comparable is True
    assert all(row.delta_state == "computed" for row in outcome.rows)


def test_mismatched_attempts_are_marked_not_comparable() -> None:
    baseline = {
        "case_attempt_id": "anchor_a",
        "case_id": "case_a",
        "surface_class": "local_or_open_weight",
        "runtime_version": "v5",
        "contract_snapshot_id": "snap_a",
        "validator_suite_id": "suite_a",
        "retry_policy_id": "retry_a",
        "contract_gate_pass": True,
        "task_success_score": 0.8,
        "operational_metrics": {"latency_ms": 10.0, "cost_estimate_usd": 0.0, "stability_score": 1.0},
    }
    candidate = dict(baseline, case_attempt_id="candidate_a", surface_class="openrouter_routed")
    outcome = compute_control_deltas(candidate, baseline)
    assert outcome.comparable is False
    assert all(row.delta_state.startswith("not_comparable") for row in outcome.rows)
