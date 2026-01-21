"""
Proactive Intervention System - Phase 2B: Pattern prediction and intervention

This module provides proactive ADHD support through pattern recognition,
intervention scheduling, and context switch handling.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum

from .dynamic_adaptation import AttentionState, UserCognitiveState

logger = logging.getLogger(__name__)


class InterventionType(Enum):
    """Types of proactive interventions."""
    BREAK_REMINDER = "break_reminder"
    FOCUS_BOOST = "focus_boost"
    CONTEXT_REORIENTATION = "context_reorientation"
    COGNITIVE_LOAD_WARNING = "cognitive_load_warning"
    ENERGY_OPTIMIZATION = "energy_optimization"
    PATTERN_AWARENESS = "pattern_awareness"


@dataclass
class Intervention:
    """A proactive intervention for ADHD support."""
    intervention_id: str
    user_id: str
    intervention_type: InterventionType
    trigger_condition: str
    confidence_score: float  # 0.0-1.0
    scheduled_time: datetime
    message: str
    context_data: Dict[str, Any] = field(default_factory=dict)
    delivered: bool = False
    delivered_time: Optional[datetime] = None
    user_response: Optional[str] = None


@dataclass
class CognitivePattern:
    """Learned cognitive pattern for prediction."""
    pattern_id: str
    user_id: str
    pattern_type: str  # fatigue_cycle, focus_peak, context_switch
    confidence_score: float
    trigger_conditions: Dict[str, Any]
    historical_occurrences: List[datetime]
    average_lead_time: int  # minutes before event
    intervention_suggestions: List[str]
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class ContextSwitchEvent:
    """Context switch tracking for pattern learning."""
    switch_id: str
    user_id: str
    timestamp: datetime
    from_context: str
    to_context: str
    trigger_reason: str  # voluntary, interruption, fatigue, completion
    cognitive_state_before: UserCognitiveState
    cognitive_state_after: Optional[UserCognitiveState] = None
    disruption_level: float  # 0.0-1.0 (how disruptive was the switch)


class PatternPredictor:
    """
    ML-powered pattern recognition for ADHD behavior prediction.

    Learns from historical data to predict cognitive challenges and optimal intervention timing.
    """

    def __init__(self):
        self.patterns: Dict[str, List[CognitivePattern]] = {}
        self.context_switches: Dict[str, List[ContextSwitchEvent]] = {}
        self.intervention_history: Dict[str, List[Intervention]] = {}

    def record_context_switch(self, switch: ContextSwitchEvent) -> None:
        """Record a context switch event for pattern learning."""
        user_id = switch.user_id

        if user_id not in self.context_switches:
            self.context_switches[user_id] = []

        self.context_switches[user_id].append(switch)

        # Keep only recent switches (last 30 days)
        cutoff = datetime.now() - timedelta(days=30)
        self.context_switches[user_id] = [
            s for s in self.context_switches[user_id]
            if s.timestamp > cutoff
        ]

    def analyze_patterns(self, user_id: str) -> List[CognitivePattern]:
        """Analyze historical data to identify cognitive patterns."""
        if user_id not in self.context_switches:
            return []

        switches = self.context_switches[user_id]
        if len(switches) < 5:  # Need minimum data
            return []

        patterns = []

        # Analyze fatigue patterns
        fatigue_pattern = self._detect_fatigue_pattern(switches)
        if fatigue_pattern:
            patterns.append(fatigue_pattern)

        # Analyze focus peak patterns
        focus_pattern = self._detect_focus_peak_pattern(switches)
        if focus_pattern:
            patterns.append(focus_pattern)

        # Analyze context switch disruption patterns
        disruption_pattern = self._detect_disruption_pattern(switches)
        if disruption_pattern:
            patterns.append(disruption_pattern)

        # Store patterns
        self.patterns[user_id] = patterns

        return patterns

    def _detect_fatigue_pattern(self, switches: List[ContextSwitchEvent]) -> Optional[CognitivePattern]:
        """Detect fatigue-related context switches."""
        fatigue_switches = [
            s for s in switches
            if s.trigger_reason == "fatigue" and s.cognitive_state_before
        ]

        if len(fatigue_switches) < 3:
            return None

        # Analyze timing patterns
        fatigue_hours = [s.timestamp.hour for s in fatigue_switches]
        most_common_hour = max(set(fatigue_hours), key=fatigue_hours.count)

        # Calculate average lead time (when fatigue warning should be given)
        # Assume fatigue builds over 30-60 minutes
        avg_lead_time = 45

        return CognitivePattern(
            pattern_id=f"fatigue_{fatigue_switches[0].user_id}",
            user_id=fatigue_switches[0].user_id,
            pattern_type="fatigue_cycle",
            confidence_score=min(len(fatigue_switches) / 10, 1.0),  # Higher confidence with more data
            trigger_conditions={
                "time_of_day": most_common_hour,
                "cognitive_load_threshold": 0.7,
                "attention_state": "fatigued"
            },
            historical_occurrences=[s.timestamp for s in fatigue_switches],
            average_lead_time=avg_lead_time,
            intervention_suggestions=[
                "Schedule break reminder 45 minutes before typical fatigue time",
                "Suggest energy-boosting activities (hydration, stretching)",
                "Warn about increasing cognitive load"
            ]
        )

    def _detect_focus_peak_pattern(self, switches: List[ContextSwitchEvent]) -> Optional[CognitivePattern]:
        """Detect when user is most focused."""
        focus_switches = [
            s for s in switches
            if s.cognitive_state_before and
               s.cognitive_state_before.attention_state.name in ["FOCUSED", "HYPERFOCUSED"]
        ]

        if len(focus_switches) < 3:
            return None

        focus_hours = [s.timestamp.hour for s in focus_switches]
        peak_hour = max(set(focus_hours), key=focus_hours.count)

        return CognitivePattern(
            pattern_id=f"focus_peak_{focus_switches[0].user_id}",
            user_id=focus_switches[0].user_id,
            pattern_type="focus_peak",
            confidence_score=min(len(focus_switches) / 8, 1.0),
            trigger_conditions={
                "time_of_day": peak_hour,
                "energy_level": "high",
                "cognitive_load": "<0.6"
            },
            historical_occurrences=[s.timestamp for s in focus_switches],
            average_lead_time=0,  # No lead time needed
            intervention_suggestions=[
                "Suggest tackling complex tasks during peak focus times",
                "Minimize interruptions during focus periods",
                "Celebrate and reinforce successful focus sessions"
            ]
        )

    def _detect_disruption_pattern(self, switches: List[ContextSwitchEvent]) -> Optional[CognitivePattern]:
        """Detect context switches that cause high disruption."""
        high_disruption_switches = [
            s for s in switches
            if s.disruption_level > 0.7 and s.trigger_reason == "interruption"
        ]

        if len(high_disruption_switches) < 2:
            return None

        return CognitivePattern(
            pattern_id=f"disruption_{high_disruption_switches[0].user_id}",
            user_id=high_disruption_switches[0].user_id,
            pattern_type="context_switch",
            confidence_score=min(len(high_disruption_switches) / 5, 1.0),
            trigger_conditions={
                "disruption_level": ">0.7",
                "trigger_reason": "interruption",
                "attention_state": "hyperfocused"
            },
            historical_occurrences=[s.timestamp for s in high_disruption_switches],
            average_lead_time=5,  # Warn 5 minutes before potential disruption
            intervention_suggestions=[
                "Buffer against interruptions during deep focus",
                "Use gentle transition techniques for context switches",
                "Create interruption-resistant work environments"
            ]
        )

    def predict_next_event(self, user_id: str, current_state: UserCognitiveState) -> List[Dict[str, Any]]:
        """
        Predict upcoming cognitive events based on current state and patterns.

        Returns list of predicted events with confidence scores.
        """
        if user_id not in self.patterns:
            return []

        predictions = []
        patterns = self.patterns[user_id]

        current_hour = datetime.now().hour

        for pattern in patterns:
            prediction = self._evaluate_pattern_trigger(pattern, current_state, current_hour)
            if prediction:
                predictions.append(prediction)

        return sorted(predictions, key=lambda x: x["confidence"], reverse=True)

    def _evaluate_pattern_trigger(
        self,
        pattern: CognitivePattern,
        current_state: UserCognitiveState,
        current_hour: int
    ) -> Optional[Dict[str, Any]]:
        """Evaluate if a pattern should trigger based on current conditions."""

        # Check time-based triggers
        if "time_of_day" in pattern.trigger_conditions:
            pattern_hour = pattern.trigger_conditions["time_of_day"]
            if abs(current_hour - pattern_hour) <= 1:  # Within 1 hour
                time_match = True
            else:
                return None  # Time doesn't match
        else:
            time_match = True

        # Check cognitive state triggers
        state_match = True
        if "cognitive_load_threshold" in pattern.trigger_conditions:
            threshold = pattern.trigger_conditions["cognitive_load_threshold"]
            if isinstance(threshold, str) and threshold.startswith(">"):
                required_load = float(threshold[1:])
                state_match = current_state.cognitive_load > required_load
            elif isinstance(threshold, str) and threshold.startswith("<"):
                required_load = float(threshold[1:])
                state_match = current_state.cognitive_load < required_load
            elif current_state.cognitive_load >= threshold:
                state_match = True

        if "attention_state" in pattern.trigger_conditions:
            required_state = pattern.trigger_conditions["attention_state"]
            state_match = state_match and current_state.attention_state.name.lower() == required_state

        if not state_match:
            return None

        # Calculate confidence based on pattern strength and recency
        base_confidence = pattern.confidence_score

        # Boost confidence for recent patterns
        days_since_last = (datetime.now() - pattern.last_updated).days
        recency_boost = max(0, 1 - (days_since_last / 30))  # Boost decays over 30 days

        confidence = min(base_confidence * (1 + recency_boost * 0.2), 1.0)

        return {
            "pattern_type": pattern.pattern_type,
            "confidence": confidence,
            "predicted_time": datetime.now() + timedelta(minutes=pattern.average_lead_time),
            "intervention_suggestions": pattern.intervention_suggestions,
            "trigger_reason": pattern.trigger_conditions
        }


class InterventionScheduler:
    """
    Schedules and manages proactive interventions based on pattern predictions.

    Provides intelligent timing and delivery of ADHD support interventions.
    """

    def __init__(self, pattern_predictor: PatternPredictor):
        self.pattern_predictor = pattern_predictor
        self.pending_interventions: Dict[str, List[Intervention]] = {}
        self.delivered_interventions: Dict[str, List[Intervention]] = {}
        self.intervention_templates = self._initialize_templates()

    def _initialize_templates(self) -> Dict[InterventionType, Dict[str, Any]]:
        """Initialize intervention templates."""
        return {
            InterventionType.BREAK_REMINDER: {
                "message_template": "💭 You've been focused for {duration} minutes. Consider taking a 5-minute break to maintain peak performance.",
                "urgency": "gentle",
                "follow_up_allowed": True
            },
            InterventionType.FOCUS_BOOST: {
                "message_template": "🎯 Great focus period detected! This is an optimal time for tackling complex tasks.",
                "urgency": "positive",
                "follow_up_allowed": False
            },
            InterventionType.CONTEXT_REORIENTATION: {
                "message_template": "🔄 Context switch detected. Previous task: '{previous_context}'. Current focus: smooth transition support available.",
                "urgency": "supportive",
                "follow_up_allowed": True
            },
            InterventionType.COGNITIVE_LOAD_WARNING: {
                "message_template": "⚠️ Cognitive load increasing. Current level: {load:.1f}. Consider breaking complex tasks into smaller steps.",
                "urgency": "caution",
                "follow_up_allowed": True
            },
            InterventionType.ENERGY_OPTIMIZATION: {
                "message_template": "⚡ Energy pattern detected. Current level: {energy}. Consider {suggestion} for optimal performance.",
                "urgency": "informational",
                "follow_up_allowed": True
            },
            InterventionType.PATTERN_AWARENESS: {
                "message_template": "📊 Pattern insight: You perform best during {peak_times}. Consider scheduling important tasks then.",
                "urgency": "educational",
                "follow_up_allowed": False
            }
        }

    def schedule_intervention(
        self,
        user_id: str,
        intervention_type: InterventionType,
        trigger_data: Dict[str, Any],
        confidence: float,
        delay_minutes: int = 0
    ) -> Optional[Intervention]:
        """
        Schedule a proactive intervention.

        Returns the scheduled intervention or None if scheduling fails.
        """
        try:
            intervention_id = f"{intervention_type.value}_{user_id}_{int(datetime.now().timestamp())}"

            # Get template
            template = self.intervention_templates.get(intervention_type)
            if not template:
                logger.error(f"No template found for intervention type: {intervention_type}")
                return None

            # Generate message
            message = self._generate_message(template["message_template"], trigger_data)

            # Schedule time
            scheduled_time = datetime.now() + timedelta(minutes=delay_minutes)

            intervention = Intervention(
                intervention_id=intervention_id,
                user_id=user_id,
                intervention_type=intervention_type,
                trigger_condition=json.dumps(trigger_data),
                confidence_score=confidence,
                scheduled_time=scheduled_time,
                message=message,
                context_data=trigger_data
            )

            # Add to pending interventions
            if user_id not in self.pending_interventions:
                self.pending_interventions[user_id] = []

            self.pending_interventions[user_id].append(intervention)

            # Sort by scheduled time
            self.pending_interventions[user_id].sort(key=lambda x: x.scheduled_time)

            logger.info(f"Scheduled intervention {intervention_id} for user {user_id} at {scheduled_time}")
            return intervention

        except Exception as e:
            logger.error(f"Failed to schedule intervention: {e}")
            return None

    def _generate_message(self, template: str, data: Dict[str, Any]) -> str:
        """Generate intervention message from template and data."""
        try:
            return template.format(**data)
        except KeyError as e:
            logger.warning(f"Missing data for template formatting: {e}")
            return template  # Return template as-is if formatting fails

    def get_pending_interventions(self, user_id: str) -> List[Intervention]:
        """Get all pending interventions for a user."""
        return self.pending_interventions.get(user_id, [])

    def deliver_intervention(self, intervention: Intervention) -> bool:
        """Mark intervention as delivered and move to history."""
        try:
            intervention.delivered = True
            intervention.delivered_time = datetime.now()

            # Move from pending to delivered
            user_pending = self.pending_interventions.get(intervention.user_id, [])
            if intervention in user_pending:
                user_pending.remove(intervention)

            # Add to delivered history
            if intervention.user_id not in self.delivered_interventions:
                self.delivered_interventions[intervention.user_id] = []

            self.delivered_interventions[intervention.user_id].append(intervention)

            # Keep only recent history (last 30 days)
            cutoff = datetime.now() - timedelta(days=30)
            self.delivered_interventions[intervention.user_id] = [
                i for i in self.delivered_interventions[intervention.user_id]
                if i.delivered_time and i.delivered_time > cutoff
            ]

            logger.info(f"Delivered intervention {intervention.intervention_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to deliver intervention {intervention.intervention_id}: {e}")
            return False

    def check_due_interventions(self) -> List[Intervention]:
        """Check for interventions that are due for delivery."""
        now = datetime.now()
        due_interventions = []

        for user_interventions in self.pending_interventions.values():
            for intervention in user_interventions:
                if (not intervention.delivered and
                    intervention.scheduled_time <= now):
                    due_interventions.append(intervention)

        return due_interventions

    def cancel_intervention(self, intervention_id: str, user_id: str) -> bool:
        """Cancel a pending intervention."""
        user_pending = self.pending_interventions.get(user_id, [])

        for intervention in user_pending:
            if intervention.intervention_id == intervention_id:
                user_pending.remove(intervention)
                logger.info(f"Cancelled intervention {intervention_id}")
                return True

        return False

    def get_intervention_stats(self, user_id: str) -> Dict[str, Any]:
        """Get intervention statistics for a user."""
        pending = self.pending_interventions.get(user_id, [])
        delivered = self.delivered_interventions.get(user_id, [])

        # Calculate effectiveness
        if delivered:
            avg_response_time = sum(
                (i.delivered_time - i.scheduled_time).total_seconds() / 60
                for i in delivered
                if i.delivered_time
            ) / len(delivered)
        else:
            avg_response_time = 0

        # Intervention type distribution
        type_counts = {}
        for intervention in delivered:
            int_type = intervention.intervention_type.value
            type_counts[int_type] = type_counts.get(int_type, 0) + 1

        return {
            "pending_count": len(pending),
            "delivered_count": len(delivered),
            "avg_response_time_minutes": round(avg_response_time, 1),
            "intervention_types": type_counts,
            "next_scheduled": min((i.scheduled_time for i in pending), default=None)
        }


class ContextSwitchHandler:
    """
    Handles context switches with minimal disruption.

    Provides smooth transitions and re-orientation support.
    """

    def __init__(self):
        self.switch_history: Dict[str, List[ContextSwitchEvent]] = {}
        self.reorientation_templates = self._initialize_templates()

    def _initialize_templates(self) -> Dict[str, str]:
        """Initialize reorientation message templates."""
        return {
            "interruption_recovery": "🔄 **Context Switch Detected**\n\nYou were working on: *{previous_context}*\nNow focusing on: *{current_context}*\n\n💡 **Quick Re-orientation:**\n- Take 30 seconds to review your current task\n- Note any incomplete thoughts from previous context\n- Use this transition as a natural break point\n\nReady to continue? Take a deep breath and dive back in!",

            "voluntary_transition": "🔄 **Smooth Transition**\n\nMoving from: *{previous_context}*\nTo: *{current_context}*\n\n✨ **Transition Tips:**\n- Carry forward any relevant insights\n- Reset your mental workspace\n- Approach with fresh perspective\n\nYou've got this!",

            "fatigue_driven": "🔄 **Restorative Transition**\n\nPrevious context: *{previous_context}*\nNew focus: *{current_context}*\n\n🧘 **Mindful Transition:**\n- Acknowledge the fatigue as a signal to rest\n- Use this break to recharge\n- Return refreshed and ready\n\nYour well-being comes first!",

            "completion_based": "🎉 **Task Completion Transition**\n\nCompleted: *{previous_context}*\nNext: *{current_context}*\n\n🏆 **Celebration & Setup:**\n- Take a moment to acknowledge completion\n- Carry momentum to the next task\n- Set up your workspace for success\n\nGreat work!"
        }

    def handle_context_switch(
        self,
        user_id: str,
        from_context: str,
        to_context: str,
        trigger_reason: str,
        cognitive_state: UserCognitiveState
    ) -> Dict[str, Any]:
        """
        Handle a context switch with appropriate support.

        Returns transition support information.
        """
        # Record the switch
        switch_event = ContextSwitchEvent(
            switch_id=f"switch_{user_id}_{int(datetime.now().timestamp())}",
            user_id=user_id,
            timestamp=datetime.now(),
            from_context=from_context,
            to_context=to_context,
            trigger_reason=trigger_reason,
            cognitive_state_before=cognitive_state,
            disruption_level=self._calculate_disruption_level(trigger_reason, cognitive_state)
        )

        if user_id not in self.switch_history:
            self.switch_history[user_id] = []

        self.switch_history[user_id].append(switch_event)

        # Generate reorientation support
        reorientation_message = self._generate_reorientation_message(
            from_context, to_context, trigger_reason
        )

        # Calculate transition difficulty
        difficulty_score = self._calculate_transition_difficulty(trigger_reason, cognitive_state)

        # Suggest transition strategies
        strategies = self._get_transition_strategies(trigger_reason, difficulty_score)

        return {
            "switch_event": switch_event,
            "reorientation_message": reorientation_message,
            "difficulty_score": difficulty_score,
            "transition_strategies": strategies,
            "estimated_recovery_time": self._estimate_recovery_time(difficulty_score, trigger_reason)
        }

    def _calculate_disruption_level(self, trigger_reason: str, cognitive_state: UserCognitiveState) -> float:
        """Calculate how disruptive the context switch is."""
        base_disruption = {
            "voluntary": 0.2,
            "completion": 0.1,
            "fatigue": 0.4,
            "interruption": 0.8
        }.get(trigger_reason, 0.5)

        # Adjust based on cognitive state
        if cognitive_state.attention_state.name == "HYPERFOCUSED":
            base_disruption *= 1.5  # Much more disruptive when hyperfocused

        if cognitive_state.cognitive_load > 0.8:
            base_disruption *= 1.3  # More disruptive under high load

        return min(base_disruption, 1.0)

    def _generate_reorientation_message(self, from_context: str, to_context: str, trigger_reason: str) -> str:
        """Generate appropriate reorientation message."""
        template = self.reorientation_templates.get(trigger_reason, self.reorientation_templates["voluntary_transition"])

        return template.format(
            previous_context=from_context,
            current_context=to_context
        )

    def _calculate_transition_difficulty(self, trigger_reason: str, cognitive_state: UserCognitiveState) -> float:
        """Calculate transition difficulty score."""
        difficulty = 0.3  # Base difficulty

        # Adjust based on trigger reason
        if trigger_reason == "interruption":
            difficulty += 0.4
        elif trigger_reason == "fatigue":
            difficulty += 0.2

        # Adjust based on cognitive state
        if cognitive_state.cognitive_load > 0.7:
            difficulty += 0.2
        if cognitive_state.attention_state.name == "SCATTERED":
            difficulty += 0.2

        return min(difficulty, 1.0)

    def _get_transition_strategies(self, trigger_reason: str, difficulty: float) -> List[str]:
        """Get transition strategies based on context."""
        strategies = []

        if trigger_reason == "interruption":
            strategies.extend([
                "Take 1 minute to note your last thought before switching",
                "Use a physical marker (sticky note, bookmark) to return to your place",
                "Set a reminder to review context when returning"
            ])

        elif trigger_reason == "fatigue":
            strategies.extend([
                "Take a 5-10 minute break before switching",
                "Do light physical activity (stretch, walk)",
                "Hydrate and have a small, healthy snack"
            ])

        if difficulty > 0.6:
            strategies.extend([
                "Write a brief transition note: 'I was working on X, next is Y'",
                "Use the 2-minute rule: spend 2 minutes setting up the new context",
                "Acknowledge the difficulty - it's normal for complex transitions"
            ])

        return strategies[:5]  # Limit to 5 strategies

    def _estimate_recovery_time(self, difficulty: float, trigger_reason: str) -> int:
        """Estimate time needed to recover from context switch (minutes)."""
        base_time = 2  # Base recovery time

        # Adjust for difficulty
        base_time += difficulty * 8  # Up to 8 additional minutes for max difficulty

        # Adjust for trigger reason
        if trigger_reason == "interruption":
            base_time += 3
        elif trigger_reason == "fatigue":
            base_time += 5  # Fatigue requires more recovery time

        return int(base_time)

    def get_switch_patterns(self, user_id: str) -> Dict[str, Any]:
        """Get context switch patterns for a user."""
        if user_id not in self.switch_history:
            return {"status": "no_data"}

        switches = self.switch_history[user_id]

        # Analyze patterns
        trigger_counts = {}
        avg_disruption = 0.0
        avg_recovery_time = 0.0

        for switch in switches:
            trigger = switch.trigger_reason
            trigger_counts[trigger] = trigger_counts.get(trigger, 0) + 1
            avg_disruption += switch.disruption_level

            # Estimate recovery time for analysis
            difficulty = self._calculate_transition_difficulty(trigger, switch.cognitive_state_before)
            avg_recovery_time += self._estimate_recovery_time(difficulty, trigger)

        if switches:
            avg_disruption /= len(switches)
            avg_recovery_time /= len(switches)

        return {
            "total_switches": len(switches),
            "trigger_distribution": trigger_counts,
            "average_disruption": round(avg_disruption, 2),
            "average_recovery_minutes": round(avg_recovery_time, 1),
            "most_common_trigger": max(trigger_counts.items(), key=lambda x: x[1])[0] if trigger_counts else None
        }


class FatigueDetector:
    """
    Detects cognitive fatigue patterns and suggests interventions.

    Monitors cognitive load trends and predicts fatigue onset.
    """

    def __init__(self):
        self.fatigue_patterns: Dict[str, Dict[str, Any]] = {}
        self.fatigue_thresholds = {
            "low": 0.6,
            "medium": 0.75,
            "high": 0.85,
            "critical": 0.95
        }

    def analyze_fatigue_trend(
        self,
        user_id: str,
        cognitive_states: List[UserCognitiveState],
        time_window_minutes: int = 60
    ) -> Dict[str, Any]:
        """Analyze cognitive load trend for fatigue detection."""
        if len(cognitive_states) < 3:
            return {"status": "insufficient_data"}

        # Filter recent states
        cutoff = datetime.now() - timedelta(minutes=time_window_minutes)
        recent_states = [
            state for state in cognitive_states
            if state.last_updated > cutoff
        ]

        if len(recent_states) < 3:
            return {"status": "insufficient_recent_data"}

        # Calculate trend
        loads = [state.cognitive_load for state in recent_states]
        load_trend = self._calculate_trend(loads)

        # Detect fatigue patterns
        fatigue_level = self._assess_fatigue_level(load_trend, loads[-1])

        # Predict fatigue onset
        prediction = self._predict_fatigue_onset(loads, load_trend)

        # Generate interventions
        interventions = self._generate_fatigue_interventions(fatigue_level, prediction)

        result = {
            "fatigue_level": fatigue_level,
            "load_trend": round(load_trend, 3),
            "current_load": round(loads[-1], 2),
            "prediction": prediction,
            "recommended_interventions": interventions,
            "trend_analysis": self._analyze_trend_pattern(loads)
        }

        # Store for pattern learning
        self.fatigue_patterns[user_id] = result

        return result

    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate linear trend in values (-1 to 1, negative = decreasing, positive = increasing)."""
        if len(values) < 2:
            return 0.0

        # Simple linear regression slope
        n = len(values)
        x = list(range(n))
        y = values

        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_xx = sum(xi * xi for xi in x)

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x)
        return slope

    def _assess_fatigue_level(self, trend: float, current_load: float) -> str:
        """Assess fatigue level based on trend and current load."""
        # Increasing load trend + high current load = fatigue
        risk_score = (trend * 0.5) + (current_load * 0.5)  # Weighted combination

        if risk_score > self.fatigue_thresholds["critical"]:
            return "critical"
        elif risk_score > self.fatigue_thresholds["high"]:
            return "high"
        elif risk_score > self.fatigue_thresholds["medium"]:
            return "medium"
        elif risk_score > self.fatigue_thresholds["low"]:
            return "low"
        else:
            return "none"

    def _predict_fatigue_onset(self, loads: List[float], trend: float) -> Optional[Dict[str, Any]]:
        """Predict when fatigue will onset."""
        if trend <= 0:  # Load is not increasing
            return None

        current_load = loads[-1]
        time_to_critical = (self.fatigue_thresholds["high"] - current_load) / trend

        if time_to_critical > 0 and time_to_critical < 60:  # Predict within next hour
            onset_time = datetime.now() + timedelta(minutes=time_to_critical)
            return {
                "predicted_onset": onset_time,
                "minutes_until": round(time_to_critical, 1),
                "confidence": min(abs(trend) * 2, 1.0)  # Higher trend = higher confidence
            }

        return None

    def _generate_fatigue_interventions(self, fatigue_level: str, prediction: Optional[Dict]) -> List[str]:
        """Generate appropriate fatigue interventions."""
        interventions = []

        if fatigue_level == "critical":
            interventions.extend([
                "URGENT: Take an immediate 15-minute break",
                "Consider rescheduling complex tasks to tomorrow",
                "Hydrate and have a protein-rich snack",
                "Avoid making important decisions right now"
            ])

        elif fatigue_level == "high":
            interventions.extend([
                "Take a 10-minute break with deep breathing",
                "Switch to a low-cognitive task",
                "Increase hydration and consider a healthy snack",
                "Review and simplify current task complexity"
            ])

        elif fatigue_level == "medium":
            interventions.extend([
                "Take a 5-minute stretch break",
                "Practice the 4-7-8 breathing technique",
                "Have a glass of water",
                "Consider a short walk if possible"
            ])

        elif fatigue_level == "low":
            interventions.extend([
                "Consider a 2-minute mindfulness break",
                "Stretch your neck and shoulders",
                "Take a few deep breaths",
                "Stay hydrated"
            ])

        if prediction and prediction["minutes_until"] < 30:
            interventions.insert(0, f"⚠️ Fatigue predicted in {prediction['minutes_until']} minutes")

        return interventions

    def _analyze_trend_pattern(self, loads: List[float]) -> Dict[str, Any]:
        """Analyze the pattern in cognitive load trend."""
        if len(loads) < 5:
            return {"pattern": "insufficient_data"}

        # Check for cyclical patterns
        diffs = [loads[i+1] - loads[i] for i in range(len(loads)-1)]
        increasing_periods = sum(1 for d in diffs if d > 0.05)
        decreasing_periods = sum(1 for d in diffs if d < -0.05)

        if increasing_periods > decreasing_periods * 1.5:
            pattern = "consistently_increasing"
        elif decreasing_periods > increasing_periods * 1.5:
            pattern = "consistently_decreasing"
        elif abs(increasing_periods - decreasing_periods) < 2:
            pattern = "stable_with_fluctuations"
        else:
            pattern = "cyclical"

        return {
            "pattern": pattern,
            "increasing_periods": increasing_periods,
            "decreasing_periods": decreasing_periods,
            "volatility": round(sum(abs(d) for d in diffs) / len(diffs), 3)
        }


class ProactiveInterventionSystem:
    """
    Phase 2B: Complete proactive intervention system.

    Integrates pattern prediction, intervention scheduling, context switch handling,
    and fatigue detection for comprehensive ADHD support.
    """

    def __init__(self):
        self.pattern_predictor = PatternPredictor()
        self.intervention_scheduler = InterventionScheduler(self.pattern_predictor)
        self.context_handler = ContextSwitchHandler()
        self.fatigue_detector = FatigueDetector()

        # Integration state
        self.active_users: Dict[str, Dict[str, Any]] = {}

    async def initialize(self) -> bool:
        """Initialize the proactive intervention system."""
        logger.info("🧠 Initializing Proactive Intervention System...")

        # System is ready to go
        logger.info("✅ Proactive Intervention System initialized")
        return True

    async def process_user_state(
        self,
        user_id: str,
        cognitive_state: UserCognitiveState,
        context_switches: List[ContextSwitchEvent] = None
    ) -> Dict[str, Any]:
        """
        Process user state and generate proactive interventions.

        This is the main entry point for proactive intervention logic.
        """
        # Update user tracking
        if user_id not in self.active_users:
            self.active_users[user_id] = {
                "cognitive_states": [],
                "last_processed": None,
                "pattern_analysis": None
            }

        user_data = self.active_users[user_id]
        user_data["cognitive_states"].append(cognitive_state)
        user_data["last_processed"] = datetime.now()

        # Keep only recent states (last 2 hours)
        cutoff = datetime.now() - timedelta(hours=2)
        user_data["cognitive_states"] = [
            state for state in user_data["cognitive_states"]
            if state.last_updated > cutoff
        ]

        # Analyze patterns if we have enough data
        if len(user_data["cognitive_states"]) >= 5:
            patterns = self.pattern_predictor.analyze_patterns(user_id)
            user_data["pattern_analysis"] = patterns

        # Record context switches if provided
        if context_switches:
            for switch in context_switches:
                self.pattern_predictor.record_context_switch(switch)
                self.context_handler.handle_context_switch(
                    switch.user_id, switch.from_context, switch.to_context,
                    switch.trigger_reason, switch.cognitive_state_before
                )

        # Generate interventions
        interventions = await self._generate_interventions(user_id, cognitive_state)

        # Check for due interventions
        due_interventions = self.intervention_scheduler.check_due_interventions()

        # Filter for this user
        user_due_interventions = [i for i in due_interventions if i.user_id == user_id]

        return {
            "new_interventions": interventions,
            "due_interventions": user_due_interventions,
            "pattern_insights": self._get_pattern_insights(user_id),
            "fatigue_analysis": self._analyze_fatigue_risk(user_id, cognitive_state)
        }

    async def _generate_interventions(self, user_id: str, cognitive_state: UserCognitiveState) -> List[Intervention]:
        """Generate proactive interventions based on current state."""
        interventions = []

        # Check for break reminders
        if self._should_schedule_break(cognitive_state):
            intervention = self.intervention_scheduler.schedule_intervention(
                user_id=user_id,
                intervention_type=InterventionType.BREAK_REMINDER,
                trigger_data={
                    "duration": cognitive_state.focus_duration,
                    "cognitive_load": cognitive_state.cognitive_load
                },
                confidence=0.8,
                delay_minutes=5  # Remind in 5 minutes
            )
            if intervention:
                interventions.append(intervention)

        # Check for cognitive load warnings
        if cognitive_state.cognitive_load > 0.8:
            intervention = self.intervention_scheduler.schedule_intervention(
                user_id=user_id,
                intervention_type=InterventionType.COGNITIVE_LOAD_WARNING,
                trigger_data={
                    "load": cognitive_state.cognitive_load,
                    "attention_state": cognitive_state.attention_state.value
                },
                confidence=0.9,
                delay_minutes=0  # Immediate
            )
            if intervention:
                interventions.append(intervention)

        # Check for focus boost opportunities
        if (cognitive_state.attention_state.name == "HYPERFOCUSED" and
            cognitive_state.energy_level in ["high", "hyper"]):
            intervention = self.intervention_scheduler.schedule_intervention(
                user_id=user_id,
                intervention_type=InterventionType.FOCUS_BOOST,
                trigger_data={
                    "attention_state": cognitive_state.attention_state.value,
                    "energy_level": cognitive_state.energy_level
                },
                confidence=0.7,
                delay_minutes=0  # Immediate positive reinforcement
            )
            if intervention:
                interventions.append(intervention)

        # Pattern-based interventions
        predictions = self.pattern_predictor.predict_next_event(user_id, cognitive_state)
        for prediction in predictions:
            if prediction["confidence"] > 0.7:
                intervention = self.intervention_scheduler.schedule_intervention(
                    user_id=user_id,
                    intervention_type=InterventionType.PATTERN_AWARENESS,
                    trigger_data={
                        "pattern_type": prediction["pattern_type"],
                        "peak_times": prediction.get("trigger_reason", {}).get("time_of_day", "optimal times")
                    },
                    confidence=prediction["confidence"],
                    delay_minutes=0
                )
                if intervention:
                    interventions.append(intervention)

        return interventions

    def _should_schedule_break(self, cognitive_state: UserCognitiveState) -> bool:
        """Determine if a break reminder should be scheduled."""
        # Schedule break if focused for 20+ minutes with moderate-high cognitive load
        return (cognitive_state.focus_duration >= 20 and
                cognitive_state.cognitive_load > 0.5 and
                cognitive_state.attention_state.name in ["FOCUSED", "HYPERFOCUSED"])

    def _get_pattern_insights(self, user_id: str) -> Dict[str, Any]:
        """Get pattern insights for the user."""
        user_data = self.active_users.get(user_id, {})
        patterns = user_data.get("pattern_analysis", [])

        insights = {
            "total_patterns": len(patterns),
            "high_confidence_patterns": len([p for p in patterns if p.confidence_score > 0.8]),
            "pattern_types": list(set(p.pattern_type for p in patterns))
        }

        # Add context switch insights
        switch_patterns = self.context_handler.get_switch_patterns(user_id)
        if switch_patterns.get("status") != "no_data":
            insights["context_switch_patterns"] = switch_patterns

        return insights

    def _analyze_fatigue_risk(self, user_id: str, cognitive_state: UserCognitiveState) -> Dict[str, Any]:
        """Analyze fatigue risk for the user."""
        user_data = self.active_users.get(user_id, {})
        cognitive_states = user_data.get("cognitive_states", [])

        if len(cognitive_states) < 3:
            return {"status": "insufficient_data"}

        # Use fatigue detector
        analysis = self.fatigue_detector.analyze_fatigue_trend(
            user_id, cognitive_states, time_window_minutes=60
        )

        return analysis

    def get_pending_interventions(self, user_id: str) -> List[Intervention]:
        """Get all pending interventions for a user."""
        return self.intervention_scheduler.get_pending_interventions(user_id)

    def deliver_intervention(self, intervention_id: str, user_id: str, response: Optional[str] = None) -> bool:
        """Deliver a specific intervention."""
        pending = self.intervention_scheduler.get_pending_interventions(user_id)

        for intervention in pending:
            if intervention.intervention_id == intervention_id:
                intervention.user_response = response
                return self.intervention_scheduler.deliver_intervention(intervention)

        return False

    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics."""
        total_users = len(self.active_users)
        total_states = sum(len(user_data["cognitive_states"]) for user_data in self.active_users.values())
        total_patterns = sum(len(user_data.get("pattern_analysis", [])) for user_data in self.active_users.values())

        # Intervention stats
        all_pending = []
        all_delivered = []
        for user_id in self.active_users.keys():
            all_pending.extend(self.intervention_scheduler.get_pending_interventions(user_id))
            stats = self.intervention_scheduler.get_intervention_stats(user_id)
            # Note: We'd need to collect delivered from individual user stats

        return {
            "active_users": total_users,
            "total_cognitive_states": total_states,
            "learned_patterns": total_patterns,
            "pending_interventions": len(all_pending),
            "system_health": "operational"
        }</content>
</xai:function_call">The file content contains invalid XML/HTML markup. Please provide clean Python code only.