"""E9 Anthropic cache-control integration coverage."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = ROOT / "services" / "repo-truth-extractor"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

import run_extraction_v5 as runner  # noqa: E402
from lib.spend_ledger import SpendLedger, compute_optimized_cost, get_model_cost_rate  # noqa: E402
from lib.structured_output_contracts import prompt_caching_directives_for_provider  # noqa: E402


def _cfg(tmp_path: Path) -> Any:
    cfg = runner.RunnerConfig.__new__(runner.RunnerConfig)
    object.__setattr__(cfg, "ledger", SpendLedger(tmp_path, "e9_anthropic_cache"))
    object.__setattr__(cfg, "max_cost_usd", None)
    object.__setattr__(cfg, "default_service_tier", "default")
    object.__setattr__(cfg, "enable_cached_input", True)
    return cfg


def test_anthropic_via_openrouter_explicit_cache_control_markers() -> None:
    directives = prompt_caching_directives_for_provider(
        "openrouter",
        "anthropic/claude-opus-4.6",
        prompt_text_lengths=(1200, 800, 400),
        cache_strategy="cache_control_explicit",
        auto_cache_enabled=True,
    )

    assert directives["applied"] is True
    assert directives["strategy"] == "cache_control_explicit"
    assert directives["cache_control_markers"]
    assert directives["prompt_cache_key"] is None


def test_route_prompt_cache_directives_pass_anthropic_markers(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)

    directives = runner._route_prompt_cache_directives_for_execution(
        {
            "provider": "openrouter",
            "model_id": "anthropic/claude-opus-4.6",
            "cache_strategy": "cache_control_explicit",
        },
        cfg,
        system_prompt="stable system prefix",
        user_content="mutable request",
    )

    assert directives["applied"] is True
    assert directives["cache_control_markers"]


def test_first_anthropic_cache_write_cost_is_one_point_two_five_x_input() -> None:
    rate = get_model_cost_rate(
        provider="openrouter",
        model_id="anthropic/claude-opus-4.6",
    )
    priced = compute_optimized_cost(
        rate,
        input_tokens=1_000_000,
        output_tokens=0,
        cache_write_input_tokens=1_000_000,
    )

    assert priced["final_cost_usd"] == pytest.approx(6.25)
    assert priced["cache_write_input_rate_per_1m_usd"] == pytest.approx(6.25)


def test_subsequent_anthropic_cache_read_cost_is_tenth_input_rate() -> None:
    rate = get_model_cost_rate(
        provider="openrouter",
        model_id="anthropic/claude-opus-4.6",
    )
    priced = compute_optimized_cost(
        rate,
        input_tokens=1_000_000,
        output_tokens=0,
        cached_input_tokens=1_000_000,
    )

    assert priced["final_cost_usd"] == pytest.approx(0.50)
    assert priced["cached_input_rate_per_1m_usd"] == pytest.approx(0.50)


def test_cache_write_to_read_ratio_is_more_than_ten_x() -> None:
    rate = get_model_cost_rate(
        provider="openrouter",
        model_id="anthropic/claude-opus-4.6",
    )
    write = compute_optimized_cost(
        rate,
        input_tokens=1_000_000,
        output_tokens=0,
        cache_write_input_tokens=1_000_000,
    )
    read = compute_optimized_cost(
        rate,
        input_tokens=1_000_000,
        output_tokens=0,
        cached_input_tokens=1_000_000,
    )

    assert write["final_cost_usd"] / read["final_cost_usd"] == pytest.approx(12.5)


def test_mocked_anthropic_usage_parses_cache_read_input_tokens() -> None:
    cached = runner._runtime_cached_input_tokens(
        {
            "usage": {
                "input_tokens": 1_000_000,
                "output_tokens": 0,
                "cache_read_input_tokens": 900_000,
            }
        }
    )

    assert cached == 900_000


def test_anthropic_cache_discount_surfaces_in_runtime_spend(tmp_path: Path) -> None:
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
                "cache_read_input_tokens": 1_000_000,
            }
        },
        response_text="{}",
        route="openrouter/anthropic/claude-opus-4.6",
    )

    assert priced is not None
    assert priced["estimated_cost_usd"] == pytest.approx(0.50)
    assert priced["cost_breakdown"]["cache_discount_usd"] == pytest.approx(4.50)
