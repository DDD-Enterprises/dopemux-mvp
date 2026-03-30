from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence

from .runtime import (
    append_command_log,
    execute_or_dry_run,
    fingerprint_payload,
    run_command,
    shell_join,
)
from .schema import (
    Fingerprint,
    ValidationReport,
    ValidationStatus,
    ValidationStepResult,
)

SCOPED_VALIDATION_SCOPES = {
    "changed_files",
    "docs_frontmatter_files",
    "docs_validator_files",
}


def _unique_paths(paths: Sequence[str]) -> List[str]:
    unique: Dict[str, None] = {}
    for path in paths:
        normalized = str(path).strip()
        if normalized:
            unique[normalized] = None
    return sorted(unique)


def _is_docs_frontmatter_candidate(path: str) -> bool:
    normalized = path.replace("\\", "/")
    if not normalized.endswith(".md"):
        return False
    if normalized.startswith(("docs/", "task-packets/", "UPGRADES/")):
        return True
    parts = normalized.split("/")
    if len(parts) >= 3 and parts[0] in {"services", "docker"} and parts[2] == "docs":
        return True
    return False


def _is_docs_validator_candidate(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return normalized.endswith(".md") and normalized.startswith(
        ("docs/", "task-packets/")
    )


def _resolve_step_files(scope: str, changed_files: Sequence[str]) -> Optional[List[str]]:
    if scope == "changed_files":
        return list(changed_files)
    if scope == "docs_frontmatter_files":
        return [path for path in changed_files if _is_docs_frontmatter_candidate(path)]
    if scope == "docs_validator_files":
        return [path for path in changed_files if _is_docs_validator_candidate(path)]
    return None


def _build_scoped_command(command: Sequence[str], scope_files: Sequence[str]) -> List[str]:
    scoped = [str(part) for part in command]
    if scoped[:2] == ["pre-commit", "run"] and "--files" not in scoped:
        return [*scoped, "--files", *scope_files]
    return [*scoped, *scope_files]


def _collect_changed_files(
    *,
    cwd: Path,
    base_sha: str,
    commands_log: Path,
    timeout_seconds: int,
) -> List[str]:
    collected: List[str] = []
    commands = [
        ["git", "diff", "--name-only", "--diff-filter=ACMR", f"{base_sha}...HEAD"],
        ["git", "diff", "--name-only", "--diff-filter=ACMR", "HEAD"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    ]
    for command in commands:
        result = run_command(command, cwd=cwd, timeout_seconds=timeout_seconds)
        append_command_log(commands_log, result)
        if result.returncode != 0:
            raise RuntimeError(
                result.stderr.strip()
                or f"Unable to resolve changed files for validation via {shell_join(command)}"
            )
        collected.extend(line.strip() for line in result.stdout.splitlines())
    return _unique_paths(collected)


def validation_fingerprint(
    *,
    pr_id: int,
    head_sha: str,
    base_sha: str,
    policy_fingerprint: str,
    lifecycle_state: str,
) -> Fingerprint:
    payload = {
        "pr_id": pr_id,
        "head_sha": head_sha,
        "base_sha": base_sha,
        "policy_fingerprint": policy_fingerprint,
        "lifecycle_state": lifecycle_state,
    }
    digest = fingerprint_payload(payload)
    return Fingerprint(
        input_fingerprint=digest,
        valid_for_sha=head_sha,
        stale_if=[
            "PR head SHA changes",
            "base SHA changes",
            "effective policy fingerprint changes",
            "applied tree contents change",
        ],
        created_from_state=lifecycle_state,
    )


def run_validation(
    *,
    repo_root: Path,
    worktree_path: Optional[Path],
    policy: Dict[str, Any],
    execute: bool,
    commands_log: Path,
    pr_id: int,
    head_sha: str,
    base_sha: str,
    policy_fingerprint: str,
    lifecycle_state: str,
    progress_callback: Optional[Callable[[str, str], None]] = None,
) -> ValidationReport:
    target_cwd = worktree_path or repo_root
    steps_cfg = list(policy.get("validation", {}).get("steps", []))
    timeout_seconds = int(
        policy.get("timeouts", {}).get("subprocess_seconds", 600) or 600
    )
    fingerprint = validation_fingerprint(
        pr_id=pr_id,
        head_sha=head_sha,
        base_sha=base_sha,
        policy_fingerprint=policy_fingerprint,
        lifecycle_state=lifecycle_state,
    )
    if not execute:
        steps = [
            ValidationStepResult(
                name=str(step.get("name", "unnamed-step")),
                command=shell_join(step.get("command", [])),
                status="planned",
            )
            for step in steps_cfg
        ]
        return ValidationReport(
            status=ValidationStatus.NOT_EXECUTED,
            required_for_merge_ready=bool(
                policy.get("validation", {}).get(
                    "require_local_validation_for_merge_ready", True
                )
            ),
            steps=steps,
            attempts=0,
            remediation_applied=False,
            fingerprint=fingerprint,
        )

    step_results: List[ValidationStepResult] = []
    remediation_applied = False
    changed_files: Optional[List[str]] = None
    if any(str(step.get("scope", "repo")) in SCOPED_VALIDATION_SCOPES for step in steps_cfg):
        if progress_callback:
            progress_callback("Resolving changed files for scoped validation", "INFO")
        try:
            changed_files = _collect_changed_files(
                cwd=target_cwd,
                base_sha=base_sha,
                commands_log=commands_log,
                timeout_seconds=timeout_seconds,
            )
        except RuntimeError as exc:
            return ValidationReport(
                status=ValidationStatus.FAILED,
                required_for_merge_ready=bool(
                    policy.get("validation", {}).get(
                        "require_local_validation_for_merge_ready", True
                    )
                ),
                steps=[
                    ValidationStepResult(
                        name="validation-scope-resolution",
                        command="git diff --name-only",
                        status="failed",
                        returncode=1,
                        stderr=str(exc),
                    )
                ],
                attempts=1,
                remediation_applied=False,
                fingerprint=fingerprint,
            )

    for step in steps_cfg:
        command = [str(part) for part in step.get("command", [])]
        name = str(step.get("name", "unnamed-step"))
        scope = str(step.get("scope", "repo"))
        if scope in SCOPED_VALIDATION_SCOPES:
            scoped_files = _resolve_step_files(scope, changed_files or [])
            if not scoped_files:
                if progress_callback:
                    progress_callback(
                        f"Skipping step: {name} (no files matched scope {scope})",
                        "INFO",
                    )
                step_results.append(
                    ValidationStepResult(
                        name=name,
                        command=shell_join(command),
                        status="skipped",
                    )
                )
                continue
            command = _build_scoped_command(command, scoped_files)

        if progress_callback:
            progress_callback(f"Running step: {name}", "INFO")

        result = execute_or_dry_run(
            command,
            execute=True,
            cwd=target_cwd,
            commands_log=commands_log,
            timeout_seconds=timeout_seconds,
        )
        status = "passed" if result.returncode == 0 else "failed"

        if progress_callback:
            if status == "passed":
                progress_callback(f"Step '{name}' PASSED", "SUCCESS")
            else:
                progress_callback(f"Step '{name}' FAILED (Exit {result.returncode})", "ERROR")

        step_results.append(
            ValidationStepResult(
                name=name,
                command=shell_join(command),
                status=status,
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
            )
        )
        if result.returncode != 0:
            if name == "docs-frontmatter-fix":
                remediation_applied = True
                continue
            return ValidationReport(
                status=ValidationStatus.FAILED,
                required_for_merge_ready=bool(
                    policy.get("validation", {}).get(
                        "require_local_validation_for_merge_ready", True
                    )
                ),
                steps=step_results,
                attempts=1,
                remediation_applied=remediation_applied,
                fingerprint=fingerprint,
            )
    return ValidationReport(
        status=ValidationStatus.PASSED,
        required_for_merge_ready=bool(
            policy.get("validation", {}).get(
                "require_local_validation_for_merge_ready", True
            )
        ),
        steps=step_results,
        attempts=1,
        remediation_applied=remediation_applied,
        fingerprint=fingerprint,
    )


def validation_report_md(report: ValidationReport) -> str:
    lines = [
        "# Validation Report",
        "",
        f"- status: {report.status}",
        f"- passed: {report.passed}",
        f"- attempts: {report.attempts}",
        f"- remediation_applied: {report.remediation_applied}",
        "",
        "## Steps",
    ]
    for step in report.steps:
        lines.extend(
            [
                f"### {step.name}",
                f"- command: `{step.command}`",
                f"- status: {step.status}",
                f"- exit_code: {step.returncode}",
                "",
            ]
        )
        if step.stdout.strip():
            lines.extend(["```text", step.stdout.strip(), "```", ""])
        if step.stderr.strip():
            lines.extend(["```text", step.stderr.strip(), "```", ""])
    if report.fingerprint is not None:
        lines.extend(
            [
                "## Fingerprint",
                f"- input_fingerprint: `{report.fingerprint.input_fingerprint}`",
                f"- valid_for_sha: `{report.fingerprint.valid_for_sha}`",
                f"- created_from_state: `{report.fingerprint.created_from_state}`",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"
