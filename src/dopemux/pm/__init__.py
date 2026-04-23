"""PM Plane canonical task model and store.

This package defines the single source of lifecycle truth for PM tasks.
Trinity boundary: imports nothing from Memory (ConPort), Search (Serena),
or services/*.
"""

from importlib import import_module
from typing import Any

from .models import PMTask, PMTaskStatus, PMTransitionRequest, content_hash_task_id
from .store import InMemoryPMTaskStore, PMTaskStore, StaleWriteError, TaskNotFoundError
from .chronicle import pm_get_work_chronicle, pm_append_work_chronicle, pm_correct_work_chronicle

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
    "pm_update_work_item",
    "pm_transition_work_item",
    "pm_log_progress",
    "pm_log_decision",
    "CanonicalReceipt",
    "MirrorReceipt",
    "PMWriteConfig",
]

_LAZY_EXPORTS = {
    "pm_get_project_context": (".reads", "pm_get_project_context"),
    "pm_get_priority_queue": (".reads", "pm_get_priority_queue"),
    "pm_get_blockers": (".reads", "pm_get_blockers"),
    "pm_get_workflow_state": (".reads", "pm_get_workflow_state"),
    "pm_get_sprint_snapshot": (".reads", "pm_get_sprint_snapshot"),
    "pm_get_decision_context": (".reads", "pm_get_decision_context"),
    "pm_update_work_item": (".writes", "pm_update_work_item"),
    "pm_transition_work_item": (".writes", "pm_transition_work_item"),
    "pm_log_progress": (".writes", "pm_log_progress"),
    "pm_log_decision": (".writes", "pm_log_decision"),
    "CanonicalReceipt": (".writes", "CanonicalReceipt"),
    "MirrorReceipt": (".writes", "MirrorReceipt"),
    "PMWriteConfig": (".writes", "PMWriteConfig"),
}


def __getattr__(name: str) -> Any:
    target = _LAZY_EXPORTS.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module_name, attr_name = target
    value = getattr(import_module(module_name, __name__), attr_name)
    globals()[name] = value
    return value
