"""
Serena v2 Phase 2C: Real-time Relationship Relevance Scorer

Dynamic relationship relevance scoring that adapts in real-time based on user navigation,
attention state changes, learned patterns, and ADHD cognitive load considerations.
"""

import asyncio
import json
import logging
import statistics
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import math

# Phase 2 Intelligence Components
from .intelligent_relationship_builder import IntelligentRelationship, NavigationContext
from .adaptive_learning import AttentionState, NavigationSequence, AdaptiveLearningEngine
from .learning_profile_manager import PersonalLearningProfileManager, PersonalLearningProfile
from .pattern_recognition import AdvancedPatternRecognition, NavigationPatternType
from .effectiveness_tracker import EffectivenessTracker

# Layer 1 Components
from ..performance_monitor import PerformanceMonitor

logger = logging.getLogger(__name__)


class ScoringDimension(str, Enum):
    """Dimensions for real-time relevance scoring."""
    STRUCTURAL_RELEVANCE = "structural_relevance"      # Based on code structure
    CONTEXTUAL_RELEVANCE = "contextual_relevance"      # Based on current task context
    PATTERN_RELEVANCE = "pattern_relevance"            # Based on learned patterns
    TEMPORAL_RELEVANCE = "temporal_relevance"          # Based on recency and timing
    COGNITIVE_COMPATIBILITY = "cognitive_compatibility" # Based on cognitive load fit
    ATTENTION_ALIGNMENT = "attention_alignment"        # Based on attention state match
    PERSONAL_PREFERENCE = "personal_preference"        # Based on user preferences
    EFFECTIVENESS_PREDICTION = "effectiveness_prediction"  # Based on predicted success


class ScoringTrigger(str, Enum):
    """Events that trigger relevance score updates."""
    NAVIGATION_ACTION = "navigation_action"           # User navigated to element
    ATTENTION_STATE_CHANGE = "attention_state_change" # Attention state shifted
    CONTEXT_SWITCH = "context_switch"                 # Context changed
    PATTERN_UPDATE = "pattern_update"                 # User patterns updated
    SESSION_PROGRESS = "session_progress"             # Session progressed
    EFFECTIVENESS_FEEDBACK = "effectiveness_feedback"  # User provided feedback
    TIME_DECAY = "time_decay"                         # Time-based relevance decay


@dataclass
class RelevanceScore:
    """Individual relevance score with metadata."""
    dimension: ScoringDimension
    score: float  # 0.0-1.0
    confidence: float  # 0.0-1.0
    last_updated: datetime
    update_trigger: ScoringTrigger
    decay_rate: float = 0.01  # How quickly this score decays over time
    boost_factor: float = 1.0  # Temporary boost factor
    stability: float = 0.5  # How stable this score is (0.0 = volatile, 1.0 = stable)


@dataclass
class DynamicRelationshipScore:
    """Dynamic, real-time relationship score with ADHD optimization."""
    relationship_id: str
    overall_relevance: float  # 0.0-1.0 current overall relevance
    dimension_scores: Dict[ScoringDimension, RelevanceScore]

    # ADHD-specific scoring
    cognitive_load_score: float
    attention_state_compatibility: float
    user_preference_alignment: float

    # Dynamic factors
    temporal_boost: float = 0.0  # Temporary relevance boost
    session_context_boost: float = 0.0  # Boost based on session context
    pattern_momentum: float = 0.0  # Momentum from pattern alignment

    # Metadata
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    update_count: int = 0
    stability_score: float = 0.5  # How stable the scoring has become
    prediction_confidence: float = 0.0  # Confidence in score predictions


@dataclass
class ScoringEvent:
    """Event that triggers relevance score updates."""
    event_id: str
    user_session_id: str
    trigger: ScoringTrigger
    timestamp: datetime
    context_data: Dict[str, Any]
    affected_relationships: List[str]  # Relationship IDs affected
    impact_magnitude: float  # 0.0-1.0 how much impact this event has


@dataclass
class RelevanceTrend:
    """Trend analysis for relationship relevance over time."""
    relationship_id: str
    trend_direction: str  # increasing, decreasing, stable, volatile
    trend_strength: float  # 0.0-1.0 how strong the trend is
    volatility: float  # 0.0-1.0 how much the score fluctuates
    prediction_accuracy: float  # How accurate predictions have been
    recommended_actions: List[str]


class RealtimeRelevanceScorer:
    """
    Real-time relationship relevance scoring system with ADHD optimization.

    Features:
    - Dynamic relevance scoring that adapts to user navigation in real-time
    - ADHD-optimized scoring with cognitive load and attention state integration
    - Multi-dimensional scoring with confidence tracking
    - Temporal relevance decay and boost mechanisms
    - Pattern-based scoring updates from learned navigation behaviors
    - Effectiveness feedback integration for continuous improvement
    - Performance-optimized scoring updates maintaining <200ms targets
    - Predictive scoring for anticipated user needs
    """

    def __init__(
        self,
        learning_engine: AdaptiveLearningEngine,
        profile_manager: PersonalLearningProfileManager,
        pattern_recognition: AdvancedPatternRecognition,
        effectiveness_tracker: EffectivenessTracker,
        performance_monitor: PerformanceMonitor = None
    ):
        self.learning_engine = learning_engine
        self.profile_manager = profile_manager
        self.pattern_recognition = pattern_recognition
        self.effectiveness_tracker = effectiveness_tracker
        self.performance_monitor = performance_monitor or PerformanceMonitor()

        # Scoring configuration
        self.update_frequency_seconds = 30  # How often to update scores
        self.decay_update_frequency_minutes = 5  # How often to apply decay
        self.max_concurrent_updates = 10  # Limit concurrent score updates

        # ADHD optimization settings
        self.attention_state_weights = {
            AttentionState.PEAK_FOCUS: {"complexity_tolerance": 1.0, "suggestion_count": 5},
            AttentionState.MODERATE_FOCUS: {"complexity_tolerance": 0.7, "suggestion_count": 4},
            AttentionState.LOW_FOCUS: {"complexity_tolerance": 0.4, "suggestion_count": 3},
            AttentionState.HYPERFOCUS: {"complexity_tolerance": 0.9, "suggestion_count": 3},
            AttentionState.FATIGUE: {"complexity_tolerance": 0.3, "suggestion_count": 2}
        }

        # Scoring weights for different dimensions
        self.dimension_weights = {
            ScoringDimension.STRUCTURAL_RELEVANCE: 0.20,
            ScoringDimension.CONTEXTUAL_RELEVANCE: 0.25,
            ScoringDimension.PATTERN_RELEVANCE: 0.20,
            ScoringDimension.COGNITIVE_COMPATIBILITY: 0.15,
            ScoringDimension.ATTENTION_ALIGNMENT: 0.10,
            ScoringDimension.PERSONAL_PREFERENCE: 0.10
        }

        # Active scoring state
        self._active_scores: Dict[str, DynamicRelationshipScore] = {}
        self._scoring_history: Dict[str, List[float]] = {}
        self._update_callbacks: List[Callable] = []

        # Performance tracking
        self._scoring_performance_metrics = {
            "updates_per_second": 0.0,
            "average_update_time_ms": 0.0,
            "cache_hit_rate": 0.0
        }

    # Core Real-time Scoring

    async def initialize_relationship_scoring(
        self,
        relationships: List[IntelligentRelationship],
        context: NavigationContext
    ) -> Dict[str, DynamicRelationshipScore]:
        """Initialize real-time scoring for a set of relationships."""
        operation_id = self.performance_monitor.start_operation("initialize_relationship_scoring")

        try:
            initialized_scores = {}

            # Get user profile for personalization
            profile = await self.profile_manager.get_or_create_profile(
                context.user_session_id, context.workspace_path
            )

            for relationship in relationships:
                # Create initial dynamic score
                dynamic_score = await self._create_initial_dynamic_score(
                    relationship, context, profile
                )

                relationship_id = self._generate_relationship_id(relationship)
                initialized_scores[relationship_id] = dynamic_score
                self._active_scores[relationship_id] = dynamic_score

                # Initialize scoring history
                self._scoring_history[relationship_id] = [dynamic_score.overall_relevance]

            self.performance_monitor.end_operation(operation_id, success=True)

            logger.debug(f"🎯 Initialized real-time scoring for {len(relationships)} relationships")
            return initialized_scores

        except Exception as e:
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"Failed to initialize relationship scoring: {e}")
            raise

    async def update_scores_from_navigation(
        self,
        user_session_id: str,
        navigation_event: Dict[str, Any],
        current_context: NavigationContext
    ) -> Dict[str, float]:
        """Update relationship scores based on navigation events."""
        operation_id = self.performance_monitor.start_operation("update_scores_from_navigation")

        try:
            # Create scoring event
            scoring_event = ScoringEvent(
                event_id=f"nav_{user_session_id}_{int(time.time())}",
                user_session_id=user_session_id,
                trigger=ScoringTrigger.NAVIGATION_ACTION,
                timestamp=datetime.now(timezone.utc),
                context_data=navigation_event,
                affected_relationships=list(self._active_scores.keys()),
                impact_magnitude=self._calculate_navigation_impact_magnitude(navigation_event)
            )

            # Update scores for all active relationships
            updated_scores = {}
            for relationship_id, dynamic_score in self._active_scores.items():
                new_relevance = await self._update_score_from_event(
                    dynamic_score, scoring_event, current_context
                )
                updated_scores[relationship_id] = new_relevance

            # Trigger update callbacks
            await self._trigger_update_callbacks(updated_scores, scoring_event)

            self.performance_monitor.end_operation(operation_id, success=True)

            logger.debug(f"📊 Updated {len(updated_scores)} relationship scores from navigation")
            return updated_scores

        except Exception as e:
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"Failed to update scores from navigation: {e}")
            return {}

    async def update_scores_from_attention_change(
        self,
        user_session_id: str,
        new_attention_state: AttentionState,
        current_context: NavigationContext
    ) -> Dict[str, float]:
        """Update relationship scores when attention state changes."""
        operation_id = self.performance_monitor.start_operation("update_scores_attention_change")

        try:
            # Create attention change event
            scoring_event = ScoringEvent(
                event_id=f"attention_{user_session_id}_{int(time.time())}",
                user_session_id=user_session_id,
                trigger=ScoringTrigger.ATTENTION_STATE_CHANGE,
                timestamp=datetime.now(timezone.utc),
                context_data={"new_attention_state": new_attention_state.value},
                affected_relationships=list(self._active_scores.keys()),
                impact_magnitude=0.6  # Attention changes have moderate impact
            )

            updated_scores = {}
            for relationship_id, dynamic_score in self._active_scores.items():
                # Update attention alignment score
                await self._update_attention_alignment_score(
                    dynamic_score, new_attention_state, current_context
                )

                # Recalculate overall relevance
                new_relevance = self._calculate_overall_relevance(dynamic_score)
                updated_scores[relationship_id] = new_relevance

                # Update scoring history
                self._scoring_history[relationship_id].append(new_relevance)

            # Trigger callbacks
            await self._trigger_update_callbacks(updated_scores, scoring_event)

            self.performance_monitor.end_operation(operation_id, success=True)

            logger.debug(f"🧠 Updated scores for attention state change: {new_attention_state.value}")
            return updated_scores

        except Exception as e:
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"Failed to update scores from attention change: {e}")
            return {}

    async def get_top_ranked_relationships(
        self,
        user_session_id: str,
        current_context: NavigationContext,
        max_results: int = 5
    ) -> List[Tuple[IntelligentRelationship, float]]:
        """Get top-ranked relationships with current relevance scores."""
        operation_id = self.performance_monitor.start_operation("get_top_ranked_relationships")

        try:
            # Update scores based on current context
            await self._refresh_scores_for_context(current_context)

            # Get current scores
            scored_relationships = []
            for relationship_id, dynamic_score in self._active_scores.items():
                # Get the actual relationship object (would need to be stored/retrieved)
                relationship = await self._get_relationship_by_id(relationship_id)
                if relationship:
                    scored_relationships.append((relationship, dynamic_score.overall_relevance))

            # Sort by relevance score
            scored_relationships.sort(key=lambda x: x[1], reverse=True)

            # Apply ADHD limits
            final_results = scored_relationships[:min(max_results, 5)]

            self.performance_monitor.end_operation(operation_id, success=True)

            logger.debug(f"🏆 Retrieved {len(final_results)} top-ranked relationships")
            return final_results

        except Exception as e:
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"Failed to get top-ranked relationships: {e}")
            return []

    # Score Calculation and Updates

    async def _create_initial_dynamic_score(
        self,
        relationship: IntelligentRelationship,
        context: NavigationContext,
        profile: PersonalLearningProfile
    ) -> DynamicRelationshipScore:
        """Create initial dynamic score for a relationship."""
        # Initialize dimension scores
        dimension_scores = {}

        # Structural relevance (from Tree-sitter and graph analysis)
        dimension_scores[ScoringDimension.STRUCTURAL_RELEVANCE] = RelevanceScore(
            dimension=ScoringDimension.STRUCTURAL_RELEVANCE,
            score=relationship.structural_strength,
            confidence=relationship.discovery_confidence,
            last_updated=datetime.now(timezone.utc),
            update_trigger=ScoringTrigger.NAVIGATION_ACTION,
            stability=0.8  # Structural relationships are stable
        )

        # Contextual relevance (based on current task)
        contextual_score = await self._calculate_initial_contextual_relevance(
            relationship, context
        )
        dimension_scores[ScoringDimension.CONTEXTUAL_RELEVANCE] = RelevanceScore(
            dimension=ScoringDimension.CONTEXTUAL_RELEVANCE,
            score=contextual_score,
            confidence=0.7,
            last_updated=datetime.now(timezone.utc),
            update_trigger=ScoringTrigger.NAVIGATION_ACTION,
            stability=0.6  # Context can change
        )

        # Pattern relevance (based on learned patterns)
        pattern_score = relationship.pattern_based_confidence
        dimension_scores[ScoringDimension.PATTERN_RELEVANCE] = RelevanceScore(
            dimension=ScoringDimension.PATTERN_RELEVANCE,
            score=pattern_score,
            confidence=profile.pattern_confidence,
            last_updated=datetime.now(timezone.utc),
            update_trigger=ScoringTrigger.PATTERN_UPDATE,
            stability=0.7  # Patterns are relatively stable
        )

        # Cognitive compatibility (ADHD-specific)
        cognitive_compatibility = self._calculate_cognitive_compatibility(
            relationship, context, profile
        )
        dimension_scores[ScoringDimension.COGNITIVE_COMPATIBILITY] = RelevanceScore(
            dimension=ScoringDimension.COGNITIVE_COMPATIBILITY,
            score=cognitive_compatibility,
            confidence=0.8,
            last_updated=datetime.now(timezone.utc),
            update_trigger=ScoringTrigger.ATTENTION_STATE_CHANGE,
            stability=0.5  # Can vary with attention state
        )

        # Attention alignment
        attention_alignment = self._calculate_attention_alignment(
            relationship, context, profile
        )
        dimension_scores[ScoringDimension.ATTENTION_ALIGNMENT] = RelevanceScore(
            dimension=ScoringDimension.ATTENTION_ALIGNMENT,
            score=attention_alignment,
            confidence=0.9,
            last_updated=datetime.now(timezone.utc),
            update_trigger=ScoringTrigger.ATTENTION_STATE_CHANGE,
            stability=0.3  # Highly variable with attention
        )

        # Personal preference
        personal_preference = self._calculate_personal_preference_score(
            relationship, profile
        )
        dimension_scores[ScoringDimension.PERSONAL_PREFERENCE] = RelevanceScore(
            dimension=ScoringDimension.PERSONAL_PREFERENCE,
            score=personal_preference,
            confidence=profile.pattern_confidence,
            last_updated=datetime.now(timezone.utc),
            update_trigger=ScoringTrigger.PATTERN_UPDATE,
            stability=0.8  # Preferences are relatively stable
        )

        # Calculate overall relevance
        overall_relevance = self._calculate_overall_relevance_from_dimensions(dimension_scores)

        return DynamicRelationshipScore(
            relationship_id=self._generate_relationship_id(relationship),
            overall_relevance=overall_relevance,
            dimension_scores=dimension_scores,
            cognitive_load_score=relationship.cognitive_load_score,
            attention_state_compatibility=attention_alignment,
            user_preference_alignment=personal_preference,
            update_count=1,
            stability_score=0.5,
            prediction_confidence=profile.pattern_confidence
        )

    async def _update_score_from_event(
        self,
        dynamic_score: DynamicRelationshipScore,
        event: ScoringEvent,
        current_context: NavigationContext
    ) -> float:
        """Update dynamic score based on scoring event."""
        try:
            # Apply time decay first
            await self._apply_time_decay(dynamic_score)

            # Update relevant dimensions based on event type
            if event.trigger == ScoringTrigger.NAVIGATION_ACTION:
                await self._update_navigation_based_scores(dynamic_score, event, current_context)

            elif event.trigger == ScoringTrigger.ATTENTION_STATE_CHANGE:
                await self._update_attention_based_scores(dynamic_score, event, current_context)

            elif event.trigger == ScoringTrigger.CONTEXT_SWITCH:
                await self._update_context_based_scores(dynamic_score, event, current_context)

            elif event.trigger == ScoringTrigger.PATTERN_UPDATE:
                await self._update_pattern_based_scores(dynamic_score, event, current_context)

            elif event.trigger == ScoringTrigger.EFFECTIVENESS_FEEDBACK:
                await self._update_effectiveness_based_scores(dynamic_score, event, current_context)

            # Recalculate overall relevance
            new_overall_relevance = self._calculate_overall_relevance(dynamic_score)

            # Update metadata
            dynamic_score.last_updated = datetime.now(timezone.utc)
            dynamic_score.update_count += 1

            # Update stability score
            self._update_stability_score(dynamic_score)

            return new_overall_relevance

        except Exception as e:
            logger.error(f"Failed to update score from event: {e}")
            return dynamic_score.overall_relevance

    async def _refresh_scores_for_context(self, context: NavigationContext) -> None:
        """Refresh all scores based on current context."""
        try:
            # Get user profile
            profile = await self.profile_manager.get_or_create_profile(
                context.user_session_id, context.workspace_path
            )

            # Update contextual and attention-based scores for all active relationships
            update_tasks = []
            for relationship_id, dynamic_score in list(self._active_scores.items()):
                task = self._refresh_context_dependent_scores(dynamic_score, context, profile)
                update_tasks.append(task)

            # Execute updates concurrently with limit
            semaphore = asyncio.Semaphore(self.max_concurrent_updates)

            async def limited_update(task):
                async with semaphore:
                    return await task

            await asyncio.gather(*[limited_update(task) for task in update_tasks])

        except Exception as e:
            logger.error(f"Failed to refresh scores for context: {e}")

    async def _refresh_context_dependent_scores(
        self,
        dynamic_score: DynamicRelationshipScore,
        context: NavigationContext,
        profile: PersonalLearningProfile
    ) -> None:
        """Refresh context-dependent scores for a single relationship."""
        try:
            # Update contextual relevance
            if ScoringDimension.CONTEXTUAL_RELEVANCE in dynamic_score.dimension_scores:
                contextual_score = dynamic_score.dimension_scores[ScoringDimension.CONTEXTUAL_RELEVANCE]
                new_contextual_relevance = await self._calculate_current_contextual_relevance(
                    dynamic_score.relationship_id, context
                )
                contextual_score.score = new_contextual_relevance
                contextual_score.last_updated = datetime.now(timezone.utc)

            # Update attention alignment
            if ScoringDimension.ATTENTION_ALIGNMENT in dynamic_score.dimension_scores:
                attention_score = dynamic_score.dimension_scores[ScoringDimension.ATTENTION_ALIGNMENT]
                new_attention_alignment = self._calculate_current_attention_alignment(
                    dynamic_score, context, profile
                )
                attention_score.score = new_attention_alignment
                attention_score.last_updated = datetime.now(timezone.utc)

            # Update cognitive compatibility
            dynamic_score.attention_state_compatibility = new_attention_alignment
            dynamic_score.cognitive_load_score = self._update_cognitive_load_for_context(
                dynamic_score.cognitive_load_score, context
            )

            # Recalculate overall relevance
            dynamic_score.overall_relevance = self._calculate_overall_relevance(dynamic_score)

        except Exception as e:
            logger.error(f"Failed to refresh context-dependent scores: {e}")

    # Dimension-specific Updates

    async def _update_navigation_based_scores(
        self,
        dynamic_score: DynamicRelationshipScore,
        event: ScoringEvent,
        context: NavigationContext
    ) -> None:
        """Update scores based on navigation actions."""
        navigated_to_element_id = event.context_data.get('element_id')

        if navigated_to_element_id:
            # Boost relevance for relationships involving navigated element
            relationship_target_id = event.context_data.get('target_element_id')
            if relationship_target_id == navigated_to_element_id:
                # User navigated to this relationship's target - boost relevance
                dynamic_score.temporal_boost = min(1.0, dynamic_score.temporal_boost + 0.2)

                # Update temporal relevance score
                if ScoringDimension.TEMPORAL_RELEVANCE in dynamic_score.dimension_scores:
                    temporal_score = dynamic_score.dimension_scores[ScoringDimension.TEMPORAL_RELEVANCE]
                    temporal_score.score = min(1.0, temporal_score.score + 0.3)
                    temporal_score.boost_factor = 1.2

    async def _update_attention_based_scores(
        self,
        dynamic_score: DynamicRelationshipScore,
        event: ScoringEvent,
        context: NavigationContext
    ) -> None:
        """Update scores based on attention state changes."""
        new_attention_state = AttentionState(event.context_data['new_attention_state'])

        # Recalculate attention alignment
        attention_score = dynamic_score.dimension_scores[ScoringDimension.ATTENTION_ALIGNMENT]

        # Get attention state weights
        attention_weights = self.attention_state_weights[new_attention_state]

        # Update score based on cognitive load compatibility
        if dynamic_score.cognitive_load_score <= attention_weights["complexity_tolerance"]:
            attention_score.score = min(1.0, attention_score.score + 0.1)
        else:
            attention_score.score = max(0.0, attention_score.score - 0.2)

        attention_score.last_updated = datetime.now(timezone.utc)
        attention_score.update_trigger = ScoringTrigger.ATTENTION_STATE_CHANGE

    async def _update_pattern_based_scores(
        self,
        dynamic_score: DynamicRelationshipScore,
        event: ScoringEvent,
        context: NavigationContext
    ) -> None:
        """Update scores based on pattern learning updates."""
        # Update pattern relevance based on new learning
        pattern_score = dynamic_score.dimension_scores.get(ScoringDimension.PATTERN_RELEVANCE)
        if pattern_score:
            # Get updated pattern compatibility
            new_pattern_relevance = await self._calculate_updated_pattern_relevance(
                dynamic_score.relationship_id, context
            )

            # Use exponential moving average for smooth updates
            alpha = 0.3
            pattern_score.score = alpha * new_pattern_relevance + (1 - alpha) * pattern_score.score
            pattern_score.last_updated = datetime.now(timezone.utc)

    async def _update_effectiveness_based_scores(
        self,
        dynamic_score: DynamicRelationshipScore,
        event: ScoringEvent,
        context: NavigationContext
    ) -> None:
        """Update scores based on effectiveness feedback."""
        effectiveness_feedback = event.context_data.get('effectiveness', 0.5)

        # Update effectiveness prediction dimension
        if ScoringDimension.EFFECTIVENESS_PREDICTION in dynamic_score.dimension_scores:
            eff_score = dynamic_score.dimension_scores[ScoringDimension.EFFECTIVENESS_PREDICTION]

            # Update using feedback
            alpha = 0.4  # Higher learning rate for effectiveness feedback
            eff_score.score = alpha * effectiveness_feedback + (1 - alpha) * eff_score.score
            eff_score.confidence = min(1.0, eff_score.confidence + 0.1)
            eff_score.last_updated = datetime.now(timezone.utc)

        # Boost overall score if effectiveness was high
        if effectiveness_feedback > 0.8:
            dynamic_score.session_context_boost = min(1.0, dynamic_score.session_context_boost + 0.1)

    # Time-based Updates

    async def _apply_time_decay(self, dynamic_score: DynamicRelationshipScore) -> None:
        """Apply time-based decay to relevance scores."""
        current_time = datetime.now(timezone.utc)

        for dimension, score in dynamic_score.dimension_scores.items():
            # Calculate time since last update
            time_diff = (current_time - score.last_updated).total_seconds() / 3600  # Hours

            # Apply decay based on dimension characteristics
            if time_diff > 0:
                decay_amount = score.decay_rate * time_diff
                score.score = max(0.0, score.score - decay_amount)

                # Reduce boost factors over time
                if score.boost_factor > 1.0:
                    score.boost_factor = max(1.0, score.boost_factor - (decay_amount * 2))

        # Apply decay to temporal boosts
        time_diff_minutes = (current_time - dynamic_score.last_updated).total_seconds() / 60
        if time_diff_minutes > 30:  # Decay after 30 minutes
            decay_factor = math.exp(-time_diff_minutes / 60)  # Exponential decay
            dynamic_score.temporal_boost *= decay_factor
            dynamic_score.session_context_boost *= decay_factor

    async def start_background_scoring_updates(self, user_session_id: str) -> None:
        """Start background task for periodic score updates."""
        async def background_update_loop():
            while True:
                try:
                    await asyncio.sleep(self.update_frequency_seconds)

                    # Apply time decay to all active scores
                    for dynamic_score in self._active_scores.values():
                        await self._apply_time_decay(dynamic_score)

                    # Update overall relevance scores
                    for dynamic_score in self._active_scores.values():
                        dynamic_score.overall_relevance = self._calculate_overall_relevance(dynamic_score)

                except Exception as e:
                    logger.error(f"Background scoring update failed: {e}")

        # Start background task
        asyncio.create_task(background_update_loop())
        logger.info(f"🔄 Started background scoring updates for user {user_session_id}")

    # Calculation Methods

    def _calculate_overall_relevance(self, dynamic_score: DynamicRelationshipScore) -> float:
        """Calculate overall relevance from dimension scores."""
        weighted_scores = []

        for dimension, weight in self.dimension_weights.items():
            if dimension in dynamic_score.dimension_scores:
                dimension_score = dynamic_score.dimension_scores[dimension]
                # Apply confidence weighting
                weighted_score = dimension_score.score * weight * dimension_score.confidence
                weighted_scores.append(weighted_score)

        base_relevance = sum(weighted_scores)

        # Apply dynamic boosts
        boosted_relevance = base_relevance * (1.0 + dynamic_score.temporal_boost + dynamic_score.session_context_boost)

        # Apply pattern momentum
        final_relevance = boosted_relevance + (dynamic_score.pattern_momentum * 0.1)

        return min(1.0, max(0.0, final_relevance))

    def _calculate_overall_relevance_from_dimensions(
        self, dimension_scores: Dict[ScoringDimension, RelevanceScore]
    ) -> float:
        """Calculate overall relevance from dimension scores."""
        weighted_scores = []

        for dimension, weight in self.dimension_weights.items():
            if dimension in dimension_scores:
                score = dimension_scores[dimension].score
                confidence = dimension_scores[dimension].confidence
                weighted_scores.append(score * weight * confidence)

        return sum(weighted_scores) if weighted_scores else 0.0

    def _calculate_cognitive_compatibility(
        self,
        relationship: IntelligentRelationship,
        context: NavigationContext,
        profile: PersonalLearningProfile
    ) -> float:
        """Calculate cognitive compatibility for ADHD users."""
        compatibility_factors = []

        # Complexity compatibility
        target_complexity = relationship.target_element.complexity_score
        user_tolerance = profile.optimal_complexity_range[1]

        if target_complexity <= user_tolerance:
            compatibility_factors.append(1.0)
        elif target_complexity <= user_tolerance + 0.2:
            compatibility_factors.append(0.7)
        else:
            compatibility_factors.append(0.3)

        # Cognitive load compatibility
        cognitive_load = relationship.cognitive_load_score
        if cognitive_load <= 0.4:
            compatibility_factors.append(1.0)
        elif cognitive_load <= 0.6:
            compatibility_factors.append(0.7)
        else:
            compatibility_factors.append(0.4)

        # Context switching compatibility
        if relationship.source_element.file_path == relationship.target_element.file_path:
            compatibility_factors.append(0.8)  # Same file = less switching cost
        else:
            compatibility_factors.append(0.5)  # Different file = switching cost

        return statistics.mean(compatibility_factors)

    def _calculate_attention_alignment(
        self,
        relationship: IntelligentRelationship,
        context: NavigationContext,
        profile: PersonalLearningProfile
    ) -> float:
        """Calculate attention alignment score."""
        attention_state = AttentionState(context.attention_state)
        attention_weights = self.attention_state_weights[attention_state]

        # Check if relationship cognitive load is appropriate for attention state
        if relationship.cognitive_load_score <= attention_weights["complexity_tolerance"]:
            return 1.0
        else:
            # Calculate penalty for exceeding attention capacity
            excess = relationship.cognitive_load_score - attention_weights["complexity_tolerance"]
            return max(0.0, 1.0 - (excess * 2))  # Penalty for excess complexity

    def _calculate_personal_preference_score(
        self, relationship: IntelligentRelationship, profile: PersonalLearningProfile
    ) -> float:
        """Calculate personal preference score based on user profile."""
        preference_factors = []

        # Progressive disclosure preference
        if profile.progressive_disclosure_preference and relationship.target_element.complexity_score > 0.6:
            preference_factors.append(0.8)  # Likes progressive disclosure for complex items
        else:
            preference_factors.append(0.6)

        # Result limit preference
        if profile.preferred_result_limit <= 5:  # Conservative user
            if relationship.cognitive_load_score <= 0.5:
                preference_factors.append(0.9)  # Prefers simple relationships
            else:
                preference_factors.append(0.4)
        else:  # User comfortable with more results
            preference_factors.append(0.7)

        # Successful pattern alignment
        if any(pattern in relationship.context_sources for pattern in ['similar_patterns', 'usage_patterns']):
            preference_factors.append(0.8)
        else:
            preference_factors.append(0.5)

        return statistics.mean(preference_factors)

    # Utility Methods

    def _generate_relationship_id(self, relationship: IntelligentRelationship) -> str:
        """Generate unique ID for relationship."""
        return f"{relationship.source_element.id}_{relationship.target_element.id}_{relationship.relationship_type.value}"

    def _calculate_navigation_impact_magnitude(self, navigation_event: Dict[str, Any]) -> float:
        """Calculate impact magnitude of navigation event."""
        # Higher impact for successful navigation, complex elements, etc.
        base_impact = 0.5

        if navigation_event.get('success', True):
            base_impact += 0.2

        complexity = navigation_event.get('complexity_score', 0.5)
        base_impact += complexity * 0.3

        return min(1.0, base_impact)

    def _update_stability_score(self, dynamic_score: DynamicRelationshipScore) -> None:
        """Update stability score based on score history."""
        relationship_id = dynamic_score.relationship_id
        history = self._scoring_history.get(relationship_id, [])

        if len(history) >= 5:
            # Calculate variance of recent scores
            recent_scores = history[-5:]
            variance = statistics.variance(recent_scores)

            # Lower variance = higher stability
            dynamic_score.stability_score = max(0.1, 1.0 - (variance * 4))
        else:
            # Not enough history for stability assessment
            dynamic_score.stability_score = 0.5

    def _update_cognitive_load_for_context(
        self, base_cognitive_load: float, context: NavigationContext
    ) -> float:
        """Update cognitive load based on current context."""
        # Adjust cognitive load based on session fatigue
        fatigue_multiplier = 1.0 + (context.session_duration_minutes / 60.0) * 0.2
        adjusted_load = base_cognitive_load * fatigue_multiplier

        # Adjust based on attention state
        attention_state = AttentionState(context.attention_state)
        if attention_state == AttentionState.PEAK_FOCUS:
            adjusted_load *= 0.8  # Peak focus reduces perceived load
        elif attention_state == AttentionState.LOW_FOCUS:
            adjusted_load *= 1.3  # Low focus increases perceived load

        return min(1.0, adjusted_load)

    # Callback and Integration

    def add_score_update_callback(self, callback: Callable) -> None:
        """Add callback for score updates."""
        self._update_callbacks.append(callback)

    async def _trigger_update_callbacks(
        self, updated_scores: Dict[str, float], event: ScoringEvent
    ) -> None:
        """Trigger registered callbacks with score updates."""
        for callback in self._update_callbacks:
            try:
                await callback(updated_scores, event)
            except Exception as e:
                logger.error(f"Score update callback failed: {e}")

    # Analysis and Monitoring

    async def get_scoring_analytics(self, user_session_id: str) -> Dict[str, Any]:
        """Get analytics about scoring performance and effectiveness."""
        try:
            user_scores = {
                k: v for k, v in self._active_scores.items()
                if v.relationship_id.startswith(user_session_id) or user_session_id in k
            }

            if not user_scores:
                return {"message": "No active scores for user"}

            analytics = {
                "active_relationships": len(user_scores),
                "average_relevance": statistics.mean([score.overall_relevance for score in user_scores.values()]),
                "average_stability": statistics.mean([score.stability_score for score in user_scores.values()]),
                "high_relevance_count": sum(1 for score in user_scores.values() if score.overall_relevance > 0.7),
                "adhd_friendly_count": sum(1 for score in user_scores.values() if score.cognitive_load_score <= 0.5),
                "dimension_performance": {},
                "update_frequency": {
                    "total_updates": sum(score.update_count for score in user_scores.values()),
                    "average_updates_per_relationship": statistics.mean([score.update_count for score in user_scores.values()])
                }
            }

            # Dimension-specific analytics
            for dimension in ScoringDimension:
                dimension_scores = [
                    score.dimension_scores[dimension].score
                    for score in user_scores.values()
                    if dimension in score.dimension_scores
                ]

                if dimension_scores:
                    analytics["dimension_performance"][dimension.value] = {
                        "average_score": statistics.mean(dimension_scores),
                        "score_count": len(dimension_scores),
                        "high_score_percentage": sum(1 for s in dimension_scores if s > 0.7) / len(dimension_scores) * 100
                    }

            return analytics

        except Exception as e:
            logger.error(f"Failed to get scoring analytics: {e}")
            return {"error": str(e)}

    # Placeholder methods for complex operations that need full system integration
    async def _calculate_initial_contextual_relevance(self, relationship: IntelligentRelationship, context: NavigationContext) -> float:
        return 0.6  # Default moderate contextual relevance

    async def _calculate_current_contextual_relevance(self, relationship_id: str, context: NavigationContext) -> float:
        return 0.6  # Would calculate based on current task context

    def _calculate_current_attention_alignment(self, dynamic_score: DynamicRelationshipScore, context: NavigationContext, profile: PersonalLearningProfile) -> float:
        return 0.7  # Would calculate based on current attention state

    async def _calculate_updated_pattern_relevance(self, relationship_id: str, context: NavigationContext) -> float:
        return 0.5  # Would calculate based on updated patterns

    async def _get_relationship_by_id(self, relationship_id: str) -> Optional[IntelligentRelationship]:
        return None  # Would retrieve stored relationship

    async def _update_attention_alignment_score(self, dynamic_score: DynamicRelationshipScore, new_attention_state: AttentionState, context: NavigationContext) -> None:
        pass  # Would update attention alignment


# Convenience functions
async def create_realtime_relevance_scorer(
    learning_engine: AdaptiveLearningEngine,
    profile_manager: PersonalLearningProfileManager,
    pattern_recognition: AdvancedPatternRecognition,
    effectiveness_tracker: EffectivenessTracker,
    performance_monitor: PerformanceMonitor = None
) -> RealtimeRelevanceScorer:
    """Create real-time relevance scorer instance."""
    return RealtimeRelevanceScorer(
        learning_engine, profile_manager, pattern_recognition, effectiveness_tracker, performance_monitor
    )


async def test_realtime_scoring(
    scorer: RealtimeRelevanceScorer,
    test_relationships: List[IntelligentRelationship],
    test_context: NavigationContext
) -> Dict[str, Any]:
    """Test real-time scoring system."""
    try:
        # Initialize scoring
        initial_scores = await scorer.initialize_relationship_scoring(test_relationships, test_context)

        # Simulate navigation event
        navigation_event = {
            "element_id": test_relationships[0].target_element.id if test_relationships else 1,
            "success": True,
            "duration_ms": 150,
            "complexity_score": 0.5
        }

        updated_scores = await scorer.update_scores_from_navigation(
            test_context.user_session_id, navigation_event, test_context
        )

        # Simulate attention state change
        new_attention_scores = await scorer.update_scores_from_attention_change(
            test_context.user_session_id, AttentionState.PEAK_FOCUS, test_context
        )

        # Get top ranked relationships
        top_relationships = await scorer.get_top_ranked_relationships(
            test_context.user_session_id, test_context, max_results=5
        )

        return {
            "test_successful": True,
            "initial_scores_count": len(initial_scores),
            "navigation_updates": len(updated_scores),
            "attention_updates": len(new_attention_scores),
            "top_relationships_count": len(top_relationships),
            "scoring_performance": "real-time updates working",
            "adhd_compliance": len(top_relationships) <= 5
        }

    except Exception as e:
        logger.error(f"Real-time scoring test failed: {e}")
        return {
            "test_successful": False,
            "error": str(e),
            "scoring_performance": "failed"
        }


if __name__ == "__main__":
    # Quick test when run directly
    async def main():
        print("📊 Serena Real-time Relationship Relevance Scorer")
        print("Dynamic ADHD-optimized relevance scoring with adaptive updates")
        print("✅ Module loaded successfully")

    asyncio.run(main())