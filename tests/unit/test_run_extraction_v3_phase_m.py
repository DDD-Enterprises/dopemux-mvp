from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import pytest


RUNNER_PATH = Path(__file__).resolve().parents[2] / "UPGRADES" / "run_extraction_v3.py"
SPEC = importlib.util.spec_from_file_location("run_extraction_v3", RUNNER_PATH)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


def make_dirs(tmp_path: Path) -> dict[str, Path]:
    phase_names = {
        "A": "A_repo_control_plane",
        "H": "H_home_control_plane",
        "M": "M_runtime_exports",
        "D": "D_docs_pipeline",
        "C": "C_code_surfaces",
        "E": "E_execution_plane",
        "W": "W_workflow_plane",
        "B": "B_boundary_plane",
        "G": "G_governance_plane",
        "Q": "Q_quality_assurance",
        "R": "R_arbitration",
        "X": "X_feature_index",
        "T": "T_task_packets",
        "Z": "Z_handoff_freeze",
    }
    dirs: dict[str, Path] = {"root": tmp_path}
    for phase, dirname in phase_names.items():
        phase_dir = tmp_path / dirname
        (phase_dir / "norm").mkdir(parents=True, exist_ok=True)
        (phase_dir / "raw").mkdir(parents=True, exist_ok=True)
        (phase_dir / "qa").mkdir(parents=True, exist_ok=True)
        dirs[phase] = phase_dir
    return dirs


def make_cfg(profile: str) -> runner.RunnerConfig:
    return runner.RunnerConfig(
        dry_run=True,
        max_files_docs=10,
        max_files_code=10,
        max_chars=100000,
        file_truncate_chars=1000,
        home_scan_mode="safe",
        r_profile=profile,
        resume=True,
        rpm_openai=60,
        tpm_openai=120000,
        rpm_gemini=15,
        tpm_gemini=64000,
        rpm_xai=30,
        tpm_xai=90000,
        max_inflight=1,
    )


def materialize_required_artifacts(dirs: dict[str, Path], groups: dict[str, list[tuple[str, ...]]], phases: list[str]) -> None:
    for phase in phases:
        for group in groups.get(phase, []):
            pattern = group[0]
            filename = pattern.replace("*", "SAMPLE")
            if not filename.endswith((".json", ".md", ".txt")):
                filename = f"{filename}.json"
            artifact = dirs[phase] / "norm" / filename
            artifact.write_text("{}\n", encoding="utf-8")


def test_phase_m_prompt_corpus_exists() -> None:
    prompt_files = sorted(Path("UPGRADES").glob("PROMPT_M*.md"))
    expected = [f"PROMPT_M{i}_" for i in range(7)]
    assert len(prompt_files) == 7
    names = [path.name for path in prompt_files]
    for marker in expected:
        assert any(name.startswith(marker) for name in names)


def test_run_phase_r_base_and_full_gate_messages(tmp_path: Path) -> None:
    dirs = make_dirs(tmp_path)

    with pytest.raises(RuntimeError, match=re.escape("profile 'base'")):
        runner.run_phase_R(dirs, make_cfg("base"))

    groups = runner.load_r_required_artifact_groups_by_profile()
    materialize_required_artifacts(
        dirs,
        groups["base"],
        phases=runner.required_input_phases_for_r_profile("base"),
    )

    try:
        runner.run_phase_R(dirs, make_cfg("full"))
        raise AssertionError("expected full profile gate to fail when M artifacts are missing")
    except RuntimeError as exc:
        message = str(exc)
        assert "profile 'full'" in message
        assert "M:" in message


def test_phase_manifest_writer_has_required_keys(tmp_path: Path) -> None:
    dirs = make_dirs(tmp_path)
    prompt_path = tmp_path / "PROMPT_A0_TEST.md"
    prompt_path.write_text("Goal: TEST.json\n", encoding="utf-8")

    runner.write_phase_manifest(
        phase="A",
        dirs=dirs,
        cfg=make_cfg("base"),
        prompts=[
            runner.PromptSpec(
                step_id="A0",
                prompt_path=prompt_path,
                output_artifacts=("TEST.json",),
            )
        ],
        context_items=[
            {
                "path": str((tmp_path / "input.txt").resolve()),
                "size": 5,
                "mtime": 0.0,
                "name": "input.txt",
            }
        ],
        max_files=10,
        outputs_before=[],
        outputs_after=[str((dirs["A"] / "norm" / "TEST.json").resolve())],
    )

    manifest_path = dirs["A"] / "qa" / "PHASE_A_MANIFEST.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    for key in [
        "phase",
        "run_id",
        "created_at",
        "prompt_files",
        "step_ids",
        "input_files",
        "output_files",
        "caps",
        "redactions",
        "resume_mode",
    ]:
        assert key in payload
