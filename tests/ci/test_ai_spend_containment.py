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
GEMINI_REUSABLE = (
    "gemini-review.yml",
    "gemini-triage.yml",
    "gemini-invoke.yml",
    "gemini-plan-execute.yml",
)
GEMINI_ADVISORY = (
    "gemini-dispatch.yml",
    "gemini-scheduled-triage.yml",
    "gemini-review.yml",
    "gemini-triage.yml",
    "gemini-invoke.yml",
)


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
            if (
                name not in provider_backed
                and _workflow_calls(workflow) & provider_backed
            ):
                provider_backed.add(name)
                changed = True
    return provider_backed


def _assert_default_false_spend_input(path: Path) -> None:
    dispatch = _triggers(path)["workflow_dispatch"]
    spend = dispatch["inputs"]["allow_api_spend"]
    assert spend["type"] == "boolean"
    assert spend["default"] == "false"
    assert spend["required"] == "false"
    assert (
        "separate explicit operator spend authorization" in spend["description"].lower()
    )


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


def test_security_review_manual_summary_is_reachable() -> None:
    workflow = _load(SECURITY_REVIEW)
    security_job = workflow["jobs"]["security-review"]
    summary = workflow["jobs"]["security-summary"]
    condition = " ".join(str(summary.get("if", "")).split())
    script = summary["steps"][0]["run"]

    assert "github.event_name == 'workflow_dispatch'" in condition
    assert "github.event_name == 'pull_request'" not in condition
    assert security_job["outputs"]["provider_outcome"] == (
        "${{ steps.claude_security_review.outcome }}"
    )
    assert summary["env"]["PROVIDER_OUTCOME"] == (
        "${{ needs.security-review.outputs.provider_outcome }}"
    )
    assert "No security verdict was produced" in script
    assert "Ready for merge" not in script


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


def test_gemini_dispatch_validates_exact_target_before_routing() -> None:
    workflow = _load(WORKFLOWS / "gemini-dispatch.yml")
    inputs = workflow["on"]["workflow_dispatch"]["inputs"]
    dispatch = workflow["jobs"]["dispatch"]
    steps = dispatch["steps"]
    validation = next(step for step in steps if step.get("id") == "validate_target")
    script = validation["with"]["script"]

    assert inputs["target_type"] == {
        "description": "Exact target type for the selected route",
        "required": "true",
        "type": "choice",
        "options": ["pull_request", "issue"],
    }
    assert inputs["target_head_sha"]["type"] == "string"
    assert inputs["target_head_sha"]["required"] == "false"
    assert dispatch["outputs"]["target_repository"] == (
        "${{ steps.validate_target.outputs.target_repository }}"
    )
    assert dispatch["outputs"]["target_type"] == (
        "${{ steps.validate_target.outputs.target_type }}"
    )
    assert dispatch["outputs"]["target_number"] == (
        "${{ steps.validate_target.outputs.target_number }}"
    )
    assert dispatch["outputs"]["target_head_sha"] == (
        "${{ steps.validate_target.outputs.target_head_sha }}"
    )
    assert "github.rest.repos.get" in script
    assert "github.rest.pulls.get" in script
    assert "github.rest.issues.get" in script
    assert "DDD-Enterprises/dopemux-mvp" in str(validation["env"])
    assert "Number.isSafeInteger" in script
    assert "target_head_sha_mismatch" in script


def test_gemini_dispatch_passes_validated_target_to_every_reusable() -> None:
    workflow = _load(WORKFLOWS / "gemini-dispatch.yml")

    for job_name in ("review", "triage", "invoke", "plan-execute"):
        call = workflow["jobs"][job_name]
        assert call["with"]["target_repository"] == (
            "${{ needs.dispatch.outputs.target_repository }}"
        )
        assert call["with"]["target_type"] == (
            "${{ needs.dispatch.outputs.target_type }}"
        )
        assert call["with"]["target_number"] == (
            "${{ needs.dispatch.outputs.target_number }}"
        )
        assert call["with"]["target_head_sha"] == (
            "${{ needs.dispatch.outputs.target_head_sha }}"
        )


@pytest.mark.parametrize("filename", GEMINI_REUSABLE)
def test_gemini_reusable_revalidates_explicit_target_before_provider(
    filename: str,
) -> None:
    workflow = _load(WORKFLOWS / filename)
    inputs = workflow["on"]["workflow_call"]["inputs"]
    serialized = (WORKFLOWS / filename).read_text(encoding="utf-8")
    provider_jobs = [
        job
        for job in workflow["jobs"].values()
        if any(
            str(step.get("uses", "")).startswith(GEMINI_ACTION_PREFIX)
            for step in job.get("steps", [])
        )
    ]

    assert set(inputs) >= {
        "target_repository",
        "target_type",
        "target_number",
        "target_head_sha",
        "additional_context",
    }
    assert inputs["target_repository"]["required"] == "true"
    assert inputs["target_type"]["required"] == "true"
    assert inputs["target_number"]["required"] == "true"
    assert provider_jobs
    assert "github.event.pull_request" not in serialized
    assert "github.event.issue" not in serialized

    for job in provider_jobs:
        steps = job["steps"]
        validation_index = next(
            index
            for index, step in enumerate(steps)
            if step.get("id") == "validate_target"
        )
        provider_index = next(
            index
            for index, step in enumerate(steps)
            if str(step.get("uses", "")).startswith(GEMINI_ACTION_PREFIX)
        )
        validation = steps[validation_index]
        script = validation["with"]["script"]
        assert validation_index < provider_index
        assert "github.rest.repos.get" in script
        assert "github.rest.pulls.get" in script
        assert "github.rest.issues.get" in script
        assert "Number.isSafeInteger" in script
        assert "target_head_sha_mismatch" in script
        assert "steps.validate_target.outputs.target_number" in serialized


def test_gemini_approve_requires_separate_repository_mutation_authority() -> None:
    dispatch = _load(WORKFLOWS / "gemini-dispatch.yml")
    plan_call = dispatch["jobs"]["plan-execute"]
    plan = _load(WORKFLOWS / "gemini-plan-execute.yml")
    plan_inputs = plan["on"]["workflow_call"]["inputs"]

    assert (
        dispatch["jobs"]["dispatch"]["outputs"]["repository_mutation_authorized"]
        == "false"
    )
    assert "needs.dispatch.outputs.repository_mutation_authorized == 'true'" in (
        " ".join(str(plan_call.get("if", "")).split())
    )
    assert plan_call["with"]["repository_mutation_authorized"] == "false"
    assert plan_call["permissions"]["contents"] == "read"
    assert plan_inputs["repository_mutation_authorized"] == {
        "description": "Separate repository mutation authority",
        "required": "false",
        "type": "boolean",
        "default": "false",
    }
    assert "inputs.repository_mutation_authorized == true" in (
        " ".join(str(plan["jobs"]["plan-execute"].get("if", "")).split())
    )


@pytest.mark.parametrize("filename", GEMINI_ADVISORY)
def test_gemini_spend_only_routes_are_advisory(filename: str) -> None:
    workflow = _load(WORKFLOWS / filename)
    serialized = (WORKFLOWS / filename).read_text(encoding="utf-8")

    for job_name, job in workflow["jobs"].items():
        if filename == "gemini-dispatch.yml" and job_name == "plan-execute":
            continue
        permissions = job.get("permissions", {})
        for scope in ("contents", "issues", "pull-requests"):
            assert permissions.get(scope) != "write", f"{filename}:{job_name}:{scope}"
        for step in job.get("steps", []):
            inputs = step.get("with", {})
            for permission in (
                "permission-contents",
                "permission-issues",
                "permission-pull-requests",
            ):
                assert inputs.get(permission) != "write", (
                    f"{filename}:{job_name}:{step.get('name')}:{permission}"
                )

    forbidden_mutations = {
        "gemini-dispatch.yml": ("gh issue comment",),
        "gemini-scheduled-triage.yml": ("github.rest.issues.setLabels",),
        "gemini-review.yml": (
            "add_comment_to_pending_review",
            "pull_request_review_write",
        ),
        "gemini-triage.yml": ("github.rest.issues.setLabels",),
        "gemini-invoke.yml": ("add_issue_comment",),
    }
    for mutation in forbidden_mutations[filename]:
        assert mutation not in serialized
