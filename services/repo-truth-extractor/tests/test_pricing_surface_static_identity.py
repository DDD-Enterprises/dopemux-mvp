from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _v5_smoke_helpers import load_runner_module


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from lib.pricing_surface import pricing_surface_matrix_rows, pricing_surface_metadata
from lib.spend_ledger import SpendLedger


def _no_provider_call(*_args: Any, **_kwargs: Any) -> Any:
    raise AssertionError("pricing-surface static tests must not invoke provider clients")


def _static_route(provider: str, model_id: str, api_key_env: str) -> dict[str, Any]:
    runner = load_runner_module()
    endpoint_base = (
        "https://openrouter.ai/api/v1"
        if provider == "openrouter"
        else (
            "https://api.x.ai/v1"
            if provider == "xai"
            else f"https://api.{provider}.example/v1"
        )
    )
    return runner.build_static_route_fingerprint_metadata(
        provider=provider,
        model_id=model_id,
        api_key_env=api_key_env,
        endpoint_base_url=endpoint_base,
        endpoint_url=f"{endpoint_base}/chat/completions",
        transport="openai_sdk",
        structured_output_mode="json_schema",
    )


def test_direct_xai_pricing_surface_is_xai_direct() -> None:
    route = _static_route("xai", "grok-fixture", "XAI_API_KEY")

    assert route["provider_route_kind"] == "direct_provider"
    assert route["upstream_provider"] == "xai"
    assert route["economic_surface"] == "xai_direct"
    assert route["pricing_surface"] == "xai_direct"
    assert route["pricing_authority"] == "direct_provider_catalog_or_unknown"
    assert route["api_key_env"] == "XAI_API_KEY"
    assert route["direct_provider_billing_inherited"] is None
    assert route["pricing_live_validation_status"] == "LIVE_VALIDATION_REQUIRED"


def test_openrouter_xai_pricing_surface_is_openrouter_not_xai_direct() -> None:
    route = _static_route("openrouter", "x-ai/grok-fixture", "OPENROUTER_API_KEY")

    assert route["provider_route_kind"] == "openrouter_proxy_xai"
    assert route["upstream_provider"] == "xai"
    assert route["economic_surface"] == "openrouter"
    assert route["pricing_surface"] == "openrouter"
    assert route["pricing_authority"] == "openrouter_catalog_or_unknown"
    assert route["api_key_env"] == "OPENROUTER_API_KEY"
    assert route["direct_provider_billing_inherited"] is False
    assert route["pricing_live_validation_status"] == "LIVE_VALIDATION_REQUIRED"
    assert route["pricing_surface"] != "xai_direct"


def test_openrouter_xai_pricing_proof_differs_from_direct_xai() -> None:
    direct = _static_route("xai", "grok-fixture", "XAI_API_KEY")
    proxied = _static_route("openrouter", "x-ai/grok-fixture", "OPENROUTER_API_KEY")

    assert direct["upstream_provider"] == proxied["upstream_provider"] == "xai"
    assert direct["pricing_surface"] != proxied["pricing_surface"]
    assert direct["economic_surface"] != proxied["economic_surface"]
    assert direct["api_key_env"] != proxied["api_key_env"]
    assert direct["provider_route_kind"] != proxied["provider_route_kind"]
    assert direct["provider_signature"] != proxied["provider_signature"]
    assert direct["route_fingerprint_hash"] != proxied["route_fingerprint_hash"]


def test_spend_ledger_rows_preserve_pricing_surface(tmp_path: Path) -> None:
    ledger = SpendLedger(tmp_path, "pricing_surface_static")

    openrouter_spend = ledger.accumulate(
        "A",
        100,
        50,
        provider="openrouter",
        model_id="x-ai/grok-4.1-fast",
        route="openrouter/x-ai/grok-4.1-fast",
    )
    direct_xai_spend = ledger.accumulate(
        "A",
        100,
        50,
        provider="xai",
        model_id="grok-4.20",
        route="xai/grok-4.20",
    )

    assert openrouter_spend["economic_surface"] == "openrouter"
    assert openrouter_spend["pricing_surface"] == "openrouter"
    assert openrouter_spend["direct_provider_billing_inherited"] is False
    assert direct_xai_spend["economic_surface"] == "xai_direct"
    assert direct_xai_spend["pricing_surface"] == "xai_direct"
    assert direct_xai_spend["direct_provider_billing_inherited"] is None

    payload = json.loads((tmp_path / "spend_ledger.json").read_text(encoding="utf-8"))
    openrouter_row = payload["models"]["openrouter/x-ai/grok-4.1-fast"]
    direct_xai_row = payload["models"]["xai/grok-4.20"]
    assert openrouter_row["pricing_surface"] == "openrouter"
    assert openrouter_row["economic_surface"] == "openrouter"
    assert openrouter_row["upstream_provider"] == "xai"
    assert openrouter_row["direct_provider_billing_inherited"] is False
    assert direct_xai_row["pricing_surface"] == "xai_direct"
    assert direct_xai_row["economic_surface"] == "xai_direct"


def test_pricing_surface_matrix_covers_required_static_cases() -> None:
    rows = pricing_surface_matrix_rows()
    by_label = {row["label"]: row for row in rows}

    assert set(by_label) == {
        "Direct xAI",
        "OpenRouter x-ai",
        "OpenRouter OpenAI",
        "OpenRouter unknown/native",
        "Direct OpenAI",
        "Direct Gemini",
        "Unknown provider",
    }
    assert by_label["Direct xAI"]["pricing_surface"] == "xai_direct"
    assert by_label["OpenRouter x-ai"]["pricing_surface"] == "openrouter"
    assert by_label["OpenRouter x-ai"]["direct_provider_billing_inherited"] is False
    assert by_label["OpenRouter OpenAI"]["upstream_provider"] == "openai"
    assert by_label["OpenRouter OpenAI"]["billing_authority"] == "openrouter_catalog_or_unknown"
    assert by_label["OpenRouter unknown/native"]["provider_route_kind"] == (
        "openrouter_native_or_unknown"
    )
    assert by_label["OpenRouter unknown/native"]["pricing_surface"] == "openrouter"
    assert by_label["Direct OpenAI"]["pricing_surface"] == "openai_direct"
    assert by_label["Direct Gemini"]["pricing_surface"] == "gemini_direct"
    assert by_label["Unknown provider"]["pricing_surface"] == "unknown"
    assert by_label["Unknown provider"]["billing_authority"] == "unknown"


def test_static_pricing_visibility_does_not_call_provider_clients(
    monkeypatch: Any,
) -> None:
    runner = load_runner_module()
    for attr in (
        "get_http_session",
        "get_gemini_client",
        "get_xai_client",
        "get_openrouter_client",
        "get_openai_client",
    ):
        monkeypatch.setattr(runner, attr, _no_provider_call, raising=False)

    route = runner.build_static_route_fingerprint_metadata(
        provider="openrouter",
        model_id="x-ai/grok-fixture",
        api_key_env="OPENROUTER_API_KEY",
        endpoint_base_url="https://openrouter.ai/api/v1",
        endpoint_url="https://openrouter.ai/api/v1/chat/completions",
        transport="openai_sdk",
        structured_output_mode="json_schema",
    )
    pricing = pricing_surface_metadata(route_identity=route)

    assert pricing["pricing_surface"] == "openrouter"
    assert pricing["direct_provider_billing_inherited"] is False
