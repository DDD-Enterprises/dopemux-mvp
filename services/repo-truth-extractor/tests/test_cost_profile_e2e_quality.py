"""E9 quality cost-profile integration coverage."""

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
from lib.spend_ledger import SpendLedger  # noqa: E402


def _cfg(tmp_path: Path) -> Any:
    cfg = runner.RunnerConfig.__new__(runner.RunnerConfig)
    object.__setattr__(cfg, "ledger", SpendLedger(tmp_path, "e9_quality"))
    object.__setattr__(cfg, "max_cost_usd", None)
    object.__setattr__(cfg, "default_service_tier", "priority")
    object.__setattr__(cfg, "enable_cached_input", True)
    object.__setattr__(cfg, "disabled_providers", ())
    return cfg


def _first_route(lane: str, tier: str, **kwargs: Any) -> tuple[str, str, str]:
    ladder = runner.derive_ladder_for_cell("quality", lane, tier, **kwargs)
    assert len(ladder) == 1
    return ladder[0]


def test_quality_profile_sets_priority_and_disables_batch() -> None:
    profile = runner.COST_PROFILES["quality"]

    assert profile["routing_policy"] == "quality"
    assert profile["default_service_tier"] == "priority"
    assert profile["enable_batch_when_supported"] is False
    assert profile["escalation_max_hops"] == 3


def test_quality_synth_critical_defaults_to_opus_4_6_not_4_7() -> None:
    assert _first_route("SYNTH", "critical") == (
        "openrouter",
        "anthropic/claude-opus-4.6",
        "OPENROUTER_API_KEY",
    )


def test_quality_alias_override_canary_switches_synth_critical_to_opus_4_7() -> None:
    assert _first_route(
        "SYNTH",
        "critical",
        cli_overrides={
            "QUALITY_SYNTH_CRITICAL_MODEL": "anthropic/claude-opus-4.7",
        },
    ) == (
        "openrouter",
        "anthropic/claude-opus-4.7",
        "OPENROUTER_API_KEY",
    )


def test_quality_ce_medium_uses_gpt_5_5() -> None:
    assert _first_route("CE", "medium") == (
        "openrouter",
        "openai/gpt-5.5",
        "OPENROUTER_API_KEY",
    )


def test_quality_ce_high_uses_gpt_5_5() -> None:
    assert _first_route("CE", "high") == (
        "openrouter",
        "openai/gpt-5.5",
        "OPENROUTER_API_KEY",
    )


def test_quality_disabled_openrouter_removes_profile_route() -> None:
    assert (
        runner.derive_ladder_for_cell(
            "quality",
            "SYNTH",
            "critical",
            disabled_providers=("openrouter",),
        )
        == []
    )


def test_quality_priority_spend_matches_expected_dollars(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)

    priced = runner._pricing_preview(
        cfg,
        provider="openai",
        model_id="gpt-5.4",
        input_tokens=1_000_000,
        output_tokens=100_000,
        execution_mode="sync",
        service_tier="priority",
    )

    assert priced is not None
    assert priced["estimated_cost_usd"] == pytest.approx(10.0)
    assert priced["cost_breakdown"]["tier_multiplier"] == 2.5


def test_quality_route_batch_metadata_carries_priority_and_anthropic_cache(
    tmp_path: Path,
) -> None:
    cfg = _cfg(tmp_path)

    metadata = runner._route_optimizer_batch_metadata(
        {
            "provider": "openrouter",
            "model_id": "anthropic/claude-opus-4.6",
            "service_tier": "priority",
            "cache_strategy": "cache_control_explicit",
        },
        cfg,
        system_prompt="stable system prefix",
        user_content="mutable request",
    )

    assert metadata["service_tier"] == "priority"
    assert metadata["cache_strategy"] == "cache_control_explicit"
    assert metadata["cache_strategy_applied"] == "true"


def test_legacy_optimal_resolves_to_quality_profile() -> None:
    name, profile = runner.resolve_cost_profile("optimal")

    assert name == "quality"
    assert profile["routing_policy"] == "quality"
