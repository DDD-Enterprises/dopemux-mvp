"""
Attention Monitor for ADHD-optimized development.

Tracks attention patterns, keystrokes, context switches, and classifies
attention states to provide adaptive interface adjustments.
"""

import json
import threading
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from rich.console import Console

console = Console()


@dataclass
class AttentionMetrics:
    """Attention metrics data structure."""

    timestamp: datetime
    keystroke_rate: float  # Keys per minute
    error_rate: float  # Errors per minute
    context_switches: int  # File/directory switches
    pause_duration: float  # Seconds since last activity
    focus_score: float  # Calculated focus score (0-1)
    attention_state: str  # classified state


class AttentionState:
    """Attention state classification."""

    FOCUSED = "focused"
    NORMAL = "normal"
    SCATTERED = "scattered"
    HYPERFOCUS = "hyperfocus"
    DISTRACTED = "distracted"


class AttentionMonitor:
    """
    Monitors and classifies user attention patterns.

    Features:
    - Real-time keystroke and activity tracking
    - Context switch detection
    - Attention state classification
    - Adaptive interface recommendations
    - Privacy-respecting metrics (no actual keystrokes logged)
    """

    def __init__(self, project_path: Path):
        """Initialize attention monitor."""
        self.project_path = project_path
        self.data_dir = project_path / ".dopemux" / "attention"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Monitoring state
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._callbacks: List[Callable[[AttentionMetrics], None]] = []

        # Metrics storage
        self._metrics_history: deque = deque(maxlen=1000)  # Last 1000 samples
        self._session_start = datetime.now()
        self._last_activity = datetime.now()
        self._current_file = ""
        self._keystroke_buffer: deque = deque(maxlen=60)  # Last 60 seconds
        self._error_buffer: deque = deque(maxlen=60)
        self._context_switch_buffer: deque = deque(maxlen=300)  # Last 5 minutes

        # State tracking
        self._current_state = AttentionState.NORMAL
        self._state_duration = 0
        self._focus_session_start: Optional[datetime] = None

        # Configuration
        self.sample_interval = 5  # seconds
        self.keystroke_threshold = 2.0  # keys per second for active typing
        self.context_switch_threshold = 3  # switches per minute for scattered
        self.focus_threshold = 0.7  # focus score threshold
        self.hyperfocus_duration = 45  # minutes for hyperfocus detection

    def start_monitoring(self) -> None:
        """Start attention monitoring in background thread."""
        if self._monitoring:
            return

        self._monitoring = True
        self._session_start = datetime.now()
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

        console.print("[green]🧠 Attention monitoring started[/green]")

    def stop_monitoring(self) -> None:
        """Stop attention monitoring."""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1)

        # Save final metrics
        self._save_session_metrics()
        console.print("[blue]Attention monitoring stopped[/blue]")

    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current attention metrics."""
        if not self._metrics_history:
            return self._get_default_metrics()

        latest_metrics = self._metrics_history[-1]
        session_duration = (datetime.now() - self._session_start).total_seconds() / 60

        return {
            "attention_state": latest_metrics.attention_state,
            "focus_score": latest_metrics.focus_score,
            "session_duration": session_duration,
            "keystroke_rate": latest_metrics.keystroke_rate,
            "error_rate": latest_metrics.error_rate,
            "context_switches": sum(
                m.context_switches for m in list(self._metrics_history)[-12:]
            ),  # Last minute
            "state_duration": self._state_duration,
            "monitoring_active": self._monitoring,
        }

    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session."""
        if not self._metrics_history:
            return {}

        metrics_list = list(self._metrics_history)
        total_samples = len(metrics_list)

        # Calculate averages
        avg_focus_score = sum(m.focus_score for m in metrics_list) / total_samples
        total_context_switches = sum(m.context_switches for m in metrics_list)
        session_duration = (datetime.now() - self._session_start).total_seconds() / 60

        # State distribution
        state_counts = {}
        for m in metrics_list:
            state_counts[m.attention_state] = state_counts.get(m.attention_state, 0) + 1

        state_percentages = {
            state: (count / total_samples) * 100
            for state, count in state_counts.items()
        }

        return {
            "session_duration_minutes": session_duration,
            "average_focus_score": avg_focus_score,
            "total_context_switches": total_context_switches,
            "context_switches_per_hour": (
                (total_context_switches / session_duration) * 60
                if session_duration > 0
                else 0
            ),
            "state_distribution": state_percentages,
            "productivity_score": self._calculate_productivity_score(),
            "recommendations": self._generate_recommendations(),
        }

    def add_callback(self, callback: Callable[[AttentionMetrics], None]) -> None:
        """Add callback for attention state changes."""
        self._callbacks.append(callback)

    def simulate_activity(self, activity_type: str, **kwargs) -> None:
        """Simulate activity for testing (development use)."""
        now = datetime.now()
        self._last_activity = now

        if activity_type == "keystroke":
            self._keystroke_buffer.append(now)
        elif activity_type == "error":
            self._error_buffer.append(now)
        elif activity_type == "file_switch":
            self._context_switch_buffer.append(now)
            self._current_file = kwargs.get("file", self._current_file)

        # Trigger immediate metrics update
        if self._monitoring:
            self._collect_metrics()

    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self._monitoring:
            try:
                self._collect_metrics()
                time.sleep(self.sample_interval)
            except Exception as e:
                console.print(f"[red]Attention monitoring error: {e}[/red]")
                time.sleep(self.sample_interval)

    def _collect_metrics(self) -> None:
        """Collect current metrics sample."""
        now = datetime.now()

        # Calculate metrics
        keystroke_rate = self._calculate_keystroke_rate()
        error_rate = self._calculate_error_rate()
        context_switches = self._calculate_context_switches()
        pause_duration = (now - self._last_activity).total_seconds()

        # Calculate focus score
        focus_score = self._calculate_focus_score(
            keystroke_rate, error_rate, context_switches, pause_duration
        )

        # Classify attention state
        attention_state = self._classify_attention_state(
            keystroke_rate, error_rate, context_switches, pause_duration, focus_score
        )

        # Create metrics object
        metrics = AttentionMetrics(
            timestamp=now,
            keystroke_rate=keystroke_rate,
            error_rate=error_rate,
            context_switches=context_switches,
            pause_duration=pause_duration,
            focus_score=focus_score,
            attention_state=attention_state,
        )

        # Store metrics
        self._metrics_history.append(metrics)

        # Update state tracking
        self._update_state_tracking(attention_state, now)

        # Notify callbacks
        for callback in self._callbacks:
            try:
                callback(metrics)
            except Exception as e:
                console.print(f"[yellow]Callback error: {e}[/yellow]")

    def _calculate_keystroke_rate(self) -> float:
        """Calculate current keystroke rate (keys per minute)."""
        now = datetime.now()
        cutoff = now - timedelta(seconds=60)

        # Count keystrokes in last minute
        recent_keystrokes = sum(1 for ts in self._keystroke_buffer if ts > cutoff)
        return recent_keystrokes  # Already per minute

    def _calculate_error_rate(self) -> float:
        """Calculate current error rate (errors per minute)."""
        now = datetime.now()
        cutoff = now - timedelta(seconds=60)

        # Count errors in last minute
        recent_errors = sum(1 for ts in self._error_buffer if ts > cutoff)
        return recent_errors

    def _calculate_context_switches(self) -> int:
        """Calculate context switches in last sample period."""
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.sample_interval)

        # Count switches in current sample period
        recent_switches = sum(1 for ts in self._context_switch_buffer if ts > cutoff)
        return recent_switches

    def _calculate_focus_score(
        self,
        keystroke_rate: float,
        error_rate: float,
        context_switches: int,
        pause_duration: float,
    ) -> float:
        """Calculate normalized focus score (0-1)."""
        # Base score from activity level
        activity_score = min(keystroke_rate / 60, 1.0)  # Normalize to 60 keys/min max

        # Penalty for errors
        error_penalty = min(error_rate / 10, 0.5)  # Max 50% penalty for errors

        # Penalty for context switches
        switch_penalty = min(context_switches / 5, 0.3)  # Max 30% penalty for switches

        # Penalty for long pauses
        pause_penalty = (
            min(pause_duration / 300, 0.4) if pause_duration > 30 else 0
        )  # 5 min max

        # Calculate final score
        focus_score = activity_score - error_penalty - switch_penalty - pause_penalty
        return max(0, min(1, focus_score))

    def _classify_attention_state(
        self,
        keystroke_rate: float,
        error_rate: float,
        context_switches: int,
        pause_duration: float,
        focus_score: float,
    ) -> str:
        """Classify current attention state."""
        # Check for distraction (long pause)
        if pause_duration > 600:  # 10 minutes
            return AttentionState.DISTRACTED

        # Check for hyperfocus (sustained high activity)
        if (
            focus_score > 0.8
            and keystroke_rate > 30
            and self._state_duration > self.hyperfocus_duration * 60
        ):
            return AttentionState.HYPERFOCUS

        # Check for scattered attention (high context switches)
        if context_switches > self.context_switch_threshold:
            return AttentionState.SCATTERED

        # Check for focused state (high focus score, low errors)
        if focus_score > self.focus_threshold and error_rate < 2:
            return AttentionState.FOCUSED

        # Default to normal
        return AttentionState.NORMAL

    def _update_state_tracking(self, new_state: str, timestamp: datetime) -> None:
        """Update attention state tracking."""
        if new_state != self._current_state:
            # State change
            self._current_state = new_state
            self._state_duration = 0

            # Track focus sessions
            if new_state == AttentionState.FOCUSED:
                self._focus_session_start = timestamp
            elif self._focus_session_start:
                # Focus session ended
                focus_duration = (
                    timestamp - self._focus_session_start
                ).total_seconds() / 60
                self._log_focus_session(focus_duration)
                self._focus_session_start = None

            console.print(f"[blue]Attention state: {new_state}[/blue]")
        else:
            # Same state, increment duration
            self._state_duration += self.sample_interval

    def _log_focus_session(self, duration: float) -> None:
        """Log completed focus session."""
        if duration > 5:  # Only log sessions > 5 minutes
            session_log = {
                "duration_minutes": duration,
                "timestamp": datetime.now().isoformat(),
                "quality_score": self._calculate_session_quality(),
            }

            log_file = self.data_dir / "focus_sessions.jsonl"
            with open(log_file, "a") as f:
                f.write(json.dumps(session_log) + "\n")

    def _calculate_session_quality(self) -> float:
        """Calculate quality score for completed focus session."""
        if not self._metrics_history:
            return 0.5

        # Average focus score during session
        recent_metrics = list(self._metrics_history)[-20:]  # Last 20 samples
        avg_focus = sum(m.focus_score for m in recent_metrics) / len(recent_metrics)
        return avg_focus

    def _calculate_productivity_score(self) -> float:
        """Calculate overall productivity score for session."""
        if not self._metrics_history:
            return 0.5

        metrics_list = list(self._metrics_history)

        # Factors for productivity
        avg_focus = sum(m.focus_score for m in metrics_list) / len(metrics_list)
        focused_time_ratio = sum(
            1 for m in metrics_list if m.attention_state == AttentionState.FOCUSED
        ) / len(metrics_list)
        low_error_ratio = sum(1 for m in metrics_list if m.error_rate < 2) / len(
            metrics_list
        )

        # Weighted score
        productivity = (
            avg_focus * 0.4 + focused_time_ratio * 0.4 + low_error_ratio * 0.2
        )
        return productivity

    def _generate_recommendations(self) -> List[str]:
        """Generate ADHD-specific recommendations."""
        recommendations = []
        current_metrics = self.get_current_metrics()

        if current_metrics["attention_state"] == AttentionState.SCATTERED:
            recommendations.extend(
                [
                    "Consider taking a short break to reset focus",
                    "Try working on a single file for the next 25 minutes",
                    "Enable 'Do Not Disturb' mode to reduce distractions",
                ]
            )

        elif current_metrics["attention_state"] == AttentionState.HYPERFOCUS:
            recommendations.extend(
                [
                    "You've been in deep focus for a while - consider a break",
                    "Remember to hydrate and look away from the screen",
                    "Set a timer for the next 15 minutes to check in",
                ]
            )

        elif current_metrics["focus_score"] < 0.5:
            recommendations.extend(
                [
                    "Low focus detected - try the Pomodoro technique",
                    "Consider changing your environment or taking a walk",
                    "Break current task into smaller, more manageable pieces",
                ]
            )

        elif current_metrics["session_duration"] > 90:
            recommendations.append(
                "Long session detected - consider taking a longer break"
            )

        return recommendations

    def _save_session_metrics(self) -> None:
        """Save session metrics to file."""
        session_data = {
            "session_start": self._session_start.isoformat(),
            "session_end": datetime.now().isoformat(),
            "summary": self.get_session_summary(),
            "total_samples": len(self._metrics_history),
        }

        session_file = (
            self.data_dir / f'session_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        )
        with open(session_file, "w") as f:
            json.dump(session_data, f, indent=2)

    def _get_default_metrics(self) -> Dict[str, Any]:
        """Get default metrics when no data available."""
        return {
            "attention_state": AttentionState.NORMAL,
            "focus_score": 0.5,
            "session_duration": 0,
            "keystroke_rate": 0,
            "error_rate": 0,
            "context_switches": 0,
            "state_duration": 0,
            "monitoring_active": self._monitoring,
        }
