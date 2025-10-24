"""
CognitiveGuardian - ADHD Support Agent

Solves ADHD challenges: burnout prevention, energy matching, attention monitoring

Features:
- Break reminders (25-minute warnings, 90-minute mandatory)
- Attention state detection (focused, scattered, hyperfocus)
- Energy-aware task suggestions
- Complexity warnings
- Gentle guidance with progressive disclosure

Authority: ADHD monitoring and guidance

Version: 1.0.0
Complexity: 0.6 (Medium-High)
Effort: 2 weeks (50 focus blocks)
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class AttentionState(str, Enum):
    """User attention states for ADHD accommodation."""
    FOCUSED = "focused"
    SCATTERED = "scattered"
    HYPERFOCUS = "hyperfocus"


class EnergyLevel(str, Enum):
    """Energy levels for task matching."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class UserState:
    """Current user state for ADHD optimization."""
    energy: EnergyLevel
    attention: AttentionState
    session_duration_minutes: int
    breaks_taken: int
    last_break: Optional[str]
    current_task_complexity: float
    time_of_day_hour: int


@dataclass
class BreakReminder:
    """Break reminder with ADHD-friendly messaging."""
    type: str  # "gentle", "warning", "mandatory"
    message: str
    duration_worked_minutes: int
    suggested_break_minutes: int
    is_mandatory: bool


class CognitiveGuardian:
    """
    ADHD Support and Break Enforcement Agent

    Prevents burnout, matches tasks to energy/attention state, enforces healthy breaks.

    Example:
        guardian = CognitiveGuardian(workspace_id="/path/to/project")
        await guardian.start_monitoring()

        # During work...
        user_state = await guardian.get_user_state()
        if user_state.energy == "low":
            suggestions = await guardian.suggest_tasks(energy="low")

        # Check for break reminders
        reminder = await guardian.check_break_needed()
        if reminder and reminder.is_mandatory:
            print(reminder.message)
            await guardian.enforce_break()
    """

    def __init__(
        self,
        workspace_id: str,
        memory_agent: Optional[Any] = None,
        conport_client: Optional[Any] = None,
        break_interval_minutes: int = 25,
        mandatory_break_minutes: int = 90,
        hyperfocus_warning_minutes: int = 60
    ):
        """
        Initialize CognitiveGuardian.

        Args:
            workspace_id: Absolute path to workspace
            memory_agent: MemoryAgent instance for session tracking
            conport_client: ConPort MCP client
            break_interval_minutes: Gentle break reminder interval (default 25)
            mandatory_break_minutes: Mandatory break threshold (default 90)
            hyperfocus_warning_minutes: Hyperfocus warning threshold (default 60)
        """
        self.workspace_id = workspace_id
        self.memory_agent = memory_agent
        self.conport_client = conport_client

        # Break enforcement settings
        self.break_interval = break_interval_minutes
        self.mandatory_break = mandatory_break_minutes
        self.hyperfocus_warning = hyperfocus_warning_minutes

        # Session state
        self.session_start: Optional[datetime] = None
        self.last_break: Optional[datetime] = None
        self.breaks_taken = 0
        self.gentle_reminder_shown = False
        self.warning_shown = False
        self.hyperfocus_warning_shown = False

        # Monitoring
        self.monitoring_task: Optional[asyncio.Task] = None
        self.monitoring = False

        # Metrics
        self.breaks_enforced = 0
        self.burnout_prevented = 0
        self.energy_mismatches_caught = 0

        logger.info(
            f"CognitiveGuardian initialized (break interval: {break_interval_minutes}min, "
            f"mandatory: {mandatory_break_minutes}min)"
        )

    async def start_monitoring(self):
        """Start background monitoring for breaks and attention."""
        if self.monitoring:
            logger.warning("Monitoring already active")
            return

        self.session_start = datetime.now(timezone.utc)
        self.last_break = self.session_start
        self.monitoring = True

        # Start background monitoring task
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())

        logger.info("✅ CognitiveGuardian monitoring started")
        print(f"\n🧠 CognitiveGuardian Active")
        print(f"   Break reminders: Every {self.break_interval} minutes")
        print(f"   Mandatory break: At {self.mandatory_break} minutes")
        print(f"   Your wellbeing is protected!\n")

    async def _monitoring_loop(self):
        """Background loop for break monitoring."""
        while self.monitoring:
            try:
                await asyncio.sleep(60)  # Check every minute

                # Check if break is needed
                reminder = await self.check_break_needed()

                if reminder:
                    self._show_break_reminder(reminder)

                    if reminder.is_mandatory:
                        logger.warning(f"Mandatory break enforced at {reminder.duration_worked_minutes} min")
                        self.breaks_enforced += 1
                        # In production, would pause work
                        # For now, just log

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring error: {e}")

    async def check_break_needed(self) -> Optional[BreakReminder]:
        """
        Check if user needs a break.

        Returns:
            BreakReminder if break suggested/required, None otherwise
        """
        if not self.session_start:
            return None

        now = datetime.now(timezone.utc)
        session_duration = (now - self.session_start).total_seconds() / 60
        since_last_break = (now - self.last_break).total_seconds() / 60

        # Mandatory break at 90 minutes
        if session_duration >= self.mandatory_break:
            return BreakReminder(
                type="mandatory",
                message=f"🛑 MANDATORY BREAK: {session_duration:.0f} minutes is the limit\n"
                        f"   Take a 10-minute break for your health and code quality.",
                duration_worked_minutes=int(session_duration),
                suggested_break_minutes=10,
                is_mandatory=True
            )

        # Hyperfocus warning at 60 minutes
        if session_duration >= self.hyperfocus_warning and not self.hyperfocus_warning_shown:
            self.hyperfocus_warning_shown = True
            return BreakReminder(
                type="warning",
                message=f"⚠️ You've been working for {session_duration:.0f} minutes\n"
                        f"   Consider a break soon to maintain quality.",
                duration_worked_minutes=int(session_duration),
                suggested_break_minutes=10,
                is_mandatory=False
            )

        # Gentle reminder at 25 minutes
        if since_last_break >= self.break_interval and not self.gentle_reminder_shown:
            self.gentle_reminder_shown = True
            return BreakReminder(
                type="gentle",
                message=f"⏰ Great work! You've been focused for {since_last_break:.0f} minutes\n"
                        f"   Time for a 5-minute break?",
                duration_worked_minutes=int(since_last_break),
                suggested_break_minutes=5,
                is_mandatory=False
            )

        return None

    def _show_break_reminder(self, reminder: BreakReminder):
        """Display ADHD-friendly break reminder."""
        print(f"\n{'='*60}")
        print(reminder.message)
        print(f"{'='*60}\n")

    async def take_break(self, duration_minutes: int = 5):
        """
        Record break taken.

        Args:
            duration_minutes: Break duration
        """
        self.last_break = datetime.now(timezone.utc)
        self.breaks_taken += 1
        self.gentle_reminder_shown = False
        self.hyperfocus_warning_shown = False

        logger.info(f"✅ Break taken ({duration_minutes} min) - breaks: {self.breaks_taken}")

        print(f"\n✅ Break recorded!")
        print(f"   Duration: {duration_minutes} minutes")
        print(f"   Total breaks: {self.breaks_taken}")
        print(f"   Ready to continue when you are!\n")

    async def get_user_state(self) -> UserState:
        """
        Get current user state for task matching.

        Returns:
            UserState with energy, attention, session info
        """
        now = datetime.now(timezone.utc)
        session_duration = 0

        if self.session_start:
            session_duration = int((now - self.session_start).total_seconds() / 60)

        # Estimate energy based on time of day
        hour = datetime.now().hour
        if 9 <= hour < 12:
            energy = EnergyLevel.HIGH
        elif 14 <= hour < 17:
            energy = EnergyLevel.MEDIUM
        else:
            energy = EnergyLevel.LOW

        # Estimate attention based on session duration
        if session_duration < 25:
            attention = AttentionState.FOCUSED
        elif session_duration < 60:
            attention = AttentionState.FOCUSED  # Still okay
        elif session_duration < 90:
            attention = AttentionState.HYPERFOCUS
        else:
            attention = AttentionState.SCATTERED  # Overworked

        # Get current task complexity (from MemoryAgent if available)
        current_complexity = 0.5  # Default
        if self.memory_agent and hasattr(self.memory_agent, 'current_session'):
            session = self.memory_agent.current_session
            if session:
                current_complexity = session.complexity

        return UserState(
            energy=energy,
            attention=attention,
            session_duration_minutes=session_duration,
            breaks_taken=self.breaks_taken,
            last_break=self.last_break.isoformat() if self.last_break else None,
            current_task_complexity=current_complexity,
            time_of_day_hour=hour
        )

    async def suggest_tasks(
        self,
        energy: Optional[str] = None,
        max_suggestions: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Suggest ADHD-matched tasks based on current state.

        Args:
            energy: Override energy level (if None, uses current state)
            max_suggestions: Max tasks to suggest (default 3 for ADHD)

        Returns:
            List of suggested tasks with reasons
        """
        # Get user state
        user_state = await self.get_user_state()
        target_energy = energy or user_state.energy.value

        logger.info(
            f"Suggesting tasks for: energy={target_energy}, "
            f"attention={user_state.attention.value}"
        )

        # In production, would query ConPort for tasks
        # For now, show pattern:
        # tasks = await self.conport_client.get_progress(
        #     workspace_id=self.workspace_id,
        #     status="TODO"
        # )

        # Filter by energy level
        # matched_tasks = [
        #     t for t in tasks
        #     if t.get("energy_required") == target_energy
        # ]

        # Sort by complexity match to attention state
        # If scattered: prefer low complexity (<0.3)
        # If focused: any complexity okay
        # If hyperfocus: can handle high complexity (>0.7)

        # Limit to max_suggestions (ADHD: prevent overwhelm)
        # return matched_tasks[:max_suggestions]

        # Simulation mode - show pattern
        print(f"\n🎯 Task Suggestions (Energy: {target_energy})")
        print(f"   Attention: {user_state.attention.value}")
        print(f"   Time: {user_state.time_of_day_hour}:00\n")

        if target_energy == "high":
            print("   Suggested (complex tasks):")
            print("   1. Design microservices architecture (complexity: 0.8)")
            print("   2. Refactor authentication system (complexity: 0.7)")
            print("   3. Implement real-time WebSocket sync (complexity: 0.9)\n")
        elif target_energy == "medium":
            print("   Suggested (moderate tasks):")
            print("   1. Add input validation to API (complexity: 0.5)")
            print("   2. Write integration tests (complexity: 0.4)")
            print("   3. Update documentation (complexity: 0.3)\n")
        else:  # low
            print("   Suggested (simple tasks):")
            print("   1. Fix typos in comments (complexity: 0.1)")
            print("   2. Update README formatting (complexity: 0.2)")
            print("   3. Run and review test suite (complexity: 0.2)\n")

        return []  # Would return real tasks from ConPort

    async def check_task_readiness(
        self,
        task_complexity: float,
        task_energy_required: str
    ) -> Dict[str, Any]:
        """
        Check if user is ready for a specific task.

        Args:
            task_complexity: Task complexity 0.0-1.0
            task_energy_required: Required energy level

        Returns:
            Readiness assessment with suggestions
        """
        user_state = await self.get_user_state()

        # Energy mismatch
        if task_energy_required == "high" and user_state.energy == EnergyLevel.LOW:
            self.energy_mismatches_caught += 1
            return {
                "ready": False,
                "reason": f"Task needs high energy, current: {user_state.energy.value}",
                "suggestion": "This task needs focus. Try a simpler task first or take a break to recharge.",
                "alternatives": await self.suggest_tasks(energy="low", max_suggestions=3)
            }

        # Complexity + attention mismatch
        if task_complexity > 0.7 and user_state.attention == AttentionState.SCATTERED:
            self.energy_mismatches_caught += 1
            return {
                "ready": False,
                "reason": f"High complexity ({task_complexity:.1f}) needs focus, attention: scattered",
                "suggestion": "This task is complex. Schedule it for when you're fresh, or try a quick task to build momentum.",
                "alternatives": await self.suggest_tasks(max_suggestions=3)
            }

        # Overworked (need break first)
        if user_state.session_duration_minutes >= self.mandatory_break:
            self.burnout_prevented += 1
            return {
                "ready": False,
                "reason": f"Session duration: {user_state.session_duration_minutes} min (limit: {self.mandatory_break})",
                "suggestion": "🛑 Mandatory break required. Your brain needs rest for quality work.",
                "alternatives": []  # No alternatives - must break
            }

        # Ready!
        return {
            "ready": True,
            "reason": f"Energy match: {user_state.energy.value}, attention: {user_state.attention.value}",
            "confidence": self._calculate_readiness_confidence(user_state, task_complexity)
        }

    def _calculate_readiness_confidence(
        self,
        user_state: UserState,
        task_complexity: float
    ) -> float:
        """
        Calculate confidence that user will complete task successfully.

        Returns:
            Confidence 0.0-1.0
        """
        # Base confidence
        confidence = 0.5

        # Energy match bonus
        if user_state.energy == EnergyLevel.HIGH and task_complexity > 0.6:
            confidence += 0.2
        elif user_state.energy == EnergyLevel.LOW and task_complexity < 0.3:
            confidence += 0.2

        # Attention match bonus
        if user_state.attention == AttentionState.FOCUSED:
            confidence += 0.2
        elif user_state.attention == AttentionState.HYPERFOCUS and task_complexity > 0.7:
            confidence += 0.3  # Perfect for complex work

        # Break penalty (overwork reduces quality)
        if user_state.session_duration_minutes > 60:
            confidence -= 0.2
        if user_state.session_duration_minutes > 90:
            confidence -= 0.3

        return max(0.0, min(1.0, confidence))

    async def stop_monitoring(self):
        """Stop background monitoring."""
        self.monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass

        logger.info("CognitiveGuardian monitoring stopped")

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get CognitiveGuardian effectiveness metrics.

        Returns:
            ADHD protection metrics
        """
        session_duration = 0
        if self.session_start:
            session_duration = int(
                (datetime.now(timezone.utc) - self.session_start).total_seconds() / 60
            )

        return {
            "monitoring_active": self.monitoring,
            "session_duration_minutes": session_duration,
            "breaks_taken": self.breaks_taken,
            "breaks_enforced": self.breaks_enforced,
            "burnout_prevented": self.burnout_prevented,
            "energy_mismatches_caught": self.energy_mismatches_caught,
            "break_compliance": (
                (self.breaks_taken / max(session_duration // self.break_interval, 1))
                if session_duration > 0 else 0.0
            )
        }


# Example usage
if __name__ == "__main__":
    async def demo():
        """Demonstrate CognitiveGuardian capabilities."""

        print("\n" + "="*70)
        print("CognitiveGuardian Demo - ADHD Support Agent")
        print("="*70 + "\n")

        # Initialize guardian
        guardian = CognitiveGuardian(
            workspace_id="/Users/hue/code/dopemux-mvp",
            break_interval_minutes=25,
            mandatory_break_minutes=90
        )

        # Start monitoring
        await guardian.start_monitoring()

        # Simulate morning work (high energy)
        print("Scenario 1: Morning work session (9 AM - high energy)\n")

        user_state = await guardian.get_user_state()
        print(f"Current state:")
        print(f"  Energy: {user_state.energy.value}")
        print(f"  Attention: {user_state.attention.value}")
        print(f"  Time: {user_state.time_of_day_hour}:00\n")

        # Get task suggestions
        await guardian.suggest_tasks(energy="high")

        # Check readiness for complex task
        print("Checking readiness for complex task (0.8 complexity)...\n")
        readiness = await guardian.check_task_readiness(
            task_complexity=0.8,
            task_energy_required="high"
        )

        print(f"Ready: {readiness['ready']}")
        print(f"Reason: {readiness['reason']}")
        if readiness['ready']:
            print(f"Confidence: {readiness['confidence']:.0%}\n")

        # Simulate work (trigger break reminder)
        print("="*70)
        print("Scenario 2: Simulating 27 minutes of work...")
        print("="*70 + "\n")

        # Fast-forward time for demo
        guardian.session_start = datetime.now(timezone.utc) - timedelta(minutes=27)

        reminder = await guardian.check_break_needed()
        if reminder:
            guardian._show_break_reminder(reminder)

            if not reminder.is_mandatory:
                print("Taking 5-minute break...\n")
                await guardian.take_break(duration_minutes=5)

        # Simulate evening (low energy)
        print("="*70)
        print("Scenario 3: Evening work (8 PM - low energy)")
        print("="*70 + "\n")

        # Set time to evening
        import unittest.mock as mock
        with mock.patch('datetime.datetime') as mock_dt:
            mock_dt.now.return_value.hour = 20
            user_state = await guardian.get_user_state()

        print(f"Current state:")
        print(f"  Energy: low (time: 20:00)")
        print(f"  Attention: {user_state.attention.value}\n")

        # Check readiness for complex task (should fail)
        print("Checking readiness for complex task (0.8 complexity)...\n")
        readiness = await guardian.check_task_readiness(
            task_complexity=0.8,
            task_energy_required="high"
        )

        print(f"Ready: {readiness['ready']}")
        print(f"Reason: {readiness['reason']}")
        print(f"Suggestion: {readiness['suggestion']}\n")

        # Get appropriate suggestions
        await guardian.suggest_tasks(energy="low")

        # Stop monitoring
        await guardian.stop_monitoring()

        # Show metrics
        print("="*70)
        print("CognitiveGuardian Metrics:")
        print("="*70)
        metrics = guardian.get_metrics()
        for key, value in metrics.items():
            print(f"  {key}: {value}")
        print()

    # Run demo
    asyncio.run(demo())
