from __future__ import annotations

import json
from pathlib import Path

import pytest

from benchmarking.openrouter_structured_benchmark import (
    BenchmarkExecutionError,
    DPMX_LIVE_OK_ENV,
    LIVE_BENCHMARK_ENV,
    load_benchmark_fixtures,
    run_structured_benchmark,
    stable_result_json,
    validate_live_mode_allowed,
)


FIXTURE_PATH = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "openrouter_structured_benchmark_fixtures.json"
)


def _valid_payload() -> dict:
    return {
        "repo_name": "atlas-api",
        "primary_language": "Python",
        "summary_status": "OBSERVED",
        "facts": [
            {
                "key": "ci_system",
                "value": "GitHub Actions",
                "status": "OBSERVED",
                "evidence": [
                    {
                        "path": "README.md",
                        "start_line": 1,
                        "end_line": 2,
                    }
                ],
            }
        ],
        "unknowns": [],
        "conflicts": [],
        "direct_overlap_evaluation": "NOT_REQUIRED",
    }


def _base_response(**overrides: object) -> dict:
    response = {
        "route_profile_id": "or_qwen_structured_benchmark",
        "requested_model": "qwen/qwen3-coder",
        "actual_model": "qwen/qwen3-coder",
        "actual_provider": "openrouter",
        "route_classification": "OPENROUTER_VALUE_CANDIDATE",
        "direct_overlap_status": "NOT_DIRECT_OVERLAP",
        "response_format_type": "json_schema",
        "structured_outputs_supported": True,
        "content": json.dumps(_valid_payload(), sort_keys=True),
        "usage": {"prompt_tokens": 100, "completion_tokens": 20},
        "pricing": {"prompt": "0.000001", "completion": "0.000002"},
        "latency_ms": 42,
        "retries": [],
        "fallbacks": [],
    }
    response.update(overrides)
    return response


def test_fixture_catalog_contains_required_tiny_rte_cases() -> None:
    catalog = load_benchmark_fixtures(FIXTURE_PATH)

    assert [fixture["fixture_id"] for fixture in catalog["fixtures"]] == [
        "small_clean_repo",
        "doc_code_contradiction_repo",
        "sparse_doc_repo",
    ]
    assert catalog["schema"]["schema_id"] == "rte_repo_summary_benchmark_v1"
    assert catalog["schema"]["schema"]["additionalProperties"] is False
    assert all(fixture["live_allowed"] is False for fixture in catalog["fixtures"])


def test_offline_benchmark_succeeds_with_valid_strict_json() -> None:
    catalog = load_benchmark_fixtures(FIXTURE_PATH)
    result = run_structured_benchmark(
        fixture=catalog["fixtures"][0],
        schema_record=catalog["schema"],
        model_response=_base_response(),
        certification_mode=True,
    )

    assert result["json_parse_success"] is True
    assert result["schema_validation_success"] is True
    assert result["actual_model"] == "qwen/qwen3-coder"
    assert result["actual_provider"] == "openrouter"
    assert result["cost_estimate"] == "0.0001400000"
    assert result["final_artifact_allowed"] is True


def test_factually_wrong_response_blocks_certification() -> None:
    catalog = load_benchmark_fixtures(FIXTURE_PATH)
    payload = _valid_payload()
    payload["repo_name"] = "wrong-repo"

    result = run_structured_benchmark(
        fixture=catalog["fixtures"][0],
        schema_record=catalog["schema"],
        model_response=_base_response(content=json.dumps(payload)),
        certification_mode=True,
    )

    assert result["json_parse_success"] is True
    assert result["schema_validation_success"] is True
    assert result["final_artifact_allowed"] is False
    assert "expected_fact_mismatch:repo_name" in result["validation_errors"]
    assert result["expected_validation_outcome"] == "PASS"
    assert "expected_validation_outcome_mismatch:PASS:FAIL" in result["validation_errors"]


def test_invalid_json_fails_parse_and_blocks_certification() -> None:
    catalog = load_benchmark_fixtures(FIXTURE_PATH)
    result = run_structured_benchmark(
        fixture=catalog["fixtures"][0],
        schema_record=catalog["schema"],
        model_response=_base_response(content="{not-json"),
        certification_mode=True,
    )

    assert result["json_parse_success"] is False
    assert result["schema_validation_success"] is False
    assert result["final_artifact_allowed"] is False
    assert "invalid_json" in result["validation_errors"]


def test_schema_mismatch_fails_validation_and_blocks_certification() -> None:
    payload = _valid_payload()
    payload.pop("facts")
    catalog = load_benchmark_fixtures(FIXTURE_PATH)

    result = run_structured_benchmark(
        fixture=catalog["fixtures"][0],
        schema_record=catalog["schema"],
        model_response=_base_response(content=json.dumps(payload)),
        certification_mode=True,
    )

    assert result["json_parse_success"] is True
    assert result["schema_validation_success"] is False
    assert result["final_artifact_allowed"] is False
    assert any(
        "schema_validation_failed" in error for error in result["validation_errors"]
    )


def test_missing_actual_model_fails_certification_mode() -> None:
    catalog = load_benchmark_fixtures(FIXTURE_PATH)
    result = run_structured_benchmark(
        fixture=catalog["fixtures"][0],
        schema_record=catalog["schema"],
        model_response=_base_response(actual_model=""),
        certification_mode=True,
    )

    assert result["json_parse_success"] is True
    assert result["schema_validation_success"] is True
    assert result["final_artifact_allowed"] is False
    assert "missing_actual_model" in result["validation_errors"]


def test_downgrade_to_json_object_is_detected_and_blocks_certification() -> None:
    catalog = load_benchmark_fixtures(FIXTURE_PATH)
    result = run_structured_benchmark(
        fixture=catalog["fixtures"][0],
        schema_record=catalog["schema"],
        model_response=_base_response(response_format_type="json_object"),
        certification_mode=True,
    )

    assert result["downgrade_detected"] is True
    assert result["final_artifact_allowed"] is False
    assert "response_format_downgrade_json_object" in result["validation_errors"]


def test_live_mode_without_opt_in_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(LIVE_BENCHMARK_ENV, raising=False)

    with pytest.raises(BenchmarkExecutionError, match=LIVE_BENCHMARK_ENV):
        validate_live_mode_allowed(
            live_mode=True,
            route_profile_id="or_qwen_structured_benchmark",
            requested_model="qwen/qwen3-coder",
        )


def test_live_mode_requires_repo_wide_live_consent() -> None:
    with pytest.raises(BenchmarkExecutionError, match=DPMX_LIVE_OK_ENV):
        validate_live_mode_allowed(
            live_mode=True,
            route_profile_id="or_qwen_structured_benchmark",
            requested_model="qwen/qwen3-coder",
            env={
                LIVE_BENCHMARK_ENV: "1",
                "OPENROUTER_API_KEY": "fixture-key",
            },
        )


def test_live_mode_accepts_explicit_env_without_network_call() -> None:
    catalog = load_benchmark_fixtures(FIXTURE_PATH)
    result = run_structured_benchmark(
        fixture=catalog["fixtures"][0],
        schema_record=catalog["schema"],
        model_response=_base_response(),
        certification_mode=True,
        live_mode=True,
        env={
            DPMX_LIVE_OK_ENV: "1",
            LIVE_BENCHMARK_ENV: "1",
            "OPENROUTER_API_KEY": "fixture-key",
        },
    )

    assert result["json_parse_success"] is True
    assert result["schema_validation_success"] is True


def test_unsupported_structured_output_route_blocks_certification() -> None:
    catalog = load_benchmark_fixtures(FIXTURE_PATH)
    result = run_structured_benchmark(
        fixture=catalog["fixtures"][0],
        schema_record=catalog["schema"],
        model_response=_base_response(structured_outputs_supported=False),
        certification_mode=True,
    )

    assert result["final_artifact_allowed"] is False
    assert "unsupported_structured_output_route" in result["validation_errors"]


def test_direct_overlap_exception_marks_comparison_required() -> None:
    catalog = load_benchmark_fixtures(FIXTURE_PATH)
    result = run_structured_benchmark(
        fixture=catalog["fixtures"][1],
        schema_record=catalog["schema"],
        model_response=_base_response(
            route_classification="DIRECT_OVERLAP_EXCEPTION",
            direct_overlap_status="DIRECT_OVERLAP_EXCEPTION",
        ),
        certification_mode=True,
    )

    assert result["direct_overlap_status"] == "DIRECT_OVERLAP_EXCEPTION"
    assert result["direct_overlap_comparison_required"] is True
    assert result["final_artifact_allowed"] is False


def test_free_experimental_route_cannot_be_final_artifact_allowed() -> None:
    catalog = load_benchmark_fixtures(FIXTURE_PATH)
    result = run_structured_benchmark(
        fixture=catalog["fixtures"][0],
        schema_record=catalog["schema"],
        model_response=_base_response(
            route_classification="FREE_EXPERIMENTAL",
            requested_model="qwen/qwen3-coder:free",
            actual_model="qwen/qwen3-coder:free",
        ),
        certification_mode=True,
    )

    assert result["route_classification"] == "FREE_EXPERIMENTAL"
    assert result["final_artifact_allowed"] is False
    assert (
        "free_experimental_not_final_artifact_authority" in result["validation_errors"]
    )


def test_benchmark_result_json_is_deterministic_and_secret_redacted() -> None:
    secret = "sk" + "-or-v1-secretvalue0123456789"
    catalog = load_benchmark_fixtures(FIXTURE_PATH)
    result_one = run_structured_benchmark(
        fixture=catalog["fixtures"][0],
        schema_record=catalog["schema"],
        model_response=_base_response(content=json.dumps(_valid_payload()) + secret),
        certification_mode=True,
    )
    result_two = run_structured_benchmark(
        fixture=catalog["fixtures"][0],
        schema_record=catalog["schema"],
        model_response=_base_response(content=json.dumps(_valid_payload()) + secret),
        certification_mode=True,
    )

    encoded = stable_result_json(result_one)
    assert encoded == stable_result_json(result_two)
    assert secret not in encoded
    assert "sk" + "-or-" not in encoded
    assert result_one["redaction_status"] == "REDACTED"


def test_parseable_response_with_secret_like_value_does_not_leak() -> None:
    secret = "sk" + "-or-v1-secretvalue0123456789"
    payload = _valid_payload()
    payload["facts"][0]["evidence"][0]["path"] = secret
    catalog = load_benchmark_fixtures(FIXTURE_PATH)

    result = run_structured_benchmark(
        fixture=catalog["fixtures"][0],
        schema_record=catalog["schema"],
        model_response=_base_response(content=json.dumps(payload)),
        certification_mode=True,
    )

    encoded = stable_result_json(result)
    assert result["json_parse_success"] is True
    assert result["redaction_status"] == "REDACTED"
    assert secret not in encoded
