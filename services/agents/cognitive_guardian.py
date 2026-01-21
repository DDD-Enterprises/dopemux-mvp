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
    workspace_path: Optional[str] = None  # Multi-workspace tracking


@dataclass
class BreakReminder:
    """Break reminder with ADHD-friendly messaging."""
    type: str  # "gentle", "warning", "mandatory"
    message: str
    duration_worked_minutes: int
    suggested_break_minutes: int
    is_mandatory: bool
    workspace_path: Optional[str] = None  # Multi-workspace tracking


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
            logger.info(reminder.message)
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
        
        # MCP Integration
        self._in_claude_code = self._detect_claude_code_context()

        logger.info(
            f"CognitiveGuardian initialized (break interval: {break_interval_minutes}min, "
            f"mandatory: {mandatory_break_minutes}min, MCP: {self._in_claude_code})"
        )
    
    def _detect_claude_code_context(self) -> bool:
        """Detect if running in Claude Code/MCP environment."""
        try:
            import sys
            return 'mcp' in sys.modules or hasattr(sys, '_mcp_tools')
        except Exception as e:
            return False
    
            logger.error(f"Error: {e}")
    async def _load_user_preferences(self):
        """Load ADHD preferences from ConPort."""
        if not self._in_claude_code:
            return
            
        try:
            from mcp_tools import mcp__conport__get_custom_data
            
            prefs = await mcp__conport__get_custom_data(
                workspace_id=self.workspace_id,
                category="adhd_preferences",
                key="break_intervals"
            )
            
            if prefs:
                self.break_interval = prefs.get("gentle_reminder", 25)
                self.mandatory_break = prefs.get("mandatory", 90)
                self.hyperfocus_warning = prefs.get("hyperfocus_warning", 60)
                
                logger.info(f"Loaded ADHD preferences: {prefs}")
        except Exception as e:
            logger.warning(f"Could not load preferences, using defaults: {e}")

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
        logger.info(f"\n🧠 CognitiveGuardian Active")
        logger.info(f"   Break reminders: Every {self.break_interval} minutes")
        logger.info(f"   Mandatory break: At {self.mandatory_break} minutes")
        logger.info(f"   Your wellbeing is protected!\n")

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
        logger.info(f"\n{'='*60}")
        logger.info(reminder.message)
        logger.info(f"{'='*60}\n")

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

        logger.info(f"\n✅ Break recorded!")
        logger.info(f"   Duration: {duration_minutes} minutes")
        logger.info(f"   Total breaks: {self.breaks_taken}")
        logger.info(f"   Ready to continue when you are!\n")
    
    async def _save_user_state(self, user_state: UserState):
        """
        Persist user state to ConPort for cross-session continuity.
        
        Args:
            user_state: Current user state to save
        """
        if not self._in_claude_code:
            return  # Skip if not in Claude Code
        
        try:
            # Dynamic import to avoid dependency when not in Claude Code
            from mcp_tools import mcp__conport__update_active_context
            
            await mcp__conport__update_active_context(
                workspace_id=self.workspace_id,
                patch_content={
                    "cognitive_guardian_state": {
                        "energy": user_state.energy.value,
                        "attention": user_state.attention.value,
                        "session_duration_minutes": user_state.session_duration_minutes,
                        "breaks_taken": user_state.breaks_taken,
                        "last_break": user_state.last_break,
                        "current_task_complexity": user_state.current_task_complexity,
                        "time_of_day_hour": user_state.time_of_day_hour,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
            
            logger.debug("User state persisted to ConPort")
        except Exception as e:
            logger.error(f"Failed to save user state: {e}")
    
    async def _save_metrics(self):
        """Persist metrics to ConPort for tracking."""
        if not self._in_claude_code:
            return
        
        try:
            from mcp_tools import mcp__conport__log_custom_data
            
            metrics = self.get_metrics()
            
            await mcp__conport__log_custom_data(
                workspace_id=self.workspace_id,
                category="adhd_metrics",
                key=f"session_{datetime.now(timezone.utc).isoformat()}",
                value=metrics
            )
            
            logger.debug("Metrics persisted to ConPort")
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")

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

        user_state = UserState(
            energy=energy,
            attention=attention,
            session_duration_minutes=session_duration,
            breaks_taken=self.breaks_taken,
            last_break=self.last_break.isoformat() if self.last_break else None,
            current_task_complexity=current_complexity,
            time_of_day_hour=hour
        )
        
        # Persist to ConPort
        await self._save_user_state(user_state)
        
        return user_state

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

        # Real ConPort queries or fallback to simulation
        if not self._in_claude_code:
            return self._simulate_task_suggestions(target_energy, max_suggestions)

        try:
            from mcp_tools import mcp__conport__get_progress

            # Get all TODO tasks from ConPort
            all_tasks = await mcp__conport__get_progress(
                workspace_id=self.workspace_id,
                status="TODO"
            )

            # Filter by energy level and attention state
            matched_tasks = []
            for task in all_tasks:
                task_energy = task.get("energy_required", "medium")
                task_complexity = task.get("complexity", 0.5)

                # Energy match
                if task_energy != target_energy:
                    continue

                # Attention match (if scattered, skip complex tasks)
                if user_state.attention == AttentionState.SCATTERED:
                    if task_complexity > 0.5:
                        continue  # Skip complex when scattered

                # Calculate match score
                match_score = self._calculate_task_match_score(
                    user_state, task_complexity, task_energy
                )

                matched_tasks.append({
                    "title": task.get("title", "Untitled"),
                    "complexity": task_complexity,
                    "energy_required": task_energy,
                    "description": task.get("description", ""),
                    "match_score": match_score
                })

            # Sort by match score (descending)
            matched_tasks.sort(key=lambda t: t["match_score"], reverse=True)

            # Limit to max_suggestions (ADHD: prevent overwhelm)
            top_tasks = matched_tasks[:max_suggestions]

            # Display suggestions
            logger.info(f"\n🎯 Task Suggestions (Energy: {target_energy})")
            logger.info(f"   Attention: {user_state.attention.value}")
            logger.info(f"   Found {len(matched_tasks)} matches, showing top {len(top_tasks)}\n")

            for i, task in enumerate(top_tasks, 1):
                logger.info(f"   {i}. {task['title']} (complexity: {task['complexity']:.1f})")
            logger.info()

            return top_tasks

        except Exception as e:
            logger.error(f"ConPort query failed: {e}")
            return self._simulate_task_suggestions(target_energy, max_suggestions)

    def _calculate_task_match_score(
        self,
        user_state: UserState,
        task_complexity: float,
        task_energy: str
    ) -> float:
        """Calculate how well a task matches user's current state."""
        score = 0.5  # Base score

        # Energy match bonus
        if task_energy == user_state.energy.value:
            score += 0.3

        # Complexity match to attention
        if user_state.attention == AttentionState.HYPERFOCUS:
            if task_complexity > 0.7:
                score += 0.2  # Perfect for complex work
        elif user_state.attention == AttentionState.FOCUSED:
            if 0.3 <= task_complexity <= 0.7:
                score += 0.2  # Moderate complexity ok
        elif user_state.attention == AttentionState.SCATTERED:
            if task_complexity < 0.3:
                score += 0.2  # Simple only

        return min(1.0, score)

    def _simulate_task_suggestions(
        self,
        target_energy: str,
        max_suggestions: int
    ) -> List[Dict[str, Any]]:
        """Simulation mode for when ConPort unavailable."""
        logger.info(f"\n🎯 Task Suggestions (Energy: {target_energy}) [SIMULATION]")
        logger.info(f"   ConPort unavailable, showing examples\n")

    def _simulate_task_suggestions(
        self,
        target_energy: str,
        max_suggestions: int
    ) -> List[Dict[str, Any]]:
        """Simulation mode for when ConPort unavailable."""
        logger.info(f"\n🎯 Task Suggestions (Energy: {target_energy}) [SIMULATION]")
        logger.info(f"   ConPort unavailable, showing examples\n")

        if target_energy == "high":
            logger.info("   Suggested (complex tasks):")
            logger.info("   1. Design microservices architecture (complexity: 0.8)")
            logger.info("   2. Refactor authentication system (complexity: 0.7)")
            logger.info("   3. Implement real-time WebSocket sync (complexity: 0.9)\n")
        elif target_energy == "medium":
            logger.info("   Suggested (moderate tasks):")
            logger.info("   1. Add input validation to API (complexity: 0.5)")
            logger.info("   2. Write integration tests (complexity: 0.4)")
            logger.info("   3. Update documentation (complexity: 0.3)\n")
        else:  # low
            logger.info("   Suggested (simple tasks):")
            logger.info("   1. Fix typos in comments (complexity: 0.1)")
            logger.info("   2. Update README formatting (complexity: 0.2)")
            logger.info("   3. Run and review test suite (complexity: 0.2)\n")

        return []  # No real tasks in simulation

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

        # Save final metrics
        await self._save_metrics()

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

        logger.info("\n" + "="*70)
        logger.info("CognitiveGuardian Demo - ADHD Support Agent")
        logger.info("="*70 + "\n")

        # Initialize guardian
        guardian = CognitiveGuardian(
            workspace_id="/Users/hue/code/dopemux-mvp",
            break_interval_minutes=25,
            mandatory_break_minutes=90
        )

        # Start monitoring
        await guardian.start_monitoring()

        # Simulate morning work (high energy)
        logger.info("Scenario 1: Morning work session (9 AM - high energy)\n")

        user_state = await guardian.get_user_state()
        logger.info(f"Current state:")
        logger.info(f"  Energy: {user_state.energy.value}")
        logger.info(f"  Attention: {user_state.attention.value}")
        logger.info(f"  Time: {user_state.time_of_day_hour}:00\n")

        # Get task suggestions
        await guardian.suggest_tasks(energy="high")

        # Check readiness for complex task
        logger.info("Checking readiness for complex task (0.8 complexity)...\n")
        readiness = await guardian.check_task_readiness(
            task_complexity=0.8,
            task_energy_required="high"
        )

        logger.info(f"Ready: {readiness['ready']}")
        logger.info(f"Reason: {readiness['reason']}")
        if readiness['ready']:
            logger.info(f"Confidence: {readiness['confidence']:.0%}\n")

        # Simulate work (trigger break reminder)
        logger.info("="*70)
        logger.info("Scenario 2: Simulating 27 minutes of work...")
        logger.info("="*70 + "\n")

        # Fast-forward time for demo
        guardian.session_start = datetime.now(timezone.utc) - timedelta(minutes=27)

        reminder = await guardian.check_break_needed()
        if reminder:
            guardian._show_break_reminder(reminder)

            if not reminder.is_mandatory:
                logger.info("Taking 5-minute break...\n")
                await guardian.take_break(duration_minutes=5)

        # Simulate evening (low energy)
        logger.info("="*70)
        logger.info("Scenario 3: Evening work (8 PM - low energy)")
        logger.info("="*70 + "\n")

        # Set time to evening
        import unittest.mock as mock
        with mock.patch('datetime.datetime') as mock_dt:
            mock_dt.now.return_value.hour = 20
            user_state = await guardian.get_user_state()

        logger.info(f"Current state:")
        logger.info(f"  Energy: low (time: 20:00)")
        logger.info(f"  Attention: {user_state.attention.value}\n")

        # Check readiness for complex task (should fail)
        logger.info("Checking readiness for complex task (0.8 complexity)...\n")
        readiness = await guardian.check_task_readiness(
            task_complexity=0.8,
            task_energy_required="high"
        )

        logger.info(f"Ready: {readiness['ready']}")
        logger.info(f"Reason: {readiness['reason']}")
        logger.info(f"Suggestion: {readiness['suggestion']}\n")

        # Get appropriate suggestions
        await guardian.suggest_tasks(energy="low")

        # Stop monitoring
        await guardian.stop_monitoring()

        # Show metrics
        logger.info("="*70)
        logger.info("CognitiveGuardian Metrics:")
        logger.info("="*70)
        metrics = guardian.get_metrics()
        for key, value in metrics.items():
            logger.info(f"  {key}: {value}")
        logger.info()

    # Run demo
    asyncio.run(demo())
