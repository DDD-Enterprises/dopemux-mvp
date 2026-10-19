from __future__ import annotations


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


# --- Appended hardening regressions (reuse existing `loader` fixture and imports) ---


def _valid_series_with_packets(packets):
    return {
        "series_id": "SERIES-001",
        "project_id": "dopemux-mvp",
        "status": "IN_PROGRESS",
        "packets": packets,
    }


@pytest.mark.parametrize("bad_top", [[], None, "series", 42, [{"series_id": "X"}]])
def test_rejects_non_object_top_level(loader: DopetaskSeriesLoader, bad_top) -> None:
    # Baseline: AttributeError ('list'/'NoneType' has no attribute 'keys').
    with pytest.raises(SeriesSchemaError, match="must be a JSON object"):
        loader.parse_dict(bad_top)


def test_load_file_rejects_top_level_list(loader: DopetaskSeriesLoader, tmp_path) -> None:
    state_file = tmp_path / "series_state.json"
    state_file.write_text("[]", encoding="utf-8")
    with pytest.raises(SeriesSchemaError, match="must be a JSON object"):
        loader.load_file(state_file)


def test_load_file_rejects_top_level_null(loader: DopetaskSeriesLoader, tmp_path) -> None:
    state_file = tmp_path / "series_state.json"
    state_file.write_text("null", encoding="utf-8")
    with pytest.raises(SeriesSchemaError, match="must be a JSON object"):
        loader.load_file(state_file)


@pytest.mark.parametrize(
    "bad_packets",
    [None, "TP-1", 7, {"tp_id": "TP-1", "status": "PLANNED"}],
)
def test_rejects_non_list_packets(loader: DopetaskSeriesLoader, bad_packets) -> None:
    # Baseline: TypeError (None not iterable) or AttributeError (str/dict keys iterated).
    with pytest.raises(SeriesSchemaError, match="'packets' must be a list"):
        loader.parse_dict(_valid_series_with_packets(bad_packets))


@pytest.mark.parametrize("bad_packet", ["TP-1", None, 3, ["TP-1", "PLANNED"]])
def test_rejects_non_dict_packet_entry(loader: DopetaskSeriesLoader, bad_packet) -> None:
    # Baseline: AttributeError (.keys() on non-dict).
    with pytest.raises(SeriesSchemaError, match="Packet at index 1 must be an object"):
        loader.parse_dict(
            _valid_series_with_packets([{"tp_id": "TP-0", "status": "VALIDATED"}, bad_packet])
        )


@pytest.mark.parametrize(
    "bad_deps",
    ["TP-1", 42, {"TP-1": True}, [1], [None], [""], ["TP-1", 2]],
)
def test_rejects_malformed_depends_on(loader: DopetaskSeriesLoader, bad_deps) -> None:
    # Baseline: TypeError for int, character-iteration for str, dict-key admission,
    # or a misleading "non-existent packet" error for non-string entries.
    data = _valid_series_with_packets(
        [
            {"tp_id": "TP-1", "status": "VALIDATED"},
            {"tp_id": "TP-2", "status": "PLANNED", "depends_on": bad_deps},
        ]
    )
    with pytest.raises(SeriesSchemaError, match="depends_on"):
        loader.parse_dict(data)


@pytest.mark.parametrize("bad_id", [None, "", "   ", 7, ["TP-1"]])
def test_rejects_invalid_packet_identifier(loader: DopetaskSeriesLoader, bad_id) -> None:
    # Baseline: silently admits None/""/int ids, TypeError for unhashable list.
    with pytest.raises(SeriesSchemaError, match="invalid tp_id"):
        loader.parse_dict(_valid_series_with_packets([{"tp_id": bad_id, "status": "PLANNED"}]))


def test_rejects_non_string_packet_status(loader: DopetaskSeriesLoader) -> None:
    # Baseline: PacketStatus(None) -> ValueError -> UNKNOWN, silently admitted.
    with pytest.raises(SeriesSchemaError, match="status must be a string"):
        loader.parse_dict(_valid_series_with_packets([{"tp_id": "TP-1", "status": None}]))


@pytest.mark.parametrize("field_name", ["series_id", "project_id"])
@pytest.mark.parametrize("bad_value", [None, "", 12])
def test_rejects_invalid_series_identity_fields(
    loader: DopetaskSeriesLoader, field_name, bad_value
) -> None:
    data = _valid_series_with_packets([{"tp_id": "TP-1", "status": "PLANNED"}])
    data[field_name] = bad_value
    with pytest.raises(SeriesSchemaError, match=field_name):
        loader.parse_dict(data)


def test_well_formed_series_preserved_after_hardening(loader: DopetaskSeriesLoader) -> None:
    data = {
        "series_id": "SERIES-009",
        "project_id": "dopemux-mvp",
        "status": "WEIRD",
        "packets": [
            {"tp_id": "TP-1", "status": "MAGIC"},
            {"tp_id": "TP-2", "status": "PLANNED", "depends_on": ["TP-1"], "is_final": True},
        ],
    }
    result = loader.parse_dict(data)
    assert result.identity.series_id == "SERIES-009"
    assert result.identity.project_id == "dopemux-mvp"
    assert result.identity.version == "0.5.1"
    assert result.status == SeriesStatus.UNKNOWN
    assert result.raw_status == "WEIRD"
    assert [p.tp_id for p in result.packets] == ["TP-1", "TP-2"]
    assert result.packets[0].status == PacketStatus.UNKNOWN
    assert result.packets[0].depends_on == []
    assert result.packets[0].is_final is False
    assert result.packets[1].status == PacketStatus.PLANNED
    assert result.packets[1].depends_on == ["TP-1"]
    assert result.packets[1].is_final is True


def test_dag_validation_still_rejects_self_dependency(loader: DopetaskSeriesLoader) -> None:
    data = _valid_series_with_packets(
        [{"tp_id": "TP-1", "status": "IN_PROGRESS", "depends_on": ["TP-1"]}]
    )
    with pytest.raises(SeriesSchemaError, match="Cycle detected"):
        loader.parse_dict(data)


def test_duplicate_packet_id_still_rejected(loader: DopetaskSeriesLoader) -> None:
    data = _valid_series_with_packets(
        [{"tp_id": "TP-1", "status": "PLANNED"}, {"tp_id": "TP-1", "status": "PLANNED"}]
    )
    with pytest.raises(SeriesSchemaError, match="Duplicate packet ID"):
        loader.parse_dict(data)
