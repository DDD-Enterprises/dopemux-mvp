from __future__ import annotations

import subprocess
import sys
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.cli.benchmark_registry_smoke import run_registry_smoke
from benchmarking.registry.registry_loader import seed_registry
from benchmarking.storage.sqlite_repo import BenchmarkCatalogRepo


def test_case_set_registry_links_cases_snapshot_and_control_anchor(tmp_path: Path) -> None:
    repo = BenchmarkCatalogRepo.from_root(tmp_path)
    bundle = seed_registry(repo)

    starter = repo.fetch_benchmark_case_set("benchmark_registry_starter_v1")
    assert starter is not None
    assert len(starter["case_ids"]) == 6
    assert starter["control_anchor_group_id"] == "anchor_openai_general_v1"

    anchor = repo.fetch_control_anchor_group(starter["control_anchor_group_id"])
    assert anchor is not None
    assert anchor["route_ids"] == ["route_openai_gpt_5_4_v1"]
    assert anchor["candidate_route_ids"] == []

    for case_id in starter["case_ids"]:
        case = repo.fetch_benchmark_case(case_id)
        assert case is not None
        assert case["contract_snapshot_id"] == bundle.contract_snapshot.contract_snapshot_id
        assert repo.fetch_validator_suite(case["validator_suite_id"]) is not None


def test_registry_smoke_cli_exits_successfully_and_proves_linkage(tmp_path: Path) -> None:
    cli_path = SERVICE_ROOT / "benchmarking" / "cli" / "benchmark_registry_smoke.py"
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
    assert "\"contract_snapshot_id\"" in result.stdout
    report = run_registry_smoke(root=tmp_path / "benchmarks-second")
    assert len(report["case_ids"]) == 6
    assert report["db_row_counts"]["benchmark_case_set"] == 2

