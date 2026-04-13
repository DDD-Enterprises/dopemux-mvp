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
from benchmarking.reporting.pipeline import BenchmarkReportingPipeline
from benchmarking.scenarios.hardening import (
    FULL_STARTER_CASE_IDS,
    apply_hardening_run_overrides,
    apply_regression_degradation,
)
from benchmarking.rollups.pipeline import BenchmarkScoringPipeline
from benchmarking.storage.hashing import stable_json_dumps
from benchmarking.storage.paths import benchmark_paths
from benchmarking.synthesis.governance_pipeline import GovernanceSynthesisPipeline


def _changed_summary(change_summaries: list[dict[str, object]]) -> dict[str, object]:
    for summary in change_summaries:
        change = dict(summary.get("recommendation_state_change", {}))
        if bool(change.get("changed")):
            return summary
    return change_summaries[0] if change_summaries else {}


def _candidate_by_state(candidate_details: list[dict[str, object]], state: str) -> dict[str, object]:
    for payload in candidate_details:
        if payload.get("current_recommendation_state") == state:
            return payload
    return candidate_details[0] if candidate_details else {}


def _candidate_by_case(candidate_details: list[dict[str, object]], case_id: str) -> dict[str, object]:
    for payload in candidate_details:
        if payload.get("case_id") == case_id:
            return payload
    return candidate_details[0] if candidate_details else {}


def run_hardening_smoke(root: Path | None = None, proof_dir: Path | None = None) -> dict[str, object]:
    executor = AttemptExecutor(root)
    baseline = executor.execute_starter_set(FULL_STARTER_CASE_IDS)
    current = executor.execute_starter_set(FULL_STARTER_CASE_IDS)

    regression_attempt_id = apply_regression_degradation(root, current.benchmark_run_id)
    scenario_summary = apply_hardening_run_overrides(root, current.benchmark_run_id)

    scoring = BenchmarkScoringPipeline(root)
    scoring.score_run(baseline.benchmark_run_id)
    scoring.score_run(current.benchmark_run_id, prior_run_id=baseline.benchmark_run_id)

    governance = GovernanceSynthesisPipeline(root)
    governance.synthesize_run(baseline.benchmark_run_id)
    governance.synthesize_run(current.benchmark_run_id)

    reports = BenchmarkReportingPipeline(root).build_reports(
        current.benchmark_run_id,
        prior_run_id=baseline.benchmark_run_id,
    )
    payload = {
        "baseline_run_id": baseline.benchmark_run_id,
        "benchmark_run_id": current.benchmark_run_id,
        "scenario_summary": {
            **scenario_summary,
            "regression_case_attempt_id": regression_attempt_id,
        },
        "db_row_counts": executor.repo.count_rows(),
        "sample_portfolio_summary": reports["portfolio_summary"],
        "sample_profile_summary": reports["profile_summaries"][0] if reports["profile_summaries"] else {},
        "sample_candidate_detail": _candidate_by_case(
            reports["candidate_details"],
            "tool_aware_repo_reasoning_v1",
        ),
        "sample_governance_history": reports["governance_histories"][0] if reports["governance_histories"] else {},
        "sample_change_summary": _changed_summary(reports["change_summaries"]),
        "sample_phase_s_candidate": _candidate_by_case(
            reports["candidate_details"],
            "adjudication_conflict_ruling_v1",
        ),
        "sample_stale_candidate": _candidate_by_case(
            reports["candidate_details"],
            "repair_merge_conflict_normalization_v1",
        ),
        "sample_regression_candidate": _candidate_by_case(
            reports["candidate_details"],
            "strict_extract_conflicting_evidence_v1",
        ),
    }
    if proof_dir is not None:
        proof_dir.mkdir(parents=True, exist_ok=True)
        benchmark_root = benchmark_paths(root).root
        (proof_dir / "RUN_MANIFEST.json").write_text(stable_json_dumps(payload) + "\n", encoding="utf-8")
        (proof_dir / "db_row_counts.json").write_text(stable_json_dumps(payload["db_row_counts"]) + "\n", encoding="utf-8")
        (proof_dir / "sample_portfolio_summary.json").write_text(
            stable_json_dumps(payload["sample_portfolio_summary"]) + "\n",
            encoding="utf-8",
        )
        (proof_dir / "sample_profile_summary.json").write_text(
            stable_json_dumps(payload["sample_profile_summary"]) + "\n",
            encoding="utf-8",
        )
        (proof_dir / "sample_candidate_detail.json").write_text(
            stable_json_dumps(payload["sample_candidate_detail"]) + "\n",
            encoding="utf-8",
        )
        (proof_dir / "sample_governance_history.json").write_text(
            stable_json_dumps(payload["sample_governance_history"]) + "\n",
            encoding="utf-8",
        )
        (proof_dir / "sample_change_summary.json").write_text(
            stable_json_dumps(payload["sample_change_summary"]) + "\n",
            encoding="utf-8",
        )
        tree_lines = sorted(str(path.relative_to(benchmark_root)) for path in benchmark_root.rglob("*"))
        (proof_dir / "benchmark_tree.txt").write_text("\n".join(tree_lines) + "\n", encoding="utf-8")
        (proof_dir / "smoke_output.txt").write_text(
            "\n".join(
                [
                    f"baseline_run_id={baseline.benchmark_run_id}",
                    f"benchmark_run_id={current.benchmark_run_id}",
                    f"regression_case_attempt_id={regression_attempt_id}",
                    f"stale_disputed_case_attempt_id={scenario_summary['stale_disputed_case_attempt_id']}",
                    f"blocked_governance_case_attempt_id={scenario_summary['blocked_governance_case_attempt_id']}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="S1 hardening smoke for expanded corpus and state-transition coverage.")
    parser.add_argument("--benchmark-root", type=Path, default=None)
    parser.add_argument("--proof-dir", type=Path, default=None)
    args = parser.parse_args(argv)
    payload = run_hardening_smoke(root=args.benchmark_root, proof_dir=args.proof_dir)
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
