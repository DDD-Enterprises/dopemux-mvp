"""
Procrastination Detection & Intervention

Detects procrastination patterns:
- Research rabbit holes (endless reading without output)
- Productive procrastination (cleaning code instead of hard task)
- Task switching carousel (avoiding the real priority)
- Perfectionism paralysis (endless polishing, no shipping)

Gentle interventions:
- Micro-tasks (5-minute commitment)
- Gamification (streaks, rewards)
- Accountability check-ins
- Task breakdown assistance

ADHD Benefit: Non-judgmental awareness, actionable interventions
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ProcrastinationType(Enum):
    """Types of procrastination patterns."""
    NONE = "none"
    RESEARCH_RABBIT_HOLE = "research_rabbit_hole"
    PRODUCTIVE_PROCRASTINATION = "productive_procrastination"
    TASK_SWITCHING_CAROUSEL = "task_switching_carousel"
    PERFECTIONISM_PARALYSIS = "perfectionism_paralysis"
    DECISION_PARALYSIS = "decision_paralysis"


@dataclass
class ProcrastinationSignal:
    """Individual procrastination signal."""
    signal_type: ProcrastinationType
    confidence: float  # 0.0-1.0
    evidence: List[str]
    duration_minutes: int
    detected_at: datetime


@dataclass
class MicroTask:
    """5-minute micro-task for intervention."""
    task_id: str
    description: str
    estimated_minutes: int = 5
    parent_task: Optional[str] = None
    completed: bool = False
    completed_at: Optional[datetime] = None


class ProcrastinationDetector:
    """
    Detect and intervene on procrastination patterns.
    
    Uses gentle, ADHD-friendly interventions:
    - Non-judgmental awareness
    - Micro-tasks (5-min commitments)
    - Gamification
    - Supportive accountability
    """
    
    def __init__(
        self,
        research_threshold_minutes: int = 30,
        switching_threshold: int = 5,
        polish_threshold_minutes: int = 45
    ):
        """
        Initialize procrastination detector.
        
        Args:
            research_threshold_minutes: Minutes of reading with no output
            switching_threshold: Number of switches in 20 minutes
            polish_threshold_minutes: Minutes polishing same work
        """
        self.research_threshold = research_threshold_minutes
        self.switching_threshold = switching_threshold
        self.polish_threshold = polish_threshold_minutes
        
        # State tracking
        self.detected_patterns: List[ProcrastinationSignal] = []
        self.micro_tasks_offered: List[MicroTask] = []
        self.intervention_history: List[Dict[str, Any]] = []
        
        # Gamification state
        self.micro_task_streak = 0
        self.total_micro_tasks_completed = 0
    
    async def check_procrastination(
        self,
        user_id: str,
        activity_data: Dict[str, Any],
        priority_task: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check for procrastination patterns.
        
        Args:
            user_id: User identifier
            activity_data: Recent activity with:
                - file_views: List of files viewed
                - file_edits: List of files edited
                - git_commits: Recent commits
                - task_switches: Recent task changes
                - time_on_current_task: Minutes
            priority_task: The high-priority task user should work on
        
        Returns:
            Detection results with interventions
        """
        signals = []
        
        # Signal 1: Research rabbit hole
        research_signal = self._detect_research_rabbit_hole(activity_data)
        if research_signal:
            signals.append(research_signal)
        
        # Signal 2: Productive procrastination
        prod_proc_signal = self._detect_productive_procrastination(
            activity_data,
            priority_task
        )
        if prod_proc_signal:
            signals.append(prod_proc_signal)
        
        # Signal 3: Task switching carousel
        switching_signal = self._detect_task_switching(activity_data)
        if switching_signal:
            signals.append(switching_signal)
        
        # Signal 4: Perfectionism paralysis
        perfectionism_signal = self._detect_perfectionism(activity_data)
        if perfectionism_signal:
            signals.append(perfectionism_signal)
        
        # Signal 5: Decision paralysis
        decision_signal = self._detect_decision_paralysis(activity_data)
        if decision_signal:
            signals.append(decision_signal)
        
        # Store detected patterns
        self.detected_patterns.extend(signals)
        
        # Generate interventions if procrastination detected
        if signals:
            interventions = await self._generate_interventions(
                user_id,
                signals,
                priority_task
            )
            
            return {
                "procrastination_detected": True,
                "patterns": [
                    {
                        "type": s.signal_type.value,
                        "confidence": s.confidence,
                        "evidence": s.evidence,
                        "duration_minutes": s.duration_minutes
                    }
                    for s in signals
                ],
                "interventions": interventions,
                "tone": "supportive"  # Always supportive, never judgmental
            }
        else:
            return {
                "procrastination_detected": False,
                "message": "Focused work detected. Keep it up! 🎯"
            }
    
    def _detect_research_rabbit_hole(
        self,
        activity_data: Dict[str, Any]
    ) -> Optional[ProcrastinationSignal]:
        """Detect endless research with no output."""
        file_views = activity_data.get('file_views', [])
        file_edits = activity_data.get('file_edits', [])
        time_reading = activity_data.get('time_reading_minutes', 0)
        
        # Many views, few edits = research rabbit hole
        view_count = len(file_views)
        edit_count = len(file_edits)
        
        if view_count > 10 and edit_count < 2 and time_reading > self.research_threshold:
            evidence = [
                f"Viewed {view_count} files but edited only {edit_count}",
                f"Reading for {time_reading} minutes without writing",
                "Low output-to-input ratio"
            ]
            
            return ProcrastinationSignal(
                signal_type=ProcrastinationType.RESEARCH_RABBIT_HOLE,
                confidence=min(1.0, time_reading / 60),
                evidence=evidence,
                duration_minutes=time_reading,
                detected_at=datetime.now()
            )
        
        return None
    
    def _detect_productive_procrastination(
        self,
        activity_data: Dict[str, Any],
        priority_task: Optional[str]
    ) -> Optional[ProcrastinationSignal]:
        """Detect doing useful work to avoid hard task."""
        if not priority_task:
            return None
        
        current_task = activity_data.get('current_task')
        recent_commits = activity_data.get('git_commits', [])
        
        # Check if working on non-priority items
        if current_task and current_task != priority_task:
            # Check if commits are low-value (refactoring, docs, formatting)
            low_value_indicators = ['refactor', 'cleanup', 'format', 'docs', 'comment']
            recent_commit_msgs = [c.get('message', '').lower() for c in recent_commits]
            
            low_value_count = sum(
                1 for msg in recent_commit_msgs
                if any(indicator in msg for indicator in low_value_indicators)
            )
            
            if low_value_count >= 2:
                evidence = [
                    f"Priority task: '{priority_task}'",
                    f"Actually working on: '{current_task}'",
                    f"{low_value_count} low-value commits (cleanup, formatting, etc.)",
                    "Avoiding high-priority, high-difficulty work"
                ]
                
                return ProcrastinationSignal(
                    signal_type=ProcrastinationType.PRODUCTIVE_PROCRASTINATION,
                    confidence=0.75,
                    evidence=evidence,
                    duration_minutes=activity_data.get('time_on_current_task', 0),
                    detected_at=datetime.now()
                )
        
        return None
    
    def _detect_task_switching(
        self,
        activity_data: Dict[str, Any]
    ) -> Optional[ProcrastinationSignal]:
        """Detect rapid task switching (carousel)."""
        task_switches = activity_data.get('task_switches', [])
        time_window = 20  # minutes
        
        # Count switches in last 20 minutes
        now = datetime.now()
        recent_switches = [
            s for s in task_switches
            if isinstance(s, dict) and
            (now - s.get('timestamp', now)).total_seconds() / 60 <= time_window
        ]
        
        if len(recent_switches) >= self.switching_threshold:
            evidence = [
                f"{len(recent_switches)} task switches in {time_window} minutes",
                f"Tasks: {', '.join(s.get('task', 'unknown') for s in recent_switches[:3])}...",
                "Unable to commit to single task"
            ]
            
            return ProcrastinationSignal(
                signal_type=ProcrastinationType.TASK_SWITCHING_CAROUSEL,
                confidence=min(1.0, len(recent_switches) / 10),
                evidence=evidence,
                duration_minutes=time_window,
                detected_at=datetime.now()
            )
        
        return None
    
    def _detect_perfectionism(
        self,
        activity_data: Dict[str, Any]
    ) -> Optional[ProcrastinationSignal]:
        """Detect endless polishing without shipping."""
        same_file_time = activity_data.get('time_on_same_file_minutes', 0)
        edit_count = activity_data.get('edit_count_same_file', 0)
        commits = activity_data.get('git_commits', [])
        
        # Many edits to same file, long time, but no commits
        if same_file_time > self.polish_threshold and edit_count > 20 and len(commits) == 0:
            evidence = [
                f"Editing same file for {same_file_time} minutes",
                f"{edit_count} edits but no commits",
                "Polishing without shipping"
            ]
            
            return ProcrastinationSignal(
                signal_type=ProcrastinationType.PERFECTIONISM_PARALYSIS,
                confidence=0.8,
                evidence=evidence,
                duration_minutes=same_file_time,
                detected_at=datetime.now()
            )
        
        return None
    
    def _detect_decision_paralysis(
        self,
        activity_data: Dict[str, Any]
    ) -> Optional[ProcrastinationSignal]:
        """Detect stuck on decision-making."""
        # Look for: viewing multiple similar files, no action
        file_views = activity_data.get('file_views', [])
        file_edits = activity_data.get('file_edits', [])
        time_deciding = activity_data.get('time_on_current_task', 0)
        
        # Similar files viewed repeatedly, but no edits
        if len(file_views) > 5 and len(file_edits) == 0 and time_deciding > 20:
            # Check for repeated viewing of same files
            unique_views = set(file_views)
            if len(file_views) > len(unique_views) * 1.5:  # Repeated views
                evidence = [
                    f"Viewed {len(file_views)} files ({len(unique_views)} unique)",
                    "Repeated viewing of same files",
                    f"No edits in {time_deciding} minutes",
                    "Analysis paralysis - can't decide how to proceed"
                ]
                
                return ProcrastinationSignal(
                    signal_type=ProcrastinationType.DECISION_PARALYSIS,
                    confidence=0.7,
                    evidence=evidence,
                    duration_minutes=time_deciding,
                    detected_at=datetime.now()
                )
        
        return None
    
    async def _generate_interventions(
        self,
        user_id: str,
        signals: List[ProcrastinationSignal],
        priority_task: Optional[str]
    ) -> Dict[str, Any]:
        """Generate interventions for detected procrastination."""
        # Get strongest signal
        primary_signal = max(signals, key=lambda s: s.confidence)
        
        interventions = {
            "awareness_message": self._get_awareness_message(primary_signal),
            "micro_tasks": [],
            "gamification": self._get_gamification_status(),
            "accountability": None,
            "encouragement": self._get_encouragement(primary_signal)
        }
        
        # Generate micro-tasks based on pattern
        if primary_signal.signal_type == ProcrastinationType.RESEARCH_RABBIT_HOLE:
            micro_tasks = self._create_output_micro_tasks(priority_task)
        elif primary_signal.signal_type == ProcrastinationType.PRODUCTIVE_PROCRASTINATION:
            micro_tasks = self._create_priority_micro_tasks(priority_task)
        elif primary_signal.signal_type == ProcrastinationType.TASK_SWITCHING_CAROUSEL:
            micro_tasks = self._create_commitment_micro_tasks(priority_task)
        elif primary_signal.signal_type == ProcrastinationType.PERFECTIONISM_PARALYSIS:
            micro_tasks = self._create_shipping_micro_tasks()
        elif primary_signal.signal_type == ProcrastinationType.DECISION_PARALYSIS:
            micro_tasks = self._create_decision_micro_tasks()
        else:
            micro_tasks = []
        
        # Store and return micro-tasks
        self.micro_tasks_offered.extend(micro_tasks)
        interventions["micro_tasks"] = [
            {
                "task_id": mt.task_id,
                "description": mt.description,
                "estimated_minutes": mt.estimated_minutes
            }
            for mt in micro_tasks
        ]
        
        # Record intervention
        self.intervention_history.append({
            "user_id": user_id,
            "timestamp": datetime.now(),
            "pattern": primary_signal.signal_type.value,
            "intervention": interventions
        })
        
        return interventions
    
    def _get_awareness_message(self, signal: ProcrastinationSignal) -> str:
        """Get gentle awareness message."""
        messages = {
            ProcrastinationType.RESEARCH_RABBIT_HOLE: (
                "💡 **Gentle observation**: You've been reading for a while without writing. "
                "Research is valuable, but let's capture some output before we forget!"
            ),
            ProcrastinationType.PRODUCTIVE_PROCRASTINATION: (
                "🎯 **Friendly reminder**: That's useful work, but there's a harder task waiting. "
                "This might be avoidance (totally normal!). Want to tackle the priority first?"
            ),
            ProcrastinationType.TASK_SWITCHING_CAROUSEL: (
                "🔄 **Pattern noticed**: You're switching between tasks rapidly. "
                "Totally get the restless feeling! Let's pick one and commit for just 5 minutes."
            ),
            ProcrastinationType.PERFECTIONISM_PARALYSIS: (
                "✨ **Observation**: You've been polishing this for a while. "
                "It's probably already good enough! Done is better than perfect. Ready to ship?"
            ),
            ProcrastinationType.DECISION_PARALYSIS: (
                "🤔 **I see you're stuck on a decision**. Analysis paralysis is real! "
                "Let's pick one option and move forward - we can always iterate."
            )
        }
        
        return messages.get(signal.signal_type, "Let's refocus together.")
    
    def _get_encouragement(self, signal: ProcrastinationSignal) -> str:
        """Get encouraging message."""
        return (
            "Remember: Progress > Perfection. Every small step counts. "
            "You've got this! 💪"
        )
    
    def _create_output_micro_tasks(self, priority_task: Optional[str]) -> List[MicroTask]:
        """Create micro-tasks to generate output from research."""
        return [
            MicroTask(
                task_id=f"micro_{datetime.now().timestamp()}_1",
                description="Write 3 bullet points summarizing what you learned",
                estimated_minutes=3,
                parent_task=priority_task
            ),
            MicroTask(
                task_id=f"micro_{datetime.now().timestamp()}_2",
                description="Create one test case based on your research",
                estimated_minutes=5,
                parent_task=priority_task
            ),
            MicroTask(
                task_id=f"micro_{datetime.now().timestamp()}_3",
                description="Write one function signature you'll implement",
                estimated_minutes=2,
                parent_task=priority_task
            )
        ]
    
    def _create_priority_micro_tasks(self, priority_task: Optional[str]) -> List[MicroTask]:
        """Create micro-tasks for priority work."""
        return [
            MicroTask(
                task_id=f"micro_{datetime.now().timestamp()}_1",
                description=f"Work on {priority_task or 'priority task'} for just 5 minutes",
                estimated_minutes=5,
                parent_task=priority_task
            ),
            MicroTask(
                task_id=f"micro_{datetime.now().timestamp()}_2",
                description="Write the simplest possible version (no perfection)",
                estimated_minutes=10,
                parent_task=priority_task
            )
        ]
    
    def _create_commitment_micro_tasks(self, priority_task: Optional[str]) -> List[MicroTask]:
        """Create micro-tasks to commit to one thing."""
        return [
            MicroTask(
                task_id=f"micro_{datetime.now().timestamp()}_1",
                description="Pick ONE task and close all other files",
                estimated_minutes=2,
                parent_task=priority_task
            ),
            MicroTask(
                task_id=f"micro_{datetime.now().timestamp()}_2",
                description="Set timer for 15 min and commit to this task only",
                estimated_minutes=15,
                parent_task=priority_task
            )
        ]
    
    def _create_shipping_micro_tasks(self) -> List[MicroTask]:
        """Create micro-tasks to ship work."""
        return [
            MicroTask(
                task_id=f"micro_{datetime.now().timestamp()}_1",
                description="Commit current state as 'WIP' - preserve your work!",
                estimated_minutes=2
            ),
            MicroTask(
                task_id=f"micro_{datetime.now().timestamp()}_2",
                description="Ask: 'What's the minimum viable version?' - do that",
                estimated_minutes=10
            )
        ]
    
    def _create_decision_micro_tasks(self) -> List[MicroTask]:
        """Create micro-tasks to break decision paralysis."""
        return [
            MicroTask(
                task_id=f"micro_{datetime.now().timestamp()}_1",
                description="Flip a coin: pick option A or B and commit",
                estimated_minutes=1
            ),
            MicroTask(
                task_id=f"micro_{datetime.now().timestamp()}_2",
                description="Implement the simplest approach - iterate later",
                estimated_minutes=10
            )
        ]
    
    def _get_gamification_status(self) -> Dict[str, Any]:
        """Get gamification status."""
        return {
            "current_streak": self.micro_task_streak,
            "total_completed": self.total_micro_tasks_completed,
            "next_milestone": self._get_next_milestone(),
            "badge_earned": self._check_badge_earned()
        }
    
    def _get_next_milestone(self) -> str:
        """Get next gamification milestone."""
        if self.total_micro_tasks_completed < 5:
            return f"{5 - self.total_micro_tasks_completed} micro-tasks until 'Getting Started' badge"
        elif self.total_micro_tasks_completed < 25:
            return f"{25 - self.total_micro_tasks_completed} micro-tasks until 'Momentum Builder' badge"
        else:
            return "You're crushing it! Keep the streak alive 🔥"
    
    def _check_badge_earned(self) -> Optional[str]:
        """Check if new badge earned."""
        if self.total_micro_tasks_completed == 5:
            return "🎖️ Getting Started - First 5 micro-tasks!"
        elif self.total_micro_tasks_completed == 25:
            return "🏆 Momentum Builder - 25 micro-tasks completed!"
        elif self.total_micro_tasks_completed == 100:
            return "👑 Procrastination Warrior - 100 micro-tasks!"
        return None
    
    def complete_micro_task(self, task_id: str) -> Dict[str, Any]:
        """Mark micro-task as complete."""
        task = next((t for t in self.micro_tasks_offered if t.task_id == task_id), None)
        
        if not task:
            return {"error": "Task not found"}
        
        if task.completed:
            return {"error": "Task already completed"}
        
        task.completed = True
        task.completed_at = datetime.now()
        
        self.total_micro_tasks_completed += 1
        self.micro_task_streak += 1
        
        badge = self._check_badge_earned()
        
        return {
            "success": True,
            "task": task.description,
            "streak": self.micro_task_streak,
            "total": self.total_micro_tasks_completed,
            "badge_earned": badge,
            "encouragement": "Nice! One step at a time. 🎯"
        }
