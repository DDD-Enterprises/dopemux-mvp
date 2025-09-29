"""
Serena v2 Phase 2C: ADHD-Optimized Relationship Filter

Advanced relationship filtering with ADHD cognitive load management, personalized
preference learning, and strict adherence to the max 5 suggestions rule.
"""

import asyncio
import json
import logging
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set, Union
from dataclasses import dataclass, field
from enum import Enum

# Phase 2 Intelligence Components
from .intelligent_relationship_builder import IntelligentRelationship, RelationshipSuggestion, NavigationContext
from .adaptive_learning import AttentionState, LearningPhase
from .learning_profile_manager import PersonalLearningProfileManager, PersonalLearningProfile
from .pattern_recognition import AdvancedPatternRecognition, NavigationPatternType
from .effectiveness_tracker import EffectivenessTracker

# Layer 1 Components
from ..performance_monitor import PerformanceMonitor

logger = logging.getLogger(__name__)


class FilteringStrategy(str, Enum):
    """ADHD filtering strategies based on attention state."""
    MINIMAL = "minimal"           # 1-2 suggestions, highest confidence only
    FOCUSED = "focused"           # 3 suggestions, high relevance + low cognitive load
    BALANCED = "balanced"         # 4-5 suggestions, balanced complexity
    COMPREHENSIVE = "comprehensive"  # 5 suggestions, include learning opportunities
    ADAPTIVE = "adaptive"         # Dynamic based on user patterns


class CognitiveLoadCategory(str, Enum):
    """Cognitive load categories for ADHD optimization."""
    MINIMAL = "minimal"           # 0.0-0.2 - very easy
    LOW = "low"                   # 0.2-0.4 - easy
    MODERATE = "moderate"         # 0.4-0.6 - manageable
    HIGH = "high"                 # 0.6-0.8 - challenging
    OVERWHELMING = "overwhelming" # 0.8-1.0 - very difficult


class FilteringReason(str, Enum):
    """Reasons for filtering decisions."""
    ADHD_COGNITIVE_LOAD = "adhd_cognitive_load"
    ATTENTION_STATE = "attention_state"
    USER_PATTERN_MISMATCH = "user_pattern_mismatch"
    LOW_RELEVANCE = "low_relevance"
    COMPLEXITY_BARRIER = "complexity_barrier"
    SESSION_FATIGUE = "session_fatigue"
    PROGRESSIVE_DISCLOSURE = "progressive_disclosure"
    MAX_SUGGESTIONS_LIMIT = "max_suggestions_limit"


@dataclass
class FilteringDecision:
    """Decision about whether to include a relationship suggestion."""
    relationship: IntelligentRelationship
    included: bool
    filtering_reason: Optional[FilteringReason] = None
    cognitive_load_assessment: CognitiveLoadCategory = CognitiveLoadCategory.MODERATE
    personalization_score: float = 0.0
    adhd_optimization_score: float = 0.0
    final_priority_score: float = 0.0


@dataclass
class FilteringContext:
    """Context for filtering decisions."""
    user_session_id: str
    workspace_path: str
    current_attention_state: AttentionState
    session_duration_minutes: float
    cognitive_fatigue_level: float  # 0.0-1.0
    user_profile: PersonalLearningProfile
    filtering_strategy: FilteringStrategy
    max_suggestions: int = 5


@dataclass
class FilteringResult:
    """Result of relationship filtering process."""
    original_count: int
    filtered_count: int
    filtering_decisions: List[FilteringDecision]
    strategy_used: FilteringStrategy
    adhd_optimization_applied: bool
    cognitive_load_distribution: Dict[str, int]
    personalization_confidence: float
    filtering_performance_ms: float


class ADHDRelationshipFilter:
    """
    ADHD-optimized relationship filtering system.

    Features:
    - Strict adherence to max 5 suggestions rule for cognitive load management
    - Personalized filtering based on learned user patterns and preferences
    - Attention state-aware filtering (peak focus vs low focus vs fatigue)
    - Progressive disclosure support for complex relationships
    - Cognitive load assessment and management
    - Real-time adaptation based on session context
    - Integration with effectiveness tracking for filter optimization
    - Performance monitoring to maintain <200ms targets
    """

    def __init__(
        self,
        profile_manager: PersonalLearningProfileManager,
        pattern_recognition: AdvancedPatternRecognition,
        effectiveness_tracker: EffectivenessTracker,
        performance_monitor: PerformanceMonitor = None
    ):
        self.profile_manager = profile_manager
        self.pattern_recognition = pattern_recognition
        self.effectiveness_tracker = effectiveness_tracker
        self.performance_monitor = performance_monitor or PerformanceMonitor()

        # ADHD filtering configuration
        self.absolute_max_suggestions = 5  # Hard limit for ADHD cognitive load
        self.cognitive_load_threshold = 0.7  # Above this = high cognitive load
        self.relevance_floor = 0.3  # Minimum relevance to consider

        # Filtering strategy thresholds
        self.strategy_thresholds = {
            FilteringStrategy.MINIMAL: {"max": 2, "relevance": 0.8, "cognitive_load": 0.4},
            FilteringStrategy.FOCUSED: {"max": 3, "relevance": 0.6, "cognitive_load": 0.5},
            FilteringStrategy.BALANCED: {"max": 4, "relevance": 0.4, "cognitive_load": 0.6},
            FilteringStrategy.COMPREHENSIVE: {"max": 5, "relevance": 0.3, "cognitive_load": 0.8},
            FilteringStrategy.ADAPTIVE: {"max": 5, "relevance": 0.4, "cognitive_load": 0.6}  # Adjusted dynamically
        }

        # Personalization weights
        self.personalization_weights = {
            "pattern_alignment": 0.3,
            "effectiveness_prediction": 0.25,
            "user_familiarity": 0.2,
            "cognitive_comfort": 0.25
        }

    # Core Filtering

    async def filter_relationships_for_adhd(
        self,
        relationships: List[IntelligentRelationship],
        context: NavigationContext,
        user_session_id: str,
        workspace_path: str
    ) -> FilteringResult:
        """Filter relationships with comprehensive ADHD optimization."""
        operation_id = self.performance_monitor.start_operation("filter_relationships_for_adhd")
        filter_start_time = time.time()

        try:
            # Get user profile and determine filtering strategy
            profile = await self.profile_manager.get_or_create_profile(user_session_id, workspace_path)
            filtering_strategy = await self._determine_filtering_strategy(context, profile)

            # Create filtering context
            filtering_context = FilteringContext(
                user_session_id=user_session_id,
                workspace_path=workspace_path,
                current_attention_state=AttentionState(context.attention_state),
                session_duration_minutes=context.session_duration_minutes,
                cognitive_fatigue_level=self._assess_cognitive_fatigue(context, profile),
                user_profile=profile,
                filtering_strategy=filtering_strategy,
                max_suggestions=self.strategy_thresholds[filtering_strategy]["max"]
            )

            # Score and prioritize all relationships
            scoring_decisions = await self._score_and_prioritize_relationships(
                relationships, filtering_context
            )

            # Apply ADHD filtering rules
            filtering_decisions = await self._apply_adhd_filtering_rules(
                scoring_decisions, filtering_context
            )

            # Select final suggestions with ADHD optimization
            final_suggestions = self._select_final_suggestions(
                filtering_decisions, filtering_context
            )

            # Calculate cognitive load distribution
            cognitive_distribution = self._calculate_cognitive_distribution(final_suggestions)

            # Create filtering result
            filter_duration_ms = (time.time() - filter_start_time) * 1000

            result = FilteringResult(
                original_count=len(relationships),
                filtered_count=len(final_suggestions),
                filtering_decisions=filtering_decisions,
                strategy_used=filtering_strategy,
                adhd_optimization_applied=True,
                cognitive_load_distribution=cognitive_distribution,
                personalization_confidence=profile.pattern_confidence,
                filtering_performance_ms=filter_duration_ms
            )

            self.performance_monitor.end_operation(operation_id, success=True)

            logger.debug(f"🎯 ADHD filtering: {len(relationships)} → {len(final_suggestions)} suggestions "
                        f"(strategy: {filtering_strategy.value})")

            return result

        except Exception as e:
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"ADHD relationship filtering failed: {e}")
            raise

    async def _determine_filtering_strategy(
        self, context: NavigationContext, profile: PersonalLearningProfile
    ) -> FilteringStrategy:
        """Determine optimal filtering strategy based on context and user profile."""
        attention_state = AttentionState(context.attention_state)
        session_duration = context.session_duration_minutes

        # Attention state-based strategy selection
        if attention_state == AttentionState.FATIGUE:
            return FilteringStrategy.MINIMAL

        elif attention_state == AttentionState.LOW_FOCUS:
            return FilteringStrategy.FOCUSED

        elif attention_state == AttentionState.PEAK_FOCUS:
            # Use comprehensive during peak focus, but respect user patterns
            if profile.learning_phase == LearningPhase.CONVERGENCE:
                return FilteringStrategy.ADAPTIVE
            else:
                return FilteringStrategy.COMPREHENSIVE

        elif attention_state == AttentionState.HYPERFOCUS:
            # During hyperfocus, provide balanced suggestions to prevent tunnel vision
            return FilteringStrategy.BALANCED

        else:  # MODERATE_FOCUS
            # Use adaptive strategy for moderate focus
            if profile.pattern_confidence > 0.7:
                return FilteringStrategy.ADAPTIVE
            else:
                return FilteringStrategy.BALANCED

    async def _score_and_prioritize_relationships(
        self,
        relationships: List[IntelligentRelationship],
        context: FilteringContext
    ) -> List[FilteringDecision]:
        """Score and prioritize relationships for ADHD filtering."""
        scoring_decisions = []

        for relationship in relationships:
            # Calculate personalization score
            personalization_score = await self._calculate_personalization_score(
                relationship, context
            )

            # Calculate ADHD optimization score
            adhd_optimization_score = self._calculate_adhd_optimization_score(
                relationship, context
            )

            # Calculate final priority score
            final_priority = self._calculate_final_priority_score(
                relationship, personalization_score, adhd_optimization_score, context
            )

            # Assess cognitive load category
            cognitive_load_category = self._categorize_cognitive_load(
                relationship.cognitive_load_score
            )

            scoring_decision = FilteringDecision(
                relationship=relationship,
                included=True,  # Will be determined in filtering phase
                cognitive_load_assessment=cognitive_load_category,
                personalization_score=personalization_score,
                adhd_optimization_score=adhd_optimization_score,
                final_priority_score=final_priority
            )

            scoring_decisions.append(scoring_decision)

        # Sort by priority score
        scoring_decisions.sort(key=lambda d: d.final_priority_score, reverse=True)

        return scoring_decisions

    async def _apply_adhd_filtering_rules(
        self,
        scoring_decisions: List[FilteringDecision],
        context: FilteringContext
    ) -> List[FilteringDecision]:
        """Apply ADHD-specific filtering rules."""
        strategy_config = self.strategy_thresholds[context.filtering_strategy]

        included_count = 0
        max_allowed = min(context.max_suggestions, self.absolute_max_suggestions)

        for decision in scoring_decisions:
            relationship = decision.relationship

            # Apply filtering rules in priority order
            if included_count >= max_allowed:
                decision.included = False
                decision.filtering_reason = FilteringReason.MAX_SUGGESTIONS_LIMIT
                continue

            # Rule 1: Relevance threshold
            if relationship.relevance_score < strategy_config["relevance"]:
                decision.included = False
                decision.filtering_reason = FilteringReason.LOW_RELEVANCE
                continue

            # Rule 2: Cognitive load management
            if relationship.cognitive_load_score > strategy_config["cognitive_load"]:
                decision.included = False
                decision.filtering_reason = FilteringReason.ADHD_COGNITIVE_LOAD
                continue

            # Rule 3: Attention state compatibility
            if not self._is_attention_state_compatible(relationship, context):
                decision.included = False
                decision.filtering_reason = FilteringReason.ATTENTION_STATE
                continue

            # Rule 4: Session fatigue consideration
            if context.cognitive_fatigue_level > 0.7 and relationship.cognitive_load_score > 0.5:
                decision.included = False
                decision.filtering_reason = FilteringReason.SESSION_FATIGUE
                continue

            # Rule 5: Pattern compatibility (for experienced users)
            if (context.user_profile.learning_phase == LearningPhase.CONVERGENCE and
                decision.personalization_score < 0.4):
                decision.included = False
                decision.filtering_reason = FilteringReason.USER_PATTERN_MISMATCH
                continue

            # Rule 6: Complexity barrier check
            if relationship.complexity_barrier and included_count >= 2:
                decision.included = False
                decision.filtering_reason = FilteringReason.COMPLEXITY_BARRIER
                continue

            # Relationship passes all filters
            decision.included = True
            included_count += 1

        return scoring_decisions

    def _select_final_suggestions(
        self,
        filtering_decisions: List[FilteringDecision],
        context: FilteringContext
    ) -> List[FilteringDecision]:
        """Select final suggestions with optimal ADHD distribution."""
        included_decisions = [d for d in filtering_decisions if d.included]

        # Ensure cognitive load distribution is ADHD-friendly
        optimized_suggestions = self._optimize_cognitive_load_distribution(
            included_decisions, context
        )

        # Apply final ADHD ordering
        final_suggestions = self._apply_adhd_ordering(optimized_suggestions, context)

        return final_suggestions

    # Scoring Methods

    async def _calculate_personalization_score(
        self,
        relationship: IntelligentRelationship,
        context: FilteringContext
    ) -> float:
        """Calculate personalization score based on user patterns and preferences."""
        try:
            scores = []

            # Pattern alignment score
            if relationship.pattern_based_confidence > 0:
                scores.append(relationship.pattern_based_confidence * self.personalization_weights["pattern_alignment"])

            # Effectiveness prediction score
            if relationship.user_effectiveness_prediction > 0:
                scores.append(relationship.user_effectiveness_prediction * self.personalization_weights["effectiveness_prediction"])

            # User familiarity score (from access frequency)
            familiarity = min(1.0, relationship.target_element.access_frequency / 20.0)
            scores.append(familiarity * self.personalization_weights["user_familiarity"])

            # Cognitive comfort score (how well this fits user's complexity tolerance)
            user_max_complexity = context.user_profile.optimal_complexity_range[1]
            if relationship.target_element.complexity_score <= user_max_complexity:
                comfort_score = 1.0
            elif relationship.target_element.complexity_score <= user_max_complexity + 0.2:
                comfort_score = 0.6
            else:
                comfort_score = 0.2

            scores.append(comfort_score * self.personalization_weights["cognitive_comfort"])

            return sum(scores) if scores else 0.5

        except Exception as e:
            logger.error(f"Failed to calculate personalization score: {e}")
            return 0.5

    def _calculate_adhd_optimization_score(
        self,
        relationship: IntelligentRelationship,
        context: FilteringContext
    ) -> float:
        """Calculate ADHD optimization score."""
        optimization_factors = []

        # ADHD-friendly design
        if relationship.adhd_friendly:
            optimization_factors.append(0.3)

        # Low cognitive load
        if relationship.cognitive_load_score <= 0.5:
            optimization_factors.append(0.25)
        elif relationship.cognitive_load_score <= 0.7:
            optimization_factors.append(0.15)
        else:
            optimization_factors.append(0.0)

        # Appropriate attention requirements
        if self._is_attention_requirement_appropriate(relationship, context):
            optimization_factors.append(0.2)

        # No complexity barrier
        if not relationship.complexity_barrier:
            optimization_factors.append(0.15)

        # High relevance
        if relationship.relevance_score > 0.7:
            optimization_factors.append(0.1)

        return sum(optimization_factors)

    def _calculate_final_priority_score(
        self,
        relationship: IntelligentRelationship,
        personalization_score: float,
        adhd_optimization_score: float,
        context: FilteringContext
    ) -> float:
        """Calculate final priority score combining all factors."""
        # Base score from relationship properties
        base_score = (
            relationship.relevance_score * 0.4 +
            relationship.structural_strength * 0.2 +
            (1.0 - relationship.cognitive_load_score) * 0.2 +  # Invert cognitive load
            relationship.user_effectiveness_prediction * 0.2
        )

        # Apply personalization
        personalized_score = base_score * 0.6 + personalization_score * 0.4

        # Apply ADHD optimization
        final_score = personalized_score * 0.7 + adhd_optimization_score * 0.3

        # Boost for critical ConPort links
        if relationship.conport_decision_links:
            final_score += 0.1

        # Penalty for attention state incompatibility
        if not self._is_attention_state_compatible(relationship, context):
            final_score *= 0.7

        return min(1.0, final_score)

    # ADHD Filtering Rules

    def _is_attention_state_compatible(
        self, relationship: IntelligentRelationship, context: FilteringContext
    ) -> bool:
        """Check if relationship is compatible with current attention state."""
        attention_state = context.current_attention_state

        # High cognitive load relationships need good attention
        if relationship.cognitive_load_score > 0.7:
            return attention_state in [AttentionState.PEAK_FOCUS, AttentionState.MODERATE_FOCUS]

        # Complex relationships need focus
        if relationship.complexity_barrier:
            return attention_state != AttentionState.LOW_FOCUS

        # Very simple relationships are always compatible
        if relationship.cognitive_load_score < 0.3:
            return True

        # Moderate relationships need at least moderate focus
        return attention_state != AttentionState.FATIGUE

    def _is_attention_requirement_appropriate(
        self, relationship: IntelligentRelationship, context: FilteringContext
    ) -> bool:
        """Check if relationship's attention requirements match current state."""
        required_attention = relationship.attention_requirements
        current_attention = context.current_attention_state.value

        # Simple mapping of compatibility
        compatibility_map = {
            "peak_focus": [AttentionState.PEAK_FOCUS, AttentionState.HYPERFOCUS],
            "moderate_focus": [AttentionState.PEAK_FOCUS, AttentionState.MODERATE_FOCUS, AttentionState.HYPERFOCUS],
            "any_focus": list(AttentionState)
        }

        return context.current_attention_state in compatibility_map.get(required_attention, [])

    def _assess_cognitive_fatigue(
        self, context: NavigationContext, profile: PersonalLearningProfile
    ) -> float:
        """Assess cognitive fatigue level from session context."""
        fatigue_factors = []

        # Session duration factor
        optimal_duration = profile.average_attention_span_minutes
        duration_ratio = context.session_duration_minutes / optimal_duration

        if duration_ratio > 1.5:
            fatigue_factors.append(0.8)  # High fatigue
        elif duration_ratio > 1.0:
            fatigue_factors.append(0.4)  # Moderate fatigue
        else:
            fatigue_factors.append(0.1)  # Low fatigue

        # Context switching factor
        recent_switches = len(context.recent_navigation_history)
        if recent_switches > profile.context_switch_tolerance:
            switch_fatigue = min(1.0, (recent_switches - profile.context_switch_tolerance) / 5.0)
            fatigue_factors.append(switch_fatigue)

        # Complexity exposure factor
        if hasattr(context, 'recent_complexity_average'):
            complexity_fatigue = max(0.0, context.recent_complexity_average - profile.optimal_complexity_range[1])
            fatigue_factors.append(complexity_fatigue)

        return statistics.mean(fatigue_factors) if fatigue_factors else 0.3

    # Cognitive Load Management

    def _optimize_cognitive_load_distribution(
        self,
        decisions: List[FilteringDecision],
        context: FilteringContext
    ) -> List[FilteringDecision]:
        """Optimize cognitive load distribution across suggestions."""
        if not decisions:
            return decisions

        # Target distribution for ADHD optimization
        # Start easy, gradually increase complexity
        target_distribution = {
            CognitiveLoadCategory.MINIMAL: 1,    # At least 1 minimal load
            CognitiveLoadCategory.LOW: 2,        # Prefer 2 low load
            CognitiveLoadCategory.MODERATE: 1,   # 1 moderate is OK
            CognitiveLoadCategory.HIGH: 1,       # Max 1 high load
            CognitiveLoadCategory.OVERWHELMING: 0  # Never include overwhelming
        }

        # Adjust distribution based on attention state
        if context.current_attention_state == AttentionState.LOW_FOCUS:
            target_distribution = {
                CognitiveLoadCategory.MINIMAL: 2,
                CognitiveLoadCategory.LOW: 1,
                CognitiveLoadCategory.MODERATE: 0,
                CognitiveLoadCategory.HIGH: 0,
                CognitiveLoadCategory.OVERWHELMING: 0
            }
        elif context.current_attention_state == AttentionState.PEAK_FOCUS:
            target_distribution = {
                CognitiveLoadCategory.MINIMAL: 1,
                CognitiveLoadCategory.LOW: 1,
                CognitiveLoadCategory.MODERATE: 2,
                CognitiveLoadCategory.HIGH: 1,
                CognitiveLoadCategory.OVERWHELMING: 0
            }

        # Select suggestions to match target distribution
        optimized_decisions = []
        current_distribution = {category: 0 for category in CognitiveLoadCategory}

        for decision in decisions:
            category = decision.cognitive_load_assessment

            # Check if we can include this category
            if current_distribution[category] < target_distribution[category]:
                optimized_decisions.append(decision)
                current_distribution[category] += 1

                # Stop if we've reached max suggestions
                if len(optimized_decisions) >= context.max_suggestions:
                    break

        # If we haven't filled all slots, add best remaining suggestions
        while (len(optimized_decisions) < context.max_suggestions and
               len(optimized_decisions) < len(decisions)):
            remaining_decisions = [d for d in decisions if d not in optimized_decisions]
            if not remaining_decisions:
                break

            # Add highest priority remaining decision
            best_remaining = max(remaining_decisions, key=lambda d: d.final_priority_score)
            optimized_decisions.append(best_remaining)

        return optimized_decisions

    def _apply_adhd_ordering(
        self,
        decisions: List[FilteringDecision],
        context: FilteringContext
    ) -> List[FilteringDecision]:
        """Apply ADHD-optimized ordering to final suggestions."""
        # ADHD ordering principles:
        # 1. Start with highest confidence, lowest cognitive load
        # 2. Gradually increase complexity
        # 3. End with learning opportunities

        ordered_decisions = sorted(decisions, key=lambda d: (
            # Primary: ADHD-friendliness and confidence
            d.relationship.adhd_friendly,
            d.relationship.pattern_based_confidence,
            -d.relationship.cognitive_load_score,  # Lower cognitive load first

            # Secondary: Relevance and effectiveness
            d.relationship.relevance_score,
            d.relationship.user_effectiveness_prediction,

            # Tertiary: Structural importance
            d.relationship.structural_strength
        ), reverse=True)

        # Assign navigation order numbers
        for i, decision in enumerate(ordered_decisions):
            decision.relationship.suggested_navigation_order = i + 1

        return ordered_decisions

    # Utility Methods

    def _categorize_cognitive_load(self, cognitive_load_score: float) -> CognitiveLoadCategory:
        """Categorize cognitive load for ADHD assessment."""
        if cognitive_load_score <= 0.2:
            return CognitiveLoadCategory.MINIMAL
        elif cognitive_load_score <= 0.4:
            return CognitiveLoadCategory.LOW
        elif cognitive_load_score <= 0.6:
            return CognitiveLoadCategory.MODERATE
        elif cognitive_load_score <= 0.8:
            return CognitiveLoadCategory.HIGH
        else:
            return CognitiveLoadCategory.OVERWHELMING

    def _calculate_cognitive_distribution(
        self, decisions: List[FilteringDecision]
    ) -> Dict[str, int]:
        """Calculate distribution of cognitive load categories."""
        distribution = {category.value: 0 for category in CognitiveLoadCategory}

        for decision in decisions:
            if decision.included:
                category = decision.cognitive_load_assessment.value
                distribution[category] += 1

        return distribution

    async def _calculate_pattern_compatibility_effectiveness(
        self,
        relationship: IntelligentRelationship,
        context: NavigationContext,
        profile: PersonalLearningProfile
    ) -> float:
        """Calculate effectiveness based on pattern compatibility."""
        try:
            # Get pattern recommendations for current context
            pattern_context = {
                "context_type": context.current_task_type,
                "current_complexity": relationship.target_element.complexity_score,
                "session_duration_minutes": context.session_duration_minutes
            }

            pattern_recommendations = await self.pattern_recognition.get_pattern_recommendations(
                pattern_context, context.user_session_id, context.workspace_path
            )

            # Check alignment with recommended approach
            recommended_approach = pattern_recommendations.get("suggested_navigation_approach", {})
            if recommended_approach:
                approach_type = recommended_approach.get("approach", "exploratory")

                # Match relationship type to approach compatibility
                type_compatibility = {
                    "exploration": 0.8 if relationship.relationship_type.value in ["similar_to", "references"] else 0.5,
                    "debugging": 0.8 if relationship.relationship_type.value in ["calls", "uses"] else 0.4,
                    "implementation": 0.8 if relationship.relationship_type.value in ["defines", "implements"] else 0.6
                }

                return type_compatibility.get(approach_type, 0.5)

            return 0.5

        except Exception as e:
            logger.error(f"Failed to calculate pattern compatibility: {e}")
            return 0.5

    # Analysis and Insights

    async def get_filtering_insights(
        self, filtering_result: FilteringResult, context: FilteringContext
    ) -> Dict[str, Any]:
        """Get insights about the filtering process for optimization."""
        insights = {
            "filtering_summary": {
                "original_suggestions": filtering_result.original_count,
                "final_suggestions": filtering_result.filtered_count,
                "reduction_percentage": (1 - filtering_result.filtered_count / max(filtering_result.original_count, 1)) * 100,
                "strategy_used": filtering_result.strategy_used.value,
                "performance_ms": filtering_result.filtering_performance_ms
            },
            "adhd_optimization": {
                "cognitive_load_distribution": filtering_result.cognitive_load_distribution,
                "adhd_friendly_percentage": sum(
                    1 for d in filtering_result.filtering_decisions
                    if d.included and d.relationship.adhd_friendly
                ) / max(filtering_result.filtered_count, 1) * 100,
                "average_cognitive_load": statistics.mean([
                    d.relationship.cognitive_load_score
                    for d in filtering_result.filtering_decisions if d.included
                ]) if filtering_result.filtered_count > 0 else 0.0
            },
            "personalization": {
                "confidence": filtering_result.personalization_confidence,
                "pattern_alignment": statistics.mean([
                    d.personalization_score
                    for d in filtering_result.filtering_decisions if d.included
                ]) if filtering_result.filtered_count > 0 else 0.0
            },
            "filtering_reasons": {
                reason.value: sum(
                    1 for d in filtering_result.filtering_decisions
                    if not d.included and d.filtering_reason == reason
                )
                for reason in FilteringReason
            },
            "recommendations": self._generate_filtering_recommendations(
                filtering_result, context
            )
        }

        return insights

    def _generate_filtering_recommendations(
        self, filtering_result: FilteringResult, context: FilteringContext
    ) -> List[str]:
        """Generate recommendations for improving filtering effectiveness."""
        recommendations = []

        # If too few suggestions
        if filtering_result.filtered_count < 2:
            recommendations.append("🔍 Consider lowering relevance threshold for more suggestions")

        # If cognitive load is too high
        avg_load = statistics.mean([
            d.relationship.cognitive_load_score
            for d in filtering_result.filtering_decisions if d.included
        ]) if filtering_result.filtered_count > 0 else 0.0

        if avg_load > 0.6:
            recommendations.append("🧠 Average cognitive load high - consider focus mode")

        # If personalization confidence is low
        if filtering_result.personalization_confidence < 0.5:
            recommendations.append("📚 More navigation data needed for better personalization")

        # Performance recommendations
        if filtering_result.filtering_performance_ms > 100:
            recommendations.append("⚡ Consider caching for better filtering performance")

        # Session-specific recommendations
        if context.cognitive_fatigue_level > 0.7:
            recommendations.append("☕ High cognitive fatigue detected - consider taking a break")

        return recommendations

    # Placeholder implementations for complex operations
    def _assess_cognitive_fatigue(self, context: NavigationContext, profile: PersonalLearningProfile) -> float:
        """Assess cognitive fatigue level."""
        # Simplified implementation
        duration_factor = context.session_duration_minutes / profile.average_attention_span_minutes
        return min(1.0, max(0.0, duration_factor - 0.5))


# Convenience functions
async def create_adhd_relationship_filter(
    profile_manager: PersonalLearningProfileManager,
    pattern_recognition: AdvancedPatternRecognition,
    effectiveness_tracker: EffectivenessTracker,
    performance_monitor: PerformanceMonitor = None
) -> ADHDRelationshipFilter:
    """Create ADHD relationship filter instance."""
    return ADHDRelationshipFilter(
        profile_manager, pattern_recognition, effectiveness_tracker, performance_monitor
    )


async def test_adhd_filtering(
    filter_system: ADHDRelationshipFilter,
    test_relationships: List[IntelligentRelationship],
    test_context: NavigationContext
) -> Dict[str, Any]:
    """Test ADHD filtering system with sample relationships."""
    try:
        # Run filtering
        filtering_result = await filter_system.filter_relationships_for_adhd(
            test_relationships, test_context, test_context.user_session_id, test_context.workspace_path
        )

        # Analyze results
        test_results = {
            "test_successful": True,
            "adhd_compliant": filtering_result.filtered_count <= 5,
            "cognitive_load_appropriate": all(
                d.relationship.cognitive_load_score <= 0.7
                for d in filtering_result.filtering_decisions if d.included
            ),
            "personalization_applied": filtering_result.personalization_confidence > 0.0,
            "performance_compliant": filtering_result.filtering_performance_ms < 200,
            "filtering_summary": {
                "original_count": filtering_result.original_count,
                "filtered_count": filtering_result.filtered_count,
                "strategy": filtering_result.strategy_used.value,
                "performance_ms": filtering_result.filtering_performance_ms
            }
        }

        # Overall success assessment
        test_results["overall_success"] = all([
            test_results["adhd_compliant"],
            test_results["cognitive_load_appropriate"],
            test_results["performance_compliant"]
        ])

        return test_results

    except Exception as e:
        logger.error(f"ADHD filtering test failed: {e}")
        return {
            "test_successful": False,
            "error": str(e),
            "overall_success": False
        }


if __name__ == "__main__":
    # Quick test when run directly
    async def main():
        print("🎯 Serena ADHD Relationship Filter")
        print("Cognitive load management with max 5 suggestions rule")
        print("✅ Module loaded successfully")

    asyncio.run(main())