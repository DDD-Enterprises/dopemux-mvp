from pathlib import Path

from dopemux.workflow import (
    WorkflowCheckpoint,
    WorkflowCheckpointStatus,
    WorkflowPhase,
    WorkflowState,
    WorkflowStatus,
    WorkflowTask,
    parse_workflow_checkpoint,
    validate_phase_entry,
)
from dopemux.workflow.models import utc_now_iso


def _build_state(tmp_path: Path) -> WorkflowState:
    task_dir = tmp_path / "tasks" / "task-001"
    task_dir.mkdir(parents=True)
    task = WorkflowTask(
        task_id="task-001",
        title="Ship workflow kit",
        summary="Implement the next slice",
        artifact_dir=str(task_dir),
        verification_commands=["pytest -q"],
    )
    now = utc_now_iso()
    return WorkflowState(
        workflow_id="wf-001",
        workspace_root=str(tmp_path),
        instance_id="A",
        mode="manager",
        phase=WorkflowPhase.BRIEF,
        current_task_id=task.task_id,
        iteration=0,
        max_iterations=0,
        max_minutes=0,
        completion_token="WORKFLOW_COMPLETE",
        started_at=now,
        updated_at=now,
        status=WorkflowStatus.ACTIVE,
        tasks=[task],
    )


def test_parse_workflow_checkpoint_extracts_verification_commands():
    checkpoint = parse_workflow_checkpoint(
        '<workflow-checkpoint phase="plan_review" status="approved" '
        'task="task-001" summary="Plan approved" artifact="/tmp/plan-review.md" '
        'verification="pytest -q;;ruff check src" />'
    )

    assert checkpoint is not None
    assert checkpoint.phase == WorkflowPhase.PLAN_REVIEW
    assert checkpoint.status == WorkflowCheckpointStatus.APPROVED
    assert checkpoint.task_id == "task-001"
    assert checkpoint.artifact_path == "/tmp/plan-review.md"
    assert checkpoint.verification_commands == ["pytest -q", "ruff check src"]


def test_validate_phase_entry_enforces_review_gates(tmp_path: Path):
    state = _build_state(tmp_path)

    assert "Plan phase requires an approved research review." in validate_phase_entry(
        state, WorkflowPhase.PLAN
    )
    assert "Implementation requires an approved plan review." in validate_phase_entry(
        state, WorkflowPhase.IMPLEMENT
    )

    state.add_checkpoint(
        WorkflowCheckpoint(
            phase=WorkflowPhase.RESEARCH_REVIEW,
            status=WorkflowCheckpointStatus.APPROVED,
            task_id="task-001",
            summary="Research approved",
        )
    )
    assert validate_phase_entry(state, WorkflowPhase.PLAN) == []

    state.add_checkpoint(
        WorkflowCheckpoint(
            phase=WorkflowPhase.PLAN_REVIEW,
            status=WorkflowCheckpointStatus.APPROVED,
            task_id="task-001",
            summary="Plan approved",
        )
    )
    assert validate_phase_entry(state, WorkflowPhase.IMPLEMENT) == []


def test_complete_gate_requires_closed_tasks_artifacts_and_verification(tmp_path: Path):
    state = _build_state(tmp_path)
    task = state.current_task()
    assert task is not None

    failures = validate_phase_entry(state, WorkflowPhase.COMPLETE)
    assert any("tasks remain open" in failure for failure in failures)
    assert any("missing required artifacts" in failure for failure in failures)
    assert any("have not passed" in failure for failure in failures)

    for filename in (
        "research.md",
        "research-review.md",
        "plan.md",
        "plan-review.md",
    ):
        (Path(task.artifact_dir) / filename).write_text("# artifact\n", encoding="utf-8")

    task.status = "done"
    task.metadata["verification_passed"] = True

    assert validate_phase_entry(state, WorkflowPhase.COMPLETE) == []
