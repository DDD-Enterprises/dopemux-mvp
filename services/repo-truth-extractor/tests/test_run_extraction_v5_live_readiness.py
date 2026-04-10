from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_runner_module() -> types.ModuleType:
    module_path = _repo_root() / "services" / "repo-truth-extractor" / "run_extraction_v5.py"
    spec = importlib.util.spec_from_file_location("run_extraction_v5_live_readiness", module_path)
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
        "executor": "thread",
        "routing_policy": "cost",
        "disable_escalation": False,
        "escalation_max_hops": 2,
        "batch_mode": False,
        "batch_provider": "auto",
        "batch_poll_seconds": 30,
        "batch_wait_timeout_seconds": 1800,
        "batch_max_requests_per_job": 2000,
        "batch_submit_only": False,
        "webhook_url": "",
        "webhook_secret": "",
        "webhook_timeout_seconds": 5,
        "webhook_required": False,
        "webhook_auto_continue": False,
        "live_ok": True,
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
    }
    for key, value in defaults.items():
        object.__setattr__(cfg, key, value)
    return cfg


def test_call_llm_missing_api_key_returns_failure_meta_without_trace_crash(monkeypatch) -> None:
    runner = _load_runner_module()
    cfg = _make_cfg(runner)
    monkeypatch.setattr(runner, "_live_llm_calls_blocked_for_tests", lambda: False)
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    result = runner.call_llm(
        provider="xai",
        model_id="grok-4.20-beta-0309-non-reasoning",
        api_key_env="XAI_API_KEY",
        system_prompt="Return exactly OK.",
        user_content="Return the single token OK.",
        cfg=cfg,
    )
    assert result["ok"] is False
    assert result["meta"]["failure_type"] == "auth_missing"
    assert str(result["meta"]["trace_id"]).strip()


def test_route_readiness_summary_honors_benchmark_owned_lane(monkeypatch) -> None:
    runner = _load_runner_module()
    monkeypatch.setenv(
        "DPMX_BENCHMARK_ROUTE_OWNERSHIP",
        json.dumps(
            {
                "enabled": True,
                "mode": "strict_extraction_lane_owned_v1",
                "scope": "phase_a_json_managed",
                "target_phase": "A",
                "benchmark_case_id": "strict_extract_conflicting_evidence_v1",
                "route_id": "route_openai_gpt_5_4_v1",
                "surface_id": "surface_openai_api_v1",
                "surface_class": "direct_provider_api",
                "provider_name": "openai",
                "model_key": "openai/gpt-5.4",
                "provider_model_id": "gpt-5.4",
                "route_pin": "gpt-5.4",
                "api_key_env": "OPENAI_API_KEY",
                "strict_json_schema": True,
                "strict_passthrough_verified": True,
            },
            sort_keys=True,
            separators=(",", ":"),
        ),
    )
    summary = runner.derive_route_readiness_summary(["A"], "cost")
    required_routes = summary["routes"]
    assert required_routes
    assert {row["provider"] for row in required_routes} == {"openai"}
    assert {row["model_id"] for row in required_routes} == {"gpt-5.4"}
    assert summary["api_key_env_categories"]["required_active_route"] == ["OPENAI_API_KEY"]
