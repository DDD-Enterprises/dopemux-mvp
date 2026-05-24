"""E7: --disable-provider kill-switch coverage.

The kill-switch wires from CLI flag → ``args._resolved_disabled_providers`` →
``cfg.disabled_providers`` (a Tuple[str, ...]) → consumed by
``llm_runtime.call_llm_with_ladder`` (E7). Before E7 the field existed but
ladder iteration ignored it; the CLI was effectively a no-op for the
multi-route failover path.

These tests exercise the post-E7 contract:

- A single ``--disable-provider`` value removes that provider from failover.
- Multiple disabled providers are all honored.
- All-providers-disabled returns an escalation_trigger that names the
  operator-explicit source (not the preflight-derived one).
- Matching is case-insensitive.
- ``derive_ladder_for_cell(disabled_providers=…)`` accepts the same input
  shape (sets, tuples, lists) and produces consistent output.
"""

from __future__ import annotations

import sys
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
    """Build a minimal cfg-like namespace exposing only the fields that
    ``llm_runtime.call_llm_with_ladder`` reads. Using ``SimpleNamespace``
    keeps the test surface independent of the much larger ``RunnerConfig``
    dataclass (and its required fields)."""
    return SimpleNamespace(
        disabled_providers=tuple(disabled_providers),
        provider_denylist=tuple(provider_denylist),
        escalation_max_hops=escalation_max_hops,
        retry_max_attempts=retry_max_attempts,
        disable_escalation=disable_escalation,
    )


def _success_executor(routes_seen):
    """Records each (route, hop_index) call and returns an artifacts_ok payload
    so the ladder loop terminates after the first attempt."""

    def _exec(route, hop_index, **_kwargs):
        routes_seen.append((route, hop_index))
        return {
            "response_text": "{}",
            "request_meta": {},
            "artifacts": [{"id": "ok"}],
            "route": route,
            "artifacts_ok": True,
            "escalation_trigger": None,
        }

    return _exec


def _force_escalate_executor(routes_seen):
    """Returns an escalation_trigger on every hop so the ladder iterates to
    exhaustion. Used to confirm the filtered ladder length controls how many
    attempts actually run."""

    def _exec(route, hop_index, **_kwargs):
        routes_seen.append((route, hop_index))
        return {
            "response_text": "",
            "request_meta": {"failure_type": "provider"},
            "artifacts": [],
            "route": route,
            "artifacts_ok": False,
            "escalation_trigger": "provider_failure",
        }

    return _exec


def _deps():
    return runner._llm_runtime_deps()


def test_single_disabled_provider_skipped_in_failover():
    cfg = _minimal_cfg(disabled_providers=("openrouter",))
    ladder = [
        ("openrouter", "openai/gpt-5-mini", "OPENROUTER_API_KEY"),
        ("xai", "grok-4-1-fast-non-reasoning", "XAI_API_KEY"),
    ]
    routes_seen: list = []
    result = llm_runtime.call_llm_with_ladder(
        _deps(),
        phase="A",
        step_id="A0",
        partition_id="A_P0001",
        routing_policy="value-default",
        routing_tier="extract",
        ladder=ladder,
        cfg=cfg,
        execute_attempt=_success_executor(routes_seen),
    )
    # Only the xai route should be attempted; openrouter is operator-disabled.
    assert len(routes_seen) == 1
    assert routes_seen[0][0][0] == "xai"
    assert result["request_meta"].get("failure_type") != "routing_empty_ladder"


def test_all_providers_disabled_returns_operator_disabled_trigger():
    cfg = _minimal_cfg(
        disabled_providers=("openrouter", "xai", "gemini"),
    )
    ladder = [
        ("openrouter", "openai/gpt-5-mini", "OPENROUTER_API_KEY"),
        ("xai", "grok-4-1-fast-non-reasoning", "XAI_API_KEY"),
    ]
    routes_seen: list = []
    result = llm_runtime.call_llm_with_ladder(
        _deps(),
        phase="A",
        step_id="A0",
        partition_id="A_P0001",
        routing_policy="value-default",
        routing_tier="extract",
        ladder=ladder,
        cfg=cfg,
        execute_attempt=_success_executor(routes_seen),
    )
    assert routes_seen == []
    assert result["escalation_trigger"] == "routing_all_routes_operator_disabled"
    assert "disabled_providers" in result["request_meta"]["provider_error_reason"]


def test_multiple_disabled_providers_honored():
    cfg = _minimal_cfg(disabled_providers=("openrouter", "xai"))
    ladder = [
        ("openrouter", "openai/gpt-5-mini", "OPENROUTER_API_KEY"),
        ("xai", "grok-4-1-fast-non-reasoning", "XAI_API_KEY"),
        ("gemini", "gemini-3-flash-preview", "GEMINI_API_KEY"),
    ]
    routes_seen: list = []
    llm_runtime.call_llm_with_ladder(
        _deps(),
        phase="A",
        step_id="A0",
        partition_id="A_P0001",
        routing_policy="value-default",
        routing_tier="extract",
        ladder=ladder,
        cfg=cfg,
        execute_attempt=_success_executor(routes_seen),
    )
    assert len(routes_seen) == 1
    assert routes_seen[0][0][0] == "gemini"


def test_disabled_provider_match_is_case_insensitive():
    cfg = _minimal_cfg(disabled_providers=("OPENROUTER",))
    ladder = [
        ("openrouter", "openai/gpt-5-mini", "OPENROUTER_API_KEY"),
        ("xai", "grok-4-1-fast-non-reasoning", "XAI_API_KEY"),
    ]
    routes_seen: list = []
    llm_runtime.call_llm_with_ladder(
        _deps(),
        phase="A",
        step_id="A0",
        partition_id="A_P0001",
        routing_policy="value-default",
        routing_tier="extract",
        ladder=ladder,
        cfg=cfg,
        execute_attempt=_success_executor(routes_seen),
    )
    assert len(routes_seen) == 1
    assert routes_seen[0][0][0] == "xai"


def test_combined_denylist_and_disabled_emits_combined_trigger():
    cfg = _minimal_cfg(
        disabled_providers=("xai",),
        provider_denylist=("openrouter",),
    )
    ladder = [
        ("openrouter", "openai/gpt-5-mini", "OPENROUTER_API_KEY"),
        ("xai", "grok-4-1-fast-non-reasoning", "XAI_API_KEY"),
    ]
    routes_seen: list = []
    result = llm_runtime.call_llm_with_ladder(
        _deps(),
        phase="A",
        step_id="A0",
        partition_id="A_P0001",
        routing_policy="value-default",
        routing_tier="extract",
        ladder=ladder,
        cfg=cfg,
        execute_attempt=_success_executor(routes_seen),
    )
    assert routes_seen == []
    assert result["escalation_trigger"] == "routing_all_routes_unusable_combined"
    reason = result["request_meta"]["provider_error_reason"]
    assert "provider_denylist" in reason
    assert "disabled_providers" in reason


def test_unrelated_disabled_provider_does_not_make_denylist_trigger_combined():
    cfg = _minimal_cfg(
        disabled_providers=("xai",),
        provider_denylist=("openrouter",),
    )
    ladder = [
        ("openrouter", "openai/gpt-5-mini", "OPENROUTER_API_KEY"),
    ]
    routes_seen: list = []
    result = llm_runtime.call_llm_with_ladder(
        _deps(),
        phase="A",
        step_id="A0",
        partition_id="A_P0001",
        routing_policy="value-default",
        routing_tier="extract",
        ladder=ladder,
        cfg=cfg,
        execute_attempt=_success_executor(routes_seen),
    )
    assert routes_seen == []
    assert result["escalation_trigger"] == "routing_all_routes_preflight_denylisted"
    reason = result["request_meta"]["provider_error_reason"]
    assert "provider_denylist:openrouter" in reason
    assert "disabled_providers" not in reason


def test_derive_ladder_for_cell_accepts_set_input():
    runner._derive_ladder_for_cell_cached.cache_clear()
    routes = runner.derive_ladder_for_cell(
        "value-default",
        "SYNTH",
        "HIGH",
        disabled_providers={"OPENROUTER"},  # set instead of tuple/list
    )
    # SYNTH/HIGH is openrouter-only → set form should filter it just like the
    # tuple/list form does.
    assert routes == []
