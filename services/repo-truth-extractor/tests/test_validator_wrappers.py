from __future__ import annotations

import sys
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.executors.phase_s_adapter import PhaseSAdapter
from benchmarking.executors.prescan_adapter import PrescanAdapter
from benchmarking.validators.fl_int_validator_wrapper import FLIntValidatorWrapper
from benchmarking.validators.phase_s_validator_wrapper import PhaseSValidatorWrapper
from benchmarking.validators.prescan_validator_wrapper import PrescanValidatorWrapper
from benchmarking.validators.runtime_validator_wrapper import RuntimeValidatorWrapper


def test_validator_wrappers_return_deterministic_structural_results(tmp_path: Path) -> None:
    prescan_execution = PrescanAdapter().execute(
        {"case_id": "prescan_route_inventory_v1", "validator_suite_id": "validators_prescan_repo_reasoning_v1"},
        tmp_path / "prescan",
    )
    prescan_result = PrescanValidatorWrapper().validate(
        prescan_execution,
        {"validator_suite_id": "validators_prescan_repo_reasoning_v1"},
    )
    assert prescan_result.passed is True
    assert prescan_result.strength_class == "moderate"

    phase_s_execution = PhaseSAdapter().execute(
        {"case_id": "repair_merge_conflict_normalization_v1", "validator_suite_id": "validators_phase_s_advisory_v1"},
        tmp_path / "phase_s",
    )
    phase_s_result = PhaseSValidatorWrapper().validate(
        phase_s_execution,
        {"validator_suite_id": "validators_phase_s_advisory_v1"},
    )
    assert phase_s_result.passed is True
    assert phase_s_result.strength_class == "moderate"


def test_weaker_validator_family_preserves_explicit_strength_metadata(tmp_path: Path) -> None:
    execution = PhaseSAdapter().execute(
        {"case_id": "repair_merge_conflict_normalization_v1", "validator_suite_id": "validators_phase_s_advisory_v1"},
        tmp_path / "phase_s_2",
    )
    result = PhaseSValidatorWrapper().validate(
        execution,
        {"validator_suite_id": "validators_phase_s_advisory_v1"},
    )
    assert result.strength_class == "moderate"

