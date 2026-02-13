"""
PM Plane canonical task model and store.

This package defines the single source of lifecycle truth for PM tasks.
Trinity boundary: imports nothing from Memory (ConPort), Search (Serena),
or services/*.
"""

from .models import PMTask, PMTaskStatus, PMTransitionRequest, content_hash_task_id
from .store import InMemoryPMTaskStore, PMTaskStore, StaleWriteError, TaskNotFoundError

__all__ = [
    "PMTask",
    "PMTaskStatus",
    "PMTransitionRequest",
    "content_hash_task_id",
    "PMTaskStore",
    "InMemoryPMTaskStore",
    "TaskNotFoundError",
    "StaleWriteError",
]
