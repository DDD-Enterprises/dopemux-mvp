"""Optimizer-aware pricing math (May 2026 schema extension).

Covers:
- Flex service_tier multiplier (0.5x).
- Priority service_tier multiplier (2.5x).
- Cached input pricing (cache_read_multiplier).
- Batch discount.
- Tiered pricing (Gemini Pro >200K).
- Combined multipliers.
- Preventive cost cap helper (make_projected_cost_check).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = ROOT / "services" / "repo-truth-extractor"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from lib.spend_ledger import (
    SpendLedger,
    compute_optimized_cost,
    get_model_cost_rate,
    make_projected_cost_check,
)
import run_extraction_v5 as runner  # noqa: E402


def _make_cfg(**overrides):
    payload = {
        "dry_run": False,
        "max_files_docs": 35,
        "max_files_code": 20,
        "max_chars": 650000,
        "max_request_bytes": 200000,
        "file_truncate_chars": 70000,
        "home_scan_mode": "safe",
        "resume": False,
        "fail_fast_auth": True,
        "gemini_auth_mode": "auto",
        "gemini_transport": "sdk",
        "openai_transport": "openai_sdk",
        "xai_transport": "openai_sdk",
        "retry_policy": "default",
        "retry_max_attempts": 1,
        "retry_base_seconds": 0.0,
        "retry_max_seconds": 0.0,
        "phase_auth_fail_threshold": 1,
        "partition_workers": 1,
        "debug_phase_inputs": False,
        "fail_fast_missing_inputs": False,
        "routing_policy": "balanced_openrouter",
    }
    payload.update(overrides)
    return runner.RunnerConfig(**payload)


def test_default_tier_no_optimizers_matches_legacy_math() -> None:
    rate = get_model_cost_rate(provider="openai", model_id="gpt-5.4")
    out = compute_optimized_cost(
        rate,
        input_tokens=1_000_000,
        output_tokens=100_000,
    )
    # Expected: 1.0 × $2.50 + 0.1 × $15.00 = $2.50 + $1.50 = $4.00
    assert abs(out["final_cost_usd"] - 4.00) < 0.001
    assert out["tier_multiplier"] == 1.0
    assert out["batch_multiplier"] == 1.0
    assert out["cached_input_tokens"] == 0


def test_flex_tier_halves_cost_for_openai_models() -> None:
    rate = get_model_cost_rate(provider="openai", model_id="gpt-5.4")
    out = compute_optimized_cost(
        rate,
        input_tokens=1_000_000,
        output_tokens=100_000,
        service_tier="flex",
    )
    # Expected: $4.00 × 0.5 = $2.00
    assert abs(out["final_cost_usd"] - 2.00) < 0.001
    assert out["tier_multiplier"] == 0.5
    assert out["service_tier"] == "flex"
    assert any("service_tier:flex" in tag for tag in out["applied_optimizers"])


def test_priority_tier_multiplies_cost_for_openai_models() -> None:
    rate = get_model_cost_rate(provider="openai", model_id="gpt-5.4")
    out = compute_optimized_cost(
        rate,
        input_tokens=1_000_000,
        output_tokens=100_000,
        service_tier="priority",
    )
    # Expected: $4.00 × 2.5 = $10.00
    assert abs(out["final_cost_usd"] - 10.00) < 0.001
    assert out["tier_multiplier"] == 2.5
    assert out["service_tier"] == "priority"


def test_cached_input_priced_at_cached_rate() -> None:
    """gpt-5.4 input is $2.50/M, cached is $0.25/M (10%)."""
    rate = get_model_cost_rate(provider="openai", model_id="gpt-5.4")
    out = compute_optimized_cost(
        rate,
        input_tokens=1_000_000,
        output_tokens=0,
        cached_input_tokens=500_000,  # half from cache
    )
    # Expected:
    #   uncached input: 0.5M × $2.50 = $1.25
    #   cached input:   0.5M × $0.25 = $0.125
    #   total:                          $1.375
    assert abs(out["final_cost_usd"] - 1.375) < 0.001
    assert out["cached_input_tokens"] == 500_000
    assert out["uncached_input_tokens"] == 500_000
    # cache discount = full-rate input - actual = $2.50 - $1.375 = $1.125
    assert abs(out["cache_discount_usd"] - 1.125) < 0.001


def test_runtime_spend_accounting_uses_cached_tokens(tmp_path: Path) -> None:
    cfg = _make_cfg(enable_cached_input=True)
    ledger = SpendLedger(tmp_path, "run_cached")
    object.__setattr__(cfg, "ledger", ledger)

    record = runner._accumulate_runtime_spend(
        cfg,
        phase="R",
        step_id="R7",
        partition_id="R_P0001",
        provider="openrouter",
        model_id="anthropic/claude-opus-4.6",
        execution_mode="sync",
        response_summary={
            "usage": {
                "input_tokens": 1_000_000,
                "output_tokens": 0,
                "cached_tokens": 1_000_000,
            }
        },
        response_text="{}",
        fallback_input_tokens=1,
        fallback_output_tokens=1,
    )

    assert record is not None
    assert record["cached_tokens"] == 1_000_000
    assert record["cost_breakdown"]["cached_input_tokens"] == 1_000_000
    assert record["cost_breakdown"]["cache_discount_usd"] > 0


def test_batch_discount_applied_when_is_batch_true() -> None:
    rate = get_model_cost_rate(provider="openai", model_id="gpt-5.4")
    out = compute_optimized_cost(
        rate,
        input_tokens=1_000_000,
        output_tokens=100_000,
        is_batch=True,
    )
    # Expected: $4.00 × 0.5 (batch_discount=0.5 in catalog) = $2.00
    assert abs(out["final_cost_usd"] - 2.00) < 0.001
    assert out["batch_multiplier"] == 0.5
    assert out["is_batch"] is True


def test_pricing_preview_marks_batch_submit_for_optimizer_discount(tmp_path: Path) -> None:
    cfg = _make_cfg(enable_batch_when_supported=True)
    ledger = SpendLedger(tmp_path, "run_batch_preview")
    object.__setattr__(cfg, "ledger", ledger)

    preview = runner._pricing_preview(
        cfg,
        provider="openai",
        model_id="gpt-5.4",
        input_tokens=1_000_000,
        output_tokens=100_000,
        execution_mode="batch_submit",
        route="openai/gpt-5.4",
    )

    assert preview is not None
    assert preview["cost_breakdown"]["is_batch"] is True
    assert preview["cost_breakdown"]["batch_multiplier"] == 0.5


def test_combined_flex_and_cache_stack() -> None:
    rate = get_model_cost_rate(provider="openai", model_id="gpt-5.4")
    out = compute_optimized_cost(
        rate,
        input_tokens=1_000_000,
        output_tokens=100_000,
        cached_input_tokens=500_000,
        service_tier="flex",
    )
    # Base with cache: $1.375 + (0.1M × $15) = $1.375 + $1.50 = $2.875
    # Flex 0.5x:                                          $1.4375
    assert abs(out["final_cost_usd"] - 1.4375) < 0.001


def test_tiered_pricing_applies_above_threshold() -> None:
    """gemini-3.1-pro-preview: $2/$12 ≤200K, $4/$18 >200K."""
    rate = get_model_cost_rate(provider="gemini", model_id="gemini-3.1-pro-preview")
    # Below threshold: standard rate
    below = compute_optimized_cost(
        rate, input_tokens=100_000, output_tokens=10_000, prompt_token_count=100_000
    )
    # Expected: 0.1M × $2 + 0.01M × $12 = $0.20 + $0.12 = $0.32
    assert abs(below["final_cost_usd"] - 0.32) < 0.001

    # Above threshold: tiered rate
    above = compute_optimized_cost(
        rate, input_tokens=300_000, output_tokens=10_000, prompt_token_count=300_000
    )
    # Expected: 0.3M × $4 + 0.01M × $18 = $1.20 + $0.18 = $1.38
    assert abs(above["final_cost_usd"] - 1.38) < 0.001


def test_unknown_model_returns_none_for_optimizer_fields() -> None:
    """A model not in the catalog should still resolve (via fallback) and have
    all optimizer fields as None — i.e., callers can detect "no optimizer
    info available" without exception."""
    rate = get_model_cost_rate(provider="unknown", model_id="frobozz-9000")
    assert rate["unknown_model"] is True
    assert rate["service_tier_flex_multiplier"] is None
    assert rate["service_tier_priority_multiplier"] is None
    assert rate["cache_read_multiplier"] is None
    assert rate["batch_discount"] is None
    # And compute should still work, just with default multipliers
    out = compute_optimized_cost(rate, input_tokens=1_000_000, output_tokens=0)
    assert out["final_cost_usd"] > 0
    assert out["tier_multiplier"] == 1.0


def test_make_projected_cost_check_blocks_over_cap() -> None:
    rate = get_model_cost_rate(provider="openai", model_id="gpt-5.4")
    # Current spend $9.50, cap $10. Adding ~$1 of work should breach.
    check = make_projected_cost_check(
        rate=rate, current_total_cost_usd=9.50, max_cost_usd=10.00
    )
    # 200K input + 50K output ≈ 0.2 × $2.50 + 0.05 × $15 = $0.50 + $0.75 = $1.25
    assert check(input_tokens=200_000, output_tokens=50_000) is False
    # 10K input + 5K output ≈ tiny
    assert check(input_tokens=10_000, output_tokens=5_000) is True


def test_make_projected_cost_check_no_cap_always_ok() -> None:
    rate = get_model_cost_rate(provider="openai", model_id="gpt-5.4")
    check = make_projected_cost_check(
        rate=rate, current_total_cost_usd=1_000_000.0, max_cost_usd=None
    )
    assert check(input_tokens=10_000_000_000, output_tokens=10_000_000_000) is True


def test_anthropic_cache_read_uses_cache_read_multiplier() -> None:
    """Claude opus 4.6: $5 input, cache_read $0.50 (10% via cache_read_multiplier=0.1)."""
    rate = get_model_cost_rate(
        provider="openrouter", model_id="anthropic/claude-opus-4.6"
    )
    if rate.get("input_cost_per_1m_usd") and rate.get("cache_read_multiplier") is not None:
        out = compute_optimized_cost(
            rate,
            input_tokens=1_000_000,
            output_tokens=0,
            cached_input_tokens=1_000_000,
        )
        # All from cache: 1M × $5 × 0.1 = $0.50
        assert abs(out["final_cost_usd"] - 0.50) < 0.01


def test_data_residency_us_multiplier_for_claude_4_6() -> None:
    """Anthropic Sonnet 4.6 / Opus 4.6+ supports inference_geo='us' = 1.1x.
    The catalog doesn't currently have data_residency_us_multiplier populated
    for these models — this test just verifies the data_residency wiring path
    is exercised and doesn't blow up when the field is missing."""
    rate = get_model_cost_rate(
        provider="openrouter", model_id="anthropic/claude-opus-4.6"
    )
    out = compute_optimized_cost(
        rate,
        input_tokens=1_000_000,
        output_tokens=0,
        data_residency="us",
    )
    # Field missing → multiplier 1.0 → cost unchanged
    assert out["data_residency_multiplier"] == 1.0


def test_optimizer_fields_present_on_resolved_rate() -> None:
    """After E2, every get_model_cost_rate() response should include the
    optimizer field keys (possibly None) so downstream code can detect
    availability uniformly."""
    rate = get_model_cost_rate(provider="openai", model_id="gpt-5.4")
    for key in (
        "service_tier_flex_multiplier",
        "service_tier_priority_multiplier",
        "cache_read_multiplier",
        "cached_input_cost_per_1m_usd",
        "batch_discount",
        "prompt_cache_min_tokens",
        "auto_cache_enabled",
        "context_window",
        "supports_json_schema_strict",
    ):
        assert key in rate, f"optimizer field {key} missing from get_model_cost_rate response"
