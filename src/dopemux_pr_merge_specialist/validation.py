from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from .runtime import execute_or_dry_run, fingerprint_payload, shell_join
from .schema import (
    Fingerprint,
    ValidationReport,
    ValidationStatus,
    ValidationStepResult,
)


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
    for step in steps_cfg:
        command = [str(part) for part in step.get("command", [])]
        name = str(step.get("name", "unnamed-step"))
        
        if progress_callback:
            progress_callback(f"Running step: {name}", "INFO")
            
        result = execute_or_dry_run(
            command,
            execute=True,
            cwd=target_cwd,
            commands_log=commands_log,
            timeout_seconds=int(
                policy.get("timeouts", {}).get("subprocess_seconds", 600) or 600
            ),
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
