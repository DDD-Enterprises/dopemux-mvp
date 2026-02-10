"""Shared logging utilities for Dopemux services and scripts."""

from __future__ import annotations

import contextvars
import json
import logging
import os
import socket
import sys
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional

try:
    from prometheus_client import Counter

    LOG_RECORDS_TOTAL = Counter(
        "dopemux_log_records_total",
        "Total number of log records emitted by Dopemux services.",
        ["service", "level", "logger"],
    )
except Exception:  # pragma: no cover - optional dependency path
    LOG_RECORDS_TOTAL = None


_STANDARD_RECORD_ATTRS = set(logging.makeLogRecord({}).__dict__.keys())
_LOG_CONTEXT: contextvars.ContextVar[Optional[Dict[str, Any]]] = (
    contextvars.ContextVar("dopemux_log_context", default=None)
)
_DOGSTATSD_CLIENT: Optional["_DogStatsdClient"] = None


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _safe_label(value: Any, fallback: str = "unknown") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text or fallback


class _DogStatsdClient:
    """Small UDP DogStatsD client with best-effort fire-and-forget semantics."""

    def __init__(self, host: str, port: int, prefix: str):
        self._host = host
        self._port = port
        self._prefix = prefix.strip(".")
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def emit_count(self, metric: str, value: int, tags: Dict[str, str]) -> None:
        metric_name = metric if not self._prefix else f"{self._prefix}.{metric}"
        payload = f"{metric_name}:{int(value)}|c"
        if tags:
            tag_list = [f"{k}:{v}" for k, v in tags.items()]
            payload = f"{payload}|#{','.join(tag_list)}"
        try:
            self._socket.sendto(payload.encode("utf-8"), (self._host, self._port))
        except OSError:
            # Never fail application logging because metrics emission fails.
            pass


def _init_dogstatsd_client() -> Optional[_DogStatsdClient]:
    enabled = _env_flag("DOPMUX_LOG_DATADOG_ENABLED", default=False) or _env_flag(
        "DD_LOGS_ENABLED",
        default=False,
    )
    if not enabled:
        return None

    host = os.getenv("DD_AGENT_HOST", "127.0.0.1")
    port = int(os.getenv("DD_DOGSTATSD_PORT", "8125"))
    prefix = os.getenv("DOPMUX_LOG_STATSD_PREFIX", "dopemux")
    return _DogStatsdClient(host=host, port=port, prefix=prefix)


def current_log_context() -> Dict[str, Any]:
    """Return the active request/task context for logging."""
    return dict(_LOG_CONTEXT.get() or {})


def bind_log_context(**fields: Any) -> contextvars.Token:
    """Bind context fields (request/task/workspace identifiers) to current context."""
    context = current_log_context()
    context.update({k: v for k, v in fields.items() if v is not None})
    return _LOG_CONTEXT.set(context)


def clear_log_context() -> contextvars.Token:
    """Clear all bound log context values."""
    return _LOG_CONTEXT.set({})


def reset_log_context(token: contextvars.Token) -> None:
    """Restore previous log context using the token returned by bind operations."""
    _LOG_CONTEXT.reset(token)


class _ContextFilter(logging.Filter):
    """Inject bound context values into every log record."""

    def __init__(self, service_name: str):
        super().__init__()
        self._service_name = service_name

    def filter(self, record: logging.LogRecord) -> bool:
        context = current_log_context()
        service = _safe_label(context.get("service", self._service_name))
        request_id = _safe_label(context.get("request_id"), fallback="-")
        task_packet_id = _safe_label(context.get("task_packet_id"), fallback="-")
        workspace_id = _safe_label(context.get("workspace_id"), fallback="-")

        record.service = service
        record.request_id = request_id
        record.task_packet_id = task_packet_id
        record.workspace_id = workspace_id

        for key, value in context.items():
            if key not in record.__dict__:
                setattr(record, key, value)

        if LOG_RECORDS_TOTAL is not None:
            LOG_RECORDS_TOTAL.labels(
                service=service,
                level=record.levelname,
                logger=record.name,
            ).inc()

        if _DOGSTATSD_CLIENT is not None:
            tags = {
                "service": service,
                "level": record.levelname.lower(),
                "logger": record.name,
            }
            _DOGSTATSD_CLIENT.emit_count("log_records_total", 1, tags)
            if record.levelno >= logging.ERROR:
                _DOGSTATSD_CLIENT.emit_count("log_errors_total", 1, tags)

        return True


class _TextFormatter(logging.Formatter):
    """Plain text formatter with durable context fields."""

    def format(self, record: logging.LogRecord) -> str:
        record.service = getattr(record, "service", "unknown")
        record.request_id = getattr(record, "request_id", "-")
        record.task_packet_id = getattr(record, "task_packet_id", "-")
        record.workspace_id = getattr(record, "workspace_id", "-")
        return super().format(record)


class _JsonFormatter(logging.Formatter):
    """Structured JSON formatter for machine-friendly log ingestion."""

    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": getattr(record, "service", "unknown"),
            "request_id": getattr(record, "request_id", "-"),
            "task_packet_id": getattr(record, "task_packet_id", "-"),
            "workspace_id": getattr(record, "workspace_id", "-"),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process": record.process,
            "thread": record.threadName,
        }

        for key, value in record.__dict__.items():
            if key in _STANDARD_RECORD_ATTRS:
                continue
            payload.setdefault(key, value)

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def configure_logging(
    service_name: str,
    *,
    level: Optional[str] = None,
    json_logs: Optional[bool] = None,
    force: bool = True,
) -> logging.Logger:
    """
    Configure root logging with service context and optional structured output.

    Environment overrides:
    - LOG_LEVEL
    - LOG_FORMAT=json
    - LOG_JSON=true
    - DOPMUX_LOG_DATADOG_ENABLED=true
    """
    global _DOGSTATSD_CLIENT

    resolved_level_name = (level or os.getenv("LOG_LEVEL", "INFO")).upper()
    resolved_level = getattr(logging, resolved_level_name, logging.INFO)

    if json_logs is None:
        log_format = os.getenv("LOG_FORMAT", "").strip().lower()
        json_logs = _env_flag("LOG_JSON", default=False) or log_format == "json"

    if _DOGSTATSD_CLIENT is None:
        _DOGSTATSD_CLIENT = _init_dogstatsd_client()

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(_ContextFilter(service_name))
    if json_logs:
        handler.setFormatter(_JsonFormatter())
    else:
        handler.setFormatter(
            _TextFormatter(
                "%(asctime)s %(levelname)s %(service)s %(name)s "
                "rid=%(request_id)s task=%(task_packet_id)s "
                "workspace=%(workspace_id)s %(message)s"
            )
        )

    root_logger = logging.getLogger()
    if force:
        for existing in list(root_logger.handlers):
            root_logger.removeHandler(existing)
    root_logger.addHandler(handler)
    root_logger.setLevel(resolved_level)

    bind_log_context(service=service_name)
    return logging.getLogger(service_name)


try:
    from starlette.middleware.base import BaseHTTPMiddleware
except Exception:  # pragma: no cover - optional runtime dependency
    BaseHTTPMiddleware = object  # type: ignore[misc,assignment]


class RequestIDMiddleware(BaseHTTPMiddleware):  # type: ignore[misc]
    """Attach and propagate an `X-Request-ID` across each HTTP request."""

    def __init__(self, app: Any, header_name: str = "X-Request-ID"):
        super().__init__(app)  # type: ignore[arg-type]
        self.header_name = header_name
        self.logger = logging.getLogger(__name__)

    async def dispatch(self, request: Any, call_next: Any) -> Any:
        request_id = request.headers.get(self.header_name) or str(uuid.uuid4())
        token = bind_log_context(request_id=request_id)
        try:
            response = await call_next(request)
        except Exception:
            self.logger.exception(
                "Unhandled exception while processing request",
                extra={
                    "method": getattr(request, "method", "unknown"),
                    "path": str(getattr(getattr(request, "url", None), "path", "/")),
                },
            )
            raise
        finally:
            reset_log_context(token)

        response.headers[self.header_name] = request_id
        return response


def bind_task_packet(task_packet_id: str, workspace_id: Optional[str] = None) -> None:
    """Convenience helper for long-running debug packet collection jobs."""
    bind_log_context(task_packet_id=task_packet_id, workspace_id=workspace_id)


def enrich_logger(logger: logging.Logger, **fields: Any) -> logging.LoggerAdapter:
    """Return a logger adapter that injects static structured fields."""
    return logging.LoggerAdapter(logger, fields)


def normalize_log_level_names(levels: Iterable[str]) -> Dict[str, str]:
    """Normalize various level aliases into canonical names."""
    mapping = {
        "warn": "warning",
        "fatal": "critical",
    }
    normalized: Dict[str, str] = {}
    for level in levels:
        key = level.strip().lower()
        normalized[level] = mapping.get(key, key)
    return normalized


__all__ = [
    "RequestIDMiddleware",
    "bind_log_context",
    "bind_task_packet",
    "clear_log_context",
    "configure_logging",
    "current_log_context",
    "enrich_logger",
    "normalize_log_level_names",
    "reset_log_context",
]
