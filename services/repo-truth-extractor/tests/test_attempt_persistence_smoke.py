from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.cli.benchmark_catalog_smoke import run_smoke


def test_attempt_persistence_smoke_verifies_db_filesystem_linkage(tmp_path: Path) -> None:
    proof_dir = tmp_path / "proof"
    report = run_smoke(root=tmp_path / "benchmarks", proof_dir=proof_dir)

    assert report.db_row_counts["benchmark_run"] == 1
    assert report.db_row_counts["benchmark_case_set"] == 1
    assert report.db_row_counts["benchmark_case_attempt"] == 1
    assert report.db_row_counts["evidence_bundle"] == 1
    assert Path(report.bundle_path).exists()
    assert report.sample_attempt["evidence_bundle_id"] == report.bundle_id
    assert report.evidence_manifest["case_attempt_id"] == report.case_attempt_id
    assert (proof_dir / "sample_attempt.json").exists()
    assert (proof_dir / "sample_evidence_manifest.json").exists()


def test_smoke_cli_exits_successfully_and_prints_json(tmp_path: Path) -> None:
    cli_path = SERVICE_ROOT / "benchmarking" / "cli" / "benchmark_catalog_smoke.py"
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
    assert payload["bundle_id"].startswith("bundle_")
    assert payload["db_row_counts"]["benchmark_case_attempt"] == 1

