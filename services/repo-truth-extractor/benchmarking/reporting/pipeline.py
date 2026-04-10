from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..storage.hashing import stable_json_dumps
from ..storage.paths import run_paths
from ..storage.sqlite_repo import BenchmarkCatalogRepo
from .archetype_summary import build_archetype_summaries
from .candidate_detail import build_candidate_detail
from .change_summary import build_change_summary
from .explainability import candidate_key
from .governance_history import build_governance_history
from .portfolio_summary import build_portfolio_summary
from .profile_summary import build_profile_summaries


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any] | list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json_dumps(payload) + "\n", encoding="utf-8")


class BenchmarkReportingPipeline:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root
        self.repo = BenchmarkCatalogRepo.from_root(root)

    def _run_artifacts(self, benchmark_run_id: str) -> tuple[dict[str, Any], dict[str, dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
        run = run_paths(benchmark_run_id, self.root)
        portfolio_view = _load_json(run.rollups_dir / "PORTFOLIO_VIEW.json")
        profile_fit_rows = {}
        archetype_rollups = {}
        governance_packets = {}
        for path in sorted(run.rollups_dir.glob("PROFILE_FIT__*.json")):
            payload = _load_json(path)
            profile_fit_rows[str(payload["profile_id"])] = payload
        for path in sorted(run.rollups_dir.glob("ARCHETYPE_ROLLUP__*.json")):
            payload = _load_json(path)
            archetype_rollups[str(payload["archetype_id"])] = payload
        for path in sorted(run.governance_dir.glob("GOVERNANCE_PACKET__*.json")):
            payload = _load_json(path)
            governance_packets[str(payload["recommendation_id"])] = payload
        return portfolio_view, profile_fit_rows, archetype_rollups, governance_packets

    def build_reports(self, benchmark_run_id: str, prior_run_id: str | None = None) -> dict[str, Any]:
        current_run = self.repo.fetch_benchmark_run(benchmark_run_id)
        if current_run is None:
            raise RuntimeError(f"missing benchmark run {benchmark_run_id}")
        current_recommendations = [
            item for item in self.repo.list_promotion_recommendations() if str(item.get("benchmark_run_id")) == benchmark_run_id
        ]
        all_decisions = self.repo.list_governance_decisions()
        current_attempts = {item["evidence_bundle_id"]: item for item in self.repo.list_attempts(benchmark_run_id)}
        current_bundles = {
            rec["bundle_id"]: rec
            for rec in [self.repo.fetch_bundle(item["evidence_bundle_id"]) for item in current_attempts.values()]
            if rec is not None
        }
        portfolio_view, profile_fit_rows, archetype_rollups, governance_packets = self._run_artifacts(benchmark_run_id)
        case_set_rollup = _load_json(run_paths(benchmark_run_id, self.root).rollups_dir / "CASESET_ROLLUP__benchmark_registry_starter_v1.json")

        prior_recommendations: list[dict[str, Any]] = []
        prior_histories: dict[str, dict[str, Any]] = {}
        if prior_run_id is not None:
            prior_recommendations = [
                item for item in self.repo.list_promotion_recommendations() if str(item.get("benchmark_run_id")) == prior_run_id
            ]
            for recommendation in prior_recommendations:
                prior_histories[candidate_key(recommendation)] = build_governance_history(
                    recommendation,
                    prior_recommendations,
                    all_decisions,
                )

        portfolio_summary = build_portfolio_summary(benchmark_run_id, portfolio_view, current_recommendations)
        profile_summaries = build_profile_summaries(benchmark_run_id, list(profile_fit_rows.values()), current_recommendations)
        archetype_summaries = build_archetype_summaries(benchmark_run_id, list(archetype_rollups.values()), current_recommendations)

        candidate_details: list[dict[str, Any]] = []
        governance_histories: list[dict[str, Any]] = []
        change_summaries: list[dict[str, Any]] = []
        for recommendation in current_recommendations:
            packet = governance_packets[str(recommendation["recommendation_id"])]
            attempt = current_attempts[str(recommendation["evidence_bundle_ids"][0])]
            bundle = current_bundles[str(recommendation["evidence_bundle_ids"][0])]
            case = self.repo.fetch_benchmark_case(str(attempt["case_id"]))
            if case is None:
                raise RuntimeError(f"missing case for attempt {attempt['case_attempt_id']}")
            control_deltas = self.repo.list_control_deltas(candidate_attempt_id=str(attempt["case_attempt_id"]))
            governance_history = build_governance_history(recommendation, current_recommendations + prior_recommendations, all_decisions)
            candidate_detail = build_candidate_detail(
                recommendation=recommendation,
                governance_packet=packet,
                attempt=attempt,
                bundle=bundle,
                case=case,
                case_set_rollup=case_set_rollup,
                archetype_rollup=archetype_rollups[str(recommendation["archetype_id"])],
                profile_fit=profile_fit_rows[str(recommendation["profile_id"])],
                control_deltas=control_deltas,
                latest_governance_decision=governance_history.get("current_effective_decision"),
            )
            previous = None
            candidate_history_key = governance_history["candidate_key"]
            if prior_recommendations:
                for item in reversed(prior_recommendations):
                    if candidate_key(item) == candidate_history_key:
                        previous = item
                        break
            change_summary = build_change_summary(
                current_recommendation=recommendation,
                previous_recommendation=previous,
                current_history=governance_history,
                previous_history=prior_histories.get(candidate_history_key),
            )
            candidate_details.append(candidate_detail)
            governance_histories.append(governance_history)
            change_summaries.append(change_summary)

        run = run_paths(benchmark_run_id, self.root)
        _write_json(run.recommendations_dir / "PORTFOLIO_SUMMARY.json", portfolio_summary)
        for payload in profile_summaries:
            _write_json(run.recommendations_dir / f"PROFILE_SUMMARY__{payload['profile_id']}.json", payload)
        for payload in archetype_summaries:
            _write_json(run.recommendations_dir / f"ARCHETYPE_SUMMARY__{payload['archetype_id']}.json", payload)
        for payload in candidate_details:
            _write_json(run.recommendations_dir / f"CANDIDATE_DETAIL__{payload['recommendation_id']}.json", payload)
        for payload in governance_histories:
            _write_json(run.governance_dir / f"GOVERNANCE_HISTORY__{payload['candidate_key']}.json", payload)
        for payload in change_summaries:
            _write_json(run.recommendations_dir / f"CHANGE_SUMMARY__{payload['recommendation_id']}.json", payload)

        return {
            "benchmark_run_id": benchmark_run_id,
            "portfolio_summary": portfolio_summary,
            "profile_summaries": profile_summaries,
            "archetype_summaries": archetype_summaries,
            "candidate_details": candidate_details,
            "governance_histories": governance_histories,
            "change_summaries": change_summaries,
        }
