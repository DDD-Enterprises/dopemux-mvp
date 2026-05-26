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
        "owner": "dopemux",
        "authority": {"primary_owner": "task-orchestrator"},
        "automation_tier": "T1",
        "triggers": ["manual"],
        "inputs": ["project_id"],
        "steps": [
            {
                "id": "queue",
                "tool": "orchestrator.status.queue",
                "mode": "read",
                "validation": ["queue report returned"],
                "on_failure": "degrade",
            },
            {
                "id": "proof_check",
                "tool": "orchestrator.proof.validate",
                "mode": "analysis",
                "schema_path": "src/dopemux/orchestrator/validation/proof.py",
                "validation": ["proof report returned"],
                "on_failure": "fail_closed",
            },
        ],
        "outputs": ["items", "more_count", "next_token"],
        "approval": {"required": False},
    }


def test_workflow_dsl_loader_returns_stable_model(tmp_path: Path) -> None:
    path = _write_yaml(tmp_path / "workflow.yaml", _workflow_payload())

    workflow = load_workflow_dsl_file(path)

    assert workflow.workflow_id == "daily-operator"
    assert workflow.owner == "dopemux"
    assert workflow.authority_primary_owner == "task-orchestrator"
    assert workflow.automation_tier == "T1"
    assert [step.step_id for step in workflow.steps] == ["queue", "proof_check"]
    assert workflow.to_dict()["steps"][0]["tool"] == "orchestrator.status.queue"


def test_workflow_dsl_validator_accepts_policy_registered_workflow(
    tmp_path: Path,
) -> None:
    path = _write_yaml(tmp_path / "workflow.yaml", _workflow_payload())

    report = validate_workflow_dsl_file(path)

    assert report.valid is True
    assert report.status == "PASS"
    assert report.errors == []
    assert report.details["step_count"] == 2


def test_workflow_dsl_validator_accepts_json_input(tmp_path: Path) -> None:
    path = tmp_path / "workflow.json"
    path.write_text(json.dumps(_workflow_payload()), encoding="utf-8")

    report = validate_workflow_dsl_file(path)

    assert report.valid is True
    assert report.status == "PASS"


def test_workflow_dsl_validator_rejects_missing_authority_owner(
    tmp_path: Path,
) -> None:
    payload = _workflow_payload()
    payload["authority"] = {}
    path = _write_yaml(tmp_path / "workflow.yaml", payload)

    report = validate_workflow_dsl_file(path)

    assert report.valid is False
    assert any(
        error["code"] == "WORKFLOW_DSL_AUTHORITY_OWNER_MISSING"
        for error in report.errors
    )


def test_workflow_dsl_validator_rejects_unknown_tier(tmp_path: Path) -> None:
    payload = _workflow_payload()
    payload["automation_tier"] = "T9000"
    path = _write_yaml(tmp_path / "workflow.yaml", payload)

    report = validate_workflow_dsl_file(path)

    assert report.valid is False
    assert any(error["code"] == "WORKFLOW_DSL_UNKNOWN_TIER" for error in report.errors)


def test_workflow_dsl_validator_rejects_forbidden_semantics(
    tmp_path: Path,
) -> None:
    payload = _workflow_payload()
    payload.update(
        {
            "auto_approve": True,
            "bridge_as_authority": True,
            "destructive": True,
            "god_mode": True,
            "silent_write": True,
        }
    )
    path = _write_yaml(tmp_path / "workflow.yaml", payload)

    report = validate_workflow_dsl_file(path)

    assert report.valid is False
    assert {
        error["code"] for error in report.errors
    } >= {
        "WORKFLOW_DSL_FORBIDDEN_AUTO_APPROVE",
        "WORKFLOW_DSL_FORBIDDEN_BRIDGE_AUTHORITY",
        "WORKFLOW_DSL_FORBIDDEN_DESTRUCTIVE",
        "WORKFLOW_DSL_FORBIDDEN_GOD_MODE",
        "WORKFLOW_DSL_FORBIDDEN_SILENT_WRITE",
    }


def test_workflow_dsl_validator_requires_canonical_writer_for_write_steps(
    tmp_path: Path,
) -> None:
    payload = _workflow_payload()
    payload["steps"][0].update(
        {
            "tool": "orchestrator.transition.apply",
            "mode": "write",
            "approval_required": True,
            "receipt_required": True,
        }
    )
    path = _write_yaml(tmp_path / "workflow.yaml", payload)

    report = validate_workflow_dsl_file(path)

    assert report.valid is False
    assert any(
        error["code"] == "WORKFLOW_DSL_WRITE_CANONICAL_WRITER_REQUIRED"
        for error in report.errors
    )


def test_workflow_dsl_validator_requires_upstream_writer_for_bridge_writes(
    tmp_path: Path,
) -> None:
    payload = _workflow_payload()
    payload["steps"][0].update(
        {
            "tool": "orchestrator.transition.apply",
            "mode": "write",
            "canonical_writer": "dopecon-bridge",
            "bridge_mediated": True,
            "approval_required": True,
            "receipt_required": True,
        }
    )
    path = _write_yaml(tmp_path / "workflow.yaml", payload)

    report = validate_workflow_dsl_file(path)

    assert report.valid is False
    assert any(
        error["code"] == "WORKFLOW_DSL_BRIDGE_UPSTREAM_WRITER_REQUIRED"
        for error in report.errors
    )


def test_workflow_dsl_validator_requires_schema_path_for_packet_or_proof_steps(
    tmp_path: Path,
) -> None:
    payload = _workflow_payload()
    payload["steps"][1].pop("schema_path")
    path = _write_yaml(tmp_path / "workflow.yaml", payload)

    report = validate_workflow_dsl_file(path)

    assert report.valid is False
    assert any(
        error["code"] == "WORKFLOW_DSL_SCHEMA_PATH_REQUIRED"
        for error in report.errors
    )


def test_workflow_dsl_validator_requires_approval_for_t4_plus_workflows(
    tmp_path: Path,
) -> None:
    payload = _workflow_payload()
    payload["automation_tier"] = "T4"
    payload["approval"] = {"required": False}
    path = _write_yaml(tmp_path / "workflow.yaml", payload)

    report = validate_workflow_dsl_file(path)

    assert report.valid is False
    assert any(
        error["code"] == "WORKFLOW_DSL_T4_APPROVAL_REQUIRED"
        for error in report.errors
    )


def test_workflow_dsl_validator_requires_tx_tu_refusal(tmp_path: Path) -> None:
    payload = _workflow_payload()
    payload["automation_tier"] = "TU"
    path = _write_yaml(tmp_path / "workflow.yaml", payload)

    report = validate_workflow_dsl_file(path)

    assert report.valid is False
    assert any(
        error["code"] == "WORKFLOW_DSL_UNRESOLVED_REFUSE_REQUIRED"
        for error in report.errors
    )


def test_workflow_dsl_validator_rejects_unknown_orchestrator_tool(
    tmp_path: Path,
) -> None:
    payload = _workflow_payload()
    payload["steps"][0]["tool"] = "orchestrator.future.unknown"
    path = _write_yaml(tmp_path / "workflow.yaml", payload)

    report = validate_workflow_dsl_file(path)

    assert report.valid is False
    assert any(
        error["code"] == "WORKFLOW_DSL_UNKNOWN_CAPABILITY"
        for error in report.errors
    )
