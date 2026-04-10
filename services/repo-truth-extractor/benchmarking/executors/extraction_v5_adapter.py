from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from .base import ExecutionResult, ExecutorAdapter

SCRIPT = Path(__file__).resolve().parents[2] / "run_extraction_v5.py"
FIXTURE_REPO = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "golden_repo_min"


class ExtractionV5Adapter(ExecutorAdapter):
    adapter_name = "runtime_v5_extraction"

    def execute(self, case: dict[str, Any], work_root: Path) -> ExecutionResult:
        self.validate_case(case)
        run_id = "benchmark_v5_case"
        output_root = work_root / "v5_run"
        command = [
            sys.executable,
            str(SCRIPT),
            "--phase",
            "A",
            "--dry-run",
            "--run-id",
            run_id,
            "--output-root",
            str(output_root),
        ]
        result = subprocess.run(
            command,
            cwd=str(FIXTURE_REPO),
            capture_output=True,
            text=True,
            check=True,
        )
        run_root = output_root / "runs" / run_id
        phase_root = run_root / "A_repo_control_plane"
        routing_fingerprint = json.loads((run_root / "RUN_ROUTING_FINGERPRINT.json").read_text(encoding="utf-8"))
        qa_payload = json.loads((phase_root / "qa" / "A0_QA.json").read_text(encoding="utf-8"))
        raw_payload = json.loads((phase_root / "raw" / "A0__A_P0001.json").read_text(encoding="utf-8"))
        output_payload = json.loads((phase_root / "norm" / "REPOCTRL_INVENTORY.json").read_text(encoding="utf-8"))
        effective_route = routing_fingerprint["effective_model_routing"]["A"]
        return ExecutionResult(
            adapter_name=self.adapter_name,
            case_id=str(case["case_id"]),
            succeeded=True,
            contract_gate_pass=not qa_payload.get("missing_expected_artifacts"),
            contract_gate_strength="strong",
            contract_fail_reason=None,
            output_artifact_ref="outputs/REPOCTRL_INVENTORY.json",
            outputs={
                "REPOCTRL_INVENTORY.json": output_payload,
                "A0_QA.json": qa_payload,
                "A0__A_P0001.json": raw_payload,
            },
            route_trace={
                "surface_class": "openrouter_routed",
                "execution_mode": "dry_run",
                "phase": "A",
                "route_hops": [effective_route],
                "routing_fingerprint_path": str(run_root / "RUN_ROUTING_FINGERPRINT.json"),
            },
            task_eval={"status": "captured", "task_success_score": 1.0},
            executor_links={
                "script": str(SCRIPT),
                "cwd": str(FIXTURE_REPO),
                "run_root": str(run_root),
                "phase_root": str(phase_root),
                "stdout_excerpt": result.stdout.splitlines()[-1] if result.stdout.splitlines() else "",
            },
            validator_inputs={
                "qa_path": str(phase_root / "qa" / "A0_QA.json"),
                "routing_fingerprint_path": str(run_root / "RUN_ROUTING_FINGERPRINT.json"),
                "phase_root": str(phase_root),
            },
            repair_invocations=int(qa_payload.get("repair_invocations", 0)),
            sidefill_invocations=int(qa_payload.get("sidefill_invocations", 0)),
            route_hop_total=1,
            work_root=str(run_root),
        )

