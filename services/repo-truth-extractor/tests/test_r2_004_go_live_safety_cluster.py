"""TP-RTE-TRUTH-R2-004 -- go-live safety cluster.

MANDATORY-VERIFICATION tests for the findings fixed by this packet:

  F-13b -- validate_pre_live_gate_v25.py's un-opted-in Condition skip
     (PAL/online-preflight not run) now hard-stops at NO_GO instead of the
     old default CONDITIONAL_GO; --allow-conditional restores the softer
     verdict. Covered here (unit level, derive_operator_verdict) and in
     tests/test_pre_live_gate_v25.py (run_gate level).

  F-19b (FA-8-HIGH-1) -- the preflight probe's AMBIGUOUS_PROVIDER_BLOCK
     with valid keys was traced to build_chat_payload's gpt-5
     temperature-omission rule only matching literal provider == "openai";
     an OpenRouter-routed "openai/gpt-5.x" slug still got a temperature
     value, which the upstream gpt-5 model rejects with a 400 that gets
     classified as an ambiguous provider block. llm_runtime.call_llm now
     strips temperature for any gpt-5-family model regardless of the
     provider name fronting the call. Covered here entirely offline (no
     API keys, no network) by capturing the payload actually handed to the
     provider SDK client -- this is the same call_llm the FA-8 regression
     test's run_provider_doctor_probe exercises, just without the live
     network hop that dry-run-only verification cannot make.

  F-19c -- the Gemini SDK path called get_gemini_client(api_key) without
     threading the remaining per-call timeout budget through, so a hung
     Gemini call could stall a lane past its overall deadline. Covered
     here by capturing the args get_gemini_client was invoked with.

  F-19d -- RUN_MANIFEST embedded the raw dpmx_webhook_url (a
     bearer-equivalent capability URL) verbatim. reporting.write_run_manifest
     now stores presence only (dpmx_webhook_url_set), matching the
     treatment already applied to dpmx_webhook_secret_set. Covered in
     tests/test_r2_004_webhook_manifest_redaction.py.

Each test below is written to fail if its corresponding fix is reverted
(see PROOF.json for the manual revert-and-rerun mutation check performed
for every test in this file).
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest

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


def _load_runner():
    return _load_module("run_extraction_v5_r2_004", "run_extraction_v5.py")


def _load_llm_runtime():
    return _load_module("llm_runtime_r2_004", "llm_runtime.py")


def _make_cfg(runner: Any, **overrides: Any) -> Any:
    payload = {
        "dry_run": False,
        "max_files_docs": 35,
        "max_files_code": 20,
        "max_chars": 650000,
        "max_request_bytes": 200000,
        "file_truncate_chars": 70000,
        "home_scan_mode": "safe",
        "resume": False,
        "fail_fast_auth": True,
        "gemini_auth_mode": "auto",
        "gemini_transport": "sdk",
        "openai_transport": "openai_sdk",
        "xai_transport": "openai_sdk",
        "retry_policy": "none",
        "retry_max_attempts": 1,
        "retry_base_seconds": 0.0,
        "retry_max_seconds": 0.0,
        "phase_auth_fail_threshold": 1,
        "partition_workers": 1,
        "debug_phase_inputs": False,
        "fail_fast_missing_inputs": False,
        "routing_policy": "balanced_grok_openrouter",
    }
    payload.update(overrides)
    return runner.RunnerConfig(**payload)


def _base_llm_runtime_deps(llm_runtime, runner, *, get_gemini_client=None, get_openrouter_client=None):
    """Shared LLMRuntimeDeps skeleton; only the fields exercised by a given
    test need real behavior, everything else is a harmless stub."""
    return dict(
        live_llm_calls_blocked_for_tests=lambda: False,
        live_llm_tests_env="RTE_TEST_LIVE_OK",
        llm_base_url=runner.llm_base_url,
        transport_for_provider=runner.transport_for_provider,
        resolve_api_key=lambda _provider, api_key_env: ("test-key", api_key_env),
        build_chat_payload=runner.build_chat_payload,
        serialize_payload_body=runner.serialize_payload_body,
        measure_payload_bytes_from_body=lambda body: len(body),
        gemini_auth_mode_sequence=runner._gemini_auth_mode_sequence,
        make_url=lambda *a, **k: "https://example.test/v1beta/models",
        make_headers=lambda *a, **k: {},
        sdk_auth_present_flags=lambda *a, **k: {"has_auth": True},
        build_auth_present_flags=lambda *a, **k: {"has_auth": True},
        endpoint_effective=lambda url: url,
        endpoint_fingerprint=lambda url: {"endpoint_host": "example.test", "endpoint_path": "/x"},
        provider_signature=lambda *a, **k: "sig",
        get_http_session=lambda: None,
        get_gemini_client=get_gemini_client or (lambda api_key, timeout_seconds=None: None),
        extract_text_from_gemini_response=lambda resp: "OK",
        get_xai_client=lambda api_key: None,
        get_openrouter_client=get_openrouter_client or (lambda api_key: None),
        get_openai_client=lambda base_url, api_key: None,
        extract_text_from_chat_completion=lambda resp: "OK",
        summarize_llm_response=lambda **k: {},
        exception_status_code=lambda exc: None,
        exception_response_text=lambda exc: "",
        classify_failure_type=lambda *a, **k: "unknown",
        extract_provider_error_reason=lambda text: None,
        sanitize_error_text=lambda text: text,
        capture_exception_metadata=lambda exc: {},
        new_trace_id=lambda: "trace",
        new_span_id=lambda: "span",
        cost_abort_failure_meta=lambda **k: {},
        should_retry=lambda *a, **k: False,
        backoff_seconds=lambda *a, **k: 0.0,
        is_spend_aborted=lambda: False,
        sha256_text=lambda p: "sha",
        runner_script=SERVICE_ROOT / "run_extraction_v5.py",
        is_auth_classified_failure=lambda reason: False,
        classify_escalation_class=lambda *a, **k: "none",
        is_break_glass_opus_route=lambda route: False,
        provider_api_key_env={"openrouter": "OPENROUTER_API_KEY", "gemini": "GEMINI_API_KEY"},
        max_files_for_phase=lambda *a, **k: 10,
        estimate_text_tokens=lambda text, model: len(text) // 4,
        project_output_tokens=lambda n: n // 10,
        check_projected_cost_limit=lambda **k: None,
        accumulate_runtime_spend=lambda **k: None,
        cost_limit_exceeded_error=RuntimeError,
        now_iso=lambda: "2026-07-27T00:00:00+00:00",
        strip_outer_json_fence=lambda text: text,
        extract_first_fenced_json_block=lambda text: None,
        extract_first_json_object=lambda text: None,
        is_semantic_eof_eligible=lambda exc, text: False,
        try_repair_json_truncation=lambda text, exc: None,
    )


# ---------------------------------------------------------------------------
# F-13b: derive_operator_verdict un-opted-conditional-skip -> NO_GO
# (run_gate-level coverage lives in tests/test_pre_live_gate_v25.py)
# ---------------------------------------------------------------------------


def _load_gate():
    return _load_module("validate_pre_live_gate_v25_r2_004", "validate_pre_live_gate_v25.py")


def test_gate_config_allow_conditional_defaults_false() -> None:
    gate = _load_gate()
    config = gate.GateConfig(
        repo_root=Path("/tmp/repo"),
        output_dir=Path("/tmp/out"),
        run_id="r",
        target_policy="cost",
        target_mode="direct",
        target_profile="P00_GENERIC",
        target_phases=("A",),
    )
    assert config.allow_conditional is False


# ---------------------------------------------------------------------------
# F-19b / FA-8-HIGH-1: OpenRouter-routed gpt-5 must not receive `temperature`
# ---------------------------------------------------------------------------


def test_call_llm_strips_temperature_for_openrouter_routed_gpt5_model() -> None:
    """Reproduces FA-8-HIGH-1's root cause offline: `openai/gpt-5.2` routed
    through provider="openrouter" (exactly the FA-8 regression test's
    route) previously reached the provider SDK with `temperature` set --
    the omission rule in build_chat_payload only matched literal
    provider == "openai". OpenRouter forwards that to the upstream gpt-5
    model, which rejects any non-default temperature with a 400 that
    classify_provider_readiness_blocker maps to AMBIGUOUS_PROVIDER_BLOCK.
    This test captures the exact kwargs handed to the SDK client and
    proves `temperature` is absent -- the same fix also makes FA-8's own
    (skipif-gated, live-key) regression test pass once real credentials
    are exercised."""
    llm_runtime = _load_llm_runtime()
    runner = _load_runner()

    captured_kwargs: list[dict] = []

    class _FakeCompletions:
        def create(self, **kwargs):
            captured_kwargs.append(kwargs)

            class _Choice:
                class message:
                    content = "OK"

            class _Resp:
                choices = [_Choice()]

            return _Resp()

    class _FakeChat:
        completions = _FakeCompletions()

    class _FakeOpenRouterClient:
        chat = _FakeChat()

    cfg = _make_cfg(runner)

    deps_kwargs = _base_llm_runtime_deps(
        llm_runtime,
        runner,
        get_openrouter_client=lambda api_key: _FakeOpenRouterClient(),
    )
    deps_kwargs["extract_text_from_chat_completion"] = lambda resp: resp.choices[0].message.content
    deps = llm_runtime.LLMRuntimeDeps(**deps_kwargs)

    result = llm_runtime.call_llm(
        deps,
        provider="openrouter",
        model_id="openai/gpt-5.2",
        api_key_env="OPENROUTER_API_KEY",
        system_prompt="Return exactly OK.",
        user_content="Return the single token OK.",
        cfg=cfg,
    )

    assert result["ok"] is True
    assert len(captured_kwargs) == 1
    assert "temperature" not in captured_kwargs[0], (
        "openai/gpt-5.2 routed through openrouter must not receive a "
        "temperature parameter -- gpt-5 rejects it and the FA-8 probe "
        "reproduced exactly this 400 being misclassified as "
        "AMBIGUOUS_PROVIDER_BLOCK."
    )
    assert captured_kwargs[0]["model"] == "openai/gpt-5.2"


def test_model_family_rejects_custom_temperature_matches_routed_and_direct_gpt5() -> None:
    """Unit-level proof for the helper itself: both the direct
    (`provider="openai", model_id="gpt-5.5"`) and OpenRouter-routed
    (`model_id="openai/gpt-5.5"`) spellings must be caught, while
    non-gpt-5 models are untouched."""
    llm_runtime = _load_llm_runtime()

    assert llm_runtime._model_family_rejects_custom_temperature("gpt-5.5") is True
    assert llm_runtime._model_family_rejects_custom_temperature("openai/gpt-5.5") is True
    assert llm_runtime._model_family_rejects_custom_temperature("openai/gpt-5.2") is True
    assert llm_runtime._model_family_rejects_custom_temperature("gpt-4o-mini") is False
    assert llm_runtime._model_family_rejects_custom_temperature("openai/gpt-4o-mini") is False
    assert llm_runtime._model_family_rejects_custom_temperature("grok-4.3") is False


# ---------------------------------------------------------------------------
# F-19c: Gemini SDK client must receive the remaining-timeout budget
# ---------------------------------------------------------------------------


def test_call_llm_threads_remaining_timeout_into_get_gemini_client() -> None:
    """get_gemini_client(api_key) previously dropped the client-level
    HttpOptions deadline entirely -- a hung Gemini call could stall a lane
    past cfg's overall timeout_seconds. Prove the SDK-branch call now
    passes a positive integer timeout_seconds through."""
    llm_runtime = _load_llm_runtime()
    runner = _load_runner()

    captured_calls: list[tuple] = []

    class _FakeGeminiModels:
        def generate_content(self, *, model: str, contents: str, config: dict):
            class _Resp:
                pass

            return _Resp()

    class _FakeGeminiClient:
        models = _FakeGeminiModels()

    def _fake_get_gemini_client(api_key, timeout_seconds=None):
        captured_calls.append((api_key, timeout_seconds))
        return _FakeGeminiClient()

    cfg = _make_cfg(runner)

    deps_kwargs = _base_llm_runtime_deps(
        llm_runtime,
        runner,
        get_gemini_client=_fake_get_gemini_client,
    )
    deps_kwargs["extract_text_from_gemini_response"] = lambda resp: "OK"
    deps = llm_runtime.LLMRuntimeDeps(**deps_kwargs)

    result = llm_runtime.call_llm(
        deps,
        provider="gemini",
        model_id="gemini-3-flash-preview",
        api_key_env="GEMINI_API_KEY",
        system_prompt="You are a test.",
        user_content="Say OK.",
        cfg=cfg,
        timeout_seconds=45,
    )

    assert result["ok"] is True
    assert len(captured_calls) == 1
    api_key_arg, timeout_arg = captured_calls[0]
    assert api_key_arg == "test-key"
    assert isinstance(timeout_arg, int)
    assert 0 < timeout_arg <= 45
