from __future__ import annotations

from decimal import Decimal, InvalidOperation
import json
import os
from pathlib import Path
import re
from typing import Any

from jsonschema import Draft202012Validator, exceptions as jsonschema_exceptions

from .storage.hashing import hash_json, stable_json_dumps


LIVE_BENCHMARK_ENV = "RTE_OPENROUTER_BENCHMARK_LIVE"
DPMX_LIVE_OK_ENV = "DPMX_LIVE_OK"
API_KEY_ENVS = ("OPENROUTER_API_KEY", "V5_OPENROUTER_API_KEY")
UNKNOWN = "UNKNOWN"

_SECRET_PATTERNS = (
    re.compile(r"Authorization:\s*Bearer\s+[A-Za-z0-9_\-.]{10,}", re.IGNORECASE),
    re.compile(r"Bearer\s+[A-Za-z0-9_\-.]{10,}", re.IGNORECASE),
    re.compile(r"\bsk" r"-or-[A-Za-z0-9_\-.]{8,}\b", re.IGNORECASE),
    re.compile(r"\bOPENROUTER_API_KEY\s*=\s*\S+", re.IGNORECASE),
    re.compile(r"\bV5_OPENROUTER_API_KEY\s*=\s*\S+", re.IGNORECASE),
)


class BenchmarkExecutionError(ValueError):
    """Raised when the benchmark harness cannot execute safely."""


def stable_result_json(result: dict[str, Any]) -> str:
    return stable_json_dumps(_redact_value(result))


def _redact_string(value: str) -> tuple[str, bool]:
    redacted = value
    changed = False
    for pattern in _SECRET_PATTERNS:
        next_value = pattern.sub("[REDACTED]", redacted)
        changed = changed or next_value != redacted
        redacted = next_value
    return redacted, changed


def _redact_value(value: Any) -> Any:
    if isinstance(value, str):
        return _redact_string(value)[0]
    if isinstance(value, list):
        return [_redact_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _redact_value(item) for key, item in sorted(value.items())}
    return value


def _contains_secret(value: Any) -> bool:
    if isinstance(value, str):
        return any(pattern.search(value) for pattern in _SECRET_PATTERNS)
    if isinstance(value, list):
        return any(_contains_secret(item) for item in value)
    if isinstance(value, dict):
        return any(
            _contains_secret(key) or _contains_secret(item)
            for key, item in value.items()
        )
    return False


def _safe_string(value: Any, *, default: str = UNKNOWN) -> str:
    if value is None:
        return default
    if not isinstance(value, str):
        return default
    normalized = value.strip()
    if not normalized:
        return default
    return _redact_string(normalized)[0]


def _load_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BenchmarkExecutionError(f"fixture JSON is malformed: {path}") from exc
    if not isinstance(payload, dict):
        raise BenchmarkExecutionError("fixture JSON root must be an object")
    return payload


def _require_fields(
    payload: dict[str, Any], fields: tuple[str, ...], *, label: str
) -> None:
    missing = [field for field in fields if field not in payload]
    if missing:
        raise BenchmarkExecutionError(
            f"{label} missing required fields: {', '.join(missing)}"
        )


def _validate_fixture_catalog(payload: dict[str, Any]) -> dict[str, Any]:
    _require_fields(payload, ("schema", "fixtures"), label="fixture catalog")
    schema_record = payload["schema"]
    fixtures = payload["fixtures"]
    if not isinstance(schema_record, dict):
        raise BenchmarkExecutionError("schema record must be an object")
    if not isinstance(fixtures, list) or not all(
        isinstance(item, dict) for item in fixtures
    ):
        raise BenchmarkExecutionError("fixtures must be an array of objects")

    _require_fields(
        schema_record,
        ("schema_id", "schema_version", "schema"),
        label="schema record",
    )
    schema = schema_record["schema"]
    if not isinstance(schema, dict):
        raise BenchmarkExecutionError("schema must be an object")
    try:
        Draft202012Validator.check_schema(schema)
    except jsonschema_exceptions.SchemaError as exc:
        raise BenchmarkExecutionError(
            "benchmark schema is not valid JSON Schema"
        ) from exc

    required_fixture_fields = (
        "fixture_id",
        "fixture_class",
        "input_text",
        "expected_schema_id",
        "expected_facts",
        "expected_validation_outcome",
        "direct_overlap_required",
        "live_allowed",
    )
    for fixture in fixtures:
        _require_fields(fixture, required_fixture_fields, label="fixture")
        if fixture["expected_schema_id"] != schema_record["schema_id"]:
            raise BenchmarkExecutionError(
                f"fixture {fixture['fixture_id']} expected schema does not match catalog"
            )
        if fixture["live_allowed"] is not False:
            raise BenchmarkExecutionError(
                f"fixture {fixture['fixture_id']} is not offline-safe"
            )

    normalized_schema_record = dict(schema_record)
    normalized_schema_record["schema_hash"] = hash_json(schema)
    return {"schema": normalized_schema_record, "fixtures": fixtures}


def load_benchmark_fixtures(path: Path) -> dict[str, Any]:
    return _validate_fixture_catalog(_load_json_object(path))


def validate_live_mode_allowed(
    *,
    live_mode: bool,
    route_profile_id: str | None,
    requested_model: str | None,
    env: dict[str, str] | None = None,
) -> None:
    if not live_mode:
        return
    source = os.environ if env is None else env
    if source.get(LIVE_BENCHMARK_ENV) != "1":
        raise BenchmarkExecutionError(
            f"live OpenRouter benchmark requires {LIVE_BENCHMARK_ENV}=1"
        )
    if source.get(DPMX_LIVE_OK_ENV) != "1":
        raise BenchmarkExecutionError(
            f"live OpenRouter benchmark requires {DPMX_LIVE_OK_ENV}=1"
        )
    if not _safe_string(route_profile_id, default=""):
        raise BenchmarkExecutionError(
            "live OpenRouter benchmark requires route_profile_id"
        )
    if not _safe_string(requested_model, default=""):
        raise BenchmarkExecutionError(
            "live OpenRouter benchmark requires requested_model"
        )
    if not any(source.get(name, "").strip() for name in API_KEY_ENVS):
        raise BenchmarkExecutionError(
            "live OpenRouter benchmark requires OPENROUTER_API_KEY or V5_OPENROUTER_API_KEY"
        )


def _parse_content(content: Any) -> tuple[bool, Any, list[str]]:
    if not isinstance(content, str):
        return False, None, ["invalid_json"]
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return False, None, ["invalid_json"]
    if not isinstance(parsed, dict):
        return False, None, ["invalid_json_root_not_object"]
    return True, parsed, []


def _validate_schema(parsed: Any, schema: dict[str, Any]) -> tuple[bool, list[str]]:
    if not isinstance(parsed, dict):
        return False, []
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(parsed), key=lambda item: list(item.path))
    if not errors:
        return True, []
    messages = []
    for error in errors:
        path = ".".join(str(item) for item in error.path) or "$"
        clean_message = _redact_string(error.message)[0]
        messages.append(f"schema_validation_failed:{path}:{clean_message}")
    return False, messages


def _estimate_cost(usage: Any, pricing: Any) -> str | None:
    if not isinstance(usage, dict) or not isinstance(pricing, dict):
        return None
    try:
        prompt_tokens = Decimal(str(usage.get("prompt_tokens", 0)))
        completion_tokens = Decimal(str(usage.get("completion_tokens", 0)))
        prompt_price = Decimal(str(pricing.get("prompt", 0)))
        completion_price = Decimal(str(pricing.get("completion", 0)))
    except (InvalidOperation, TypeError, ValueError):
        return None
    cost = (prompt_tokens * prompt_price) + (completion_tokens * completion_price)
    return f"{cost:.10f}"


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return _redact_value(value)
    if value in (None, UNKNOWN):
        return []
    return [_redact_value(value)]


def _expected_fact_errors(
    *, parsed: Any, expected_facts: Any
) -> list[str]:
    if not isinstance(expected_facts, dict):
        return ["expected_facts_invalid"]
    if not isinstance(parsed, dict):
        return []

    parsed_facts = parsed.get("facts")
    fact_values: dict[str, Any] = {}
    if isinstance(parsed_facts, list):
        for fact in parsed_facts:
            if not isinstance(fact, dict):
                continue
            key = fact.get("key")
            if isinstance(key, str) and key.strip():
                fact_values[key] = fact.get("value")

    errors: list[str] = []
    for key, expected_value in sorted(expected_facts.items()):
        if key in parsed:
            actual_value = parsed.get(key)
        else:
            actual_value = fact_values.get(key, UNKNOWN)
        if actual_value != expected_value:
            errors.append(f"expected_fact_mismatch:{_safe_string(key)}")
    return errors


def _validation_outcome(
    *, parse_success: bool, schema_success: bool, validation_errors: list[str]
) -> str:
    if (
        parse_success
        and schema_success
        and validation_errors == ["direct_overlap_comparison_required"]
    ):
        return "PASS_WITH_DIRECT_COMPARISON_REQUIRED"
    if parse_success and schema_success and not validation_errors:
        return "PASS"
    return "FAIL"


def run_structured_benchmark(
    *,
    fixture: dict[str, Any],
    schema_record: dict[str, Any],
    model_response: dict[str, Any],
    certification_mode: bool,
    live_mode: bool = False,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    validate_live_mode_allowed(
        live_mode=live_mode,
        route_profile_id=_safe_string(
            model_response.get("route_profile_id"), default=""
        ),
        requested_model=_safe_string(model_response.get("requested_model"), default=""),
        env=env,
    )

    schema = schema_record.get("schema")
    if not isinstance(schema, dict):
        raise BenchmarkExecutionError("schema_record.schema must be an object")

    response_format_type = _safe_string(
        model_response.get("response_format_type"), default=UNKNOWN
    )
    downgrade_detected = response_format_type == "json_object"
    parse_success, parsed, parse_errors = _parse_content(model_response.get("content"))
    schema_success, schema_errors = _validate_schema(parsed, schema)

    actual_model = _safe_string(model_response.get("actual_model"), default=UNKNOWN)
    route_classification = _safe_string(
        model_response.get("route_classification"),
        default=UNKNOWN,
    )
    direct_overlap_status = _safe_string(
        model_response.get("direct_overlap_status"),
        default=UNKNOWN,
    )
    structured_outputs_supported = (
        model_response.get("structured_outputs_supported") is True
    )
    direct_overlap_comparison_required = bool(
        fixture.get("direct_overlap_required")
    ) or (
        direct_overlap_status == "DIRECT_OVERLAP_EXCEPTION"
        or route_classification == "DIRECT_OVERLAP_EXCEPTION"
    )

    validation_errors: list[str] = []
    validation_errors.extend(parse_errors)
    validation_errors.extend(schema_errors)
    validation_errors.extend(
        _expected_fact_errors(
            parsed=parsed,
            expected_facts=fixture.get("expected_facts"),
        )
    )
    if certification_mode and actual_model == UNKNOWN:
        validation_errors.append("missing_actual_model")
    if downgrade_detected:
        validation_errors.append("response_format_downgrade_json_object")
    elif response_format_type != "json_schema":
        validation_errors.append(f"response_format_not_json_schema:{response_format_type}")
    if not structured_outputs_supported:
        validation_errors.append("unsupported_structured_output_route")
    if route_classification == "FREE_EXPERIMENTAL":
        validation_errors.append("free_experimental_not_final_artifact_authority")
    if direct_overlap_comparison_required:
        validation_errors.append("direct_overlap_comparison_required")
    expected_validation_outcome = _safe_string(
        fixture.get("expected_validation_outcome")
    )
    actual_validation_outcome = _validation_outcome(
        parse_success=parse_success,
        schema_success=schema_success,
        validation_errors=validation_errors,
    )
    if (
        expected_validation_outcome != UNKNOWN
        and expected_validation_outcome != actual_validation_outcome
    ):
        validation_errors.append(
            "expected_validation_outcome_mismatch:"
            f"{expected_validation_outcome}:{actual_validation_outcome}"
        )

    final_artifact_allowed = (
        bool(certification_mode)
        and parse_success
        and schema_success
        and not validation_errors
    )
    redaction_status = "REDACTED" if _contains_secret(model_response) else "NOT_NEEDED"

    result = {
        "schema_id": _safe_string(schema_record.get("schema_id")),
        "schema_hash": _safe_string(
            schema_record.get("schema_hash"), default=hash_json(schema)
        ),
        "schema_version": _safe_string(schema_record.get("schema_version")),
        "fixture_id": _safe_string(fixture.get("fixture_id")),
        "route_profile_id": _safe_string(model_response.get("route_profile_id")),
        "requested_model": _safe_string(model_response.get("requested_model")),
        "actual_model": actual_model,
        "actual_provider": _safe_string(model_response.get("actual_provider")),
        "route_classification": route_classification,
        "direct_overlap_status": direct_overlap_status,
        "direct_overlap_comparison_required": direct_overlap_comparison_required,
        "response_format_type": response_format_type,
        "expected_validation_outcome": expected_validation_outcome,
        "actual_validation_outcome": actual_validation_outcome,
        "json_parse_success": parse_success,
        "schema_validation_success": schema_success,
        "validation_errors": sorted(set(_redact_value(validation_errors))),
        "downgrade_detected": downgrade_detected,
        "usage": _redact_value(
            model_response.get("usage")
            if isinstance(model_response.get("usage"), dict)
            else {}
        ),
        "cost_estimate": _estimate_cost(
            model_response.get("usage"), model_response.get("pricing")
        ),
        "latency_ms": model_response.get("latency_ms")
        if isinstance(model_response.get("latency_ms"), (int, float))
        else None,
        "retries": _as_list(model_response.get("retries")),
        "fallbacks": _as_list(model_response.get("fallbacks")),
        "redaction_status": redaction_status,
        "certification_mode": bool(certification_mode),
        "final_artifact_allowed": final_artifact_allowed,
    }
    return _redact_value(result)
