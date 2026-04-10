from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
SERVICE_ROOT = HERE.parents[2]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.orchestration.attempt_executor import AttemptExecutor
from benchmarking.scenarios.hardening import FULL_STARTER_CASE_IDS
from benchmarking.storage.hashing import stable_json_dumps
from benchmarking.storage.paths import benchmark_paths

STARTER_CASE_IDS = FULL_STARTER_CASE_IDS


def run_execution_smoke(root: Path | None = None, proof_dir: Path | None = None) -> dict[str, object]:
    executor = AttemptExecutor(root)
    report = executor.execute_starter_set(STARTER_CASE_IDS)
    payload = {
        "benchmark_run_id": report.benchmark_run_id,
        "case_attempt_ids": report.case_attempt_ids,
        "bundle_ids": report.bundle_ids,
        "db_row_counts": report.db_row_counts,
        "sample_attempt": report.sample_attempt,
        "sample_validator_results": report.sample_validator_results,
        "sample_route_trace": report.sample_route_trace,
        "sample_executor_links": report.sample_executor_links,
    }
    if proof_dir is not None:
        proof_dir.mkdir(parents=True, exist_ok=True)
        benchmark_root = benchmark_paths(root).root
        (proof_dir / "RUN_MANIFEST.json").write_text(stable_json_dumps(payload) + "\n", encoding="utf-8")
        tree_lines = sorted(str(path.relative_to(benchmark_root)) for path in benchmark_root.rglob("*"))
        (proof_dir / "benchmark_tree.txt").write_text("\n".join(tree_lines) + "\n", encoding="utf-8")
        (proof_dir / "db_row_counts.json").write_text(stable_json_dumps(report.db_row_counts) + "\n", encoding="utf-8")
        (proof_dir / "sample_attempt.json").write_text(stable_json_dumps(report.sample_attempt) + "\n", encoding="utf-8")
        (proof_dir / "sample_validator_results.json").write_text(
            stable_json_dumps(report.sample_validator_results) + "\n",
            encoding="utf-8",
        )
        (proof_dir / "sample_route_trace.json").write_text(
            stable_json_dumps(report.sample_route_trace) + "\n",
            encoding="utf-8",
        )
        (proof_dir / "sample_executor_links.json").write_text(
            stable_json_dumps(report.sample_executor_links) + "\n",
            encoding="utf-8",
        )
        (proof_dir / "smoke_output.txt").write_text(
            "\n".join(
                [
                    f"benchmark_run_id={report.benchmark_run_id}",
                    f"case_attempt_ids={','.join(report.case_attempt_ids)}",
                    f"bundle_ids={','.join(report.bundle_ids)}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="M2 execution smoke for benchmark adapters and validators.")
    parser.add_argument("--benchmark-root", type=Path, default=None)
    parser.add_argument("--proof-dir", type=Path, default=None)
    args = parser.parse_args(argv)
    payload = run_execution_smoke(root=args.benchmark_root, proof_dir=args.proof_dir)
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
