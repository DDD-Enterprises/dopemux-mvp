"""Human and JSON reporting helpers for system-data commands."""

from __future__ import annotations

from rich.table import Table

from dopemux.console import console

from .models import PlanResult, ScanResult, ToolReport, bytes_to_human, to_plain


def tool_report_data(report: ToolReport) -> dict:
    return to_plain(report)


def render_tool_report(report: ToolReport) -> None:
    table = Table(title="System Data Toolchain")
    table.add_column("Tool")
    table.add_column("Status")
    table.add_column("Version")
    for status in report.statuses:
        table.add_row(
            status.name,
            "ok" if status.available else "missing",
            status.version or status.error or "",
        )
    console.print(table)
    if not report.ok:
        console.print(f"[warning]Install required tools: {report.install_command}[/warning]")


def render_scan(scan_result: ScanResult) -> None:
    env = scan_result.environment
    console.print(
        f"[bold]System Data Scan[/bold] pressure={env.disk_pressure} "
        f"free={bytes_to_human(env.free_bytes)} full_disk_access={env.full_disk_access}"
    )
    table = Table(title="Ranked Findings")
    table.add_column("Finding")
    table.add_column("Risk")
    table.add_column("Size")
    table.add_column("Action")
    table.add_column("Path")
    for finding in scan_result.findings[:30]:
        table.add_row(
            finding.finding_id,
            finding.risk_level,
            bytes_to_human(finding.size_bytes),
            finding.recommended_action,
            finding.path,
        )
    console.print(table)
    for warning in scan_result.warnings:
        console.print(f"[warning]{warning}[/warning]")


def render_plan(plan_result: PlanResult) -> None:
    table = Table(title="Cleanup Plan")
    table.add_column("Action")
    table.add_column("Type")
    table.add_column("Expected Reclaim")
    table.add_column("Rollback")
    table.add_column("Path")
    for action in plan_result.actions:
        table.add_row(
            action.action_id,
            action.action_type,
            bytes_to_human(action.expected_reclaim_bytes),
            action.rollback_mode,
            action.path,
        )
    console.print(table)
    for warning in plan_result.warnings:
        console.print(f"[warning]{warning}[/warning]")


def scan_data(scan_result: ScanResult) -> dict:
    return to_plain(scan_result)


def plan_data(plan_result: PlanResult) -> dict:
    return to_plain(plan_result)
