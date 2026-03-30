from __future__ import annotations

import pytest

from src.dopemux_pr_merge_specialist.dopetask_series_models import (
    DopetaskSeriesIdentity,
    DopetaskSeriesResult,
    SeriesStatus,
)
from src.dopemux_pr_merge_specialist.dopetask_status_mapper import DopetaskStatusMapper


@pytest.fixture
def mapper() -> DopetaskStatusMapper:
    return DopetaskStatusMapper()


def test_map_series_status(mapper: DopetaskStatusMapper) -> None:
    assert mapper.map_series_status("VALIDATED") == SeriesStatus.VALIDATED
    assert mapper.map_series_status("FINALIZED") == SeriesStatus.FINALIZED
    assert mapper.map_series_status("UNKNOWN_RAW") == SeriesStatus.UNKNOWN


def test_aggregate_series_governance_supervised(mapper: DopetaskStatusMapper) -> None:
    series_id = "S-1"
    identity = DopetaskSeriesIdentity(series_id=series_id, project_id="P-1")
    result = DopetaskSeriesResult(
        identity=identity, status=SeriesStatus.VALIDATED, raw_status="VALIDATED", packets=[]
    )
    
    # GO_SUPERVISED_ONLY should allow APPLY_FIX but not HIGH_RISK_AUTO_APPLY
    actions = mapper.aggregate_series_governance(result, "GO_SUPERVISED_ONLY")
    assert "APPLY_FIX" in actions
    assert "MISSION_SUMMARY" in actions
    assert "HIGH_RISK_AUTO_APPLY" not in actions


def test_aggregate_series_governance_advisory(mapper: DopetaskStatusMapper) -> None:
    series_id = "S-1"
    identity = DopetaskSeriesIdentity(series_id=series_id, project_id="P-1")
    result = DopetaskSeriesResult(
        identity=identity, status=SeriesStatus.VALIDATED, raw_status="VALIDATED", packets=[]
    )
    
    # ADVISORY_ONLY should only allow MISSION_SUMMARY
    actions = mapper.aggregate_series_governance(result, "ADVISORY_ONLY")
    assert "MISSION_SUMMARY" in actions
    assert "APPLY_FIX" not in actions
