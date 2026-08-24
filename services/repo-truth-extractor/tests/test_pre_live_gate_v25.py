from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace


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


def test_collect_truth_split_reports_target_row_match(tmp_path: Path) -> None:
    gate = _load_gate_module()

    class FakeRunner:
        def get_phase_prompts(self, phase):
            assert phase == "A"
            return [
                SimpleNamespace(
                    step_id="A0",
                    output_artifacts=("INSTRUCTION_SURFACES.json",),
                    source="legacy",
                    contract={"expected_artifacts": ["INSTRUCTION_SURFACES.json"]},
                )
            ]

    config = gate.GateConfig(
        repo_root=Path("/tmp/repo"),
        output_dir=tmp_path,
        run_id="truth_split_match",
        target_policy="cost",
        target_mode="direct",
        target_profile="P00_GENERIC",
        target_phases=("A",),
        target_step="A0",
    )
    payload, blockers, findings = gate.collect_truth_split(FakeRunner(), config)
    assert payload["status"] == "PASS"
    assert blockers == []
    assert findings == []
    assert payload["target_phase_mismatch_count"] == 0
    assert payload["rows"] == [
        {
            "phase": "A",
            "target_phase": "A",
            "step_id": "A0",
            "runner_active": True,
            "prompt_resolution_active": True,
            "promptset_declared": True,
            "model_map_declared": True,
            "artifact_declarations_present": True,
            "contract_present": True,
            "prompt_source": "legacy",
            "classification": "MATCH",
        }
    ]


def test_collect_truth_split_blocks_selected_sp_without_contract(tmp_path: Path) -> None:
    gate = _load_gate_module()

    class FakeRunner:
        def get_phase_prompts(self, phase):
            assert phase == "S"
            return [
                SimpleNamespace(
                    step_id="SP4",
                    output_artifacts=("SP4_TRUTH_PACK_INDEX.json",),
                    source="registry",
                    contract=None,
                )
            ]

    config = gate.GateConfig(
        repo_root=Path("/tmp/repo"),
        output_dir=tmp_path,
        run_id="truth_split_sp_missing_contract",
        target_policy="cost",
        target_mode="direct",
        target_profile="P00_GENERIC",
        target_phases=("S",),
        target_step="SP4",
        s_prompts_mode="registry",
    )
    payload, blockers, findings = gate.collect_truth_split(FakeRunner(), config)
    assert payload["status"] == "FAIL"
    assert payload["target_phase_mismatch_count"] == 1
    assert payload["repo_wide_mismatch_count"] == 0
    assert findings == []
    assert payload["rows"][0]["phase"] == "SP"
    assert payload["rows"][0]["target_phase"] == "S"
    assert payload["rows"][0]["step_id"] == "SP4"
    assert payload["rows"][0]["prompt_source"] == "registry"
    assert payload["rows"][0]["contract_present"] is False
    assert payload["rows"][0]["classification"] == "STALE_MODEL_MAP"
    assert [(blocker.reason_code, blocker.severity) for blocker in blockers] == [
        (gate.SP_CONTRACT_MISSING, "P0")
    ]


def test_run_gate_applies_s_prompts_mode_before_scope_derivation(
    monkeypatch, tmp_path: Path
) -> None:
    gate = _load_gate_module()
    observed = {}

    class FakeRunner:
        def set_active_s_prompts_mode(self, mode):
            observed["set_mode"] = mode

    class FakeContract:
        def compile_phase_contract_map(self):
            return {"steps": {}}

    fake_scope = {
        "validation_started_at": "2026-03-12T00:00:00+00:00",
        "git_sha": "abc123abc123abc123abc123abc123abc123abcd",
        "validator_host": "host",
        "validator_python": "3.11.0",
        "target_policy": "cost",
        "target_mode": "direct",
        "target_profile": "P00_GENERIC",
        "target_phases": ["S"],
        "target_step": "SP4",
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

    def fake_derive_scope(runner, contract_module, config):
        observed["scope_mode"] = observed.get("set_mode")
        return dict(fake_scope)

    monkeypatch.setattr(
        gate,
        "load_module",
        lambda path, name: FakeRunner()
        if "run_extraction" in str(path)
        else FakeContract(),
    )
    monkeypatch.setattr(gate, "derive_scope", fake_derive_scope)
    monkeypatch.setattr(gate, "evaluate_import_cli_smoke", lambda config: ({"status": "PASS"}, []))
    monkeypatch.setattr(gate, "evaluate_prompt_integrity", lambda runner, config: ({"status": "PASS"}, []))
    monkeypatch.setattr(gate, "collect_truth_split", lambda runner, config: ({"layer": "truth_split_audit", "status": "PASS", "rows": [], "target_phase_mismatch_count": 0, "repo_wide_mismatch_count": 0}, [], []))
    monkeypatch.setattr(gate, "evaluate_contract_map", lambda runner, contract_module, config: ({"status": "PASS"}, []))
    monkeypatch.setattr(gate, "evaluate_route_readiness", lambda runner, config, scope: ({"status": "PASS"}, []))
    monkeypatch.setattr(gate, "evaluate_pytest_layer", lambda **kwargs: ({"status": "PASS"}, [], []))
    monkeypatch.setattr(gate, "evaluate_pal_validation", lambda config, scope: ({"layer": "pal_provider_validation", "status": "PASS", "routes": []}, [], []))
    monkeypatch.setattr(gate, "evaluate_online_preflight", lambda runner, config: ({"layer": "online_provider_preflight", "status": "PASS"}, [], []))
    monkeypatch.setattr(gate, "evaluate_smoke_tests", lambda config: ({"status": "PASS"}, []))

    config = gate.GateConfig(
        repo_root=Path("/tmp/repo"),
        output_dir=tmp_path,
        run_id="registry_mode_gate",
        target_policy="cost",
        target_mode="direct",
        target_profile="P00_GENERIC",
        target_phases=("S",),
        target_step="SP4",
        s_prompts_mode="registry",
    )
    result = gate.run_gate(config)

    assert result["verdict"]["verdict"] == "GO"
    assert observed == {"set_mode": "registry", "scope_mode": "registry"}


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
        "git_sha": "abc123abc123abc123abc123abc123abc123abcd",
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
        "git_sha": "abc123abc123abc123abc123abc123abc123abcd",
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
        allow_conditional=True,
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
    assert result["verdict"]["operator_verdict"] == gate.GO_NOW
    assert result["verdict"]["environment_summary"] == {
        "tooling_status": "CONDITIONAL_GO",
        "live_online_status": "environment_blocked_or_unverified",
        "message": (
            "Repo and tooling checks can pass while live online readiness remains blocked "
            "or unverified by current provider credentials, PAL evidence, or online preflight."
        ),
    }


def test_run_gate_defaults_to_no_go_when_conditions_are_not_opted_in(
    monkeypatch, tmp_path: Path
) -> None:
    """TP-RTE-TRUTH-R2-004 / F-13b: an un-opted skip of PAL/online-preflight
    must be a hard NO_GO, not the old default CONDITIONAL_GO. This is the
    same fixture as test_run_gate_returns_conditional_go_when_only_conditions_remain
    but WITHOUT --allow-conditional (the GateConfig default), proving the
    gate's weakest posture is no longer its default posture."""
    gate = _load_gate_module()

    fake_scope = {
        "validation_started_at": "2026-03-12T00:00:00+00:00",
        "git_sha": "0123456789abcdef0123456789abcdef01234567",
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
        run_id="conditional_gate_not_allowed",
        target_policy="cost",
        target_mode="direct",
        target_profile="P00_GENERIC",
        target_phases=("A",),
        allow_online_preflight=False,
        # allow_conditional intentionally omitted -- must default to False.
        pal_validation_file=None,
        waiver_codes=(),
        required_direct_providers=(),
    )
    assert config.allow_conditional is False
    result = gate.run_gate(config)
    assert result["verdict"]["verdict"] == "NO_GO"
    assert result["verdict"]["reason_codes"] == []
    assert sorted(row["reason_code"] for row in result["verdict"]["conditions"]) == [
        gate.ONLINE_PREFLIGHT_FAILURE,
        gate.PAL_REQUIRED_UNAVAILABLE,
    ]
    assert result["verdict"]["operator_verdict"] == gate.NO_GO_CONDITIONAL_NOT_ALLOWED
    verdict_path = tmp_path / "VALIDATION_VERDICT.json"
    payload = json.loads(verdict_path.read_text(encoding="utf-8"))
    assert payload["verdict"] == "NO_GO"


def test_allow_conditional_cli_flag_defaults_false_and_wires_through_config() -> None:
    """--allow-conditional must default to False and build_config must
    thread it into GateConfig.allow_conditional (no silent drop)."""
    gate = _load_gate_module()
    parser = gate.build_arg_parser()

    default_args = parser.parse_args(["--target-phases", "A"])
    assert default_args.allow_conditional is False
    default_config = gate.build_config(default_args)
    assert default_config.allow_conditional is False

    opted_args = parser.parse_args(["--target-phases", "A", "--allow-conditional"])
    assert opted_args.allow_conditional is True
    opted_config = gate.build_config(opted_args)
    assert opted_config.allow_conditional is True


def test_derive_operator_verdict_no_go_conditional_not_allowed_when_unopted() -> None:
    """Unit-level proof for derive_operator_verdict's new branch: no
    blockers, but Conditions remain and allow_conditional=False -> the
    operator-facing verdict must be NO_GO_CONDITIONAL_NOT_ALLOWED, not the
    old GO_NOW fallthrough."""
    gate = _load_gate_module()
    conditions = [
        {
            "reason_code": gate.PAL_REQUIRED_UNAVAILABLE,
            "layer": "pal_provider_validation",
            "message": "PAL skipped",
            "details": {},
        }
    ]
    verdict, classification = gate.derive_operator_verdict(
        [], conditions, [], allow_conditional=False
    )
    assert verdict == gate.NO_GO_CONDITIONAL_NOT_ALLOWED

    verdict_allowed, _ = gate.derive_operator_verdict(
        [], conditions, [], allow_conditional=True
    )
    assert verdict_allowed == gate.GO_NOW


def test_collect_truth_split_fails_for_stale_drift_step(tmp_path: Path) -> None:
    gate = _load_gate_module()

    class FakeRunner:
        def get_phase_prompts(self, phase):
            assert phase == "A"
            return [
                SimpleNamespace(
                    step_id="FAKE_STALE_STEP",
                    output_artifacts=("FAKE.json",),
                    source="legacy",
                    contract={"expected_artifacts": ["FAKE.json"]},
                )
            ]

    config = gate.GateConfig(
        repo_root=Path("/tmp/repo"),
        output_dir=tmp_path,
        run_id="truth_split_stale_drift",
        target_policy="cost",
        target_mode="direct",
        target_profile="P00_GENERIC",
        target_phases=("A",),
        target_step="FAKE_STALE_STEP",
    )
    payload, blockers, findings = gate.collect_truth_split(FakeRunner(), config)
    assert payload["status"] == "FAIL"
    assert any(b.reason_code == gate.TARGET_TRUTH_SPLIT_MISMATCH for b in blockers)
    assert payload["rows"][0]["classification"] == "STALE_MODEL_MAP"
    assert payload["target_phase_mismatch_count"] >= 1


def test_build_config_default_output_dir_is_outside_repo_tree() -> None:
    """F-06: an operator who never passes --output-dir must not get a report
    directory inside the repo worktree. This exercises the real call site
    (build_arg_parser -> build_config), not just the DEFAULT_OUTPUT_ROOT
    constant, so it catches regressions in how the default is wired in."""
    gate = _load_gate_module()

    parser = gate.build_arg_parser()
    args = parser.parse_args(["--run-id", "f06_default_dir_probe"])
    assert args.output_dir is None  # confirm we are exercising the default path

    config = gate.build_config(args)

    repo_root = gate.REPO_ROOT.resolve()
    resolved_output_dir = config.output_dir.resolve()
    assert resolved_output_dir != repo_root
    assert repo_root not in resolved_output_dir.parents, (
        f"default output_dir {resolved_output_dir} lands inside repo tree {repo_root}"
    )
    assert resolved_output_dir == (gate.DEFAULT_OUTPUT_ROOT / "f06_default_dir_probe").resolve()


def test_build_config_honors_explicit_output_dir_even_inside_repo() -> None:
    """Explicit --output-dir must always be honored verbatim (packet invariant:
    'Honor explicit --output-dir everywhere; only the DEFAULT moves out of the
    worktree.')."""
    gate = _load_gate_module()

    parser = gate.build_arg_parser()
    explicit_dir = gate.REPO_ROOT / "reports" / "repo-truth-extractor" / "pre_live_gate_v25" / "explicit_probe"
    args = parser.parse_args(["--run-id", "explicit_probe", "--output-dir", str(explicit_dir)])

    config = gate.build_config(args)

    assert config.output_dir == explicit_dir.resolve()
