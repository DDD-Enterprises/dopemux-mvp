"""Models and gate logic for Dopemux workflow state."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
import json
import re
from typing import Any, Dict, Iterable, List, Optional


DEFAULT_COMPLETION_TOKEN = "WORKFLOW_COMPLETE"
WORKFLOW_CHECKPOINT_PATTERN = re.compile(
    r"<workflow-checkpoint\b(?P<attrs>[^>]*)/?>",
    re.IGNORECASE,
)
WORKFLOW_ATTR_PATTERN = re.compile(r'([a-zA-Z_]+)="([^"]*)"')


def utc_now_iso() -> str:
    """Return an ISO-8601 timestamp in UTC."""
    return datetime.now(timezone.utc).isoformat()


class WorkflowPhase(str, Enum):
    """Ordered lifecycle phases for the workflow kit."""

    BRIEF = "brief"
    BREAKDOWN = "breakdown"
    RESEARCH = "research"
    RESEARCH_REVIEW = "research_review"
    PLAN = "plan"
    PLAN_REVIEW = "plan_review"
    IMPLEMENT = "implement"
    REFACTOR = "refactor"
    COMPLETE = "complete"

    @classmethod
    def ordered(cls) -> List["WorkflowPhase"]:
        return [
            cls.BRIEF,
            cls.BREAKDOWN,
            cls.RESEARCH,
            cls.RESEARCH_REVIEW,
            cls.PLAN,
            cls.PLAN_REVIEW,
            cls.IMPLEMENT,
            cls.REFACTOR,
            cls.COMPLETE,
        ]


class WorkflowStatus(str, Enum):
    """High-level state of a workflow run."""

    ACTIVE = "active"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    COMPLETE = "complete"


class WorkflowCheckpointStatus(str, Enum):
    """Validation state for a checkpoint emitted by a worker or manager."""

    COMPLETE = "complete"
    APPROVED = "approved"
    REJECTED = "rejected"
    BLOCKED = "blocked"

    @property
    def is_stop_safe(self) -> bool:
        return self in {
            WorkflowCheckpointStatus.COMPLETE,
            WorkflowCheckpointStatus.APPROVED,
            WorkflowCheckpointStatus.REJECTED,
            WorkflowCheckpointStatus.BLOCKED,
        }


@dataclass
class WorkflowCheckpoint:
    """Checkpoint emitted after a bounded phase action."""

    phase: WorkflowPhase
    status: WorkflowCheckpointStatus
    checkpoint_id: str = field(default_factory=lambda: f"cp-{datetime.now(timezone.utc).timestamp():.6f}")
    task_id: Optional[str] = None
    summary: str = ""
    artifact_path: Optional[str] = None
    verification_commands: List[str] = field(default_factory=list)
    emitted_at: str = field(default_factory=utc_now_iso)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "phase": self.phase.value,
            "status": self.status.value,
            "task_id": self.task_id,
            "summary": self.summary,
            "artifact_path": self.artifact_path,
            "verification_commands": list(self.verification_commands),
            "emitted_at": self.emitted_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "WorkflowCheckpoint":
        return cls(
            checkpoint_id=str(payload.get("checkpoint_id") or f"cp-{datetime.now(timezone.utc).timestamp():.6f}"),
            phase=WorkflowPhase(str(payload.get("phase", WorkflowPhase.BRIEF.value))),
            status=WorkflowCheckpointStatus(str(payload.get("status", WorkflowCheckpointStatus.COMPLETE.value))),
            task_id=payload.get("task_id"),
            summary=str(payload.get("summary", "")),
            artifact_path=payload.get("artifact_path"),
            verification_commands=[str(cmd) for cmd in payload.get("verification_commands", [])],
            emitted_at=str(payload.get("emitted_at", utc_now_iso())),
            metadata=dict(payload.get("metadata", {})),
        )


@dataclass
class WorkflowTask:
    """Temporary local mirror of a PM-backed workflow task."""

    task_id: str
    title: str
    summary: str
    authority: str = "local-mirror"
    status: str = "todo"
    source_artifact: Optional[str] = None
    artifact_dir: Optional[str] = None
    verification_commands: List[str] = field(default_factory=list)
    required_artifacts: List[str] = field(
        default_factory=lambda: [
            "research",
            "research_review",
            "plan",
            "plan_review",
        ]
    )
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "summary": self.summary,
            "authority": self.authority,
            "status": self.status,
            "source_artifact": self.source_artifact,
            "artifact_dir": self.artifact_dir,
            "verification_commands": list(self.verification_commands),
            "required_artifacts": list(self.required_artifacts),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "WorkflowTask":
        return cls(
            task_id=str(payload["task_id"]),
            title=str(payload.get("title", payload["task_id"])),
            summary=str(payload.get("summary", "")),
            authority=str(payload.get("authority", "local-mirror")),
            status=str(payload.get("status", "todo")),
            source_artifact=payload.get("source_artifact"),
            artifact_dir=payload.get("artifact_dir"),
            verification_commands=[str(cmd) for cmd in payload.get("verification_commands", [])],
            required_artifacts=[str(item) for item in payload.get("required_artifacts", [])] or [
                "research",
                "research_review",
                "plan",
                "plan_review",
            ],
            metadata=dict(payload.get("metadata", {})),
        )


@dataclass
class WorkflowState:
    """Persisted workflow run state."""

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
    started_at: str
    updated_at: str
    status: WorkflowStatus
    history: List[Dict[str, Any]] = field(default_factory=list)
    active_workspace: Optional[str] = None
    workspace_family_root: Optional[str] = None
    brief_source: Optional[str] = None
    brief_path: Optional[str] = None
    pm_authority: str = "local-mirror"
    pm_reachable: bool = False
    tasks: List[WorkflowTask] = field(default_factory=list)
    checkpoints: List[WorkflowCheckpoint] = field(default_factory=list)
    worker_launches: List[Dict[str, Any]] = field(default_factory=list)

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
            "started_at": self.started_at,
            "updated_at": self.updated_at,
            "status": self.status.value,
            "history": self.history,
            "active_workspace": self.active_workspace,
            "workspace_family_root": self.workspace_family_root,
            "brief_source": self.brief_source,
            "brief_path": self.brief_path,
            "pm_authority": self.pm_authority,
            "pm_reachable": self.pm_reachable,
            "tasks": [task.to_dict() for task in self.tasks],
            "checkpoints": [checkpoint.to_dict() for checkpoint in self.checkpoints],
            "worker_launches": self.worker_launches,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "WorkflowState":
        return cls(
            workflow_id=str(payload["workflow_id"]),
            workspace_root=str(payload["workspace_root"]),
            instance_id=str(payload.get("instance_id", "A")),
            mode=str(payload.get("mode", "manager")),
            phase=WorkflowPhase(str(payload.get("phase", WorkflowPhase.BRIEF.value))),
            current_task_id=payload.get("current_task_id"),
            iteration=int(payload.get("iteration", 0)),
            max_iterations=int(payload.get("max_iterations", 0)),
            max_minutes=int(payload.get("max_minutes", 0)),
            completion_token=str(payload.get("completion_token", DEFAULT_COMPLETION_TOKEN)),
            started_at=str(payload.get("started_at", utc_now_iso())),
            updated_at=str(payload.get("updated_at", utc_now_iso())),
            status=WorkflowStatus(str(payload.get("status", WorkflowStatus.ACTIVE.value))),
            history=list(payload.get("history", [])),
            active_workspace=payload.get("active_workspace"),
            workspace_family_root=payload.get("workspace_family_root"),
            brief_source=payload.get("brief_source"),
            brief_path=payload.get("brief_path"),
            pm_authority=str(payload.get("pm_authority", "local-mirror")),
            pm_reachable=bool(payload.get("pm_reachable", False)),
            tasks=[WorkflowTask.from_dict(item) for item in payload.get("tasks", [])],
            checkpoints=[WorkflowCheckpoint.from_dict(item) for item in payload.get("checkpoints", [])],
            worker_launches=list(payload.get("worker_launches", [])),
        )

    def record_history(
        self,
        *,
        event: str,
        message: str,
        phase: Optional[WorkflowPhase] = None,
        task_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.updated_at = utc_now_iso()
        self.history.append(
            {
                "timestamp": self.updated_at,
                "event": event,
                "message": message,
                "phase": (phase or self.phase).value,
                "task_id": task_id or self.current_task_id,
                "details": details or {},
            }
        )

    def current_task(self) -> Optional[WorkflowTask]:
        if not self.current_task_id:
            return None
        return next((task for task in self.tasks if task.task_id == self.current_task_id), None)

    def latest_checkpoint(self, *, task_id: Optional[str] = None, phase: Optional[WorkflowPhase] = None) -> Optional[WorkflowCheckpoint]:
        for checkpoint in reversed(self.checkpoints):
            if task_id and checkpoint.task_id != task_id:
                continue
            if phase and checkpoint.phase != phase:
                continue
            return checkpoint
        return None

    def add_checkpoint(self, checkpoint: WorkflowCheckpoint) -> None:
        self.checkpoints.append(checkpoint)
        if checkpoint.task_id:
            self.current_task_id = checkpoint.task_id
        self.record_history(
            event="checkpoint",
            message=checkpoint.summary or f"{checkpoint.phase.value} checkpoint recorded",
            phase=checkpoint.phase,
            task_id=checkpoint.task_id,
            details=checkpoint.to_dict(),
        )

    def workflow_dir(self) -> Path:
        root = Path(self.workspace_root) / ".dopemux" / "workflows" / self.workflow_id
        return root

    def task_dir(self, task: WorkflowTask) -> Path:
        if task.artifact_dir:
            return Path(task.artifact_dir)
        return self.workflow_dir() / "tasks" / task.task_id

    def gate_failures_for(self, target_phase: WorkflowPhase) -> List[str]:
        return validate_phase_entry(self, target_phase)


def parse_workflow_checkpoint(text: str) -> Optional[WorkflowCheckpoint]:
    """Parse a checkpoint token emitted by a worker or manager."""
    if not text:
        return None

    match = WORKFLOW_CHECKPOINT_PATTERN.search(text)
    if not match:
        return None

    attrs = dict(WORKFLOW_ATTR_PATTERN.findall(match.group("attrs") or ""))
    phase_name = attrs.get("phase")
    if not phase_name:
        return None

    status_name = attrs.get("status", WorkflowCheckpointStatus.COMPLETE.value)
    try:
        phase = WorkflowPhase(phase_name)
        status = WorkflowCheckpointStatus(status_name)
    except ValueError:
        return None

    verification_commands = []
    if attrs.get("verification"):
        verification_commands = [cmd.strip() for cmd in attrs["verification"].split(";;") if cmd.strip()]

    return WorkflowCheckpoint(
        phase=phase,
        status=status,
        task_id=attrs.get("task"),
        summary=attrs.get("summary", ""),
        artifact_path=attrs.get("artifact"),
        verification_commands=verification_commands,
        metadata={key: value for key, value in attrs.items() if key not in {"phase", "status", "task", "summary", "artifact", "verification"}},
    )


def contains_completion_token(text: str, token: str) -> bool:
    """Return True when the configured workflow completion token is present."""
    return bool(text and token and f"<promise>{token}</promise>" in text)


def task_artifact_presence(task: WorkflowTask) -> Dict[str, bool]:
    """Check required artifact stems for a task directory."""
    directory = Path(task.artifact_dir or "")
    if not directory.exists():
        return {stem: False for stem in task.required_artifacts}

    names = {path.name.lower() for path in directory.iterdir() if path.is_file()}
    presence: Dict[str, bool] = {}
    for stem in task.required_artifacts:
        normalized = stem.lower()
        presence[stem] = any(name.startswith(normalized) and name.endswith(".md") for name in names)
    return presence


def _checkpoint_status(
    checkpoints: Iterable[WorkflowCheckpoint],
    *,
    task_id: Optional[str],
    phase: WorkflowPhase,
    status: WorkflowCheckpointStatus,
) -> bool:
    return any(
        checkpoint.phase == phase
        and checkpoint.status == status
        and (task_id is None or checkpoint.task_id == task_id)
        for checkpoint in checkpoints
    )


def validate_phase_entry(state: WorkflowState, target_phase: WorkflowPhase) -> List[str]:
    """Return human-readable gate failures for a target phase."""
    task = state.current_task()
    task_id = task.task_id if task else None
    failures: List[str] = []

    if target_phase == WorkflowPhase.RESEARCH_REVIEW:
        if task is None:
            failures.append("No active task is selected for research review.")
        else:
            presence = task_artifact_presence(task)
            if not presence.get("research", False) and not _checkpoint_status(
                state.checkpoints,
                task_id=task_id,
                phase=WorkflowPhase.RESEARCH,
                status=WorkflowCheckpointStatus.COMPLETE,
            ):
                failures.append("Research artifacts are missing for the active task.")

    if target_phase == WorkflowPhase.PLAN:
        if not _checkpoint_status(
            state.checkpoints,
            task_id=task_id,
            phase=WorkflowPhase.RESEARCH_REVIEW,
            status=WorkflowCheckpointStatus.APPROVED,
        ):
            failures.append("Plan phase requires an approved research review.")

    if target_phase == WorkflowPhase.PLAN_REVIEW:
        if task is None:
            failures.append("No active task is selected for plan review.")
        else:
            presence = task_artifact_presence(task)
            if not presence.get("plan", False) and not _checkpoint_status(
                state.checkpoints,
                task_id=task_id,
                phase=WorkflowPhase.PLAN,
                status=WorkflowCheckpointStatus.COMPLETE,
            ):
                failures.append("Plan artifacts are missing for the active task.")

    if target_phase == WorkflowPhase.IMPLEMENT:
        if not _checkpoint_status(
            state.checkpoints,
            task_id=task_id,
            phase=WorkflowPhase.PLAN_REVIEW,
            status=WorkflowCheckpointStatus.APPROVED,
        ):
            failures.append("Implementation requires an approved plan review.")

    if target_phase == WorkflowPhase.REFACTOR:
        if not _checkpoint_status(
            state.checkpoints,
            task_id=task_id,
            phase=WorkflowPhase.IMPLEMENT,
            status=WorkflowCheckpointStatus.COMPLETE,
        ):
            failures.append("Refactor requires a completed implementation checkpoint.")

    if target_phase == WorkflowPhase.COMPLETE:
        incomplete = [
            task.title
            for task in state.tasks
            if task.status not in {"done", "complete"}
        ]
        if incomplete:
            failures.append(
                "Workflow cannot complete while tasks remain open: " + ", ".join(incomplete)
            )
        for task in state.tasks:
            presence = task_artifact_presence(task)
            missing = [stem for stem, exists in presence.items() if not exists]
            if missing:
                failures.append(
                    f"Task '{task.title}' is missing required artifacts: {', '.join(missing)}"
                )
        for task in state.tasks:
            if task.verification_commands and not task.metadata.get("verification_passed", False):
                failures.append(
                    f"Task '{task.title}' has verification commands that have not passed."
                )

    return failures


def state_to_pretty_json(state: WorkflowState) -> str:
    """Serialize workflow state for inspect output."""
    return json.dumps(state.to_dict(), indent=2, sort_keys=True)
