import pytest

from dopemux.workflow import WorkflowKernel, WorkflowPhase, WorkflowState, WorkflowTask
from dopemux.workflow.models import contains_completion_token
from dopemux.claude.native_hooks import NativeHookAdapter


@pytest.fixture
def workflow(tmp_path, monkeypatch):
    monkeypatch.setenv("DOPEMUX_WORKSPACE_ROOT", str(tmp_path))
    monkeypatch.setenv("DOPEMUX_MAIN_REPO", str(tmp_path))
    state = WorkflowState.new(
        workflow_id="truth",
        workspace_root=tmp_path,
        instance_id="A",
        mode="internal",
        max_iterations=10,
        max_minutes=60,
        completion_token="DONE",
    )
    state.tasks = [WorkflowTask(task_id="A", title="Current", status="todo")]
    state.current_task_id = "A"
    state.required_artifacts = ["proof.json"]
    return WorkflowKernel(tmp_path), state, tmp_path


@pytest.mark.parametrize(
    "text",
    [
        "not DONE",
        '"DONE"',
        "> DONE",
        "```\nDONE\n```",
        "explain <promise>DONE</promise>",
    ],
)
def test_prose_is_not_completion(text):
    assert not contains_completion_token(text, "DONE")


@pytest.mark.parametrize("text", ["DONE", "<promise>DONE</promise>"])
def test_completion_requires_all_evidence(workflow, text):
    kernel, state, root = workflow
    kernel.apply_response_text(state, text)
    assert state.status.value == "active"
    state.tasks[0].status = "done"
    kernel.apply_response_text(state, text)
    assert state.status.value == "active"
    (root / "proof.json").write_text("{}")
    kernel.apply_response_text(state, text)
    assert state.status.value == "active"
    task = state.tasks[0]
    task.artifact_dir = str(root / "task")
    artifact_dir = root / "task"
    artifact_dir.mkdir()
    for name in task.required_artifacts:
        (artifact_dir / f"{name}.md").write_text("Task evidence")
    kernel.apply_response_text(state, text)
    assert kernel.load(state.workflow_id).status.value == "complete"


@pytest.mark.parametrize("task", ["A", "B"])
def test_checkpoint_does_not_self_certify_task_completion(workflow, task):
    kernel, state, _ = workflow
    kernel.apply_response_text(
        state,
        f'<workflow-checkpoint phase="complete" status="complete" task_id="{task}"/>',
    )
    assert state.tasks[0].status == "todo"


@pytest.mark.parametrize("task_id", ["A", "B"])
def test_only_matching_task_can_complete_with_required_evidence(workflow, task_id):
    kernel, state, root = workflow
    task = state.tasks[0]
    task.artifact_dir = str(root)
    task.required_artifacts = ["plan"]
    state.phase = WorkflowPhase.REFACTOR
    kernel.apply_response_text(
        state, '<workflow-checkpoint phase="implement" status="complete" task_id="A"/>'
    )
    checkpoint = (
        f'<workflow-checkpoint phase="refactor" status="complete" task_id="{task_id}"/>'
    )
    kernel.apply_response_text(state, checkpoint)
    assert task.status == "todo"
    (root / "plan.md").write_text("Evidence")
    kernel.apply_response_text(state, checkpoint)
    assert task.status == ("done" if task_id == "A" else "todo")
    # A safe pause does not claim the workflow is complete.
    assert state.status.value == "active"


def test_later_rejection_replaces_approval(workflow):
    _, state, _ = workflow
    state.record_checkpoint("plan_review", True, task_id="A")
    state.record_checkpoint("plan_review", False, task_id="A")
    assert state.validate_phase_transition(WorkflowPhase.IMPLEMENT)


def test_history_prose_cannot_authorize_stop(workflow):
    _, state, _ = workflow
    state.record_event("note", "Do not emit DONE")
    assert not state.can_stop()


def test_other_task_checkpoint_cannot_authorize_stop(workflow):
    _, state, _ = workflow
    state.record_checkpoint("brief", True, task_id="B")
    assert not state.can_stop()


def test_stop_still_allows_honest_pause_but_not_unverified_token(workflow, monkeypatch):
    kernel, state, root = workflow
    adapter = NativeHookAdapter(root)
    monkeypatch.setattr(adapter, "_active_state", lambda: state)
    adapter.kernel = kernel
    _, response = adapter._on_stop({"response": "DONE"})
    assert response.get("decision") == "block"
    _, response = adapter._on_stop(
        {
            "response": '<workflow-checkpoint phase="brief" status="skipped" task_id="A"/>'
        }
    )
    assert response.get("decision") != "block"
    assert state.status.value == "active"
