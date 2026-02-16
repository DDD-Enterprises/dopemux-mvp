# SYSTEM PROMPT\n# Prompt C4: Trinity boundary enforcement surfaces

Outputs
TRINITY_ENFORCEMENT_SURFACE.json
REFUSAL_AND_GUARDRAILS_SURFACE.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

SCOPE:
- any file containing tokens: "trinity", "boundary", "authority", "refusal", "guard", "policy"
- router/instruction injection code paths if present
- shared enforcement utilities (validators, gates)

TASK 1: TRINITY_ENFORCEMENT_SURFACE.json
Extract:
- boundary checks between planes (pm/memory/orchestrator/mcp/hooks/etc.)
- enforcement functions/classes
- any allowlist/denylist structures
Each item:
- path, line_range, symbol
- excerpt <= 35 lines
- referenced_planes[]: literal strings that look like plane names if present

TASK 2: REFUSAL_AND_GUARDRAILS_SURFACE.json
Extract:
- refusal artifacts creation
- policy evaluation
- schema validation calls
- sanitization/redaction calls
Each item:
- guard_kind: refusal|policy|validation|redaction|other
- path, line_range, symbol, excerpt <= 20 lines

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