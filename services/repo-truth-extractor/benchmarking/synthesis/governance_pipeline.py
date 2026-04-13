from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..governance.decision_log import GovernanceDecisionLog
from ..models.entities import PromotionRecommendation
from ..models.enums import BenchmarkMode
from ..models.ids import synthetic_id
from ..reporting.governance_reports import GovernanceReportWriter
from ..storage.hashing import hash_json
from ..storage.paths import run_paths
from ..storage.sqlite_repo import BenchmarkCatalogRepo
from .freshness import FreshnessPolicy, evaluate_freshness
from .governance_blockers import RecommendationPolicy, collect_blockers
from .recommendation_packets import build_governance_packet
from .recommendation_states import determine_recommendation_state


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


class GovernanceSynthesisPipeline:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root
        self.repo = BenchmarkCatalogRepo.from_root(root)
        self.report_writer = GovernanceReportWriter(root)
        self.decision_log = GovernanceDecisionLog(self.repo)

    def _rollup_artifacts(self, benchmark_run_id: str, attempt: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
        run = run_paths(benchmark_run_id, self.root)
        case_set_rollup = _load_json(run.rollups_dir / f"CASESET_ROLLUP__{attempt['case_set_id']}.json")
        archetype_rollup = _load_json(run.rollups_dir / f"ARCHETYPE_ROLLUP__{attempt['archetype_id']}.json")
        profile_fit = _load_json(run.rollups_dir / f"PROFILE_FIT__{attempt['profile_id']}.json")
        portfolio_view = _load_json(run.rollups_dir / "PORTFOLIO_VIEW.json")
        return case_set_rollup, archetype_rollup, profile_fit, portfolio_view

    def synthesize_run(self, benchmark_run_id: str) -> dict[str, Any]:
        benchmark_run = self.repo.fetch_benchmark_run(benchmark_run_id)
        if benchmark_run is None:
            raise RuntimeError(f"missing benchmark run {benchmark_run_id}")

        attempts = self.repo.list_attempts(benchmark_run_id)
        attempt_modes = sorted({str(item.get("benchmark_mode") or BenchmarkMode.RUNTIME_ROUTE.value) for item in attempts})
        if any(mode != BenchmarkMode.RUNTIME_ROUTE.value for mode in attempt_modes):
            raise RuntimeError(
                "GovernanceSynthesisPipeline is runtime_route-only; mixed or non-runtime lanes must be synthesized separately: "
                f"{attempt_modes}"
            )
        recommendations: list[dict[str, Any]] = []
        packets: list[dict[str, Any]] = []
        decisions: list[dict[str, Any]] = []
        profile_fit_rows: dict[str, dict[str, Any]] = {}
        portfolio_view: dict[str, Any] | None = None

        freshness_policy = FreshnessPolicy()
        recommendation_policy = RecommendationPolicy()

        for attempt in attempts:
            case = self.repo.fetch_benchmark_case(str(attempt["case_id"]))
            if case is None:
                raise RuntimeError(f"missing case for attempt {attempt['case_attempt_id']}")
            case_set_rollup, archetype_rollup, profile_fit, portfolio_view_payload = self._rollup_artifacts(benchmark_run_id, attempt)
            if portfolio_view is None:
                portfolio_view = portfolio_view_payload
            control_deltas = self.repo.list_control_deltas(candidate_attempt_id=str(attempt["case_attempt_id"]))
            freshness = evaluate_freshness(benchmark_run, attempt, freshness_policy)
            blockers = collect_blockers(
                attempt=attempt,
                case=case,
                profile_fit=profile_fit,
                freshness=freshness,
                control_deltas=control_deltas,
                policy=recommendation_policy,
            )
            state = determine_recommendation_state(attempt, freshness, blockers)
            delta_summary = {
                delta["metric_name"]: float(delta["delta_value"])
                for delta in control_deltas
                if str(delta.get("delta_state", "")).startswith("computed")
            }
            recommendation = PromotionRecommendation(
                recommendation_id=synthetic_id("recommendation", f"{benchmark_run_id}_{attempt['case_attempt_id']}"),
                benchmark_run_id=benchmark_run_id,
                benchmark_mode=str(attempt["benchmark_mode"]),
                candidate_type=str(attempt["candidate_type"]),
                route_id=str(attempt["route_id"]),
                surface_id=str(attempt["surface_id"]),
                archetype_id=str(attempt["archetype_id"]),
                profile_id=str(attempt["profile_id"]),
                runtime_version=str(attempt["runtime_version"]),
                contract_version=str(attempt["contract_version"]),
                contract_snapshot_id=str(attempt["contract_snapshot_id"]),
                freshness_state=state.freshness_state,
                dispute_state=state.dispute_state,
                recommendation_state=state.recommendation_state,
                failed_gates=state.failed_gates,
                evidence_bundle_ids=[str(attempt["evidence_bundle_id"])],
                relevant_rollup_ids=[
                    f"CASESET_ROLLUP__{attempt['case_set_id']}",
                    f"ARCHETYPE_ROLLUP__{attempt['archetype_id']}",
                    f"PROFILE_FIT__{attempt['profile_id']}",
                    "PORTFOLIO_VIEW",
                ],
                control_delta_summary=delta_summary,
                required_action=state.required_action,
                requires_review=state.requires_review,
                content_hash=hash_json(
                    {
                        "recommendation_id": synthetic_id("recommendation", f"{benchmark_run_id}_{attempt['case_attempt_id']}"),
                        "recommendation_state": state.recommendation_state,
                        "failed_gates": state.failed_gates,
                    }
                ),
                source_ref="m4_governance_pipeline",
            )
            self.repo.insert_promotion_recommendation(recommendation)
            recommendation_payload = self.repo.fetch_promotion_recommendation(recommendation.recommendation_id)
            assert recommendation_payload is not None
            packet = build_governance_packet(
                recommendation=recommendation_payload,
                attempt=attempt,
                case=case,
                profile_fit=profile_fit,
                case_set_rollup=case_set_rollup,
                archetype_rollup=archetype_rollup,
                control_deltas=control_deltas,
            )
            packet["governance_packet_ref"] = str(
                run_paths(benchmark_run_id, self.root).governance_dir / f"GOVERNANCE_PACKET__{recommendation.recommendation_id}.json"
            )
            recommendations.append(recommendation_payload)
            packets.append(packet)

            profile_copy = dict(profile_fit_rows.get(str(profile_fit["profile_id"])) or profile_fit)
            counts = dict(profile_copy.get("recommendation_state_counts", {}))
            counts[state.recommendation_state] = int(counts.get(state.recommendation_state, 0)) + 1
            recommendation_refs = list(profile_copy.get("recommendation_ids", []))
            recommendation_refs.append(recommendation.recommendation_id)
            profile_copy["recommendation_state_counts"] = counts
            profile_copy["recommendation_ids"] = recommendation_refs
            profile_fit_rows[str(profile_fit["profile_id"])] = profile_copy

        if portfolio_view is None:
            raise RuntimeError("missing portfolio view for governance synthesis")

        portfolio_view = dict(portfolio_view)
        portfolio_view["recommendation_state_matrix"] = [
            {
                "recommendation_id": rec["recommendation_id"],
                "route_id": rec["route_id"],
                "surface_id": rec["surface_id"],
                "profile_id": rec["profile_id"],
                "archetype_id": rec["archetype_id"],
                "recommendation_state": rec["recommendation_state"],
            }
            for rec in recommendations
        ]

        reviewable = next(
            (
                rec
                for rec in recommendations
                if rec["recommendation_state"] in {"recommended_for_review", "eligible_for_review"}
            ),
            recommendations[0] if recommendations else None,
        )
        if reviewable is not None:
            packet_ref = next(
                packet["governance_packet_ref"]
                for packet in packets
                if packet["recommendation_id"] == reviewable["recommendation_id"]
            )
            decision = self.decision_log.append_decision(
                recommendation=reviewable,
                decision_type="defer",
                actor="codex_smoke_operator",
                reason="M4 smoke records append-only governance review without auto-promotion.",
                evidence_bundle_ids=list(reviewable.get("evidence_bundle_ids", [])),
                governance_packet_ref=packet_ref,
                required_action=str(reviewable["required_action"]),
            )
            decision_payload = self.repo.fetch_governance_decision(decision.decision_id)
            assert decision_payload is not None
            decisions.append(decision_payload)

        self.report_writer.write_packets(
            benchmark_run_id=benchmark_run_id,
            recommendations=recommendations,
            packets=packets,
            decisions=decisions,
            profile_fit_rows=list(profile_fit_rows.values()),
            portfolio_view=portfolio_view,
        )
        return {
            "benchmark_run_id": benchmark_run_id,
            "recommendations": recommendations,
            "governance_packets": packets,
            "governance_decisions": decisions,
            "profile_fit_rows": list(profile_fit_rows.values()),
            "portfolio_view": portfolio_view,
            "sample_recommendation": recommendations[0] if recommendations else {},
            "sample_governance_packet": packets[0] if packets else {},
            "sample_governance_decision": decisions[0] if decisions else {},
        }
