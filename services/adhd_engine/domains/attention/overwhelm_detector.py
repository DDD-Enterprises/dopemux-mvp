"""
Overwhelm Detection & Circuit Breaker

Detects overwhelm states and provides gentle intervention to prevent ADHD spirals.

Overwhelm Signals:
- Rapid task switching (>10 switches in 15min)
- Multiple simultaneous activities
- Long periods without progress
- High complexity + low energy combination
- Declining break acceptance

Circuit Breaker Actions:
- Gentle intervention suggestions
- Task breakdown assistance
- Break recommendations
- Context saving
- Encouraging support

ADHD Benefit: Prevents spiral, provides escape route, builds resilience
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class OverwhelmLevel(Enum):
    """Overwhelm severity levels."""
    NONE = "none"
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"


@dataclass
class OverwhelmSignal:
    """Single overwhelm indicator."""
    signal_type: str  # "rapid_switching", "no_progress", "complexity_mismatch", etc.
    severity: float  # 0.0-1.0
    description: str
    detected_at: datetime = field(default_factory=datetime.now)


@dataclass
class CircuitBreakerAction:
    """Recommended intervention action."""
    action_type: str  # "break", "simplify", "save_state", "end_session"
    urgency: str  # "immediate", "soon", "suggested"
    message: str
    steps: List[str]
    benefit: str


class OverwhelmDetector:
    """
    Detect overwhelm states and trigger circuit breaker.
    
    Monitors multiple signals:
    - Task switching patterns
    - Progress indicators
    - Energy/complexity mismatches
    - Break resistance
    - Time without wins
    """
    
    def __init__(
        self,
        rapid_switch_threshold: int = 10,  # Switches in 15min
        no_progress_threshold: int = 45,  # Minutes without commit/completion
        switch_window_minutes: int = 15
    ):
        """
        Initialize overwhelm detector.
        
        Args:
            rapid_switch_threshold: Max switches before flagging
            no_progress_threshold: Minutes without progress before flagging
            switch_window_minutes: Time window for switch counting
        """
        self.rapid_switch_threshold = rapid_switch_threshold
        self.no_progress_threshold = no_progress_threshold
        self.switch_window_minutes = switch_window_minutes
        
        # State tracking
        self.recent_switches: List[datetime] = []
        self.last_progress_timestamp: Optional[datetime] = None
        self.break_refusals: int = 0
        self.overwhelm_history: List[OverwhelmSignal] = []
    
    async def check_overwhelm(
        self,
        user_id: str,
        current_state: Dict[str, Any]
    ) -> tuple[OverwhelmLevel, List[OverwhelmSignal]]:
        """
        Check for overwhelm signals.
        
        Args:
            user_id: User identifier
            current_state: Current cognitive state dict with:
                - energy_level: str
                - attention_state: str
                - task_complexity: float
                - recent_switches: List[datetime]
                - last_commit: Optional[datetime]
                - break_refusals: int
        
        Returns:
            (OverwhelmLevel, List[OverwhelmSignal])
        """
        signals: List[OverwhelmSignal] = []
        
        # Signal 1: Rapid task switching
        switch_signal = self._check_rapid_switching(current_state)
        if switch_signal:
            signals.append(switch_signal)
        
        # Signal 2: No progress/output
        progress_signal = self._check_no_progress(current_state)
        if progress_signal:
            signals.append(progress_signal)
        
        # Signal 3: Energy-complexity mismatch
        mismatch_signal = self._check_energy_mismatch(current_state)
        if mismatch_signal:
            signals.append(mismatch_signal)
        
        # Signal 4: Break resistance
        break_signal = self._check_break_resistance(current_state)
        if break_signal:
            signals.append(break_signal)
        
        # Signal 5: Attention state
        attention_signal = self._check_attention_overwhelmed(current_state)
        if attention_signal:
            signals.append(attention_signal)
        
        # Calculate overall overwhelm level
        level = self._calculate_overwhelm_level(signals)
        
        # Store in history
        if signals:
            self.overwhelm_history.extend(signals)
            # Keep last 100 signals
            self.overwhelm_history = self.overwhelm_history[-100:]
        
        logger.info(f"Overwhelm check: {level.value}, {len(signals)} signals")
        return level, signals
    
    def _check_rapid_switching(self, state: Dict[str, Any]) -> Optional[OverwhelmSignal]:
        """Check for rapid task switching."""
        recent_switches = state.get('recent_switches', [])
        
        # Filter to switch window
        cutoff = datetime.now() - timedelta(minutes=self.switch_window_minutes)
        recent = [s for s in recent_switches if s > cutoff]
        
        if len(recent) >= self.rapid_switch_threshold:
            severity = min(1.0, len(recent) / (self.rapid_switch_threshold * 1.5))
            return OverwhelmSignal(
                signal_type="rapid_switching",
                severity=severity,
                description=f"{len(recent)} task switches in {self.switch_window_minutes} minutes"
            )
        return None
    
    def _check_no_progress(self, state: Dict[str, Any]) -> Optional[OverwhelmSignal]:
        """Check for extended period without progress."""
        last_commit = state.get('last_commit')
        if not last_commit:
            return None
        
        minutes_since = (datetime.now() - last_commit).total_seconds() / 60
        
        if minutes_since >= self.no_progress_threshold:
            severity = min(1.0, minutes_since / (self.no_progress_threshold * 2))
            return OverwhelmSignal(
                signal_type="no_progress",
                severity=severity,
                description=f"{int(minutes_since)} minutes without progress"
            )
        return None
    
    def _check_energy_mismatch(self, state: Dict[str, Any]) -> Optional[OverwhelmSignal]:
        """Check for energy-complexity mismatch."""
        energy = state.get('energy_level', 'medium')
        complexity = state.get('task_complexity', 0.5)
        
        # High complexity + low energy = bad combo
        if energy in ['low', 'very_low'] and complexity > 0.7:
            severity = complexity * (1.0 if energy == 'very_low' else 0.7)
            return OverwhelmSignal(
                signal_type="energy_complexity_mismatch",
                severity=severity,
                description=f"High complexity ({complexity:.1f}) with {energy} energy"
            )
        return None
    
    def _check_break_resistance(self, state: Dict[str, Any]) -> Optional[OverwhelmSignal]:
        """Check for declining break acceptance."""
        refusals = state.get('break_refusals', 0)
        
        if refusals >= 5:
            severity = min(1.0, refusals / 10)
            return OverwhelmSignal(
                signal_type="break_resistance",
                severity=severity,
                description=f"Declined {refusals} break suggestions"
            )
        return None
    
    def _check_attention_overwhelmed(self, state: Dict[str, Any]) -> Optional[OverwhelmSignal]:
        """Check if attention state is already overwhelmed."""
        attention = state.get('attention_state', 'focused')
        
        if attention == 'overwhelmed':
            return OverwhelmSignal(
                signal_type="attention_overwhelmed",
                severity=1.0,
                description="Attention state detected as overwhelmed"
            )
        return None
    
    def _calculate_overwhelm_level(self, signals: List[OverwhelmSignal]) -> OverwhelmLevel:
        """Calculate overall overwhelm level from signals."""
        if not signals:
            return OverwhelmLevel.NONE
        
        # Weighted average of signal severities
        avg_severity = sum(s.severity for s in signals) / len(signals)
        
        # Consider signal count
        signal_multiplier = min(1.5, 1.0 + (len(signals) - 1) * 0.1)
        adjusted_severity = avg_severity * signal_multiplier
        
        if adjusted_severity >= 0.8:
            return OverwhelmLevel.CRITICAL
        elif adjusted_severity >= 0.6:
            return OverwhelmLevel.SEVERE
        elif adjusted_severity >= 0.4:
            return OverwhelmLevel.MODERATE
        else:
            return OverwhelmLevel.MILD
    
    def generate_circuit_breaker_actions(
        self,
        level: OverwhelmLevel,
        signals: List[OverwhelmSignal]
    ) -> List[CircuitBreakerAction]:
        """
        Generate intervention actions based on overwhelm level.
        
        Args:
            level: Overwhelm severity
            signals: Active overwhelm signals
        
        Returns:
            List of recommended actions
        """
        actions: List[CircuitBreakerAction] = []
        
        if level == OverwhelmLevel.NONE:
            return actions
        
        # Critical: Immediate intervention
        if level == OverwhelmLevel.CRITICAL:
            actions.append(CircuitBreakerAction(
                action_type="immediate_break",
                urgency="immediate",
                message="🛑 Critical overwhelm detected. Let's pause right now.",
                steps=[
                    "Save your current work state",
                    "Step away from the computer for 10-15 minutes",
                    "Do something physical: walk, stretch, breathe",
                    "When you return, we'll simplify your task"
                ],
                benefit="Prevents complete shutdown, allows recovery"
            ))
            
            actions.append(CircuitBreakerAction(
                action_type="end_session",
                urgency="suggested",
                message="Consider ending your work session for today.",
                steps=[
                    "It's okay to call it a day",
                    "Capture your current thoughts to ConPort",
                    "Set up tomorrow's first task (something simple)",
                    "Rest and recover"
                ],
                benefit="Prevents burnout, enables fresh start tomorrow"
            ))
        
        # Severe: Strong intervention
        elif level == OverwhelmLevel.SEVERE:
            actions.append(CircuitBreakerAction(
                action_type="reset_break",
                urgency="soon",
                message="⚠️ You're showing signs of overwhelm. Time for a reset.",
                steps=[
                    "Take a 10-minute break right now",
                    "Close extra browser tabs/windows",
                    "Pick ONE thing to focus on when you return",
                    "Lower your expectations for today"
                ],
                benefit="Reduces cognitive load, provides reset"
            ))
            
            # Check for complexity mismatch
            if any(s.signal_type == "energy_complexity_mismatch" for s in signals):
                actions.append(CircuitBreakerAction(
                    action_type="switch_task",
                    urgency="suggested",
                    message="This task is too complex for your current energy.",
                    steps=[
                        "Switch to something simpler",
                        "Come back to this when energy is higher",
                        "Try: code review, documentation, or tests"
                    ],
                    benefit="Matches task to capacity, maintains momentum"
                ))
        
        # Moderate: Gentle intervention
        elif level == OverwhelmLevel.MODERATE:
            actions.append(CircuitBreakerAction(
                action_type="simplify",
                urgency="suggested",
                message="💡 I notice you might be struggling. Let's simplify.",
                steps=[
                    "Break your current task into smaller chunks",
                    "Pick the smallest piece to complete",
                    "Celebrate completing just that one piece",
                    "Then decide: continue or switch?"
                ],
                benefit="Reduces overwhelm, creates achievable wins"
            ))
            
            # Check for rapid switching
            if any(s.signal_type == "rapid_switching" for s in signals):
                actions.append(CircuitBreakerAction(
                    action_type="commit_to_one",
                    urgency="suggested",
                    message="You've been switching tasks frequently. Let's commit to one.",
                    steps=[
                        "Pick ONE task from your open items",
                        "Commit to 15 minutes on just that task",
                        "Set a timer, close other tabs",
                        "After 15min, you can switch if needed"
                    ],
                    benefit="Builds focus, reduces task-switching overhead"
                ))
        
        # Mild: Light suggestion
        else:  # MILD
            actions.append(CircuitBreakerAction(
                action_type="check_in",
                urgency="suggested",
                message="Quick check-in: How are you feeling?",
                steps=[
                    "Take a 2-minute micro-break",
                    "Stretch, breathe, reset",
                    "Make sure you're on track with your goal"
                ],
                benefit="Early intervention prevents escalation"
            ))
        
        return actions
    
    def reset_state(self) -> None:
        """Reset detector state (e.g., after break or session end)."""
        self.recent_switches = []
        self.break_refusals = 0
        logger.info("Overwhelm detector state reset")


# Convenience function
async def check_and_intervene(
    user_id: str,
    current_state: Dict[str, Any],
    detector: Optional[OverwhelmDetector] = None
) -> Dict[str, Any]:
    """
    Check for overwhelm and return intervention recommendations.
    
    Args:
        user_id: User identifier
        current_state: Current cognitive/activity state
        detector: Optional existing detector (creates new if None)
    
    Returns:
        Dict with level, signals, actions
    """
    if detector is None:
        detector = OverwhelmDetector()
    
    level, signals = await detector.check_overwhelm(user_id, current_state)
    actions = detector.generate_circuit_breaker_actions(level, signals)
    
    return {
        "user_id": user_id,
        "overwhelm_level": level.value,
        "signals": [
            {
                "type": s.signal_type,
                "severity": s.severity,
                "description": s.description
            }
            for s in signals
        ],
        "actions": [
            {
                "type": a.action_type,
                "urgency": a.urgency,
                "message": a.message,
                "steps": a.steps,
                "benefit": a.benefit
            }
            for a in actions
        ],
        "timestamp": datetime.now().isoformat()
    }
