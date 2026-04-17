from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_runner_module() -> types.ModuleType:
    module_path = _repo_root() / "services" / "repo-truth-extractor" / "run_extraction_v5.py"
    spec = importlib.util.spec_from_file_location("run_extraction_v5_live_cert_char", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_current_rte_certification_status_payload_is_split_gate_baseline() -> None:
    payload = _load_json(_repo_root() / "reports" / "rte-production-certification-status.json")

    assert payload["artifact_version"] == "RTE_PRODUCTION_CERTIFICATION_STATUS_V2"
    assert payload["branch"] == "tp/rte-live-cert-artifact-contract-hardening"
    assert payload["final_verdict"] == "NOT_VERIFIED"
    assert payload["gates"] == {
        "artifact_contract_stability": {
            "status": "PASS",
            "summary": "Split-gate certification writer regression passes and the core RTE artifact contracts remain characterization-locked.",
        },
        "canonical_runner_correctness": {
            "status": "PASS",
            "summary": "run_extraction_v5 remains the canonical runner and the baseline runner surface plus certification writer are regression-locked.",
        },
        "live_provider_readiness": {
            "status": "PASS",
            "summary": "Doctor probes succeeded against Gemini, OpenAI, OpenRouter, and XAI with the repo's current keys.",
        },
        "operator_topology_resilience": {
            "status": "UNKNOWN",
            "summary": "No degraded-topology smoke matrix was exercised in this packet, so the topology gate stays explicit UNKNOWN.",
        },
    }
    assert payload["non_critical_unknowns"] == [
        "External non-repo consumers of the certification artifact remain unknown.",
        "Topology resilience beyond the doctor probe has not been exercised for degraded service matrices.",
        "A future packet may still need to tighten live-provider evidence across additional provider-family combinations.",
    ]


def test_rte_artifact_inventory_and_preflight_entry_points_are_explicit() -> None:
    runner = _load_runner_module()

    for symbol in [
        "run_pre_live_validator",
        "run_provider_preflight",
        "prepare_phase_provider_preflight",
        "phase_requires_provider_preflight",
        "write_confidence_ramp_artifacts",
        "write_certification_result",
        "write_coverage_rollup",
        "write_resume_proof",
    ]:
        assert hasattr(runner, symbol), symbol

    inventory = {
        "PROOF_PACK.json": [
            "services/repo-truth-extractor/reporting.py",
            "services/repo-truth-extractor/run_extraction_v5.py",
            "services/repo-truth-extractor/tests/test_v5_golden_fixture_smoke.py",
            "services/repo-truth-extractor/tests/test_rte_v5_characterization.py",
        ],
        "COVERAGE_ROLLUP.json": [
            "services/repo-truth-extractor/reporting.py",
            "services/repo-truth-extractor/run_extraction_v5.py",
            "services/repo-truth-extractor/tests/test_run_extraction_v5_rollup_reports.py",
            "services/repo-truth-extractor/tests/test_v5_golden_fixture_smoke.py",
        ],
        "RUN_DASHBOARD.json": [
            "services/repo-truth-extractor/reporting.py",
            "services/repo-truth-extractor/tests/test_run_extraction_v5_rollup_reports.py",
        ],
        "STEP_METRICS.json": [
            "services/repo-truth-extractor/reporting.py",
            "services/repo-truth-extractor/tests/test_run_extraction_v5_rollup_reports.py",
        ],
        "FAILURE_INDEX.json": [
            "services/repo-truth-extractor/reporting.py",
            "services/repo-truth-extractor/tests/test_run_extraction_v5_rollup_reports.py",
        ],
    }

    for artifact_name, reader_paths in inventory.items():
        resolved_paths = []
        for rel_path in reader_paths:
            path = _repo_root() / rel_path
            assert path.exists(), f"missing inventory path for {artifact_name}: {rel_path}"
            resolved_paths.append(path)
        assert any(artifact_name in path.read_text(encoding="utf-8") for path in resolved_paths), (
            f"expected at least one reader for {artifact_name} to reference the filename directly"
        )


def test_write_certification_result_rolls_up_split_gates_from_evidence(tmp_path: Path) -> None:
    runner = _load_runner_module()
    run_root = tmp_path / "runs" / "split_cert_probe"
    telemetry_root = run_root / "telemetry"
    telemetry_root.mkdir(parents=True, exist_ok=True)

    for relative in [
        "PROOF_PACK.json",
        "COVERAGE_ROLLUP.json",
        "RESUME_PROOF.json",
        "PRELIVE_VALIDATOR_RESULT.json",
        "telemetry/RUN_DASHBOARD.json",
        "telemetry/STEP_METRICS.json",
        "telemetry/FAILURE_INDEX.json",
    ]:
        path = run_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if relative == "PRELIVE_VALIDATOR_RESULT.json":
            path.write_text(json.dumps({"status": "PASS"}), encoding="utf-8")
        else:
            path.write_text("{}", encoding="utf-8")

    topology_payload = {
        "required_artifact_groups": {"required_groups_present_pct": 100.0},
        "provider_reachability": {
            "probes": [
                {"status_code": 200, "ready": True},
                {"status_code": 200, "ready": True},
            ]
        },
    }

    result = runner.write_certification_result(run_root, topology_payload=topology_payload)
    saved = json.loads((run_root / "CERTIFICATION_RESULT.json").read_text(encoding="utf-8"))

    assert result == saved
    assert result["overall_status"] == "VERIFIED"
    assert {gate["status"] for gate in result["gates"].values()} == {"PASS"}
    assert result["gates"]["canonical_runner_correctness"]["source"] == "PRELIVE_VALIDATOR_RESULT.json"
    assert result["gates"]["live_provider_readiness"]["status"] == "PASS"
    assert result["gates"]["artifact_contract_stability"]["status"] == "PASS"
    assert result["gates"]["operator_topology_resilience"]["status"] == "PASS"
