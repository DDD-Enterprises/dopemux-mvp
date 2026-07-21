"""Deterministic embedded-audit workflow-run identity validation.

Extracted from the inline Python previously embedded in the "Validate audit
workflow-run identity" step of `.github/workflows/pr-steward.yml` so the
identity checks are importable and unit-testable outside the Actions
runner. Pure data in, pure data out: no GitHub API calls, no file I/O, no
environment access. Every branch and error string below is preserved
exactly as it was inline; this is an extraction, not a behavior change.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RunIdentityResult:
    """Result of validating a GitHub Actions run payload's identity.

    `ok` is False whenever `errors` is non-empty. `run_head_sha` and
    `conclusion` are populated best-effort even when `ok` is False, so a
    non-success conclusion can still bind the candidate PR head and let the
    caller publish an explicit failure status rather than leaving a stale
    prior status in place.
    """

    ok: bool
    errors: tuple[str, ...]
    run_head_sha: str
    conclusion: str
    conclusion_ok: bool
    workflow_name: str
    workflow_path: str
    pr_number: int | None


def validate_run_identity(
    run: Any,
    *,
    expected_run_id: int,
    expected_repo: str,
    expected_workflow_name: str = "embedded-audit",
    expected_workflow_path_suffix: str = "embedded-audit.yml",
) -> RunIdentityResult:
    """Validate an Actions run payload against the expected embedded-audit identity.

    Checks (all fail-closed, all preserved from the original inline script):
      - run id matches the requested run id
      - repository.full_name is present and matches expected_repo
      - workflow display name and path match the expected embedded-audit workflow
      - run status is "completed"
      - head_sha is present (informational; not used for PR-head artifact identity)
      - conclusion is present (non-success conclusions are recorded, not rejected,
        so a failed audit can still bind candidate head and publish failure status)

    A malformed payload (not a mapping) is treated as a fully-failed identity
    check rather than raising, so a caller can fail closed instead of crashing.
    """
    if not isinstance(run, dict):
        return RunIdentityResult(
            ok=False,
            errors=("malformed_run_payload: run is not a mapping",),
            run_head_sha="",
            conclusion="",
            conclusion_ok=False,
            workflow_name="",
            workflow_path="",
            pr_number=None,
        )

    errors: list[str] = []

    run_id = int(run.get("id") or 0)
    if run_id != expected_run_id:
        errors.append(f"run_id_mismatch: {run_id} != {expected_run_id}")

    repository = run.get("repository")
    repo_full = repository.get("full_name") if isinstance(repository, dict) else None
    if not repo_full:
        errors.append("repository_missing: actions run lacks repository.full_name")
    elif repo_full != expected_repo:
        errors.append(f"repository_mismatch: {repo_full!r} != {expected_repo!r}")

    name = str(run.get("name") or "")
    path = str(run.get("path") or "")
    if not (name == expected_workflow_name and path.endswith(expected_workflow_path_suffix)):
        errors.append(f"workflow_mismatch: name={name!r} path={path!r}")

    status = str(run.get("status") or "")
    if status != "completed":
        errors.append(f"run_not_completed: status={status!r}")

    run_head_sha = str(run.get("head_sha") or "")
    if not run_head_sha:
        errors.append("run_head_sha_missing")

    conclusion = str(run.get("conclusion") or "")
    if not conclusion:
        errors.append("run_conclusion_missing")

    pr_number: int | None = None
    pull_requests = run.get("pull_requests")
    if isinstance(pull_requests, list) and pull_requests:
        first = pull_requests[0]
        if isinstance(first, dict) and isinstance(first.get("number"), int):
            pr_number = first["number"]

    return RunIdentityResult(
        ok=not errors,
        errors=tuple(errors),
        run_head_sha=run_head_sha,
        conclusion=conclusion,
        conclusion_ok=conclusion == "success",
        workflow_name=name,
        workflow_path=path,
        pr_number=pr_number,
    )
