from pathlib import Path

from dopemux.workflow import WorkflowOrchestrator, WorkflowState, WorkflowTask


class DummyInstanceManager:
    AVAILABLE_PORTS = [3000, 3030]

    def create_worktree(self, instance_id: str, branch_name: str) -> Path:
        return Path(f"/tmp/{instance_id}/{branch_name.replace('/', '-')}")

    def get_instance_env_vars(self, instance_id: str, port_base: int, worktree_path):
        return {
            "DOPEMUX_INSTANCE_ID": instance_id,
            "DOPEMUX_WORKSPACE_ROOT": str(worktree_path or "/tmp/main"),
            "DOPEMUX_PORT_BASE": str(port_base),
        }

    def get_next_available_instance(self, running_instances):
        return ("B", 3030)

    def _instance_id_to_port(self, instance_id: str) -> int:
        return 3030


def test_prepare_executor_launch_reuses_existing_instance_conventions(monkeypatch, tmp_path):
    monkeypatch.setattr("dopemux.workflow.store.detect_instances_sync", lambda workspace_root: [])
    orchestrator = WorkflowOrchestrator(tmp_path, instance_manager=DummyInstanceManager())
    state = WorkflowState.new(
        workflow_id="wf-1",
        workspace_root=tmp_path,
        instance_id="main",
        mode="internal",
        max_iterations=5,
        max_minutes=30,
        completion_token="DONE",
    )
    task = WorkflowTask(task_id="task-1", title="Implement")

    spec = orchestrator.prepare_executor_launch(state, task)

    assert spec.instance_id == "B"
    assert spec.command == ["dopemux", "start", "--role", "workflow-executor"]
    assert spec.worktree_path.endswith("workflow-wf-1-task-1")
    assert spec.env["DOPEMUX_INSTANCE_ID"] == "B"
    assert task.worktree_path == spec.worktree_path


def test_shell_command_uses_worktree_and_role(tmp_path):
    orchestrator = WorkflowOrchestrator(tmp_path, instance_manager=DummyInstanceManager())
    state = WorkflowState.new(
        workflow_id="wf-2",
        workspace_root=tmp_path,
        instance_id="main",
        mode="internal",
        max_iterations=5,
        max_minutes=30,
        completion_token="DONE",
    )
    task = WorkflowTask(task_id="task-2", title="Review")

    spec = orchestrator.prepare_executor_launch(state, task)
    shell_command = orchestrator.shell_command(spec)

    assert "dopemux start --role workflow-executor" in shell_command
    assert "cd " in shell_command
