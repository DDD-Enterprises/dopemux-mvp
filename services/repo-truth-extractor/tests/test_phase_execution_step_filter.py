from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

import pytest


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_module(filename: str, module_name: str):
    root = _repo_root()
    module_path = root / "services" / "repo-truth-extractor" / filename
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_execution_step_filter_accepts_single_matching_step() -> None:
    runner = _load_module("run_extraction_v3.py", "run_extraction_v3_step_filter")
    args = argparse.Namespace(phase="D", step="d1", s_steps=None)
    assert runner._get_execution_step_filter(args) == "D1"


def test_execution_step_filter_rejects_invalid_execution_combinations() -> None:
    runner = _load_module("run_extraction_v3.py", "run_extraction_v3_step_filter_invalid")

    with pytest.raises(RuntimeError, match="does not support --phase ALL"):
        runner._get_execution_step_filter(argparse.Namespace(phase="ALL", step="D0", s_steps=None))

    with pytest.raises(RuntimeError, match="does not belong to phase D"):
        runner._get_execution_step_filter(argparse.Namespace(phase="D", step="X0", s_steps=None))

    with pytest.raises(RuntimeError, match="exactly one step id"):
        runner._get_execution_step_filter(argparse.Namespace(phase="D", step="D0,D1", s_steps=None))


def test_run_phase_d_uses_selected_execution_step_filter(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    runner = _load_module("run_extraction_v3.py", "run_extraction_v3_run_phase_d")
    captured = {}

    def fake_run_phase_inner(phase, dirs, cfg, collector, item_filter, **kwargs):  # type: ignore[no-untyped-def]
        captured["phase"] = phase
        captured["selected_step_ids"] = kwargs.get("selected_step_ids")

    monkeypatch.setattr(runner, "_run_phase_inner", fake_run_phase_inner)

    cfg = runner.RunnerConfig(
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
        executor="thread",
        debug_phase_inputs=False,
        fail_fast_missing_inputs=False,
        routing_policy="balanced_grok_openrouter",
        selected_execution_step="D0",
    )
    dirs = {"root": tmp_path, "D": tmp_path / "D"}

    runner.run_phase_D(dirs, cfg)

    assert captured["phase"] == "D"
    assert captured["selected_step_ids"] == ["D0"]


def test_v4_build_v3_cmd_forwards_step() -> None:
    runner = _load_module("run_extraction_v4.py", "run_extraction_v4_step_filter")
    cmd = runner.build_v3_cmd(
        phase="D",
        run_id="rid",
        dry_run=True,
        resume=True,
        partition_workers=2,
        executor="process",
        doctor=False,
        doctor_auto_reprocess=False,
        doctor_reprocess_dry_run=False,
        doctor_reprocess_phases="",
        status=False,
        status_json=False,
        doctor_auth=False,
        preflight_providers=False,
        coverage_report=False,
        routing_policy="balanced_grok_openrouter",
        disable_escalation=False,
        escalation_max_hops=2,
        batch_mode=False,
        batch_provider="auto",
        batch_poll_seconds=30,
        batch_wait_timeout_seconds=60,
        batch_max_requests_per_job=10,
        step="D1",
        ui="plain",
        pretty=False,
        quiet=False,
        jsonl_events=False,
    )
    assert "--step" in cmd
    step_index = cmd.index("--step")
    assert cmd[step_index + 1] == "D1"
