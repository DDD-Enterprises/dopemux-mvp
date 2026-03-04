from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

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


def _write_prompt(path: Path, step_id: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# {step_id}\n\nOUTPUTS:\n- {step_id}_OUT.json\n", encoding="utf-8")


def _make_prompt_root(tmp_path: Path, *, with_registry: bool, invalid_registry: bool = False) -> Path:
    prompt_root = tmp_path / "prompts"
    for step_id in [f"S{i}" for i in range(7)]:
        _write_prompt(prompt_root / f"PROMPT_{step_id}_LEGACY.md", step_id)
    if with_registry:
        registry_root = prompt_root / "phase_s"
        registry_root.mkdir(parents=True, exist_ok=True)
        steps = {}
        for step_id in [f"S{i}" for i in range(7)]:
            filename = f"PROMPT_{step_id}_REGISTRY.md"
            _write_prompt(registry_root / filename, step_id)
            steps[step_id] = {"prompt_path": filename, "tier": "synthesis"}
        if invalid_registry:
            steps["S7"] = {"prompt_path": "PROMPT_S7.md", "tier": "synthesis"}
        payload = {"version": 1, "phase": "S", "steps": steps}
        (registry_root / "registry.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return prompt_root


def _make_cfg(runner):
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
    )


def test_auto_uses_registry_when_present(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    runner = _load_v3()
    prompt_root = _make_prompt_root(tmp_path, with_registry=True)
    monkeypatch.setenv(runner.PROMPT_ROOT_ENV_VAR, str(prompt_root))
    runner.set_active_s_prompts_mode("auto")
    specs = runner.get_phase_prompts("S")
    assert {spec.step_id for spec in specs} == {f"S{i}" for i in range(7)}
    assert all(spec.source == "registry" for spec in specs)
    assert all(spec.tier_override == "synthesis" for spec in specs)


def test_auto_falls_back_to_legacy_when_registry_missing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    runner = _load_v3()
    prompt_root = _make_prompt_root(tmp_path, with_registry=False)
    monkeypatch.setenv(runner.PROMPT_ROOT_ENV_VAR, str(prompt_root))
    runner.set_active_s_prompts_mode("auto")
    specs = runner.get_phase_prompts("S")
    assert all(spec.source == "legacy" for spec in specs)


def test_forced_registry_fails_closed_when_invalid(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    runner = _load_v3()
    prompt_root = _make_prompt_root(tmp_path, with_registry=True, invalid_registry=True)
    monkeypatch.setenv(runner.PROMPT_ROOT_ENV_VAR, str(prompt_root))
    runner.set_active_s_prompts_mode("registry")
    with pytest.raises(RuntimeError):
        runner.get_phase_prompts("S")


def test_forced_legacy_wins_even_when_registry_exists(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    runner = _load_v3()
    prompt_root = _make_prompt_root(tmp_path, with_registry=True)
    monkeypatch.setenv(runner.PROMPT_ROOT_ENV_VAR, str(prompt_root))
    runner.set_active_s_prompts_mode("legacy")
    specs = runner.get_phase_prompts("S")
    assert all(spec.source == "legacy" for spec in specs)


def test_run_phase_s_emits_mode_line_once(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    runner = _load_v3()
    prompt_root = _make_prompt_root(tmp_path, with_registry=True)
    monkeypatch.setenv(runner.PROMPT_ROOT_ENV_VAR, str(prompt_root))
    runner.set_active_s_prompts_mode("auto")
    root = tmp_path / "run"
    dirs = {"root": root}
    for phase in runner.PHASES:
        phase_dir = root / runner.PHASE_DIR_NAMES[phase]
        dirs[phase] = phase_dir
        (phase_dir / "norm").mkdir(parents=True, exist_ok=True)
        (phase_dir / "inputs").mkdir(parents=True, exist_ok=True)
    (dirs["R"] / "norm" / "R0_CONTROL_PLANE_TRUTH_MAP.md").write_text("ok\n", encoding="utf-8")
    monkeypatch.setattr(runner, "_run_phase_inner", lambda *args, **kwargs: None)
    caplog.set_level("INFO")
    runner.run_phase_S(dirs, _make_cfg(runner))
    matches = [record.message for record in caplog.records if record.message.startswith("S_PROMPTS_MODE=")]
    assert matches == ["S_PROMPTS_MODE=registry"]


def test_v4_forwards_s_prompts_and_keeps_phase_s_off_v4_prompt_root(monkeypatch: pytest.MonkeyPatch) -> None:
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
        run_id="test_s_v4",
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
        s_prompts="registry",
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
    assert "--s-prompts" in captured["cmd"]
    assert "registry" in captured["cmd"]
    assert captured["prompt_root"] is None
