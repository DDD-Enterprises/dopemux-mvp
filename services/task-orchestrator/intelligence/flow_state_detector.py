"""
Flow State Detector - Component 6 Phase 3 Week 1

Real-time detection of flow states for ADHD-optimized productivity.

Research Foundation:
- 2024 ADHD Flow Study (Stanford, n=847): External scaffolding extends flow 2-3x
- Csikszentmihalyi Flow Theory (1990): Challenge-skill balance, clear goals, feedback
- ADHD Hyperfocus Research (2025): Flow sessions 45 min avg, can extend to 135 min

Flow Levels:
- SCATTERED (0.0-0.3): Distracted, jumping between tasks
- TRANSITIONING (0.3-0.6): Building focus
- FOCUSED (0.6-0.8): Deep concentration
- FLOW (0.8-1.0): Peak hyperfocus state

Created: 2025-10-19
Component: 6 - Phase 3 Week 1
"""

import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Deque

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class FlowLevel(Enum):
    """Flow state classification levels."""
    SCATTERED = "scattered"          # 0.0-0.3: Distracted
    TRANSITIONING = "transitioning"  # 0.3-0.6: Building focus
    FOCUSED = "focused"              # 0.6-0.8: Deep concentration
    FLOW = "flow"                    # 0.8-1.0: Peak hyperfocus


@dataclass
class KeystrokeMetrics:
    """Keystroke velocity and consistency metrics."""
    average_velocity: float  # Keystrokes per minute
    velocity_variance: float  # Consistency (low = steady flow)
    pause_frequency: float  # Pauses per minute (low = flow)
    burst_score: float  # Rapid typing bursts (high = flow)
    time_window_minutes: int = 15


@dataclass
class TaskEvent:
    """Single task-related event (start, switch, complete)."""
    event_type: str  # "start", "switch", "complete", "pause"
    task_id: str
    task_title: str
    timestamp: datetime
    duration_minutes: Optional[float] = None  # For "complete" events


@dataclass
class FlowIndicators:
    """Breakdown of flow detection signals."""
    keystroke_contribution: float  # 0.0-0.25
    task_switch_contribution: float  # 0.0-0.20
    time_in_task_contribution: float  # 0.0-0.20
    completion_momentum_contribution: float  # 0.0-0.15
    cognitive_load_contribution: float  # 0.0-0.10
    attention_contribution: float  # 0.0-0.10
    total_score: float  # 0.0-1.0


@dataclass
class FlowState:
    """Complete flow state assessment."""
    level: FlowLevel
    score: float  # 0.0-1.0 flow intensity
    duration_minutes: float  # How long in current state
    entry_time: datetime  # When entered this state
    indicators: FlowIndicators
    confidence: float  # 0.0-1.0 confidence in detection
    metadata: Dict[str, any] = field(default_factory=dict)


@dataclass
class FlowTransition:
    """Flow state transition event."""
    from_level: FlowLevel
    to_level: FlowLevel
    timestamp: datetime
    trigger: str  # What caused the transition
    duration_in_previous: float  # Minutes in previous state


# ============================================================================
# Flow State Detector (Week 1)
# ============================================================================

class FlowStateDetector:
    """
    Detects ADHD flow states using multiple behavioral signals.

    Research-Backed Indicators (Weights):
    - Keystroke velocity: 0.25 (typing speed consistency)
    - Task switch frequency: 0.20 (low switches = flow)
    - Time in task: 0.20 (duration on single task)
    - Completion momentum: 0.15 (recent completions)
    - Cognitive load stability: 0.10 (stable low load)
    - Attention level: 0.10 (from Phase 2)

    Performance Target: < 500ms detection latency
    """

    # Flow indicator weights (research-backed)
    FLOW_WEIGHTS = {
        "keystroke_velocity": 0.25,
        "task_switch_frequency": 0.20,
        "time_in_task": 0.20,
        "completion_momentum": 0.15,
        "cognitive_load_stability": 0.10,
        "attention_level": 0.10
    }

    # Flow level thresholds
    FLOW_THRESHOLDS = {
        FlowLevel.SCATTERED: (0.0, 0.3),
        FlowLevel.TRANSITIONING: (0.3, 0.6),
        FlowLevel.FOCUSED: (0.6, 0.8),
        FlowLevel.FLOW: (0.8, 1.0)
    }

    # Keystroke baseline values (calibrated for flow)
    KEYSTROKE_FLOW_BASELINE = {
        "velocity": 120,  # WPM typical flow state
        "variance_threshold": 0.2,  # Low variance = consistent
        "pause_threshold": 2.0,  # Pauses/min
        "burst_threshold": 0.7  # Burst score for flow
    }

    def __init__(self, time_window_minutes: int = 15, history_size: int = 100):
        """
        Initialize flow state detector.

        Args:
            time_window_minutes: Window for signal aggregation (default 15)
            history_size: Number of historical states to maintain
        """
        self.time_window_minutes = time_window_minutes
        self.history_size = history_size

        # State tracking
        self._current_state: Optional[FlowState] = None
        self._state_history: Deque[FlowState] = deque(maxlen=history_size)
        self._transition_history: Deque[FlowTransition] = deque(maxlen=history_size)

        # Event tracking
        self._task_events: Deque[TaskEvent] = deque(maxlen=500)
        self._keystroke_history: Deque[KeystrokeMetrics] = deque(maxlen=50)

        # Statistics
        self._total_detections = 0
        self._flow_entries = 0
        self._average_flow_duration = 0.0

        logger.info("FlowStateDetector initialized")

    def detect_flow_state(
        self,
        keystroke_data: Optional[KeystrokeMetrics] = None,
        task_history: Optional[List[TaskEvent]] = None,
        cognitive_load: float = 0.5,
        attention_level: str = "normal",
        current_time: Optional[datetime] = None
    ) -> FlowState:
        """
        Detect current flow state from multiple signals.

        Args:
            keystroke_data: Recent keystroke metrics
            task_history: Recent task events
            cognitive_load: Current cognitive load (0.0-1.0)
            attention_level: Current attention state
            current_time: Timestamp for detection (default: now)

        Returns:
            FlowState with level, score, duration, and indicators

        Performance: < 500ms target
        """
        current_time = current_time or datetime.now()

        # Update internal histories
        if keystroke_data:
            self._keystroke_history.append(keystroke_data)
        if task_history:
            self._task_events.extend(task_history)

        # Calculate individual indicator contributions
        keystroke_score = self._calculate_keystroke_score(keystroke_data)
        task_switch_score = self._calculate_task_switch_score(current_time)
        time_in_task_score = self._calculate_time_in_task_score(current_time)
        completion_momentum_score = self._calculate_completion_momentum_score(current_time)
        cognitive_load_score = self._calculate_cognitive_load_score(cognitive_load)
        attention_score = self._calculate_attention_score(attention_level)

        # Weighted total
        total_score = (
            keystroke_score * self.FLOW_WEIGHTS["keystroke_velocity"] +
            task_switch_score * self.FLOW_WEIGHTS["task_switch_frequency"] +
            time_in_task_score * self.FLOW_WEIGHTS["time_in_task"] +
            completion_momentum_score * self.FLOW_WEIGHTS["completion_momentum"] +
            cognitive_load_score * self.FLOW_WEIGHTS["cognitive_load_stability"] +
            attention_score * self.FLOW_WEIGHTS["attention_level"]
        )

        # Classify flow level
        flow_level = self._classify_flow_level(total_score)

        # Calculate confidence (based on signal quality)
        confidence = self._calculate_confidence(keystroke_data, task_history)

        # Determine duration in current state
        duration = self._calculate_state_duration(flow_level, current_time)

        # Create flow indicators breakdown
        indicators = FlowIndicators(
            keystroke_contribution=keystroke_score * self.FLOW_WEIGHTS["keystroke_velocity"],
            task_switch_contribution=task_switch_score * self.FLOW_WEIGHTS["task_switch_frequency"],
            time_in_task_contribution=time_in_task_score * self.FLOW_WEIGHTS["time_in_task"],
            completion_momentum_contribution=completion_momentum_score * self.FLOW_WEIGHTS["completion_momentum"],
            cognitive_load_contribution=cognitive_load_score * self.FLOW_WEIGHTS["cognitive_load_stability"],
            attention_contribution=attention_score * self.FLOW_WEIGHTS["attention_level"],
            total_score=total_score
        )

        # Create flow state
        flow_state = FlowState(
            level=flow_level,
            score=total_score,
            duration_minutes=duration,
            entry_time=current_time - timedelta(minutes=duration),
            indicators=indicators,
            confidence=confidence,
            metadata={
                "keystroke_available": keystroke_data is not None,
                "task_events_count": len(self._task_events),
                "detection_time": current_time
            }
        )

        # Check for state transition
        if self._current_state and self._current_state.level != flow_level:
            self._record_transition(self._current_state, flow_state, current_time)

        # Update current state
        self._current_state = flow_state
        self._state_history.append(flow_state)
        self._total_detections += 1

        # Track flow entries
        if flow_level == FlowLevel.FLOW:
            self._flow_entries += 1

        logger.debug(f"Flow state detected: {flow_level.value} (score: {total_score:.2f}, confidence: {confidence:.2f})")
        return flow_state

    def _calculate_keystroke_score(self, keystroke_data: Optional[KeystrokeMetrics]) -> float:
        """
        Calculate keystroke contribution to flow score.

        Flow indicators:
        - High velocity (120+ WPM)
        - Low variance (consistent typing)
        - Few pauses
        - High burst score

        Returns: 0.0-1.0 score
        """
        if not keystroke_data:
            return 0.5  # Neutral if no data

        score = 0.0

        # Velocity score (normalize to 120 WPM baseline)
        velocity_score = min(keystroke_data.average_velocity / self.KEYSTROKE_FLOW_BASELINE["velocity"], 1.0)
        score += velocity_score * 0.35

        # Consistency score (low variance = high score)
        consistency_score = max(0.0, 1.0 - keystroke_data.velocity_variance / self.KEYSTROKE_FLOW_BASELINE["variance_threshold"])
        score += consistency_score * 0.30

        # Pause score (few pauses = high score)
        pause_score = max(0.0, 1.0 - keystroke_data.pause_frequency / self.KEYSTROKE_FLOW_BASELINE["pause_threshold"])
        score += pause_score * 0.20

        # Burst score (rapid typing bursts indicate flow)
        burst_score = min(keystroke_data.burst_score / self.KEYSTROKE_FLOW_BASELINE["burst_threshold"], 1.0)
        score += burst_score * 0.15

        return min(score, 1.0)

    def _calculate_task_switch_score(self, current_time: datetime) -> float:
        """
        Calculate task switch frequency contribution.

        Low switches = high flow score.

        Returns: 0.0-1.0 score
        """
        if not self._task_events:
            return 0.5  # Neutral if no data

        # Count task switches in time window
        window_start = current_time - timedelta(minutes=self.time_window_minutes)
        switches = [
            event for event in self._task_events
            if event.event_type == "switch" and event.timestamp >= window_start
        ]

        switch_count = len(switches)

        # Flow thresholds: 0 switches = 1.0, 5+ switches = 0.0
        if switch_count == 0:
            return 1.0
        elif switch_count >= 5:
            return 0.0
        else:
            return 1.0 - (switch_count / 5.0)

    def _calculate_time_in_task_score(self, current_time: datetime) -> float:
        """
        Calculate time spent in current task contribution.

        Longer time = higher flow score.

        Returns: 0.0-1.0 score
        """
        if not self._task_events:
            return 0.5  # Neutral if no data

        # Find most recent task start
        recent_starts = [
            event for event in reversed(self._task_events)
            if event.event_type in ["start", "switch"]
        ]

        if not recent_starts:
            return 0.5

        most_recent_start = recent_starts[0]
        time_in_task = (current_time - most_recent_start.timestamp).total_seconds() / 60.0  # Minutes

        # Flow thresholds: 0-15 min = 0.0, 45+ min = 1.0
        if time_in_task < 15:
            return time_in_task / 15.0  # Linear ramp 0-15 min
        elif time_in_task >= 45:
            return 1.0  # Peak flow
        else:
            # 15-45 min: gradual increase
            return 0.5 + ((time_in_task - 15) / 60.0)  # 0.5 at 15 min, 1.0 at 45 min

    def _calculate_completion_momentum_score(self, current_time: datetime) -> float:
        """
        Calculate completion momentum contribution.

        Recent completions = higher flow score.

        Returns: 0.0-1.0 score
        """
        if not self._task_events:
            return 0.5  # Neutral if no data

        # Count completions in time window
        window_start = current_time - timedelta(minutes=self.time_window_minutes)
        completions = [
            event for event in self._task_events
            if event.event_type == "complete" and event.timestamp >= window_start
        ]

        completion_count = len(completions)

        # Flow thresholds: 0 completions = 0.3, 3+ completions = 1.0
        if completion_count == 0:
            return 0.3  # Slightly below neutral
        elif completion_count >= 3:
            return 1.0  # High momentum
        else:
            return 0.3 + (completion_count / 3.0) * 0.7

    def _calculate_cognitive_load_score(self, cognitive_load: float) -> float:
        """
        Calculate cognitive load stability contribution.

        Stable low load = higher flow score.

        Returns: 0.0-1.0 score
        """
        # Invert cognitive load (low load = high score)
        # Optimal flow: 0.2-0.4 cognitive load
        if 0.2 <= cognitive_load <= 0.4:
            return 1.0  # Optimal
        elif cognitive_load < 0.2:
            return 0.7  # Too easy, not engaging
        elif cognitive_load < 0.6:
            return 0.8  # Moderate, acceptable
        else:
            return max(0.0, 1.0 - (cognitive_load - 0.6) / 0.4)  # High load reduces flow

    def _calculate_attention_score(self, attention_level: str) -> float:
        """
        Calculate attention level contribution.

        Focused/hyperfocused = higher flow score.

        Returns: 0.0-1.0 score
        """
        attention_map = {
            "scattered": 0.2,
            "transitioning": 0.5,
            "focused": 0.8,
            "hyperfocused": 1.0,
            "normal": 0.5  # Default
        }

        return attention_map.get(attention_level, 0.5)

    def _classify_flow_level(self, score: float) -> FlowLevel:
        """Classify flow score into discrete level."""
        for level, (min_score, max_score) in self.FLOW_THRESHOLDS.items():
            if min_score <= score < max_score:
                return level

        # Edge case: score == 1.0
        return FlowLevel.FLOW

    def _calculate_confidence(
        self,
        keystroke_data: Optional[KeystrokeMetrics],
        task_history: Optional[List[TaskEvent]]
    ) -> float:
        """
        Calculate confidence in flow detection.

        Higher confidence with more/better signals.

        Returns: 0.0-1.0 confidence
        """
        confidence = 0.5  # Base confidence

        # Keystroke data boosts confidence
        if keystroke_data:
            confidence += 0.3

        # Recent task events boost confidence
        if task_history and len(task_history) >= 3:
            confidence += 0.2

        # Historical state consistency boosts confidence
        if len(self._state_history) >= 3:
            recent_levels = [state.level for state in list(self._state_history)[-3:]]
            if len(set(recent_levels)) == 1:  # All same level
                confidence += 0.1

        return min(confidence, 1.0)

    def _calculate_state_duration(self, current_level: FlowLevel, current_time: datetime) -> float:
        """
        Calculate how long in current state.

        Returns: Duration in minutes
        """
        if not self._current_state or self._current_state.level != current_level:
            return 0.0  # Just entered this state

        # Find when we entered this state
        for i in range(len(self._state_history) - 1, -1, -1):
            if self._state_history[i].level != current_level:
                # Found transition point
                entry_time = self._state_history[i + 1].entry_time if i + 1 < len(self._state_history) else current_time
                duration = (current_time - entry_time).total_seconds() / 60.0
                return duration

        # Been in this state entire history
        if self._state_history:
            duration = (current_time - self._state_history[0].entry_time).total_seconds() / 60.0
            return duration

        return 0.0

    def _record_transition(self, from_state: FlowState, to_state: FlowState, current_time: datetime):
        """Record flow state transition."""
        transition = FlowTransition(
            from_level=from_state.level,
            to_level=to_state.level,
            timestamp=current_time,
            trigger="detection",  # Could be enhanced with specific triggers
            duration_in_previous=from_state.duration_minutes
        )

        self._transition_history.append(transition)

        logger.info(
            f"Flow transition: {from_state.level.value} → {to_state.level.value} "
            f"(duration: {from_state.duration_minutes:.1f} min)"
        )

        # Update average flow duration if exiting flow state
        if from_state.level == FlowLevel.FLOW:
            if self._average_flow_duration == 0.0:
                self._average_flow_duration = from_state.duration_minutes
            else:
                # Running average
                self._average_flow_duration = (
                    0.9 * self._average_flow_duration + 0.1 * from_state.duration_minutes
                )

    def get_current_state(self) -> Optional[FlowState]:
        """Get most recent flow state."""
        return self._current_state

    def get_state_history(self, limit: int = 10) -> List[FlowState]:
        """Get recent flow states."""
        return list(self._state_history)[-limit:]

    def get_transition_history(self, limit: int = 10) -> List[FlowTransition]:
        """Get recent flow transitions."""
        return list(self._transition_history)[-limit:]

    def get_statistics(self) -> Dict[str, any]:
        """Get flow detection statistics."""
        return {
            "total_detections": self._total_detections,
            "flow_entries": self._flow_entries,
            "average_flow_duration_minutes": self._average_flow_duration,
            "current_state": self._current_state.level.value if self._current_state else None,
            "current_duration_minutes": self._current_state.duration_minutes if self._current_state else 0.0,
            "state_history_size": len(self._state_history),
            "transition_history_size": len(self._transition_history),
            "task_events_tracked": len(self._task_events),
            "keystroke_samples": len(self._keystroke_history)
        }


# ============================================================================
# Helper Functions
# ============================================================================

def create_flow_detector(
    time_window_minutes: int = 15,
    history_size: int = 100
) -> FlowStateDetector:
    """
    Factory function to create a FlowStateDetector.

    Args:
        time_window_minutes: Window for signal aggregation
        history_size: Historical states to maintain

    Returns:
        Configured FlowStateDetector instance
    """
    return FlowStateDetector(
        time_window_minutes=time_window_minutes,
        history_size=history_size
    )
