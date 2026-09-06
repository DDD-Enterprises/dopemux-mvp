"""Structural contracts for trusted embedded-audit evidence routing."""
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "embedded-audit.yml"


def _workflow() -> dict:
    return yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)


def test_required_context_keeps_automatic_and_manual_triggers() -> None:
    workflow = _workflow()
    triggers = workflow["on"]
    assert set(triggers["pull_request_target"]["types"]) == {
        "opened",
        "synchronize",
        "reopened",
        "ready_for_review",
    }
    assert {"pr_number", "head_sha"} == set(
        triggers["workflow_dispatch"]["inputs"]
    )
    assert workflow["jobs"]["embedded-audit"]["name"] == "independent embedded audit"


def test_workflow_classifies_exact_base_head_with_trusted_source() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    steps = _workflow()["jobs"]["embedded-audit"]["steps"]
    checkout = next(
        step for step in steps if step.get("name") == "Checkout trusted audit source"
    )
    classify = next(
        step for step in steps if step.get("name") == "Classify trusted change contract"
    )
    assert "github.event.repository.default_branch" in text
    assert checkout["with"]["persist-credentials"] == "false"
    assert "validate_change_contract.py" in classify["run"]
    assert "TARGET_PR_BASE_SHA" in classify["env"]
    assert "TARGET_PR_HEAD_SHA" in classify["env"]
    assert "--format json" in classify["run"]
    assert "git checkout" not in text


def test_workflow_routes_not_required_or_signed_import_only() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    steps = _workflow()["jobs"]["embedded-audit"]["steps"]
    names = [step.get("name") for step in steps]
    assert names.index("Classify trusted change contract") < names.index(
        "Evaluate signed imported audit evidence"
    )
    assert names.index("Evaluate signed imported audit evidence") < names.index(
        "Emit audit evidence gate proof"
    )
    assert "--risk-lane" in text
    assert "--change-contract-json" in text
    assert "--local-attestation-json" in text


def test_candidate_head_is_fetched_as_objects_and_never_executed() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "git -C trusted-source fetch" in text
    assert "git -C trusted-source cat-file" in text
    assert "Candidate code is never checked out or executed" in text
    assert "working-directory: trusted-source" in text
