"""Metadata-only structured logging callbacks for Dopemux-managed LiteLLM instances."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from litellm.integrations.custom_logger import CustomLogger

TRACE_HEADER_NAME = "X-Dopemux-Trace-Id"
LITELLM_COMPONENT_NAME = "dopemux_litellm_proxy"
LOGGING_ENABLED_ENV = "DOPEMUX_LITELLM_STRUCTURED_LOGGING"
LOG_PATH_ENV = "DOPEMUX_LITELLM_JSONL_LOG_PATH"
INSTANCE_ID_ENV = "DOPEMUX_LITELLM_INSTANCE_ID"
FREEFLOW_METADATA_KEYS = (
    "route_decision_id",
    "freeflow_provider",
    "freeflow_model",
    "quota_bucket",
    "sensitivity_class",
    "selected_fallback_tier",
    "route_reason",
)


def _env_enabled(name: str, default: bool = True) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off"}


def _new_span_id() -> str:
    return uuid.uuid4().hex[:16]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {
            str(key): _safe_value(subvalue)
            for key, subvalue in value.items()
            if subvalue is not None
        }
    if isinstance(value, (list, tuple)):
        return [_safe_value(item) for item in value if item is not None]
    return str(value)


def _log_path() -> Optional[Path]:
    raw = str(os.getenv(LOG_PATH_ENV, "") or "").strip()
    if not raw:
        return None
    return Path(raw)


def _write_event(payload: Dict[str, Any]) -> None:
    if not _env_enabled(LOGGING_ENABLED_ENV, default=True):
        return
    target = _log_path()
    if target is None:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    sanitized = {key: value for key, value in payload.items() if value is not None}
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(sanitized, ensure_ascii=True, sort_keys=True) + "\n")


def _as_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if hasattr(value, "model_dump"):
        try:
            dumped = value.model_dump()
            return dumped if isinstance(dumped, dict) else {}
        except Exception:
            return {}
    return {}


def _get_metadata(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    for key in ("metadata", "litellm_metadata"):
        candidate = kwargs.get(key)
        if isinstance(candidate, dict):
            return candidate
    return {}


def _get_model_info(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    return _as_dict(kwargs.get("model_info"))


def _extract_trace_id(kwargs: Dict[str, Any]) -> str:
    metadata = _get_metadata(kwargs)
    trace_id = str(metadata.get("trace_id") or "").strip()
    if trace_id:
        return trace_id
    extra_headers = kwargs.get("extra_headers")
    if isinstance(extra_headers, dict):
        trace_id = str(extra_headers.get(TRACE_HEADER_NAME) or "").strip()
        if trace_id:
            return trace_id
    return uuid.uuid4().hex


def _extract_usage(response_obj: Any) -> Dict[str, Optional[int]]:
    usage = getattr(response_obj, "usage", None)
    if usage is None:
        return {}
    return {
        "tokens_prompt": getattr(usage, "prompt_tokens", None),
        "tokens_completion": getattr(usage, "completion_tokens", None),
        "tokens_total": getattr(usage, "total_tokens", None),
        "tokens_reasoning": getattr(usage, "reasoning_tokens", None),
        "tokens_cached": getattr(usage, "cached_tokens", None),
    }


def _base_event(event_type: str, trace_id: str, **fields: Any) -> Dict[str, Any]:
    return {
        "ts": _now_iso(),
        "component": LITELLM_COMPONENT_NAME,
        "event_type": event_type,
        "trace_id": trace_id,
        "span_id": fields.pop("span_id", None) or _new_span_id(),
        "instance_id": os.getenv(INSTANCE_ID_ENV),
        **_safe_value(fields),
    }


def _freeflow_metadata(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    metadata = _get_metadata(kwargs)
    model_info = _get_model_info(kwargs)
    merged = {key: model_info.get(key) for key in FREEFLOW_METADATA_KEYS}
    merged.update(
        {
            key: metadata.get(key)
            for key in FREEFLOW_METADATA_KEYS
            if metadata.get(key) is not None
        }
    )
    if model_info.get("freeflow_bucket_id") and merged.get("quota_bucket") is None:
        merged["quota_bucket"] = model_info["freeflow_bucket_id"]
    return {key: value for key, value in merged.items() if value is not None}


def _extract_message_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        parts = []
        for key in ("content", "text", "input", "arguments"):
            if key in value:
                parts.append(_extract_message_text(value[key]))
        return "\n".join(part for part in parts if part)
    if isinstance(value, (list, tuple)):
        return "\n".join(_extract_message_text(item) for item in value)
    return str(value)


def _estimate_input_tokens(kwargs: Dict[str, Any], metadata: Dict[str, Any]) -> int:
    from dopemux.freeflow import estimate_text_tokens

    explicit = metadata.get("estimated_input_tokens")
    if explicit is not None:
        try:
            return max(0, int(explicit))
        except (TypeError, ValueError):
            pass
    return estimate_text_tokens(_extract_message_text(kwargs.get("messages")))


def _estimate_output_tokens(
    metadata: Dict[str, Any], model_info: Dict[str, Any]
) -> int:
    explicit = metadata.get("estimated_output_tokens")
    if explicit is None:
        explicit = model_info.get("freeflow_default_output_tokens", 1024)
    try:
        return max(0, int(explicit))
    except (TypeError, ValueError):
        return 1024


def _extract_response_headers(response_obj: Any) -> Dict[str, Any]:
    for key in ("headers", "response_headers"):
        candidate = getattr(response_obj, key, None)
        if isinstance(candidate, dict):
            return candidate
    hidden = getattr(response_obj, "_hidden_params", None)
    if isinstance(hidden, dict):
        for key in ("headers", "response_headers"):
            candidate = hidden.get(key)
            if isinstance(candidate, dict):
                return candidate
    return {}


def _extract_status_code(response_obj: Any) -> Optional[int]:
    for key in ("status_code", "http_status", "http_status_code"):
        candidate = getattr(response_obj, key, None)
        if candidate is not None:
            try:
                return int(candidate)
            except (TypeError, ValueError):
                pass
    hidden = getattr(response_obj, "_hidden_params", None)
    if isinstance(hidden, dict):
        for key in ("status_code", "http_status", "http_status_code"):
            candidate = hidden.get(key)
            if candidate is not None:
                try:
                    return int(candidate)
                except (TypeError, ValueError):
                    pass
    text = str(response_obj or "")
    if "429" in text:
        return 429
    if "402" in text:
        return 402
    if "401" in text or "403" in text:
        return 401
    return None


def _record_freeflow_usage(
    kwargs: Dict[str, Any],
    response_obj: Any,
    *,
    status: str,
) -> None:
    from dopemux.freeflow import FreeflowQuotaExceeded, FreeflowQuotaLedger

    if isinstance(response_obj, FreeflowQuotaExceeded):
        return
    metadata = _get_metadata(kwargs)
    freeflow = _freeflow_metadata(kwargs)
    provider = freeflow.get("freeflow_provider")
    bucket_id = freeflow.get("quota_bucket")
    model_name = freeflow.get("freeflow_model") or metadata.get("deployment_model_name")
    model_id = str(kwargs.get("model") or "")
    if not provider or not bucket_id or not model_name:
        return

    usage = _extract_usage(response_obj)
    input_tokens = usage.get("tokens_prompt")
    output_tokens = usage.get("tokens_completion")
    if input_tokens is None:
        input_tokens = metadata.get("estimated_input_tokens") or 0
    if output_tokens is None:
        output_tokens = metadata.get("estimated_output_tokens") or 0

    ledger = FreeflowQuotaLedger()
    ledger.record_usage(
        provider=str(provider),
        model_name=str(model_name),
        model_id=model_id,
        bucket_id=str(bucket_id),
        input_tokens=int(input_tokens or 0),
        output_tokens=int(output_tokens or 0),
        route_decision_id=metadata.get("route_decision_id"),
        status=status,
        metadata={"trace_id": metadata.get("trace_id")},
    )

    status_code = _extract_status_code(response_obj)
    if status_code is not None:
        ledger.ingest_response_headers(
            provider=str(provider),
            model_name=str(model_name),
            bucket_id=str(bucket_id),
            headers=_extract_response_headers(response_obj),
            status_code=status_code,
        )


def emit_startup_event(*, log_path: Optional[str] = None, **fields: Any) -> None:
    payload = _base_event("proxy_startup", trace_id=uuid.uuid4().hex, **fields)
    if log_path:
        target = Path(log_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        sanitized = {key: value for key, value in payload.items() if value is not None}
        with target.open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(sanitized, ensure_ascii=True, sort_keys=True) + "\n"
            )
        return
    _write_event(payload)


class DopemuxLiteLLMTraceLogger(CustomLogger):
    """LiteLLM callback hook that records metadata-only request lifecycle events."""

    def __init__(self) -> None:
        super().__init__(turn_off_message_logging=True)

    async def async_pre_call_deployment_hook(
        self, kwargs: Dict[str, Any], call_type: Optional[Any]
    ) -> Optional[Dict[str, Any]]:
        metadata = dict(_get_metadata(kwargs))
        trace_id = str(metadata.get("trace_id") or "").strip() or uuid.uuid4().hex
        metadata["trace_id"] = trace_id
        model_info = _get_model_info(kwargs)
        freeflow = _freeflow_metadata({"metadata": metadata, "model_info": model_info})
        if freeflow.get("freeflow_provider"):
            from dopemux.freeflow import (
                FreeflowQuotaExceeded,
                FreeflowQuotaLedger,
                LOCAL_PROVIDERS,
                NON_SENSITIVE_CLASS,
                PROVIDER_CATALOG,
                normalize_sensitivity,
            )

            provider = str(freeflow["freeflow_provider"])
            model_name = str(
                freeflow.get("freeflow_model")
                or metadata.get("deployment_model_name")
                or kwargs.get("model")
                or ""
            )
            bucket_id = str(freeflow.get("quota_bucket") or f"{provider}:{model_name}")
            sensitivity = normalize_sensitivity(
                metadata.get("sensitivity_class")
                or model_info.get("sensitivity_class")
                or NON_SENSITIVE_CLASS
            )
            estimated_input_tokens = _estimate_input_tokens(kwargs, metadata)
            estimated_output_tokens = _estimate_output_tokens(metadata, model_info)
            metadata.update(freeflow)
            metadata.update(
                {
                    "freeflow_provider": provider,
                    "freeflow_model": model_name,
                    "quota_bucket": bucket_id,
                    "sensitivity_class": sensitivity,
                    "estimated_input_tokens": estimated_input_tokens,
                    "estimated_output_tokens": estimated_output_tokens,
                }
            )
            ledger = FreeflowQuotaLedger()
            decision = {
                "decision": "selected",
                "reason": "strict_free_pre_call_admitted",
                "sensitivity_class": sensitivity,
                "provider": provider,
                "model_name": model_name,
                "model_id": str(kwargs.get("model") or ""),
                "estimated_input_tokens": estimated_input_tokens,
                "estimated_output_tokens": estimated_output_tokens,
                "metadata": {
                    "trace_id": trace_id,
                    "quota_bucket": bucket_id,
                    "call_type": str(call_type) if call_type is not None else None,
                },
            }
            limits = _as_dict(model_info.get("freeflow_limits")) or _as_dict(
                PROVIDER_CATALOG.get(provider, {}).get("limits")
            )
            if sensitivity == "sensitive" and provider not in LOCAL_PROVIDERS:
                decision["decision"] = "blocked"
                decision["reason"] = "sensitive_hosted_route_blocked"
                metadata["route_reason"] = decision["reason"]
                metadata["route_decision_id"] = ledger.record_route_decision(decision)
                kwargs["metadata"] = metadata
                raise FreeflowQuotaExceeded(decision["reason"])

            quota = ledger.check_quota(
                provider,
                model_name,
                bucket_id,
                limits,
                estimated_input_tokens,
                estimated_output_tokens,
            )
            if not quota.allowed:
                decision["decision"] = "blocked"
                decision["reason"] = quota.reason
                metadata["route_reason"] = quota.reason
                metadata["route_decision_id"] = ledger.record_route_decision(decision)
                kwargs["metadata"] = metadata
                raise FreeflowQuotaExceeded(quota.reason, quota.reset_at)

            metadata["route_reason"] = str(
                metadata.get("route_reason") or decision["reason"]
            )
            metadata["route_decision_id"] = ledger.record_route_decision(decision)
        kwargs["metadata"] = metadata

        extra_headers = dict(kwargs.get("extra_headers") or {})
        extra_headers.setdefault(TRACE_HEADER_NAME, trace_id)
        kwargs["extra_headers"] = extra_headers
        return kwargs

    def log_pre_api_call(
        self, model: str, messages: Any, kwargs: Dict[str, Any]
    ) -> None:
        trace_id = _extract_trace_id(kwargs)
        metadata = _get_metadata(kwargs)
        _write_event(
            _base_event(
                "proxy_request_started",
                trace_id=trace_id,
                model=model,
                provider=str(
                    kwargs.get("custom_llm_provider") or kwargs.get("provider") or ""
                ),
                parent_span_id=metadata.get("parent_span_id"),
                route=metadata.get("model_group"),
                status="started",
                api_base=kwargs.get("api_base"),
                request_id=metadata.get("request_id"),
                **_freeflow_metadata(kwargs),
            )
        )

    def log_success_event(
        self, kwargs: Dict[str, Any], response_obj: Any, start_time: Any, end_time: Any
    ) -> None:
        _record_freeflow_usage(kwargs, response_obj, status="completed")
        trace_id = _extract_trace_id(kwargs)
        metadata = _get_metadata(kwargs)
        usage = _extract_usage(response_obj)
        latency_ms = None
        if start_time is not None and end_time is not None:
            latency_ms = int((end_time - start_time).total_seconds() * 1000)
        _write_event(
            _base_event(
                "proxy_request_completed",
                trace_id=trace_id,
                model=str(
                    getattr(response_obj, "model", None) or kwargs.get("model") or ""
                ),
                provider=str(
                    kwargs.get("custom_llm_provider") or kwargs.get("provider") or ""
                ),
                parent_span_id=metadata.get("parent_span_id"),
                route=metadata.get("model_group"),
                status="completed",
                latency_ms=latency_ms,
                finish_reason=(
                    getattr(
                        getattr(response_obj, "choices", [None])[0],
                        "finish_reason",
                        None,
                    )
                    if getattr(response_obj, "choices", None)
                    else None
                ),
                upstream_request_id=str(getattr(response_obj, "id", "") or "") or None,
                request_id=metadata.get("request_id"),
                **_freeflow_metadata(kwargs),
                **usage,
            )
        )

    def log_failure_event(
        self, kwargs: Dict[str, Any], response_obj: Any, start_time: Any, end_time: Any
    ) -> None:
        _record_freeflow_usage(kwargs, response_obj, status="failed")
        trace_id = _extract_trace_id(kwargs)
        metadata = _get_metadata(kwargs)
        latency_ms = None
        if start_time is not None and end_time is not None:
            latency_ms = int((end_time - start_time).total_seconds() * 1000)
        _write_event(
            _base_event(
                "proxy_request_failed",
                trace_id=trace_id,
                model=str(kwargs.get("model") or ""),
                provider=str(
                    kwargs.get("custom_llm_provider") or kwargs.get("provider") or ""
                ),
                parent_span_id=metadata.get("parent_span_id"),
                route=metadata.get("model_group"),
                status="failed",
                latency_ms=latency_ms,
                error_type=(
                    type(response_obj).__name__ if response_obj is not None else None
                ),
                error_message_excerpt=(
                    str(response_obj)[:500] if response_obj is not None else None
                ),
                request_id=metadata.get("request_id"),
                **_freeflow_metadata(kwargs),
            )
        )
