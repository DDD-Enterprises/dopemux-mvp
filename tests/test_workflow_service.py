import json
from pathlib import Path

from dopemux.workflow import WorkflowCheckpointStatus, WorkflowKernel, WorkflowPhase


def _configure_env(monkeypatch, workspace: Path, *, family_root: Path | None = None, instance_id: str = "A") -> None:
    monkeypatch.setenv("DOPEMUX_WORKSPACE_ROOT", str(workspace))
    monkeypatch.setenv("DOPEMUX_MAIN_REPO", str(family_root or workspace))
    monkeypatch.setenv("DOPEMUX_INSTANCE_ID", instance_id)


def test_init_workflow_creates_local_brief_when_no_packet_exists(monkeypatch, tmp_path: Path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _configure_env(monkeypatch, workspace)
    monkeypatch.setattr(
        WorkflowKernel,
        "probe_pm_authority",
        lambda self: {"authority": "local-mirror", "reachable": False, "url": "http://localhost:8000"},
    )

    kernel = WorkflowKernel(workspace)
    state = kernel.init_workflow(prompt="Ship the workflow kit")

    assert state.brief_source == "local-brief"
    assert state.brief_path is not None
    assert Path(state.brief_path).exists()
    payload = json.loads(kernel.state_path(state.workflow_id).read_text(encoding="utf-8"))
    assert payload["workflow_id"] == state.workflow_id
    assert payload["phase"] == WorkflowPhase.BRIEF.value


def test_resolve_prefers_workspace_ancestry_and_instance(monkeypatch, tmp_path: Path):
    family_root = tmp_path / "family"
    main_workspace = family_root / "main"
    worker_workspace = family_root / "worktrees" / "B"
    main_workspace.mkdir(parents=True)
    worker_workspace.mkdir(parents=True)

    monkeypatch.setattr(
        WorkflowKernel,
        "probe_pm_authority",
        lambda self: {"authority": "local-mirror", "reachable": False, "url": "http://localhost:8000"},
    )

    _configure_env(monkeypatch, main_workspace, family_root=family_root, instance_id="A")
    main_kernel = WorkflowKernel(main_workspace)
    main_state = main_kernel.init_workflow(prompt="Main workspace workflow", force_new=True)

    _configure_env(monkeypatch, worker_workspace, family_root=family_root, instance_id="B")
    worker_kernel = WorkflowKernel(worker_workspace)
    worker_state = worker_kernel.init_workflow(prompt="Worker workflow", force_new=True)

    nested_worker = worker_workspace / "src"
    nested_worker.mkdir()
    _configure_env(monkeypatch, worker_workspace, family_root=family_root, instance_id="B")
    resolving_kernel = WorkflowKernel(nested_worker)
    resolved = resolving_kernel.resolve()

    assert resolved is not None
    assert resolved.workflow_id == worker_state.workflow_id
    assert resolved.workflow_id != main_state.workflow_id


def test_apply_response_text_records_checkpoint_and_completion(monkeypatch, tmp_path: Path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _configure_env(monkeypatch, workspace)
    monkeypatch.setattr(
        WorkflowKernel,
        "probe_pm_authority",
        lambda self: {"authority": "local-mirror", "reachable": False, "url": "http://localhost:8000"},
    )

    kernel = WorkflowKernel(workspace)
    state = kernel.init_workflow(prompt="Finish the workflow")
    state = kernel.apply_response_text(
        state,
        '<workflow-checkpoint phase="research" status="complete" task="task-001" summary="Research done" />',
    )

    assert state.checkpoints[-1].phase == WorkflowPhase.RESEARCH
    assert state.checkpoints[-1].status == WorkflowCheckpointStatus.COMPLETE

    state = kernel.apply_response_text(state, "<promise>WORKFLOW_COMPLETE</promise>")
    assert state.phase == WorkflowPhase.COMPLETE
    assert state.status.value == "complete"
