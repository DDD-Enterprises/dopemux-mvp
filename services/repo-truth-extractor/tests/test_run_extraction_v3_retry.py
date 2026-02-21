import importlib.util
from pathlib import Path
import sys


def _load_runner_module():
    root = Path(__file__).resolve().parents[3]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    module_path = root / "services" / "repo-truth-extractor" / "run_extraction_v3.py"
    spec = importlib.util.spec_from_file_location("run_extraction_v3", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_classify_failure_type_auth_and_rate_and_payload():
    runner = _load_runner_module()
    assert runner.classify_failure_type(401, "", "unauthorized") == "auth_rejected"
    assert runner.classify_failure_type(429, "", "rate limit exceeded") == "rate_limit"
    assert runner.classify_failure_type(413, "", "payload too large") == "payload"


def test_should_retry_respects_policy_and_failure_kind():
    runner = _load_runner_module()
    assert runner.should_retry(429, "rate_limit", None, "default") is True
    assert runner.should_retry(503, "provider", None, "default") is True
    assert runner.should_retry(401, "auth_rejected", None, "default") is False
    assert runner.should_retry(429, "rate_limit", None, "none") is False


def test_backoff_seconds_doubles_and_caps():
    runner = _load_runner_module()
    assert runner.backoff_seconds(1, 2.0, 30.0) == 0.0
    assert runner.backoff_seconds(2, 2.0, 30.0) == 2.0
    assert runner.backoff_seconds(3, 2.0, 30.0) == 4.0
    assert runner.backoff_seconds(10, 2.0, 5.0) == 5.0
