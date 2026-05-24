"""Tests for service_tier passthrough + observability in call_llm().

Covers TP-RTE-COSTPROFILE-E4-FINISH-001 S6:
- `service_tier` kwarg propagates into chat_kwargs for OpenAI / OpenRouter.
- xAI provider OMITS service_tier even when caller passes it (xAI doesn't
  document the kwarg).
- `meta['service_tier_requested']` mirrors what the caller passed.
- `meta['service_tier_observed']` is sourced from
  `response_summary['usage']['service_tier']` when the provider echoes it
  back; otherwise None.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict
from unittest.mock import MagicMock


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from llm_runtime import LLMRuntimeDeps, call_llm  # noqa: E402


def _no_provider_call(*_args: Any, **_kwargs: Any) -> Any:
    raise AssertionError("provider client must not be invoked by this test")


def _build_succeeding_deps(
    captured: Dict[str, Any],
    *,
    response_usage: Dict[str, Any] | None = None,
) -> LLMRuntimeDeps:
    """LLMRuntimeDeps that drive call_llm through the OpenAI SDK success path
    with all heavy collaborators mocked. `captured` collects chat_kwargs
    so tests can assert on what reached the provider client."""
    usage = response_usage if response_usage is not None else {
        "input_tokens": 10,
        "output_tokens": 5,
        "total_tokens": 15,
    }

    def fake_get_client(_base_url: Any, _api_key: str) -> Any:
        client = MagicMock()

        def create(**kwargs: Any) -> Any:
            captured["chat_kwargs"] = kwargs
            response = MagicMock()
            response.choices = [MagicMock()]
            return response

        client.chat.completions.create = create
        return client

    def fake_xai_client(_api_key: str) -> Any:
        return fake_get_client(None, _api_key)

    return LLMRuntimeDeps(
        live_llm_calls_blocked_for_tests=lambda: False,
        live_llm_tests_env="RTE_DISABLE_LIVE_LLM_IN_TESTS",
        llm_base_url=lambda _p, _c: "https://api.openai.com/v1",
        transport_for_provider=lambda _p, _c: "openai_sdk",
        resolve_api_key=lambda _p, env: ("fake-key", env),
        build_chat_payload=lambda p, m, s, u, **_kw: {
            "model": m,
            "messages": [{"role": "system", "content": s}, {"role": "user", "content": u}],
            "temperature": 0.1,
        },
        serialize_payload_body=lambda p: json.dumps(p, sort_keys=True),
        measure_payload_bytes_from_body=len,
        gemini_auth_mode_sequence=lambda _m, _b: ["sdk_bearer"],
        make_url=lambda _p, b, _c, _k, _m: b + "/chat/completions",
        make_headers=lambda *_a: {},
        sdk_auth_present_flags=lambda _p, present: {"sdk_api_key_present": present},
        build_auth_present_flags=lambda _h, _q: {},
        endpoint_effective=lambda url: url,
        endpoint_fingerprint=lambda url: {"endpoint_host": "fixture.test"},
        provider_signature=lambda p, m, u, _mode: f"{p}/{m}/{u}",
        get_http_session=_no_provider_call,
        get_gemini_client=_no_provider_call,
        extract_text_from_gemini_response=lambda _r: "",
        get_xai_client=fake_xai_client,
        get_openrouter_client=fake_xai_client,
        get_openai_client=fake_get_client,
        extract_text_from_chat_completion=lambda _r: '{"ok": true}',
        summarize_llm_response=lambda **_kw: {
            "finish_reason": "stop",
            "text_length": 12,
            "usage": dict(usage),
        },
        exception_status_code=lambda _e: None,
        exception_response_text=lambda _e: "",
        classify_failure_type=lambda _s, _b, _t: "unknown",
        extract_provider_error_reason=lambda _b: None,
        sanitize_error_text=lambda text: text,
        capture_exception_metadata=lambda _e: {},
        new_trace_id=lambda: "trace-tier-test",
        new_span_id=lambda: "span-tier-test",
        cost_abort_failure_meta=lambda **kw: dict(kw),
        should_retry=lambda _s, _f, _e, _p: False,
        backoff_seconds=lambda _a, _b, _m: 0.0,
        is_spend_aborted=lambda: False,
        sha256_text=lambda _p: "sha256-fixture",
        runner_script=Path("run_extraction_v5.py"),
        is_auth_classified_failure=lambda _f: False,
        classify_escalation_class=lambda **_kw: "none",
        is_break_glass_opus_route=lambda _r: False,
        provider_api_key_env={"openai": "OPENAI_API_KEY"},
        max_files_for_phase=lambda _p, _c: 1,
        estimate_text_tokens=lambda s, u: len(s) + len(u),
        project_output_tokens=lambda t: t,
        check_projected_cost_limit=lambda **_kw: None,
        accumulate_runtime_spend=lambda **_kw: None,
        cost_limit_exceeded_error=RuntimeError,
        now_iso=lambda: "2026-05-23T00:00:00+00:00",
        strip_outer_json_fence=lambda _t: None,
        extract_first_fenced_json_block=lambda _t: None,
        extract_first_json_object=lambda _t: None,
        is_semantic_eof_eligible=lambda _e, _t: False,
        try_repair_json_truncation=lambda _t, _e: None,
    )


def _make_cfg() -> SimpleNamespace:
    return SimpleNamespace(
        cost_profile="value-default",
        model_alias_overrides=(),
        retry_max_attempts=1,
        retry_base_seconds=0.0,
        retry_max_seconds=0.0,
        retry_policy="none",
        gemini_auth_mode="auto",
    )


# ---------------------------------------------------------------- pass-through


def test_service_tier_propagates_to_openai_chat_kwargs() -> None:
    captured: Dict[str, Any] = {}
    deps = _build_succeeding_deps(captured)

    result = call_llm(
        deps=deps,
        provider="openai",
        model_id="gpt-5",
        api_key_env="OPENAI_API_KEY",
        system_prompt="s",
        user_content="u",
        cfg=_make_cfg(),
        service_tier="flex",
    )

    assert result["ok"] is True
    assert captured["chat_kwargs"].get("service_tier") == "flex"
    assert result["meta"]["service_tier_requested"] == "flex"


def test_service_tier_propagates_to_openrouter() -> None:
    captured: Dict[str, Any] = {}
    deps = _build_succeeding_deps(captured)

    result = call_llm(
        deps=deps,
        provider="openrouter",
        model_id="openai/gpt-5",
        api_key_env="OPENROUTER_API_KEY",
        system_prompt="s",
        user_content="u",
        cfg=_make_cfg(),
        service_tier="priority",
    )

    assert captured["chat_kwargs"].get("service_tier") == "priority"
    assert result["meta"]["service_tier_requested"] == "priority"


def test_service_tier_omitted_for_xai_even_when_set() -> None:
    """xAI does not document a service_tier kwarg; runtime must not forward it."""
    captured: Dict[str, Any] = {}
    deps = _build_succeeding_deps(captured)

    result = call_llm(
        deps=deps,
        provider="xai",
        model_id="grok-code-fast-1",
        api_key_env="XAI_API_KEY",
        system_prompt="s",
        user_content="u",
        cfg=_make_cfg(),
        service_tier="flex",
    )

    assert "service_tier" not in captured["chat_kwargs"]
    # Meta still records what the caller REQUESTED, even though it wasn't sent.
    assert result["meta"]["service_tier_requested"] == "flex"


def test_service_tier_none_means_no_chat_kwarg() -> None:
    captured: Dict[str, Any] = {}
    deps = _build_succeeding_deps(captured)

    result = call_llm(
        deps=deps,
        provider="openai",
        model_id="gpt-5",
        api_key_env="OPENAI_API_KEY",
        system_prompt="s",
        user_content="u",
        cfg=_make_cfg(),
        service_tier=None,
    )

    assert "service_tier" not in captured["chat_kwargs"]
    assert result["meta"]["service_tier_requested"] is None


def test_service_tier_invalid_value_omitted_but_recorded() -> None:
    """Invalid tier strings are not forwarded (existing whitelist), but the
    requested value is still surfaced in meta for visibility."""
    captured: Dict[str, Any] = {}
    deps = _build_succeeding_deps(captured)

    result = call_llm(
        deps=deps,
        provider="openai",
        model_id="gpt-5",
        api_key_env="OPENAI_API_KEY",
        system_prompt="s",
        user_content="u",
        cfg=_make_cfg(),
        service_tier="not-a-valid-tier",
    )

    assert "service_tier" not in captured["chat_kwargs"]
    assert result["meta"]["service_tier_requested"] == "not-a-valid-tier"


def test_service_tier_observed_surfaces_from_response_usage() -> None:
    """When the provider echoes service_tier in usage, meta exposes it."""
    captured: Dict[str, Any] = {}
    deps = _build_succeeding_deps(
        captured,
        response_usage={
            "input_tokens": 10,
            "output_tokens": 5,
            "total_tokens": 15,
            "service_tier": "default",
        },
    )

    result = call_llm(
        deps=deps,
        provider="openai",
        model_id="gpt-5",
        api_key_env="OPENAI_API_KEY",
        system_prompt="s",
        user_content="u",
        cfg=_make_cfg(),
        service_tier="flex",
    )

    assert result["meta"]["service_tier_requested"] == "flex"
    assert result["meta"]["service_tier_observed"] == "default"


def test_service_tier_observed_none_when_not_echoed() -> None:
    """When usage doesn't include service_tier, observed is None."""
    captured: Dict[str, Any] = {}
    deps = _build_succeeding_deps(captured)  # default usage has no service_tier

    result = call_llm(
        deps=deps,
        provider="openai",
        model_id="gpt-5",
        api_key_env="OPENAI_API_KEY",
        system_prompt="s",
        user_content="u",
        cfg=_make_cfg(),
        service_tier="flex",
    )

    assert result["meta"]["service_tier_observed"] is None


def test_cache_strategy_applied_reflects_prompt_cache_directives() -> None:
    """meta['cache_strategy_applied'] mirrors prompt_cache_directives['strategy']
    when applied=True; otherwise defaults to 'none'."""
    captured: Dict[str, Any] = {}
    deps = _build_succeeding_deps(captured)

    # Applied directives
    result_applied = call_llm(
        deps=deps,
        provider="openai",
        model_id="gpt-5",
        api_key_env="OPENAI_API_KEY",
        system_prompt="s",
        user_content="u",
        cfg=_make_cfg(),
        prompt_cache_directives={
            "applied": True,
            "strategy": "auto",
            "prompt_cache_key": "abc123",
        },
    )
    assert result_applied["meta"]["cache_strategy_applied"] == "auto"

    # Not applied
    result_not_applied = call_llm(
        deps=deps,
        provider="openai",
        model_id="gpt-5",
        api_key_env="OPENAI_API_KEY",
        system_prompt="s",
        user_content="u",
        cfg=_make_cfg(),
        prompt_cache_directives={
            "applied": False,
            "strategy": "none",
        },
    )
    assert result_not_applied["meta"]["cache_strategy_applied"] == "none"

    # No directives passed at all
    result_no_directives = call_llm(
        deps=deps,
        provider="openai",
        model_id="gpt-5",
        api_key_env="OPENAI_API_KEY",
        system_prompt="s",
        user_content="u",
        cfg=_make_cfg(),
    )
    assert result_no_directives["meta"]["cache_strategy_applied"] == "none"
