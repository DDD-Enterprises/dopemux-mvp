"""Security contracts for two-stage PR readiness invalidation."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
OBSERVER = ROOT / ".github" / "workflows" / "pr-readiness-invalidator.yml"
WRITER = ROOT / ".github" / "workflows" / "pr-readiness-invalidation-writer.yml"
TEMPLATE_OBSERVER = (
    ROOT / "src/dopemux/templates/init/.github/workflows/pr-readiness-invalidator.yml"
)
TEMPLATE_WRITER = (
    ROOT
    / "src/dopemux/templates/init/.github/workflows/pr-readiness-invalidation-writer.yml"
)


def _load(path: Path) -> dict:
    return yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)


@pytest.mark.parametrize("path", [OBSERVER, TEMPLATE_OBSERVER])
def test_observer_is_read_only_and_covers_all_invalidation_events(path: Path) -> None:
    workflow = _load(path)
    triggers = workflow["on"]
    text = path.read_text(encoding="utf-8").lower()

    assert set(triggers["pull_request"]["types"]) == {
        "opened",
        "synchronize",
        "reopened",
        "ready_for_review",
    }
    assert set(triggers["pull_request_review"]["types"]) == {
        "submitted",
        "edited",
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
    assert workflow["permissions"] == {"contents": "read", "pull-requests": "read"}
    assert "statuses: write" not in text
    assert "actions/checkout" not in text
    assert "cache" not in text
    assert "/statuses/" not in text
    assert "run-gemini" not in text
    assert "anthropic" not in text
    assert "comment.body" not in text
    assert "review.body" not in text


@pytest.mark.parametrize("path", [WRITER, TEMPLATE_WRITER])
def test_writer_is_trusted_workflow_run_status_only(path: Path) -> None:
    workflow = _load(path)
    text = path.read_text(encoding="utf-8").lower()

    assert workflow["on"] == {
        "workflow_run": {
            "workflows": ["PR readiness invalidator"],
            "types": ["completed"],
        }
    }
    assert workflow["permissions"] == {
        "contents": "read",
        "actions": "read",
        "pull-requests": "read",
        "statuses": "write",
    }
    assert "actions/checkout" not in text
    assert "run-gemini" not in text
    assert "anthropic" not in text
    assert "source " not in text
    assert "bash receipt" not in text
    assert 'context="pr steward / final readiness"' in text
    assert 'state="pending"' in text


def _validation_python() -> str:
    workflow = _load(WRITER)
    steps = workflow["jobs"]["invalidate"]["steps"]
    step = next(
        step
        for step in steps
        if step.get("name") == "Validate trusted invalidation binding"
    )
    match = re.search(r"python - <<'PY'\n(.*?)\nPY", step["run"], re.S)
    assert match
    return match.group(1)


def _binding_payloads() -> tuple[dict, dict, dict, dict]:
    repo = "DDD-Enterprises/dopemux-mvp"
    head = "a" * 40
    run = {
        "id": 987,
        "repository": {"id": 42, "full_name": repo},
        "name": "PR readiness invalidator",
        "path": ".github/workflows/pr-readiness-invalidator.yml",
        "status": "completed",
        "conclusion": "success",
        "event": "pull_request",
        "pull_requests": [
            {
                "number": 1287,
                "head": {
                    "sha": head,
                    "repo": {
                        "id": 42,
                        "name": "dopemux-mvp",
                        "url": "https://api.github.com/repos/DDD-Enterprises/dopemux-mvp",
                    },
                },
                "base": {
                    "repo": {
                        "id": 42,
                        "name": "dopemux-mvp",
                        "url": "https://api.github.com/repos/DDD-Enterprises/dopemux-mvp",
                    }
                },
            }
        ],
    }
    artifacts = {
        "artifacts": [{"id": 456, "name": "pr-readiness-invalidation-receipt-987"}]
    }
    receipt = {
        "schema_version": 1,
        "repository": repo,
        "workflow_run_id": 987,
        "event_name": "pull_request",
        "event_action": "opened",
        "pr_number": 1287,
        "observed_head_sha": head,
    }
    live_pr = {
        "number": 1287,
        "state": "open",
        "head": {"sha": head, "repo": {"id": 42, "full_name": repo}},
        "base": {"repo": {"id": 42, "full_name": repo}},
    }
    return run, artifacts, receipt, live_pr


def _run_binding(tmp_path: Path, mutate) -> subprocess.CompletedProcess[str]:
    run, artifacts, receipt, live_pr = _binding_payloads()
    mutate(run, artifacts, receipt, live_pr)
    paths = {}
    for name, payload in (
        ("RUN_JSON", run),
        ("ARTIFACTS_JSON", artifacts),
        ("RECEIPT_JSON", receipt),
        ("PR_JSON", live_pr),
    ):
        path = tmp_path / f"{name.lower()}.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        paths[name] = str(path)
    env = os.environ.copy()
    env.update(paths)
    env.update(
        {
            "EXPECTED_REPO": "DDD-Enterprises/dopemux-mvp",
            "EXPECTED_RUN_ID": "987",
            "GITHUB_OUTPUT": str(tmp_path / "output"),
        }
    )
    return subprocess.run(
        [sys.executable, "-"],
        input=_validation_python(),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_writer_accepts_exact_opened_binding(tmp_path: Path) -> None:
    result = _run_binding(tmp_path, lambda *_: None)

    assert result.returncode == 0, result.stdout + result.stderr


def test_writer_accepts_reopened_binding(tmp_path: Path) -> None:
    def mutate(run, _artifacts, receipt, _live_pr):
        receipt["event_action"] = "reopened"

    result = _run_binding(tmp_path, mutate)

    assert result.returncode == 0, result.stdout + result.stderr


def test_writer_accepts_synchronize_binding(tmp_path: Path) -> None:
    def mutate(_run, _artifacts, receipt, _live_pr):
        receipt["event_action"] = "synchronize"

    result = _run_binding(tmp_path, mutate)

    assert result.returncode == 0, result.stdout + result.stderr
    assert f"head_sha={'a' * 40}" in (tmp_path / "output").read_text(encoding="utf-8")


def test_writer_accepts_edited_review_binding(tmp_path: Path) -> None:
    def mutate(run, _artifacts, receipt, _live_pr):
        run["event"] = "pull_request_review"
        receipt["event_name"] = "pull_request_review"
        receipt["event_action"] = "edited"

    result = _run_binding(tmp_path, mutate)

    assert result.returncode == 0, result.stdout + result.stderr
    assert f"head_sha={'a' * 40}" in (tmp_path / "output").read_text(encoding="utf-8")


def test_writer_rejects_synchronize_receipt_when_live_head_moved(
    tmp_path: Path,
) -> None:
    def mutate(run, _artifacts, receipt, live_pr):
        receipt["event_action"] = "synchronize"
        run["pull_requests"][0]["head"]["sha"] = "b" * 40
        live_pr["head"]["sha"] = "b" * 40

    result = _run_binding(tmp_path, mutate)

    assert result.returncode != 0
    assert "receipt_head_mismatch" in result.stderr


def test_writer_rejects_unrelated_pr_number_in_receipt(tmp_path: Path) -> None:
    def mutate(_run, _artifacts, receipt, _live_pr):
        receipt["pr_number"] = 999

    result = _run_binding(tmp_path, mutate)

    assert result.returncode != 0
    assert "receipt_pr_mismatch" in result.stderr


def test_writer_rejects_repo_mismatch(tmp_path: Path) -> None:
    def mutate(_run, _artifacts, receipt, _live_pr):
        receipt["repository"] = "attacker/repo"

    result = _run_binding(tmp_path, mutate)

    assert result.returncode != 0
    assert "receipt_repository_mismatch" in result.stderr


def test_writer_rejects_head_mismatch(tmp_path: Path) -> None:
    def mutate(_run, _artifacts, receipt, _live_pr):
        receipt["observed_head_sha"] = "b" * 40

    result = _run_binding(tmp_path, mutate)

    assert result.returncode != 0
    assert "receipt_head_mismatch" in result.stderr


def test_writer_rejects_nonunique_associated_pr(tmp_path: Path) -> None:
    def mutate(run, _artifacts, _receipt, _live_pr):
        run["pull_requests"].append(run["pull_requests"][0].copy())

    result = _run_binding(tmp_path, mutate)

    assert result.returncode != 0
    assert "associated_pr_count" in result.stderr


def test_writer_rejects_review_thread_action_mismatch(tmp_path: Path) -> None:
    def mutate(run, _artifacts, receipt, _live_pr):
        run["event"] = "pull_request_review_thread"
        receipt["event_name"] = "pull_request_review_thread"
        receipt["event_action"] = "created"

    result = _run_binding(tmp_path, mutate)

    assert result.returncode != 0
    assert "event_action_not_allowed" in result.stderr


def test_templates_match_repository_workflows() -> None:
    assert TEMPLATE_OBSERVER.read_bytes() == OBSERVER.read_bytes()
    assert TEMPLATE_WRITER.read_bytes() == WRITER.read_bytes()


def test_template_steward_has_trusted_final_readiness_recovery_path() -> None:
    template_steward = (
        ROOT / "src/dopemux/templates/init/.github/workflows/pr-steward.yml"
    )

    workflow = _load(template_steward)
    text = template_steward.read_text(encoding="utf-8").lower()
    assert workflow["on"] == {
        "workflow_run": {"workflows": ["embedded-audit"], "types": ["completed"]},
        "workflow_dispatch": {
            "inputs": {
                "audit_run_id": {
                    "description": "Completed embedded-audit workflow run ID to inspect",
                    "required": "true",
                    "type": "string",
                }
            }
        },
    }
    assert workflow["permissions"]["statuses"] == "write"
    assert "pull_request:" not in text
    assert "checkout trusted steward source" in text
    assert "publish readiness status on candidate pr head" in text
    assert "allow_api_spend" not in text
    assert "run pal clink audit" not in text
    assert 'python -m pip install "$dopemux_install_spec"' in text
    assert "pip install -e ." not in text
    assert "python -m dopemux.cli pr-steward settlement fetch" in text
    assert "python -m dopemux.cli pr-steward settlement compare" in text
    assert "python -m dopemux.cli pr-steward intake" in text
    assert "python -m tools.pr_steward" not in text
    assert "scripts.audit" not in text
