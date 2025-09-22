"""
Session Manager: ADHD-friendly session lifecycle management

The Session Manager handles the complete lifecycle of MetaMCP sessions with
special focus on ADHD accommodations including context preservation, gentle
transitions, automated checkpointing, and integration with external memory
systems like Letta.

Key Features:
- Automatic session initialization and cleanup
- Context preservation across interruptions and role switches
- ADHD-optimized checkpointing (every 25 minutes by default)
- Integration with Letta memory system for context offload
- Gentle notifications and progress tracking
- Session analytics and patterns recognition

Design Principles:
- Never lose context: Multiple backup mechanisms for session state
- Gentle transitions: Smooth handoffs between roles and activities
- Progressive disclosure: Show relevant information at the right time
- Memory offload: Use external memory to prevent context window bloat
- Analytics-driven: Learn from patterns to improve user experience
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class SessionPhase(Enum):
    """Different phases of a development session"""
    INITIALIZATION = "initialization"
    PLANNING = "planning"
    IMPLEMENTATION = "implementation"
    REVIEW = "review"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    REFLECTION = "reflection"
    BREAK = "break"
    CONTEXT_SWITCH = "context_switch"


class CheckpointType(Enum):
    """Types of checkpoints for different purposes"""
    POMODORO_AUTO = "pomodoro_auto"      # Automatic 25-minute checkpoint
    ROLE_SWITCH = "role_switch"          # Before/after role changes
    TASK_COMPLETE = "task_complete"      # Task completion milestone
    ERROR_RECOVERY = "error_recovery"    # Before attempting error resolution
    MANUAL = "manual"                    # User-requested checkpoint
    SESSION_END = "session_end"          # Final checkpoint before ending
    CONTEXT_SWITCH = "context_switch"    # When switching contexts/projects
    BREAK_START = "break_start"          # Beginning of a break
    BREAK_END = "break_end"              # Returning from a break


@dataclass
class ContextSnapshot:
    """Snapshot of context at a specific moment"""
    timestamp: datetime
    checkpoint_type: CheckpointType
    session_id: str
    role: Optional[str] = None
    active_task: Optional[str] = None
    file_context: Optional[str] = None
    line_number: Optional[int] = None
    mental_model: str = ""
    next_steps: List[str] = field(default_factory=list)
    decisions_made: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    energy_level: str = "medium"  # low, medium, high
    focus_quality: str = "good"   # poor, fair, good, excellent

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['checkpoint_type'] = self.checkpoint_type.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContextSnapshot':
        """Create from dictionary"""
        data = data.copy()
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['checkpoint_type'] = CheckpointType(data['checkpoint_type'])
        return cls(**data)


@dataclass
class SessionMetrics:
    """Metrics and analytics for a session"""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_duration: timedelta = field(default_factory=lambda: timedelta(0))

    # Role usage
    roles_used: Set[str] = field(default_factory=set)
    role_transitions: int = 0
    current_role: Optional[str] = None

    # Activity tracking
    tools_used: Set[str] = field(default_factory=set)
    tool_calls: int = 0
    checkpoints_created: int = 0
    breaks_taken: int = 0

    # ADHD-specific metrics
    context_switches: int = 0
    focus_duration: timedelta = field(default_factory=lambda: timedelta(0))
    interruption_count: int = 0
    recovery_time: timedelta = field(default_factory=lambda: timedelta(0))

    # Productivity metrics
    tasks_completed: int = 0
    decisions_made: int = 0
    blockers_encountered: int = 0

    @property
    def average_focus_duration(self) -> timedelta:
        """Average focus duration between interruptions"""
        if self.interruption_count == 0:
            return self.focus_duration
        return self.focus_duration / max(self.interruption_count, 1)

    @property
    def productivity_score(self) -> float:
        """Simple productivity score based on tasks completed vs time"""
        if self.total_duration.total_seconds() == 0:
            return 0.0
        hours = self.total_duration.total_seconds() / 3600
        return min(self.tasks_completed / max(hours, 0.1), 10.0)


@dataclass
class SessionState:
    """Complete state of an active session"""
    session_id: str
    created_at: datetime
    last_activity: datetime
    current_phase: SessionPhase = SessionPhase.INITIALIZATION

    # Context preservation
    context_snapshots: List[ContextSnapshot] = field(default_factory=list)
    current_context: Optional[ContextSnapshot] = None

    # Session configuration
    adhd_accommodations: Dict[str, Any] = field(default_factory=dict)
    break_reminders: bool = True
    checkpoint_interval: int = 1500  # 25 minutes in seconds

    # Analytics
    metrics: SessionMetrics = field(init=False)

    def __post_init__(self):
        if not hasattr(self, 'metrics'):
            self.metrics = SessionMetrics(
                session_id=self.session_id,
                start_time=self.created_at
            )


class SessionManager:
    """
    Manages session lifecycle with ADHD accommodations and context preservation.

    The SessionManager provides comprehensive session management including
    automatic checkpointing, context preservation, memory integration,
    and analytics for continuous improvement.
    """

    def __init__(self, policy_config: Dict[str, Any], letta_client=None):
        self.policy_config = policy_config
        self.letta_client = letta_client

        # ADHD configuration from policy
        adhd_config = policy_config.get('rules', {}).get('adhd_optimizations', {})
        self.checkpoint_interval = adhd_config.get('context_preservation', {}).get('auto_checkpoint_interval', 1500)
        self.break_reminder_enabled = adhd_config.get('break_reminders', {}).get('enabled', True)
        self.break_reminder_interval = adhd_config.get('break_reminders', {}).get('interval', 1500)

        # Active sessions
        self.active_sessions: Dict[str, SessionState] = {}

        # Background tasks
        self._background_tasks: Set[asyncio.Task] = set()

        # Session storage
        self.session_storage_path = Path("/tmp/metamcp_sessions")
        self.session_storage_path.mkdir(exist_ok=True)

        logger.info("SessionManager initialized with ADHD accommodations")

    async def create_session(self, session_id: str,
                           user_preferences: Optional[Dict[str, Any]] = None) -> SessionState:
        """Create and initialize a new session"""

        # Apply user preferences for ADHD accommodations
        adhd_accommodations = self._configure_adhd_accommodations(user_preferences or {})

        session_state = SessionState(
            session_id=session_id,
            created_at=datetime.now(),
            last_activity=datetime.now(),
            adhd_accommodations=adhd_accommodations,
            break_reminders=adhd_accommodations.get('break_reminders', True),
            checkpoint_interval=adhd_accommodations.get('checkpoint_interval', self.checkpoint_interval)
        )

        self.active_sessions[session_id] = session_state

        # Create initial checkpoint
        initial_snapshot = await self._create_context_snapshot(
            session_id, CheckpointType.POMODORO_AUTO, "Session initialized"
        )
        session_state.context_snapshots.append(initial_snapshot)
        session_state.current_context = initial_snapshot

        # Start background monitoring for this session
        await self._start_session_monitoring(session_id)

        # Save session state
        await self._save_session_state(session_state)

        logger.info(f"Created session {session_id} with ADHD accommodations: {adhd_accommodations}")

        return session_state

    async def get_session(self, session_id: str) -> Optional[SessionState]:
        """Get active session or load from storage"""
        # Check active sessions first
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]

        # Try to load from storage
        session_state = await self._load_session_state(session_id)
        if session_state:
            self.active_sessions[session_id] = session_state
            # Restart monitoring
            await self._start_session_monitoring(session_id)

        return session_state

    async def create_checkpoint(self, session_id: str, checkpoint_type: CheckpointType,
                              description: str = "", context_data: Optional[Dict[str, Any]] = None) -> ContextSnapshot:
        """Create a context checkpoint for the session"""
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"No active session: {session_id}")

        # Create snapshot with provided context
        snapshot = await self._create_context_snapshot(
            session_id, checkpoint_type, description, context_data
        )

        # Add to session
        session.context_snapshots.append(snapshot)
        session.current_context = snapshot
        session.last_activity = datetime.now()
        session.metrics.checkpoints_created += 1

        # Store in Letta if available (for persistent memory)
        if self.letta_client:
            await self._store_context_in_letta(snapshot)

        # Save session state
        await self._save_session_state(session)

        logger.info(f"Created checkpoint for session {session_id}: {checkpoint_type.value}")

        return snapshot

    async def restore_context(self, session_id: str,
                            checkpoint_index: Optional[int] = None) -> Optional[ContextSnapshot]:
        """Restore context from a specific checkpoint"""
        session = self.active_sessions.get(session_id)
        if not session or not session.context_snapshots:
            return None

        # Use latest checkpoint if no index specified
        if checkpoint_index is None:
            checkpoint_index = -1

        if abs(checkpoint_index) > len(session.context_snapshots):
            logger.error(f"Checkpoint index {checkpoint_index} out of range for session {session_id}")
            return None

        # Restore context
        restored_snapshot = session.context_snapshots[checkpoint_index]
        session.current_context = restored_snapshot
        session.last_activity = datetime.now()

        logger.info(f"Restored context for session {session_id} from checkpoint {checkpoint_index}")

        return restored_snapshot

    async def record_activity(self, session_id: str, activity_type: str,
                            details: Optional[Dict[str, Any]] = None) -> None:
        """Record user activity for analytics and pattern recognition"""
        session = self.active_sessions.get(session_id)
        if not session:
            return

        session.last_activity = datetime.now()

        # Update metrics based on activity type
        if activity_type == "tool_call":
            session.metrics.tool_calls += 1
            if details and 'tool_name' in details:
                session.metrics.tools_used.add(details['tool_name'])

        elif activity_type == "role_switch":
            session.metrics.role_transitions += 1
            if details and 'new_role' in details:
                session.metrics.roles_used.add(details['new_role'])
                session.metrics.current_role = details['new_role']

        elif activity_type == "context_switch":
            session.metrics.context_switches += 1
            # Create automatic checkpoint for context switches
            await self.create_checkpoint(
                session_id, CheckpointType.CONTEXT_SWITCH,
                f"Context switch: {details.get('description', 'Unknown')}"
            )

        elif activity_type == "task_complete":
            session.metrics.tasks_completed += 1

        elif activity_type == "break_start":
            session.metrics.breaks_taken += 1
            await self.create_checkpoint(session_id, CheckpointType.BREAK_START, "Break started")

        elif activity_type == "break_end":
            await self.create_checkpoint(session_id, CheckpointType.BREAK_END, "Returning from break")

        elif activity_type == "interruption":
            session.metrics.interruption_count += 1

        # Save updated state
        await self._save_session_state(session)

    async def end_session(self, session_id: str) -> SessionMetrics:
        """End a session and create final analytics"""
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"No active session: {session_id}")

        # Create final checkpoint
        await self.create_checkpoint(
            session_id, CheckpointType.SESSION_END, "Session ended"
        )

        # Finalize metrics
        session.metrics.end_time = datetime.now()
        session.metrics.total_duration = session.metrics.end_time - session.metrics.start_time

        # Cancel background monitoring
        await self._stop_session_monitoring(session_id)

        # Save final state
        await self._save_session_state(session)

        # Remove from active sessions
        final_metrics = session.metrics
        del self.active_sessions[session_id]

        logger.info(f"Ended session {session_id}: {final_metrics.total_duration} duration, "
                   f"{final_metrics.tasks_completed} tasks completed")

        return final_metrics

    async def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive session summary for user feedback"""
        session = self.active_sessions.get(session_id)
        if not session:
            return {}

        # Calculate session insights
        total_time = datetime.now() - session.created_at
        checkpoints_per_hour = session.metrics.checkpoints_created / max(total_time.total_seconds() / 3600, 0.1)

        # Analyze productivity patterns
        recent_checkpoints = session.context_snapshots[-5:] if len(session.context_snapshots) > 5 else session.context_snapshots
        energy_levels = [cp.energy_level for cp in recent_checkpoints if cp.energy_level]
        focus_qualities = [cp.focus_quality for cp in recent_checkpoints if cp.focus_quality]

        return {
            'session_id': session_id,
            'duration': str(total_time),
            'current_phase': session.current_phase.value,
            'roles_used': list(session.metrics.roles_used),
            'tools_used': list(session.metrics.tools_used),
            'metrics': {
                'checkpoints_created': session.metrics.checkpoints_created,
                'checkpoints_per_hour': round(checkpoints_per_hour, 1),
                'role_transitions': session.metrics.role_transitions,
                'tool_calls': session.metrics.tool_calls,
                'tasks_completed': session.metrics.tasks_completed,
                'breaks_taken': session.metrics.breaks_taken,
                'productivity_score': round(session.metrics.productivity_score, 2)
            },
            'adhd_insights': {
                'context_switches': session.metrics.context_switches,
                'interruption_count': session.metrics.interruption_count,
                'average_focus_duration': str(session.metrics.average_focus_duration),
                'recent_energy_trend': self._analyze_trend(energy_levels),
                'recent_focus_trend': self._analyze_trend(focus_qualities)
            },
            'current_context': session.current_context.to_dict() if session.current_context else None
        }

    async def suggest_break(self, session_id: str) -> Dict[str, Any]:
        """Suggest a break based on ADHD patterns and session analytics"""
        session = self.active_sessions.get(session_id)
        if not session:
            return {'suggested': False, 'reason': 'No active session'}

        current_time = datetime.now()
        session_duration = current_time - session.created_at

        # Check various break triggers
        suggestions = []

        # Time-based (Pomodoro)
        if session_duration.total_seconds() >= session.break_reminder_interval:
            suggestions.append({
                'type': 'pomodoro',
                'reason': f"You've been working for {session_duration}",
                'recommended_break': '5-10 minutes',
                'priority': 'medium'
            })

        # Energy level analysis
        if session.current_context and session.current_context.energy_level == 'low':
            suggestions.append({
                'type': 'energy',
                'reason': "Your energy level is low",
                'recommended_break': '15-20 minutes with movement',
                'priority': 'high'
            })

        # Focus quality analysis
        if session.current_context and session.current_context.focus_quality in ['poor', 'fair']:
            suggestions.append({
                'type': 'focus',
                'reason': "Focus quality has declined",
                'recommended_break': '10-15 minutes away from screen',
                'priority': 'medium'
            })

        # Interruption frequency
        recent_time = current_time - timedelta(hours=1)
        recent_interruptions = [
            cp for cp in session.context_snapshots
            if cp.timestamp >= recent_time and cp.checkpoint_type == CheckpointType.CONTEXT_SWITCH
        ]

        if len(recent_interruptions) >= 3:
            suggestions.append({
                'type': 'interruptions',
                'reason': f"Multiple interruptions in the last hour ({len(recent_interruptions)})",
                'recommended_break': '10 minutes to reset focus',
                'priority': 'high'
            })

        # Return most relevant suggestion
        if not suggestions:
            return {'suggested': False, 'reason': 'No break triggers detected'}

        # Sort by priority and return top suggestion
        priority_order = {'high': 3, 'medium': 2, 'low': 1}
        suggestions.sort(key=lambda x: priority_order.get(x['priority'], 0), reverse=True)

        return {
            'suggested': True,
            'recommendation': suggestions[0],
            'alternative_options': suggestions[1:3]  # Up to 2 alternatives
        }

    # Private helper methods

    def _configure_adhd_accommodations(self, user_preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Configure ADHD accommodations based on user preferences"""
        defaults = {
            'break_reminders': True,
            'checkpoint_interval': self.checkpoint_interval,
            'gentle_notifications': True,
            'progressive_disclosure': True,
            'context_preservation': True,
            'focus_mode_available': True
        }

        # Apply user preferences
        accommodations = defaults.copy()

        if 'attention_span' in user_preferences:
            if user_preferences['attention_span'] == 'short':
                accommodations['checkpoint_interval'] = 900  # 15 minutes
            elif user_preferences['attention_span'] == 'long':
                accommodations['checkpoint_interval'] = 2700  # 45 minutes

        if 'interruption_sensitivity' in user_preferences:
            if user_preferences['interruption_sensitivity'] == 'high':
                accommodations['gentle_notifications'] = True
                accommodations['progressive_disclosure'] = True

        return accommodations

    async def _create_context_snapshot(self, session_id: str, checkpoint_type: CheckpointType,
                                     description: str, context_data: Optional[Dict[str, Any]] = None) -> ContextSnapshot:
        """Create a detailed context snapshot"""
        session = self.active_sessions.get(session_id)

        # Gather context information
        context_data = context_data or {}

        snapshot = ContextSnapshot(
            timestamp=datetime.now(),
            checkpoint_type=checkpoint_type,
            session_id=session_id,
            role=context_data.get('role'),
            active_task=context_data.get('active_task'),
            file_context=context_data.get('file_context'),
            line_number=context_data.get('line_number'),
            mental_model=context_data.get('mental_model', description),
            next_steps=context_data.get('next_steps', []),
            decisions_made=context_data.get('decisions_made', []),
            blockers=context_data.get('blockers', []),
            energy_level=context_data.get('energy_level', 'medium'),
            focus_quality=context_data.get('focus_quality', 'good')
        )

        return snapshot

    async def _store_context_in_letta(self, snapshot: ContextSnapshot) -> None:
        """Store context snapshot in Letta memory system"""
        if not self.letta_client:
            return

        try:
            # Create memory entry for Letta
            memory_content = {
                'type': 'context_checkpoint',
                'session_id': snapshot.session_id,
                'timestamp': snapshot.timestamp.isoformat(),
                'checkpoint_type': snapshot.checkpoint_type.value,
                'mental_model': snapshot.mental_model,
                'next_steps': snapshot.next_steps,
                'decisions_made': snapshot.decisions_made
            }

            # Store in appropriate memory tier
            if snapshot.checkpoint_type in [CheckpointType.TASK_COMPLETE, CheckpointType.SESSION_END]:
                # Important checkpoints go to long-term memory
                await self.letta_client.store_archival(json.dumps(memory_content))
            else:
                # Regular checkpoints go to recall memory
                await self.letta_client.store_recall(json.dumps(memory_content))

            logger.debug(f"Stored checkpoint in Letta: {snapshot.session_id}")

        except Exception as e:
            logger.error(f"Failed to store context in Letta: {e}")

    async def _start_session_monitoring(self, session_id: str) -> None:
        """Start background monitoring for a session"""
        task = asyncio.create_task(self._session_monitor_loop(session_id))
        self._background_tasks.add(task)

    async def _stop_session_monitoring(self, session_id: str) -> None:
        """Stop background monitoring for a session"""
        # Find and cancel the monitoring task for this session
        tasks_to_cancel = [
            task for task in self._background_tasks
            if not task.done() and getattr(task, '_session_id', None) == session_id
        ]

        for task in tasks_to_cancel:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # Remove cancelled tasks
        self._background_tasks = {task for task in self._background_tasks if not task.done()}

    async def _session_monitor_loop(self, session_id: str) -> None:
        """Background monitoring loop for a session"""
        try:
            # Store session_id on the task for cleanup
            current_task = asyncio.current_task()
            if current_task:
                current_task._session_id = session_id

            while session_id in self.active_sessions:
                await asyncio.sleep(60)  # Check every minute

                session = self.active_sessions.get(session_id)
                if not session:
                    break

                current_time = datetime.now()

                # Check for automatic checkpoint trigger
                if session.context_snapshots:
                    last_checkpoint = session.context_snapshots[-1]
                    time_since_checkpoint = current_time - last_checkpoint.timestamp

                    if time_since_checkpoint.total_seconds() >= session.checkpoint_interval:
                        await self.create_checkpoint(
                            session_id, CheckpointType.POMODORO_AUTO,
                            f"Automatic checkpoint after {time_since_checkpoint}"
                        )

                # Check for break suggestions
                if session.break_reminders:
                    suggestion = await self.suggest_break(session_id)
                    if suggestion.get('suggested') and suggestion.get('recommendation', {}).get('priority') == 'high':
                        logger.info(f"Break suggested for session {session_id}: {suggestion['recommendation']['reason']}")
                        # In practice, this would trigger UI notification

        except asyncio.CancelledError:
            logger.debug(f"Session monitoring cancelled for {session_id}")
        except Exception as e:
            logger.error(f"Session monitoring error for {session_id}: {e}")

    async def _save_session_state(self, session: SessionState) -> None:
        """Save session state to disk"""
        try:
            session_file = self.session_storage_path / f"{session.session_id}.json"

            # Convert to serializable format
            session_data = {
                'session_id': session.session_id,
                'created_at': session.created_at.isoformat(),
                'last_activity': session.last_activity.isoformat(),
                'current_phase': session.current_phase.value,
                'context_snapshots': [snapshot.to_dict() for snapshot in session.context_snapshots],
                'current_context': session.current_context.to_dict() if session.current_context else None,
                'adhd_accommodations': session.adhd_accommodations,
                'break_reminders': session.break_reminders,
                'checkpoint_interval': session.checkpoint_interval,
                'metrics': asdict(session.metrics)
            }

            # Convert datetime objects in metrics
            if 'start_time' in session_data['metrics']:
                session_data['metrics']['start_time'] = session.metrics.start_time.isoformat()
            if session.metrics.end_time:
                session_data['metrics']['end_time'] = session.metrics.end_time.isoformat()

            # Convert sets to lists
            if 'roles_used' in session_data['metrics']:
                session_data['metrics']['roles_used'] = list(session.metrics.roles_used)
            if 'tools_used' in session_data['metrics']:
                session_data['metrics']['tools_used'] = list(session.metrics.tools_used)

            # Convert timedeltas to seconds
            session_data['metrics']['total_duration'] = session.metrics.total_duration.total_seconds()
            session_data['metrics']['focus_duration'] = session.metrics.focus_duration.total_seconds()
            session_data['metrics']['recovery_time'] = session.metrics.recovery_time.total_seconds()

            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save session state {session.session_id}: {e}")

    async def _load_session_state(self, session_id: str) -> Optional[SessionState]:
        """Load session state from disk"""
        try:
            session_file = self.session_storage_path / f"{session_id}.json"

            if not session_file.exists():
                return None

            with open(session_file, 'r') as f:
                session_data = json.load(f)

            # Reconstruct session state
            session_state = SessionState(
                session_id=session_data['session_id'],
                created_at=datetime.fromisoformat(session_data['created_at']),
                last_activity=datetime.fromisoformat(session_data['last_activity']),
                current_phase=SessionPhase(session_data['current_phase']),
                adhd_accommodations=session_data.get('adhd_accommodations', {}),
                break_reminders=session_data.get('break_reminders', True),
                checkpoint_interval=session_data.get('checkpoint_interval', self.checkpoint_interval)
            )

            # Reconstruct context snapshots
            session_state.context_snapshots = [
                ContextSnapshot.from_dict(snapshot_data)
                for snapshot_data in session_data.get('context_snapshots', [])
            ]

            # Reconstruct current context
            if session_data.get('current_context'):
                session_state.current_context = ContextSnapshot.from_dict(session_data['current_context'])

            # Reconstruct metrics
            metrics_data = session_data.get('metrics', {})
            if metrics_data:
                session_state.metrics = SessionMetrics(
                    session_id=session_id,
                    start_time=datetime.fromisoformat(metrics_data.get('start_time', session_data['created_at'])),
                    end_time=datetime.fromisoformat(metrics_data['end_time']) if metrics_data.get('end_time') else None,
                    total_duration=timedelta(seconds=metrics_data.get('total_duration', 0)),
                    roles_used=set(metrics_data.get('roles_used', [])),
                    role_transitions=metrics_data.get('role_transitions', 0),
                    current_role=metrics_data.get('current_role'),
                    tools_used=set(metrics_data.get('tools_used', [])),
                    tool_calls=metrics_data.get('tool_calls', 0),
                    checkpoints_created=metrics_data.get('checkpoints_created', 0),
                    breaks_taken=metrics_data.get('breaks_taken', 0),
                    context_switches=metrics_data.get('context_switches', 0),
                    focus_duration=timedelta(seconds=metrics_data.get('focus_duration', 0)),
                    interruption_count=metrics_data.get('interruption_count', 0),
                    recovery_time=timedelta(seconds=metrics_data.get('recovery_time', 0)),
                    tasks_completed=metrics_data.get('tasks_completed', 0),
                    decisions_made=metrics_data.get('decisions_made', 0),
                    blockers_encountered=metrics_data.get('blockers_encountered', 0)
                )

            logger.info(f"Loaded session state for {session_id}")
            return session_state

        except Exception as e:
            logger.error(f"Failed to load session state {session_id}: {e}")
            return None

    def _analyze_trend(self, values: List[str]) -> str:
        """Analyze trend in categorical values"""
        if not values or len(values) < 2:
            return "insufficient_data"

        # Simple trend analysis for categorical data
        if values[-1] != values[0]:
            if values[-1] > values[0]:  # Assuming ordinal relationship
                return "improving"
            else:
                return "declining"
        else:
            return "stable"

    async def store_checkpoint(self, checkpoint: Dict[str, Any]) -> None:
        """Store a checkpoint (called by broker)"""
        session_id = checkpoint.get('session_id')
        if not session_id:
            return

        # Convert to ContextSnapshot if needed
        if isinstance(checkpoint, dict):
            snapshot = ContextSnapshot(
                timestamp=datetime.fromisoformat(checkpoint.get('timestamp', datetime.now().isoformat())),
                checkpoint_type=CheckpointType(checkpoint.get('type', 'manual')),
                session_id=session_id,
                role=checkpoint.get('role'),
                mental_model=checkpoint.get('description', '')
            )

            session = self.active_sessions.get(session_id)
            if session:
                session.context_snapshots.append(snapshot)
                session.current_context = snapshot
                await self._save_session_state(session)