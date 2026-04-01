from pathlib import Path

from dopemux.pm.models import PMTaskStatus
from dopemux.workflow import (
    WorkflowPhase,
    WorkflowState,
    WorkflowTask,
)


def test_workflow_state_round_trip_preserves_required_fields(tmp_path):
    state = WorkflowState.new(
        workflow_id="wf-main",
        workspace_root=tmp_path,
        instance_id="main",
        mode="internal",
        max_iterations=7,
        max_minutes=30,
        completion_token="WORKFLOW_COMPLETE",
    )

    payload = state.to_dict()

    assert payload["workflow_id"] == "wf-main"
    assert payload["workspace_root"] == str(tmp_path.resolve())
    assert payload["instance_id"] == "main"
    assert payload["mode"] == "internal"
    assert payload["phase"] == "brief"
    assert payload["current_task_id"] is None
    assert payload["iteration"] == 0
    assert payload["max_iterations"] == 7
    assert payload["max_minutes"] == 30
    assert payload["completion_token"] == "WORKFLOW_COMPLETE"
    assert payload["status"] == "active"
    assert payload["history"]

    restored = WorkflowState.from_dict(payload)
    assert restored.to_dict() == payload


def test_phase_transition_requires_approved_review_checkpoints(tmp_path):
    state = WorkflowState.new(
        workflow_id="wf-gates",
        workspace_root=tmp_path,
        instance_id="main",
        mode="internal",
        max_iterations=10,
        max_minutes=60,
        completion_token="DONE",
    )

    assert state.validate_phase_transition(WorkflowPhase.PLAN) == (
        "Cannot enter plan without an approved research_review checkpoint."
    )
    assert state.validate_phase_transition(WorkflowPhase.IMPLEMENT) == (
        "Cannot enter implement/refactor without an approved plan_review checkpoint."
    )

    state.record_checkpoint("research_review", True, message="research_review approved")
    assert state.validate_phase_transition(WorkflowPhase.PLAN) is None

    state.record_checkpoint("plan_review", True, message="plan_review approved")
    assert state.validate_phase_transition(WorkflowPhase.IMPLEMENT) is None


def test_complete_gate_requires_artifacts_and_completed_tasks(tmp_path):
    state = WorkflowState.new(
        workflow_id="wf-complete",
        workspace_root=tmp_path,
        instance_id="main",
        mode="internal",
        max_iterations=10,
        max_minutes=60,
        completion_token="DONE",
    )
    state.record_checkpoint("plan_review", True, message="plan_review approved")
    state.required_artifacts = ["reports/proof.json"]
    state.tasks = [
        WorkflowTask(task_id="task-1", title="Task 1", status=PMTaskStatus.TODO),
    ]

    assert state.validate_phase_transition(WorkflowPhase.COMPLETE) == (
        "Cannot complete while workflow tasks are still incomplete."
    )

    state.tasks[0].status = PMTaskStatus.DONE
    assert state.validate_phase_transition(WorkflowPhase.COMPLETE) == (
        "Cannot complete while required artifacts are missing."
    )

    artifact_path = tmp_path / "reports" / "proof.json"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text("{}", encoding="utf-8")

    assert state.validate_phase_transition(WorkflowPhase.COMPLETE) is None


def test_can_stop_requires_phase_checkpoint_or_completion_token(tmp_path):
    state = WorkflowState.new(
        workflow_id="wf-stop",
        workspace_root=tmp_path,
        instance_id="main",
        mode="internal",
        max_iterations=10,
        max_minutes=60,
        completion_token="DONE",
    )
    assert state.can_stop() is False

    state.record_checkpoint("brief", True, message="brief approved")
    assert state.can_stop() is True

    state = WorkflowState.new(
        workflow_id="wf-stop-token",
        workspace_root=tmp_path,
        instance_id="main",
        mode="internal",
        max_iterations=10,
        max_minutes=60,
        completion_token="DONE",
    )
    state.record_event("completion_notice", "Evidence bundle complete: DONE")
    assert state.can_stop() is True
