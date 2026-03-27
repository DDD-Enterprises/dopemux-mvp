from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.dopemux_pr_merge_specialist.dopetask_series_loader import (
    DopetaskSeriesLoader,
    SeriesSchemaError,
)
from src.dopemux_pr_merge_specialist.dopetask_series_models import (
    PacketStatus,
    SeriesStatus,
)


@pytest.fixture
def loader() -> DopetaskSeriesLoader:
    return DopetaskSeriesLoader()


def test_parse_valid_series(loader: DopetaskSeriesLoader) -> None:
    data = {
        "series_id": "SERIES-001",
        "project_id": "dopemux-mvp",
        "status": "VALIDATED",
        "packets": [
            {"tp_id": "TP-1", "status": "VALIDATED"},
            {"tp_id": "TP-2", "status": "PLANNED", "depends_on": ["TP-1"]},
        ],
    }
    result = loader.parse_dict(data)
    assert result.identity.series_id == "SERIES-001"
    assert result.status == SeriesStatus.VALIDATED
    assert len(result.packets) == 2
    assert result.packets[1].depends_on == ["TP-1"]


def test_rejects_missing_fields(loader: DopetaskSeriesLoader) -> None:
    with pytest.raises(SeriesSchemaError, match="Missing required series fields"):
        loader.parse_dict({"series_id": "X"})


def test_rejects_cycle(loader: DopetaskSeriesLoader) -> None:
    data = {
        "series_id": "SERIES-001",
        "project_id": "dopemux-mvp",
        "status": "IN_PROGRESS",
        "packets": [
            {"tp_id": "TP-1", "status": "IN_PROGRESS", "depends_on": ["TP-2"]},
            {"tp_id": "TP-2", "status": "IN_PROGRESS", "depends_on": ["TP-1"]},
        ],
    }
    with pytest.raises(SeriesSchemaError, match="Cycle detected"):
        loader.parse_dict(data)


def test_rejects_missing_dependency(loader: DopetaskSeriesLoader) -> None:
    data = {
        "series_id": "SERIES-001",
        "project_id": "dopemux-mvp",
        "status": "IN_PROGRESS",
        "packets": [
            {"tp_id": "TP-1", "status": "IN_PROGRESS", "depends_on": ["GHOST"]},
        ],
    }
    with pytest.raises(SeriesSchemaError, match="depends on non-existent packet 'GHOST'"):
        loader.parse_dict(data)


def test_maps_unknown_status(loader: DopetaskSeriesLoader) -> None:
    data = {
        "series_id": "SERIES-001",
        "project_id": "dopemux-mvp",
        "status": "WEIRD",
        "packets": [{"tp_id": "TP-1", "status": "MAGIC"}],
    }
    result = loader.parse_dict(data)
    assert result.status == SeriesStatus.UNKNOWN
    assert result.packets[0].status == PacketStatus.UNKNOWN
