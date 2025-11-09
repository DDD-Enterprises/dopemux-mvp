"""
ADHD Predictive Engine

Makes predictions about future ADHD states based on learned patterns.
Enables proactive (not just reactive) ADHD accommodations.

IP-005 Days 11-12: Machine Learning Component 2/2
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

try:
    from adhd_engine.models import EnergyLevel, AttentionState
    from adhd_engine.ml.pattern_learner import (
        ADHDPatternLearner,
        EnergyPattern,
        AttentionPattern,
        BreakPattern,
    )
except ImportError:  # pragma: no cover - fallback for script execution
    from models import EnergyLevel, AttentionState  # type: ignore
    from .pattern_learner import (  # type: ignore
        ADHDPatternLearner,
        EnergyPattern,
        AttentionPattern,
        BreakPattern,
    )

logger = logging.getLogger(__name__)


class PredictiveADHDEngine:
    """
    Predictive ADHD accommodation engine.

    Uses learned patterns to predict:
    - Energy levels based on time/day patterns
    - Attention states based on session context
    - Optimal break timing based on effectiveness patterns

    All predictions include confidence scores for transparency and
    fallback decision-making.

    Features:
    - Pattern-based prediction (not rule-based)
    - Confidence scoring for all predictions
    - Human-readable explanations
    - Graceful degradation (low confidence → fallback to rules)
    """

    def __init__(self, workspace_id: str):
        """
        Initialize predictive engine.

        Args:
            workspace_id: Workspace path for pattern loading
        """
        self.workspace_id = workspace_id
        self.pattern_learner = ADHDPatternLearner(workspace_id)

        # Minimum confidence threshold for using predictions
        self.min_prediction_confidence = 0.5  # Below this, fallback to rules

        # Pattern cache (loaded on demand)
        self._pattern_cache: Dict[str, Dict[str, List]] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self._cache_ttl_minutes = 15  # Refresh patterns every 15 minutes

    async def predict_energy_level(
        self,
        user_id: str,
        current_time: Optional[datetime] = None
    ) -> Tuple[str, float, str]:
        """
        Predict energy level based on time/day patterns.

        Args:
            user_id: User identifier
            current_time: Time to predict for (defaults to now)

        Returns:
            Tuple of (predicted_energy_level, confidence, explanation)

        Example:
            ("LOW", 0.73, "Based on 47 observations, you typically have LOW energy at 2pm on Mondays")
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)

        # Load patterns (with caching)
        patterns = await self._get_cached_patterns(user_id)
        energy_patterns: List[EnergyPattern] = patterns.get("energy", [])

        if not energy_patterns:
            logger.warning(f"No energy patterns found for user {user_id}, cannot predict")
            return (EnergyLevel.MEDIUM.value, 0.0, "No historical data available for prediction")

        # Find matching patterns for current time/day
        hour = current_time.hour
        day_of_week = current_time.weekday()  # 0=Monday, 6=Sunday

        # Exact match first
        exact_matches = [
            p for p in energy_patterns
            if p.time_of_day == hour and p.day_of_week == day_of_week
        ]

        if exact_matches:
            # Use highest confidence exact match
            best_match = max(exact_matches, key=lambda p: p.confidence)
            explanation = (
                f"Based on {best_match.sample_count} observations over the past weeks, "
                f"you typically have {best_match.energy_level} energy at "
                f"{hour}:00 on {self._day_name(day_of_week)}s"
            )
            return (best_match.energy_level, best_match.confidence, explanation)

        # Fallback: Same hour, any day (time-of-day pattern)
        time_matches = [
            p for p in energy_patterns
            if p.time_of_day == hour
        ]

        if time_matches:
            # Weighted average by confidence
            energy_votes: Dict[str, float] = {}
            total_weight = 0.0

            for pattern in time_matches:
                weight = pattern.confidence
                if pattern.energy_level not in energy_votes:
                    energy_votes[pattern.energy_level] = 0.0
                energy_votes[pattern.energy_level] += weight
                total_weight += weight

            predicted_energy = max(energy_votes, key=energy_votes.get)
            confidence = energy_votes[predicted_energy] / total_weight if total_weight > 0 else 0.0

            # Reduce confidence for cross-day generalization
            confidence *= 0.7

            total_samples = sum(p.sample_count for p in time_matches)
            explanation = (
                f"Based on {total_samples} observations at {hour}:00 across different days, "
                f"you typically have {predicted_energy} energy at this time"
            )
            return (predicted_energy, confidence, explanation)

        # No patterns found
        return (
            EnergyLevel.MEDIUM.value,
            0.0,
            f"No patterns found for {hour}:00 - need more historical data"
        )

    async def predict_attention_state(
        self,
        user_id: str,
        session_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, float, str]:
        """
        Predict attention state based on session context.

        Args:
            user_id: User identifier
            session_context: Context about current session (time_of_day, session_duration, etc.)

        Returns:
            Tuple of (predicted_attention_state, confidence, explanation)

        Example:
            ("FOCUSED", 0.68, "After 25-minute warmup, you typically achieve FOCUSED state for afternoon sessions")
        """
        if session_context is None:
            session_context = {}

        # Load patterns
        patterns = await self._get_cached_patterns(user_id)
        attention_patterns: List[AttentionPattern] = patterns.get("attention", [])

        if not attention_patterns:
            logger.warning(f"No attention patterns found for user {user_id}, cannot predict")
            return (
                AttentionState.FOCUSED.value,
                0.0,
                "No historical session data available for prediction"
            )

        # Determine session type from context or current time
        session_type = session_context.get('session_type')
        if not session_type:
            current_hour = datetime.now(timezone.utc).hour
            if 6 <= current_hour < 12:
                session_type = "morning"
            elif 12 <= current_hour < 18:
                session_type = "afternoon"
            else:
                session_type = "evening"

        # Find matching pattern
        matching_patterns = [
            p for p in attention_patterns
            if p.session_type == session_type
        ]

        if not matching_patterns:
            # Fallback to any pattern
            if attention_patterns:
                pattern = max(attention_patterns, key=lambda p: p.confidence)
                confidence = pattern.confidence * 0.6  # Reduce for cross-session generalization
            else:
                return (
                    AttentionState.FOCUSED.value,
                    0.0,
                    f"No patterns found for {session_type} sessions"
                )
        else:
            pattern = max(matching_patterns, key=lambda p: p.confidence)
            confidence = pattern.confidence

        # Predict attention state based on session progress
        session_minutes = session_context.get('session_minutes_elapsed', 0)

        if session_minutes < pattern.warmup_minutes:
            # Still in warmup
            predicted_state = AttentionState.TRANSITIONING.value
            explanation = (
                f"You typically need {pattern.warmup_minutes} minutes to reach peak focus "
                f"in {session_type} sessions. Currently {session_minutes} minutes in."
            )
        elif session_minutes < (pattern.warmup_minutes + pattern.peak_duration_minutes):
            # In peak focus period
            predicted_state = AttentionState.FOCUSED.value
            explanation = (
                f"Based on {pattern.sample_count} {session_type} sessions, "
                f"you typically achieve FOCUSED state after {pattern.warmup_minutes}-minute warmup "
                f"and maintain it for {pattern.peak_duration_minutes} minutes"
            )
        else:
            # Beyond peak, likely declining
            predicted_state = AttentionState.SCATTERED.value
            explanation = (
                f"Your optimal {session_type} session length is {pattern.optimal_session_length} minutes. "
                f"Consider taking a break to maintain productivity."
            )
            confidence *= 0.8  # Reduce confidence for fatigue prediction

        return (predicted_state, confidence, explanation)

    async def predict_optimal_break_timing(
        self,
        user_id: str,
        minutes_since_break: Optional[int] = None
    ) -> Tuple[int, float, str]:
        """
        Predict optimal break timing for user.

        Args:
            user_id: User identifier
            minutes_since_break: Minutes elapsed since last break

        Returns:
            Tuple of (minutes_until_recommended_break, confidence, explanation)

        Example:
            (25, 0.71, "Based on your patterns, you're most productive with 45-minute work intervals")
        """
        # Load patterns
        patterns = await self._get_cached_patterns(user_id)
        break_patterns: List[BreakPattern] = patterns.get("breaks", [])

        if not break_patterns:
            logger.warning(f"No break patterns found for user {user_id}, cannot predict")
            return (
                45,  # Default 45-minute interval
                0.0,
                "No historical break data available - using default 45-minute interval"
            )

        # Find most effective break pattern
        best_pattern = max(break_patterns, key=lambda p: p.effectiveness_score * p.confidence)

        if minutes_since_break is None:
            # No current session info - return optimal frequency
            minutes_until_break = best_pattern.frequency_minutes
            explanation = (
                f"Based on {best_pattern.sample_count} break cycles, "
                f"you're most productive with {best_pattern.frequency_minutes}-minute work intervals "
                f"followed by {best_pattern.duration_minutes}-minute breaks "
                f"(effectiveness: {best_pattern.effectiveness_score:.0%})"
            )
        else:
            # Calculate time until next recommended break
            minutes_until_break = max(0, best_pattern.frequency_minutes - minutes_since_break)

            if minutes_until_break == 0:
                explanation = (
                    f"Break recommended now! "
                    f"Your optimal work interval is {best_pattern.frequency_minutes} minutes. "
                    f"Take a {best_pattern.duration_minutes}-minute break for best productivity."
                )
            else:
                explanation = (
                    f"Recommend break in {minutes_until_break} minutes "
                    f"({best_pattern.frequency_minutes}-minute optimal interval). "
                    f"Break duration: {best_pattern.duration_minutes} minutes."
                )

        return (minutes_until_break, best_pattern.confidence, explanation)

    def get_prediction_explanation(
        self,
        user_id: str,
        prediction_type: str,
        predicted_value: str,
        confidence: float,
        sample_count: int = 0
    ) -> str:
        """
        Generate human-readable explanation of prediction.

        Args:
            user_id: User identifier
            prediction_type: "energy", "attention", or "break"
            predicted_value: Predicted value
            confidence: Prediction confidence
            sample_count: Number of observations used

        Returns:
            Human-readable explanation string
        """
        if confidence < self.min_prediction_confidence:
            return (
                f"Low confidence prediction ({confidence:.0%}). "
                f"Need more data for reliable {prediction_type} predictions. "
                f"Using rule-based fallback instead."
            )

        confidence_label = self._confidence_label(confidence)

        if prediction_type == "energy":
            return (
                f"{confidence_label} prediction: {predicted_value} energy level "
                f"(based on {sample_count} observations, {confidence:.0%} confidence)"
            )
        elif prediction_type == "attention":
            return (
                f"{confidence_label} prediction: {predicted_value} attention state "
                f"(based on session patterns, {confidence:.0%} confidence)"
            )
        elif prediction_type == "break":
            return (
                f"{confidence_label} recommendation: Break timing optimized from "
                f"{sample_count} break cycles ({confidence:.0%} confidence)"
            )
        else:
            return f"Prediction: {predicted_value} (confidence: {confidence:.0%})"

    async def _get_cached_patterns(self, user_id: str) -> Dict[str, List]:
        """
        Get patterns with caching (15-minute TTL).

        Args:
            user_id: User identifier

        Returns:
            Dictionary with "energy", "attention", "breaks" pattern lists
        """
        current_time = datetime.now(timezone.utc)

        # Check cache freshness
        if user_id in self._cache_timestamps:
            age_minutes = (current_time - self._cache_timestamps[user_id]).total_seconds() / 60
            if age_minutes < self._cache_ttl_minutes and user_id in self._pattern_cache:
                # Use cached patterns
                return self._pattern_cache[user_id]

        # Refresh patterns from ConPort
        patterns = await self.pattern_learner.load_patterns_from_conport(user_id)
        self._pattern_cache[user_id] = patterns
        self._cache_timestamps[user_id] = current_time

        return patterns

    def _confidence_label(self, confidence: float) -> str:
        """Get human-readable confidence label."""
        if confidence >= 0.9:
            return "Very high confidence"
        elif confidence >= 0.7:
            return "High confidence"
        elif confidence >= 0.5:
            return "Moderate confidence"
        else:
            return "Low confidence"

    def _day_name(self, day_of_week: int) -> str:
        """Convert day number to name."""
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        return days[day_of_week]
