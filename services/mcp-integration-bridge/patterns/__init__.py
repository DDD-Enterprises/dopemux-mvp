"""
Pattern Detection Classes for Integration Bridge
Each pattern detector analyzes events and generates insights
"""

from .base_pattern import BasePattern, PatternInsight
from .high_complexity_cluster import HighComplexityClusterPattern
from .repeated_errors import RepeatedErrorPattern
from .knowledge_gaps import KnowledgeGapPattern
from .decision_churn import DecisionChurnPattern
from .adhd_state_patterns import ADHDStatePattern
from .context_switch_frequency import ContextSwitchFrequencyPattern
from .task_abandonment import TaskAbandonmentPattern

__all__ = [
    "BasePattern",
    "PatternInsight",
    "HighComplexityClusterPattern",
    "RepeatedErrorPattern",
    "KnowledgeGapPattern",
    "DecisionChurnPattern",
    "ADHDStatePattern",
    "ContextSwitchFrequencyPattern",
    "TaskAbandonmentPattern",
]
