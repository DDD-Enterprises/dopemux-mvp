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


def _get_metadata(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    for key in ("metadata", "litellm_metadata"):
        candidate = kwargs.get(key)
        if isinstance(candidate, dict):
            return candidate
    return {}


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


def emit_startup_event(*, log_path: Optional[str] = None, **fields: Any) -> None:
    payload = _base_event("proxy_startup", trace_id=uuid.uuid4().hex, **fields)
    if log_path:
        target = Path(log_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        sanitized = {key: value for key, value in payload.items() if value is not None}
        with target.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(sanitized, ensure_ascii=True, sort_keys=True) + "\n")
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
        kwargs["metadata"] = metadata

        extra_headers = dict(kwargs.get("extra_headers") or {})
        extra_headers.setdefault(TRACE_HEADER_NAME, trace_id)
        kwargs["extra_headers"] = extra_headers
        return kwargs

    def log_pre_api_call(self, model: str, messages: Any, kwargs: Dict[str, Any]) -> None:
        trace_id = _extract_trace_id(kwargs)
        metadata = _get_metadata(kwargs)
        _write_event(
            _base_event(
                "proxy_request_started",
                trace_id=trace_id,
                model=model,
                provider=str(kwargs.get("custom_llm_provider") or kwargs.get("provider") or ""),
                parent_span_id=metadata.get("parent_span_id"),
                route=metadata.get("model_group"),
                status="started",
                api_base=kwargs.get("api_base"),
                request_id=metadata.get("request_id"),
            )
        )

    def log_success_event(
        self, kwargs: Dict[str, Any], response_obj: Any, start_time: Any, end_time: Any
    ) -> None:
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
                model=str(getattr(response_obj, "model", None) or kwargs.get("model") or ""),
                provider=str(kwargs.get("custom_llm_provider") or kwargs.get("provider") or ""),
                parent_span_id=metadata.get("parent_span_id"),
                route=metadata.get("model_group"),
                status="completed",
                latency_ms=latency_ms,
                finish_reason=getattr(getattr(response_obj, "choices", [None])[0], "finish_reason", None)
                if getattr(response_obj, "choices", None)
                else None,
                upstream_request_id=str(getattr(response_obj, "id", "") or "") or None,
                request_id=metadata.get("request_id"),
                **usage,
            )
        )

    def log_failure_event(
        self, kwargs: Dict[str, Any], response_obj: Any, start_time: Any, end_time: Any
    ) -> None:
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
                provider=str(kwargs.get("custom_llm_provider") or kwargs.get("provider") or ""),
                parent_span_id=metadata.get("parent_span_id"),
                route=metadata.get("model_group"),
                status="failed",
                latency_ms=latency_ms,
                error_type=type(response_obj).__name__ if response_obj is not None else None,
                error_message_excerpt=str(response_obj)[:500] if response_obj is not None else None,
                request_id=metadata.get("request_id"),
            )
        )
