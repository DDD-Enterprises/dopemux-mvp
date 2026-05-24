"""E8: test_model_map_v3_impact_class_enforcement.py — audit gate enforcement.

Covers packet S11 invariants:
  - structural without critical fails.
  - security_sensitive without critical fails.
  - routine + any tier passes.
  - impact_class missing fails.
  - Reclassified Phase D steps {R0, S0, T0, R11} have correct values.
"""
from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path

import pytest
import yaml

_SERVICE_DIR = Path(__file__).resolve().parents[1]
_V3_YAML = _SERVICE_DIR / "promptsets" / "v4" / "model_map.yaml"


def _load_rte_promptset():
    if "rte_promptset_v3_audit_test" in sys.modules:
        return sys.modules["rte_promptset_v3_audit_test"]
    spec = importlib.util.spec_from_file_location(
        "rte_promptset_v3_audit_test",
        _SERVICE_DIR / "rte_promptset.py",
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["rte_promptset_v3_audit_test"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def v3_doc():
    return yaml.safe_load(_V3_YAML.read_text(encoding="utf-8"))


def _by_id(payload, step_id):
    return next(s for s in payload["steps"] if s["step_id"] == step_id)


def test_committed_v3_yaml_passes_audit(v3_doc):
    """The committed v3 yaml must pass the audit cleanly."""
    rte_promptset = _load_rte_promptset()
    failures = rte_promptset.audit_model_map_v3(v3_doc)
    assert failures == [], f"committed v3 yaml failed audit: {failures}"


def test_structural_without_critical_fails(v3_doc):
    """If a structural step is downgraded to high tier, audit fails."""
    rte_promptset = _load_rte_promptset()
    mutated = copy.deepcopy(v3_doc)
    target = _by_id(mutated, "R0")
    assert target["impact_class"] == "structural"
    target["capability_tier"] = "high"
    failures = rte_promptset.audit_model_map_v3(mutated)
    assert any("R0" in f and "structural" in f and "critical" in f for f in failures)


def test_security_sensitive_without_critical_fails(v3_doc):
    rte_promptset = _load_rte_promptset()
    mutated = copy.deepcopy(v3_doc)
    target = _by_id(mutated, "R11")
    assert target["impact_class"] == "security_sensitive"
    target["capability_tier"] = "high"
    failures = rte_promptset.audit_model_map_v3(mutated)
    assert any("R11" in f and "security_sensitive" in f and "critical" in f for f in failures)


def test_routine_passes_at_any_tier(v3_doc):
    """A routine step can ride any capability_tier."""
    rte_promptset = _load_rte_promptset()
    mutated = copy.deepcopy(v3_doc)
    target = _by_id(mutated, "A0")
    assert target["impact_class"] == "routine"
    target["capability_tier"] = "low"
    failures = rte_promptset.audit_model_map_v3(mutated)
    assert not any("A0" in f for f in failures)


def test_impact_class_missing_fails(v3_doc):
    rte_promptset = _load_rte_promptset()
    mutated = copy.deepcopy(v3_doc)
    target = _by_id(mutated, "A0")
    target.pop("impact_class", None)
    failures = rte_promptset.audit_model_map_v3(mutated)
    assert any("A0" in f and "impact_class" in f for f in failures)


def test_capability_tier_missing_fails(v3_doc):
    rte_promptset = _load_rte_promptset()
    mutated = copy.deepcopy(v3_doc)
    target = _by_id(mutated, "A0")
    target.pop("capability_tier", None)
    failures = rte_promptset.audit_model_map_v3(mutated)
    assert any("A0" in f and "capability_tier" in f for f in failures)


def test_phase_d_reclassification_r0_is_structural_critical(v3_doc):
    s = _by_id(v3_doc, "R0")
    assert s["impact_class"] == "structural"
    assert s["capability_tier"] == "critical"


def test_phase_d_reclassification_s0_is_structural_critical(v3_doc):
    s = _by_id(v3_doc, "S0")
    assert s["impact_class"] == "structural"
    assert s["capability_tier"] == "critical"


def test_phase_d_reclassification_t0_is_structural_critical(v3_doc):
    s = _by_id(v3_doc, "T0")
    assert s["impact_class"] == "structural"
    assert s["capability_tier"] == "critical"


def test_phase_d_reclassification_r11_is_security_sensitive_critical(v3_doc):
    s = _by_id(v3_doc, "R11")
    assert s["impact_class"] == "security_sensitive"
    assert s["capability_tier"] == "critical"


def test_hand_picked_r7_is_important_with_critical_tier(v3_doc):
    """R7 is impact_class=important + capability_tier=critical (Phase C
    hand-pick). The enforcement is one-directional: important does NOT
    require critical, but a hand-picked critical is allowed."""
    s = _by_id(v3_doc, "R7")
    assert s["impact_class"] == "important"
    assert s["capability_tier"] == "critical"


def test_duplicate_step_id_fails_audit(v3_doc):
    rte_promptset = _load_rte_promptset()
    mutated = copy.deepcopy(v3_doc)
    mutated["steps"].append(copy.deepcopy(mutated["steps"][0]))
    failures = rte_promptset.audit_model_map_v3(mutated)
    assert any("duplicate" in f.lower() for f in failures)
