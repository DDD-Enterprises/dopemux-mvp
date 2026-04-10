from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
BENCHMARK_ROOT = REPO_ROOT / "extraction" / "repo-truth-extractor" / "benchmarks"


@dataclass(frozen=True)
class BenchmarkPaths:
    root: Path
    index_dir: Path
    runs_dir: Path
    catalog_db: Path


@dataclass(frozen=True)
class RunPaths:
    run_root: Path
    registry_snapshots_dir: Path
    case_sets_dir: Path
    rollups_dir: Path
    recommendations_dir: Path
    governance_dir: Path
    run_manifest_path: Path
    snapshot_manifest_path: Path


@dataclass(frozen=True)
class CaseSetPaths:
    case_set_root: Path
    attempts_dir: Path
    caseset_manifest_path: Path


@dataclass(frozen=True)
class AttemptPaths:
    attempt_root: Path
    outputs_dir: Path
    attempt_summary_path: Path
    route_trace_path: Path
    validator_results_path: Path
    task_eval_path: Path
    control_delta_path: Path
    executor_links_path: Path
    evidence_manifest_path: Path


def benchmark_paths(root: Path | None = None) -> BenchmarkPaths:
    actual_root = (root or BENCHMARK_ROOT).resolve()
    return BenchmarkPaths(
        root=actual_root,
        index_dir=actual_root / "index",
        runs_dir=actual_root / "runs",
        catalog_db=actual_root / "index" / "benchmark_catalog.sqlite",
    )


def run_paths(benchmark_run_id: str, root: Path | None = None) -> RunPaths:
    base = benchmark_paths(root)
    run_root = base.runs_dir / benchmark_run_id
    return RunPaths(
        run_root=run_root,
        registry_snapshots_dir=run_root / "registry_snapshots",
        case_sets_dir=run_root / "case_sets",
        rollups_dir=run_root / "rollups",
        recommendations_dir=run_root / "recommendations",
        governance_dir=run_root / "governance",
        run_manifest_path=run_root / "BENCHMARK_RUN_MANIFEST.json",
        snapshot_manifest_path=run_root / "SNAPSHOT_MANIFEST.json",
    )


def case_set_paths(benchmark_run_id: str, case_set_id: str, root: Path | None = None) -> CaseSetPaths:
    run = run_paths(benchmark_run_id, root)
    case_set_root = run.case_sets_dir / case_set_id
    return CaseSetPaths(
        case_set_root=case_set_root,
        attempts_dir=case_set_root / "attempts",
        caseset_manifest_path=case_set_root / "CASESET_MANIFEST.json",
    )


def attempt_paths(
    benchmark_run_id: str,
    case_set_id: str,
    case_attempt_id: str,
    root: Path | None = None,
) -> AttemptPaths:
    case_set = case_set_paths(benchmark_run_id, case_set_id, root)
    attempt_root = case_set.attempts_dir / case_attempt_id
    return AttemptPaths(
        attempt_root=attempt_root,
        outputs_dir=attempt_root / "outputs",
        attempt_summary_path=attempt_root / "ATTEMPT_SUMMARY.json",
        route_trace_path=attempt_root / "ROUTE_TRACE.json",
        validator_results_path=attempt_root / "VALIDATOR_RESULTS.json",
        task_eval_path=attempt_root / "TASK_EVAL.json",
        control_delta_path=attempt_root / "CONTROL_DELTA.json",
        executor_links_path=attempt_root / "EXECUTOR_LINKS.json",
        evidence_manifest_path=attempt_root / "EVIDENCE_MANIFEST.json",
    )

