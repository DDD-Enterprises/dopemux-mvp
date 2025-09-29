"""
Serena v2 Phase 2B: Advanced Pattern Recognition Engine

Sophisticated navigation pattern recognition with ADHD-specific categorization,
sequence similarity matching, and predictive effectiveness scoring.
"""

import asyncio
import json
import logging
import math
import statistics
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set, Union
from dataclasses import dataclass, field
from enum import Enum
import difflib
import hashlib

from .database import SerenaIntelligenceDatabase
from .adaptive_learning import NavigationSequence, NavigationAction, LearningPhase
from .learning_profile_manager import PersonalLearningProfileManager
from ..performance_monitor import PerformanceMonitor

logger = logging.getLogger(__name__)


class NavigationPatternType(str, Enum):
    """Types of navigation patterns for ADHD optimization."""
    EXPLORATION = "exploration"          # Discovering new code areas
    DEBUGGING = "debugging"              # Following error traces, investigating issues
    IMPLEMENTATION = "implementation"    # Writing/modifying code functionality
    REVIEW = "review"                   # Code review, understanding existing code
    REFACTORING = "refactoring"         # Restructuring code without changing behavior
    LEARNING = "learning"               # Educational navigation, understanding concepts
    CONTEXT_BUILDING = "context_building"  # Building mental model of codebase
    MAINTENANCE = "maintenance"         # Bug fixes, updates, housekeeping


class PatternComplexity(str, Enum):
    """Pattern complexity levels for ADHD assessment."""
    SIMPLE = "simple"                   # Linear, few context switches
    MODERATE = "moderate"               # Some branching, manageable complexity
    COMPLEX = "complex"                 # Multiple branches, high cognitive load
    CHAOTIC = "chaotic"                 # Highly scattered, difficult to follow


class PatternEffectiveness(str, Enum):
    """Pattern effectiveness categories."""
    HIGHLY_EFFECTIVE = "highly_effective"      # >0.8 success rate
    EFFECTIVE = "effective"                    # 0.6-0.8 success rate
    MODERATELY_EFFECTIVE = "moderately_effective"  # 0.4-0.6 success rate
    INEFFECTIVE = "ineffective"                # <0.4 success rate


@dataclass
class PatternSignature:
    """Compact representation of navigation pattern for matching."""
    sequence_length: int
    action_types: List[str]
    complexity_progression: List[str]  # binned complexity: simple, moderate, complex
    timing_pattern: str  # fast, medium, slow
    context_switches: int
    completion_status: str


@dataclass
class RecognizedPattern:
    """A recognized navigation pattern with metadata."""
    pattern_id: str
    pattern_type: NavigationPatternType
    pattern_complexity: PatternComplexity
    signature: PatternSignature
    effectiveness_score: float
    usage_frequency: int
    last_seen: datetime
    success_indicators: List[str]
    failure_indicators: List[str]
    adhd_recommendations: List[str]
    cognitive_load_score: float
    optimal_attention_state: str  # peak_focus, moderate_focus, low_focus


@dataclass
class PatternPrediction:
    """Prediction about pattern effectiveness."""
    predicted_effectiveness: float
    confidence: float
    reasoning: List[str]
    alternative_patterns: List[str]
    adhd_risk_factors: List[str]
    recommended_modifications: List[str]


@dataclass
class PatternSimilarity:
    """Similarity between two patterns."""
    similarity_score: float  # 0.0 to 1.0
    matching_elements: List[str]
    differing_elements: List[str]
    complexity_difference: float
    timing_difference: float


class AdvancedPatternRecognition:
    """
    Advanced pattern recognition engine for ADHD-optimized navigation.

    Features:
    - Sophisticated sequence similarity matching
    - ADHD-specific pattern categorization and analysis
    - Predictive effectiveness scoring based on learned patterns
    - Context switching optimization with cognitive load management
    - Pattern evolution tracking and improvement suggestions
    - Real-time pattern recognition during navigation
    - Integration with personal learning profiles
    """

    def __init__(
        self,
        database: SerenaIntelligenceDatabase,
        profile_manager: PersonalLearningProfileManager,
        performance_monitor: PerformanceMonitor = None
    ):
        self.database = database
        self.profile_manager = profile_manager
        self.performance_monitor = performance_monitor or PerformanceMonitor()

        # Pattern recognition configuration
        self.similarity_threshold = 0.7  # Minimum similarity for pattern matching
        self.min_pattern_length = 3     # Minimum actions for pattern recognition
        self.max_pattern_length = 25    # Maximum to prevent cognitive overload
        self.effectiveness_learning_rate = 0.3

        # Pattern cache for performance
        self._pattern_cache: Dict[str, List[RecognizedPattern]] = {}
        self._similarity_cache: Dict[str, PatternSimilarity] = {}

        # ADHD-specific thresholds
        self.complexity_bins = {
            "simple": (0.0, 0.3),
            "moderate": (0.3, 0.6),
            "complex": (0.6, 1.0)
        }

    # Core Pattern Recognition

    async def analyze_navigation_sequence(
        self,
        sequence: NavigationSequence,
        user_session_id: str,
        workspace_path: str
    ) -> Dict[str, Any]:
        """Analyze navigation sequence for pattern recognition."""
        operation_id = self.performance_monitor.start_operation("analyze_navigation_sequence")

        try:
            # Generate pattern signature
            signature = self._generate_pattern_signature(sequence)

            # Classify pattern type
            pattern_type = await self._classify_pattern_type(sequence, signature)

            # Assess pattern complexity
            pattern_complexity = self._assess_pattern_complexity(sequence, signature)

            # Find similar historical patterns
            similar_patterns = await self._find_similar_patterns(
                user_session_id, signature, pattern_type
            )

            # Predict effectiveness
            effectiveness_prediction = await self._predict_pattern_effectiveness(
                sequence, similar_patterns, user_session_id, workspace_path
            )

            # Generate ADHD-specific insights
            adhd_insights = await self._generate_adhd_insights(
                sequence, pattern_type, pattern_complexity, effectiveness_prediction
            )

            # Store pattern for future learning
            await self._store_recognized_pattern(
                sequence, pattern_type, pattern_complexity, signature, effectiveness_prediction
            )

            analysis_result = {
                "pattern_type": pattern_type.value,
                "pattern_complexity": pattern_complexity.value,
                "signature": signature,
                "effectiveness_prediction": effectiveness_prediction,
                "similar_patterns_found": len(similar_patterns),
                "adhd_insights": adhd_insights,
                "cognitive_load_score": self._calculate_cognitive_load(sequence),
                "recommended_improvements": await self._suggest_pattern_improvements(
                    sequence, similar_patterns, effectiveness_prediction
                )
            }

            self.performance_monitor.end_operation(operation_id, success=True)
            logger.debug(f"🔍 Analyzed pattern: {pattern_type.value} (complexity: {pattern_complexity.value})")

            return analysis_result

        except Exception as e:
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"Failed to analyze navigation sequence: {e}")
            raise

    async def get_pattern_recommendations(
        self,
        current_context: Dict[str, Any],
        user_session_id: str,
        workspace_path: str
    ) -> Dict[str, Any]:
        """Get pattern-based recommendations for current navigation context."""
        operation_id = self.performance_monitor.start_operation("get_pattern_recommendations")

        try:
            # Get user's learning profile
            profile = await self.profile_manager.get_or_create_profile(user_session_id, workspace_path)

            # Analyze current navigation context
            context_type = current_context.get('context_type', 'exploration')
            current_complexity = current_context.get('current_complexity', 0.5)
            session_duration = current_context.get('session_duration_minutes', 0)

            # Find relevant patterns
            relevant_patterns = await self._find_relevant_patterns(
                user_session_id, context_type, profile.learning_phase
            )

            # Generate recommendations based on patterns
            recommendations = {
                "suggested_navigation_approach": await self._recommend_navigation_approach(
                    relevant_patterns, current_complexity, profile
                ),
                "optimal_sequence_length": self._recommend_sequence_length(
                    relevant_patterns, profile.average_attention_span_minutes
                ),
                "complexity_management": await self._recommend_complexity_management(
                    relevant_patterns, current_complexity, profile
                ),
                "context_switching_strategy": self._recommend_context_switching_strategy(
                    relevant_patterns, session_duration
                ),
                "attention_optimization": await self._recommend_attention_optimization(
                    relevant_patterns, current_context, profile
                ),
                "pattern_confidence": self._calculate_recommendation_confidence(relevant_patterns),
                "alternative_approaches": await self._suggest_alternative_approaches(
                    relevant_patterns, current_context
                )
            }

            self.performance_monitor.end_operation(operation_id, success=True)
            return recommendations

        except Exception as e:
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"Failed to get pattern recommendations: {e}")
            raise

    # Pattern Analysis Methods

    def _generate_pattern_signature(self, sequence: NavigationSequence) -> PatternSignature:
        """Generate pattern signature for sequence matching."""
        # Extract action types
        action_types = [action.action_type for action in sequence.actions]

        # Bin complexity progression
        complexity_progression = []
        for complexity in sequence.complexity_progression:
            if complexity <= 0.3:
                complexity_progression.append("simple")
            elif complexity <= 0.6:
                complexity_progression.append("moderate")
            else:
                complexity_progression.append("complex")

        # Categorize timing
        avg_duration = sequence.total_duration_ms / max(len(sequence.actions), 1)
        if avg_duration < 2000:  # < 2 seconds per action
            timing_pattern = "fast"
        elif avg_duration < 5000:  # 2-5 seconds per action
            timing_pattern = "medium"
        else:
            timing_pattern = "slow"

        return PatternSignature(
            sequence_length=len(sequence.actions),
            action_types=action_types,
            complexity_progression=complexity_progression,
            timing_pattern=timing_pattern,
            context_switches=sequence.context_switches,
            completion_status=sequence.completion_status
        )

    async def _classify_pattern_type(
        self, sequence: NavigationSequence, signature: PatternSignature
    ) -> NavigationPatternType:
        """Classify navigation pattern type using heuristics."""
        action_types = signature.action_types
        complexity_progression = signature.complexity_progression

        # Debugging pattern: lots of following relationships, error contexts
        if ("follow_relationship" in action_types and
            action_types.count("follow_relationship") / len(action_types) > 0.4):
            return NavigationPatternType.DEBUGGING

        # Implementation pattern: view + edit actions, moderate complexity
        if ("view_element" in action_types and "edit_element" in action_types):
            return NavigationPatternType.IMPLEMENTATION

        # Exploration pattern: lots of different action types, varying complexity
        if (len(set(action_types)) > 3 and
            len(set(complexity_progression)) > 1):
            return NavigationPatternType.EXPLORATION

        # Review pattern: mostly viewing, consistent complexity
        if (action_types.count("view_element") / len(action_types) > 0.7 and
            len(set(complexity_progression)) <= 2):
            return NavigationPatternType.REVIEW

        # Learning pattern: slow timing, increasing complexity
        if (signature.timing_pattern == "slow" and
            len(complexity_progression) > 3 and
            complexity_progression[-1] == "complex"):
            return NavigationPatternType.LEARNING

        # Default to exploration
        return NavigationPatternType.EXPLORATION

    def _assess_pattern_complexity(
        self, sequence: NavigationSequence, signature: PatternSignature
    ) -> PatternComplexity:
        """Assess overall pattern complexity for ADHD considerations."""
        complexity_factors = []

        # Length factor
        if signature.sequence_length <= 5:
            complexity_factors.append(0.2)
        elif signature.sequence_length <= 10:
            complexity_factors.append(0.5)
        else:
            complexity_factors.append(0.8)

        # Context switching factor
        if signature.context_switches <= 2:
            complexity_factors.append(0.2)
        elif signature.context_switches <= 5:
            complexity_factors.append(0.5)
        else:
            complexity_factors.append(0.9)

        # Complexity progression factor
        complexity_counts = {
            "simple": signature.complexity_progression.count("simple"),
            "moderate": signature.complexity_progression.count("moderate"),
            "complex": signature.complexity_progression.count("complex")
        }

        if complexity_counts["complex"] > complexity_counts["simple"] + complexity_counts["moderate"]:
            complexity_factors.append(0.8)
        elif complexity_counts["moderate"] > complexity_counts["simple"]:
            complexity_factors.append(0.5)
        else:
            complexity_factors.append(0.2)

        # Timing factor
        if signature.timing_pattern == "fast":
            complexity_factors.append(0.3)  # Fast can be overwhelming
        elif signature.timing_pattern == "slow":
            complexity_factors.append(0.7)  # Slow suggests difficulty
        else:
            complexity_factors.append(0.4)

        overall_complexity = statistics.mean(complexity_factors)

        if overall_complexity <= 0.3:
            return PatternComplexity.SIMPLE
        elif overall_complexity <= 0.6:
            return PatternComplexity.MODERATE
        elif overall_complexity <= 0.8:
            return PatternComplexity.COMPLEX
        else:
            return PatternComplexity.CHAOTIC

    async def _find_similar_patterns(
        self,
        user_session_id: str,
        signature: PatternSignature,
        pattern_type: NavigationPatternType
    ) -> List[RecognizedPattern]:
        """Find similar historical patterns for the user."""
        try:
            # Query database for patterns of the same type
            query = """
            SELECT * FROM navigation_patterns
            WHERE user_session_id = $1
              AND pattern_type = $2
              AND created_at > NOW() - INTERVAL '30 days'
            ORDER BY effectiveness_score DESC, last_occurrence DESC
            LIMIT 20
            """

            results = await self.database.execute_query(
                query, (user_session_id, pattern_type.value)
            )

            similar_patterns = []
            for row in results:
                # Calculate similarity to current signature
                stored_signature = self._parse_stored_signature(row)
                similarity = self._calculate_pattern_similarity(signature, stored_signature)

                if similarity.similarity_score >= self.similarity_threshold:
                    pattern = RecognizedPattern(
                        pattern_id=str(row['id']),
                        pattern_type=NavigationPatternType(row['pattern_type']),
                        pattern_complexity=self._assess_stored_complexity(row),
                        signature=stored_signature,
                        effectiveness_score=row['effectiveness_score'],
                        usage_frequency=row['pattern_frequency'],
                        last_seen=row['last_occurrence'],
                        success_indicators=[],  # Would be extracted from stored data
                        failure_indicators=[],
                        adhd_recommendations=[],
                        cognitive_load_score=row.get('cognitive_fatigue_score', 0.5),
                        optimal_attention_state="moderate_focus"  # Would be stored
                    )
                    similar_patterns.append(pattern)

            return sorted(similar_patterns, key=lambda p: p.effectiveness_score, reverse=True)

        except Exception as e:
            logger.error(f"Failed to find similar patterns: {e}")
            return []

    def _calculate_pattern_similarity(
        self, sig1: PatternSignature, sig2: PatternSignature
    ) -> PatternSimilarity:
        """Calculate similarity between two pattern signatures."""
        similarity_factors = []
        matching_elements = []
        differing_elements = []

        # Action type similarity (using sequence matching)
        action_similarity = difflib.SequenceMatcher(
            None, sig1.action_types, sig2.action_types
        ).ratio()
        similarity_factors.append(action_similarity * 0.3)  # 30% weight

        if action_similarity > 0.7:
            matching_elements.append("action_sequence")
        else:
            differing_elements.append("action_sequence")

        # Complexity progression similarity
        complexity_similarity = difflib.SequenceMatcher(
            None, sig1.complexity_progression, sig2.complexity_progression
        ).ratio()
        similarity_factors.append(complexity_similarity * 0.25)  # 25% weight

        if complexity_similarity > 0.7:
            matching_elements.append("complexity_progression")
        else:
            differing_elements.append("complexity_progression")

        # Length similarity
        length_diff = abs(sig1.sequence_length - sig2.sequence_length) / max(sig1.sequence_length, sig2.sequence_length)
        length_similarity = 1.0 - length_diff
        similarity_factors.append(length_similarity * 0.2)  # 20% weight

        # Context switching similarity
        cs_diff = abs(sig1.context_switches - sig2.context_switches) / max(max(sig1.context_switches, sig2.context_switches), 1)
        cs_similarity = 1.0 - cs_diff
        similarity_factors.append(cs_similarity * 0.15)  # 15% weight

        # Timing pattern similarity
        timing_similarity = 1.0 if sig1.timing_pattern == sig2.timing_pattern else 0.5
        similarity_factors.append(timing_similarity * 0.1)  # 10% weight

        overall_similarity = sum(similarity_factors)

        return PatternSimilarity(
            similarity_score=overall_similarity,
            matching_elements=matching_elements,
            differing_elements=differing_elements,
            complexity_difference=abs(len(sig1.complexity_progression) - len(sig2.complexity_progression)),
            timing_difference=0.0 if sig1.timing_pattern == sig2.timing_pattern else 1.0
        )

    # Effectiveness Prediction

    async def _predict_pattern_effectiveness(
        self,
        sequence: NavigationSequence,
        similar_patterns: List[RecognizedPattern],
        user_session_id: str,
        workspace_path: str
    ) -> PatternPrediction:
        """Predict effectiveness based on similar patterns and user profile."""
        try:
            profile = await self.profile_manager.get_or_create_profile(user_session_id, workspace_path)

            if not similar_patterns:
                # No historical data, use profile-based prediction
                base_effectiveness = 0.5
                confidence = 0.3
                reasoning = ["No similar patterns found - using profile-based estimation"]
            else:
                # Weight by similarity and recency
                weighted_effectiveness = 0.0
                total_weight = 0.0

                for pattern in similar_patterns:
                    # Recency weight (more recent patterns weighted higher)
                    days_ago = (datetime.now(timezone.utc) - pattern.last_seen.replace(tzinfo=timezone.utc)).days
                    recency_weight = max(0.1, 1.0 - (days_ago / 30.0))  # 30-day decay

                    # Pattern frequency weight
                    frequency_weight = min(1.0, pattern.usage_frequency / 10.0)

                    # Combine weights
                    pattern_weight = recency_weight * frequency_weight

                    weighted_effectiveness += pattern.effectiveness_score * pattern_weight
                    total_weight += pattern_weight

                base_effectiveness = weighted_effectiveness / max(total_weight, 0.1)
                confidence = min(0.9, total_weight / len(similar_patterns))
                reasoning = [f"Based on {len(similar_patterns)} similar patterns"]

            # Adjust based on current context
            predicted_effectiveness = self._adjust_effectiveness_for_context(
                base_effectiveness, sequence, profile
            )

            # Generate risk factors and recommendations
            adhd_risk_factors = self._identify_adhd_risk_factors(sequence, profile)
            recommended_modifications = self._suggest_pattern_modifications(
                sequence, similar_patterns, adhd_risk_factors
            )

            # Suggest alternative patterns
            alternative_patterns = [p.pattern_id for p in similar_patterns[:3]]

            return PatternPrediction(
                predicted_effectiveness=predicted_effectiveness,
                confidence=confidence,
                reasoning=reasoning,
                alternative_patterns=alternative_patterns,
                adhd_risk_factors=adhd_risk_factors,
                recommended_modifications=recommended_modifications
            )

        except Exception as e:
            logger.error(f"Failed to predict pattern effectiveness: {e}")
            return PatternPrediction(
                predicted_effectiveness=0.5,
                confidence=0.1,
                reasoning=["Prediction failed - using default"],
                alternative_patterns=[],
                adhd_risk_factors=[],
                recommended_modifications=[]
            )

    def _adjust_effectiveness_for_context(
        self, base_effectiveness: float, sequence: NavigationSequence, profile
    ) -> float:
        """Adjust effectiveness prediction based on current context."""
        adjustments = []

        # Attention span factor
        if sequence.attention_span_seconds > profile.average_attention_span_minutes * 60:
            adjustments.append(-0.1)  # Longer than optimal attention span

        # Complexity tolerance factor
        avg_complexity = sequence.average_complexity
        if avg_complexity > profile.optimal_complexity_range[1]:
            adjustments.append(-0.15)  # Above comfort zone
        elif avg_complexity < profile.optimal_complexity_range[0]:
            adjustments.append(0.05)   # Well within comfort zone

        # Context switching factor
        if sequence.context_switches > profile.context_switch_tolerance:
            adjustments.append(-0.1)  # Too many context switches

        # Learning phase factor
        if profile.learning_phase == LearningPhase.CONVERGENCE:
            adjustments.append(0.05)  # More predictable in convergence phase

        return max(0.0, min(1.0, base_effectiveness + sum(adjustments)))

    # ADHD-Specific Analysis

    def _identify_adhd_risk_factors(self, sequence: NavigationSequence, profile) -> List[str]:
        """Identify ADHD-specific risk factors in the pattern."""
        risk_factors = []

        # Excessive context switching
        if sequence.context_switches > 5:
            risk_factors.append("High context switching may cause cognitive overload")

        # Attention span exceeded
        if sequence.attention_span_seconds > profile.average_attention_span_minutes * 60 * 1.2:
            risk_factors.append("Session length exceeds optimal attention span")

        # Complexity escalation
        if len(sequence.complexity_progression) > 3:
            complexity_trend = statistics.mean(sequence.complexity_progression[-3:]) - statistics.mean(sequence.complexity_progression[:3])
            if complexity_trend > 0.3:
                risk_factors.append("Rapid complexity increase may cause overwhelm")

        # Chaotic pattern
        if len(set(action.action_type for action in sequence.actions)) > 5:
            risk_factors.append("Too many different action types may scatter attention")

        return risk_factors

    async def _generate_adhd_insights(
        self,
        sequence: NavigationSequence,
        pattern_type: NavigationPatternType,
        pattern_complexity: PatternComplexity,
        effectiveness_prediction: PatternPrediction
    ) -> List[str]:
        """Generate ADHD-specific insights about the navigation pattern."""
        insights = []

        # Pattern type insights
        if pattern_type == NavigationPatternType.DEBUGGING:
            if pattern_complexity == PatternComplexity.COMPLEX:
                insights.append("Complex debugging patterns benefit from break points to prevent overwhelm")
            else:
                insights.append("Debugging pattern detected - systematic approach is working well")

        elif pattern_type == NavigationPatternType.EXPLORATION:
            if sequence.context_switches > 3:
                insights.append("High exploration activity - consider focusing on one area at a time")
            else:
                insights.append("Balanced exploration pattern - good for building mental models")

        elif pattern_type == NavigationPatternType.IMPLEMENTATION:
            insights.append("Implementation pattern - ideal for hyperfocus periods")

        # Complexity insights
        if pattern_complexity == PatternComplexity.CHAOTIC:
            insights.append("Pattern shows scattered attention - try progressive disclosure")
        elif pattern_complexity == PatternComplexity.SIMPLE:
            insights.append("Simple pattern - good foundation for building complexity tolerance")

        # Effectiveness insights
        if effectiveness_prediction.predicted_effectiveness > 0.8:
            insights.append("High effectiveness predicted - this pattern works well for you")
        elif effectiveness_prediction.predicted_effectiveness < 0.4:
            insights.append("Low effectiveness predicted - consider modifying approach")

        return insights

    def _calculate_cognitive_load(self, sequence: NavigationSequence) -> float:
        """Calculate cognitive load score for the sequence."""
        load_factors = []

        # Length factor (longer sequences = higher load)
        length_load = min(1.0, len(sequence.actions) / 15.0)
        load_factors.append(length_load * 0.25)

        # Context switching factor
        cs_load = min(1.0, sequence.context_switches / 8.0)
        load_factors.append(cs_load * 0.3)

        # Complexity factor
        if sequence.complexity_progression:
            avg_complexity = statistics.mean(sequence.complexity_progression)
            load_factors.append(avg_complexity * 0.25)

        # Timing factor (very fast or very slow increases load)
        avg_duration = sequence.total_duration_ms / max(len(sequence.actions), 1)
        if avg_duration < 1000 or avg_duration > 10000:  # Too fast or too slow
            load_factors.append(0.2)
        else:
            load_factors.append(0.1)

        # Completion factor (incomplete increases load)
        if sequence.completion_status != "completed":
            load_factors.append(0.2)

        return min(1.0, sum(load_factors))

    # Pattern Storage and Retrieval

    async def _store_recognized_pattern(
        self,
        sequence: NavigationSequence,
        pattern_type: NavigationPatternType,
        pattern_complexity: PatternComplexity,
        signature: PatternSignature,
        effectiveness_prediction: PatternPrediction
    ) -> None:
        """Store recognized pattern for future learning."""
        try:
            # Generate pattern hash for deduplication
            pattern_data = {
                "type": pattern_type.value,
                "signature": signature.__dict__,
                "complexity": pattern_complexity.value
            }
            pattern_hash = hashlib.md5(json.dumps(pattern_data, sort_keys=True).encode()).hexdigest()

            # Store or update pattern
            upsert_query = """
            INSERT INTO navigation_patterns (
                user_session_id, workspace_path, pattern_sequence, sequence_hash,
                pattern_type, context_switches, total_duration_ms, complexity_progression,
                effectiveness_score, completion_status, attention_span_seconds,
                cognitive_fatigue_score, pattern_frequency
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, 1)
            ON CONFLICT (user_session_id, sequence_hash)
            DO UPDATE SET
                pattern_frequency = navigation_patterns.pattern_frequency + 1,
                effectiveness_score = (navigation_patterns.effectiveness_score * 0.7 + EXCLUDED.effectiveness_score * 0.3),
                last_occurrence = NOW(),
                updated_at = NOW()
            """

            pattern_sequence_data = [action.__dict__ for action in sequence.actions]

            await self.database.execute_query(upsert_query, (
                sequence.user_session_id,
                getattr(sequence, 'workspace_path', 'default'),
                json.dumps(pattern_sequence_data),
                pattern_hash,
                pattern_type.value,
                sequence.context_switches,
                sequence.total_duration_ms,
                json.dumps(sequence.complexity_progression),
                effectiveness_prediction.predicted_effectiveness,
                sequence.completion_status,
                sequence.attention_span_seconds,
                self._calculate_cognitive_load(sequence)
            ))

        except Exception as e:
            logger.error(f"Failed to store recognized pattern: {e}")

    # Utility Methods

    def _parse_stored_signature(self, row: Dict[str, Any]) -> PatternSignature:
        """Parse pattern signature from database row."""
        try:
            pattern_data = json.loads(row['pattern_sequence'])
            action_types = [action['action_type'] for action in pattern_data]

            complexity_progression = json.loads(row['complexity_progression'])
            complexity_bins = []
            for c in complexity_progression:
                if c <= 0.3:
                    complexity_bins.append("simple")
                elif c <= 0.6:
                    complexity_bins.append("moderate")
                else:
                    complexity_bins.append("complex")

            # Estimate timing pattern from duration
            avg_duration = row['total_duration_ms'] / max(len(action_types), 1)
            timing_pattern = "fast" if avg_duration < 2000 else "medium" if avg_duration < 5000 else "slow"

            return PatternSignature(
                sequence_length=len(action_types),
                action_types=action_types,
                complexity_progression=complexity_bins,
                timing_pattern=timing_pattern,
                context_switches=row['context_switches'],
                completion_status=row['completion_status']
            )

        except Exception as e:
            logger.error(f"Failed to parse stored signature: {e}")
            return PatternSignature(0, [], [], "medium", 0, "incomplete")

    def _assess_stored_complexity(self, row: Dict[str, Any]) -> PatternComplexity:
        """Assess complexity of stored pattern."""
        try:
            cognitive_load = row.get('cognitive_fatigue_score', 0.5)
            if cognitive_load <= 0.3:
                return PatternComplexity.SIMPLE
            elif cognitive_load <= 0.6:
                return PatternComplexity.MODERATE
            elif cognitive_load <= 0.8:
                return PatternComplexity.COMPLEX
            else:
                return PatternComplexity.CHAOTIC
        except Exception:
            return PatternComplexity.MODERATE

    async def _find_relevant_patterns(
        self, user_session_id: str, context_type: str, learning_phase: LearningPhase
    ) -> List[RecognizedPattern]:
        """Find patterns relevant to current context."""
        try:
            # Query for patterns matching context and learning phase
            query = """
            SELECT * FROM navigation_patterns
            WHERE user_session_id = $1
              AND (pattern_type = $2 OR pattern_type = 'exploration')
              AND effectiveness_score > 0.5
              AND created_at > NOW() - INTERVAL '14 days'
            ORDER BY effectiveness_score DESC, pattern_frequency DESC
            LIMIT 10
            """

            results = await self.database.execute_query(query, (user_session_id, context_type))

            patterns = []
            for row in results:
                pattern = RecognizedPattern(
                    pattern_id=str(row['id']),
                    pattern_type=NavigationPatternType(row['pattern_type']),
                    pattern_complexity=self._assess_stored_complexity(row),
                    signature=self._parse_stored_signature(row),
                    effectiveness_score=row['effectiveness_score'],
                    usage_frequency=row['pattern_frequency'],
                    last_seen=row['last_occurrence'],
                    success_indicators=[],
                    failure_indicators=[],
                    adhd_recommendations=[],
                    cognitive_load_score=row.get('cognitive_fatigue_score', 0.5),
                    optimal_attention_state="moderate_focus"
                )
                patterns.append(pattern)

            return patterns

        except Exception as e:
            logger.error(f"Failed to find relevant patterns: {e}")
            return []

    async def _recommend_navigation_approach(
        self, patterns: List[RecognizedPattern], current_complexity: float, profile
    ) -> Dict[str, Any]:
        """Recommend navigation approach based on patterns."""
        if not patterns:
            return {
                "approach": "exploratory",
                "reasoning": "No historical patterns available"
            }

        # Find most effective pattern for current complexity level
        suitable_patterns = [
            p for p in patterns
            if abs(p.cognitive_load_score - current_complexity) < 0.3
        ]

        if suitable_patterns:
            best_pattern = max(suitable_patterns, key=lambda p: p.effectiveness_score)
            return {
                "approach": best_pattern.pattern_type.value,
                "reasoning": f"Based on effective {best_pattern.pattern_type.value} pattern",
                "expected_effectiveness": best_pattern.effectiveness_score
            }

        return {
            "approach": "gradual",
            "reasoning": "Current complexity level not well-represented in patterns"
        }

    def _recommend_sequence_length(
        self, patterns: List[RecognizedPattern], attention_span_minutes: float
    ) -> int:
        """Recommend optimal sequence length."""
        if patterns:
            avg_length = statistics.mean(p.signature.sequence_length for p in patterns
                                       if p.effectiveness_score > 0.7)
            return max(3, min(15, int(avg_length)))

        # Default based on attention span
        return max(3, min(10, int(attention_span_minutes / 3)))

    async def _recommend_complexity_management(
        self, patterns: List[RecognizedPattern], current_complexity: float, profile
    ) -> Dict[str, Any]:
        """Recommend complexity management strategies."""
        recommendations = {
            "start_simple": current_complexity > profile.optimal_complexity_range[1],
            "progressive_disclosure": True,
            "complexity_filtering": current_complexity > 0.7,
            "break_points": []
        }

        # Analyze effective patterns for complexity management
        effective_patterns = [p for p in patterns if p.effectiveness_score > 0.7]
        if effective_patterns:
            avg_cognitive_load = statistics.mean(p.cognitive_load_score for p in effective_patterns)
            if avg_cognitive_load < 0.5:
                recommendations["approach"] = "maintain_simple_focus"
            else:
                recommendations["approach"] = "gradual_complexity_increase"

        return recommendations

    def _recommend_context_switching_strategy(
        self, patterns: List[RecognizedPattern], session_duration: float
    ) -> Dict[str, Any]:
        """Recommend context switching strategies."""
        if patterns:
            effective_patterns = [p for p in patterns if p.effectiveness_score > 0.7]
            if effective_patterns:
                avg_context_switches = statistics.mean(p.signature.context_switches for p in effective_patterns)
                return {
                    "max_switches": max(2, int(avg_context_switches)),
                    "strategy": "controlled_switching",
                    "reasoning": "Based on historically effective patterns"
                }

        # Default ADHD-friendly strategy
        max_switches = 3 if session_duration < 30 else 5
        return {
            "max_switches": max_switches,
            "strategy": "minimal_switching",
            "reasoning": "Conservative approach for ADHD optimization"
        }

    async def _recommend_attention_optimization(
        self, patterns: List[RecognizedPattern], current_context: Dict[str, Any], profile
    ) -> List[str]:
        """Recommend attention optimization strategies."""
        recommendations = []

        session_duration = current_context.get('session_duration_minutes', 0)

        if session_duration > profile.average_attention_span_minutes:
            recommendations.append("Consider taking a short break")

        if patterns:
            high_load_patterns = [p for p in patterns if p.cognitive_load_score > 0.7]
            if high_load_patterns and len(high_load_patterns) / len(patterns) > 0.5:
                recommendations.append("Enable focus mode to reduce cognitive load")

        recommendations.append("Use progressive disclosure to manage information")

        return recommendations

    def _calculate_recommendation_confidence(self, patterns: List[RecognizedPattern]) -> float:
        """Calculate confidence in pattern-based recommendations."""
        if not patterns:
            return 0.2

        # Confidence based on pattern count and effectiveness
        pattern_count_factor = min(1.0, len(patterns) / 5.0)
        avg_effectiveness = statistics.mean(p.effectiveness_score for p in patterns)

        return min(0.95, pattern_count_factor * avg_effectiveness)

    async def _suggest_alternative_approaches(
        self, patterns: List[RecognizedPattern], current_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Suggest alternative navigation approaches."""
        alternatives = []

        if patterns:
            # Group by pattern type
            by_type = {}
            for pattern in patterns:
                if pattern.pattern_type not in by_type:
                    by_type[pattern.pattern_type] = []
                by_type[pattern.pattern_type].append(pattern)

            # Suggest top 2 alternative types
            for pattern_type, type_patterns in sorted(by_type.items(),
                                                    key=lambda x: max(p.effectiveness_score for p in x[1]),
                                                    reverse=True)[:2]:
                best_pattern = max(type_patterns, key=lambda p: p.effectiveness_score)
                alternatives.append({
                    "approach": pattern_type.value,
                    "effectiveness": best_pattern.effectiveness_score,
                    "complexity": best_pattern.pattern_complexity.value
                })

        return alternatives

    def _suggest_pattern_modifications(
        self,
        sequence: NavigationSequence,
        similar_patterns: List[RecognizedPattern],
        risk_factors: List[str]
    ) -> List[str]:
        """Suggest modifications to improve pattern effectiveness."""
        modifications = []

        if "High context switching" in ' '.join(risk_factors):
            modifications.append("Reduce context switches by focusing on one area longer")

        if "Session length exceeds" in ' '.join(risk_factors):
            modifications.append("Break into shorter focused sessions")

        if "Rapid complexity increase" in ' '.join(risk_factors):
            modifications.append("Use progressive complexity increase")

        if similar_patterns:
            most_effective = max(similar_patterns, key=lambda p: p.effectiveness_score)
            if most_effective.signature.sequence_length < len(sequence.actions):
                modifications.append("Consider shorter navigation sequences")

        return modifications

    async def _suggest_pattern_improvements(
        self,
        sequence: NavigationSequence,
        similar_patterns: List[RecognizedPattern],
        effectiveness_prediction: PatternPrediction
    ) -> List[str]:
        """Suggest improvements for the navigation pattern."""
        improvements = []

        if effectiveness_prediction.predicted_effectiveness < 0.6:
            improvements.extend(effectiveness_prediction.recommended_modifications)

        if sequence.context_switches > 5:
            improvements.append("Reduce context switching to improve focus")

        if len(sequence.actions) > 15:
            improvements.append("Break long sequences into shorter, focused sessions")

        if similar_patterns:
            best_pattern = max(similar_patterns, key=lambda p: p.effectiveness_score)
            if best_pattern.effectiveness_score > effectiveness_prediction.predicted_effectiveness + 0.2:
                improvements.append(f"Consider using {best_pattern.pattern_type.value} approach")

        return improvements


# Convenience functions
async def create_pattern_recognition_engine(
    database: SerenaIntelligenceDatabase,
    profile_manager: PersonalLearningProfileManager,
    performance_monitor: PerformanceMonitor = None
) -> AdvancedPatternRecognition:
    """Create pattern recognition engine instance."""
    return AdvancedPatternRecognition(database, profile_manager, performance_monitor)


if __name__ == "__main__":
    # Quick test when run directly
    async def main():
        print("🔍 Serena Advanced Pattern Recognition Engine")
        print("ADHD-optimized navigation pattern analysis and prediction")
        print("✅ Module loaded successfully")

    asyncio.run(main())