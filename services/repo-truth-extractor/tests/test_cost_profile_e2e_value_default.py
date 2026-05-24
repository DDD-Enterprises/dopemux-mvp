"""E9 value-default cost-profile integration coverage.

The tests stay test-only and exercise the runtime seams that carry
cost_profile, cell aliases, v3 route optimizer metadata, call_llm kwargs, and
spend-ledger pricing.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = ROOT / "services" / "repo-truth-extractor"
FIXTURE_ROOT = SERVICE_ROOT / "tests" / "fixtures"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

import run_extraction_v5 as runner  # noqa: E402
from lib.spend_ledger import SpendLedger  # noqa: E402
from lib.structured_output_contracts import route_entries_for_stage  # noqa: E402


def _cfg(tmp_path: Path, *, default_service_tier: str = "default") -> Any:
    cfg = runner.RunnerConfig.__new__(runner.RunnerConfig)
    object.__setattr__(cfg, "ledger", SpendLedger(tmp_path, "e9_value_default"))
    object.__setattr__(cfg, "max_cost_usd", None)
    object.__setattr__(cfg, "default_service_tier", default_service_tier)
    object.__setattr__(cfg, "enable_cached_input", True)
    object.__setattr__(cfg, "disabled_providers", ())
    object.__setattr__(cfg, "cost_profile", "value-default")
    object.__setattr__(
        cfg,
        "cost_profile_notes",
        runner.COST_PROFILES["value-default"]["notes"],
    )
    return cfg


def _first_route(profile: str, lane: str, tier: str) -> tuple[str, str, str]:
    ladder = runner.derive_ladder_for_cell(profile, lane, tier)
    assert len(ladder) == 1
    return ladder[0]


def _fixture_step(step_id: str) -> Dict[str, Any]:
    payload = yaml.safe_load((FIXTURE_ROOT / "model_map_v3_minimal.yaml").read_text())
    for row in payload["steps"]:
        if row["step_id"] == step_id:
            return {"lane": row}
    raise AssertionError(f"missing fixture step {step_id}")


def test_value_default_profile_is_default_operator_profile() -> None:
    name, profile = runner.resolve_cost_profile(None)

    assert name == "value-default"
    assert profile["routing_policy"] == "balanced_openrouter"
    assert profile["default_service_tier"] == "default"
    assert profile["enable_cached_input"] is True
    assert profile["enable_batch_when_supported"] is True


def test_value_default_ce_medium_cell_alias_routes_through_openrouter() -> None:
    assert _first_route("value-default", "CE", "medium") == (
        "openrouter",
        "openai/gpt-5.3-codex",
        "OPENROUTER_API_KEY",
    )


def test_value_default_ce_high_cell_alias_routes_through_openrouter() -> None:
    assert _first_route("value-default", "CE", "high") == (
        "openrouter",
        "openai/gpt-5.4",
        "OPENROUTER_API_KEY",
    )


def test_value_default_synth_high_uses_sonnet_4_6_via_openrouter() -> None:
    assert _first_route("value-default", "SYNTH", "high") == (
        "openrouter",
        "anthropic/claude-sonnet-4.6",
        "OPENROUTER_API_KEY",
    )


def test_value_default_synth_critical_uses_opus_4_6_via_openrouter() -> None:
    assert _first_route("value-default", "SYNTH", "critical") == (
        "openrouter",
        "anthropic/claude-opus-4.6",
        "OPENROUTER_API_KEY",
    )


def test_value_default_bulk_extract_alias_resolves_to_mini_openrouter_route() -> None:
    assert _first_route("value-default", "BULK", "extract") == (
        "openrouter",
        "openai/gpt-5.4-mini",
        "OPENROUTER_API_KEY",
    )


def test_value_default_fixture_preserves_v3_route_optimizer_metadata() -> None:
    rows = route_entries_for_stage(_fixture_step("A2"), "primary")

    assert rows == [
        {
            "provider": "openai",
            "model_id": "gpt-5.4-mini",
            "api_key_env": "OPENAI_API_KEY",
            "structured_output_mode": "none",
            "strict_json_schema": False,
            "strict_passthrough_verified": False,
            "service_tier": "flex",
            "cache_strategy": "auto",
        }
    ]


def test_value_default_long_context_tag_delta_preserves_impact_class_fail_closed() -> None:
    rows = route_entries_for_stage(_fixture_step("S1"), "primary")

    assert rows
    assert rows[0]["provider"] == "gemini"
    assert rows[0]["model_id"] == "gemini-3.5-flash"
    assert rows[0]["context_window"] == 1_000_000


def test_value_default_call_llm_receives_service_tier_and_cache_directives(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: Dict[str, Any] = {}

    def fake_runtime_call_llm(_deps: Any, *_args: Any, **kwargs: Any) -> Dict[str, Any]:
        captured.update(kwargs)
        return {"ok": True, "text": "{}", "meta": {}}

    monkeypatch.setattr(runner, "llm_runtime_call_llm", fake_runtime_call_llm)

    result = runner.call_llm(
        provider="openai",
        model_id="gpt-5.4-mini",
        api_key_env="OPENAI_API_KEY",
        system_prompt="system",
        user_content="user",
        cfg=SimpleNamespace(),
        service_tier="flex",
        prompt_cache_directives={"applied": True, "strategy": "auto"},
        disabled_providers={"gemini"},
    )

    assert result["ok"] is True
    assert captured["service_tier"] == "flex"
    assert captured["prompt_cache_directives"]["strategy"] == "auto"
    assert captured["disabled_providers"] == {"gemini"}


def test_value_default_cached_flex_spend_matches_expected_dollars(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)

    priced = runner._accumulate_runtime_spend(
        cfg,
        phase="A",
        step_id="A2",
        partition_id="A_P0001",
        provider="openai",
        model_id="gpt-5.4",
        execution_mode="sync",
        response_summary={
            "usage": {
                "input_tokens": 1_000_000,
                "output_tokens": 100_000,
                "cached_tokens": 500_000,
            }
        },
        response_text="{}",
        route="openai/gpt-5.4",
        service_tier="flex",
    )

    assert priced is not None
    assert priced["estimated_cost_usd"] == pytest.approx(1.4375)
    assert priced["cost_breakdown"]["service_tier"] == "flex"
    assert priced["cost_breakdown"]["cached_input_tokens"] == 500_000

    ledger = json.loads((tmp_path / "spend_ledger.json").read_text())
    assert ledger["run_id"] == "e9_value_default"
    assert ledger["total_cost_usd"] == pytest.approx(1.4375)


def test_value_default_cfg_carries_profile_name_for_proof_payloads(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)

    proof_payload = {
        "run_id": "e9_value_default",
        "cost_profile": cfg.cost_profile,
        "cost_profile_notes": cfg.cost_profile_notes,
    }

    assert proof_payload["cost_profile"] == "value-default"
    assert "NEW DEFAULT" in proof_payload["cost_profile_notes"]
