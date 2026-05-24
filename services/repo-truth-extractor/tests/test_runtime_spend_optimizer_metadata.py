"""Runtime spend accounting must preserve cost-profile optimizer metadata.

These tests cover the E9 blocker found before the E9 test-only packet:
``run_extraction_v5`` passed headline token counts into ``SpendLedger`` while
dropping cached-input, service-tier, and batch-discount metadata that the ledger
already knows how to price.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = ROOT / "services" / "repo-truth-extractor"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

import run_extraction_v5 as runner  # noqa: E402
from lib.spend_ledger import SpendLedger  # noqa: E402


def _cfg(tmp_path: Path, *, default_service_tier: str = "default"):
    cfg = runner.RunnerConfig.__new__(runner.RunnerConfig)
    object.__setattr__(cfg, "ledger", SpendLedger(tmp_path, "optimizer_runtime"))
    object.__setattr__(cfg, "max_cost_usd", None)
    object.__setattr__(cfg, "default_service_tier", default_service_tier)
    return cfg


def test_accumulate_runtime_spend_prices_cached_tokens_and_observed_service_tier(
    tmp_path: Path,
) -> None:
    cfg = _cfg(tmp_path)

    priced = runner._accumulate_runtime_spend(
        cfg,
        phase="A",
        step_id="A1",
        partition_id="A_P0001",
        provider="openai",
        model_id="gpt-5.4",
        execution_mode="sync",
        response_summary={
            "usage": {
                "input_tokens": 1_000_000,
                "output_tokens": 100_000,
                "cached_tokens": 500_000,
                "service_tier": "flex",
            }
        },
        response_text="{}",
        route="openai/gpt-5.4",
    )

    assert priced is not None
    assert priced["estimated_cost_usd"] == pytest.approx(1.4375)
    assert priced["cost_breakdown"]["cached_input_tokens"] == 500_000
    assert priced["cost_breakdown"]["service_tier"] == "flex"
    assert priced["cost_breakdown"]["cache_discount_usd"] == pytest.approx(1.125)


def test_accumulate_runtime_spend_uses_cfg_service_tier_when_provider_does_not_echo(
    tmp_path: Path,
) -> None:
    cfg = _cfg(tmp_path, default_service_tier="flex")

    priced = runner._accumulate_runtime_spend(
        cfg,
        phase="A",
        step_id="A1",
        partition_id="A_P0001",
        provider="openai",
        model_id="gpt-5.4",
        execution_mode="sync",
        response_summary={
            "usage": {
                "input_tokens": 1_000_000,
                "output_tokens": 100_000,
                "prompt_tokens_details": {"cached_tokens": 500_000},
            }
        },
        response_text="{}",
        route="openai/gpt-5.4",
    )

    assert priced is not None
    assert priced["estimated_cost_usd"] == pytest.approx(1.4375)
    assert priced["cost_breakdown"]["service_tier"] == "flex"
    assert priced["cost_breakdown"]["cached_input_tokens"] == 500_000


def test_accumulate_runtime_spend_preserves_default_sync_cost_without_optimizers(
    tmp_path: Path,
) -> None:
    cfg = _cfg(tmp_path)

    priced = runner._accumulate_runtime_spend(
        cfg,
        phase="A",
        step_id="A1",
        partition_id="A_P0001",
        provider="openai",
        model_id="gpt-5.4",
        execution_mode="sync",
        response_summary={
            "usage": {"input_tokens": 1_000_000, "output_tokens": 100_000}
        },
        response_text="{}",
        route="openai/gpt-5.4",
    )

    assert priced is not None
    assert priced["estimated_cost_usd"] == pytest.approx(4.0)
    assert priced["cost_breakdown"]["is_batch"] is False
    assert priced["cost_breakdown"]["batch_multiplier"] == 1.0


def test_accumulate_runtime_spend_prices_anthropic_cache_write_tokens(
    tmp_path: Path,
) -> None:
    cfg = _cfg(tmp_path)

    priced = runner._accumulate_runtime_spend(
        cfg,
        phase="S",
        step_id="S1",
        partition_id="S_P0001",
        provider="openrouter",
        model_id="anthropic/claude-opus-4.6",
        execution_mode="sync",
        response_summary={
            "usage": {
                "input_tokens": 1_000_000,
                "output_tokens": 0,
                "cache_creation_input_tokens": 1_000_000,
            }
        },
        response_text="{}",
        route="openrouter/anthropic/claude-opus-4.6",
    )

    assert priced is not None
    assert priced["estimated_cost_usd"] == pytest.approx(6.25)
    assert priced["cost_breakdown"]["cache_write_input_tokens"] == 1_000_000
    assert priced["cost_breakdown"]["cache_write_input_rate_per_1m_usd"] == 6.25
    assert "cache_write(1000000tok,5m)" in priced["cost_breakdown"]["applied_optimizers"]


def test_reserve_projected_spend_prices_batch_submit_with_batch_discount(
    tmp_path: Path,
) -> None:
    cfg = _cfg(tmp_path)

    reserved = runner._reserve_projected_spend(
        cfg,
        phase="A",
        step_id="A1",
        partition_id="A_P0001",
        provider="openai",
        model_id="gpt-5.4",
        input_tokens=1_000_000,
        output_tokens=100_000,
        execution_mode="batch_submit",
        route="openai/gpt-5.4",
    )

    assert reserved is not None
    assert reserved["estimated_cost_usd"] == pytest.approx(2.0)
    assert reserved["cost_breakdown"]["is_batch"] is True
    assert reserved["cost_breakdown"]["batch_multiplier"] == 0.5
