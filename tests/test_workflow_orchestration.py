import subprocess
from pathlib import Path
from types import SimpleNamespace

from dopemux.workflow import WorkflowKernel
from dopemux.workflow.orchestration import WorkflowOrchestrator


class FakeInstanceManager:
    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root

    def get_next_available_instance(self, running):
        return ("B", 4310)

    def get_instance_env_vars(self, instance_id, port_base, worktree_path):
        return {
            "DOPEMUX_INSTANCE_ID": instance_id,
            "DOPEMUX_PORT_BASE": str(port_base),
            "DOPEMUX_WORKSPACE_ROOT": str(worktree_path),
        }

    def create_worktree(self, instance_id, branch_name):
        path = self.workspace_root / "worktrees" / instance_id
        path.mkdir(parents=True, exist_ok=True)
        return path


class FakeTmuxController:
    def __init__(self) -> None:
        self.calls = []

    def get_active_session_name(self):
        return "dopemux-main"

    def new_window(self, **kwargs):
        self.calls.append(kwargs)


def _state(monkeypatch, tmp_path: Path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    monkeypatch.setenv("DOPEMUX_WORKSPACE_ROOT", str(workspace))
    monkeypatch.setenv("DOPEMUX_MAIN_REPO", str(workspace))
    monkeypatch.setenv("DOPEMUX_INSTANCE_ID", "A")
    monkeypatch.setattr(
        WorkflowKernel,
        "probe_pm_authority",
        lambda self: {"authority": "local-mirror", "reachable": False, "url": "http://localhost:8000"},
    )
    kernel = WorkflowKernel(workspace)
    state = kernel.init_workflow(prompt="Implement isolated worker support")
    task = state.current_task()
    assert task is not None
    task.verification_commands = ["pytest -q tests/test_workflow_service.py"]
    return kernel, state, task, workspace


def test_build_worker_launch_spec_includes_workflow_context(monkeypatch, tmp_path: Path):
    _, state, task, workspace = _state(monkeypatch, tmp_path)
    tmux = FakeTmuxController()
    manager = FakeInstanceManager(workspace)
    from dopemux.workflow import orchestration
    monkeypatch.setattr(
        orchestration,
        "detect_instances_sync",
        lambda workspace_root: [],
    )

    orchestrator = WorkflowOrchestrator(
        workspace,
        tmux_controller=tmux,
        instance_manager=manager,
    )
    spec = orchestrator.build_worker_launch_spec(state, task)

    assert spec.instance_id == "B"
    assert spec.branch_name.startswith("codex/workflow-")
    assert "--role workflow-executor" in spec.command
    assert spec.environment["DOPEMUX_WORKFLOW_ID"] == state.workflow_id
    assert spec.environment["DOPEMUX_WORKFLOW_TASK_ID"] == task.task_id


def test_spawn_worker_creates_worktree_and_tmux_window(monkeypatch, tmp_path: Path):
    _, state, task, workspace = _state(monkeypatch, tmp_path)
    tmux = FakeTmuxController()
    manager = FakeInstanceManager(workspace)
    from dopemux.workflow import orchestration
    monkeypatch.setattr(
        orchestration,
        "detect_instances_sync",
        lambda workspace_root: [],
    )

    orchestrator = WorkflowOrchestrator(
        workspace,
        tmux_controller=tmux,
        instance_manager=manager,
    )
    spec = orchestrator.spawn_worker(state, task)

    assert spec.worktree_path.exists()
    assert tmux.calls
    assert tmux.calls[0]["window_name"] == f"workflow-{task.task_id}"


def test_validate_task_completion_marks_task_done(monkeypatch, tmp_path: Path):
    kernel, state, task, workspace = _state(monkeypatch, tmp_path)
    for filename in (
        "research.md",
        "research-review.md",
        "plan.md",
        "plan-review.md",
    ):
        (Path(task.artifact_dir) / filename).write_text("# artifact\n", encoding="utf-8")

    def _runner(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=args,
            returncode=0,
            stdout="ok",
            stderr="",
        )

    tmux = FakeTmuxController()
    manager = FakeInstanceManager(workspace)
    from dopemux.workflow import orchestration
    monkeypatch.setattr(
        orchestration,
        "detect_instances_sync",
        lambda workspace_root: [],
    )
    orchestrator = WorkflowOrchestrator(
        workspace,
        tmux_controller=tmux,
        instance_manager=manager,
    )

    result = orchestrator.validate_task_completion(state, task, runner=_runner)
    reloaded = kernel.load(state.workflow_id)

    assert result["verification_passed"] is True
    assert result["task_status"] == "done"
    assert reloaded.current_task().status == "done"
