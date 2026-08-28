"""Structural contracts preventing automatic provider-backed CI spend."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
CI_COMPLETE = ROOT / ".github" / "workflows" / "ci-complete.yml"
SECURITY_REVIEW = ROOT / ".github" / "workflows" / "security-review.yml"
CLAUDE_ACTION_PREFIX = "anthropics/claude-code-security-review@"


def _load(path: Path) -> dict[str, Any]:
    return yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)


def _triggers(path: Path) -> dict[str, Any]:
    triggers = _load(path)["on"]
    assert isinstance(triggers, dict), f"{path.name} must declare structured triggers"
    return triggers


def _claude_steps(path: Path) -> list[dict[str, Any]]:
    jobs = _load(path)["jobs"]
    return [
        step
        for job in jobs.values()
        for step in job.get("steps", [])
        if str(step.get("uses", "")).startswith(CLAUDE_ACTION_PREFIX)
    ]


def _assert_manual_spend_dominates(step: dict[str, Any]) -> None:
    condition = " ".join(str(step.get("if", "")).split())
    assert "github.event_name == 'workflow_dispatch'" in condition
    assert "inputs.allow_api_spend == true" in condition
    assert "env.ANTHROPIC_API_KEY != ''" in condition


def test_ci_complete_retains_automatic_pull_request_ci() -> None:
    triggers = _triggers(CI_COMPLETE)

    assert set(triggers["pull_request"]["types"]) == {
        "opened",
        "synchronize",
        "reopened",
        "ready_for_review",
    }


@pytest.mark.parametrize("event_name", ["pull_request", "push", "merge_group"])
def test_ci_complete_automatic_event_cannot_invoke_claude(event_name: str) -> None:
    triggers = _triggers(CI_COMPLETE)
    claude_steps = _claude_steps(CI_COMPLETE)

    assert event_name in triggers
    assert claude_steps, "ci-complete must retain an explicitly gated manual route"
    for step in claude_steps:
        _assert_manual_spend_dominates(step)


def test_ci_complete_manual_dispatch_defaults_spend_false() -> None:
    dispatch = _triggers(CI_COMPLETE)["workflow_dispatch"]
    spend_input = dispatch["inputs"]["allow_api_spend"]

    assert spend_input["type"] == "boolean"
    assert spend_input["default"] == "false"
    assert spend_input["required"] == "false"


def test_ci_complete_manual_gate_preserves_operator_authority_boundary() -> None:
    dispatch = _triggers(CI_COMPLETE)["workflow_dispatch"]
    description = dispatch["inputs"]["allow_api_spend"]["description"].lower()

    assert "separate explicit operator spend authorization" in description


def test_security_review_is_workflow_dispatch_only() -> None:
    triggers = _triggers(SECURITY_REVIEW)

    assert set(triggers) == {"workflow_dispatch"}
    assert "pull_request" not in triggers
    assert "push" not in triggers
    assert "merge_group" not in triggers


def test_security_review_manual_dispatch_defaults_spend_false() -> None:
    dispatch = _triggers(SECURITY_REVIEW)["workflow_dispatch"]
    spend_input = dispatch["inputs"]["allow_api_spend"]

    assert spend_input["type"] == "boolean"
    assert spend_input["default"] == "false"
    assert spend_input["required"] == "false"


def test_security_review_manual_gate_preserves_operator_authority_boundary() -> None:
    dispatch = _triggers(SECURITY_REVIEW)["workflow_dispatch"]
    description = dispatch["inputs"]["allow_api_spend"]["description"].lower()

    assert "separate explicit operator spend authorization" in description


@pytest.mark.parametrize("path", [CI_COMPLETE, SECURITY_REVIEW])
def test_every_claude_security_action_is_dominated_by_manual_spend_gate(
    path: Path,
) -> None:
    claude_steps = _claude_steps(path)

    assert claude_steps, f"{path.name} must retain an explicitly gated manual route"
    for step in claude_steps:
        _assert_manual_spend_dominates(step)
