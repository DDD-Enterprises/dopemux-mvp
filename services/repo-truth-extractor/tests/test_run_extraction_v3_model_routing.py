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
    )


def _reset_routing(runner) -> None:
    runner.apply_model_overrides(runner.DEFAULT_GEMINI_MODEL_ID)


def test_gemini_override_updates_gemini_phases_only() -> None:
    runner = _load_runner_module()
    _reset_routing(runner)
    runner.apply_model_overrides("models/gemini-2.5-flash")
    payload = runner.effective_model_routing_payload()

    gemini_phases = [phase for phase, route in payload.items() if route["provider"] == "gemini"]
    assert gemini_phases
    for phase in gemini_phases:
        assert payload[phase]["model_id"] == "models/gemini-2.5-flash"

    openai_phases = [phase for phase, route in payload.items() if route["provider"] == "openai"]
    assert openai_phases
    for phase in openai_phases:
        assert payload[phase]["model_id"] != "models/gemini-2.5-flash"


def test_collect_provider_routes_returns_unique_provider_rows() -> None:
    runner = _load_runner_module()
    _reset_routing(runner)
    routes = runner.collect_provider_routes()
    assert set(routes.keys()) >= {"gemini", "openai", "xai"}
    assert routes["gemini"]["provider"] == "gemini"
    assert routes["openai"]["api_key_env"] == "OPENAI_API_KEY"


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


def test_print_config_reports_effective_model_routing(tmp_path: Path) -> None:
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
    assert payload["effective_model_routing"]["A"]["provider"] == "gemini"
    assert payload["effective_model_routing"]["A"]["model_id"] == "models/gemini-2.5-flash"


def test_run_manifest_records_effective_model_routing(tmp_path: Path) -> None:
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
            "--gemini-model-id",
            "models/gemini-2.5-flash",
        ],
        cwd=str(tmp_path),
        check=True,
        text=True,
        capture_output=True,
    )

    manifest_path = tmp_path / "extraction" / "repo-truth-extractor" / "v3" / "runs" / run_id / "RUN_MANIFEST.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["effective_model_routing"]["A"]["provider"] == "gemini"
    assert payload["effective_model_routing"]["A"]["model_id"] == "models/gemini-2.5-flash"
