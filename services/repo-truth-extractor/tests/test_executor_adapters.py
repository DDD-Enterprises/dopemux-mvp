from __future__ import annotations

import sys
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.executors.extraction_v5_adapter import ExtractionV5Adapter
from benchmarking.executors.fl_int_adapter import FLIntAdapter
from benchmarking.executors.phase_s_adapter import PhaseSAdapter
from benchmarking.executors.prescan_adapter import PrescanAdapter


def _case(case_id: str, validator_suite_id: str = "validators_runtime_strict_json_v1") -> dict[str, object]:
    return {"case_id": case_id, "validator_suite_id": validator_suite_id}


def test_executor_adapters_instantiate_and_expose_boundary_shape(tmp_path: Path) -> None:
    adapters = [
        PrescanAdapter(),
        ExtractionV5Adapter(),
        PhaseSAdapter(),
        FLIntAdapter(),
    ]
    for adapter in adapters:
        assert adapter.adapter_name
    assert PrescanAdapter().execute(_case("prescan_route_inventory_v1"), tmp_path / "prescan").output_artifact_ref
    assert PhaseSAdapter().execute(_case("repair_merge_conflict_normalization_v1"), tmp_path / "phase_s").route_trace


def test_executor_adapters_reject_incompatible_case_definitions(tmp_path: Path) -> None:
    adapter = ExtractionV5Adapter()
    try:
        adapter.execute({}, tmp_path)
    except ValueError as exc:
        assert "benchmark case" in str(exc)
    else:
        raise AssertionError("expected invalid case definition to fail")

