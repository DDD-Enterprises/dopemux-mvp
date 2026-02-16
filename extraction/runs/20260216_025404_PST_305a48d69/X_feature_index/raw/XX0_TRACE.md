# SYSTEM PROMPT\n# Phase X (GPT-5.2): Feature index + contracts catalog (developer gold)

## Purpose
A lot of your repo power is buried in instruction files, configs, and “workflow glue”. This phase builds a contract catalog:
commands
events
schemas
config knobs
instruction file levers
services + ports
workflows and artifacts

## Output artifacts
FEATURE_INDEX.json (developer queryable)
CONTRACT_CATALOG.md (human)
WORKFLOW_CATALOG.md (human)

## Prompt
ROLE: Systems cataloger.
SCOPE: Produce a developer-queryable feature index and contract catalog.
INPUTS: Phase A/H/D/C normalized JSONs + Phase R outputs. No scanning.

OUTPUTS:
1) FEATURE_INDEX.json
   - keys:
     - features[]
     - each feature:
       - id
       - name
       - planes[]
       - implemented_status (implemented|planned|partial|unknown)
       - evidence_refs[]
       - surfaces: {code_paths[], repo_ctrl_paths[], home_ctrl_paths[], doc_paths[]}
       - commands[] (cli/tools/scripts)
       - events[] (producer/consumer/topic)
       - stores[] (sqlite/postgres/tables)
       - configs[] (key paths only)
       - instruction_levers[] (instruction file names/blocks)
       - tests[] (if known)
       - risks[] (from Phase R risk ledger)

2) CONTRACT_CATALOG.md
   - tables: events, schemas, CLI/API surfaces, config levers, instruction levers
   - each entry includes citations and location

3) WORKFLOW_CATALOG.md
   - list workflows with triggers, steps, events, stores, outputs, and acceptance checks

RULES:
- Cite every entry.
- No invention.
- Deterministic ordering by id.
\n\n# USER CONTEXT\n\n--- FILE: /Users/hue/code/dopemux-mvp/src/core/config.py ---\n"""
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