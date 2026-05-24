"""E8: test_model_map_v3_loader.py — verify v3 schema parse + version helpers.

Covers packet S10 invariants:
  - version=3.0 is recognized.
  - lane_defaults parses into the expected 4 profiles × 10 cells shape.
  - Per-step override wins over lane_defaults at the materialized level.
  - tag_definitions has exactly the 8-tag enum.
  - validate_model_map_version raises on bad/missing/unsupported versions.
  - lane_defaults_cell returns expected ladders for representative cells.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
import yaml

_SERVICE_DIR = Path(__file__).resolve().parents[1]
_V3_YAML = _SERVICE_DIR / "promptsets" / "v4" / "model_map.yaml"
_V2_BACKUP = _SERVICE_DIR / "promptsets" / "v4" / "model_map.v2.yaml.bak"


def _load_rte_promptset():
    if "rte_promptset_v3_load_test" in sys.modules:
        return sys.modules["rte_promptset_v3_load_test"]
    spec = importlib.util.spec_from_file_location(
        "rte_promptset_v3_load_test",
        _SERVICE_DIR / "rte_promptset.py",
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["rte_promptset_v3_load_test"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def v3_doc():
    return yaml.safe_load(_V3_YAML.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def v2_backup_doc():
    return yaml.safe_load(_V2_BACKUP.read_text(encoding="utf-8"))


def test_v3_version_recognized(v3_doc):
    assert v3_doc.get("version") == "3.0"


def test_v3_lane_defaults_has_four_profiles(v3_doc):
    lane_defaults = v3_doc.get("lane_defaults")
    assert isinstance(lane_defaults, dict)
    assert set(lane_defaults.keys()) == {"economy", "value-default", "quality", "experimental"}


def test_v3_tag_definitions_has_exactly_eight_tags(v3_doc):
    tag_definitions = v3_doc.get("tag_definitions")
    assert isinstance(tag_definitions, dict)
    expected_tags = {
        "low_temp",
        "long_context",
        "schema_critical",
        "tooling_heavy",
        "control_plane",
        "security_sensitive",
        "eval_canary",
        "direct_openai_required",
    }
    assert set(tag_definitions.keys()) == expected_tags


def test_v3_step_count_preserved_from_v2(v3_doc, v2_backup_doc):
    v2_ids = {s["step_id"] for s in v2_backup_doc["steps"]}
    v3_ids = {s["step_id"] for s in v3_doc["steps"]}
    assert v2_ids == v3_ids
    assert len(v3_doc["steps"]) == 136


def test_v3_lane_defaults_value_default_cells_populated(v3_doc):
    """All 10 populated cells exist in value-default profile."""
    rte_promptset = _load_rte_promptset()
    profile = "value-default"
    expected_cells = [
        ("CE", "low"), ("CE", "medium"), ("CE", "high"),
        ("EXTRACT", "low"), ("EXTRACT", "medium"), ("EXTRACT", "high"),
        ("SYNTH", "high"), ("SYNTH", "critical"),
        ("AGG", "low"), ("AGG", "medium"),
    ]
    for lane, tier in expected_cells:
        cell = rte_promptset.lane_defaults_cell(
            v3_doc, cost_profile=profile, lane_class=lane, capability_tier=tier,
        )
        assert cell is not None, f"lane_defaults[{profile}][{lane}][{tier}] missing"
        assert cell["primary_routes"], f"({lane},{tier}) primary_routes empty"


def test_v3_per_step_override_has_hand_curated_routes(v3_doc):
    """The 6 overrides retain hand-curated per-step routes — they do NOT
    require their derived (lane_class, capability_tier) cell to exist in
    lane_defaults (T0 lands at CE/critical which is not populated; the
    override block is the whole reason this cell can stay unpopulated)."""
    by_id = {s["step_id"]: s for s in v3_doc["steps"]}
    overrides = {"Z0", "C10", "S12", "T0", "T1", "T3"}
    for step_id in overrides:
        s = by_id[step_id]
        assert "primary_routes" in s
        assert s["primary_routes"], f"{step_id} override has empty primary_routes"


def test_v3_non_override_step_routes_equal_cell_defaults(v3_doc):
    """Non-override step routes ARE the materialized cell defaults."""
    rte_promptset = _load_rte_promptset()
    overrides = {"Z0", "C10", "S12", "T0", "T1", "T3"}
    # Sample one step from each populated cell that isn't an override.
    samples = ["A0", "A2", "R2", "S5", "M0", "Z9"]
    for step_id in samples:
        s = next(row for row in v3_doc["steps"] if row["step_id"] == step_id)
        assert step_id not in overrides
        cell = rte_promptset.lane_defaults_cell(
            v3_doc,
            cost_profile="value-default",
            lane_class=s["lane_class"],
            capability_tier=s["capability_tier"],
        )
        assert cell is not None
        # Materialized step routes equal cell defaults (deep-equal on model_id
        # tuple — full dict compare is exercised by the migration idempotency
        # test).
        step_ids = [(r["provider"], r["model_id"]) for r in s["primary_routes"]]
        cell_ids = [(r["provider"], r["model_id"]) for r in cell["primary_routes"]]
        assert step_ids == cell_ids, f"{step_id} routes differ from cell defaults"


def test_validate_model_map_version_recognizes_v2(v2_backup_doc):
    rte_promptset = _load_rte_promptset()
    assert rte_promptset.validate_model_map_version(v2_backup_doc) == "2.0"


def test_validate_model_map_version_recognizes_v3(v3_doc):
    rte_promptset = _load_rte_promptset()
    assert rte_promptset.validate_model_map_version(v3_doc) == "3.0"


def test_validate_model_map_version_raises_on_missing_version():
    rte_promptset = _load_rte_promptset()
    with pytest.raises(ValueError, match="missing a top-level `version`"):
        rte_promptset.validate_model_map_version({"steps": []})


def test_validate_model_map_version_raises_on_unsupported_version():
    rte_promptset = _load_rte_promptset()
    with pytest.raises(ValueError, match="Unsupported model_map.yaml version"):
        rte_promptset.validate_model_map_version({"version": "1.0", "steps": []})


def test_validate_model_map_version_raises_on_non_mapping():
    rte_promptset = _load_rte_promptset()
    with pytest.raises(ValueError, match="must decode to a mapping"):
        rte_promptset.validate_model_map_version([1, 2, 3])


def test_v3_synth_high_cell_uses_phase_c_consensus_models(v3_doc):
    """Phase C cell map: (SYNTH, high) primary is anthropic/claude-sonnet-4.6."""
    rte_promptset = _load_rte_promptset()
    cell = rte_promptset.lane_defaults_cell(
        v3_doc, cost_profile="value-default", lane_class="SYNTH", capability_tier="high"
    )
    assert cell is not None
    primary = cell["primary_routes"]
    assert primary[0]["provider"] == "openrouter"
    assert primary[0]["model_id"] == "anthropic/claude-sonnet-4.6"


def test_v3_synth_critical_cell_uses_phase_d_consensus_opus_46(v3_doc):
    """Phase D Change 2: SYNTH critical primary is claude-opus-4.6 (not 4.7)."""
    rte_promptset = _load_rte_promptset()
    cell = rte_promptset.lane_defaults_cell(
        v3_doc, cost_profile="value-default", lane_class="SYNTH", capability_tier="critical"
    )
    assert cell is not None
    primary = cell["primary_routes"]
    assert primary[0]["model_id"] == "anthropic/claude-opus-4.6"
