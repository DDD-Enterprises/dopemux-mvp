from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


def _load_runner_module():
    root = Path(__file__).resolve().parents[3]
    module_path = root / "services" / "repo-truth-extractor" / "run_extraction_v3.py"
    spec = importlib.util.spec_from_file_location("run_extraction_v3", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _make_cfg(runner):
    return runner.RunnerConfig(
        dry_run=False,
        max_files_docs=10,
        max_files_code=10,
        max_chars=10000,
        max_request_bytes=200000,
        file_truncate_chars=500,
        home_scan_mode="safe",
        resume=False,
        fail_fast_auth=False,
        gemini_auth_mode="auto",
        gemini_transport="sdk",
        openai_transport="openai_sdk",
        xai_transport="openai_sdk",
        retry_policy="none",
        retry_max_attempts=1,
        retry_base_seconds=0.0,
        retry_max_seconds=0.0,
        phase_auth_fail_threshold=5,
        partition_workers=1,
        debug_phase_inputs=False,
        fail_fast_missing_inputs=False,
        routing_policy="cost",
    )


def _reset_routing(runner) -> None:
    runner.apply_model_overrides(runner.DEFAULT_GEMINI_MODEL_ID, "cost")


def test_step_tier_classifier_is_deterministic() -> None:
    runner = _load_runner_module()
    assert runner.resolve_step_tier("A", "A0") == "bulk"
    assert runner.resolve_step_tier("A", "A1") == "extract"
    assert runner.resolve_step_tier("Q", "Q1") == "qa"
    assert runner.resolve_step_tier("C", "C9") == "qa"
    assert runner.resolve_step_tier("R", "R1") == "synthesis"
    assert runner.resolve_step_tier("Z", "Z2") == "synthesis"


def test_cost_policy_ladders_map_expected_defaults() -> None:
    runner = _load_runner_module()
    _reset_routing(runner)
    assert runner.resolve_step_ladder("cost", "A", "A0")[0] == ("openai", "gpt-5-nano", "OPENAI_API_KEY")
    assert runner.resolve_step_ladder("cost", "A", "A1")[0] == ("google", "gemini-2.5-flash", "GEMINI_API_KEY")
    assert runner.resolve_step_ladder("cost", "R", "R1")[0] == ("openai", "gpt-5.2", "OPENAI_API_KEY")
    assert runner.resolve_step_ladder("cost", "Q", "Q9")[0] == ("openai", "gpt-5-nano", "OPENAI_API_KEY")


def test_gemini_override_rewrites_all_gemini_rungs() -> None:
    runner = _load_runner_module()
    runner.apply_model_overrides("models/gemini-2.5-flash", "cost")
    ladders = runner.routing_ladders_payload()
    for policy_rows in ladders.values():
        for routes in policy_rows.values():
            for route in routes:
                if route["provider"] == "gemini":
                    assert route["model_id"] == "models/gemini-2.5-flash"


def test_collect_provider_routes_returns_unique_route_rows() -> None:
    runner = _load_runner_module()
    _reset_routing(runner)
    routes = runner.collect_provider_routes(phases=["A", "R"], routing_policy="cost")
    providers = {row["provider"] for row in routes.values()}
    assert "openai" in providers
    assert "gemini" in providers
    assert "xai" in providers


def test_provider_preflight_fails_when_probe_fails(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    runner = _load_runner_module()

    def fake_probe(provider, model_id, api_key_env, cfg):  # type: ignore[no-untyped-def]
        if provider == "gemini":
            return {
                "provider": provider,
                "model_id": model_id,
                "status_code": 401,
                "failure_type": "auth_rejected",
            }
        return {
            "provider": provider,
            "model_id": model_id,
            "status_code": 200,
            "failure_type": None,
        }

    monkeypatch.setattr(runner, "run_provider_doctor_probe", fake_probe)

    ok, payload = runner.run_provider_preflight(
        root=tmp_path,
        run_id="test_preflight",
        cfg=_make_cfg(runner),
        phases=["A"],
    )

    assert ok is False
    assert payload["status"] == "FAIL"
    assert "gemini" in payload["failed_providers"]


def test_print_config_reports_effective_model_routing_and_policy(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[3]
    script = root / "services" / "repo-truth-extractor" / "run_extraction_v3.py"
    run_id = "test_model_routing_print_config"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--print-config",
            "--run-id",
            run_id,
            "--no-write-latest",
            "--gemini-model-id",
            "models/gemini-2.5-flash",
            "--routing-policy",
            "cost",
            "--phase",
            "A",
        ],
        cwd=str(tmp_path),
        check=True,
        text=True,
        capture_output=True,
    )
    payload = json.loads(result.stdout)
    assert payload["cli"]["gemini_model_id"] == "models/gemini-2.5-flash"
    assert payload["cli"]["routing_policy"] == "cost"
    assert payload["effective_model_routing"]["A"]["provider"] == "openai"
    assert payload["effective_model_routing"]["A"]["model_id"] == "gpt-5-nano"


def test_run_manifest_records_routing_policy(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[3]
    script = root / "services" / "repo-truth-extractor" / "run_extraction_v3.py"
    run_id = "test_model_routing_manifest"
    subprocess.run(
        [
            sys.executable,
            str(script),
            "--print-config",
            "--run-id",
            run_id,
            "--no-write-latest",
            "--phase",
            "A",
            "--routing-policy",
            "cost",
        ],
        cwd=str(tmp_path),
        check=True,
        text=True,
        capture_output=True,
    )

    manifest_path = tmp_path / "extraction" / "repo-truth-extractor" / "v3" / "runs" / run_id / "RUN_MANIFEST.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["routing_policy"] == "cost"
    assert payload["routing_policy_version"] == "RTE_ROUTING_V1"
    assert "routing_ladders" in payload


def test_balanced_policy_ladders_match_user_request() -> None:
    runner = _load_runner_module()
    _reset_routing(runner)
    # Bulk should prefer gemini-2.5-flash
    assert runner.resolve_step_ladder("balanced", "A", "A0")[0] == ("gemini", "gemini-2.5-flash", "GEMINI_API_KEY")
    # Extract should prefer gemini-2.5-flash
    assert runner.resolve_step_ladder("balanced", "A", "A1")[0] == ("gemini", "gemini-2.5-flash", "GEMINI_API_KEY")
    # Synthesis should use opus-4.6
    assert runner.resolve_step_ladder("balanced", "R", "R1")[1] == ("openrouter", "anthropic/claude-opus-4.6", "OPENROUTER_API_KEY")
