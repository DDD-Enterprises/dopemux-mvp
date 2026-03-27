"""Persistence and orchestration helpers for Dopemux workflows."""

from __future__ import annotations

import json
import re
import shlex
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from ..instance_manager import InstanceManager, detect_instances_sync
from ..workspace_detection import get_workspace_root
from .models import ExecutorLaunchSpec, WorkflowState, WorkflowStatus, WorkflowTask


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip()).strip("-")
    return slug or "workflow"


def _atomic_json_write(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        json.dump(payload, handle, indent=2, sort_keys=False)
        handle.write("\n")
        temp_path = Path(handle.name)
    temp_path.replace(path)


class WorkflowStore:
    """Canonical writer for workspace-local workflow state."""

    INDEX_VERSION = 1

    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root.expanduser().resolve()
        self.workflows_dir = self.workspace_root / ".dopemux" / "workflows"
        self.index_path = self.workflows_dir / "index.json"

    @classmethod
    def for_path(cls, start_path: Optional[Path] = None) -> "WorkflowStore":
        if start_path is None:
            return cls(get_workspace_root(None))
        return cls(cls._resolve_explicit_workspace_root(start_path))

    @staticmethod
    def _resolve_explicit_workspace_root(start_path: Path) -> Path:
        current = start_path.expanduser().resolve()
        if current.is_file():
            current = current.parent
        for candidate in (current, *current.parents):
            if (candidate / ".dopemux" / "workflows").exists():
                return candidate
            if (candidate / ".dopetaskroot").exists():
                return candidate
            if (candidate / "pyproject.toml").exists():
                return candidate
            if (candidate / ".git").exists():
                return candidate
        return current

    def _state_path(self, workflow_id: str) -> Path:
        return self.workflows_dir / workflow_id / "state.json"

    def _load_index(self) -> Dict[str, Any]:
        if not self.index_path.exists():
            return {
                "version": self.INDEX_VERSION,
                "updated_at": None,
                "workflows_by_instance": {},
            }
        with self.index_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            raise ValueError(f"Invalid workflow index at {self.index_path}")
        data.setdefault("version", self.INDEX_VERSION)
        data.setdefault("workflows_by_instance", {})
        return data

    def _save_index(self, index: Dict[str, Any]) -> None:
        _atomic_json_write(self.index_path, index)

    def save(self, state: WorkflowState) -> WorkflowState:
        path = self._state_path(state.workflow_id)
        _atomic_json_write(path, state.to_dict())
        index = self._load_index()
        mapping = dict(index.get("workflows_by_instance") or {})
        if state.status == WorkflowStatus.ACTIVE:
            mapping[state.instance_id] = state.workflow_id
        elif mapping.get(state.instance_id) == state.workflow_id:
            mapping.pop(state.instance_id, None)
        index["workflows_by_instance"] = mapping
        index["updated_at"] = state.updated_at
        self._save_index(index)
        return state

    def load(self, workflow_id: str) -> WorkflowState:
        path = self._state_path(workflow_id)
        if not path.exists():
            raise FileNotFoundError(f"Workflow state not found: {workflow_id}")
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        return WorkflowState.from_dict(payload)

    def list_states(self) -> Iterable[WorkflowState]:
        if not self.workflows_dir.exists():
            return []
        states = []
        for state_path in sorted(self.workflows_dir.glob("*/state.json")):
            try:
                with state_path.open("r", encoding="utf-8") as handle:
                    states.append(WorkflowState.from_dict(json.load(handle)))
            except (OSError, ValueError, json.JSONDecodeError):
                continue
        return states

    def resolve_active(self, instance_id: str) -> Optional[WorkflowState]:
        index = self._load_index()
        workflow_id = (index.get("workflows_by_instance") or {}).get(instance_id)
        if workflow_id:
            return self.load(str(workflow_id))
        candidates = [
            state
            for state in self.list_states()
            if state.instance_id == instance_id and state.status == WorkflowStatus.ACTIVE
        ]
        if not candidates and instance_id != "main":
            candidates = [
                state for state in self.list_states() if state.status == WorkflowStatus.ACTIVE
            ]
        return candidates[0] if len(candidates) == 1 else None

    def create_or_resume(
        self,
        *,
        workflow_id: Optional[str],
        instance_id: str,
        mode: str,
        max_iterations: int,
        max_minutes: int,
        completion_token: str,
    ) -> WorkflowState:
        existing = self.resolve_active(instance_id)
        if existing is not None:
            return existing

        resolved_id = workflow_id
        if not resolved_id:
            resolved_id = _slugify(f"{self.workspace_root.name}-{instance_id}")
        path = self._state_path(resolved_id)
        if path.exists():
            state = self.load(resolved_id)
        else:
            state = WorkflowState.new(
                workflow_id=resolved_id,
                workspace_root=self.workspace_root,
                instance_id=instance_id,
                mode=mode,
                max_iterations=max_iterations,
                max_minutes=max_minutes,
                completion_token=completion_token,
            )
        return self.save(state)

    def cancel(self, state: WorkflowState, reason: str) -> WorkflowState:
        state.status = WorkflowStatus.CANCELLED
        state.record_event("workflow_cancelled", reason or "Workflow cancelled")
        return self.save(state)

    def inspect(self, state: WorkflowState) -> Dict[str, Any]:
        checkpoints: Dict[str, Optional[bool]] = {}
        for checkpoint in ("brief", "research_review", "plan_review", state.phase.value):
            latest = None
            for entry in reversed(state.history):
                if entry.checkpoint == checkpoint:
                    latest = entry.approved
                    break
            checkpoints[checkpoint] = latest
        return {
            "workflow_id": state.workflow_id,
            "workspace_root": state.workspace_root,
            "instance_id": state.instance_id,
            "mode": state.mode,
            "status": state.status.value,
            "phase": state.phase.value,
            "current_task_id": state.current_task_id,
            "iteration": state.iteration,
            "max_iterations": state.max_iterations,
            "max_minutes": state.max_minutes,
            "completion_token": state.completion_token,
            "checkpoints": checkpoints,
            "validation": state.validation_summary(),
            "history_count": len(state.history),
        }


class WorkflowOrchestrator:
    """Manager/executor orchestration helper built on existing worktree primitives."""

    def __init__(
        self,
        workspace_root: Path,
        instance_manager: Optional[InstanceManager] = None,
    ):
        self.workspace_root = workspace_root.expanduser().resolve()
        self.instance_manager = instance_manager or InstanceManager(self.workspace_root)

    def _choose_instance_id(self) -> str:
        running = detect_instances_sync(self.workspace_root)
        instance_id, _ = self.instance_manager.get_next_available_instance(running)
        return instance_id

    def prepare_executor_launch(
        self,
        state: WorkflowState,
        task: WorkflowTask,
        *,
        instance_id: Optional[str] = None,
        branch_name: Optional[str] = None,
        extra_args: Optional[Iterable[str]] = None,
    ) -> ExecutorLaunchSpec:
        selected_instance = instance_id or task.instance_id or self._choose_instance_id()
        selected_branch = branch_name or f"workflow/{state.workflow_id}-{task.task_id}"
        if selected_instance in {"main", "", "A"}:
            worktree_path = self.workspace_root
            port_base = self.instance_manager.AVAILABLE_PORTS[0]
            env = self.instance_manager.get_instance_env_vars("A", port_base, None)
            normalized_instance = "main"
        else:
            worktree_path = Path(task.worktree_path) if task.worktree_path else self.instance_manager.create_worktree(
                selected_instance,
                selected_branch,
            )
            port_base = self.instance_manager._instance_id_to_port(selected_instance)
            env = self.instance_manager.get_instance_env_vars(selected_instance, port_base, worktree_path)
            normalized_instance = selected_instance

        command = ["dopemux", "start", "--role", "workflow-executor"]
        for arg in extra_args or []:
            command.append(str(arg))

        task.instance_id = normalized_instance
        task.worktree_path = str(worktree_path)
        return ExecutorLaunchSpec(
            workflow_id=state.workflow_id,
            task_id=task.task_id,
            instance_id=normalized_instance,
            branch_name=selected_branch,
            worktree_path=str(worktree_path),
            command=command,
            env={str(key): str(value) for key, value in env.items()},
        )

    @staticmethod
    def shell_command(spec: ExecutorLaunchSpec) -> str:
        return f"cd {shlex.quote(spec.worktree_path)} && {shlex.join(spec.command)}"
