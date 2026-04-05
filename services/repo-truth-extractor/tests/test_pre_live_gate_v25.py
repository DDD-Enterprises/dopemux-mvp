from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


def _load_gate_module():
    root = Path(__file__).resolve().parents[3]
    module_path = root / "services" / "repo-truth-extractor" / "validate_pre_live_gate_v25.py"
    spec = importlib.util.spec_from_file_location("validate_pre_live_gate_v25", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_default_policy_requires_direct_gemini_and_xai() -> None:
    gate = _load_gate_module()
    assert gate.DEFAULT_TARGET_POLICY == "balanced_openrouter"
    assert gate.resolve_required_direct_providers("balanced_openrouter", None) == ("gemini", "xai")


def test_truth_split_prefers_specific_classification() -> None:
    gate = _load_gate_module()
    assert (
        gate.classify_truth_split_row(
            step_id="A11",
            runner_active=True,
            prompt_resolution_active=False,
            promptset_declared=True,
            model_map_declared=True,
            artifact_declarations_present=True,
        )
        == "STALE_RUNNER_REGISTRY"
    )
    assert (
        gate.classify_truth_split_row(
            step_id="Q11",
            runner_active=False,
            prompt_resolution_active=False,
            promptset_declared=True,
            model_map_declared=True,
            artifact_declarations_present=True,
        )
        == "STALE_PROMPTSET"
    )
    assert (
        gate.classify_truth_split_row(
            step_id="D1",
            runner_active=True,
            prompt_resolution_active=True,
            promptset_declared=True,
            model_map_declared=True,
            artifact_declarations_present=False,
        )
        == "STALE_ARTIFACT_MAP"
    )


def test_pal_validation_missing_for_active_route_is_condition(tmp_path: Path) -> None:
    gate = _load_gate_module()
    config = gate.GateConfig(
        repo_root=Path("/tmp/repo"),
        output_dir=tmp_path,
        run_id="test_gate",
        target_policy="balanced_openrouter",
        target_mode="direct",
        target_profile="P00_GENERIC",
        target_phases=("D",),
        allow_online_preflight=False,
        pal_validation_file=None,
        waiver_codes=(),
        required_direct_providers=("gemini", "xai"),
    )
    scope = {
        "required_provider_routes": [
            {
                "route_signature": "xai:grok-4-1-fast-reasoning:XAI_API_KEY",
                "provider": "xai",
                "model_id": "grok-4-1-fast-reasoning",
                "api_key_env": "XAI_API_KEY",
                "active_route_required": True,
                "fallback_chain_present": False,
            }
        ]
    }
    payload, blockers, conditions = gate.evaluate_pal_validation(config, scope)
    assert payload["status"] == "WARN"
    assert blockers == []
    assert [condition.reason_code for condition in conditions] == [gate.PAL_REQUIRED_UNAVAILABLE]


def test_run_gate_stays_offline_without_explicit_online_preflight(monkeypatch, tmp_path: Path) -> None:
    gate = _load_gate_module()

    fake_scope = {
        "validation_started_at": "2026-03-12T00:00:00+00:00",
        "git_sha": "abc123",
        "validator_host": "host",
        "validator_python": "3.11.0",
        "target_policy": "balanced_openrouter",
        "target_mode": "direct",
        "target_profile": "P00_GENERIC",
        "target_phases": ["A"],
        "target_runner_path": "/tmp/run_extraction_v5.py",
        "target_runner_sha256": "runner",
        "promptset_sha256": "promptset",
        "artifacts_sha256": "artifacts",
        "model_map_sha256": "modelmap",
        "required_provider_routes": [
            {
                "route_signature": "gemini:gemini-2.5-pro:GEMINI_API_KEY",
                "provider": "gemini",
                "model_id": "gemini-2.5-pro",
                "api_key_env": "GEMINI_API_KEY",
                "active_route_required": True,
                "fallback_chain_present": True,
                "steps": [{"phase": "A", "step_id": "A0"}],
            },
            {
                "route_signature": "xai:grok-code-fast-1:XAI_API_KEY",
                "provider": "xai",
                "model_id": "grok-code-fast-1",
                "api_key_env": "XAI_API_KEY",
                "active_route_required": True,
                "fallback_chain_present": False,
                "steps": [{"phase": "A", "step_id": "A0"}],
            },
        ],
        "required_api_key_envs": ["GEMINI_API_KEY", "XAI_API_KEY"],
        "routing_fingerprint_sha256": "routing",
        "phase_contract_map_sha256": "contract",
    }

    class FakeRunner:
        PHASES = ["A"]
        REQUIRED_PROMPT_STEP_IDS = {"A": {"A0"}}

        def get_phase_prompts(self, phase):
            return []

    monkeypatch.setattr(gate, "load_module", lambda path, name: FakeRunner() if "run_extraction" in str(path) else type("FakeContract", (), {"compile_phase_contract_map": lambda self=None: {"steps": {}}, "write_phase_contract_map": lambda self, root, run_id: root / "PHASE_CONTRACT_MAP.json"})())
    monkeypatch.setattr(gate, "derive_scope", lambda runner, contract_module, config: fake_scope)
    monkeypatch.setattr(gate, "evaluate_import_cli_smoke", lambda config: ({"status": "PASS"}, []))
    monkeypatch.setattr(gate, "evaluate_prompt_integrity", lambda runner, config: ({"status": "PASS"}, []))
    monkeypatch.setattr(gate, "collect_truth_split", lambda runner, config: ({"layer": "truth_split_audit", "status": "PASS", "rows": [], "target_phase_mismatch_count": 0, "repo_wide_mismatch_count": 0}, [], []))
    monkeypatch.setattr(gate, "evaluate_contract_map", lambda runner, contract_module, config: ({"status": "PASS"}, []))
    monkeypatch.setattr(gate, "evaluate_route_readiness", lambda runner, config, scope: ({"status": "PASS"}, []))
    monkeypatch.setattr(gate, "evaluate_pytest_layer", lambda **kwargs: ({"status": "PASS"}, [], []))
    monkeypatch.setattr(
        gate,
        "evaluate_pal_validation",
        lambda config, scope: (
            {
                "layer": "pal_provider_validation",
                "status": "PASS",
                "routes": [
                    {
                        "route_signature": "gemini:gemini-2.5-pro:GEMINI_API_KEY",
                        "provider": "gemini",
                        "source_type": "api_docs",
                        "source_locator": "https://ai.google.dev/gemini-api/docs",
                        "validation_timestamp": "2026-03-12T00:00:00+00:00",
                        "auth_mode_repo": "auto",
                        "auth_mode_official": "api_key",
                        "transport_repo": "sdk",
                        "transport_official": "sdk",
                        "endpoint_repo": "https://generativelanguage.googleapis.com",
                        "endpoint_official": "https://generativelanguage.googleapis.com",
                        "model_id_repo": "gemini-2.5-pro",
                        "model_reference_mode": "exact_model_documented",
                        "model_reference_official": "gemini-2.5-pro",
                        "active_route_required": True,
                        "fallback_chain_present": True,
                        "compatibility_status": "compatible",
                        "mismatch_class": "",
                        "notes": "",
                    }
                ],
                "conditions": [],
            },
            [],
            [],
        ),
    )
    monkeypatch.setattr(gate, "evaluate_smoke_tests", lambda config: ({"status": "FAIL"}, [gate.Blocker(gate.MISSING_SMOKE_EVIDENCE, "smoke_and_verify_evidence", "P0", "missing smoke")]))

    config = gate.GateConfig(
        repo_root=Path("/tmp/repo"),
        output_dir=tmp_path,
        run_id="offline_gate",
        target_policy="balanced_openrouter",
        target_mode="direct",
        target_profile="P00_GENERIC",
        target_phases=("A",),
        allow_online_preflight=False,
        pal_validation_file=None,
        waiver_codes=(),
        required_direct_providers=("gemini", "xai"),
    )
    result = gate.run_gate(config)
    assert result["verdict"]["verdict"] == "NO_GO"
    assert gate.ONLINE_PREFLIGHT_FAILURE not in result["verdict"]["reason_codes"]
    assert gate.ONLINE_PREFLIGHT_FAILURE in {
        row["reason_code"] for row in result["verdict"]["conditions"]
    }
    verdict_path = tmp_path / "VALIDATION_VERDICT.json"
    payload = json.loads(verdict_path.read_text(encoding="utf-8"))
    assert payload["verdict"] == "NO_GO"


def test_bounded_route_readiness_does_not_fail_on_global_provider_expectation() -> None:
    gate = _load_gate_module()
    config = gate.GateConfig(
        repo_root=Path("/tmp/repo"),
        output_dir=Path("/tmp/out"),
        run_id="bounded_scope",
        target_policy="balanced_openrouter",
        target_mode="direct",
        target_profile="P00_GENERIC",
        target_phases=("A",),
        allow_online_preflight=True,
        pal_validation_file=None,
        waiver_codes=(),
        required_direct_providers=("gemini", "xai"),
    )
    scope = {
        "required_provider_routes": [
            {
                "route_signature": "openrouter:openai/gpt-5.3-codex:OPENROUTER_API_KEY",
                "provider": "openrouter",
                "model_id": "openai/gpt-5.3-codex",
                "api_key_env": "OPENROUTER_API_KEY",
                "active_route_required": True,
                "fallback_chain_present": True,
            },
            {
                "route_signature": "xai:grok-4.20-beta-0309-reasoning:XAI_API_KEY",
                "provider": "xai",
                "model_id": "grok-4.20-beta-0309-reasoning",
                "api_key_env": "XAI_API_KEY",
                "active_route_required": True,
                "fallback_chain_present": True,
            },
        ],
        "required_api_key_envs": [],
    }

    payload, blockers = gate.evaluate_route_readiness(runner=None, config=config, scope=scope)

    assert payload["bounded_target_scope"] is True
    assert payload["missing_required_direct_providers"] == ["gemini"]
    assert blockers == []


def test_operator_verdict_prefers_environment_before_external() -> None:
    gate = _load_gate_module()
    blockers = [
        {
            "reason_code": gate.REQUIRED_API_KEY_MISSING,
            "layer": "route_derived_readiness",
            "severity": "P0",
            "message": "missing env",
            "details": {"missing_api_key_envs": ["XAI_API_KEY"]},
        },
        {
            "reason_code": gate.ONLINE_PREFLIGHT_FAILURE,
            "layer": "online_provider_preflight",
            "severity": "P0",
            "message": "preflight failed",
            "details": {
                "probes": [
                    {
                        "provider": "openrouter",
                        "api_key_present": True,
                        "failure_type": "auth_rejected",
                        "status_code": 401,
                    }
                ]
            },
        },
    ]

    operator_verdict, classification = gate.derive_operator_verdict(
        blockers,
        conditions=[],
        repo_wide_findings=[],
    )

    assert operator_verdict == gate.NO_GO_ENV
    assert len(classification["environment_blockers"]) == 1
    assert len(classification["external_provider_blockers"]) == 1


def test_run_gate_returns_conditional_go_when_only_conditions(monkeypatch, tmp_path: Path) -> None:
    gate = _load_gate_module()

    fake_scope = {
        "validation_started_at": "2026-03-12T00:00:00+00:00",
        "git_sha": "abc123",
        "validator_host": "host",
        "validator_python": "3.11.0",
        "target_policy": "balanced_openrouter",
        "target_mode": "direct",
        "target_profile": "P00_GENERIC",
        "target_phases": ["A"],
        "target_runner_path": "/tmp/run_extraction_v5.py",
        "target_runner_sha256": "runner",
        "promptset_sha256": "promptset",
        "artifacts_sha256": "artifacts",
        "model_map_sha256": "modelmap",
        "required_provider_routes": [],
        "required_api_key_envs": [],
        "routing_fingerprint_sha256": "routing",
        "phase_contract_map_sha256": "contract",
    }

    class FakeRunner:
        PHASES = ["A"]
        REQUIRED_PROMPT_STEP_IDS = {"A": {"A0"}}

        def get_phase_prompts(self, phase):
            return []

    monkeypatch.setattr(gate, "load_module", lambda path, name: FakeRunner() if "run_extraction" in str(path) else type("FakeContract", (), {"compile_phase_contract_map": lambda self=None: {"steps": {}}, "write_phase_contract_map": lambda self, root, run_id: root / "PHASE_CONTRACT_MAP.json"})())
    monkeypatch.setattr(gate, "derive_scope", lambda runner, contract_module, config: fake_scope)
    monkeypatch.setattr(gate, "evaluate_import_cli_smoke", lambda config: ({"status": "PASS"}, []))
    monkeypatch.setattr(gate, "evaluate_prompt_integrity", lambda runner, config: ({"status": "PASS"}, []))
    monkeypatch.setattr(gate, "collect_truth_split", lambda runner, config: ({"layer": "truth_split_audit", "status": "PASS", "rows": [], "target_phase_mismatch_count": 0, "repo_wide_mismatch_count": 0}, [], []))
    monkeypatch.setattr(gate, "evaluate_contract_map", lambda runner, contract_module, config: ({"status": "PASS"}, []))
    monkeypatch.setattr(gate, "evaluate_route_readiness", lambda runner, config, scope: ({"status": "PASS"}, []))
    monkeypatch.setattr(gate, "evaluate_pytest_layer", lambda **kwargs: ({"status": "PASS"}, [], []))
    monkeypatch.setattr(
        gate,
        "evaluate_pal_validation",
        lambda config, scope: (
            {"layer": "pal_provider_validation", "status": "WARN", "routes": [], "conditions": [{"reason_code": gate.PAL_REQUIRED_UNAVAILABLE, "layer": "pal_provider_validation", "message": "missing pal", "details": {}}]},
            [],
            [gate.GateCondition(gate.PAL_REQUIRED_UNAVAILABLE, "pal_provider_validation", "missing pal", {})],
        ),
    )
    monkeypatch.setattr(
        gate,
        "evaluate_online_preflight",
        lambda runner, config: (
            {"layer": "online_provider_preflight", "status": "WARN", "allow_online_preflight": False, "payload": None, "conditions": [{"reason_code": gate.ONLINE_PREFLIGHT_FAILURE, "layer": "online_provider_preflight", "message": "skipped", "details": {"allow_online_preflight": False}}]},
            [],
            [gate.GateCondition(gate.ONLINE_PREFLIGHT_FAILURE, "online_provider_preflight", "skipped", {"allow_online_preflight": False})],
        ),
    )
    monkeypatch.setattr(gate, "evaluate_smoke_tests", lambda config: ({"status": "PASS"}, []))

    config = gate.GateConfig(
        repo_root=Path("/tmp/repo"),
        output_dir=tmp_path,
        run_id="conditional_gate",
        target_policy="balanced_openrouter",
        target_mode="direct",
        target_profile="P00_GENERIC",
        target_phases=("A",),
        allow_online_preflight=False,
        pal_validation_file=None,
        waiver_codes=(),
        required_direct_providers=("gemini", "xai"),
    )
    result = gate.run_gate(config)

    assert result["verdict"]["verdict"] == "CONDITIONAL_GO"
    assert result["verdict"]["operator_verdict"] == gate.GO_NOW
    assert {row["reason_code"] for row in result["verdict"]["conditions"]} == {
        gate.ONLINE_PREFLIGHT_FAILURE,
        gate.PAL_REQUIRED_UNAVAILABLE,
    }
