from __future__ import annotations

import importlib.util
import json
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


runner = _load_runner_module()


def _make_cfg():
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
        routing_policy="balanced_grok_openrouter",
    )


def test_phase_d_provider_preflight_blocks_on_openrouter_402(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def fake_probe(provider, model_id, api_key_env, cfg):  # type: ignore[no-untyped-def]
        if provider == "openrouter":
            return {
                "provider": provider,
                "model_id": model_id,
                "status_code": 402,
                "failure_type": "payload",
                "provider_error_reason": "insufficient_credits",
            }
        return {
            "provider": provider,
            "model_id": model_id,
            "status_code": 200,
            "failure_type": None,
        }

    monkeypatch.setattr(runner, "run_provider_doctor_probe", fake_probe)

    with pytest.raises(RuntimeError) as exc_info:
        runner.prepare_phase_provider_preflight(tmp_path, "run_d_preflight", "D", _make_cfg())

    assert "denylisted_providers=openrouter" in str(exc_info.value)
    payload_path = tmp_path / runner.V3_DOCTOR_ROOT / "PROVIDER_PREFLIGHT__D.json"
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    assert payload["status"] == "FAIL"
    assert payload["denylisted_providers"] == ["openrouter"]


def test_phase_d_provider_preflight_is_not_required_when_no_openrouter_routes() -> None:
    cfg = runner.RunnerConfig(
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
    assert runner.phase_requires_provider_preflight("D", cfg) is False
