from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _v5_smoke_helpers import load_runner_module
from benchmarking.direct_model.spend import SpendGuard
from benchmarking.pricing.coverage import build_pricing_coverage_report
from lib.proof_contract import build_conformance_report
from lib.risk_dashboard import build_rte_risk_dashboard, collect_rte_risk_dashboard_inputs
from lib.spend_ledger import SpendLedger


def _no_provider_call(*_args: Any, **_kwargs: Any) -> Any:
    raise AssertionError("artifact compatibility tests must not invoke provider clients")


def _openrouter_xai_route(runner: Any) -> dict[str, Any]:
    return runner.build_static_route_fingerprint_metadata(
        provider="openrouter",
        model_id="x-ai/grok-fixture",
        api_key_env="OPENROUTER_API_KEY",
        endpoint_base_url="https://openrouter.ai/api/v1",
        endpoint_url="https://openrouter.ai/api/v1/chat/completions",
        transport="openai_sdk",
        structured_output_mode="json_schema",
    )


def _direct_xai_route(runner: Any) -> dict[str, Any]:
    return runner.build_static_route_fingerprint_metadata(
        provider="xai",
        model_id="grok-fixture",
        api_key_env="XAI_API_KEY",
        endpoint_base_url="https://api.x.ai/v1",
        endpoint_url="https://api.x.ai/v1/chat/completions",
        transport="openai_sdk",
        structured_output_mode="json_schema",
    )


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_enriched_request_meta_preserves_route_and_pricing_fields() -> None:
    runner = load_runner_module()
    meta = runner.enrich_request_meta(
        {
            "provider": "openrouter",
            "model_id": "x-ai/grok-fixture",
            "api_key_env_resolved": "OPENROUTER_API_KEY",
            "endpoint_base_url": "https://openrouter.ai/api/v1",
            "endpoint_effective": "https://openrouter.ai/api/v1/chat/completions",
            "transport": "openai_sdk",
            "response_summary": {"returned_model_id": "grok-returned-fixture"},
            "structured_output": {"structured_output_mode_effective": "json_schema"},
        },
        run_id="compat-static",
        phase="A",
        step_id="A1",
        partition_id="A_P0001",
        provider="openrouter",
        model_id="x-ai/grok-fixture",
    )

    assert meta["provider"] == "openrouter"
    assert meta["model_id"] == "x-ai/grok-fixture"
    assert meta["requested_provider"] == "openrouter"
    assert meta["requested_model_id"] == "x-ai/grok-fixture"
    assert meta["provider_route_kind"] == "openrouter_proxy_xai"
    assert meta["upstream_provider"] == "xai"
    assert meta["economic_surface"] == "openrouter"
    assert meta["pricing_surface"] == "openrouter"
    assert meta["pricing_authority"] == "openrouter_catalog_or_unknown"
    assert meta["direct_provider_billing_inherited"] is False
    assert meta["live_validation_status"] == "LIVE_VALIDATION_REQUIRED"
    assert meta["pricing_live_validation_status"] == "LIVE_VALIDATION_REQUIRED"
    assert meta["returned_model_id"] == "grok-returned-fixture"

    material = runner.static_route_fingerprint_material(meta)
    assert material["economic_surface"] == "openrouter"
    assert "returned_model_id" not in material
    assert meta["route_fingerprint_hash"] == runner.static_route_fingerprint_hash(material)


def test_status_proof_dashboard_consumers_accept_enriched_artifacts(tmp_path: Path) -> None:
    runner = load_runner_module()
    run_root = tmp_path / "run"
    route = _openrouter_xai_route(runner)

    dashboard = runner.write_run_dashboard_snapshot(
        run_root,
        payload={
            "summary": {"PASS": 1, "FAIL": 0, "IN_PROGRESS": 0, "NOT_STARTED": 0},
            "phases": {"A": {"status": "PASS", "route_metadata": route}},
        },
        source="compat_fixture",
    )
    saved_dashboard = json.loads(
        (run_root / "telemetry" / "RUN_DASHBOARD.json").read_text(encoding="utf-8")
    )
    assert dashboard["payload"]["phases"]["A"]["route_metadata"]["pricing_surface"] == "openrouter"
    assert saved_dashboard["payload"]["phases"]["A"]["route_metadata"]["upstream_provider"] == "xai"
    assert saved_dashboard["payload"]["phases"]["A"]["route_metadata"][
        "direct_provider_billing_inherited"
    ] is False

    failure_index = runner.write_failure_index_snapshot(
        run_root,
        phase="A",
        step_id="A1",
        failure_histogram={"provider": 1},
        first_failure={
            "partition_id": "A_P0001",
            "failure_class": "provider",
            "request_meta": route,
        },
    )
    assert failure_index["steps"]["A:A1"]["first_failure"]["request_meta"][
        "pricing_surface"
    ] == "openrouter"

    for relative, payload in {
        "PROOF_PACK.json": {
            "run_id": "compat-static",
            "git_sha": "abc123",
            "runner_sha256": "runner-digest",
            "argv": ["run_extraction_v5.py", "--phase", "A", "--dry-run"],
            "cwd": "/repo",
            "updated_at": "2026-05-15T00:00:00Z",
            "phases": {"A": {"counts": {"raw": 1}}},
            "linked_artifacts": {"run_routing_fingerprint": "/repo/RUN_ROUTING_FINGERPRINT.json"},
            "route_metadata_fixture": route,
        },
        "COVERAGE_ROLLUP.json": {"status": "PASS", "route_metadata_fixture": route},
        "RESUME_PROOF.json": {"status": "PASS"},
        "PRELIVE_VALIDATOR_RESULT.json": {"status": "PASS"},
        "RUN_MANIFEST.json": {
            "generated_at": "2026-05-15T00:00:00Z",
            "routing_step_tiers": {"A": {"A1": "bulk"}},
            "effective_model_routing": {"A": route},
        },
        "telemetry/STEP_METRICS.json": {"steps": {}},
    }.items():
        _write_json(run_root / relative, payload)

    certification = runner.write_certification_result(run_root)
    assert certification["gates"]["artifact_contract_stability"]["status"] == "PASS"
    assert certification["gates"]["canonical_runner_correctness"]["status"] == "PASS"
    assert certification["gates"]["live_provider_readiness"]["status"] == "UNKNOWN"
    assert certification["proof_pack"]["run_status"] is None


def test_proof_contract_and_risk_dashboard_accept_additive_fields(tmp_path: Path) -> None:
    runner = load_runner_module()
    run_root = tmp_path / "run"
    route = _openrouter_xai_route(runner)
    proof_pack = {
        "run_id": "compat-static",
        "git_sha": "abc123",
        "runner_sha256": "runner-digest",
        "argv": ["run_extraction_v5.py", "--phase", "A", "--dry-run"],
        "cwd": "/repo",
        "updated_at": "2026-05-15T00:00:00Z",
        "phases": {"A": {"counts": {"raw": 1}}},
        "linked_artifacts": {
            "coverage_rollup": "/repo/COVERAGE_ROLLUP.json",
            "run_routing_fingerprint": "/repo/RUN_ROUTING_FINGERPRINT.json",
        },
        "route_metadata_fixture": route,
    }
    _write_json(run_root / "PROOF_PACK.json", proof_pack)
    _write_json(run_root / "RUN_MANIFEST.json", {"effective_model_routing": {"A": route}})

    report = build_conformance_report(
        proof_pack,
        artifact_path="services/repo-truth-extractor/extraction/repo-truth-extractor/v5/runs/run/PROOF_PACK.json",
    )
    assert report["overall_status"] == "PARTIAL"
    assert report["artifact"]["classification"] == "runtime_generated_evidence"
    assert report["fields"]["generated_artifact_list"]["status"] in {
        "SATISFIED",
        "PARTIAL",
    }

    inputs = collect_rte_risk_dashboard_inputs(
        run_id="compat-static",
        run_root=run_root,
        repo_root=Path.cwd(),
        git_sha="abc123",
        run_dashboard={"payload": {"phases": {"A": {"route_metadata": route}}}},
    )
    dashboard = build_rte_risk_dashboard(inputs)

    assert inputs["run_dashboard"]["payload"]["phases"]["A"]["route_metadata"][
        "pricing_surface"
    ] == "openrouter"
    assert dashboard["provider_call_status"] == "LIVE_VALIDATION_REQUIRED"
    assert dashboard["live_validation_status"] == "BLOCKED"
    assert "PASS1_IDENTITY: exact Pass 1 artifact identity is UNKNOWN" in dashboard["unknowns"]


def test_pricing_and_spend_consumers_preserve_openrouter_xai_authority(
    tmp_path: Path,
) -> None:
    report = build_pricing_coverage_report(
        universe=("openrouter/x-ai/grok-4.1-fast", "xai/grok-4.20")
    )
    rows = {row["model_key"]: row for row in report["rows"]}

    assert rows["openrouter/x-ai/grok-4.1-fast"]["upstream_provider"] == "xai"
    assert rows["openrouter/x-ai/grok-4.1-fast"]["economic_surface"] == "openrouter"
    assert rows["openrouter/x-ai/grok-4.1-fast"]["pricing_surface"] == "openrouter"
    assert rows["openrouter/x-ai/grok-4.1-fast"][
        "direct_provider_billing_inherited"
    ] is False
    assert rows["xai/grok-4.20"]["economic_surface"] == "xai_direct"
    assert rows["xai/grok-4.20"]["pricing_surface"] == "xai_direct"

    guard = SpendGuard()
    openrouter_estimate = guard.estimate(
        provider="openrouter",
        model_id="x-ai/grok-4.1-fast",
        input_tokens=100,
        output_tokens=50,
    )
    direct_xai_estimate = guard.estimate(
        provider="xai",
        model_id="grok-4.20",
        input_tokens=100,
        output_tokens=50,
    )
    assert openrouter_estimate.upstream_provider == "xai"
    assert openrouter_estimate.pricing_surface == "openrouter"
    assert openrouter_estimate.direct_provider_billing_inherited is False
    assert direct_xai_estimate.pricing_surface == "xai_direct"

    _write_json(
        tmp_path / "spend_ledger.json",
        {
            "run_id": "compat-static",
            "pricing_version": "baseline_v1",
            "total_cost_usd": 0.001,
            "unknown_model_events": 0,
            "fallback_usage_count": 0,
            "providers": {"openrouter": {"usage_count": 1}},
            "phases": {
                "A": {
                    "models": {
                        "openrouter/x-ai/grok-4.1-fast": {
                            "provider": "openrouter",
                            "model_id": "x-ai/grok-4.1-fast",
                            "pricing_key": "openrouter/x-ai/grok-4.1-fast",
                            "pricing_source": "fixture",
                            "upstream_provider": "xai",
                            "economic_surface": "openrouter",
                            "pricing_surface": "openrouter",
                            "direct_provider_billing_inherited": False,
                            "additive_future_field": "ignored_by_loader",
                        }
                    },
                    "providers": {"openrouter": {"usage_count": 1}},
                }
            },
            "models": {
                "openrouter/x-ai/grok-4.1-fast": {
                    "provider": "openrouter",
                    "model_id": "x-ai/grok-4.1-fast",
                    "pricing_key": "openrouter/x-ai/grok-4.1-fast",
                    "pricing_source": "fixture",
                    "upstream_provider": "xai",
                    "economic_surface": "openrouter",
                    "pricing_surface": "openrouter",
                    "direct_provider_billing_inherited": False,
                    "additive_future_field": "ignored_by_loader",
                }
            },
        },
    )
    ledger = SpendLedger(tmp_path, "compat-static")
    loaded = ledger.record.models["openrouter/x-ai/grok-4.1-fast"]
    assert loaded.upstream_provider == "xai"
    assert loaded.economic_surface == "openrouter"
    assert loaded.pricing_surface == "openrouter"
    assert loaded.direct_provider_billing_inherited is False


def test_static_artifact_compatibility_paths_do_not_call_provider_clients(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    runner = load_runner_module()
    for attr in (
        "get_http_session",
        "get_gemini_client",
        "get_xai_client",
        "get_openrouter_client",
        "get_openai_client",
        "llm_runtime_call_llm",
        "llm_runtime_call_llm_with_ladder",
        "run_provider_preflight",
    ):
        if hasattr(runner, attr):
            monkeypatch.setattr(runner, attr, _no_provider_call, raising=False)

    openrouter_route = _openrouter_xai_route(runner)
    direct_route = _direct_xai_route(runner)
    runner.write_run_dashboard_snapshot(
        tmp_path,
        payload={"phases": {"A": {"openrouter": openrouter_route, "direct": direct_route}}},
        source="compat_no_provider",
    )
    report = build_pricing_coverage_report(
        universe=("openrouter/x-ai/grok-4.1-fast", "xai/grok-4.20")
    )

    assert openrouter_route["pricing_surface"] == "openrouter"
    assert direct_route["pricing_surface"] == "xai_direct"
    assert report["active_benchmark_universe_size"] == 2
