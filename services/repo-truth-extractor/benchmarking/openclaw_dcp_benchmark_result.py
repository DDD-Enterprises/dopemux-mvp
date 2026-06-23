from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator

from .storage.hashing import hash_json, stable_json_dumps


_PROVIDER_VALUES = {
    "openai",
    "anthropic",
    "google",
    "openrouter",
    "local",
    "manual",
    "multiple",
    "unknown",
}
_RUNNER_VALUES = {
    "openclaw",
    "codex",
    "claude_code",
    "gemini_antigravity",
    "openrouter_generic",
    "direct_api",
    "manual_app",
    "shell_local",
    "dopetask",
    "unknown",
}
_DIFF_APPLICABILITY_VALUES = {
    "applies",
    "does_not_apply",
    "not_applicable",
    "unknown",
}
_TESTS_RESULT_VALUES = {
    "passed",
    "failed",
    "not_run",
    "not_applicable",
    "unknown",
}
_SECRET_PATTERNS = (
    re.compile(r"Authorization:\s*Bearer\s+[A-Za-z0-9_\-.]{10,}", re.IGNORECASE),
    re.compile(r"Bearer\s+[A-Za-z0-9_\-.]{10,}", re.IGNORECASE),
    re.compile(r"\bsk" r"-or-[A-Za-z0-9_\-.]{8,}\b", re.IGNORECASE),
    re.compile(r"\bOPENROUTER_API_KEY\s*=\s*\S+", re.IGNORECASE),
    re.compile(r"\bV5_OPENROUTER_API_KEY\s*=\s*\S+", re.IGNORECASE),
)


def _repo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[3]


def load_benchmark_result_schema(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or _repo_root_from_here()
    path = root / "contracts" / "openclaw-dcp-routing" / "benchmark_result.schema.json"
    return json.loads(path.read_text(encoding="utf-8"))


def validate_benchmark_result(
    result: dict[str, Any], schema: dict[str, Any] | None = None
) -> list[str]:
    validator = Draft7Validator(schema or load_benchmark_result_schema())
    errors = sorted(validator.iter_errors(result), key=lambda item: list(item.path))
    messages: list[str] = []
    for error in errors:
        path = ".".join(str(part) for part in error.path) or "$"
        messages.append(f"{path}: {error.message}")
    return messages


def stable_benchmark_result_json(result: dict[str, Any]) -> str:
    return stable_json_dumps(result)


def _safe_string(value: Any, *, default: str = "unknown") -> str:
    if not isinstance(value, str):
        return default
    normalized = value.strip()
    return normalized or default


def _redact_string(value: str) -> str:
    redacted = value
    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def _enum_string(value: Any, allowed: set[str], *, default: str = "unknown") -> str:
    normalized = _safe_string(value, default=default).lower()
    return normalized if normalized in allowed else default


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _non_negative_float(value: Any) -> float | None:
    parsed = _float_or_none(value)
    if parsed is None or parsed < 0:
        return None
    return parsed


def _ratio_or_none(value: Any) -> float | None:
    parsed = _float_or_none(value)
    if parsed is None or parsed < 0 or parsed > 1:
        return None
    return parsed


def _non_negative_int(value: Any, *, default: int = 0) -> int:
    if isinstance(value, bool):
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed >= 0 else default


def _non_negative_int_or_none(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    if isinstance(value, str) and re.fullmatch(r"\d+", value.strip()):
        return int(value)
    return None


def _bool(value: Any) -> bool:
    return bool(value is True)


def _error_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return sorted(_safe_string(item, default="unknown_error") for item in value)


def _path_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return sorted(_safe_string(item, default="unknown_path") for item in value)


def _id_part(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9_.:-]+", "_", value.strip())
    return normalized.strip("_") or "unknown"


def _provider_drift(
    *, observed_provider: str, expected_provider: str | None
) -> dict[str, Any]:
    expected = (
        _enum_string(expected_provider, _PROVIDER_VALUES)
        if expected_provider
        else None
    )
    if expected is None:
        return {
            "detected": True,
            "details": f"expected provider missing, observed {observed_provider}",
        }
    if expected == "unknown" or observed_provider == "unknown":
        return {
            "detected": True,
            "details": f"expected provider {expected}, observed {observed_provider}",
        }
    if expected and observed_provider != expected:
        return {
            "detected": True,
            "details": f"expected provider {expected}, observed {observed_provider}",
        }
    return {"detected": False, "details": ""}


def _privacy_violation(metrics: dict[str, Any]) -> dict[str, Any]:
    detected = _bool(metrics.get("privacy_violation_detected"))
    return {
        "detected": detected,
        "details": _redact_string(
            _safe_string(metrics.get("privacy_violation_details"), default="")
        )
        if detected
        else "",
    }


def _certification_recommendation(
    *,
    final_artifact_allowed: bool,
    json_valid: bool,
    schema_valid: bool,
    evidence_precision: float,
    unsupported_claim_count: int,
    unsupported_claim_rate: float,
    hallucinated_file_count: int,
    contradiction_recall: float | None,
    core_field_stability: float | None,
    provider_drift_detected: bool,
    privacy_violation_detected: bool,
) -> str:
    hard_fail = (
        not final_artifact_allowed
        or not json_valid
        or not schema_valid
        or unsupported_claim_count > 0
        or unsupported_claim_rate > 0.01
        or hallucinated_file_count > 0
        or provider_drift_detected
        or privacy_violation_detected
    )
    if hard_fail:
        return "DO_NOT_CERTIFY"
    if contradiction_recall is None or core_field_stability is None:
        return "NEEDS_MORE_DATA"
    if (
        evidence_precision >= 0.98
        and contradiction_recall >= 0.9
        and core_field_stability >= 0.95
    ):
        return "CERTIFY"
    return "DO_NOT_CERTIFY"


def build_benchmark_result(
    *,
    fixture: dict[str, Any],
    structured_result: dict[str, Any],
    created_at: str,
    metrics: dict[str, Any] | None = None,
    expected_provider: str | None = None,
    benchmark_result_id: str | None = None,
) -> dict[str, Any]:
    metric_values = metrics or {}
    fixture_id = _safe_string(
        fixture.get("fixture_id") or structured_result.get("fixture_id"),
        default="unknown_fixture",
    )
    route_tested = _safe_string(
        structured_result.get("route_profile_id"),
        default="unknown_route",
    )
    requested_model = _safe_string(structured_result.get("requested_model"))
    actual_model = _safe_string(structured_result.get("actual_model"))
    provider = _enum_string(structured_result.get("actual_provider"), _PROVIDER_VALUES)
    runner = _enum_string(
        structured_result.get("runner")
        or metric_values.get("runner")
        or "openrouter_generic",
        _RUNNER_VALUES,
    )

    validation_errors = _error_list(structured_result.get("validation_errors"))
    json_valid = _bool(structured_result.get("json_parse_success"))
    schema_valid = _bool(structured_result.get("schema_validation_success"))
    final_artifact_allowed = _bool(structured_result.get("final_artifact_allowed"))

    evidence_precision = _ratio_or_none(
        metric_values.get("evidence_grounding_precision")
    )
    if evidence_precision is None:
        evidence_precision = 0.0
    evidence_sample_count = _non_negative_int(metric_values.get("evidence_sample_count"))
    unsupported_claim_count = _non_negative_int_or_none(
        metric_values.get("unsupported_claim_count")
    )
    if unsupported_claim_count is None:
        unsupported_claim_count = 1 if "unsupported_claim_count" in metric_values else 0
    unsupported_claim_rate = _ratio_or_none(metric_values.get("unsupported_claim_rate"))
    if unsupported_claim_rate is None:
        if "unsupported_claim_rate" in metric_values:
            unsupported_claim_rate = 1.0
        elif "unsupported_claim_count" in metric_values and unsupported_claim_count == 0:
            unsupported_claim_rate = 0.0
        else:
            unsupported_claim_rate = 1.0
    hallucinated_paths = _path_list(metric_values.get("hallucinated_file_paths"))
    hallucinated_file_count = _non_negative_int(
        metric_values.get("hallucinated_file_count"),
        default=len(hallucinated_paths),
    )
    if hallucinated_file_count == 0 and hallucinated_paths:
        hallucinated_file_count = len(hallucinated_paths)

    contradiction_recall = _ratio_or_none(metric_values.get("contradiction_recall"))
    if contradiction_recall is None and "contradiction_recall" in metric_values:
        contradiction_recall = 0.0
    core_field_stability = _ratio_or_none(metric_values.get("core_field_stability"))
    if core_field_stability is None and "core_field_stability" in metric_values:
        core_field_stability = 0.0
    provider_drift = _provider_drift(
        observed_provider=provider,
        expected_provider=expected_provider,
    )
    privacy_violation = _privacy_violation(metric_values)

    recommendation = _certification_recommendation(
        final_artifact_allowed=final_artifact_allowed,
        json_valid=json_valid,
        schema_valid=schema_valid,
        evidence_precision=evidence_precision,
        unsupported_claim_count=unsupported_claim_count,
        unsupported_claim_rate=unsupported_claim_rate,
        hallucinated_file_count=hallucinated_file_count,
        contradiction_recall=contradiction_recall,
        core_field_stability=core_field_stability,
        provider_drift_detected=provider_drift["detected"],
        privacy_violation_detected=privacy_violation["detected"],
    )
    pass_fail = "PASS" if recommendation == "CERTIFY" else "FAIL"
    identity = _safe_string(benchmark_result_id, default="") or (
        "br_"
        + _id_part(fixture_id)
        + "_"
        + hash_json(
            {
                "fixture_id": fixture_id,
                "route_tested": route_tested,
                "requested_model": requested_model,
                "actual_model": actual_model,
                "provider": provider,
                "created_at": created_at,
            }
        )[:12]
    )

    return {
        "schema_version": "1.0.0",
        "benchmark_result_id": identity,
        "fixture_id": fixture_id,
        "route_tested": route_tested,
        "requested_model": requested_model,
        "actual_model": actual_model,
        "provider": provider,
        "runner": runner,
        "pass_fail": pass_fail,
        "json_validity": {"valid": json_valid, "rate": 1.0 if json_valid else 0.0},
        "schema_validity": {
            "valid": schema_valid,
            "rate": 1.0 if schema_valid else 0.0,
            "errors": [] if schema_valid else validation_errors,
        },
        "evidence_grounding": {
            "precision": evidence_precision,
            "sample_count": evidence_sample_count,
        },
        "unsupported_claims": {
            "count": unsupported_claim_count,
            "rate": unsupported_claim_rate,
        },
        "hallucinated_files": {
            "count": hallucinated_file_count,
            "paths": hallucinated_paths,
        },
        "contradiction_recall": contradiction_recall,
        "core_field_stability": core_field_stability,
        "diff_applicability": _enum_string(
            metric_values.get("diff_applicability"),
            _DIFF_APPLICABILITY_VALUES,
            default="not_applicable",
        ),
        "tests_result": _enum_string(
            metric_values.get("tests_result"),
            _TESTS_RESULT_VALUES,
            default="not_run",
        ),
        "latency": {
            "wall_ms": _non_negative_float(structured_result.get("latency_ms")),
            "ttfb_ms": _non_negative_float(metric_values.get("ttfb_ms")),
            "ttft_ms": _non_negative_float(metric_values.get("ttft_ms")),
        },
        "cost": {
            "actual_usd": _non_negative_float(metric_values.get("actual_usd")),
            "estimated_usd": _non_negative_float(
                structured_result.get("cost_estimate")
            ),
        },
        "provider_drift": provider_drift,
        "privacy_violation": privacy_violation,
        "certification_recommendation": recommendation,
        "created_at": created_at,
    }
