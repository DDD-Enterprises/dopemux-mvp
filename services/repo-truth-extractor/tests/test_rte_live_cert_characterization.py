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
    assert result["overall_status"] == "UNKNOWN"
    assert result["gates"]["canonical_runner_correctness"]["source"] == "PRELIVE_VALIDATOR_RESULT.json"
    assert result["gates"]["canonical_runner_correctness"]["status"] == "PASS"
    assert result["gates"]["live_provider_readiness"]["status"] == "UNKNOWN"
    assert result["gates"]["artifact_contract_stability"]["status"] == "PASS"
    assert result["gates"]["operator_topology_resilience"]["status"] == "UNKNOWN"
    assert result["gates"]["live_provider_readiness"]["evidence"]["topology_probes_observed"] == [
        {"status_code": 200, "ready": True},
        {"status_code": 200, "ready": True},
    ]
    assert result["gates"]["operator_topology_resilience"]["evidence"][
        "required_artifact_groups"
    ] == {"required_groups_present_pct": 100.0}


def test_write_certification_result_requires_explicit_provider_and_topology_status(tmp_path: Path) -> None:
    runner = _load_runner_module()
    run_root = tmp_path / "runs" / "strict_cert_probe"
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

    result = runner.write_certification_result(
        run_root,
        provider_preflight_payload={
            "status": "PASS",
            "phase_scope": ["A", "H", "D", "C"],
            "step_scope": {},
            "scope_kind": "launch",
            "scope_complete_for_launch": True,
        },
        topology_payload={
            "status": "PASS",
            "required_artifact_groups": {"required_groups_present_pct": 100.0},
            "provider_reachability": {
                "probes": [{"status_code": 200, "ready": True}],
            },
        },
    )

    assert result["overall_status"] == "VERIFIED"
    assert {gate["status"] for gate in result["gates"].values()} == {"PASS"}
    assert result["gates"]["live_provider_readiness"]["status"] == "PASS"
    assert result["gates"]["live_provider_readiness"]["source"] == "run-scoped full-launch provider preflight"
    assert result["gates"]["operator_topology_resilience"]["status"] == "PASS"


def test_write_certification_result_rejects_partial_scope_provider_preflight(tmp_path: Path) -> None:
    runner = _load_runner_module()
    run_root = tmp_path / "runs" / "partial_scope_probe"
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

    (run_root / "RUN_MANIFEST.json").write_text(
        json.dumps(
            {
                "generated_at": "2026-04-17T08:00:00+00:00",
                "routing_step_tiers": {"A": {}, "H": {}, "D": {}, "C": {}},
            }
        ),
        encoding="utf-8",
    )
    (run_root / "PROVIDER_PREFLIGHT.json").write_text(
        json.dumps(
            {
                "generated_at": "2026-04-17T08:01:00+00:00",
                "status": "PASS",
                "phase_scope": ["D"],
                "step_scope": {},
                "scope_kind": "phase",
                "scope_complete_for_launch": False,
            }
        ),
        encoding="utf-8",
    )

    result = runner.write_certification_result(run_root)

    assert result["gates"]["live_provider_readiness"]["status"] == "UNKNOWN"
    assert result["gates"]["live_provider_readiness"]["source"] == "provider preflight payload incomplete for launch"
    assert result["gates"]["live_provider_readiness"]["evidence"]["provider_preflight_scope"]["reason"] == "scope_not_marked_launch_complete"


def test_write_certification_result_rejects_provider_preflight_missing_scope_metadata(tmp_path: Path) -> None:
    runner = _load_runner_module()
    run_root = tmp_path / "runs" / "missing_scope_probe"
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

    (run_root / "PROVIDER_PREFLIGHT.json").write_text(
        json.dumps({"generated_at": "2026-04-17T08:01:00+00:00", "status": "PASS"}),
        encoding="utf-8",
    )

    result = runner.write_certification_result(run_root)

    assert result["gates"]["live_provider_readiness"]["status"] == "UNKNOWN"
    assert result["gates"]["live_provider_readiness"]["evidence"]["provider_preflight_scope"]["reason"] == "scope_not_marked_launch_complete"


def test_write_certification_result_accepts_full_scope_provider_preflight(tmp_path: Path) -> None:
    runner = _load_runner_module()
    run_root = tmp_path / "runs" / "full_scope_probe"
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

    (run_root / "RUN_MANIFEST.json").write_text(
        json.dumps(
            {
                "generated_at": "2026-04-17T08:00:00+00:00",
                "routing_step_tiers": {"A": {}, "H": {}, "D": {}, "C": {}},
            }
        ),
        encoding="utf-8",
    )
    (run_root / "PROVIDER_PREFLIGHT.json").write_text(
        json.dumps(
            {
                "generated_at": "2026-04-17T08:01:00+00:00",
                "status": "PASS",
                "phase_scope": ["A", "H", "D", "C"],
                "step_scope": {},
                "scope_kind": "launch",
                "scope_complete_for_launch": True,
            }
        ),
        encoding="utf-8",
    )

    result = runner.write_certification_result(run_root)

    assert result["gates"]["live_provider_readiness"]["status"] == "PASS"
    assert result["gates"]["live_provider_readiness"]["evidence"]["provider_preflight_scope"]["reason"] == "launch_complete"


def test_write_certification_result_rejects_stale_run_local_preflight_after_manifest_refresh(tmp_path: Path) -> None:
    runner = _load_runner_module()
    run_root = tmp_path / "runs" / "stale_run_local_probe"
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

    (run_root / "RUN_MANIFEST.json").write_text(
        json.dumps(
            {
                "generated_at": "2026-04-17T09:00:00+00:00",
                "routing_step_tiers": {"A": {}, "H": {}, "D": {}, "C": {}},
            }
        ),
        encoding="utf-8",
    )
    (run_root / "PROVIDER_PREFLIGHT.json").write_text(
        json.dumps(
            {
                "generated_at": "2026-04-17T08:00:00+00:00",
                "status": "PASS",
                "phase_scope": ["A", "H", "D", "C"],
                "step_scope": {},
                "scope_kind": "launch",
                "scope_complete_for_launch": True,
            }
        ),
        encoding="utf-8",
    )

    result = runner.write_certification_result(run_root)

    assert result["gates"]["live_provider_readiness"]["status"] == "UNKNOWN"
    assert result["gates"]["live_provider_readiness"]["evidence"]["provider_preflight_scope"]["reason"] == "provider_preflight_older_than_run_manifest"


def test_write_certification_result_ignores_stale_shared_doctor_pass_files(tmp_path: Path) -> None:
    runner = _load_runner_module()
    run_root = tmp_path / "artifact-root" / "runs" / "stale_doctor_probe"
    telemetry_root = run_root / "telemetry"
    doctor_root = tmp_path / "artifact-root" / "doctor"
    telemetry_root.mkdir(parents=True, exist_ok=True)
    doctor_root.mkdir(parents=True, exist_ok=True)

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

    (doctor_root / "PROVIDER_PREFLIGHT.json").write_text(
        json.dumps({"status": "PASS", "run_id": "stale_run"}), encoding="utf-8"
    )
    (doctor_root / "DOCTOR_FULL.json").write_text(
        json.dumps({"status": "PASS", "run_id": "stale_run"}), encoding="utf-8"
    )

    result = runner.write_certification_result(run_root)

    assert result["overall_status"] == "UNKNOWN"
    assert result["gates"]["live_provider_readiness"]["status"] == "UNKNOWN"
    assert result["gates"]["operator_topology_resilience"]["status"] == "UNKNOWN"
    assert result["gates"]["live_provider_readiness"]["evidence"]["provider_preflight"] is None


def test_write_certification_result_does_not_promote_proof_pack_status_to_pass(tmp_path: Path) -> None:
    runner = _load_runner_module()
    run_root = tmp_path / "runs" / "proof_only_probe"
    telemetry_root = run_root / "telemetry"
    telemetry_root.mkdir(parents=True, exist_ok=True)

    for relative, payload in {
        "PROOF_PACK.json": {"run_status": "OK", "blocked_reason": None},
        "COVERAGE_ROLLUP.json": {},
        "RESUME_PROOF.json": {},
        "telemetry/RUN_DASHBOARD.json": {},
        "telemetry/STEP_METRICS.json": {},
        "telemetry/FAILURE_INDEX.json": {},
    }.items():
        path = run_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    result = runner.write_certification_result(run_root)

    assert result["gates"]["canonical_runner_correctness"]["status"] == "UNKNOWN"
    assert result["gates"]["canonical_runner_correctness"]["source"] == "run-scoped validator missing"
    assert result["gates"]["canonical_runner_correctness"]["evidence"]["proof_pack"]["run_status"] == "OK"


def test_run_doctor_full_certification_stays_unknown_without_explicit_gate_statuses(
    monkeypatch, tmp_path: Path
) -> None:
    runner = _load_runner_module()
    run_root = tmp_path / "artifact-root" / "runs" / "doctor_probe"
    doctor_root = tmp_path / "artifact-root" / "doctor"
    dirs = {"root": run_root}
    cfg = runner.RunnerConfig.__new__(runner.RunnerConfig)
    object.__setattr__(cfg, "routing_policy", "cost")

    doctor_root.mkdir(parents=True, exist_ok=True)
    (doctor_root / "PROVIDER_PREFLIGHT.json").write_text(
        json.dumps({"status": "PASS", "run_id": "stale_run"}), encoding="utf-8"
    )
    (doctor_root / "DOCTOR_FULL.json").write_text(
        json.dumps({"status": "PASS", "run_id": "stale_run"}), encoding="utf-8"
    )

    monkeypatch.setattr(runner, "collect_prompt_index", lambda: ({}, []))
    monkeypatch.setattr(runner, "get_phase_prompts", lambda phase: [])
    monkeypatch.setattr(
        runner,
        "get_required_artifact_status",
        lambda dirs_arg, phases: {"required_groups_present_pct": 100.0},
    )
    monkeypatch.setattr(
        runner,
        "collect_provider_routes",
        lambda **kwargs: {
            "A:A0": {
                "provider": "openrouter",
                "model_id": "openai/gpt-5.4",
                "api_key_env": "OPENROUTER_API_KEY",
            }
        },
    )
    monkeypatch.setattr(
        runner,
        "run_provider_doctor_probe",
        lambda **kwargs: {"provider": "openrouter", "status_code": 200, "ready": True},
    )
    monkeypatch.setattr(runner, "get_git_sha", lambda root: "deadbeef")

    exit_code = runner.run_doctor_full(
        tmp_path,
        dirs,
        run_id="doctor_probe",
        phases=["A"],
        cfg=cfg,
    )

    assert exit_code == 1
    certification = json.loads(
        (run_root / "CERTIFICATION_RESULT.json").read_text(encoding="utf-8")
    )
    assert certification["overall_status"] == "UNKNOWN"
    assert certification["gates"]["live_provider_readiness"]["status"] == "UNKNOWN"
    assert certification["gates"]["operator_topology_resilience"]["status"] == "UNKNOWN"
