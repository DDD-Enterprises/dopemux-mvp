# SYSTEM PROMPT\n# Prompt C5: TaskX integration surfaces

Outputs
TASKX_INTEGRATION_SURFACE.json
TASKX_PACKET_IO_HINTS.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

SCOPE:
- src/** containing "taskx"
- docs are in D; here we only do code
- .taskx surfaces are Phase A/H; here link any references

TASK 1: TASKX_INTEGRATION_SURFACE.json
Extract:
- code that calls taskx CLI
- code that reads/writes task packets
- operator instruction injection/compilation calls (if present)
Each item:
- item_kind: cli_invocation|packet_read|packet_write|instruction_compile|other
- path, line_range, symbol
- excerpt <= 35 lines

TASK 2: TASKX_PACKET_IO_HINTS.json
Extract literal packet schema hints:
- json keys referenced (e.g., "objective","scope","acceptance_criteria")
- file naming conventions in code
For each hint:
- path, line_range, excerpt <= 12 lines
- keys[] or patterns[]

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