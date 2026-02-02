"""
Task-Orchestrator Data Models.

Extracted from enhanced_orchestrator.py lines 93-165.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class TaskStatus(str, Enum):
    """Enhanced task status with ADHD considerations."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    NEEDS_BREAK = "needs_break"
    CONTEXT_SWITCH = "context_switch"
    PAUSED = "paused"


class AgentType(str, Enum):
    """AI agent types for task coordination."""
    CONPORT = "conport"
    SERENA = "serena"
    TASKMASTER = "taskmaster"
    CLAUDE_FLOW = "claude_flow"
    PAL = "pal"  # Renamed from ZEN


@dataclass
class OrchestrationTask:
    """Enhanced task representation for orchestration."""
    id: str
    leantime_id: Optional[int] = None
    conport_id: Optional[int] = None
    title: str = ""
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 1
    complexity_score: float = 0.5
    estimated_minutes: int = 25
    assigned_agent: Optional[AgentType] = None

    # ADHD-specific fields
    energy_required: str = "medium"  # low, medium, high
    cognitive_load: float = 0.5  # 0.0-1.0
    context_switches_allowed: int = 2
    break_frequency_minutes: int = 25

    # Orchestration metadata
    dependencies: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)
    agent_assignments: Dict[str, str] = field(default_factory=dict)
    progress_checkpoints: List[Dict] = field(default_factory=list)

    # Sync tracking
    last_synced: Optional[datetime] = None
    sync_conflicts: List[str] = field(default_factory=list)


@dataclass
class SyncEvent:
    """Event for multi-directional synchronization."""
    source_system: str
    target_systems: List[str]
    event_type: str
    task_id: str
    data: Dict[str, Any]
    timestamp: datetime
    adhd_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentPoolEntry:
    """AI agent pool entry."""
    available: bool = True
    current_tasks: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    max_concurrent: int = 1


@dataclass
class OrchestratorMetrics:
    """Orchestration metrics tracking."""
    tasks_orchestrated: int = 0
    sync_events_processed: int = 0
    ai_agent_dispatches: int = 0
    adhd_accommodations_applied: int = 0
    implicit_automations_triggered: int = 0
