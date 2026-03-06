from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest


def _load_v3():
    root = Path(__file__).resolve().parents[3]
    module_path = root / "services" / "repo-truth-extractor" / "run_extraction_v3.py"
    spec = importlib.util.spec_from_file_location("run_extraction_v3", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_v4():
    root = Path(__file__).resolve().parents[3]
    module_path = root / "services" / "repo-truth-extractor" / "run_extraction_v4.py"
    spec = importlib.util.spec_from_file_location("run_extraction_v4", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _make_cfg(runner, *, selected_s_steps=None):
    return runner.RunnerConfig(
        dry_run=True,
        max_files_docs=10,
        max_files_code=10,
        max_chars=10000,
        max_request_bytes=200000,
        file_truncate_chars=1000,
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
        routing_policy="cost",
        selected_s_steps=selected_s_steps,
    )


def test_no_flags_or_env_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = _load_v3()
    monkeypatch.delenv(runner.S_STEPS_ENV_VAR, raising=False)
    args = SimpleNamespace(s_steps=None)
    assert runner._get_s_step_controls(args) is None


def test_s_steps_are_normalized_to_canonical_order() -> None:
    runner = _load_v3()
    args = SimpleNamespace(s_steps="S2,S0")
    assert runner._get_s_step_controls(args) == ["S0", "S2"]


def test_duplicates_fail_closed() -> None:
    runner = _load_v3()
    with pytest.raises(RuntimeError):
        runner._get_s_step_controls(SimpleNamespace(s_steps="S0,S0"))


def test_invalid_step_fails_closed() -> None:
    runner = _load_v3()
    with pytest.raises(RuntimeError):
        runner._get_s_step_controls(SimpleNamespace(s_steps="S0,SX"))


def test_env_only_selection_works(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = _load_v3()
    monkeypatch.setenv(runner.S_STEPS_ENV_VAR, "S4,S1")
    assert runner._get_s_step_controls(SimpleNamespace(s_steps=None)) == ["S1", "S4"]


def test_cli_overrides_env(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = _load_v3()
    monkeypatch.setenv(runner.S_STEPS_ENV_VAR, "S4,S1")
    assert runner._get_s_step_controls(SimpleNamespace(s_steps="S2,S0")) == ["S0", "S2"]


def test_run_phase_s_passes_selected_steps(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    runner = _load_v3()
    captured = {}
    root = tmp_path / "run"
    dirs = {"root": root}
    for phase in runner.PHASES:
        phase_dir = root / runner.PHASE_DIR_NAMES[phase]
        dirs[phase] = phase_dir
        (phase_dir / "norm").mkdir(parents=True, exist_ok=True)
        (phase_dir / "inputs").mkdir(parents=True, exist_ok=True)
    (dirs["R"] / "norm" / "R0_CONTROL_PLANE_TRUTH_MAP.md").write_text("ok\n", encoding="utf-8")
    manifest_path = root / "manual_rulings" / "truth_pack.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text("{}\n", encoding="utf-8")

    def fake_manifest(*args, **kwargs):  # type: ignore[no-untyped-def]
        return manifest_path

    def fake_run_phase_inner(*args, **kwargs):  # type: ignore[no-untyped-def]
        captured["selected_step_ids"] = kwargs.get("selected_step_ids")

    monkeypatch.setattr(runner, "_write_s_truth_pack_provenance_manifest", fake_manifest)
    monkeypatch.setattr(runner, "_run_phase_inner", fake_run_phase_inner)
    runner.run_phase_S(dirs, _make_cfg(runner, selected_s_steps=("S0", "S2")))
    assert captured["selected_step_ids"] == ["S0", "S2"]


def test_v4_forwards_s_steps(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = _load_v4()
    captured = {}

    def fake_call(cmd, prompt_root=None):  # type: ignore[no-untyped-def]
        captured["cmd"] = list(cmd)
        captured["prompt_root"] = prompt_root
        return 0

    monkeypatch.setattr(runner, "call_v3_runner", fake_call)
    monkeypatch.setattr(runner, "verify_resume_proof_prompt_paths", lambda *args, **kwargs: None)
    rc = runner.run_pipeline(
        phase="S",
        run_id="test_s_v4_steps",
        dry_run=True,
        resume=False,
        partition_workers=1,
        executor="thread",
        doctor=False,
        doctor_auto_reprocess=False,
        doctor_reprocess_dry_run=False,
        doctor_reprocess_phases="",
        status=False,
        status_json=False,
        doctor_auth=False,
        preflight_providers=False,
        coverage_report=False,
        sync=False,
        routing_policy="cost",
        s_prompts=None,
        s_steps="S2,S0",
        disable_escalation=False,
        escalation_max_hops=2,
        batch_mode=False,
        batch_provider="auto",
        batch_poll_seconds=30,
        batch_wait_timeout_seconds=86400,
        batch_max_requests_per_job=2000,
        ui="plain",
        pretty=False,
        quiet=False,
        jsonl_events=False,
    )
    assert rc == 0
    assert "--s-steps" in captured["cmd"]
    assert "S2,S0" in captured["cmd"]
    assert captured["prompt_root"] is None


def test_v3_help_does_not_expose_s_extra_steps() -> None:
    root = Path(__file__).resolve().parents[3]
    script = root / "services" / "repo-truth-extractor" / "run_extraction_v3.py"
    result = subprocess.run(
        [sys.executable, str(script), "--help"],
        check=True,
        text=True,
        capture_output=True,
    )
    assert "--s-steps" in result.stdout
    assert "--s-extra-steps" not in result.stdout


def test_v4_help_does_not_expose_s_extra_steps() -> None:
    root = Path(__file__).resolve().parents[3]
    script = root / "services" / "repo-truth-extractor" / "run_extraction_v4.py"
    result = subprocess.run(
        [sys.executable, str(script), "--help"],
        check=True,
        text=True,
        capture_output=True,
    )
    combined = f"{result.stdout}\n{result.stderr}"
    assert "--s-steps" in combined
    assert "--s-extra-steps" not in combined
