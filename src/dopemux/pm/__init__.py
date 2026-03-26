"""
PM Plane canonical task model and store.

This package defines the single source of lifecycle truth for PM tasks.
Trinity boundary: imports nothing from Memory (ConPort), Search (Serena),
or services/*.
"""

from .models import PMTask, PMTaskStatus, PMTransitionRequest, content_hash_task_id
from .store import InMemoryPMTaskStore, PMTaskStore, StaleWriteError, TaskNotFoundError
from .chronicle import pm_get_work_chronicle, pm_append_work_chronicle, pm_correct_work_chronicle
from .reads import (
    pm_get_project_context,
    pm_get_priority_queue,
    pm_get_blockers,
    pm_get_workflow_state,
    pm_get_sprint_snapshot,
    pm_get_decision_context,
)

__all__ = [
    "PMTask",
    "PMTaskStatus",
    "PMTransitionRequest",
    "content_hash_task_id",
    "PMTaskStore",
    "InMemoryPMTaskStore",
    "TaskNotFoundError",
    "StaleWriteError",
    "pm_get_work_chronicle",
    "pm_append_work_chronicle",
    "pm_correct_work_chronicle",
    "pm_get_project_context",
    "pm_get_priority_queue",
    "pm_get_blockers",
    "pm_get_workflow_state",
    "pm_get_sprint_snapshot",
    "pm_get_decision_context",
]

from .writes import (
    pm_update_work_item,
    pm_transition_work_item,
    pm_log_progress,
    CanonicalReceipt,
    MirrorReceipt,
    PMWriteConfig,
)

__all__.extend([
    "pm_update_work_item",
    "pm_transition_work_item",
    "pm_log_progress",
    "CanonicalReceipt",
    "MirrorReceipt",
    "PMWriteConfig",
])
