"""Tests for cell alias resolution at call_llm() entry.

Covers TP-RTE-COSTPROFILE-E4-FINISH-001 S3/S7:
- When `model_id` arrives as a `${ALIAS_NAME}` placeholder it is resolved
  via `run_extraction_v5.resolve_cell_alias` (CLI overrides > env > profile).
- Resolution is lazy: non-placeholder model_ids are passed through unchanged.
- Cycle / unresolved aliases raise `ValueError` rather than sending the bare
  placeholder to the provider client.
- Result meta surfaces `model_id_requested` (the original) and
  `_resolved_from_alias` (bool) so downstream debugging can see the
  before/after.
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

import llm_runtime  # noqa: E402
from llm_runtime import LLMRuntimeDeps, call_llm  # noqa: E402


def _no_provider_call(*_args: Any, **_kwargs: Any) -> Any:
    raise AssertionError("provider client must not be invoked by this test")


def _build_succeeding_deps(captured: Dict[str, Any]) -> LLMRuntimeDeps:
    """Construct LLMRuntimeDeps that drive call_llm through the OpenAI SDK
    success path with all heavy collaborators mocked. `captured` collects
    the chat_kwargs that were ultimately passed to the mock OpenAI client so
    tests can assert on the resolved model_id and service_tier values."""

    def fake_get_openai_client(_base_url: Any, _api_key: str) -> Any:
        client = MagicMock()

        def create(**kwargs: Any) -> Any:
            captured["chat_kwargs"] = kwargs
            response = MagicMock()
            response.choices = [MagicMock()]
            return response

        client.chat.completions.create = create
        return client

    return LLMRuntimeDeps(
        live_llm_calls_blocked_for_tests=lambda: False,
        live_llm_tests_env="RTE_DISABLE_LIVE_LLM_IN_TESTS",
        llm_base_url=lambda _provider, _cfg: "https://api.openai.com/v1",
        transport_for_provider=lambda _provider, _cfg: "openai_sdk",
        resolve_api_key=lambda _provider, api_key_env: ("fake-key", api_key_env),
        build_chat_payload=lambda provider, model_id, system, user, **_kw: {
            "model": model_id,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.1,
        },
        serialize_payload_body=lambda p: json.dumps(p, sort_keys=True),
        measure_payload_bytes_from_body=len,
        gemini_auth_mode_sequence=lambda _mode, _base_url: ["sdk_bearer"],
        make_url=lambda _p, base_url, _c, _k, _m: base_url + "/chat/completions",
        make_headers=lambda *_a: {},
        sdk_auth_present_flags=lambda _p, present: {"sdk_api_key_present": present},
        build_auth_present_flags=lambda _h, _q: {},
        endpoint_effective=lambda url: url,
        endpoint_fingerprint=lambda url: {"endpoint_host": "fixture.test"},
        provider_signature=lambda p, m, u, _mode: f"{p}/{m}/{u}",
        get_http_session=_no_provider_call,
        get_gemini_client=_no_provider_call,
        extract_text_from_gemini_response=lambda _r: "",
        get_xai_client=lambda _key: fake_get_openai_client(None, _key),
        get_openrouter_client=lambda _key: fake_get_openai_client(None, _key),
        get_openai_client=fake_get_openai_client,
        extract_text_from_chat_completion=lambda _r: '{"ok": true}',
        summarize_llm_response=lambda **_kw: {
            "finish_reason": "stop",
            "text_length": 12,
            "usage": {
                "input_tokens": 100,
                "output_tokens": 50,
                "total_tokens": 150,
            },
        },
        exception_status_code=lambda _e: None,
        exception_response_text=lambda _e: "",
        classify_failure_type=lambda _s, _b, _t: "unknown",
        extract_provider_error_reason=lambda _b: None,
        sanitize_error_text=lambda text: text,
        capture_exception_metadata=lambda _e: {},
        new_trace_id=lambda: "trace-alias-test",
        new_span_id=lambda: "span-alias-test",
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


def _make_cfg(
    cost_profile: str = "value-default",
    model_alias_overrides: Any = (),
) -> SimpleNamespace:
    """Minimal cfg object exposing only what call_llm needs for alias resolution."""
    return SimpleNamespace(
        cost_profile=cost_profile,
        model_alias_overrides=model_alias_overrides,
        retry_max_attempts=1,
        retry_base_seconds=0.0,
        retry_max_seconds=0.0,
        retry_policy="none",
        gemini_auth_mode="auto",
    )


# --------------------------------------------------------- non-placeholder path


def test_non_placeholder_model_id_passes_through_unchanged() -> None:
    captured: Dict[str, Any] = {}
    deps = _build_succeeding_deps(captured)
    cfg = _make_cfg()

    result = call_llm(
        deps=deps,
        provider="openai",
        model_id="gpt-5",
        api_key_env="OPENAI_API_KEY",
        system_prompt="sys",
        user_content="usr",
        cfg=cfg,
    )

    assert result["ok"] is True
    assert result["meta"]["model_id"] == "gpt-5"
    assert result["meta"]["model_id_requested"] == "gpt-5"
    assert result["meta"]["_resolved_from_alias"] is False
    assert captured["chat_kwargs"]["model"] == "gpt-5"


# ------------------------------------------------------------ alias resolution


def test_alias_resolved_via_cli_overrides_takes_precedence(monkeypatch) -> None:
    captured: Dict[str, Any] = {}
    deps = _build_succeeding_deps(captured)
    cfg = _make_cfg(
        cost_profile="value-default",
        model_alias_overrides=[("QUALITY_SYNTH_CRITICAL_MODEL", "openai/gpt-5.2-pro")],
    )
    monkeypatch.setenv("QUALITY_SYNTH_CRITICAL_MODEL", "openai/gpt-5-mini")

    result = call_llm(
        deps=deps,
        provider="openai",
        model_id="${QUALITY_SYNTH_CRITICAL_MODEL}",
        api_key_env="OPENAI_API_KEY",
        system_prompt="sys",
        user_content="usr",
        cfg=cfg,
    )

    assert result["ok"] is True
    # CLI overrides win over env
    assert result["meta"]["model_id"] == "openai/gpt-5.2-pro"
    assert result["meta"]["model_id_requested"] == "${QUALITY_SYNTH_CRITICAL_MODEL}"
    assert result["meta"]["_resolved_from_alias"] is True
    assert captured["chat_kwargs"]["model"] == "openai/gpt-5.2-pro"


def test_alias_resolved_via_env_when_no_cli_override(monkeypatch) -> None:
    captured: Dict[str, Any] = {}
    deps = _build_succeeding_deps(captured)
    cfg = _make_cfg(cost_profile="value-default")
    monkeypatch.setenv("QUALITY_SYNTH_CRITICAL_MODEL", "openai/gpt-5-mini")

    result = call_llm(
        deps=deps,
        provider="openai",
        model_id="${QUALITY_SYNTH_CRITICAL_MODEL}",
        api_key_env="OPENAI_API_KEY",
        system_prompt="sys",
        user_content="usr",
        cfg=cfg,
    )

    assert result["meta"]["model_id"] == "openai/gpt-5-mini"
    assert result["meta"]["_resolved_from_alias"] is True
    assert captured["chat_kwargs"]["model"] == "openai/gpt-5-mini"


def test_unresolved_alias_raises_value_error(monkeypatch) -> None:
    """If neither CLI overrides, env, nor profile resolve the alias,
    resolve_cell_alias returns the bare placeholder — call_llm must raise
    rather than send `${...}` to the provider client."""
    import pytest

    captured: Dict[str, Any] = {}
    deps = _build_succeeding_deps(captured)
    cfg = _make_cfg(cost_profile="value-default")
    monkeypatch.delenv("NONEXISTENT_ALIAS_MODEL", raising=False)

    with pytest.raises(ValueError, match=r"alias unresolved|cycle"):
        call_llm(
            deps=deps,
            provider="openai",
            model_id="${NONEXISTENT_ALIAS_MODEL}",
            api_key_env="OPENAI_API_KEY",
            system_prompt="sys",
            user_content="usr",
            cfg=cfg,
        )


def test_alias_resolution_runs_after_disabled_providers_gate() -> None:
    """Disabled-provider check must trip BEFORE alias resolution so a blocked
    route doesn't trigger lookup work."""
    import pytest

    captured: Dict[str, Any] = {}
    deps = _build_succeeding_deps(captured)
    cfg = _make_cfg()

    with pytest.raises(RuntimeError, match="administratively disabled"):
        call_llm(
            deps=deps,
            provider="openai",
            model_id="${SOME_ALIAS}",  # would otherwise fail resolution
            api_key_env="OPENAI_API_KEY",
            system_prompt="sys",
            user_content="usr",
            cfg=cfg,
            disabled_providers={"openai"},
        )


def test_alias_resolution_skipped_when_no_placeholder() -> None:
    """Non-placeholder model_ids bypass resolve_cell_alias entirely (lazy)."""
    captured: Dict[str, Any] = {}
    deps = _build_succeeding_deps(captured)
    cfg = _make_cfg()

    # Use a unique model name that wouldn't ever match an alias mapping.
    result = call_llm(
        deps=deps,
        provider="openai",
        model_id="openai/gpt-5-mini-direct-passthrough",
        api_key_env="OPENAI_API_KEY",
        system_prompt="sys",
        user_content="usr",
        cfg=cfg,
    )
    assert result["meta"]["_resolved_from_alias"] is False
    assert result["meta"]["model_id"] == "openai/gpt-5-mini-direct-passthrough"


def test_alias_resolution_with_dict_cli_overrides() -> None:
    """`model_alias_overrides` can also be a dict (not just iterable of tuples)."""
    captured: Dict[str, Any] = {}
    deps = _build_succeeding_deps(captured)
    cfg = _make_cfg(
        model_alias_overrides={"ALIAS_X": "openai/gpt-5-mini"},
    )

    result = call_llm(
        deps=deps,
        provider="openai",
        model_id="${ALIAS_X}",
        api_key_env="OPENAI_API_KEY",
        system_prompt="sys",
        user_content="usr",
        cfg=cfg,
    )

    assert result["meta"]["model_id"] == "openai/gpt-5-mini"
    assert result["meta"]["_resolved_from_alias"] is True


def test_chain_cycle_resolution_raises_value_error(monkeypatch) -> None:
    """If resolve_cell_alias resolves `${X}` to a different placeholder `${Y}`,
    call_llm must fail-fast rather than send the placeholder through to the
    provider (or worse, recurse into another resolution attempt)."""
    import pytest

    captured: Dict[str, Any] = {}
    deps = _build_succeeding_deps(captured)
    cfg = _make_cfg()

    def fake_resolve(alias_or_model, cost_profile, *, cli_overrides=None, env=None):
        # Simulate `${X} -> ${Y}` chain (resolve returns a DIFFERENT placeholder).
        return "${Y_NEVER_RESOLVED}"

    import run_extraction_v5

    monkeypatch.setattr(run_extraction_v5, "resolve_cell_alias", fake_resolve)

    with pytest.raises(ValueError, match=r"alias unresolved|cycle"):
        call_llm(
            deps=deps,
            provider="openai",
            model_id="${X}",
            api_key_env="OPENAI_API_KEY",
            system_prompt="sys",
            user_content="usr",
            cfg=cfg,
        )
