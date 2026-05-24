"""E9 batch-discount integration coverage."""

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
from lib.batch_clients import (  # noqa: E402
    BATCH_STATIC_PROOF_MARKERS,
    BatchRequest,
    BatchRoute,
    OpenRouterBatchClient,
    UnsupportedBatchProvider,
    build_openai_compatible_batch_static_proof,
)
from lib.spend_ledger import SpendLedger  # noqa: E402


def _cfg(tmp_path: Path) -> Any:
    cfg = runner.RunnerConfig.__new__(runner.RunnerConfig)
    object.__setattr__(cfg, "ledger", SpendLedger(tmp_path, "e9_batch"))
    object.__setattr__(cfg, "max_cost_usd", None)
    object.__setattr__(cfg, "default_service_tier", "default")
    object.__setattr__(cfg, "enable_cached_input", True)
    return cfg


def test_batch_reserved_spend_is_half_standard_cost(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)

    reserved = runner._reserve_projected_spend(
        cfg,
        phase="A",
        step_id="A2",
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
    assert reserved["cost_breakdown"]["batch_multiplier"] == 0.5


def test_runtime_batch_spend_is_half_standard_cost(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)

    priced = runner._accumulate_runtime_spend(
        cfg,
        phase="A",
        step_id="A2",
        partition_id="A_P0001",
        provider="openai",
        model_id="gpt-5.4",
        execution_mode="batch",
        response_summary={"usage": {"input_tokens": 1_000_000, "output_tokens": 100_000}},
        response_text="{}",
        route="openai/gpt-5.4",
    )

    assert priced is not None
    assert priced["estimated_cost_usd"] == pytest.approx(2.0)
    assert priced["cost_breakdown"]["is_batch"] is True


def test_route_metadata_triggers_batch_service_tier_and_cache_flags(
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
        system_prompt="stable system prefix",
        user_content="mutable request",
    )

    assert metadata["service_tier"] == "flex"
    assert metadata["cache_strategy"] == "auto"
    assert metadata["cache_strategy_applied"] == "true"


def test_build_v5_batch_request_preserves_optimizer_metadata() -> None:
    request = runner.build_v5_batch_request(
        custom_id="A_P0001",
        model_id="gpt-5.4",
        system_prompt="system",
        user_content="user",
        provider="openai",
        selected_route=("openai", "gpt-5.4", "OPENAI_API_KEY"),
        selected_route_entry=None,
        transport="openai_sdk",
        strict_contract_required=False,
        step_contract=None,
        artifact_names=(),
        force_json_output=True,
        metadata={
            "phase": "A",
            "step_id": "A2",
            "service_tier": "flex",
            "cache_strategy": "auto",
            "cache_strategy_applied": "true",
        },
    )

    assert request.metadata["service_tier"] == "flex"
    assert request.metadata["cache_strategy"] == "auto"
    assert request.force_json_output is True


def test_openrouter_batch_remains_unsupported_without_provider_call() -> None:
    client = object.__new__(OpenRouterBatchClient)

    with pytest.raises(UnsupportedBatchProvider, match="OpenRouter is not supported"):
        client.submit(
            [
                BatchRequest(
                    custom_id="A_P0001",
                    model_id="openai/gpt-5.4",
                    system_prompt="system",
                    user_content="user",
                )
            ],
            BatchRoute(
                provider="openrouter",
                model_id="openai/gpt-5.4",
                api_key_env="OPENROUTER_API_KEY",
            ),
            {"phase": "A", "step_id": "A2"},
        )


def test_xai_batch_static_proof_warns_operator_until_live_verified() -> None:
    proof = build_openai_compatible_batch_static_proof(
        request_custom_ids=["X_P0001"],
        output_rows=[{"custom_id": "X_P0001"}],
        error_rows=[],
        batch_info={"id": "batch-xai", "status": "completed"},
        provider="xai",
        requested_provider="xai",
        requested_model_id="grok-4.20-beta-0309-non-reasoning",
    )

    assert proof["not_live_validated"] is True
    assert "NOT_LIVE_VALIDATED" in proof["markers"]
    assert set(BATCH_STATIC_PROOF_MARKERS).issubset(set(proof["markers"]))
