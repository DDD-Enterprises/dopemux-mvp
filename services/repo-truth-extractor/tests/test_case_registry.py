from __future__ import annotations

import sys
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.registry.registry_loader import seed_registry
from benchmarking.storage.sqlite_repo import BenchmarkCatalogRepo


def test_case_registry_seed_persists_and_loads_cases(tmp_path: Path) -> None:
    repo = BenchmarkCatalogRepo.from_root(tmp_path)
    bundle = seed_registry(repo)

    cases = repo.list_benchmark_cases()
    case_ids = [case["case_id"] for case in cases]

    assert len(cases) == 6
    assert "prescan_route_inventory_v1" in case_ids
    assert "strict_extract_conflicting_evidence_v1" in case_ids
    assert "tool_aware_repo_reasoning_v1" in case_ids

    strict_case = repo.fetch_benchmark_case("strict_extract_conflicting_evidence_v1")
    assert strict_case is not None
    assert strict_case["contract_snapshot_id"] == bundle.contract_snapshot.contract_snapshot_id
    assert strict_case["validator_suite_id"] == "validators_runtime_strict_json_v1"
    assert strict_case["surface_scope"] == ["openrouter_routed"]
    assert strict_case["benchmark_mode"] == "runtime_route"
    assert strict_case["candidate_type"] == "route_candidate"
    assert strict_case["execution_family"] == "runtime_integrated_execution"
    assert strict_case["route_distinctness_required"] is True
