"""E7: derive_ladder_for_cell + infer_route_for_model coverage.

Validates the new cell-aliased ladder derivation API:

- derive_ladder_for_cell returns the expected route for each (profile, lane,
  capability_tier) cell.
- CLI alias overrides propagate to the resolved model_id.
- Env vars propagate (and the snapshot participates in the cache key so a
  later env change correctly invalidates the cached entry).
- Cache invalidation: changing overrides between calls returns the new value.
- Unresolved alias raises ValueError with an operator-actionable message.
- Disabled providers filter routes out of the returned ladder.
- infer_route_for_model has deterministic prefix-based mapping and fails closed
  on unknown prefixes.

These tests rely on the cost_profile registry shipped in E1/E2; if those
profile entries change, the assertions below need to follow.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = ROOT / "services" / "repo-truth-extractor"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

import run_extraction_v5 as runner  # noqa: E402


# ---------------------------------------------------------------------------
# infer_route_for_model
# ---------------------------------------------------------------------------


def test_infer_route_openrouter_openai_prefix():
    route = runner.infer_route_for_model("openai/gpt-5.4")
    assert route == ("openrouter", "openai/gpt-5.4", "OPENROUTER_API_KEY")


def test_infer_route_openrouter_anthropic_prefix():
    route = runner.infer_route_for_model("anthropic/claude-sonnet-4.6")
    assert route == (
        "openrouter",
        "anthropic/claude-sonnet-4.6",
        "OPENROUTER_API_KEY",
    )


def test_infer_route_direct_gemini():
    route = runner.infer_route_for_model("gemini-3-flash-preview")
    assert route == ("gemini", "gemini-3-flash-preview", "GEMINI_API_KEY")


def test_infer_route_direct_xai_grok():
    route = runner.infer_route_for_model("grok-4-1-fast-non-reasoning")
    assert route == (
        "xai",
        "grok-4-1-fast-non-reasoning",
        "XAI_API_KEY",
    )


def test_infer_route_unknown_prefix_fails_closed():
    with pytest.raises(ValueError, match="no provider prefix matched"):
        runner.infer_route_for_model("frobnitz/foo-bar-1.2")


def test_infer_route_empty_input_raises():
    with pytest.raises(ValueError, match="empty/non-string"):
        runner.infer_route_for_model("")
    with pytest.raises(ValueError, match="empty/non-string"):
        runner.infer_route_for_model("   ")


# ---------------------------------------------------------------------------
# derive_ladder_for_cell
# ---------------------------------------------------------------------------


def _reset_ladder_cache():
    """LRU cache leaks across tests; clear before any test that mutates env
    or relies on a fresh resolution."""
    runner._derive_ladder_for_cell_cached.cache_clear()


def test_derive_ladder_for_cell_value_default_synth_high():
    _reset_ladder_cache()
    routes = runner.derive_ladder_for_cell("value-default", "SYNTH", "HIGH")
    assert routes == [
        ("openrouter", "anthropic/claude-sonnet-4.6", "OPENROUTER_API_KEY"),
    ]


def test_derive_ladder_for_cell_quality_synth_critical():
    _reset_ladder_cache()
    routes = runner.derive_ladder_for_cell("quality", "SYNTH", "CRITICAL")
    assert routes == [
        ("openrouter", "anthropic/claude-opus-4.6", "OPENROUTER_API_KEY"),
    ]


def test_derive_ladder_for_cell_cli_override_propagates():
    _reset_ladder_cache()
    routes = runner.derive_ladder_for_cell(
        "value-default",
        "SYNTH",
        "HIGH",
        cli_overrides={"VALUE_DEFAULT_SYNTH_HIGH_MODEL": "openai/gpt-5-mini"},
    )
    assert routes == [
        ("openrouter", "openai/gpt-5-mini", "OPENROUTER_API_KEY"),
    ]


def test_derive_ladder_for_cell_env_var_propagates(monkeypatch):
    _reset_ladder_cache()
    monkeypatch.setenv("VALUE_DEFAULT_SYNTH_HIGH_MODEL", "anthropic/claude-opus-4.7")
    routes = runner.derive_ladder_for_cell("value-default", "SYNTH", "HIGH")
    assert routes == [
        ("openrouter", "anthropic/claude-opus-4.7", "OPENROUTER_API_KEY"),
    ]


def test_derive_ladder_for_cell_cache_invalidates_on_override_change():
    _reset_ladder_cache()
    first = runner.derive_ladder_for_cell(
        "value-default",
        "SYNTH",
        "HIGH",
        cli_overrides={"VALUE_DEFAULT_SYNTH_HIGH_MODEL": "openai/gpt-5-mini"},
    )
    second = runner.derive_ladder_for_cell(
        "value-default",
        "SYNTH",
        "HIGH",
        cli_overrides={"VALUE_DEFAULT_SYNTH_HIGH_MODEL": "anthropic/claude-haiku-4.5"},
    )
    assert first[0][1] == "openai/gpt-5-mini"
    assert second[0][1] == "anthropic/claude-haiku-4.5"


def test_derive_ladder_for_cell_unresolved_alias_raises():
    _reset_ladder_cache()
    # SYNTH_CRITICAL_FALLBACK exists only on the quality profile; calling it
    # against value-default has no alias entry → must raise rather than send
    # a literal placeholder downstream.
    with pytest.raises(ValueError, match="alias .* unresolved"):
        runner.derive_ladder_for_cell(
            "value-default", "SYNTH", "CRITICAL_FALLBACK"
        )


def test_derive_ladder_for_cell_disabled_provider_filters_route():
    _reset_ladder_cache()
    routes = runner.derive_ladder_for_cell(
        "value-default",
        "SYNTH",
        "HIGH",
        disabled_providers=["openrouter"],
    )
    # The only route in the value-default SYNTH/HIGH cell is openrouter → filter
    # drops it and the list is empty so callers can decide to fall through.
    assert routes == []


def test_derive_ladder_for_cell_unsupported_stage_raises():
    _reset_ladder_cache()
    with pytest.raises(NotImplementedError, match="reserved for E8"):
        runner.derive_ladder_for_cell(
            "value-default", "SYNTH", "HIGH", stage="full_ladder"
        )
