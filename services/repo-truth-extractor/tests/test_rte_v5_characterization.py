from __future__ import annotations

import importlib.util
import json
import os
import shutil
import sys
from pathlib import Path
from types import SimpleNamespace
from types import ModuleType

import pytest


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_module(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_v5() -> ModuleType:
    return _load_module(
        _repo_root() / "services" / "repo-truth-extractor" / "run_extraction_v5.py",
        "run_extraction_v5_characterization",
    )


def _load_v4() -> ModuleType:
    return _load_module(
        _repo_root() / "services" / "repo-truth-extractor" / "run_extraction_v4.py",
        "run_extraction_v4_characterization",
    )


def test_upgrades_and_extractor_runner_resolution_preserves_v5_authority() -> None:
    src_path = str(_repo_root() / "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    from dopemux.commands import extractor_commands

    repo_root = _repo_root()

    assert extractor_commands._extractor_runner_path(repo_root, "v5").name == "run_extraction_v5.py"
    assert extractor_commands._extractor_runner_path(repo_root, "v4").name == "run_extraction_v4.py"
    assert extractor_commands._extractor_runner_path(repo_root, "v3").name == "run_extraction_v3.py"


def test_truth_run_finds_v5_runner_directly() -> None:
    src_path = str(_repo_root() / "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    from dopemux.commands import extract_commands

    runner_path = extract_commands._find_runner(_repo_root())
    assert runner_path is not None
    assert runner_path.name == "run_extraction_v5.py"
    assert runner_path == _repo_root() / "services" / "repo-truth-extractor" / "run_extraction_v5.py"


def test_truth_cli_still_routes_through_pipeline_runner() -> None:
    cli_source = (_repo_root() / "src" / "dopemux" / "cli.py").read_text(encoding="utf-8")

    assert "def truth_command(" in cli_source
    assert "runner = PipelineRunner(project_path)" in cli_source
    assert "runner.run_all(" in cli_source


def test_import_surface_stability_for_packet_symbols() -> None:
    runner = _load_v5()
    expected_symbols = {
        "ACTIVE_ROUTING_LADDERS",
        "FIRST_LIVE_PRESET_DEFAULT_CAP_USD",
        "INTERACTIVE_SAFE_BATCH_WAIT_SECONDS",
        "OutputLayout",
        "PHASE_DIR_NAMES",
        "PROMPT_ROOT_ENV_VAR",
        "RETRY_COST_REPORT_FILENAME",
        "RunnerConfig",
        "UI",
        "UiConfig",
        "_prompt_hash_report_for_phase",
        "build_chat_payload",
        "call_llm",
        "call_llm_with_ladder",
        "configure_output_layout",
        "current_doctor_root",
        "derive_route_readiness_summary",
        "get_phase_prompts",
        "get_run_dirs",
        "latest_run_id_path",
        "promptset_fingerprint",
        "run_provider_preflight",
        "write_coverage_rollup",
        "write_resume_proof",
    }

    missing = sorted(symbol for symbol in expected_symbols if not hasattr(runner, symbol))
    assert not missing, f"Missing expected run_extraction_v5 exports: {missing}"


def test_output_layout_defaults_preserve_v5_contract_roots(tmp_path: Path) -> None:
    runner = _load_v5()

    layout = runner.configure_output_layout(tmp_path, None)
    assert layout.extraction_root == (tmp_path / runner.V5_EXTRACTION_ROOT).resolve()
    assert layout.runs_root == (tmp_path / runner.V5_RUNS_ROOT).resolve()
    assert layout.doctor_root == (tmp_path / runner.V5_DOCTOR_ROOT).resolve()
    assert layout.latest_run_file == (tmp_path / runner.V5_LATEST_RUN_FILE).resolve()


def test_run_phase_sp_requires_actual_r_inputs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    runner = _load_v5()
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        runner,
        "_plan_sp_phase_impl",
        lambda dirs, to_items: {
            "input_sources": {(tmp_path / "x.json"): "X"},
            "r_input_count": 0,
            "plan": SimpleNamespace(precollected_items=[]),
        },
    )
    monkeypatch.setattr(
        runner,
        "_run_phase_inner",
        lambda *args, **kwargs: captured.setdefault("run_phase_inner", True),
    )

    with pytest.raises(RuntimeError, match="Phase SP requires R norm outputs"):
        runner.run_phase_SP({"root": tmp_path}, object())

    assert "run_phase_inner" not in captured


def test_v4_run_pipeline_preserves_s_int_prompt_root_and_sync_behavior(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = _load_v4()
    captured: dict[str, object] = {}

    def _fake_build_v3_cmd(**kwargs):
        captured["build_v3_cmd"] = kwargs
        return ["python", "run_extraction_v3.py", "--phase", str(kwargs["phase"])]

    def _fake_call_v3_runner(cmd, prompt_root=None):
        captured["call_v3_runner"] = {"cmd": list(cmd), "prompt_root": prompt_root}
        return 0

    def _fake_sync_run_to_v4(run_id: str, sync_phases):
        captured["sync_run_to_v4"] = {"run_id": run_id, "sync_phases": list(sync_phases)}

    monkeypatch.setattr(runner, "build_v3_cmd", _fake_build_v3_cmd)
    monkeypatch.setattr(runner, "call_v3_runner", _fake_call_v3_runner)
    monkeypatch.setattr(runner, "sync_run_to_v4", _fake_sync_run_to_v4)
    monkeypatch.setattr(runner, "load_promptset", lambda: {"all_phase_order": ["A", "S_INT"]})

    rc = runner.run_pipeline(
        phase="S_INT",
        run_id="v4_s_int_probe",
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
        sync=True,
        routing_policy="cost",
        disable_escalation=False,
        escalation_max_hops=2,
        batch_mode=False,
        batch_provider="auto",
        batch_poll_seconds=30,
        batch_wait_timeout_seconds=1800,
        batch_max_requests_per_job=2000,
        step=None,
        s_prompts=None,
        s_steps=None,
        d0_max_files=None,
        d1_max_files=None,
        ui="plain",
        pretty=False,
        quiet=False,
        jsonl_events=False,
    )

    assert rc == 0
    assert captured["build_v3_cmd"]["phase"] == "S_INT"
    assert captured["call_v3_runner"]["prompt_root"] is None
    assert "sync_run_to_v4" not in captured


def test_v4_non_s_phase_still_forwards_v4_prompt_root(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = _load_v4()
    captured: dict[str, object] = {}

    monkeypatch.setattr(runner, "build_v3_cmd", lambda **kwargs: ["python", "run_extraction_v3.py"])
    def _fake_call_v3_runner(cmd, prompt_root=None):
        captured["prompt_root"] = prompt_root
        return 0

    monkeypatch.setattr(runner, "call_v3_runner", _fake_call_v3_runner)
    monkeypatch.setattr(runner, "verify_resume_proof_prompt_paths", lambda run_id, prompt_root: None)
    monkeypatch.setattr(runner, "sync_run_to_v4", lambda run_id, sync_phases: None)
    monkeypatch.setattr(runner, "load_promptset", lambda: {"all_phase_order": ["A"]})

    rc = runner.run_pipeline(
        phase="A",
        run_id="v4_prompt_root_probe",
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
        disable_escalation=False,
        escalation_max_hops=2,
        batch_mode=False,
        batch_provider="auto",
        batch_poll_seconds=30,
        batch_wait_timeout_seconds=1800,
        batch_max_requests_per_job=2000,
        step=None,
        s_prompts=None,
        s_steps=None,
        d0_max_files=None,
        d1_max_files=None,
        ui="plain",
        pretty=False,
        quiet=False,
        jsonl_events=False,
    )

    assert rc == 0
    assert captured["prompt_root"] == runner.V4_PROMPT_ROOT


def test_blocked_promptset_exits_fail_closed_and_writes_blocked_artifacts(tmp_path: Path) -> None:
    repo_root = _repo_root()
    prompt_root = tmp_path / "blocked_promptset"
    prompt_root.mkdir(parents=True, exist_ok=True)
    source_prompt = (
        repo_root
        / "services"
        / "repo-truth-extractor"
        / "promptsets"
        / "v4"
        / "prompts"
        / "PROMPT_A0_REPO_CONTROL_INVENTORY___PARTITION_PLAN.md"
    )
    shutil.copy2(source_prompt, prompt_root / source_prompt.name)

    output_root = tmp_path / "artifacts"
    env = dict(os.environ)
    env["REPO_TRUTH_EXTRACTOR_PROMPT_ROOT"] = str(prompt_root)

    proc = __import__("subprocess").run(
        [
            sys.executable,
            str(repo_root / "services" / "repo-truth-extractor" / "run_extraction_v5.py"),
            "--phase",
            "A",
            "--dry-run",
            "--run-id",
            "blocked_promptset_probe",
            "--ui",
            "plain",
            "--output-root",
            str(output_root),
        ],
        cwd=str(repo_root),
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert proc.returncode == 2

    run_root = output_root / "runs" / "blocked_promptset_probe"
    coverage = json.loads((run_root / "COVERAGE_ROLLUP.json").read_text(encoding="utf-8"))
    resume = json.loads((run_root / "RESUME_PROOF.json").read_text(encoding="utf-8"))
    proof = json.loads((run_root / "PROOF_PACK.json").read_text(encoding="utf-8"))

    assert coverage["run_status"] == "BLOCKED"
    assert coverage["blocked_promptset"] is True
    assert resume["blocked_promptset"] is True
    assert proof["run_status"] == "BLOCKED"
    assert proof["blocked_reason"] == "PROMPTSET_INVALID"
