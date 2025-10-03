"""
Data models for ADHD Accommodation Engine.

Extracted from task-orchestrator/adhd_engine.py as part of Path C migration.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class EnergyLevel(str, Enum):
    """Developer energy levels for task matching."""
    VERY_LOW = "very_low"      # Post-hyperfocus crash, need simple tasks
    LOW = "low"                # Limited capacity, easy wins only
    MEDIUM = "medium"          # Normal capacity, standard tasks
    HIGH = "high"              # Peak performance, complex tasks OK
    HYPERFOCUS = "hyperfocus"  # Intense concentration, single complex task


class AttentionState(str, Enum):
    """Current attention state tracking."""
    SCATTERED = "scattered"        # Difficulty focusing, need structure
    TRANSITIONING = "transitioning"# Moving between tasks/contexts
    FOCUSED = "focused"           # Good concentration, productive
    HYPERFOCUSED = "hyperfocused" # Intense focus, needs protection
    OVERWHELMED = "overwhelmed"   # Too much information, need reduction


class CognitiveLoadLevel(str, Enum):
    """Cognitive load assessment levels."""
    MINIMAL = "minimal"       # 0.0-0.2: Very easy, autopilot tasks
    LOW = "low"              # 0.2-0.4: Easy tasks, minimal thinking
    MODERATE = "moderate"    # 0.4-0.6: Standard tasks, normal effort
    HIGH = "high"            # 0.6-0.8: Complex tasks, focused attention
    EXTREME = "extreme"      # 0.8-1.0: Very complex, peak concentration


@dataclass
class ADHDProfile:
    """Developer ADHD profile for personalized accommodations."""
    user_id: str

    # Core ADHD characteristics
    hyperfocus_tendency: float = 0.7        # 0.0-1.0, higher = more likely to hyperfocus
    distraction_sensitivity: float = 0.6    # 0.0-1.0, higher = more easily distracted
    context_switch_penalty: float = 0.4     # 0.0-1.0, harder to switch contexts
    break_resistance: float = 0.3           # 0.0-1.0, higher = resists taking breaks

    # Energy patterns
    energy_pattern: str = "variable"        # stable, variable, cyclical
    peak_hours: List[int] = None           # Hours when energy is typically highest
    crash_indicators: List[str] = None      # Signs of energy crash

    # Focus preferences
    optimal_task_duration: int = 25         # Minutes of optimal focus time
    max_task_duration: int = 90            # Maximum before forced break
    preferred_complexity: str = "moderate"  # minimal, low, moderate, high
    focus_music_preference: bool = True     # Prefers background music/noise

    # Accommodation preferences
    visual_progress_bars: bool = True       # Wants visual progress feedback
    gentle_reminders: bool = True          # Prefers gentle vs sharp reminders
    celebration_feedback: bool = True       # Wants completion celebrations
    break_activity_suggestions: bool = True # Wants break activity ideas

    def __post_init__(self):
        if self.peak_hours is None:
            self.peak_hours = [9, 10, 14, 15]  # Default morning and afternoon peaks
        if self.crash_indicators is None:
            self.crash_indicators = ["excessive_scrolling", "task_switching", "procrastination"]


@dataclass
class AccommodationRecommendation:
    """Recommendation for ADHD accommodation."""
    accommodation_type: str
    urgency: str  # immediate, soon, when_convenient
    message: str
    action_required: bool
    suggested_actions: List[str]
    cognitive_benefit: str
    implementation_effort: str  # minimal, low, moderate, high
