"""
Metrics Collection for ADHD Intelligence Layer

Collects and exposes Prometheus metrics for Component 6 observability.

Created: 2025-10-20
Component: 6 - Phase 1a (Observability Foundation)
Purpose: Track ADHD workflow metrics, focus patterns, cognitive load trends

Key Metrics:
- ADHD workflow completion rate (target: 85%)
- Focus duration patterns (session lengths, flow frequency)
- Task completion velocity (tasks/day, complexity-adjusted)
- Cognitive load trends (average load, overwhelm frequency)
- Context switch frequency and recovery time
"""

import time

import logging

logger = logging.getLogger(__name__)

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum

try:
    from prometheus_client import Counter, Histogram, Gauge, Summary, CollectorRegistry
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Graceful degradation: metrics collection disabled if prometheus_client not installed


class MetricType(Enum):
    """Metric types for different use cases."""
    COUNTER = "counter"      # Monotonically increasing (total tasks completed)
    GAUGE = "gauge"          # Can go up/down (current cognitive load)
    HISTOGRAM = "histogram"  # Distribution (task duration buckets)
    SUMMARY = "summary"      # Percentiles (p50, p95, p99 of focus duration)


class MetricsCollector:
    """
    Central metrics collection for ADHD Intelligence Layer.

    Provides Prometheus-compatible metrics with ADHD-specific context.
    Falls back to in-memory tracking if Prometheus unavailable.

    Usage:
        metrics = MetricsCollector()

        # Track task completion
        metrics.record_task_completion(
            task_id="task-001",
            duration_seconds=1200,
            complexity=0.65,
            adhd_state="focused"
        )

        # Track cognitive load
        metrics.record_cognitive_load(load=0.72)

        # Track context switches
        metrics.record_context_switch(
            from_context="task-001",
            to_context="task-002",
            recovery_seconds=120
        )
    """

    def __init__(self, registry: Optional[Any] = None):
        """
        Initialize metrics collector.

        Args:
            registry: Optional Prometheus registry. Creates new if None.
        """
        self.enabled = PROMETHEUS_AVAILABLE
        self.registry = registry if registry else (CollectorRegistry() if PROMETHEUS_AVAILABLE else None)

        # In-memory fallback for when Prometheus unavailable
        self.in_memory_metrics: Dict[str, List[float]] = {}

        if self.enabled:
            self._initialize_prometheus_metrics()
        else:
            logger.info("⚠️  Prometheus not available - metrics collection disabled")

    def _initialize_prometheus_metrics(self):
        """Initialize all Prometheus metrics."""

        # ========================================================================
        # ADHD Workflow Completion Metrics
        # ========================================================================

        self.tasks_started = Counter(
            'adhd_tasks_started_total',
            'Total number of tasks started',
            ['energy_level', 'complexity_range'],
            registry=self.registry
        )

        self.tasks_completed = Counter(
            'adhd_tasks_completed_total',
            'Total number of tasks completed',
            ['energy_level', 'complexity_range', 'completion_type'],
            registry=self.registry
        )

        self.tasks_abandoned = Counter(
            'adhd_tasks_abandoned_total',
            'Total number of tasks abandoned (F001 untracked work)',
            ['reason'],
            registry=self.registry
        )

        self.task_completion_rate = Gauge(
            'adhd_task_completion_rate',
            'Current task completion rate (completed / started)',
            registry=self.registry
        )

        # ========================================================================
        # Focus Duration & Flow State Metrics
        # ========================================================================

        self.focus_duration_seconds = Histogram(
            'adhd_focus_duration_seconds',
            'Distribution of focus session durations',
            buckets=[60, 300, 600, 900, 1500, 2700, 3600],  # 1min to 1hour
            registry=self.registry
        )

        self.flow_sessions = Counter(
            'adhd_flow_sessions_total',
            'Total number of flow state sessions detected',
            ['flow_duration_range'],
            registry=self.registry
        )

        self.flow_duration_seconds = Summary(
            'adhd_flow_duration_seconds',
            'Flow state session durations (percentiles)',
            registry=self.registry
        )

        self.current_flow_state = Gauge(
            'adhd_current_flow_state',
            'Current flow state (1 = in flow, 0 = not in flow)',
            registry=self.registry
        )

        # ========================================================================
        # Task Velocity Metrics
        # ========================================================================

        self.task_duration_seconds = Histogram(
            'adhd_task_duration_seconds',
            'Distribution of task completion times',
            buckets=[60, 300, 600, 1800, 3600, 7200, 14400],  # 1min to 4hours
            registry=self.registry
        )

        self.task_velocity_per_day = Gauge(
            'adhd_task_velocity_per_day',
            'Tasks completed per day (rolling average)',
            registry=self.registry
        )

        self.complexity_adjusted_velocity = Gauge(
            'adhd_complexity_adjusted_velocity',
            'Velocity weighted by task complexity',
            registry=self.registry
        )

        # ========================================================================
        # Cognitive Load Metrics
        # ========================================================================

        self.cognitive_load = Gauge(
            'adhd_cognitive_load',
            'Current cognitive load score (0.0-1.0)',
            ['load_category'],  # low/optimal/high/critical
            registry=self.registry
        )

        self.cognitive_load_history = Histogram(
            'adhd_cognitive_load_distribution',
            'Distribution of cognitive load scores',
            buckets=[0.2, 0.4, 0.6, 0.8, 1.0],
            registry=self.registry
        )

        self.overwhelm_events = Counter(
            'adhd_overwhelm_events_total',
            'Total overwhelm events (load > 0.85)',
            ['trigger_reason'],
            registry=self.registry
        )

        self.time_in_optimal_load = Counter(
            'adhd_time_in_optimal_load_seconds',
            'Total time spent in optimal cognitive load (0.6-0.7)',
            registry=self.registry
        )

        # ========================================================================
        # Context Switch Metrics
        # ========================================================================

        self.context_switches = Counter(
            'adhd_context_switches_total',
            'Total context switches',
            ['switch_reason'],  # interrupt/intentional/break_return
            registry=self.registry
        )

        self.context_switch_recovery_seconds = Histogram(
            'adhd_context_switch_recovery_seconds',
            'Time to recover from context switch',
            buckets=[2, 5, 10, 30, 60, 300, 900],  # 2sec to 15min
            registry=self.registry
        )

        self.context_switches_per_day = Gauge(
            'adhd_context_switches_per_day',
            'Context switches per day (rolling average)',
            registry=self.registry
        )

    # ========================================================================
    # Recording Methods
    # ========================================================================

    def record_task_start(
        self,
        task_id: str,
        energy_level: str,
        complexity: float
    ):
        """Record when a task is started."""
        complexity_range = self._classify_complexity(complexity)

        if self.enabled:
            self.tasks_started.labels(
                energy_level=energy_level,
                complexity_range=complexity_range
            ).inc()
        else:
            self._record_in_memory('tasks_started', 1.0)

    def record_task_completion(
        self,
        task_id: str,
        duration_seconds: float,
        complexity: float,
        energy_level: str,
        completion_type: str = "full"  # full/partial/abandoned
    ):
        """
        Record task completion.

        Args:
            task_id: Unique task identifier
            duration_seconds: Time to complete
            complexity: Task complexity (0.0-1.0)
            energy_level: Energy when completed (low/medium/high)
            completion_type: full/partial/abandoned
        """
        complexity_range = self._classify_complexity(complexity)

        if self.enabled:
            self.tasks_completed.labels(
                energy_level=energy_level,
                complexity_range=complexity_range,
                completion_type=completion_type
            ).inc()

            self.task_duration_seconds.observe(duration_seconds)

            # Update completion rate
            self._update_completion_rate()
        else:
            self._record_in_memory('tasks_completed', 1.0)
            self._record_in_memory('task_duration', duration_seconds)

    def record_task_abandonment(self, task_id: str, reason: str):
        """Record when a task is abandoned."""
        if self.enabled:
            self.tasks_abandoned.labels(reason=reason).inc()
        else:
            self._record_in_memory('tasks_abandoned', 1.0)

    def record_flow_state(
        self,
        in_flow: bool,
        duration_seconds: Optional[float] = None
    ):
        """
        Record flow state detection.

        Args:
            in_flow: Whether currently in flow state
            duration_seconds: Flow duration if session ended
        """
        if self.enabled:
            self.current_flow_state.set(1.0 if in_flow else 0.0)

            if duration_seconds is not None and in_flow:
                self.flow_duration_seconds.observe(duration_seconds)

                duration_range = self._classify_flow_duration(duration_seconds)
                self.flow_sessions.labels(
                    flow_duration_range=duration_range
                ).inc()
        else:
            self._record_in_memory('flow_state', 1.0 if in_flow else 0.0)

    def record_focus_duration(self, duration_seconds: float):
        """Record a completed focus session."""
        if self.enabled:
            self.focus_duration_seconds.observe(duration_seconds)
        else:
            self._record_in_memory('focus_duration', duration_seconds)

    def record_cognitive_load(self, load: float):
        """
        Record current cognitive load.

        Args:
            load: Cognitive load score (0.0-1.0)
        """
        category = self._classify_cognitive_load(load)

        if self.enabled:
            self.cognitive_load.labels(load_category=category).set(load)
            self.cognitive_load_history.observe(load)

            # Track optimal load time
            if 0.6 <= load <= 0.7:
                self.time_in_optimal_load.inc()

            # Track overwhelm
            if load > 0.85:
                self.overwhelm_events.labels(
                    trigger_reason="high_load"
                ).inc()
        else:
            self._record_in_memory('cognitive_load', load)

    def record_context_switch(
        self,
        from_context: str,
        to_context: str,
        switch_reason: str,
        recovery_seconds: Optional[float] = None
    ):
        """
        Record a context switch event.

        Args:
            from_context: Previous context (task ID or "none")
            to_context: New context (task ID or "none")
            switch_reason: interrupt/intentional/break_return
            recovery_seconds: Time to recover (if measured)
        """
        if self.enabled:
            self.context_switches.labels(
                switch_reason=switch_reason
            ).inc()

            if recovery_seconds is not None:
                self.context_switch_recovery_seconds.observe(recovery_seconds)
        else:
            self._record_in_memory('context_switches', 1.0)
            if recovery_seconds:
                self._record_in_memory('recovery_time', recovery_seconds)

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _classify_complexity(self, complexity: float) -> str:
        """Classify complexity into ranges."""
        if complexity < 0.3:
            return "low"
        elif complexity < 0.6:
            return "medium"
        else:
            return "high"

    def _classify_flow_duration(self, seconds: float) -> str:
        """Classify flow session duration."""
        if seconds < 600:
            return "short"  # < 10 min
        elif seconds < 1800:
            return "medium"  # 10-30 min
        else:
            return "long"  # > 30 min

    def _classify_cognitive_load(self, load: float) -> str:
        """Classify cognitive load category."""
        if load < 0.3:
            return "low"
        elif load < 0.7:
            return "optimal"
        elif load < 0.85:
            return "high"
        else:
            return "critical"

    def _update_completion_rate(self):
        """Update task completion rate gauge."""
        # This would query Prometheus to calculate rate
        # For now, it's updated externally via dedicated calculation
        pass

    def _record_in_memory(self, metric_name: str, value: float):
        """Fallback: record metric in memory when Prometheus unavailable."""
        if metric_name not in self.in_memory_metrics:
            self.in_memory_metrics[metric_name] = []

        self.in_memory_metrics[metric_name].append({
            'timestamp': datetime.now(),
            'value': value
        })

        # Keep only last 1000 samples per metric
        if len(self.in_memory_metrics[metric_name]) > 1000:
            self.in_memory_metrics[metric_name] = self.in_memory_metrics[metric_name][-1000:]

    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Get summary statistics (useful for debugging).

        Returns:
            Dict with current metric values
        """
        if not self.enabled:
            return {
                "status": "disabled",
                "reason": "prometheus_client not installed",
                "in_memory_metrics": {
                    name: len(values)
                    for name, values in self.in_memory_metrics.items()
                }
            }

        return {
            "status": "enabled",
            "prometheus_available": True,
            "metrics_registered": len(self.registry._collector_to_names)
        }


# Singleton instance for easy import
_metrics_instance: Optional[MetricsCollector] = None

def get_metrics() -> MetricsCollector:
    """Get singleton metrics collector instance."""
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = MetricsCollector()
    return _metrics_instance
