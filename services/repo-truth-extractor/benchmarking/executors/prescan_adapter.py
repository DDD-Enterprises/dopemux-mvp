from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from .base import ExecutionResult, ExecutorAdapter

SCRIPT = Path(__file__).resolve().parents[2] / "run_prescan.py"
FIXTURE_REPO = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "golden_repo_min"


class PrescanAdapter(ExecutorAdapter):
    adapter_name = "prescan"

    def execute(self, case: dict[str, Any], work_root: Path) -> ExecutionResult:
        self.validate_case(case)
        output_dir = work_root / "prescan_output"
        command = [
            sys.executable,
            str(SCRIPT),
            "--repo-root",
            str(FIXTURE_REPO),
            "--output-dir",
            str(output_dir),
            "--dry-run",
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        intelligence_path = output_dir / "prescan_intelligence.json"
        manifest_path = output_dir / "corpus_manifest.json"
        outputs = {
            "prescan_intelligence.json": json.loads(intelligence_path.read_text(encoding="utf-8")),
            "corpus_manifest.json": json.loads(manifest_path.read_text(encoding="utf-8")),
        }
        return ExecutionResult(
            adapter_name=self.adapter_name,
            case_id=str(case["case_id"]),
            succeeded=True,
            contract_gate_pass=all(path.exists() for path in (intelligence_path, manifest_path)),
            contract_gate_strength="moderate",
            contract_fail_reason=None,
            output_artifact_ref="outputs/prescan_intelligence.json",
            outputs=outputs,
            route_trace={
                "surface_class": "local_or_open_weight",
                "execution_mode": "local_dry_run",
                "route_hops": [],
                "logical_route_id": case.get("case_id"),
            },
            task_eval={"status": "captured", "task_success_score": 1.0},
            executor_links={
                "script": str(SCRIPT),
                "fixture_repo": str(FIXTURE_REPO),
                "stdout_excerpt": result.stdout.splitlines()[-1] if result.stdout.splitlines() else "",
            },
            validator_inputs={
                "intelligence_path": str(intelligence_path),
                "manifest_path": str(manifest_path),
            },
            work_root=str(output_dir),
            metadata={"stderr": result.stderr},
        )

