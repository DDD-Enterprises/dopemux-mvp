from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from ..models.entities import BenchmarkCaseAttempt
from ..storage.hashing import stable_json_dumps
from ..storage.sqlite_repo import BenchmarkCatalogRepo


FULL_STARTER_CASE_IDS = [
    "prescan_route_inventory_v1",
    "strict_extract_conflicting_evidence_v1",
    "repair_merge_conflict_normalization_v1",
    "adjudication_conflict_ruling_v1",
    "fl_int_output_shaping_v1",
    "tool_aware_repo_reasoning_v1",
]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(stable_json_dumps(payload) + "\n", encoding="utf-8")


def _attempt_map(repo: BenchmarkCatalogRepo, benchmark_run_id: str) -> dict[str, dict[str, Any]]:
    return {str(item["case_id"]): item for item in repo.list_attempts(benchmark_run_id)}


def apply_hardening_run_overrides(root: Path | None, benchmark_run_id: str) -> dict[str, str]:
    repo = BenchmarkCatalogRepo.from_root(root)
    attempts = _attempt_map(repo, benchmark_run_id)

    repair_attempt = attempts["repair_merge_conflict_normalization_v1"]
    repaired = replace(
        BenchmarkCaseAttempt(**repair_attempt),
        timestamp_utc="2026-03-01T00:00:00Z",
        unknowns_open=["phase_s_contract_requires_manual_review"],
        source_ref="s1_hardening_fixture",
    )
    repo.insert_benchmark_case_attempt(repaired)

    tool_aware_attempt = attempts["tool_aware_repo_reasoning_v1"]
    blocked = replace(
        BenchmarkCaseAttempt(**tool_aware_attempt),
        profile_id="governance_pending_review",
        retry_policy_id="retry_anchor_mismatch_v1",
        source_ref="s1_hardening_fixture",
    )
    repo.insert_benchmark_case_attempt(blocked)

    return {
        "stale_disputed_case_attempt_id": repaired.case_attempt_id,
        "blocked_governance_case_attempt_id": blocked.case_attempt_id,
    }


def apply_regression_degradation(
    root: Path | None,
    benchmark_run_id: str,
    case_id: str = "strict_extract_conflicting_evidence_v1",
) -> str:
    repo = BenchmarkCatalogRepo.from_root(root)
    attempts = _attempt_map(repo, benchmark_run_id)
    attempt = attempts[case_id]
    bundle = repo.fetch_bundle(str(attempt["evidence_bundle_id"]))
    if bundle is None:
        raise RuntimeError(f"missing bundle for {attempt['case_attempt_id']}")
    bundle_root = Path(str(bundle["root_path"]))
    executor_links = _load_json(bundle_root / "EXECUTOR_LINKS.json")
    executor_links.pop("script", None)
    executor_links["fixture_note"] = "S1 regression fixture removes script provenance to lower artifact completeness."
    _write_json(bundle_root / "EXECUTOR_LINKS.json", executor_links)
    return str(attempt["case_attempt_id"])
