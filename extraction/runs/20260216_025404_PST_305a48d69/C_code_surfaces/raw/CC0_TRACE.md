# SYSTEM PROMPT\n# Prompt C0: Code inventory + partition plan (mandatory)

Outputs
CODE_INVENTORY.json
CODE_PARTITION_PLAN.json
ROLE: Mechanical indexer. No reasoning. JSON only. ASCII only.

SCOPE:
- src/**
- services/**
- shared/**
- tools/**
- scripts/**
- dashboard/**, ui-dashboard-backend/** (if code)
- plugins/**, components/** (if code)

OUTPUT 1: CODE_INVENTORY.json
For each file:
- path
- size_bytes
- file_kind by extension (py|ts|js|sh|yaml|toml|md|sql|other)
- sha256 if <= 1MB else null
- first_nonempty_line
- contains_tokens[] match from:
  ["event","bus","publish","emit","consume","subscriber","producer",
   "dope-memory","chronicle","sqlite","postgres","mirror","schema","migration","trigger","ttl",
   "taskx","packet","orchestrator","runner","workflow","hook","mcp",
   "determinism","idempotent","uuid","random","async","thread","queue","retry",
   "trinity","boundary","refusal","guard","policy","allowlist","denylist",
   "typer","click","fastapi","flask","uvicorn","gunicorn"]

OUTPUT 2: CODE_PARTITION_PLAN.json
Create deterministic partitions with explicit path lists:
C1_SERVICE_ENTRYPOINTS
C2_EVENTBUS_WIRING
C3_DOPE_MEMORY_SURFACES
C4_TRINITY_ENFORCEMENT_SURFACES
C5_TASKX_INTEGRATION_SURFACES
C6_WORKFLOW_RUNNERS_AND_COORDINATION
C7_API_AND_UI_BACKENDS
C8_DETERMINISM_IDEMPOTENCY_CONCURRENCY_SCANS

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