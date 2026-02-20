from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

CLASSIFICATION_VERSION = "reqmeta_v1"

TRANSPORT_FAILURE_TYPES = {
    "quota_or_billing",
    "auth",
    "timeout",
    "network",
    "provider_5xx",
    "provider_4xx_other",
    "unknown_transport",
    "none",
}

CONTENT_FAILURE_TYPES = {
    "contract_violation",
    "parse",
    "schema",
    "ok",
    "none",
}


def _status_code_to_int(value: Any) -> Optional[int]:
    if isinstance(value, int):
        return value
    try:
        return int(str(value))
    except Exception:
        return None


def classify_transport_failure(
    *,
    failure_type: Any,
    status_code: Any,
    response_received: bool,
    exception_type: Any = None,
) -> str:
    failure = str(failure_type or "").strip().lower()
    status = _status_code_to_int(status_code)
    exc = str(exception_type or "").strip().lower()

    if not failure and status is None and response_received:
        return "none"

    if (
        failure in {"quota_or_billing", "rate_limit"}
        or status == 429
    ):
        return "quota_or_billing"
    if failure.startswith("auth_") or failure in {
        "api_key_missing_or_invalid",
        "permission_denied",
        "auth_rejected",
    } or status in {401, 403}:
        return "auth"
    if failure == "timeout" or status == 408 or exc in {"timeout", "readtimeout", "connecttimeout"}:
        return "timeout"
    if failure == "network" or exc in {"connectionerror"}:
        return "network"
    if isinstance(status, int) and status >= 500:
        return "provider_5xx"
    if isinstance(status, int) and 400 <= status < 500:
        return "provider_4xx_other"
    if not response_received:
        return "unknown_transport"
    return "none"


def classify_content_failure(
    *,
    parsed_json: bool,
    artifacts_ok: bool,
    strict_decode_error: bool,
    validation_reason: Optional[str] = None,
) -> str:
    reason = str(validation_reason or "").strip().lower()
    if artifacts_ok:
        return "ok"
    if not parsed_json:
        if strict_decode_error:
            return "parse"
        return "contract_violation"
    if reason.startswith("no_expected_artifacts") or reason.startswith("artifacts_missing_or_not_list"):
        return "schema"
    if reason.startswith("missing_success_json"):
        return "none"
    return "schema"


def merge_final_failure_type(
    *,
    transport_failure: str,
    content_failure: str,
    io_persist_error: bool = False,
) -> str:
    if io_persist_error:
        return "io_persist"
    if transport_failure != "none":
        return transport_failure
    if content_failure in {"parse", "schema", "contract_violation"}:
        return content_failure
    if content_failure == "ok":
        return "ok"
    return "unknown_failure"


def classify_partition_failure(
    *,
    failure_type: Any,
    status_code: Any,
    response_received: bool,
    exception_type: Any,
    parsed_json: bool,
    artifacts_ok: bool,
    strict_decode_error: bool,
    validation_reason: Optional[str] = None,
    io_persist_error: bool = False,
) -> Tuple[str, str, str]:
    transport = classify_transport_failure(
        failure_type=failure_type,
        status_code=status_code,
        response_received=response_received,
        exception_type=exception_type,
    )
    content = classify_content_failure(
        parsed_json=parsed_json,
        artifacts_ok=artifacts_ok,
        strict_decode_error=strict_decode_error,
        validation_reason=validation_reason,
    )
    final = merge_final_failure_type(
        transport_failure=transport,
        content_failure=content,
        io_persist_error=io_persist_error,
    )
    return transport, content, final


def attach_classification_fields(
    request_meta: Dict[str, Any],
    *,
    parsed_json: bool,
    artifacts_ok: bool,
    strict_decode_error: bool,
    validation_reason: Optional[str] = None,
    io_persist_error: bool = False,
) -> Dict[str, Any]:
    failure_type_transport, failure_type_content, final_failure_type = classify_partition_failure(
        failure_type=request_meta.get("failure_type"),
        status_code=request_meta.get("status_code"),
        response_received=bool(request_meta.get("response_received")),
        exception_type=request_meta.get("exception_type"),
        parsed_json=parsed_json,
        artifacts_ok=artifacts_ok,
        strict_decode_error=strict_decode_error,
        validation_reason=validation_reason,
        io_persist_error=io_persist_error,
    )
    enriched = dict(request_meta)
    enriched["failure_type_transport"] = failure_type_transport
    enriched["failure_type_content"] = failure_type_content
    enriched["final_failure_type"] = final_failure_type
    enriched["classification_version"] = CLASSIFICATION_VERSION
    return enriched
