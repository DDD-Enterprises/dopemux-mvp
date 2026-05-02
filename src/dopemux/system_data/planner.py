"""Adaptive cleanup planner with truthful reclaim logic."""

from __future__ import annotations

from pathlib import Path

from .models import PlanItem, PlanResult, ScanResult
from .platform_macos import same_device


def build_plan(
    scan_result: ScanResult,
    *,
    quarantine_dir: Path | None = None,
    targets: tuple[str, ...] = (),
) -> PlanResult:
    target_set = {target for token in targets for target in token.split(",") if target}
    actions: list[PlanItem] = []
    warnings = list(scan_result.warnings)
    critical = scan_result.environment.disk_pressure == "critical"
    if critical:
        warnings.append("critical disk mode: same-volume quarantine changes geography, not capacity")

    order = 0
    for finding in scan_result.findings:
        if target_set and finding.finding_id not in target_set and finding.category not in target_set:
            continue
        order += 1
        expected = finding.reclaim_estimate_bytes
        action_type = finding.recommended_action
        blocked_reason = None
        rollback_mode = "none"
        preconditions = tuple(f"{app} should be closed" for app in finding.requires_app_quit)

        if finding.risk_level == "blocked":
            action_type = "blocked"
            expected = 0
            blocked_reason = finding.rationale
        elif action_type == "docker_prune" and not scan_result.environment.docker_cli_installed:
            action_type = "blocked"
            expected = 0
            blocked_reason = "Docker CLI is missing; Dopemux will not raw-delete Docker storage."
            warnings.append("Docker CLI missing: Docker cleanup is report-only")
        elif action_type == "docker_prune" and not scan_result.environment.docker_daemon_reachable:
            action_type = "blocked"
            expected = 0
            blocked_reason = "Docker is installed but the daemon is asleep or broken."
            warnings.append("Docker daemon unreachable: Docker cleanup is report-only")
        elif finding.risk_level == "review_first":
            action_type = "review_required"
            expected = 0
            rollback_mode = "quarantine_manifest"
        elif action_type == "clear_safe_path" and quarantine_dir:
            source = Path(finding.path)
            same = same_device(source, quarantine_dir)
            if same:
                expected = 0
                rollback_mode = "same_volume_quarantine"
                warnings.append(f"same-volume quarantine for {finding.path}: expected reclaim is 0")
            else:
                rollback_mode = "external_quarantine"
                expected = finding.size_bytes
            if critical and same:
                action_type = "clear_safe_path"
                expected = finding.size_bytes
                rollback_mode = "delete_in_place"
            else:
                action_type = "quarantine"

        actions.append(
            PlanItem(
                action_id=f"A{order:04d}",
                target_finding_id=finding.finding_id,
                path=finding.path,
                action_type=action_type,
                dry_run_supported=True,
                requires_confirmation=finding.risk_level != "safe_clear",
                destructive_level="none" if action_type in {"blocked", "review_required"} else "low",
                expected_reclaim_bytes=expected,
                preconditions=preconditions,
                rollback_mode=rollback_mode,
                blocked_reason=blocked_reason,
                execution_order=order,
                rationale=finding.rationale,
            )
        )

    return PlanResult(
        environment=scan_result.environment,
        findings=scan_result.findings,
        actions=tuple(actions),
        warnings=tuple(sorted(set(warnings))),
    )
