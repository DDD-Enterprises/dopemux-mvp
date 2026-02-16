# SYSTEM PROMPT\n# Prompt C3: Dope-Memory surfaces

Outputs
DOPE_MEMORY_CODE_SURFACE.json
DOPE_MEMORY_SCHEMAS.json
DOPE_MEMORY_DB_WRITES.json
MIGRATIONS_SURFACE.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

SCOPE:
- services/**working-memory-assistant**/** (or any memory service folder)
- docs/spec/dope-memory is docs (handled in D), here is code only
- any module containing chronicle, mirror, sqlite, postgres, schema, migration, ttl

TASK 1: DOPE_MEMORY_CODE_SURFACE.json
Extract:
- store classes (SQLite/Postgres adapters)
- ingestion functions
- search/query functions
- mirror sync functions
- retention/ttl logic locations
Each item:
- item_kind: store|adapter|ingest|query|sync|retention|index
- path, line_range, symbol, excerpt <= 35 lines

TASK 2: DOPE_MEMORY_SCHEMAS.json
Extract schema definitions:
- .sql files: CREATE TABLE/INDEX/TRIGGER statements (full statement)
- inline SQL strings if they contain CREATE/ALTER
For each schema object:
- object_kind: table|index|trigger|view|migration
- name
- path, line_range
- statement (string)
JSON only.

TASK 3: DOPE_MEMORY_DB_WRITES.json
Extract write paths:
- INSERT/UPDATE/DELETE statements or ORM calls if detectable
- file path, line_range, symbol, excerpt <= 12 lines
- write_kind: insert|update|delete|upsert|unknown
- table_name if literal else null

TASK 4: MIGRATIONS_SURFACE.json
Extract migration runners and version tracking:
- path, line_range, symbol
- migration file lists if present
- schema_migrations table usage if present
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