"""
F-NEW-8: Proactive Break Suggestion Engine

Prevents ADHD burnout by detecting high cognitive load patterns and
suggesting breaks BEFORE exhaustion occurs.

Architecture:
- EventBus consumer (complexity, cognitive state, duration events)
- Correlation engine (detects burnout risk patterns)
- Gentle suggestion delivery (non-intrusive)

ADHD Impact: CRITICAL
- Prevents burnout before it happens
- Proactive vs reactive support
- Personalized to individual patterns

Based on Zen thinkdeep design (Decision #313)
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from collections import deque
from statistics import mean, stdev

logger = logging.getLogger(__name__)


@dataclass
class BreakSuggestion:
    """Proactive break suggestion with context."""
    priority: str  # low, medium, high, critical
    message: str
    reason: str
    suggested_duration: int  # minutes
    triggered_by: List[str]  # Event types that triggered this
    timestamp: datetime
    workspace_path: Optional[str] = None  # Multi-workspace tracking


@dataclass
class CognitiveLoadWindow:
    """Sliding window of cognitive load indicators."""
    window_minutes: int = 25  # Pomodoro standard
    complexity_events: deque = None
    cognitive_states: deque = None
    session_start: Optional[datetime] = None
    last_break: Optional[datetime] = None

    def __post_init__(self):
        if self.complexity_events is None:
            self.complexity_events = deque(maxlen=10)  # Last 10 events
        if self.cognitive_states is None:
            self.cognitive_states = deque(maxlen=10)


@dataclass
class CognitiveLoadPrediction:
    """Prediction of future cognitive load with confidence."""
    predicted_load: float  # 0.0-1.0 scale
    confidence: float  # 0.0-1.0 scale
    time_horizon: int  # minutes ahead
    reason: str  # why this prediction
    factors: List[str]  # contributing factors
    timestamp: datetime


@dataclass
class HistoricalPattern:
    """Learned pattern from historical data."""
    pattern_type: str  # 'complexity_trend', 'energy_cycle', 'attention_drop'
    confidence: float  # 0.0-1.0 based on historical accuracy
    trigger_conditions: List[str]  # when this pattern applies
    prediction: str  # what it predicts
    last_updated: datetime


class BreakSuggestionEngine:
    """
    Proactive break suggestion engine using event correlation.

    Monitors:
    - High complexity code work (Serena events)
    - Cognitive state changes (ADHD Engine events)
    - Session duration (time tracking)
    - Break history

    Suggests breaks when:
    - Sustained high complexity work (3+ events in 25 min)
    - Cognitive decline detected (energy dropping, attention scattered)
    - Time threshold exceeded (>25 min since break)
    - Combination of above indicates burnout risk
    """

    def __init__(self, user_id: str = "default", event_bus = None):
        """
        Initialize break suggestion engine with prediction capabilities.

        Args:
            user_id: User identifier for personalization
            event_bus: Optional EventBus for emitting break suggestions
        """
        self.user_id = user_id
        self.event_bus = event_bus
        self.cognitive_window = CognitiveLoadWindow()

        # Thresholds (configurable, ADHD-optimized)
        self.complexity_event_threshold = 3  # 3+ high complexity events
        self.window_minutes = 25  # Sliding window size
        self.min_session_duration = 25  # Minutes before suggesting breaks
        self.min_break_interval = 25  # Minutes between break suggestions

        # Prediction settings
        self.prediction_enabled = True
        self.prediction_horizon = 15  # minutes ahead to predict
        self.prediction_threshold = 0.7  # confidence level to trigger proactive suggestions

        # State
        self.last_suggestion: Optional[datetime] = None
        self.suggestion_history: deque = deque(maxlen=10)

        # Prediction state
        self.historical_patterns: Dict[str, HistoricalPattern] = {}
        self.prediction_history: deque = deque(maxlen=20)  # Keep last 20 predictions
        self.conport_client = None  # Will be initialized if available

        # ADHD personalization
        self.gentle_mode = True  # Use gentle language
        self.celebration_mode = True  # Celebrate break adherence

        # Metrics
        self.suggestions_emitted = 0
        self.predictions_made = 0
        self.accurate_predictions = 0  # For tracking prediction accuracy

    async def _predict_cognitive_load(self) -> Optional[CognitiveLoadPrediction]:
        """
        Predict future cognitive load based on current trends and historical patterns.

        Uses simple statistical analysis and pattern recognition to forecast
        when cognitive overload is likely to occur.

        Returns:
            CognitiveLoadPrediction if prediction confidence is high enough, None otherwise
        """
        if not self.prediction_enabled:
            return None

        now = datetime.now(timezone.utc)

        # Gather current indicators
        factors = []
        predicted_load = 0.0
        confidence = 0.0

        # Factor 1: Complexity trend analysis
        complexity_scores = [e['score'] for e in self.cognitive_window.complexity_events
                           if e['timestamp'] > now - timedelta(minutes=self.window_minutes)]

        if complexity_scores:
            avg_complexity = mean(complexity_scores)
            factors.append(f"complexity_trend_{avg_complexity:.2f}")

            # High complexity suggests future overload
            if avg_complexity > 0.6:
                predicted_load += 0.4
                confidence += 0.3
            elif avg_complexity > 0.4:
                predicted_load += 0.2
                confidence += 0.2

        # Factor 2: Cognitive state trends
        if self.cognitive_window.cognitive_states:
            recent_states = list(self.cognitive_window.cognitive_states)[-3:]  # Last 3 states
            energy_trend = [s['energy'] for s in recent_states]
            attention_trend = [s['attention'] for s in recent_states]

            # Check for declining energy
            if 'low' in energy_trend[-2:]:  # Low energy in last 2 states
                predicted_load += 0.3
                confidence += 0.3
                factors.append("energy_declining")

            # Check for deteriorating attention
            if 'scattered' in attention_trend[-2:] or 'transitioning' in attention_trend[-2:]:
                predicted_load += 0.3
                confidence += 0.2
                factors.append("attention_deteriorating")

        # Factor 3: Session duration without breaks
        if self.cognitive_window.session_start and not self.cognitive_window.last_break:
            session_duration = (now - self.cognitive_window.session_start).total_seconds() / 60
            if session_duration > self.min_session_duration:
                predicted_load += 0.2
                confidence += 0.2
                factors.append(f"long_session_{session_duration:.0f}min")

        # Factor 4: Historical pattern analysis (if ConPort available)
        if self.conport_client:
            try:
                patterns = await self.conport_client.get_task_completion_patterns(self.user_id)
                # Simple pattern: if high complexity tasks recently completed, predict fatigue
                if patterns.get('completion_rate', 0) < 0.7:
                    predicted_load += 0.2
                    confidence += 0.1
                    factors.append("recent_task_failures")
            except Exception as e:
                logger.debug(f"Could not get ConPort patterns: {e}")

        # Only return prediction if confidence is sufficient
        if confidence >= 0.4:  # Minimum confidence threshold
            prediction = CognitiveLoadPrediction(
                predicted_load=min(predicted_load, 1.0),  # Cap at 1.0
                confidence=min(confidence, 1.0),
                time_horizon=self.prediction_horizon,
                reason=f"Predicted cognitive load based on {len(factors)} indicators",
                factors=factors,
                timestamp=now
            )

            self.prediction_history.append(prediction)
            self.predictions_made += 1

            logger.debug(f"Made cognitive load prediction: load={prediction.predicted_load:.2f}, confidence={prediction.confidence:.2f}")
            return prediction

        return None

    def _create_proactive_suggestion(self, prediction: CognitiveLoadPrediction) -> BreakSuggestion:
        """
        Create a proactive break suggestion based on cognitive load prediction.

        Args:
            prediction: The cognitive load prediction

        Returns:
            BreakSuggestion with proactive context
        """
        # Determine suggestion priority based on predicted load
        if prediction.predicted_load > 0.8:
            priority = "high"
            duration = 15  # Longer break needed
        elif prediction.predicted_load > 0.6:
            priority = "medium"
            duration = 10
        else:
            priority = "low"
            duration = 5

        # Create ADHD-friendly message
        factors_text = ", ".join(prediction.factors[:3])  # Show top 3 factors
        message = f"I notice some patterns suggesting you might benefit from a short break soon ({factors_text}). Consider taking {duration} minutes to recharge."

        if self.gentle_mode:
            message = f"You're doing great! Based on recent patterns, a {duration}-minute break might help maintain your focus."

        suggestion = BreakSuggestion(
            priority=priority,
            message=message,
            reason=f"Proactive prediction: {prediction.reason}",
            suggested_duration=duration,
            triggered_by=["cognitive_load_prediction"],
            timestamp=datetime.now(timezone.utc)
        )

        # Track metrics
        self.suggestions_emitted += 1
        self.last_suggestion = suggestion.timestamp
        self.suggestion_history.append(suggestion)

        return suggestion

    async def on_complexity_event(self, event: Dict):
        """
        Handle high complexity code event from Serena.

        Args:
            event: {
                'type': 'code.complexity.high',
                'file_path': str,
                'complexity_score': float,
                'timestamp': str
            }
        """
        timestamp = datetime.fromisoformat(event.get('timestamp', datetime.now().isoformat()))

        # Add to sliding window
        self.cognitive_window.complexity_events.append({
            'file': event.get('file_path'),
            'score': event.get('complexity_score', 0.6),
            'timestamp': timestamp
        })

        logger.debug(f"Complexity event: {event.get('file_path')} ({event.get('complexity_score')})")

        # Check if suggestion needed (returns suggestion if triggered)
        suggestion = await self._evaluate_suggestion_triggers()
        if suggestion:
            logger.info(f"Break suggestion from complexity event: {suggestion.message}")
        return suggestion

    async def on_cognitive_state_change(self, event: Dict):
        """
        Handle cognitive state change event from ADHD Engine.

        Args:
            event: {
                'type': 'cognitive.state.change',
                'energy_level': str,
                'attention_state': str,
                'timestamp': str
            }
        """
        timestamp = datetime.fromisoformat(event.get('timestamp', datetime.now().isoformat()))

        # Add to sliding window
        self.cognitive_window.cognitive_states.append({
            'energy': event.get('energy_level'),
            'attention': event.get('attention_state'),
            'timestamp': timestamp
        })

        logger.debug(f"Cognitive change: energy={event.get('energy_level')}, attention={event.get('attention_state')}")

        # Check if suggestion needed (returns suggestion if triggered)
        suggestion = await self._evaluate_suggestion_triggers()
        if suggestion:
            logger.info(f"Break suggestion from cognitive change: {suggestion.message}")
        return suggestion

    async def on_session_start(self, timestamp: Optional[datetime] = None):
        """Mark session start time."""
        self.cognitive_window.session_start = timestamp or datetime.now(timezone.utc)
        logger.info(f"Session started at {self.cognitive_window.session_start}")

    async def on_break_taken(self, timestamp: Optional[datetime] = None):
        """Mark break taken (resets suggestion timer)."""
        self.cognitive_window.last_break = timestamp or datetime.now(timezone.utc)

        if self.celebration_mode:
            logger.info(f"✅ Great job taking a break! Keep it up!")

    async def _evaluate_suggestion_triggers(self) -> Optional[BreakSuggestion]:
        """
        Evaluate if break suggestion should be triggered.

        Rules (ALL must be met):
        1. Sustained high complexity (3+ events in window)
        2. Cognitive decline (energy drop OR attention scattered)
        3. Time threshold (session > 25 min, last break > 25 min ago)
        4. Cooldown period (> 25 min since last suggestion)

        Returns:
            BreakSuggestion if triggered, None otherwise
        """
        now = datetime.now(timezone.utc)

        # Get events in current window
        window_start = now - timedelta(minutes=self.window_minutes)

        complexity_in_window = [
            e for e in self.cognitive_window.complexity_events
            if e['timestamp'] > window_start
        ]

        # Rule 1: Sustained high complexity?
        high_complexity = len(complexity_in_window) >= self.complexity_event_threshold

        if not high_complexity:
            # Check for proactive prediction even without current high complexity
            prediction = await self._predict_cognitive_load()
            if prediction and prediction.predicted_load > self.prediction_threshold:
                return self._create_proactive_suggestion(prediction)
            return None  # Not enough complexity events

        # Rule 2: Cognitive decline?
        cognitive_decline = False
        latest_state = None

        if self.cognitive_window.cognitive_states:
            latest_state = self.cognitive_window.cognitive_states[-1]
            energy = latest_state.get('energy', 'medium')
            attention = latest_state.get('attention', 'focused')

            # Decline indicators
            if energy == 'low':
                cognitive_decline = True
            if attention in ['scattered', 'transitioning']:
                cognitive_decline = True

        # For initial implementation: Don't require cognitive decline
        # (Time + Complexity is enough for first version)
        # Future: Make cognitive_decline required for non-critical suggestions

        # Rule 3: Time threshold?
        session_duration = None
        time_since_break = None

        if self.cognitive_window.session_start:
            session_duration = (now - self.cognitive_window.session_start).total_seconds() / 60

        if self.cognitive_window.last_break:
            time_since_break = (now - self.cognitive_window.last_break).total_seconds() / 60

        time_threshold_met = (
            (session_duration and session_duration > self.min_session_duration) or
            (time_since_break and time_since_break > self.min_break_interval)
        )

        if not time_threshold_met:
            return None  # Not enough time elapsed

        # Rule 4: Cooldown period?
        if self.last_suggestion:
            since_last = (now - self.last_suggestion).total_seconds() / 60
            if since_last < self.min_break_interval:
                return None  # Too soon since last suggestion

        # All rules met - generate suggestion!
        suggestion = await self._generate_suggestion(
            complexity_count=len(complexity_in_window),
            cognitive_state=latest_state if self.cognitive_window.cognitive_states else None,
            session_duration=session_duration,
            time_since_break=time_since_break
        )

        # Update state
        self.last_suggestion = now
        self.suggestion_history.append(suggestion)

        logger.info(f"⚠️ Break suggestion triggered: {suggestion.message}")

        return suggestion

    async def _generate_suggestion(
        self,
        complexity_count: int,
        cognitive_state: Optional[Dict],
        session_duration: Optional[float],
        time_since_break: Optional[float]
    ) -> BreakSuggestion:
        """
        Generate break suggestion with context.

        Args:
            complexity_count: Number of high complexity events
            cognitive_state: Latest cognitive state
            session_duration: Minutes since session start
            time_since_break: Minutes since last break

        Returns:
            BreakSuggestion with personalized message
        """
        triggers = []
        priority = "medium"

        # Build message based on triggers
        if complexity_count >= 5:
            triggers.append("very_high_complexity")
            if priority == "medium":
                priority = "high"
        elif complexity_count >= 3:
            triggers.append("high_complexity")

        if cognitive_state:
            energy = cognitive_state.get('energy')
            attention = cognitive_state.get('attention')

            if energy == 'low':
                triggers.append("low_energy")
                if priority != "critical":
                    priority = "high"

            if attention == 'scattered':
                triggers.append("scattered_attention")
                if priority != "critical":
                    priority = "high"

        if session_duration and session_duration > 60:
            triggers.append("long_session")
            priority = "critical"  # >60 min = mandatory

        # Generate gentle, personalized message
        if priority == "critical":
            message = f"MANDATORY BREAK - {int(session_duration or 0)} min of high complexity work"
            reason = "Burnout prevention - take 10 min break immediately"
            duration = 10
        elif priority == "high":
            minutes = int(time_since_break or session_duration or 25)
            message = f"High complexity work for {minutes} min - break recommended"
            reason = "Maintain productivity and prevent cognitive fatigue"
            duration = 5
        else:
            message = "Consider taking a 5 min break"
            reason = "Sustained focus detected - breaks improve performance"
            duration = 5

        return BreakSuggestion(
            priority=priority,
            message=message,
            reason=reason,
            suggested_duration=duration,
            triggered_by=triggers,
            timestamp=datetime.now(timezone.utc)
        )

    async def get_current_status(self) -> Dict:
        """
        Get current break suggestion engine status.

        Returns:
            Status dict with window data and last suggestion
        """
        now = datetime.now(timezone.utc)

        return {
            'user_id': self.user_id,
            'session_start': self.cognitive_window.session_start.isoformat() if self.cognitive_window.session_start else None,
            'last_break': self.cognitive_window.last_break.isoformat() if self.cognitive_window.last_break else None,
            'complexity_events_in_window': len(self.cognitive_window.complexity_events),
            'last_suggestion': self.last_suggestion.isoformat() if self.last_suggestion else None,
            'suggestions_today': len(self.suggestion_history),
            'current_time': now.isoformat()
        }


# Global singleton per user
_break_engines: Dict[str, BreakSuggestionEngine] = {}


async def get_break_suggestion_engine(user_id: str = "default") -> BreakSuggestionEngine:
    """
    Get or create break suggestion engine for user.

    Args:
        user_id: User identifier

    Returns:
        BreakSuggestionEngine instance
    """
    global _break_engines

    if user_id not in _break_engines:
        _break_engines[user_id] = BreakSuggestionEngine(user_id=user_id)

    return _break_engines[user_id]
