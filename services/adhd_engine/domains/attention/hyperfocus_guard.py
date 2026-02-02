"""
Hyperfocus Detection & Protection

Detects hyperfocus states and provides protection mechanisms:
- Auto-save work every 5 minutes
- Block non-critical notifications
- Silent guardian timer (gentle reminder at 90-120min)
- Track hyperfocus sessions for pattern analysis
- Post-hyperfocus crash detection and recovery

ADHD Benefit: Protects deep work while preventing burnout crashes
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import asyncio

logger = logging.getLogger(__name__)


class HyperfocusPhase(Enum):
    """Hyperfocus session phases."""
    NONE = "none"
    BUILDING = "building"  # Entering hyperfocus (15-30min)
    ACTIVE = "active"  # Full hyperfocus (30-90min)
    EXTENDED = "extended"  # Beyond optimal (90-120min)
    CRITICAL = "critical"  # Dangerous territory (>120min)
    CRASHED = "crashed"  # Post-hyperfocus crash


@dataclass
class HyperfocusSession:
    """Hyperfocus session tracking."""
    user_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    peak_duration_minutes: int = 0
    auto_saves_triggered: int = 0
    warnings_shown: int = 0
    context_snapshot: Optional[Dict[str, Any]] = None
    crash_detected: bool = False
    recovery_duration_minutes: Optional[int] = None


@dataclass
class ProtectionAction:
    """Protection action taken during hyperfocus."""
    action_type: str  # "auto_save", "block_notification", "gentle_reminder"
    timestamp: datetime
    was_successful: bool
    details: Optional[str] = None


class HyperfocusGuard:
    """
    Protect hyperfocus sessions while preventing burnout.
    
    Features:
    - Detects hyperfocus entry (30+ min sustained focus)
    - Auto-saves work every 5 minutes
    - Blocks non-critical notifications
    - Sets guardian timer (gentle reminder at 90-120min)
    - Tracks sessions for pattern analysis
    - Detects post-hyperfocus crashes
    """
    
    def __init__(
        self,
        auto_save_interval_minutes: int = 5,
        gentle_reminder_minutes: int = 90,
        critical_threshold_minutes: int = 120,
        crash_energy_threshold: str = "low"
    ):
        """
        Initialize hyperfocus guard.
        
        Args:
            auto_save_interval_minutes: How often to trigger auto-save
            gentle_reminder_minutes: When to show gentle reminder
            critical_threshold_minutes: When hyperfocus becomes dangerous
            crash_energy_threshold: Energy level indicating crash
        """
        self.auto_save_interval = auto_save_interval_minutes
        self.gentle_reminder = gentle_reminder_minutes
        self.critical_threshold = critical_threshold_minutes
        self.crash_energy_threshold = crash_energy_threshold
        
        # State tracking
        self.active_sessions: Dict[str, HyperfocusSession] = {}
        self.session_history: List[HyperfocusSession] = []
        self.protection_actions: List[ProtectionAction] = []
        
        # Auto-save callback (to be set by integration)
        self.auto_save_callback: Optional[callable] = None
        self.notification_blocker_callback: Optional[callable] = None
    
    async def check_and_protect(
        self,
        user_id: str,
        current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check for hyperfocus and apply protection.
        
        Args:
            user_id: User identifier
            current_state: Current cognitive state with:
                - attention_state: str
                - session_duration: int (minutes)
                - energy_level: str
                - last_activity: datetime
        
        Returns:
            Protection status dict
        """
        attention = current_state.get('attention_state', 'focused')
        duration = current_state.get('session_duration', 0)
        energy = current_state.get('energy_level', 'medium')
        
        # Determine hyperfocus phase
        phase = self._determine_phase(attention, duration, energy)
        
        # Get or create session
        session = self.active_sessions.get(user_id)
        
        # Handle phase transitions
        if phase in [HyperfocusPhase.ACTIVE, HyperfocusPhase.EXTENDED, HyperfocusPhase.CRITICAL]:
            if not session:
                # Start new hyperfocus session
                session = self._start_session(user_id, current_state)
                self.active_sessions[user_id] = session
                logger.info(f"🧠 Hyperfocus session started for {user_id}")
            
            # Apply protections
            actions = await self._apply_protections(session, phase, current_state)
            
            return {
                "user_id": user_id,
                "hyperfocus_active": True,
                "phase": phase.value,
                "duration_minutes": duration,
                "protections_applied": len(actions),
                "actions": [a.action_type for a in actions],
                "recommendation": self._get_phase_recommendation(phase)
            }
        
        elif phase == HyperfocusPhase.CRASHED:
            # Handle crash
            if session:
                session.crash_detected = True
                session.end_time = datetime.now()
                self.session_history.append(session)
                del self.active_sessions[user_id]
            
            return {
                "user_id": user_id,
                "hyperfocus_active": False,
                "phase": phase.value,
                "crash_detected": True,
                "recovery_protocol": self._generate_recovery_protocol(session)
            }
        
        else:  # NONE or BUILDING
            # End active session if exists
            if session and phase == HyperfocusPhase.NONE:
                session.end_time = datetime.now()
                self.session_history.append(session)
                del self.active_sessions[user_id]
                logger.info(f"Hyperfocus session ended normally for {user_id}")
            
            return {
                "user_id": user_id,
                "hyperfocus_active": False,
                "phase": phase.value,
                "protections_applied": 0
            }
    
    def _determine_phase(
        self,
        attention: str,
        duration: int,
        energy: str
    ) -> HyperfocusPhase:
        """Determine current hyperfocus phase."""
        # Check for crash (low energy after hyperfocus period)
        if energy in ['low', 'very_low'] and duration > 60:
            return HyperfocusPhase.CRASHED
        
        # Not in hyperfocus
        if attention != 'hyperfocused':
            if duration > 15 and attention == 'focused':
                return HyperfocusPhase.BUILDING
            return HyperfocusPhase.NONE
        
        # In hyperfocus - determine severity
        if duration >= self.critical_threshold:
            return HyperfocusPhase.CRITICAL
        elif duration >= self.gentle_reminder:
            return HyperfocusPhase.EXTENDED
        elif duration >= 30:
            return HyperfocusPhase.ACTIVE
        else:
            return HyperfocusPhase.BUILDING
    
    def _start_session(
        self,
        user_id: str,
        current_state: Dict[str, Any]
    ) -> HyperfocusSession:
        """Start new hyperfocus session."""
        return HyperfocusSession(
            user_id=user_id,
            start_time=datetime.now(),
            context_snapshot=current_state.copy()
        )
    
    async def _apply_protections(
        self,
        session: HyperfocusSession,
        phase: HyperfocusPhase,
        current_state: Dict[str, Any]
    ) -> List[ProtectionAction]:
        """Apply protection mechanisms."""
        actions = []
        now = datetime.now()
        duration = (now - session.start_time).total_seconds() / 60
        
        # Update peak duration
        session.peak_duration_minutes = max(session.peak_duration_minutes, int(duration))
        
        # Protection 1: Auto-save every 5 minutes
        if duration % self.auto_save_interval < 1:  # Check if we're at a 5-min mark
            action = await self._trigger_auto_save(session)
            if action:
                actions.append(action)
        
        # Protection 2: Block non-critical notifications (all phases)
        if self.notification_blocker_callback:
            action = await self._block_notifications(session)
            if action:
                actions.append(action)
        
        # Protection 3: Gentle reminder at 90min
        if phase == HyperfocusPhase.EXTENDED and session.warnings_shown == 0:
            action = self._show_gentle_reminder(session, duration)
            actions.append(action)
            session.warnings_shown += 1
        
        # Protection 4: Stronger warning at 120min
        if phase == HyperfocusPhase.CRITICAL and session.warnings_shown == 1:
            action = self._show_critical_warning(session, duration)
            actions.append(action)
            session.warnings_shown += 1
        
        # Store actions
        self.protection_actions.extend(actions)
        
        return actions
    
    async def _trigger_auto_save(self, session: HyperfocusSession) -> Optional[ProtectionAction]:
        """Trigger auto-save mechanism."""
        try:
            if self.auto_save_callback:
                success = await self.auto_save_callback(session.user_id)
                session.auto_saves_triggered += 1
                
                return ProtectionAction(
                    action_type="auto_save",
                    timestamp=datetime.now(),
                    was_successful=success,
                    details=f"Auto-save #{session.auto_saves_triggered}"
                )
            else:
                logger.warning("Auto-save callback not configured")
                return None
        except Exception as e:
            logger.error(f"Auto-save failed: {e}")
            return ProtectionAction(
                action_type="auto_save",
                timestamp=datetime.now(),
                was_successful=False,
                details=str(e)
            )
    
    async def _block_notifications(self, session: HyperfocusSession) -> Optional[ProtectionAction]:
        """Block non-critical notifications."""
        try:
            if self.notification_blocker_callback:
                success = await self.notification_blocker_callback(session.user_id, enabled=True)
                
                return ProtectionAction(
                    action_type="block_notifications",
                    timestamp=datetime.now(),
                    was_successful=success,
                    details="Non-critical notifications blocked"
                )
            return None
        except Exception as e:
            logger.error(f"Notification blocking failed: {e}")
            return None
    
    def _show_gentle_reminder(self, session: HyperfocusSession, duration: float) -> ProtectionAction:
        """Show gentle reminder at 90min."""
        logger.info(f"⏰ Gentle reminder: {session.user_id} has been in hyperfocus for {int(duration)} min")
        
        # This would trigger a notification via the notification service
        return ProtectionAction(
            action_type="gentle_reminder",
            timestamp=datetime.now(),
            was_successful=True,
            details=f"Gentle reminder shown at {int(duration)} minutes"
        )
    
    def _show_critical_warning(self, session: HyperfocusSession, duration: float) -> ProtectionAction:
        """Show critical warning at 120min."""
        logger.warning(f"⚠️ Critical warning: {session.user_id} has been in hyperfocus for {int(duration)} min")
        
        return ProtectionAction(
            action_type="critical_warning",
            timestamp=datetime.now(),
            was_successful=True,
            details=f"Critical warning shown at {int(duration)} minutes"
        )
    
    def _get_phase_recommendation(self, phase: HyperfocusPhase) -> str:
        """Get recommendation for current phase."""
        recommendations = {
            HyperfocusPhase.BUILDING: "You're entering flow. Great! I'll protect your focus.",
            HyperfocusPhase.ACTIVE: "Deep work mode active. I'm auto-saving and blocking distractions.",
            HyperfocusPhase.EXTENDED: "⏰ You've been focused for 90+ minutes. Consider wrapping up soon.",
            HyperfocusPhase.CRITICAL: "⚠️ You've been in hyperfocus for 2+ hours. Please take a break soon to prevent crash.",
            HyperfocusPhase.CRASHED: "Post-hyperfocus crash detected. Time for recovery.",
            HyperfocusPhase.NONE: "No hyperfocus detected."
        }
        return recommendations[phase]
    
    def _generate_recovery_protocol(self, session: Optional[HyperfocusSession]) -> Dict[str, Any]:
        """Generate recovery protocol for post-hyperfocus crash."""
        duration = 0
        if session:
            duration = (session.end_time - session.start_time).total_seconds() / 60
        
        # Longer hyperfocus = longer recovery
        recommended_recovery = min(60, max(20, int(duration * 0.3)))
        
        return {
            "detected": True,
            "session_duration": int(duration) if session else 0,
            "recommended_recovery_minutes": recommended_recovery,
            "recovery_activities": [
                "Step away from computer completely",
                "Physical movement (walk, stretch)",
                "Hydrate and eat something",
                "Avoid making important decisions",
                "Rest your eyes and brain"
            ],
            "next_tasks": [
                "Review what you accomplished (celebrate!)",
                "Choose a SIMPLE task for when you return",
                "Lower expectations for rest of session",
                "Consider ending work day if late"
            ]
        }
    
    def get_session_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get statistics for user's hyperfocus sessions."""
        user_sessions = [s for s in self.session_history if s.user_id == user_id]
        
        if not user_sessions:
            return {"error": "No hyperfocus sessions recorded"}
        
        total_sessions = len(user_sessions)
        avg_duration = sum(s.peak_duration_minutes for s in user_sessions) / total_sessions
        total_crashes = sum(1 for s in user_sessions if s.crash_detected)
        total_auto_saves = sum(s.auto_saves_triggered for s in user_sessions)
        
        return {
            "total_sessions": total_sessions,
            "average_duration_minutes": int(avg_duration),
            "crash_rate": total_crashes / total_sessions if total_sessions > 0 else 0,
            "total_auto_saves": total_auto_saves,
            "longest_session_minutes": max(s.peak_duration_minutes for s in user_sessions),
            "recommendation": self._get_pattern_recommendation(user_sessions)
        }
    
    def _get_pattern_recommendation(self, sessions: List[HyperfocusSession]) -> str:
        """Generate recommendation based on session patterns."""
        if not sessions:
            return "Not enough data"
        
        avg_duration = sum(s.peak_duration_minutes for s in sessions) / len(sessions)
        crash_rate = sum(1 for s in sessions if s.crash_detected) / len(sessions)
        
        if crash_rate > 0.5:
            return f"⚠️ High crash rate ({crash_rate:.0%}). Try setting a hard stop at {int(avg_duration * 0.8)} minutes."
        elif avg_duration > 120:
            return f"Your hyperfocus sessions average {int(avg_duration)} min. Consider shorter sessions with breaks."
        else:
            return f"Healthy hyperfocus pattern. Average {int(avg_duration)} min sessions."
