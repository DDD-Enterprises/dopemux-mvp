from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_reprocess_script_emits_matrix_plan_only(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[3]
    script = root / "scripts" / "reprocess_failed_partitions.py"
    run_root = tmp_path / "extraction" / "runs"
    run_id = "run_test"
    phase_dir = run_root / run_id / "A_repo_control_plane"
    qa_dir = phase_dir / "qa"
    qa_dir.mkdir(parents=True, exist_ok=True)

    _write_json(
        qa_dir / "PHASE_FAILURE_ROLLUP.json",
        {
            "failures": [
                {
                    "step_id": "A1",
                    "partition_id": "A_P0001",
                    "validation_reason": "parse",
                    "resolved_cause": "parse",
                },
                {
                    "step_id": "A1",
                    "partition_id": "A_P0002",
                    "validation_reason": "quota_or_billing",
                    "resolved_cause": "quota_or_billing",
                },
            ]
        },
    )
    _write_json(
        qa_dir / "PARSE_FAILURE_SHAPES.json",
        {
            "rows": [
                {"step_id": "A1", "partition_id": "A_P0001", "shape": "truncated_string"},
            ]
        },
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(script),
            "--run-root",
            str(run_root),
            "--run-id",
            run_id,
            "--emit-plan-only",
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(root),
    )
    assert completed.returncode == 0, completed.stderr
    assert "Reprocess plan summary" in completed.stdout
    assert "rerun_partitions" in completed.stdout
