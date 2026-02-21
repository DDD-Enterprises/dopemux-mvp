from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


RUNNER_PATH = Path(__file__).resolve().parents[2] / "services" / "repo-truth-extractor" / "run_extraction_v3.py"
SPEC = importlib.util.spec_from_file_location("run_extraction_v3", RUNNER_PATH)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


def make_dirs(tmp_path: Path) -> dict[str, Path]:
    dirs = {"root": tmp_path}
    for phase, dirname in runner.PHASE_DIR_NAMES.items():
        phase_dir = tmp_path / dirname
        (phase_dir / "norm").mkdir(parents=True, exist_ok=True)
        (phase_dir / "raw").mkdir(parents=True, exist_ok=True)
        (phase_dir / "qa").mkdir(parents=True, exist_ok=True)
        dirs[phase] = phase_dir
    return dirs


def make_cfg() -> runner.RunnerConfig:
    return runner.RunnerConfig(
        dry_run=True,
        max_files_docs=10,
        max_files_code=10,
        max_chars=100000,
        max_request_bytes=200000,
        file_truncate_chars=1000,
        home_scan_mode="safe",
        resume=True,
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
    )


def materialize_required_artifacts(dirs: dict[str, Path], phases: list[str]) -> None:
    for phase in phases:
        groups = runner.R_REQUIRED_ARTIFACT_GROUPS.get(phase, [])
        for group in groups:
            pattern = group[0]
            filename = pattern.replace("*", "SAMPLE")
            if not filename.endswith((".json", ".md", ".txt")):
                filename = f"{filename}.json"
            artifact = dirs[phase] / "norm" / filename
            artifact.write_text("{}\n", encoding="utf-8")


def test_phase_m_prompt_corpus_not_active_in_repo_truth_extractor() -> None:
    prompt_files = sorted((Path("services/repo-truth-extractor/prompts/v3")).glob("PROMPT_M*.md"))
    assert len(prompt_files) == 7


def test_run_phase_r_gates_on_required_norm_artifacts(tmp_path: Path) -> None:
    dirs = make_dirs(tmp_path)

    with pytest.raises(RuntimeError, match="Phase R requires normalized inputs"):
        runner.run_phase_R(dirs, make_cfg())

    materialize_required_artifacts(dirs, phases=runner.R_REQUIRED_INPUT_PHASES)
    runner.run_phase_R(dirs, make_cfg())


def test_write_run_manifest_has_required_keys(tmp_path: Path) -> None:
    dirs = make_dirs(tmp_path)
    prompt_path = tmp_path / "PROMPT_A0_TEST.md"
    prompt_path.write_text("Goal: TEST.json\n", encoding="utf-8")

    args = runner.argparse.Namespace(
        phase="A",
        dry_run=True,
        resume=True,
        max_files_docs=10,
        max_files_code=10,
        max_chars=1000,
        max_request_bytes=200000,
        file_truncate_chars=1000,
        home_scan_mode="safe",
        fail_fast_auth=False,
        gemini_auth_mode="auto",
        gemini_model_id=runner.DEFAULT_GEMINI_MODEL_ID,
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
        run_id="run-test",
        no_write_latest=True,
        write_latest_even_on_dry_run=False,
        doctor=False,
        doctor_auth=False,
        preflight_providers=False,
        coverage_report=False,
        ui="plain",
        quiet=True,
        jsonl_events=False,
        pretty=False,
        print_promptpack=False,
        verify_phase_output=None,
        print_config=False,
    )
    run_context = runner.RunContext(
        run_id="run-test",
        source="explicit",
        latest_file=tmp_path / "latest_run_id.txt",
        latest_written=False,
    )

    runner.write_run_manifest(
        root=tmp_path,
        dirs=dirs,
        run_id="run-test",
        args=args,
        run_context=run_context,
        phases=["A"],
    )
    manifest_path = dirs["root"] / "RUN_MANIFEST.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["run_id"] == "run-test"
    assert "generated_at" in payload
    assert "effective_model_routing" in payload
    assert "cli" in payload
