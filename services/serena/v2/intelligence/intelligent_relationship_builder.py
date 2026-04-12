"""
Serena v2 Phase 2C: Intelligent Relationship Builder

Enhanced code relationship discovery with Tree-sitter integration, ConPort knowledge graph bridge,
and personalized ADHD-optimized relationship filtering and scoring.
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

# Phase 2 Intelligence Components
from .database import SerenaIntelligenceDatabase
from .graph_operations import SerenaGraphOperations, RelationshipType, CodeElementNode, RelationshipEdge
from .adaptive_learning import AdaptiveLearningEngine
from .learning_profile_manager import PersonalLearningProfileManager
from .pattern_recognition import AdvancedPatternRecognition, NavigationPatternType

# Layer 1 Components
from ..tree_sitter_analyzer import TreeSitterAnalyzer, StructuralElement, CodeComplexity
from ..performance_monitor import PerformanceMonitor

logger = logging.getLogger(__name__)


class RelationshipRelevance(str, Enum):
    """Relevance levels for ADHD-optimized relationship filtering."""
    HIGHLY_RELEVANT = "highly_relevant"      # >0.8 relevance, always show
    RELEVANT = "relevant"                    # 0.6-0.8 relevance, show in normal mode
    MODERATELY_RELEVANT = "moderately_relevant"  # 0.4-0.6 relevance, show in comprehensive mode
    LOW_RELEVANCE = "low_relevance"          # 0.2-0.4 relevance, only show if explicitly requested
    IRRELEVANT = "irrelevant"                # <0.2 relevance, never show


class RelationshipContext(str, Enum):
    """Context for relationship discovery."""
    CURRENT_TASK = "current_task"            # Related to immediate task
    RECENT_NAVIGATION = "recent_navigation"  # From recent navigation history
    SIMILAR_PATTERNS = "similar_patterns"    # From similar navigation patterns
    DECISION_CONTEXT = "decision_context"    # From ConPort decision links
    STRUCTURAL = "structural"                # From Tree-sitter structural analysis
    USAGE_PATTERNS = "usage_patterns"        # From usage frequency analysis


@dataclass
class IntelligentRelationship:
    """Enhanced relationship with personalized intelligence and ADHD optimization."""
    # Core relationship data
    source_element: CodeElementNode
    target_element: CodeElementNode
    relationship_type: RelationshipType
    structural_strength: float  # 0.0-1.0 from Tree-sitter analysis

    # Intelligence metadata
    relevance_score: float  # 0.0-1.0 personalized relevance
    relevance_level: RelationshipRelevance
    context_sources: List[RelationshipContext]
    cognitive_load_score: float  # 0.0-1.0 cognitive burden

    # ADHD optimization
    adhd_friendly: bool
    suggested_navigation_order: int  # 1-5 for ADHD ordering
    attention_requirements: str  # peak_focus, moderate_focus, etc.
    complexity_barrier: bool  # Whether complexity difference creates barrier

    # Personalization
    user_effectiveness_prediction: float  # Predicted effectiveness for this user
    pattern_based_confidence: float  # Confidence based on user patterns
    previous_usage_success: Optional[float] = None  # Past success with this relationship

    # Context integration
    conport_decision_links: List[str] = field(default_factory=list)  # Linked ConPort decisions
    recent_navigation_relevance: float = 0.0  # Relevance based on recent navigation
    structural_importance: float = 0.0  # Importance from Tree-sitter analysis

    # Metadata
    discovery_method: str = "combined"  # tree_sitter, conport, patterns, combined
    discovery_confidence: float = 0.0
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class RelationshipSuggestion:
    """Relationship suggestion with ADHD-optimized presentation."""
    relationship: IntelligentRelationship
    suggestion_reason: str
    adhd_guidance: str
    navigation_strategy: str
    estimated_cognitive_load: str  # "low", "medium", "high"
    break_recommendation: Optional[str] = None


@dataclass
class NavigationContext:
    """Context for intelligent relationship discovery."""
    current_element: CodeElementNode
    current_task_type: str  # exploration, debugging, implementation, etc.
    user_session_id: str
    workspace_path: str
    session_duration_minutes: float
    recent_navigation_history: List[int]  # Recent element IDs
    attention_state: str
    complexity_tolerance: float
    current_focus_goal: Optional[str] = None


class IntelligentRelationshipBuilder:
    """
    Intelligent relationship builder for ADHD-optimized code navigation.

    Features:
    - Enhanced Tree-sitter integration with personalized intelligence
    - ConPort knowledge graph bridge for decision context correlation
    - ADHD-optimized relationship filtering (max 5 suggestions rule)
    - Real-time relationship relevance scoring with cognitive load weighting
    - Personalized relationship recommendations based on learned patterns
    - Context-aware relationship discovery and ranking
    - Progressive disclosure of complex relationships
    - Integration with all Phase 2A and 2B components
    """

    def __init__(
        self,
        database: SerenaIntelligenceDatabase,
        graph_operations: SerenaGraphOperations,
        tree_sitter_analyzer: TreeSitterAnalyzer,
        learning_engine: AdaptiveLearningEngine,
        profile_manager: PersonalLearningProfileManager,
        pattern_recognition: AdvancedPatternRecognition,
        performance_monitor: PerformanceMonitor = None
    ):
        self.database = database
        self.graph_operations = graph_operations
        self.tree_sitter_analyzer = tree_sitter_analyzer
        self.learning_engine = learning_engine
        self.profile_manager = profile_manager
        self.pattern_recognition = pattern_recognition
        self.performance_monitor = performance_monitor or PerformanceMonitor()

        # ADHD optimization configuration
        self.max_suggestions = 5  # ADHD cognitive load limit
        self.relevance_threshold = 0.4  # Minimum relevance to show
        self.complexity_barrier_threshold = 0.5  # Complexity difference that creates barrier
        self.cognitive_load_weights = {
            "structural_complexity": 0.3,
            "relationship_distance": 0.2,
            "context_switching_cost": 0.3,
            "user_familiarity": 0.2
        }

        # Caching for performance
        self._relationship_cache: Dict[str, List[IntelligentRelationship]] = {}
        self._relevance_cache: Dict[str, float] = {}

    # Core Relationship Discovery

    async def discover_intelligent_relationships(
        self,
        context: NavigationContext,
        discovery_modes: Optional[List[RelationshipContext]] = None
    ) -> List[RelationshipSuggestion]:
        """Discover intelligent relationships with personalized ADHD optimization."""
        operation_id = self.performance_monitor.start_operation("discover_intelligent_relationships")

        try:
            if discovery_modes is None:
                discovery_modes = [
                    RelationshipContext.STRUCTURAL,
                    RelationshipContext.RECENT_NAVIGATION,
                    RelationshipContext.SIMILAR_PATTERNS,
                    RelationshipContext.DECISION_CONTEXT
                ]

            # Get user's learning profile for personalization
            profile = await self.profile_manager.get_or_create_profile(
                context.user_session_id, context.workspace_path
            )

            # Discover relationships from multiple sources
            all_relationships = []

            for mode in discovery_modes:
                mode_relationships = await self._discover_relationships_by_mode(context, mode)
                all_relationships.extend(mode_relationships)

            # Remove duplicates while preserving intelligence metadata
            unique_relationships = self._deduplicate_relationships(all_relationships)

            # Score and rank relationships with personalized intelligence
            scored_relationships = await self._score_relationships_with_intelligence(
                unique_relationships, context, profile
            )

            # Apply ADHD-optimized filtering
            filtered_relationships = await self._apply_adhd_filtering(
                scored_relationships, context, profile
            )

            # Generate suggestions with ADHD guidance
            suggestions = await self._generate_relationship_suggestions(
                filtered_relationships, context, profile
            )

            self.performance_monitor.end_operation(operation_id, success=True)

            logger.debug(f"🧠 Discovered {len(all_relationships)} relationships, "
                        f"filtered to {len(suggestions)} ADHD-optimized suggestions")

            return suggestions

        except Exception as e:
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"Failed to discover intelligent relationships: {e}")
            raise

    async def _discover_relationships_by_mode(
        self, context: NavigationContext, mode: RelationshipContext
    ) -> List[IntelligentRelationship]:
        """Discover relationships using a specific discovery mode."""
        try:
            if mode == RelationshipContext.STRUCTURAL:
                return await self._discover_structural_relationships(context)

            elif mode == RelationshipContext.RECENT_NAVIGATION:
                return await self._discover_navigation_based_relationships(context)

            elif mode == RelationshipContext.SIMILAR_PATTERNS:
                return await self._discover_pattern_based_relationships(context)

            elif mode == RelationshipContext.DECISION_CONTEXT:
                return await self._discover_conport_linked_relationships(context)

            elif mode == RelationshipContext.USAGE_PATTERNS:
                return await self._discover_usage_based_relationships(context)

            else:
                return []

        except Exception as e:
            logger.error(f"Failed to discover relationships for mode {mode}: {e}")
            return []

    async def _discover_structural_relationships(
        self, context: NavigationContext
    ) -> List[IntelligentRelationship]:
        """Discover relationships using enhanced Tree-sitter structural analysis."""
        try:
            current_element = context.current_element

            # Use Tree-sitter to analyze structural relationships
            if not await self.tree_sitter_analyzer.is_available():
                logger.debug("Tree-sitter not available, using fallback relationship discovery")
                return await self._fallback_structural_discovery(context)

            # Get Tree-sitter analysis for current element's file
            file_analysis = await self.tree_sitter_analyzer.analyze_file(
                current_element.file_path
            )

            relationships = []

            if file_analysis:
                # Find structural relationships to current element
                current_structural_element = self._find_structural_element(
                    file_analysis.elements, current_element
                )

                if current_structural_element:
                    # Discover relationships through Tree-sitter
                    structural_relationships = await self._extract_tree_sitter_relationships(
                        current_structural_element, file_analysis, context
                    )
                    relationships.extend(structural_relationships)

            return relationships

        except Exception as e:
            logger.error(f"Failed to discover structural relationships: {e}")
            return []

    async def _discover_navigation_based_relationships(
        self, context: NavigationContext
    ) -> List[IntelligentRelationship]:
        """Discover relationships based on recent navigation patterns."""
        try:
            relationships = []

            # Get recently navigated elements
            if context.recent_navigation_history:
                recent_element_ids = context.recent_navigation_history[-10:]  # Last 10 elements

                for element_id in recent_element_ids:
                    # Get existing relationships from Phase 2A graph
                    related_pairs = await self.graph_operations.get_related_elements(
                        element_id, mode=self.graph_operations.NavigationMode.EXPLORE
                    )

                    for related_element, relationship_edge in related_pairs:
                        # Check if related to current element
                        if related_element.id == context.current_element.id:
                            continue

                        intelligent_relationship = await self._create_intelligent_relationship(
                            context.current_element,
                            related_element,
                            relationship_edge,
                            [RelationshipContext.RECENT_NAVIGATION]
                        )

                        if intelligent_relationship:
                            relationships.append(intelligent_relationship)

            return relationships

        except Exception as e:
            logger.error(f"Failed to discover navigation-based relationships: {e}")
            return []

    async def _discover_pattern_based_relationships(
        self, context: NavigationContext
    ) -> List[IntelligentRelationship]:
        """Discover relationships based on learned navigation patterns."""
        try:
            relationships = []

            # Get user's successful navigation patterns
            profile = await self.profile_manager.get_or_create_profile(
                context.user_session_id, context.workspace_path
            )

            if profile.successful_patterns:
                # Get pattern recommendations for current context
                pattern_context = {
                    "context_type": context.current_task_type,
                    "current_complexity": context.current_element.complexity_score,
                    "session_duration_minutes": context.session_duration_minutes
                }

                pattern_recommendations = await self.pattern_recognition.get_pattern_recommendations(
                    pattern_context, context.user_session_id, context.workspace_path
                )

                # Use pattern insights to find relevant relationships
                approach = pattern_recommendations.get("suggested_navigation_approach", {})
                if approach.get("approach") in ["exploration", "debugging", "implementation"]:
                    # Find relationships that match successful patterns
                    pattern_relationships = await self._find_pattern_aligned_relationships(
                        context, approach.get("approach"), profile
                    )
                    relationships.extend(pattern_relationships)

            return relationships

        except Exception as e:
            logger.error(f"Failed to discover pattern-based relationships: {e}")
            return []

    async def _discover_conport_linked_relationships(
        self, context: NavigationContext
    ) -> List[IntelligentRelationship]:
        """Discover relationships through ConPort knowledge graph integration."""
        try:
            relationships = []

            # Query ConPort integration links for current element
            query = """
            SELECT * FROM conport_integration_links
            WHERE serena_element_id = $1
              AND conport_workspace = $2
              AND user_confirmed = TRUE
            ORDER BY link_strength DESC
            LIMIT 10
            """

            conport_links = await self.database.execute_query(
                query, (context.current_element.id, context.workspace_path)
            )

            for link in conport_links:
                # Find code elements related through ConPort decisions
                related_elements = await self._find_elements_linked_to_conport_item(
                    link['conport_item_type'],
                    link['conport_item_id'],
                    context.workspace_path
                )

                for related_element in related_elements:
                    if related_element.id == context.current_element.id:
                        continue

                    # Create intelligent relationship with ConPort context
                    intelligent_relationship = IntelligentRelationship(
                        source_element=context.current_element,
                        target_element=related_element,
                        relationship_type=RelationshipType.SIMILAR_TO,  # ConPort-based similarity
                        structural_strength=0.0,  # Not structurally based
                        relevance_score=link['link_strength'],
                        relevance_level=RelationshipRelevance.RELEVANT,
                        context_sources=[RelationshipContext.DECISION_CONTEXT],
                        cognitive_load_score=0.3,  # ConPort links are typically easy to understand
                        adhd_friendly=True,
                        suggested_navigation_order=1,
                        attention_requirements="moderate_focus",
                        complexity_barrier=False,
                        user_effectiveness_prediction=0.8,  # ConPort links tend to be effective
                        pattern_based_confidence=0.7,
                        conport_decision_links=[link['conport_item_id']],
                        discovery_method="conport_bridge",
                        discovery_confidence=link['link_strength']
                    )

                    relationships.append(intelligent_relationship)

            return relationships

        except Exception as e:
            logger.error(f"Failed to discover ConPort-linked relationships: {e}")
            return []

    # Relationship Scoring and Intelligence

    async def _score_relationships_with_intelligence(
        self,
        relationships: List[IntelligentRelationship],
        context: NavigationContext,
        profile
    ) -> List[IntelligentRelationship]:
        """Score relationships with personalized intelligence and ADHD optimization."""
        try:
            for relationship in relationships:
                # Calculate personalized relevance score
                relevance_score = await self._calculate_personalized_relevance(
                    relationship, context, profile
                )
                relationship.relevance_score = relevance_score
                relationship.relevance_level = self._categorize_relevance(relevance_score)

                # Calculate cognitive load with personal factors
                cognitive_load = await self._calculate_cognitive_load_with_personalization(
                    relationship, context, profile
                )
                relationship.cognitive_load_score = cognitive_load

                # Predict user effectiveness for this relationship
                effectiveness_prediction = await self._predict_user_effectiveness(
                    relationship, context, profile
                )
                relationship.user_effectiveness_prediction = effectiveness_prediction

                # Determine ADHD-friendliness
                relationship.adhd_friendly = self._assess_adhd_friendliness(
                    relationship, profile
                )

                # Suggest navigation order based on ADHD principles
                relationship.suggested_navigation_order = self._suggest_navigation_order(
                    relationship, context
                )

                # Determine attention requirements
                relationship.attention_requirements = self._determine_attention_requirements(
                    relationship, context
                )

            return relationships

        except Exception as e:
            logger.error(f"Failed to score relationships with intelligence: {e}")
            return relationships

    async def _calculate_personalized_relevance(
        self,
        relationship: IntelligentRelationship,
        context: NavigationContext,
        profile
    ) -> float:
        """Calculate personalized relevance score."""
        relevance_factors = []

        # Structural relevance (from Tree-sitter)
        structural_relevance = relationship.structural_strength
        relevance_factors.append(structural_relevance * 0.3)

        # Task context relevance
        task_relevance = await self._calculate_task_context_relevance(
            relationship, context
        )
        relevance_factors.append(task_relevance * 0.25)

        # Pattern-based relevance (from learned patterns)
        pattern_relevance = await self._calculate_pattern_based_relevance(
            relationship, context, profile
        )
        relevance_factors.append(pattern_relevance * 0.25)

        # Recent navigation relevance
        navigation_relevance = self._calculate_recent_navigation_relevance(
            relationship, context
        )
        relevance_factors.append(navigation_relevance * 0.1)

        # ConPort decision relevance
        conport_relevance = len(relationship.conport_decision_links) * 0.2
        relevance_factors.append(min(1.0, conport_relevance) * 0.1)

        return min(1.0, sum(relevance_factors))

    async def _calculate_cognitive_load_with_personalization(
        self,
        relationship: IntelligentRelationship,
        context: NavigationContext,
        profile
    ) -> float:
        """Calculate cognitive load with personal ADHD factors."""
        load_factors = []

        # Base complexity load
        source_complexity = relationship.source_element.complexity_score
        target_complexity = relationship.target_element.complexity_score
        complexity_load = (source_complexity + target_complexity) / 2
        load_factors.append(complexity_load * self.cognitive_load_weights["structural_complexity"])

        # Context switching load (if different files/types)
        if relationship.source_element.file_path != relationship.target_element.file_path:
            switch_load = 0.4  # File switching adds load
        elif relationship.source_element.element_type != relationship.target_element.element_type:
            switch_load = 0.2  # Type switching adds some load
        else:
            switch_load = 0.0

        load_factors.append(switch_load * self.cognitive_load_weights["context_switching_cost"])

        # Relationship distance load (how far apart structurally)
        distance_load = self._estimate_relationship_distance(relationship)
        load_factors.append(distance_load * self.cognitive_load_weights["relationship_distance"])

        # User familiarity load (lower load for familiar patterns)
        familiarity_load = 1.0 - min(1.0, relationship.target_element.access_frequency / 20.0)
        load_factors.append(familiarity_load * self.cognitive_load_weights["user_familiarity"])

        # Personalize based on user's complexity tolerance
        total_load = sum(load_factors)

        # Adjust based on user's current attention state
        if context.attention_state == "low_focus":
            total_load *= 1.3  # Higher perceived load when attention is low
        elif context.attention_state == "peak_focus":
            total_load *= 0.8  # Lower perceived load during peak focus

        return min(1.0, total_load)

    async def _predict_user_effectiveness(
        self,
        relationship: IntelligentRelationship,
        context: NavigationContext,
        profile
    ) -> float:
        """Predict how effective this relationship will be for the user."""
        effectiveness_factors = []

        # Base effectiveness from relationship strength
        base_effectiveness = relationship.structural_strength
        effectiveness_factors.append(base_effectiveness * 0.3)

        # Complexity compatibility with user preferences
        target_complexity = relationship.target_element.complexity_score
        user_comfort_zone = profile.optimal_complexity_range[1]

        if target_complexity <= user_comfort_zone:
            complexity_effectiveness = 1.0
        elif target_complexity <= user_comfort_zone + 0.2:  # Slightly outside comfort zone
            complexity_effectiveness = 0.7
        else:
            complexity_effectiveness = 0.4

        effectiveness_factors.append(complexity_effectiveness * 0.25)

        # Pattern compatibility (how well this fits user's successful patterns)
        pattern_effectiveness = await self._calculate_pattern_compatibility_effectiveness(
            relationship, context, profile
        )
        effectiveness_factors.append(pattern_effectiveness * 0.25)

        # Previous usage success (if any)
        if relationship.previous_usage_success is not None:
            effectiveness_factors.append(relationship.previous_usage_success * 0.2)
        else:
            effectiveness_factors.append(0.6 * 0.2)  # Default moderate effectiveness

        return min(1.0, sum(effectiveness_factors))

    # ADHD Optimization

    async def _apply_adhd_filtering(
        self,
        relationships: List[IntelligentRelationship],
        context: NavigationContext,
        profile
    ) -> List[IntelligentRelationship]:
        """Apply ADHD-optimized filtering to relationship suggestions."""
        # Sort by relevance and ADHD-friendliness
        sorted_relationships = sorted(
            relationships,
            key=lambda r: (
                r.relevance_score,
                1.0 if r.adhd_friendly else 0.5,
                -r.cognitive_load_score,  # Lower cognitive load = better
                r.user_effectiveness_prediction
            ),
            reverse=True
        )

        # Apply progressive filtering based on attention state
        if context.attention_state == "low_focus":
            # Very aggressive filtering for low focus
            filtered = [r for r in sorted_relationships
                       if r.adhd_friendly and r.cognitive_load_score <= 0.4]
            limit = min(3, len(filtered))
        elif context.attention_state == "fatigue":
            # Minimal suggestions when fatigued
            filtered = [r for r in sorted_relationships
                       if r.adhd_friendly and r.cognitive_load_score <= 0.3]
            limit = min(2, len(filtered))
        elif context.attention_state == "peak_focus":
            # More comprehensive during peak focus
            filtered = [r for r in sorted_relationships
                       if r.relevance_score >= 0.3]
            limit = self.max_suggestions
        else:  # moderate_focus
            # Standard ADHD filtering
            filtered = [r for r in sorted_relationships
                       if r.relevance_score >= self.relevance_threshold]
            limit = self.max_suggestions

        # Apply hard limit for cognitive load management
        return filtered[:limit]

    def _assess_adhd_friendliness(self, relationship: IntelligentRelationship, profile) -> bool:
        """Assess if relationship is ADHD-friendly for the user."""
        # Multiple criteria for ADHD-friendliness
        criteria_met = 0
        total_criteria = 5

        # Low cognitive load
        if relationship.cognitive_load_score <= 0.5:
            criteria_met += 1

        # Within user's complexity comfort zone
        if relationship.target_element.complexity_score <= profile.optimal_complexity_range[1]:
            criteria_met += 1

        # High confidence/relevance
        if relationship.relevance_score >= 0.6:
            criteria_met += 1

        # Low complexity barrier
        complexity_diff = abs(
            relationship.source_element.complexity_score -
            relationship.target_element.complexity_score
        )
        if complexity_diff <= self.complexity_barrier_threshold:
            criteria_met += 1
            relationship.complexity_barrier = False
        else:
            relationship.complexity_barrier = True

        # Structural or decision-based (more reliable than speculative)
        if RelationshipContext.STRUCTURAL in relationship.context_sources or \
           RelationshipContext.DECISION_CONTEXT in relationship.context_sources:
            criteria_met += 1

        # ADHD-friendly if meets majority of criteria
        return criteria_met >= 3

    def _suggest_navigation_order(
        self, relationship: IntelligentRelationship, context: NavigationContext
    ) -> int:
        """Suggest ADHD-optimized navigation order (1-5)."""
        # Start with relevance-based ordering
        if relationship.relevance_score >= 0.8:
            base_order = 1
        elif relationship.relevance_score >= 0.6:
            base_order = 2
        elif relationship.relevance_score >= 0.4:
            base_order = 3
        else:
            base_order = 4

        # Adjust based on cognitive load
        if relationship.cognitive_load_score > 0.7:
            base_order = min(5, base_order + 2)  # Push complex relationships later
        elif relationship.cognitive_load_score < 0.3:
            base_order = max(1, base_order - 1)  # Promote simple relationships

        # Adjust based on ADHD-friendliness
        if relationship.adhd_friendly:
            base_order = max(1, base_order - 1)

        # Consider attention requirements
        if (context.attention_state == "low_focus" and
            relationship.attention_requirements == "peak_focus"):
            base_order = 5  # Save for later

        return min(5, max(1, base_order))

    def _determine_attention_requirements(
        self, relationship: IntelligentRelationship, context: NavigationContext
    ) -> str:
        """Determine attention level required for this relationship."""
        if relationship.cognitive_load_score > 0.7 or relationship.complexity_barrier:
            return "peak_focus"
        elif relationship.cognitive_load_score > 0.4:
            return "moderate_focus"
        else:
            return "any_focus"

    # Suggestion Generation

    async def _generate_relationship_suggestions(
        self,
        relationships: List[IntelligentRelationship],
        context: NavigationContext,
        profile
    ) -> List[RelationshipSuggestion]:
        """Generate ADHD-optimized relationship suggestions with guidance."""
        suggestions = []

        for relationship in relationships:
            # Generate suggestion reason
            reason = self._generate_suggestion_reason(relationship, context)

            # Generate ADHD-specific guidance
            adhd_guidance = self._generate_adhd_guidance(relationship, context, profile)

            # Suggest navigation strategy
            nav_strategy = self._suggest_navigation_strategy(relationship, context)

            # Estimate cognitive load impact
            load_category = self._categorize_cognitive_load(relationship.cognitive_load_score)

            # Break recommendation if needed
            break_rec = None
            if relationship.cognitive_load_score > 0.7 and context.session_duration_minutes > 20:
                break_rec = "Consider a short break before exploring this complex relationship"

            suggestion = RelationshipSuggestion(
                relationship=relationship,
                suggestion_reason=reason,
                adhd_guidance=adhd_guidance,
                navigation_strategy=nav_strategy,
                estimated_cognitive_load=load_category,
                break_recommendation=break_rec
            )

            suggestions.append(suggestion)

        return suggestions

    def _generate_suggestion_reason(
        self, relationship: IntelligentRelationship, context: NavigationContext
    ) -> str:
        """Generate human-readable reason for suggesting this relationship."""
        reasons = []

        if RelationshipContext.STRUCTURAL in relationship.context_sources:
            reasons.append(f"structurally {relationship.relationship_type.value}")

        if RelationshipContext.DECISION_CONTEXT in relationship.context_sources:
            reasons.append("linked through project decisions")

        if RelationshipContext.RECENT_NAVIGATION in relationship.context_sources:
            reasons.append("from your recent navigation")

        if RelationshipContext.SIMILAR_PATTERNS in relationship.context_sources:
            reasons.append("matches your successful patterns")

        if relationship.target_element.access_frequency > 10:
            reasons.append("frequently accessed code")

        base_reason = f"Related to {relationship.target_element.element_name}"
        if reasons:
            return f"{base_reason} ({', '.join(reasons)})"
        else:
            return base_reason

    def _generate_adhd_guidance(
        self, relationship: IntelligentRelationship, context: NavigationContext, profile
    ) -> str:
        """Generate ADHD-specific guidance for the relationship."""
        guidance_parts = []

        # Complexity guidance
        target_complexity = relationship.target_element.complexity_score
        if target_complexity > profile.optimal_complexity_range[1]:
            guidance_parts.append("Complex area - best during focused time")
        elif target_complexity < 0.3:
            guidance_parts.append("Simple area - good anytime")

        # Cognitive load guidance
        if relationship.cognitive_load_score > 0.6:
            guidance_parts.append("Higher cognitive load - take your time")
        elif relationship.cognitive_load_score < 0.3:
            guidance_parts.append("Low cognitive load - easy to explore")

        # Context switching guidance
        if relationship.source_element.file_path != relationship.target_element.file_path:
            guidance_parts.append("Different file - prepare for context switch")

        # Pattern-based guidance
        if relationship.pattern_based_confidence > 0.8:
            guidance_parts.append("Matches your effective patterns")

        return " • ".join(guidance_parts) if guidance_parts else "Standard navigation"

    def _suggest_navigation_strategy(
        self, relationship: IntelligentRelationship, context: NavigationContext
    ) -> str:
        """Suggest navigation strategy for the relationship."""
        if relationship.complexity_barrier:
            return "Progressive: Start with overview, then dive into details"
        elif relationship.cognitive_load_score > 0.6:
            return "Focused: Requires concentrated attention"
        elif RelationshipContext.DECISION_CONTEXT in relationship.context_sources:
            return "Contextual: Review related decisions first"
        else:
            return "Direct: Navigate directly"

    def _categorize_cognitive_load(self, cognitive_load_score: float) -> str:
        """Categorize cognitive load for user-friendly display."""
        if cognitive_load_score <= 0.3:
            return "low"
        elif cognitive_load_score <= 0.6:
            return "medium"
        else:
            return "high"

    # Utility Methods

    def _categorize_relevance(self, relevance_score: float) -> RelationshipRelevance:
        """Categorize relevance score into ADHD-friendly levels."""
        if relevance_score >= 0.8:
            return RelationshipRelevance.HIGHLY_RELEVANT
        elif relevance_score >= 0.6:
            return RelationshipRelevance.RELEVANT
        elif relevance_score >= 0.4:
            return RelationshipRelevance.MODERATELY_RELEVANT
        elif relevance_score >= 0.2:
            return RelationshipRelevance.LOW_RELEVANCE
        else:
            return RelationshipRelevance.IRRELEVANT

    def _deduplicate_relationships(
        self, relationships: List[IntelligentRelationship]
    ) -> List[IntelligentRelationship]:
        """Remove duplicate relationships while preserving best intelligence metadata."""
        seen_pairs = set()
        unique_relationships = []

        for relationship in relationships:
            # Create key for deduplication
            pair_key = (
                relationship.source_element.id,
                relationship.target_element.id,
                relationship.relationship_type
            )

            if pair_key not in seen_pairs:
                seen_pairs.add(pair_key)
                unique_relationships.append(relationship)
            else:
                # Merge intelligence metadata from duplicate
                existing = next(r for r in unique_relationships
                              if (r.source_element.id, r.target_element.id, r.relationship_type) == pair_key)

                # Combine context sources
                existing.context_sources = list(set(existing.context_sources + relationship.context_sources))

                # Use higher relevance score
                if relationship.relevance_score > existing.relevance_score:
                    existing.relevance_score = relationship.relevance_score

                # Combine ConPort links
                existing.conport_decision_links.extend(relationship.conport_decision_links)

        return unique_relationships

    async def _find_elements_linked_to_conport_item(
        self, item_type: str, item_id: str, workspace_path: str
    ) -> List[CodeElementNode]:
        """Find code elements linked to a ConPort item."""
        try:
            query = """
            SELECT ce.* FROM code_elements ce
            JOIN conport_integration_links cil ON ce.id = cil.serena_element_id
            WHERE cil.conport_item_type = $1
              AND cil.conport_item_id = $2
              AND cil.conport_workspace = $3
              AND cil.link_strength > 0.5
            ORDER BY cil.link_strength DESC
            LIMIT 10
            """

            results = await self.database.execute_query(
                query, (item_type, item_id, workspace_path)
            )

            return [CodeElementNode(**row) for row in results]

        except Exception as e:
            logger.error(f"Failed to find ConPort-linked elements: {e}")
            return []

    def _find_structural_element(
        self, elements: List[StructuralElement], target_element: CodeElementNode
    ) -> Optional[StructuralElement]:
        """Find corresponding structural element from Tree-sitter analysis."""
        for element in elements:
            if (element.name == target_element.element_name and
                element.start_line == target_element.start_line):
                return element
        return None

    async def _extract_tree_sitter_relationships(
        self,
        structural_element: StructuralElement,
        file_analysis,
        context: NavigationContext
    ) -> List[IntelligentRelationship]:
        """Extract relationships from Tree-sitter analysis."""
        relationships = []

        try:
            # Get related elements from Tree-sitter metadata
            metadata = structural_element.metadata or {}

            # Example: function calls, class inheritance, imports
            if 'calls' in metadata:
                for called_function in metadata['calls']:
                    # Find corresponding code element
                    target_element = await self._find_code_element_by_tree_sitter_ref(
                        called_function, context.current_element.file_path
                    )

                    if target_element:
                        relationship = IntelligentRelationship(
                            source_element=context.current_element,
                            target_element=target_element,
                            relationship_type=RelationshipType.CALLS,
                            structural_strength=0.9,  # High confidence from Tree-sitter
                            relevance_score=0.0,  # Will be calculated later
                            relevance_level=RelationshipRelevance.RELEVANT,
                            context_sources=[RelationshipContext.STRUCTURAL],
                            cognitive_load_score=0.0,  # Will be calculated later
                            adhd_friendly=True,  # Will be assessed later
                            suggested_navigation_order=1,
                            attention_requirements="moderate_focus",
                            complexity_barrier=False,
                            user_effectiveness_prediction=0.0,  # Will be calculated
                            pattern_based_confidence=0.0,
                            structural_importance=0.8,
                            discovery_method="tree_sitter",
                            discovery_confidence=0.9
                        )
                        relationships.append(relationship)

            return relationships

        except Exception as e:
            logger.error(f"Failed to extract Tree-sitter relationships: {e}")
            return []

    async def _fallback_structural_discovery(
        self, context: NavigationContext
    ) -> List[IntelligentRelationship]:
        """Fallback structural relationship discovery when Tree-sitter unavailable."""
        try:
            # Use existing graph operations as fallback
            related_pairs = await self.graph_operations.get_related_elements(
                context.current_element.id,
                mode=self.graph_operations.NavigationMode.EXPLORE
            )

            relationships = []
            for related_element, relationship_edge in related_pairs:
                intelligent_relationship = await self._create_intelligent_relationship(
                    context.current_element,
                    related_element,
                    relationship_edge,
                    [RelationshipContext.STRUCTURAL]
                )
                if intelligent_relationship:
                    relationships.append(intelligent_relationship)

            return relationships

        except Exception as e:
            logger.error(f"Failed fallback structural discovery: {e}")
            return []

    async def _create_intelligent_relationship(
        self,
        source: CodeElementNode,
        target: CodeElementNode,
        edge: RelationshipEdge,
        context_sources: List[RelationshipContext]
    ) -> Optional[IntelligentRelationship]:
        """Create intelligent relationship from basic relationship data."""
        try:
            return IntelligentRelationship(
                source_element=source,
                target_element=target,
                relationship_type=RelationshipType(edge.relationship_type),
                structural_strength=edge.strength,
                relevance_score=0.0,  # Will be calculated
                relevance_level=RelationshipRelevance.RELEVANT,
                context_sources=context_sources,
                cognitive_load_score=edge.cognitive_load,
                adhd_friendly=edge.adhd_recommended,
                suggested_navigation_order=1,
                attention_requirements="moderate_focus",
                complexity_barrier=False,
                user_effectiveness_prediction=0.0,  # Will be calculated
                pattern_based_confidence=edge.confidence,
                discovery_method="graph_operations",
                discovery_confidence=edge.confidence
            )

        except Exception as e:
            logger.error(f"Failed to create intelligent relationship: {e}")
            return None

    # Placeholder implementations for complex calculations
    async def _calculate_task_context_relevance(
        self, relationship: IntelligentRelationship, context: NavigationContext
    ) -> float:
        """Calculate relevance based on current task context."""
        # Implementation would analyze task type and relationship alignment
        return 0.6  # Default moderate relevance

    async def _calculate_pattern_based_relevance(
        self, relationship: IntelligentRelationship, context: NavigationContext, profile
    ) -> float:
        """Calculate relevance based on learned navigation patterns."""
        # Implementation would match against successful patterns
        return 0.5  # Default moderate pattern relevance

    def _calculate_recent_navigation_relevance(
        self, relationship: IntelligentRelationship, context: NavigationContext
    ) -> float:
        """Calculate relevance based on recent navigation."""
        if relationship.target_element.id in context.recent_navigation_history:
            return 0.8  # High relevance if recently visited
        return 0.2

    def _estimate_relationship_distance(self, relationship: IntelligentRelationship) -> float:
        """Estimate structural distance between elements."""
        # Simple distance estimate based on file and line differences
        if relationship.source_element.file_path != relationship.target_element.file_path:
            return 0.8  # Different files = high distance

        line_diff = abs(relationship.source_element.start_line - relationship.target_element.start_line)
        return min(0.8, line_diff / 100.0)  # Normalize line distance

    async def _calculate_pattern_compatibility_effectiveness(
        self, relationship: IntelligentRelationship, context: NavigationContext, profile
    ) -> float:
        """Calculate effectiveness based on pattern compatibility."""
        # Implementation would match against user's successful patterns
        return 0.6  # Default moderate compatibility

    async def _find_pattern_aligned_relationships(
        self, context: NavigationContext, approach: str, profile
    ) -> List[IntelligentRelationship]:
        """Find relationships aligned with successful patterns."""
        # Implementation would query for relationships matching successful pattern characteristics
        return []

    async def _find_code_element_by_tree_sitter_ref(
        self, tree_sitter_ref: str, file_path: str
    ) -> Optional[CodeElementNode]:
        """Find code element by Tree-sitter reference."""
        # Implementation would resolve Tree-sitter references to code elements
        return None


# Convenience functions
async def create_intelligent_relationship_builder(
    database: SerenaIntelligenceDatabase,
    graph_operations: SerenaGraphOperations,
    tree_sitter_analyzer: TreeSitterAnalyzer,
    learning_engine: AdaptiveLearningEngine,
    profile_manager: PersonalLearningProfileManager,
    pattern_recognition: AdvancedPatternRecognition,
    performance_monitor: PerformanceMonitor = None
) -> IntelligentRelationshipBuilder:
    """Create intelligent relationship builder instance."""
    return IntelligentRelationshipBuilder(
        database, graph_operations, tree_sitter_analyzer, learning_engine,
        profile_manager, pattern_recognition, performance_monitor
    )


async def test_relationship_suggestions(
    relationship_builder: IntelligentRelationshipBuilder,
    test_context: NavigationContext
) -> Dict[str, Any]:
    """Test relationship suggestion quality and ADHD optimization."""
    try:
        # Discover relationships
        suggestions = await relationship_builder.discover_intelligent_relationships(test_context)

        # Analyze suggestion quality
        test_results = {
            "suggestions_generated": len(suggestions),
            "adhd_compliant": len(suggestions) <= 5,  # Max 5 suggestions rule
            "average_relevance": statistics.mean([s.relationship.relevance_score for s in suggestions]) if suggestions else 0.0,
            "adhd_friendly_percentage": sum(1 for s in suggestions if s.relationship.adhd_friendly) / max(len(suggestions), 1),
            "low_cognitive_load_percentage": sum(1 for s in suggestions if s.relationship.cognitive_load_score <= 0.5) / max(len(suggestions), 1),
            "suggestions_details": [
                {
                    "target": s.relationship.target_element.element_name,
                    "relevance": round(s.relationship.relevance_score, 2),
                    "cognitive_load": s.estimated_cognitive_load,
                    "adhd_friendly": s.relationship.adhd_friendly,
                    "reason": s.suggestion_reason
                }
                for s in suggestions
            ]
        }

        # Assess overall quality
        test_results["quality_rating"] = "excellent" if (
            test_results["adhd_compliant"] and
            test_results["average_relevance"] > 0.7 and
            test_results["adhd_friendly_percentage"] > 0.8
        ) else "good" if (
            test_results["adhd_compliant"] and
            test_results["average_relevance"] > 0.5
        ) else "needs_improvement"

        return test_results

    except Exception as e:
        logger.error(f"Failed to test relationship suggestions: {e}")
        return {"error": str(e), "quality_rating": "error"}


if __name__ == "__main__":
    # Quick test when run directly
    async def main():
        print("🔗 Serena Intelligent Relationship Builder")
        print("ADHD-optimized code relationships with personalized intelligence")
        print("✅ Module loaded successfully")

    asyncio.run(main())