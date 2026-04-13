from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
SERVICE_ROOT = HERE.parents[2]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.campaigns.admissibility import evaluate_admissibility
from benchmarking.campaigns.manifest import build_campaign_manifest
from benchmarking.campaigns.route_identity import RouteTelemetryError, build_route_identity_record
from benchmarking.campaigns.route_separation import (
    build_corrected_control_strategy,
    build_route_identity_truth_table,
    classify_route_collapse,
    render_r1b_decision_memo,
    render_route_collapse_diagnosis,
)
from benchmarking.campaigns.selection import build_r1_campaign_plan
from benchmarking.reporting.route_identity_admissibility import write_route_identity_admissibility
from benchmarking.storage.hashing import stable_json_dumps
from benchmarking.storage.paths import benchmark_paths
from benchmarking.storage.sqlite_repo import BenchmarkCatalogRepo


def _write_json(path: Path, payload: dict[str, Any] | list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json_dumps(payload) + "\n", encoding="utf-8")


def _latest_run_id(repo: BenchmarkCatalogRepo) -> str:
    runs = repo.list_benchmark_runs()
    if not runs:
        raise RuntimeError("no benchmark runs available for route separation analysis")
    return str(runs[-1]["benchmark_run_id"])


def _load_route_identities(
    *,
    repo: BenchmarkCatalogRepo,
    run_ids: list[str],
    intended_keys: set[tuple[str, str]],
) -> tuple[list[Any], dict[tuple[str, str], list[dict[str, str]]]]:
    route_identities = []
    route_errors: dict[tuple[str, str], list[dict[str, str]]] = {}
    for run_id in run_ids:
        for attempt in repo.list_attempts(run_id):
            key = (str(attempt["case_id"]), str(attempt["route_id"]))
            if key not in intended_keys:
                continue
            try:
                route_identities.append(build_route_identity_record(repo, attempt))
            except RouteTelemetryError as exc:
                route_errors.setdefault(key, []).append(
                    {
                        "blocker_code": exc.blocker_code,
                        "message": str(exc),
                    }
                )
    return route_identities, route_errors


def run_smoke(
    root: Path | None = None,
    proof_dir: Path | None = None,
    benchmark_run_ids: list[str] | None = None,
) -> dict[str, Any]:
    repo = BenchmarkCatalogRepo.from_root(root)
    plan = build_r1_campaign_plan(repo)
    manifest = build_campaign_manifest(plan)
    run_ids = list(benchmark_run_ids or [])
    if not run_ids:
        run_ids = [_latest_run_id(repo)]

    intended_routes = [
        {
            "route_id": item["route_id"],
            "cohort": item["cohort"],
            "case_id": item["case_id"],
            "surface_class": item["surface_class"],
            "provider_name": item["provider_name"],
            "model_key": item["model_key"],
            "provider_model_id": item["provider_model_id"],
        }
        for item in manifest["control_candidates"] + manifest["campaign_candidates"]
    ]
    intended_keys = {(str(item["case_id"]), str(item["route_id"])) for item in intended_routes}
    route_identities, route_errors = _load_route_identities(
        repo=repo,
        run_ids=run_ids,
        intended_keys=intended_keys,
    )
    admissibility = evaluate_admissibility(
        benchmark_run_ids=run_ids,
        route_identities=route_identities,
        intended_routes=intended_routes,
        route_errors=route_errors,
        required_repeat_count=1,
    )
    for run_id in run_ids:
        write_route_identity_admissibility(run_id, admissibility, root)

    truth_table = build_route_identity_truth_table(
        intended_routes=intended_routes,
        route_identities=route_identities,
        route_errors=route_errors,
        admissibility=admissibility,
    )
    classification = classify_route_collapse(truth_table)
    strategy = build_corrected_control_strategy(
        manifest=manifest,
        truth_table=truth_table,
        admissibility=admissibility,
    )
    bounded_result = {
        "status": "admissible" if strategy.get("r1_restart_truthful") else "blocked",
        "strategy_type": strategy.get("strategy_type"),
        "campaign_id": plan.campaign_id,
        "benchmark_run_ids": run_ids,
        "r1_restart_truthful": bool(strategy.get("r1_restart_truthful")),
        "blocking_reason_codes": list(admissibility.get("admissibility_blocker_codes", [])),
        "notes": list(strategy.get("notes", [])),
    }
    diagnosis_md = render_route_collapse_diagnosis(
        truth_table=truth_table,
        admissibility=admissibility,
    )
    decision_memo = render_r1b_decision_memo(
        truth_table=truth_table,
        classification=classification,
        strategy=strategy,
    )
    payload = {
        "campaign_id": plan.campaign_id,
        "benchmark_run_ids": run_ids,
        "admissibility": admissibility,
        "classification": classification,
        "corrected_control_strategy": strategy,
        "bounded_admissibility_result": bounded_result,
        "r1_restart_truthful": bool(strategy.get("r1_restart_truthful")),
        "db_row_counts": repo.count_rows(),
    }

    if proof_dir is not None:
        proof_dir.mkdir(parents=True, exist_ok=True)
        benchmark_root = benchmark_paths(root).root
        _write_json(proof_dir / "RUN_MANIFEST.json", payload)
        _write_json(proof_dir / "route_identity_truth_table.json", truth_table)
        _write_json(proof_dir / "route_collapse_classification.json", classification)
        _write_json(proof_dir / "corrected_control_strategy.json", strategy)
        _write_json(proof_dir / "bounded_admissibility_result.json", bounded_result)
        _write_json(proof_dir / "db_row_counts.json", payload["db_row_counts"])
        (proof_dir / "route_collapse_diagnosis.md").write_text(diagnosis_md, encoding="utf-8")
        (proof_dir / "R1B_DECISION_MEMO.md").write_text(decision_memo, encoding="utf-8")
        (proof_dir / "IMPLEMENTATION_NOTES.md").write_text(
            "\n".join(
                [
                    "# Implementation Notes",
                    "",
                    "- Route separation diagnosis is derived from persisted benchmark evidence plus runtime code authority.",
                    "- No recommendation states or governance packets are generated from invalidated R1 outputs.",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        (proof_dir / "smoke_output.txt").write_text(
            "\n".join(
                [
                    f"benchmark_run_ids={','.join(run_ids)}",
                    f"admissibility_status={admissibility['status']}",
                    f"strategy_status={strategy['status']}",
                    f"r1_restart_truthful={str(strategy['r1_restart_truthful']).lower()}",
                    f"blockers={','.join(admissibility.get('admissibility_blocker_codes', []))}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        tree_lines = sorted(str(path.relative_to(benchmark_root)) for path in benchmark_root.rglob("*"))
        (proof_dir / "benchmark_tree.txt").write_text("\n".join(tree_lines) + "\n", encoding="utf-8")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run bounded route-separation diagnosis for R1B.")
    parser.add_argument("--benchmark-root", type=Path, default=None)
    parser.add_argument("--proof-dir", type=Path, default=None)
    parser.add_argument("--benchmark-run-id", action="append", default=None)
    args = parser.parse_args(argv)
    payload = run_smoke(root=args.benchmark_root, proof_dir=args.proof_dir, benchmark_run_ids=args.benchmark_run_id)
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
