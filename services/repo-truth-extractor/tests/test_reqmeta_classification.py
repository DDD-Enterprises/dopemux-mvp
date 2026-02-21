from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_module():
    root = Path(__file__).resolve().parents[3]
    module_path = root / "services" / "repo-truth-extractor" / "lib" / "request_meta_classification.py"
    spec = importlib.util.spec_from_file_location("request_meta_classification", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_reqmeta_classification_transport_429() -> None:
    module = _load_module()
    transport, content, final = module.classify_partition_failure(
        failure_type="rate_limit",
        status_code=429,
        response_received=False,
        exception_type="RateLimitError",
        parsed_json=False,
        artifacts_ok=False,
        strict_decode_error=False,
    )
    assert transport == "quota_or_billing"
    assert content == "contract_violation"
    assert final == "quota_or_billing"


def test_reqmeta_classification_auth_failure() -> None:
    module = _load_module()
    transport, content, final = module.classify_partition_failure(
        failure_type="auth_rejected",
        status_code=401,
        response_received=False,
        exception_type="AuthError",
        parsed_json=False,
        artifacts_ok=False,
        strict_decode_error=False,
    )
    assert transport == "auth"
    assert final == "auth"


def test_reqmeta_parse_after_successful_transport() -> None:
    module = _load_module()
    enriched = module.attach_classification_fields(
        {
            "failure_type": None,
            "status_code": 200,
            "response_received": True,
        },
        parsed_json=False,
        artifacts_ok=False,
        strict_decode_error=True,
    )
    assert enriched["failure_type_transport"] == "none"
    assert enriched["failure_type_content"] == "parse"
    assert enriched["final_failure_type"] == "parse"


def test_reqmeta_missing_success_json_maps_to_io_persist() -> None:
    module = _load_module()
    enriched = module.attach_classification_fields(
        {
            "failure_type": None,
            "status_code": 200,
            "response_received": True,
        },
        parsed_json=True,
        artifacts_ok=True,
        strict_decode_error=False,
        validation_reason="missing_success_json",
        io_persist_error=True,
    )
    assert enriched["final_failure_type"] == "io_persist"
