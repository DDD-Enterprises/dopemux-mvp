"""Textual TUI for the macOS system-data scrubber."""

from __future__ import annotations

import subprocess
from typing import Any

from .models import PlanResult, ScanResult, bytes_to_human


def run_tui(scan_result: ScanResult, plan_result: PlanResult) -> None:
    try:
        from textual.app import App, ComposeResult
        from textual.containers import Horizontal, Vertical
        from textual.widgets import (
            DataTable,
            Footer,
            Header,
            Static,
            TabbedContent,
            TabPane,
        )
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise RuntimeError("Textual is required for system-data tui") from exc

    class SystemDataApp(App):
        TITLE = "Dopemux System Data"
        CSS_PATH = "../ui/dopemux.tcss"
        BINDINGS = [
            ("q", "quit", "Quit"),
            ("b", "btop", "btop"),
        ]

        def compose(self) -> ComposeResult:
            yield Header()
            with TabbedContent(initial="overview"):
                with TabPane("Overview", id="overview"):
                    yield Static(self._overview(), id="system-data-overview")
                with TabPane("Findings", id="findings"):
                    yield DataTable(id="findings-table")
                with TabPane("Plan", id="plan"):
                    yield DataTable(id="plan-table")
                with TabPane("Processes", id="processes"):
                    yield DataTable(id="processes-table")
                with TabPane("Monitor", id="monitor"):
                    yield Static(
                        "Press b to launch btop. Return here when the monitor exits.",
                        id="monitor-panel",
                    )
                with TabPane("Execute", id="execute"):
                    yield Static(self._execute(), id="execute-panel")
                with TabPane("Restore", id="restore"):
                    yield Static(self._restore(), id="restore-panel")
            yield Footer()

        def on_mount(self) -> None:
            findings = self.query_one("#findings-table", DataTable)
            findings.add_columns("Risk", "Size", "Action", "Path")
            for finding in scan_result.findings:
                findings.add_row(
                    finding.risk_level,
                    bytes_to_human(finding.size_bytes),
                    finding.recommended_action,
                    finding.path,
                )
            plan = self.query_one("#plan-table", DataTable)
            plan.add_columns("Action", "Type", "Reclaim", "Rollback", "Path")
            for action in plan_result.actions:
                plan.add_row(
                    action.action_id,
                    action.action_type,
                    bytes_to_human(action.expected_reclaim_bytes),
                    action.rollback_mode,
                    action.path,
                )
            processes = self.query_one("#processes-table", DataTable)
            processes.add_columns("PID", "CPU", "Memory", "Command")
            for row in scan_result.processes[:100]:
                processes.add_row(
                    self._cell(row, "PID", "pid"),
                    self._cell(row, "CPU", "cpu"),
                    self._cell(row, "Memory", "memory", "mem"),
                    self._cell(row, "Command", "command", "Command"),
                )
            if not scan_result.processes:
                processes.add_row("-", "-", "-", "No matching process rows from procs.")

        def _overview(self) -> str:
            env = scan_result.environment
            lines = [
                "Dopemux system-data scrubber",
                f"Disk pressure: {env.disk_pressure}",
                f"Free: {bytes_to_human(env.free_bytes)} / {bytes_to_human(env.total_bytes)}",
                f"Full Disk Access: {env.full_disk_access}",
                f"Findings: {len(scan_result.findings)}",
                f"Actions: {len(plan_result.actions)}",
                "Same-volume quarantine never counts as reclaimed capacity.",
            ]
            return "\n".join(lines)

        def _cell(self, row: dict[str, Any], *keys: str) -> str:
            for key in keys:
                value = row.get(key)
                if value not in (None, ""):
                    return str(value)
            return "-"

        def _execute(self) -> str:
            executable = [
                action
                for action in plan_result.actions
                if action.action_type not in {"blocked", "review_required"}
            ]
            review = [
                action
                for action in plan_result.actions
                if action.action_type in {"blocked", "review_required"}
            ]
            return "\n".join(
                [
                    "Execution is dry-run first.",
                    f"Executable actions: {len(executable)}",
                    f"Review/blocked actions: {len(review)}",
                    "Real mutation requires the CLI path: dopemux system-data clean --execute --yes.",
                    "Same-volume quarantine still means zero reclaimed capacity.",
                ]
            )

        def _restore(self) -> str:
            return "Restore uses quarantine manifests. Real restore remains explicit and review-first."

        def action_btop(self) -> None:
            self.exit()
            subprocess.run(["btop"], check=False)

    SystemDataApp().run()
