"""E8: test_model_map_v3_per_step_overrides.py — 6 override steps.

Covers packet S13 invariants:
  - Each of {Z0, C10, S12, T0, T1, T3} has a per-step *_routes block.
  - Override routes are valid (provider + model_id + api_key_env populated).
  - Override routes match the hand-curated migration script source (not
    just any value).
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
import yaml

_SERVICE_DIR = Path(__file__).resolve().parents[1]
_V3_YAML = _SERVICE_DIR / "promptsets" / "v4" / "model_map.yaml"
_MIGRATE_SCRIPT = _SERVICE_DIR / "promptsets" / "v4" / "scripts" / "migrate_model_map_v2_to_v3.py"


def _load_migrate():
    if "_v3_overrides_test_migrate" in sys.modules:
        return sys.modules["_v3_overrides_test_migrate"]
    spec = importlib.util.spec_from_file_location("_v3_overrides_test_migrate", _MIGRATE_SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_v3_overrides_test_migrate"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def v3_doc():
    return yaml.safe_load(_V3_YAML.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def by_id(v3_doc):
    return {s["step_id"]: s for s in v3_doc["steps"]}


OVERRIDE_STEPS = ("Z0", "C10", "S12", "T0", "T1", "T3")


@pytest.mark.parametrize("step_id", OVERRIDE_STEPS)
def test_override_has_primary_routes(by_id, step_id):
    s = by_id[step_id]
    assert s["primary_routes"], f"{step_id} primary_routes empty"


@pytest.mark.parametrize("step_id", OVERRIDE_STEPS)
def test_override_routes_have_required_fields(by_id, step_id):
    s = by_id[step_id]
    for stage in ("primary_routes", "repair_routes", "sidefill_routes"):
        for r in s.get(stage, []):
            assert r.get("provider"), f"{step_id}.{stage} missing provider"
            assert r.get("model_id"), f"{step_id}.{stage} missing model_id"
            assert r.get("api_key_env"), f"{step_id}.{stage} missing api_key_env"


def test_override_set_matches_migration_script_constant(by_id):
    migrate = _load_migrate()
    yaml_overrides = set(OVERRIDE_STEPS)
    assert migrate.OVERRIDE_STEPS == yaml_overrides


@pytest.mark.parametrize("step_id", OVERRIDE_STEPS)
def test_override_routes_match_migration_script_source(by_id, step_id):
    """The per-step routes in v3 yaml MUST equal the OVERRIDE_ROUTES
    constant in the migration script — proves the migration's "preserve
    verbatim" semantic for the override set."""
    migrate = _load_migrate()
    yaml_step = by_id[step_id]
    script_routes = migrate.OVERRIDE_ROUTES[step_id]
    for stage in ("primary_routes", "repair_routes", "sidefill_routes"):
        yaml_routes = yaml_step.get(stage, [])
        # The script's _canonical_route applies field ordering + bool
        # normalization, matching what's emitted in yaml.
        expected = [migrate._canonical_route(r) for r in script_routes.get(stage, [])]
        assert yaml_routes == expected, f"{step_id}.{stage} drift between yaml and script"


def test_t0_override_has_critical_tier_via_structural_impact_class(by_id):
    """T0 is in override set AND impact_class=structural ⇒ critical."""
    s = by_id["T0"]
    assert s["impact_class"] == "structural"
    assert s["capability_tier"] == "critical"


def test_c10_override_was_reclassified_to_synth(by_id):
    """C10 was BULK_CODE_HEAVY in v2; Phase C reclassified to SYNTH/high."""
    s = by_id["C10"]
    assert s["lane_class"] == "SYNTH"
    assert s["capability_tier"] == "high"


def test_z0_override_is_ce_low_freeze(by_id):
    """Z0 is the deterministic CE/low freeze step (single primary route)."""
    s = by_id["Z0"]
    assert s["lane_class"] == "CE"
    assert s["capability_tier"] == "low"
    assert len(s["primary_routes"]) == 1


def test_s12_override_is_ce_high_strict_signature(by_id):
    """S12 produces strict JSON sigs; CE/high lane."""
    s = by_id["S12"]
    assert s["lane_class"] == "CE"
    assert s["capability_tier"] == "high"
    # All primary routes are strict-capable for the signature contract.
    assert all(r.get("strict_json_schema") for r in s["primary_routes"])


def test_non_override_step_has_no_extra_unexpected_fields(by_id):
    """Spot-check A0 (a non-override) — its routes ARE the cell defaults
    and it carries no override-only fields."""
    s = by_id["A0"]
    assert "Z0" not in {"phase": s.get("phase"), "step_id": s.get("step_id")}.values()
    # A0 lands in (CE, medium) cell defaults; primary[0] is openrouter per
    # Phase D Change A.
    assert s["primary_routes"][0]["provider"] == "openrouter"
