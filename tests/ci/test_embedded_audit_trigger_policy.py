"""Structural contracts for final-audit cost containment and readiness invalidation."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_AUDIT = ROOT / ".github" / "workflows" / "embedded-audit.yml"
TEMPLATE_AUDIT = (
    ROOT
    / "src"
    / "dopemux"
    / "templates"
    / "init"
    / ".github"
    / "workflows"
    / "embedded-audit.yml"
)
REPOSITORY_INVALIDATOR = ROOT / ".github" / "workflows" / "pr-readiness-invalidator.yml"
TEMPLATE_INVALIDATOR = (
    ROOT
    / "src"
    / "dopemux"
    / "templates"
    / "init"
    / ".github"
    / "workflows"
    / "pr-readiness-invalidator.yml"
)


def _load(path: Path) -> dict:
    return yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)


def _review_gate_step() -> dict:
    steps = _load(REPOSITORY_AUDIT)["jobs"]["embedded-audit"]["steps"]
    return next(
        step for step in steps if step.get("name") == "Review settlement preflight"
    )


@pytest.mark.parametrize("path", [REPOSITORY_AUDIT, TEMPLATE_AUDIT])
def test_embedded_audit_is_manual_dispatch_only(path: Path) -> None:
    triggers = _load(path)["on"]

    assert set(triggers) == {"workflow_dispatch"}
    assert "pull_request_target" not in triggers
    assert "pull_request" not in triggers


def test_repository_audit_keeps_exact_manual_identity_inputs() -> None:
    inputs = _load(REPOSITORY_AUDIT)["on"]["workflow_dispatch"]["inputs"]

    assert {"pr_number", "head_sha"} <= set(inputs)
    assert inputs["pr_number"]["required"] == "true"
    assert inputs["head_sha"]["required"] == "true"


def test_repository_audit_manual_dispatch_defaults_spend_false() -> None:
    inputs = _load(REPOSITORY_AUDIT)["on"]["workflow_dispatch"]["inputs"]
    spend_input = inputs["allow_api_spend"]

    assert spend_input["type"] == "boolean"
    assert spend_input["default"] == "false"
    assert spend_input["required"] == "false"
    assert (
        "separate explicit operator spend authorization"
        in spend_input["description"].lower()
    )


def test_repository_audit_provider_runner_requires_manual_spend_authority() -> None:
    steps = _load(REPOSITORY_AUDIT)["jobs"]["embedded-audit"]["steps"]
    setup = next(
        step
        for step in steps
        if step.get("name") == "Setup trusted Claude audit runner"
    )
    install = next(
        step
        for step in steps
        if step.get("name") == "Install trusted Claude audit runner"
    )
    runner = next(step for step in steps if step.get("name") == "Run PAL clink audit")

    for step in (setup, install):
        condition = " ".join(str(step.get("if", "")).split())
        assert "steps.head_integrity.outputs.verified == 'true'" in condition
        assert "inputs.allow_api_spend == true" in condition

    assert runner["env"]["ALLOW_API_SPEND"] == "${{ inputs.allow_api_spend }}"
    assert '[ "$ALLOW_API_SPEND" != true ]' in runner["run"]
    assert "Explicit operator API spend authority was not granted." in runner["run"]


def test_review_settlement_preflight_precedes_every_model_stage() -> None:
    steps = _load(REPOSITORY_AUDIT)["jobs"]["embedded-audit"]["steps"]
    names = [step.get("name") for step in steps]
    preflight_index = names.index("Review settlement preflight")

    for model_stage in (
        "Static auditor route preflight",
        "Setup trusted Claude audit runner",
        "Install trusted Claude audit runner",
        "Run PAL clink audit",
    ):
        assert preflight_index < names.index(model_stage)

    script = steps[preflight_index]["run"]
    env = steps[preflight_index]["env"]
    assert "PRE_MODEL_REVIEW_GATE" in script
    assert "EXPECTED_HEAD_SHA" in env
    assert "trusted-source/scripts/audit/review_settlement.py fetch" in script
    assert "--min-ready-age-seconds 300" in script
    assert "--min-activity-quiet-seconds 120" in script
    assert names.index("Checkout trusted audit source") < preflight_index


@pytest.mark.parametrize("path", [REPOSITORY_INVALIDATOR, TEMPLATE_INVALIDATOR])
def test_readiness_invalidator_is_zero_model_read_only_observer(path: Path) -> None:
    workflow = _load(path)
    triggers = workflow["on"]
    permissions = workflow["permissions"]
    serialized = path.read_text(encoding="utf-8").lower()

    assert set(triggers["pull_request"]["types"]) == {
        "opened",
        "synchronize",
        "reopened",
        "ready_for_review",
    }
    assert set(triggers["pull_request_review"]["types"]) == {
        "submitted",
        "dismissed",
    }
    assert set(triggers["pull_request_review_comment"]["types"]) == {
        "created",
        "edited",
        "deleted",
    }
    assert set(triggers["pull_request_review_thread"]["types"]) == {
        "resolved",
        "unresolved",
    }
    assert permissions == {"contents": "read", "pull-requests": "read"}
    assert "actions/checkout" not in serialized
    assert "claude" not in serialized
    assert "pal clink" not in serialized
    assert "anthropic" not in serialized
    assert "actions/upload-artifact@v4" in serialized
    assert "invalidation-receipt.json" in serialized
    assert "statuses: write" not in serialized
    assert "/statuses/" not in serialized
    assert "comment.body" not in serialized
    assert "pull_request_review_thread:resolved" in serialized
    assert "pull_request_review_thread:unresolved" in serialized


def test_init_template_packages_readiness_invalidator() -> None:
    assert TEMPLATE_INVALIDATOR.is_file()
