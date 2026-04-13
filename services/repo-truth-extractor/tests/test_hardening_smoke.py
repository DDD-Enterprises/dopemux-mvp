from __future__ import annotations

import sys
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.cli.benchmark_hardening_smoke import run_hardening_smoke


def test_hardening_smoke_exercises_all_six_archetypes_and_real_state_paths(tmp_path: Path) -> None:
    payload = run_hardening_smoke(root=tmp_path / "benchmarks", proof_dir=tmp_path / "proof")

    assert payload["db_row_counts"]["benchmark_case_attempt"] == 12
    assert payload["sample_candidate_detail"]["case_id"] == "tool_aware_repo_reasoning_v1"
    assert payload["sample_candidate_detail"]["current_recommendation_state"] == "ineligible"
    assert "missing_comparable_control_anchor" in payload["sample_candidate_detail"]["failed_gates"]
    assert "governance_posture_unresolved" in payload["sample_candidate_detail"]["failed_gates"]

    assert payload["sample_phase_s_candidate"]["case_id"] == "adjudication_conflict_ruling_v1"
    assert payload["sample_phase_s_candidate"]["current_recommendation_state"] == "eligible_for_review"
    assert payload["sample_phase_s_candidate"]["phase_caveat"] == "phase_s_policy_sensitive"

    assert payload["sample_stale_candidate"]["case_id"] == "repair_merge_conflict_normalization_v1"
    assert payload["sample_stale_candidate"]["current_recommendation_state"] == "stale_disputed"

    assert payload["sample_regression_candidate"]["case_id"] == "strict_extract_conflicting_evidence_v1"
    assert payload["sample_regression_candidate"]["current_recommendation_state"] == "ineligible"
    assert "regression_delta_below_policy_floor" in payload["sample_regression_candidate"]["failed_gates"]
