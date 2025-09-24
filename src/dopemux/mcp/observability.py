"""
Observability: Metrics collection and health monitoring for MetaMCP

The Observability module provides comprehensive monitoring, metrics collection,
and health assessment for the MetaMCP role-aware tool brokering system. It
includes ADHD-friendly alerting and performance tracking designed to provide
actionable insights without overwhelming users.

Key Features:
- Comprehensive metrics collection (performance, usage, errors)
- Health monitoring with actionable alerts
- ADHD-optimized notification system
- Historical trend analysis
- Prometheus metrics export
- Custom dashboard data preparation

Integration Points:
- MetaMCP Broker: Core metrics provider
- Server Manager: Connection health monitoring
- Token Manager: Budget and usage metrics
- Role Manager: Transition and escalation metrics
"""

import logging
import statistics
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics collected"""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class AlertSeverity(Enum):
    """Alert severity levels"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Metric:
    """Individual metric data point"""

    name: str
    type: MetricType
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    help_text: str = ""


@dataclass
class Alert:
    """System alert"""

    id: str
    severity: AlertSeverity
    title: str
    description: str
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolution_time: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def age_seconds(self) -> float:
        return (datetime.now() - self.timestamp).total_seconds()

    @property
    def is_adhd_gentle(self) -> bool:
        """Check if this alert should use gentle ADHD notifications"""
        return self.severity in [AlertSeverity.INFO, AlertSeverity.WARNING]


class MetricsCollector:
    """
    Comprehensive metrics collection for MetaMCP system.

    The MetricsCollector provides centralized metrics gathering including
    performance, usage, errors, and system health. It's designed to provide
    actionable insights while respecting ADHD attention patterns.
    """

    def __init__(self, retention_hours: int = 24):
        self.retention_hours = retention_hours
        self.start_time = datetime.now()

        # Metrics storage
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, List[float]] = defaultdict(list)

        # Recent activity tracking (last hour)
        self.recent_activity = deque(maxlen=3600)  # One per second for an hour

        # ADHD-specific metrics
        self.context_switches = 0
        self.focus_sessions = []
        self.break_reminders_sent = 0

        # Performance tracking
        self.response_times = defaultdict(list)
        self.error_counts = defaultdict(int)

        logger.info("MetricsCollector initialized")

    def record_startup(self) -> None:
        """Record system startup metrics"""
        self.record_counter("metamcp_startups_total", 1)
        self.record_gauge("metamcp_start_timestamp", time.time())
        logger.info("Recorded startup metrics")

    def record_tool_call(
        self,
        role: str,
        tool_name: str,
        method: str,
        execution_time_ms: int,
        tokens_used: int,
        optimizations_applied: int,
    ) -> None:
        """Record tool call metrics"""
        labels = {"role": role, "tool": tool_name, "method": method}

        # Count and timing
        self.record_counter("metamcp_tool_calls_total", 1, labels)
        self.record_histogram(
            "metamcp_tool_call_duration_ms", execution_time_ms, labels
        )

        # Token usage
        self.record_counter("metamcp_tokens_used_total", tokens_used, labels)
        self.record_histogram("metamcp_tokens_per_call", tokens_used, labels)

        # Optimizations
        if optimizations_applied > 0:
            self.record_counter(
                "metamcp_optimizations_applied_total", optimizations_applied, labels
            )

        # Track recent activity
        self.recent_activity.append(
            {
                "timestamp": datetime.now(),
                "type": "tool_call",
                "role": role,
                "tool": tool_name,
                "execution_time_ms": execution_time_ms,
                "tokens_used": tokens_used,
            }
        )

    def record_tool_call_failure(self, tool_name: str, method: str, error: str) -> None:
        """Record tool call failure"""
        labels = {
            "tool": tool_name,
            "method": method,
            "error_type": self._classify_error(error),
        }

        self.record_counter("metamcp_tool_call_errors_total", 1, labels)
        self.error_counts[f"{tool_name}.{method}"] += 1

    def record_role_switch(
        self, from_role: Optional[str], to_role: str, switch_time_ms: int
    ) -> None:
        """Record role switch metrics"""
        labels = {"from_role": from_role or "none", "to_role": to_role}

        self.record_counter("metamcp_role_switches_total", 1, labels)
        self.record_histogram("metamcp_role_switch_duration_ms", switch_time_ms, labels)

        # ADHD-specific tracking
        self.context_switches += 1

        self.recent_activity.append(
            {
                "timestamp": datetime.now(),
                "type": "role_switch",
                "from_role": from_role,
                "to_role": to_role,
                "switch_time_ms": switch_time_ms,
            }
        )

    def record_role_switch_failure(
        self, session_id: str, to_role: str, error: str
    ) -> None:
        """Record role switch failure"""
        labels = {"to_role": to_role, "error_type": self._classify_error(error)}

        self.record_counter("metamcp_role_switch_errors_total", 1, labels)

    def record_budget_warning(
        self, session_id: str, role: str, usage_percentage: float
    ) -> None:
        """Record budget warning event"""
        labels = {
            "role": role,
            "severity": "warning" if usage_percentage < 90 else "critical",
        }

        self.record_counter("metamcp_budget_warnings_total", 1, labels)
        self.record_gauge(
            "metamcp_budget_usage_percentage", usage_percentage, {"session": session_id}
        )

    def record_server_health(
        self, server_name: str, status: str, response_time_ms: float
    ) -> None:
        """Record server health metrics"""
        labels = {"server": server_name, "status": status}

        self.record_gauge(
            "metamcp_server_health", 1 if status == "ready" else 0, labels
        )
        self.record_histogram(
            "metamcp_server_response_time_ms", response_time_ms, labels
        )

    def record_adhd_metric(
        self, metric_name: str, value: float, context: Dict[str, str] = None
    ) -> None:
        """Record ADHD-specific metrics"""
        labels = context or {}
        labels["adhd_metric"] = "true"

        if metric_name == "focus_session_start":
            self.focus_sessions.append(
                {"start_time": datetime.now(), "context": context}
            )

        elif metric_name == "focus_session_end":
            if self.focus_sessions:
                session = self.focus_sessions[-1]
                session["end_time"] = datetime.now()
                session["duration_minutes"] = (
                    session["end_time"] - session["start_time"]
                ).total_seconds() / 60

        elif metric_name == "break_reminder_sent":
            self.break_reminders_sent += 1

        self.record_gauge(f"metamcp_adhd_{metric_name}", value, labels)

    def record_counter(
        self, name: str, value: float, labels: Dict[str, str] = None
    ) -> None:
        """Record a counter metric"""
        metric = Metric(
            name=name, type=MetricType.COUNTER, value=value, labels=labels or {}
        )

        self.metrics[name].append(metric)
        self.counters[name] += value

    def record_gauge(
        self, name: str, value: float, labels: Dict[str, str] = None
    ) -> None:
        """Record a gauge metric"""
        metric = Metric(
            name=name, type=MetricType.GAUGE, value=value, labels=labels or {}
        )

        self.metrics[name].append(metric)
        self.gauges[name] = value

    def record_histogram(
        self, name: str, value: float, labels: Dict[str, str] = None
    ) -> None:
        """Record a histogram metric"""
        metric = Metric(
            name=name, type=MetricType.HISTOGRAM, value=value, labels=labels or {}
        )

        self.metrics[name].append(metric)
        self.histograms[name].append(value)

        # Keep only recent values
        if len(self.histograms[name]) > 1000:
            self.histograms[name] = self.histograms[name][-1000:]

    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary"""
        uptime_seconds = (datetime.now() - self.start_time).total_seconds()

        # Recent activity analysis
        recent_tool_calls = [
            activity
            for activity in self.recent_activity
            if activity["type"] == "tool_call"
            and (datetime.now() - activity["timestamp"]).total_seconds() < 3600
        ]

        recent_role_switches = [
            activity
            for activity in self.recent_activity
            if activity["type"] == "role_switch"
            and (datetime.now() - activity["timestamp"]).total_seconds() < 3600
        ]

        # Performance metrics
        response_time_summary = {}
        for metric_name, values in self.histograms.items():
            if "duration_ms" in metric_name or "response_time" in metric_name:
                if values:
                    response_time_summary[metric_name] = {
                        "count": len(values),
                        "avg": statistics.mean(values),
                        "median": statistics.median(values),
                        "p95": self._percentile(values, 95),
                        "min": min(values),
                        "max": max(values),
                    }

        # ADHD metrics
        active_focus_sessions = len(
            [s for s in self.focus_sessions if "end_time" not in s]
        )
        completed_focus_sessions = [s for s in self.focus_sessions if "end_time" in s]
        avg_focus_duration = (
            statistics.mean([s["duration_minutes"] for s in completed_focus_sessions])
            if completed_focus_sessions
            else 0
        )

        return {
            "system": {
                "uptime_seconds": uptime_seconds,
                "uptime_formatted": self._format_duration(uptime_seconds),
                "start_time": self.start_time.isoformat(),
            },
            "activity": {
                "total_tool_calls": self.counters.get("metamcp_tool_calls_total", 0),
                "total_role_switches": self.counters.get(
                    "metamcp_role_switches_total", 0
                ),
                "recent_tool_calls_1h": len(recent_tool_calls),
                "recent_role_switches_1h": len(recent_role_switches),
                "context_switches_total": self.context_switches,
            },
            "performance": response_time_summary,
            "errors": {
                "tool_call_errors": self.counters.get(
                    "metamcp_tool_call_errors_total", 0
                ),
                "role_switch_errors": self.counters.get(
                    "metamcp_role_switch_errors_total", 0
                ),
                "error_rate_1h": self._calculate_error_rate(),
            },
            "adhd_metrics": {
                "active_focus_sessions": active_focus_sessions,
                "completed_focus_sessions": len(completed_focus_sessions),
                "avg_focus_duration_minutes": round(avg_focus_duration, 1),
                "break_reminders_sent": self.break_reminders_sent,
            },
            "tokens": {
                "total_tokens_used": self.counters.get("metamcp_tokens_used_total", 0),
                "optimizations_applied": self.counters.get(
                    "metamcp_optimizations_applied_total", 0
                ),
            },
        }

    def get_prometheus_metrics(self) -> str:
        """Export metrics in Prometheus format"""
        lines = []

        # Add help and type information
        metric_info = {
            "metamcp_tool_calls_total": ("counter", "Total number of tool calls"),
            "metamcp_tool_call_duration_ms": (
                "histogram",
                "Tool call execution time in milliseconds",
            ),
            "metamcp_tokens_used_total": ("counter", "Total tokens consumed"),
            "metamcp_role_switches_total": ("counter", "Total role switches"),
            "metamcp_server_health": (
                "gauge",
                "Server health status (1=healthy, 0=unhealthy)",
            ),
        }

        for metric_name, (metric_type, help_text) in metric_info.items():
            lines.append(f"# HELP {metric_name} {help_text}")
            lines.append(f"# TYPE {metric_name} {metric_type}")

        # Export current metric values
        for name, value in self.counters.items():
            lines.append(f"{name} {value}")

        for name, value in self.gauges.items():
            lines.append(f"{name} {value}")

        # Export histogram summaries
        for name, values in self.histograms.items():
            if values:
                lines.append(f"{name}_count {len(values)}")
                lines.append(f"{name}_sum {sum(values)}")

        return "\n".join(lines)

    def _classify_error(self, error: str) -> str:
        """Classify error type for metrics labeling"""
        error_lower = error.lower()

        if "timeout" in error_lower:
            return "timeout"
        elif "connection" in error_lower:
            return "connection"
        elif "permission" in error_lower or "auth" in error_lower:
            return "permission"
        elif "budget" in error_lower or "token" in error_lower:
            return "budget"
        else:
            return "other"

    def _calculate_error_rate(self) -> float:
        """Calculate error rate for the last hour"""
        now = datetime.now()
        cutoff = now - timedelta(hours=1)

        error_activities = [
            activity
            for activity in self.recent_activity
            if activity["timestamp"] >= cutoff and "error" in activity.get("type", "")
        ]

        total_activities = [
            activity
            for activity in self.recent_activity
            if activity["timestamp"] >= cutoff
        ]

        if not total_activities:
            return 0.0

        return len(error_activities) / len(total_activities)

    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile value"""
        if not values:
            return 0.0

        sorted_values = sorted(values)
        index = int((percentile / 100.0) * len(sorted_values))
        return sorted_values[min(index, len(sorted_values) - 1)]

    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format"""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds // 60)}m {int(seconds % 60)}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"


class HealthMonitor:
    """
    System health monitoring and alerting for MetaMCP.

    The HealthMonitor provides comprehensive health assessment including
    ADHD-friendly alerting that provides actionable information without
    causing anxiety or overwhelming users.
    """

    def __init__(self):
        self.alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []

        # Health thresholds
        self.thresholds = {
            "response_time_warning_ms": 1000,
            "response_time_critical_ms": 5000,
            "error_rate_warning": 0.05,  # 5%
            "error_rate_critical": 0.15,  # 15%
            "memory_warning_mb": 1024,
            "memory_critical_mb": 2048,
            "budget_warning_pct": 80,
            "budget_critical_pct": 95,
        }

        # ADHD-specific alert settings
        self.adhd_settings = {
            "gentle_notifications": True,
            "max_concurrent_alerts": 3,
            "alert_cooldown_seconds": 300,  # 5 minutes
            "use_progressive_disclosure": True,
        }

        logger.info("HealthMonitor initialized")

    async def get_health_status(
        self,
        broker_status: str,
        active_sessions: int,
        server_manager: Any,
        metrics: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Get comprehensive system health status"""

        # Collect health data
        health_data = {
            "overall_status": "healthy",
            "broker_status": broker_status,
            "active_sessions": active_sessions,
            "timestamp": datetime.now().isoformat(),
            "components": {},
            "alerts": {},
            "recommendations": [],
        }

        # Check broker health
        if broker_status != "ready":
            await self._raise_alert(
                "broker_status",
                AlertSeverity.ERROR,
                "Broker Not Ready",
                f"MetaMCP broker status is {broker_status}",
                {"component": "broker", "status": broker_status},
            )
            health_data["overall_status"] = "degraded"

        # Check server health
        if server_manager:
            server_health = await server_manager.get_overall_health()
            health_data["components"]["servers"] = {
                "status": (
                    "healthy"
                    if server_health > 0.8
                    else "degraded" if server_health > 0.5 else "failed"
                ),
                "health_score": server_health,
            }

            if server_health < 0.5:
                await self._raise_alert(
                    "server_health",
                    AlertSeverity.CRITICAL,
                    "Multiple Server Failures",
                    f"Server health score is {server_health:.1%}",
                    {"component": "servers", "health_score": server_health},
                )
                health_data["overall_status"] = "failed"
            elif server_health < 0.8:
                await self._raise_alert(
                    "server_health",
                    AlertSeverity.WARNING,
                    "Server Health Degraded",
                    f"Server health score is {server_health:.1%}",
                    {"component": "servers", "health_score": server_health},
                )
                if health_data["overall_status"] == "healthy":
                    health_data["overall_status"] = "degraded"

        # Check performance metrics
        performance = metrics.get("performance", {})
        for metric_name, stats in performance.items():
            if "avg" in stats:
                avg_time = stats["avg"]
                if avg_time > self.thresholds["response_time_critical_ms"]:
                    await self._raise_alert(
                        f"performance_{metric_name}",
                        AlertSeverity.CRITICAL,
                        "Slow Performance",
                        f"{metric_name} averaging {avg_time:.0f}ms",
                        {"metric": metric_name, "avg_time": avg_time},
                    )
                elif avg_time > self.thresholds["response_time_warning_ms"]:
                    await self._raise_alert(
                        f"performance_{metric_name}",
                        AlertSeverity.WARNING,
                        "Performance Degraded",
                        f"{metric_name} averaging {avg_time:.0f}ms",
                        {"metric": metric_name, "avg_time": avg_time},
                    )

        # Check error rates
        error_rate = metrics.get("errors", {}).get("error_rate_1h", 0)
        if error_rate > self.thresholds["error_rate_critical"]:
            await self._raise_alert(
                "error_rate",
                AlertSeverity.CRITICAL,
                "High Error Rate",
                f"Error rate is {error_rate:.1%} in the last hour",
                {"error_rate": error_rate},
            )
        elif error_rate > self.thresholds["error_rate_warning"]:
            await self._raise_alert(
                "error_rate",
                AlertSeverity.WARNING,
                "Elevated Error Rate",
                f"Error rate is {error_rate:.1%} in the last hour",
                {"error_rate": error_rate},
            )

        # ADHD-specific health checks
        adhd_metrics = metrics.get("adhd_metrics", {})
        avg_focus_duration = adhd_metrics.get("avg_focus_duration_minutes", 0)

        if avg_focus_duration > 0 and avg_focus_duration < 15:
            health_data["recommendations"].append(
                {
                    "type": "adhd_optimization",
                    "priority": "medium",
                    "message": f"Average focus duration is {avg_focus_duration:.1f} minutes. Consider enabling break reminders.",
                    "action": "enable_break_reminders",
                }
            )

        # Check for excessive context switching
        metrics.get("activity", {}).get("context_switches_total", 0)
        recent_switches = metrics.get("activity", {}).get("recent_role_switches_1h", 0)

        if recent_switches > 10:  # More than 10 role switches in an hour
            health_data["recommendations"].append(
                {
                    "type": "adhd_optimization",
                    "priority": "medium",
                    "message": f"{recent_switches} role switches in the last hour. Consider staying in one role longer.",
                    "action": "suggest_role_consistency",
                }
            )

        # Compile active alerts
        active_alerts = {
            alert_id: {
                "severity": alert.severity.value,
                "title": alert.title,
                "description": alert.description,
                "age_seconds": alert.age_seconds,
                "is_gentle": alert.is_adhd_gentle,
            }
            for alert_id, alert in self.alerts.items()
            if not alert.resolved
        }

        # Apply ADHD-friendly alert filtering
        if self.adhd_settings["gentle_notifications"]:
            active_alerts = self._filter_alerts_for_adhd(active_alerts)

        health_data["alerts"] = {
            "active": active_alerts,
            "total_active": len(active_alerts),
            "resolved_today": len(
                [
                    alert
                    for alert in self.alert_history
                    if alert.resolved
                    and alert.resolution_time
                    and (datetime.now() - alert.resolution_time).days < 1
                ]
            ),
        }

        return health_data

    async def _raise_alert(
        self,
        alert_id: str,
        severity: AlertSeverity,
        title: str,
        description: str,
        metadata: Dict[str, Any] = None,
    ) -> None:
        """Raise a system alert"""

        # Check if alert already exists and is recent
        if alert_id in self.alerts:
            existing_alert = self.alerts[alert_id]
            if (
                not existing_alert.resolved
                and existing_alert.age_seconds
                < self.adhd_settings["alert_cooldown_seconds"]
            ):
                return  # Don't spam alerts

        alert = Alert(
            id=alert_id,
            severity=severity,
            title=title,
            description=description,
            metadata=metadata or {},
        )

        self.alerts[alert_id] = alert
        self.alert_history.append(alert)

        # Log the alert
        log_level = {
            AlertSeverity.INFO: logging.INFO,
            AlertSeverity.WARNING: logging.WARNING,
            AlertSeverity.ERROR: logging.ERROR,
            AlertSeverity.CRITICAL: logging.CRITICAL,
        }.get(severity, logging.INFO)

        logger.log(log_level, f"Alert raised: {title} - {description}")

    def _filter_alerts_for_adhd(self, alerts: Dict[str, Any]) -> Dict[str, Any]:
        """Filter and prioritize alerts for ADHD users"""

        # Sort by severity and recency
        sorted_alerts = sorted(
            alerts.items(),
            key=lambda x: (
                {"critical": 4, "error": 3, "warning": 2, "info": 1}.get(
                    x[1]["severity"], 0
                ),
                -x[1]["age_seconds"],  # Newer alerts first
            ),
            reverse=True,
        )

        # Limit to max concurrent alerts
        max_alerts = self.adhd_settings["max_concurrent_alerts"]
        limited_alerts = dict(sorted_alerts[:max_alerts])

        # Group gentle alerts
        gentle_alerts = {k: v for k, v in limited_alerts.items() if v["is_gentle"]}
        critical_alerts = {
            k: v for k, v in limited_alerts.items() if not v["is_gentle"]
        }

        # If we have critical alerts, prioritize those
        if critical_alerts:
            return critical_alerts

        return gentle_alerts

    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an active alert"""
        if alert_id in self.alerts and not self.alerts[alert_id].resolved:
            self.alerts[alert_id].resolved = True
            self.alerts[alert_id].resolution_time = datetime.now()
            logger.info(f"Alert resolved: {alert_id}")
            return True
        return False

    def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of alert status"""
        active_alerts = [alert for alert in self.alerts.values() if not alert.resolved]

        severity_counts = {
            "critical": len(
                [a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]
            ),
            "error": len(
                [a for a in active_alerts if a.severity == AlertSeverity.ERROR]
            ),
            "warning": len(
                [a for a in active_alerts if a.severity == AlertSeverity.WARNING]
            ),
            "info": len([a for a in active_alerts if a.severity == AlertSeverity.INFO]),
        }

        return {
            "total_active": len(active_alerts),
            "severity_breakdown": severity_counts,
            "oldest_alert_age_seconds": max(
                [alert.age_seconds for alert in active_alerts], default=0
            ),
            "adhd_friendly_count": len(
                [alert for alert in active_alerts if alert.is_adhd_gentle]
            ),
        }
