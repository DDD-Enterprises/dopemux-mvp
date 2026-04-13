"""
Serena v2 Phase 2B: Context Switching Optimizer

ADHD-optimized context switching management with intelligent interruption handling,
task continuation support, and attention preservation strategies.
"""

import asyncio
import json
import logging
import statistics
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set, Union
from dataclasses import dataclass, field
from enum import Enum

from .database import SerenaIntelligenceDatabase
from .adaptive_learning import NavigationSequence, NavigationAction, AttentionState
from .learning_profile_manager import PersonalLearningProfileManager
from .effectiveness_tracker import EffectivenessTracker
from ..performance_monitor import PerformanceMonitor

logger = logging.getLogger(__name__)


class ContextSwitchType(str, Enum):
    """Types of context switches for ADHD analysis."""
    VOLUNTARY = "voluntary"           # User-initiated switch
    INVOLUNTARY = "involuntary"      # External interruption
    ATTENTION_DRIVEN = "attention_driven"  # ADHD attention shift
    TASK_COMPLETION = "task_completion"    # Natural task boundary
    COMPLEXITY_ESCAPE = "complexity_escape"  # Switching due to overwhelm
    EXPLORATION = "exploration"       # Exploratory switching
    ERROR_RECOVERY = "error_recovery" # Switching due to errors


class SwitchSeverity(str, Enum):
    """Severity of context switch impact."""
    MINIMAL = "minimal"               # Easy to resume
    MODERATE = "moderate"             # Some effort to resume
    HIGH = "high"                     # Significant effort to resume
    SEVERE = "severe"                 # Very difficult to resume


class InterruptionType(str, Enum):
    """Types of interruptions that cause context switches."""
    NOTIFICATION = "notification"     # System/app notifications
    HUMAN = "human"                   # Person interrupting
    ENVIRONMENTAL = "environmental"   # External environment
    INTERNAL = "internal"             # ADHD internal distraction
    SYSTEM = "system"                 # System-related interruption
    PLANNED = "planned"               # Scheduled interruption


@dataclass
class ContextSwitchEvent:
    """Individual context switch event with ADHD analysis."""
    switch_id: str
    user_session_id: str
    timestamp: datetime
    switch_type: ContextSwitchType
    severity: SwitchSeverity
    interruption_type: Optional[InterruptionType] = None

    # Context information
    from_context: Dict[str, Any] = field(default_factory=dict)
    to_context: Dict[str, Any] = field(default_factory=dict)
    complexity_delta: float = 0.0  # Change in complexity level

    # ADHD-specific data
    attention_state_before: Optional[AttentionState] = None
    attention_state_after: Optional[AttentionState] = None
    cognitive_load_increase: float = 0.0
    resumption_difficulty: float = 0.0  # 0.0 = easy, 1.0 = very difficult

    # Timing data
    switch_duration_ms: float = 0.0
    resumption_time_ms: float = 0.0
    total_overhead_ms: float = 0.0

    # Effectiveness impact
    productivity_impact: float = 0.0  # -1.0 = very negative, 1.0 = very positive
    user_frustration: Optional[float] = None  # 0.0 = none, 1.0 = maximum


@dataclass
class SwitchingPattern:
    """Pattern of context switching behavior."""
    pattern_id: str
    user_session_id: str
    pattern_type: str  # frequent_switcher, focused_worker, etc.
    switch_frequency: float  # switches per hour
    average_switch_cost: float  # average overhead in seconds
    most_common_switch_type: ContextSwitchType
    problematic_switches: List[ContextSwitchType]
    optimal_switches: List[ContextSwitchType]

    # ADHD characteristics
    attention_span_variance: float  # How much attention span varies
    complexity_tolerance_variance: float
    interruption_sensitivity: float  # How much interruptions affect user
    recovery_efficiency: float  # How quickly user recovers from switches

    # Improvement metrics
    switch_reduction_potential: float  # 0.0 to 1.0
    suggested_strategies: List[str] = field(default_factory=list)


@dataclass
class TaskContinuationContext:
    """Context information for resuming tasks after switches."""
    task_id: str
    user_session_id: str
    paused_at: datetime
    context_snapshot: Dict[str, Any]
    attention_state: AttentionState
    complexity_level: float
    progress_indicators: List[str]
    breadcrumb_trail: List[str]  # Navigation breadcrumbs
    resumption_hints: List[str]
    estimated_resumption_time: float


class ContextSwitchingOptimizer:
    """
    Context switching optimizer for ADHD-friendly navigation.

    Features:
    - Real-time context switch detection and analysis
    - ADHD-specific cognitive load assessment for switches
    - Intelligent interruption handling and management
    - Task continuation support with context preservation
    - Attention span preservation strategies
    - Context switch pattern learning and optimization
    - Proactive switch prevention and guidance
    - Recovery time minimization techniques
    """

    def __init__(
        self,
        database: SerenaIntelligenceDatabase,
        profile_manager: PersonalLearningProfileManager,
        effectiveness_tracker: EffectivenessTracker,
        performance_monitor: PerformanceMonitor = None
    ):
        self.database = database
        self.profile_manager = profile_manager
        self.effectiveness_tracker = effectiveness_tracker
        self.performance_monitor = performance_monitor or PerformanceMonitor()

        # Switch detection configuration
        self.switch_detection_threshold_seconds = 10  # Minimum time between contexts
        self.complexity_change_threshold = 0.3  # Significant complexity change
        self.attention_preservation_window_minutes = 5  # Time to preserve attention context

        # Active tracking
        self._active_contexts: Dict[str, Dict[str, Any]] = {}
        self._recent_switches: Dict[str, List[ContextSwitchEvent]] = {}
        self._continuation_contexts: Dict[str, TaskContinuationContext] = {}

        # Pattern analysis
        self._switching_patterns: Dict[str, SwitchingPattern] = {}

        # ADHD-specific thresholds
        self.adhd_switch_limits = {
            AttentionState.PEAK_FOCUS: 2,      # Very few switches during peak focus
            AttentionState.MODERATE_FOCUS: 4,  # Moderate switches okay
            AttentionState.LOW_FOCUS: 6,       # More switches expected
            AttentionState.HYPERFOCUS: 1,      # Almost no switches during hyperfocus
            AttentionState.FATIGUE: 8          # Many switches when fatigued
        }

    # Core Context Switch Detection

    async def detect_context_switch(
        self,
        user_session_id: str,
        current_context: Dict[str, Any],
        previous_context: Optional[Dict[str, Any]] = None
    ) -> Optional[ContextSwitchEvent]:
        """Detect and analyze context switch events."""
        operation_id = self.performance_monitor.start_operation("detect_context_switch")

        try:
            if not previous_context:
                # No previous context - this is a session start
                await self._record_context_start(user_session_id, current_context)
                self.performance_monitor.end_operation(operation_id, success=True)
                return None

            # Analyze context change
            switch_detected = await self._analyze_context_change(
                previous_context, current_context
            )

            if not switch_detected:
                self.performance_monitor.end_operation(operation_id, success=True, cache_hit=True)
                return None

            # Create context switch event
            switch_event = await self._create_switch_event(
                user_session_id, previous_context, current_context
            )

            # Analyze ADHD impact
            await self._analyze_adhd_impact(switch_event, user_session_id)

            # Store and track the switch
            await self._track_context_switch(switch_event)

            # Check for pattern violations
            await self._check_switching_patterns(switch_event)

            self.performance_monitor.end_operation(operation_id, success=True)

            logger.debug(f"🔄 Context switch detected: {switch_event.switch_type.value} "
                        f"(severity: {switch_event.severity.value})")

            return switch_event

        except Exception as e:
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"Failed to detect context switch: {e}")
            return None

    async def handle_interruption(
        self,
        user_session_id: str,
        interruption_type: InterruptionType,
        current_context: Dict[str, Any],
        interruption_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle interruption with ADHD-optimized strategies."""
        operation_id = self.performance_monitor.start_operation("handle_interruption")

        try:
            # Get user profile for personalized handling
            profile = await self.profile_manager.get_or_create_profile(
                user_session_id, current_context.get('workspace_path', 'default')
            )

            # Create task continuation context
            continuation_context = await self._create_continuation_context(
                user_session_id, current_context
            )

            # Determine interruption handling strategy
            handling_strategy = await self._determine_interruption_strategy(
                interruption_type, profile, current_context
            )

            # Apply ADHD-specific handling
            response = await self._apply_interruption_handling(
                handling_strategy, continuation_context, interruption_data
            )

            # Store continuation context for later resumption
            if continuation_context:
                self._continuation_contexts[continuation_context.task_id] = continuation_context

            self.performance_monitor.end_operation(operation_id, success=True)

            logger.info(f"🚨 Handled interruption: {interruption_type.value} "
                       f"(strategy: {handling_strategy['type']})")

            return response

        except Exception as e:
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"Failed to handle interruption: {e}")
            return {"status": "error", "message": str(e)}

    async def suggest_task_resumption(
        self,
        user_session_id: str,
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Suggest how to resume tasks after context switches."""
        operation_id = self.performance_monitor.start_operation("suggest_task_resumption")

        try:
            # Find relevant continuation contexts
            if task_id and task_id in self._continuation_contexts:
                contexts = [self._continuation_contexts[task_id]]
            else:
                # Find recent continuation contexts for user
                contexts = [
                    ctx for ctx in self._continuation_contexts.values()
                    if ctx.user_session_id == user_session_id and
                    (datetime.now(timezone.utc) - ctx.paused_at).seconds < 3600  # Within 1 hour
                ]

            if not contexts:
                self.performance_monitor.end_operation(operation_id, success=True)
                return {
                    "resumption_suggestions": [],
                    "message": "No recent tasks to resume"
                }

            # Generate resumption suggestions
            suggestions = []
            for context in contexts:
                suggestion = await self._generate_resumption_suggestion(context)
                suggestions.append(suggestion)

            # Sort by estimated ease of resumption
            suggestions.sort(key=lambda s: s['resumption_difficulty'])

            self.performance_monitor.end_operation(operation_id, success=True)

            return {
                "resumption_suggestions": suggestions[:3],  # Top 3 suggestions
                "total_paused_tasks": len(contexts)
            }

        except Exception as e:
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"Failed to suggest task resumption: {e}")
            return {"resumption_suggestions": [], "error": str(e)}

    # Context Switch Analysis

    async def _analyze_context_change(
        self, previous_context: Dict[str, Any], current_context: Dict[str, Any]
    ) -> bool:
        """Analyze if a significant context change occurred."""
        changes = []

        # File/element change
        if previous_context.get('file_path') != current_context.get('file_path'):
            changes.append('file_change')

        if previous_context.get('element_id') != current_context.get('element_id'):
            changes.append('element_change')

        # Complexity change
        prev_complexity = previous_context.get('complexity_score', 0.0)
        curr_complexity = current_context.get('complexity_score', 0.0)
        if abs(prev_complexity - curr_complexity) > self.complexity_change_threshold:
            changes.append('complexity_change')

        # Activity type change
        if previous_context.get('activity_type') != current_context.get('activity_type'):
            changes.append('activity_change')

        # Time gap
        prev_time = previous_context.get('timestamp')
        curr_time = current_context.get('timestamp')
        if prev_time and curr_time:
            time_gap = (curr_time - prev_time).total_seconds()
            if time_gap > self.switch_detection_threshold_seconds:
                changes.append('time_gap')

        # Significant change if multiple factors changed
        return len(changes) >= 2 or 'activity_change' in changes

    async def _create_switch_event(
        self,
        user_session_id: str,
        previous_context: Dict[str, Any],
        current_context: Dict[str, Any]
    ) -> ContextSwitchEvent:
        """Create context switch event with analysis."""
        switch_id = f"switch_{user_session_id}_{int(time.time() * 1000)}"

        # Determine switch type
        switch_type = await self._classify_switch_type(previous_context, current_context)

        # Calculate complexity delta
        prev_complexity = previous_context.get('complexity_score', 0.0)
        curr_complexity = current_context.get('complexity_score', 0.0)
        complexity_delta = curr_complexity - prev_complexity

        # Estimate severity
        severity = self._estimate_switch_severity(previous_context, current_context, complexity_delta)

        # Calculate timing
        prev_time = previous_context.get('timestamp', datetime.now(timezone.utc))
        curr_time = current_context.get('timestamp', datetime.now(timezone.utc))
        switch_duration = (curr_time - prev_time).total_seconds() * 1000

        return ContextSwitchEvent(
            switch_id=switch_id,
            user_session_id=user_session_id,
            timestamp=curr_time,
            switch_type=switch_type,
            severity=severity,
            from_context=previous_context,
            to_context=current_context,
            complexity_delta=complexity_delta,
            switch_duration_ms=switch_duration,
            total_overhead_ms=switch_duration  # Will be refined with more data
        )

    async def _classify_switch_type(
        self, previous_context: Dict[str, Any], current_context: Dict[str, Any]
    ) -> ContextSwitchType:
        """Classify the type of context switch."""
        # Check for completion-based switch
        if previous_context.get('completion_status') == 'completed':
            return ContextSwitchType.TASK_COMPLETION

        # Check for complexity escape (switching to simpler task)
        prev_complexity = previous_context.get('complexity_score', 0.0)
        curr_complexity = current_context.get('complexity_score', 0.0)
        if prev_complexity > 0.7 and curr_complexity < prev_complexity - 0.3:
            return ContextSwitchType.COMPLEXITY_ESCAPE

        # Check for error-driven switch
        if previous_context.get('error_encountered', False):
            return ContextSwitchType.ERROR_RECOVERY

        # Check for exploration
        if (current_context.get('activity_type') == 'exploration' or
            current_context.get('file_path') != previous_context.get('file_path')):
            return ContextSwitchType.EXPLORATION

        # Check time gap for involuntary switch
        prev_time = previous_context.get('timestamp', datetime.now(timezone.utc))
        curr_time = current_context.get('timestamp', datetime.now(timezone.utc))
        time_gap = (curr_time - prev_time).total_seconds()

        if time_gap > 300:  # 5 minutes gap suggests interruption
            return ContextSwitchType.INVOLUNTARY

        # Default to voluntary
        return ContextSwitchType.VOLUNTARY

    def _estimate_switch_severity(
        self,
        previous_context: Dict[str, Any],
        current_context: Dict[str, Any],
        complexity_delta: float
    ) -> SwitchSeverity:
        """Estimate the severity of context switch impact."""
        severity_factors = []

        # Complexity change factor
        if abs(complexity_delta) > 0.5:
            severity_factors.append(0.8)
        elif abs(complexity_delta) > 0.3:
            severity_factors.append(0.5)
        else:
            severity_factors.append(0.2)

        # Activity type change factor
        if previous_context.get('activity_type') != current_context.get('activity_type'):
            severity_factors.append(0.6)
        else:
            severity_factors.append(0.3)

        # File/scope change factor
        if previous_context.get('file_path') != current_context.get('file_path'):
            severity_factors.append(0.7)
        else:
            severity_factors.append(0.2)

        # Working memory factor (based on context depth)
        prev_depth = len(previous_context.get('breadcrumb_trail', []))
        if prev_depth > 5:  # Deep context is harder to resume
            severity_factors.append(0.8)
        elif prev_depth > 2:
            severity_factors.append(0.4)
        else:
            severity_factors.append(0.1)

        overall_severity = statistics.mean(severity_factors)

        if overall_severity > 0.7:
            return SwitchSeverity.SEVERE
        elif overall_severity > 0.5:
            return SwitchSeverity.HIGH
        elif overall_severity > 0.3:
            return SwitchSeverity.MODERATE
        else:
            return SwitchSeverity.MINIMAL

    async def _analyze_adhd_impact(self, switch_event: ContextSwitchEvent, user_session_id: str) -> None:
        """Analyze ADHD-specific impact of context switch."""
        try:
            # Get user profile for personalized analysis
            profile = await self.profile_manager.get_or_create_profile(
                user_session_id, switch_event.to_context.get('workspace_path', 'default')
            )

            # Estimate cognitive load increase
            base_load = 0.2  # Base switching cost
            complexity_load = abs(switch_event.complexity_delta) * 0.3
            severity_load = {
                SwitchSeverity.MINIMAL: 0.1,
                SwitchSeverity.MODERATE: 0.3,
                SwitchSeverity.HIGH: 0.6,
                SwitchSeverity.SEVERE: 0.9
            }.get(switch_event.severity, 0.3)

            switch_event.cognitive_load_increase = min(1.0, base_load + complexity_load + severity_load)

            # Estimate resumption difficulty based on ADHD characteristics
            user_switch_tolerance = profile.context_switch_tolerance
            difficulty_factors = [
                switch_event.cognitive_load_increase,
                min(1.0, switch_event.switch_duration_ms / 30000),  # Longer gaps = harder to resume
                1.0 - (user_switch_tolerance / 10.0)  # Lower tolerance = higher difficulty
            ]

            switch_event.resumption_difficulty = statistics.mean(difficulty_factors)

            # Estimate productivity impact
            if switch_event.switch_type == ContextSwitchType.COMPLEXITY_ESCAPE:
                switch_event.productivity_impact = 0.2  # Positive - needed break
            elif switch_event.switch_type == ContextSwitchType.TASK_COMPLETION:
                switch_event.productivity_impact = 0.5  # Positive - natural completion
            elif switch_event.severity == SwitchSeverity.SEVERE:
                switch_event.productivity_impact = -0.8  # Very negative
            else:
                switch_event.productivity_impact = -switch_event.cognitive_load_increase

        except Exception as e:
            logger.error(f"Failed to analyze ADHD impact: {e}")

    # Interruption Handling

    async def _determine_interruption_strategy(
        self,
        interruption_type: InterruptionType,
        profile,
        current_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Determine best strategy for handling interruption."""
        # Get current attention state
        current_attention = current_context.get('attention_state', AttentionState.MODERATE_FOCUS)

        # Base strategy based on interruption type and attention state
        if interruption_type == InterruptionType.NOTIFICATION:
            if current_attention in [AttentionState.PEAK_FOCUS, AttentionState.HYPERFOCUS]:
                strategy = {
                    "type": "defer",
                    "action": "Queue notification for later review",
                    "preserve_context": True,
                    "estimated_delay_minutes": 15
                }
            else:
                strategy = {
                    "type": "quick_handle",
                    "action": "Handle quickly if low cognitive load",
                    "preserve_context": True,
                    "max_handling_time_minutes": 2
                }

        elif interruption_type == InterruptionType.HUMAN:
            strategy = {
                "type": "graceful_transition",
                "action": "Save context and handle human interaction",
                "preserve_context": True,
                "context_notes": "Human interruption - preserve navigation state"
            }

        elif interruption_type == InterruptionType.INTERNAL:
            if current_attention == AttentionState.LOW_FOCUS:
                strategy = {
                    "type": "allow_with_guidance",
                    "action": "Allow switch but provide return guidance",
                    "preserve_context": True,
                    "guidance": "Natural attention shift - preserved context for easy return"
                }
            else:
                strategy = {
                    "type": "gentle_redirect",
                    "action": "Gently encourage focus maintenance",
                    "preserve_context": True,
                    "encouragement": "You're in good focus - try to maintain current task"
                }

        else:  # SYSTEM, ENVIRONMENTAL, PLANNED
            strategy = {
                "type": "context_preserve",
                "action": "Preserve full context for seamless resumption",
                "preserve_context": True,
                "full_snapshot": True
            }

        # Personalize based on user profile
        if profile.average_attention_span_minutes < 15:  # Short attention span
            strategy["additional_support"] = "Extra context preservation for short attention span"
            strategy["resumption_reminders"] = True

        return strategy

    async def _apply_interruption_handling(
        self,
        strategy: Dict[str, Any],
        continuation_context: Optional[TaskContinuationContext],
        interruption_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Apply the interruption handling strategy."""
        response = {
            "strategy_applied": strategy["type"],
            "action_taken": strategy["action"],
            "context_preserved": strategy.get("preserve_context", False)
        }

        if strategy["type"] == "defer":
            response["message"] = "💡 Interruption deferred to preserve your focus"
            response["deferred_until"] = datetime.now(timezone.utc) + timedelta(
                minutes=strategy.get("estimated_delay_minutes", 15)
            )

        elif strategy["type"] == "quick_handle":
            response["message"] = "⚡ Quick handling - context preserved"
            response["max_time_minutes"] = strategy.get("max_handling_time_minutes", 2)

        elif strategy["type"] == "graceful_transition":
            response["message"] = "🤝 Graceful transition - your work is safely saved"
            response["continuation_available"] = continuation_context is not None

        elif strategy["type"] == "allow_with_guidance":
            response["message"] = strategy.get("guidance", "Switch allowed with guidance")
            response["return_guidance"] = "Context preserved for easy return"

        elif strategy["type"] == "gentle_redirect":
            response["message"] = strategy.get("encouragement", "Gentle focus encouragement")
            response["focus_preservation"] = True

        else:  # context_preserve
            response["message"] = "📋 Full context preserved for seamless resumption"
            response["full_snapshot"] = strategy.get("full_snapshot", False)

        # Add ADHD-specific support
        if strategy.get("additional_support"):
            response["adhd_support"] = strategy["additional_support"]

        if strategy.get("resumption_reminders"):
            response["resumption_reminders"] = True

        return response

    async def _create_continuation_context(
        self, user_session_id: str, current_context: Dict[str, Any]
    ) -> TaskContinuationContext:
        """Create context for task continuation after interruption."""
        task_id = f"task_{user_session_id}_{int(time.time())}"

        # Generate context snapshot
        context_snapshot = {
            "file_path": current_context.get('file_path'),
            "element_id": current_context.get('element_id'),
            "activity_type": current_context.get('activity_type'),
            "complexity_score": current_context.get('complexity_score', 0.0),
            "navigation_history": current_context.get('navigation_history', []),
            "search_terms": current_context.get('recent_searches', []),
            "working_memory": current_context.get('working_memory', [])
        }

        # Generate breadcrumb trail
        breadcrumbs = []
        if current_context.get('file_path'):
            breadcrumbs.append(f"📁 {Path(current_context['file_path']).name}")
        if current_context.get('element_name'):
            breadcrumbs.append(f"🎯 {current_context['element_name']}")
        if current_context.get('activity_type'):
            breadcrumbs.append(f"⚡ {current_context['activity_type']}")

        # Generate resumption hints
        hints = []
        if current_context.get('activity_type') == 'debugging':
            hints.append("🐛 You were debugging - check recent error traces")
        elif current_context.get('activity_type') == 'implementation':
            hints.append("⚒️ You were implementing - review recent code changes")
        elif current_context.get('activity_type') == 'exploration':
            hints.append("🔍 You were exploring - continue from where you left off")

        complexity = current_context.get('complexity_score', 0.0)
        if complexity > 0.7:
            hints.append("🧠 Complex area - take time to rebuild mental model")
        elif complexity < 0.3:
            hints.append("✅ Simple area - should be easy to resume")

        # Estimate resumption time based on complexity and interruption
        base_time = 30  # 30 seconds base resumption time
        complexity_time = complexity * 60  # Up to 1 minute for complex areas
        context_depth_time = len(breadcrumbs) * 15  # 15 seconds per breadcrumb level

        estimated_resumption_time = base_time + complexity_time + context_depth_time

        return TaskContinuationContext(
            task_id=task_id,
            user_session_id=user_session_id,
            paused_at=datetime.now(timezone.utc),
            context_snapshot=context_snapshot,
            attention_state=current_context.get('attention_state', AttentionState.MODERATE_FOCUS),
            complexity_level=complexity,
            progress_indicators=current_context.get('progress_indicators', []),
            breadcrumb_trail=breadcrumbs,
            resumption_hints=hints,
            estimated_resumption_time=estimated_resumption_time
        )

    async def _generate_resumption_suggestion(
        self, context: TaskContinuationContext
    ) -> Dict[str, Any]:
        """Generate suggestion for resuming a paused task."""
        time_since_pause = (datetime.now(timezone.utc) - context.paused_at).total_seconds() / 60

        suggestion = {
            "task_id": context.task_id,
            "paused_at": context.paused_at.isoformat(),
            "time_since_pause_minutes": round(time_since_pause, 1),
            "resumption_difficulty": context.estimated_resumption_time / 120.0,  # Normalize to 0-1
            "breadcrumbs": context.breadcrumb_trail,
            "hints": context.resumption_hints,
            "estimated_resumption_time_seconds": context.estimated_resumption_time
        }

        # Adjust recommendation based on time elapsed
        if time_since_pause < 5:  # Very recent
            suggestion["recommendation"] = "🚀 Easy to resume - context still fresh"
            suggestion["priority"] = "high"
        elif time_since_pause < 30:  # Recent
            suggestion["recommendation"] = "✅ Good time to resume - context retrievable"
            suggestion["priority"] = "medium"
        elif time_since_pause < 120:  # Moderate delay
            suggestion["recommendation"] = "📋 May need context review - but still resumable"
            suggestion["priority"] = "medium"
        else:  # Long delay
            suggestion["recommendation"] = "🔄 Significant context rebuilding needed"
            suggestion["priority"] = "low"

        # Add complexity-based guidance
        if context.complexity_level > 0.7:
            suggestion["complexity_guidance"] = "High complexity - take time to rebuild understanding"
        elif context.complexity_level < 0.3:
            suggestion["complexity_guidance"] = "Low complexity - should resume easily"

        return suggestion

    # Pattern Analysis and Optimization

    async def analyze_switching_patterns(
        self, user_session_id: str, time_period_days: int = 7
    ) -> SwitchingPattern:
        """Analyze user's context switching patterns for optimization."""
        operation_id = self.performance_monitor.start_operation("analyze_switching_patterns")

        try:
            # Query recent switches
            query = """
            SELECT * FROM context_switches
            WHERE user_session_id = $1
              AND timestamp > NOW() - INTERVAL '%s days'
            ORDER BY timestamp DESC
            """ % time_period_days

            results = await self.database.execute_query(query, (user_session_id,))

            if not results:
                # Return default pattern for new users
                return SwitchingPattern(
                    pattern_id=f"pattern_{user_session_id}",
                    user_session_id=user_session_id,
                    pattern_type="new_user",
                    switch_frequency=0.0,
                    average_switch_cost=30.0,  # Default 30 seconds
                    most_common_switch_type=ContextSwitchType.VOLUNTARY,
                    problematic_switches=[],
                    optimal_switches=[],
                    attention_span_variance=0.5,
                    complexity_tolerance_variance=0.3,
                    interruption_sensitivity=0.5,
                    recovery_efficiency=0.7,
                    switch_reduction_potential=0.3
                )

            # Analyze patterns
            switches = [self._parse_switch_from_row(row) for row in results]

            # Calculate metrics
            total_hours = time_period_days * 24
            switch_frequency = len(switches) / total_hours

            # Average switch cost
            switch_costs = [s.total_overhead_ms / 1000 for s in switches if s.total_overhead_ms > 0]
            average_switch_cost = statistics.mean(switch_costs) if switch_costs else 30.0

            # Most common switch type
            switch_types = [s.switch_type for s in switches]
            most_common_type = max(set(switch_types), key=switch_types.count) if switch_types else ContextSwitchType.VOLUNTARY

            # Identify problematic and optimal switches
            problematic_switches = [
                s.switch_type for s in switches
                if s.severity in [SwitchSeverity.HIGH, SwitchSeverity.SEVERE] or s.productivity_impact < -0.5
            ]

            optimal_switches = [
                s.switch_type for s in switches
                if s.severity == SwitchSeverity.MINIMAL and s.productivity_impact > 0
            ]

            # ADHD characteristics
            attention_spans = [s.switch_duration_ms / 1000 / 60 for s in switches]  # Convert to minutes
            attention_span_variance = statistics.variance(attention_spans) if len(attention_spans) > 1 else 0.5

            complexity_deltas = [abs(s.complexity_delta) for s in switches]
            complexity_tolerance_variance = statistics.variance(complexity_deltas) if len(complexity_deltas) > 1 else 0.3

            # Interruption sensitivity
            involuntary_switches = len([s for s in switches if s.switch_type == ContextSwitchType.INVOLUNTARY])
            interruption_sensitivity = min(1.0, involuntary_switches / max(len(switches), 1))

            # Recovery efficiency
            resumption_difficulties = [s.resumption_difficulty for s in switches if s.resumption_difficulty > 0]
            recovery_efficiency = 1.0 - statistics.mean(resumption_difficulties) if resumption_difficulties else 0.7

            # Switch reduction potential
            unnecessary_switches = len([s for s in switches if s.switch_type in [ContextSwitchType.COMPLEXITY_ESCAPE, ContextSwitchType.INVOLUNTARY]])
            switch_reduction_potential = min(1.0, unnecessary_switches / max(len(switches), 1))

            # Generate improvement strategies
            strategies = self._generate_switching_strategies(
                switch_frequency, most_common_type, problematic_switches, switch_reduction_potential
            )

            pattern = SwitchingPattern(
                pattern_id=f"pattern_{user_session_id}_{int(time.time())}",
                user_session_id=user_session_id,
                pattern_type=self._classify_switching_pattern(switch_frequency, interruption_sensitivity),
                switch_frequency=switch_frequency,
                average_switch_cost=average_switch_cost,
                most_common_switch_type=most_common_type,
                problematic_switches=list(set(problematic_switches)),
                optimal_switches=list(set(optimal_switches)),
                attention_span_variance=attention_span_variance,
                complexity_tolerance_variance=complexity_tolerance_variance,
                interruption_sensitivity=interruption_sensitivity,
                recovery_efficiency=recovery_efficiency,
                switch_reduction_potential=switch_reduction_potential,
                suggested_strategies=strategies
            )

            self.performance_monitor.end_operation(operation_id, success=True)

            logger.info(f"📊 Analyzed switching pattern: {pattern.pattern_type} "
                       f"(frequency: {switch_frequency:.1f}/hour)")

            return pattern

        except Exception as e:
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"Failed to analyze switching patterns: {e}")
            raise

    def _classify_switching_pattern(
        self, switch_frequency: float, interruption_sensitivity: float
    ) -> str:
        """Classify user's switching pattern type."""
        if switch_frequency > 4.0:  # More than 4 switches per hour
            if interruption_sensitivity > 0.6:
                return "highly_distractible"
            else:
                return "frequent_switcher"
        elif switch_frequency > 2.0:  # 2-4 switches per hour
            if interruption_sensitivity > 0.5:
                return "moderately_distractible"
            else:
                return "balanced_switcher"
        elif switch_frequency > 0.5:  # 0.5-2 switches per hour
            return "focused_worker"
        else:  # Very low switching
            return "hyperfocused"

    def _generate_switching_strategies(
        self,
        switch_frequency: float,
        most_common_type: ContextSwitchType,
        problematic_switches: List[ContextSwitchType],
        reduction_potential: float
    ) -> List[str]:
        """Generate strategies for optimizing context switching."""
        strategies = []

        # Frequency-based strategies
        if switch_frequency > 3.0:
            strategies.append("🎯 Practice single-tasking - focus on one area for longer periods")
            strategies.append("📱 Minimize notifications during focus time")

        # Type-based strategies
        if most_common_type == ContextSwitchType.COMPLEXITY_ESCAPE:
            strategies.append("🧠 Use progressive complexity increase to build tolerance")
            strategies.append("💡 Take planned breaks before overwhelm occurs")

        if ContextSwitchType.INVOLUNTARY in problematic_switches:
            strategies.append("🛡️ Create interruption-free time blocks")
            strategies.append("📋 Use task continuation contexts for smooth resumption")

        # Reduction potential strategies
        if reduction_potential > 0.5:
            strategies.append("⚡ High improvement potential - focus on switch reduction")
            strategies.append("🔄 Practice task completion before switching")

        # General ADHD strategies
        strategies.append("⏰ Use attention span awareness to plan switches")
        strategies.append("🧭 Keep navigation breadcrumbs for easy context rebuilding")

        return strategies

    # Database Operations

    async def _track_context_switch(self, switch_event: ContextSwitchEvent) -> None:
        """Store context switch event in database."""
        try:
            insert_query = """
            INSERT INTO context_switches (
                switch_id, user_session_id, timestamp, switch_type, severity,
                interruption_type, from_context, to_context, complexity_delta,
                attention_state_before, attention_state_after, cognitive_load_increase,
                resumption_difficulty, switch_duration_ms, resumption_time_ms,
                total_overhead_ms, productivity_impact, user_frustration
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
            """

            await self.database.execute_query(insert_query, (
                switch_event.switch_id,
                switch_event.user_session_id,
                switch_event.timestamp,
                switch_event.switch_type.value,
                switch_event.severity.value,
                switch_event.interruption_type.value if switch_event.interruption_type else None,
                json.dumps(switch_event.from_context),
                json.dumps(switch_event.to_context),
                switch_event.complexity_delta,
                switch_event.attention_state_before.value if switch_event.attention_state_before else None,
                switch_event.attention_state_after.value if switch_event.attention_state_after else None,
                switch_event.cognitive_load_increase,
                switch_event.resumption_difficulty,
                switch_event.switch_duration_ms,
                switch_event.resumption_time_ms,
                switch_event.total_overhead_ms,
                switch_event.productivity_impact,
                switch_event.user_frustration
            ))

            # Add to recent switches cache
            if switch_event.user_session_id not in self._recent_switches:
                self._recent_switches[switch_event.user_session_id] = []

            self._recent_switches[switch_event.user_session_id].append(switch_event)

            # Keep only recent switches (last 20)
            self._recent_switches[switch_event.user_session_id] = \
                self._recent_switches[switch_event.user_session_id][-20:]

        except Exception as e:
            logger.error(f"Failed to track context switch: {e}")

    async def _check_switching_patterns(self, switch_event: ContextSwitchEvent) -> None:
        """Check if switch violates established patterns and provide guidance."""
        try:
            user_id = switch_event.user_session_id

            # Get recent switches for pattern analysis
            recent_switches = self._recent_switches.get(user_id, [])

            if len(recent_switches) < 3:
                return  # Not enough data for pattern analysis

            # Check switch frequency
            recent_hour_switches = [
                s for s in recent_switches
                if (datetime.now(timezone.utc) - s.timestamp).seconds < 3600
            ]

            if len(recent_hour_switches) > 5:  # Too many switches in one hour
                logger.warning(f"⚠️ High switch frequency detected for user {user_id}")
                # Could trigger intervention here

            # Check for complexity escape pattern
            complexity_escapes = [
                s for s in recent_switches[-5:]  # Last 5 switches
                if s.switch_type == ContextSwitchType.COMPLEXITY_ESCAPE
            ]

            if len(complexity_escapes) >= 3:
                logger.info(f"🧠 Complexity avoidance pattern detected for user {user_id}")
                # Could suggest complexity tolerance building

        except Exception as e:
            logger.error(f"Failed to check switching patterns: {e}")

    # Utility Methods

    def _parse_switch_from_row(self, row: Dict[str, Any]) -> ContextSwitchEvent:
        """Parse context switch event from database row."""
        return ContextSwitchEvent(
            switch_id=row['switch_id'],
            user_session_id=row['user_session_id'],
            timestamp=row['timestamp'],
            switch_type=ContextSwitchType(row['switch_type']),
            severity=SwitchSeverity(row['severity']),
            interruption_type=InterruptionType(row['interruption_type']) if row['interruption_type'] else None,
            from_context=json.loads(row['from_context']),
            to_context=json.loads(row['to_context']),
            complexity_delta=row['complexity_delta'],
            attention_state_before=AttentionState(row['attention_state_before']) if row['attention_state_before'] else None,
            attention_state_after=AttentionState(row['attention_state_after']) if row['attention_state_after'] else None,
            cognitive_load_increase=row['cognitive_load_increase'],
            resumption_difficulty=row['resumption_difficulty'],
            switch_duration_ms=row['switch_duration_ms'],
            resumption_time_ms=row['resumption_time_ms'],
            total_overhead_ms=row['total_overhead_ms'],
            productivity_impact=row['productivity_impact'],
            user_frustration=row['user_frustration']
        )

    async def _record_context_start(self, user_session_id: str, context: Dict[str, Any]) -> None:
        """Record the start of a new context/session."""
        self._active_contexts[user_session_id] = context
        logger.debug(f"🆕 New context started for user {user_session_id}")


# Convenience functions
async def create_context_switching_optimizer(
    database: SerenaIntelligenceDatabase,
    profile_manager: PersonalLearningProfileManager,
    effectiveness_tracker: EffectivenessTracker,
    performance_monitor: PerformanceMonitor = None
) -> ContextSwitchingOptimizer:
    """Create context switching optimizer instance."""
    return ContextSwitchingOptimizer(database, profile_manager, effectiveness_tracker, performance_monitor)


if __name__ == "__main__":
    # Quick test when run directly
    async def main():
        print("🔄 Serena Context Switching Optimizer")
        print("ADHD-optimized interruption handling and task continuation")
        print("✅ Module loaded successfully")

    asyncio.run(main())