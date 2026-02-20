# SYSTEM PROMPT\n# Prompt C2: EventBus wiring truth surfaces

Outputs
EVENTBUS_SURFACE.json
EVENT_PRODUCERS.json
EVENT_CONSUMERS.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

SCOPE:
- any file matching tokens "event", "bus", "publish", "emit", "dispatch", "subscriber"
- adapters in shared/** and services/**

TASK 1: EVENTBUS_SURFACE.json
Extract:
- event bus interfaces/classes
- registration points
- dispatch functions
- adapter implementations (e.g., in-proc, queue, db, http)
Each item:
- item_kind: interface|impl|adapter|dispatcher|registry
- path, line_range, symbol
- excerpt <= 30 lines
- referenced_event_names[]: literal strings that look like event names (no inference)

TASK 2: EVENT_PRODUCERS.json
Extract any call sites that emit/publish events:
- producer_id
- event_name literal (if string present, else null)
- path, line_range, symbol (caller function)
- excerpt <= 12 lines
- target_bus_symbol if explicit

TASK 3: EVENT_CONSUMERS.json
Extract any call sites that subscribe/consume:
- consumer_id
- event_name literal (if string present, else null)
- handler symbol
- path, line_range, excerpt <= 20 lines

RULES:
- If event name is computed, store null and capture excerpt.
- JSON only.\n\n# USER CONTEXT\n\n--- FILE: /Users/hue/code/dopemux-mvp/src/core/config.py ---\n"""
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