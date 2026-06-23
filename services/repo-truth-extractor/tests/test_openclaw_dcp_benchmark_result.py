from __future__ import annotations

from pathlib import Path

from jsonschema import Draft7Validator

from benchmarking.openclaw_dcp_benchmark_result import (
    build_benchmark_result,
    load_benchmark_result_schema,
    stable_benchmark_result_json,
    validate_benchmark_result,
)


REPO_ROOT = Path(__file__).resolve().parents[3]


def _fixture() -> dict:
    return {"fixture_id": "small_clean_repo"}


def _structured_result(**overrides: object) -> dict:
    result = {
        "fixture_id": "small_clean_repo",
        "route_profile_id": "or_qwen_structured_benchmark",
        "requested_model": "qwen/qwen3-coder",
        "actual_model": "qwen/qwen3-coder",
        "actual_provider": "openrouter",
        "json_parse_success": True,
        "schema_validation_success": True,
        "validation_errors": [],
        "final_artifact_allowed": True,
        "latency_ms": 42,
        "cost_estimate": "0.0001400000",
    }
    result.update(overrides)
    return result


def test_builds_contract_schema_valid_certification_result() -> None:
    schema = load_benchmark_result_schema(REPO_ROOT)

    result = build_benchmark_result(
        fixture=_fixture(),
        structured_result=_structured_result(),
        created_at="2026-06-22T00:00:00Z",
        expected_provider="openrouter",
        metrics={
            "evidence_grounding_precision": 0.99,
            "evidence_sample_count": 12,
            "unsupported_claim_count": 0,
            "unsupported_claim_rate": 0.0,
            "contradiction_recall": 0.95,
            "core_field_stability": 0.98,
        },
    )

    assert Draft7Validator(schema).is_valid(result)
    assert validate_benchmark_result(result, schema) == []
    assert result["schema_version"] == "1.0.0"
    assert result["benchmark_result_id"].startswith("br_small_clean_repo_")
    assert result["route_tested"] == "or_qwen_structured_benchmark"
    assert result["pass_fail"] == "PASS"
    assert result["certification_recommendation"] == "CERTIFY"
    assert result["latency"] == {"wall_ms": 42.0, "ttfb_ms": None, "ttft_ms": None}
    assert result["cost"] == {"actual_usd": None, "estimated_usd": 0.00014}


def test_failures_emit_schema_valid_do_not_certify_result() -> None:
    schema = load_benchmark_result_schema(REPO_ROOT)

    result = build_benchmark_result(
        fixture=_fixture(),
        structured_result=_structured_result(
            schema_validation_success=False,
            validation_errors=["schema_validation_failed:$.facts"],
            final_artifact_allowed=False,
        ),
        created_at="2026-06-22T00:00:00Z",
    )

    assert validate_benchmark_result(result, schema) == []
    assert result["pass_fail"] == "FAIL"
    assert result["schema_validity"] == {
        "valid": False,
        "rate": 0.0,
        "errors": ["schema_validation_failed:$.facts"],
    }
    assert result["certification_recommendation"] == "DO_NOT_CERTIFY"
    assert result["contradiction_recall"] is None
    assert result["core_field_stability"] is None


def test_provider_drift_blocks_certification_and_remains_schema_valid() -> None:
    result = build_benchmark_result(
        fixture=_fixture(),
        structured_result=_structured_result(actual_provider="anthropic"),
        created_at="2026-06-22T00:00:00Z",
        expected_provider="openrouter",
        metrics={
            "evidence_grounding_precision": 0.99,
            "evidence_sample_count": 12,
            "contradiction_recall": 0.95,
            "core_field_stability": 0.98,
        },
    )

    assert validate_benchmark_result(result, load_benchmark_result_schema(REPO_ROOT)) == []
    assert result["provider"] == "anthropic"
    assert result["provider_drift"] == {
        "detected": True,
        "details": "expected provider openrouter, observed anthropic",
    }
    assert result["pass_fail"] == "FAIL"
    assert result["certification_recommendation"] == "DO_NOT_CERTIFY"


def test_missing_grounding_precision_does_not_certify_even_when_other_metrics_pass() -> None:
    result = build_benchmark_result(
        fixture=_fixture(),
        structured_result=_structured_result(),
        created_at="2026-06-22T00:00:00Z",
        expected_provider="openrouter",
        metrics={
            "evidence_sample_count": 12,
            "contradiction_recall": 0.95,
            "core_field_stability": 0.98,
        },
    )

    assert validate_benchmark_result(result, load_benchmark_result_schema(REPO_ROOT)) == []
    assert result["evidence_grounding"]["precision"] == 0.0
    assert result["certification_recommendation"] == "DO_NOT_CERTIFY"


def test_missing_expected_provider_does_not_certify_even_when_observed_provider_passes() -> None:
    result = build_benchmark_result(
        fixture=_fixture(),
        structured_result=_structured_result(),
        created_at="2026-06-22T00:00:00Z",
        metrics={
            "evidence_grounding_precision": 0.99,
            "evidence_sample_count": 12,
            "contradiction_recall": 0.95,
            "core_field_stability": 0.98,
        },
    )

    assert validate_benchmark_result(result, load_benchmark_result_schema(REPO_ROOT)) == []
    assert result["provider_drift"] == {
        "detected": True,
        "details": "expected provider missing, observed openrouter",
    }
    assert result["certification_recommendation"] == "DO_NOT_CERTIFY"


def test_missing_unsupported_claim_metrics_do_not_certify() -> None:
    result = build_benchmark_result(
        fixture=_fixture(),
        structured_result=_structured_result(),
        created_at="2026-06-22T00:00:00Z",
        expected_provider="openrouter",
        metrics={
            "evidence_grounding_precision": 0.99,
            "evidence_sample_count": 12,
            "contradiction_recall": 0.95,
            "core_field_stability": 0.98,
        },
    )

    assert validate_benchmark_result(result, load_benchmark_result_schema(REPO_ROOT)) == []
    assert result["unsupported_claims"] == {"count": 0, "rate": 1.0}
    assert result["certification_recommendation"] == "DO_NOT_CERTIFY"


def test_malformed_unsupported_claim_count_does_not_certify() -> None:
    result = build_benchmark_result(
        fixture=_fixture(),
        structured_result=_structured_result(),
        created_at="2026-06-22T00:00:00Z",
        expected_provider="openrouter",
        metrics={
            "evidence_grounding_precision": 0.99,
            "evidence_sample_count": 12,
            "unsupported_claim_count": "bad",
            "contradiction_recall": 0.95,
            "core_field_stability": 0.98,
        },
    )

    assert validate_benchmark_result(result, load_benchmark_result_schema(REPO_ROOT)) == []
    assert result["unsupported_claims"] == {"count": 1, "rate": 1.0}
    assert result["certification_recommendation"] == "DO_NOT_CERTIFY"


def test_non_integral_unsupported_claim_count_does_not_certify() -> None:
    result = build_benchmark_result(
        fixture=_fixture(),
        structured_result=_structured_result(),
        created_at="2026-06-22T00:00:00Z",
        expected_provider="openrouter",
        metrics={
            "evidence_grounding_precision": 0.99,
            "evidence_sample_count": 12,
            "unsupported_claim_count": 0.9,
            "contradiction_recall": 0.95,
            "core_field_stability": 0.98,
        },
    )

    assert validate_benchmark_result(result, load_benchmark_result_schema(REPO_ROOT)) == []
    assert result["unsupported_claims"] == {"count": 1, "rate": 1.0}
    assert result["certification_recommendation"] == "DO_NOT_CERTIFY"


def test_unknown_expected_and_observed_provider_do_not_certify() -> None:
    result = build_benchmark_result(
        fixture=_fixture(),
        structured_result=_structured_result(actual_provider=""),
        created_at="2026-06-22T00:00:00Z",
        expected_provider="unknown",
        metrics={
            "evidence_grounding_precision": 0.99,
            "evidence_sample_count": 12,
            "unsupported_claim_count": 0,
            "unsupported_claim_rate": 0.0,
            "contradiction_recall": 0.95,
            "core_field_stability": 0.98,
        },
    )

    assert validate_benchmark_result(result, load_benchmark_result_schema(REPO_ROOT)) == []
    assert result["provider"] == "unknown"
    assert result["provider_drift"] == {
        "detected": True,
        "details": "expected provider unknown, observed unknown",
    }
    assert result["certification_recommendation"] == "DO_NOT_CERTIFY"


def test_privacy_violation_details_are_redacted() -> None:
    secret = "sk" + "-or-v1-secretvalue0123456789"

    result = build_benchmark_result(
        fixture=_fixture(),
        structured_result=_structured_result(),
        created_at="2026-06-22T00:00:00Z",
        expected_provider="openrouter",
        metrics={
            "privacy_violation_detected": True,
            "privacy_violation_details": f"fixture included {secret}",
        },
    )

    assert validate_benchmark_result(result, load_benchmark_result_schema(REPO_ROOT)) == []
    assert secret not in result["privacy_violation"]["details"]
    assert "sk" + "-or-" not in stable_benchmark_result_json(result)
    assert result["privacy_violation"]["details"] == "fixture included [REDACTED]"


def test_privacy_violation_details_redact_bearer_and_env_secret_formats() -> None:
    secret_values = [
        "Authorization: Bearer abcdefghijklmnop",
        "Bearer abcdefghijklmnop",
        "OPENROUTER_API_KEY=secret-value",
        "V5_OPENROUTER_API_KEY=secret-value",
        "OPENAI_API_KEY=sk-proj-placeholdersecret0123456789",
        "ANTHROPIC_API_KEY=anthropic-placeholder-secret",
        "GEMINI_API_KEY=gemini-placeholder-secret",
        "GOOGLE_API_KEY=google-placeholder-secret",
        "sk-proj-placeholdersecret0123456789",
        "sk-placeholdersecret0123456789",
    ]

    for secret in secret_values:
        result = build_benchmark_result(
            fixture=_fixture(),
            structured_result=_structured_result(),
            created_at="2026-06-22T00:00:00Z",
            expected_provider="openrouter",
            metrics={
                "privacy_violation_detected": True,
                "privacy_violation_details": f"fixture included {secret}",
            },
        )

        encoded = stable_benchmark_result_json(result)
        assert validate_benchmark_result(result, load_benchmark_result_schema(REPO_ROOT)) == []
        assert secret not in result["privacy_violation"]["details"]
        assert secret not in encoded


def test_non_finite_latency_and_cost_are_rejected_before_serialization() -> None:
    result = build_benchmark_result(
        fixture=_fixture(),
        structured_result=_structured_result(latency_ms="Infinity", cost_estimate="NaN"),
        created_at="2026-06-22T00:00:00Z",
        expected_provider="openrouter",
        metrics={
            "evidence_grounding_precision": 0.99,
            "evidence_sample_count": 12,
            "unsupported_claim_count": 0,
            "unsupported_claim_rate": 0.0,
            "contradiction_recall": 0.95,
            "core_field_stability": 0.98,
        },
    )

    assert validate_benchmark_result(result, load_benchmark_result_schema(REPO_ROOT)) == []
    assert result["latency"]["wall_ms"] is None
    assert result["cost"]["estimated_usd"] is None
    assert "Infinity" not in stable_benchmark_result_json(result)
    assert "NaN" not in stable_benchmark_result_json(result)


def test_invalid_optional_metric_enums_fall_back_to_contract_defaults() -> None:
    result = build_benchmark_result(
        fixture=_fixture(),
        structured_result=_structured_result(),
        created_at="2026-06-22T00:00:00Z",
        metrics={
            "diff_applicability": "maybe",
            "tests_result": "greenish",
            "evidence_grounding_precision": 0.99,
            "evidence_sample_count": 12,
            "contradiction_recall": 0.95,
            "core_field_stability": 0.98,
        },
    )

    assert validate_benchmark_result(result, load_benchmark_result_schema(REPO_ROOT)) == []
    assert result["diff_applicability"] == "not_applicable"
    assert result["tests_result"] == "not_run"


def test_out_of_range_ratio_metrics_emit_schema_valid_do_not_certify_result() -> None:
    result = build_benchmark_result(
        fixture=_fixture(),
        structured_result=_structured_result(),
        created_at="2026-06-22T00:00:00Z",
        benchmark_result_id="",
        metrics={
            "evidence_grounding_precision": 1.5,
            "unsupported_claim_rate": -0.1,
            "contradiction_recall": 2.0,
            "core_field_stability": -1.0,
        },
    )

    assert validate_benchmark_result(result, load_benchmark_result_schema(REPO_ROOT)) == []
    assert result["benchmark_result_id"].startswith("br_small_clean_repo_")
    assert result["evidence_grounding"]["precision"] == 0.0
    assert result["unsupported_claims"]["rate"] == 1.0
    assert result["contradiction_recall"] == 0.0
    assert result["core_field_stability"] == 0.0
    assert result["certification_recommendation"] == "DO_NOT_CERTIFY"


def test_stable_json_is_deterministic() -> None:
    kwargs = {
        "fixture": _fixture(),
        "structured_result": _structured_result(),
        "created_at": "2026-06-22T00:00:00Z",
        "metrics": {
            "evidence_grounding_precision": 0.99,
            "evidence_sample_count": 12,
            "contradiction_recall": 0.95,
            "core_field_stability": 0.98,
        },
    }

    first = stable_benchmark_result_json(build_benchmark_result(**kwargs))
    second = stable_benchmark_result_json(build_benchmark_result(**kwargs))

    assert first == second
