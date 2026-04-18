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
        raise RuntimeError("no benchmark runs available for route admissibility analysis")
    return str(runs[-1]["benchmark_run_id"])


def _admissibility_intended_routes(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    # Route-identity admissibility only applies to the bounded live lane that emits
    # route telemetry. Synthetic/local adapters remain part of the campaign, but
    # they are not admissibility-gating surfaces.
    return [
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
        if bool(item.get("live_execution"))
    ]


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
    attempts: list[dict[str, Any]] = []
    for run_id in run_ids:
        attempts.extend(repo.list_attempts(run_id))

    intended_routes = _admissibility_intended_routes(manifest)
    if not intended_routes:
        raise RuntimeError("no live admissibility-gating routes were selected for the current campaign plan")
    intended_keys = {(str(item["case_id"]), str(item["route_id"])) for item in intended_routes}

    route_identities = []
    route_errors: dict[tuple[str, str], list[dict[str, str]]] = {}
    for attempt in attempts:
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

    admissibility = evaluate_admissibility(
        benchmark_run_ids=run_ids,
        route_identities=route_identities,
        intended_routes=intended_routes,
        route_errors=route_errors,
        required_repeat_count=1,
    )
    for run_id in run_ids:
        write_route_identity_admissibility(run_id, admissibility, root)

    payload = {
        "benchmark_run_ids": run_ids,
        "campaign_id": plan.campaign_id,
        "admissibility": admissibility,
        "db_row_counts": repo.count_rows(),
        "can_restart_r1_truthfully": admissibility.get("status") == "admissible",
    }

    if proof_dir is not None:
        proof_dir.mkdir(parents=True, exist_ok=True)
        benchmark_root = benchmark_paths(root).root
        _write_json(proof_dir / "RUN_MANIFEST.json", payload)
        if route_identities:
            _write_json(proof_dir / "sample_route_identity.json", route_identities[0].to_dict())
        else:
            _write_json(
                proof_dir / "sample_route_identity.json",
                {"status": "not_available", "reason": "no route identities could be derived from the selected run"},
            )
        if admissibility.get("status") == "blocked":
            _write_json(proof_dir / "sample_admissibility_blocked.json", admissibility)
            _write_json(
                proof_dir / "sample_admissibility_passed.json",
                {
                    "status": "not_feasible_yet",
                    "reason": "No passing distinct-signature example is currently available under the active runtime behavior for this bounded smoke.",
                },
            )
        else:
            _write_json(proof_dir / "sample_admissibility_passed.json", admissibility)
            _write_json(
                proof_dir / "sample_admissibility_blocked.json",
                {"status": "not_blocked", "reason": "selected run passed admissibility"},
            )
        _write_json(proof_dir / "route_signature_comparison.json", {"comparisons": admissibility.get("comparisons", [])})
        _write_json(proof_dir / "db_row_counts.json", payload["db_row_counts"])
        (proof_dir / "smoke_output.txt").write_text(
            "\n".join(
                [
                    f"benchmark_run_ids={','.join(run_ids)}",
                    f"admissibility_status={admissibility['status']}",
                    f"campaign_state={admissibility['campaign_state']}",
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
    parser = argparse.ArgumentParser(description="Run bounded route identity admissibility analysis for R1.")
    parser.add_argument("--benchmark-root", type=Path, default=None)
    parser.add_argument("--proof-dir", type=Path, default=None)
    parser.add_argument("--benchmark-run-id", action="append", default=None)
    args = parser.parse_args(argv)
    payload = run_smoke(root=args.benchmark_root, proof_dir=args.proof_dir, benchmark_run_ids=args.benchmark_run_id)
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
