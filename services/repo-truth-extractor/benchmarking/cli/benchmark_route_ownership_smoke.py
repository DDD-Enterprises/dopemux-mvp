from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
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
)
from benchmarking.campaigns.selection import CampaignAssignment, build_r1_campaign_plan
from benchmarking.orchestration.attempt_executor import AttemptExecutor
from benchmarking.storage.hashing import stable_json_dumps
from benchmarking.storage.paths import benchmark_paths
from benchmarking.storage.sqlite_repo import BenchmarkCatalogRepo


STRICT_OWNERSHIP_ROUTE_IDS = {
    "route_openrouter_openai_gpt_5_4_v1",
    "route_openai_gpt_5_4_v1",
    "route_openrouter_openai_gpt_5_3_codex_v1",
    "route_openai_gpt_5_4_mini_v1",
}


def _write_json(path: Path, payload: dict[str, Any] | list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json_dumps(payload) + "\n", encoding="utf-8")


def _load_route_identities(
    *,
    repo: BenchmarkCatalogRepo,
    run_id: str,
    intended_keys: set[tuple[str, str]],
) -> tuple[list[Any], dict[tuple[str, str], list[dict[str, str]]]]:
    route_identities = []
    route_errors: dict[tuple[str, str], list[dict[str, str]]] = {}
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


def _ownership_assignments(repo: BenchmarkCatalogRepo) -> list[CampaignAssignment]:
    plan = build_r1_campaign_plan(repo)
    selected = [
        assignment
        for assignment in plan.campaign_assignments
        if assignment.case_id == "strict_extract_conflicting_evidence_v1"
        and assignment.candidate.route_id in STRICT_OWNERSHIP_ROUTE_IDS
    ]
    updated: list[CampaignAssignment] = []
    for assignment in selected:
        updated.append(
            replace(
                assignment,
                live_execution=False,
                benchmark_route_ownership_mode="strict_extraction_lane_owned_v1",
                benchmark_route_ownership_scope="phase_a_json_managed",
                operator_note=(
                    assignment.operator_note + " "
                    + "Benchmark-only route ownership enabled for phase A JSON-managed strict extraction proof in dry-run mode."
                ).strip(),
            )
        )
    return updated


def _before_after(
    *,
    before_repo: BenchmarkCatalogRepo,
    before_run_id: str | None,
    after_route_identities: list[Any],
) -> dict[str, Any]:
    after_by_route = {str(item.declared_route_id): item for item in after_route_identities}
    after_run_ids = sorted({str(item.benchmark_run_id) for item in after_route_identities})
    payload: dict[str, Any] = {
        "before_run_id": before_run_id,
        "after_run_ids": after_run_ids,
        "routes": [],
    }
    if not before_run_id:
        return payload
    before_attempts = before_repo.list_attempts(before_run_id)
    before_records = {}
    for attempt in before_attempts:
        route_id = str(attempt["route_id"])
        if route_id not in STRICT_OWNERSHIP_ROUTE_IDS:
            continue
        try:
            before_records[route_id] = build_route_identity_record(before_repo, attempt)
        except RouteTelemetryError:
            continue
    for route_id in sorted(STRICT_OWNERSHIP_ROUTE_IDS):
        before = before_records.get(route_id)
        after = after_by_route.get(route_id)
        payload["routes"].append(
            {
                "route_id": route_id,
                "before_signature_hash": before.effective_route_signature_hash if before else None,
                "after_signature_hash": after.effective_route_signature_hash if after else None,
                "before_selected_route_identity": before.selected_route_identity if before else {},
                "after_selected_route_identity": after.selected_route_identity if after else {},
            }
        )
    return payload


def _design_doc() -> str:
    return "\n".join(
        [
            "# Route Ownership Design",
            "",
            "- Benchmark-mode route ownership is injected only through the benchmark adapter via `DPMX_BENCHMARK_ROUTE_OWNERSHIP`.",
            "- The runtime consumes that payload only for phase `A` JSON-managed steps and only when `mode=strict_extraction_lane_owned_v1`.",
            "- Normal production routing remains unchanged when the env payload is absent.",
            "- The bounded R1C proof executes in dry-run mode so route resolution distinctness can be proven without conflating it with current live provider auth readiness.",
            "- The strict repair path and bulk soft-gate repair path also honor the benchmark-owned route so telemetry reflects the real execution path rather than only the launch intent.",
        ]
    ) + "\n"


def _decision_memo(
    *,
    admissibility: dict[str, Any],
    strategy: dict[str, Any],
    restart_truthful: bool,
) -> str:
    lane_yes = bool(strategy.get("r1_restart_truthful"))
    admitted = ", ".join(strategy.get("admitted_route_ids", [])) or "none"
    return "\n".join(
        [
            "# R1C Decision Memo",
            "",
            "1. Where exactly was route intent being overridden?",
            "- `run_extraction_v5.py` resolved JSON-managed A-phase step routes from `promptsets/v4/model_map.yaml` before campaign-declared route identity could own the step.",
            "",
            "2. What benchmark-only ownership mechanism was introduced, if any?",
            "- A benchmark-only env-backed route ownership payload is injected by the benchmark adapter and consumed only for phase-A JSON-managed route resolution when explicitly enabled.",
            "",
            "3. Did the two control routes become meaningfully distinct for the lane?",
            f"- {'Yes' if lane_yes else 'No'}.",
            "",
            "4. Did bounded admissibility pass?",
            f"- {'Yes' if str(admissibility.get('status')) == 'admissible' else 'No'}.",
            "",
            "5. Can R1 be restarted truthfully now?",
            f"- {'Yes' if restart_truthful else 'No'}.",
            "",
            "6. If yes, with what exact cohort and lane scope?",
            f"- {admitted}",
            "",
            "7. If no, should the lane be marked non-contestable under current runtime design?",
            (
                "- No; benchmark-mode route ownership restored a truthful bounded contest, "
                "but live provider readiness still needs to be proven before restarting R1."
                if lane_yes and not restart_truthful
                else (
                    "- No; benchmark-mode route ownership restored a truthful bounded contest."
                    if restart_truthful
                    else "- Yes; this lane remains non-contestable without a broader runtime redesign."
                )
            ),
        ]
    ) + "\n"


def run_smoke(
    root: Path | None = None,
    proof_dir: Path | None = None,
    before_run_id: str | None = None,
) -> dict[str, Any]:
    repo = BenchmarkCatalogRepo.from_root(root)
    assignments = _ownership_assignments(repo)
    if not assignments:
        raise RuntimeError("no strict extraction assignments available for route ownership proof")

    executor = AttemptExecutor(root)
    reports = [
        executor.execute_assignments(
            assignments=[assignment],
            case_set_id="r1_first_campaign_v1",
            run_type="benchmark_route_ownership_smoke",
            trigger_ref="TP-RTE-BENCH-R1C",
            benchmark_run_prefix="r1c_owned",
        )
        for assignment in assignments
    ]
    run_ids = [report.benchmark_run_id for report in reports]

    manifest = build_campaign_manifest(build_r1_campaign_plan(repo))
    intended_routes = [
        {
            "route_id": assignment.candidate.route_id,
            "cohort": assignment.candidate.cohort,
            "case_id": assignment.case_id,
            "surface_class": assignment.candidate.surface_class,
            "provider_name": assignment.candidate.provider_name,
            "model_key": assignment.candidate.model_key,
            "provider_model_id": assignment.candidate.provider_model_id,
        }
        for assignment in assignments
    ]
    intended_keys = {(str(item["case_id"]), str(item["route_id"])) for item in intended_routes}
    route_identities, route_errors = _load_route_identities(
        repo=repo,
        run_id=run_ids[0],
        intended_keys=intended_keys,
    )
    for extra_run_id in run_ids[1:]:
        extra_identities, extra_errors = _load_route_identities(
            repo=repo,
            run_id=extra_run_id,
            intended_keys=intended_keys,
        )
        route_identities.extend(extra_identities)
        for key, value in extra_errors.items():
            route_errors.setdefault(key, []).extend(value)
    admissibility = evaluate_admissibility(
        benchmark_run_ids=run_ids,
        route_identities=route_identities,
        intended_routes=intended_routes,
        route_errors=route_errors,
        required_repeat_count=1,
    )
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
    restart_truthful = False
    distinctness = {
        "status": "distinct" if str(admissibility.get("status")) == "admissible" else "blocked",
        "proof_execution_mode": "dry_run",
        "control_signature_hashes": {
            row["route_id"]: row.get("effective_route_signature_hash")
            for row in truth_table
            if str(row.get("cohort")) == "control"
        },
        "lane_distinctness_proven": bool(strategy.get("r1_restart_truthful")),
        "r1_restart_truthful": restart_truthful,
    }
    before_after = _before_after(
        before_repo=repo,
        before_run_id=before_run_id,
        after_route_identities=route_identities,
    )
    payload = {
        "benchmark_run_ids": run_ids,
        "admissibility": admissibility,
        "classification": classification,
        "bounded_distinctness_result": distinctness,
        "bounded_admissibility_result": {
            "status": admissibility.get("status"),
            "campaign_state": admissibility.get("campaign_state"),
            "blocking_reason_codes": admissibility.get("admissibility_blocker_codes", []),
            "proof_execution_mode": "dry_run",
            "lane_distinctness_proven": bool(strategy.get("r1_restart_truthful")),
            "live_provider_readiness": "not_verified_in_r1c",
            "r1_restart_truthful": restart_truthful,
        },
        "corrected_control_strategy": strategy,
        "route_ownership_before_after": before_after,
        "r1_restart_truthful": restart_truthful,
        "db_row_counts": repo.count_rows(),
    }

    if proof_dir is not None:
        proof_dir.mkdir(parents=True, exist_ok=True)
        benchmark_root = benchmark_paths(root).root
        _write_json(proof_dir / "RUN_MANIFEST.json", payload)
        (proof_dir / "route_ownership_design.md").write_text(_design_doc(), encoding="utf-8")
        _write_json(proof_dir / "route_ownership_truth_table.json", truth_table)
        _write_json(proof_dir / "route_ownership_before_after.json", before_after)
        _write_json(proof_dir / "bounded_distinctness_result.json", distinctness)
        _write_json(proof_dir / "bounded_admissibility_result.json", payload["bounded_admissibility_result"])
        (proof_dir / "R1C_DECISION_MEMO.md").write_text(
            _decision_memo(admissibility=admissibility, strategy=strategy, restart_truthful=restart_truthful),
            encoding="utf-8",
        )
        (proof_dir / "IMPLEMENTATION_NOTES.md").write_text(
            "\n".join(
                [
                    "# Implementation Notes",
                    "",
                    "- Benchmark route ownership is opt-in and benchmark-scoped only.",
                    "- The bounded proof uses dry-run execution so it proves route-resolution ownership and emitted telemetry separation without claiming live provider readiness.",
                    "- The bounded proof intentionally excludes non-strict-capable direct candidates from the contested strict extraction lane.",
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
                    f"lane_distinctness_proven={str(strategy['r1_restart_truthful']).lower()}",
                    "live_provider_readiness=not_verified_in_r1c",
                    f"r1_restart_truthful={str(restart_truthful).lower()}",
                    f"admitted_routes={','.join(strategy.get('admitted_route_ids', []))}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        tree_lines = sorted(str(path.relative_to(benchmark_root)) for path in benchmark_root.rglob("*"))
        (proof_dir / "benchmark_tree.txt").write_text("\n".join(tree_lines) + "\n", encoding="utf-8")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run bounded benchmark route ownership proof for R1C.")
    parser.add_argument("--benchmark-root", type=Path, default=None)
    parser.add_argument("--proof-dir", type=Path, default=None)
    parser.add_argument("--before-run-id", default=None)
    args = parser.parse_args(argv)
    payload = run_smoke(root=args.benchmark_root, proof_dir=args.proof_dir, before_run_id=args.before_run_id)
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
