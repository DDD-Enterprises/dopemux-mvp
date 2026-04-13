from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import phases


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


def test_phase_sequence_and_choices_match_v5_runner_surface() -> None:
    runner = _load_runner_module()

    assert [phase.value for phase in phases.PhaseId] == phases.PHASES
    assert runner.PHASES == phases.PHASES
    assert runner.VERIFY_PHASE_CHOICES == phases.VERIFY_PHASE_CHOICES


def test_phase_metadata_maps_are_reexported_from_v5() -> None:
    runner = _load_runner_module()

    assert runner.PHASE_DIR_NAMES == phases.PHASE_DIR_NAMES
    assert runner.PHASE_DISPLAY_NAMES == phases.PHASE_DISPLAY_NAMES
    assert runner.PHASE_PURPOSES == phases.PHASE_PURPOSES
    assert runner.PHASE_REQUIRED_DEPENDENCIES == phases.PHASE_REQUIRED_DEPENDENCIES
    assert runner.PHASE_OPTIONAL_DEPENDENCIES == phases.PHASE_OPTIONAL_DEPENDENCIES
    assert runner.R_REQUIRED_INPUT_PHASES == phases.R_REQUIRED_INPUT_PHASES
    assert runner.R_OPTIONAL_INPUT_PHASES == phases.R_OPTIONAL_INPUT_PHASES
    assert runner.CODE_HEAVY_PHASES == phases.CODE_HEAVY_PHASES
    assert runner.REQUIRED_PROMPT_STEP_IDS == phases.REQUIRED_PROMPT_STEP_IDS
