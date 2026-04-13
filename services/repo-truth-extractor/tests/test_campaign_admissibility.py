from __future__ import annotations

import sys
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.campaigns.admissibility import (
    CANDIDATE_CONTROL_COLLAPSE,
    IDENTICAL_CONTROL_SIGNATURE,
    INSUFFICIENT_PREFLIGHT_EVIDENCE,
    UNSTABLE_EFFECTIVE_SIGNATURE,
    evaluate_admissibility,
)
from benchmarking.campaigns.route_identity import RouteIdentityRecord


def _identity(route_id: str, cohort: str, signature_hash: str, case_attempt_id: str = "attempt") -> RouteIdentityRecord:
    return RouteIdentityRecord(
        benchmark_run_id="run",
        case_attempt_id=case_attempt_id,
        case_id="strict_extract_conflicting_evidence_v1",
        phase_or_step_family="A",
        surface_class="openrouter_routed",
        runtime_version="v5",
        contract_version="v4",
        contract_snapshot_id="snapshot",
        evidence_bundle_id=f"bundle_{case_attempt_id}",
        declared_route_id=route_id,
        selected_route_identity={"declared_route_id": route_id},
        effective_route_signature={"A:A0": [signature_hash]},
        effective_route_signature_hash=signature_hash,
        route_signature_source_refs=["outputs/STEP_METRICS.json"],
        admissibility_status="derived",
        admissibility_blocker_codes=[],
        admissibility_notes=[],
    )


def test_identical_controls_are_blocked() -> None:
    payload = evaluate_admissibility(
        benchmark_run_ids=["run"],
        route_identities=[
            _identity("control_a", "control", "same_hash", "attempt_a"),
            _identity("control_b", "control", "same_hash", "attempt_b"),
        ],
        intended_routes=[
            {"route_id": "control_a", "cohort": "control", "case_id": "strict_extract_conflicting_evidence_v1"},
            {"route_id": "control_b", "cohort": "control", "case_id": "strict_extract_conflicting_evidence_v1"},
        ],
    )
    assert payload["status"] == "blocked"
    assert IDENTICAL_CONTROL_SIGNATURE in payload["admissibility_blocker_codes"]


def test_candidate_control_collapse_is_blocked() -> None:
    payload = evaluate_admissibility(
        benchmark_run_ids=["run"],
        route_identities=[
            _identity("control_a", "control", "control_hash", "attempt_a"),
            _identity("candidate_a", "premium", "control_hash", "attempt_b"),
        ],
        intended_routes=[
            {"route_id": "control_a", "cohort": "control", "case_id": "strict_extract_conflicting_evidence_v1"},
            {"route_id": "candidate_a", "cohort": "premium", "case_id": "strict_extract_conflicting_evidence_v1"},
        ],
    )
    assert payload["status"] == "blocked"
    assert CANDIDATE_CONTROL_COLLAPSE in payload["admissibility_blocker_codes"]


def test_unstable_signature_is_blocked() -> None:
    payload = evaluate_admissibility(
        benchmark_run_ids=["run1", "run2"],
        route_identities=[
            _identity("candidate_a", "premium", "hash_one", "attempt_a"),
            _identity("candidate_a", "premium", "hash_two", "attempt_b"),
        ],
        intended_routes=[
            {"route_id": "candidate_a", "cohort": "premium", "case_id": "strict_extract_conflicting_evidence_v1"},
        ],
        required_repeat_count=2,
    )
    assert payload["status"] == "blocked"
    assert UNSTABLE_EFFECTIVE_SIGNATURE in payload["admissibility_blocker_codes"]


def test_insufficient_preflight_evidence_is_blocked() -> None:
    payload = evaluate_admissibility(
        benchmark_run_ids=["run"],
        route_identities=[],
        intended_routes=[
            {"route_id": "control_a", "cohort": "control", "case_id": "strict_extract_conflicting_evidence_v1"},
        ],
        required_repeat_count=1,
    )
    assert payload["status"] == "blocked"
    assert INSUFFICIENT_PREFLIGHT_EVIDENCE in payload["admissibility_blocker_codes"]


def test_distinct_controls_can_pass() -> None:
    payload = evaluate_admissibility(
        benchmark_run_ids=["run"],
        route_identities=[
            _identity("control_a", "control", "hash_a", "attempt_a"),
            _identity("control_b", "control", "hash_b", "attempt_b"),
        ],
        intended_routes=[
            {"route_id": "control_a", "cohort": "control", "case_id": "strict_extract_conflicting_evidence_v1"},
            {"route_id": "control_b", "cohort": "control", "case_id": "strict_extract_conflicting_evidence_v1"},
        ],
    )
    assert payload["status"] == "admissible"
