# SYSTEM PROMPT\n# Prompt C8: Determinism / idempotency / concurrency location scans

Outputs
DETERMINISM_RISK_LOCATIONS.json
IDEMPOTENCY_RISK_LOCATIONS.json
CONCURRENCY_RISK_LOCATIONS.json
SECRETS_RISK_LOCATIONS.json (location-only)
ROLE: Mechanical scanner. No reasoning. JSON only. ASCII only.

Scan code for risk locations:

DETERMINISM:
- random, secrets, uuid
- datetime.now, time.time
- unordered iteration over dict/set without sorting
- implicit locale/timezone conversions

IDEMPOTENCY:
- UPDATE/DELETE on evidence/log tables
- retries without idempotency keys
- "upsert" behavior without stable keys
- side effects without ledger write

CONCURRENCY:
- async/await, threading, multiprocessing
- queue usage, background tasks
- locks, semaphores
- retries/backoff

SECRETS:
- reading env vars with token/key/secret names
- loading .env, secret files
- printing config values

For each hit:
- risk_type
- path, line_range
- excerpt <= 7 lines
- matched_token

JSON only.\n\n# USER CONTEXT\n\n--- FILE: /Users/hue/code/dopemux-mvp/src/core/config.py ---\n"""
Simple Config class for backward compatibility.

This provides a simple interface for the Leantime bridge while
maintaining compatibility with the ConfigManager.
"""

from typing import Any, Dict, Optional


class Config:
    """Simple configuration class."""

    def __init__(self, data: Optional[Dict[str, Any]] = None):
        self.data = data or {}

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        if "." not in key:
            return self.data.get(key, default)

        current = self.data
        for part in key.split('.'):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
        return current

    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        if "." not in key:
            self.data[key] = value
            return

        current = self.data
        parts = key.split('.')
        for part in parts[:-1]:
            current = current.setdefault(part, {})
        current[parts[-1]] = value

    def update(self, other: Dict[str, Any]) -> None:
        """Update configuration with another dictionary."""
        self.data.update(other)
\n\n--- FILE: /Users/hue/code/dopemux-mvp/src/core/monitoring.py ---\n"""
Metrics collection for Dopemux operations.

Provides monitoring and metrics collection capabilities for
ADHD optimization and integration tracking.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class MetricRecord:
    """Individual metric record."""

    service: str
    method: str
    status: str
    timestamp: datetime = field(default_factory=datetime.now)
    duration: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class MetricsCollector:
    """Collects and tracks... [truncated for trace]