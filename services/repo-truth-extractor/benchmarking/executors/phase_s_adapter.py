from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

from .base import ExecutionResult, ExecutorAdapter

SCRIPT = Path(__file__).resolve().parents[2] / "run_extraction_v5.py"


def _load_runner():
    spec = importlib.util.spec_from_file_location("benchmark_phase_s_runner", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


class PhaseSAdapter(ExecutorAdapter):
    adapter_name = "phase_s"

    def execute(self, case: dict[str, Any], work_root: Path) -> ExecutionResult:
        self.validate_case(case)
        runner = _load_runner()
        registry = runner._load_phase_s_registry()
        prompts = runner._resolve_phase_s_prompts(runner.get_active_s_prompts_mode())
        payload = {
            "registry_step_count": len(registry),
            "step_ids": sorted(registry.keys()),
            "prompt_steps": [prompt.step_id for prompt in prompts],
            "prompt_paths": [str(prompt.prompt_path) for prompt in prompts],
        }
        return ExecutionResult(
            adapter_name=self.adapter_name,
            case_id=str(case["case_id"]),
            succeeded=True,
            contract_gate_pass=bool(registry and prompts),
            contract_gate_strength="moderate",
            contract_fail_reason=None,
            output_artifact_ref="outputs/phase_s_registry_summary.json",
            outputs={"phase_s_registry_summary.json": payload},
            route_trace={
                "surface_class": "local_or_open_weight",
                "execution_mode": "local_registry_resolution",
                "route_hops": [],
                "phase_s_registry_path": str(runner.phase_s_registry_path()),
            },
            task_eval={"status": "captured", "task_success_score": 1.0},
            executor_links={
                "script": str(SCRIPT),
                "registry_path": str(runner.phase_s_registry_path()),
            },
            validator_inputs={
                "registry_step_count": len(registry),
                "prompt_count": len(prompts),
                "payload": payload,
            },
            work_root=str(work_root),
        )

