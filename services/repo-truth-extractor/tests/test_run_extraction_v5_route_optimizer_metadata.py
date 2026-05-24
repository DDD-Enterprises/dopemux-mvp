"""Route optimizer metadata must reach the v5 runtime.

E9 is test-only, but pre-E9 tracing found that ``model_map.yaml`` v3 route
metadata stopped before ``run_extraction_v5`` called the LLM runtime. These
tests cover the prerequisite production boundary: route ``service_tier`` and
``cache_strategy`` must flow into request kwargs, cost projections, runtime
spend accounting, and batch metadata.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict

import pytest


ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = ROOT / "services" / "repo-truth-extractor"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

import run_extraction_v5 as runner  # noqa: E402
from lib.spend_ledger import SpendLedger  # noqa: E402
from lib.structured_output_contracts import route_entries_for_stage  # noqa: E402


def _cfg(tmp_path: Path, *, default_service_tier: str = "default") -> Any:
    cfg = runner.RunnerConfig.__new__(runner.RunnerConfig)
    object.__setattr__(cfg, "ledger", SpendLedger(tmp_path, "route_optimizer"))
    object.__setattr__(cfg, "max_cost_usd", None)
    object.__setattr__(cfg, "default_service_tier", default_service_tier)
    object.__setattr__(cfg, "enable_cached_input", True)
    object.__setattr__(cfg, "disabled_providers", ())
    return cfg


def test_route_entries_preserve_cache_strategy_for_runtime_consumers() -> None:
    contract = {
        "phase": "S",
        "step_id": "S1",
        "lane": {
            "primary_routes": [
                {
                    "provider": "openrouter",
                    "model_id": "anthropic/claude-opus-4.6",
                    "api_key_env": "OPENROUTER_API_KEY",
                    "cache_strategy": " cache_control_explicit ",
                },
                {
                    "provider": "openai",
                    "model_id": "gpt-5.4",
                    "api_key_env": "OPENAI_API_KEY",
                },
            ]
        },
    }

    rows = route_entries_for_stage(contract, "primary")

    assert rows[0]["cache_strategy"] == "cache_control_explicit"
    assert rows[1]["cache_strategy"] is None


def test_call_llm_wrapper_forwards_optimizer_kwargs_to_runtime(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: Dict[str, Any] = {}

    def fake_runtime_call_llm(_deps: Any, *_args: Any, **kwargs: Any) -> Dict[str, Any]:
        captured.update(kwargs)
        return {"ok": True, "text": "{}", "meta": {}}

    monkeypatch.setattr(runner, "llm_runtime_call_llm", fake_runtime_call_llm)

    result = runner.call_llm(
        provider="openai",
        model_id="gpt-5.4",
        api_key_env="OPENAI_API_KEY",
        system_prompt="system",
        user_content="user",
        cfg=SimpleNamespace(),
        service_tier="flex",
        prompt_cache_directives={"applied": True, "strategy": "auto"},
        disabled_providers={"openrouter"},
    )

    assert result["ok"] is True
    assert captured["service_tier"] == "flex"
    assert captured["prompt_cache_directives"] == {"applied": True, "strategy": "auto"}
    assert captured["disabled_providers"] == {"openrouter"}


def test_route_service_tier_prefers_route_entry_over_profile_default(
    tmp_path: Path,
) -> None:
    cfg = _cfg(tmp_path, default_service_tier="priority")

    assert (
        runner._route_service_tier_for_execution(
            {"service_tier": " flex "},
            cfg,
        )
        == "flex"
    )
    assert (
        runner._route_service_tier_for_execution(
            {"service_tier": None},
            cfg,
        )
        == "priority"
    )


def test_route_prompt_cache_directives_use_route_cache_strategy(
    tmp_path: Path,
) -> None:
    cfg = _cfg(tmp_path)

    directives = runner._route_prompt_cache_directives_for_execution(
        {
            "provider": "openrouter",
            "model_id": "anthropic/claude-opus-4.6",
            "cache_strategy": "cache_control_explicit",
        },
        cfg,
        system_prompt="stable system prefix",
        user_content="mutable user request",
    )

    assert directives["applied"] is True
    assert directives["strategy"] == "cache_control_explicit"
    assert directives["cache_control_markers"]


def test_pricing_preview_accepts_route_service_tier(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path, default_service_tier="default")

    priced = runner._pricing_preview(
        cfg,
        provider="openai",
        model_id="gpt-5.4",
        input_tokens=1_000_000,
        output_tokens=100_000,
        execution_mode="sync",
        route="openai/gpt-5.4",
        service_tier="flex",
    )

    assert priced is not None
    assert priced["estimated_cost_usd"] == pytest.approx(2.0)
    assert priced["cost_breakdown"]["service_tier"] == "flex"


def test_accumulate_runtime_spend_accepts_route_service_tier_when_not_echoed(
    tmp_path: Path,
) -> None:
    cfg = _cfg(tmp_path, default_service_tier="default")

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


def test_route_optimizer_metadata_builds_string_batch_metadata(
    tmp_path: Path,
) -> None:
    cfg = _cfg(tmp_path)

    metadata = runner._route_optimizer_batch_metadata(
        {
            "provider": "openai",
            "model_id": "gpt-5.4",
            "service_tier": "flex",
            "cache_strategy": "auto",
        },
        cfg,
        system_prompt="system",
        user_content="user",
    )

    assert metadata["service_tier"] == "flex"
    assert metadata["cache_strategy"] == "auto"
    assert metadata["cache_strategy_applied"] == "true"
