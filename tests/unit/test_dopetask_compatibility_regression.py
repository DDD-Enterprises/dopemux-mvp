"""Recovered MP023 regression tests."""

import types

import pytest

from dopemux_pr_merge_specialist.dopetask_compatibility_mode import (
    CANONICAL_BODY_FIELDS,
    DopetaskCompatibilityMode,
)


def _canonical_body() -> dict:
    return {
        "status": "PASS",
        "summary": "done",
        "acceptance_checks": [],
        "validation": {"outcome": "PASS", "gates": []},
        "artifacts": [],
        "manifest": {"generator": "dopetask", "version": "1"},
    }


# ---- positive controls (must pass on baseline and on fix) -------------------


def test_flat_canonical_bundle_is_canonical():
    bundle = {"id": "tp-1", **_canonical_body()}
    result = DopetaskCompatibilityMode().check(bundle)
    assert result.is_canonical is True
    assert result.missing_canonical == []
    assert result.normalized is bundle
    assert result.warnings == []


def test_nested_canonical_bundle_is_canonical():
    bundle = {"pr_id": "pr-7", "body": _canonical_body()}
    result = DopetaskCompatibilityMode().check(bundle)
    assert result.is_canonical is True
    assert result.missing_canonical == []
    assert result.normalized is bundle


def test_legacy_flat_bundle_is_normalized_with_warnings():
    bundle = {"id": "tp-legacy", "next_tactic": "ship it", "generator": "old-gen"}
    result = DopetaskCompatibilityMode().check(bundle)
    assert result.is_canonical is False
    assert result.missing_canonical == sorted(CANONICAL_BODY_FIELDS)
    norm = result.normalized
    assert norm["status"] == "UNKNOWN"
    assert norm["acceptance_checks"] == []
    assert norm["validation"] == {"outcome": "UNKNOWN", "gates": []}
    assert norm["summary"] == "ship it"
    assert norm["manifest"] == {"generator": "old-gen", "version": "legacy"}
    assert "artifacts" not in norm
    assert result.warnings[0].startswith("Compatibility mode activated")
    assert any("'artifacts'" in w and "left absent" in w for w in result.warnings)
    # original bundle must not be mutated
    assert "status" not in bundle


def test_missing_id_is_not_canonical_but_does_not_raise():
    result = DopetaskCompatibilityMode().check(_canonical_body())
    assert result.is_canonical is False
    assert result.missing_canonical == []


# ---- negative regressions (fail on baseline, pass on fix) -------------------


def test_non_dict_bundle_list_raises_type_error():
    # baseline: AttributeError ('list' object has no attribute 'get')
    with pytest.raises(TypeError, match="dict"):
        DopetaskCompatibilityMode().check([("id", "tp-1")])


def test_non_dict_bundle_none_raises_type_error():
    # baseline: AttributeError on None.get
    with pytest.raises(TypeError, match="dict"):
        DopetaskCompatibilityMode().check(None)


def test_non_dict_mapping_proxy_does_not_silently_pass_canonicality():
    # baseline: MappingProxyType has .get/.keys so it is reported canonical
    proxy = types.MappingProxyType({"id": "tp-1", **_canonical_body()})
    with pytest.raises(TypeError, match="dict"):
        DopetaskCompatibilityMode().check(proxy)


def test_nested_body_string_raises_type_error():
    # baseline: AttributeError ('str' object has no attribute 'keys')
    with pytest.raises(TypeError, match="body"):
        DopetaskCompatibilityMode().check({"id": "tp-1", "body": "not-a-dict"})


def test_nested_body_list_raises_type_error():
    with pytest.raises(TypeError, match="body"):
        DopetaskCompatibilityMode().check({"tp_id": "tp-2", "body": ["status"]})


def test_nested_body_none_raises_type_error():
    # baseline: body=None is used verbatim -> AttributeError on None.keys()
    with pytest.raises(TypeError, match="body"):
        DopetaskCompatibilityMode().check({"pr_id": "pr-3", "body": None})
