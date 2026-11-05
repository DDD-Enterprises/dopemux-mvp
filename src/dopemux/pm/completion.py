"""Completion evidence port. Production policy/provider qualification is separate."""

from dataclasses import dataclass
from typing import Protocol
import base64
import hashlib
from pathlib import Path, PurePosixPath
import tempfile

from .ownership import canonical_json, parse_json_object


@dataclass(frozen=True)
class VerifiedCompletion:
    project_id: str
    task_id: str
    task_version: int
    policy_id: str
    policy_version: int
    snapshot: bytes
    snapshot_sha256: str
    gate_scope: str

    def receipt_value(self):
        return dict(
            policy_id=self.policy_id,
            policy_version=self.policy_version,
            snapshot_sha256=self.snapshot_sha256,
            gate_scope=self.gate_scope,
        )


class CompletionEvidenceVerifier(Protocol):
    def verify(
        self, *, project_id: str, task: dict, reference: dict, policy: dict
    ) -> VerifiedCompletion: ...


class DenyCompletionVerifier:
    def verify(self, **_):
        raise PermissionError("Completion verifier unavailable")


@dataclass(frozen=True)
class KernelBinding:
    """Trusted composition binding, not caller-provided path or policy selection."""

    project_id: str
    task_id: str
    workflow_id: str
    source_revision: str
    policy_id: str
    policy_version: int
    required_task_artifacts: tuple[str, ...] = (
        "research",
        "research_review",
        "plan",
        "plan_review",
    )
    required_workflow_artifacts: tuple[str, ...] = ()
    workflow_scope: bool = False


class KernelCompletionVerifier:
    """Verify immutable evidence against R2 kernel gates, never code correctness.

    A trusted producer supplies canonical snapshot bytes containing base64 artifact
    contents. The verifier copies those bytes at composition; it never opens a
    caller filesystem path or trusts a model's completion phrase.
    """

    def __init__(self, evidence: dict[str, tuple[KernelBinding, bytes]]):
        self._evidence = {key: (binding, bytes(raw)) for key, (binding, raw) in evidence.items()}

    @staticmethod
    def _relative(value):
        if not isinstance(value, str):
            raise ValueError("Artifact path must be a string")
        p = PurePosixPath(value)
        if (
            not value
            or p.is_absolute()
            or ".." in p.parts
            or "\\" in value
            or p.as_posix() != value
        ):
            raise ValueError("Unsafe artifact path")
        return p

    @staticmethod
    def _workflow_shape(workflow):
        """Reject malformed sealed fields before the permissive mirror parser."""
        if not isinstance(workflow, dict):
            raise ValueError("Workflow must be an object")

        def fields(value, strings=(), optional_strings=(), lists=(), objects=()):
            if not isinstance(value, dict):
                raise ValueError("Workflow record must be an object")
            for key in strings:
                if key in value and not isinstance(value[key], str):
                    raise ValueError("Workflow string field required")
            for key in optional_strings:
                if (
                    key in value
                    and value[key] is not None
                    and not isinstance(value[key], str)
                ):
                    raise ValueError("Workflow optional string field required")
            for key in lists:
                if key in value and not isinstance(value[key], list):
                    raise ValueError("Workflow list field required")
            for key in objects:
                if key in value and not isinstance(value[key], dict):
                    raise ValueError("Workflow object field required")

        def string_list(value):
            if not isinstance(value, list) or any(
                not isinstance(v, str) for v in value
            ):
                raise ValueError("Artifact/command list must contain strings")

        fields(
            workflow,
            strings=(
                "workflow_id",
                "workspace_root",
                "instance_id",
                "mode",
                "phase",
                "status",
                "completion_token",
                "started_at",
                "updated_at",
                "pm_authority",
            ),
            optional_strings=(
                "current_task_id",
                "active_workspace",
                "workspace_family_root",
                "brief_source",
                "brief_path",
            ),
            lists=(
                "tasks",
                "checkpoints",
                "required_artifacts",
                "history",
                "worker_launches",
            ),
        )
        if not {"workflow_id", "workspace_root"} <= workflow.keys():
            raise ValueError("Required workflow fields absent")
        for key in ("iteration", "max_iterations", "max_minutes"):
            if key in workflow and type(workflow[key]) is not int:
                raise ValueError("Workflow integer field required")
        if "pm_reachable" in workflow and type(workflow["pm_reachable"]) is not bool:
            raise ValueError("Workflow boolean field required")
        for key in ("history", "worker_launches"):
            if any(not isinstance(v, dict) for v in workflow.get(key, [])):
                raise ValueError("Workflow record list required")
        string_list(workflow.get("required_artifacts", []))
        for task in workflow.get("tasks", []):
            fields(
                task,
                strings=("task_id", "title", "summary", "authority", "status"),
                optional_strings=("source_artifact", "artifact_dir"),
                objects=("metadata",),
            )
            if "task_id" not in task:
                raise ValueError("Task id absent")
            string_list(task.get("verification_commands", []))
            required = task.get("required_artifacts")
            string_list(required)
            if not required:
                raise ValueError("Task artifact policy absent")
        for checkpoint in workflow.get("checkpoints", []):
            fields(
                checkpoint,
                strings=("phase", "status", "summary", "timestamp"),
                optional_strings=("task_id",),
                objects=("metadata",),
            )
            if not {"phase", "status"} <= checkpoint.keys():
                raise ValueError("Checkpoint gate fields absent")

    def verify(self, *, project_id, task, reference, policy):
        from dopemux.workflow.models import (
            WorkflowState,
            WorkflowPhase,
            WorkflowCheckpointStatus,
            task_artifact_presence,
            validate_phase_entry,
        )

        item = self._evidence.get(reference["id"])
        if item is None:
            raise PermissionError("Unknown completion reference")
        binding, raw = item
        sha = hashlib.sha256(raw).hexdigest()
        if sha != reference["sha256"]:
            raise ValueError("Snapshot digest mismatch")
        snapshot = parse_json_object(raw)
        if canonical_json(snapshot) != raw or set(snapshot) != {
            "schema_version",
            "project_id",
            "task_id",
            "task_version",
            "identity",
            "source_revision",
            "workflow",
            "artifacts",
        }:
            raise ValueError("Invalid sealed snapshot")
        if (
            snapshot["schema_version"] != "dopemux.pm.kernel-snapshot.v1"
            or type(snapshot["task_version"]) is not int
        ):
            raise ValueError("Invalid snapshot schema")
        if (binding.project_id, binding.task_id, binding.policy_id, binding.policy_version) != (
            project_id,
            task["task_id"],
            policy["id"],
            policy["version"],
        ):
            raise ValueError("Completion policy binding mismatch")
        if (
            snapshot["project_id"],
            snapshot["task_id"],
            snapshot["task_version"],
            snapshot["identity"],
            snapshot["source_revision"],
        ) != (
            project_id,
            task["task_id"],
            task["version"],
            task["identity"],
            binding.source_revision,
        ):
            raise ValueError("Completion source binding mismatch")
        self._workflow_shape(snapshot["workflow"])
        if not isinstance(snapshot["artifacts"], dict) or any(
            not isinstance(encoded, str) for encoded in snapshot["artifacts"].values()
        ):
            raise ValueError("Artifacts must map paths to base64 strings")
        # Parse failures belong to the sealed-input boundary, not arbitrary verifier bugs.
        try:
            state = WorkflowState.from_dict(snapshot["workflow"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Invalid workflow snapshot") from exc
        artifacts = [
            (self._relative(name), base64.b64decode(encoded, validate=True))
            for name, encoded in snapshot["artifacts"].items()
        ]
        for workflow_task in state.tasks:
            self._relative(workflow_task.artifact_dir)
        for required in state.required_artifacts:
            self._relative(required)
        if (
            state.workflow_id != binding.workflow_id
            or state.current_task_id != binding.task_id
            or state.phase
            not in (
                {WorkflowPhase.REFACTOR, WorkflowPhase.COMPLETE}
                if binding.workflow_scope
                else {WorkflowPhase.REFACTOR}
            )
        ):
            raise ValueError("Workflow/task phase mismatch")
        ids = [t.task_id for t in state.tasks]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate workflow task")
        current = state.current_task()
        if current is None or not binding.required_task_artifacts:
            raise ValueError("Required task absent")
        for workflow_task in state.tasks:
            if tuple(workflow_task.required_artifacts) != binding.required_task_artifacts:
                raise ValueError("Task artifact policy mismatch")
        if tuple(state.required_artifacts) != binding.required_workflow_artifacts:
            raise ValueError("Workflow artifact policy mismatch")
        relevant = [
            c
            for c in state.checkpoints
            if c.task_id == binding.task_id and c.phase == WorkflowPhase.REFACTOR
        ]
        if not relevant or relevant[-1].status not in {
            WorkflowCheckpointStatus.COMPLETE,
            WorkflowCheckpointStatus.APPROVED,
        }:
            raise ValueError("Matching completion checkpoint absent")
        with tempfile.TemporaryDirectory(prefix="pm-kernel-snapshot-") as directory:
            root = Path(directory)
            for relative, data in artifacts:
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            state.workspace_root = str(root)
            for workflow_task in state.tasks:
                workflow_task.artifact_dir = str(root / self._relative(workflow_task.artifact_dir))
            for required in state.required_artifacts:
                self._relative(required)
            presence = task_artifact_presence(current, state.workspace_root)
            if not presence or not all(presence.values()):
                raise ValueError("Task evidence missing")
            for phase in (WorkflowPhase.PLAN, WorkflowPhase.IMPLEMENT, WorkflowPhase.REFACTOR):
                if validate_phase_entry(state, phase):
                    raise ValueError("Kernel phase gate denied")
            if binding.workflow_scope and validate_phase_entry(state, WorkflowPhase.COMPLETE):
                raise ValueError("Workflow-wide completion gate denied")
        return VerifiedCompletion(
            project_id,
            task["task_id"],
            task["version"],
            policy["id"],
            policy["version"],
            raw,
            sha,
            "workflow-kernel:"
            + ("workflow-evidence-shape" if binding.workflow_scope else "task-evidence-shape"),
        )
