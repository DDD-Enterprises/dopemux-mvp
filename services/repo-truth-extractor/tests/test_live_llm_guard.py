from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest


def _load_runner_module(filename: str, module_name: str):
    root = Path(__file__).resolve().parents[3]
    module_path = root / "services" / "repo-truth-extractor" / filename
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _make_cfg(runner):
    return runner.RunnerConfig(
        dry_run=False,
        max_files_docs=10,
        max_files_code=10,
        max_chars=10000,
        max_request_bytes=200000,
        file_truncate_chars=500,
        home_scan_mode="safe",
        resume=False,
        fail_fast_auth=False,
        gemini_auth_mode="auto",
        gemini_transport="sdk",
        openai_transport="openai_sdk",
        xai_transport="openai_sdk",
        retry_policy="none",
        retry_max_attempts=1,
        retry_base_seconds=0.0,
        retry_max_seconds=0.0,
        phase_auth_fail_threshold=5,
        partition_workers=1,
        debug_phase_inputs=False,
        fail_fast_missing_inputs=False,
        routing_policy="balanced_grok_openrouter",
    )


@pytest.mark.parametrize(
    ("filename", "module_name"),
    [
        ("run_extraction_v3.py", "run_extraction_v3_live_guard"),
        ("run_extraction_v5.py", "run_extraction_v5_live_guard"),
    ],
)
def test_live_llm_guard_blocks_by_default_in_test_context(
    filename: str,
    module_name: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _load_runner_module(filename, module_name)
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "unit::live_guard")
    monkeypatch.delenv(runner.RTE_DISABLE_LIVE_LLM_IN_TESTS_ENV, raising=False)
    monkeypatch.delenv(runner.RTE_ALLOW_LIVE_LLM_IN_TESTS_ENV, raising=False)

    assert runner._live_llm_calls_blocked_for_tests() is True


@pytest.mark.parametrize(
    ("filename", "module_name"),
    [
        ("run_extraction_v3.py", "run_extraction_v3_live_guard_allow"),
        ("run_extraction_v5.py", "run_extraction_v5_live_guard_allow"),
    ],
)
def test_live_llm_guard_allow_override_disables_block(
    filename: str,
    module_name: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _load_runner_module(filename, module_name)
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "unit::live_guard")
    monkeypatch.setenv(runner.RTE_ALLOW_LIVE_LLM_IN_TESTS_ENV, "1")
    monkeypatch.delenv(runner.RTE_DISABLE_LIVE_LLM_IN_TESTS_ENV, raising=False)

    assert runner._live_llm_calls_blocked_for_tests() is False


@pytest.mark.parametrize(
    ("filename", "module_name"),
    [
        ("run_extraction_v3.py", "run_extraction_v3_live_guard_call"),
        ("run_extraction_v5.py", "run_extraction_v5_live_guard_call"),
    ],
)
def test_call_llm_raises_when_live_calls_blocked(
    filename: str,
    module_name: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _load_runner_module(filename, module_name)
    cfg = _make_cfg(runner)
    monkeypatch.setenv(runner.RTE_DISABLE_LIVE_LLM_IN_TESTS_ENV, "1")
    monkeypatch.delenv(runner.RTE_ALLOW_LIVE_LLM_IN_TESTS_ENV, raising=False)

    with pytest.raises(RuntimeError, match="Live LLM call blocked in test context"):
        runner.call_llm(
            provider="openai",
            model_id="gpt-5-mini",
            api_key_env="OPENAI_API_KEY",
            system_prompt="system",
            user_content="user",
            cfg=cfg,
        )
