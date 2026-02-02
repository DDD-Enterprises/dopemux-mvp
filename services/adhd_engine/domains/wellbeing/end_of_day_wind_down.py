"""
End-of-Day Wind Down Protocol

Structured session closing ritual to:
- Capture unfinished thoughts to ConPort
- Save cursor positions and context for tomorrow
- Provide quick wins summary
- Prepare tomorrow's top 3 tasks
- Energy recovery check
- Reduce next-day anxiety

ADHD Benefit: Closure, reduces anxiety, prepares for successful next session
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class DailyWrapUp:
    """Daily session wrap-up summary."""
    user_id: str
    date: datetime
    
    # Accomplishments
    tasks_completed: int = 0
    commits_made: int = 0
    focus_minutes: int = 0
    hyperfocus_sessions: int = 0
    breaks_taken: int = 0
    
    # State
    final_energy_level: str = "unknown"
    ending_mood: Optional[str] = None  # User self-report
    
    # Tomorrow's prep
    tomorrow_tasks: List[str] = field(default_factory=list)
    tomorrow_context_saved: bool = False
    
    # Recommendations
    recovery_needed: bool = False
    suggested_evening_activity: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for storage."""
        return {
            "user_id": self.user_id,
            "date": self.date.isoformat(),
            "tasks_completed": self.tasks_completed,
            "commits_made": self.commits_made,
            "focus_minutes": self.focus_minutes,
            "hyperfocus_sessions": self.hyperfocus_sessions,
            "breaks_taken": self.breaks_taken,
            "final_energy_level": self.final_energy_level,
            "ending_mood": self.ending_mood,
            "tomorrow_tasks": self.tomorrow_tasks,
            "tomorrow_context_saved": self.tomorrow_context_saved,
            "recovery_needed": self.recovery_needed,
            "suggested_evening_activity": self.suggested_evening_activity
        }


class EndOfDayWindDown:
    """
    Manage end-of-day wind down ritual.
    
    Integrates with:
    - ConPort: Save unfinished thoughts and context
    - Context Preserver: Save cursor positions
    - Task Recommender: Prepare tomorrow's tasks
    - Energy Tracker: Recovery assessment
    """
    
    def __init__(
        self,
        conport_client=None,
        context_preserver=None,
        typical_end_hour: int = 18  # 6 PM default
    ):
        """
        Initialize wind down manager.
        
        Args:
            conport_client: ConPort client for saving thoughts
            context_preserver: Context preserver for state saving
            typical_end_hour: Typical end-of-day hour (for reminders)
        """
        self.conport = conport_client
        self.context_preserver = context_preserver
        self.typical_end_hour = typical_end_hour
        
        # History
        self.wrap_up_history: List[DailyWrapUp] = []
    
    async def initiate_wind_down(
        self,
        user_id: str,
        current_state: Dict[str, Any],
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Initiate end-of-day wind down ritual.
        
        Args:
            user_id: User identifier
            current_state: Current session state
            force: Force wind down even if not typical end time
        
        Returns:
            Wind down guide with steps and summary
        """
        current_hour = datetime.now().hour
        
        # Check if it's end-of-day time
        if not force and current_hour < self.typical_end_hour:
            return {
                "should_wind_down": False,
                "reason": f"Not yet end-of-day (current: {current_hour}:00, typical: {self.typical_end_hour}:00)",
                "suggestion": "Continue working, or use force=True to wind down early"
            }
        
        logger.info(f"🌅 Initiating end-of-day wind down for {user_id}")
        
        # Step 1: Gather session statistics
        stats = await self._gather_session_stats(user_id, current_state)
        
        # Step 2: Generate wrap-up summary
        wrap_up = self._generate_wrap_up(user_id, stats, current_state)
        
        # Step 3: Capture unfinished thoughts
        thoughts = await self._capture_unfinished_thoughts(user_id, current_state)
        
        # Step 4: Save context for tomorrow
        context_saved = await self._save_tomorrow_context(user_id, current_state)
        wrap_up.tomorrow_context_saved = context_saved
        
        # Step 5: Prepare tomorrow's tasks
        tomorrow_tasks = await self._prepare_tomorrow_tasks(user_id, current_state)
        wrap_up.tomorrow_tasks = tomorrow_tasks
        
        # Step 6: Energy recovery check
        recovery = self._assess_recovery_needs(current_state, stats)
        wrap_up.recovery_needed = recovery['needed']
        wrap_up.suggested_evening_activity = recovery.get('activity')
        
        # Step 7: Mood check-in
        # (In real implementation, would prompt user)
        
        # Store in history
        self.wrap_up_history.append(wrap_up)
        
        return {
            "wind_down_complete": True,
            "summary": self._format_summary(wrap_up),
            "quick_wins": self._extract_quick_wins(stats),
            "tomorrow_preview": {
                "tasks": tomorrow_tasks,
                "predicted_energy": "medium",  # Could use energy predictor here
                "context_saved": context_saved
            },
            "recovery": recovery,
            "closing_message": self._generate_closing_message(wrap_up)
        }
    
    async def _gather_session_stats(
        self,
        user_id: str,
        current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Gather statistics for today's session."""
        # In real implementation, would query activity tracking services
        # For now, extract from current_state or use defaults
        
        return {
            "tasks_completed": current_state.get('tasks_completed', 0),
            "commits_made": current_state.get('commits_made', 0),
            "focus_minutes": current_state.get('total_focus_minutes', 0),
            "hyperfocus_sessions": current_state.get('hyperfocus_count', 0),
            "breaks_taken": current_state.get('breaks_accepted', 0),
            "breaks_suggested": current_state.get('breaks_suggested', 0),
            "context_switches": current_state.get('context_switches', 0)
        }
    
    def _generate_wrap_up(
        self,
        user_id: str,
        stats: Dict[str, Any],
        current_state: Dict[str, Any]
    ) -> DailyWrapUp:
        """Generate wrap-up summary from stats."""
        return DailyWrapUp(
            user_id=user_id,
            date=datetime.now(),
            tasks_completed=stats.get('tasks_completed', 0),
            commits_made=stats.get('commits_made', 0),
            focus_minutes=stats.get('focus_minutes', 0),
            hyperfocus_sessions=stats.get('hyperfocus_sessions', 0),
            breaks_taken=stats.get('breaks_taken', 0),
            final_energy_level=current_state.get('energy_level', 'unknown')
        )
    
    async def _capture_unfinished_thoughts(
        self,
        user_id: str,
        current_state: Dict[str, Any]
    ) -> List[str]:
        """Capture unfinished thoughts to ConPort."""
        thoughts = []
        
        # Get current task/focus
        current_task = current_state.get('current_task')
        if current_task:
            thoughts.append(f"Working on: {current_task}")
        
        # Get open questions/blockers
        blockers = current_state.get('blockers', [])
        thoughts.extend([f"Blocker: {b}" for b in blockers])
        
        # Save to ConPort
        if self.conport and thoughts:
            try:
                await self.conport.log_decision(
                    summary="End-of-day thoughts captured",
                    rationale="Unfinished work context for tomorrow",
                    implementation_details="\n".join(thoughts)
                )
                logger.info(f"💭 Captured {len(thoughts)} thoughts to ConPort")
            except Exception as e:
                logger.error(f"Failed to save thoughts: {e}")
        
        return thoughts
    
    async def _save_tomorrow_context(
        self,
        user_id: str,
        current_state: Dict[str, Any]
    ) -> bool:
        """Save context for tomorrow's session."""
        if not self.context_preserver:
            logger.warning("Context preserver not available")
            return False
        
        try:
            # Use context preserver to save current state
            context = await self.context_preserver.capture_current_context(
                user_id=user_id,
                workspace_path=current_state.get('workspace_path')
            )
            
            logger.info(f"💾 Context saved for tomorrow: {len(context.active_files)} files")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save context: {e}")
            return False
    
    async def _prepare_tomorrow_tasks(
        self,
        user_id: str,
        current_state: Dict[str, Any]
    ) -> List[str]:
        """Prepare top 3 tasks for tomorrow."""
        tasks = []
        
        # Task 1: Continue current work (if unfinished)
        current_task = current_state.get('current_task')
        if current_task:
            tasks.append(f"Continue: {current_task}")
        
        # Task 2: Address any blockers
        blockers = current_state.get('blockers', [])
        if blockers:
            tasks.append(f"Resolve: {blockers[0]}")
        
        # Task 3: Something simple for warm-up
        tasks.append("Warm-up: Review PR comments or update docs")
        
        # Trim to top 3
        return tasks[:3]
    
    def _assess_recovery_needs(
        self,
        current_state: Dict[str, Any],
        stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess if user needs recovery."""
        energy = current_state.get('energy_level', 'medium')
        focus_minutes = stats.get('focus_minutes', 0)
        hyperfocus_count = stats.get('hyperfocus_sessions', 0)
        
        # Determine if recovery needed
        needs_recovery = (
            energy in ['low', 'very_low'] or
            focus_minutes > 240 or  # >4 hours focused
            hyperfocus_count > 1  # Multiple hyperfocus sessions
        )
        
        # Suggest evening activity
        if energy in ['low', 'very_low']:
            activity = "Rest and recharge - avoid screens, early bedtime recommended"
        elif focus_minutes > 240:
            activity = "Light physical activity (walk, yoga) to decompress from intense focus"
        elif hyperfocus_count > 0:
            activity = "Gentle evening - your brain worked hard today, be kind to it"
        else:
            activity = "Normal evening activities, you have good energy reserves"
        
        return {
            "needed": needs_recovery,
            "reason": f"Energy: {energy}, Focus: {focus_minutes}min, Hyperfocus: {hyperfocus_count}",
            "activity": activity,
            "bedtime_suggestion": "Earlier than usual" if needs_recovery else "Normal schedule"
        }
    
    def _format_summary(self, wrap_up: DailyWrapUp) -> str:
        """Format wrap-up summary for display."""
        lines = [
            "🌅 **End-of-Day Summary**",
            "",
            f"✅ **Completed**: {wrap_up.tasks_completed} tasks",
            f"💻 **Commits**: {wrap_up.commits_made}",
            f"🧠 **Focus Time**: {wrap_up.focus_minutes} minutes",
            f"⚡ **Hyperfocus Sessions**: {wrap_up.hyperfocus_sessions}",
            f"☕ **Breaks Taken**: {wrap_up.breaks_taken}",
            f"🔋 **Final Energy**: {wrap_up.final_energy_level.title()}",
        ]
        
        return "\n".join(lines)
    
    def _extract_quick_wins(self, stats: Dict[str, Any]) -> List[str]:
        """Extract quick wins from today's work."""
        wins = []
        
        tasks = stats.get('tasks_completed', 0)
        if tasks > 0:
            wins.append(f"✅ Completed {tasks} {'task' if tasks == 1 else 'tasks'}")
        
        commits = stats.get('commits_made', 0)
        if commits > 0:
            wins.append(f"💻 Made {commits} {'commit' if commits == 1 else 'commits'}")
        
        focus = stats.get('focus_minutes', 0)
        if focus >= 120:
            wins.append(f"🧠 {focus} minutes of focused work")
        
        breaks = stats.get('breaks_taken', 0)
        if breaks > 0:
            wins.append(f"☕ Took {breaks} breaks (self-care!)")
        
        if not wins:
            wins.append("🎯 You showed up and worked - that counts!")
        
        return wins
    
    def _generate_closing_message(self, wrap_up: DailyWrapUp) -> str:
        """Generate encouraging closing message."""
        energy = wrap_up.final_energy_level
        
        if energy in ['low', 'very_low']:
            return "You worked hard today. Your brain needs rest. Disconnect, recharge, and come back fresh tomorrow. 💙"
        elif wrap_up.hyperfocus_sessions > 0:
            return "Impressive focus today! Remember to recover well. Tomorrow is another opportunity. 🌟"
        elif wrap_up.tasks_completed > 3:
            return "Productive day! You accomplished a lot. Celebrate your wins and rest well. 🎉"
        else:
            return "Every day you show up matters. Rest well and we'll tackle tomorrow together. 💪"
    
    def should_remind_wind_down(self, user_id: str, current_hour: int) -> bool:
        """Check if should remind user to wind down."""
        # Remind at typical end hour + 30 min
        if current_hour == self.typical_end_hour:
            return True
        
        # Stronger reminder 1 hour past typical
        if current_hour == self.typical_end_hour + 1:
            return True
        
        return False
    
    def get_wind_down_reminder_message(self, current_hour: int) -> str:
        """Get wind down reminder message."""
        if current_hour == self.typical_end_hour:
            return "🌅 It's about that time. Ready to wrap up for the day?"
        elif current_hour > self.typical_end_hour:
            return f"⏰ It's {current_hour}:00. Time to wind down - your brain needs rest!"
        else:
            return "Consider wrapping up your session soon."


# Convenience function
async def wind_down_now(
    user_id: str,
    current_state: Dict[str, Any],
    conport_client=None,
    context_preserver=None
) -> Dict[str, Any]:
    """
    Perform end-of-day wind down immediately.
    
    Args:
        user_id: User identifier
        current_state: Current session state
        conport_client: Optional ConPort client
        context_preserver: Optional context preserver
    
    Returns:
        Wind down summary
    """
    wind_down = EndOfDayWindDown(
        conport_client=conport_client,
        context_preserver=context_preserver
    )
    
    return await wind_down.initiate_wind_down(
        user_id=user_id,
        current_state=current_state,
        force=True
    )
