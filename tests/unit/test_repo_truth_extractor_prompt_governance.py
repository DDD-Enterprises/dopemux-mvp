from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SERVICE_ROOT = REPO_ROOT / "services" / "repo-truth-extractor"
RUNNER_PATH = SERVICE_ROOT / "run_extraction_v5.py"
PHASE_S_ROOT = SERVICE_ROOT / "prompts" / "phase_s"
PRESCAN_ROOT = SERVICE_ROOT / "prompts" / "prescan"


def _load_runner_module():
    service_root = str(SERVICE_ROOT)
    if service_root in sys.path:
        sys.path.remove(service_root)
    sys.path.insert(0, service_root)

    for module_name, module in list(sys.modules.items()):
        if module_name != "extractor" and not module_name.startswith("extractor."):
            continue
        module_file = getattr(module, "__file__", None)
        if module_file is None or not Path(module_file).resolve().is_relative_to(SERVICE_ROOT):
            sys.modules.pop(module_name, None)

    spec = importlib.util.spec_from_file_location(
        "run_extraction_v5_prompt_governance", RUNNER_PATH
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_phase_sp_registry_uses_declared_routing_tiers() -> None:
    runner = _load_runner_module()

    specs = {spec.step_id: spec for spec in runner.get_phase_prompts("SP")}

    assert specs["SP0"].tier_override == "synthesis"
    assert specs["SP11"].tier_override == "qa"
    assert specs["SP12"].tier_override == "qa"


def test_phase_sp_supports_generic_single_step_filtering() -> None:
    runner = _load_runner_module()

    selected = runner._get_execution_step_filter(
        SimpleNamespace(step="SP7", phase="SP", s_steps=None)
    )

    assert selected == "SP7"
    cfg = runner.RunnerConfig(
        dry_run=True,
        max_files_docs=1,
        max_files_code=1,
        max_chars=1,
        max_request_bytes=1,
        file_truncate_chars=1,
        home_scan_mode="safe",
        resume=False,
        fail_fast_auth=True,
        gemini_auth_mode="auto",
        gemini_transport="sdk",
        openai_transport="openai_sdk",
        xai_transport="openai_sdk",
        retry_policy="none",
        retry_max_attempts=1,
        retry_base_seconds=0.0,
        retry_max_seconds=0.0,
        phase_auth_fail_threshold=1,
        partition_workers=1,
        debug_phase_inputs=False,
        fail_fast_missing_inputs=False,
        selected_execution_step=selected,
    )
    assert runner._selected_execution_step_ids_for_phase(cfg, "SP") == ["SP7"]


def test_phase_s_prompt_mode_tracks_explicit_selection() -> None:
    runner = _load_runner_module()

    runner.set_active_s_prompts_mode(None)
    assert runner.get_active_s_prompts_mode() == runner.S_PROMPTS_LEGACY

    runner.set_active_s_prompts_mode("auto")
    assert runner.get_active_s_prompts_mode() == "auto"

    runner.set_active_s_prompts_mode("registry")
    assert runner.get_active_s_prompts_mode() == "registry"


def test_post_review_preset_sequence_includes_sp_phase() -> None:
    runner = _load_runner_module()

    assert runner.first_live_phase_sequence("post-review") == [
        "R",
        "X",
        "T",
        "Z",
        "S",
        "SP",
    ]


def test_promptset_rules_injection_is_idempotent() -> None:
    runner = _load_runner_module()

    prompt = "# Test\n\n## Shared Rules\nRefer to PROMPTSET_RULES.md.\n"
    once = runner._inject_promptset_rules(prompt)
    twice = runner._inject_promptset_rules(once)

    assert "Evidence Rules" in once
    assert once == twice
    assert twice.count("## PROMPTSET_RULES.md (Injected)") == 1


def test_phase_sp_posttail_prompts_exist_and_match_contract() -> None:
    prompt_files = [
        "PROMPT_SP7_DEDUPE_SORT.md",
        "PROMPT_SP8_DRIFT_CHECK.md",
        "PROMPT_SP9_PROMOTION_READINESS.md",
        "PROMPT_SP10_REDACTION_PASS.md",
        "PROMPT_SP11_CONTRACT_LINTER.md",
        "PROMPT_SP12_STABILITY_SIGNATURE.md",
    ]

    for filename in prompt_files:
        path = PHASE_S_ROOT / filename
        assert path.exists(), f"Missing prompt file: {filename}"
        text = path.read_text(encoding="utf-8")
        assert "OUTPUTS:" in text
        assert "Output JSON only." in text
        assert ("FAIL_CLOSED" in text) or ("fail closed" in text.lower())
        assert "print the secret" not in text.lower()
        assert "sk-" not in text.lower()
        assert "api_key=" not in text.lower()


def test_registry_populations_exist_and_have_required_fields() -> None:
    registry_populations = {
        "SP": SERVICE_ROOT / "prompts" / "phase_s" / "registry.json",
        "FL_INT": SERVICE_ROOT / "prompts" / "phase_fl_int" / "registry.json",
        "S_INT": SERVICE_ROOT / "prompts" / "phase_s_int" / "registry.json",
    }
    required_step_fields = {"prompt_path", "outputs", "routing_tier", "max_hops"}

    for name, path in registry_populations.items():
        assert path.exists(), f"Registry missing: {name} at {path}"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert "steps" in data, f"Registry {name} missing 'steps' key"
        assert data["steps"], f"Registry {name} has no steps"
        base_dir = path.parent
        for step_id, step in data["steps"].items():
            for field in required_step_fields:
                assert field in step, f"{name}/{step_id} missing field: {field}"
            prompt_path = base_dir / step["prompt_path"]
            assert prompt_path.exists(), (
                f"{name}/{step_id}: prompt_path does not exist: {prompt_path}"
            )
            schema_path_val = step.get("schema_path")
            if schema_path_val is None:
                continue
            schema_path = base_dir / schema_path_val
            assert schema_path.exists(), (
                f"{name}/{step_id}: schema_path does not exist: {schema_path}"
            )
            json.loads(schema_path.read_text(encoding="utf-8"))


def test_prescan_registry_matches_embedded_prompt_constants() -> None:
    data = json.loads((PRESCAN_ROOT / "registry.json").read_text(encoding="utf-8"))
    grok_path = SERVICE_ROOT / "lib" / "prescan" / "grok_passes.py"
    grok_text = grok_path.read_text(encoding="utf-8")

    assert set(data["steps"]) == {
        "PRESCAN_DEDUP",
        "PRESCAN_DISCOVER",
        "PRESCAN_FEASIBILITY",
        "PRESCAN_OPTIMIZE",
    }
    assert "PASS_SYSTEM_PROMPTS" in grok_text

    for step_id, step in data["steps"].items():
        assert step["constant_name"] in grok_text
        suffix = step_id.replace("PRESCAN_", "").lower()
        assert f'"{suffix}"' in grok_text
        schema_path = PRESCAN_ROOT / step["schema_path"]
        assert schema_path.exists(), f"{step_id}: schema missing at {schema_path}"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        assert "required" in schema, f"{step_id}: schema missing 'required' key"


def test_contract_snapshot_capture_is_deterministic_for_same_inputs() -> None:
    if str(SERVICE_ROOT) not in sys.path:
        sys.path.insert(0, str(SERVICE_ROOT))

    from benchmarking.registry.snapshot_capture import build_contract_snapshot

    snapshot_one = build_contract_snapshot()
    snapshot_two = build_contract_snapshot()

    assert snapshot_one.contract_snapshot_id == snapshot_two.contract_snapshot_id
    assert snapshot_one.snapshot_hash == snapshot_two.snapshot_hash
    assert snapshot_one.runtime_version == "v5"
    assert snapshot_one.contract_version == "promptsets/v4"
    assert "services/repo-truth-extractor/run_extraction_v5.py" in snapshot_one.source_files
    assert "services/repo-truth-extractor/promptsets/v4/promptset.yaml" in snapshot_one.source_files


def test_validator_suite_capture_uses_real_source_hashes() -> None:
    if str(SERVICE_ROOT) not in sys.path:
        sys.path.insert(0, str(SERVICE_ROOT))

    from benchmarking.registry.snapshot_capture import (
        build_contract_snapshot,
        build_validator_suite,
    )

    build_contract_snapshot()
    validator_suite = build_validator_suite(
        validator_suite_id="validators_phase_s_advisory_v1",
        surface_scope=["direct_provider_api", "openrouter_routed"],
        validators=["phase_s_registry_presence"],
        strength_class="moderate",
        contract_rigor="phase_s_weaker_contract_caveat",
        source_paths=[
            SERVICE_ROOT / "prompts" / "phase_s" / "registry.json",
            SERVICE_ROOT / "prompts" / "phase_s" / "PROMPT_SP11_CONTRACT_LINTER.md",
        ],
    )

    assert validator_suite.version_hash == validator_suite.content_hash
    assert "services/repo-truth-extractor/prompts/phase_s/registry.json" in validator_suite.source_files
    assert len(validator_suite.content_hashes) == 2
    assert all(len(value) == 64 for value in validator_suite.content_hashes.values())


def test_phase_s_rejects_non_base_steps_in_selection() -> None:
    runner = _load_runner_module()

    with pytest.raises(RuntimeError, match="only allows S0-S12"):
        runner._get_s_step_controls(SimpleNamespace(s_steps="S0,S13"))
