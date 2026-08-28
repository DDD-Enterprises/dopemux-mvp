"""Structural contracts preventing automatic provider-backed CI spend."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"
CI_COMPLETE = ROOT / ".github" / "workflows" / "ci-complete.yml"
SECURITY_REVIEW = ROOT / ".github" / "workflows" / "security-review.yml"
CLAUDE_ACTION_PREFIX = "anthropics/claude-code-security-review@"
GEMINI_ACTION_PREFIX = "google-github-actions/run-gemini-cli@"


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


def _workflow_calls(workflow: dict[str, Any]) -> set[str]:
    calls = set()
    for job in workflow.get("jobs", {}).values():
        target = str(job.get("uses", ""))
        if target.startswith("./.github/workflows/"):
            calls.add(Path(target).name)
    return calls


def _has_direct_gemini_call(workflow: dict[str, Any]) -> bool:
    return any(
        str(step.get("uses", "")).startswith(GEMINI_ACTION_PREFIX)
        for job in workflow.get("jobs", {}).values()
        for step in job.get("steps", [])
    )


def _gemini_provider_workflows() -> set[str]:
    parsed = {path.name: _load(path) for path in WORKFLOWS.glob("*.yml")}
    provider_backed = {
        name for name, workflow in parsed.items() if _has_direct_gemini_call(workflow)
    }
    changed = True
    while changed:
        changed = False
        for name, workflow in parsed.items():
            if name not in provider_backed and _workflow_calls(workflow) & provider_backed:
                provider_backed.add(name)
                changed = True
    return provider_backed


def _assert_default_false_spend_input(path: Path) -> None:
    dispatch = _triggers(path)["workflow_dispatch"]
    spend = dispatch["inputs"]["allow_api_spend"]
    assert spend["type"] == "boolean"
    assert spend["default"] == "false"
    assert spend["required"] == "false"
    assert "separate explicit operator spend authorization" in spend["description"].lower()


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


def test_provider_route_discovery_includes_all_current_gemini_entrypoints() -> None:
    provider_backed = _gemini_provider_workflows()

    assert {
        "gemini-dispatch.yml",
        "gemini-scheduled-triage.yml",
        "gemini-review.yml",
        "gemini-triage.yml",
        "gemini-invoke.yml",
        "gemini-plan-execute.yml",
    } <= provider_backed


@pytest.mark.parametrize(
    "filename", ["gemini-dispatch.yml", "gemini-scheduled-triage.yml"]
)
def test_gemini_provider_entrypoint_is_manual_dispatch_only(filename: str) -> None:
    path = WORKFLOWS / filename

    assert set(_triggers(path)) == {"workflow_dispatch"}
    _assert_default_false_spend_input(path)


@pytest.mark.parametrize(
    "filename", ["gemini-dispatch.yml", "gemini-scheduled-triage.yml"]
)
def test_gemini_provider_jobs_require_explicit_manual_spend_gate(filename: str) -> None:
    workflow = _load(WORKFLOWS / filename)
    provider_jobs = []
    provider_workflows = _gemini_provider_workflows()
    for job in workflow["jobs"].values():
        direct = any(
            str(step.get("uses", "")).startswith(GEMINI_ACTION_PREFIX)
            for step in job.get("steps", [])
        )
        called = Path(str(job.get("uses", ""))).name in provider_workflows
        if direct or called:
            provider_jobs.append(job)

    assert provider_jobs
    for job in provider_jobs:
        condition = " ".join(str(job.get("if", "")).split())
        assert "github.event_name == 'workflow_dispatch'" in condition
        assert "inputs.allow_api_spend == true" in condition


def test_gemini_manual_true_keeps_provider_routes_mechanically_reachable() -> None:
    dispatch = _load(WORKFLOWS / "gemini-dispatch.yml")
    scheduled = _load(WORKFLOWS / "gemini-scheduled-triage.yml")

    assert _workflow_calls(dispatch) & _gemini_provider_workflows()
    assert _has_direct_gemini_call(scheduled)
