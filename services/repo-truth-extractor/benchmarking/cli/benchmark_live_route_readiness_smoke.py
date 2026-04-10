from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import types
from dataclasses import replace
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
SERVICE_ROOT = HERE.parents[2]
REPO_ROOT = HERE.parents[4]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.campaigns.admissibility import evaluate_admissibility
from benchmarking.campaigns.route_identity import RouteTelemetryError, build_route_identity_record
from benchmarking.campaigns.route_separation import build_route_identity_truth_table
from benchmarking.campaigns.selection import CampaignAssignment, build_r1_campaign_plan
from benchmarking.orchestration.attempt_executor import AttemptExecutor
from benchmarking.storage.hashing import stable_json_dumps
from benchmarking.storage.paths import benchmark_paths
from benchmarking.storage.sqlite_repo import BenchmarkCatalogRepo


STRICT_LIVE_ROUTE_IDS = {
    "route_openrouter_openai_gpt_5_4_v1",
    "route_openai_gpt_5_4_v1",
    "route_openrouter_openai_gpt_5_3_codex_v1",
}


def _load_runner_module() -> types.ModuleType:
    module_path = SERVICE_ROOT / "run_extraction_v5.py"
    spec = importlib.util.spec_from_file_location("run_extraction_v5_r1d_live_readiness", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _make_cfg(runner: types.ModuleType):
    cfg = runner.RunnerConfig.__new__(runner.RunnerConfig)
    defaults = {
        "dry_run": False,
        "max_files_docs": 35,
        "max_files_code": 20,
        "max_chars": 650000,
        "max_request_bytes": 200000,
        "file_truncate_chars": 70000,
        "home_scan_mode": "safe",
        "resume": False,
        "fail_fast_auth": True,
        "gemini_auth_mode": "auto",
        "gemini_transport": "sdk",
        "openai_transport": "openai_sdk",
        "xai_transport": "openai_sdk",
        "retry_policy": "default",
        "retry_max_attempts": 1,
        "retry_base_seconds": 0.0,
        "retry_max_seconds": 0.0,
        "phase_auth_fail_threshold": 1,
        "partition_workers": 1,
        "debug_phase_inputs": False,
        "fail_fast_missing_inputs": False,
        "executor": "thread",
        "routing_policy": "cost",
        "disable_escalation": False,
        "escalation_max_hops": 2,
        "batch_mode": False,
        "batch_provider": "auto",
        "batch_poll_seconds": 30,
        "batch_wait_timeout_seconds": 1800,
        "batch_max_requests_per_job": 2000,
        "batch_submit_only": False,
        "webhook_url": "",
        "webhook_secret": "",
        "webhook_timeout_seconds": 5,
        "webhook_required": False,
        "webhook_auto_continue": False,
        "live_ok": True,
        "selected_s_steps": None,
        "selected_execution_step": None,
        "d0_max_files": None,
        "d1_max_files": None,
        "provider_denylist": (),
        "compare_mode": None,
        "compare_model": None,
        "compare_provider": None,
        "compare_steps": None,
        "prescan_dir": None,
        "router": None,
        "max_cost_usd": None,
        "ledger": None,
    }
    for key, value in defaults.items():
        object.__setattr__(cfg, key, value)
    return cfg


def _write_json(path: Path, payload: dict[str, Any] | list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json_dumps(payload) + "\n", encoding="utf-8")


def _live_assignments(repo: BenchmarkCatalogRepo) -> list[CampaignAssignment]:
    plan = build_r1_campaign_plan(repo)
    selected = [
        assignment
        for assignment in plan.campaign_assignments
        if assignment.case_id == "strict_extract_conflicting_evidence_v1"
        and assignment.candidate.route_id in STRICT_LIVE_ROUTE_IDS
    ]
    return [
        replace(
            assignment,
            live_execution=True,
            benchmark_route_ownership_mode="strict_extraction_lane_owned_v1",
            benchmark_route_ownership_scope="phase_a_json_managed",
            operator_note=(
                assignment.operator_note
                + " "
                + "R1D bounded live owned-lane readiness proof."
            ).strip(),
        )
        for assignment in selected
    ]


def _ownership_payload(assignment: CampaignAssignment, route_record: dict[str, Any]) -> str:
    provider_name = assignment.candidate.provider_name
    provider_model_id = assignment.candidate.provider_model_id
    return json.dumps(
        {
            "enabled": True,
            "mode": "strict_extraction_lane_owned_v1",
            "scope": "phase_a_json_managed",
            "target_phase": assignment.phase,
            "benchmark_case_id": assignment.case_id,
            "route_id": assignment.candidate.route_id,
            "surface_id": assignment.candidate.surface_id,
            "surface_class": assignment.candidate.surface_class,
            "provider_name": provider_name,
            "model_key": assignment.candidate.model_key,
            "provider_model_id": provider_model_id,
            "route_pin": str(route_record.get("route_pin") or ""),
            "api_key_env": str(route_record.get("api_key_ref") or ""),
            "strict_json_schema": True,
            "strict_passthrough_verified": bool(route_record.get("strict_passthrough_verified"))
            or (
                str(provider_name).strip().lower() == "openrouter"
                and str(provider_model_id).strip().startswith("openai/")
            ),
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def _provider_readiness(repo: BenchmarkCatalogRepo, assignments: list[CampaignAssignment]) -> dict[str, Any]:
    runner = _load_runner_module()
    cfg = _make_cfg(runner)
    rows: list[dict[str, Any]] = []
    original_payload = os.environ.get("DPMX_BENCHMARK_ROUTE_OWNERSHIP")
    try:
        for assignment in assignments:
            route_record = repo.fetch_route(assignment.candidate.route_id)
            if route_record is None:
                continue
            os.environ["DPMX_BENCHMARK_ROUTE_OWNERSHIP"] = _ownership_payload(assignment, route_record)
            readiness_summary = runner.derive_route_readiness_summary(["A"], "cost")
            probe = runner.run_provider_doctor_probe(
                provider=assignment.candidate.provider_name,
                model_id=assignment.candidate.provider_model_id,
                api_key_env=str(route_record.get("api_key_ref") or ""),
                cfg=cfg,
            )
            ready = int(probe.get("status_code") or 0) == 200 and not probe.get("failure_type")
            rows.append(
                {
                    "route_id": assignment.candidate.route_id,
                    "cohort": assignment.candidate.cohort,
                    "provider_name": assignment.candidate.provider_name,
                    "provider_model_id": assignment.candidate.provider_model_id,
                    "api_key_env": str(route_record.get("api_key_ref") or ""),
                    "benchmark_route_ownership_mode": assignment.benchmark_route_ownership_mode,
                    "benchmark_route_ownership_scope": assignment.benchmark_route_ownership_scope,
                    "route_readiness_summary": readiness_summary,
                    "provider_probe": probe,
                    "ready": ready,
                }
            )
    finally:
        if original_payload is None:
            os.environ.pop("DPMX_BENCHMARK_ROUTE_OWNERSHIP", None)
        else:
            os.environ["DPMX_BENCHMARK_ROUTE_OWNERSHIP"] = original_payload
    ready_route_ids = [row["route_id"] for row in rows if row["ready"]]
    control_rows = [row for row in rows if row["cohort"] == "control"]
    premium_rows = [row for row in rows if row["cohort"] == "premium"]
    return {
        "status": "ready" if rows and all(row["ready"] for row in rows) else "blocked",
        "routes": rows,
        "ready_route_ids": ready_route_ids,
        "required_control_pair_ready": len(control_rows) == 2 and all(row["ready"] for row in control_rows),
        "premium_candidate_ready": all(row["ready"] for row in premium_rows) if premium_rows else False,
    }


def _load_route_identities(
    repo: BenchmarkCatalogRepo,
    benchmark_run_ids: list[str],
    intended_keys: set[tuple[str, str]],
) -> tuple[list[Any], dict[tuple[str, str], list[dict[str, str]]]]:
    route_identities: list[Any] = []
    route_errors: dict[tuple[str, str], list[dict[str, str]]] = {}
    for run_id in benchmark_run_ids:
        for attempt in repo.list_attempts(run_id):
            key = (str(attempt["case_id"]), str(attempt["route_id"]))
            if key not in intended_keys:
                continue
            try:
                route_identities.append(build_route_identity_record(repo, attempt))
            except RouteTelemetryError as exc:
                route_errors.setdefault(key, []).append(
                    {"blocker_code": exc.blocker_code, "message": str(exc)}
                )
    return route_identities, route_errors


def _route_spend_summary(repo: BenchmarkCatalogRepo, route_identities: list[Any]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    total_spend = 0.0
    for record in route_identities:
        bundle = repo.fetch_bundle(record.evidence_bundle_id)
        if bundle is None:
            continue
        attempt_root = Path(str(bundle["root_path"]))
        route_trace = json.loads((attempt_root / "ROUTE_TRACE.json").read_text(encoding="utf-8"))
        run_root = Path(str(route_trace.get("run_root") or ""))
        spend_ledger_path = run_root / "spend_ledger.json"
        spend_payload = {}
        observed_spend = None
        if spend_ledger_path.exists():
            spend_payload = json.loads(spend_ledger_path.read_text(encoding="utf-8"))
            observed_spend = spend_payload.get("actual_cost_usd")
            if observed_spend is None:
                observed_spend = spend_payload.get("total_actual_cost_usd")
            if observed_spend is None:
                observed_spend = spend_payload.get("total_cost_usd")
        if observed_spend is not None:
            total_spend += float(observed_spend)
        rows.append(
            {
                "route_id": record.declared_route_id,
                "case_attempt_id": record.case_attempt_id,
                "spend_ledger_path": str(spend_ledger_path),
                "observed_spend_usd": observed_spend,
                "spend_payload": spend_payload,
            }
        )
    return {"total_observed_spend_usd": round(total_spend, 6), "attempts": rows}


def _decision_memo(
    *,
    readiness: dict[str, Any],
    admissibility: dict[str, Any],
    restart_truthful: bool,
    live_attempted_route_ids: list[str],
) -> str:
    ready_routes = ", ".join(readiness.get("ready_route_ids", [])) or "none"
    attempted_routes = ", ".join(live_attempted_route_ids) or "none"
    failures = [
        f"{row['route_id']}:{row['provider_probe'].get('failure_type') or row['provider_probe'].get('status_code')}"
        for row in readiness.get("routes", [])
        if not row.get("ready")
    ]
    return "\n".join(
        [
            "# R1D Decision Memo",
            "",
            "1. Which live providers/routes were actually ready?",
            f"- {ready_routes}",
            "",
            "2. Did the owned lane remain distinct under live execution?",
            f"- {'Yes' if str(admissibility.get('status')) == 'admissible' else 'No'}",
            "",
            "3. Did live admissibility pass?",
            f"- {'Yes' if str(admissibility.get('status')) == 'admissible' else 'No'}",
            "",
            "4. What failures or anomalies occurred?",
            f"- {', '.join(failures) if failures else 'none observed'}",
            "",
            "5. Can R1 be restarted truthfully now?",
            f"- {'Yes' if restart_truthful else 'No'}",
            "",
            "6. If yes, with what exact cohort and lane scope?",
            f"- {attempted_routes}",
            "",
            "7. If no, what exact blocker still prevents restart?",
            (
                "- OpenRouter-owned control/candidate routes were not live-ready, so the owned strict extraction lane lacks enough live evidence for a truthful control-pair restart."
                if not restart_truthful
                else "- none"
            ),
        ]
    ) + "\n"


def run_smoke(root: Path | None = None, proof_dir: Path | None = None) -> dict[str, Any]:
    repo = BenchmarkCatalogRepo.from_root(root)
    assignments = _live_assignments(repo)
    if not assignments:
        raise RuntimeError("no owned strict-extraction assignments available for R1D")

    readiness = _provider_readiness(repo, assignments)
    ready_route_ids = set(readiness["ready_route_ids"])
    ready_assignments = [assignment for assignment in assignments if assignment.candidate.route_id in ready_route_ids]

    benchmark_run_ids: list[str] = []
    if ready_assignments:
        executor = AttemptExecutor(root)
        for assignment in ready_assignments:
            report = executor.execute_assignments(
                assignments=[assignment],
                case_set_id="r1_first_campaign_v1",
                run_type="benchmark_live_route_readiness_smoke",
                trigger_ref="TP-RTE-BENCH-R1D",
                benchmark_run_prefix="r1d_live",
            )
            benchmark_run_ids.append(report.benchmark_run_id)

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
    route_identities, route_errors = _load_route_identities(repo, benchmark_run_ids, intended_keys)
    admissibility = evaluate_admissibility(
        benchmark_run_ids=benchmark_run_ids,
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
    spend_summary = _route_spend_summary(repo, route_identities)
    restart_truthful = bool(readiness.get("required_control_pair_ready")) and str(admissibility.get("status")) == "admissible"
    distinctness = {
        "status": "distinct" if str(admissibility.get("status")) == "admissible" else "blocked",
        "live_attempted_route_ids": sorted(ready_route_ids),
        "control_signature_hashes": {
            row["route_id"]: row.get("effective_route_signature_hash")
            for row in truth_table
            if str(row.get("cohort")) == "control"
        },
        "r1_restart_truthful": restart_truthful,
    }
    live_admissibility = {
        "status": str(admissibility.get("status")),
        "campaign_state": str(admissibility.get("campaign_state")),
        "blocking_reason_codes": list(admissibility.get("admissibility_blocker_codes", [])),
        "benchmark_run_ids": benchmark_run_ids,
        "live_ready_route_ids": sorted(ready_route_ids),
        "r1_restart_truthful": restart_truthful,
    }
    payload = {
        "provider_readiness_report": readiness,
        "live_route_identity_truth_table": truth_table,
        "live_distinctness_result": distinctness,
        "live_admissibility_result": live_admissibility,
        "spend_and_failure_summary": {
            **spend_summary,
            "provider_failures": [
                {
                    "route_id": row["route_id"],
                    "failure_type": row["provider_probe"].get("failure_type"),
                    "status_code": row["provider_probe"].get("status_code"),
                    "provider_error_reason": row["provider_probe"].get("provider_error_reason"),
                }
                for row in readiness["routes"]
                if not row["ready"]
            ],
        },
        "benchmark_run_ids": benchmark_run_ids,
        "r1_restart_truthful": restart_truthful,
    }

    if proof_dir is not None:
        proof_dir.mkdir(parents=True, exist_ok=True)
        benchmark_root = benchmark_paths(root).root
        _write_json(proof_dir / "RUN_MANIFEST.json", payload)
        _write_json(proof_dir / "provider_readiness_report.json", readiness)
        _write_json(proof_dir / "live_route_identity_truth_table.json", truth_table)
        _write_json(proof_dir / "live_distinctness_result.json", distinctness)
        _write_json(proof_dir / "live_admissibility_result.json", live_admissibility)
        _write_json(proof_dir / "spend_and_failure_summary.json", payload["spend_and_failure_summary"])
        (proof_dir / "R1D_DECISION_MEMO.md").write_text(
            _decision_memo(
                readiness=readiness,
                admissibility=admissibility,
                restart_truthful=restart_truthful,
                live_attempted_route_ids=sorted(ready_route_ids),
            ),
            encoding="utf-8",
        )
        (proof_dir / "provider_preflight_output.txt").write_text(
            stable_json_dumps(readiness) + "\n",
            encoding="utf-8",
        )
        (proof_dir / "smoke_output.txt").write_text(
            "\n".join(
                [
                    f"ready_routes={','.join(sorted(ready_route_ids))}",
                    f"benchmark_run_ids={','.join(benchmark_run_ids)}",
                    f"live_admissibility_status={live_admissibility['status']}",
                    f"r1_restart_truthful={str(restart_truthful).lower()}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run bounded live owned-lane readiness proof for R1D.")
    parser.add_argument("--benchmark-root", type=Path, default=None)
    parser.add_argument("--proof-dir", type=Path, default=None)
    args = parser.parse_args(argv)
    payload = run_smoke(root=args.benchmark_root, proof_dir=args.proof_dir)
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
