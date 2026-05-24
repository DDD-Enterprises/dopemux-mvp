"""E8: test_model_map_v3_tag_routing_deltas.py — tag enum + routing delta.

Covers packet S12 invariants:
  - 8-tag enum is exact + bounded.
  - schema_critical filters to strict-capable routes.
  - direct_openai_required selects direct OpenAI route.
  - tag_rationale required for tagged steps.
  - Unknown tag rejected by audit.
  - Critical-safety: tag deltas cannot drop the last strict-capable route
    for structural/security_sensitive steps.
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


def _load_module(name, rel_path):
    key = f"_v3_tag_test_{name}"
    if key in sys.modules:
        return sys.modules[key]
    spec = importlib.util.spec_from_file_location(key, _SERVICE_DIR / rel_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[key] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_rte_promptset():
    return _load_module("rte_promptset", "rte_promptset.py")


def _load_structured_output_contracts():
    return _load_module("structured_output_contracts", "lib/structured_output_contracts.py")


@pytest.fixture(scope="module")
def v3_doc():
    return yaml.safe_load(_V3_YAML.read_text(encoding="utf-8"))


def test_tag_enum_has_exactly_eight_members(v3_doc):
    rte_promptset = _load_rte_promptset()
    tag_definitions = v3_doc["tag_definitions"]
    assert set(tag_definitions.keys()) == set(rte_promptset.MODEL_MAP_V3_TAG_ENUM)
    assert len(rte_promptset.MODEL_MAP_V3_TAG_ENUM) == 8


def test_unknown_tag_rejected_by_audit(v3_doc):
    rte_promptset = _load_rte_promptset()
    mutated = copy.deepcopy(v3_doc)
    target = next(s for s in mutated["steps"] if s["step_id"] == "R0")
    target["tags"] = list(target.get("tags", [])) + ["bogus_tag"]
    failures = rte_promptset.audit_model_map_v3(mutated)
    assert any("bogus_tag" in f for f in failures)


def test_tag_rationale_required(v3_doc):
    rte_promptset = _load_rte_promptset()
    mutated = copy.deepcopy(v3_doc)
    target = next(s for s in mutated["steps"] if s["step_id"] == "R0")
    target["tag_rationale"] = ""
    failures = rte_promptset.audit_model_map_v3(mutated)
    assert any("R0" in f and "tag_rationale" in f for f in failures)


def test_filter_supports_json_schema_strict_drops_non_strict():
    soc = _load_structured_output_contracts()
    routes = [
        {"provider": "openai", "model_id": "a", "strict_json_schema": False},
        {"provider": "openrouter", "model_id": "b", "strict_json_schema": True},
    ]
    tag_definitions = {
        "schema_critical": {"routing_delta": {"filter_supports_json_schema_strict": True}}
    }
    out = soc.apply_tag_routing_delta(routes, tags=["schema_critical"], tag_definitions=tag_definitions)
    assert [r["model_id"] for r in out] == ["b"]


def test_filter_provider_drops_non_matching():
    soc = _load_structured_output_contracts()
    routes = [
        {"provider": "openai", "model_id": "a", "strict_json_schema": True},
        {"provider": "openrouter", "model_id": "b", "strict_json_schema": True},
    ]
    tag_definitions = {
        "direct_openai_required": {"routing_delta": {"filter_provider": "openai"}}
    }
    out = soc.apply_tag_routing_delta(routes, tags=["direct_openai_required"], tag_definitions=tag_definitions)
    assert [r["provider"] for r in out] == ["openai"]


def test_route_allowlist_glob_match():
    soc = _load_structured_output_contracts()
    routes = [
        {"provider": "openrouter", "model_id": "anthropic/claude-opus-4.6", "strict_json_schema": True},
        {"provider": "openai", "model_id": "gpt-5.4-mini", "strict_json_schema": True},
        {"provider": "openrouter", "model_id": "anthropic/claude-sonnet-4.6", "strict_json_schema": True},
    ]
    tag_definitions = {
        "security_sensitive": {
            "routing_delta": {
                "route_allowlist": ["anthropic/claude-opus-*"],
            }
        }
    }
    out = soc.apply_tag_routing_delta(routes, tags=["security_sensitive"], tag_definitions=tag_definitions)
    assert [r["model_id"] for r in out] == ["anthropic/claude-opus-4.6"]


def test_route_allowlist_matches_provider_qualified_direct_routes():
    soc = _load_structured_output_contracts()
    routes = [
        {"provider": "openai", "model_id": "gpt-5.5", "strict_json_schema": True},
        {"provider": "openai", "model_id": "gpt-5.4-mini", "strict_json_schema": True},
        {"provider": "openrouter", "model_id": "anthropic/claude-opus-4.6", "strict_json_schema": True},
    ]
    tag_definitions = {
        "security_sensitive": {
            "routing_delta": {
                "route_allowlist": ["openai/gpt-5.5*"],
            }
        }
    }

    out = soc.apply_tag_routing_delta(routes, tags=["security_sensitive"], tag_definitions=tag_definitions)

    assert [(r["provider"], r["model_id"]) for r in out] == [("openai", "gpt-5.5")]


def test_hard_filter_returns_empty_when_no_route_matches():
    soc = _load_structured_output_contracts()
    routes = [
        {"provider": "openrouter", "model_id": "openai/gpt-5.4", "strict_json_schema": False},
    ]
    tag_definitions = {
        "direct_openai_required": {"routing_delta": {"filter_provider": "openai"}}
    }

    out = soc.apply_tag_routing_delta(routes, tags=["direct_openai_required"], tag_definitions=tag_definitions)

    assert out == []


def test_critical_safety_preserves_last_strict_capable_route():
    """For structural impact_class, tag delta must not drop the last strict-capable route."""
    soc = _load_structured_output_contracts()
    # If the only strict-capable route is "a" and a tag would drop it, the
    # delta is refused for critical-safety.
    routes = [
        {"provider": "openai", "model_id": "a", "strict_json_schema": True},
        {"provider": "openrouter", "model_id": "b", "strict_json_schema": False},
    ]
    tag_definitions = {
        # Tag would filter to non-openai (would drop the only strict route).
        "bogus_filter": {"routing_delta": {"filter_provider": "openrouter"}}
    }
    out = soc.apply_tag_routing_delta(
        routes,
        tags=["bogus_filter"],
        tag_definitions=tag_definitions,
        impact_class="structural",
    )
    # Critical-safety: kept the original strict-capable list, not the filtered version.
    assert any(r.get("strict_json_schema") for r in out)


def test_no_tags_returns_routes_unchanged():
    soc = _load_structured_output_contracts()
    routes = [{"provider": "openai", "model_id": "a", "strict_json_schema": True}]
    out = soc.apply_tag_routing_delta(routes, tags=[], tag_definitions={})
    assert out == routes


def test_route_entries_for_stage_no_op_when_lane_has_no_tags(v3_doc):
    """Backwards-compat: lanes without tags hit the v2 code path."""
    soc = _load_structured_output_contracts()
    # Fake step_contract with v2-shape lane (no tags field).
    step_contract = {
        "lane": {
            "lane_class": "CE",
            "primary_routes": [
                {
                    "provider": "openai",
                    "model_id": "gpt-5.4",
                    "api_key_env": "OPENAI_API_KEY",
                    "strict_json_schema": True,
                }
            ],
            "repair_routes": [],
            "sidefill_routes": [],
        }
    }
    out = soc.route_entries_for_stage(step_contract, "primary")
    assert len(out) == 1
    assert out[0]["model_id"] == "gpt-5.4"


def test_route_entries_for_stage_applies_tag_delta_when_tags_present():
    soc = _load_structured_output_contracts()
    step_contract = {
        "lane": {
            "lane_class": "CE",
            "impact_class": "routine",
            "tags": ["direct_openai_required"],
            "tag_definitions": {
                "direct_openai_required": {"routing_delta": {"filter_provider": "openai"}}
            },
            "primary_routes": [
                {"provider": "openrouter", "model_id": "openai/gpt-5.4",
                 "api_key_env": "OPENROUTER_API_KEY", "strict_json_schema": True},
                {"provider": "openai", "model_id": "gpt-5.4",
                 "api_key_env": "OPENAI_API_KEY", "strict_json_schema": True},
            ],
            "repair_routes": [],
            "sidefill_routes": [],
        }
    }
    out = soc.route_entries_for_stage(step_contract, "primary")
    assert all(r["provider"] == "openai" for r in out)
    assert len(out) == 1


def test_committed_v3_tag_definitions_have_routing_delta(v3_doc):
    """Every tag in the enum must have a routing_delta (even if no-op)."""
    rte_promptset = _load_rte_promptset()
    for tag in rte_promptset.MODEL_MAP_V3_TAG_ENUM:
        entry = v3_doc["tag_definitions"][tag]
        assert "routing_delta" in entry, f"tag {tag} missing routing_delta"
        assert isinstance(entry["routing_delta"], dict)
