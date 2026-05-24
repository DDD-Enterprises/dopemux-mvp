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
    # JSONL is one JSON object per line; parse the first line specifically so
    # the test stays robust if a future change submits multiple requests in
    # one batch upload or appends a trailing newline.
    first_line = next(line for line in jsonl.splitlines() if line.strip())
    body = json.loads(first_line)
    assert body["body"]["service_tier"] == "flex"
    assert body["body"]["reasoning_effort"] == "low"


def test_ladder_hop_route_entry_uses_index_to_disambiguate_request_options() -> None:
    runner = _load_module(
        "run_extraction_v5_route_entry_hop_options",
        "run_extraction_v5.py",
    )
    step_contract = {
        "lane": {
            "primary_routes": [
                {
                    "provider": "xai",
                    "model_id": "grok-4.3",
                    "api_key_env": "XAI_API_KEY",
                    "reasoning_effort": "low",
                },
                {
                    "provider": "xai",
                    "model_id": "grok-4.3",
                    "api_key_env": "XAI_API_KEY",
                    "reasoning_effort": "none",
                },
            ]
        }
    }
    ladder_entries = step_contract["lane"]["primary_routes"]

    first = runner._route_entry_for_ladder_hop(
        step_contract,
        ("xai", "grok-4.3", "XAI_API_KEY"),
        0,
        ladder_entries,
    )
    second = runner._route_entry_for_ladder_hop(
        step_contract,
        ("xai", "grok-4.3", "XAI_API_KEY"),
        1,
        ladder_entries,
    )

    assert first["reasoning_effort"] == "low"
    assert second["reasoning_effort"] == "none"


def test_strict_batch_request_uses_resolved_route_request_options() -> None:
    runner = _load_module(
        "run_extraction_v5_strict_batch_options",
        "run_extraction_v5.py",
    )
    artifact_name = "STRICT_OPTIONS.json"
    step_contract = {
        "phase": "A",
        "step_id": "A1",
        "scope": {"json_managed": True},
        "expected_artifacts": [artifact_name],
        "artifact_order": [artifact_name],
        "lane": {
            "lane_class": "BULK_DOCS_STRICT",
            "strict_schema_required": True,
            "strict_schema_required_primary": True,
            "primary_routes": [
                {
                    "provider": "openai",
                    "model_id": "gpt-5.5",
                    "api_key_env": "OPENAI_API_KEY",
                    "structured_output_mode": "json_schema",
                    "strict_json_schema": True,
                    "strict_passthrough_verified": True,
                    "service_tier": "flex",
                }
            ],
        },
        "artifacts": {
            artifact_name: {
                "canonical_schema_id": "STRICT_OPTIONS@v1",
                "required_fields": ["id", "path", "line_range"],
                "prompt_required_item_fields": [],
                "allow_empty_array_fields": [],
            }
        },
    }

    request = runner.build_v5_batch_request(
        custom_id="A_P0001",
        model_id="gpt-5.5",
        system_prompt="Return JSON.",
        user_content="Extract the fixture.",
        provider="openai",
        selected_route=("openai", "gpt-5.5", "OPENAI_API_KEY"),
        selected_route_entry=None,
        transport="openai_sdk",
        strict_contract_required=True,
        step_contract=step_contract,
        artifact_names=(artifact_name,),
        force_json_output=False,
        metadata={"phase": "A", "step_id": "A1", "partition_id": "A_P0001"},
    )

    assert request.request_options == {"service_tier": "flex"}


# ---------------------------------------------------------------------------
# Follow-up review fixes: route_options consolidation + ladder regressions
# ---------------------------------------------------------------------------


def test_normalize_route_request_options_drops_literal_none_case_insensitive() -> None:
    route_options = _load_module(
        "lib_route_options_drops_none",
        "lib/route_options.py",
    )

    normalized = route_options.normalize_route_request_options(
        {
            "service_tier": "flex",
            "reasoning_effort": "none",
        }
    )
    assert normalized == {"service_tier": "flex"}

    for sentinel in ("none", "NONE", " None ", "  noNE  "):
        result = route_options.normalize_route_request_options(
            {"reasoning_effort": sentinel}
        )
        assert result == {}, f"sentinel {sentinel!r} should normalize to empty dict"

    only_none = route_options.normalize_route_request_options(
        {"service_tier": "none", "reasoning_effort": "NONE"}
    )
    assert only_none == {}


def test_normalize_route_request_options_rejects_non_string_scalars() -> None:
    """YAML footgun: ``service_tier: true`` would otherwise stringify to
    ``"True"`` and be forwarded to the provider. Booleans, numbers, and
    ``None`` are rejected — only string values pass the allowlist.
    """
    route_options = _load_module(
        "lib_route_options_non_string_reject",
        "lib/route_options.py",
    )

    for bad in (True, False, 1, 0, 3.14, None, ["flex"], {"nested": "flex"}):
        assert route_options.normalize_route_request_options(
            {"service_tier": bad, "reasoning_effort": "low"}
        ) == {"reasoning_effort": "low"}, (
            f"service_tier={bad!r} should be rejected, reasoning_effort kept"
        )

    assert (
        route_options.normalize_route_request_options(
            {"service_tier": True, "reasoning_effort": False}
        )
        == {}
    )


def test_route_options_constant_lives_in_shared_module_and_is_reused() -> None:
    """M2 — ROUTE_REQUEST_OPTION_KEYS must be sourced from lib/route_options.py.

    Asserted two ways: (a) the shared constant has the expected value, and
    (b) no consuming source file still hand-rolls the tuple. Identity (``is``)
    cannot be used here because every importlib.util.spec_from_file_location
    call produces a fresh module with a fresh tuple object — equality with a
    grep against the source files is the durable check.
    """
    route_options = _load_module(
        "lib_route_options_shared_constant",
        "lib/route_options.py",
    )
    assert route_options.ROUTE_REQUEST_OPTION_KEYS == (
        "service_tier",
        "reasoning_effort",
    )

    runner = _load_module(
        "run_extraction_v5_shared_constant",
        "run_extraction_v5.py",
    )
    batch_clients = _load_module(
        "lib_batch_clients_shared_constant",
        "lib/batch_clients.py",
    )
    llm_runtime = _load_module(
        "llm_runtime_shared_constant",
        "llm_runtime.py",
    )
    phase_contract_map = _load_module(
        "lib_phase_contract_map_shared_constant",
        "lib/phase_contract_map.py",
    )
    structured_output_contracts = _load_module(
        "lib_structured_output_contracts_shared_constant",
        "lib/structured_output_contracts.py",
    )

    for module in (
        runner,
        batch_clients,
        llm_runtime,
        phase_contract_map,
        structured_output_contracts,
    ):
        assert (
            module.ROUTE_REQUEST_OPTION_KEYS == route_options.ROUTE_REQUEST_OPTION_KEYS
        ), f"{module.__name__} must expose the same ROUTE_REQUEST_OPTION_KEYS tuple"

    # Belt-and-suspenders: scan each source file directly so any future
    # contributor who reintroduces a local definition fails this test.
    consumer_paths = (
        "run_extraction_v5.py",
        "llm_runtime.py",
        "lib/batch_clients.py",
        "lib/phase_contract_map.py",
        "lib/structured_output_contracts.py",
    )
    for relative in consumer_paths:
        text = (SERVICE_ROOT / relative).read_text(encoding="utf-8")
        assert "ROUTE_REQUEST_OPTION_KEYS = (" not in text, (
            f"{relative} must import ROUTE_REQUEST_OPTION_KEYS from "
            "lib.route_options, not redefine it locally"
        )


def test_optimal_extract_ladder_has_distinct_fallback_entries() -> None:
    runner = _load_module(
        "run_extraction_v5_ladder_distinct",
        "run_extraction_v5.py",
    )
    extract_ladder = runner.ROUTING_LADDERS["optimal"]["extract"]
    assert len(extract_ladder) >= 2, "optimal.extract should retain two-deep fallback"
    identities = {(provider, model_id) for provider, model_id, _api_key in extract_ladder}
    assert len(identities) == len(extract_ladder), (
        f"optimal.extract ladder must have distinct (provider, model_id) entries; "
        f"got duplicates in {extract_ladder!r}"
    )


def test_grok_4_3_routes_with_reasoning_effort_none_normalize_to_empty() -> None:
    """Regression: 139 YAML rows declare ``reasoning_effort: none``.

    The runtime must treat the literal as the absence of the field so we never
    forward ``reasoning_effort="none"`` to xAI's chat completions API (the
    documented enum is ``low|high``).
    """
    route_options = _load_module(
        "lib_route_options_grok_none",
        "lib/route_options.py",
    )
    rows = [
        {
            "provider": "xai",
            "model_id": "grok-4.3",
            "api_key_env": "XAI_API_KEY",
            "reasoning_effort": "none",
        }
        for _ in range(139)
    ]
    for row in rows:
        normalized = route_options.normalize_route_request_options(row)
        assert "reasoning_effort" not in normalized


def test_full_chain_build_chat_payload_to_sdk_kwargs() -> None:
    """End-to-end: real build_chat_payload -> real call_llm -> SDK kwargs.

    Closes the L2 gap where the existing
    ``test_llm_runtime_forwards_request_options_to_sdk_chat_completion`` test
    used a stubbed build_chat_payload that pre-baked the options into the
    payload. Here we wire the *real* runner payload builder into the runtime
    deps and assert the options arrive at chat.completions.create unchanged.
    """
    runner = _load_module("run_extraction_v5_full_chain", "run_extraction_v5.py")
    llm_runtime = _load_module("llm_runtime_full_chain", "llm_runtime.py")

    captured: dict[str, Any] = {}

    class _Message:
        content = "{}"

    class _Choice:
        message = _Message()

    class _Response:
        choices = [_Choice()]

    class _Completions:
        def create(self, **kwargs: Any) -> _Response:
            captured.update(kwargs)
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
        build_chat_payload=runner.build_chat_payload,
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
        service_tier="priority",
        request_options_override={
            "service_tier": "flex",
            "reasoning_effort": "low",
        },
    )

    assert result["ok"] is True
    assert captured["service_tier"] == "flex"
    assert captured["reasoning_effort"] == "low"
    # The literal "none" must be dropped end-to-end, never reaching the SDK.
    captured.clear()
    result_none = llm_runtime.call_llm(
        deps=deps,
        provider="xai",
        model_id="grok-4.3",
        api_key_env="XAI_API_KEY",
        system_prompt="system",
        user_content="user",
        cfg=cfg,
        request_options_override={"reasoning_effort": "none"},
    )
    assert result_none["ok"] is True
    assert "reasoning_effort" not in captured
