from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
SERVICE_ROOT = HERE.parents[2]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.campaigns.manifest import build_campaign_manifest
from benchmarking.campaigns.selection import build_r1_campaign_plan
from benchmarking.orchestration.attempt_executor import AttemptExecutor
from benchmarking.reporting.pipeline import BenchmarkReportingPipeline
from benchmarking.rollups.pipeline import BenchmarkScoringPipeline
from benchmarking.storage.hashing import stable_json_dumps
from benchmarking.storage.paths import benchmark_paths, run_paths
from benchmarking.storage.sqlite_repo import BenchmarkCatalogRepo
from benchmarking.synthesis.governance_pipeline import GovernanceSynthesisPipeline


def _write_json(path: Path, payload: dict[str, Any] | list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json_dumps(payload) + "\n", encoding="utf-8")


def _preflight_output() -> str:
    command = [
        sys.executable,
        str(SERVICE_ROOT / "run_extraction_v5.py"),
        "--preset",
        "first-live",
        "--dry-run",
        "--preflight-providers",
    ]
    result = subprocess.run(
        command,
        cwd=str(SERVICE_ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    return (result.stdout or "") + ("\n" + result.stderr if result.stderr else "")


def _decision_rows(candidate_details: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for detail in candidate_details:
        control_rows = detail.get("control_deltas", [])
        control_anchor_used = None
        if control_rows:
            control_anchor_used = control_rows[0].get("anchor_attempt_id")
        rows.append(
            {
                "route_id": detail["route_id"],
                "surface_class": detail["surface_class"],
                "cohort": detail.get("cohort"),
                "archetype_id": detail["archetype_id"],
                "target_profile": detail["profile_id"],
                "recommendation_state": detail["current_recommendation_state"],
                "required_action": detail["required_action"],
                "key_blockers": detail["failed_gates"],
                "control_anchor_used": control_anchor_used,
                "evidence_bundle_refs": [detail["evidence_bundle_ref"]],
                "operator_note": (
                    "phase_s caveat remains in force."
                    if detail.get("phase_caveat")
                    else "Bounded R1 route contest on current harness."
                ),
            }
        )
    return rows


def _load_admissibility_gate(root: Path | None, benchmark_run_id: str) -> dict[str, Any]:
    artifact_path = run_paths(benchmark_run_id, root).recommendations_dir / "ROUTE_IDENTITY_ADMISSIBILITY.json"
    if not artifact_path.exists():
        raise RuntimeError(
            "campaign admission requires a route identity admissibility artifact. "
            f"Missing: {artifact_path}"
        )
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    if str(payload.get("status")) != "admissible":
        raise RuntimeError(
            "campaign admission blocked by route identity admissibility gate: "
            f"{payload.get('admissibility_blocker_codes', [])}"
        )
    return payload


def _policy_recommendations(candidate_details: list[dict[str, Any]]) -> list[str]:
    states = [str(item["current_recommendation_state"]) for item in candidate_details]
    recommendations: list[str] = []
    if any(state == "recommended_for_review" for state in states):
        recommendations.append(
            "Adopt an initial weekly bounded strict-extraction cadence on the repo-truth-extractor service root for production-eligible routes that remain recommended_for_review."
        )
    if any("phase_s_policy_sensitive" == item.get("phase_caveat") for item in candidate_details):
        recommendations.append(
            "Keep phase_s under stricter manual review; R1 did not add new provider-backed evidence strong enough to weaken that caveat."
        )
    if any("experimental_only" == state for state in states):
        recommendations.append(
            "Maintain experimental_lab containment for local/open-weight routes; R1 continues to show they should not leave policy containment automatically."
        )
    if any("ineligible" == state for state in states):
        recommendations.append(
            "Do not widen production thresholds for candidates missing clean control-relative evidence or carrying unresolved governance blockers."
        )
    if not recommendations:
        recommendations.append("No policy adjustment is justified beyond continuing the bounded campaign cadence.")
    return recommendations


def _post_run_decision_memo(
    *,
    plan_manifest: dict[str, Any],
    candidate_details: list[dict[str, Any]],
    baseline_run_id: str,
    campaign_run_id: str,
) -> str:
    decision_rows = _decision_rows(candidate_details)
    recommendations = _policy_recommendations(candidate_details)
    recommended = [row["route_id"] for row in decision_rows if row["recommendation_state"] == "recommended_for_review"]
    experimental = [row["route_id"] for row in decision_rows if row["recommendation_state"] == "experimental_only"]
    blocked = [
        row["route_id"]
        for row in decision_rows
        if row["recommendation_state"] in {"ineligible", "quarantined", "stale_disputed"}
    ]
    return "\n".join(
        [
            "# POST_RUN_DECISION_MEMO",
            "",
            f"- campaign_id: {plan_manifest['campaign_id']}",
            f"- baseline_run_id: {baseline_run_id}",
            f"- campaign_run_id: {campaign_run_id}",
            f"- repo_root: {plan_manifest['repo_root']}",
            "",
            "## Recommendation states",
            f"- recommended_for_review: {', '.join(recommended) if recommended else 'none'}",
            f"- experimental_only: {', '.join(experimental) if experimental else 'none'}",
            f"- ineligible_or_quarantined: {', '.join(blocked) if blocked else 'none'}",
            "",
            "## Control anchor posture",
            "- Keep the existing OpenRouter strict anchor and direct OpenAI anchor for now; both remain the only bounded comparable baselines exercised in this campaign.",
            "",
            "## Policy recommendations",
            *[f"- {item}" for item in recommendations],
            "",
            "## Unresolved questions",
            "- R1 only contests the live runtime-v5 A-phase path on the repo-truth-extractor service root; broader archetype expansion still depends on provider-backed adapters beyond runtime_v5.",
            "- Strict contract steps remain pinned by promptsets/v4 model_map.yaml, so direct-provider candidates primarily contest non-strict A-lane steps in this bounded campaign.",
            "- The admitted cohort was reduced below the packet maximum after observing real live-step latency; the held-out balanced and experimental routes remain unbenchmarked rather than implicitly rejected.",
            "- Recommendation history is still reconstructed across runs rather than stored as a first-class recommendation-history table.",
            "",
            "## Decision table",
            *[
                f"- {row['route_id']} | {row['surface_class']} | {row['archetype_id']} | {row['target_profile']} | {row['recommendation_state']} | {row['required_action']} | blockers={row['key_blockers']}"
                for row in decision_rows
            ],
            "",
        ]
    )


def run_campaign(
    root: Path | None = None,
    proof_dir: Path | None = None,
    admissibility_run_id: str | None = None,
) -> dict[str, Any]:
    repo = BenchmarkCatalogRepo.from_root(root)
    plan = build_r1_campaign_plan(repo)
    manifest = build_campaign_manifest(plan)
    preflight = _preflight_output()
    if not admissibility_run_id:
        raise RuntimeError("campaign admission requires --admissibility-run-id")
    admissibility_gate = _load_admissibility_gate(root, admissibility_run_id)

    executor = AttemptExecutor(root)
    scoring = BenchmarkScoringPipeline(root)
    governance = GovernanceSynthesisPipeline(root)
    reporting = BenchmarkReportingPipeline(root)

    campaign_report = executor.execute_assignments(
        assignments=plan.campaign_assignments,
        case_set_id=plan.case_set_id,
        run_type="benchmark_campaign_candidate",
        trigger_ref=plan.campaign_id,
        benchmark_run_prefix="r1_campaign",
    )
    scoring_payload = scoring.score_run(campaign_report.benchmark_run_id)
    governance_payload = governance.synthesize_run(campaign_report.benchmark_run_id)
    reporting_payload = reporting.build_reports(campaign_report.benchmark_run_id)
    decision_rows = _decision_rows(reporting_payload["candidate_details"])
    memo = _post_run_decision_memo(
        plan_manifest=manifest,
        candidate_details=reporting_payload["candidate_details"],
        baseline_run_id="same_run_controls",
        campaign_run_id=campaign_report.benchmark_run_id,
    )

    payload = {
        "campaign_id": plan.campaign_id,
        "baseline_run_id": "same_run_controls",
        "campaign_run_id": campaign_report.benchmark_run_id,
        "selected_candidate_set": [
            {
                "route_id": item["route_id"],
                "cohort": item["cohort"],
                "surface_class": item["surface_class"],
                "provider_name": item["provider_name"],
                "model_key": item["model_key"],
                "case_id": item["case_id"],
                "archetype_id": item["archetype_id"],
                "profile_id": item["profile_id"],
                "admission_reason": item["admission_reason"],
            }
            for item in manifest["campaign_candidates"]
        ],
        "recommendation_states": [
            {
                "route_id": item["route_id"],
                "archetype_id": item["archetype_id"],
                "profile_id": item["target_profile"],
                "recommendation_state": item["recommendation_state"],
                "required_action": item["required_action"],
                "key_blockers": item["key_blockers"],
            }
            for item in decision_rows
        ],
        "db_row_counts": repo.count_rows(),
        "sample_recommendation": governance_payload["sample_recommendation"],
        "sample_governance_packet": governance_payload["sample_governance_packet"],
        "sample_candidate_detail": reporting_payload["candidate_details"][0] if reporting_payload["candidate_details"] else {},
        "sample_portfolio_summary": reporting_payload["portfolio_summary"],
        "policy_recommendations": _policy_recommendations(reporting_payload["candidate_details"]),
        "admissibility_run_id": admissibility_run_id,
        "admissibility_gate": admissibility_gate,
    }

    if proof_dir is not None:
        proof_dir.mkdir(parents=True, exist_ok=True)
        benchmark_root = benchmark_paths(root).root
        _write_json(proof_dir / "RUN_MANIFEST.json", payload)
        _write_json(proof_dir / "CAMPAIGN_MANIFEST.json", manifest)
        _write_json(proof_dir / "db_row_counts.json", payload["db_row_counts"])
        _write_json(proof_dir / "sample_portfolio_summary.json", reporting_payload["portfolio_summary"])
        if reporting_payload["profile_summaries"]:
            _write_json(proof_dir / "sample_profile_summary.json", reporting_payload["profile_summaries"][0])
        if reporting_payload["candidate_details"]:
            sample_detail = reporting_payload["candidate_details"][0]
            _write_json(
                proof_dir / f"sample_candidate_detail__{sample_detail['recommendation_id']}.json",
                sample_detail,
            )
        if governance_payload["governance_packets"]:
            sample_packet = governance_payload["governance_packets"][0]
            _write_json(
                proof_dir / f"sample_governance_packet__{sample_packet['recommendation_id']}.json",
                sample_packet,
            )
        if governance_payload["recommendations"]:
            sample_rec = governance_payload["recommendations"][0]
            _write_json(
                proof_dir / f"sample_recommendation__{sample_rec['recommendation_id']}.json",
                sample_rec,
            )
        _write_json(proof_dir / "candidate_matrix.json", decision_rows)
        (proof_dir / "POST_RUN_DECISION_MEMO.md").write_text(memo, encoding="utf-8")
        (proof_dir / "campaign_preflight.txt").write_text(preflight, encoding="utf-8")
        (proof_dir / "smoke_output.txt").write_text(
            "\n".join(
                [
                    "baseline_run_id=same_run_controls",
                    f"campaign_run_id={campaign_report.benchmark_run_id}",
                    f"selected_routes={','.join(item['route_id'] for item in payload['selected_candidate_set'])}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        tree_lines = sorted(str(path.relative_to(benchmark_root)) for path in benchmark_root.rglob("*"))
        (proof_dir / "benchmark_tree.txt").write_text("\n".join(tree_lines) + "\n", encoding="utf-8")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the bounded R1 benchmark campaign.")
    parser.add_argument("--benchmark-root", type=Path, default=None)
    parser.add_argument("--proof-dir", type=Path, default=None)
    parser.add_argument("--admissibility-run-id", default=None)
    args = parser.parse_args(argv)
    payload = run_campaign(
        root=args.benchmark_root,
        proof_dir=args.proof_dir,
        admissibility_run_id=args.admissibility_run_id,
    )
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
