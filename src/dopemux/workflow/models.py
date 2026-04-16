"""Models and gate logic for Dopemux workflow state."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
import json
import re
from typing import Any, Dict, Iterable, List, Optional

from dopemux.pm.models import PMTaskStatus
from services.shared.brand_voice import StatusChip, tone_name, voice_header


DEFAULT_COMPLETION_TOKEN = "WORKFLOW_COMPLETE"
WORKFLOW_CHECKPOINT_PATTERN = re.compile(
    r"<workflow-checkpoint\b(?P<attrs>[^>]*)/?>",
    re.IGNORECASE,
)


def utc_now_iso() -> str:
    """Return current UTC time in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def contains_completion_token(text: str, token: str) -> bool:
    """Return True if text contains the completion token, possibly inside a <promise>."""
    if not token:
        return False
    # Check for direct inclusion
    if token in text:
        return True
    # Check for promise wrapping
    pattern = rf"<promise\b[^>]*>.*?{re.escape(token)}.*?</promise>"
    return bool(re.search(pattern, text, re.DOTALL | re.IGNORECASE))


def workflow_brand_meta(
    chip: StatusChip = StatusChip.LOGGED,
    *,
    surface: str = "ui",
) -> Dict[str, str]:
    """Return additive operator metadata for workflow surfaces.

    This helper is intentionally separate from ``to_dict`` payload emission so
    existing workflow-state serialization contracts do not drift implicitly.
    """
    return {
        "status_chip": chip.label,
        "tone": tone_name(chip),
        "voice_header": voice_header(surface),
    }


class WorkflowStatus(str, Enum):
    """Overall status of a workflow run."""

    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETE = "complete"
    CANCELLED = "cancelled"
    FAILED = "failed"


class WorkflowPhase(str, Enum):
    """Distinct phases of an internal execution ritual."""

    BRIEF = "brief"
    RESEARCH = "research"
    RESEARCH_REVIEW = "research_review"
    PLAN = "plan"
    PLAN_REVIEW = "plan_review"
    IMPLEMENT = "implement"
    REFACTOR = "refactor"
    COMPLETE = "complete"


class WorkflowCheckpointStatus(str, Enum):
    """Status of a phase gate or checkpoint."""

    COMPLETE = "complete"
    APPROVED = "approved"
    REJECTED = "rejected"
    SKIPPED = "skipped"

    @property
    def is_stop_safe(self) -> bool:
        """Return True if this status allows stopping the session."""
        return self in {self.COMPLETE, self.APPROVED, self.SKIPPED}


@dataclass
class WorkflowCheckpoint:
    """A recorded gate or status marker within a workflow."""

    phase: WorkflowPhase
    status: WorkflowCheckpointStatus
    summary: str = ""
    task_id: Optional[str] = None
    timestamp: str = field(default_factory=utc_now_iso)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase": self.phase.value,
            "status": self.status.value,
            "summary": self.summary,
            "task_id": self.task_id,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "WorkflowCheckpoint":
        return cls(
            phase=WorkflowPhase(payload["phase"]),
            status=WorkflowCheckpointStatus(payload["status"]),
            summary=payload.get("summary", ""),
            task_id=payload.get("task_id"),
            timestamp=payload.get("timestamp", utc_now_iso()),
            metadata=dict(payload.get("metadata", {})),
        )


@dataclass
class WorkflowTask:
    """Temporary local mirror of a PM-backed workflow task."""

    task_id: str
    title: str
    summary: str = ""
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
            "verification_commands": self.verification_commands,
            "required_artifacts": self.required_artifacts,
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
    required_artifacts: List[str] = field(default_factory=list)
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
            "required_artifacts": self.required_artifacts,
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
            required_artifacts=list(payload.get("required_artifacts", [])),
            worker_launches=list(payload.get("worker_launches", [])),
        )

    @classmethod
    def new(
        cls,
        workflow_id: str,
        workspace_root: Path,
        instance_id: str = "A",
        mode: str = "manager",
        max_iterations: int = 0,
        max_minutes: int = 0,
        completion_token: str = DEFAULT_COMPLETION_TOKEN,
    ) -> "WorkflowState":
        """Create a fresh WorkflowState with current timestamps."""
        now = utc_now_iso()
        state = cls(
            workflow_id=workflow_id,
            workspace_root=str(workspace_root),
            instance_id=instance_id,
            mode=mode,
            phase=WorkflowPhase.BRIEF,
            current_task_id=None,
            iteration=0,
            max_iterations=max_iterations,
            max_minutes=max_minutes,
            completion_token=completion_token,
            started_at=now,
            updated_at=now,
            status=WorkflowStatus.ACTIVE,
        )
        state.record_history(event="workflow.new", message="Workflow state created.")
        return state

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

    def record_event(self, event: str, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Record a generic event in history."""
        self.record_history(event=event, message=message, details=details)

    def record_checkpoint(self, phase: str | WorkflowPhase, approved: bool, message: str = "", task_id: Optional[str] = None) -> None:
        """Helper to create and add a checkpoint."""
        checkpoint = WorkflowCheckpoint(
            phase=WorkflowPhase(phase) if isinstance(phase, str) else phase,
            status=WorkflowCheckpointStatus.APPROVED if approved else WorkflowCheckpointStatus.REJECTED,
            summary=message,
            task_id=task_id or self.current_task_id,
        )
        self.add_checkpoint(checkpoint)

    def validate_phase_transition(self, target_phase: WorkflowPhase) -> Optional[str]:
        """Legacy wrapper for validate_phase_entry returning single string or None."""
        failures = validate_phase_entry(self, target_phase)
        return failures[0] if failures else None

    def can_stop(self) -> bool:
        """Return True if the workflow is in a stoppable state."""
        # A workflow can stop if there's an approved checkpoint for the current phase
        # or if a completion token was seen in history.
        for h in self.history:
            msg = h.get("message", "")
            if contains_completion_token(msg, self.completion_token) or (self.completion_token and self.completion_token in msg):
                return True
        
        latest = self.latest_checkpoint(phase=self.phase)
        if latest and latest.status.is_stop_safe:
            return True
            
        return False

    def current_task(self) -> Optional[WorkflowTask]:
        if not self.current_task_id:
            return None
        return next((task for task in self.tasks if task.task_id == self.current_task_id), None)

    def add_checkpoint(self, checkpoint: WorkflowCheckpoint) -> None:
        self.checkpoints.append(checkpoint)
        self.record_history(
            event="checkpoint.added",
            message=f"Checkpoint recorded for phase '{checkpoint.phase.value}': {checkpoint.status.value}",
            phase=checkpoint.phase,
            task_id=checkpoint.task_id,
            details=checkpoint.to_dict(),
        )

    def latest_checkpoint(self, phase: Optional[WorkflowPhase] = None) -> Optional[WorkflowCheckpoint]:
        filtered = [c for c in self.checkpoints if phase is None or c.phase == phase]
        return filtered[-1] if filtered else None


def task_artifact_presence(task: WorkflowTask) -> Dict[str, bool]:
    """Return a map of required artifact stems to their local presence."""
    if not task.artifact_dir:
        return {stem: False for stem in task.required_artifacts}

    art_dir = Path(task.artifact_dir)
    if not art_dir.is_dir():
        return {stem: False for stem in task.required_artifacts}

    # Gather all file stems in the directory
    names = set()
    for p in art_dir.iterdir():
        if p.is_file():
            lowered = p.name.lower()
            names.add(lowered)
            # Support both hyphen and underscore normalization
            names.add(lowered.replace("-", "_"))

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
            failures.append("Cannot enter plan without an approved research_review checkpoint.")

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
            failures.append("Cannot enter implement/refactor without an approved plan_review checkpoint.")

    if target_phase == WorkflowPhase.REFACTOR:
        if not _checkpoint_status(
            state.checkpoints,
            task_id=task_id,
            phase=WorkflowPhase.IMPLEMENT,
            status=WorkflowCheckpointStatus.COMPLETE,
        ):
            failures.append("Refactor requires a completed implementation checkpoint.")

    if target_phase == WorkflowPhase.COMPLETE:
        if any(t.status not in {PMTaskStatus.DONE, "done", "complete"} for t in state.tasks):
            failures.append("Cannot complete while workflow tasks are still incomplete.")
        root = Path(state.workspace_root)
        for artifact_rel_path in state.required_artifacts:
            if not (root / artifact_rel_path).exists():
                failures.append("Cannot complete while required artifacts are missing.")
                break
    return failures


def parse_workflow_checkpoint(text: str) -> Optional[WorkflowCheckpoint]:
    """Parse a workflow checkpoint from raw text."""
    match = WORKFLOW_CHECKPOINT_PATTERN.search(text)
    if not match:
        return None

    attrs_text = match.group("attrs")
    # Simple attribute parser
    attrs: Dict[str, str] = {}
    for attr_match in re.finditer(r'(?P<key>\w+)=(?P<quote>["\'])(?P<val>.*?)(?P=quote)', attrs_text):
        attrs[attr_match.group("key")] = attr_match.group("val")

    try:
        phase = WorkflowPhase(attrs.get("phase", "brief"))
        status = WorkflowCheckpointStatus(attrs.get("status", "complete"))
        return WorkflowCheckpoint(
            phase=phase,
            status=status,
            summary=attrs.get("summary", ""),
            task_id=attrs.get("task_id"),
        )
    except (ValueError, KeyError):
        return None


def state_to_pretty_json(state: WorkflowState) -> str:
    """Serialize workflow state for inspect output."""
    return json.dumps(state.to_dict(), indent=2, sort_keys=True)
