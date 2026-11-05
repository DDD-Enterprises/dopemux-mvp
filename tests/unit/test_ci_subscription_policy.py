"""Exercise checked-in CI admission and summaries without calling providers.

These tests catch automatic PR model admission, skipped-review false greens,
and accidental weakening of the deterministic required-job gate. They evaluate
the workflow expressions and execute only provider-free summary shell blocks.
"""

import json
import os
from pathlib import Path
import re
import subprocess

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"
POLICY_WORKFLOWS = (
    "gemini-dispatch.yml",
    "gemini-scheduled-triage.yml",
    "ci-complete.yml",
    "security-review.yml",
)
REQUIRED = (
    "code-quality", "tests", "extractor-smoke", "audit-validator",
    "routing-consistency", "extractor-full", "extractor-lint", "auditor-router",
)
EXPRESSION = re.compile(r"\$\{\{(.*?)\}\}", re.DOTALL)


def workflow(name):
    # BaseLoader preserves the Actions `on` key and scalar expression strings.
    return yaml.load((WORKFLOWS / name).read_text(), Loader=yaml.BaseLoader)


def context(event_name, action="opened", *, draft=False, fork=False, key=True,
            body="", association="COLLABORATOR", sender="User"):
    repo = "DDD-Enterprises/dopemux-mvp"
    author = {"body": body, "author_association": association}
    return {
        "github": {
            "repository": repo, "event_name": event_name,
            "event": {
                "action": action, "sender": {"type": sender},
                "pull_request": {**author, "draft": draft, "head": {"repo": {
                    "fork": fork, "full_name": "other/fork" if fork else repo,
                }}},
                "comment": author, "review": author, "issue": author,
            },
        },
        "env": {"ANTHROPIC_API_KEY": "synthetic-key-present" if key else ""},
        "steps": {
            "model_review": {"outcome": "skipped"},
            "find_issues": {"outputs": {"issues_to_triage": "[1]"}},
            "detect_gemini_credentials": {"outputs": {
                "available": "true" if key else "false",
            }},
        },
        "needs": {"dispatch": {"result": "success", "outputs": {
            "command": "review", "has_gemini_credentials": "true" if key else "false",
        }}},
    }


def evaluate(expression, data):
    """Evaluate the workflow's small expression subset; unknown syntax fails."""
    expression = expression.strip().removeprefix("${{").removesuffix("}}").strip()
    expression = re.sub(
        r"\b(?:github|env|steps|needs)(?:\.[\w-]+)+",
        lambda match: f"lookup({match.group()!r})", expression,
    )
    expression = expression.replace("&&", " and ").replace("||", " or ")
    expression = re.sub(r"!(?!=)", " not ", expression)
    expression = re.sub(
        r"'(?:''|[^'])*'|\btrue\b|\bfalse\b",
        lambda match: {"true": "True", "false": "False"}.get(match.group(), match.group()),
        expression,
    )

    def lookup(path):
        value = data
        for part in path.split("."):
            value = value.get(part, "") if isinstance(value, dict) else ""
        return value

    return eval(expression.strip(), {"__builtins__": {}}, {
        "lookup": lookup, "always": lambda: True, "cancelled": lambda: False,
        "failure": lambda: False, "success": lambda: True,
        "fromJSON": json.loads, "startsWith": lambda text, prefix: text.startswith(prefix),
        "contains": lambda values, value: value in values,
    })


def model_steps(document, data):
    """Find reachable known provider actions, following local reusable jobs."""
    calls = []
    for job_id, job in document["jobs"].items():
        if not job.get("uses") and not any(
                step.get("uses", "").startswith(("anthropics/", "google-github-actions/run-gemini-cli@"))
                for step in job.get("steps", [])):
            continue
        if not evaluate(job.get("if", "success()"), data):
            continue
        dependencies = job.get("needs", [])
        if isinstance(dependencies, str):
            dependencies = [dependencies]
        if any(data["needs"].get(dep, {}).get("result") != "success"
               for dep in dependencies):
            continue
        if job.get("uses", "").startswith("./.github/workflows/"):
            calls.extend(model_steps(workflow(Path(job["uses"]).name), data))
        for step in job.get("steps", []):
            provider = step.get("uses", "").split("@")[0]
            if provider in {
                "anthropics/claude-code-security-review",
                "google-github-actions/run-gemini-cli",
            } and evaluate(step.get("if", "success()"), data):
                calls.append((job_id, provider))
    return calls


@pytest.mark.parametrize("action", ["opened", "synchronize", "reopened", "ready_for_review"])
@pytest.mark.parametrize("draft", [False, True])
@pytest.mark.parametrize("fork", [False, True])
@pytest.mark.parametrize("key", [False, True])
@pytest.mark.parametrize("body", ["", "@gemini-cli /review"])
@pytest.mark.parametrize("name", POLICY_WORKFLOWS)
def test_pr_lifecycle_never_admits_model_even_with_command_in_body(name, action, draft, fork, key, body):
    data = context("pull_request", action, draft=draft, fork=fork, key=key, body=body)
    doc = workflow(name)
    if name == "gemini-dispatch.yml":
        admitted = bool(evaluate(doc["jobs"]["dispatch"]["if"], data))
        data["needs"]["dispatch"]["result"] = "success" if admitted else "skipped"
    assert model_steps(doc, data) == [], name


@pytest.mark.parametrize("event_name,action", [
    ("pull_request_target", "ready_for_review"), ("merge_group", "checks_requested"),
])
def test_pr_derived_security_events_cannot_admit_claude(event_name, action):
    data = context(event_name, action)
    for name in ("ci-complete.yml", "security-review.yml"):
        assert model_steps(workflow(name), data) == []


@pytest.mark.parametrize("event_name,action,body,association,sender,want", [
    ("issues", "opened", "", "NONE", "User", True),
    ("issues", "reopened", "", "NONE", "User", True),
    ("pull_request_review", "submitted", "Approved", "COLLABORATOR", "User", False),
    ("pull_request_review", "submitted", "@gemini-cli /review", "COLLABORATOR", "User", True),
    ("pull_request_review_comment", "created", "@gemini-cli /review", "OWNER", "User", True),
    ("issue_comment", "created", "@gemini-cli /review", "MEMBER", "User", True),
    ("issue_comment", "created", "@gemini-cli /review", "NONE", "User", False),
    ("issue_comment", "created", "@gemini-cli /review", "OWNER", "Bot", False),
])
def test_existing_issue_and_explicit_trusted_command_admission_is_preserved(
        event_name, action, body, association, sender, want):
    data = context(event_name, action, body=body, association=association, sender=sender)
    actual = evaluate(workflow("gemini-dispatch.yml")["jobs"]["dispatch"]["if"], data)
    assert bool(actual) is want


@pytest.mark.parametrize("name", ["ci-complete.yml", "security-review.yml"])
@pytest.mark.parametrize("event_name", ["push", "workflow_dispatch"])
@pytest.mark.parametrize("key", [False, True])
def test_non_pr_security_retains_credential_guard(name, event_name, key):
    # workflow_dispatch is only currently subscribed by ci-complete; this also
    # proves the action condition does not silently enable a missing key.
    data = context(event_name, key=key)
    assert bool(model_steps(workflow(name), data)) is key


@pytest.mark.parametrize("event_name", ["schedule", "push", "workflow_dispatch"])
@pytest.mark.parametrize("key", [False, True])
def test_scheduled_triage_retains_existing_non_pr_credential_guard(event_name, key):
    assert bool(model_steps(workflow("gemini-scheduled-triage.yml"),
                            context(event_name, key=key))) is key


def run_summary(script, data, tmp_path, script_env=None):
    summary = tmp_path / "summary.md"
    rendered = EXPRESSION.sub(lambda match: str(evaluate(match.group(1), data)), script)
    result = subprocess.run(
        ["bash", "--noprofile", "--norc", "-eo", "pipefail", "-c", rendered],
        env={**os.environ, "GITHUB_STEP_SUMMARY": summary.name, **{
            key: EXPRESSION.sub(lambda match: str(evaluate(match.group(1), data)), value)
            for key, value in (script_env or {}).items()
        }},
        cwd=tmp_path,
        capture_output=True, text=True, check=False,
    )
    return result, summary.read_text() if summary.exists() else ""


@pytest.mark.parametrize("name,job_id", [
    ("ci-complete.yml", "security"), ("security-review.yml", "security-review"),
])
@pytest.mark.parametrize("event_name", ["pull_request", "merge_group"])
def test_security_not_run_is_pending_and_fails_closed(name, job_id, event_name, tmp_path):
    data = context(event_name)
    job = workflow(name)["jobs"][job_id]
    terminal = [step for step in job["steps"] if "run" in step and
                evaluate(step.get("if", "success()"), data)]
    assert terminal, "A skipped provider action cannot stand in for security review"
    results = [run_summary(step["run"], data, tmp_path, step.get("env")) for step in terminal]
    assert any(result.returncode != 0 for result, _ in results)
    assert any("NOT_RUN" in text and "pending" in text.lower() for _, text in results)


@pytest.mark.parametrize("name,job_id", [
    ("ci-complete.yml", "security"), ("security-review.yml", "security-review"),
])
@pytest.mark.parametrize("outcome", ["skipped", "success", "failure", "cancelled"])
def test_non_pr_security_summary_reports_actual_action_outcome(name, job_id, outcome, tmp_path):
    data = context("push")
    data["steps"]["model_review"]["outcome"] = outcome
    summaries = [step for step in workflow(name)["jobs"][job_id]["steps"] if "run" in step]
    assert summaries, "Security status must reflect whether its provider action ran"
    terminal = summaries[-1]
    _, text = run_summary(terminal["run"], data, tmp_path, terminal.get("env"))
    if outcome == "skipped":
        assert "NOT_RUN" in text and "pending" in text.lower()
    elif outcome == "success":
        assert "Model analysis completed" in text and "not merge approval" in text
    else:
        assert "incomplete" in text.lower()


@pytest.mark.parametrize("result", ["success", "skipped", "failure", "cancelled"])
def test_separate_pr_security_summary_never_accepts_a_skipped_review(result, tmp_path):
    data = context("pull_request")
    data["needs"] = {"security-review": {"result": result}}
    step = workflow("security-review.yml")["jobs"]["security-summary"]["steps"][0]
    actual, text = run_summary(step["run"], data, tmp_path)
    assert actual.returncode != 0
    assert "NOT_RUN" in text and "pending" in text.lower()


@pytest.mark.parametrize("failed_job", [None, *REQUIRED])
def test_summary_preserves_deterministic_gate_without_claiming_security_clear(failed_job, tmp_path):
    data = context("pull_request")
    data["needs"] = {job: {"result": "success"} for job in REQUIRED}
    data["needs"].update({
        "security": {"result": "failure", "outputs": {"model_review_outcome": "skipped"}},
        "docs": {"result": "success"},
        **{job: {"result": "skipped"} for job in ("installer-smoke", "scoped-coverage", "integration")},
    })
    if failed_job:
        data["needs"][failed_job]["result"] = "failure"
    script = workflow("ci-complete.yml")["jobs"]["ci-summary"]["steps"][0]["run"]
    result, text = run_summary(script, data, tmp_path)
    assert (result.returncode == 0) is (failed_job is None)
    assert "NOT_RUN" in text and "pending" in text.lower()
    assert "Memory systems are secure" not in text
    assert "Ready to merge" not in text


def test_provider_action_inventory_has_no_unexamined_automatic_caller():
    direct = set()
    reusable = set()
    for path in WORKFLOWS.glob("*.yml"):
        doc = workflow(path.name)
        for job in doc.get("jobs", {}).values():
            if job.get("uses", "").startswith("./.github/workflows/gemini-"):
                reusable.add(path.name)
            for step in job.get("steps", []):
                uses = step.get("uses", "").lower()
                if any(provider in uses for provider in ("anthropic", "gemini", "openai", "openrouter")):
                    direct.add(path.name)
    assert reusable == {"gemini-dispatch.yml"}
    assert direct == {
        "ci-complete.yml", "security-review.yml", "gemini-scheduled-triage.yml",
        "gemini-review.yml", "gemini-triage.yml", "gemini-invoke.yml", "gemini-plan-execute.yml",
    }
    for name in direct - set(POLICY_WORKFLOWS):
        assert set(workflow(name)["on"]) == {"workflow_call"}
