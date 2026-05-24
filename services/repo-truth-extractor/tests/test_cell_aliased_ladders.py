"""E7: derive_ladder_for_cell + infer_route_for_model coverage.

Validates the new cell-aliased ladder derivation API:

- derive_ladder_for_cell returns the expected route for each (profile, lane,
  capability_tier) cell.
- CLI alias overrides propagate to the resolved model_id.
- Env vars propagate (and the snapshot participates in the cache key so a
  later env change correctly invalidates the cached entry).
- Cache invalidation: changing overrides between calls returns the new value.
- Unresolved alias raises ValueError with an operator-actionable message.
- Disabled providers filter routes out of the returned ladder.
- infer_route_for_model has deterministic prefix-based mapping and fails closed
  on unknown prefixes.

These tests rely on the cost_profile registry shipped in E1/E2; if those
profile entries change, the assertions below need to follow.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = ROOT / "services" / "repo-truth-extractor"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

import run_extraction_v5 as runner  # noqa: E402


# ---------------------------------------------------------------------------
# infer_route_for_model
# ---------------------------------------------------------------------------


def test_infer_route_openrouter_openai_prefix():
    route = runner.infer_route_for_model("openai/gpt-5.4")
    assert route == ("openrouter", "openai/gpt-5.4", "OPENROUTER_API_KEY")


def test_infer_route_openrouter_anthropic_prefix():
    route = runner.infer_route_for_model("anthropic/claude-sonnet-4.6")
    assert route == (
        "openrouter",
        "anthropic/claude-sonnet-4.6",
        "OPENROUTER_API_KEY",
    )


def test_infer_route_direct_gemini():
    route = runner.infer_route_for_model("gemini-3-flash-preview")
    assert route == ("gemini", "gemini-3-flash-preview", "GEMINI_API_KEY")


def test_infer_route_direct_xai_grok():
    route = runner.infer_route_for_model("grok-4-1-fast-non-reasoning")
    assert route == (
        "xai",
        "grok-4-1-fast-non-reasoning",
        "XAI_API_KEY",
    )


def test_infer_route_unknown_prefix_fails_closed():
    with pytest.raises(ValueError, match="no provider prefix matched"):
        runner.infer_route_for_model("frobnitz/foo-bar-1.2")


def test_infer_route_empty_input_raises():
    with pytest.raises(ValueError, match="empty/non-string"):
        runner.infer_route_for_model("")
    with pytest.raises(ValueError, match="empty/non-string"):
        runner.infer_route_for_model("   ")


# ---------------------------------------------------------------------------
# derive_ladder_for_cell
# ---------------------------------------------------------------------------


def _reset_ladder_cache():
    """LRU cache leaks across tests; clear before any test that mutates env
    or relies on a fresh resolution."""
    runner._derive_ladder_for_cell_cached.cache_clear()


def _make_cfg(**overrides):
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
        "retry_policy": "default",
        "retry_max_attempts": 1,
        "retry_base_seconds": 0.0,
        "retry_max_seconds": 0.0,
        "phase_auth_fail_threshold": 1,
        "partition_workers": 1,
        "debug_phase_inputs": False,
        "fail_fast_missing_inputs": False,
        "routing_policy": "balanced_openrouter",
        "cost_profile": "value-default",
    }
    payload.update(overrides)
    return runner.RunnerConfig(**payload)


def _fake_partition_context(**_kwargs):
    return (
        "PARTITION_PATH=/tmp/e7",
        {
            "files_included": 1,
            "files_skipped": 0,
            "context_bytes": 20,
            "redaction_hits": 0,
        },
    )


def _capture_ladder_success(captured):
    def fake_call_llm_with_ladder(**kwargs):
        ladder = [tuple(route) for route in kwargs["ladder"]]
        captured.append(
            {
                "ladder": ladder,
                "routing_tier": kwargs.get("routing_tier"),
            }
        )
        artifacts = [{"artifact_name": "OUT.json", "payload": {"items": []}}]
        return {
            "response_text": json.dumps({"artifacts": artifacts}),
            "request_meta": {
                "failure_type": None,
                "status_code": 200,
                "provider": ladder[0][0],
                "model_id": ladder[0][1],
                "route_attempts": [],
                "route_hop_total": 1,
            },
            "artifacts": artifacts,
            "route": ladder[0],
            "artifacts_ok": True,
            "escalation_trigger": None,
        }

    return fake_call_llm_with_ladder


def _execute_single_partition(monkeypatch, tmp_path, *, phase, step_id, partition):
    prompt_path = tmp_path / f"PROMPT_{phase}_{step_id}.md"
    prompt_path.write_text("Goal: OUT.json\n", encoding="utf-8")
    phase_dir = tmp_path / f"{phase}_phase"
    (phase_dir / "raw").mkdir(parents=True, exist_ok=True)
    prompt_spec = runner.PromptSpec(
        step_id=step_id,
        prompt_path=prompt_path,
        output_artifacts=("OUT.json",),
    )
    monkeypatch.setattr(runner, "_step_contract_for", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(runner, "build_partition_context", _fake_partition_context)
    captured = []
    monkeypatch.setattr(
        runner,
        "call_llm_with_ladder",
        _capture_ladder_success(captured),
    )
    stats = runner.execute_step_for_partitions(
        phase=phase,
        prompt_spec=prompt_spec,
        partitions=[partition],
        phase_dir=phase_dir,
        cfg=_make_cfg(),
    )
    assert stats["failed"] == 0
    assert captured
    return captured


def test_build_cell_alias_key_matches_registry_convention():
    assert (
        runner._build_cell_alias_key("value-default", "SYNTH", "CRITICAL")
        == "VALUE_DEFAULT_SYNTH_CRITICAL_MODEL"
    )


def test_derive_ladder_for_cell_value_default_synth_high():
    _reset_ladder_cache()
    routes = runner.derive_ladder_for_cell("value-default", "SYNTH", "HIGH")
    assert routes == [
        ("openrouter", "anthropic/claude-sonnet-4.6", "OPENROUTER_API_KEY"),
    ]


def test_derive_ladder_for_cell_quality_synth_critical():
    _reset_ladder_cache()
    routes = runner.derive_ladder_for_cell("quality", "SYNTH", "CRITICAL")
    assert routes == [
        ("openrouter", "anthropic/claude-opus-4.6", "OPENROUTER_API_KEY"),
    ]


def test_derive_ladder_for_cell_cli_override_propagates():
    _reset_ladder_cache()
    routes = runner.derive_ladder_for_cell(
        "value-default",
        "SYNTH",
        "HIGH",
        cli_overrides={"VALUE_DEFAULT_SYNTH_HIGH_MODEL": "openai/gpt-5-mini"},
    )
    assert routes == [
        ("openrouter", "openai/gpt-5-mini", "OPENROUTER_API_KEY"),
    ]


def test_derive_ladder_for_cell_env_var_propagates(monkeypatch):
    _reset_ladder_cache()
    monkeypatch.setenv("VALUE_DEFAULT_SYNTH_HIGH_MODEL", "anthropic/claude-opus-4.7")
    routes = runner.derive_ladder_for_cell("value-default", "SYNTH", "HIGH")
    assert routes == [
        ("openrouter", "anthropic/claude-opus-4.7", "OPENROUTER_API_KEY"),
    ]


def test_derive_ladder_for_cell_empty_env_var_is_unset(monkeypatch):
    _reset_ladder_cache()
    monkeypatch.setenv("VALUE_DEFAULT_SYNTH_HIGH_MODEL", "")
    routes = runner.derive_ladder_for_cell("value-default", "SYNTH", "HIGH")
    assert routes == [
        ("openrouter", "anthropic/claude-sonnet-4.6", "OPENROUTER_API_KEY"),
    ]


def test_derive_ladder_for_cell_cache_invalidates_on_override_change():
    _reset_ladder_cache()
    first = runner.derive_ladder_for_cell(
        "value-default",
        "SYNTH",
        "HIGH",
        cli_overrides={"VALUE_DEFAULT_SYNTH_HIGH_MODEL": "openai/gpt-5-mini"},
    )
    second = runner.derive_ladder_for_cell(
        "value-default",
        "SYNTH",
        "HIGH",
        cli_overrides={"VALUE_DEFAULT_SYNTH_HIGH_MODEL": "anthropic/claude-haiku-4.5"},
    )
    assert first[0][1] == "openai/gpt-5-mini"
    assert second[0][1] == "anthropic/claude-haiku-4.5"


def test_derive_ladder_for_cell_unresolved_alias_raises():
    _reset_ladder_cache()
    # SYNTH_CRITICAL_FALLBACK exists only on the quality profile; calling it
    # against value-default has no alias entry → must raise rather than send
    # a literal placeholder downstream.
    with pytest.raises(ValueError, match="alias .* unresolved"):
        runner.derive_ladder_for_cell(
            "value-default", "SYNTH", "CRITICAL_FALLBACK"
        )


def test_derive_ladder_for_cell_disabled_provider_filters_route():
    _reset_ladder_cache()
    routes = runner.derive_ladder_for_cell(
        "value-default",
        "SYNTH",
        "HIGH",
        disabled_providers=["openrouter"],
    )
    # The only route in the value-default SYNTH/HIGH cell is openrouter → filter
    # drops it and the list is empty so callers can decide to fall through.
    assert routes == []


def test_derive_ladder_for_cell_unsupported_stage_raises():
    _reset_ladder_cache()
    with pytest.raises(NotImplementedError, match="reserved for E8"):
        runner.derive_ladder_for_cell(
            "value-default", "SYNTH", "HIGH", stage="full_ladder"
        )


def test_non_json_route_uses_cost_profile_alias_primary_with_legacy_tail():
    _reset_ladder_cache()
    cfg = _make_cfg()
    route_info = runner.resolve_effective_step_route("S", "S1", cfg)
    ladder = route_info["ladder"]
    assert route_info["reason"] == "cost_profile_cell_alias_primary_legacy_tail"
    assert route_info["cell_alias_key"] == "VALUE_DEFAULT_SYNTH_CRITICAL_MODEL"
    assert ladder[0] == (
        "openrouter",
        "anthropic/claude-opus-4.6",
        "OPENROUTER_API_KEY",
    )
    assert len(ladder) > 1
    assert len(ladder) == len(set(ladder))


def test_model_alias_override_changes_production_primary_route():
    _reset_ladder_cache()
    cfg = _make_cfg(
        model_alias_overrides=(
            ("VALUE_DEFAULT_SYNTH_CRITICAL_MODEL", "openai/gpt-5-mini"),
        )
    )
    route_info = runner.resolve_effective_step_route("S", "S1", cfg)
    assert route_info["ladder"][0] == (
        "openrouter",
        "openai/gpt-5-mini",
        "OPENROUTER_API_KEY",
    )


def test_json_managed_route_stays_contract_owned():
    cfg = _make_cfg()
    contract = runner._step_contract_for("D", "D1")
    route_info = runner.resolve_effective_step_route(
        "D", "D1", cfg, step_contract=contract
    )
    assert route_info["reason"] == "contract_lane_primary_strict"
    assert route_info["provider"] == "openrouter"
    assert route_info["model_id"] == "openai/gpt-5.3-codex"


def test_route_ladder_from_route_info_preserves_full_partition_ladder():
    route_info = {
        "ladder": [
            ("openrouter", "openai/gpt-5-mini", "OPENROUTER_API_KEY"),
            ["xai", "grok-4-1-fast-non-reasoning", "XAI_API_KEY"],
        ]
    }
    assert runner._route_ladder_from_route_info(route_info) == [
        ("openrouter", "openai/gpt-5-mini", "OPENROUTER_API_KEY"),
        ("xai", "grok-4-1-fast-non-reasoning", "XAI_API_KEY"),
    ]


def test_execute_step_passes_cost_profile_ladder_to_runtime(monkeypatch, tmp_path):
    _reset_ladder_cache()
    captured = _execute_single_partition(
        monkeypatch,
        tmp_path,
        phase="S",
        step_id="S1",
        partition={"id": "S_P0001", "paths": ["/tmp/e7"]},
    )
    ladder = captured[0]["ladder"]
    assert ladder[0] == (
        "openrouter",
        "anthropic/claude-opus-4.6",
        "OPENROUTER_API_KEY",
    )
    assert len(ladder) > 1


def test_partition_tier_override_passes_partition_ladder_to_runtime(
    monkeypatch, tmp_path
):
    _reset_ladder_cache()
    captured = _execute_single_partition(
        monkeypatch,
        tmp_path,
        phase="A",
        step_id="A1",
        partition={
            "id": "A_P0001",
            "paths": ["/tmp/e7"],
            "tier_override": "synthesis",
        },
    )
    ladder = captured[0]["ladder"]
    assert captured[0]["routing_tier"] == "synthesis"
    assert ladder[0] == (
        "openrouter",
        "anthropic/claude-sonnet-4.6",
        "OPENROUTER_API_KEY",
    )
    assert len(ladder) > 1
