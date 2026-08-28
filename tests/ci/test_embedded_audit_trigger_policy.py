"""Structural contracts for final-audit cost containment and readiness invalidation."""
from __future__ import annotations

import copy
import json
import os
import re
import subprocess
import sys
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
REPOSITORY_INVALIDATOR = (
    ROOT / ".github" / "workflows" / "pr-readiness-invalidator.yml"
)
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
    return next(step for step in steps if step.get("name") == "Review settlement preflight")


def _review_gate_python() -> str:
    match = re.search(r"python - <<'PY'\n(.*?)\nPY", _review_gate_step()["run"], re.S)
    assert match, "review settlement preflight must contain executable Python"
    return match.group(1)


def _settled_payload() -> dict:
    return {
        "data": {
            "repository": {
                "pullRequest": {
                    "number": 1287,
                    "state": "OPEN",
                    "isDraft": False,
                    "merged": False,
                    "headRefOid": "a" * 40,
                    "readyForReviewEvents": {
                        "pageInfo": {"hasPreviousPage": False},
                        "nodes": [{"createdAt": "2026-08-27T19:50:00Z"}],
                    },
                    "reviews": {
                        "pageInfo": {"hasPreviousPage": False},
                        "nodes": [
                            {
                                "submittedAt": "2026-08-27T19:53:00Z",
                                "updatedAt": "2026-08-27T19:53:00Z",
                                "state": "COMMENTED",
                            }
                        ],
                    },
                    "reviewThreads": {
                        "pageInfo": {"hasNextPage": False},
                        "nodes": [
                            {
                                "isResolved": True,
                                "comments": {
                                    "pageInfo": {"hasPreviousPage": False},
                                    "nodes": [
                                        {
                                            "createdAt": "2026-08-27T19:54:00Z",
                                            "updatedAt": "2026-08-27T19:54:00Z",
                                        }
                                    ],
                                },
                            }
                        ],
                    },
                }
            }
        }
    }


def _run_review_gate(tmp_path: Path, payload: dict) -> subprocess.CompletedProcess[str]:
    payload_path = tmp_path / "review-settlement.json"
    payload_path.write_text(json.dumps(payload), encoding="utf-8")
    env = os.environ.copy()
    env.update(
        {
            "EXPECTED_REPO": "DDD-Enterprises/dopemux-mvp",
            "PR_NUMBER": "1287",
            "EXPECTED_HEAD_SHA": "a" * 40,
            "MIN_READY_AGE_SECONDS": "300",
            "MIN_ACTIVITY_QUIET_SECONDS": "120",
            "REVIEW_SETTLEMENT_JSON": str(payload_path),
            "NOW_ISO": "2026-08-27T20:00:00Z",
            "GITHUB_STEP_SUMMARY": str(tmp_path / "summary.md"),
        }
    )
    return subprocess.run(
        [sys.executable, "-"],
        input=_review_gate_python(),
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
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
    assert env["MIN_READY_AGE_SECONDS"] == "300"
    assert env["MIN_ACTIVITY_QUIET_SECONDS"] == "120"
    assert "reviewThreads" in script
    assert "hasNextPage" in script
    assert "readyForReviewEvents" in script


def test_review_settlement_gate_accepts_settled_exact_head(tmp_path: Path) -> None:
    result = _run_review_gate(tmp_path, _settled_payload())

    assert result.returncode == 0, result.stdout + result.stderr
    summary = json.loads(result.stdout)
    assert summary["marker"] == "PRE_MODEL_REVIEW_GATE"
    assert summary["status"] == "PASS"
    assert summary["reasons"] == []


def test_review_settlement_gate_blocks_head_drift(tmp_path: Path) -> None:
    payload = _settled_payload()
    payload["data"]["repository"]["pullRequest"]["headRefOid"] = "b" * 40

    result = _run_review_gate(tmp_path, payload)

    assert result.returncode == 1
    assert "head_sha_mismatch" in json.loads(result.stdout)["reasons"]


def test_review_settlement_gate_blocks_unresolved_thread(tmp_path: Path) -> None:
    payload = _settled_payload()
    payload["data"]["repository"]["pullRequest"]["reviewThreads"]["nodes"][0][
        "isResolved"
    ] = False

    result = _run_review_gate(tmp_path, payload)

    assert result.returncode == 1
    assert "unresolved_review_threads" in json.loads(result.stdout)["reasons"]


def test_review_settlement_gate_blocks_early_dispatch(tmp_path: Path) -> None:
    payload = _settled_payload()
    payload["data"]["repository"]["pullRequest"]["readyForReviewEvents"]["nodes"] = [
        {"createdAt": "2026-08-27T19:58:00Z"}
    ]

    result = _run_review_gate(tmp_path, payload)

    assert result.returncode == 1
    assert "ready_for_review_too_recent" in json.loads(result.stdout)["reasons"]


def test_review_settlement_gate_blocks_recent_review_activity(tmp_path: Path) -> None:
    payload = copy.deepcopy(_settled_payload())
    payload["data"]["repository"]["pullRequest"]["reviews"]["nodes"][0][
        "updatedAt"
    ] = "2026-08-27T19:59:30Z"

    result = _run_review_gate(tmp_path, payload)

    assert result.returncode == 1
    assert "review_activity_too_recent" in json.loads(result.stdout)["reasons"]


@pytest.mark.parametrize("path", [REPOSITORY_INVALIDATOR, TEMPLATE_INVALIDATOR])
def test_readiness_invalidator_is_zero_model_and_status_only(path: Path) -> None:
    workflow = _load(path)
    triggers = workflow["on"]
    permissions = workflow["permissions"]
    serialized = path.read_text(encoding="utf-8").lower()

    assert set(triggers["pull_request"]["types"]) == {"ready_for_review"}
    assert set(triggers["pull_request_review"]["types"]) == {
        "submitted",
        "dismissed",
    }
    assert set(triggers["pull_request_review_comment"]["types"]) == {
        "created",
        "edited",
        "deleted",
    }
    assert permissions == {"contents": "read", "statuses": "write"}
    assert "actions/checkout" not in serialized
    assert "claude" not in serialized
    assert "pal clink" not in serialized
    assert "anthropic" not in serialized
    assert 'context="pr steward / final readiness"' in serialized
    assert 'state="pending"' in serialized
    assert "/statuses/${pr_head_sha}" in serialized


def test_init_template_packages_readiness_invalidator() -> None:
    assert TEMPLATE_INVALIDATOR.is_file()
