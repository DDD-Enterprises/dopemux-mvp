"""Enhanced ADHD monitor pane with alerts and findings."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, List
from datetime import datetime

from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.console import Group
from textual.widgets import Static


@dataclass(slots=True)
class ADHDMonitorPayload:
    energy: Any
    session_minutes: int
    health: Optional[Any]
    focus: Optional[Any]
    switches_15m: int
    untracked_files: int
    untracked_age: int
    untracked_confidence: float
    files: List[str]
    # Phase 8 additions
    hyperfocus_warning: bool = False
    overwhelm_alert: bool = False
    recent_findings: List[Dict] = None
    
    def __post_init__(self):
        if self.recent_findings is None:
            self.recent_findings = []


class ADHDMonitorPane(Static):
    """Displays ADHD engine metrics + Serena untracked work + Phase 8 alerts."""

    DEFAULT_CSS = """
    ADHDMonitorPane {
        padding: 1 1;
        height: 100%;
        overflow-y: auto;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._last_payload: Optional[ADHDMonitorPayload] = None

    def _format_session_time(self, minutes: int) -> Text:
        """Format session time with color coding."""
        if minutes >= 120:
            return Text(f"🔥 {minutes}m HYPERFOCUS!", style="bold red blink")
        elif minutes >= 90:
            return Text(f"⚠️ {minutes}m (consider break)", style="bold yellow")
        elif minutes >= 60:
            return Text(f"⏱️ {minutes}m", style="cyan")
        else:
            return Text(f"{minutes}m", style="dim cyan")

    def _build_alerts_panel(self, payload: ADHDMonitorPayload) -> Optional[Panel]:
        """Build alerts panel for hyperfocus/overwhelm."""
        alerts = []
        
        if payload.hyperfocus_warning or payload.session_minutes >= 90:
            time_text = f"{payload.session_minutes} minutes of focused work"
            alerts.append(Text(f"🔥 HYPERFOCUS: {time_text}", style="bold magenta"))
            alerts.append(Text("   Take a 10-minute break!", style="yellow"))
        
        if payload.overwhelm_alert:
            alerts.append(Text("😰 OVERWHELM DETECTED", style="bold red"))
            alerts.append(Text("   1. Save your context", style="dim"))
            alerts.append(Text("   2. Step away for 15 min", style="dim"))
            alerts.append(Text("   3. Return to easiest task", style="dim"))
        
        if not alerts:
            return None
        
        alert_content = Table.grid()
        for alert in alerts:
            alert_content.add_row(alert)
        
        return Panel(
            alert_content,
            title="[bold red]⚠️ ALERTS[/bold red]",
            border_style="red",
        )

    def _build_findings_panel(self, findings: List[Dict]) -> Optional[Panel]:
        """Build recent findings panel."""
        if not findings:
            return None
        
        table = Table.grid(expand=True)
        table.add_column(justify="left", width=3)
        table.add_column(justify="left")
        
        severity_icons = {
            "low": "💡",
            "medium": "💛",
            "high": "🧡",
            "critical": "❤️‍🔥",
        }
        
        for finding in findings[-5:]:  # Last 5 findings
            icon = severity_icons.get(finding.get("severity", "medium"), "•")
            msg = finding.get("message", "")[:40]
            table.add_row(icon, Text(msg, style="dim"))
        
        return Panel(
            table,
            title="[bold cyan]📋 Recent Findings[/bold cyan]",
            border_style="cyan",
        )

    def compose_renderable(self, payload: ADHDMonitorPayload):
        # Main metrics
        metrics = Table.grid(expand=True)
        metrics.add_column(justify="left")
        metrics.add_column(justify="right")
        
        # Energy with icon
        energy_icons = {"high": "⚡", "medium": "🔋", "low": "🪫"}
        energy_icon = energy_icons.get(str(payload.energy).lower(), "❓")
        energy_style = "bold green" if payload.energy == "high" else ("yellow" if payload.energy == "medium" else "red")
        metrics.add_row("Energy", Text(f"{energy_icon} {payload.energy}", style=energy_style))
        
        # Session time
        metrics.add_row("Session", self._format_session_time(payload.session_minutes))
        
        # Focus with icon
        focus_icons = {"hyperfocus": "🔥", "focused": "🎯", "distracted": "🌊", "fatigued": "😴"}
        focus_icon = focus_icons.get(str(payload.focus).lower(), "🧠")
        metrics.add_row("Focus", Text(f"{focus_icon} {payload.focus or '—'}", style="bold cyan"))
        
        # Context switches
        switch_style = "red" if payload.switches_15m >= 5 else ("yellow" if payload.switches_15m >= 3 else "green")
        metrics.add_row("Context Switches (15m)", Text(str(payload.switches_15m), style=switch_style))

        # Untracked work
        untracked = Table.grid(expand=True)
        untracked.add_column(justify="left", ratio=1)
        untracked.add_column(justify="right", ratio=1)
        untracked.add_row("Files", Text(str(payload.untracked_files), style="yellow"))
        untracked.add_row("Age", Text(f"{payload.untracked_age}d", style="yellow"))
        untracked.add_row("Confidence", Text(f"{payload.untracked_confidence:.2f}", style="yellow"))

        # Files list
        files_table = Table.grid(expand=True)
        files_table.add_column(justify="left")
        if payload.files:
            for f in payload.files[:10]:  # Limit to 10
                files_table.add_row(Text(f, style="dim"))
        else:
            files_table.add_row(Text("No untracked files", style="dim green"))

        # Build layout
        components = []
        
        # Alerts first (if any)
        alerts_panel = self._build_alerts_panel(payload)
        if alerts_panel:
            components.append(alerts_panel)
        
        # Main grid
        main_grid = Table.grid(expand=True, padding=(0, 1))
        main_grid.add_column(ratio=1)
        main_grid.add_column(ratio=1)
        main_grid.add_row(metrics, Panel(untracked, title="Untracked Work", border_style="yellow"))
        components.append(main_grid)
        
        # Findings panel
        findings_panel = self._build_findings_panel(payload.recent_findings)
        if findings_panel:
            components.append(findings_panel)
        
        # Files
        components.append(Panel(files_table, title="Untracked Files", border_style="cyan"))

        return Panel(
            Group(*components),
            title="[bold #7dfbf6]🧠 ADHD Monitor[/bold #7dfbf6]",
            border_style="bright_magenta",
        )

    def update_from_sources(self, data: Dict[str, Any]) -> None:
        adhd = data.get("adhd") or {}
        activity = data.get("activity") or {}
        serena = data.get("serena") or {}
        findings = data.get("findings") or []
        
        session_min = int(adhd.get("session_minutes") or 0)
        
        payload = ADHDMonitorPayload(
            energy=adhd.get("energy", "N/A"),
            session_minutes=session_min,
            health=adhd.get("health"),
            focus=adhd.get("focus"),
            switches_15m=int(activity.get("switches_15m") or 0),
            untracked_files=int(serena.get("file_count") or 0),
            untracked_age=int(serena.get("age_days") or 0),
            untracked_confidence=float(serena.get("confidence") or 0.0),
            files=list(serena.get("files") or []),
            hyperfocus_warning=session_min >= 90,
            overwhelm_alert=adhd.get("attention") == "overwhelmed",
            recent_findings=findings,
        )
        self._last_payload = payload
        self.update(self.compose_renderable(payload))

