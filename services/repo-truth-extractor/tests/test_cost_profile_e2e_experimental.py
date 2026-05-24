"""E9 experimental cost-profile integration coverage."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = ROOT / "services" / "repo-truth-extractor"
FIXTURE_ROOT = SERVICE_ROOT / "tests" / "fixtures"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

import run_extraction_v5 as runner  # noqa: E402


def _minimal_model_map() -> dict:
    return yaml.safe_load((FIXTURE_ROOT / "model_map_v3_minimal.yaml").read_text())


def test_experimental_profile_sets_bleed_edge_notes_warning_and_cap() -> None:
    profile = runner.COST_PROFILES["experimental"]

    assert profile["routing_policy"] == "optimal"
    assert profile["default_service_tier"] == "default"
    assert profile["enable_batch_when_supported"] is False
    assert profile["max_cost_usd_default"] == 25.00
    assert "Bleed-edge frontier models" in profile["notes"]
    assert "Not for production" in profile["warning"]


def test_experimental_notes_name_frontier_model_families() -> None:
    notes = runner.COST_PROFILES["experimental"]["notes"]

    assert "gpt-5.5-pro" in notes
    assert "claude-opus-4.7" in notes
    assert "gemini-3.5-flash" in notes


def test_experimental_ce_medium_alias_uses_gpt_5_5() -> None:
    assert runner.derive_ladder_for_cell("experimental", "CE", "medium") == [
        ("openrouter", "openai/gpt-5.5", "OPENROUTER_API_KEY")
    ]


def test_experimental_synth_high_alias_uses_opus_4_7() -> None:
    assert runner.derive_ladder_for_cell("experimental", "SYNTH", "high") == [
        ("openrouter", "anthropic/claude-opus-4.7", "OPENROUTER_API_KEY")
    ]


def test_experimental_synth_critical_alias_uses_opus_4_7() -> None:
    assert runner.derive_ladder_for_cell("experimental", "SYNTH", "critical") == [
        ("openrouter", "anthropic/claude-opus-4.7", "OPENROUTER_API_KEY")
    ]


def test_experimental_fixture_contains_gpt_5_5_pro_and_gemini_flash_routes() -> None:
    lane = _minimal_model_map()["lane_defaults"]["experimental"]["EXTRACT"]["high"]
    models = {row["model_id"] for row in lane["primary_routes"]}

    assert "gpt-5.5-pro" in models
    assert "gemini-3.5-flash" in models


def test_experimental_fixture_step_preserves_service_tier_and_cache_strategy() -> None:
    rows = [
        row
        for row in _minimal_model_map()["steps"]
        if row["phase"] == "X" and row["step_id"] == "X1"
    ]

    assert len(rows) == 1
    first_route = rows[0]["primary_routes"][0]
    assert first_route["model_id"] == "gpt-5.5-pro"
    assert first_route["service_tier"] == "default"
    assert first_route["cache_strategy"] == "auto"
