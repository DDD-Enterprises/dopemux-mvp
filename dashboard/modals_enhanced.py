"""
Enhanced Modals with Real API Integration (Day 6)
Wire modals to live backend services for production-ready monitoring
"""

import asyncio
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from contextlib import asynccontextmanager
import logging

try:
    from textual.screen import ModalScreen
    from textual.containers import Container
    from textual.widgets import Static, DataTable
    from textual.app import ComposeResult
    from rich.text import Text
    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False

from dashboard.service_clients import (
    ADHDEngineClient,
    DockerServiceClient,
    ConPortClient
)
from prometheus_client import PrometheusClient, PrometheusConfig
from sparkline_generator import SparklineGenerator

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Monitor modal performance metrics"""
    
    def __init__(self):
        self.metrics = {}
    
    @asynccontextmanager
    async def track(self, metric_name: str):
        """Track execution time of async operations"""
        start = time.perf_counter()
        
        try:
            yield
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            
            self.metrics.setdefault(metric_name, []).append(duration_ms)
            
            # Log if slow
            if duration_ms > 500:
                logger.warning(
                    f"{metric_name} took {duration_ms:.0f}ms (target: <500ms)"
                )
            
            # Keep only last 100 measurements
            if len(self.metrics[metric_name]) > 100:
                self.metrics[metric_name] = self.metrics[metric_name][-100:]


# Global performance monitor
perf_monitor = PerformanceMonitor()


if TEXTUAL_AVAILABLE:
    class BaseModal(ModalScreen):
        """Base modal with common functionality"""
        
        BINDINGS = [
            ("escape", "dismiss", "Close"),
            ("q", "dismiss", "Close"),
        ]
        
        def action_dismiss(self) -> None:
            """Close modal"""
            self.dismiss()


    class TaskDetailModal(BaseModal):
        """
        Task Detail Modal with Real ADHD Engine Integration
        Shows task suitability assessment and context from live APIs
        """
        
        CSS = """
        #modal-container {
            align: center middle;
            width: 80;
            height: 30;
            background: $panel;
            border: heavy $accent;
        }
        
        #modal-header {
            background: $accent;
            color: $surface;
            text-align: center;
            height: 1;
        }
        
        #modal-content {
            height: 1fr;
            padding: 1;
            overflow-y: auto;
        }
        
        #modal-footer {
            background: $surface;
            color: $text;
            text-align: center;
            height: 1;
        }
        """
        
        def __init__(self, task_id: str = "current"):
            super().__init__()
            self.task_id = task_id
            self.adhd_client = ADHDEngineClient()
            self.conport_client = ConPortClient()
        
        def compose(self) -> ComposeResult:
            with Container(id="modal-container"):
                yield Static(f"Task Details: {self.task_id}", id="modal-header")
                yield Static("⏳ Loading task assessment...", id="modal-content")
                yield Static("[Esc] Close  [r] Refresh  [c] Complete", id="modal-footer")
        
        async def on_mount(self) -> None:
            """Fetch and display real task data"""
            content_widget = self.query_one("#modal-content", Static)
            
            try:
                async with perf_monitor.track('task_modal_load'):
                    # Fetch data in parallel
                    task_data, assessment, context = await asyncio.gather(
                        self._fetch_task_data(),
                        self._fetch_assessment(),
                        self.conport_client.get_current_context()
                    )
                    
                    rendered = self._render_task_content(
                        task_data,
                        assessment,
                        context
                    )
                    content_widget.update(rendered)
            except Exception as e:
                logger.error(f"Failed to load task modal: {e}")
                content_widget.update(
                    f"[yellow]⚠ Unable to load task data[/yellow]\n\n"
                    f"Error: {str(e)}\n\n"
                    f"Please ensure ADHD Engine is running."
                )
        
        async def _fetch_task_data(self) -> Dict[str, Any]:
            """Fetch task metadata"""
            # TODO: Get from task management system when available
            return {
                "id": self.task_id,
                "title": "Implement API integration",
                "description": "Wire dashboard modals to real backend services",
                "complexity": 0.75,
                "estimated_duration_minutes": 120,
                "requires_deep_focus": True,
                "tags": ["backend", "api", "integration"]
            }
        
        async def _fetch_assessment(self) -> Dict[str, Any]:
            """Get real-time ADHD task assessment"""
            task_data = await self._fetch_task_data()
            
            assessment = await self.adhd_client.assess_task(
                user_id="default",
                task_data=task_data
            )
            
            return assessment
        
        def _render_task_content(
            self,
            task: Dict[str, Any],
            assessment: Dict[str, Any],
            context: Dict[str, Any]
        ) -> str:
            """Render complete task detail view"""
            score = assessment.get('suitability_score', 0)
            is_suitable = assessment.get('is_suitable', False)
            
            # Suitability indicator
            if score >= 0.8:
                color, icon, status = "green", "✓", "EXCELLENT"
            elif score >= 0.6:
                color, icon, status = "yellow", "•", "GOOD"
            elif score >= 0.4:
                color, icon, status = "yellow", "!", "MARGINAL"
            else:
                color, icon, status = "red", "✗", "POOR"
            
            output = f"""
[bold cyan]📊 TASK OVERVIEW[/bold cyan]
Title: [bold]{task.get('title', 'Unknown')}[/bold]
ID: {task.get('id')}
Complexity: {task.get('complexity', 0):.0%}
Estimated: {task.get('estimated_duration_minutes', 0)} minutes

[bold cyan]🧠 ADHD SUITABILITY ASSESSMENT[/bold cyan]
Overall: [{color}]{icon} {status} ({score:.0%})[/{color}]

Match Breakdown:"""
            
            # Match breakdown
            breakdown = assessment.get('match_breakdown', {})
            for metric, value in breakdown.items():
                metric_name = metric.replace('_', ' ').title()
                bar = self._render_bar(value, width=15)
                output += f"\n  {metric_name:15} {bar} {value:.0%}"
            
            # Cognitive load prediction
            if load_impact := assessment.get('cognitive_load_impact'):
                predicted = load_impact.get('predicted_load', 0)
                category = load_impact.get('load_category', 'UNKNOWN')
                output += f"\n\nPredicted Load: {predicted:.0%} ([yellow]{category}[/yellow])"
            
            # Accommodations
            if accommodations := assessment.get('accommodations', []):
                output += "\n\n[bold cyan]💡 RECOMMENDED ACCOMMODATIONS[/bold cyan]"
                for acc in accommodations[:5]:  # Limit to 5
                    importance = acc.get('importance', 'MEDIUM')
                    desc = acc.get('description', '')
                    icon_map = {'HIGH': '🔴', 'MEDIUM': '🟡', 'LOW': '⚪'}
                    output += f"\n  {icon_map.get(importance, '•')} {desc}"
            
            # Warnings
            if warnings := assessment.get('warnings', []):
                output += "\n\n[bold yellow]⚠ WARNINGS[/bold yellow]"
                for warning in warnings[:3]:
                    output += f"\n  • {warning}"
            
            # Current context
            output += f"""

[bold cyan]📍 CURRENT CONTEXT[/bold cyan]
Project: {context.get('current_project', 'Unknown')}
Session Duration: {context.get('session_duration_minutes', 0)} minutes
Context Switches: {context.get('context_switches_count', 0)}
"""
            
            # Alternative suggestions
            if alternatives := assessment.get('alternative_suggestions', []):
                output += "\n[bold cyan]🔄 ALTERNATIVE TASKS[/bold cyan]"
                for alt in alternatives[:3]:
                    alt_score = alt.get('suitability_score', 0)
                    output += f"\n  • {alt.get('title')} ({alt_score:.0%})"
                    output += f"\n    [dim]{alt.get('reason')}[/dim]"
            
            return output.strip()
        
        def _render_bar(self, value: float, width: int = 15) -> str:
            """Render a simple progress bar"""
            filled = int(value * width)
            empty = width - filled
            
            if value >= 0.8:
                color = "green"
            elif value >= 0.6:
                color = "yellow"
            else:
                color = "red"
            
            return f"[{color}]{'█' * filled}{'░' * empty}[/{color}]"


    class ServiceLogsModal(BaseModal):
        """
        Service Logs Modal with Real Docker Integration
        Live streaming logs from Docker containers
        """
        
        CSS = """
        #modal-container {
            align: center middle;
            width: 90;
            height: 35;
            background: $panel;
            border: heavy $accent;
        }
        
        #modal-header {
            background: $accent;
            color: $surface;
            text-align: center;
            height: 1;
        }
        
        #log-table {
            height: 1fr;
        }
        
        #modal-footer {
            background: $surface;
            color: $text;
            text-align: center;
            height: 1;
        }
        """
        
        def __init__(self, service_name: str = "adhd_engine"):
            super().__init__()
            self.service_name = service_name
            self.docker_client = DockerServiceClient()
            self.auto_refresh = True
            self.refresh_interval = 2.0  # seconds
        
        def compose(self) -> ComposeResult:
            with Container(id="modal-container"):
                yield Static(
                    f"Service Logs: {self.service_name} (Live)",
                    id="modal-header"
                )
                yield DataTable(id="log-table")
                yield Static(
                    "[Esc] Close  [r] Refresh  [p] Pause",
                    id="modal-footer"
                )
        
        async def on_mount(self) -> None:
            """Initialize log viewer with real data"""
            table = self.query_one("#log-table", DataTable)
            table.add_columns("Time", "Level", "Message")
            table.cursor_type = "row"
            
            # Fetch initial data
            await self._refresh_logs()
            
            # Start auto-refresh
            if self.auto_refresh:
                self.set_interval(
                    self.refresh_interval,
                    self._refresh_logs
                )
        
        async def _refresh_logs(self) -> None:
            """Refresh logs from Docker"""
            try:
                async with perf_monitor.track('service_logs_refresh'):
                    status, logs = await asyncio.gather(
                        self.docker_client.get_service_status(self.service_name),
                        self.docker_client.get_recent_logs(self.service_name, lines=50)
                    )
                    
                    # Update header with status
                    is_healthy = status.get('is_healthy', False)
                    status_text = status.get('status', 'Unknown')
                    status_icon = "🟢" if is_healthy else "🔴"
                    
                    header = self.query_one("#modal-header", Static)
                    header.update(
                        f"{status_icon} {self.service_name} - {status_text}"
                    )
                    
                    # Render logs
                    await self._render_logs(logs)
            except Exception as e:
                logger.error(f"Failed to refresh logs: {e}")
        
        async def _render_logs(self, logs: List[str]) -> None:
            """Render logs in table"""
            table = self.query_one("#log-table", DataTable)
            table.clear()
            
            for log_line in logs[-30:]:  # Last 30 lines only
                if not log_line.strip():
                    continue
                
                # Parse log line (simple heuristic)
                timestamp, level, message = self._parse_log_line(log_line)
                
                # Color-code by level
                level_styles = {
                    "ERROR": "bold red",
                    "WARN": "bold yellow",
                    "WARNING": "bold yellow",
                    "INFO": "blue",
                    "DEBUG": "dim"
                }
                
                style = level_styles.get(level.upper(), "white")
                
                table.add_row(
                    timestamp,
                    Text(level, style=style),
                    message[:80]  # Truncate long messages
                )
        
        def _parse_log_line(self, line: str) -> tuple:
            """Parse log line into components"""
            # Simple parser - can be enhanced
            parts = line.split(maxsplit=2)
            
            if len(parts) >= 3:
                timestamp = parts[0]
                level = parts[1].strip("[]:")
                message = parts[2] if len(parts) > 2 else ""
            elif len(parts) == 2:
                timestamp = parts[0]
                level = "INFO"
                message = parts[1]
            else:
                timestamp = datetime.now().strftime("%H:%M:%S")
                level = "INFO"
                message = line
            
            return timestamp[:8], level, message
        
        BINDINGS = [
            *BaseModal.BINDINGS,
            ("r", "refresh", "Refresh"),
            ("p", "toggle_pause", "Pause"),
        ]
        
        def action_refresh(self) -> None:
            """Force refresh logs"""
            asyncio.create_task(self._refresh_logs())
        
        def action_toggle_pause(self) -> None:
            """Toggle auto-refresh"""
            self.auto_refresh = not self.auto_refresh
            status = "PAUSED" if not self.auto_refresh else "LIVE"
            self.app.notify(f"Auto-refresh: {status}", severity="information")


    class PatternAnalysisModal(BaseModal):
        """
        Pattern Analysis Modal with Prometheus Aggregations
        Detects behavioral patterns from metrics
        """
        
        CSS = """
        #modal-container {
            align: center middle;
            width: 75;
            height: 30;
            background: $panel;
            border: heavy $accent;
        }
        
        #modal-header {
            background: $accent;
            color: $surface;
            text-align: center;
            height: 1;
        }
        
        #modal-content {
            height: 1fr;
            padding: 1;
            overflow-y: auto;
        }
        
        #modal-footer {
            background: $surface;
            color: $text;
            text-align: center;
            height: 1;
        }
        """
        
        def __init__(self):
            super().__init__()
            self.prom_client = PrometheusClient()
        
        def compose(self) -> ComposeResult:
            with Container(id="modal-container"):
                yield Static("Pattern Analysis (7 Days)", id="modal-header")
                yield Static("⏳ Analyzing patterns...", id="modal-content")
                yield Static("[Esc] Close  [r] Refresh", id="modal-footer")
        
        async def on_mount(self) -> None:
            """Analyze patterns from metrics"""
            content_widget = self.query_one("#modal-content", Static)
            
            try:
                async with perf_monitor.track('pattern_modal_load'):
                    patterns = await asyncio.gather(
                        self._detect_context_switch_pattern(),
                        self._detect_energy_pattern(),
                        self._detect_productivity_pattern(),
                        return_exceptions=True
                    )
                    
                    rendered = self._render_patterns(patterns)
                    content_widget.update(rendered)
            except Exception as e:
                logger.error(f"Failed to analyze patterns: {e}")
                content_widget.update(
                    f"[yellow]⚠ Pattern analysis unavailable[/yellow]\n\n"
                    f"Ensure Prometheus is running with historical data."
                )
        
        async def _detect_context_switch_pattern(self) -> Dict[str, Any]:
            """Detect high context-switch periods"""
            try:
                query = 'rate(adhd_context_switches_total[5m])'
                data = await self.prom_client.query_range(query, hours=24)
                
                if not data:
                    return {"pattern": "no_data"}
                
                # Count high-switch periods (> 2 per 5min)
                high_periods = [v for _, v in data if v > 2]
                
                if len(high_periods) > 10:
                    return {
                        "pattern": "frequent_context_switches",
                        "severity": "high",
                        "count": len(high_periods),
                        "recommendation": "Consider longer focus blocks with notifications disabled"
                    }
                elif len(high_periods) > 5:
                    return {
                        "pattern": "moderate_context_switches",
                        "severity": "medium",
                        "count": len(high_periods),
                        "recommendation": "Group similar tasks to reduce switching"
                    }
                
                return {"pattern": "normal_context_switching", "severity": "low"}
            except Exception as e:
                logger.error(f"Context switch pattern detection failed: {e}")
                return {"pattern": "error", "error": str(e)}
        
        async def _detect_energy_pattern(self) -> Dict[str, Any]:
            """Detect energy level patterns by time of day"""
            try:
                query = 'adhd_energy_level'
                data = await self.prom_client.query_range(query, hours=168)  # 7 days
                
                if not data:
                    return {"pattern": "no_data"}
                
                # Group by hour of day
                hour_energy = {}
                for timestamp, value in data:
                    hour = timestamp.hour
                    hour_energy.setdefault(hour, []).append(value)
                
                # Find peak hours
                avg_by_hour = {
                    h: sum(vals) / len(vals)
                    for h, vals in hour_energy.items()
                    if vals
                }
                
                if avg_by_hour:
                    sorted_hours = sorted(
                        avg_by_hour.items(),
                        key=lambda x: x[1],
                        reverse=True
                    )
                    
                    peak_hours = [h for h, _ in sorted_hours[:3]]
                    
                    return {
                        "pattern": "daily_energy_cycle",
                        "peak_hours": peak_hours,
                        "recommendation": f"Schedule deep work during hours: {', '.join(map(str, peak_hours))}"
                    }
                
                return {"pattern": "insufficient_data"}
            except Exception as e:
                logger.error(f"Energy pattern detection failed: {e}")
                return {"pattern": "error", "error": str(e)}
        
        async def _detect_productivity_pattern(self) -> Dict[str, Any]:
            """Detect task completion velocity patterns"""
            try:
                query = 'increase(adhd_tasks_completed_total[24h])'
                data = await self.prom_client.query_range(query, hours=168)
                
                if not data or len(data) < 7:
                    return {"pattern": "insufficient_data"}
                
                # Calculate weekly average
                values = [v for _, v in data]
                avg_daily = sum(values) / len(values)
                
                # Recent vs historical
                recent_avg = sum(values[-7:]) / 7 if len(values) >= 7 else avg_daily
                
                if recent_avg > avg_daily * 1.2:
                    trend = "improving"
                    status = "Productivity increasing! 📈"
                elif recent_avg < avg_daily * 0.8:
                    trend = "declining"
                    status = "Productivity declining - consider rest 📉"
                else:
                    trend = "stable"
                    status = "Productivity stable ➡️"
                
                return {
                    "pattern": "productivity_trend",
                    "trend": trend,
                    "status": status,
                    "avg_tasks_per_day": avg_daily,
                    "recent_avg": recent_avg
                }
            except Exception as e:
                logger.error(f"Productivity pattern detection failed: {e}")
                return {"pattern": "error", "error": str(e)}
        
        def _render_patterns(self, patterns: List[Dict[str, Any]]) -> str:
            """Render pattern analysis results"""
            output = "[bold cyan]📊 DETECTED PATTERNS[/bold cyan]\n\n"
            
            for i, pattern in enumerate(patterns, 1):
                if isinstance(pattern, Exception):
                    output += f"[red]Pattern {i}: Error - {pattern}[/red]\n\n"
                    continue
                
                pattern_type = pattern.get('pattern', 'unknown')
                
                if pattern_type == 'no_data':
                    output += f"[dim]Pattern {i}: No data available[/dim]\n\n"
                elif pattern_type == 'error':
                    output += f"[yellow]Pattern {i}: {pattern.get('error')}[/yellow]\n\n"
                elif pattern_type == 'insufficient_data':
                    output += f"[dim]Pattern {i}: Insufficient data[/dim]\n\n"
                else:
                    # Render actual pattern
                    severity = pattern.get('severity', 'low')
                    severity_icons = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
                    icon = severity_icons.get(severity, '⚪')
                    
                    output += f"{icon} [bold]{pattern_type.replace('_', ' ').title()}[/bold]\n"
                    
                    if rec := pattern.get('recommendation'):
                        output += f"  💡 {rec}\n"
                    
                    if status := pattern.get('status'):
                        output += f"  {status}\n"
                    
                    # Additional details
                    for key, value in pattern.items():
                        if key not in ['pattern', 'severity', 'recommendation', 'status', 'error']:
                            output += f"  {key}: {value}\n"
                    
                    output += "\n"
            
            return output.strip() or "[dim]No patterns detected[/dim]"


    class MetricHistoryModal(BaseModal):
        """
        Metric History Modal with Time-Series Visualization
        Shows sparklines and statistics for selected metric
        """
        
        CSS = """
        #modal-container {
            align: center middle;
            width: 70;
            height: 25;
            background: $panel;
            border: heavy $accent;
        }
        
        #modal-header {
            background: $accent;
            color: $surface;
            text-align: center;
            height: 1;
        }
        
        #modal-content {
            height: 1fr;
            padding: 1;
        }
        
        #modal-footer {
            background: $surface;
            color: $text;
            text-align: center;
            height: 1;
        }
        """
        
        def __init__(self, metric_name: str = "adhd_cognitive_load"):
            super().__init__()
            self.metric_name = metric_name
            self.prom_client = PrometheusClient()
            self.sparkline_gen = SparklineGenerator(
                PrometheusConfig(base_url="http://localhost:9090")
            )
        
        def compose(self) -> ComposeResult:
            with Container(id="modal-container"):
                yield Static(f"Metric: {self.metric_name}", id="modal-header")
                yield Static("⏳ Loading history...", id="modal-content")
                yield Static("[Esc] Close  [r] Refresh", id="modal-footer")
        
        async def on_mount(self) -> None:
            """Load metric history"""
            content_widget = self.query_one("#modal-content", Static)
            
            try:
                async with perf_monitor.track('metric_modal_load'):
                    # Fetch different time ranges
                    data_2h, data_24h, data_7d = await asyncio.gather(
                        self.prom_client.query_range(
                            self.metric_name, hours=2, step="1m"
                        ),
                        self.prom_client.query_range(
                            self.metric_name, hours=24, step="5m"
                        ),
                        self.prom_client.query_range(
                            self.metric_name, hours=168, step="1h"
                        )
                    )
                    
                    rendered = self._render_history(data_2h, data_24h, data_7d)
                    content_widget.update(rendered)
            except Exception as e:
                logger.error(f"Failed to load metric history: {e}")
                content_widget.update(
                    f"[yellow]⚠ Unable to load metric history[/yellow]\n\n"
                    f"Ensure Prometheus is running at localhost:9090"
                )
        
        def _render_history(
            self,
            data_2h: List,
            data_24h: List,
            data_7d: List
        ) -> str:
            """Render metric history with sparklines"""
            output = f"[bold cyan]📈 {self.metric_name}[/bold cyan]\n\n"
            
            # Sparklines
            output += "[bold]Trends:[/bold]\n\n"
            
            if data_2h:
                values_2h = [v for _, v in data_2h]
                sparkline = self.sparkline_gen._render_sparkline(values_2h, width=40)
                current = values_2h[-1] if values_2h else 0
                output += f"Last 2 hours:  {sparkline}  [{current:.2f}]\n"
            
            if data_24h:
                values_24h = [v for _, v in data_24h]
                sparkline = self.sparkline_gen._render_sparkline(values_24h, width=40)
                current = values_24h[-1] if values_24h else 0
                output += f"Last 24 hours: {sparkline}  [{current:.2f}]\n"
            
            if data_7d:
                values_7d = [v for _, v in data_7d]
                sparkline = self.sparkline_gen._render_sparkline(values_7d, width=40)
                current = values_7d[-1] if values_7d else 0
                output += f"Last 7 days:   {sparkline}  [{current:.2f}]\n"
            
            # Statistics
            if data_7d:
                values = [v for _, v in data_7d]
                
                avg = sum(values) / len(values)
                min_val = min(values)
                max_val = max(values)
                
                # Trend
                if len(values) >= 10:
                    recent_avg = sum(values[-10:]) / 10
                    older_avg = sum(values[:10]) / 10
                    trend = "↑ INCREASING" if recent_avg > older_avg else "↓ DECREASING"
                else:
                    trend = "→ STABLE"
                
                output += f"""

[bold]Statistics (7 days):[/bold]
  Average: {avg:.2f}
  Min:     {min_val:.2f}
  Max:     {max_val:.2f}
  Range:   {max_val - min_val:.2f}
  Trend:   {trend}
"""
            
            return output.strip() or "[dim]No data available[/dim]"
