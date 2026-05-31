from __future__ import annotations

import subprocess
import sys
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.campaigns.selection import ensure_r1_campaign_records
from benchmarking.cli.benchmark_registry_smoke import run_registry_smoke
from benchmarking.registry.registry_loader import seed_registry
from benchmarking.storage.sqlite_repo import BenchmarkCatalogRepo


def test_case_set_registry_links_cases_snapshot_and_control_anchor(tmp_path: Path) -> None:
    repo = BenchmarkCatalogRepo.from_root(tmp_path)
    bundle = seed_registry(repo)

    starter = repo.fetch_benchmark_case_set("benchmark_registry_starter_v1")
    assert starter is not None
    assert len(starter["case_ids"]) == 6
    assert starter["control_anchor_group_id"] == "anchor_openai_general_v1"

    anchor = repo.fetch_control_anchor_group(starter["control_anchor_group_id"])
    assert anchor is not None
    assert anchor["route_ids"] == ["route_openai_gpt_5_4_v1"]
    assert anchor["candidate_route_ids"] == []

    for case_id in starter["case_ids"]:
        case = repo.fetch_benchmark_case(case_id)
        assert case is not None
        assert case["contract_snapshot_id"] == bundle.contract_snapshot.contract_snapshot_id
        assert repo.fetch_validator_suite(case["validator_suite_id"]) is not None


def test_registry_seeds_gemini_strict_candidates_unverified(tmp_path: Path) -> None:
    # Gemini attestation routes and surface follow the r1-campaign-seed pattern
    # (matching surface_gemini_api_v1): seeded by ensure_r1_campaign_records, not
    # seed_registry. seed_registry alone must NOT contain them to avoid INSERT OR
    # REPLACE collisions with different source_ref values.
    repo = BenchmarkCatalogRepo.from_root(tmp_path)

    # Confirm seed_registry does NOT include the gemini direct surface or routes.
    seed_registry(repo)
    assert repo.fetch_provider_surface("surface_gemini_direct_api_v1") is None
    assert repo.fetch_route("route_gemini_direct_gemini_3_1_pro_preview_v1") is None
    assert repo.fetch_route("route_openrouter_gemini_3_1_pro_preview_v1") is None

    # After ensure_r1_campaign_records, the surface and routes are present.
    ensure_r1_campaign_records(repo)

    direct_surface = repo.fetch_provider_surface("surface_gemini_direct_api_v1")
    assert direct_surface is not None
    assert direct_surface["provider_name"] == "gemini"
    assert direct_surface["surface_class"] == "direct_provider_api"

    direct = repo.fetch_route("route_gemini_direct_gemini_3_1_pro_preview_v1")
    assert direct is not None
    assert direct["surface_id"] == "surface_gemini_direct_api_v1"
    assert direct["model_key"] == "gemini/gemini-3.1-pro-preview"
    assert direct["provider_model_id"] == "gemini-3.1-pro-preview"
    assert direct["api_key_ref"] == "GEMINI_API_KEY"
    assert direct["strict_json_schema_declared"] is True
    assert direct["strict_passthrough_verified"] is False

    routed = repo.fetch_route("route_openrouter_gemini_3_1_pro_preview_v1")
    assert routed is not None
    assert routed["surface_id"] == "surface_openrouter_api_v1"
    assert routed["model_key"] == "google/gemini-3.1-pro-preview"
    assert routed["provider_model_id"] == "google/gemini-3.1-pro-preview"
    assert routed["api_key_ref"] == "OPENROUTER_API_KEY"
    assert routed["strict_json_schema_declared"] is True
    assert routed["strict_passthrough_verified"] is False


def test_registry_smoke_cli_exits_successfully_and_proves_linkage(tmp_path: Path) -> None:
    cli_path = SERVICE_ROOT / "benchmarking" / "cli" / "benchmark_registry_smoke.py"
    result = subprocess.run(
        [
            sys.executable,
            str(cli_path),
            "--benchmark-root",
            str(tmp_path / "benchmarks"),
            "--proof-dir",
            str(tmp_path / "proof"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "\"contract_snapshot_id\"" in result.stdout
    report = run_registry_smoke(root=tmp_path / "benchmarks-second")
    assert len(report["case_ids"]) == 6
    assert report["db_row_counts"]["benchmark_case_set"] == 2
