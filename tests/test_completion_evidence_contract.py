import pytest

from dopemux.claude.native_hooks import NativeHookAdapter
from dopemux.workflow import WorkflowKernel, WorkflowPhase, WorkflowState, WorkflowTask


@pytest.fixture
def ready(tmp_path, monkeypatch):
    monkeypatch.setenv("DOPEMUX_WORKSPACE_ROOT", str(tmp_path))
    monkeypatch.setenv("DOPEMUX_MAIN_REPO", str(tmp_path))
    state = WorkflowState.new(
        workflow_id="evidence",
        workspace_root=tmp_path,
        instance_id="A",
        mode="internal",
        max_iterations=10,
        max_minutes=60,
        completion_token="DONE",
    )
    folder = tmp_path / "task"
    folder.mkdir()
    (folder / "plan.md").write_text("Evidence")
    (tmp_path / "proof.json").write_text("{}")
    state.tasks = [
        WorkflowTask(
            task_id="A",
            title="Task",
            status="done",
            artifact_dir=str(folder),
            required_artifacts=["plan"],
        )
    ]
    state.current_task_id = "A"
    state.required_artifacts = ["proof.json"]
    return WorkflowKernel(tmp_path), state, tmp_path


@pytest.mark.parametrize("kind", ["directory", "empty", "outside", "symlink"])
def test_workflow_completion_requires_contained_nonempty_regular_evidence(ready, kind):
    kernel, state, root = ready
    proof = root / "proof.json"
    proof.unlink()
    if kind == "directory":
        proof.mkdir()
    elif kind == "empty":
        proof.touch()
    else:
        outside = root.parent / "outside.json"
        outside.write_text("{}")
        if kind == "outside":
            state.required_artifacts = ["../outside.json"]
        else:
            proof.symlink_to(outside)
    kernel.apply_response_text(state, "DONE")
    assert state.status.value == "active"


@pytest.mark.parametrize("kind", ["missing", "empty", "no_requirements", "symlink"])
def test_completion_rechecks_each_tasks_evidence(ready, kind):
    kernel, state, root = ready
    task = state.tasks[0]
    artifact = root / "task/plan.md"
    artifact.unlink()
    if kind == "empty":
        artifact.touch()
    elif kind == "no_requirements":
        task.required_artifacts = []
    elif kind == "symlink":
        outside = root.parent / "outside.md"
        outside.write_text("Evidence")
        artifact.symlink_to(outside)
    kernel.apply_response_text(state, "DONE")
    assert state.status.value == "active"


def test_rejection_retains_claimed_checkpoint_and_current_identity(ready):
    kernel, state, _ = ready
    kernel.apply_response_text(
        state, '<workflow-checkpoint phase="complete" status="complete" task_id="B"/>'
    )
    rejected = state.history[-1]
    assert rejected["details"]["checkpoint"]["task_id"] == "B"
    assert rejected["details"]["checkpoint"]["phase"] == "complete"
    assert rejected["details"]["current_task_id"] == "A"


def test_stop_message_distinguishes_pause_from_completion(ready, monkeypatch):
    kernel, state, root = ready
    state.phase = WorkflowPhase.BRIEF
    adapter = NativeHookAdapter(root)
    adapter.kernel = kernel
    monkeypatch.setattr(adapter, "_active_state", lambda: state)
    _, response = adapter._on_stop(
        {
            "response": '<workflow-checkpoint phase="brief" status="skipped" task_id="A"/>'
        }
    )
    assert "paused" in response["systemMessage"].lower()
    assert state.status.value == "active"


def test_taskless_snapshot_can_still_pause(ready):
    kernel, state, _ = ready
    state.tasks = []
    state.current_task_id = None
    kernel.apply_response_text(
        state, '<workflow-checkpoint phase="brief" status="skipped"/>'
    )
    loaded = WorkflowState.from_dict(state.to_dict())
    assert loaded.can_stop()
    assert loaded.status.value == "active"


def test_complete_with_actual_configured_evidence(ready):
    kernel, state, _ = ready
    kernel.apply_response_text(state, "DONE")
    assert state.status.value == "complete"
