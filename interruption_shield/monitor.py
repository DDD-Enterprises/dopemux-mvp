#!/usr/bin/env python3
"""
Productivity Monitor for False Positive Detection

Monitors user productivity over a 15-minute window to prevent
deactivation of interruption shields during productive work.

ADHD Optimization:
- 15-minute monitoring window (matches ADHD focus cycles)
- Graceful degradation when monitoring unavailable
- Multiple productivity signals for accuracy
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import deque

logger = logging.getLogger(__name__)

@dataclass
class ProductivitySample:
    """Single productivity measurement"""
    timestamp: datetime
    keystrokes: int = 0
    mouse_movements: int = 0
    window_switches: int = 0
    application_focus_time: float = 0.0  # seconds
    score: float = 0.0  # 0.0 to 1.0

@dataclass
class ProductivityMetrics:
    """Aggregated productivity metrics"""
    samples: deque = field(default_factory=lambda: deque(maxlen=100))
    average_score: float = 0.0
    trend_direction: str = "stable"  # increasing, decreasing, stable
    confidence: float = 0.0  # 0.0 to 1.0

class ProductivityMonitor:
    """
    Monitors user productivity to detect false positives in shield deactivation.

    Tracks multiple productivity signals:
    - Keystroke frequency
    - Mouse activity
    - Application focus time
    - Window switching patterns
    """

    def __init__(self, window_minutes: int = 15, threshold: float = 0.7):
        """
        Initialize productivity monitor

        Args:
            window_minutes: Monitoring window duration
            threshold: Minimum productivity score to avoid false positive
        """
        self.window_minutes = window_minutes
        self.threshold = threshold
        self.metrics = ProductivityMetrics()

        # Monitoring state
        self.is_monitoring = False
        self.monitor_task: Optional[asyncio.Task] = None

        # Baseline calibration
        self.baseline_samples = 5
        self.baseline_calibrated = False

    async def start_monitoring(self):
        """Start productivity monitoring"""
        if self.is_monitoring:
            logger.warning("Productivity monitoring already active")
            return

        logger.info(f"📊 Starting productivity monitoring ({self.window_minutes}min window)")
        self.is_monitoring = True
        self.monitor_task = asyncio.create_task(self._monitor_loop())

    async def stop_monitoring(self):
        """Stop productivity monitoring"""
        if self.is_monitoring:
            logger.info("📊 Stopping productivity monitoring")
            self.is_monitoring = False

            if self.monitor_task:
                self.monitor_task.cancel()
                try:
                    await self.monitor_task
                except asyncio.CancelledError:
                    pass
                self.monitor_task = None

    async def get_current_productivity(self) -> float:
        """
        Get current productivity score (0.0 to 1.0)

        Returns:
            Productivity score where:
            - 0.0 = no activity
            - 0.5 = baseline activity
            - 1.0 = high productivity
        """
        if not self.metrics.samples:
            return 0.0

        # Calculate weighted average of recent samples
        recent_samples = [s for s in self.metrics.samples
                         if (datetime.now() - s.timestamp).seconds < (self.window_minutes * 60)]

        if not recent_samples:
            return 0.0

        weights = []
        scores = []

        for sample in recent_samples:
            # Weight recent samples more heavily
            age_seconds = (datetime.now() - sample.timestamp).seconds
            weight = max(0.1, 1.0 - (age_seconds / (self.window_minutes * 60)))
            weights.append(weight)
            scores.append(sample.score)

        if not weights:
            return 0.0

        # Weighted average
        total_weight = sum(weights)
        weighted_score = sum(w * s for w, s in zip(weights, scores)) / total_weight

        return min(1.0, max(0.0, weighted_score))

    async def is_productive_enough(self) -> bool:
        """Check if current productivity exceeds the threshold"""
        current = await self.get_current_productivity()
        return current >= self.threshold

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of productivity metrics"""
        return {
            "is_monitoring": self.is_monitoring,
            "current_productivity": self.metrics.average_score,
            "trend": self.metrics.trend_direction,
            "confidence": self.metrics.confidence,
            "samples_count": len(self.metrics.samples),
            "window_minutes": self.window_minutes,
            "threshold": self.threshold,
            "baseline_calibrated": self.baseline_calibrated
        }

    async def _monitor_loop(self):
        """Main monitoring loop"""
        try:
            while self.is_monitoring:
                try:
                    # Collect productivity sample
                    sample = await self._collect_productivity_sample()

                    # Add to metrics
                    self.metrics.samples.append(sample)

                    # Update rolling averages
                    await self._update_metrics()

                    # Log significant changes
                    if sample.score > 0.8:
                        logger.debug(f"📊 High productivity detected: {sample.score:.2f}")
                    elif sample.score < 0.2:
                        logger.debug(f"📊 Low productivity detected: {sample.score:.2f}")

                except Exception as e:
                    logger.error(f"Error in monitoring loop: {e}")

                # Sample every 30 seconds
                await asyncio.sleep(30)

        except asyncio.CancelledError:
            logger.info("📊 Monitoring loop cancelled")
            raise

    async def _collect_productivity_sample(self) -> ProductivitySample:
        """Collect a single productivity sample"""
        start_time = time.time()

        # Collect various productivity signals
        keystrokes = await self._count_keystrokes()
        mouse_movements = await self._count_mouse_movements()
        window_switches = await self._count_window_switches()
        focus_time = await self._measure_focus_time()

        collection_time = time.time() - start_time

        # Calculate productivity score (0.0 to 1.0)
        score = self._calculate_productivity_score(
            keystrokes, mouse_movements, window_switches, focus_time, collection_time
        )

        return ProductivitySample(
            timestamp=datetime.now(),
            keystrokes=keystrokes,
            mouse_movements=mouse_movements,
            window_switches=window_switches,
            application_focus_time=focus_time,
            score=score
        )

    async def _count_keystrokes(self) -> int:
        """Count keystrokes in the last 30 seconds"""
        try:
            # This would integrate with system input monitoring
            # For now, return a mock value based on system activity
            import platform
            system = platform.system()

            if system == "Darwin":
                # macOS: could use Quartz events or similar
                return 42  # Mock value
            elif system == "Linux":
                # Linux: could read from /dev/input
                return 38  # Mock value
            elif system == "Windows":
                # Windows: could use GetAsyncKeyState
                return 45  # Mock value
            else:
                return 0

        except Exception:
            return 0

    async def _count_mouse_movements(self) -> int:
        """Count mouse movements in the last 30 seconds"""
        try:
            # This would track mouse position changes
            # For now, return mock values
            import platform
            system = platform.system()

            if system in ["Darwin", "Linux", "Windows"]:
                return 156  # Mock value - active mouse movement
            else:
                return 0

        except Exception:
            return 0

    async def _count_window_switches(self) -> int:
        """Count application/window switches in the last 30 seconds"""
        try:
            # This would track window focus changes
            # For now, return mock values (low = focused work)
            return 2  # Mock value - occasional switches

        except Exception:
            return 0

    async def _measure_focus_time(self) -> float:
        """Measure time spent focused on current application"""
        try:
            # This would measure continuous focus time
            # For now, return mock values
            return 25.0  # Mock value - 25 seconds focused

        except Exception:
            return 0.0

    def _calculate_productivity_score(self, keystrokes: int, mouse: int,
                                    switches: int, focus_time: float,
                                    collection_time: float) -> float:
        """
        Calculate productivity score from collected signals

        Formula considers:
        - Keystroke frequency (writing/coding activity)
        - Mouse activity (navigation/interaction)
        - Window switches (context switching - negative)
        - Focus time (continuous attention)
        """

        # Normalize inputs to 0-1 scale
        keystroke_score = min(1.0, keystrokes / 100.0)  # 100+ keystrokes = very active
        mouse_score = min(1.0, mouse / 500.0)          # 500+ movements = very active
        focus_score = min(1.0, focus_time / 30.0)      # 30+ seconds focused = good

        # Window switches are negative (more switches = less productive)
        switch_penalty = min(0.5, switches / 10.0)     # 10+ switches = significant penalty

        # Weighted combination
        # Keystrokes: 40% (primary coding indicator)
        # Focus time: 30% (attention span)
        # Mouse: 20% (interaction)
        # Switches: -10% (penalty)
        raw_score = (
            keystroke_score * 0.4 +
            focus_score * 0.3 +
            mouse_score * 0.2 -
            switch_penalty * 0.1
        )

        # Ensure bounds and calibrate
        score = max(0.0, min(1.0, raw_score))

        # Apply baseline calibration if available
        if self.baseline_calibrated and len(self.metrics.samples) >= self.baseline_samples:
            baseline_avg = sum(s.score for s in list(self.metrics.samples)[-self.baseline_samples:]) / self.baseline_samples
            # Adjust score relative to baseline (prevents false high scores)
            score = max(0.0, score - (baseline_avg * 0.2))

        return score

    async def _update_metrics(self):
        """Update rolling metrics and detect trends"""
        if len(self.metrics.samples) < 2:
            return

        # Calculate average score
        recent_scores = [s.score for s in self.metrics.samples]
        self.metrics.average_score = sum(recent_scores) / len(recent_scores)

        # Detect trend (simple linear regression slope)
        if len(recent_scores) >= 3:
            n = len(recent_scores)
            x = list(range(n))
            y = recent_scores

            # Simple slope calculation
            x_mean = sum(x) / n
            y_mean = sum(y) / n

            numerator = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, y))
            denominator = sum((xi - x_mean) ** 2 for xi in x)

            if denominator > 0:
                slope = numerator / denominator
                if slope > 0.01:
                    self.metrics.trend_direction = "increasing"
                elif slope < -0.01:
                    self.metrics.trend_direction = "decreasing"
                else:
                    self.metrics.trend_direction = "stable"

        # Calculate confidence based on sample consistency
        if len(recent_scores) >= 5:
            mean = sum(recent_scores) / len(recent_scores)
            variance = sum((s - mean) ** 2 for s in recent_scores) / len(recent_scores)
            std_dev = variance ** 0.5

            # Confidence = 1 - (std_dev / mean) normalized to 0-1
            if mean > 0:
                confidence = 1.0 - min(1.0, std_dev / mean)
                self.metrics.confidence = max(0.0, confidence)
            else:
                self.metrics.confidence = 0.0

        # Mark baseline as calibrated
        if not self.baseline_calibrated and len(self.metrics.samples) >= self.baseline_samples:
            self.baseline_calibrated = True
            logger.info("📊 Productivity baseline calibrated")