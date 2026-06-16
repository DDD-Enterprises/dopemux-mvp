"""Unit tests for DMX-DCP-MODEL-ROUTING-MVP-0004 read-only DCP CLI."""

from __future__ import annotations

import json

from click.testing import CliRunner

from dopemux.commands.dcp_commands import dcp
from dopemux.dcp.routing_model import BackendKind, RouteStatus, TaskSource, TaskType


def test_classify_help() -> None:
    runner = CliRunner()
    result = runner.invoke(dcp, ["classify", "--help"])
    assert result.exit_code == 0
    assert "RouteDecision" in result.output


def test_recommend_backend_help() -> None:
    runner = CliRunner()
    result = runner.invoke(dcp, ["recommend-backend", "--help"])
    assert result.exit_code == 0
    assert "backend policy" in result.output.lower()


def test_classify_docs_only_task() -> None:
    runner = CliRunner()
    payload = {
        "task_source": "OPERATOR",
        "task_type": "DESIGN_ONLY",
        "touches_docs": True,
        "has_unknown_authority": False,
        "authority_class": "OPERATOR",
    }
    result = runner.invoke(dcp, ["classify"], input=json.dumps(payload))
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["task_type"] == TaskType.DESIGN_ONLY.value
    assert data["task_source"] == TaskSource.OPERATOR.value


def test_classify_unknown_authority_fails_closed() -> None:
    runner = CliRunner()
    payload = {"task_type": "CODE_CHANGE", "has_unknown_authority": True}
    result = runner.invoke(dcp, ["classify"], input=json.dumps(payload))
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["status"] != RouteStatus.ALLOWED.value


def test_recommend_backend_for_classified_route() -> None:
    runner = CliRunner()
    classify_payload = {
        "task_source": "OPERATOR",
        "task_type": "CODE_CHANGE",
        "touches_files": True,
        "touches_tests": True,
        "is_repo_changing": True,
        "is_non_trivial": False,
        "has_unknown_authority": False,
        "authority_class": "OPERATOR",
        "evidence_refs": ["proof/TP-DCP-0001/PROOF.json"],
    }
    classify_result = runner.invoke(dcp, ["classify"], input=json.dumps(classify_payload))
    assert classify_result.exit_code == 0
    decision = json.loads(classify_result.output)

    recommend_result = runner.invoke(
        dcp, ["recommend-backend"], input=json.dumps(decision)
    )
    assert recommend_result.exit_code == 0
    recommendation = json.loads(recommend_result.output)
    assert recommendation["policy_version"] == "DMX-DCP-MODEL-ROUTING-MVP-0003"
    if recommendation["blocked"] is False:
        assert recommendation["preferred_backend"] != BackendKind.NONE.value


def test_classify_rejects_invalid_json() -> None:
    runner = CliRunner()
    result = runner.invoke(dcp, ["classify"], input="{not-json")
    assert result.exit_code != 0


def test_classify_requires_stdin_when_no_input_flag() -> None:
    runner = CliRunner()
    result = runner.invoke(dcp, ["classify"])
    assert result.exit_code != 0
    assert "json payload" in result.output.lower()