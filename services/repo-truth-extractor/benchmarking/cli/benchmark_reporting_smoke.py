from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
SERVICE_ROOT = HERE.parents[2]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.cli.benchmark_scoring_smoke import run_scoring_smoke
from benchmarking.governance.decision_log import GovernanceDecisionLog
from benchmarking.reporting.pipeline import BenchmarkReportingPipeline
from benchmarking.storage.hashing import stable_json_dumps
from benchmarking.storage.paths import benchmark_paths
from benchmarking.synthesis.governance_pipeline import GovernanceSynthesisPipeline


def _pick_candidate(details: list[dict[str, object]], state: str) -> dict[str, object]:
    for detail in details:
        if detail.get("current_recommendation_state") == state:
            return detail
    return details[0] if details else {}


def run_reporting_smoke(root: Path | None = None, proof_dir: Path | None = None) -> dict[str, object]:
    scoring_payload = run_scoring_smoke(root=root, proof_dir=None)
    governance = GovernanceSynthesisPipeline(root)
    governance.synthesize_run(str(scoring_payload["baseline_run_id"]))
    governance.synthesize_run(str(scoring_payload["benchmark_run_id"]))
    decision_log = GovernanceDecisionLog(governance.repo)
    current_recommendations = [
        item
        for item in governance.repo.list_promotion_recommendations()
        if str(item.get("benchmark_run_id")) == str(scoring_payload["benchmark_run_id"])
    ]
    for recommendation in current_recommendations:
        decisions = governance.repo.list_governance_decisions(str(recommendation["recommendation_id"]))
        if not decisions:
            continue
        latest = decisions[-1]
        decision_log.append_decision(
            recommendation=recommendation,
            decision_type="defer",
            actor="codex_reporting_history",
            reason="S1 reporting smoke appends a superseding governance review touch to exercise history views.",
            evidence_bundle_ids=list(recommendation.get("evidence_bundle_ids", [])),
            governance_packet_ref=str(latest.get("governance_packet_ref") or ""),
            required_action=str(recommendation.get("required_action") or ""),
            supersedes_decision_id=str(latest["decision_id"]),
        )
        break
    reporting = BenchmarkReportingPipeline(root)
    report = reporting.build_reports(
        benchmark_run_id=str(scoring_payload["benchmark_run_id"]),
        prior_run_id=str(scoring_payload["baseline_run_id"]),
    )
    candidate_detail = _pick_candidate(report["candidate_details"], "recommended_for_review")
    experimental_detail = _pick_candidate(report["candidate_details"], "experimental_only")
    governance_history = next(
        (
            item
            for item in sorted(
                report["governance_histories"],
                key=lambda candidate: (
                    len(candidate.get("decision_history", [])),
                    len(candidate.get("recommendation_history", [])),
                ),
                reverse=True,
            )
            if item.get("current_effective_decision") is not None
        ),
        report["governance_histories"][0] if report["governance_histories"] else {},
    )
    change_summary = next(
        (
            item
            for item in report["change_summaries"]
            if item["recommendation_state_change"]["changed"]
        ),
        report["change_summaries"][0] if report["change_summaries"] else {},
    )
    payload = {
        "baseline_run_id": scoring_payload["baseline_run_id"],
        "benchmark_run_id": scoring_payload["benchmark_run_id"],
        "db_row_counts": reporting.repo.count_rows(),
        "sample_portfolio_summary": report["portfolio_summary"],
        "sample_profile_summary": report["profile_summaries"][0] if report["profile_summaries"] else {},
        "sample_candidate_detail": candidate_detail,
        "sample_experimental_candidate_detail": experimental_detail,
        "sample_governance_history": governance_history,
        "sample_change_summary": change_summary,
    }
    if proof_dir is not None:
        proof_dir.mkdir(parents=True, exist_ok=True)
        benchmark_root = benchmark_paths(root).root
        (proof_dir / "RUN_MANIFEST.json").write_text(stable_json_dumps(payload) + "\n", encoding="utf-8")
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
        (proof_dir / "benchmark_tree.txt").write_text(
            "\n".join(sorted(str(path.relative_to(benchmark_root)) for path in benchmark_root.rglob("*"))) + "\n",
            encoding="utf-8",
        )
        (proof_dir / "smoke_output.txt").write_text(
            "\n".join(
                [
                    f"baseline_run_id={scoring_payload['baseline_run_id']}",
                    f"benchmark_run_id={scoring_payload['benchmark_run_id']}",
                    f"candidate_detail_count={len(report['candidate_details'])}",
                    f"governance_history_count={len(report['governance_histories'])}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="M5 reporting smoke for benchmark explainability and operator views.")
    parser.add_argument("--benchmark-root", type=Path, default=None)
    parser.add_argument("--proof-dir", type=Path, default=None)
    args = parser.parse_args(argv)
    payload = run_reporting_smoke(root=args.benchmark_root, proof_dir=args.proof_dir)
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
