from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
SERVICE_ROOT = HERE.parents[2]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.models.manifests import SmokeLinkageReport
from benchmarking.registry.seed_records import synthetic_fixture_records
from benchmarking.storage.bundle_writer import EvidenceBundleWriter
from benchmarking.storage.hashing import stable_json_dumps
from benchmarking.storage.paths import benchmark_paths
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


def _sqlite_schema_dump(db_path: Path) -> str:
    with sqlite3.connect(str(db_path)) as conn:
        rows = conn.execute(
            """
            SELECT type, name, sql
            FROM sqlite_master
            WHERE sql IS NOT NULL
            ORDER BY type, name
            """
        ).fetchall()
    lines: list[str] = []
    for row_type, name, sql in rows:
        lines.append(f"-- {row_type}:{name}")
        lines.append(str(sql).strip() + ";")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def run_smoke(root: Path | None = None, proof_dir: Path | None = None) -> SmokeLinkageReport:
    repo_root = Path(__file__).resolve().parents[4]
    records = synthetic_fixture_records(_git_commit(repo_root))
    repo = BenchmarkCatalogRepo.from_root(root)
    writer = EvidenceBundleWriter(root)

    surface = records["provider_surface"]
    model = records["model"]
    route = records["route"]
    contract_snapshot = records["contract_snapshot"]
    validator_suite = records["validator_suite"]
    control_anchor_group = records["control_anchor_group"]
    archetype = records["archetype"]
    profile = records["profile"]
    retry_policy = records["retry_policy"]
    benchmark_case = records["benchmark_case"]
    case_set = records["benchmark_case_set"]
    benchmark_run = records["benchmark_run"]
    attempt = records["benchmark_case_attempt"]
    validator_result = records["validator_result"]
    control_delta = records["control_delta"]
    recommendation = records["promotion_recommendation"]
    decision = records["governance_decision"]
    registry_snapshot_files = records["registry_snapshot_files"]

    writer.write_run_layout(
        benchmark_run=benchmark_run,
        case_set_id=case_set.case_set_id,
        contract_version=attempt.contract_version,
        contract_snapshot_id=contract_snapshot.contract_snapshot_id,
        registry_snapshot_files=registry_snapshot_files,
    )
    writer.write_case_set_layout(
        benchmark_run_id=benchmark_run.benchmark_run_id,
        case_set_id=case_set.case_set_id,
        case_ids=case_set.case_ids,
        control_anchor_group_id=case_set.control_anchor_group_id,
    )
    written_bundle = writer.write_attempt_bundle(
        attempt=attempt,
        route_trace=records["route_trace"],
        validator_results=records["validator_results_payload"],
        task_eval=records["task_eval_payload"],
        control_delta=records["control_delta_payload"],
        executor_links=records["executor_links_payload"],
        output_payloads=records["outputs"],
    )

    repo.insert_provider_surface(surface)
    repo.insert_model(model)
    repo.insert_route(route)
    repo.insert_contract_snapshot(contract_snapshot)
    repo.insert_validator_suite(validator_suite)
    repo.insert_archetype(archetype)
    repo.insert_control_anchor_group(control_anchor_group)
    repo.insert_profile(profile)
    repo.insert_retry_policy(retry_policy)
    repo.insert_benchmark_case(benchmark_case)
    repo.insert_benchmark_case_set(case_set)
    repo.insert_benchmark_run(benchmark_run)
    repo.insert_evidence_bundle(written_bundle.bundle)
    repo.insert_benchmark_case_attempt(attempt)
    repo.insert_validator_result(validator_result)
    repo.insert_control_delta(control_delta)
    repo.insert_promotion_recommendation(recommendation)
    repo.insert_governance_decision(decision)

    fetched_attempt = repo.fetch_attempt(attempt.case_attempt_id)
    if fetched_attempt is None:
        raise RuntimeError("smoke linkage failure: benchmark_case_attempt was not persisted")
    fetched_bundle = repo.fetch_bundle(written_bundle.bundle.bundle_id)
    if fetched_bundle is None:
        raise RuntimeError("smoke linkage failure: evidence_bundle was not persisted")
    if fetched_attempt["evidence_bundle_id"] != written_bundle.bundle.bundle_id:
        raise RuntimeError("smoke linkage failure: attempt does not reference persisted bundle")
    if fetched_bundle["benchmark_run_id"] != benchmark_run.benchmark_run_id:
        raise RuntimeError("smoke linkage failure: bundle does not reference benchmark run")
    if Path(fetched_bundle["root_path"]).resolve() != written_bundle.attempt_dir.resolve():
        raise RuntimeError("smoke linkage failure: bundle root path does not resolve to written attempt dir")

    report = SmokeLinkageReport(
        benchmark_run_id=benchmark_run.benchmark_run_id,
        case_set_id=case_set.case_set_id,
        case_attempt_id=attempt.case_attempt_id,
        bundle_id=written_bundle.bundle.bundle_id,
        bundle_path=str(written_bundle.attempt_dir),
        db_row_counts=repo.count_rows(),
        sample_attempt=fetched_attempt,
        evidence_manifest=written_bundle.manifest_payload,
    )

    if proof_dir is not None:
        proof_dir.mkdir(parents=True, exist_ok=True)
        benchmark_root = benchmark_paths(root).root
        (proof_dir / "RUN_MANIFEST.json").write_text(stable_json_dumps(report.to_dict()) + "\n", encoding="utf-8")
        (proof_dir / "smoke_output.txt").write_text(
            "\n".join(
                [
                    f"benchmark_run_id={benchmark_run.benchmark_run_id}",
                    f"case_set_id={case_set.case_set_id}",
                    f"case_attempt_id={attempt.case_attempt_id}",
                    f"bundle_id={written_bundle.bundle.bundle_id}",
                    f"bundle_path={written_bundle.attempt_dir}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        (proof_dir / "sqlite_schema_dump.txt").write_text(
            _sqlite_schema_dump(repo.db_path),
            encoding="utf-8",
        )
        tree_lines = sorted(str(path.relative_to(benchmark_root)) for path in benchmark_root.rglob("*"))
        (proof_dir / "benchmark_tree.txt").write_text("\n".join(tree_lines) + "\n", encoding="utf-8")
        (proof_dir / "db_row_counts.json").write_text(
            stable_json_dumps(report.db_row_counts) + "\n",
            encoding="utf-8",
        )
        (proof_dir / "sample_attempt.json").write_text(
            stable_json_dumps(report.sample_attempt) + "\n",
            encoding="utf-8",
        )
        (proof_dir / "sample_evidence_manifest.json").write_text(
            stable_json_dumps(report.evidence_manifest) + "\n",
            encoding="utf-8",
        )

    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Synthetic smoke for benchmark catalog bootstrap and bundle linkage.")
    parser.add_argument("--benchmark-root", type=Path, default=None, help="Override benchmark root.")
    parser.add_argument("--proof-dir", type=Path, default=None, help="Optional proof artifact output directory.")
    args = parser.parse_args(argv)

    report = run_smoke(root=args.benchmark_root, proof_dir=args.proof_dir)
    print(json.dumps(report.to_dict(), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
