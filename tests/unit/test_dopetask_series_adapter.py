from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.dopemux_pr_merge_specialist.dopetask_adapter import DopetaskAdapter
from src.dopemux_pr_merge_specialist.dopetask_bundle_loader import DopetaskBundleLoader
from src.dopemux_pr_merge_specialist.dopetask_series_models import SeriesStatus
from src.dopemux_pr_merge_specialist.dopetask_status_mapper import DopetaskStatusMapper


@pytest.fixture
def adapter(tmp_path: Path) -> DopetaskAdapter:
    loader = DopetaskBundleLoader(tmp_path)
    mapper = DopetaskStatusMapper()
    return DopetaskAdapter(loader, mapper)


def test_adapter_from_series_state_path(adapter: DopetaskAdapter, tmp_path: Path) -> None:
    state_file = tmp_path / "state.json"
    data = {
        "series_id": "SERIES-123",
        "project_id": "dopemux-mvp",
        "status": "VALIDATED",
        "packets": [{"tp_id": "TP-1", "status": "VALIDATED"}],
    }
    state_file.write_text(json.dumps(data), encoding="utf-8")

    result = adapter.from_series_state_path(state_file, posture="GO_SUPERVISED_ONLY")
    assert result.identity.series_id == "SERIES-123"
    assert result.status == SeriesStatus.VALIDATED
    assert "APPLY_FIX" in result.allowed_actions


def test_adapter_from_series_id(adapter: DopetaskAdapter, tmp_path: Path) -> None:
    series_id = "SERIES-456"
    series_dir = tmp_path / ".dopetask" / "series" / series_id
    series_dir.mkdir(parents=True)
    state_file = series_dir / "state.json"
    data = {
        "series_id": series_id,
        "project_id": "dopemux-mvp",
        "status": "IN_PROGRESS",
        "packets": [{"tp_id": "TP-1", "status": "IN_PROGRESS"}],
    }
    state_file.write_text(json.dumps(data), encoding="utf-8")

    result = adapter.from_series_id(series_id, repo_path=tmp_path)
    assert result.identity.series_id == series_id
    assert result.status == SeriesStatus.IN_PROGRESS
