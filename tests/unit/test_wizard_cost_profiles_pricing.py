"""TP-RTE-TRUTH-R4-004 (F-43): the wizard's cost-estimate stage used to price
models from a hand-maintained static MODEL_PRICING table ("last synced
2026-07-12") that had already drifted from config/pricing.yaml -- the single
pricing authority TP-RTE-TRUTH-R2-001 established (services/repo-truth-
extractor/extractor/costing.py::load_pricing_registry). Example of the
already-manifested drift found while fixing this: the old static table
priced openai/gpt-5.2 at ($2.00, $8.00); config/pricing.yaml prices it at
($2.50, $15.00).

These tests assert `_model_price` resolves against the LIVE
config/pricing.yaml content (reading that file directly here too, so the
test never hardcodes a number that could itself go stale) and that a
missing/unreadable pricing file degrades to the documented fallback instead
of crashing the wizard.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

import dopemux.ux.wizard.cost_profiles as cost_profiles

REPO_ROOT = Path(__file__).resolve().parents[2]
PRICING_CONFIG_PATH = REPO_ROOT / "config" / "pricing.yaml"


@pytest.fixture(autouse=True)
def _reset_pricing_cache():
    cost_profiles.reset_pricing_cache()
    yield
    cost_profiles.reset_pricing_cache()


def _live_pricing_row(key: str) -> tuple[float, float]:
    payload = yaml.safe_load(PRICING_CONFIG_PATH.read_text(encoding="utf-8"))
    row = payload["models"][key]
    return float(row["input_cost_per_m"]), float(row["output_cost_per_m"])


def test_pricing_config_exists_and_is_readable():
    assert PRICING_CONFIG_PATH.exists(), (
        f"config/pricing.yaml not found at {PRICING_CONFIG_PATH} -- "
        "the pricing-authority test below has nothing to compare against."
    )


def test_model_price_matches_live_pricing_yaml_for_direct_provider():
    """openai/gpt-5.2 is a real, already-manifested drift case: the old
    static MODEL_PRICING table said (2.00, 8.00); the live catalog says
    something else. Assert against the live file, not a hardcoded number,
    so this test can't itself go stale."""
    expected = _live_pricing_row("openai/gpt-5.2")
    assert cost_profiles._model_price("openai", "gpt-5.2") == expected
    # The pre-fix static table's value for this model -- must NOT match,
    # proving the estimate is no longer reading the stale snapshot.
    assert expected != (2.00, 8.00)


def test_model_price_matches_live_pricing_yaml_for_openrouter_compound_model():
    expected = _live_pricing_row("openrouter/openai/gpt-5.2-chat")
    assert cost_profiles._model_price("openrouter", "openai/gpt-5.2-chat") == expected


def test_model_price_falls_back_when_pricing_config_unreadable(monkeypatch, tmp_path):
    missing_path = tmp_path / "does-not-exist.yaml"
    monkeypatch.setattr(cost_profiles, "_PRICING_CONFIG_PATH", missing_path)
    cost_profiles.reset_pricing_cache()

    # A model present in the small fallback table still resolves.
    assert cost_profiles._model_price("openai", "gpt-5-nano") == (0.10, 0.40)
    # A model absent from both the (unreadable) live registry and the
    # fallback table degrades to the documented mid-range guess rather than
    # raising.
    assert cost_profiles._model_price("openai", "some-brand-new-model") == (1.00, 4.00)


def test_estimate_cost_runs_for_every_shipped_routing_policy():
    for policy in cost_profiles.ROUTING_LADDERS:
        low, high = cost_profiles.estimate_cost(policy, 50_000_000)
        assert low >= 0
        assert high >= low
