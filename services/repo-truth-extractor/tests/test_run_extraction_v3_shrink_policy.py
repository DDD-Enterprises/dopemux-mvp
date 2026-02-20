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


def test_classify_failure_type_maps_payload_and_rate_and_unknown() -> None:
    runner = _load_runner_module()
    assert runner.classify_failure_type(413, "", "payload too large") == "payload"
    assert runner.classify_failure_type(429, "", "rate limit") == "rate_limit"
    assert runner.classify_failure_type(None, "", "") == "unknown"


def test_is_auth_classified_failure_truth_table() -> None:
    runner = _load_runner_module()
    assert runner.is_auth_classified_failure("auth_rejected") is True
    assert runner.is_auth_classified_failure("api_key_missing_or_invalid") is True
    assert runner.is_auth_classified_failure("rate_limit") is False


def test_retryable_exception_detection() -> None:
    runner = _load_runner_module()
    assert runner.is_retryable_exception(TimeoutError("connection timeout")) is True
    assert runner.is_retryable_exception(RuntimeError("boom")) is False
