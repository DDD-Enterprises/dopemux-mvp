from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import rte_config


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


def test_runtime_paths_match_v5_runner_surface() -> None:
    runner = _load_runner_module()

    assert runner.RUNNER_SCRIPT == rte_config.RUNNER_SCRIPT
    assert rte_config.RUNNER_SCRIPT == Path(runner.__file__).resolve()
    assert rte_config.RUNNER_SCRIPT.name == "run_extraction_v5.py"
    assert runner.REPO_ROOT == rte_config.REPO_ROOT
    assert runner.PRICING_CONFIG_PATH == rte_config.PRICING_CONFIG_PATH
    assert runner.V5_EXTRACTION_ROOT == rte_config.RUNTIME_PATHS.extraction_root
    assert runner.V5_RUNS_ROOT == rte_config.RUNTIME_PATHS.runs_root
    assert runner.V5_LATEST_RUN_FILE == rte_config.RUNTIME_PATHS.latest_run_file
    assert runner.V5_DOCTOR_ROOT == rte_config.RUNTIME_PATHS.doctor_root


def test_static_runtime_constants_are_reexported_from_v5() -> None:
    runner = _load_runner_module()

    assert runner.PROMPT_ROOT_ENV_VAR == rte_config.PROMPT_ROOT_ENV_VAR
    assert runner.LEGACY_PROMPT_ROOT_ENV_VAR == rte_config.LEGACY_PROMPT_ROOT_ENV_VAR
    assert runner.S_PROMPTS_MODE_ENV_VAR == rte_config.S_PROMPTS_MODE_ENV_VAR
    assert runner.S_PROMPTS_MODES == rte_config.S_PROMPTS_MODES
    assert runner.PROOF_PACK_FILENAME == rte_config.PROOF_PACK_FILENAME
    assert runner.COVERAGE_ROLLUP_FILENAME == rte_config.COVERAGE_ROLLUP_FILENAME
    assert runner.RESUME_PROOF_FILENAME == rte_config.RESUME_PROOF_FILENAME
    assert runner.PROMPTGEN_DEFAULT_INCLUDE_GLOBS == rte_config.PROMPTGEN_DEFAULT_INCLUDE_GLOBS
    assert runner.PROMPTGEN_DEFAULT_EXCLUDE_GLOBS == rte_config.PROMPTGEN_DEFAULT_EXCLUDE_GLOBS
    assert runner.BENCHMARK_ROUTE_OWNERSHIP_MODE == rte_config.BENCHMARK_ROUTE_OWNERSHIP_MODE
