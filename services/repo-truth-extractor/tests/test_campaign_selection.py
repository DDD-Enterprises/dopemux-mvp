from __future__ import annotations

import sys
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.campaigns.manifest import build_campaign_manifest
from benchmarking.campaigns.selection import build_r1_campaign_plan
from benchmarking.cli.benchmark_route_admissibility_smoke import _admissibility_intended_routes
from benchmarking.orchestration.attempt_executor import _step_route_signature
from benchmarking.registry.registry_loader import seed_registry
from benchmarking.storage.sqlite_repo import BenchmarkCatalogRepo


def test_r1_campaign_selection_is_bounded_and_explicit(tmp_path: Path) -> None:
    repo = BenchmarkCatalogRepo.from_root(tmp_path)
    seed_registry(repo)
    plan = build_r1_campaign_plan(repo)
    manifest = build_campaign_manifest(plan)

    cohorts = [item["cohort"] for item in manifest["campaign_candidates"]]
    assert cohorts.count("control") == 2
    assert cohorts.count("premium") == 2
    assert cohorts.count("balanced") == 2
    assert cohorts.count("experimental") == 1
    assert len(manifest["campaign_candidates"]) == 7

    route_ids = {item["route_id"] for item in manifest["campaign_candidates"]}
    assert "route_openrouter_openai_gpt_5_4_v1" in route_ids
    assert "route_openai_gpt_5_4_v1" in route_ids
    assert "route_local_fixture_v1" in route_ids
    assert "route_openrouter_openai_gpt_5_3_codex_v1" in route_ids
    assert "route_openai_gpt_5_4_mini_v1" in route_ids
    assert "route_gemini_direct_gemini_3_1_pro_preview_v1" in route_ids
    assert "route_openrouter_gemini_3_1_pro_preview_v1" in route_ids
    assert manifest["case_set_id"] == "r1_first_campaign_v1"
    assert manifest["contract_snapshot_id"]


def test_step_route_signature_is_stable() -> None:
    left = _step_route_signature(
        {
            "step_route_counts": {
                "A:A2": ["xai/grok-4.20-beta-0309-reasoning"],
                "A:A0": ["openrouter/openai/gpt-5.3-codex"],
            }
        }
    )
    right = _step_route_signature(
        {
            "step_route_counts": {
                "A:A0": ["openrouter/openai/gpt-5.3-codex"],
                "A:A2": ["xai/grok-4.20-beta-0309-reasoning"],
            }
        }
    )
    different = _step_route_signature(
        {
            "step_route_counts": {
                "A:A0": ["openrouter/openai/gpt-5.3-codex"],
                "A:A2": ["openai/gpt-5.4"],
            }
        }
    )
    assert left == right
    assert left != different


def test_route_admissibility_only_gates_live_campaign_assignments(tmp_path: Path) -> None:
    repo = BenchmarkCatalogRepo.from_root(tmp_path)
    seed_registry(repo)
    plan = build_r1_campaign_plan(repo)
    manifest = build_campaign_manifest(plan)

    intended_routes = _admissibility_intended_routes(manifest)

    assert intended_routes
    assert all(item["case_id"] == "strict_extract_conflicting_evidence_v1" for item in intended_routes)
    assert {item["route_id"] for item in intended_routes} == {
        "route_openrouter_openai_gpt_5_4_v1",
        "route_openai_gpt_5_4_v1",
        "route_openrouter_openai_gpt_5_3_codex_v1",
        "route_openai_gpt_5_4_mini_v1",
        "route_gemini_direct_gemini_3_1_pro_preview_v1",
        "route_openrouter_gemini_3_1_pro_preview_v1",
    }
