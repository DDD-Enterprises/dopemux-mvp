from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.cli.benchmark_execution_smoke import run_execution_smoke


def test_attempt_execution_smoke_persists_attempts_and_bundle_linkage(tmp_path: Path) -> None:
    proof_dir = tmp_path / "proof"
    report = run_execution_smoke(root=tmp_path / "benchmarks", proof_dir=proof_dir)
    assert len(report["case_attempt_ids"]) == 6
    assert report["db_row_counts"]["benchmark_case_attempt"] == 6
    assert report["db_row_counts"]["validator_result"] == 6
    assert report["db_row_counts"]["evidence_bundle"] == 6
    assert report["sample_attempt"]["validator_pass"] is True
    assert report["sample_route_trace"]["execution_mode"]
    assert (proof_dir / "sample_validator_results.json").exists()


def test_execution_smoke_cli_exits_successfully(tmp_path: Path) -> None:
    cli_path = SERVICE_ROOT / "benchmarking" / "cli" / "benchmark_execution_smoke.py"
    result = subprocess.run(
        [
            sys.executable,
            str(cli_path),
            "--benchmark-root",
            str(tmp_path / "benchmarks"),
            "--proof-dir",
            str(tmp_path / "proof"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout.strip())
    assert len(payload["case_attempt_ids"]) == 6
    assert payload["db_row_counts"]["validator_result"] == 6
