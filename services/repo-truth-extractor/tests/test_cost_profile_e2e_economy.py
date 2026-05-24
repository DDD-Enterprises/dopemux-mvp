"""E9 economy cost-profile integration coverage."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = ROOT / "services" / "repo-truth-extractor"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

import run_extraction_v5 as runner  # noqa: E402
from lib.spend_ledger import SpendLedger, get_model_cost_rate, make_projected_cost_check  # noqa: E402


def _cfg(tmp_path: Path) -> Any:
    cfg = runner.RunnerConfig.__new__(runner.RunnerConfig)
    object.__setattr__(cfg, "ledger", SpendLedger(tmp_path, "e9_economy"))
    object.__setattr__(cfg, "max_cost_usd", 5.00)
    object.__setattr__(cfg, "default_service_tier", "flex")
    object.__setattr__(cfg, "enable_cached_input", True)
    object.__setattr__(cfg, "disabled_providers", ())
    return cfg


def _first_route(lane: str, tier: str) -> tuple[str, str, str]:
    ladder = runner.derive_ladder_for_cell("economy", lane, tier)
    assert len(ladder) == 1
    return ladder[0]


def test_economy_profile_sets_flex_and_five_dollar_default_cap() -> None:
    profile = runner.COST_PROFILES["economy"]

    assert profile["routing_policy"] == "cost"
    assert profile["default_service_tier"] == "flex"
    assert profile["max_cost_usd_default"] == 5.00
    assert profile["escalation_max_hops"] == 1


def test_economy_ce_medium_uses_codex_mini_route() -> None:
    assert _first_route("CE", "medium") == (
        "openrouter",
        "openai/gpt-5.1-codex-mini",
        "OPENROUTER_API_KEY",
    )


def test_economy_synth_high_uses_haiku_4_5() -> None:
    assert _first_route("SYNTH", "high") == (
        "openrouter",
        "anthropic/claude-haiku-4.5",
        "OPENROUTER_API_KEY",
    )


def test_economy_synth_critical_uses_sonnet_4_5() -> None:
    assert _first_route("SYNTH", "critical") == (
        "openrouter",
        "anthropic/claude-sonnet-4.5",
        "OPENROUTER_API_KEY",
    )


def test_economy_bulk_extract_uses_mini_alias() -> None:
    assert _first_route("BULK", "extract") == (
        "openrouter",
        "openai/gpt-5.4-mini",
        "OPENROUTER_API_KEY",
    )


def test_economy_route_service_tier_falls_back_to_profile_flex(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)

    assert runner._route_service_tier_for_execution({}, cfg) == "flex"


def test_economy_flex_spend_halves_openai_cost(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)

    priced = runner._pricing_preview(
        cfg,
        provider="openai",
        model_id="gpt-5.4",
        input_tokens=1_000_000,
        output_tokens=100_000,
        execution_mode="sync",
        service_tier="flex",
    )

    assert priced is not None
    assert priced["estimated_cost_usd"] == pytest.approx(2.0)
    assert priced["cost_breakdown"]["tier_multiplier"] == 0.5


def test_economy_preventive_cap_blocks_before_expensive_call() -> None:
    rate = get_model_cost_rate(provider="openai", model_id="gpt-5.4")
    check = make_projected_cost_check(
        rate=rate,
        current_total_cost_usd=4.80,
        max_cost_usd=5.00,
    )

    assert check(input_tokens=10_000, output_tokens=5_000, service_tier="flex") is True
    assert check(input_tokens=200_000, output_tokens=50_000, service_tier="flex") is False


def test_economy_cli_applies_default_cost_cap_when_omitted(tmp_path: Path) -> None:
    env = {**os.environ, "RTE_DISABLE_LIVE_LLM_IN_TESTS": "1"}
    result = subprocess.run(
        [
            sys.executable,
            str(SERVICE_ROOT / "run_extraction_v5.py"),
            "--phase",
            "A",
            "--run-id",
            "e9_economy_cli",
            "--output-root",
            str(tmp_path),
            "--cost-profile",
            "economy",
            "--print-config",
        ],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Applied cost-profile default --max-cost-usd=5.00" in result.stderr
    payload = json.loads(result.stdout[result.stdout.find("{"):])
    assert payload["cli"]["routing_policy"] == "cost"
