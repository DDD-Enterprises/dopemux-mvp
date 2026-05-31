from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.registry.openrouter_discovery import (
    LIVE_FETCH_ENV,
    OpenRouterMetadataError,
    build_openrouter_discovery_snapshot,
    classify_openrouter_model,
    fetch_openrouter_models_live,
    stable_snapshot_json,
)


FIXTURE_PATH = (
    Path(__file__).resolve().parent / "fixtures" / "openrouter_models_sample.json"
)


def _fixture_payload() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_direct_overlap_models_are_excluded() -> None:
    rows = {
        "openai": classify_openrouter_model({"id": "openai/gpt-4o-mini"}),
        "gemini": classify_openrouter_model({"id": "google/gemini-2.5-pro"}),
        "anthropic": classify_openrouter_model({"id": "anthropic/claude-sonnet-4.5"}),
        "xai": classify_openrouter_model({"id": "x-ai/grok-4"}),
        "mistral": classify_openrouter_model({"id": "mistralai/mistral-large"}),
    }

    assert {row["classification_label"] for row in rows.values()} == {
        "DIRECT_OVERLAP_EXCLUDE"
    }
    assert rows["openai"]["direct_overlap_status"] == "DIRECT_OVERLAP"
    assert rows["gemini"]["vendor"] == "Google Gemini"
    assert rows["anthropic"]["benchmark_priority"] == "LOW"


def test_direct_overlap_exception_requires_explicit_or_advantage_reason() -> None:
    default_row = classify_openrouter_model({"id": "deepseek/deepseek-chat"})
    weak_exception_row = classify_openrouter_model(
        {"id": "deepseek/deepseek-chat"},
        or_advantage_reasons={"deepseek/deepseek-chat": "repo preference only"},
    )
    exception_row = classify_openrouter_model(
        {"id": "deepseek/deepseek-chat"},
        or_advantage_reasons={
            "deepseek/deepseek-chat": "OpenRouter provider fallback and route telemetry must be benchmarked before route-profile admission."
        },
    )

    assert default_row["classification_label"] == "BENCHMARK_ONLY"
    assert weak_exception_row["classification_label"] == "BENCHMARK_ONLY"
    assert exception_row["classification_label"] == "DIRECT_OVERLAP_EXCEPTION"
    assert exception_row["direct_overlap_status"] == "DIRECT_OVERLAP_EXCEPTION"
    assert any(
        "provider fallback and route telemetry" in reason
        for reason in exception_row["classification_reasons"]
    )


def test_free_routes_are_experimental_and_preserve_privacy_warning() -> None:
    pinned_free = classify_openrouter_model({"id": "qwen/qwen3-coder:free"})
    native_free = classify_openrouter_model(
        {
            "id": "openrouter/owl-alpha",
            "description": "Prompts and outputs are logged by the provider.",
            "pricing": {"prompt": "0", "completion": "0", "request": "0"},
        }
    )

    assert pinned_free["classification_label"] == "FREE_EXPERIMENTAL"
    assert pinned_free["free_or_paid"] == "FREE"
    assert native_free["classification_label"] == "FREE_EXPERIMENTAL"
    assert native_free["privacy_warning"] == "PROVIDER_LOGGING_INDICATED"


def test_hosted_open_weight_candidate_is_admitted_for_benchmarking() -> None:
    row = classify_openrouter_model(
        {
            "id": "qwen/qwen3-coder",
            "supported_parameters": ["max_tokens", "structured_outputs"],
            "context_length": 262144,
            "top_provider": {"context_length": 262144},
        }
    )

    assert row["classification_label"] == "OPENROUTER_VALUE_CANDIDATE"
    assert row["structured_output_support"] == "SUPPORTED"
    assert row["benchmark_priority"] == "HIGH"
    assert row["top_provider_context_length"] == 262144


def test_unknown_and_malformed_metadata_fail_closed() -> None:
    unknown = classify_openrouter_model({"id": "unknown-lab/unknown-model"})

    assert unknown["classification_label"] == "BENCHMARK_ONLY"
    assert unknown["context_length"] == "UNKNOWN"
    assert unknown["supported_parameters"] == "UNKNOWN"
    assert unknown["structured_output_support"] == "UNKNOWN"

    with pytest.raises(OpenRouterMetadataError):
        classify_openrouter_model({"name": "missing id"})

    with pytest.raises(OpenRouterMetadataError):
        build_openrouter_discovery_snapshot({"data": [{"id": "bad", "pricing": []}]})

    with pytest.raises(OpenRouterMetadataError):
        build_openrouter_discovery_snapshot(
            {"data": [{"id": "bad", "pricing": {"prompt": []}}]}
        )


def test_no_secret_or_auth_header_appears_in_output() -> None:
    fake_secret = "sk" + "-or-v1-" + "secretvalue0123456789"
    fake_bearer = "Bearer " + fake_secret
    row = classify_openrouter_model(
        {
            "id": "qwen/qwen3-coder",
            "name": fake_bearer,
            "headers": {"Authorization": fake_bearer},
            "pricing": {"prompt": "0.1", "completion": "0.2"},
            "supported_parameters": ["structured_outputs"],
        }
    )
    encoded = stable_snapshot_json({"models": [row]})

    assert "sk" + "-or-" not in encoded
    assert "Authorization" not in encoded
    assert "Bearer " not in encoded
    assert "[REDACTED]" in encoded


def test_live_fetch_requires_explicit_opt_in(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(LIVE_FETCH_ENV, raising=False)

    with pytest.raises(OpenRouterMetadataError, match=LIVE_FETCH_ENV):
        fetch_openrouter_models_live(timeout_seconds=0.001)


def test_fixture_metadata_produces_deterministic_sorted_output() -> None:
    snapshot_one = build_openrouter_discovery_snapshot(
        _fixture_payload(),
        source_ref="fixture:openrouter_models_sample.json",
        generated_at="UNKNOWN",
        or_advantage_reasons={
            "deepseek/deepseek-chat": "OpenRouter provider fallback and route telemetry must be benchmarked before route-profile admission."
        },
    )
    snapshot_two = build_openrouter_discovery_snapshot(
        _fixture_payload(),
        source_ref="fixture:openrouter_models_sample.json",
        generated_at="UNKNOWN",
        or_advantage_reasons={
            "deepseek/deepseek-chat": "OpenRouter provider fallback and route telemetry must be benchmarked before route-profile admission."
        },
    )

    assert stable_snapshot_json(snapshot_one) == stable_snapshot_json(snapshot_two)
    model_ids = [row["id"] for row in snapshot_one["models"]]
    assert model_ids == sorted(model_ids)
    assert snapshot_one["classification_counts"] == {
        "BENCHMARK_ONLY": 2,
        "DIRECT_OVERLAP_EXCEPTION": 1,
        "DIRECT_OVERLAP_EXCLUDE": 5,
        "FREE_EXPERIMENTAL": 2,
        "OPENROUTER_VALUE_CANDIDATE": 1,
    }
