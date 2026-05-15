from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

import llm_runtime
from _v5_smoke_helpers import load_runner_module
from lib.prescan.provider_catalog import _route_identity
from lib.structured_output_contracts import build_provider_step_contract_output


def _no_provider_call(*_args: Any, **_kwargs: Any) -> Any:
    raise AssertionError("provider client must not be invoked by static route tests")


def _fake_deps() -> llm_runtime.LLMRuntimeDeps:
    return llm_runtime.LLMRuntimeDeps(
        live_llm_calls_blocked_for_tests=lambda: False,
        live_llm_tests_env="RTE_TEST_LIVE_OK",
        llm_base_url=lambda provider, _cfg: (
            "https://openrouter.ai/api/v1"
            if provider == "openrouter"
            else "https://api.x.ai/v1"
        ),
        transport_for_provider=lambda _provider, _cfg: "openai_sdk",
        resolve_api_key=lambda _provider, api_key_env: ("", api_key_env),
        build_chat_payload=lambda _provider, model_id, system_prompt, user_content, **_kwargs: {
            "model": model_id,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        },
        serialize_payload_body=lambda payload: json.dumps(payload, sort_keys=True),
        measure_payload_bytes_from_body=len,
        gemini_auth_mode_sequence=lambda _mode, _base_url: ["sdk_bearer"],
        make_url=lambda _provider, base_url, _cfg, _api_key, _mode: base_url + "/chat/completions",
        make_headers=lambda *_args: {},
        sdk_auth_present_flags=lambda _provider, present: {"sdk_api_key_present": present},
        build_auth_present_flags=lambda _headers, _query_key: {},
        endpoint_effective=lambda url: url,
        endpoint_fingerprint=lambda url: {"endpoint_host": "fixture.test", "endpoint_path": url},
        provider_signature=lambda provider, model_id, endpoint_url, _mode: (
            f"provider={provider};model={model_id};endpoint={endpoint_url}"
        ),
        get_http_session=_no_provider_call,
        get_gemini_client=_no_provider_call,
        extract_text_from_gemini_response=lambda _response: "",
        get_xai_client=_no_provider_call,
        get_openrouter_client=_no_provider_call,
        get_openai_client=_no_provider_call,
        extract_text_from_chat_completion=lambda _response: "",
        summarize_llm_response=lambda **_kwargs: {},
        exception_status_code=lambda _exc: None,
        exception_response_text=lambda _exc: "",
        classify_failure_type=lambda _status, _body, _text: "unknown",
        extract_provider_error_reason=lambda _body: None,
        sanitize_error_text=lambda text: text,
        capture_exception_metadata=lambda _exc: {},
        new_trace_id=lambda: "trace-static",
        new_span_id=lambda: "span-static",
        cost_abort_failure_meta=lambda **kwargs: dict(kwargs),
        should_retry=lambda _status, _failure, _exc, _policy: False,
        backoff_seconds=lambda _attempt, _base, _max: 0.0,
        is_spend_aborted=lambda: False,
        sha256_text=lambda _path: "sha256-fixture",
        runner_script=Path("run_extraction_v5.py"),
        is_auth_classified_failure=lambda _failure: False,
        classify_escalation_class=lambda **_kwargs: "none",
        is_break_glass_opus_route=lambda _route: False,
        provider_api_key_env={"openrouter": "OPENROUTER_API_KEY", "xai": "XAI_API_KEY"},
        max_files_for_phase=lambda _phase, _cfg: 1,
        estimate_text_tokens=lambda system, user: len(system) + len(user),
        project_output_tokens=lambda input_tokens: input_tokens,
        check_projected_cost_limit=lambda **_kwargs: None,
        accumulate_runtime_spend=lambda **_kwargs: None,
        cost_limit_exceeded_error=RuntimeError,
        now_iso=lambda: "2026-05-15T00:00:00+00:00",
        strip_outer_json_fence=lambda _text: None,
        extract_first_fenced_json_block=lambda _text: None,
        extract_first_json_object=lambda _text: None,
        is_semantic_eof_eligible=lambda _exc, _text: False,
        try_repair_json_truncation=lambda _text, _exc: None,
    )


def _step_contract() -> dict[str, Any]:
    return {
        "phase": "A",
        "step_id": "A1",
        "scope": {"json_managed": True},
        "expected_artifacts": ["STATIC_ROUTE_FIXTURE.json"],
        "artifact_order": ["STATIC_ROUTE_FIXTURE.json"],
        "lane": {"lane_class": "BULK_DOCS_STRICT"},
        "artifacts": {
            "STATIC_ROUTE_FIXTURE.json": {
                "canonical_schema_id": "STATIC_ROUTE_FIXTURE@v1",
                "required_fields": ["id", "path", "line_range"],
                "prompt_required_item_fields": [],
                "allow_empty_array_fields": [],
            }
        },
    }


def test_direct_xai_route_identity_is_direct_provider_with_xai_surface() -> None:
    identity = llm_runtime.classify_route_identity(
        provider="xai",
        model_id="grok-fixture",
        api_key_env="XAI_API_KEY",
        endpoint_base_url="https://api.x.ai/v1",
        endpoint_effective="https://api.x.ai/v1/chat/completions",
        transport="openai_sdk",
        provider_signature="provider=xai;model=grok-fixture",
        structured_output={"structured_output_mode_effective": "json_schema"},
    )

    assert identity["requested_provider"] == "xai"
    assert identity["requested_model_id"] == "grok-fixture"
    assert identity["provider_route_kind"] == "direct_provider"
    assert identity["upstream_provider"] == "xai"
    assert identity["economic_surface"] == "xai_direct"
    assert identity["api_key_env"] == "XAI_API_KEY"
    assert identity["provider_schema_variant"] == "xai_relaxed_direct"


def test_openrouter_xai_route_identity_is_proxy_with_openrouter_surface() -> None:
    identity = llm_runtime.classify_route_identity(
        provider="openrouter",
        model_id="x-ai/grok-fixture",
        api_key_env="OPENROUTER_API_KEY",
        endpoint_base_url="https://openrouter.ai/api/v1",
        endpoint_effective="https://openrouter.ai/api/v1/chat/completions",
        transport="openai_sdk",
        provider_signature="provider=openrouter;model=x-ai/grok-fixture",
        structured_output={"structured_output_mode_effective": "json_schema"},
    )

    assert identity["requested_provider"] == "openrouter"
    assert identity["requested_model_id"] == "x-ai/grok-fixture"
    assert identity["provider_route_kind"] == "openrouter_proxy_xai"
    assert identity["upstream_provider"] == "xai"
    assert identity["economic_surface"] == "openrouter"
    assert identity["api_key_env"] == "OPENROUTER_API_KEY"
    assert identity["provider_schema_variant"] == "openrouter_proxy_xai_relaxed"
    assert identity["live_validation_status"] == "LIVE_VALIDATION_REQUIRED"
    assert identity["direct_provider_guarantees_inherited"] is False


def test_call_llm_openrouter_xai_missing_key_adds_proxy_metadata_without_provider_call() -> None:
    result = llm_runtime.call_llm(
        _fake_deps(),
        provider="openrouter",
        model_id="x-ai/grok-fixture",
        api_key_env="OPENROUTER_API_KEY",
        system_prompt="Return JSON.",
        user_content="{}",
        cfg=SimpleNamespace(gemini_auth_mode="auto"),
        structured_output_override={
            "structured_output_mode_requested": "json_schema",
            "structured_output_mode_effective": "json_schema",
            "provider_schema_variant": "openrouter_proxy_xai_relaxed",
        },
    )

    assert result["ok"] is False
    meta = result["meta"]
    assert meta["failure_type"] == "auth_missing"
    assert meta["requested_provider"] == "openrouter"
    assert meta["provider_route_kind"] == "openrouter_proxy_xai"
    assert meta["upstream_provider"] == "xai"
    assert meta["economic_surface"] == "openrouter"
    assert meta["api_key_env"] == "OPENROUTER_API_KEY"
    assert meta["live_validation_status"] == "LIVE_VALIDATION_REQUIRED"


def test_returned_model_metadata_does_not_rewrite_openrouter_xai_route_kind() -> None:
    runner = load_runner_module()

    meta = runner.enrich_request_meta(
        {
            "provider": "openrouter",
            "model_id": "x-ai/grok-fixture",
            "api_key_env_resolved": "OPENROUTER_API_KEY",
            "endpoint_base_url": "https://openrouter.ai/api/v1",
            "endpoint_effective": "https://openrouter.ai/api/v1/chat/completions",
            "transport": "openai_sdk",
            "response_summary": {"returned_model_id": "grok-fixture-returned"},
            "structured_output": {"structured_output_mode_effective": "json_schema"},
        },
        run_id="run-static",
        phase="A",
        step_id="A1",
        partition_id="A_P0001",
        provider="openrouter",
        model_id="x-ai/grok-fixture",
    )

    assert meta["returned_model_id"] == "grok-fixture-returned"
    assert meta["requested_provider"] == "openrouter"
    assert meta["requested_model_id"] == "x-ai/grok-fixture"
    assert meta["provider"] == "openrouter"
    assert meta["model_id"] == "x-ai/grok-fixture"
    assert meta["provider_route_kind"] == "openrouter_proxy_xai"
    assert meta["economic_surface"] == "openrouter"
    assert meta["live_validation_status"] == "LIVE_VALIDATION_REQUIRED"


def test_openrouter_xai_structured_output_label_preserves_xai_relaxed_behavior() -> None:
    response_format, response_meta = build_provider_step_contract_output(
        route={
            "provider": "openrouter",
            "model_id": "x-ai/grok-fixture",
            "api_key_env": "OPENROUTER_API_KEY",
            "structured_output_mode": "json_schema",
            "strict_json_schema": False,
        },
        transport="openai_sdk",
        step_contract=_step_contract(),
        artifact_names=("STATIC_ROUTE_FIXTURE.json",),
    )

    assert response_format["type"] == "json_schema"
    assert response_meta["schema_variant"] == "xai_relaxed"
    assert response_meta["schema_variant_behavior"] == "xai_relaxed"
    assert response_meta["provider_schema_variant"] == "openrouter_proxy_xai_relaxed"
    assert response_meta["structured_output_mode_effective"] == "json_schema"


def test_prescan_route_identity_labels_openrouter_xai_proxy_static_risk() -> None:
    identity = _route_identity("openrouter", "x-ai/grok-fixture")

    assert identity["requested_provider"] == "openrouter"
    assert identity["requested_model_id"] == "x-ai/grok-fixture"
    assert identity["provider_route_kind"] == "openrouter_proxy_xai"
    assert identity["upstream_provider"] == "xai"
    assert identity["economic_surface"] == "openrouter"
    assert identity["billing_independent_from_upstream"] is True
    assert identity["live_validation_status"] == "LIVE_VALIDATION_REQUIRED"
