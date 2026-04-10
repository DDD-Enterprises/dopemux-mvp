from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from .base import ExecutionResult, ExecutorAdapter
from .fixtures import build_fl_int_run_root

SCRIPT = Path(__file__).resolve().parents[2] / "run_fl_int.py"


class FLIntAdapter(ExecutorAdapter):
    adapter_name = "fl_int"

    def execute(self, case: dict[str, Any], work_root: Path) -> ExecutionResult:
        self.validate_case(case)
        fixture_root = build_fl_int_run_root(work_root / "fixture")
        command = [
            sys.executable,
            str(SCRIPT),
            "--run-root",
            str(fixture_root),
            "--dry-run",
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        summary = json.loads(result.stdout)
        output_root = fixture_root / "postprocess" / "fl_int_v1"
        machine_summary = json.loads((output_root / "FL_INT_MACHINE_SUMMARY.json").read_text(encoding="utf-8"))
        fl_int_input = json.loads((output_root / "FL_INT_INPUT.json").read_text(encoding="utf-8"))
        return ExecutionResult(
            adapter_name=self.adapter_name,
            case_id=str(case["case_id"]),
            succeeded=summary["status"] == "DRY_RUN",
            contract_gate_pass=summary["status"] == "DRY_RUN",
            contract_gate_strength="strong",
            contract_fail_reason=None,
            output_artifact_ref="outputs/FL_INT_MACHINE_SUMMARY.json",
            outputs={
                "FL_INT_MACHINE_SUMMARY.json": machine_summary,
                "FL_INT_INPUT.json": fl_int_input,
            },
            route_trace={
                "surface_class": "local_or_open_weight",
                "execution_mode": "dry_run",
                "route_hops": [],
                "run_root": str(fixture_root),
            },
            task_eval={"status": "captured", "task_success_score": 1.0},
            executor_links={
                "script": str(SCRIPT),
                "fixture_root": str(fixture_root),
                "output_root": str(output_root),
            },
            validator_inputs={
                "summary_path": str(output_root / "FL_INT_MACHINE_SUMMARY.json"),
                "input_path": str(output_root / "FL_INT_INPUT.json"),
            },
            work_root=str(output_root),
            metadata={"stdout": result.stdout},
        )
