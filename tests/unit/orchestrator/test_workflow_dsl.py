import json
from pathlib import Path

import yaml

from dopemux.orchestrator.workflow_dsl import (
    load_workflow_dsl_file,
    validate_workflow_dsl_file,
)


def _write_yaml(path: Path, payload: dict) -> Path:
    path.write_text(yaml.safe_dump(payload, sort_keys=True), encoding="utf-8")
    return path


def _workflow_payload() -> dict:
    return {
        "schema_version": "1",
        "id": "daily-operator",
        "title": "Daily operator workflow",
        "initial_state": "queued",
        "states": [
            {"id": "queued", "title": "Queued"},
            {"id": "active", "title": "Active"},
            {"id": "done", "title": "Done", "terminal": True},
        ],
        "transitions": [
            {
                "id": "preview_start",
                "from": "queued",
                "to": "active",
                "capability": "orchestrator.transition.preview",
                "receipt_required": True,
            },
            {
                "id": "preview_finish",
                "from": "active",
                "to": "done",
                "capability": "orchestrator.transition.preview",
                "receipt_required": True,
            },
        ],
    }


def test_workflow_dsl_loader_returns_stable_model(tmp_path: Path) -> None:
    path = _write_yaml(tmp_path / "workflow.yaml", _workflow_payload())

    workflow = load_workflow_dsl_file(path)

    assert workflow.workflow_id == "daily-operator"
    assert workflow.initial_state == "queued"
    assert [state.state_id for state in workflow.states] == [
        "queued",
        "active",
        "done",
    ]
    assert workflow.to_dict()["transitions"][0]["capability"] == (
        "orchestrator.transition.preview"
    )


def test_workflow_dsl_validator_accepts_policy_registered_workflow(
    tmp_path: Path,
) -> None:
    path = _write_yaml(tmp_path / "workflow.yaml", _workflow_payload())

    report = validate_workflow_dsl_file(path)

    assert report.valid is True
    assert report.status == "PASS"
    assert report.errors == []
    assert report.details["state_count"] == 3
    assert report.details["transition_count"] == 2


def test_workflow_dsl_validator_accepts_json_input(tmp_path: Path) -> None:
    path = tmp_path / "workflow.json"
    path.write_text(json.dumps(_workflow_payload()), encoding="utf-8")

    report = validate_workflow_dsl_file(path)

    assert report.valid is True
    assert report.status == "PASS"


def test_workflow_dsl_validator_rejects_duplicate_states(tmp_path: Path) -> None:
    payload = _workflow_payload()
    payload["states"].append({"id": "queued", "title": "Duplicate"})
    path = _write_yaml(tmp_path / "workflow.yaml", payload)

    report = validate_workflow_dsl_file(path)

    assert report.valid is False
    assert any(error["code"] == "WORKFLOW_DSL_DUPLICATE_STATE" for error in report.errors)


def test_workflow_dsl_validator_rejects_missing_transition_target(
    tmp_path: Path,
) -> None:
    payload = _workflow_payload()
    payload["transitions"][0]["to"] = "missing"
    path = _write_yaml(tmp_path / "workflow.yaml", payload)

    report = validate_workflow_dsl_file(path)

    assert report.valid is False
    assert any(error["code"] == "WORKFLOW_DSL_UNKNOWN_TO_STATE" for error in report.errors)


def test_workflow_dsl_validator_rejects_transition_from_terminal_state(
    tmp_path: Path,
) -> None:
    payload = _workflow_payload()
    payload["transitions"].append(
        {
            "id": "bad_terminal_edge",
            "from": "done",
            "to": "active",
            "capability": "orchestrator.transition.preview",
            "receipt_required": True,
        }
    )
    path = _write_yaml(tmp_path / "workflow.yaml", payload)

    report = validate_workflow_dsl_file(path)

    assert report.valid is False
    assert any(
        error["code"] == "WORKFLOW_DSL_TERMINAL_SOURCE"
        for error in report.errors
    )


def test_workflow_dsl_validator_rejects_unknown_capability(tmp_path: Path) -> None:
    payload = _workflow_payload()
    payload["transitions"][0]["capability"] = "orchestrator.future.unknown"
    path = _write_yaml(tmp_path / "workflow.yaml", payload)

    report = validate_workflow_dsl_file(path)

    assert report.valid is False
    assert any(
        error["code"] == "WORKFLOW_DSL_UNKNOWN_CAPABILITY"
        for error in report.errors
    )


def test_workflow_dsl_validator_requires_gates_for_write_capabilities(
    tmp_path: Path,
) -> None:
    payload = _workflow_payload()
    payload["transitions"][0].update(
        {
            "capability": "orchestrator.transition.apply",
            "approval_required": False,
            "receipt_required": False,
        }
    )
    path = _write_yaml(tmp_path / "workflow.yaml", payload)

    report = validate_workflow_dsl_file(path)

    assert report.valid is False
    assert any(
        error["code"] == "WORKFLOW_DSL_WRITE_APPROVAL_REQUIRED"
        for error in report.errors
    )
    assert any(
        error["code"] == "WORKFLOW_DSL_WRITE_RECEIPT_REQUIRED"
        for error in report.errors
    )


def test_workflow_dsl_validator_rejects_automatic_write_capability(
    tmp_path: Path,
) -> None:
    payload = _workflow_payload()
    payload["transitions"][0].update(
        {
            "capability": "orchestrator.transition.apply",
            "approval_required": True,
            "receipt_required": True,
            "automatic": True,
        }
    )
    path = _write_yaml(tmp_path / "workflow.yaml", payload)

    report = validate_workflow_dsl_file(path)

    assert report.valid is False
    assert any(
        error["code"] == "WORKFLOW_DSL_AUTOMATIC_CAPABILITY_FORBIDDEN"
        for error in report.errors
    )
