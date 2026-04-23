from dopemux.pm.writes import PMActionKind
from dopemux.ui.pm_writes import (
    authority_label,
    render_adapter_confirmation,
    render_write_confirmation,
    render_write_receipt,
)


def test_authority_label_matches_phase1_targets():
    assert authority_label(PMActionKind.METADATA_UPDATE) == "leantime"
    assert authority_label(PMActionKind.WORKFLOW_TRANSITION) == "task-orchestrator"
    assert authority_label(PMActionKind.PROGRESS_LOG) == "conport"
    assert authority_label(PMActionKind.DECISION_LOG) == "conport"


def test_render_metadata_confirmation_names_leantime():
    rendered = render_write_confirmation(
        PMActionKind.METADATA_UPDATE,
        work_item_id="LT-2217",
        fields=["title", "notes"],
    )

    assert "WRITE -> leantime: update ticket metadata" in rendered
    assert "work item: LT-2217" in rendered
    assert "fields: notes, title" in rendered
    assert "Enter commits" in rendered
    assert "Esc cancels" in rendered


def test_render_workflow_confirmation_names_task_orchestrator():
    rendered = render_write_confirmation(
        PMActionKind.WORKFLOW_TRANSITION,
        project_id="proj-9",
        work_item_id="T-203",
        current_state="TODO",
        transition="start",
    )

    assert "WRITE -> task-orchestrator: transition workflow state" in rendered
    assert "project: proj-9" in rendered
    assert "requested transition: start" in rendered


def test_render_progress_and_decision_confirmation_name_conport():
    progress = render_write_confirmation(PMActionKind.PROGRESS_LOG, work_item_id="T-10")
    decision = render_write_confirmation(PMActionKind.DECISION_LOG, work_item_id="T-10")

    assert "WRITE -> conport: record progress" in progress
    assert "WRITE -> conport: commit decision" in decision


def test_render_adapter_confirmation_is_not_presented_as_authority_write():
    rendered = render_adapter_confirmation("replay pm event")

    assert rendered.startswith("ADAPTER -> dopecon-bridge: replay pm event")
    assert "WRITE ->" not in rendered


def test_render_receipts_keep_mirrors_separate():
    metadata_lines = render_write_receipt(PMActionKind.METADATA_UPDATE, identifier="LT-2217")
    workflow_lines = render_write_receipt(PMActionKind.WORKFLOW_TRANSITION, identifier="T-203")
    progress_lines = render_write_receipt(
        PMActionKind.PROGRESS_LOG,
        identifier="T-203",
        mirror_targets={"dope-memory": "chronicle receipt"},
    )
    decision_lines = render_write_receipt(PMActionKind.DECISION_LOG, identifier="T-203")

    assert metadata_lines == ["Updated: leantime metadata for LT-2217"]
    assert workflow_lines == ["Transitioned: task-orchestrator workflow for T-203"]
    assert progress_lines == [
        "Logged: conport progress entry",
        "Mirrored: dope-memory chronicle receipt",
    ]
    assert decision_lines == ["Logged: conport decision entry"]
