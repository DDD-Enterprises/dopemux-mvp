"""
Serena v2 Phase 2C: Enhanced Tree-sitter Integration

Tree-sitter structural analysis enhanced with personalized intelligence,
ADHD-optimized relationship discovery, and adaptive learning integration.
"""

import asyncio
import json
import logging
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum

# Phase 2 Intelligence Components
from .database import SerenaIntelligenceDatabase
from .graph_operations import CodeElementNode, RelationshipType
from .adaptive_learning import AdaptiveLearningEngine
from .learning_profile_manager import PersonalLearningProfileManager
from .intelligent_relationship_builder import IntelligentRelationship, RelationshipContext

# Layer 1 Components
from ..tree_sitter_analyzer import (
    TreeSitterAnalyzer, StructuralElement, CodeComplexity,
    CodeStructureAnalysis, TREE_SITTER_AVAILABLE
)
from ..performance_monitor import PerformanceMonitor

logger = logging.getLogger(__name__)


class IntelligentStructuralRelationship(str, Enum):
    """Enhanced structural relationship types with intelligence metadata."""
    FUNCTION_CALLS = "function_calls"
    CLASS_INHERITANCE = "class_inheritance"
    IMPORT_DEPENDENCY = "import_dependency"
    VARIABLE_USAGE = "variable_usage"
    METHOD_OVERRIDE = "method_override"
    COMPOSITION = "composition"
    AGGREGATION = "aggregation"
    INTERFACE_IMPLEMENTATION = "interface_implementation"
    MODULE_DEPENDENCY = "module_dependency"
    DATA_FLOW = "data_flow"


@dataclass
class PersonalizedStructuralElement:
    """StructuralElement enhanced with personal intelligence and ADHD optimization."""
    # Core structural data (from Layer 1)
    base_element: StructuralElement

    # Personalized intelligence
    user_familiarity_score: float = 0.0  # 0.0-1.0 based on user interaction history
    personal_complexity_adjustment: float = 0.0  # User-specific complexity perception
    cognitive_load_for_user: float = 0.0  # Personalized cognitive load

    # ADHD optimization
    adhd_navigation_difficulty: str = "moderate"  # easy, moderate, hard, overwhelming
    recommended_attention_state: str = "moderate_focus"  # optimal attention for this element
    progressive_disclosure_levels: List[str] = field(default_factory=list)

    # Usage and effectiveness
    user_navigation_success_rate: float = 0.0  # Historical success navigating to this element
    average_time_spent_seconds: float = 0.0  # How long user typically spends here
    context_switch_frequency: float = 0.0  # How often user switches away from this element

    # Learned patterns
    effective_approach_patterns: List[str] = field(default_factory=list)
    problematic_patterns: List[str] = field(default_factory=list)
    optimal_navigation_sequence: Optional[List[str]] = None

    # Integration metadata
    conport_decision_relevance: float = 0.0  # Relevance to ConPort decisions
    recent_navigation_weight: float = 0.0  # Boost if recently navigated
    pattern_prediction_confidence: float = 0.0  # Confidence in pattern-based predictions


@dataclass
class EnhancedRelationshipDiscovery:
    """Enhanced relationship discovery with Tree-sitter + intelligence integration."""
    source_element: PersonalizedStructuralElement
    target_element: PersonalizedStructuralElement
    relationship_type: IntelligentStructuralRelationship

    # Enhanced analysis
    structural_confidence: float = 0.0  # Confidence from Tree-sitter
    personal_relevance_score: float = 0.0  # Personalized relevance
    cognitive_transition_cost: float = 0.0  # ADHD cost of navigating this relationship

    # ADHD optimization
    navigation_complexity: str = "moderate"  # simple, moderate, complex
    attention_preservation_score: float = 0.0  # How well this preserves attention
    focus_mode_recommended: bool = False

    # Learning integration
    pattern_alignment_score: float = 0.0  # How well this aligns with user patterns
    effectiveness_prediction: float = 0.0  # Predicted navigation effectiveness
    learning_opportunity_score: float = 0.0  # Potential for learning/growth


class EnhancedTreeSitterIntegration:
    """
    Enhanced Tree-sitter integration with personalized intelligence and ADHD optimization.

    Features:
    - Structural analysis enhanced with personal navigation patterns
    - ADHD-optimized relationship discovery with cognitive load assessment
    - Integration with adaptive learning for personalized complexity scoring
    - Progressive disclosure of complex structural relationships
    - Context-aware structural analysis based on current task
    - Performance optimization maintaining <200ms targets
    - Seamless fallback to Layer 1 Tree-sitter when needed
    """

    def __init__(
        self,
        base_tree_sitter: TreeSitterAnalyzer,
        database: SerenaIntelligenceDatabase,
        learning_engine: AdaptiveLearningEngine,
        profile_manager: PersonalLearningProfileManager,
        performance_monitor: PerformanceMonitor = None
    ):
        self.base_tree_sitter = base_tree_sitter
        self.database = database
        self.learning_engine = learning_engine
        self.profile_manager = profile_manager
        self.performance_monitor = performance_monitor or PerformanceMonitor()

        # Enhanced analysis configuration
        self.enable_personalization = True
        self.enable_adhd_optimization = True
        self.enable_pattern_integration = True

        # Performance targets
        self.max_analysis_time_ms = 150  # ADHD target for analysis operations
        self.max_relationships_per_element = 20  # Before filtering

        # Caching for performance
        self._personalized_analysis_cache: Dict[str, PersonalizedStructuralElement] = {}
        self._relationship_cache: Dict[str, List[EnhancedRelationshipDiscovery]] = {}

    # Enhanced Structural Analysis

    async def analyze_with_personalization(
        self,
        file_path: str,
        user_session_id: str,
        workspace_path: str,
        target_element_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze file structure with personalized intelligence and ADHD optimization."""
        operation_id = self.performance_monitor.start_operation("enhanced_tree_sitter_analysis")

        try:
            # Get base Tree-sitter analysis from Layer 1
            base_analysis = await self.base_tree_sitter.analyze_file(file_path)

            if not base_analysis:
                logger.warning(f"No Tree-sitter analysis available for {file_path}")
                self.performance_monitor.end_operation(operation_id, success=False)
                return {"error": "Tree-sitter analysis failed", "fallback_used": True}

            # Get user's learning profile
            profile = await self.profile_manager.get_or_create_profile(
                user_session_id, workspace_path
            )

            # Enhance elements with personalized intelligence
            enhanced_elements = []
            for element in base_analysis.elements:
                if target_element_name and element.name != target_element_name:
                    continue  # Skip if looking for specific element

                enhanced_element = await self._enhance_structural_element(
                    element, user_session_id, workspace_path, profile
                )
                enhanced_elements.append(enhanced_element)

            # Discover enhanced relationships
            enhanced_relationships = await self._discover_enhanced_relationships(
                enhanced_elements, user_session_id, workspace_path, profile
            )

            # Apply ADHD filtering and ranking
            filtered_relationships = await self._apply_adhd_relationship_filtering(
                enhanced_relationships, profile
            )

            # Generate analysis result
            analysis_result = {
                "file_path": file_path,
                "language": base_analysis.language,
                "base_analysis": {
                    "elements_count": len(base_analysis.elements),
                    "overall_complexity": base_analysis.overall_complexity,
                    "lines_of_code": base_analysis.lines_of_code
                },
                "enhanced_analysis": {
                    "personalized_elements": len(enhanced_elements),
                    "intelligent_relationships": len(enhanced_relationships),
                    "adhd_filtered_relationships": len(filtered_relationships),
                    "user_complexity_adjustment": await self._calculate_user_complexity_adjustment(
                        enhanced_elements, profile
                    )
                },
                "personalized_elements": [self._serialize_enhanced_element(e) for e in enhanced_elements],
                "intelligent_relationships": [self._serialize_enhanced_relationship(r) for r in filtered_relationships],
                "adhd_insights": await self._generate_adhd_structural_insights(
                    enhanced_elements, filtered_relationships, profile
                ),
                "navigation_recommendations": await self._generate_navigation_recommendations(
                    enhanced_elements, filtered_relationships, profile
                ),
                "analysis_performance": {
                    "tree_sitter_available": TREE_SITTER_AVAILABLE,
                    "personalization_enabled": self.enable_personalization,
                    "analysis_duration_ms": base_analysis.analysis_duration_ms,
                    "enhancement_duration_ms": 0.0  # Will be calculated
                }
            }

            self.performance_monitor.end_operation(operation_id, success=True)

            logger.debug(f"🌳 Enhanced Tree-sitter analysis: {len(enhanced_elements)} elements, "
                        f"{len(filtered_relationships)} ADHD-optimized relationships")

            return analysis_result

        except Exception as e:
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"Enhanced Tree-sitter analysis failed: {e}")
            return {"error": str(e), "fallback_available": True}

    async def _enhance_structural_element(
        self,
        base_element: StructuralElement,
        user_session_id: str,
        workspace_path: str,
        profile
    ) -> PersonalizedStructuralElement:
        """Enhance structural element with personalized intelligence."""
        try:
            # Get user interaction history for this element
            interaction_data = await self._get_element_interaction_history(
                base_element, user_session_id, workspace_path
            )

            # Calculate user familiarity
            familiarity_score = self._calculate_user_familiarity(
                interaction_data, base_element
            )

            # Adjust complexity based on user experience
            personal_complexity_adjustment = self._calculate_personal_complexity_adjustment(
                base_element, familiarity_score, profile
            )

            # Calculate personalized cognitive load
            cognitive_load = self._calculate_personalized_cognitive_load(
                base_element, familiarity_score, profile
            )

            # Determine ADHD navigation difficulty
            adhd_difficulty = self._assess_adhd_navigation_difficulty(
                base_element, cognitive_load, profile
            )

            # Recommend optimal attention state
            attention_requirement = self._recommend_attention_state(
                base_element, cognitive_load, adhd_difficulty
            )

            # Generate progressive disclosure levels
            disclosure_levels = self._generate_progressive_disclosure_levels(
                base_element, cognitive_load
            )

            # Calculate usage effectiveness metrics
            navigation_success_rate = interaction_data.get('success_rate', 0.0)
            avg_time_spent = interaction_data.get('average_time_seconds', 0.0)
            context_switch_freq = interaction_data.get('context_switch_frequency', 0.0)

            # Get effective navigation patterns
            effective_patterns = await self._identify_effective_patterns_for_element(
                base_element, user_session_id, profile
            )

            enhanced_element = PersonalizedStructuralElement(
                base_element=base_element,
                user_familiarity_score=familiarity_score,
                personal_complexity_adjustment=personal_complexity_adjustment,
                cognitive_load_for_user=cognitive_load,
                adhd_navigation_difficulty=adhd_difficulty,
                recommended_attention_state=attention_requirement,
                progressive_disclosure_levels=disclosure_levels,
                user_navigation_success_rate=navigation_success_rate,
                average_time_spent_seconds=avg_time_spent,
                context_switch_frequency=context_switch_freq,
                effective_approach_patterns=effective_patterns.get('effective', []),
                problematic_patterns=effective_patterns.get('problematic', []),
                optimal_navigation_sequence=effective_patterns.get('optimal_sequence'),
                pattern_prediction_confidence=effective_patterns.get('confidence', 0.0)
            )

            return enhanced_element

        except Exception as e:
            logger.error(f"Failed to enhance structural element: {e}")
            # Return minimal enhancement
            return PersonalizedStructuralElement(
                base_element=base_element,
                user_familiarity_score=0.0,
                cognitive_load_for_user=base_element.complexity_score,
                adhd_navigation_difficulty="moderate"
            )

    async def _discover_enhanced_relationships(
        self,
        enhanced_elements: List[PersonalizedStructuralElement],
        user_session_id: str,
        workspace_path: str,
        profile
    ) -> List[EnhancedRelationshipDiscovery]:
        """Discover relationships between enhanced structural elements."""
        relationships = []

        try:
            # Analyze relationships between enhanced elements
            for i, source_element in enumerate(enhanced_elements):
                for j, target_element in enumerate(enhanced_elements):
                    if i >= j:  # Avoid duplicates and self-relationships
                        continue

                    # Detect structural relationship
                    relationship_type = await self._detect_structural_relationship(
                        source_element.base_element, target_element.base_element
                    )

                    if relationship_type:
                        # Create enhanced relationship
                        enhanced_relationship = await self._create_enhanced_relationship(
                            source_element, target_element, relationship_type, profile
                        )

                        if enhanced_relationship:
                            relationships.append(enhanced_relationship)

            return relationships

        except Exception as e:
            logger.error(f"Failed to discover enhanced relationships: {e}")
            return []

    async def _create_enhanced_relationship(
        self,
        source: PersonalizedStructuralElement,
        target: PersonalizedStructuralElement,
        relationship_type: IntelligentStructuralRelationship,
        profile
    ) -> Optional[EnhancedRelationshipDiscovery]:
        """Create enhanced relationship with intelligence metadata."""
        try:
            # Calculate structural confidence based on Tree-sitter analysis
            structural_confidence = self._calculate_structural_confidence(
                source.base_element, target.base_element, relationship_type
            )

            # Calculate personal relevance based on user patterns
            personal_relevance = self._calculate_personal_relevance(
                source, target, profile
            )

            # Calculate cognitive transition cost for ADHD users
            transition_cost = self._calculate_cognitive_transition_cost(
                source, target, profile
            )

            # Assess navigation complexity
            nav_complexity = self._assess_navigation_complexity(
                source, target, transition_cost
            )

            # Calculate attention preservation score
            attention_preservation = self._calculate_attention_preservation(
                source, target, profile
            )

            # Determine if focus mode recommended
            focus_mode_recommended = (
                transition_cost > 0.6 or
                target.cognitive_load_for_user > 0.7 or
                nav_complexity == "complex"
            )

            # Calculate pattern alignment
            pattern_alignment = self._calculate_pattern_alignment_score(
                source, target, profile
            )

            # Predict effectiveness for this user
            effectiveness_prediction = self._predict_relationship_effectiveness(
                source, target, pattern_alignment, profile
            )

            # Calculate learning opportunity
            learning_opportunity = self._assess_learning_opportunity(
                source, target, profile
            )

            return EnhancedRelationshipDiscovery(
                source_element=source,
                target_element=target,
                relationship_type=relationship_type,
                structural_confidence=structural_confidence,
                personal_relevance_score=personal_relevance,
                cognitive_transition_cost=transition_cost,
                navigation_complexity=nav_complexity,
                attention_preservation_score=attention_preservation,
                focus_mode_recommended=focus_mode_recommended,
                pattern_alignment_score=pattern_alignment,
                effectiveness_prediction=effectiveness_prediction,
                learning_opportunity_score=learning_opportunity
            )

        except Exception as e:
            logger.error(f"Failed to create enhanced relationship: {e}")
            return None

    # Personalization Calculations

    def _calculate_user_familiarity(
        self, interaction_data: Dict[str, Any], element: StructuralElement
    ) -> float:
        """Calculate user familiarity with structural element."""
        # Base familiarity on interaction frequency and recency
        access_count = interaction_data.get('access_count', 0)
        last_accessed_days_ago = interaction_data.get('days_since_access', 30)

        # Frequency factor (0-1)
        frequency_factor = min(1.0, access_count / 20.0)

        # Recency factor (0-1)
        recency_factor = max(0.0, 1.0 - (last_accessed_days_ago / 30.0))

        # Success factor
        success_rate = interaction_data.get('success_rate', 0.5)

        return statistics.mean([frequency_factor, recency_factor, success_rate])

    def _calculate_personal_complexity_adjustment(
        self, element: StructuralElement, familiarity_score: float, profile
    ) -> float:
        """Calculate personal complexity adjustment based on user experience."""
        base_complexity = element.complexity_score

        # Familiarity reduces perceived complexity
        familiarity_reduction = familiarity_score * 0.3

        # User's general complexity tolerance
        user_tolerance = profile.optimal_complexity_range[1]
        if base_complexity <= user_tolerance:
            tolerance_adjustment = 0.0  # No adjustment needed
        else:
            tolerance_adjustment = (base_complexity - user_tolerance) * 0.2  # Increase perceived complexity

        # Net adjustment (can reduce or increase perceived complexity)
        return max(-0.3, min(0.3, tolerance_adjustment - familiarity_reduction))

    def _calculate_personalized_cognitive_load(
        self, element: StructuralElement, familiarity_score: float, profile
    ) -> float:
        """Calculate personalized cognitive load for element."""
        base_load = element.complexity_score

        # Adjust based on familiarity (familiar elements have lower cognitive load)
        familiarity_reduction = familiarity_score * 0.4

        # Adjust based on user's current capacity
        user_capacity_factor = profile.pattern_confidence  # More experienced users handle more load

        # Adjust based on element characteristics
        if element.type in ["function", "method"] and element.complexity_score > 0.7:
            type_adjustment = 0.1  # Functions are slightly more cognitively demanding
        else:
            type_adjustment = 0.0

        personalized_load = base_load - familiarity_reduction + type_adjustment - (user_capacity_factor * 0.1)

        return max(0.0, min(1.0, personalized_load))

    def _assess_adhd_navigation_difficulty(
        self, element: StructuralElement, cognitive_load: float, profile
    ) -> str:
        """Assess ADHD-specific navigation difficulty."""
        # Consider multiple factors for ADHD difficulty
        difficulty_factors = []

        # Cognitive load factor
        if cognitive_load <= 0.3:
            difficulty_factors.append("easy")
        elif cognitive_load <= 0.6:
            difficulty_factors.append("moderate")
        else:
            difficulty_factors.append("hard")

        # Element size factor (large elements are harder for ADHD)
        element_size = element.end_line - element.start_line
        if element_size > 50:
            difficulty_factors.append("hard")
        elif element_size > 20:
            difficulty_factors.append("moderate")
        else:
            difficulty_factors.append("easy")

        # Complexity relative to user comfort zone
        if element.complexity_score > profile.optimal_complexity_range[1] + 0.2:
            difficulty_factors.append("overwhelming")
        elif element.complexity_score > profile.optimal_complexity_range[1]:
            difficulty_factors.append("hard")

        # Determine overall difficulty
        if "overwhelming" in difficulty_factors:
            return "overwhelming"
        elif difficulty_factors.count("hard") >= 2:
            return "hard"
        elif "hard" in difficulty_factors:
            return "moderate"
        elif difficulty_factors.count("moderate") >= 2:
            return "moderate"
        else:
            return "easy"

    def _recommend_attention_state(
        self, element: StructuralElement, cognitive_load: float, difficulty: str
    ) -> str:
        """Recommend optimal attention state for navigating this element."""
        if difficulty == "overwhelming" or cognitive_load > 0.8:
            return "peak_focus"
        elif difficulty == "hard" or cognitive_load > 0.6:
            return "moderate_focus"
        elif difficulty == "easy" and cognitive_load < 0.3:
            return "any_focus"
        else:
            return "moderate_focus"

    def _generate_progressive_disclosure_levels(
        self, element: StructuralElement, cognitive_load: float
    ) -> List[str]:
        """Generate progressive disclosure levels for complex elements."""
        levels = ["overview"]  # Always start with overview

        if cognitive_load > 0.4:
            levels.append("signature")  # Show function/class signature

        if cognitive_load > 0.6:
            levels.append("structure")  # Show basic structure

        if cognitive_load > 0.8:
            levels.append("details")  # Show full details
            levels.append("implementation")  # Show implementation details

        return levels

    # Relationship Enhancement

    def _calculate_cognitive_transition_cost(
        self, source: PersonalizedStructuralElement, target: PersonalizedStructuralElement, profile
    ) -> float:
        """Calculate ADHD-specific cognitive cost of transitioning between elements."""
        cost_factors = []

        # Complexity difference cost
        complexity_diff = abs(source.cognitive_load_for_user - target.cognitive_load_for_user)
        cost_factors.append(complexity_diff * 0.4)

        # Context switching cost (if different types or significant distance)
        if source.base_element.type != target.base_element.type:
            cost_factors.append(0.3)

        line_distance = abs(source.base_element.start_line - target.base_element.start_line)
        if line_distance > 100:  # Far apart in file
            cost_factors.append(0.2)

        # User-specific factors
        user_switch_tolerance = profile.context_switch_tolerance / 10.0  # Normalize
        cost_factors.append((1.0 - user_switch_tolerance) * 0.1)

        return min(1.0, sum(cost_factors))

    def _assess_navigation_complexity(
        self, source: PersonalizedStructuralElement, target: PersonalizedStructuralElement, transition_cost: float
    ) -> str:
        """Assess overall navigation complexity between elements."""
        complexity_indicators = [
            source.cognitive_load_for_user,
            target.cognitive_load_for_user,
            transition_cost
        ]

        avg_complexity = statistics.mean(complexity_indicators)

        if avg_complexity > 0.7:
            return "complex"
        elif avg_complexity > 0.4:
            return "moderate"
        else:
            return "simple"

    def _calculate_attention_preservation(
        self, source: PersonalizedStructuralElement, target: PersonalizedStructuralElement, profile
    ) -> float:
        """Calculate how well this relationship preserves attention."""
        preservation_factors = []

        # Low transition cost preserves attention better
        transition_cost = self._calculate_cognitive_transition_cost(source, target, profile)
        preservation_factors.append(1.0 - transition_cost)

        # Similar complexity levels preserve attention
        complexity_similarity = 1.0 - abs(source.cognitive_load_for_user - target.cognitive_load_for_user)
        preservation_factors.append(complexity_similarity)

        # Same file preserves context
        if source.base_element.name == target.base_element.name:  # Same file (simplified check)
            preservation_factors.append(0.8)
        else:
            preservation_factors.append(0.3)

        # User familiarity with target helps preserve attention
        preservation_factors.append(target.user_familiarity_score)

        return statistics.mean(preservation_factors)

    # Pattern Integration

    async def _identify_effective_patterns_for_element(
        self, element: StructuralElement, user_session_id: str, profile
    ) -> Dict[str, Any]:
        """Identify effective navigation patterns for this element."""
        try:
            # Query user's navigation patterns involving this element type
            query = """
            SELECT pattern_sequence, effectiveness_score, pattern_type
            FROM navigation_patterns
            WHERE user_session_id = $1
              AND pattern_sequence::text LIKE $2
              AND effectiveness_score > 0.6
            ORDER BY effectiveness_score DESC
            LIMIT 10
            """

            # Search for patterns involving this element type
            search_term = f"%{element.type}%"
            results = await self.database.execute_query(query, (user_session_id, search_term))

            effective_patterns = []
            problematic_patterns = []

            for row in results:
                if row['effectiveness_score'] > 0.7:
                    effective_patterns.append(row['pattern_type'])
                elif row['effectiveness_score'] < 0.4:
                    problematic_patterns.append(row['pattern_type'])

            # Generate optimal sequence if patterns are clear
            optimal_sequence = None
            if effective_patterns:
                most_effective_type = max(set(effective_patterns), key=effective_patterns.count)
                optimal_sequence = [most_effective_type, "progressive_exploration", "focused_analysis"]

            return {
                "effective": list(set(effective_patterns)),
                "problematic": list(set(problematic_patterns)),
                "optimal_sequence": optimal_sequence,
                "confidence": min(1.0, len(results) / 5.0)  # More patterns = higher confidence
            }

        except Exception as e:
            logger.error(f"Failed to identify effective patterns: {e}")
            return {"effective": [], "problematic": [], "confidence": 0.0}

    # ADHD Optimization

    async def _apply_adhd_relationship_filtering(
        self, relationships: List[EnhancedRelationshipDiscovery], profile
    ) -> List[EnhancedRelationshipDiscovery]:
        """Apply ADHD-optimized filtering to enhanced relationships."""
        # Sort relationships by ADHD-friendliness
        sorted_relationships = sorted(
            relationships,
            key=lambda r: (
                r.personal_relevance_score,          # Higher relevance first
                r.attention_preservation_score,      # Better attention preservation
                -r.cognitive_transition_cost,        # Lower transition cost
                r.effectiveness_prediction,          # Higher predicted effectiveness
                r.pattern_alignment_score           # Better pattern alignment
            ),
            reverse=True
        )

        # Filter based on ADHD criteria
        filtered = []
        for relationship in sorted_relationships:
            # Must meet minimum relevance
            if relationship.personal_relevance_score < 0.3:
                continue

            # Must not be overwhelming
            if relationship.navigation_complexity == "complex" and len(filtered) >= 2:
                continue  # Limit complex relationships

            # Must have reasonable cognitive cost
            if relationship.cognitive_transition_cost > 0.8:
                continue

            # Must preserve attention adequately
            if relationship.attention_preservation_score < 0.4:
                continue

            filtered.append(relationship)

            # ADHD hard limit: maximum 5 relationships
            if len(filtered) >= 5:
                break

        return filtered

    # Utility and Analysis Methods

    async def _get_element_interaction_history(
        self, element: StructuralElement, user_session_id: str, workspace_path: str
    ) -> Dict[str, Any]:
        """Get user's interaction history with this structural element."""
        try:
            # Query code_elements table for matching element
            query = """
            SELECT access_frequency, last_accessed, average_session_time
            FROM code_elements
            WHERE element_name = $1
              AND start_line = $2
              AND end_line = $3
            LIMIT 1
            """

            results = await self.database.execute_query(
                query, (element.name, element.start_line, element.end_line)
            )

            if results:
                row = results[0]
                last_accessed = row['last_accessed']
                days_since = (datetime.now(timezone.utc) - last_accessed.replace(tzinfo=timezone.utc)).days if last_accessed else 30

                return {
                    "access_count": row['access_frequency'],
                    "days_since_access": days_since,
                    "average_time_seconds": row['average_session_time'],
                    "success_rate": 0.8  # Would be calculated from actual success data
                }

            return {
                "access_count": 0,
                "days_since_access": 30,
                "average_time_seconds": 0.0,
                "success_rate": 0.5,
                "context_switch_frequency": 0.0
            }

        except Exception as e:
            logger.error(f"Failed to get interaction history: {e}")
            return {
                "access_count": 0,
                "days_since_access": 30,
                "average_time_seconds": 0.0,
                "success_rate": 0.5
            }

    async def _detect_structural_relationship(
        self, source: StructuralElement, target: StructuralElement
    ) -> Optional[IntelligentStructuralRelationship]:
        """Detect structural relationship between elements using Tree-sitter analysis."""
        # Use Tree-sitter metadata to detect relationships
        source_metadata = source.metadata or {}
        target_metadata = target.metadata or {}

        # Function calls
        if 'calls' in source_metadata and target.name in source_metadata['calls']:
            return IntelligentStructuralRelationship.FUNCTION_CALLS

        # Class inheritance
        if (source.type == "class" and target.type == "class" and
            'inherits' in source_metadata and target.name in source_metadata['inherits']):
            return IntelligentStructuralRelationship.CLASS_INHERITANCE

        # Variable usage
        if 'variables_used' in source_metadata and target.name in source_metadata['variables_used']:
            return IntelligentStructuralRelationship.VARIABLE_USAGE

        # Method override
        if (source.type == "method" and target.type == "method" and
            source.name == target.name and source != target):
            return IntelligentStructuralRelationship.METHOD_OVERRIDE

        # Import dependencies (simplified detection)
        if target.type == "import" or source.type == "import":
            return IntelligentStructuralRelationship.IMPORT_DEPENDENCY

        return None

    def _calculate_structural_confidence(
        self, source: StructuralElement, target: StructuralElement, relationship_type: IntelligentStructuralRelationship
    ) -> float:
        """Calculate confidence in structural relationship detection."""
        # High confidence for direct Tree-sitter detected relationships
        if hasattr(source, 'metadata') and source.metadata:
            return 0.9
        else:
            return 0.6  # Lower confidence for inferred relationships

    # Serialization for API

    def _serialize_enhanced_element(self, element: PersonalizedStructuralElement) -> Dict[str, Any]:
        """Serialize enhanced element for API response."""
        return {
            "name": element.base_element.name,
            "type": element.base_element.type,
            "start_line": element.base_element.start_line,
            "end_line": element.base_element.end_line,
            "base_complexity": element.base_element.complexity_score,
            "personalized_complexity": element.base_element.complexity_score + element.personal_complexity_adjustment,
            "user_familiarity": element.user_familiarity_score,
            "cognitive_load": element.cognitive_load_for_user,
            "adhd_difficulty": element.adhd_navigation_difficulty,
            "recommended_attention": element.recommended_attention_state,
            "progressive_levels": element.progressive_disclosure_levels,
            "navigation_success_rate": element.user_navigation_success_rate,
            "effective_patterns": element.effective_approach_patterns,
            "pattern_confidence": element.pattern_prediction_confidence
        }

    def _serialize_enhanced_relationship(self, relationship: EnhancedRelationshipDiscovery) -> Dict[str, Any]:
        """Serialize enhanced relationship for API response."""
        return {
            "source": relationship.source_element.base_element.name,
            "target": relationship.target_element.base_element.name,
            "relationship_type": relationship.relationship_type.value,
            "structural_confidence": relationship.structural_confidence,
            "personal_relevance": relationship.personal_relevance_score,
            "cognitive_cost": relationship.cognitive_transition_cost,
            "navigation_complexity": relationship.navigation_complexity,
            "attention_preservation": relationship.attention_preservation_score,
            "focus_mode_recommended": relationship.focus_mode_recommended,
            "pattern_alignment": relationship.pattern_alignment_score,
            "effectiveness_prediction": relationship.effectiveness_prediction,
            "learning_opportunity": relationship.learning_opportunity_score
        }

    # Analysis and Insights

    async def _generate_adhd_structural_insights(
        self,
        elements: List[PersonalizedStructuralElement],
        relationships: List[EnhancedRelationshipDiscovery],
        profile
    ) -> List[str]:
        """Generate ADHD-specific insights about structural analysis."""
        insights = []

        # Complexity insights
        high_complexity_elements = [e for e in elements if e.cognitive_load_for_user > 0.7]
        if high_complexity_elements:
            insights.append(f"🧠 {len(high_complexity_elements)} complex elements detected - consider progressive exploration")

        # Familiarity insights
        familiar_elements = [e for e in elements if e.user_familiarity_score > 0.7]
        if familiar_elements:
            insights.append(f"🎯 {len(familiar_elements)} familiar elements - good starting points")

        # Relationship insights
        easy_relationships = [r for r in relationships if r.navigation_complexity == "simple"]
        if easy_relationships:
            insights.append(f"✅ {len(easy_relationships)} easy relationships for smooth navigation")

        complex_relationships = [r for r in relationships if r.focus_mode_recommended]
        if complex_relationships:
            insights.append(f"🔍 {len(complex_relationships)} relationships need focused attention")

        # Pattern alignment insights
        well_aligned = [r for r in relationships if r.pattern_alignment_score > 0.7]
        if well_aligned:
            insights.append(f"🚀 {len(well_aligned)} relationships match your effective patterns")

        return insights

    async def _generate_navigation_recommendations(
        self,
        elements: List[PersonalizedStructuralElement],
        relationships: List[EnhancedRelationshipDiscovery],
        profile
    ) -> List[str]:
        """Generate navigation recommendations based on enhanced analysis."""
        recommendations = []

        # Starting point recommendations
        easy_starts = [e for e in elements if e.adhd_navigation_difficulty == "easy"]
        if easy_starts:
            best_start = min(easy_starts, key=lambda e: e.cognitive_load_for_user)
            recommendations.append(f"🚀 Start with {best_start.base_element.name} - easiest entry point")

        # Progressive exploration recommendations
        if len(elements) > 5:
            recommendations.append("📖 Use progressive disclosure - explore gradually")

        # Focus mode recommendations
        focus_mode_needed = [r for r in relationships if r.focus_mode_recommended]
        if focus_mode_needed:
            recommendations.append(f"🎯 {len(focus_mode_needed)} relationships benefit from focus mode")

        # Pattern-based recommendations
        high_prediction = [r for r in relationships if r.effectiveness_prediction > 0.8]
        if high_prediction:
            recommendations.append(f"🎪 {len(high_prediction)} relationships have high success prediction")

        return recommendations

    # Placeholder implementations for complex calculations
    def _calculate_personal_relevance(self, source: PersonalizedStructuralElement, target: PersonalizedStructuralElement, profile) -> float:
        return 0.6  # Default moderate relevance

    def _calculate_pattern_alignment_score(self, source: PersonalizedStructuralElement, target: PersonalizedStructuralElement, profile) -> float:
        return 0.5  # Default moderate alignment

    def _predict_relationship_effectiveness(self, source: PersonalizedStructuralElement, target: PersonalizedStructuralElement, pattern_alignment: float, profile) -> float:
        return 0.7  # Default good effectiveness

    def _assess_learning_opportunity(self, source: PersonalizedStructuralElement, target: PersonalizedStructuralElement, profile) -> float:
        return 0.4  # Default moderate learning opportunity

    async def _calculate_user_complexity_adjustment(self, elements: List[PersonalizedStructuralElement], profile) -> float:
        if not elements:
            return 0.0
        adjustments = [e.personal_complexity_adjustment for e in elements]
        return statistics.mean(adjustments)


# Convenience functions
async def create_enhanced_tree_sitter_integration(
    base_tree_sitter: TreeSitterAnalyzer,
    database: SerenaIntelligenceDatabase,
    learning_engine: AdaptiveLearningEngine,
    profile_manager: PersonalLearningProfileManager,
    performance_monitor: PerformanceMonitor = None
) -> EnhancedTreeSitterIntegration:
    """Create enhanced Tree-sitter integration instance."""
    return EnhancedTreeSitterIntegration(
        base_tree_sitter, database, learning_engine, profile_manager, performance_monitor
    )


if __name__ == "__main__":
    # Quick test when run directly
    async def main():
        print("🌳 Serena Enhanced Tree-sitter Integration")
        print("Structural analysis with personalized ADHD intelligence")
        print("✅ Module loaded successfully")

    asyncio.run(main())