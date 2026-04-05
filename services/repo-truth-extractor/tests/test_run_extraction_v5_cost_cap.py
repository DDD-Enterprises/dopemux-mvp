from __future__ import annotations

import importlib.util
import json
from decimal import Decimal
from pathlib import Path
import sys

import pytest


def _load_runner_module():
    root = Path(__file__).resolve().parents[3]
    module_path = root / "services" / "repo-truth-extractor" / "run_extraction_v5.py"
    spec = importlib.util.spec_from_file_location(
        "run_extraction_v5_cost_cap",
        module_path,
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _make_cfg(runner, **overrides):
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
        "max_cost_usd": 0.10,
    }
    payload.update(overrides)
    return runner.RunnerConfig(**payload)


def test_initialize_spend_tracker_writes_empty_ledger_when_routes_are_priced(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    runner = _load_runner_module()
    cfg = _make_cfg(runner)
    monkeypatch.setattr(
        runner,
        "load_pricing_registry",
        lambda path=runner.PRICING_CONFIG_PATH: (
            {
                "openrouter/openai/gpt-5.4": {
                    "input_cost_per_m": Decimal("5.00"),
                    "output_cost_per_m": Decimal("20.00"),
                },
                "xai/grok-4.20-beta-0309-reasoning": {
                    "input_cost_per_m": Decimal("3.00"),
                    "output_cost_per_m": Decimal("15.00"),
                },
            },
            "sha-test",
        ),
    )
    monkeypatch.setattr(
        runner,
        "collect_provider_routes",
        lambda phases, routing_policy, selected_step_ids_by_phase=None: {
            "openrouter:openai/gpt-5.4:OPENROUTER_API_KEY": {
                "provider": "openrouter",
                "model_id": "openai/gpt-5.4",
                "api_key_env": "OPENROUTER_API_KEY",
            },
            "xai:grok-4.20-beta-0309-reasoning:XAI_API_KEY": {
                "provider": "xai",
                "model_id": "grok-4.20-beta-0309-reasoning",
                "api_key_env": "XAI_API_KEY",
            },
        },
    )

    snapshot = runner.initialize_spend_tracker(
        run_root=tmp_path,
        run_id="cost_cap_ok",
        cfg=cfg,
        phases=["A"],
    )

    assert snapshot is not None
    assert snapshot["max_cost_usd"] == 0.1
    assert snapshot["entries_total"] == 0
    ledger_path = tmp_path / runner.TELEMETRY_DIRNAME / runner.SPEND_LEDGER_FILENAME
    assert ledger_path.exists()


def test_initialize_spend_tracker_rejects_missing_route_pricing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    runner = _load_runner_module()
    cfg = _make_cfg(runner)
    monkeypatch.setattr(
        runner,
        "load_pricing_registry",
        lambda path=runner.PRICING_CONFIG_PATH: (
            {
                "openrouter/openai/gpt-5.4": {
                    "input_cost_per_m": Decimal("5.00"),
                    "output_cost_per_m": Decimal("20.00"),
                }
            },
            "sha-test",
        ),
    )
    monkeypatch.setattr(
        runner,
        "collect_provider_routes",
        lambda phases, routing_policy, selected_step_ids_by_phase=None: {
            "openrouter:openai/gpt-5.3-codex:OPENROUTER_API_KEY": {
                "provider": "openrouter",
                "model_id": "openai/gpt-5.3-codex",
                "api_key_env": "OPENROUTER_API_KEY",
            },
            "openrouter:openai/gpt-5.4:OPENROUTER_API_KEY": {
                "provider": "openrouter",
                "model_id": "openai/gpt-5.4",
                "api_key_env": "OPENROUTER_API_KEY",
            },
        },
    )

    with pytest.raises(RuntimeError, match="openrouter/openai/gpt-5.3-codex"):
        runner.initialize_spend_tracker(
            run_root=tmp_path,
            run_id="cost_cap_missing_price",
            cfg=cfg,
            phases=["A"],
        )


def test_initialize_spend_tracker_honors_selected_execution_step_for_route_coverage(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    runner = _load_runner_module()
    cfg = _make_cfg(runner, selected_execution_step="A2")
    monkeypatch.setattr(
        runner,
        "load_pricing_registry",
        lambda path=runner.PRICING_CONFIG_PATH: (
            {
                "xai/grok-4.20-beta-0309-reasoning": {
                    "input_cost_per_m": Decimal("3.00"),
                    "output_cost_per_m": Decimal("15.00"),
                },
                "xai/grok-4.20-beta-0309-non-reasoning": {
                    "input_cost_per_m": Decimal("2.00"),
                    "output_cost_per_m": Decimal("8.00"),
                },
            },
            "sha-test",
        ),
    )

    snapshot = runner.initialize_spend_tracker(
        run_root=tmp_path,
        run_id="cost_cap_a2_only",
        cfg=cfg,
        phases=["A"],
    )

    assert snapshot is not None
    assert snapshot["entries_total"] == 0
    ledger_path = tmp_path / runner.TELEMETRY_DIRNAME / runner.SPEND_LEDGER_FILENAME
    assert ledger_path.exists()


def test_update_run_manifest_startup_failure_marks_manifest_failed(
    tmp_path: Path,
) -> None:
    runner = _load_runner_module()
    manifest_path = tmp_path / "RUN_MANIFEST.json"
    manifest_path.write_text(
        json.dumps(
            {
                "run_id": "run_001",
                "run_status": "OK",
                "phase_status": "ready",
            }
        ),
        encoding="utf-8",
    )

    runner.update_run_manifest_startup_failure(
        tmp_path,
        failure_reason="cost_cap_setup_failed",
        failure_message="Pricing config missing route coverage for active target: openrouter/openai/gpt-5.3-codex",
    )

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["run_status"] == "FAILED"
    assert payload["phase_status"] == "startup_failed"
    assert payload["failure_reason"] == "cost_cap_setup_failed"
    assert "openrouter/openai/gpt-5.3-codex" in payload["failure_message"]


def test_record_request_cost_marks_breach_and_writes_ledger(tmp_path: Path) -> None:
    runner = _load_runner_module()
    runner.reset_spend_tracker()
    runner._ACTIVE_SPEND_TRACKER = runner.SpendTrackerState(
        run_root=tmp_path,
        run_id="cost_cap_breach",
        max_cost_usd=Decimal("0.10"),
        pricing_source="test",
        pricing_sha256="sha",
        pricing_registry={
            "openrouter/openai/gpt-5-mini": {
                "input_cost_per_m": Decimal("0.40"),
                "output_cost_per_m": Decimal("1.60"),
            }
        },
        total_cost_usd=Decimal("0"),
        cost_abort_triggered=False,
        abort_reason=None,
        entries=[],
    )
    meta = {
        "response_summary": {
            "usage": {
                "prompt_tokens": 100000,
                "completion_tokens": 100000,
                "total_tokens": 200000,
            }
        }
    }

    updated = runner.record_request_cost(
        meta,
        phase="A",
        step_id="A1",
        partition_id="A_P0001",
        provider="openrouter",
        model_id="openai/gpt-5-mini",
    )

    assert updated["failure_type"] == "cost_aborted"
    assert updated["cost_cap"]["cost_abort_triggered"] is True
    ledger_path = tmp_path / runner.TELEMETRY_DIRNAME / runner.SPEND_LEDGER_FILENAME
    payload = json.loads(ledger_path.read_text(encoding="utf-8"))
    assert payload["entries_total"] == 1
    assert payload["cost_abort_triggered"] is True
    assert payload["totals_by_phase_usd"]["A"] > 0.1


def test_call_llm_blocks_after_cost_abort(monkeypatch, tmp_path: Path) -> None:
    runner = _load_runner_module()
    runner.reset_spend_tracker()
    runner._ACTIVE_SPEND_TRACKER = runner.SpendTrackerState(
        run_root=tmp_path,
        run_id="already_aborted",
        max_cost_usd=Decimal("0.10"),
        pricing_source="test",
        pricing_sha256="sha",
        pricing_registry={},
        total_cost_usd=Decimal("0.11"),
        cost_abort_triggered=True,
        abort_reason="cost_cap_exceeded total_cost_usd=0.11 max_cost_usd=0.1",
        entries=[],
    )
    cfg = _make_cfg(runner)
    monkeypatch.setattr(runner, "_live_llm_calls_blocked_for_tests", lambda: False)
    monkeypatch.setattr(runner, "resolve_api_key", lambda provider, env: ("key", env))

    result = runner.call_llm(
        provider="openrouter",
        model_id="openai/gpt-5-mini",
        api_key_env="OPENROUTER_API_KEY",
        system_prompt="Return OK.",
        user_content="Return OK.",
        cfg=cfg,
    )

    assert result["ok"] is False
    assert result["meta"]["failure_type"] == "cost_aborted"
    assert result["meta"]["provider_error_reason"].startswith("cost_cap_exceeded")
