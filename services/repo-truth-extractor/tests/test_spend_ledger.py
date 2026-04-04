from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _runner_script() -> Path:
    return _repo_root() / "services" / "repo-truth-extractor" / "run_extraction_v5.py"


def _load_runner_module() -> types.ModuleType:
    module_path = _runner_script()
    spec = importlib.util.spec_from_file_location("run_extraction_v5_spend_tests", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_spend_ledger_module() -> types.ModuleType:
    module_path = _repo_root() / "services" / "repo-truth-extractor" / "lib" / "spend_ledger.py"
    spec = importlib.util.spec_from_file_location("spend_ledger_spend_tests", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _make_cfg(runner: types.ModuleType):
    cfg = runner.RunnerConfig.__new__(runner.RunnerConfig)
    defaults = {
        "dry_run": False,
        "max_files_docs": 10,
        "max_files_code": 10,
        "max_chars": 50000,
        "max_request_bytes": 100000,
        "file_truncate_chars": 10000,
        "home_scan_mode": "safe",
        "resume": False,
        "fail_fast_auth": False,
        "gemini_auth_mode": "auto",
        "gemini_transport": "sdk",
        "openai_transport": "openai_sdk",
        "xai_transport": "openai_sdk",
        "retry_policy": "none",
        "retry_max_attempts": 1,
        "retry_base_seconds": 0.0,
        "retry_max_seconds": 0.0,
        "phase_auth_fail_threshold": 5,
        "partition_workers": 1,
        "debug_phase_inputs": False,
        "fail_fast_missing_inputs": False,
        "executor": "thread",
        "routing_policy": "cost",
        "disable_escalation": False,
        "escalation_max_hops": 2,
        "batch_mode": False,
        "batch_provider": "auto",
        "batch_poll_seconds": 1,
        "batch_wait_timeout_seconds": 60,
        "batch_max_requests_per_job": 2000,
        "batch_submit_only": False,
        "webhook_url": "",
        "webhook_secret": "",
        "webhook_timeout_seconds": 5,
        "webhook_required": False,
        "webhook_auto_continue": False,
        "live_ok": False,
        "selected_s_steps": None,
        "selected_execution_step": None,
        "d0_max_files": None,
        "d1_max_files": None,
        "provider_denylist": (),
        "compare_mode": None,
        "compare_model": None,
        "compare_provider": None,
        "compare_steps": None,
        "prescan_dir": None,
        "router": None,
        "max_cost_usd": None,
        "ledger": None,
        "fl_int_provider_timeout_seconds": 180,
        "fl_int_f0_batch_timeout_seconds": 210,
    }
    for key, value in defaults.items():
        object.__setattr__(cfg, key, value)
    return cfg


def test_model_cost_rate_exact_and_fuzzy_match() -> None:
    spend_ledger = _load_spend_ledger_module()

    exact = spend_ledger.get_model_cost_rate(
        provider="openrouter",
        model_id="openai/gpt-5-mini",
    )
    fuzzy = spend_ledger.get_model_cost_rate(model_id="gpt-5-mini", route="openai/gpt-5-mini")

    assert exact["pricing_key"] == "openrouter/openai/gpt-5-mini"
    assert exact["match_type"] == "exact"
    assert fuzzy["pricing_key"] in {
        "openai/gpt-5-mini",
        "gpt-5-mini",
    }
    assert fuzzy["match_type"] in {"exact", "fuzzy"}
    assert fuzzy["unknown_model"] is False


def test_unknown_fallback_increments_legacy_and_new_counters(tmp_path: Path) -> None:
    spend_ledger = _load_spend_ledger_module()
    ledger = spend_ledger.SpendLedger(tmp_path, "fallback_run")

    priced = ledger.accumulate(
        "A",
        1000,
        500,
        provider="mystery",
        model_id="weird-model",
        route="mystery/weird-model",
    )

    assert priced["unknown_model"] is True
    assert ledger.record.fallback_usage_count == 1
    assert ledger.record.unknown_model_events == 1


def test_persistence_round_trip_preserves_model_provider_and_fallback_counts(
    tmp_path: Path,
) -> None:
    spend_ledger = _load_spend_ledger_module()
    ledger = spend_ledger.SpendLedger(tmp_path, "round_trip", max_cost_usd=3.5)
    ledger.accumulate(
        "R",
        1200,
        600,
        provider="openrouter",
        model_id="openai/gpt-5-mini",
    )
    ledger.accumulate(
        "R",
        300,
        200,
        provider="mystery",
        model_id="weird-model",
    )

    reloaded = spend_ledger.SpendLedger(tmp_path, "round_trip")

    assert reloaded.record.total_cost_usd == pytest.approx(ledger.record.total_cost_usd)
    assert "openrouter/openai/gpt-5-mini" in reloaded.record.models
    assert "openrouter" in reloaded.record.providers
    assert reloaded.record.fallback_usage_count == 1
    assert reloaded.record.unknown_model_events == 1


def test_retries_and_escalations_count_as_additional_model_usage(tmp_path: Path) -> None:
    spend_ledger = _load_spend_ledger_module()
    ledger = spend_ledger.SpendLedger(tmp_path, "retry_counts")

    ledger.accumulate(
        "Q",
        100,
        50,
        provider="openai",
        model_id="gpt-5-mini",
        route="openai/gpt-5-mini",
    )
    ledger.accumulate(
        "Q",
        100,
        50,
        provider="openai",
        model_id="gpt-5-mini",
        route="openai/gpt-5-mini",
    )

    model_row = ledger.record.models["openai/gpt-5-mini"]
    provider_row = ledger.record.providers["openai"]
    phase_row = ledger.record.phases["Q"]

    assert model_row.usage_count == 2
    assert provider_row.usage_count == 2
    assert phase_row.models["openai/gpt-5-mini"].usage_count == 2


def test_batch_watch_cost_breach_stops_after_first_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _load_runner_module()
    spend_ledger = _load_spend_ledger_module()
    cfg = _make_cfg(runner)
    ledger = spend_ledger.SpendLedger(tmp_path, "batch_watch_breach", max_cost_usd=0.00001)
    object.__setattr__(cfg, "ledger", ledger)
    object.__setattr__(cfg, "max_cost_usd", 0.00001)

    phase_dir = tmp_path / "A_repo_control_plane"
    batch_dir = phase_dir / "batch"
    raw_dir = phase_dir / "raw"
    batch_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = tmp_path / "PROMPT_A1.md"
    prompt_path.write_text("Return OUT.json", encoding="utf-8")
    (phase_dir / "inputs").mkdir(parents=True, exist_ok=True)

    write_payload = {
        "run_id": "batch_watch_breach",
        "phase_id": "A",
        "jobs": [
            {
                "run_id": "batch_watch_breach",
                "phase_id": "A",
                "step_id": "A1",
                "partition_id": "A_P0001",
                "provider_id": "openai",
                "model_id": "gpt-5-mini",
                "api_key_env": "OPENAI_API_KEY",
                "job_id": "job-1",
                "state": "submitted",
                "estimated_input_tokens": 100,
                "estimated_output_tokens": 100000,
            },
            {
                "run_id": "batch_watch_breach",
                "phase_id": "A",
                "step_id": "A1",
                "partition_id": "A_P0002",
                "provider_id": "openai",
                "model_id": "gpt-5-mini",
                "api_key_env": "OPENAI_API_KEY",
                "job_id": "job-2",
                "state": "submitted",
                "estimated_input_tokens": 10,
                "estimated_output_tokens": 10,
            },
        ],
    }
    (batch_dir / "BATCH_JOB_INDEX.json").write_text(
        json.dumps(write_payload), encoding="utf-8"
    )

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(
        runner,
        "get_phase_prompts",
        lambda phase: [
            runner.PromptSpec(
                step_id="A1",
                prompt_path=prompt_path,
                output_artifacts=("OUT.json",),
            )
        ],
    )

    class FakeBatchClient:
        def __init__(self) -> None:
            self.polled: list[str] = []
            self.fetched: list[str] = []

        def poll(self, job_id: str) -> str:
            self.polled.append(job_id)
            return "completed"

        def fetch_results(self, job_id: str):
            self.fetched.append(job_id)
            if job_id == "job-1":
                return [
                    runner.BatchResult(
                        custom_id="A_P0001",
                        output_text=json.dumps(
                            {
                                "artifacts": [
                                    {
                                        "artifact_name": "OUT.json",
                                        "payload": {"schema": "itemlist@v1", "items": []},
                                    }
                                ]
                            }
                        ),
                        meta={
                            "response": {
                                "body": {
                                    "usage": {
                                        "prompt_tokens": 100,
                                        "completion_tokens": 100000,
                                    }
                                }
                            }
                        },
                    )
                ]
            return [
                runner.BatchResult(
                    custom_id="A_P0002",
                    output_text=json.dumps(
                        {
                            "artifacts": [
                                {
                                    "artifact_name": "OUT.json",
                                    "payload": {"schema": "itemlist@v1", "items": []},
                                }
                            ]
                        }
                    ),
                )
            ]

        def cancel(self, job_id: str) -> None:
            return None

    fake_client = FakeBatchClient()
    monkeypatch.setattr(runner, "build_batch_client", lambda provider, api_key, cfg: fake_client)

    with pytest.raises(runner.CostLimitExceededError):
        runner.run_batch_watch(
            root=tmp_path,
            run_id="batch_watch_breach",
            phase="A",
            dirs={"root": tmp_path, "A": phase_dir},
            cfg=cfg,
            ui=None,
        )

    assert (raw_dir / "A1__A_P0001.json").exists()
    assert not (raw_dir / "A1__A_P0002.json").exists()
    assert fake_client.fetched == ["job-1"]
