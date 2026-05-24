from __future__ import annotations

import copy
import json
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Sequence, Tuple

try:
    from output_safety import sanitize_payload_for_output, sanitize_text_for_output
except ModuleNotFoundError:  # pragma: no cover - supports direct importlib test loading
    _service_dir = str(Path(__file__).resolve().parents[1])
    if _service_dir not in sys.path:
        sys.path.insert(0, _service_dir)
    from output_safety import sanitize_payload_for_output, sanitize_text_for_output


class UnsupportedBatchProvider(RuntimeError):
    """Raised when a provider is not supported for live batch execution."""


@dataclass(frozen=True)
class BatchRequest:
    custom_id: str
    model_id: str
    system_prompt: str
    user_content: str
    force_json_output: bool = False
    metadata: Dict[str, str] = field(default_factory=dict)
    response_format: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class BatchResult:
    custom_id: str
    output_text: str
    error: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BatchRoute:
    provider: str
    model_id: str
    api_key_env: str
    base_url: Optional[str] = None


BATCH_STATIC_PROOF_MARKERS: Tuple[str, ...] = (
    "STATIC_FIXTURE_VALIDATED",
    "DOWNLOADED_JSONL_MISSING_IF_NOT_FOUND",
    "NOT_LIVE_VALIDATED",
    "LIVE_VALIDATION_REQUIRED",
    "NO_PROVIDER_CALLS_PERFORMED",
)

OPENAI_COMPATIBLE_SUCCESS_STATUSES = frozenset({"completed", "succeeded", "done"})
OPENAI_COMPATIBLE_FAILURE_STATUSES = frozenset(
    {"failed", "expired", "cancelled", "canceled", "timeout"}
)
OPENAI_COMPATIBLE_TERMINAL_STATUSES = (
    OPENAI_COMPATIBLE_SUCCESS_STATUSES | OPENAI_COMPATIBLE_FAILURE_STATUSES
)
BATCH_JSONL_CORRUPTION_THRESHOLD = 0.05


class BatchClient(Protocol):
    def submit(
        self,
        requests: Sequence[BatchRequest],
        route: BatchRoute,
        step_context: Dict[str, Any],
    ) -> str:
        ...

    def poll(self, job_id: str) -> str:
        ...

    def fetch_results(self, job_id: str) -> List[BatchResult]:
        ...

    def cancel(self, job_id: str) -> None:
        ...


def _metadata_flag_enabled(metadata: Dict[str, str], key: str) -> bool:
    return str(metadata.get(key) or "").strip().lower() in {"1", "true", "yes", "on"}


def _metadata_field(metadata: Dict[str, str], key: str) -> Optional[str]:
    """Phase E5: read a metadata string field (e.g. service_tier) with
    lower-case normalization. Returns None if absent or empty."""
    if not isinstance(metadata, dict):
        return None
    value = metadata.get(key)
    if value is None:
        return None
    token = str(value).strip().lower()
    return token or None


def classify_batch_terminal_status(status: str) -> Dict[str, Any]:
    token = str(status or "").strip().lower()
    if token in OPENAI_COMPATIBLE_SUCCESS_STATUSES:
        status_class = "success"
    elif token == "failed":
        status_class = "failed"
    elif token == "expired":
        status_class = "expired"
    elif token in {"cancelled", "canceled"}:
        status_class = "cancelled"
    elif token == "timeout":
        status_class = "timeout"
    elif token:
        status_class = "non_terminal"
    else:
        status_class = "unknown"
    return {
        "status": token or "unknown",
        "status_class": status_class,
        "terminal": token in OPENAI_COMPATIBLE_TERMINAL_STATUSES,
        "successful": token in OPENAI_COMPATIBLE_SUCCESS_STATUSES,
        "failure_terminal": token in OPENAI_COMPATIBLE_FAILURE_STATUSES,
    }


def _safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _safe_int(value: Any) -> Optional[int]:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    try:
        return int(str(value))
    except Exception:
        return None


def _redaction_status(raw: str, redacted: str) -> str:
    return "redacted" if raw != redacted else "clean"


def _partition_id_from_custom_id(custom_id: str) -> str:
    token = str(custom_id or "").strip()
    return token if "_P" in token else ""


def _phase_from_custom_id(custom_id: str) -> str:
    token = str(custom_id or "").strip()
    if "_P" not in token:
        return ""
    prefix = token.split("_P", 1)[0].strip()
    return prefix if prefix else ""


def build_batch_request_static_metadata(
    request: BatchRequest,
    route: Optional[BatchRoute] = None,
    *,
    wire_row: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Return proof-safe request-row metadata without raw prompt payload text."""

    body = _safe_dict(_safe_dict(wire_row).get("body")) if isinstance(wire_row, dict) else {}
    response_format = (
        _safe_dict(body.get("response_format"))
        if isinstance(body.get("response_format"), dict)
        else _safe_dict(request.response_format)
    )
    metadata = dict(request.metadata or {})
    custom_id = str(
        (_safe_dict(wire_row).get("custom_id") if isinstance(wire_row, dict) else "")
        or request.custom_id
        or ""
    )
    provider = str(route.provider if route is not None else metadata.get("provider", "")).strip()
    requested_model_id = str(
        body.get("model")
        or request.model_id
        or (route.model_id if route is not None else "")
        or ""
    )
    return {
        "custom_id": custom_id,
        "method": str(_safe_dict(wire_row).get("method") or "POST"),
        "url": str(_safe_dict(wire_row).get("url") or "/v1/chat/completions"),
        "body.model": requested_model_id,
        "body.messages_present_boolean": bool(
            isinstance(body.get("messages"), list)
            if body
            else request.system_prompt is not None and request.user_content is not None
        ),
        "body.response_format_type_if_present": str(response_format.get("type") or ""),
        "provider": provider,
        "requested_model_id": requested_model_id,
        "structured_output_mode_if_present": str(
            metadata.get("structured_output_mode")
            or response_format.get("type")
            or ""
        ),
        "partition_id_if_encoded": str(
            metadata.get("partition_id") or _partition_id_from_custom_id(custom_id)
        ),
        "phase_if_encoded": str(metadata.get("phase") or _phase_from_custom_id(custom_id)),
        "step_id_if_encoded": str(metadata.get("step_id") or ""),
        "payload_text_included": False,
        "redaction_status": "metadata_only_no_raw_payload",
    }


def _output_row_metadata(row: Dict[str, Any]) -> Dict[str, Any]:
    response = _safe_dict(row.get("response"))
    body = _safe_dict(response.get("body"))
    choices = _safe_list(body.get("choices"))
    first_choice = _safe_dict(choices[0]) if choices else {}
    message = _safe_dict(first_choice.get("message"))
    error = _safe_dict(row.get("error"))
    status_code = _safe_int(response.get("status_code"))
    failure_type = ""
    if error:
        failure_type = "provider_error"
    elif status_code is not None and status_code >= 400:
        failure_type = "provider_response_status"
    elif not body:
        failure_type = "response_body_missing"
    return {
        "custom_id": str(row.get("custom_id") or ""),
        "response_status_code": status_code,
        "response_body_present": bool(body),
        "response_id_if_present": str(body.get("id") or response.get("request_id") or ""),
        "returned_model_id_if_present": str(body.get("model") or ""),
        "finish_reason_if_present": str(first_choice.get("finish_reason") or ""),
        "usage_if_present": sanitize_payload_for_output(body.get("usage", {})),
        "failure_type_if_any": failure_type,
        "parse_status": "parsed",
        "schema_status_if_any": "not_checked_static_fixture",
        "redaction_status": "metadata_only_no_raw_payload",
        "response_message_present": bool(message),
    }


def _error_row_metadata(row: Dict[str, Any]) -> Dict[str, Any]:
    error = _safe_dict(row.get("error"))
    response = _safe_dict(row.get("response"))
    body = _safe_dict(response.get("body"))
    body_error = _safe_dict(body.get("error"))
    source_error = error or body_error
    raw_message = str(
        source_error.get("message")
        or row.get("message")
        or response.get("error")
        or "batch_error"
    )
    redacted_message = sanitize_text_for_output(raw_message)
    status_code = _safe_int(row.get("status_code"))
    if status_code is None:
        status_code = _safe_int(response.get("status_code"))
    return {
        "custom_id": str(row.get("custom_id") or ""),
        "error_type": str(source_error.get("type") or row.get("type") or "batch_error"),
        "error_code": str(source_error.get("code") or row.get("code") or ""),
        "error_message_redacted": redacted_message,
        "status_code_if_present": status_code,
        "failure_type": "provider_error",
        "redaction_status": _redaction_status(raw_message, redacted_message),
    }


_DISCARDED_LINES_SAMPLE_LIMIT = 50


def _parse_jsonl_rows(raw_text: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    discarded_lines: List[Dict[str, Any]] = []
    discarded_count = 0
    total_lines = 0
    blank_line_count = 0
    for line_number, raw_line in enumerate(str(raw_text or "").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            blank_line_count += 1
            continue
        total_lines += 1
        try:
            row = json.loads(line)
        except Exception as exc:
            discarded_count += 1
            if len(discarded_lines) < _DISCARDED_LINES_SAMPLE_LIMIT:
                discarded_lines.append(
                    {
                        "line_number": line_number,
                        "reason": "invalid_json",
                        "error_type": type(exc).__name__,
                        "preview_redacted": sanitize_text_for_output(line[:200]),
                    }
                )
            continue
        if not isinstance(row, dict):
            discarded_count += 1
            if len(discarded_lines) < _DISCARDED_LINES_SAMPLE_LIMIT:
                discarded_lines.append(
                    {
                        "line_number": line_number,
                        "reason": "non_object_json",
                        "preview_redacted": sanitize_text_for_output(line[:200]),
                    }
                )
            continue
        rows.append(row)
    threshold_exceeded = (
        total_lines > 0
        and (discarded_count / total_lines) > BATCH_JSONL_CORRUPTION_THRESHOLD
    )
    report = {
        "total_line_count": total_lines,
        "blank_line_count": blank_line_count,
        "valid_row_count": len(rows),
        "discarded_line_count": discarded_count,
        "corrupt_line_count": discarded_count,
        "discarded_lines": discarded_lines,
        "corruption_threshold": BATCH_JSONL_CORRUPTION_THRESHOLD,
        "corruption_threshold_exceeded": threshold_exceeded,
        "parse_status": (
            "corrupt_threshold_exceeded"
            if threshold_exceeded
            else ("parsed_with_discards" if discarded_count else "parsed")
        ),
    }
    return rows, report


def parse_openai_compatible_batch_output_jsonl(
    raw_text: str,
    *,
    raise_on_corruption: bool = False,
    not_live_validated: bool = True,
) -> Dict[str, Any]:
    rows, report = _parse_jsonl_rows(raw_text)
    metadata_rows = [_output_row_metadata(row) for row in rows]
    report = dict(report)
    report.update(
        {
            "artifact_class": "provider_output_jsonl_fixture",
            "rows": metadata_rows,
            "custom_ids": sorted(
                str(row.get("custom_id") or "") for row in metadata_rows if row.get("custom_id")
            ),
            "markers": list(BATCH_STATIC_PROOF_MARKERS) if not_live_validated else [],
            "not_live_validated": bool(not_live_validated),
        }
    )
    if raise_on_corruption and report["corruption_threshold_exceeded"]:
        raise RuntimeError(
            "BatchCorruptionError: "
            f"{report['discarded_line_count']}/{report['total_line_count']} "
            "results discarded (>5%)"
        )
    return report


def parse_openai_compatible_batch_error_jsonl(
    raw_text: str,
    *,
    raise_on_corruption: bool = False,
    not_live_validated: bool = True,
) -> Dict[str, Any]:
    rows, report = _parse_jsonl_rows(raw_text)
    metadata_rows = [_error_row_metadata(row) for row in rows]
    report = dict(report)
    report.update(
        {
            "artifact_class": "provider_error_jsonl_fixture",
            "rows": metadata_rows,
            "custom_ids": sorted(
                str(row.get("custom_id") or "") for row in metadata_rows if row.get("custom_id")
            ),
            "markers": list(BATCH_STATIC_PROOF_MARKERS) if not_live_validated else [],
            "not_live_validated": bool(not_live_validated),
        }
    )
    if raise_on_corruption and report["corruption_threshold_exceeded"]:
        raise RuntimeError(
            "BatchCorruptionError: "
            f"{report['discarded_line_count']}/{report['total_line_count']} "
            "error rows discarded (>5%)"
        )
    return report


def build_openai_compatible_batch_static_proof(
    *,
    request_custom_ids: Sequence[str],
    output_rows: Sequence[Dict[str, Any]],
    error_rows: Sequence[Dict[str, Any]],
    batch_info: Optional[Dict[str, Any]] = None,
    provider: str = "",
    requested_provider: str = "",
    requested_model_id: str = "",
) -> Dict[str, Any]:
    info = dict(batch_info or {})
    status = str(info.get("status") or "fixture_static").strip().lower()
    terminal = classify_batch_terminal_status(status)
    requested_ids = sorted({str(custom_id) for custom_id in request_custom_ids if str(custom_id)})
    result_ids = sorted(
        {
            str(row.get("custom_id") or "")
            for row in output_rows
            if isinstance(row, dict) and str(row.get("custom_id") or "")
        }
    )
    error_ids = sorted(
        {
            str(row.get("custom_id") or "")
            for row in error_rows
            if isinstance(row, dict) and str(row.get("custom_id") or "")
        }
    )
    observed_ids = set(result_ids) | set(error_ids)
    missing_ids = sorted(set(requested_ids) - observed_ids)
    duplicate_ids = sorted(set(result_ids) & set(error_ids))
    partial_failure = bool(error_ids or missing_ids or duplicate_ids)
    return {
        "batch_id": str(info.get("id") or info.get("batch_id") or ""),
        "provider": provider or str(info.get("provider") or ""),
        "requested_provider": requested_provider or provider or str(info.get("requested_provider") or ""),
        "requested_model_id": requested_model_id or str(info.get("requested_model_id") or ""),
        "status": status,
        "status_class": terminal["status_class"],
        "created_at": str(info.get("created_at") or ""),
        "completed_at_if_present": str(info.get("completed_at") or ""),
        "failed_at_if_present": str(info.get("failed_at") or ""),
        "cancelled_at_if_present": str(info.get("cancelled_at") or info.get("canceled_at") or ""),
        "expired_at_if_present": str(info.get("expired_at") or ""),
        "output_file_id": str(info.get("output_file_id") or ""),
        "error_file_id": str(info.get("error_file_id") or ""),
        "request_count": len(requested_ids),
        "result_count": len(result_ids),
        "error_count": len(error_ids),
        "missing_row_count": len(missing_ids),
        "missing_custom_ids": missing_ids,
        "duplicate_custom_ids_in_output_and_error": duplicate_ids,
        "partial_failure": partial_failure,
        "full_success": not partial_failure and bool(requested_ids),
        "missing_rows_are_hard_failure": bool(missing_ids),
        "not_live_validated": True,
        "markers": list(BATCH_STATIC_PROOF_MARKERS),
        "proof_scope": "local_static_fixture_only",
    }


def _response_format_for_request(req: BatchRequest) -> Optional[Dict[str, Any]]:
    strict_requested = _metadata_flag_enabled(req.metadata, "strict")
    if isinstance(req.response_format, dict):
        response_format = copy.deepcopy(req.response_format)
        rf_type = str(response_format.get("type") or "").strip()
        if strict_requested:
            json_schema = response_format.get("json_schema")
            schema = json_schema.get("schema") if isinstance(json_schema, dict) else None
            if (
                rf_type != "json_schema"
                or not isinstance(json_schema, dict)
                or not isinstance(schema, dict)
            ):
                raise ValueError("Strict batch request requires response_format.type=json_schema")
        return response_format
    if strict_requested:
        raise ValueError("Strict batch request requires response_format.type=json_schema")
    if req.force_json_output:
        return {"type": "json_object"}
    return None


class OpenAIBatchClient:
    def __init__(self, api_key: str, base_url: Optional[str] = None) -> None:
        from openai import OpenAI

        kwargs: Dict[str, Any] = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self._client = OpenAI(**kwargs)

    def submit(
        self,
        requests: Sequence[BatchRequest],
        route: BatchRoute,
        step_context: Dict[str, Any],
    ) -> str:
        payload_rows: List[Dict[str, Any]] = []
        for req in requests:
            body: Dict[str, Any] = {
                "model": req.model_id,
                "messages": [
                    {"role": "system", "content": req.system_prompt},
                    {"role": "user", "content": req.user_content},
                ],
                "temperature": 0.1,
            }
            response_format = _response_format_for_request(req)
            if response_format is not None:
                body["response_format"] = response_format
            # Phase E5: pass service_tier through batch payload if the request
            # carries it via metadata. Batch API itself is already a 50%
            # discount; service_tier in batch is honored by OpenAI but doesn't
            # stack further (batch IS flex-equivalent). We still emit it so
            # the request is honest about intent and the spend ledger can
            # reason about the actual tier path.
            requested_tier = _metadata_field(req.metadata, "service_tier")
            if requested_tier and requested_tier in ("default", "flex", "priority", "auto"):
                body["service_tier"] = requested_tier
            payload_rows.append(
                {
                    "custom_id": req.custom_id,
                    "method": "POST",
                    "url": "/v1/chat/completions",
                    "body": body,
                }
            )

        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", suffix=".jsonl", delete=False
        ) as handle:
            for row in payload_rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            payload_path = Path(handle.name)
        try:
            with payload_path.open("rb") as upload:
                file_obj = self._client.files.create(file=upload, purpose="batch")
            metadata = {
                "provider": route.provider,
                "phase": str(step_context.get("phase", "")),
                "step_id": str(step_context.get("step_id", "")),
            }
            batch_obj = self._client.batches.create(
                completion_window="24h",
                endpoint="/v1/chat/completions",
                input_file_id=str(file_obj.id),
                metadata=metadata,
            )
            return str(batch_obj.id)
        finally:
            try:
                payload_path.unlink(missing_ok=True)
            except Exception:
                pass

    def poll(self, job_id: str) -> str:
        batch_obj = self._client.batches.retrieve(job_id)
        return str(getattr(batch_obj, "status", "") or "").lower()

    def get_batch_info(self, job_id: str) -> Dict[str, Any]:
        batch_obj = self._client.batches.retrieve(job_id)
        return {
            "id": str(getattr(batch_obj, "id", "")),
            "status": str(getattr(batch_obj, "status", "") or "").lower(),
            "output_file_id": str(getattr(batch_obj, "output_file_id", "") or ""),
            "error_file_id": str(getattr(batch_obj, "error_file_id", "") or ""),
            "created_at": str(getattr(batch_obj, "created_at", "")),
            "completed_at": str(getattr(batch_obj, "completed_at", "")),
            "failed_at": str(getattr(batch_obj, "failed_at", "")),
            "expired_at": str(getattr(batch_obj, "expired_at", "")),
        }

    def fetch_results(self, job_id: str) -> List[BatchResult]:
        batch_obj = self._client.batches.retrieve(job_id)
        output_file_id = getattr(batch_obj, "output_file_id", None)
        if not output_file_id:
            return []
        content_obj = self._client.files.content(str(output_file_id))
        if hasattr(content_obj, "text"):
            raw_text = str(content_obj.text)
        elif hasattr(content_obj, "read"):
            value = content_obj.read()
            raw_text = (
                value.decode("utf-8", errors="replace")
                if isinstance(value, (bytes, bytearray))
                else str(value)
            )
        else:
            raw_text = str(content_obj)

        import logging
        logger = logging.getLogger(__name__)

        results: List[BatchResult] = []
        total_lines = 0
        discarded_lines = 0

        for line in raw_text.splitlines():
            line = line.strip()
            if not line:
                continue
            total_lines += 1
            try:
                row = json.loads(line)
            except Exception as e:
                discarded_lines += 1
                logger.warning(
                    "Discarding invalid JSON line in batch result: %s... Error: %s",
                    line[:200],
                    e,
                )
                continue
            if not isinstance(row, dict):
                discarded_lines += 1
                logger.warning("Discarding non-object JSON line in batch result: %s", line[:200])
                continue
            custom_id = str(row.get("custom_id") or "")
            response = row.get("response") if isinstance(row.get("response"), dict) else {}
            body = response.get("body") if isinstance(response.get("body"), dict) else {}
            output_text = ""
            choices = body.get("choices")
            if isinstance(choices, list) and choices:
                first = choices[0] if isinstance(choices[0], dict) else {}
                message = first.get("message") if isinstance(first.get("message"), dict) else {}
                output_text = str(message.get("content") or "")
            error_row = row.get("error")
            error = None
            if isinstance(error_row, dict):
                error = sanitize_text_for_output(
                    str(error_row.get("message") or error_row.get("code") or "batch_error")
                )
            safe_meta = sanitize_payload_for_output(row)
            if not isinstance(safe_meta, dict):
                logger.warning(
                    "sanitize_payload_for_output returned non-dict for custom_id=%s; "
                    "dropping row metadata",
                    custom_id,
                )
                safe_meta = {}
            results.append(
                BatchResult(
                    custom_id=custom_id,
                    output_text=output_text,
                    error=error,
                    meta=safe_meta,
                )
            )

        if total_lines > 0 and (discarded_lines / total_lines) > 0.05:
            raise RuntimeError(
                f"BatchCorruptionError: {discarded_lines}/{total_lines} results discarded (>5%)"
            )
        return results

    def cancel(self, job_id: str) -> None:
        self._client.batches.cancel(job_id)


class XAIBatchClient(OpenAIBatchClient):
    def __init__(self, api_key: str, base_url: str = "https://api.x.ai/v1") -> None:
        super().__init__(api_key=api_key, base_url=base_url)


class OpenRouterBatchClient(OpenAIBatchClient):
    def __init__(self, api_key: str, base_url: str = "https://openrouter.ai/api/v1") -> None:
        super().__init__(api_key=api_key, base_url=base_url)

    def submit(
        self,
        requests: Sequence[BatchRequest],
        route: BatchRoute,
        step_context: Dict[str, Any],
    ) -> str:
        raise UnsupportedBatchProvider(
            "OpenRouter is not supported for live batch execution. Use openai, gemini, or xai. "
            "OpenRouter remains available for sync routing."
        )


class GeminiBatchClient:
    def __init__(self, api_key: str) -> None:
        from google import genai

        self._client = genai.Client(api_key=api_key)

    def submit(
        self,
        requests: Sequence[BatchRequest],
        route: BatchRoute,
        step_context: Dict[str, Any],
    ) -> str:
        inlined_requests: List[Dict[str, Any]] = []
        for req in requests:
            config: Dict[str, Any] = {"temperature": 0.1, "system_instruction": req.system_prompt}
            if req.force_json_output:
                config["response_mime_type"] = "application/json"
            inlined_requests.append(
                {
                    "model": req.model_id,
                    "contents": req.user_content,
                    "metadata": {"custom_id": req.custom_id, **req.metadata},
                    "config": config,
                }
            )
        batch_job = self._client.batches.create(
            model=route.model_id,
            src=inlined_requests,
            config={
                "display_name": f"{step_context.get('phase','')}_{step_context.get('step_id','')}",
            },
        )
        return str(getattr(batch_job, "name", "") or "")

    def poll(self, job_id: str) -> str:
        batch_job = self._client.batches.get(name=job_id)
        state = getattr(batch_job, "state", None)
        return str(state).lower() if state is not None else ""

    def fetch_results(self, job_id: str) -> List[BatchResult]:
        batch_job = self._client.batches.get(name=job_id)
        dest = getattr(batch_job, "dest", None)
        inlined_responses = getattr(dest, "inlined_responses", None) if dest is not None else None
        if not isinstance(inlined_responses, list):
            return []
        results: List[BatchResult] = []
        for row in inlined_responses:
            metadata = getattr(row, "metadata", None)
            metadata_dict = dict(metadata) if isinstance(metadata, dict) else {}
            custom_id = str(metadata_dict.get("custom_id") or "")
            response_obj = getattr(row, "response", None)
            output_text = str(getattr(response_obj, "text", "") or "")
            error_obj = getattr(row, "error", None)
            error = str(getattr(error_obj, "message", "") or "") if error_obj is not None else None
            results.append(
                BatchResult(
                    custom_id=custom_id,
                    output_text=output_text,
                    error=error,
                    meta={
                        "metadata": metadata_dict,
                        "state": str(getattr(batch_job, "state", "")),
                    },
                )
            )
        return results

    def cancel(self, job_id: str) -> None:
        self._client.batches.cancel(name=job_id)
