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

    def __init__(self, user_id: str = "default"):
        """
        Initialize break suggestion engine.

        Args:
            user_id: User identifier for personalization
        """
        self.user_id = user_id
        self.cognitive_window = CognitiveLoadWindow()

        # Thresholds (configurable, ADHD-optimized)
        self.complexity_event_threshold = 3  # 3+ high complexity events
        self.window_minutes = 25  # Sliding window size
        self.min_session_duration = 25  # Minutes before suggesting breaks
        self.min_break_interval = 25  # Minutes between break suggestions

        # State
        self.last_suggestion: Optional[datetime] = None
        self.suggestion_history: deque = deque(maxlen=10)

        # ADHD personalization
        self.gentle_mode = True  # Use gentle language
        self.celebration_mode = True  # Celebrate break adherence

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

        # Check if suggestion needed
        await self._evaluate_suggestion_triggers()

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

        # Check if suggestion needed
        await self._evaluate_suggestion_triggers()

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
            priority = "high"
        elif complexity_count >= 3:
            triggers.append("high_complexity")

        if cognitive_state:
            energy = cognitive_state.get('energy')
            attention = cognitive_state.get('attention')

            if energy == 'low':
                triggers.append("low_energy")
                priority = "high"

            if attention == 'scattered':
                triggers.append("scattered_attention")
                priority = "high" if priority != "critical" else "critical"

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
