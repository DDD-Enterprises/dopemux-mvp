from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = REPO_ROOT / "services" / "repo-truth-extractor"


def _load_module(name: str, relative_path: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, SERVICE_ROOT / relative_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_build_chat_payload_preserves_allowlisted_request_options_only() -> None:
    runner = _load_module("run_extraction_v5_request_options", "run_extraction_v5.py")

    payload = runner.build_chat_payload(
        provider="openai",
        model_id="gpt-5.5",
        system_prompt="system",
        user_content="user",
        request_options={
            "service_tier": "flex",
            "reasoning_effort": "low",
            "api_key_env": "SHOULD_NOT_LEAK",
            "unknown": "ignored",
        },
    )

    assert payload["service_tier"] == "flex"
    assert payload["reasoning_effort"] == "low"
    assert "api_key_env" not in payload
    assert "unknown" not in payload


def test_phase_contract_routes_preserve_request_options() -> None:
    contracts = _load_module(
        "structured_output_contracts_request_options",
        "lib/structured_output_contracts.py",
    )
    model_map = {
        "lane": {
            "primary_routes": [
                {
                    "provider": "openai",
                    "model_id": "gpt-5.5",
                    "api_key_env": "OPENAI_API_KEY",
                    "service_tier": "flex",
                    "reasoning_effort": "low",
                }
            ]
        }
    }

    routes = contracts.route_entries_for_stage(model_map, "primary")

    assert routes == [
        {
            "provider": "openai",
            "model_id": "gpt-5.5",
            "api_key_env": "OPENAI_API_KEY",
            "structured_output_mode": "none",
            "strict_json_schema": False,
            "strict_passthrough_verified": False,
            "service_tier": "flex",
            "reasoning_effort": "low",
        }
    ]


def test_llm_runtime_forwards_request_options_to_sdk_chat_completion() -> None:
    llm_runtime = _load_module("llm_runtime_request_options", "llm_runtime.py")
    observed: dict[str, Any] = {}

    class _Message:
        content = "{}"

    class _Choice:
        message = _Message()

    class _Response:
        choices = [_Choice()]

    class _Completions:
        def create(self, **kwargs: Any) -> _Response:
            observed.update(kwargs)
            return _Response()

    class _Chat:
        completions = _Completions()

    class _Client:
        chat = _Chat()

    deps = llm_runtime.LLMRuntimeDeps(
        live_llm_calls_blocked_for_tests=lambda: False,
        live_llm_tests_env="DPMX_LIVE_LLM_TESTS",
        llm_base_url=lambda provider, cfg: "https://api.openai.com/v1",
        transport_for_provider=lambda provider, cfg: "openai_sdk",
        resolve_api_key=lambda provider, api_key_env: ("test-key", api_key_env),
        build_chat_payload=lambda provider, model_id, system_prompt, user_content, **kwargs: {
            "model": model_id,
            "messages": [{"role": "user", "content": "user"}],
            "temperature": 0,
            "service_tier": "flex",
            "reasoning_effort": "low",
        },
        serialize_payload_body=lambda payload: json.dumps(payload).encode("utf-8"),
        measure_payload_bytes_from_body=lambda body: len(body),
        gemini_auth_mode_sequence=lambda auth_mode, base_url: ["sdk_bearer"],
        make_url=lambda provider, base_url, cfg, api_key, effective_mode: base_url,
        make_headers=lambda provider, api_key, cfg, effective_mode: {},
        sdk_auth_present_flags=lambda provider, has_api_key: {"bearer": has_api_key},
        build_auth_present_flags=lambda headers, query_key: {},
        endpoint_effective=lambda url: url,
        endpoint_fingerprint=lambda url: {},
        provider_signature=lambda provider, model_id, endpoint_url, mode: "sig",
        get_http_session=lambda: None,
        get_gemini_client=lambda api_key: None,
        extract_text_from_gemini_response=lambda response: "{}",
        get_xai_client=lambda api_key: _Client(),
        get_openrouter_client=lambda api_key: _Client(),
        get_openai_client=lambda base_url, api_key: _Client(),
        extract_text_from_chat_completion=lambda response: response.choices[0].message.content,
        summarize_llm_response=lambda **kwargs: {"finish_reason": "stop"},
        exception_status_code=lambda exc: None,
        exception_response_text=lambda exc: "",
        classify_failure_type=lambda status_code, body, text: "unknown",
        extract_provider_error_reason=lambda body: None,
        sanitize_error_text=lambda text: text,
        capture_exception_metadata=lambda exc: {},
        new_trace_id=lambda: "trace",
        new_span_id=lambda: "span",
        cost_abort_failure_meta=lambda **kwargs: {},
        should_retry=lambda status_code, failure_type, exc, provider: False,
        backoff_seconds=lambda attempt, base, max_seconds: 0.0,
        is_spend_aborted=lambda: False,
        sha256_text=lambda path: "sha",
        runner_script=Path("run_extraction_v5.py"),
        is_auth_classified_failure=lambda failure_type: False,
        classify_escalation_class=lambda **kwargs: "none",
        is_break_glass_opus_route=lambda route: False,
        provider_api_key_env={"openai": "OPENAI_API_KEY"},
        max_files_for_phase=lambda phase, cfg: 0,
        estimate_text_tokens=lambda system, user: 1,
        project_output_tokens=lambda input_tokens: 1,
        check_projected_cost_limit=lambda **kwargs: None,
        accumulate_runtime_spend=lambda **kwargs: None,
        cost_limit_exceeded_error=RuntimeError,
        now_iso=lambda: "2026-05-23T00:00:00+00:00",
        strip_outer_json_fence=lambda text: None,
        extract_first_fenced_json_block=lambda text: None,
        extract_first_json_object=lambda text: None,
        is_semantic_eof_eligible=lambda exc, text: False,
        try_repair_json_truncation=lambda text, exc: None,
    )
    cfg = type(
        "Cfg",
        (),
        {
            "retry_max_attempts": 1,
            "retry_base_seconds": 0.0,
            "retry_max_seconds": 0.0,
            "gemini_auth_mode": "sdk_bearer",
        },
    )()

    result = llm_runtime.call_llm(
        deps=deps,
        provider="openai",
        model_id="gpt-5.5",
        api_key_env="OPENAI_API_KEY",
        system_prompt="system",
        user_content="user",
        cfg=cfg,
    )

    assert result["ok"] is True
    assert observed["service_tier"] == "flex"
    assert observed["reasoning_effort"] == "low"


def test_openai_batch_jsonl_serializes_request_options(tmp_path: Path) -> None:
    batch_clients = _load_module("batch_clients_request_options", "lib/batch_clients.py")
    captured: dict[str, Any] = {}

    class _Files:
        def __init__(self) -> None:
            self.uploads: list[str] = []

        def create(self, *, file: Any, purpose: str) -> Any:
            assert purpose == "batch"
            payload = file.read()
            self.uploads.append(
                payload.decode("utf-8")
                if isinstance(payload, (bytes, bytearray))
                else str(payload)
            )
            return type("FileResult", (), {"id": "file_123"})()

    class _Batches:
        def create(self, **kwargs: Any) -> Any:
            return type("BatchResult", (), {"id": "batch_123"})()

    class _Client:
        def __init__(self) -> None:
            self.files = _Files()
            self.batches = _Batches()

    client = object.__new__(batch_clients.OpenAIBatchClient)
    fake = _Client()
    client._client = fake
    request = batch_clients.BatchRequest(
        custom_id="A1:0",
        model_id="gpt-5.5",
        system_prompt="system",
        user_content="user",
        request_options={"service_tier": "flex", "reasoning_effort": "low"},
    )

    job_id = client.submit(
        [request],
        batch_clients.BatchRoute("openai", "gpt-5.5", "OPENAI_API_KEY"),
        {"phase": "A", "step_id": "A1"},
    )

    assert job_id == "batch_123"
    jsonl = fake.files.uploads[0]
    body = json.loads(jsonl)
    assert body["body"]["service_tier"] == "flex"
    assert body["body"]["reasoning_effort"] == "low"
