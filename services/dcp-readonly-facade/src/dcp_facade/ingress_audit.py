"""Structured redacted audit events for the loopback ingress (TP-0014)."""

from __future__ import annotations

import json
import threading
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Optional

from .redaction import redact_value


@dataclass
class IngressAuditEvent:
    ts: float
    decision: str
    path: str
    method: str
    connector_id: Optional[str] = None
    credential_fingerprint: Optional[str] = None
    audit_label: Optional[str] = None
    status_code: int = 0
    reason: str = ""
    client_host: Optional[str] = None
    redactions: list[str] = field(default_factory=list)

    def to_public_dict(self) -> dict[str, Any]:
        raw = asdict(self)
        clean, cats = redact_value(raw, [])
        if isinstance(clean, dict):
            clean["redactions"] = sorted(set(list(clean.get("redactions") or []) + cats))
            return clean
        return {"event": clean, "redactions": cats}


class IngressAuditLog:
    """In-memory bounded audit log for tests and local operators."""

    def __init__(self, *, max_events: int = 1000):
        self._max = max(1, max_events)
        self._events: list[IngressAuditEvent] = []
        self._lock = threading.Lock()

    def record(self, event: IngressAuditEvent) -> IngressAuditEvent:
        # Never retain raw Authorization-like material in reason/path.
        clean_reason, cats = redact_value(event.reason, [])
        event.reason = str(clean_reason)
        event.redactions = sorted(set(event.redactions + cats))
        with self._lock:
            self._events.append(event)
            if len(self._events) > self._max:
                self._events = self._events[-self._max :]
        return event

    def events(self) -> list[IngressAuditEvent]:
        with self._lock:
            return list(self._events)

    def clear(self) -> None:
        with self._lock:
            self._events.clear()

    def dump_json_lines(self) -> str:
        return "\n".join(json.dumps(ev.to_public_dict(), sort_keys=True) for ev in self.events())


def now_ts() -> float:
    return time.time()
