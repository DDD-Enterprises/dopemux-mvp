"""
F-NEW-9 Week 1: Energy-Aware Task Matching Engine

Core algorithm matching tasks to cognitive state.
ADHD Optimization: Prevents task-energy mismatch, reduces decision fatigue.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class EnergyLevel(str, Enum):
    """Energy levels from F-NEW-6 Session Intelligence."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AttentionState(str, Enum):
    """Attention states from ADHD Engine."""
    FOCUSED = "focused"
    TRANSITIONING = "transitioning"
    SCATTERED = "scattered"


@dataclass
class CognitiveState:
    """Current cognitive state from F-NEW-6."""
    energy: EnergyLevel
    attention: AttentionState
    cognitive_load: float  # 0.0-1.0
    time_until_break_min: Optional[int] = None


@dataclass
class Task:
    """Task with ADHD-relevant metadata."""
    task_id: str
    title: str
    description: str
    complexity: float  # 0.0-1.0 from F-NEW-3
    estimated_minutes: int
    priority: str  # "low", "medium", "high", "critical"
    task_type: str  # "deep_work", "implementation", "documentation", "bug_fix", "review"
    requires_focus: bool  # True for tasks needing sustained attention


@dataclass
class TaskSuggestion:
    """Task suggestion with match reasoning."""
    task: Task
    match_score: float  # 0.0-1.0
    rank: int
    match_reason: str
    energy_alignment: float
    attention_alignment: float
    time_alignment: float


class EnergyTaskMatcher:
    """
    Matches energy level to task complexity.

    Matrix:
    - High energy → 0.6-1.0 complexity (refactoring, architecture)
    - Medium energy → 0.3-0.6 complexity (implementation, features)
    - Low energy → 0.0-0.3 complexity (docs, fixes, reviews)
    """

    @staticmethod
    def calculate_energy_match(energy: EnergyLevel, complexity: float) -> Tuple[float, str]:
        """
        Calculate energy-complexity alignment score.

        Returns:
            (score, reason) where score is 0.0-1.0

        Perfect match scores:
        - High energy + high complexity (0.7-1.0): 1.0
        - Medium energy + medium complexity (0.3-0.6): 1.0
        - Low energy + low complexity (0.0-0.3): 1.0
        """
        if energy == EnergyLevel.HIGH:
            # Prefer high complexity during high energy
            if complexity >= 0.7:
                score = 1.0
                reason = "High energy perfect for complex refactoring/architecture"
            elif complexity >= 0.5:
                score = 0.8
                reason = "High energy good for moderate complexity"
            elif complexity >= 0.3:
                score = 0.5
                reason = "High energy underutilized on medium task"
            else:
                score = 0.2
                reason = "High energy wasted on simple task - consider harder work"

        elif energy == EnergyLevel.MEDIUM:
            # Prefer medium complexity
            if 0.3 <= complexity <= 0.6:
                score = 1.0
                reason = "Medium energy matches implementation/feature work"
            elif complexity > 0.6:
                score = 0.6
                reason = "Medium energy may struggle with high complexity"
            else:
                score = 0.7
                reason = "Medium energy works for simple tasks but underutilized"

        else:  # LOW
            # Prefer low complexity
            if complexity <= 0.3:
                score = 1.0
                reason = "Low energy perfect for documentation/fixes"
            elif complexity <= 0.5:
                score = 0.5
                reason = "Low energy may struggle with moderate complexity"
            else:
                score = 0.1
                reason = "Low energy + high complexity = frustration risk"

        return score, reason


class AttentionTaskMatcher:
    """
    Matches attention state to task type characteristics.

    Matrix:
    - Focused → Deep work, complex logic, sustained concentration
    - Transitioning → Moderate tasks, clear boundaries
    - Scattered → Atomic tasks, checklists, no dependencies
    """

    @staticmethod
    def calculate_attention_match(attention: AttentionState, task: Task) -> Tuple[float, str]:
        """
        Calculate attention-task type alignment score.

        Returns:
            (score, reason) where score is 0.0-1.0
        """
        if attention == AttentionState.FOCUSED:
            # Can handle any task, prefer deep work
            if task.requires_focus or task.task_type in ['deep_work', 'architecture', 'refactoring']:
                score = 1.0
                reason = "Focused attention ideal for deep work"
            elif task.task_type in ['implementation', 'feature']:
                score = 0.9
                reason = "Focused attention great for implementation"
            else:
                score = 0.7
                reason = "Focused attention works but task doesn't require it"

        elif attention == AttentionState.TRANSITIONING:
            # Prefer moderate tasks with clear boundaries
            if task.requires_focus:
                score = 0.5
                reason = "Transitioning attention may struggle with deep focus tasks"
            elif task.task_type in ['implementation', 'feature', 'bug_fix']:
                score = 1.0
                reason = "Transitioning attention good for bounded tasks"
            else:
                score = 0.8
                reason = "Transitioning attention works for simple tasks"

        else:  # SCATTERED
            # Prefer atomic, simple tasks
            if task.requires_focus:
                score = 0.1
                reason = "Scattered attention incompatible with focus-requiring tasks"
            elif task.task_type in ['documentation', 'review', 'bug_fix']:
                score = 1.0
                reason = "Scattered attention perfect for atomic tasks"
            elif task.complexity < 0.3:
                score = 0.9
                reason = "Scattered attention works for simple tasks"
            else:
                score = 0.3
                reason = "Scattered attention struggles with complex tasks"

        return score, reason


class TimeTaskMatcher:
    """
    Matches available time to task duration.

    Prevents time blindness: Don't start 2-hour task with 15 minutes available.
    """

    @staticmethod
    def calculate_time_match(time_available_min: Optional[int], task_duration_min: int) -> Tuple[float, str]:
        """
        Calculate time-duration alignment score.

        Returns:
            (score, reason) where score is 0.0-1.0

        Rules:
        - Task fits in available time: 1.0
        - Task 80% of time: 0.8 (some buffer)
        - Task exceeds time: scaled down
        """
        if time_available_min is None:
            # Unknown time available - no penalty
            return 0.8, "Time available unknown, assuming sufficient"

        if task_duration_min <= time_available_min:
            # Task fits
            buffer = time_available_min - task_duration_min
            if buffer >= 10:
                score = 1.0
                reason = f"Task fits comfortably ({buffer}min buffer)"
            else:
                score = 0.9
                reason = f"Task fits with tight timing ({buffer}min buffer)"
        else:
            # Task exceeds time
            ratio = time_available_min / task_duration_min
            score = ratio * 0.5  # Penalty for exceeding
            overage = task_duration_min - time_available_min
            reason = f"Task exceeds time by {overage}min - consider shorter task"

        return score, reason


class TaskMatchingEngine:
    """
    Main matching engine combining energy, attention, and time factors.

    Weights:
    - Energy-complexity: 50%
    - Attention-task type: 30%
    - Time-duration: 20%
    """

    def __init__(self):
        self.energy_matcher = EnergyTaskMatcher()
        self.attention_matcher = AttentionTaskMatcher()
        self.time_matcher = TimeTaskMatcher()

        # Matching weights
        self.weights = {
            'energy': 0.50,
            'attention': 0.30,
            'time': 0.20
        }

    def calculate_match_score(
        self,
        cognitive_state: CognitiveState,
        task: Task
    ) -> TaskSuggestion:
        """
        Calculate overall task match score.

        Returns:
            TaskSuggestion with detailed match reasoning
        """
        # Get individual alignment scores
        energy_score, energy_reason = self.energy_matcher.calculate_energy_match(
            cognitive_state.energy,
            task.complexity
        )

        attention_score, attention_reason = self.attention_matcher.calculate_attention_match(
            cognitive_state.attention,
            task
        )

        time_score, time_reason = self.time_matcher.calculate_time_match(
            cognitive_state.time_until_break_min,
            task.estimated_minutes
        )

        # Weighted combination
        match_score = (
            energy_score * self.weights['energy'] +
            attention_score * self.weights['attention'] +
            time_score * self.weights['time']
        )

        # Build comprehensive match reason
        match_reason = f"{energy_reason}. {attention_reason}. {time_reason}"

        return TaskSuggestion(
            task=task,
            match_score=match_score,
            rank=0,  # Set by caller after sorting
            match_reason=match_reason,
            energy_alignment=energy_score,
            attention_alignment=attention_score,
            time_alignment=time_score
        )

    def suggest_tasks(
        self,
        cognitive_state: CognitiveState,
        available_tasks: List[Task],
        count: int = 3
    ) -> List[TaskSuggestion]:
        """
        Get top N task suggestions for current cognitive state.

        Args:
            cognitive_state: Current energy/attention/load
            available_tasks: TODO tasks to choose from
            count: Number of suggestions (default 3, ADHD-safe)

        Returns:
            Top N tasks ranked by match score
        """
        # Calculate match scores for all tasks
        suggestions = []
        for task in available_tasks:
            suggestion = self.calculate_match_score(cognitive_state, task)
            suggestions.append(suggestion)

        # Sort by match score (descending)
        suggestions.sort(key=lambda s: s.match_score, reverse=True)

        # Assign ranks and return top N
        for i, suggestion in enumerate(suggestions[:count], start=1):
            suggestion.rank = i

        logger.info(f"Task suggestions: {len(suggestions)} evaluated, returning top {count}")

        return suggestions[:count]

    def detect_task_mismatch(
        self,
        cognitive_state: CognitiveState,
        current_task: Task
    ) -> Optional[Dict]:
        """
        Detect if current task doesn't match cognitive state.

        Returns:
            None if good match, warning dict if mismatch detected
        """
        match = self.calculate_match_score(cognitive_state, current_task)

        if match.match_score < 0.4:
            # Poor match - warn user
            return {
                'is_mismatch': True,
                'severity': 'high',
                'current_task': current_task.title,
                'match_score': match.match_score,
                'recommendation': 'Consider switching to a better-matched task',
                'reason': match.match_reason
            }
        elif match.match_score < 0.6:
            # Suboptimal match
            return {
                'is_mismatch': True,
                'severity': 'medium',
                'current_task': current_task.title,
                'match_score': match.match_score,
                'recommendation': 'Task is workable but not ideal for current state',
                'reason': match.match_reason
            }
        else:
            # Good match
            return None
