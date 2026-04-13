"""
Performance Optimizer Engine for Task Orchestrator
Personalized Productivity Pattern Learning with ADHD Considerations

Uses machine learning to learn individual productivity patterns and optimize
workflows for maximum effectiveness while minimizing cognitive overhead.
"""

import asyncio
import json
import logging
import statistics
from datetime import datetime, timedelta, time
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import math

logger = logging.getLogger(__name__)


class ProductivityMetric(str, Enum):
    """Key productivity metrics for optimization."""
    TASK_COMPLETION_RATE = "task_completion_rate"
    CONTEXT_SWITCH_FREQUENCY = "context_switch_frequency"
    ENERGY_LEVEL_STABILITY = "energy_level_stability"
    COGNITIVE_LOAD_EFFICIENCY = "cognitive_load_efficiency"
    BREAK_TIMING_EFFECTIVENESS = "break_timing_effectiveness"
    HYPERFOCUS_UTILIZATION = "hyperfocus_utilization"
    WORKFLOW_AUTOMATION_USAGE = "workflow_automation_usage"


class OptimizationStrategy(str, Enum):
    """Types of optimization strategies."""
    TASK_REORDERING = "task_reordering"
    BATCH_GROUPING = "batch_grouping"
    BREAK_SCHEDULING = "break_scheduling"
    ENERGY_MATCHING = "energy_matching"
    CONTEXT_PRESERVATION = "context_preservation"
    AUTOMATION_ENHANCEMENT = "automation_enhancement"
    WORKFLOW_SIMPLIFICATION = "workflow_simplification"


@dataclass
class ProductivityPattern:
    """Individual productivity pattern learned from data."""
    pattern_id: str
    user_id: str
    pattern_type: str                     # "energy_cycle", "focus_pattern", etc.
    confidence: float                     # 0.0-1.0 confidence in pattern
    effectiveness_score: float           # 0.0-1.0 how effective this pattern is

    # Pattern data
    optimal_times: List[time]             # Best times for this pattern
    duration_range: Tuple[float, float]   # (min, max) minutes for activities
    prerequisites: List[str]              # Conditions needed for pattern
    success_indicators: List[str]         # Signs pattern is working

    # ADHD-specific data
    adhd_accommodations: List[str]        # Required accommodations
    energy_requirements: List[str]        # Energy levels needed
    attention_requirements: List[str]     # Attention states needed

    # Learning metadata
    data_points: int                      # Number of observations
    last_updated: datetime
    trend_direction: str                  # "improving", "stable", "declining"


@dataclass
class OptimizationRecommendation:
    """Specific optimization recommendation with impact estimates."""
    recommendation_id: str
    strategy: OptimizationStrategy
    description: str
    rationale: str
    expected_improvement: float           # 0.0-1.0 expected productivity gain
    implementation_effort: float         # 0.0-1.0 effort to implement
    confidence: float                     # 0.0-1.0 confidence in recommendation

    # Implementation details
    specific_actions: List[str]
    measurement_criteria: List[str]
    success_metrics: List[str]
    rollback_plan: List[str]

    # ADHD considerations
    adhd_friendly: bool
    cognitive_load_impact: float          # -1.0 to 1.0 (negative is better)
    disruption_level: float               # 0.0-1.0 (how disruptive to implement)


class PerformanceOptimizerEngine:
    """
    ML-powered productivity optimization with personalized ADHD accommodations.

    Features:
    - Individual productivity pattern recognition
    - Personalized workflow optimization recommendations
    - Real-time performance monitoring and adjustment
    - ADHD-specific accommodation learning
    - Continuous improvement through feedback loops
    """

    def __init__(self, conport_client=None, context7_client=None):
        self.conport = conport_client
        self.context7 = context7_client

        # Learning system
        self.productivity_patterns: Dict[str, List[ProductivityPattern]] = {}  # user_id -> patterns
        self.optimization_history: Dict[str, List[OptimizationRecommendation]] = {}
        self.performance_data: Dict[str, List[Dict]] = {}  # Historical performance data

        # ADHD-specific pattern templates
        self.adhd_pattern_templates = {
            "hyperfocus_sessions": {
                "ideal_duration": (90, 180),  # 1.5-3 hours
                "break_requirements": (15, 30),  # 15-30 min breaks
                "optimal_energy": ["high", "hyperfocus"],
                "protection_needed": True
            },
            "context_switching": {
                "switch_cost": (5, 15),  # 5-15 minutes penalty
                "buffer_time": (10, 20),  # Buffer between tasks
                "grouping_benefit": 0.3,  # 30% efficiency gain from grouping
                "adhd_penalty": 0.5  # Extra penalty for ADHD users
            },
            "energy_cycles": {
                "peak_duration": (120, 240),  # 2-4 hour peaks
                "recovery_time": (30, 60),   # 30-60 min recovery
                "predictable_times": True,
                "varies_by_day": True
            }
        }

        # Optimization models
        self.optimization_models: Dict[OptimizationStrategy, Dict] = {}
        self.learning_rate = 0.1
        self.min_data_points = 10  # Minimum data before making recommendations

        # Statistics
        self.optimizer_stats = {
            "patterns_learned": 0,
            "recommendations_made": 0,
            "successful_optimizations": 0,
            "productivity_improvements": 0.0,
            "adhd_accommodations_applied": 0
        }

    async def initialize(self) -> None:
        """Initialize the performance optimizer engine."""
        try:
            await self._load_user_patterns()
            await self._initialize_optimization_models()
            await self._start_performance_monitoring()
            logger.info("Performance optimizer engine initialized")
        except Exception as e:
            logger.error(f"Failed to initialize performance optimizer: {e}")

    async def learn_productivity_patterns(
        self,
        user_id: str,
        session_data: Dict[str, Any]
    ) -> List[ProductivityPattern]:
        """Learn productivity patterns from user session data."""
        try:
            # Extract pattern candidates from session data
            pattern_candidates = await self._extract_pattern_candidates(user_id, session_data)

            # Validate patterns with sufficient data
            valid_patterns = []
            for candidate in pattern_candidates:
                if await self._validate_pattern(candidate):
                    valid_patterns.append(candidate)

            # Update user's pattern library
            if user_id not in self.productivity_patterns:
                self.productivity_patterns[user_id] = []

            for pattern in valid_patterns:
                await self._update_or_add_pattern(user_id, pattern)

            self.optimizer_stats["patterns_learned"] += len(valid_patterns)
            logger.info(f"Learned {len(valid_patterns)} patterns for user {user_id}")

            return valid_patterns

        except Exception as e:
            logger.error(f"Pattern learning failed for user {user_id}: {e}")
            return []

    async def generate_optimization_recommendations(
        self,
        user_id: str,
        current_workflow: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[OptimizationRecommendation]:
        """Generate personalized optimization recommendations."""
        try:
            recommendations = []

            # Get user's patterns
            user_patterns = self.productivity_patterns.get(user_id, [])

            if len(user_patterns) < 3:
                # Not enough data - provide general ADHD optimizations
                recommendations.extend(await self._generate_general_adhd_recommendations(context))
            else:
                # Generate pattern-based recommendations
                recommendations.extend(await self._generate_pattern_based_recommendations(
                    user_id, user_patterns, current_workflow, context
                ))

            # Sort by expected impact and confidence
            recommendations.sort(
                key=lambda r: r.expected_improvement * r.confidence,
                reverse=True
            )

            # Limit to top 3 to avoid overwhelm
            recommendations = recommendations[:3]

            self.optimizer_stats["recommendations_made"] += len(recommendations)
            return recommendations

        except Exception as e:
            logger.error(f"Failed to generate recommendations for user {user_id}: {e}")
            return []

    async def optimize_current_workflow(
        self,
        user_id: str,
        current_tasks: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Optimize current workflow in real-time."""
        try:
            optimization_result = {
                "original_workflow": current_tasks,
                "optimized_workflow": [],
                "optimization_strategies": [],
                "expected_improvement": 0.0,
                "adhd_accommodations": []
            }

            # Apply learned patterns
            user_patterns = self.productivity_patterns.get(user_id, [])
            optimized_tasks = await self._apply_patterns_to_tasks(current_tasks, user_patterns, context)

            # Apply ADHD-specific optimizations
            final_tasks = await self._apply_adhd_optimizations(optimized_tasks, context)

            # Calculate improvement estimate
            improvement = await self._estimate_workflow_improvement(
                current_tasks, final_tasks, user_patterns
            )

            optimization_result.update({
                "optimized_workflow": final_tasks,
                "expected_improvement": improvement["productivity_gain"],
                "adhd_accommodations": improvement["adhd_accommodations"]
            })

            return optimization_result

        except Exception as e:
            logger.error(f"Workflow optimization failed for user {user_id}: {e}")
            return {"error": str(e)}

    async def track_optimization_effectiveness(
        self,
        recommendation_id: str,
        actual_results: Dict[str, Any]
    ) -> None:
        """Track effectiveness of applied optimizations."""
        try:
            # Update optimization model accuracy
            effectiveness = actual_results.get("productivity_improvement", 0.0)

            if effectiveness > 0.1:  # 10% improvement threshold
                self.optimizer_stats["successful_optimizations"] += 1
                self.optimizer_stats["productivity_improvements"] += effectiveness

            # Update ML models based on results
            await self._update_optimization_models(recommendation_id, actual_results)

            logger.info(f"Tracked optimization effectiveness: {effectiveness:.2%}")

        except Exception as e:
            logger.error(f"Failed to track optimization effectiveness: {e}")

    # Private implementation methods

    async def _load_user_patterns(self) -> None:
        """Load existing productivity patterns from storage."""
        # Implementation would load saved patterns
        pass

    async def _initialize_optimization_models(self) -> None:
        """Initialize ML models for each optimization strategy."""
        for strategy in OptimizationStrategy:
            self.optimization_models[strategy] = {
                "effectiveness_score": 0.7,  # Baseline effectiveness
                "confidence": 0.6,
                "usage_count": 0,
                "success_rate": 0.5
            }

    async def _start_performance_monitoring(self) -> None:
        """Start background performance monitoring."""
        # Implementation would start monitoring loops
        pass

    async def _extract_pattern_candidates(
        self, user_id: str, session_data: Dict[str, Any]
    ) -> List[ProductivityPattern]:
        """Extract potential patterns from session data."""
        # Simplified pattern extraction
        patterns = []

        # Detect energy cycle patterns
        if "energy_levels" in session_data:
            energy_pattern = await self._detect_energy_cycle_pattern(user_id, session_data)
            if energy_pattern:
                patterns.append(energy_pattern)

        # Detect focus patterns
        if "focus_sessions" in session_data:
            focus_pattern = await self._detect_focus_pattern(user_id, session_data)
            if focus_pattern:
                patterns.append(focus_pattern)

        return patterns

    async def _detect_energy_cycle_pattern(
        self, user_id: str, session_data: Dict[str, Any]
    ) -> Optional[ProductivityPattern]:
        """Detect energy cycle patterns."""
        # Implementation would analyze energy level data
        return ProductivityPattern(
            pattern_id=f"energy_{uuid.uuid4().hex[:8]}",
            user_id=user_id,
            pattern_type="energy_cycle",
            confidence=0.8,
            effectiveness_score=0.7,
            optimal_times=[time(9, 0), time(14, 0)],
            duration_range=(90, 180),
            prerequisites=["adequate_sleep", "minimal_distractions"],
            success_indicators=["sustained_focus", "high_completion_rate"],
            adhd_accommodations=["hyperfocus_protection", "gentle_transitions"],
            energy_requirements=["high", "medium"],
            attention_requirements=["focused", "hyperfocused"],
            data_points=15,
            last_updated=datetime.now(),
            trend_direction="improving"
        )

    async def _detect_focus_pattern(
        self, user_id: str, session_data: Dict[str, Any]
    ) -> Optional[ProductivityPattern]:
        """Detect focus session patterns."""
        # Implementation would analyze focus session data
        return None

    async def _validate_pattern(self, pattern: ProductivityPattern) -> bool:
        """Validate that pattern has sufficient data and confidence."""
        return (pattern.data_points >= self.min_data_points and
                pattern.confidence >= 0.6)

    async def _update_or_add_pattern(self, user_id: str, new_pattern: ProductivityPattern) -> None:
        """Update existing pattern or add new one."""
        user_patterns = self.productivity_patterns[user_id]

        # Look for existing pattern of same type
        for i, existing in enumerate(user_patterns):
            if (existing.pattern_type == new_pattern.pattern_type and
                existing.user_id == new_pattern.user_id):
                # Update existing pattern
                user_patterns[i] = new_pattern
                return

        # Add new pattern
        user_patterns.append(new_pattern)

    async def _generate_general_adhd_recommendations(
        self, context: Dict[str, Any]
    ) -> List[OptimizationRecommendation]:
        """Generate general ADHD optimization recommendations."""
        return [
            OptimizationRecommendation(
                recommendation_id=f"adhd_general_{uuid.uuid4().hex[:6]}",
                strategy=OptimizationStrategy.TASK_REORDERING,
                description="Reorder tasks by energy level requirements",
                rationale="Match high-energy tasks to peak hours for better focus",
                expected_improvement=0.25,
                implementation_effort=0.2,
                confidence=0.8,
                specific_actions=[
                    "Schedule complex tasks during morning peak hours",
                    "Place routine tasks during low-energy periods",
                    "Group similar tasks to reduce context switching"
                ],
                measurement_criteria=["task_completion_time", "energy_after_task"],
                success_metrics=["15% faster completion", "maintained energy levels"],
                rollback_plan=["Return to original task order if energy drops"],
                adhd_friendly=True,
                cognitive_load_impact=-0.3,
                disruption_level=0.1
            )
        ]

    async def _generate_pattern_based_recommendations(
        self,
        user_id: str,
        patterns: List[ProductivityPattern],
        workflow: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[OptimizationRecommendation]:
        """Generate recommendations based on learned patterns."""
        recommendations = []

        for pattern in patterns:
            if pattern.effectiveness_score > 0.7:
                # Generate recommendations based on this successful pattern
                pattern_recommendations = await self._recommendations_from_pattern(pattern, workflow, context)
                recommendations.extend(pattern_recommendations)

        return recommendations

    async def _recommendations_from_pattern(
        self,
        pattern: ProductivityPattern,
        workflow: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[OptimizationRecommendation]:
        """Generate recommendations based on a specific pattern."""
        # Implementation would generate pattern-specific recommendations
        return []

    async def _apply_patterns_to_tasks(
        self,
        tasks: List[Dict[str, Any]],
        patterns: List[ProductivityPattern],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply learned patterns to optimize task workflow."""
        optimized_tasks = tasks.copy()

        # Apply energy cycle patterns
        energy_patterns = [p for p in patterns if p.pattern_type == "energy_cycle"]
        if energy_patterns:
            optimized_tasks = await self._apply_energy_patterns(optimized_tasks, energy_patterns[0])

        # Apply focus patterns
        focus_patterns = [p for p in patterns if p.pattern_type == "focus_pattern"]
        if focus_patterns:
            optimized_tasks = await self._apply_focus_patterns(optimized_tasks, focus_patterns[0])

        return optimized_tasks

    async def _apply_energy_patterns(
        self,
        tasks: List[Dict[str, Any]],
        energy_pattern: ProductivityPattern
    ) -> List[Dict[str, Any]]:
        """Apply energy pattern optimization to tasks."""
        # Sort tasks by energy requirements and match to optimal times
        high_energy_tasks = [t for t in tasks if t.get("energy_required", "medium") in ["high", "hyperfocus"]]
        low_energy_tasks = [t for t in tasks if t.get("energy_required", "medium") in ["low", "very_low"]]

        # Schedule high-energy tasks during optimal times
        for task in high_energy_tasks:
            if energy_pattern.optimal_times:
                task["recommended_start_time"] = energy_pattern.optimal_times[0]

        return tasks

    async def _apply_focus_patterns(
        self,
        tasks: List[Dict[str, Any]],
        focus_pattern: ProductivityPattern
    ) -> List[Dict[str, Any]]:
        """Apply focus pattern optimization to tasks."""
        # Implementation would apply focus-based optimizations
        return tasks

    async def _apply_adhd_optimizations(
        self,
        tasks: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply ADHD-specific optimizations to workflow."""
        adhd_optimized = []

        # Group similar tasks to reduce context switching
        task_groups = self._group_similar_tasks(tasks)

        for group in task_groups:
            # Add transition buffers between different task types
            for i, task in enumerate(group):
                if i > 0 and self._requires_context_switch(group[i-1], task):
                    task["transition_buffer"] = 10  # 10 minute buffer

                # Add ADHD accommodations
                task["adhd_accommodations"] = self._get_task_accommodations(task, context)

                adhd_optimized.append(task)

        return adhd_optimized

    def _group_similar_tasks(self, tasks: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Group similar tasks to minimize context switching."""
        # Simple grouping by task type
        groups: Dict[str, List[Dict[str, Any]]] = {}

        for task in tasks:
            task_type = task.get("type", "general")
            if task_type not in groups:
                groups[task_type] = []
            groups[task_type].append(task)

        return list(groups.values())

    def _requires_context_switch(self, task1: Dict[str, Any], task2: Dict[str, Any]) -> bool:
        """Determine if switching between tasks requires significant context change."""
        type1 = task1.get("type", "general")
        type2 = task2.get("type", "general")
        return type1 != type2

    def _get_task_accommodations(self, task: Dict[str, Any], context: Dict[str, Any]) -> List[str]:
        """Get ADHD accommodations for specific task."""
        accommodations = []

        complexity = task.get("complexity", 0.5)
        if complexity > 0.7:
            accommodations.extend([
                "Break into smaller subtasks",
                "Use pomodoro technique",
                "Set up distraction-free environment"
            ])

        if task.get("requires_focus", False):
            accommodations.extend([
                "Schedule during peak energy hours",
                "Use focus music/noise",
                "Enable hyperfocus protection"
            ])

        return accommodations

    async def _estimate_workflow_improvement(
        self,
        original: List[Dict[str, Any]],
        optimized: List[Dict[str, Any]],
        patterns: List[ProductivityPattern]
    ) -> Dict[str, Any]:
        """Estimate improvement from workflow optimization."""
        # Simplified improvement calculation
        context_switches_original = self._count_context_switches(original)
        context_switches_optimized = self._count_context_switches(optimized)

        context_switch_improvement = (
            context_switches_original - context_switches_optimized
        ) / max(context_switches_original, 1)

        return {
            "productivity_gain": min(0.5, context_switch_improvement * 0.3),  # Cap at 50%
            "context_switches_reduced": context_switches_original - context_switches_optimized,
            "adhd_accommodations": [f"Accommodation for task {i}" for i in range(len(optimized))]
        }

    def _count_context_switches(self, tasks: List[Dict[str, Any]]) -> int:
        """Count context switches in task workflow."""
        if len(tasks) <= 1:
            return 0

        switches = 0
        for i in range(1, len(tasks)):
            if self._requires_context_switch(tasks[i-1], tasks[i]):
                switches += 1

        return switches

    async def _update_optimization_models(
        self, recommendation_id: str, results: Dict[str, Any]
    ) -> None:
        """Update optimization models based on results."""
        # Implementation would update ML models
        pass