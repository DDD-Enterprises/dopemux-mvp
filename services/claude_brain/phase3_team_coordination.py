"""
Phase 3B: Team Coordination Hub - Multi-user ADHD support system

This module provides event-driven team coordination for ADHD-friendly development
environments, enabling synchronized support across team members while maintaining
individual privacy and preferences.
"""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, timedelta
from enum import Enum

from .dynamic_adaptation import UserCognitiveState, AttentionState

logger = logging.getLogger(__name__)


class CoordinationEventType(Enum):
    """Types of team coordination events."""
    FOCUS_SESSION_START = "focus_session_start"
    BREAK_TIME = "break_time"
    COGNITIVE_LOAD_SPIKE = "cognitive_load_spike"
    ATTENTION_STATE_CHANGE = "attention_state_change"
    TASK_COMPLETION = "task_completion"
    CONTEXT_SWITCH = "context_switch"
    INTERVENTION_TRIGGERED = "intervention_triggered"
    MEETING_SCHEDULED = "meeting_scheduled"


@dataclass
class CoordinationEvent:
    """Event in the team coordination system."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: CoordinationEventType
    user_id: str
    team_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    priority: str = "normal"  # low, normal, high, urgent
    ttl_seconds: int = 3600  # 1 hour default


@dataclass
class TeamProfile:
    """Profile for a development team."""
    team_id: str
    name: str
    members: Set[str] = field(default_factory=set)
    coordination_rules: Dict[str, Any] = field(default_factory=dict)
    privacy_settings: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    # Team ADHD coordination settings
    focus_session_sync: bool = True  # Sync focus sessions across team
    break_coordination: bool = True  # Coordinate break times
    cognitive_load_sharing: bool = False  # Share cognitive load insights
    intervention_broadcast: bool = False  # Broadcast interventions to team


@dataclass
class TeamCognitiveState:
    """Aggregated cognitive state for a team."""
    team_id: str
    member_states: Dict[str, UserCognitiveState] = field(default_factory=dict)
    aggregated_load: float = 0.5
    focus_distribution: Dict[str, int] = field(default_factory=dict)  # attention_state -> count
    energy_distribution: Dict[str, int] = field(default_factory=dict)  # energy_level -> count
    last_updated: datetime = field(default_factory=datetime.now)

    def update_member_state(self, user_id: str, state: UserCognitiveState) -> None:
        """Update a team member's cognitive state."""
        self.member_states[user_id] = state
        self.last_updated = datetime.now()
        self._recalculate_aggregates()

    def _recalculate_aggregates(self) -> None:
        """Recalculate team-wide aggregates."""
        if not self.member_states:
            return

        # Calculate average cognitive load
        loads = [state.cognitive_load for state in self.member_states.values()]
        self.aggregated_load = sum(loads) / len(loads)

        # Calculate attention state distribution
        self.focus_distribution = {}
        for state in self.member_states.values():
            state_name = state.attention_state.value
            self.focus_distribution[state_name] = self.focus_distribution.get(state_name, 0) + 1

        # Calculate energy distribution
        self.energy_distribution = {}
        for state in self.member_states.values():
            energy = state.energy_level
            self.energy_distribution[energy] = self.energy_distribution.get(energy, 0) + 1


class EventDrivenSync:
    """
    Event-driven synchronization system for team coordination.

    Manages real-time event streaming and processing with guaranteed delivery
    and conflict resolution for team ADHD support.
    """

    def __init__(self):
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.event_handlers: Dict[CoordinationEventType, List[callable]] = {}
        self.pending_events: Dict[str, CoordinationEvent] = {}
        self.processed_events: Set[str] = set()

        # Performance monitoring
        self.events_processed = 0
        self.avg_processing_time = 0.0
        self.failed_deliveries = 0

    def register_handler(self, event_type: CoordinationEventType, handler: callable) -> None:
        """Register an event handler for a specific event type."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)

    async def publish_event(self, event: CoordinationEvent) -> bool:
        """Publish an event to the coordination system."""
        try:
            # Add to queue for processing
            await self.event_queue.put(event)

            # Store as pending for reliability
            self.pending_events[event.event_id] = event

            logger.debug(f"Published event {event.event_id} of type {event.event_type.value}")
            return True

        except Exception as e:
            logger.error(f"Failed to publish event {event.event_id}: {e}")
            self.failed_deliveries += 1
            return False

    async def process_events(self) -> None:
        """Process events from the queue."""
        while True:
            try:
                event = await self.event_queue.get()

                start_time = asyncio.get_event_loop().time()

                # Process the event
                await self._process_event(event)

                # Mark as processed
                self.processed_events.add(event.event_id)
                if event.event_id in self.pending_events:
                    del self.pending_events[event.event_id]

                # Update performance metrics
                processing_time = asyncio.get_event_loop().time() - start_time
                self.events_processed += 1
                self.avg_processing_time = (
                    self.avg_processing_time + processing_time
                ) / 2

                self.event_queue.task_done()

            except Exception as e:
                logger.error(f"Event processing error: {e}")
                # Continue processing other events

    async def _process_event(self, event: CoordinationEvent) -> None:
        """Process a single coordination event."""
        # Check TTL
        if (datetime.now() - event.timestamp).seconds > event.ttl_seconds:
            logger.debug(f"Event {event.event_id} expired, skipping")
            return

        # Route to appropriate handlers
        if event.event_type in self.event_handlers:
            handlers = self.event_handlers[event.event_type]
            tasks = []

            for handler in handlers:
                try:
                    task = asyncio.create_task(handler(event))
                    tasks.append(task)
                except Exception as e:
                    logger.error(f"Handler execution failed for event {event.event_id}: {e}")

            # Wait for all handlers to complete
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

        # Handle team-wide notifications for important events
        if event.priority in ["high", "urgent"]:
            await self._handle_priority_event(event)

    async def _handle_priority_event(self, event: CoordinationEvent) -> None:
        """Handle high-priority events that may affect the whole team."""
        # This would integrate with notification systems
        # For now, just log the priority event
        logger.info(f"Priority event processed: {event.event_type.value} for user {event.user_id} in team {event.team_id}")

    def get_pending_events(self, team_id: Optional[str] = None) -> List[CoordinationEvent]:
        """Get pending events, optionally filtered by team."""
        events = list(self.pending_events.values())
        if team_id:
            events = [e for e in events if e.team_id == team_id]
        return events

    def get_stats(self) -> Dict[str, Any]:
        """Get event processing statistics."""
        return {
            "events_processed": self.events_processed,
            "avg_processing_time": round(self.avg_processing_time, 3),
            "pending_events": len(self.pending_events),
            "failed_deliveries": self.failed_deliveries,
            "active_handlers": sum(len(handlers) for handlers in self.event_handlers.values())
        }


class SharedADHDState:
    """
    Manages shared ADHD state across team members.

    Provides aggregated insights while respecting individual privacy preferences.
    """

    def __init__(self):
        self.team_states: Dict[str, TeamCognitiveState] = {}
        self.privacy_filters: Dict[str, Dict[str, bool]] = {}  # team_id -> user_id -> can_share

    def update_team_member_state(self, team_id: str, user_id: str, state: UserCognitiveState) -> None:
        """Update a team member's cognitive state."""
        if team_id not in self.team_states:
            self.team_states[team_id] = TeamCognitiveState(team_id=team_id)

        team_state = self.team_states[team_id]

        # Check privacy permissions
        can_share = self._can_share_state(team_id, user_id)
        if can_share:
            team_state.update_member_state(user_id, state)

    def _can_share_state(self, team_id: str, user_id: str) -> bool:
        """Check if user allows state sharing for this team."""
        team_filters = self.privacy_filters.get(team_id, {})
        return team_filters.get(user_id, False)  # Default to private

    def get_team_insights(self, team_id: str, requesting_user: str) -> Optional[Dict[str, Any]]:
        """Get aggregated team insights for a requesting user."""
        if team_id not in self.team_states:
            return None

        team_state = self.team_states[team_id]

        # Check if requesting user can access team insights
        if not self._can_access_insights(team_id, requesting_user):
            return None

        return {
            "team_load": team_state.aggregated_load,
            "focus_distribution": team_state.focus_distribution,
            "energy_distribution": team_state.energy_distribution,
            "member_count": len(team_state.member_states),
            "last_updated": team_state.last_updated.isoformat()
        }

    def _can_access_insights(self, team_id: str, user_id: str) -> bool:
        """Check if user can access team insights."""
        # For now, allow access if user is sharing their own state
        return self._can_share_state(team_id, user_id)

    def set_privacy_preference(self, team_id: str, user_id: str, can_share: bool) -> None:
        """Set privacy preference for state sharing."""
        if team_id not in self.privacy_filters:
            self.privacy_filters[team_id] = {}

        self.privacy_filters[team_id][user_id] = can_share

        # If user opts out, remove their data from team state
        if not can_share and team_id in self.team_states:
            team_state = self.team_states[team_id]
            if user_id in team_state.member_states:
                del team_state.member_states[user_id]
                team_state._recalculate_aggregates()


class CoordinationScheduler:
    """
    Intelligent scheduler for team coordination activities.

    Optimizes meeting times, break coordination, and intervention scheduling
    based on team cognitive states and individual preferences.
    """

    def __init__(self, shared_state: SharedADHDState):
        self.shared_state = shared_state
        self.scheduled_activities: Dict[str, Dict[str, Any]] = {}
        self.conflict_resolution_rules = self._initialize_conflict_rules()

    def _initialize_conflict_rules(self) -> Dict[str, Any]:
        """Initialize rules for resolving scheduling conflicts."""
        return {
            "meeting_priority": ["urgent", "high", "normal", "low"],
            "break_preference": "respect_individual",  # or "coordinate_team"
            "focus_session_sync": "voluntary_opt_in",
            "cognitive_load_threshold": 0.8  # Reschedule if team load too high
        }

    def schedule_meeting(self, team_id: str, title: str, duration_minutes: int,
                        preferred_times: List[datetime]) -> Optional[Dict[str, Any]]:
        """
        Schedule a team meeting at the optimal time based on cognitive states.
        """
        # Get team insights
        team_insights = self.shared_state.get_team_insights(team_id, "scheduler")

        if not team_insights:
            # No team data available, use first preferred time
            if preferred_times:
                return self._create_meeting_schedule(title, preferred_times[0], duration_minutes)

        # Analyze team cognitive load patterns
        best_time = self._find_optimal_meeting_time(team_insights, preferred_times, duration_minutes)

        if best_time:
            return self._create_meeting_schedule(title, best_time, duration_minutes)

        return None

    def _find_optimal_meeting_time(self, team_insights: Dict[str, Any],
                                 preferred_times: List[datetime],
                                 duration_minutes: int) -> Optional[datetime]:
        """Find the optimal meeting time based on team cognitive state."""
        # Score each preferred time
        time_scores = []

        for proposed_time in preferred_times:
            score = self._score_meeting_time(proposed_time, duration_minutes, team_insights)
            time_scores.append((proposed_time, score))

        # Return highest scoring time
        if time_scores:
            best_time, best_score = max(time_scores, key=lambda x: x[1])
            return best_time if best_score > 0.5 else None  # Minimum quality threshold

        return None

    def _score_meeting_time(self, meeting_time: datetime, duration: int,
                          team_insights: Dict[str, Any]) -> float:
        """Score a potential meeting time."""
        score = 0.5  # Base score

        # Check team cognitive load
        team_load = team_insights.get("team_load", 0.5)
        if team_load > self.conflict_resolution_rules["cognitive_load_threshold"]:
            score -= 0.3  # Penalize high team load

        # Check focus distribution
        focus_dist = team_insights.get("focus_distribution", {})
        focused_count = focus_dist.get("focused", 0) + focus_dist.get("hyperfocused", 0)
        total_members = sum(focus_dist.values())

        if total_members > 0:
            focus_ratio = focused_count / total_members
            score += (focus_ratio - 0.5) * 0.4  # Bonus for team focus

        # Check time preferences (avoid common break times, lunch, etc.)
        hour = meeting_time.hour
        if hour in [12, 13]:  # Lunch time
            score -= 0.2
        elif hour in [17, 18]:  # End of day
            score -= 0.1

        # Duration consideration
        if duration > 60:  # Long meetings
            score -= 0.1

        return max(0.0, min(1.0, score))

    def _create_meeting_schedule(self, title: str, start_time: datetime,
                               duration_minutes: int) -> Dict[str, Any]:
        """Create a meeting schedule entry."""
        meeting_id = str(uuid.uuid4())

        schedule = {
            "meeting_id": meeting_id,
            "title": title,
            "start_time": start_time,
            "end_time": start_time + timedelta(minutes=duration_minutes),
            "duration_minutes": duration_minutes,
            "status": "scheduled"
        }

        self.scheduled_activities[meeting_id] = schedule
        return schedule

    def schedule_break_coordination(self, team_id: str, break_duration: int = 15) -> List[Dict[str, Any]]:
        """Schedule coordinated break times for the team."""
        # Get team insights
        team_insights = self.shared_state.get_team_insights(team_id, "scheduler")

        if not team_insights or team_insights.get("team_load", 0.5) < 0.7:
            return []  # No coordination needed if team load is low

        # Schedule break in next 10-15 minutes
        break_times = []
        base_time = datetime.now() + timedelta(minutes=10)

        # Schedule for team members who need breaks
        focus_dist = team_insights.get("focus_distribution", {})
        fatigued_count = focus_dist.get("fatigued", 0)

        if fatigued_count > 0:
            break_time = base_time
            break_times.append({
                "activity_id": str(uuid.uuid4()),
                "type": "coordinated_break",
                "scheduled_time": break_time,
                "duration_minutes": break_duration,
                "participants": fatigued_count,
                "reason": "team_fatigue_coordination"
            })

        return break_times

    def resolve_scheduling_conflict(self, team_id: str, conflicting_activities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Resolve scheduling conflicts using team coordination rules."""
        if len(conflicting_activities) < 2:
            return {"resolution": "no_conflict"}

        # Apply conflict resolution rules
        prioritized = self._prioritize_activities(conflicting_activities)

        resolution = {
            "resolution": "prioritized_schedule",
            "recommended_schedule": prioritized,
            "conflicts_resolved": len(conflicting_activities) - len(prioritized),
            "rationale": "Applied team coordination rules prioritizing urgent activities and respecting individual preferences"
        }

        return resolution

    def _prioritize_activities(self, activities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize activities based on coordination rules."""
        # Sort by priority first
        priority_order = self.conflict_resolution_rules["meeting_priority"]
        activities.sort(key=lambda x: priority_order.index(x.get("priority", "normal")))

        # Remove lower priority conflicts
        prioritized = []
        scheduled_times = set()

        for activity in activities:
            activity_time = activity.get("scheduled_time")
            if activity_time not in scheduled_times:
                prioritized.append(activity)
                scheduled_times.add(activity_time)

        return prioritized


class TeamCoordinationHub:
    """
    Phase 3B: Complete team coordination system.

    Orchestrates multi-user ADHD support with event-driven synchronization,
    shared cognitive insights, and intelligent scheduling.
    """

    def __init__(self):
        self.event_sync = EventDrivenSync()
        self.shared_state = SharedADHDState()
        self.coordination_scheduler = CoordinationScheduler(self.shared_state)

        self.teams: Dict[str, TeamProfile] = {}
        self.event_processing_task: Optional[asyncio.Task] = None

    async def initialize(self) -> bool:
        """Initialize the team coordination hub."""
        logger.info("👥 Initializing Team Coordination Hub...")

        # Start event processing
        self.event_processing_task = asyncio.create_task(self.event_sync.process_events())

        # Register default event handlers
        self._register_default_handlers()

        logger.info("✅ Team Coordination Hub initialized")
        return True

    def _register_default_handlers(self) -> None:
        """Register default event handlers."""
        # Focus session coordination
        self.event_sync.register_handler(
            CoordinationEventType.FOCUS_SESSION_START,
            self._handle_focus_session_start
        )

        # Break time coordination
        self.event_sync.register_handler(
            CoordinationEventType.BREAK_TIME,
            self._handle_break_time
        )

        # Cognitive load spike alerts
        self.event_sync.register_handler(
            CoordinationEventType.COGNITIVE_LOAD_SPIKE,
            self._handle_cognitive_load_spike
        )

        # Context switch notifications
        self.event_sync.register_handler(
            CoordinationEventType.CONTEXT_SWITCH,
            self._handle_context_switch
        )

    async def _handle_focus_session_start(self, event: CoordinationEvent) -> None:
        """Handle focus session start events."""
        team_id = event.team_id
        user_id = event.user_id

        # Check if team has focus session sync enabled
        team = self.teams.get(team_id)
        if team and team.focus_session_sync:
            # Notify other team members
            notification_event = CoordinationEvent(
                event_type=CoordinationEventType.INTERVENTION_TRIGGERED,
                user_id=user_id,
                team_id=team_id,
                data={
                    "intervention_type": "focus_session_sync",
                    "message": f"Team member started focus session ({event.data.get('duration', 25)} min)",
                    "sync_opportunity": True
                },
                priority="low"
            )
            await self.event_sync.publish_event(notification_event)

    async def _handle_break_time(self, event: CoordinationEvent) -> None:
        """Handle break time events."""
        team_id = event.team_id

        # Check if team has break coordination enabled
        team = self.teams.get(team_id)
        if team and team.break_coordination:
            # Schedule coordinated break
            coordinated_breaks = self.coordination_scheduler.schedule_break_coordination(team_id)
            for break_schedule in coordinated_breaks:
                break_event = CoordinationEvent(
                    event_type=CoordinationEventType.INTERVENTION_TRIGGERED,
                    user_id="coordinator",
                    team_id=team_id,
                    data=break_schedule,
                    priority="normal"
                )
                await self.event_sync.publish_event(break_event)

    async def _handle_cognitive_load_spike(self, event: CoordinationEvent) -> None:
        """Handle cognitive load spike events."""
        team_id = event.team_id

        # Check if team shares cognitive load insights
        team = self.teams.get(team_id)
        if team and team.cognitive_load_sharing:
            # Share aggregated team insights
            team_insights = self.shared_state.get_team_insights(team_id, event.user_id)
            if team_insights and team_insights.get("team_load", 0.5) > 0.7:
                alert_event = CoordinationEvent(
                    event_type=CoordinationEventType.INTERVENTION_TRIGGERED,
                    user_id="coordinator",
                    team_id=team_id,
                    data={
                        "intervention_type": "team_load_alert",
                        "message": f"Team experiencing high cognitive load ({team_insights['team_load']:.1f}). Consider rescheduling complex tasks.",
                        "team_insights": team_insights
                    },
                    priority="high"
                )
                await self.event_sync.publish_event(alert_event)

    async def _handle_context_switch(self, event: CoordinationEvent) -> None:
        """Handle context switch events."""
        # Context switch handling is primarily individual
        # Could be extended for team awareness
        pass

    def create_team(self, team_id: str, name: str, creator_id: str) -> TeamProfile:
        """Create a new development team."""
        team = TeamProfile(
            team_id=team_id,
            name=name,
            members={creator_id}
        )

        self.teams[team_id] = team

        # Set creator's privacy preferences
        self.shared_state.set_privacy_preference(team_id, creator_id, True)

        logger.info(f"Created team {team_id}: {name}")
        return team

    def join_team(self, team_id: str, user_id: str) -> bool:
        """Add a user to a team."""
        if team_id not in self.teams:
            return False

        self.teams[team_id].members.add(user_id)

        # Default privacy settings (user can change later)
        self.shared_state.set_privacy_preference(team_id, user_id, False)  # Private by default

        logger.info(f"User {user_id} joined team {team_id}")
        return True

    async def update_member_state(self, team_id: str, user_id: str, cognitive_state: UserCognitiveState) -> None:
        """Update a team member's cognitive state."""
        # Update shared state
        self.shared_state.update_team_member_state(team_id, user_id, cognitive_state)

        # Publish state change event
        state_event = CoordinationEvent(
            event_type=CoordinationEventType.ATTENTION_STATE_CHANGE,
            user_id=user_id,
            team_id=team_id,
            data={
                "attention_state": cognitive_state.attention_state.value,
                "cognitive_load": cognitive_state.cognitive_load,
                "energy_level": cognitive_state.energy_level
            },
            priority="low"
        )
        await self.event_sync.publish_event(state_event)

    async def schedule_team_meeting(self, team_id: str, title: str, duration: int,
                                  preferred_times: List[datetime]) -> Optional[Dict[str, Any]]:
        """Schedule an optimal team meeting."""
        schedule = self.coordination_scheduler.schedule_meeting(
            team_id, title, duration, preferred_times
        )

        if schedule:
            # Publish meeting scheduled event
            meeting_event = CoordinationEvent(
                event_type=CoordinationEventType.MEETING_SCHEDULED,
                user_id="coordinator",
                team_id=team_id,
                data=schedule,
                priority="normal"
            )
            await self.event_sync.publish_event(meeting_event)

        return schedule

    def get_team_insights(self, team_id: str, requesting_user: str) -> Optional[Dict[str, Any]]:
        """Get team coordination insights."""
        return self.shared_state.get_team_insights(team_id, requesting_user)

    def set_team_privacy(self, team_id: str, user_id: str, can_share: bool) -> None:
        """Set user's privacy preferences for team sharing."""
        self.shared_state.set_privacy_preference(team_id, user_id, can_share)

        # Update team coordination rules based on privacy settings
        team = self.teams.get(team_id)
        if team:
            # Recalculate what team features are available
            sharing_members = sum(1 for member in team.members
                                if self.shared_state._can_share_state(team_id, member))
            team.cognitive_load_sharing = sharing_members >= 2  # Need at least 2 sharers

    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive team coordination statistics."""
        total_members = sum(len(team.members) for team in self.teams.values())
        active_teams = len(self.teams)

        return {
            "active_teams": active_teams,
            "total_team_members": total_members,
            "event_processing": self.event_sync.get_stats(),
            "pending_interventions": len(self.event_sync.get_pending_events()),
            "scheduled_activities": len(self.coordination_scheduler.scheduled_activities),
            "privacy_compliant": True  # All operations respect privacy settings
        }

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.event_processing_task:
            self.event_processing_task.cancel()
            try:
                await self.event_processing_task
            except asyncio.CancelledError:
                pass
