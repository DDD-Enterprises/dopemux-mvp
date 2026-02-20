from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_runner_module():
    root = Path(__file__).resolve().parents[3]
    module_path = root / "services" / "repo-truth-extractor" / "run_extraction_v3.py"
    spec = importlib.util.spec_from_file_location("run_extraction_v3", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_enrich_request_meta_adds_required_routing_keys() -> None:
    runner = _load_runner_module()
    meta = runner.enrich_request_meta(
        {
            "status_code": 429,
            "failure_type": "rate_limit",
            "retry_trace": [{"attempt": 1, "status_code": 429}],
        },
        run_id="run-123",
        phase="A",
        step_id="A0",
        partition_id="A_P0001",
        provider="gemini",
        model_id=runner.DEFAULT_GEMINI_MODEL_ID,
    )

    assert meta["run_id"] == "run-123"
    assert meta["phase"] == "A"
    assert meta["step_id"] == "A0"
    assert meta["partition_id"] == "A_P0001"
    assert meta["provider"] == "gemini"
    assert "routing_signature" in meta
    assert "provider_signature" in meta


def test_classify_failure_type_handles_provider_reasons() -> None:
    runner = _load_runner_module()
    assert runner.classify_failure_type(429, "resource_exhausted", "") == "quota_or_billing"
    assert runner.classify_failure_type(500, "", "server exploded") == "provider"
