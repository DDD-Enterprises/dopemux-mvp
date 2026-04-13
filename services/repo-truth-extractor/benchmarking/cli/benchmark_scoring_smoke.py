from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
SERVICE_ROOT = HERE.parents[2]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.cli.benchmark_execution_smoke import STARTER_CASE_IDS
from benchmarking.orchestration.attempt_executor import AttemptExecutor
from benchmarking.rollups.pipeline import BenchmarkScoringPipeline
from benchmarking.storage.hashing import stable_json_dumps
from benchmarking.storage.paths import benchmark_paths, run_paths


def run_scoring_smoke(root: Path | None = None, proof_dir: Path | None = None) -> dict[str, object]:
    executor = AttemptExecutor(root)
    baseline = executor.execute_starter_set(STARTER_CASE_IDS)
    current = executor.execute_starter_set(STARTER_CASE_IDS)
    pipeline = BenchmarkScoringPipeline(root)
    pipeline.score_run(baseline.benchmark_run_id)
    report = pipeline.score_run(current.benchmark_run_id, prior_run_id=baseline.benchmark_run_id)
    payload = {
        "baseline_run_id": baseline.benchmark_run_id,
        "benchmark_run_id": current.benchmark_run_id,
        "scored_attempt_ids": report["scored_attempt_ids"],
        "db_row_counts": executor.repo.count_rows(),
        "sample_attempt": report["sample_attempt"],
        "sample_control_delta": report["sample_control_delta"],
        "sample_case_set_rollup": report["case_set_rollup"],
        "sample_archetype_rollup": report["archetype_rollups"][0] if report["archetype_rollups"] else {},
        "sample_profile_fit": report["profile_fit_rows"][0] if report["profile_fit_rows"] else {},
        "sample_portfolio_view": report["portfolio_view"],
        "sample_regression_comparison": report["regression_comparison"],
    }
    if proof_dir is not None:
        proof_dir.mkdir(parents=True, exist_ok=True)
        benchmark_root = benchmark_paths(root).root
        (proof_dir / "RUN_MANIFEST.json").write_text(stable_json_dumps(payload) + "\n", encoding="utf-8")
        (proof_dir / "db_row_counts.json").write_text(stable_json_dumps(payload["db_row_counts"]) + "\n", encoding="utf-8")
        (proof_dir / "sample_attempt.json").write_text(stable_json_dumps(payload["sample_attempt"]) + "\n", encoding="utf-8")
        (proof_dir / "sample_control_delta.json").write_text(stable_json_dumps(payload["sample_control_delta"]) + "\n", encoding="utf-8")
        (proof_dir / "sample_case_set_rollup.json").write_text(stable_json_dumps(payload["sample_case_set_rollup"]) + "\n", encoding="utf-8")
        (proof_dir / "sample_archetype_rollup.json").write_text(stable_json_dumps(payload["sample_archetype_rollup"]) + "\n", encoding="utf-8")
        (proof_dir / "sample_profile_fit.json").write_text(stable_json_dumps(payload["sample_profile_fit"]) + "\n", encoding="utf-8")
        (proof_dir / "sample_portfolio_view.json").write_text(stable_json_dumps(payload["sample_portfolio_view"]) + "\n", encoding="utf-8")
        (proof_dir / "sample_regression_comparison.json").write_text(
            stable_json_dumps(payload["sample_regression_comparison"]) + "\n",
            encoding="utf-8",
        )
        tree_lines = sorted(str(path.relative_to(benchmark_root)) for path in benchmark_root.rglob("*"))
        (proof_dir / "benchmark_tree.txt").write_text("\n".join(tree_lines) + "\n", encoding="utf-8")
        rollups_dir = run_paths(current.benchmark_run_id, root).rollups_dir
        (proof_dir / "smoke_output.txt").write_text(
            "\n".join(
                [
                    f"baseline_run_id={baseline.benchmark_run_id}",
                    f"benchmark_run_id={current.benchmark_run_id}",
                    f"rollups_dir={rollups_dir}",
                    f"scored_attempt_ids={','.join(report['scored_attempt_ids'])}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="M3 scoring smoke for benchmark scoring and rollups.")
    parser.add_argument("--benchmark-root", type=Path, default=None)
    parser.add_argument("--proof-dir", type=Path, default=None)
    args = parser.parse_args(argv)
    payload = run_scoring_smoke(root=args.benchmark_root, proof_dir=args.proof_dir)
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
