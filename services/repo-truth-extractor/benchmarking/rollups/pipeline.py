from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from ..models.entities import BenchmarkCaseAttempt
from ..models.enums import BenchmarkMode
from ..rollups.archetype_rollups import build_archetype_rollups
from ..rollups.case_set_rollups import build_case_set_rollup
from ..rollups.portfolio_view import build_portfolio_view
from ..rollups.profile_fit import build_profile_fit_rows
from ..rollups.regression_compare import build_regression_comparison
from ..scoring.contract_gate import evaluate_contract_gate
from ..scoring.control_deltas import compute_control_deltas
from ..scoring.operational_metrics import normalize_operational_metrics
from ..scoring.task_scoring import score_attempt
from ..storage.hashing import stable_json_dumps
from ..storage.paths import run_paths
from ..storage.sqlite_repo import BenchmarkCatalogRepo


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any] | list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = stable_json_dumps(payload) + "\n"
    path.write_text(raw, encoding="utf-8")


class BenchmarkScoringPipeline:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root
        self.repo = BenchmarkCatalogRepo.from_root(root)

    def _bundle_artifacts(self, attempt: dict[str, Any]) -> dict[str, dict[str, Any]]:
        bundle = self.repo.fetch_bundle(str(attempt["evidence_bundle_id"]))
        if bundle is None:
            raise RuntimeError(f"missing evidence bundle for {attempt['case_attempt_id']}")
        bundle_root = Path(str(bundle["root_path"]))
        return {
            "route_trace": _load_json(bundle_root / "ROUTE_TRACE.json"),
            "task_eval": _load_json(bundle_root / "TASK_EVAL.json"),
            "validator_results": _load_json(bundle_root / "VALIDATOR_RESULTS.json"),
            "executor_links": _load_json(bundle_root / "EXECUTOR_LINKS.json"),
        }

    def _anchor_attempt(
        self,
        attempt: dict[str, Any],
        prior_run_id: str | None,
        current_candidates: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any] | None:
        candidates: list[dict[str, Any]] = []
        if prior_run_id is not None:
            candidates = self.repo.list_attempts(prior_run_id)
        elif current_candidates is not None:
            candidates = list(current_candidates)
        if not candidates:
            return None
        anchor_group = self.repo.fetch_control_anchor_group(str(attempt["control_anchor_group_id"]))
        allowed_routes = set(anchor_group.get("route_ids", [])) if anchor_group is not None else set()
        for candidate in reversed(candidates):
            if allowed_routes and str(candidate.get("route_id")) not in allowed_routes:
                continue
            if all(
                attempt.get(field) == candidate.get(field)
                for field in (
                    "case_id",
                    "surface_class",
                    "runtime_version",
                    "contract_snapshot_id",
                    "validator_suite_id",
                    "retry_policy_id",
                )
            ):
                return candidate
        return None

    def score_run(self, benchmark_run_id: str, prior_run_id: str | None = None) -> dict[str, Any]:
        run = self.repo.fetch_benchmark_run(benchmark_run_id)
        if run is None:
            raise RuntimeError(f"missing benchmark run {benchmark_run_id}")
        attempts = self.repo.list_attempts(benchmark_run_id)
        attempt_modes = sorted({str(item.get("benchmark_mode") or BenchmarkMode.RUNTIME_ROUTE.value) for item in attempts})
        if any(mode != BenchmarkMode.RUNTIME_ROUTE.value for mode in attempt_modes):
            raise RuntimeError(
                "BenchmarkScoringPipeline is runtime_route-only; mixed or non-runtime lanes must be processed separately: "
                f"{attempt_modes}"
            )
        case_set_ids = sorted({str(item["case_set_id"]) for item in attempts})
        if len(case_set_ids) != 1:
            raise RuntimeError(f"expected exactly one case set per scored run, got {case_set_ids}")
        case_set = self.repo.fetch_benchmark_case_set(case_set_ids[0])
        if case_set is None:
            raise RuntimeError(f"missing benchmark case set {case_set_ids[0]}")

        scored_attempts: list[dict[str, Any]] = []
        sample_control_delta: dict[str, Any] | None = None

        for attempt in attempts:
            case = self.repo.fetch_benchmark_case(str(attempt["case_id"]))
            validator_suite = self.repo.fetch_validator_suite(str(attempt["validator_suite_id"]))
            if case is None or validator_suite is None:
                raise RuntimeError(f"missing case or validator suite for attempt {attempt['case_attempt_id']}")
            validator_rows = self.repo.list_validator_results(str(attempt["case_attempt_id"]))
            bundle_artifacts = self._bundle_artifacts(attempt)
            contract_gate = evaluate_contract_gate(attempt, validator_rows, validator_suite)
            task_score = score_attempt(
                case=case,
                attempt=attempt,
                contract_gate=contract_gate,
                task_eval=bundle_artifacts["task_eval"],
                route_trace=bundle_artifacts["route_trace"],
                validator_results=validator_rows,
                executor_links=bundle_artifacts["executor_links"],
            )
            metrics = normalize_operational_metrics(
                attempt=attempt,
                route_trace=bundle_artifacts["route_trace"],
                task_eval=bundle_artifacts["task_eval"],
                contract_gate=contract_gate,
            )
            updated_attempt = replace(
                BenchmarkCaseAttempt(**attempt),
                contract_gate_pass=contract_gate.contract_gate_pass,
                contract_gate_strength=contract_gate.contract_gate_strength,
                contract_fail_reason=contract_gate.contract_fail_reason,
                first_pass_valid=contract_gate.first_pass_valid,
                structural_failure_classification=contract_gate.structural_failure_classification,
                task_success_score=task_score.task_success_score,
                task_score_breakdown=task_score.task_score_breakdown,
                scoring_policy_id=task_score.scoring_policy_id,
                scoring_policy_version=task_score.scoring_policy_version,
                operational_metrics=metrics,
                source_ref="m3_scoring_pipeline",
            )
            self.repo.insert_benchmark_case_attempt(updated_attempt)
            scored_payload = self.repo.fetch_attempt(updated_attempt.case_attempt_id)
            assert scored_payload is not None
            scored_attempts.append(scored_payload)

            anchor_attempt = self._anchor_attempt(scored_payload, prior_run_id, current_candidates=scored_attempts)
            if anchor_attempt is None:
                continue
            delta_outcome = compute_control_deltas(scored_payload, anchor_attempt)
            for row in delta_outcome.rows:
                self.repo.insert_control_delta(row)
            if sample_control_delta is None and delta_outcome.rows:
                sample_control_delta = delta_outcome.rows[0].to_dict()

        case_set_rollup = build_case_set_rollup(benchmark_run_id, case_set, scored_attempts)
        archetype_rollups = build_archetype_rollups(benchmark_run_id, scored_attempts)
        profile_fit_rows = build_profile_fit_rows(
            benchmark_run_id=benchmark_run_id,
            profiles=self.repo.list_profiles(),
            attempts=scored_attempts,
        )
        portfolio_view = build_portfolio_view(benchmark_run_id, profile_fit_rows, archetype_rollups)

        prior_case_set_rollup: dict[str, Any] | None = None
        if prior_run_id is not None:
            prior_attempts = self.repo.list_attempts(prior_run_id)
            prior_case_set_rollup = build_case_set_rollup(prior_run_id, case_set, prior_attempts)
        regression_comparison = build_regression_comparison(case_set_rollup, prior_case_set_rollup)

        paths = run_paths(benchmark_run_id, self.root)
        _write_json(paths.rollups_dir / f"CASESET_ROLLUP__{case_set['case_set_id']}.json", case_set_rollup)
        for archetype_rollup in archetype_rollups:
            _write_json(
                paths.rollups_dir / f"ARCHETYPE_ROLLUP__{archetype_rollup['archetype_id']}.json",
                archetype_rollup,
            )
        for profile_fit in profile_fit_rows:
            _write_json(paths.rollups_dir / f"PROFILE_FIT__{profile_fit['profile_id']}.json", profile_fit)
        _write_json(paths.rollups_dir / "PORTFOLIO_VIEW.json", portfolio_view)
        _write_json(
            paths.rollups_dir / f"REGRESSION_COMPARISON__{case_set['case_set_id']}.json",
            regression_comparison,
        )

        return {
            "benchmark_run_id": benchmark_run_id,
            "scored_attempt_ids": [attempt["case_attempt_id"] for attempt in scored_attempts],
            "case_set_rollup": case_set_rollup,
            "archetype_rollups": archetype_rollups,
            "profile_fit_rows": profile_fit_rows,
            "portfolio_view": portfolio_view,
            "regression_comparison": regression_comparison,
            "sample_attempt": scored_attempts[0] if scored_attempts else {},
            "sample_control_delta": sample_control_delta or {},
        }
