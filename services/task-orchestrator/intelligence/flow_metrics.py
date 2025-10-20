"""
Flow Metrics Collector - Component 6 Phase 3 Week 1

Prometheus metrics for ADHD flow state monitoring and analysis.

Metrics Categories:
1. Flow State Distribution: Time in each flow level
2. Flow Session Duration: How long flow sessions last
3. Flow Entries: Frequency of entering flow
4. Flow Interruptions: What breaks flow states
5. Flow Transitions: State change patterns

Created: 2025-10-19
Component: 6 - Phase 3 Week 1
"""

import logging
from typing import Optional

from .flow_state_detector import FlowLevel, FlowState, FlowTransition

logger = logging.getLogger(__name__)

# Prometheus imports (graceful degradation if unavailable)
try:
    from prometheus_client import Counter, Gauge, Histogram
    PROMETHEUS_AVAILABLE = True
except ImportError:
    logger.warning("Prometheus client not available - metrics disabled")
    PROMETHEUS_AVAILABLE = False


# ============================================================================
# Flow Metrics Collector
# ============================================================================

class FlowMetricsCollector:
    """
    Collects Prometheus metrics for ADHD flow state monitoring.

    Metrics:
    - flow_state_duration: Time spent in each flow level
    - flow_session_duration: Duration of flow sessions when exiting
    - flow_entries_total: Number of times entered flow state
    - flow_interruptions_total: Interruptions during flow
    - flow_transitions_total: State transitions count
    - current_flow_score: Real-time flow intensity (0.0-1.0)
    - flow_confidence: Detection confidence score

    Integration:
    - Grafana dashboards for flow visualization
    - Alerting when flow interrupted
    - Historical trend analysis
    """

    def __init__(self, workspace_id: str, enabled: bool = True):
        """
        Initialize flow metrics collector.

        Args:
            workspace_id: Workspace identifier for metric labeling
            enabled: Whether metrics collection is enabled
        """
        self.workspace_id = workspace_id
        self.enabled = enabled and PROMETHEUS_AVAILABLE

        if not self.enabled:
            logger.info("Flow metrics collection disabled (Prometheus unavailable or disabled)")
            return

        # Flow state duration (histogram)
        self.flow_state_duration = Histogram(
            "flow_state_duration_minutes",
            "Duration spent in each flow state level",
            ["workspace", "flow_level"],
            buckets=[1, 5, 10, 15, 30, 45, 60, 90, 120, 180]  # Minutes
        )

        # Flow session duration (histogram - only for FLOW level)
        self.flow_session_duration = Histogram(
            "flow_session_duration_minutes",
            "Duration of complete flow sessions (FLOW level)",
            ["workspace"],
            buckets=[15, 30, 45, 60, 90, 120, 135, 150, 180]  # Target: 45 → 135 min
        )

        # Flow entries counter
        self.flow_entries_total = Counter(
            "flow_entries_total",
            "Number of times entered flow state (FLOW level)",
            ["workspace"]
        )

        # Flow interruptions counter
        self.flow_interruptions_total = Counter(
            "flow_interruptions_total",
            "Interruptions that broke flow state",
            ["workspace", "from_level", "interruption_trigger"]
        )

        # Flow transitions counter
        self.flow_transitions_total = Counter(
            "flow_transitions_total",
            "Flow state transitions",
            ["workspace", "from_level", "to_level"]
        )

        # Current flow score (gauge - real-time)
        self.current_flow_score = Gauge(
            "current_flow_score",
            "Real-time flow intensity score (0.0-1.0)",
            ["workspace"]
        )

        # Current flow level (gauge - encoded as numeric)
        self.current_flow_level_numeric = Gauge(
            "current_flow_level_numeric",
            "Current flow level (0=scattered, 1=transitioning, 2=focused, 3=flow)",
            ["workspace"]
        )

        # Flow detection confidence (gauge)
        self.flow_confidence = Gauge(
            "flow_confidence",
            "Confidence in flow state detection (0.0-1.0)",
            ["workspace"]
        )

        # Flow indicator contributions (gauges)
        self.keystroke_contribution = Gauge(
            "flow_keystroke_contribution",
            "Keystroke contribution to flow score",
            ["workspace"]
        )

        self.task_switch_contribution = Gauge(
            "flow_task_switch_contribution",
            "Task switch contribution to flow score",
            ["workspace"]
        )

        self.time_in_task_contribution = Gauge(
            "flow_time_in_task_contribution",
            "Time in task contribution to flow score",
            ["workspace"]
        )

        self.completion_momentum_contribution = Gauge(
            "flow_completion_momentum_contribution",
            "Completion momentum contribution to flow score",
            ["workspace"]
        )

        # Session statistics
        self._total_flow_entries = 0
        self._total_flow_interruptions = 0
        self._average_flow_duration = 0.0

        logger.info(f"FlowMetricsCollector initialized for workspace: {workspace_id}")

    def record_flow_state(self, flow_state: FlowState):
        """
        Record current flow state metrics.

        Args:
            flow_state: Current flow state from detector
        """
        if not self.enabled:
            return

        # Update real-time gauges
        self.current_flow_score.labels(workspace=self.workspace_id).set(flow_state.score)
        self.current_flow_level_numeric.labels(workspace=self.workspace_id).set(
            self._encode_flow_level(flow_state.level)
        )
        self.flow_confidence.labels(workspace=self.workspace_id).set(flow_state.confidence)

        # Update indicator contribution gauges
        self.keystroke_contribution.labels(workspace=self.workspace_id).set(
            flow_state.indicators.keystroke_contribution
        )
        self.task_switch_contribution.labels(workspace=self.workspace_id).set(
            flow_state.indicators.task_switch_contribution
        )
        self.time_in_task_contribution.labels(workspace=self.workspace_id).set(
            flow_state.indicators.time_in_task_contribution
        )
        self.completion_momentum_contribution.labels(workspace=self.workspace_id).set(
            flow_state.indicators.completion_momentum_contribution
        )

        logger.debug(
            f"Flow state recorded: {flow_state.level.value} "
            f"(score: {flow_state.score:.2f}, duration: {flow_state.duration_minutes:.1f} min)"
        )

    def record_flow_transition(self, transition: FlowTransition):
        """
        Record flow state transition.

        Args:
            transition: Flow transition event
        """
        if not self.enabled:
            return

        # Increment transition counter
        self.flow_transitions_total.labels(
            workspace=self.workspace_id,
            from_level=transition.from_level.value,
            to_level=transition.to_level.value
        ).inc()

        # Record duration in previous state
        self.flow_state_duration.labels(
            workspace=self.workspace_id,
            flow_level=transition.from_level.value
        ).observe(transition.duration_in_previous)

        # If exiting flow state, record session duration
        if transition.from_level == FlowLevel.FLOW:
            self.flow_session_duration.labels(
                workspace=self.workspace_id
            ).observe(transition.duration_in_previous)

            # Track average flow duration
            self._total_flow_entries += 1
            if self._average_flow_duration == 0.0:
                self._average_flow_duration = transition.duration_in_previous
            else:
                self._average_flow_duration = (
                    0.9 * self._average_flow_duration + 0.1 * transition.duration_in_previous
                )

            logger.info(
                f"Flow session ended: {transition.duration_in_previous:.1f} min "
                f"(avg: {self._average_flow_duration:.1f} min)"
            )

        # If entering flow state, increment entries
        if transition.to_level == FlowLevel.FLOW:
            self.flow_entries_total.labels(workspace=self.workspace_id).inc()
            logger.info("Entered flow state")

        # Detect interruptions (flow degradation)
        if self._is_interruption(transition):
            self.record_flow_interruption(transition)

        logger.debug(
            f"Flow transition recorded: {transition.from_level.value} → {transition.to_level.value} "
            f"(duration: {transition.duration_in_previous:.1f} min)"
        )

    def record_flow_interruption(self, transition: FlowTransition):
        """
        Record flow interruption event.

        Args:
            transition: Transition that represents interruption
        """
        if not self.enabled:
            return

        self.flow_interruptions_total.labels(
            workspace=self.workspace_id,
            from_level=transition.from_level.value,
            interruption_trigger=transition.trigger
        ).inc()

        self._total_flow_interruptions += 1

        logger.warning(
            f"Flow interruption: {transition.from_level.value} → {transition.to_level.value} "
            f"(trigger: {transition.trigger}, lost {transition.duration_in_previous:.1f} min)"
        )

    def _is_interruption(self, transition: FlowTransition) -> bool:
        """
        Determine if transition represents an interruption.

        Interruption criteria:
        - FLOW → anything except FOCUSED
        - FOCUSED → SCATTERED
        - Any significant degradation

        Returns: True if interruption, False otherwise
        """
        from_numeric = self._encode_flow_level(transition.from_level)
        to_numeric = self._encode_flow_level(transition.to_level)

        # Significant degradation (2+ levels)
        if from_numeric - to_numeric >= 2:
            return True

        # Specific interruption patterns
        if transition.from_level == FlowLevel.FLOW and transition.to_level != FlowLevel.FOCUSED:
            return True

        if transition.from_level == FlowLevel.FOCUSED and transition.to_level == FlowLevel.SCATTERED:
            return True

        return False

    def _encode_flow_level(self, level: FlowLevel) -> int:
        """Encode flow level as numeric for Prometheus gauge."""
        encoding = {
            FlowLevel.SCATTERED: 0,
            FlowLevel.TRANSITIONING: 1,
            FlowLevel.FOCUSED: 2,
            FlowLevel.FLOW: 3
        }
        return encoding.get(level, 0)

    def get_statistics(self) -> dict:
        """Get flow metrics statistics."""
        return {
            "total_flow_entries": self._total_flow_entries,
            "total_flow_interruptions": self._total_flow_interruptions,
            "average_flow_duration_minutes": self._average_flow_duration,
            "interruption_rate": (
                self._total_flow_interruptions / max(self._total_flow_entries, 1)
            ) if self._total_flow_entries > 0 else 0.0,
            "prometheus_enabled": self.enabled
        }


# ============================================================================
# Helper Functions
# ============================================================================

def create_flow_metrics_collector(
    workspace_id: str,
    enabled: bool = True
) -> FlowMetricsCollector:
    """
    Factory function to create a FlowMetricsCollector.

    Args:
        workspace_id: Workspace identifier
        enabled: Whether to enable metrics collection

    Returns:
        Configured FlowMetricsCollector instance
    """
    return FlowMetricsCollector(
        workspace_id=workspace_id,
        enabled=enabled
    )


# ============================================================================
# Grafana Dashboard Configuration
# ============================================================================

FLOW_DASHBOARD_PANELS = """
Grafana Dashboard Configuration for ADHD Flow State Monitoring

Panel 1: Real-Time Flow Score
- Metric: current_flow_score
- Type: Gauge (0.0-1.0)
- Thresholds: 0.3 (SCATTERED), 0.6 (TRANSITIONING), 0.8 (FOCUSED), 1.0 (FLOW)
- Colors: Red → Yellow → Green → Blue

Panel 2: Flow Level Timeline
- Metric: current_flow_level_numeric
- Type: Time series
- Transform: 0 → SCATTERED, 1 → TRANSITIONING, 2 → FOCUSED, 3 → FLOW
- Visualization: Stacked area chart

Panel 3: Flow Session Duration Distribution
- Metric: flow_session_duration_minutes
- Type: Histogram
- Buckets: 15, 30, 45, 60, 90, 120, 135, 150, 180
- Target: 45 min (baseline) → 135 min (goal)

Panel 4: Flow Entries vs Interruptions
- Metrics: flow_entries_total, flow_interruptions_total
- Type: Stat panels (side by side)
- Calculation: Rate over 24h
- Target: 4-5 entries/day, <2 interruptions/day

Panel 5: Flow Indicator Breakdown
- Metrics: flow_keystroke_contribution, flow_task_switch_contribution, etc.
- Type: Stacked bar chart
- Shows contribution of each indicator to total flow score

Panel 6: Flow Transition Heatmap
- Metric: flow_transitions_total
- Type: Heatmap
- Rows: from_level (SCATTERED → FLOW)
- Columns: to_level (SCATTERED → FLOW)
- Shows most common transition patterns

Panel 7: Average Flow Duration Trend
- Metric: flow_session_duration_minutes
- Type: Time series
- Aggregation: Moving average (24h)
- Target line: 135 minutes (3x ADHD baseline)

Panel 8: Flow Confidence Score
- Metric: flow_confidence
- Type: Gauge (0.0-1.0)
- Indicates reliability of flow detection

Alerts:
1. Flow Interrupted: flow_interruptions_total rate > 3 per 4 hours
2. Low Flow Entry Rate: flow_entries_total < 2 per day
3. Short Flow Sessions: flow_session_duration_minutes < 30 min consistently
4. Detection Confidence Low: flow_confidence < 0.5 for 15+ min
"""
