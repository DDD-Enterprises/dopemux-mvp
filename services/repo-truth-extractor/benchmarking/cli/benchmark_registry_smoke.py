from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
SERVICE_ROOT = HERE.parents[2]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.registry.registry_loader import seed_registry
from benchmarking.storage.hashing import stable_json_dumps
from benchmarking.storage.sqlite_repo import BenchmarkCatalogRepo


def _git_commit(repo_root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return "UNKNOWN"
    return result.stdout.strip() or "UNKNOWN"


def run_registry_smoke(root: Path | None = None, proof_dir: Path | None = None) -> dict[str, object]:
    repo = BenchmarkCatalogRepo.from_root(root)
    bundle = seed_registry(repo)
    contract_snapshot = repo.fetch_contract_snapshot(bundle.contract_snapshot.contract_snapshot_id)
    if contract_snapshot is None:
        raise RuntimeError("contract snapshot missing after seed")
    validator_suites = repo.list_validator_suites()
    cases = repo.list_benchmark_cases()
    case_sets = repo.list_benchmark_case_sets()
    starter_case_set = repo.fetch_benchmark_case_set("benchmark_registry_starter_v1")
    if starter_case_set is None:
        raise RuntimeError("starter case-set missing after seed")
    linked_case_ids = set(starter_case_set["case_ids"])
    if linked_case_ids != {case["case_id"] for case in cases}:
        raise RuntimeError("case-set linkage mismatch")
    for case in cases:
        if case["contract_snapshot_id"] != contract_snapshot["contract_snapshot_id"]:
            raise RuntimeError(f"case {case['case_id']} not linked to seeded contract snapshot")
        if repo.fetch_validator_suite(case["validator_suite_id"]) is None:
            raise RuntimeError(f"case {case['case_id']} not linked to a seeded validator suite")
    report = {
        "git_commit": _git_commit(Path(__file__).resolve().parents[4]),
        "contract_snapshot_id": contract_snapshot["contract_snapshot_id"],
        "contract_snapshot_hash": contract_snapshot["snapshot_hash"],
        "validator_suite_ids": [suite["validator_suite_id"] for suite in validator_suites],
        "case_ids": [case["case_id"] for case in cases],
        "case_set_ids": [case_set["case_set_id"] for case_set in case_sets],
        "db_row_counts": repo.count_rows(),
        "starter_case_set": starter_case_set,
        "contract_snapshot": contract_snapshot,
    }
    if proof_dir is not None:
        proof_dir.mkdir(parents=True, exist_ok=True)
        (proof_dir / "RUN_MANIFEST.json").write_text(stable_json_dumps(report) + "\n", encoding="utf-8")
        (proof_dir / "snapshot_manifest.json").write_text(
            stable_json_dumps(contract_snapshot) + "\n",
            encoding="utf-8",
        )
        (proof_dir / "validator_suites.json").write_text(
            stable_json_dumps(validator_suites) + "\n",
            encoding="utf-8",
        )
        (proof_dir / "benchmark_cases.json").write_text(stable_json_dumps(cases) + "\n", encoding="utf-8")
        (proof_dir / "benchmark_case_sets.json").write_text(stable_json_dumps(case_sets) + "\n", encoding="utf-8")
        (proof_dir / "db_row_counts.json").write_text(
            stable_json_dumps(report["db_row_counts"]) + "\n",
            encoding="utf-8",
        )
        (proof_dir / "smoke_output.txt").write_text(
            "\n".join(
                [
                    f"contract_snapshot_id={contract_snapshot['contract_snapshot_id']}",
                    f"validator_suite_ids={','.join(report['validator_suite_ids'])}",
                    f"case_ids={','.join(report['case_ids'])}",
                    f"case_set_ids={','.join(report['case_set_ids'])}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="M1 synthetic smoke for benchmark registry and snapshot capture.")
    parser.add_argument("--benchmark-root", type=Path, default=None, help="Override benchmark root.")
    parser.add_argument("--proof-dir", type=Path, default=None, help="Optional proof output directory.")
    args = parser.parse_args(argv)
    report = run_registry_smoke(root=args.benchmark_root, proof_dir=args.proof_dir)
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

