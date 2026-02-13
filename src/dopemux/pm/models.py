"""
Canonical PM task model.

Implements ADR-PM-001: one canonical task object as the only authority
for lifecycle state. Every producer maps into this object before any
lifecycle transition is accepted.

Task ID policy (ConPort Decision #1):
- If source_task_id exists: sha256(source:source_task_id)
- Else fallback: sha256(source:normalized(title):normalized(description))
- created_at_utc MUST NOT be included in hash inputs.
"""

import hashlib
import re
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class PMTaskStatus(str, Enum):
    """Canonical PM task lifecycle statuses.

    Exactly 5 values. All producers must map into this set.
    """

    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    DONE = "DONE"
    CANCELED = "CANCELED"


class PMTask(BaseModel):
    """Canonical PM task — single source of lifecycle truth.

    Invariants:
    - task_id is immutable and globally stable for the task lifecycle.
    - status uses only PMTaskStatus enum values.
    - version is monotonic; stale writes are refused.
    """

    task_id: str
    title: str
    status: PMTaskStatus = PMTaskStatus.TODO
    source: str
    created_at_utc: datetime
    updated_at_utc: datetime
    version: int = Field(default=1, ge=1)

    description: Optional[str] = None
    source_task_id: Optional[str] = None
    refs: Dict[str, Any] = Field(default_factory=dict)
    meta: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": False}


class PMTransitionRequest(BaseModel):
    """Request to transition a PM task's status.

    Invariants:
    - idempotency_key is required; duplicate keys are no-op replays.
    - expected_version is required; mismatch raises StaleWriteError.
    """

    idempotency_key: str
    expected_version: int = Field(ge=1)
    new_status: PMTaskStatus
    ts_utc: datetime
    source: str
    reason: Optional[str] = None

    model_config = {"frozen": True}


def normalize_text(s: str) -> str:
    """Normalize text for deterministic hashing.

    Lowercases, strips, and collapses internal whitespace.
    """
    s = s.strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def content_hash_task_id(
    source: str,
    source_task_id: Optional[str],
    title: str,
    description: Optional[str] = None,
) -> str:
    """Generate deterministic task ID.

    Policy (ConPort Decision #1):
    - If source_task_id exists: sha256(source:source_task_id)
    - Else: sha256(source:normalized(title):normalized(description))
    - created_at_utc is NEVER included in hash inputs.

    Returns lowercase hex string.
    """
    if source_task_id is not None:
        hash_input = f"{source}:{source_task_id}"
    else:
        norm_title = normalize_text(title)
        norm_desc = normalize_text(description or "")
        hash_input = f"{source}:{norm_title}:{norm_desc}"

    return hashlib.sha256(hash_input.encode("utf-8")).hexdigest()
