from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest


def _load_runner_module():
    root = Path(__file__).resolve().parents[3]
    module_path = root / "services" / "repo-truth-extractor" / "run_extraction_v5.py"
    spec = importlib.util.spec_from_file_location("run_extraction_v5", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_v5_phase_c_g_and_q_promptsets_cover_required_steps_in_numeric_order() -> None:
    runner = _load_runner_module()

    for phase in ("C", "G", "Q"):
        specs = runner.get_phase_prompts(phase)
        observed_steps = [spec.step_id for spec in specs]
        assert observed_steps == sorted(observed_steps, key=runner.step_sort_key)
        assert set(observed_steps) == runner.REQUIRED_PROMPT_STEP_IDS[phase]
        assert all(spec.prompt_path.exists() for spec in specs)
        assert all(spec.output_artifacts for spec in specs)


def test_v4_schema_rollout_manifest_tracks_packet_03_tranche() -> None:
    root = Path(__file__).resolve().parents[3]
    schema_dir = root / "services" / "repo-truth-extractor" / "promptsets" / "v4" / "schemas"
    coverage_path = schema_dir / "SCHEMA_COVERAGE.json"

    assert schema_dir.exists()
    coverage = __import__("json").loads(coverage_path.read_text(encoding="utf-8"))

    tracked_steps = coverage["tracked_prompt_step_ids"]
    schema_files = coverage["schema_files"]

    assert tracked_steps == ["C18", "C19", "C20", "C21", "G6", "G7"]
    assert coverage["tracked_prompt_count"] == len(tracked_steps)
    assert coverage["schema_file_count"] == len(schema_files)
    assert all((schema_dir / name).exists() for name in schema_files)


def test_v5_phase_sp_registry_and_step_controls_match_current_contract() -> None:
    runner = _load_runner_module()

    specs = runner.get_phase_prompts("SP")

    assert [spec.step_id for spec in specs] == [f"SP{i}" for i in range(13)]
    assert runner.REQUIRED_PROMPT_STEP_IDS["SP"] == {f"SP{i}" for i in range(13)}
    assert all(spec.source == "registry" for spec in specs)
    assert all(spec.prompt_path.exists() for spec in specs)
    assert all(spec.tier_override in {"bulk", "extract", "synthesis", "qa"} for spec in specs)


def test_v5_phase_sp_supports_generic_single_step_filtering() -> None:
    runner = _load_runner_module()

    selected = runner._get_execution_step_filter(
        SimpleNamespace(step="SP7", phase="SP", s_steps=None)
    )

    assert selected == "SP7"
    cfg = runner.RunnerConfig(
        dry_run=True,
        max_files_docs=1,
        max_files_code=1,
        max_chars=1,
        max_request_bytes=1,
        file_truncate_chars=1,
        home_scan_mode="safe",
        resume=False,
        fail_fast_auth=True,
        gemini_auth_mode="auto",
        gemini_transport="sdk",
        openai_transport="openai_sdk",
        xai_transport="openai_sdk",
        retry_policy="none",
        retry_max_attempts=1,
        retry_base_seconds=0.0,
        retry_max_seconds=0.0,
        phase_auth_fail_threshold=1,
        partition_workers=1,
        debug_phase_inputs=False,
        fail_fast_missing_inputs=False,
        selected_execution_step=selected,
    )
    assert runner._selected_execution_step_ids_for_phase(cfg, "SP") == ["SP7"]


def test_v5_post_review_preset_sequence_includes_sp_phase() -> None:
    runner = _load_runner_module()

    assert runner.first_live_phase_sequence("post-review") == [
        "R",
        "X",
        "T",
        "Z",
        "S",
        "SP",
    ]


def test_v5_phase_s_always_returns_legacy_prompts() -> None:
    runner = _load_runner_module()

    specs = runner.get_phase_prompts("S")

    assert all(spec.source == "legacy" for spec in specs)
    assert [spec.step_id for spec in specs] == [f"S{i}" for i in range(13)]


def test_v5_phase_s_rejects_non_base_steps_in_selection() -> None:
    runner = _load_runner_module()

    with pytest.raises(RuntimeError, match="only allows S0-S12"):
        runner._get_s_step_controls(SimpleNamespace(s_steps="S0,S13"))
