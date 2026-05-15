from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _v5_smoke_helpers import load_runner_module, make_cfg


def _no_provider_call(*_args: Any, **_kwargs: Any) -> Any:
    raise AssertionError("route fingerprint tests must not invoke provider clients")


def _direct_xai_fingerprint() -> dict[str, Any]:
    runner = load_runner_module()
    return runner.build_static_route_fingerprint_metadata(
        provider="xai",
        model_id="grok-fixture",
        api_key_env="XAI_API_KEY",
        endpoint_base_url="https://api.x.ai/v1",
        endpoint_url="https://api.x.ai/v1/chat/completions",
        transport="openai_sdk",
        structured_output_mode="json_schema",
    )


def _openrouter_xai_fingerprint() -> dict[str, Any]:
    runner = load_runner_module()
    return runner.build_static_route_fingerprint_metadata(
        provider="openrouter",
        model_id="x-ai/grok-fixture",
        api_key_env="OPENROUTER_API_KEY",
        endpoint_base_url="https://openrouter.ai/api/v1",
        endpoint_url="https://openrouter.ai/api/v1/chat/completions",
        transport="openai_sdk",
        structured_output_mode="json_schema",
    )


def test_direct_xai_route_fingerprint_records_direct_identity() -> None:
    route = _direct_xai_fingerprint()

    assert route["requested_provider"] == "xai"
    assert route["requested_model_id"] == "grok-fixture"
    assert route["provider_route_kind"] == "direct_provider"
    assert route["upstream_provider"] == "xai"
    assert route["economic_surface"] == "xai_direct"
    assert route["api_key_env"] == "XAI_API_KEY"
    assert route["endpoint_base_url"] == "https://api.x.ai/v1"
    assert route["endpoint_effective"] == "https://api.x.ai/v1/chat/completions"
    assert route["transport"] == "openai_sdk"
    assert route["structured_output_mode"] == "json_schema"
    assert route["provider_schema_variant"] == "xai_relaxed_direct"
    assert route["live_validation_status"] == "LIVE_VALIDATION_REQUIRED"
    assert route["fingerprint_authority"] == "static_request_route_metadata"
    assert route["live_provider_behavior_proven"] is False
    assert route["route_fingerprint_material"]["economic_surface"] == "xai_direct"


def test_openrouter_xai_route_fingerprint_records_proxy_identity() -> None:
    route = _openrouter_xai_fingerprint()

    assert route["requested_provider"] == "openrouter"
    assert route["requested_model_id"] == "x-ai/grok-fixture"
    assert route["provider_route_kind"] == "openrouter_proxy_xai"
    assert route["upstream_provider"] == "xai"
    assert route["economic_surface"] == "openrouter"
    assert route["api_key_env"] == "OPENROUTER_API_KEY"
    assert route["endpoint_base_url"] == "https://openrouter.ai/api/v1"
    assert route["endpoint_effective"] == "https://openrouter.ai/api/v1/chat/completions"
    assert route["transport"] == "openai_sdk"
    assert route["structured_output_mode"] == "json_schema"
    assert route["provider_schema_variant"] == "openrouter_proxy_xai_relaxed"
    assert route["direct_provider_guarantees_inherited"] is False
    assert route["live_validation_status"] == "LIVE_VALIDATION_REQUIRED"
    assert route["fingerprint_authority"] == "static_request_route_metadata"
    assert route["live_provider_behavior_proven"] is False
    assert route["route_fingerprint_material"]["economic_surface"] == "openrouter"


def test_openrouter_xai_fingerprint_differs_from_direct_xai() -> None:
    direct = _direct_xai_fingerprint()
    proxied = _openrouter_xai_fingerprint()

    assert direct["upstream_provider"] == proxied["upstream_provider"] == "xai"
    assert direct["route_fingerprint_hash"] != proxied["route_fingerprint_hash"]
    assert direct["route_fingerprint_material"] != proxied["route_fingerprint_material"]


def test_returned_model_metadata_does_not_rewrite_requested_route_identity() -> None:
    runner = load_runner_module()
    enriched = runner.enrich_request_meta(
        {
            "provider": "openrouter",
            "model_id": "x-ai/grok-fixture",
            "api_key_env_resolved": "OPENROUTER_API_KEY",
            "endpoint_base_url": "https://openrouter.ai/api/v1",
            "endpoint_effective": "https://openrouter.ai/api/v1/chat/completions",
            "transport": "openai_sdk",
            "response_summary": {"returned_model_id": "grok-returned-fixture"},
            "structured_output": {"structured_output_mode_effective": "json_schema"},
        },
        run_id="run-static",
        phase="A",
        step_id="A1",
        partition_id="A_P0001",
        provider="openrouter",
        model_id="x-ai/grok-fixture",
    )

    assert enriched["returned_model_id"] == "grok-returned-fixture"
    assert enriched["requested_provider"] == "openrouter"
    assert enriched["requested_model_id"] == "x-ai/grok-fixture"
    assert enriched["provider_route_kind"] == "openrouter_proxy_xai"
    assert enriched["economic_surface"] == "openrouter"

    material = runner.static_route_fingerprint_material(enriched)
    assert "returned_model_id" not in material
    assert material["requested_provider"] == "openrouter"
    assert material["requested_model_id"] == "x-ai/grok-fixture"


def test_run_routing_fingerprint_static_artifact_preserves_existing_shape(
    tmp_path: Path, monkeypatch: Any
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

    run_root = tmp_path / "run"
    run_root.mkdir()
    runner.write_run_routing_fingerprint(run_root, "run-static", make_cfg(runner), ["D"])

    payload = json.loads((run_root / "RUN_ROUTING_FINGERPRINT.json").read_text())
    row = payload["phases"]["D"][0]

    assert payload["fingerprint_authority"] == "static_request_route_metadata"
    assert payload["live_provider_behavior_proven"] is False
    assert payload["live_validation_status"] == "LIVE_VALIDATION_REQUIRED"
    assert payload["route_fingerprint_input_fields"] == list(
        runner.ROUTE_FINGERPRINT_INPUT_FIELDS
    )
    assert row["provider"]
    assert row["model_id"]
    assert row["api_key_env"]
    assert row["routing_signature"]
    assert row["requested_provider"] == row["provider"]
    assert row["requested_model_id"] == row["model_id"]
    assert row["provider_route_kind"]
    assert row["economic_surface"]
    assert row["endpoint_effective"]
    assert row["provider_signature"]
    assert row["structured_output_mode"]
    assert row["provider_schema_variant"]
    assert row["route_fingerprint_material"]
    assert row["route_fingerprint_hash"]
