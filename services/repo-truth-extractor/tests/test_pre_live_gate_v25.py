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
    assert gate.DEFAULT_TARGET_POLICY == "cost"
    assert gate.resolve_required_direct_providers("cost", None) == ()


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


def test_collect_truth_split_fails_closed_until_implemented() -> None:
    # S7 (audit): the runner/promptset/model-map drift audit is unimplemented. It must
    # fail closed with a waivable P1 blocker, never a fake PASS.
    gate = _load_gate_module()
    payload, blockers, findings = gate.collect_truth_split(None, None)
    assert payload["status"] == "NOT_IMPLEMENTED"
    assert len(blockers) == 1
    assert blockers[0].reason_code == gate.TRUTH_SPLIT_NOT_IMPLEMENTED
    assert blockers[0].severity == "P1"
    assert findings == []


def test_pal_validation_is_conditional_when_missing_for_active_route(tmp_path: Path) -> None:
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
    assert payload["status"] == "SKIPPED"
    assert blockers == []
    assert any(condition.reason_code == gate.PAL_REQUIRED_UNAVAILABLE for condition in conditions)


def test_route_readiness_only_requires_active_route_api_keys(tmp_path: Path, monkeypatch) -> None:
    gate = _load_gate_module()
    config = gate.GateConfig(
        repo_root=Path("/tmp/repo"),
        output_dir=tmp_path,
        run_id="test_gate",
        target_policy="cost",
        target_mode="direct",
        target_profile="P00_GENERIC",
        target_phases=("A",),
        allow_online_preflight=False,
        pal_validation_file=None,
        waiver_codes=(),
        required_direct_providers=(),
    )
    scope = {
        "required_provider_routes": [
            {
                "route_signature": "xai:grok-code-fast-1:XAI_API_KEY",
                "provider": "xai",
                "model_id": "grok-code-fast-1",
                "api_key_env": "XAI_API_KEY",
                "active_route_required": True,
                "optional_fallback": False,
                "configured_not_required": False,
                "fallback_chain_present": True,
            },
            {
                "route_signature": "openrouter:openai/gpt-5-mini:OPENROUTER_API_KEY",
                "provider": "openrouter",
                "model_id": "openai/gpt-5-mini",
                "api_key_env": "OPENROUTER_API_KEY",
                "active_route_required": False,
                "optional_fallback": True,
                "configured_not_required": False,
                "fallback_chain_present": False,
            },
        ],
        "required_api_key_envs": ["XAI_API_KEY"],
        "fallback_api_key_envs": ["OPENROUTER_API_KEY"],
        "configured_not_required_api_key_envs": ["OPENAI_API_KEY"],
        "route_readiness_summary": {
            "api_key_env_categories": {
                "required_active_route": ["XAI_API_KEY"],
                "optional_fallback": ["OPENROUTER_API_KEY"],
                "configured_not_required": ["OPENAI_API_KEY"],
            },
            "provider_categories": {
                "required_active_route": ["xai"],
                "optional_fallback": ["openrouter"],
                "configured_not_required": ["openai"],
            },
        },
    }
    monkeypatch.setenv("XAI_API_KEY", "present")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    payload, blockers = gate.evaluate_route_readiness(None, config, scope)
    assert payload["status"] == "PASS"
    assert payload["missing_api_key_envs"] == []
    assert payload["missing_fallback_api_key_envs"] == ["OPENROUTER_API_KEY"]
    assert payload["configured_not_required_api_key_envs"] == ["OPENAI_API_KEY"]
    assert payload["api_key_env_categories"]["required_active_route"] == ["XAI_API_KEY"]
    assert blockers == []


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
        "routing_fingerprint_hash": "routing",
        "phase_contract_map_hash": "contract",
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
            },
            [],
            [gate.Condition(gate.PAL_REQUIRED_UNAVAILABLE, "pal_provider_validation", "PAL skipped")],
        ),
    )
    monkeypatch.setattr(
        gate,
        "evaluate_online_preflight",
        lambda runner, config: (
            {
                "layer": "online_provider_preflight",
                "status": "SKIPPED",
                "allow_online_preflight": False,
                "payload": None,
            },
            [],
            [gate.Condition(gate.ONLINE_PREFLIGHT_FAILURE, "online_provider_preflight", "preflight skipped")],
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
    assert gate.PAL_REQUIRED_UNAVAILABLE not in result["verdict"]["reason_codes"]
    verdict_path = tmp_path / "VALIDATION_VERDICT.json"
    payload = json.loads(verdict_path.read_text(encoding="utf-8"))
    assert payload["verdict"] == "NO_GO"


def test_run_gate_returns_conditional_go_when_only_conditions_remain(monkeypatch, tmp_path: Path) -> None:
    gate = _load_gate_module()

    fake_scope = {
        "validation_started_at": "2026-03-12T00:00:00+00:00",
        "git_sha": "abc123",
        "validator_host": "host",
        "validator_python": "3.11.0",
        "target_policy": "cost",
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
        "fallback_api_key_envs": [],
        "all_route_api_key_envs": [],
        "routing_fingerprint_hash": "routing",
        "phase_contract_map_hash": "contract",
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
            {"layer": "pal_provider_validation", "status": "SKIPPED", "routes": []},
            [],
            [gate.Condition(gate.PAL_REQUIRED_UNAVAILABLE, "pal_provider_validation", "PAL skipped")],
        ),
    )
    monkeypatch.setattr(
        gate,
        "evaluate_online_preflight",
        lambda runner, config: (
            {"layer": "online_provider_preflight", "status": "SKIPPED", "allow_online_preflight": False, "payload": None},
            [],
            [gate.Condition(gate.ONLINE_PREFLIGHT_FAILURE, "online_provider_preflight", "preflight skipped")],
        ),
    )
    monkeypatch.setattr(gate, "evaluate_smoke_tests", lambda config: ({"status": "PASS"}, []))

    config = gate.GateConfig(
        repo_root=Path("/tmp/repo"),
        output_dir=tmp_path,
        run_id="conditional_gate",
        target_policy="cost",
        target_mode="direct",
        target_profile="P00_GENERIC",
        target_phases=("A",),
        allow_online_preflight=False,
        pal_validation_file=None,
        waiver_codes=(),
        required_direct_providers=(),
    )
    result = gate.run_gate(config)
    assert result["verdict"]["verdict"] == "CONDITIONAL_GO"
    assert result["verdict"]["reason_codes"] == []
    assert sorted(row["reason_code"] for row in result["verdict"]["conditions"]) == [
        gate.ONLINE_PREFLIGHT_FAILURE,
        gate.PAL_REQUIRED_UNAVAILABLE,
    ]
    assert result["verdict"]["environment_summary"] == {
        "tooling_status": "CONDITIONAL_GO",
        "live_online_status": "environment_blocked_or_unverified",
        "message": (
            "Repo and tooling checks can pass while live online readiness remains blocked "
            "or unverified by current provider credentials, PAL evidence, or online preflight."
        ),
    }
