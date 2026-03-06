from __future__ import annotations

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


def _base_cfg(runner, **overrides):  # type: ignore[no-untyped-def]
    payload = dict(
        dry_run=False,
        max_files_docs=25,
        max_files_code=25,
        max_chars=100000,
        max_request_bytes=200000,
        file_truncate_chars=500,
        home_scan_mode="safe",
        resume=False,
        fail_fast_auth=False,
        gemini_auth_mode="auto",
        gemini_transport="sdk",
        openai_transport="openai_sdk",
        xai_transport="openai_sdk",
        retry_policy="default",
        retry_max_attempts=4,
        retry_base_seconds=2.0,
        retry_max_seconds=30.0,
        phase_auth_fail_threshold=5,
        partition_workers=1,
        debug_phase_inputs=False,
        fail_fast_missing_inputs=False,
        executor="thread",
        routing_policy="balanced_grok_openrouter",
        disable_escalation=False,
        escalation_max_hops=2,
        batch_mode=False,
        batch_provider="auto",
        batch_poll_seconds=30,
        batch_wait_timeout_seconds=86400,
        batch_max_requests_per_job=2000,
        batch_submit_only=False,
        webhook_url="",
        webhook_secret="",
        webhook_timeout_seconds=5,
        webhook_required=False,
        webhook_auto_continue=False,
        live_ok=False,
        selected_s_steps=None,
        selected_execution_step=None,
        d0_max_files=None,
        d1_max_files=None,
        provider_denylist=(),
    )
    payload.update(overrides)
    return runner.RunnerConfig(**payload)


def test_parse_positive_optional_int_validates() -> None:
    runner = _load_module("run_extraction_v3.py", "run_extraction_v3_d_caps_parse")
    assert runner._parse_positive_optional_int(None, "--d0-max-files") is None
    assert runner._parse_positive_optional_int("", "--d0-max-files") is None
    assert runner._parse_positive_optional_int("15", "--d0-max-files") == 15

    with pytest.raises(RuntimeError, match="must be > 0"):
        runner._parse_positive_optional_int("0", "--d0-max-files")

    with pytest.raises(RuntimeError, match="must be > 0"):
        runner._parse_positive_optional_int("-1", "--d1-max-files")

    with pytest.raises(RuntimeError, match="must be a positive integer"):
        runner._parse_positive_optional_int("abc", "--d1-max-files")


def test_apply_file_cap_is_deterministic_and_lexicographic(tmp_path: Path) -> None:
    runner = _load_module("run_extraction_v3.py", "run_extraction_v3_d_caps_sort")
    cfg = _base_cfg(runner, d0_max_files=2, d1_max_files=3)
    paths = [
        str(tmp_path / "docs" / "z.md"),
        str(tmp_path / "docs" / "a.md"),
        str(tmp_path / "docs" / "m.md"),
    ]

    kept_first, dropped_first = runner._apply_file_cap("D0", "D_P0001", paths, cfg, tmp_path)
    kept_second, dropped_second = runner._apply_file_cap("D0", "D_P0001", list(reversed(paths)), cfg, tmp_path)

    assert kept_first == ["docs/a.md", "docs/m.md"]
    assert dropped_first == ["docs/z.md"]
    assert kept_first == kept_second
    assert dropped_first == dropped_second


def test_apply_file_cap_only_affects_d0_and_d1(tmp_path: Path) -> None:
    runner = _load_module("run_extraction_v3.py", "run_extraction_v3_d_caps_scope")
    cfg = _base_cfg(runner, d0_max_files=1, d1_max_files=1)
    paths = [str(tmp_path / "docs" / "b.md"), str(tmp_path / "docs" / "a.md")]

    kept_d0, dropped_d0 = runner._apply_file_cap("D0", "D_P0001", paths, cfg, tmp_path)
    kept_d2, dropped_d2 = runner._apply_file_cap("D2", "D_P0001", paths, cfg, tmp_path)

    assert kept_d0 == ["docs/a.md"]
    assert dropped_d0 == ["docs/b.md"]
    assert kept_d2 == paths
    assert dropped_d2 == []
    assert runner._step_file_cap("D0", cfg) == 1
    assert runner._step_file_cap("D1", cfg) == 1
    assert runner._step_file_cap("D2", cfg) is None


def test_pressure_cap_metadata_is_deterministic() -> None:
    runner = _load_module("run_extraction_v3.py", "run_extraction_v3_d_caps_meta")
    payload = runner._pressure_cap_metadata(
        phase="D",
        step_id="D1",
        partition_id="D_P0028",
        cap=15,
        kept=["docs/a.md", "docs/b.md"],
        dropped=["docs/y.md", "docs/z.md"],
    )
    assert payload == {
        "phase": "D",
        "step": "D1",
        "partition_id": "D_P0028",
        "cap": 15,
        "kept": ["docs/a.md", "docs/b.md"],
        "dropped": ["docs/y.md", "docs/z.md"],
    }


def test_v4_build_v3_cmd_forwards_d_pressure_flags() -> None:
    runner = _load_module("run_extraction_v4.py", "run_extraction_v4_d_caps_forward")
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
        d0_max_files=15,
        d1_max_files=12,
        ui="plain",
        pretty=False,
        quiet=False,
        jsonl_events=False,
    )
    assert "--d0-max-files" in cmd
    assert cmd[cmd.index("--d0-max-files") + 1] == "15"
    assert "--d1-max-files" in cmd
    assert cmd[cmd.index("--d1-max-files") + 1] == "12"

