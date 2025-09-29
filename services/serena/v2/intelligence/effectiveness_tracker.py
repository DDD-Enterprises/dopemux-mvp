"""
Serena v2 Phase 2B: Effectiveness Tracking System

Multi-dimensional effectiveness measurement with automatic pattern improvement,
A/B testing for navigation strategies, and ADHD-optimized feedback loops.
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
import random
import hashlib

from .database import SerenaIntelligenceDatabase
from .adaptive_learning import NavigationSequence, LearningPhase
from .learning_profile_manager import PersonalLearningProfileManager
from .pattern_recognition import AdvancedPatternRecognition, NavigationPatternType
from ..performance_monitor import PerformanceMonitor

logger = logging.getLogger(__name__)


class EffectivenessDimension(str, Enum):
    """Dimensions of navigation effectiveness."""
    COMPLETION = "completion"                # Task completion rate
    EFFICIENCY = "efficiency"                # Time to completion
    SATISFACTION = "satisfaction"            # User-reported satisfaction
    COGNITIVE_LOAD = "cognitive_load"        # Mental effort required
    LEARNING = "learning"                    # Knowledge gained
    RETENTION = "retention"                  # Information retained
    TRANSFER = "transfer"                    # Application to new contexts
    ADHD_COMFORT = "adhd_comfort"           # ADHD-specific comfort level


class FeedbackType(str, Enum):
    """Types of effectiveness feedback."""
    IMPLICIT = "implicit"                    # Derived from behavior
    EXPLICIT = "explicit"                    # Direct user feedback
    PERFORMANCE = "performance"              # Performance metrics
    BIOMETRIC = "biometric"                 # Future: stress, attention metrics
    CONTEXTUAL = "contextual"               # Environmental factors


class ABTestStatus(str, Enum):
    """A/B test status."""
    PLANNING = "planning"
    RUNNING = "running"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    PAUSED = "paused"


@dataclass
class EffectivenessScore:
    """Multi-dimensional effectiveness measurement."""
    dimension: EffectivenessDimension
    score: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    data_points: int
    last_updated: datetime
    improvement_trend: float  # -1.0 to 1.0
    source: FeedbackType


@dataclass
class EffectivenessProfile:
    """Comprehensive effectiveness profile for a pattern or approach."""
    pattern_id: str
    user_session_id: str
    effectiveness_scores: Dict[EffectivenessDimension, EffectivenessScore]
    overall_effectiveness: float
    sample_size: int
    measurement_period_days: int
    last_measurement: datetime
    improvement_suggestions: List[str] = field(default_factory=list)
    confidence_level: float = 0.0


@dataclass
class ABTest:
    """A/B test for navigation strategies."""
    test_id: str
    test_name: str
    description: str
    user_session_id: str
    strategy_a: Dict[str, Any]  # Control strategy
    strategy_b: Dict[str, Any]  # Test strategy
    status: ABTestStatus
    start_date: datetime
    end_date: Optional[datetime]
    target_sample_size: int
    current_sample_size: int
    results_a: List[float] = field(default_factory=list)
    results_b: List[float] = field(default_factory=list)
    statistical_significance: Optional[float] = None
    winner: Optional[str] = None  # 'A', 'B', or 'no_difference'


@dataclass
class ImprovementRecommendation:
    """Recommendation for improving navigation effectiveness."""
    recommendation_id: str
    pattern_id: str
    dimension: EffectivenessDimension
    current_score: float
    target_score: float
    improvement_strategy: str
    implementation_steps: List[str]
    expected_impact: float
    confidence: float
    priority: str  # high, medium, low
    adhd_specific: bool


class EffectivenessTracker:
    """
    Effectiveness tracking system for ADHD-optimized navigation learning.

    Features:
    - Multi-dimensional effectiveness measurement and tracking
    - Automatic pattern improvement based on effectiveness feedback
    - A/B testing for navigation strategies and accommodations
    - ADHD-specific effectiveness metrics and optimization
    - Real-time feedback integration and adaptation
    - Statistical analysis and trend detection
    - Performance integration with Layer 1 monitoring
    """

    def __init__(
        self,
        database: SerenaIntelligenceDatabase,
        profile_manager: PersonalLearningProfileManager,
        pattern_recognition: AdvancedPatternRecognition,
        performance_monitor: PerformanceMonitor = None
    ):
        self.database = database
        self.profile_manager = profile_manager
        self.pattern_recognition = pattern_recognition
        self.performance_monitor = performance_monitor or PerformanceMonitor()

        # Tracking configuration
        self.min_sample_size = 5  # Minimum samples for reliable measurement
        self.confidence_threshold = 0.7  # Minimum confidence for recommendations
        self.improvement_threshold = 0.1  # Minimum improvement to consider significant
        self.measurement_window_days = 14  # Rolling window for effectiveness measurement

        # Active tracking data
        self._effectiveness_cache: Dict[str, EffectivenessProfile] = {}
        self._active_ab_tests: Dict[str, ABTest] = {}
        self._feedback_buffer: List[Dict[str, Any]] = []

        # ADHD-specific weights for effectiveness dimensions
        self.adhd_dimension_weights = {
            EffectivenessDimension.COMPLETION: 0.25,
            EffectivenessDimension.EFFICIENCY: 0.15,
            EffectivenessDimension.SATISFACTION: 0.20,
            EffectivenessDimension.COGNITIVE_LOAD: 0.25,  # High weight for ADHD
            EffectivenessDimension.ADHD_COMFORT: 0.15     # ADHD-specific dimension
        }

    # Core Effectiveness Tracking

    async def track_navigation_effectiveness(
        self,
        sequence: NavigationSequence,
        user_feedback: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> EffectivenessProfile:
        """Track effectiveness of a navigation sequence."""
        operation_id = self.performance_monitor.start_operation("track_navigation_effectiveness")

        try:
            # Generate pattern ID for tracking
            pattern_id = await self._generate_pattern_id(sequence)

            # Measure effectiveness across dimensions
            effectiveness_scores = await self._measure_effectiveness_dimensions(
                sequence, user_feedback, context
            )

            # Calculate overall effectiveness
            overall_effectiveness = self._calculate_overall_effectiveness(effectiveness_scores)

            # Get or create effectiveness profile
            profile = await self._get_or_create_effectiveness_profile(
                pattern_id, sequence.user_session_id
            )

            # Update profile with new measurements
            await self._update_effectiveness_profile(
                profile, effectiveness_scores, overall_effectiveness
            )

            # Check for improvement opportunities
            recommendations = await self._analyze_improvement_opportunities(profile)
            profile.improvement_suggestions = [r.improvement_strategy for r in recommendations]

            # Store updated profile
            await self._store_effectiveness_profile(profile)

            # Trigger automatic improvements if conditions met
            await self._trigger_automatic_improvements(profile, recommendations)

            # Check A/B test participation
            await self._check_ab_test_participation(sequence, profile)

            self.performance_monitor.end_operation(operation_id, success=True)

            logger.debug(f"📊 Tracked effectiveness for pattern {pattern_id}: {overall_effectiveness:.2f}")
            return profile

        except Exception as e:
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"Failed to track navigation effectiveness: {e}")
            raise

    async def record_explicit_feedback(
        self,
        pattern_id: str,
        user_session_id: str,
        feedback: Dict[str, Any]
    ) -> None:
        """Record explicit user feedback about navigation effectiveness."""
        try:
            feedback_entry = {
                "pattern_id": pattern_id,
                "user_session_id": user_session_id,
                "feedback_type": FeedbackType.EXPLICIT.value,
                "feedback_data": feedback,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            self._feedback_buffer.append(feedback_entry)

            # Process feedback if buffer is large enough
            if len(self._feedback_buffer) >= 10:
                await self._process_feedback_buffer()

            logger.debug(f"📝 Recorded explicit feedback for pattern {pattern_id}")

        except Exception as e:
            logger.error(f"Failed to record explicit feedback: {e}")

    async def get_effectiveness_insights(
        self,
        user_session_id: str,
        workspace_path: str,
        time_period_days: int = 7
    ) -> Dict[str, Any]:
        """Get effectiveness insights for user over time period."""
        operation_id = self.performance_monitor.start_operation("get_effectiveness_insights")

        try:
            # Query effectiveness data
            query = """
            SELECT pattern_id, effectiveness_scores, overall_effectiveness, sample_size, last_measurement
            FROM effectiveness_profiles
            WHERE user_session_id = $1
              AND last_measurement > NOW() - INTERVAL '%s days'
            ORDER BY overall_effectiveness DESC
            """ % time_period_days

            results = await self.database.execute_query(query, (user_session_id,))

            insights = {
                "period_days": time_period_days,
                "total_patterns_tracked": len(results),
                "effectiveness_summary": {},
                "top_performing_patterns": [],
                "improvement_opportunities": [],
                "adhd_specific_insights": [],
                "trends": {}
            }

            if results:
                # Calculate summary statistics
                effectiveness_scores = [r['overall_effectiveness'] for r in results]
                insights["effectiveness_summary"] = {
                    "average": round(statistics.mean(effectiveness_scores), 2),
                    "median": round(statistics.median(effectiveness_scores), 2),
                    "best": round(max(effectiveness_scores), 2),
                    "improvement_needed": sum(1 for s in effectiveness_scores if s < 0.6)
                }

                # Top performing patterns
                insights["top_performing_patterns"] = [
                    {
                        "pattern_id": r['pattern_id'],
                        "effectiveness": round(r['overall_effectiveness'], 2),
                        "sample_size": r['sample_size']
                    }
                    for r in results[:5]
                ]

                # ADHD-specific insights
                insights["adhd_specific_insights"] = await self._generate_adhd_effectiveness_insights(
                    user_session_id, results
                )

            self.performance_monitor.end_operation(operation_id, success=True)
            return insights

        except Exception as e:
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"Failed to get effectiveness insights: {e}")
            raise

    # Effectiveness Measurement

    async def _measure_effectiveness_dimensions(
        self,
        sequence: NavigationSequence,
        user_feedback: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[EffectivenessDimension, EffectivenessScore]:
        """Measure effectiveness across all dimensions."""
        scores = {}

        # Completion effectiveness
        completion_score = self._measure_completion_effectiveness(sequence)
        scores[EffectivenessDimension.COMPLETION] = EffectivenessScore(
            dimension=EffectivenessDimension.COMPLETION,
            score=completion_score,
            confidence=0.9,  # High confidence from behavioral data
            data_points=1,
            last_updated=datetime.now(timezone.utc),
            improvement_trend=0.0,
            source=FeedbackType.IMPLICIT
        )

        # Efficiency effectiveness
        efficiency_score = self._measure_efficiency_effectiveness(sequence)
        scores[EffectivenessDimension.EFFICIENCY] = EffectivenessScore(
            dimension=EffectivenessDimension.EFFICIENCY,
            score=efficiency_score,
            confidence=0.8,
            data_points=1,
            last_updated=datetime.now(timezone.utc),
            improvement_trend=0.0,
            source=FeedbackType.PERFORMANCE
        )

        # Cognitive load effectiveness (inverse of cognitive load)
        cognitive_load_score = self._measure_cognitive_load_effectiveness(sequence)
        scores[EffectivenessDimension.COGNITIVE_LOAD] = EffectivenessScore(
            dimension=EffectivenessDimension.COGNITIVE_LOAD,
            score=cognitive_load_score,
            confidence=0.7,
            data_points=1,
            last_updated=datetime.now(timezone.utc),
            improvement_trend=0.0,
            source=FeedbackType.IMPLICIT
        )

        # ADHD comfort (based on pattern characteristics)
        adhd_comfort_score = self._measure_adhd_comfort_effectiveness(sequence)
        scores[EffectivenessDimension.ADHD_COMFORT] = EffectivenessScore(
            dimension=EffectivenessDimension.ADHD_COMFORT,
            score=adhd_comfort_score,
            confidence=0.8,
            data_points=1,
            last_updated=datetime.now(timezone.utc),
            improvement_trend=0.0,
            source=FeedbackType.IMPLICIT
        )

        # User satisfaction (if provided)
        if user_feedback and 'satisfaction' in user_feedback:
            satisfaction_score = min(1.0, max(0.0, user_feedback['satisfaction'] / 5.0))  # Assume 1-5 scale
            scores[EffectivenessDimension.SATISFACTION] = EffectivenessScore(
                dimension=EffectivenessDimension.SATISFACTION,
                score=satisfaction_score,
                confidence=1.0,  # Direct user input
                data_points=1,
                last_updated=datetime.now(timezone.utc),
                improvement_trend=0.0,
                source=FeedbackType.EXPLICIT
            )

        return scores

    def _measure_completion_effectiveness(self, sequence: NavigationSequence) -> float:
        """Measure completion effectiveness based on sequence outcomes."""
        if sequence.completion_status == "completed":
            return 1.0
        elif sequence.completion_status == "partially_completed":
            return 0.6
        elif sequence.completion_status == "abandoned":
            return 0.2
        else:  # incomplete
            return 0.4

    def _measure_efficiency_effectiveness(self, sequence: NavigationSequence) -> float:
        """Measure efficiency based on time and actions."""
        # Ideal efficiency: reasonable time per action, minimal backtracking
        actions_count = len(sequence.actions)
        duration_minutes = sequence.total_duration_ms / 60000

        if actions_count == 0:
            return 0.0

        # Average time per action (ideal: 30 seconds to 2 minutes)
        avg_time_per_action = duration_minutes / actions_count

        if 0.5 <= avg_time_per_action <= 2.0:  # 30 seconds to 2 minutes
            time_efficiency = 1.0
        elif avg_time_per_action < 0.5:  # Too fast, might be superficial
            time_efficiency = 0.6
        elif avg_time_per_action <= 4.0:  # Moderately slow
            time_efficiency = 0.7
        else:  # Very slow
            time_efficiency = 0.4

        # Context switching efficiency (fewer switches = better for ADHD)
        switch_efficiency = max(0.0, 1.0 - (sequence.context_switches / max(actions_count, 1)))

        return (time_efficiency + switch_efficiency) / 2

    def _measure_cognitive_load_effectiveness(self, sequence: NavigationSequence) -> float:
        """Measure cognitive load effectiveness (lower load = higher effectiveness)."""
        load_factors = []

        # Length factor
        length_load = min(1.0, len(sequence.actions) / 15.0)
        load_factors.append(length_load)

        # Context switching load
        cs_load = min(1.0, sequence.context_switches / 8.0)
        load_factors.append(cs_load)

        # Complexity load
        if sequence.complexity_progression:
            avg_complexity = statistics.mean(sequence.complexity_progression)
            load_factors.append(avg_complexity)

        # Duration load (very long sessions increase cognitive load)
        duration_load = min(1.0, sequence.total_duration_ms / (60 * 60 * 1000))  # Normalize to hours
        load_factors.append(duration_load * 0.5)  # Lower weight for duration

        overall_load = statistics.mean(load_factors)
        return max(0.0, 1.0 - overall_load)  # Invert load to get effectiveness

    def _measure_adhd_comfort_effectiveness(self, sequence: NavigationSequence) -> float:
        """Measure ADHD-specific comfort and accommodation effectiveness."""
        comfort_factors = []

        # Attention span compatibility
        attention_span_seconds = sequence.attention_span_seconds
        typical_adhd_span = 25 * 60  # 25 minutes

        if attention_span_seconds <= typical_adhd_span:
            comfort_factors.append(1.0)
        elif attention_span_seconds <= typical_adhd_span * 1.5:
            comfort_factors.append(0.7)
        else:
            comfort_factors.append(0.4)

        # Context switching comfort (ADHD users prefer fewer switches)
        if sequence.context_switches <= 3:
            comfort_factors.append(1.0)
        elif sequence.context_switches <= 6:
            comfort_factors.append(0.6)
        else:
            comfort_factors.append(0.3)

        # Complexity progression comfort (gradual is better for ADHD)
        if sequence.complexity_progression:
            complexity_variance = statistics.variance(sequence.complexity_progression) if len(sequence.complexity_progression) > 1 else 0
            if complexity_variance <= 0.1:  # Stable complexity
                comfort_factors.append(0.9)
            elif complexity_variance <= 0.3:  # Moderate variation
                comfort_factors.append(0.6)
            else:  # High variation
                comfort_factors.append(0.3)

        # Completion comfort
        if sequence.completion_status == "completed":
            comfort_factors.append(1.0)
        elif sequence.completion_status == "partially_completed":
            comfort_factors.append(0.5)
        else:
            comfort_factors.append(0.2)

        return statistics.mean(comfort_factors)

    def _calculate_overall_effectiveness(
        self, scores: Dict[EffectivenessDimension, EffectivenessScore]
    ) -> float:
        """Calculate weighted overall effectiveness score."""
        weighted_scores = []

        for dimension, weight in self.adhd_dimension_weights.items():
            if dimension in scores:
                score = scores[dimension].score
                confidence = scores[dimension].confidence
                weighted_scores.append(score * weight * confidence)

        return min(1.0, sum(weighted_scores)) if weighted_scores else 0.0

    # Profile Management

    async def _get_or_create_effectiveness_profile(
        self, pattern_id: str, user_session_id: str
    ) -> EffectivenessProfile:
        """Get or create effectiveness profile for pattern."""
        cache_key = f"{user_session_id}_{pattern_id}"

        if cache_key in self._effectiveness_cache:
            return self._effectiveness_cache[cache_key]

        # Try to load from database
        try:
            query = """
            SELECT * FROM effectiveness_profiles
            WHERE pattern_id = $1 AND user_session_id = $2
            """

            results = await self.database.execute_query(query, (pattern_id, user_session_id))

            if results:
                row = results[0]
                effectiveness_scores = json.loads(row['effectiveness_scores'])

                # Convert back to EffectivenessScore objects
                scores_dict = {}
                for dim_name, score_data in effectiveness_scores.items():
                    dimension = EffectivenessDimension(dim_name)
                    scores_dict[dimension] = EffectivenessScore(
                        dimension=dimension,
                        score=score_data['score'],
                        confidence=score_data['confidence'],
                        data_points=score_data['data_points'],
                        last_updated=datetime.fromisoformat(score_data['last_updated']),
                        improvement_trend=score_data['improvement_trend'],
                        source=FeedbackType(score_data['source'])
                    )

                profile = EffectivenessProfile(
                    pattern_id=row['pattern_id'],
                    user_session_id=row['user_session_id'],
                    effectiveness_scores=scores_dict,
                    overall_effectiveness=row['overall_effectiveness'],
                    sample_size=row['sample_size'],
                    measurement_period_days=self.measurement_window_days,
                    last_measurement=row['last_measurement'],
                    improvement_suggestions=json.loads(row.get('improvement_suggestions', '[]')),
                    confidence_level=row.get('confidence_level', 0.0)
                )
            else:
                # Create new profile
                profile = EffectivenessProfile(
                    pattern_id=pattern_id,
                    user_session_id=user_session_id,
                    effectiveness_scores={},
                    overall_effectiveness=0.0,
                    sample_size=0,
                    measurement_period_days=self.measurement_window_days,
                    last_measurement=datetime.now(timezone.utc),
                    improvement_suggestions=[],
                    confidence_level=0.0
                )

            self._effectiveness_cache[cache_key] = profile
            return profile

        except Exception as e:
            logger.error(f"Failed to load effectiveness profile: {e}")
            # Return new profile as fallback
            return EffectivenessProfile(
                pattern_id=pattern_id,
                user_session_id=user_session_id,
                effectiveness_scores={},
                overall_effectiveness=0.0,
                sample_size=0,
                measurement_period_days=self.measurement_window_days,
                last_measurement=datetime.now(timezone.utc)
            )

    async def _update_effectiveness_profile(
        self,
        profile: EffectivenessProfile,
        new_scores: Dict[EffectivenessDimension, EffectivenessScore],
        overall_effectiveness: float
    ) -> None:
        """Update effectiveness profile with new measurements."""
        # Update individual dimension scores using exponential moving average
        alpha = 0.3  # Learning rate

        for dimension, new_score in new_scores.items():
            if dimension in profile.effectiveness_scores:
                existing_score = profile.effectiveness_scores[dimension]

                # Update score with moving average
                updated_score = alpha * new_score.score + (1 - alpha) * existing_score.score

                # Calculate improvement trend
                improvement_trend = new_score.score - existing_score.score

                # Update the score object
                existing_score.score = updated_score
                existing_score.confidence = min(1.0, existing_score.confidence + 0.1)
                existing_score.data_points += 1
                existing_score.last_updated = datetime.now(timezone.utc)
                existing_score.improvement_trend = improvement_trend

            else:
                # First measurement for this dimension
                profile.effectiveness_scores[dimension] = new_score

        # Update overall effectiveness
        profile.overall_effectiveness = alpha * overall_effectiveness + (1 - alpha) * profile.overall_effectiveness
        profile.sample_size += 1
        profile.last_measurement = datetime.now(timezone.utc)

        # Update confidence level based on sample size
        profile.confidence_level = min(0.95, profile.sample_size / 20.0)

    # A/B Testing

    async def start_ab_test(
        self,
        test_name: str,
        user_session_id: str,
        strategy_a: Dict[str, Any],
        strategy_b: Dict[str, Any],
        target_sample_size: int = 20
    ) -> ABTest:
        """Start A/B test for navigation strategies."""
        try:
            test_id = f"ab_{user_session_id}_{int(time.time())}"

            ab_test = ABTest(
                test_id=test_id,
                test_name=test_name,
                description=f"Testing {test_name} for user {user_session_id}",
                user_session_id=user_session_id,
                strategy_a=strategy_a,
                strategy_b=strategy_b,
                status=ABTestStatus.RUNNING,
                start_date=datetime.now(timezone.utc),
                end_date=None,
                target_sample_size=target_sample_size,
                current_sample_size=0
            )

            self._active_ab_tests[test_id] = ab_test

            logger.info(f"🧪 Started A/B test: {test_name} for user {user_session_id}")
            return ab_test

        except Exception as e:
            logger.error(f"Failed to start A/B test: {e}")
            raise

    async def _check_ab_test_participation(
        self, sequence: NavigationSequence, profile: EffectivenessProfile
    ) -> None:
        """Check if sequence should participate in A/B tests."""
        try:
            for test_id, ab_test in self._active_ab_tests.items():
                if (ab_test.user_session_id == sequence.user_session_id and
                    ab_test.status == ABTestStatus.RUNNING and
                    ab_test.current_sample_size < ab_test.target_sample_size):

                    # Randomly assign to A or B (50/50 split)
                    use_strategy_b = random.random() < 0.5

                    effectiveness = profile.overall_effectiveness

                    if use_strategy_b:
                        ab_test.results_b.append(effectiveness)
                    else:
                        ab_test.results_a.append(effectiveness)

                    ab_test.current_sample_size += 1

                    # Check if test is complete
                    if ab_test.current_sample_size >= ab_test.target_sample_size:
                        await self._complete_ab_test(test_id)

        except Exception as e:
            logger.error(f"Failed to check A/B test participation: {e}")

    async def _complete_ab_test(self, test_id: str) -> None:
        """Complete A/B test and analyze results."""
        try:
            ab_test = self._active_ab_tests[test_id]
            ab_test.status = ABTestStatus.ANALYZING

            # Perform statistical analysis
            if len(ab_test.results_a) >= 5 and len(ab_test.results_b) >= 5:
                mean_a = statistics.mean(ab_test.results_a)
                mean_b = statistics.mean(ab_test.results_b)

                # Simple significance test (t-test would be more rigorous)
                diff = abs(mean_a - mean_b)
                pooled_std = statistics.stdev(ab_test.results_a + ab_test.results_b)

                if diff > pooled_std * 0.5:  # Simple significance threshold
                    ab_test.statistical_significance = 0.95
                    ab_test.winner = "B" if mean_b > mean_a else "A"
                else:
                    ab_test.statistical_significance = 0.3
                    ab_test.winner = "no_difference"
            else:
                ab_test.winner = "insufficient_data"

            ab_test.status = ABTestStatus.COMPLETED
            ab_test.end_date = datetime.now(timezone.utc)

            logger.info(f"🏁 Completed A/B test {test_id}: Winner = {ab_test.winner}")

        except Exception as e:
            logger.error(f"Failed to complete A/B test: {e}")

    # Improvement Analysis

    async def _analyze_improvement_opportunities(
        self, profile: EffectivenessProfile
    ) -> List[ImprovementRecommendation]:
        """Analyze effectiveness profile for improvement opportunities."""
        recommendations = []

        try:
            for dimension, score in profile.effectiveness_scores.items():
                if score.score < 0.7 and score.confidence > 0.5:  # Room for improvement
                    recommendation = await self._generate_improvement_recommendation(
                        profile.pattern_id, dimension, score
                    )
                    if recommendation:
                        recommendations.append(recommendation)

            # Sort by expected impact
            recommendations.sort(key=lambda r: r.expected_impact, reverse=True)

            return recommendations[:5]  # Top 5 recommendations

        except Exception as e:
            logger.error(f"Failed to analyze improvement opportunities: {e}")
            return []

    async def _generate_improvement_recommendation(
        self,
        pattern_id: str,
        dimension: EffectivenessDimension,
        score: EffectivenessScore
    ) -> Optional[ImprovementRecommendation]:
        """Generate specific improvement recommendation."""
        try:
            current_score = score.score
            target_score = min(1.0, current_score + 0.2)  # Target 20% improvement

            if dimension == EffectivenessDimension.COMPLETION:
                return ImprovementRecommendation(
                    recommendation_id=f"improve_{pattern_id}_{dimension.value}",
                    pattern_id=pattern_id,
                    dimension=dimension,
                    current_score=current_score,
                    target_score=target_score,
                    improvement_strategy="Break down complex navigation into smaller, focused steps",
                    implementation_steps=[
                        "Identify natural stopping points in navigation sequence",
                        "Set micro-goals for each navigation segment",
                        "Use progressive disclosure to reduce cognitive overload"
                    ],
                    expected_impact=0.15,
                    confidence=0.8,
                    priority="high",
                    adhd_specific=True
                )

            elif dimension == EffectivenessDimension.COGNITIVE_LOAD:
                return ImprovementRecommendation(
                    recommendation_id=f"improve_{pattern_id}_{dimension.value}",
                    pattern_id=pattern_id,
                    dimension=dimension,
                    current_score=current_score,
                    target_score=target_score,
                    improvement_strategy="Reduce cognitive load through complexity filtering",
                    implementation_steps=[
                        "Enable complexity filtering for high-complexity elements",
                        "Implement progressive disclosure of information",
                        "Reduce context switching frequency"
                    ],
                    expected_impact=0.2,
                    confidence=0.9,
                    priority="high",
                    adhd_specific=True
                )

            elif dimension == EffectivenessDimension.EFFICIENCY:
                return ImprovementRecommendation(
                    recommendation_id=f"improve_{pattern_id}_{dimension.value}",
                    pattern_id=pattern_id,
                    dimension=dimension,
                    current_score=current_score,
                    target_score=target_score,
                    improvement_strategy="Optimize navigation sequence and reduce backtracking",
                    implementation_steps=[
                        "Pre-plan navigation routes using learned patterns",
                        "Implement intelligent prefetching",
                        "Reduce redundant navigation actions"
                    ],
                    expected_impact=0.12,
                    confidence=0.7,
                    priority="medium",
                    adhd_specific=False
                )

            return None

        except Exception as e:
            logger.error(f"Failed to generate improvement recommendation: {e}")
            return None

    async def _trigger_automatic_improvements(
        self,
        profile: EffectivenessProfile,
        recommendations: List[ImprovementRecommendation]
    ) -> None:
        """Trigger automatic improvements based on recommendations."""
        try:
            high_priority_recs = [r for r in recommendations if r.priority == "high" and r.expected_impact > 0.15]

            for rec in high_priority_recs:
                if rec.dimension == EffectivenessDimension.COGNITIVE_LOAD and rec.adhd_specific:
                    # Automatically enable complexity filtering
                    await self._apply_cognitive_load_improvement(profile, rec)

                elif rec.dimension == EffectivenessDimension.COMPLETION and rec.confidence > 0.8:
                    # Suggest pattern modifications
                    await self._apply_completion_improvement(profile, rec)

        except Exception as e:
            logger.error(f"Failed to trigger automatic improvements: {e}")

    async def _apply_cognitive_load_improvement(
        self, profile: EffectivenessProfile, recommendation: ImprovementRecommendation
    ) -> None:
        """Apply cognitive load improvement automatically."""
        logger.info(f"🔧 Auto-applying cognitive load improvement for pattern {profile.pattern_id}")
        # Implementation would integrate with navigation system to enable complexity filtering

    async def _apply_completion_improvement(
        self, profile: EffectivenessProfile, recommendation: ImprovementRecommendation
    ) -> None:
        """Apply completion improvement automatically."""
        logger.info(f"🎯 Auto-applying completion improvement for pattern {profile.pattern_id}")
        # Implementation would modify navigation patterns to improve completion

    # Database Operations

    async def _store_effectiveness_profile(self, profile: EffectivenessProfile) -> None:
        """Store effectiveness profile to database."""
        try:
            # Convert effectiveness scores to JSON
            scores_json = {}
            for dimension, score in profile.effectiveness_scores.items():
                scores_json[dimension.value] = {
                    "score": score.score,
                    "confidence": score.confidence,
                    "data_points": score.data_points,
                    "last_updated": score.last_updated.isoformat(),
                    "improvement_trend": score.improvement_trend,
                    "source": score.source.value
                }

            upsert_query = """
            INSERT INTO effectiveness_profiles (
                pattern_id, user_session_id, effectiveness_scores, overall_effectiveness,
                sample_size, last_measurement, improvement_suggestions, confidence_level
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (pattern_id, user_session_id)
            DO UPDATE SET
                effectiveness_scores = EXCLUDED.effectiveness_scores,
                overall_effectiveness = EXCLUDED.overall_effectiveness,
                sample_size = EXCLUDED.sample_size,
                last_measurement = EXCLUDED.last_measurement,
                improvement_suggestions = EXCLUDED.improvement_suggestions,
                confidence_level = EXCLUDED.confidence_level,
                updated_at = NOW()
            """

            await self.database.execute_query(upsert_query, (
                profile.pattern_id,
                profile.user_session_id,
                json.dumps(scores_json),
                profile.overall_effectiveness,
                profile.sample_size,
                profile.last_measurement,
                json.dumps(profile.improvement_suggestions),
                profile.confidence_level
            ))

        except Exception as e:
            logger.error(f"Failed to store effectiveness profile: {e}")

    # Utility Methods

    async def _generate_pattern_id(self, sequence: NavigationSequence) -> str:
        """Generate pattern ID for effectiveness tracking."""
        # Use pattern recognition to get a consistent pattern ID
        pattern_data = {
            "user_id": sequence.user_session_id,
            "action_types": [action.action_type for action in sequence.actions],
            "complexity_range": "simple" if sequence.average_complexity <= 0.3 else
                              "moderate" if sequence.average_complexity <= 0.6 else "complex",
            "length": len(sequence.actions)
        }

        pattern_string = json.dumps(pattern_data, sort_keys=True)
        return hashlib.md5(pattern_string.encode()).hexdigest()[:12]

    async def _process_feedback_buffer(self) -> None:
        """Process accumulated feedback."""
        try:
            for feedback_entry in self._feedback_buffer:
                # Store feedback to database
                insert_query = """
                INSERT INTO effectiveness_feedback (
                    pattern_id, user_session_id, feedback_type, feedback_data, timestamp
                ) VALUES ($1, $2, $3, $4, $5)
                """

                await self.database.execute_query(insert_query, (
                    feedback_entry['pattern_id'],
                    feedback_entry['user_session_id'],
                    feedback_entry['feedback_type'],
                    json.dumps(feedback_entry['feedback_data']),
                    feedback_entry['timestamp']
                ))

            self._feedback_buffer.clear()

        except Exception as e:
            logger.error(f"Failed to process feedback buffer: {e}")

    async def _generate_adhd_effectiveness_insights(
        self, user_session_id: str, effectiveness_data: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate ADHD-specific effectiveness insights."""
        insights = []

        try:
            effectiveness_scores = [r['overall_effectiveness'] for r in effectiveness_data]

            if effectiveness_scores:
                avg_effectiveness = statistics.mean(effectiveness_scores)

                if avg_effectiveness > 0.8:
                    insights.append("🚀 Excellent navigation effectiveness - your patterns are working well")
                elif avg_effectiveness > 0.6:
                    insights.append("✅ Good navigation effectiveness with room for optimization")
                else:
                    insights.append("📈 Significant improvement opportunities identified")

                # Check for patterns
                high_performing = [r for r in effectiveness_data if r['overall_effectiveness'] > 0.8]
                if high_performing:
                    insights.append(f"🎯 {len(high_performing)} highly effective patterns identified for reuse")

                # Sample size insights
                well_measured = [r for r in effectiveness_data if r['sample_size'] >= 5]
                if len(well_measured) < len(effectiveness_data) * 0.5:
                    insights.append("📊 More navigation data needed for reliable pattern analysis")

        except Exception as e:
            logger.error(f"Failed to generate ADHD insights: {e}")

        return insights


# Convenience functions
async def create_effectiveness_tracker(
    database: SerenaIntelligenceDatabase,
    profile_manager: PersonalLearningProfileManager,
    pattern_recognition: AdvancedPatternRecognition,
    performance_monitor: PerformanceMonitor = None
) -> EffectivenessTracker:
    """Create effectiveness tracker instance."""
    return EffectivenessTracker(database, profile_manager, pattern_recognition, performance_monitor)


if __name__ == "__main__":
    # Quick test when run directly
    async def main():
        print("📊 Serena Effectiveness Tracking System")
        print("Multi-dimensional effectiveness measurement with ADHD optimization")
        print("✅ Module loaded successfully")

    asyncio.run(main())