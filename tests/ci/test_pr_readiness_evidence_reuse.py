"""Offline contracts for metadata-only, exact-head audit evidence reuse."""

import copy
import json
import re
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github/workflows"
RECHECK = WORKFLOWS / "pr-steward-recheck.yml"
REPO = "DDD-Enterprises/dopemux-mvp"
HEAD = "a" * 40
BASE = "b" * 40
CI_NAME = "🚀 Complete CI Pipeline (ADHD-Optimized)"
ARTIFACT_NAME = f"embedded-audit-pr-42-head-{HEAD}-proof"
PREFIX = f"repos/{REPO}"
EXPENSIVE = ("ci-complete.yml", "preflight.yml", "embedded-audit.yml")


def workflow(name):
    path = WORKFLOWS / name
    assert path.is_file(), f"Missing workflow: {name}"
    return yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)


@pytest.mark.parametrize("name", EXPENSIVE)
def test_expensive_workflows_only_use_head_change_pr_activities(name):
    triggers = workflow(name)["on"]
    event = "pull_request_target" if name == "embedded-audit.yml" else "pull_request"
    assert triggers[event]["types"] == ["opened", "synchronize", "reopened"]
    assert "pull_request_review" not in triggers
    assert "workflow_dispatch" in triggers
    if name == "ci-complete.yml":
        assert triggers["push"] == {"branches": ["main"]}
        assert triggers["merge_group"] == {"types": ["checks_requested"]}


def test_recheck_triggers_permissions_and_concurrency():
    doc = workflow(RECHECK.name)
    assert doc["on"] == {
        "pull_request_target": {"types": ["ready_for_review"]},
        "pull_request_review": {"types": ["submitted", "dismissed"]},
        "workflow_run": {"workflows": [CI_NAME], "types": ["completed"]},
        "workflow_dispatch": {"inputs": {"pr_number": {
            "description": "Open pull request number to recheck",
            "required": "true", "type": "string",
        }}},
    }
    assert doc["permissions"] == {
        "contents": "read", "pull-requests": "read", "actions": "write",
    }
    concurrency = doc["concurrency"]
    assert concurrency["cancel-in-progress"] == "true"
    for pr_source in ("github.event.pull_request.number", "inputs.pr_number",
                      "github.event.workflow_run.pull_requests[0].number"):
        assert pr_source in concurrency["group"]
    assert set(doc["jobs"]) == {"recheck"}
    job = doc["jobs"]["recheck"]
    assert "permissions" not in job
    assert int(job["timeout-minutes"]) <= 5


def test_recheck_has_no_checkout_candidate_execution_or_provider_surface():
    doc = workflow(RECHECK.name)
    text = RECHECK.read_text(encoding="utf-8").lower()
    for forbidden in ("actions/checkout", "download-artifact", "secrets.",
                      "claude", "gemini", "anthropic", "openai", "litellm",
                      "api_key", "id-token", "pip install", "npm ", "git fetch"):
        assert forbidden not in text
    steps = doc["jobs"]["recheck"]["steps"]
    assert len(steps) == 1
    assert "uses" not in steps[0]
    assert steps[0]["env"] == {"GH_TOKEN": "${{ github.token }}"}
    assert "${{" not in steps[0]["run"]
    assert steps[0]["run"].startswith("python3 - <<'PY'\n")


def fixture(event_name="pull_request_target", action="ready_for_review"):
    repository = {"id": 7, "full_name": REPO, "default_branch": "main"}
    pr = {"number": 42, "state": "open", "head": {"sha": HEAD},
          "base": {"sha": BASE, "repo": repository}}
    run = {"id": 90, "repository": repository, "name": "embedded-audit",
           "path": ".github/workflows/embedded-audit.yml", "workflow_id": 9,
           "status": "completed", "conclusion": "success",
           "event": "pull_request_target", "head_sha": BASE}
    artifact = {"id": 100, "name": ARTIFACT_NAME, "expired": False,
                "created_at": "2026-01-01T00:00:00Z",
                "expires_at": "2099-01-01T00:00:00Z",
                "workflow_run": {"id": 90, "repository_id": 7}}
    ci_run = {**run, "id": 80, "workflow_id": 8, "name": CI_NAME,
              "path": ".github/workflows/ci-complete.yml",
              "event": "pull_request", "head_sha": HEAD,
              "pull_requests": [{"number": 42, "head": {"sha": HEAD},
                                 "base": {"repo": {"id": 7}}}]}
    event = {"action": action, "repository": repository,
             "number": 42, "pull_request": copy.deepcopy(pr)}
    if event_name == "workflow_run":
        event = {"action": "completed", "repository": repository,
                 "workflow_run": copy.deepcopy(ci_run)}
    elif event_name == "workflow_dispatch":
        event = {"repository": repository, "inputs": {"pr_number": "42"}}
    return {"event_name": event_name, "event": event, "repo": repository,
            "pr": pr, "run": run, "ci_run": ci_run, "artifacts": [artifact],
            "run_artifacts": [copy.deepcopy(artifact)]}


def execute(monkeypatch, tmp_path, data):
    """Execute the actual inline script; replace only the GitHub API boundary."""
    step = workflow(RECHECK.name)["jobs"]["recheck"]["steps"][0]
    shell = step["run"]
    assert shell.endswith("\nPY\n")
    source = shell.split("\n", 1)[1].rsplit("\nPY", 1)[0]
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps(data["event"]), encoding="utf-8")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))
    monkeypatch.setenv("GITHUB_EVENT_NAME", data["event_name"])
    monkeypatch.setenv("GITHUB_REPOSITORY", REPO)
    monkeypatch.setenv("GITHUB_REPOSITORY_ID", "7")
    dispatches, reads = [], []
    pr_reads = 0
    run_reads = 0

    def api(command, *, input=None, **kwargs):
        nonlocal pr_reads, run_reads
        assert command[:3] == ["gh", "api", "--method"]
        assert kwargs == {"check": True, "capture_output": True, "text": True}
        method, route = command[3:5]
        if method == "POST":
            assert command[5:] == ["--input", "-"]
            dispatches.append((route, json.loads(input)))
            return subprocess.CompletedProcess(command, 0, "", "")
        assert method == "GET"
        reads.append(route)
        if route in data.get("api_errors", []):
            raise subprocess.CalledProcessError(1, command, stderr="API unavailable")
        if route == PREFIX:
            result = data["repo"]
        elif route == f"{PREFIX}/pulls/42":
            pr_reads += 1
            result = data.get("pr_after", data["pr"]) if pr_reads > 1 else data["pr"]
        elif route.startswith(f"{PREFIX}/actions/workflows/"):
            filename = route.rsplit("/", 1)[1]
            result = {"id": {"ci-complete.yml": 8, "embedded-audit.yml": 9,
                             "pr-steward.yml": 10}[filename],
                      "path": f".github/workflows/{filename}"}
            result.update(data.get("workflow_overrides", {}).get(filename, {}))
        elif route == f"{PREFIX}/actions/runs/80":
            result = data["ci_run"]
        elif route == f"{PREFIX}/actions/runs/90":
            run_reads += 1
            result = data.get("run_after", data["run"]) if run_reads > 1 else data["run"]
        elif route.startswith(f"{PREFIX}/actions/runs/") and route.endswith("/artifacts"):
            result = [{"artifacts": data["run_artifacts"]}]
        elif route == f"{PREFIX}/actions/artifacts?name={ARTIFACT_NAME}&per_page=100":
            result = data.get("pages", [{"artifacts": data["artifacts"]}])
        elif route.startswith(f"{PREFIX}/actions/runs/"):
            result = data["other_runs"][int(route.rsplit("/", 1)[1])]
        else:
            raise AssertionError(f"Unexpected API route: {route}")
        paginated = "artifacts" in route
        assert command[5:] == (["--paginate", "--slurp"] if paginated else [])
        return subprocess.CompletedProcess(command, 0, json.dumps(result), "")

    monkeypatch.setattr(subprocess, "run", api)
    error = None
    try:
        exec(compile(source, str(RECHECK), "exec"), {"__name__": "__main__"})
    except (SystemExit, ValueError, subprocess.CalledProcessError) as exc:
        error = str(exc)
    return dispatches, error, reads


@pytest.mark.parametrize("event_name,action", [
    ("pull_request_target", "ready_for_review"),
    ("pull_request_review", "submitted"), ("pull_request_review", "dismissed"),
    ("workflow_run", "completed"), ("workflow_dispatch", None),
])
def test_valid_events_dispatch_only_steward_on_default_branch(monkeypatch, tmp_path, event_name, action):
    data = fixture(event_name, action)
    data["repo"]["default_branch"] = "trunk"
    dispatches, error, _ = execute(monkeypatch, tmp_path, data)
    assert error is None
    assert dispatches == [(f"{PREFIX}/actions/workflows/pr-steward.yml/dispatches",
                           {"ref": "trunk", "inputs": {"audit_run_id": "90"}})]


@pytest.mark.parametrize("field,value", [
    ("number", 41), ("state", "closed"), ("head.sha", "c" * 40),
    ("head.sha", "invalid"), ("base.repo.full_name", "attacker/repo"),
    ("base.repo.id", 99),
])
@pytest.mark.parametrize("when", ["pr", "pr_after"])
def test_live_pr_identity_and_races_fail_closed(monkeypatch, tmp_path, field, value, when):
    data = fixture()
    data[when] = copy.deepcopy(data["pr"])
    target = data[when]
    parts = field.split(".")
    for part in parts[:-1]:
        target = target[part]
    target[parts[-1]] = value
    dispatches, error, _ = execute(monkeypatch, tmp_path, data)
    assert error
    assert dispatches == []


@pytest.mark.parametrize("value", ["", "0", "-1", "42x", "042", "42\n", True, 4.2])
def test_manual_pr_must_be_strict_positive_integer(monkeypatch, tmp_path, value):
    data = fixture("workflow_dispatch")
    data["event"]["inputs"]["pr_number"] = value
    dispatches, error, _ = execute(monkeypatch, tmp_path, data)
    assert error
    assert dispatches == []


@pytest.mark.parametrize("source", ["event", "live"])
@pytest.mark.parametrize("change", [{"id": 99}, {"full_name": "attacker/repo"}])
def test_repository_identity_must_match_context(monkeypatch, tmp_path, source, change):
    data = fixture()
    if source == "event":
        data["event"]["repository"] = {**data["repo"], **change}
    else:
        data["repo"] = {**data["repo"], **change}
    dispatches, error, _ = execute(monkeypatch, tmp_path, data)
    assert error
    assert dispatches == []


@pytest.mark.parametrize("change", ["number", "head", "base_repo", "action"])
def test_stale_or_invalid_review_event_fails_closed(monkeypatch, tmp_path, change):
    data = fixture("pull_request_review", "submitted")
    event = data["event"]
    if change == "number":
        event["number"] = 43
    elif change == "head":
        event["pull_request"]["head"]["sha"] = BASE
    elif change == "base_repo":
        event["pull_request"]["base"]["repo"]["full_name"] = "attacker/repo"
    else:
        event["action"] = "edited"
    dispatches, error, _ = execute(monkeypatch, tmp_path, data)
    assert error
    assert dispatches == []


@pytest.mark.parametrize("action", ["submitted", "dismissed"])
def test_stale_review_commit_still_dispatches_exact_head_recheck(monkeypatch, tmp_path, action):
    data = fixture("pull_request_review", action)
    data["event"]["review"] = {"commit_id": BASE}
    dispatches, error, _ = execute(monkeypatch, tmp_path, data)
    assert error is None
    assert dispatches == [(f"{PREFIX}/actions/workflows/pr-steward.yml/dispatches",
                           {"ref": "main", "inputs": {"audit_run_id": "90"}})]


@pytest.mark.parametrize("filename", ["ci-complete.yml", "embedded-audit.yml", "pr-steward.yml"])
def test_workflow_metadata_must_bind_expected_path(monkeypatch, tmp_path, filename):
    data = fixture("workflow_run")
    data["workflow_overrides"] = {filename: {"path": ".github/workflows/impostor.yml"}}
    dispatches, error, _ = execute(monkeypatch, tmp_path, data)
    assert error
    assert dispatches == []


@pytest.mark.parametrize("endpoint", ["", "/pulls/42", "/actions/runs/90",
                                      "/actions/runs/90/artifacts"])
def test_api_errors_do_not_dispatch_or_retry(monkeypatch, tmp_path, endpoint):
    data = fixture()
    data["api_errors"] = [PREFIX + endpoint]
    dispatches, error, reads = execute(monkeypatch, tmp_path, data)
    assert error
    assert dispatches == []
    assert reads.count(PREFIX + endpoint) == 1


@pytest.mark.parametrize("field,value", [
    ("name", "other CI"), ("path", ".github/workflows/other.yml"),
    ("workflow_id", 99), ("status", "in_progress"), ("head_sha", BASE),
    ("repository", {"id": 99, "full_name": "attacker/repo"}),
])
@pytest.mark.parametrize("source", ["event", "live"])
def test_ci_completion_requires_trusted_source_identity_and_head(monkeypatch, tmp_path, field, value, source):
    data = fixture("workflow_run")
    run = data["event"]["workflow_run"] if source == "event" else data["ci_run"]
    run[field] = value
    dispatches, error, _ = execute(monkeypatch, tmp_path, data)
    assert error
    assert dispatches == []


@pytest.mark.parametrize("field,value", [
    ("event", "push"), ("event", "merge_group"),
    ("conclusion", "failure"), ("conclusion", "cancelled"), ("conclusion", None),
])
def test_irrelevant_or_unsuccessful_ci_completion_is_quiet_noop(monkeypatch, tmp_path, field, value):
    data = fixture("workflow_run")
    data["event"]["workflow_run"][field] = value
    dispatches, error, reads = execute(monkeypatch, tmp_path, data)
    assert error is None
    assert dispatches == []
    assert not any("/pulls/" in route or "artifacts" in route for route in reads)


@pytest.mark.parametrize("field,value", [
    ("event", "push"), ("conclusion", "failure"), ("conclusion", "cancelled"),
])
def test_live_ci_refresh_contradiction_fails_closed(monkeypatch, tmp_path, field, value):
    data = fixture("workflow_run")
    data["ci_run"][field] = value
    dispatches, error, _ = execute(monkeypatch, tmp_path, data)
    assert error
    assert dispatches == []


def test_no_ci_pr_association_is_noop_without_guessing(monkeypatch, tmp_path):
    data = fixture("workflow_run")
    data["event"]["workflow_run"]["pull_requests"] = []
    dispatches, error, reads = execute(monkeypatch, tmp_path, data)
    assert error is None
    assert dispatches == []
    assert not any("/pulls/" in route or "artifacts" in route for route in reads)


@pytest.mark.parametrize("source", ["event", "live"])
def test_ambiguous_ci_pr_association_fails_closed(monkeypatch, tmp_path, source):
    data = fixture("workflow_run")
    run = data["event"]["workflow_run"] if source == "event" else data["ci_run"]
    run["pull_requests"].append({"number": 43, "head": {"sha": HEAD}})
    dispatches, error, _ = execute(monkeypatch, tmp_path, data)
    assert error
    assert dispatches == []


@pytest.mark.parametrize("field,value", [
    ("name", "other"), ("path", ".github/workflows/other.yml"),
    ("path", "untrusted/embedded-audit.yml"), ("workflow_id", 99),
    ("conclusion", "failure"), ("conclusion", None),
    ("status", "in_progress"), ("id", 91),
    ("repository", {"id": 7, "full_name": "attacker/repo"}),
    ("repository", {}),
])
@pytest.mark.parametrize("when", ["run", "run_after"])
def test_audit_run_must_remain_successful_and_trusted(monkeypatch, tmp_path, field, value, when):
    data = fixture()
    data[when] = {**data["run"], field: value}
    dispatches, error, _ = execute(monkeypatch, tmp_path, data)
    assert error
    assert dispatches == []


@pytest.mark.parametrize("change", [
    {"name": f"embedded-audit-pr-42-head-{BASE}-proof"},
    {"name": f"embedded-audit-pr-43-head-{HEAD}-proof"},
    {"name": ARTIFACT_NAME + "-extra"}, {"expired": True}, {"expired": None},
    {"expires_at": "2000-01-01T00:00:00Z"}, {"expires_at": "invalid"},
    {"created_at": "invalid"}, {"id": None},
    {"workflow_run": {"id": 90, "repository_id": 99}},
])
def test_wrong_stale_expired_or_malformed_artifact_fails_closed(monkeypatch, tmp_path, change):
    data = fixture()
    data["artifacts"][0].update(change)
    dispatches, error, _ = execute(monkeypatch, tmp_path, data)
    assert error
    assert dispatches == []


def test_missing_artifact_fails_closed(monkeypatch, tmp_path):
    data = fixture()
    data["artifacts"] = []
    dispatches, error, _ = execute(monkeypatch, tmp_path, data)
    assert error
    assert dispatches == []


def test_latest_artifact_selection_is_paginated_and_deterministic(monkeypatch, tmp_path):
    data = fixture()
    older = {**data["artifacts"][0], "id": 99,
             "workflow_run": {"id": 89, "repository_id": 7}}
    data["other_runs"] = {89: {**data["run"], "id": 89}}
    data["pages"] = [{"artifacts": [older]}, {"artifacts": data["artifacts"]}]
    first, error, _ = execute(monkeypatch, tmp_path, data)
    assert error is None
    assert first[0][1]["inputs"] == {"audit_run_id": "90"}
    data["pages"].reverse()
    second, error, _ = execute(monkeypatch, tmp_path, data)
    assert error is None
    assert second == first


def test_artifact_creation_time_takes_priority_over_id(monkeypatch, tmp_path):
    data = fixture()
    older = {**data["artifacts"][0], "id": 101, "created_at": "2025-01-01T00:00:00Z",
             "workflow_run": {"id": 89, "repository_id": 7}}
    data["other_runs"] = {89: {**data["run"], "id": 89}}
    data["artifacts"].append(older)
    dispatches, error, _ = execute(monkeypatch, tmp_path, data)
    assert error is None
    assert dispatches[0][1]["inputs"] == {"audit_run_id": "90"}


@pytest.mark.parametrize("conclusion", [
    "failure", "cancelled", "timed_out", "stale", None,
])
def test_newer_trusted_non_success_audit_fails_closed(monkeypatch, tmp_path, conclusion):
    data = fixture()
    newer = {**data["artifacts"][0], "id": 101, "created_at": "2026-01-02T00:00:00Z",
             "workflow_run": {"id": 91, "repository_id": 7}}
    data["other_runs"] = {91: {**data["run"], "id": 91, "conclusion": conclusion}}
    data["artifacts"].append(newer)
    dispatches, error, _ = execute(monkeypatch, tmp_path, data)
    assert error
    assert dispatches == []


@pytest.mark.parametrize("change", [
    {"name": "impostor"},
    {"path": "untrusted/embedded-audit.yml"},
    {"workflow_id": 99},
    {"status": "in_progress"},
    {"repository": {"id": 7, "full_name": "attacker/repo"}},
])
def test_newer_untrusted_run_is_not_considered(monkeypatch, tmp_path, change):
    data = fixture()
    newer = {**data["artifacts"][0], "id": 101, "created_at": "2026-01-02T00:00:00Z",
             "workflow_run": {"id": 91, "repository_id": 7}}
    data["other_runs"] = {91: {**data["run"], "id": 91, **change}}
    data["artifacts"].append(newer)
    dispatches, error, _ = execute(monkeypatch, tmp_path, data)
    assert error is None
    assert dispatches[0][1]["inputs"] == {"audit_run_id": "90"}


@pytest.mark.parametrize("ambiguity", ["duplicate", "other_head", "missing", "expired"])
def test_ambiguous_or_changed_selected_run_artifacts_fail_closed(monkeypatch, tmp_path, ambiguity):
    data = fixture()
    if ambiguity == "duplicate":
        data["artifacts"].append(copy.deepcopy(data["artifacts"][0]))
    elif ambiguity == "other_head":
        data["run_artifacts"].append({**data["artifacts"][0], "id": 101,
                                      "name": f"embedded-audit-pr-42-head-{BASE}-proof"})
    elif ambiguity == "missing":
        data["run_artifacts"] = []
    else:
        data["run_artifacts"][0]["expired"] = True
    dispatches, error, _ = execute(monkeypatch, tmp_path, data)
    assert error
    assert dispatches == []


@pytest.mark.parametrize("body,association,sender,expected", [
    ("Approved", "COLLABORATOR", "User", False),
    ("", "OWNER", "User", False),
    ("@gemini-cli /review", "COLLABORATOR", "User", True),
    ("@gemini-cli /review", "NONE", "User", False),
    ("@gemini-cli /review", "OWNER", "Bot", False),
])
def test_gemini_review_submission_requires_explicit_collaborator_command(body, association, sender, expected):
    """Amendment 001: evaluate the existing gate, without invoking its actions."""
    doc = workflow("gemini-dispatch.yml")
    assert doc["on"]["pull_request_review"]["types"] == ["submitted"]
    condition = doc["jobs"]["dispatch"]["if"]
    condition = condition.replace("&&", " and ").replace("||", " or ")
    condition = re.sub(r"\bfalse\b", "False", condition)
    empty = SimpleNamespace(body="", author_association="")
    github = SimpleNamespace(event_name="pull_request_review", event=SimpleNamespace(
        action="submitted", sender=SimpleNamespace(type=sender),
        comment=empty, issue=empty,
        review=SimpleNamespace(body=body, author_association=association),
    ))
    result = eval(condition, {"__builtins__": {}}, {
        "github": github, "fromJSON": json.loads,
        "startsWith": lambda text, prefix: text.startswith(prefix),
        "contains": lambda values, value: value in values,
    })
    assert result is expected
