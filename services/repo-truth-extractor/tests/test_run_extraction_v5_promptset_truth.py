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


def test_v5_phase_c_and_q_promptsets_cover_required_steps_in_numeric_order() -> None:
    runner = _load_runner_module()

    for phase in ("C", "Q"):
        specs = runner.get_phase_prompts(phase)
        observed_steps = [spec.step_id for spec in specs]
        assert observed_steps == sorted(observed_steps, key=runner.step_sort_key)
        assert set(observed_steps) == runner.REQUIRED_PROMPT_STEP_IDS[phase]
        assert all(spec.prompt_path.exists() for spec in specs)
        assert all(spec.output_artifacts for spec in specs)


def test_v5_phase_s_registry_and_step_controls_match_current_contract() -> None:
    runner = _load_runner_module()
    runner.set_active_s_prompts_mode("registry")

    specs = runner.get_phase_prompts("S")

    assert [spec.step_id for spec in specs] == [f"S{i}" for i in range(13)]
    assert all(spec.source == "registry" for spec in specs)
    assert all(spec.prompt_path.exists() for spec in specs)
    assert all(spec.tier_override in {"bulk", "extract", "synthesis", "qa"} for spec in specs)
    assert runner._get_s_step_controls(SimpleNamespace(s_steps="S12,S0")) == ["S0", "S12"]


def test_v5_phase_s_rejects_non_base_steps_in_selection() -> None:
    runner = _load_runner_module()

    with pytest.raises(RuntimeError, match="only allows S0-S12"):
        runner._get_s_step_controls(SimpleNamespace(s_steps="S0,S13"))
