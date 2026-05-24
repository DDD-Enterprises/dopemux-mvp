"""E7: per-request failover coverage.

The failover contract introduced in E7:

- On provider failure (5xx / timeout / 429 / quota_or_billing) the ladder
  advances to the next route immediately. ``call_llm_with_ladder`` continues
  while ``payload["escalation_trigger"]`` is truthy AND hops remain.
- The ladder iteration is bounded by ``min(escalation_max_hops+1, len(ladder))``;
  failover counts against this single shared bound — there is no separate
  failover budget.
- Per-route retries are fast-failover on non-terminal hops
  (``retry_attempts_override=1`` is passed down to ``call_llm``) and use the
  cfg-level ``retry_max_attempts`` on the final hop. The closure receives the
  override via kwarg and forwards it to ``call_llm``.
- Real client errors (4xx other than 429) do NOT failover — they should raise
  or fail the contract; failover semantics here are gated on the failure_type
  bucket returned by the LLM call.
- ``effective_max_attempts`` is logged when > 30, warning the operator of a
  potential cost-multiplication misconfiguration.

These tests use a SimpleNamespace cfg and a mock executor to isolate the
ladder iteration logic from real LLM transport.
"""

from __future__ import annotations

import logging
import sys
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = ROOT / "services" / "repo-truth-extractor"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

import llm_runtime  # noqa: E402
import run_extraction_v5 as runner  # noqa: E402


def _minimal_cfg(
    *,
    disabled_providers=(),
    provider_denylist=(),
    escalation_max_hops=2,
    retry_max_attempts=3,
    disable_escalation=False,
):
    return SimpleNamespace(
        disabled_providers=tuple(disabled_providers),
        provider_denylist=tuple(provider_denylist),
        escalation_max_hops=escalation_max_hops,
        retry_max_attempts=retry_max_attempts,
        disable_escalation=disable_escalation,
    )


def _deps():
    return runner._llm_runtime_deps()


def _scripted_executor(scripts, calls):
    """Build an execute_attempt that returns ``scripts[hop_index]`` on each
    hop and appends ``(route, hop_index, retry_attempts_override)`` to
    ``calls`` so tests can assert on what the loop attempted.

    ``scripts`` is a list of dicts that get returned verbatim (after the route
    field is injected). Use this to construct hop-by-hop scenarios.
    """

    def _exec(route, hop_index, *, retry_attempts_override=None):
        calls.append((route, hop_index, retry_attempts_override))
        if hop_index >= len(scripts):
            return {
                "response_text": "",
                "request_meta": {"failure_type": "test_overflow"},
                "artifacts": [],
                "route": route,
                "artifacts_ok": False,
                "escalation_trigger": "test_overflow",
            }
        payload = dict(scripts[hop_index])
        payload["route"] = route
        return payload

    return _exec


def _provider_failure_payload(failure_type):
    return {
        "response_text": "",
        "request_meta": {"failure_type": failure_type},
        "artifacts": [],
        "artifacts_ok": False,
        "escalation_trigger": "provider_failure",
    }


def _success_payload():
    return {
        "response_text": "{}",
        "request_meta": {},
        "artifacts": [{"id": "ok"}],
        "artifacts_ok": True,
        "escalation_trigger": None,
    }


# ---------------------------------------------------------------------------
# core failover semantics
# ---------------------------------------------------------------------------


def test_single_provider_failure_triggers_failover():
    cfg = _minimal_cfg(escalation_max_hops=2)
    ladder = [
        ("openrouter", "openai/gpt-5-mini", "OPENROUTER_API_KEY"),
        ("xai", "grok-4-1-fast-non-reasoning", "XAI_API_KEY"),
    ]
    scripts = [_provider_failure_payload("provider"), _success_payload()]
    calls: list = []
    result = llm_runtime.call_llm_with_ladder(
        _deps(),
        phase="A",
        step_id="A0",
        partition_id="A_P0001",
        routing_policy="value-default",
        routing_tier="extract",
        ladder=ladder,
        cfg=cfg,
        execute_attempt=_scripted_executor(scripts, calls),
    )
    assert [c[0][0] for c in calls] == ["openrouter", "xai"]
    assert result["request_meta"].get("route_hop_total") == 2
    assert result["request_meta"].get("escalation_trigger") is None


def test_two_consecutive_provider_failures_exhaust_failover():
    cfg = _minimal_cfg(escalation_max_hops=2)
    ladder = [
        ("openrouter", "openai/gpt-5-mini", "OPENROUTER_API_KEY"),
        ("xai", "grok-4-1-fast-non-reasoning", "XAI_API_KEY"),
        ("gemini", "gemini-3-flash-preview", "GEMINI_API_KEY"),
    ]
    scripts = [
        _provider_failure_payload("provider"),
        _provider_failure_payload("provider"),
        _provider_failure_payload("provider"),
    ]
    calls: list = []
    result = llm_runtime.call_llm_with_ladder(
        _deps(),
        phase="A",
        step_id="A0",
        partition_id="A_P0001",
        routing_policy="value-default",
        routing_tier="extract",
        ladder=ladder,
        cfg=cfg,
        execute_attempt=_scripted_executor(scripts, calls),
    )
    # max_hops = min(escalation_max_hops+1, len(ladder)) = min(3, 3) = 3.
    assert [c[0][0] for c in calls] == ["openrouter", "xai", "gemini"]
    # Final result reflects the last attempt's failure_type, not a synthetic
    # "all failed" marker (consistent with pre-E7 behavior).
    assert result["request_meta"].get("failure_type") == "provider"


def test_timeout_treated_as_provider_failure_for_failover():
    cfg = _minimal_cfg(escalation_max_hops=2)
    ladder = [
        ("openrouter", "openai/gpt-5-mini", "OPENROUTER_API_KEY"),
        ("xai", "grok-4-1-fast-non-reasoning", "XAI_API_KEY"),
    ]
    scripts = [_provider_failure_payload("timeout"), _success_payload()]
    calls: list = []
    llm_runtime.call_llm_with_ladder(
        _deps(),
        phase="A",
        step_id="A0",
        partition_id="A_P0001",
        routing_policy="value-default",
        routing_tier="extract",
        ladder=ladder,
        cfg=cfg,
        execute_attempt=_scripted_executor(scripts, calls),
    )
    # timeout-triggered escalation should reach the second hop.
    assert len(calls) == 2


def test_rate_limit_treated_as_provider_failure_for_failover():
    cfg = _minimal_cfg(escalation_max_hops=2)
    ladder = [
        ("openrouter", "openai/gpt-5-mini", "OPENROUTER_API_KEY"),
        ("xai", "grok-4-1-fast-non-reasoning", "XAI_API_KEY"),
    ]
    scripts = [_provider_failure_payload("rate_limit"), _success_payload()]
    calls: list = []
    llm_runtime.call_llm_with_ladder(
        _deps(),
        phase="A",
        step_id="A0",
        partition_id="A_P0001",
        routing_policy="value-default",
        routing_tier="extract",
        ladder=ladder,
        cfg=cfg,
        execute_attempt=_scripted_executor(scripts, calls),
    )
    assert len(calls) == 2


def test_ladder_of_length_one_means_no_failover():
    cfg = _minimal_cfg(escalation_max_hops=5)
    ladder = [("openrouter", "openai/gpt-5-mini", "OPENROUTER_API_KEY")]
    scripts = [_provider_failure_payload("provider")]
    calls: list = []
    llm_runtime.call_llm_with_ladder(
        _deps(),
        phase="A",
        step_id="A0",
        partition_id="A_P0001",
        routing_policy="value-default",
        routing_tier="extract",
        ladder=ladder,
        cfg=cfg,
        execute_attempt=_scripted_executor(scripts, calls),
    )
    # Even though escalation_max_hops=5, the ladder of length 1 caps max_hops
    # to 1 (min). So failover is impossible.
    assert len(calls) == 1


def test_disable_escalation_short_circuits_failover():
    cfg = _minimal_cfg(escalation_max_hops=5, disable_escalation=True)
    ladder = [
        ("openrouter", "openai/gpt-5-mini", "OPENROUTER_API_KEY"),
        ("xai", "grok-4-1-fast-non-reasoning", "XAI_API_KEY"),
    ]
    scripts = [_provider_failure_payload("provider"), _success_payload()]
    calls: list = []
    llm_runtime.call_llm_with_ladder(
        _deps(),
        phase="A",
        step_id="A0",
        partition_id="A_P0001",
        routing_policy="value-default",
        routing_tier="extract",
        ladder=ladder,
        cfg=cfg,
        execute_attempt=_scripted_executor(scripts, calls),
    )
    # disable_escalation forces max_hops=1, so failover is suppressed even
    # with a multi-route ladder.
    assert len(calls) == 1


# ---------------------------------------------------------------------------
# retry_attempts_override plumbing
# ---------------------------------------------------------------------------


def test_intermediate_hops_receive_retry_attempts_override_of_one():
    cfg = _minimal_cfg(escalation_max_hops=2, retry_max_attempts=5)
    ladder = [
        ("openrouter", "openai/gpt-5-mini", "OPENROUTER_API_KEY"),
        ("xai", "grok-4-1-fast-non-reasoning", "XAI_API_KEY"),
        ("gemini", "gemini-3-flash-preview", "GEMINI_API_KEY"),
    ]
    scripts = [
        _provider_failure_payload("provider"),
        _provider_failure_payload("provider"),
        _provider_failure_payload("provider"),
    ]
    calls: list = []
    llm_runtime.call_llm_with_ladder(
        _deps(),
        phase="A",
        step_id="A0",
        partition_id="A_P0001",
        routing_policy="value-default",
        routing_tier="extract",
        ladder=ladder,
        cfg=cfg,
        execute_attempt=_scripted_executor(scripts, calls),
    )
    # First two hops are non-terminal → retry_attempts_override = 1.
    # Last hop is terminal → None (use cfg default).
    overrides = [c[2] for c in calls]
    assert overrides == [1, 1, None]


def test_single_hop_ladder_uses_default_retry_policy():
    cfg = _minimal_cfg(escalation_max_hops=2, retry_max_attempts=5)
    ladder = [("openrouter", "openai/gpt-5-mini", "OPENROUTER_API_KEY")]
    scripts = [_success_payload()]
    calls: list = []
    llm_runtime.call_llm_with_ladder(
        _deps(),
        phase="A",
        step_id="A0",
        partition_id="A_P0001",
        routing_policy="value-default",
        routing_tier="extract",
        ladder=ladder,
        cfg=cfg,
        execute_attempt=_scripted_executor(scripts, calls),
    )
    # Only one hop, which IS the final hop, so retry_attempts_override is None.
    assert calls[0][2] is None


def test_backward_compatible_executor_without_override_kwarg():
    """A pre-E7 executor closure that does NOT accept retry_attempts_override
    should still work — the ladder catches TypeError and falls back to the
    two-arg form. Verifies the migration path for callers that haven't yet
    been updated."""
    cfg = _minimal_cfg(escalation_max_hops=2, retry_max_attempts=3)
    ladder = [
        ("openrouter", "openai/gpt-5-mini", "OPENROUTER_API_KEY"),
        ("xai", "grok-4-1-fast-non-reasoning", "XAI_API_KEY"),
    ]
    calls: list = []

    def _legacy_exec(route, hop_index):  # no override kwarg!
        calls.append((route, hop_index))
        return _success_payload() if hop_index == 1 else _provider_failure_payload("provider")

    llm_runtime.call_llm_with_ladder(
        _deps(),
        phase="A",
        step_id="A0",
        partition_id="A_P0001",
        routing_policy="value-default",
        routing_tier="extract",
        ladder=ladder,
        cfg=cfg,
        execute_attempt=_legacy_exec,
    )
    assert [c[0][0] for c in calls] == ["openrouter", "xai"]


# ---------------------------------------------------------------------------
# worst-case attempt bound + cost warning
# ---------------------------------------------------------------------------


def test_effective_max_attempts_warning_above_threshold(caplog):
    """When (max_hops - 1) + retry_max_attempts exceeds 30, the runtime logs
    a warning surfacing the cost risk. Below the threshold no warning fires.
    """
    cfg = _minimal_cfg(escalation_max_hops=10, retry_max_attempts=25)
    ladder = [
        ("openrouter", f"openai/gpt-5-{i}", "OPENROUTER_API_KEY")
        for i in range(11)
    ]
    scripts = [_success_payload()] + [
        _provider_failure_payload("provider") for _ in range(10)
    ]
    calls: list = []
    with caplog.at_level(logging.WARNING, logger="llm_runtime"):
        llm_runtime.call_llm_with_ladder(
            _deps(),
            phase="A",
            step_id="A0",
            partition_id="A_P0001",
            routing_policy="value-default",
            routing_tier="extract",
            ladder=ladder,
            cfg=cfg,
            execute_attempt=_scripted_executor(scripts, calls),
        )
    warning_msgs = [r.message for r in caplog.records if "effective_max_attempts" in r.message]
    assert warning_msgs, "expected effective_max_attempts warning above soft cap"


def test_effective_max_attempts_no_warning_under_threshold(caplog):
    cfg = _minimal_cfg(escalation_max_hops=2, retry_max_attempts=3)
    ladder = [
        ("openrouter", "openai/gpt-5-mini", "OPENROUTER_API_KEY"),
        ("xai", "grok-4-1-fast-non-reasoning", "XAI_API_KEY"),
    ]
    scripts = [_success_payload(), _success_payload()]
    calls: list = []
    with caplog.at_level(logging.WARNING, logger="llm_runtime"):
        llm_runtime.call_llm_with_ladder(
            _deps(),
            phase="A",
            step_id="A0",
            partition_id="A_P0001",
            routing_policy="value-default",
            routing_tier="extract",
            ladder=ladder,
            cfg=cfg,
            execute_attempt=_scripted_executor(scripts, calls),
        )
    warning_msgs = [r.message for r in caplog.records if "effective_max_attempts" in r.message]
    assert not warning_msgs, "no warning expected at default-ish settings"


def test_retry_override_one_does_not_sleep_after_terminal_attempt(monkeypatch):
    class _FailingSession:
        def post(self, *_args, **_kwargs):
            raise llm_runtime.requests.exceptions.Timeout("synthetic timeout")

    backoff_calls: list = []
    sleep_calls: list = []
    retry_events: list = []
    deps = replace(
        _deps(),
        live_llm_calls_blocked_for_tests=lambda: False,
        llm_base_url=lambda _provider, _cfg: "https://example.invalid",
        transport_for_provider=lambda _provider, _cfg: "openai_compat_http",
        resolve_api_key=lambda _provider, env: ("test-key", env),
        build_chat_payload=lambda *_args, **_kwargs: {"messages": []},
        serialize_payload_body=lambda _payload: "{}",
        measure_payload_bytes_from_body=lambda body: len(body),
        make_url=lambda *_args: "https://example.invalid/chat/completions",
        make_headers=lambda *_args: {"Authorization": "Bearer test"},
        sdk_auth_present_flags=lambda *_args: {},
        build_auth_present_flags=lambda *_args: {},
        endpoint_effective=lambda url: url,
        endpoint_fingerprint=lambda _url: {},
        provider_signature=lambda *_args: "sig",
        get_http_session=lambda: _FailingSession(),
        exception_status_code=lambda _exc: 503,
        exception_response_text=lambda _exc: "provider unavailable",
        classify_failure_type=lambda _status, _body, _text: "provider",
        extract_provider_error_reason=lambda _body: "provider_unavailable",
        capture_exception_metadata=lambda exc: {"exception_type": type(exc).__name__},
        new_trace_id=lambda: "trace-test",
        new_span_id=lambda: "span-test",
        should_retry=lambda *_args: True,
        backoff_seconds=lambda attempt, *_args: backoff_calls.append(attempt) or 2.0,
        is_spend_aborted=lambda: False,
        is_auth_classified_failure=lambda _failure: False,
    )
    cfg = SimpleNamespace(
        retry_policy="default",
        retry_max_attempts=3,
        retry_base_seconds=1.0,
        retry_max_seconds=5.0,
        gemini_auth_mode="auto",
    )
    monkeypatch.setattr(
        llm_runtime.time,
        "sleep",
        lambda seconds: sleep_calls.append(seconds),
    )

    result = llm_runtime.call_llm(
        deps,
        provider="openrouter",
        model_id="openai/gpt-5-mini",
        api_key_env="OPENROUTER_API_KEY",
        system_prompt="system",
        user_content="user",
        cfg=cfg,
        retry_attempts_override=1,
        retry_callback=lambda *args: retry_events.append(args),
    )

    assert result["ok"] is False
    assert result["meta"]["failure_type"] == "provider"
    assert backoff_calls == []
    assert sleep_calls == []
    assert retry_events == []
