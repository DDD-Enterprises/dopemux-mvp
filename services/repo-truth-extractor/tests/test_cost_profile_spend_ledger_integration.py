"""E9 spend-ledger integration coverage for cost-profile optimizers."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = ROOT / "services" / "repo-truth-extractor"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from lib.spend_ledger import (  # noqa: E402
    SpendLedger,
    compute_optimized_cost,
    get_model_cost_rate,
    make_projected_cost_check,
)


def test_accumulate_cached_input_reduces_final_cost(tmp_path: Path) -> None:
    ledger = SpendLedger(tmp_path, "e9_spend")
    priced = ledger.accumulate(
        "A",
        1_000_000,
        0,
        provider="openai",
        model_id="gpt-5.4",
        cached_input_tokens=500_000,
    )

    assert priced["estimated_cost_usd"] == pytest.approx(1.375)
    assert priced["cost_breakdown"]["cache_discount_usd"] == pytest.approx(1.125)


def test_accumulate_flex_service_tier_applies_multiplier(tmp_path: Path) -> None:
    ledger = SpendLedger(tmp_path, "e9_spend")
    priced = ledger.accumulate(
        "A",
        1_000_000,
        100_000,
        provider="openai",
        model_id="gpt-5.4",
        service_tier="flex",
    )

    assert priced["estimated_cost_usd"] == pytest.approx(2.0)
    assert priced["cost_breakdown"]["tier_multiplier"] == 0.5


def test_accumulate_batch_applies_discount(tmp_path: Path) -> None:
    ledger = SpendLedger(tmp_path, "e9_spend")
    priced = ledger.accumulate(
        "A",
        1_000_000,
        100_000,
        provider="openai",
        model_id="gpt-5.4",
        is_batch=True,
    )

    assert priced["estimated_cost_usd"] == pytest.approx(2.0)
    assert priced["cost_breakdown"]["batch_multiplier"] == 0.5


def test_tier_cache_and_batch_stack_to_expected_effective_cost() -> None:
    rate = get_model_cost_rate(provider="openai", model_id="gpt-5.4")

    priced = compute_optimized_cost(
        rate,
        input_tokens=1_000_000,
        output_tokens=100_000,
        cached_input_tokens=500_000,
        service_tier="flex",
        is_batch=True,
    )

    assert priced["final_cost_usd"] == pytest.approx(0.71875)
    assert priced["tier_multiplier"] == 0.5
    assert priced["batch_multiplier"] == 0.5


def test_preventive_cap_blocks_projected_call_before_execution() -> None:
    rate = get_model_cost_rate(provider="openai", model_id="gpt-5.4")
    check = make_projected_cost_check(
        rate=rate,
        current_total_cost_usd=9.50,
        max_cost_usd=10.00,
    )

    assert check(input_tokens=200_000, output_tokens=50_000) is False


def test_preventive_cap_accounts_for_flex_optimizer() -> None:
    rate = get_model_cost_rate(provider="openai", model_id="gpt-5.4")
    check = make_projected_cost_check(
        rate=rate,
        current_total_cost_usd=9.50,
        max_cost_usd=10.00,
    )

    assert check(input_tokens=100_000, output_tokens=20_000, service_tier="flex") is True


def test_cached_input_ratio_is_visible_in_returned_breakdown() -> None:
    rate = get_model_cost_rate(provider="openai", model_id="gpt-5.4")
    priced = compute_optimized_cost(
        rate,
        input_tokens=1_000_000,
        output_tokens=0,
        cached_input_tokens=250_000,
    )

    assert priced["cached_input_tokens"] / priced["input_tokens"] == pytest.approx(0.25)
    assert priced["uncached_input_tokens"] == 750_000


def test_spend_ledger_json_persists_effective_total_and_model_surface(
    tmp_path: Path,
) -> None:
    ledger = SpendLedger(tmp_path, "e9_spend")
    ledger.accumulate(
        "A",
        1_000_000,
        100_000,
        provider="openai",
        model_id="gpt-5.4",
        service_tier="flex",
    )

    payload = json.loads((tmp_path / "spend_ledger.json").read_text())
    assert payload["total_cost_usd"] == pytest.approx(2.0)
    assert payload["models"]["openai/gpt-5.4"]["estimated_cost_usd"] == pytest.approx(2.0)
    assert payload["providers"]["openai"]["usage_count"] == 1


def test_unknown_model_fallback_is_recorded_in_ledger(tmp_path: Path) -> None:
    ledger = SpendLedger(tmp_path, "e9_spend")
    priced = ledger.accumulate(
        "A",
        1_000,
        100,
        provider="unknown",
        model_id="unknown-model",
    )

    payload = json.loads((tmp_path / "spend_ledger.json").read_text())
    assert priced["unknown_model"] is True
    assert payload["unknown_model_events"] == 1
    assert payload["fallback_usage_count"] == 1


def test_phase_model_and_provider_totals_match_effective_cost(tmp_path: Path) -> None:
    ledger = SpendLedger(tmp_path, "e9_spend")
    ledger.accumulate(
        "S",
        1_000_000,
        0,
        provider="openrouter",
        model_id="anthropic/claude-opus-4.6",
        cached_input_tokens=1_000_000,
    )

    payload = json.loads((tmp_path / "spend_ledger.json").read_text())
    assert payload["phases"]["S"]["estimated_cost_usd"] == pytest.approx(0.50)
    assert payload["phases"]["S"]["providers"]["openrouter"]["estimated_cost_usd"] == pytest.approx(0.50)
