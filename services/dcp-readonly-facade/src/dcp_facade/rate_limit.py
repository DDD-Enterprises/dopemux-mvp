"""Per-connector rate and concurrency limits (TP-DCP-MCP-RO-0014)."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class RateLimitConfig:
    requests_per_minute: int
    burst: int
    max_concurrent: int


@dataclass
class RateLimitDecision:
    allowed: bool
    reason: str
    code: str
    retry_after_seconds: float = 0.0


class ConnectorRateLimiter:
    """Token-bucket + concurrency gate keyed by connector_id."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._buckets: dict[str, _Bucket] = {}
        self._inflight: dict[str, int] = {}

    def allow(self, connector_id: str, config: RateLimitConfig, *, now: Optional[float] = None) -> RateLimitDecision:
        current = now if now is not None else time.monotonic()
        with self._lock:
            bucket = self._buckets.get(connector_id)
            if bucket is None:
                bucket = _Bucket(
                    tokens=float(config.burst),
                    updated_at=current,
                    rpm=config.requests_per_minute,
                    burst=config.burst,
                )
                self._buckets[connector_id] = bucket
            else:
                bucket.rpm = config.requests_per_minute
                bucket.burst = config.burst

            bucket.refill(current)
            inflight = self._inflight.get(connector_id, 0)
            if inflight >= config.max_concurrent:
                return RateLimitDecision(
                    allowed=False,
                    reason="rate limit exceeded",
                    code="max_concurrent",
                    retry_after_seconds=0.5,
                )
            if bucket.tokens < 1.0:
                return RateLimitDecision(
                    allowed=False,
                    reason="rate limit exceeded",
                    code="requests_per_minute",
                    retry_after_seconds=max(0.1, 60.0 / max(config.requests_per_minute, 1)),
                )
            bucket.tokens -= 1.0
            self._inflight[connector_id] = inflight + 1
            return RateLimitDecision(allowed=True, reason="ok", code="ok")

    def release(self, connector_id: str) -> None:
        with self._lock:
            inflight = self._inflight.get(connector_id, 0)
            if inflight <= 1:
                self._inflight.pop(connector_id, None)
            else:
                self._inflight[connector_id] = inflight - 1


class _Bucket:
    def __init__(self, *, tokens: float, updated_at: float, rpm: int, burst: int):
        self.tokens = tokens
        self.updated_at = updated_at
        self.rpm = rpm
        self.burst = burst

    def refill(self, now: float) -> None:
        elapsed = max(0.0, now - self.updated_at)
        self.updated_at = now
        rate_per_sec = max(self.rpm, 1) / 60.0
        self.tokens = min(float(self.burst), self.tokens + elapsed * rate_per_sec)
