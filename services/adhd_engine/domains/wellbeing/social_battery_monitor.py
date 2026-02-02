"""
Social Battery Monitor

Tracks social interaction drain for ADHD users, recommending recovery periods
and helping plan around social events.

ADHD Challenge Addressed:
- Social interactions are cognitively expensive for many ADHD individuals
- Masking (hiding ADHD symptoms) drains energy rapidly
- Difficulty estimating how much social energy remains
- Need for recovery time after social events often overlooked
- Calendar planning without accounting for social energy costs

Features:
- Track social interaction types and their drain rates
- Monitor current social battery level (0-100%)
- Recommend recovery periods based on depletion
- Integrate with calendar for event planning
- Detect when social battery is critically low
- Suggest accommodations (async communication, short meetings)
"""
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class InteractionType(Enum):
    """Types of social interactions with different drain rates."""
    MEETING_LARGE = "meeting_large"  # >10 people, high drain
    MEETING_SMALL = "meeting_small"  # 3-10 people, medium drain
    ONE_ON_ONE = "one_on_one"  # 1:1, low-medium drain
    PRESENTATION = "presentation"  # Public speaking, very high drain
    ASYNC_COMM = "async_comm"  # Email/Slack, minimal drain
    CASUAL = "casual"  # Hallway chat, low drain
    DEEP_WORK = "deep_work"  # Solo work, recharges (+)


class MaskingLevel(Enum):
    """Level of ADHD symptom masking during interaction."""
    NONE = "none"  # Safe space, no masking needed
    LOW = "low"  # Minimal masking (trusted colleagues)
    MEDIUM = "medium"  # Professional masking (normal work)
    HIGH = "high"  # Heavy masking (important meetings, clients)


@dataclass
class InteractionDrainRate:
    """Drain rates for different interaction types and masking levels."""
    interaction_type: InteractionType
    masking_level: MaskingLevel
    base_drain_per_minute: float  # 0.0-5.0 points per minute
    
    # Drain rate modifiers
    DRAIN_RATES = {
        InteractionType.MEETING_LARGE: {
            MaskingLevel.NONE: 0.5,
            MaskingLevel.LOW: 1.0,
            MaskingLevel.MEDIUM: 1.5,
            MaskingLevel.HIGH: 2.5
        },
        InteractionType.MEETING_SMALL: {
            MaskingLevel.NONE: 0.3,
            MaskingLevel.LOW: 0.6,
            MaskingLevel.MEDIUM: 1.0,
            MaskingLevel.HIGH: 1.8
        },
        InteractionType.ONE_ON_ONE: {
            MaskingLevel.NONE: 0.2,
            MaskingLevel.LOW: 0.4,
            MaskingLevel.MEDIUM: 0.7,
            MaskingLevel.HIGH: 1.2
        },
        InteractionType.PRESENTATION: {
            MaskingLevel.NONE: 1.5,
            MaskingLevel.LOW: 2.0,
            MaskingLevel.MEDIUM: 3.0,
            MaskingLevel.HIGH: 4.0
        },
        InteractionType.ASYNC_COMM: {
            MaskingLevel.NONE: 0.05,
            MaskingLevel.LOW: 0.1,
            MaskingLevel.MEDIUM: 0.2,
            MaskingLevel.HIGH: 0.4
        },
        InteractionType.CASUAL: {
            MaskingLevel.NONE: 0.1,
            MaskingLevel.LOW: 0.3,
            MaskingLevel.MEDIUM: 0.5,
            MaskingLevel.HIGH: 0.8
        },
        InteractionType.DEEP_WORK: {
            MaskingLevel.NONE: -0.5,  # Negative = recharge
            MaskingLevel.LOW: -0.3,
            MaskingLevel.MEDIUM: -0.1,
            MaskingLevel.HIGH: 0.0
        }
    }
    
    @classmethod
    def get_drain_rate(
        cls,
        interaction_type: InteractionType,
        masking_level: MaskingLevel
    ) -> float:
        """Get base drain rate for interaction type and masking level."""
        return cls.DRAIN_RATES[interaction_type][masking_level]


@dataclass
class SocialInteraction:
    """Record of a social interaction."""
    interaction_id: str
    interaction_type: InteractionType
    masking_level: MaskingLevel
    start_time: datetime
    duration_minutes: int
    participants_count: int = 1
    description: Optional[str] = None
    calendar_event_id: Optional[str] = None
    
    # Calculated fields
    energy_drain: float = 0.0  # Total energy drained
    recovery_time_needed: int = 0  # Minutes of recovery needed
    
    def calculate_drain(self) -> float:
        """
        Calculate energy drain for this interaction.
        
        Factors:
        - Base drain rate (interaction type + masking level)
        - Duration
        - Participant count multiplier (more people = more drain)
        """
        base_rate = InteractionDrainRate.get_drain_rate(
            self.interaction_type,
            self.masking_level
        )
        
        # Participant multiplier (more people = more cognitive load)
        if self.participants_count <= 2:
            participant_multiplier = 1.0
        elif self.participants_count <= 5:
            participant_multiplier = 1.2
        elif self.participants_count <= 10:
            participant_multiplier = 1.5
        else:
            participant_multiplier = 2.0
        
        total_drain = base_rate * self.duration_minutes * participant_multiplier
        self.energy_drain = max(0, total_drain)  # Can't drain negative
        
        # Recovery time = drain * 0.5 (30 min recovery per hour of draining interaction)
        self.recovery_time_needed = int(self.energy_drain * 0.5)
        
        return self.energy_drain


@dataclass
class SocialBatteryState:
    """Current state of social battery."""
    current_level: float  # 0-100%
    max_level: float = 100.0
    last_updated: datetime = field(default_factory=datetime.now)
    
    # Thresholds
    CRITICAL_THRESHOLD = 20.0
    LOW_THRESHOLD = 40.0
    OPTIMAL_THRESHOLD = 70.0
    
    def is_critical(self) -> bool:
        """Battery critically low (<20%)."""
        return self.current_level < self.CRITICAL_THRESHOLD
    
    def is_low(self) -> bool:
        """Battery low (20-40%)."""
        return self.CRITICAL_THRESHOLD <= self.current_level < self.LOW_THRESHOLD
    
    def is_optimal(self) -> bool:
        """Battery optimal (>70%)."""
        return self.current_level >= self.OPTIMAL_THRESHOLD
    
    def drain(self, amount: float) -> None:
        """Drain energy from battery."""
        self.current_level = max(0, self.current_level - amount)
        self.last_updated = datetime.now()
    
    def recharge(self, amount: float) -> None:
        """Recharge battery."""
        self.current_level = min(self.max_level, self.current_level + amount)
        self.last_updated = datetime.now()
    
    def get_status_emoji(self) -> str:
        """Get emoji representing current battery level."""
        if self.current_level >= 90:
            return "🔋"  # Full
        elif self.current_level >= 70:
            return "🔋"  # High
        elif self.current_level >= 40:
            return "🔌"  # Medium
        elif self.current_level >= 20:
            return "⚠️"  # Low
        else:
            return "🚨"  # Critical


@dataclass
class RecoveryRecommendation:
    """Recommendation for social battery recovery."""
    recovery_type: str  # "immediate", "scheduled", "preventive"
    recommended_duration_minutes: int
    activities: List[str]
    urgency: str  # "critical", "high", "medium", "low"
    rationale: str


class SocialBatteryMonitor:
    """
    ADHD-aware social battery monitoring system.
    
    Features:
    - Track social interactions and energy drain
    - Monitor current battery level
    - Recommend recovery periods
    - Integrate with calendar for planning
    - Detect critical depletion
    - Suggest accommodations
    """
    
    def __init__(
        self,
        user_id: str,
        initial_level: float = 100.0,
        bridge_client=None  # AsyncDopeconBridgeClient
    ):
        """
        Initialize social battery monitor.
        
        Args:
            user_id: User identifier
            initial_level: Starting battery level (default 100%)
            bridge_client: DopeconBridge client for persistence
        """
        self.user_id = user_id
        self.battery = SocialBatteryState(current_level=initial_level)
        self.bridge_client = bridge_client
        
        # History
        self.interaction_history: List[SocialInteraction] = []
        self.daily_drain_history: Dict[str, float] = {}  # date -> total drain
        
        # User preferences (can be customized)
        self.preferred_recovery_activities = [
            "Deep work session (solo coding)",
            "Short walk outside",
            "Noise-cancelling headphones + music",
            "15-minute meditation",
            "Read documentation quietly"
        ]
        
        logger.info(f"SocialBatteryMonitor initialized for user {user_id}")
    
    async def log_interaction(
        self,
        interaction_type: InteractionType,
        duration_minutes: int,
        masking_level: MaskingLevel = MaskingLevel.MEDIUM,
        participants_count: int = 1,
        description: Optional[str] = None,
        calendar_event_id: Optional[str] = None
    ) -> SocialInteraction:
        """
        Log a social interaction and update battery.
        
        Args:
            interaction_type: Type of interaction
            duration_minutes: How long the interaction lasted
            masking_level: How much masking was required
            participants_count: Number of participants
            description: Optional description
            calendar_event_id: Optional calendar event ID
        
        Returns:
            SocialInteraction record with calculated drain
        """
        interaction = SocialInteraction(
            interaction_id=f"SI-{len(self.interaction_history)+1}",
            interaction_type=interaction_type,
            masking_level=masking_level,
            start_time=datetime.now(),
            duration_minutes=duration_minutes,
            participants_count=participants_count,
            description=description,
            calendar_event_id=calendar_event_id
        )
        
        # Calculate drain
        drain = interaction.calculate_drain()
        
        # Update battery
        self.battery.drain(drain)
        
        # Store in history
        self.interaction_history.append(interaction)
        
        # Update daily drain
        today = datetime.now().date().isoformat()
        self.daily_drain_history[today] = (
            self.daily_drain_history.get(today, 0.0) + drain
        )
        
        logger.info(
            f"Logged interaction: {interaction_type.value}, "
            f"drain={drain:.1f}, battery now at {self.battery.current_level:.1f}%"
        )
        
        # Persist to ConPort
        if self.bridge_client:
            try:
                await self.bridge_client.log_custom_data(
                    workspace_id=self.user_id,
                    category="social_battery",
                    key=f"interaction_{interaction.interaction_id}",
                    value={
                        "type": interaction_type.value,
                        "duration": duration_minutes,
                        "masking": masking_level.value,
                        "drain": drain,
                        "battery_after": self.battery.current_level,
                        "timestamp": datetime.now().isoformat()
                    }
                )
            except Exception as e:
                logger.error(f"Failed to persist interaction to ConPort: {e}")
        
        return interaction
    
    async def get_current_state(self) -> Dict[str, Any]:
        """
        Get current social battery state.
        
        Returns:
            {
                "level": 75.5,
                "status": "optimal",
                "emoji": "🔋",
                "last_interaction": {...},
                "time_since_last_drain": "2h 15min",
                "today_drain": 45.2
            }
        """
        last_interaction = (
            self.interaction_history[-1] if self.interaction_history else None
        )
        
        time_since_last = None
        if last_interaction:
            delta = datetime.now() - last_interaction.start_time
            hours = int(delta.total_seconds() // 3600)
            minutes = int((delta.total_seconds() % 3600) // 60)
            time_since_last = f"{hours}h {minutes}min"
        
        today = datetime.now().date().isoformat()
        today_drain = self.daily_drain_history.get(today, 0.0)
        
        return {
            "level": round(self.battery.current_level, 1),
            "status": self._get_status_label(),
            "emoji": self.battery.get_status_emoji(),
            "last_interaction": (
                {
                    "type": last_interaction.interaction_type.value,
                    "duration": last_interaction.duration_minutes,
                    "drain": last_interaction.energy_drain
                } if last_interaction else None
            ),
            "time_since_last_drain": time_since_last,
            "today_total_drain": round(today_drain, 1)
        }
    
    def _get_status_label(self) -> str:
        """Get status label for current battery level."""
        if self.battery.is_critical():
            return "critical"
        elif self.battery.is_low():
            return "low"
        elif self.battery.is_optimal():
            return "optimal"
        else:
            return "medium"
    
    async def check_and_recommend_recovery(self) -> Optional[RecoveryRecommendation]:
        """
        Check if recovery is needed and generate recommendation.
        
        Returns:
            RecoveryRecommendation if recovery needed, None otherwise
        """
        if not self.battery.is_critical() and not self.battery.is_low():
            # Battery healthy, no recovery needed
            return None
        
        if self.battery.is_critical():
            # Critical: immediate recovery required
            return RecoveryRecommendation(
                recovery_type="immediate",
                recommended_duration_minutes=60,
                activities=[
                    "🚨 STOP: Social battery critically low",
                    "Cancel non-essential meetings if possible",
                    "Block next hour for recovery",
                    "Switch to async communication only",
                    *self.preferred_recovery_activities[:2]
                ],
                urgency="critical",
                rationale=(
                    f"Battery at {self.battery.current_level:.0f}% (critical). "
                    "Continued social interaction will lead to burnout. "
                    "Immediate recovery required."
                )
            )
        
        elif self.battery.is_low():
            # Low: scheduled recovery recommended
            return RecoveryRecommendation(
                recovery_type="scheduled",
                recommended_duration_minutes=30,
                activities=[
                    f"⚠️ Battery low ({self.battery.current_level:.0f}%)",
                    "Schedule 30min recovery before next meeting",
                    "Prefer async communication for next few hours",
                    *self.preferred_recovery_activities[:3]
                ],
                urgency="high",
                rationale=(
                    f"Battery at {self.battery.current_level:.0f}% (low). "
                    "Recovery recommended before additional social interactions."
                )
            )
        
        return None
    
    async def recharge_session(self, duration_minutes: int) -> Dict[str, Any]:
        """
        Log a recovery/recharge session.
        
        Args:
            duration_minutes: Duration of recovery session
        
        Returns:
            {
                "recharge_amount": 15.5,
                "battery_before": 35.0,
                "battery_after": 50.5,
                "status": "Recharged to medium level"
            }
        """
        battery_before = self.battery.current_level
        
        # Recharge rate: ~0.5 points per minute of deep work
        recharge_amount = duration_minutes * 0.5
        
        self.battery.recharge(recharge_amount)
        
        logger.info(
            f"Recharge session: {duration_minutes}min, "
            f"+{recharge_amount:.1f} points, "
            f"battery now at {self.battery.current_level:.1f}%"
        )
        
        # Persist to ConPort
        if self.bridge_client:
            try:
                await self.bridge_client.log_custom_data(
                    workspace_id=self.user_id,
                    category="social_battery",
                    key=f"recharge_{datetime.now().isoformat()}",
                    value={
                        "duration": duration_minutes,
                        "recharge_amount": recharge_amount,
                        "battery_after": self.battery.current_level,
                        "timestamp": datetime.now().isoformat()
                    }
                )
            except Exception as e:
                logger.error(f"Failed to persist recharge to ConPort: {e}")
        
        return {
            "recharge_amount": round(recharge_amount, 1),
            "battery_before": round(battery_before, 1),
            "battery_after": round(self.battery.current_level, 1),
            "status": f"Recharged to {self._get_status_label()} level"
        }
    
    async def predict_calendar_impact(
        self,
        upcoming_events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Predict social battery impact of upcoming calendar events.
        
        Args:
            upcoming_events: List of calendar events
                [
                    {
                        "title": "Team standup",
                        "start_time": "2026-02-02T10:00:00",
                        "duration_minutes": 15,
                        "participants_count": 8,
                        "event_type": "meeting_small"  # Optional, auto-detect if missing
                    }
                ]
        
        Returns:
            {
                "current_level": 75.0,
                "predicted_end_of_day_level": 25.0,
                "total_drain_predicted": 50.0,
                "critical_events": [...]  # Events that will push below critical
                "recommended_adjustments": [...]
            }
        """
        current_level = self.battery.current_level
        predicted_level = current_level
        critical_events = []
        total_drain = 0.0
        
        for event in upcoming_events:
            # Auto-detect interaction type if not provided
            interaction_type = self._detect_interaction_type(event)
            masking_level = self._estimate_masking_level(event)
            
            # Calculate predicted drain
            drain_rate = InteractionDrainRate.get_drain_rate(
                interaction_type,
                masking_level
            )
            
            duration = event.get("duration_minutes", 30)
            participants = event.get("participants_count", 5)
            
            # Participant multiplier
            if participants <= 2:
                multiplier = 1.0
            elif participants <= 5:
                multiplier = 1.2
            elif participants <= 10:
                multiplier = 1.5
            else:
                multiplier = 2.0
            
            event_drain = drain_rate * duration * multiplier
            predicted_level -= event_drain
            total_drain += event_drain
            
            # Check if this event pushes us below critical
            if predicted_level < SocialBatteryState.CRITICAL_THRESHOLD:
                critical_events.append({
                    "title": event.get("title", "Unknown event"),
                    "start_time": event.get("start_time"),
                    "predicted_battery_after": round(predicted_level, 1),
                    "drain": round(event_drain, 1)
                })
        
        # Generate recommendations
        recommendations = []
        if predicted_level < SocialBatteryState.CRITICAL_THRESHOLD:
            recommendations.append(
                "⚠️ Day will end with critically low battery"
            )
            recommendations.append(
                "Consider: Cancel/reschedule non-essential meetings"
            )
            recommendations.append(
                "Block recovery time between meetings"
            )
        elif predicted_level < SocialBatteryState.LOW_THRESHOLD:
            recommendations.append(
                "Battery will be low by end of day"
            )
            recommendations.append(
                "Schedule recovery time in afternoon"
            )
        
        return {
            "current_level": round(current_level, 1),
            "predicted_end_of_day_level": round(predicted_level, 1),
            "total_drain_predicted": round(total_drain, 1),
            "critical_events": critical_events,
            "recommended_adjustments": recommendations
        }
    
    def _detect_interaction_type(self, event: Dict[str, Any]) -> InteractionType:
        """Auto-detect interaction type from calendar event."""
        event_type = event.get("event_type")
        if event_type:
            return InteractionType(event_type)
        
        # Auto-detect based on title and participants
        title = event.get("title", "").lower()
        participants = event.get("participants_count", 5)
        
        if any(kw in title for kw in ["present", "demo", "showcase"]):
            return InteractionType.PRESENTATION
        elif participants > 10:
            return InteractionType.MEETING_LARGE
        elif participants >= 3:
            return InteractionType.MEETING_SMALL
        elif participants == 2:
            return InteractionType.ONE_ON_ONE
        else:
            return InteractionType.CASUAL
    
    def _estimate_masking_level(self, event: Dict[str, Any]) -> MaskingLevel:
        """Estimate required masking level from calendar event."""
        masking = event.get("masking_level")
        if masking:
            return MaskingLevel(masking)
        
        # Auto-detect based on event characteristics
        title = event.get("title", "").lower()
        
        if any(kw in title for kw in ["client", "executive", "board", "demo"]):
            return MaskingLevel.HIGH
        elif any(kw in title for kw in ["team", "standup", "sync"]):
            return MaskingLevel.MEDIUM
        elif any(kw in title for kw in ["1:1", "coffee", "chat"]):
            return MaskingLevel.LOW
        else:
            return MaskingLevel.MEDIUM
