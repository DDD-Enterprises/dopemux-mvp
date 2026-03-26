"""Typed workflow models for Dopemux internal workflow runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _isoformat(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


class WorkflowPhase(str, Enum):
    """Canonical workflow phases."""

    BRIEF = "brief"
    BREAKDOWN = "breakdown"
    RESEARCH = "research"
    RESEARCH_REVIEW = "research_review"
    PLAN = "plan"
    PLAN_REVIEW = "plan_review"
    IMPLEMENT = "implement"
    REFACTOR = "refactor"
    COMPLETE = "complete"


WORKFLOW_PHASE_ORDER: List[WorkflowPhase] = [
    WorkflowPhase.BRIEF,
    WorkflowPhase.BREAKDOWN,
    WorkflowPhase.RESEARCH,
    WorkflowPhase.RESEARCH_REVIEW,
    WorkflowPhase.PLAN,
    WorkflowPhase.PLAN_REVIEW,
    WorkflowPhase.IMPLEMENT,
    WorkflowPhase.REFACTOR,
    WorkflowPhase.COMPLETE,
]


class WorkflowStatus(str, Enum):
    """Lifecycle status for a workflow state."""

    ACTIVE = "active"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowTaskStatus(str, Enum):
    """Execution status for a workflow task."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class WorkflowHistoryEntry:
    """Append-only workflow history entry."""

    timestamp: str
    event: str
    phase: str
    message: str = ""
    checkpoint: Optional[str] = None
    approved: Optional[bool] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "event": self.event,
            "phase": self.phase,
            "message": self.message,
            "checkpoint": self.checkpoint,
            "approved": self.approved,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowHistoryEntry":
        return cls(
            timestamp=str(data["timestamp"]),
            event=str(data["event"]),
            phase=str(data["phase"]),
            message=str(data.get("message", "")),
            checkpoint=data.get("checkpoint"),
            approved=data.get("approved"),
            metadata=dict(data.get("metadata") or {}),
        )


@dataclass
class WorkflowTask:
    """Workflow task tracked by the manager/executor flow."""

    task_id: str
    title: str
    status: WorkflowTaskStatus = WorkflowTaskStatus.PENDING
    required_artifacts: List[str] = field(default_factory=list)
    verification_commands: List[str] = field(default_factory=list)
    worktree_path: Optional[str] = None
    instance_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "status": self.status.value,
            "required_artifacts": list(self.required_artifacts),
            "verification_commands": list(self.verification_commands),
            "worktree_path": self.worktree_path,
            "instance_id": self.instance_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowTask":
        return cls(
            task_id=str(data["task_id"]),
            title=str(data.get("title", data["task_id"])),
            status=WorkflowTaskStatus(str(data.get("status", WorkflowTaskStatus.PENDING.value))),
            required_artifacts=[str(item) for item in data.get("required_artifacts", [])],
            verification_commands=[str(item) for item in data.get("verification_commands", [])],
            worktree_path=data.get("worktree_path"),
            instance_id=data.get("instance_id"),
        )


@dataclass
class WorkflowState:
    """Canonical persisted workflow state."""

    workflow_id: str
    workspace_root: str
    instance_id: str
    mode: str
    phase: WorkflowPhase
    current_task_id: Optional[str]
    iteration: int
    max_iterations: int
    max_minutes: int
    completion_token: str
    status: WorkflowStatus
    started_at: str
    updated_at: str
    history: List[WorkflowHistoryEntry] = field(default_factory=list)
    tasks: List[WorkflowTask] = field(default_factory=list)
    required_artifacts: List[str] = field(default_factory=list)

    @classmethod
    def new(
        cls,
        workflow_id: str,
        workspace_root: Path,
        instance_id: str,
        mode: str,
        max_iterations: int,
        max_minutes: int,
        completion_token: str,
    ) -> "WorkflowState":
        now = _isoformat(_utc_now())
        state = cls(
            workflow_id=workflow_id,
            workspace_root=str(workspace_root.resolve()),
            instance_id=instance_id,
            mode=mode,
            phase=WorkflowPhase.BRIEF,
            current_task_id=None,
            iteration=0,
            max_iterations=max_iterations,
            max_minutes=max_minutes,
            completion_token=completion_token,
            status=WorkflowStatus.ACTIVE,
            started_at=now,
            updated_at=now,
        )
        state.record_event("workflow_initialized", "Workflow initialized")
        return state

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "workspace_root": self.workspace_root,
            "instance_id": self.instance_id,
            "mode": self.mode,
            "phase": self.phase.value,
            "current_task_id": self.current_task_id,
            "iteration": self.iteration,
            "max_iterations": self.max_iterations,
            "max_minutes": self.max_minutes,
            "completion_token": self.completion_token,
            "status": self.status.value,
            "started_at": self.started_at,
            "updated_at": self.updated_at,
            "history": [entry.to_dict() for entry in self.history],
            "tasks": [task.to_dict() for task in self.tasks],
            "required_artifacts": list(self.required_artifacts),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowState":
        return cls(
            workflow_id=str(data["workflow_id"]),
            workspace_root=str(data["workspace_root"]),
            instance_id=str(data.get("instance_id", "main")),
            mode=str(data.get("mode", "internal")),
            phase=WorkflowPhase(str(data.get("phase", WorkflowPhase.BRIEF.value))),
            current_task_id=data.get("current_task_id"),
            iteration=int(data.get("iteration", 0)),
            max_iterations=int(data.get("max_iterations", 50)),
            max_minutes=int(data.get("max_minutes", 120)),
            completion_token=str(data.get("completion_token", "WORKFLOW_COMPLETE")),
            status=WorkflowStatus(str(data.get("status", WorkflowStatus.ACTIVE.value))),
            started_at=str(data["started_at"]),
            updated_at=str(data["updated_at"]),
            history=[WorkflowHistoryEntry.from_dict(item) for item in data.get("history", [])],
            tasks=[WorkflowTask.from_dict(item) for item in data.get("tasks", [])],
            required_artifacts=[str(item) for item in data.get("required_artifacts", [])],
        )

    @property
    def workspace_path(self) -> Path:
        return Path(self.workspace_root)

    def touch(self) -> None:
        self.updated_at = _isoformat(_utc_now())

    def record_event(
        self,
        event: str,
        message: str,
        *,
        checkpoint: Optional[str] = None,
        approved: Optional[bool] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.history.append(
            WorkflowHistoryEntry(
                timestamp=_isoformat(_utc_now()),
                event=event,
                phase=self.phase.value,
                message=message,
                checkpoint=checkpoint,
                approved=approved,
                metadata=dict(metadata or {}),
            )
        )
        self.touch()

    def record_checkpoint(
        self,
        checkpoint: str,
        approved: bool,
        *,
        message: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        event = "checkpoint_approved" if approved else "checkpoint_rejected"
        self.record_event(
            event,
            message or checkpoint,
            checkpoint=checkpoint,
            approved=approved,
            metadata=metadata,
        )

    def approved_checkpoint(self, checkpoint: str) -> bool:
        for entry in reversed(self.history):
            if entry.checkpoint == checkpoint and entry.approved is True:
                return True
        return False

    def has_completion_token(self) -> bool:
        token = self.completion_token.strip()
        if not token:
            return False
        for entry in reversed(self.history):
            if token in entry.message:
                return True
        return False

    def elapsed_minutes(self, now: Optional[datetime] = None) -> float:
        current = now or _utc_now()
        started = _parse_datetime(self.started_at)
        delta = current - started
        return delta.total_seconds() / 60.0

    def limit_violations(self, now: Optional[datetime] = None) -> List[str]:
        issues: List[str] = []
        if self.max_iterations >= 0 and self.iteration >= self.max_iterations:
            issues.append("max_iterations")
        if self.max_minutes >= 0 and self.elapsed_minutes(now) >= self.max_minutes:
            issues.append("max_minutes")
        return issues

    def incomplete_tasks(self) -> List[WorkflowTask]:
        return [task for task in self.tasks if task.status != WorkflowTaskStatus.COMPLETED]

    def missing_required_artifacts(self) -> List[str]:
        missing: List[str] = []
        for artifact in self.required_artifacts:
            if not (self.workspace_path / artifact).exists():
                missing.append(artifact)
        for task in self.tasks:
            for artifact in task.required_artifacts:
                if not (self.workspace_path / artifact).exists():
                    missing.append(artifact)
        return sorted(set(missing))

    def set_phase(self, phase: WorkflowPhase) -> None:
        self.phase = phase
        if phase == WorkflowPhase.COMPLETE:
            self.status = WorkflowStatus.COMPLETED
        self.touch()

    def next_phase(self) -> Optional[WorkflowPhase]:
        try:
            index = WORKFLOW_PHASE_ORDER.index(self.phase)
        except ValueError:
            return None
        if index + 1 >= len(WORKFLOW_PHASE_ORDER):
            return None
        return WORKFLOW_PHASE_ORDER[index + 1]

    def validate_phase_transition(self, target: WorkflowPhase) -> Optional[str]:
        if target == WorkflowPhase.PLAN and not self.approved_checkpoint("research_review"):
            return "Cannot enter plan without an approved research_review checkpoint."
        if target in {WorkflowPhase.IMPLEMENT, WorkflowPhase.REFACTOR} and not self.approved_checkpoint("plan_review"):
            return "Cannot enter implement/refactor without an approved plan_review checkpoint."
        if target == WorkflowPhase.COMPLETE:
            if not self.approved_checkpoint("plan_review"):
                return "Cannot complete without an approved plan_review checkpoint."
            if self.incomplete_tasks():
                return "Cannot complete while workflow tasks are still incomplete."
            missing = self.missing_required_artifacts()
            if missing:
                return "Cannot complete while required artifacts are missing."
        return None

    def validation_summary(self) -> Dict[str, Any]:
        next_phase = self.next_phase()
        next_phase_blocker = self.validate_phase_transition(next_phase) if next_phase else None
        return {
            "research_review_approved": self.approved_checkpoint("research_review"),
            "plan_review_approved": self.approved_checkpoint("plan_review"),
            "missing_required_artifacts": self.missing_required_artifacts(),
            "incomplete_tasks": [task.task_id for task in self.incomplete_tasks()],
            "next_phase": next_phase.value if next_phase else None,
            "next_phase_blocker": next_phase_blocker,
            "can_stop": self.can_stop(),
            "limits_exceeded": self.limit_violations(),
        }

    def can_stop(self) -> bool:
        if self.status != WorkflowStatus.ACTIVE:
            return True
        phase_checkpoint = self.phase.value
        return self.approved_checkpoint(phase_checkpoint) or self.has_completion_token()


@dataclass
class ExecutorLaunchSpec:
    """Prepared launch instruction for a workflow executor."""

    workflow_id: str
    task_id: str
    instance_id: str
    branch_name: str
    worktree_path: str
    command: List[str]
    env: Dict[str, str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "task_id": self.task_id,
            "instance_id": self.instance_id,
            "branch_name": self.branch_name,
            "worktree_path": self.worktree_path,
            "command": list(self.command),
            "env": dict(self.env),
        }
