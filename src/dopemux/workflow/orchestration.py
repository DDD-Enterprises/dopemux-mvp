"""Worker orchestration helpers for Dopemux workflows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shlex
import subprocess
from typing import Callable, Dict, Iterable, List, Optional

from ..instance_manager import InstanceManager, detect_instances_sync
from ..tmux.controller import TmuxController
from ..voice import inject_voice_header
from .models import (
    WorkflowCheckpoint,
    WorkflowCheckpointStatus,
    WorkflowPhase,
    WorkflowState,
    WorkflowTask,
)
from .service import WorkflowKernel


@dataclass
class WorkerLaunchSpec:
    """Launch details for a workflow executor."""

    task_id: str
    instance_id: str
    port_base: int
    branch_name: str
    worktree_path: Path
    session_name: str
    window_name: str
    command: str
    environment: Dict[str, str]


class WorkflowOrchestrator:
    """Spawn and validate isolated workflow executor runs."""

    def __init__(
        self,
        workspace_root: Path,
        *,
        tmux_controller: Optional[TmuxController] = None,
        instance_manager: Optional[InstanceManager] = None,
    ) -> None:
        self.workspace_root = workspace_root.resolve()
        self.tmux_controller = tmux_controller or TmuxController()
        self.instance_manager = instance_manager or InstanceManager(self.workspace_root)

    def _next_worker_slot(self) -> tuple[str, int]:
        running = detect_instances_sync(self.workspace_root)
        return self.instance_manager.get_next_available_instance(running)

    def build_worker_launch_spec(self, state: WorkflowState, task: Optional[WorkflowTask] = None) -> WorkerLaunchSpec:
        """Preview the next executor launch without mutating the repo."""
        task = task or state.current_task()
        if task is None:
            raise ValueError("No active task is available for workflow execution.")

        instance_id, port_base = self._next_worker_slot()
        branch_name = f"codex/workflow-{state.workflow_id[:12]}-{task.task_id}"
        worktree_path = self.workspace_root / "worktrees" / instance_id
        environment = self.instance_manager.get_instance_env_vars(
            instance_id,
            port_base,
            worktree_path=worktree_path,
        )
        environment.update(
            {
                "DOPEMUX_WORKFLOW_ID": state.workflow_id,
                "DOPEMUX_WORKFLOW_TASK_ID": task.task_id,
                "DOPEMUX_WORKFLOW_MODE": "executor",
            }
        )
        prompt = inject_voice_header(task.summary, surface="agent")
        command = (
            f"dopemux start --role workflow-executor --no-recovery "
            f"--prompt {shlex.quote(prompt)}"
        )
        session_name = self.tmux_controller.get_active_session_name() or "dopemux"
        return WorkerLaunchSpec(
            task_id=task.task_id,
            instance_id=instance_id,
            port_base=port_base,
            branch_name=branch_name,
            worktree_path=worktree_path,
            session_name=session_name,
            window_name=f"workflow-{task.task_id}",
            command=command,
            environment=environment,
        )

    def spawn_worker(self, state: WorkflowState, task: Optional[WorkflowTask] = None) -> WorkerLaunchSpec:
        """Create an isolated worktree and spawn a workflow executor in tmux."""
        spec = self.build_worker_launch_spec(state, task)
        worktree_path = self.instance_manager.create_worktree(
            spec.instance_id,
            branch_name=spec.branch_name,
        )
        spec = WorkerLaunchSpec(
            task_id=spec.task_id,
            instance_id=spec.instance_id,
            port_base=spec.port_base,
            branch_name=spec.branch_name,
            worktree_path=worktree_path,
            session_name=spec.session_name,
            window_name=spec.window_name,
            command=spec.command,
            environment=spec.environment,
        )
        self.tmux_controller.new_window(
            session=spec.session_name,
            window_name=spec.window_name,
            command=spec.command,
            start_directory=str(worktree_path),
            attach=False,
            environment=spec.environment,
        )
        return spec

    def validate_task_completion(
        self,
        state: WorkflowState,
        task: Optional[WorkflowTask] = None,
        *,
        runner: Optional[Callable[..., subprocess.CompletedProcess]] = None,
    ) -> Dict[str, object]:
        """Validate required artifacts and verification commands for a task."""
        task = task or state.current_task()
        if task is None:
            raise ValueError("No active task is available for validation.")

        kernel = WorkflowKernel(Path(state.active_workspace or state.workspace_root))
        presence = {}
        if task.artifact_dir:
            from .models import task_artifact_presence

            presence = task_artifact_presence(task)
        missing = [stem for stem, exists in presence.items() if not exists]

        command_runner = runner or subprocess.run
        verification_results: List[Dict[str, object]] = []
        all_passed = True
        for command in task.verification_commands:
            completed = command_runner(
                command,
                cwd=str(Path(state.active_workspace or state.workspace_root)),
                shell=True,
                capture_output=True,
                text=True,
                check=False,
            )
            verification_results.append(
                {
                    "command": command,
                    "returncode": completed.returncode,
                    "stdout": completed.stdout,
                    "stderr": completed.stderr,
                }
            )
            if completed.returncode != 0:
                all_passed = False

        task.metadata["verification_passed"] = all_passed
        if not missing and all_passed:
            task.status = "done"
            checkpoint = state.latest_checkpoint(task_id=task.task_id, phase=WorkflowPhase.REFACTOR)
            if checkpoint is None:
                state.add_checkpoint(
                    checkpoint=state.latest_checkpoint(task_id=task.task_id)
                    or WorkflowCheckpoint(
                        phase=WorkflowPhase.REFACTOR,
                        status=WorkflowCheckpointStatus.COMPLETE,
                        task_id=task.task_id,
                        summary="Validation promoted task to done.",
                    )
                )
        else:
            task.status = "blocked"

        kernel.save(state)
        return {
            "missing_artifacts": missing,
            "verification_results": verification_results,
            "verification_passed": all_passed,
            "task_status": task.status,
        }
