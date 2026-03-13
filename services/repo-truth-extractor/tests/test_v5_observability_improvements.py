"""Tests for v5 pipeline observability improvements.

Covers:
1. call_llm() total retry delay tracking
2. _read_repair_counters() thread-safe snapshot
3. _get_http_session() singleton reuse
"""
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch


def _load_runner_module() -> types.ModuleType:
    root = Path(__file__).resolve().parents[3]
    module_path = root / "services" / "repo-truth-extractor" / "run_extraction_v5.py"
    spec = importlib.util.spec_from_file_location("run_extraction_v5", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _make_cfg(runner: types.ModuleType) -> object:
    """Build a RunnerConfig with object.__setattr__ (frozen dataclass)."""
    cfg = runner.RunnerConfig.__new__(runner.RunnerConfig)
    defaults = {
        "dry_run": False,
        "max_files_docs": 10,
        "max_files_code": 10,
        "max_chars": 50000,
        "max_request_bytes": 100000,
        "file_truncate_chars": 10000,
        "home_scan_mode": "off",
        "resume": False,
        "fail_fast_auth": False,
        "gemini_auth_mode": "auto",
        "gemini_transport": "native",
        "openai_transport": "openai_compat_http",
        "xai_transport": "openai_compat_http",
        "retry_policy": "default",
        "retry_max_attempts": 3,
        "retry_base_seconds": 1.0,
        "retry_max_seconds": 8.0,
        "phase_auth_fail_threshold": 5,
        "partition_workers": 1,
        "debug_phase_inputs": False,
        "fail_fast_missing_inputs": False,
        "executor": "thread",
        "routing_policy": "cascade",
        "disable_escalation": False,
        "escalation_max_hops": 2,
        "batch_mode": False,
        "batch_provider": "auto",
        "batch_poll_seconds": 30,
        "batch_wait_timeout_seconds": 86400,
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
    }
    for k, v in defaults.items():
        object.__setattr__(cfg, k, v)
    return cfg


def test_call_llm_retry_logs_total_delay() -> None:
    """call_llm() returns total_retry_delay_seconds in meta after exhausting retries."""
    runner = _load_runner_module()
    cfg = _make_cfg(runner)

    sleep_calls: list[float] = []

    def fake_sleep(seconds: float) -> None:
        sleep_calls.append(seconds)

    mock_session = MagicMock()
    mock_session.post.side_effect = ConnectionError("fake")

    with (
        patch.object(runner, "_live_llm_calls_blocked_for_tests", return_value=False),
        patch.object(runner, "llm_base_url", return_value="http://fake"),
        patch.object(runner, "transport_for_provider", return_value="openai_compat_http"),
        patch.object(runner, "resolve_api_key", return_value=("fake-key", "FAKE_KEY")),
        patch.object(runner, "build_chat_payload", return_value=({}, "{}")),
        patch.object(runner, "should_retry", return_value=True),
        patch.object(runner, "_get_http_session", return_value=mock_session),
        patch.object(runner.time, "sleep", side_effect=fake_sleep),
    ):
        result = runner.call_llm(
            provider="openrouter",
            model_id="test/model",
            api_key_env="FAKE_KEY",
            system_prompt="test",
            user_content="test",
            cfg=cfg,
        )

    assert result["ok"] is False
    meta = result["meta"]
    assert "total_retry_delay_seconds" in meta
    assert isinstance(meta["total_retry_delay_seconds"], float)
    assert meta["total_retry_delay_seconds"] >= 0.0


def test_read_repair_counters_snapshot() -> None:
    """_read_repair_counters() returns a copy, not a reference to the global dict."""
    runner = _load_runner_module()

    # Set known values
    with runner._REPAIR_COUNTERS_LOCK:
        runner._REPAIR_COUNTERS["attempted"] = 42
        runner._REPAIR_COUNTERS["succeeded"] = 10
        runner._REPAIR_COUNTERS["failed_ambiguous"] = 5

    snapshot = runner._read_repair_counters()

    # Values must match
    assert snapshot == {"attempted": 42, "succeeded": 10, "failed_ambiguous": 5}

    # Must be a copy - mutating snapshot must not affect global
    snapshot["attempted"] = 9999
    assert runner._REPAIR_COUNTERS["attempted"] == 42

    # Reset for other tests
    with runner._REPAIR_COUNTERS_LOCK:
        runner._REPAIR_COUNTERS["attempted"] = 0
        runner._REPAIR_COUNTERS["succeeded"] = 0
        runner._REPAIR_COUNTERS["failed_ambiguous"] = 0


def test_http_session_is_reused() -> None:
    """_get_http_session() returns the same Session object on repeated calls."""
    runner = _load_runner_module()

    # Reset the module-level session to force fresh creation
    runner._HTTP_SESSION = None

    s1 = runner._get_http_session()
    s2 = runner._get_http_session()

    assert s1 is s2, "Expected the same Session instance to be returned"
    assert hasattr(s1, "get") and hasattr(s1, "post"), "Must be a requests.Session"

    # Clean up - reset so other tests aren't affected
    runner._HTTP_SESSION = None
