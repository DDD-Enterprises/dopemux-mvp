"""
Serena v2 Phase 2B: Adaptive Learning Engine

Personal navigation pattern recognition and optimization for ADHD users.
Learns individual preferences, attention patterns, and cognitive load tolerance
to provide personalized code navigation intelligence.
"""

import asyncio
import json
import logging
import time
import statistics
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set, Union
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib

from .database import SerenaIntelligenceDatabase
from .graph_operations import SerenaGraphOperations, NavigationMode, CodeElementNode
from ..performance_monitor import PerformanceMonitor
from ..adhd_features import CodeComplexityAnalyzer

logger = logging.getLogger(__name__)


class LearningPhase(str, Enum):
    """Learning phases for pattern recognition."""
    EXPLORATION = "exploration"      # Initial learning phase
    PATTERN_DETECTION = "pattern_detection"  # Identifying patterns
    OPTIMIZATION = "optimization"    # Refining patterns
    CONVERGENCE = "convergence"      # Stable patterns established
    ADAPTATION = "adaptation"        # Ongoing refinement


class AttentionState(str, Enum):
    """User attention states for ADHD optimization."""
    PEAK_FOCUS = "peak_focus"        # High attention, can handle complexity
    MODERATE_FOCUS = "moderate_focus"  # Normal attention, moderate complexity
    LOW_FOCUS = "low_focus"          # Scattered attention, simple tasks only
    HYPERFOCUS = "hyperfocus"        # Intense focus, may miss bigger picture
    FATIGUE = "fatigue"              # Cognitive fatigue, need break


@dataclass
class NavigationAction:
    """Individual navigation action within a pattern."""
    timestamp: datetime
    action_type: str  # view_element, search, follow_relationship, etc.
    element_id: Optional[int] = None
    element_type: Optional[str] = None
    complexity_score: float = 0.0
    duration_ms: float = 0.0
    success: bool = True
    context_data: Dict[str, Any] = None

    def __post_init__(self):
        if self.context_data is None:
            self.context_data = {}


@dataclass
class NavigationSequence:
    """Sequence of navigation actions forming a pattern."""
    sequence_id: str
    user_session_id: str
    actions: List[NavigationAction]
    start_time: datetime
    end_time: datetime
    total_duration_ms: float
    context_switches: int
    complexity_progression: List[float]
    effectiveness_score: float = 0.0
    completion_status: str = "incomplete"
    attention_span_seconds: int = 0
    context_data: Dict[str, Any] = None

    def __post_init__(self):
        if self.context_data is None:
            self.context_data = {}

    @property
    def average_complexity(self) -> float:
        """Calculate average complexity of the sequence."""
        if not self.complexity_progression:
            return 0.0
        return statistics.mean(self.complexity_progression)

    @property
    def complexity_variance(self) -> float:
        """Calculate complexity variance to detect focus stability."""
        if len(self.complexity_progression) < 2:
            return 0.0
        return statistics.variance(self.complexity_progression)


@dataclass
class PersonalLearningProfile:
    """Personal learning profile for ADHD optimization."""
    user_session_id: str
    workspace_path: str

    # Attention characteristics
    average_attention_span_minutes: float = 25.0
    peak_focus_times: List[str] = None  # Time patterns when focus is best
    optimal_complexity_range: Tuple[float, float] = (0.0, 0.6)
    context_switch_tolerance: int = 3

    # Navigation preferences
    preferred_result_limit: int = 10
    complexity_filter_threshold: float = 0.7
    progressive_disclosure_preference: bool = True

    # Learning metrics
    learning_phase: LearningPhase = LearningPhase.EXPLORATION
    pattern_confidence: float = 0.0
    session_count: int = 0
    total_navigation_time_minutes: float = 0.0

    # Effectiveness tracking
    successful_patterns: List[str] = None
    problematic_patterns: List[str] = None
    adaptation_rate: float = 0.1  # How quickly to adapt to new patterns

    # ADHD accommodations
    focus_mode_trigger_threshold: float = 0.7
    fatigue_detection_enabled: bool = True
    gentle_guidance_enabled: bool = True

    def __post_init__(self):
        if self.peak_focus_times is None:
            self.peak_focus_times = []
        if self.successful_patterns is None:
            self.successful_patterns = []
        if self.problematic_patterns is None:
            self.problematic_patterns = []


class AdaptiveLearningEngine:
    """
    Adaptive learning engine for personal ADHD navigation optimization.

    Features:
    - Real-time pattern recognition from navigation sequences
    - Personal learning profile development and refinement
    - ADHD-specific accommodation learning (attention spans, complexity tolerance)
    - Context switching pattern optimization
    - Effectiveness tracking with automatic improvement
    - Convergence detection for stable pattern learning
    - Integration with Phase 2A PostgreSQL intelligence layer
    """

    def __init__(
        self,
        database: SerenaIntelligenceDatabase,
        graph_operations: SerenaGraphOperations,
        performance_monitor: PerformanceMonitor = None
    ):
        self.database = database
        self.graph_operations = graph_operations
        self.performance_monitor = performance_monitor or PerformanceMonitor()
        self.complexity_analyzer = CodeComplexityAnalyzer()

        # Learning configuration
        self.min_pattern_length = 3  # Minimum actions for pattern recognition
        self.max_pattern_length = 20  # Maximum actions to prevent cognitive overload
        self.pattern_similarity_threshold = 0.7  # Similarity threshold for pattern matching
        self.convergence_threshold = 0.8  # Pattern confidence for convergence

        # Active learning state
        self.active_sequences: Dict[str, NavigationSequence] = {}
        self.learning_profiles: Dict[str, PersonalLearningProfile] = {}

    # Core Learning Functions

    async def start_navigation_sequence(
        self,
        user_session_id: str,
        workspace_path: str,
        context: Dict[str, Any] = None
    ) -> str:
        """Start tracking a new navigation sequence."""
        operation_id = self.performance_monitor.start_operation("start_navigation_sequence")

        try:
            sequence_id = self._generate_sequence_id(user_session_id)

            sequence = NavigationSequence(
                sequence_id=sequence_id,
                user_session_id=user_session_id,
                actions=[],
                start_time=datetime.now(timezone.utc),
                end_time=datetime.now(timezone.utc),  # Will be updated
                total_duration_ms=0.0,
                context_switches=0,
                complexity_progression=[],
                context_data=context or {}
            )

            self.active_sequences[sequence_id] = sequence

            # Ensure user has a learning profile
            await self._ensure_learning_profile(user_session_id, workspace_path)

            self.performance_monitor.end_operation(operation_id, success=True)

            logger.debug(f"🎯 Started navigation sequence {sequence_id} for user {user_session_id}")
            return sequence_id

        except Exception as e:
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"Failed to start navigation sequence: {e}")
            raise

    async def record_navigation_action(
        self,
        sequence_id: str,
        action_type: str,
        element_id: Optional[int] = None,
        duration_ms: float = 0.0,
        success: bool = True,
        context_data: Dict[str, Any] = None
    ) -> None:
        """Record a navigation action within a sequence."""
        if sequence_id not in self.active_sequences:
            logger.warning(f"Unknown sequence ID: {sequence_id}")
            return

        sequence = self.active_sequences[sequence_id]

        # Get element complexity if available
        complexity_score = 0.0
        element_type = None

        if element_id:
            try:
                element = await self.graph_operations.get_element_by_id(element_id)
                if element:
                    complexity_score = element.complexity_score
                    element_type = element.element_type
            except Exception as e:
                logger.debug(f"Could not get element complexity: {e}")

        # Create navigation action
        action = NavigationAction(
            timestamp=datetime.now(timezone.utc),
            action_type=action_type,
            element_id=element_id,
            element_type=element_type,
            complexity_score=complexity_score,
            duration_ms=duration_ms,
            success=success,
            context_data=context_data or {}
        )

        # Add to sequence
        sequence.actions.append(action)
        sequence.complexity_progression.append(complexity_score)
        sequence.end_time = action.timestamp

        # Update total duration
        sequence.total_duration_ms = (sequence.end_time - sequence.start_time).total_seconds() * 1000

        # Detect context switches (significant complexity or type changes)
        if len(sequence.actions) > 1:
            prev_action = sequence.actions[-2]
            if (abs(complexity_score - prev_action.complexity_score) > 0.3 or
                element_type != prev_action.element_type):
                sequence.context_switches += 1

        # Update attention span tracking
        if len(sequence.actions) >= 2:
            sequence.attention_span_seconds = int((action.timestamp - sequence.actions[0].timestamp).total_seconds())

        logger.debug(f"📝 Recorded {action_type} action in sequence {sequence_id}")

    async def end_navigation_sequence(
        self,
        sequence_id: str,
        completion_status: str = "completed",
        user_satisfaction: Optional[float] = None
    ) -> NavigationSequence:
        """End navigation sequence and analyze for pattern learning."""
        operation_id = self.performance_monitor.start_operation("end_navigation_sequence")

        try:
            if sequence_id not in self.active_sequences:
                raise ValueError(f"Unknown sequence ID: {sequence_id}")

            sequence = self.active_sequences.pop(sequence_id)
            sequence.completion_status = completion_status
            sequence.end_time = datetime.now(timezone.utc)

            # Calculate effectiveness score
            sequence.effectiveness_score = await self._calculate_sequence_effectiveness(
                sequence, user_satisfaction
            )

            # Store sequence in database
            await self._store_navigation_sequence(sequence)

            # Update learning profile based on this sequence
            await self._update_learning_profile(sequence)

            # Analyze for pattern recognition
            await self._analyze_sequence_for_patterns(sequence)

            self.performance_monitor.end_operation(operation_id, success=True)

            logger.info(f"✅ Completed navigation sequence {sequence_id} "
                       f"(effectiveness: {sequence.effectiveness_score:.2f})")

            return sequence

        except Exception as e:
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"Failed to end navigation sequence {sequence_id}: {e}")
            raise

    async def get_learning_profile(self, user_session_id: str, workspace_path: str) -> PersonalLearningProfile:
        """Get or create learning profile for user."""
        profile_key = f"{user_session_id}_{workspace_path}"

        if profile_key in self.learning_profiles:
            return self.learning_profiles[profile_key]

        # Load from database
        try:
            query = """
            SELECT * FROM learning_profiles
            WHERE user_session_id = $1 AND workspace_path = $2
            """

            results = await self.database.execute_query(query, (user_session_id, workspace_path))

            if results:
                row = results[0]
                profile = PersonalLearningProfile(
                    user_session_id=row['user_session_id'],
                    workspace_path=row['workspace_path'],
                    average_attention_span_minutes=row['attention_span_minutes'],
                    optimal_complexity_range=(0.0, row['preferred_complexity_level'] == 'complex' and 1.0 or 0.6),
                    preferred_result_limit=row['optimal_result_limit'],
                    context_switch_tolerance=row['context_switch_tolerance'],
                    progressive_disclosure_preference=row['progressive_disclosure_preference'],
                    learning_phase=LearningPhase(row.get('learning_phase', 'exploration')),
                    session_count=row['session_count'],
                    adaptation_rate=row['adaptation_rate']
                )
            else:
                # Create new profile
                profile = PersonalLearningProfile(
                    user_session_id=user_session_id,
                    workspace_path=workspace_path
                )
                await self._store_learning_profile(profile)

            self.learning_profiles[profile_key] = profile
            return profile

        except Exception as e:
            logger.error(f"Failed to get learning profile: {e}")
            # Return default profile
            return PersonalLearningProfile(
                user_session_id=user_session_id,
                workspace_path=workspace_path
            )

    async def get_adaptive_recommendations(
        self,
        user_session_id: str,
        workspace_path: str,
        current_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Get adaptive recommendations based on learned patterns."""
        operation_id = self.performance_monitor.start_operation("get_adaptive_recommendations")

        try:
            profile = await self.get_learning_profile(user_session_id, workspace_path)

            # Analyze current attention state
            attention_state = await self._detect_attention_state(profile, current_context)

            # Generate personalized recommendations
            recommendations = {
                "navigation_mode": self._recommend_navigation_mode(profile, attention_state),
                "result_limit": self._recommend_result_limit(profile, attention_state),
                "complexity_filter": self._recommend_complexity_filter(profile, attention_state),
                "break_suggestion": self._suggest_break_if_needed(profile, current_context),
                "focus_optimization": self._recommend_focus_optimization(profile, attention_state),
                "attention_state": attention_state.value,
                "profile_confidence": profile.pattern_confidence,
                "learning_phase": profile.learning_phase.value
            }

            self.performance_monitor.end_operation(operation_id, success=True)
            return recommendations

        except Exception as e:
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"Failed to get adaptive recommendations: {e}")
            raise

    # Pattern Recognition and Analysis

    async def _analyze_sequence_for_patterns(self, sequence: NavigationSequence) -> None:
        """Analyze sequence for pattern recognition and learning."""
        try:
            # Generate pattern signature
            pattern_signature = self._generate_pattern_signature(sequence)

            # Check for similar historical patterns
            similar_patterns = await self._find_similar_patterns(
                sequence.user_session_id, pattern_signature
            )

            # Update pattern effectiveness
            if similar_patterns:
                await self._update_pattern_effectiveness(similar_patterns, sequence.effectiveness_score)

            # Check for learning convergence
            await self._check_learning_convergence(sequence.user_session_id)

        except Exception as e:
            logger.error(f"Pattern analysis failed: {e}")

    def _generate_pattern_signature(self, sequence: NavigationSequence) -> str:
        """Generate a signature for pattern matching."""
        # Create pattern based on action types, complexity progression, and timing
        pattern_elements = []

        for action in sequence.actions:
            # Discretize complexity into bins for pattern matching
            complexity_bin = "simple" if action.complexity_score <= 0.3 else \
                           "moderate" if action.complexity_score <= 0.6 else "complex"

            pattern_elements.append(f"{action.action_type}:{complexity_bin}")

        # Include sequence characteristics
        pattern_data = {
            "actions": pattern_elements,
            "context_switches": sequence.context_switches,
            "duration_category": "short" if sequence.total_duration_ms < 30000 else \
                               "medium" if sequence.total_duration_ms < 120000 else "long",
            "completion": sequence.completion_status
        }

        # Create hash signature
        pattern_string = json.dumps(pattern_data, sort_keys=True)
        return hashlib.md5(pattern_string.encode()).hexdigest()

    async def _find_similar_patterns(
        self, user_session_id: str, pattern_signature: str
    ) -> List[Dict[str, Any]]:
        """Find similar historical patterns."""
        try:
            query = """
            SELECT * FROM navigation_patterns
            WHERE user_session_id = $1
              AND sequence_hash = $2
            ORDER BY last_occurrence DESC
            LIMIT 10
            """

            return await self.database.execute_query(query, (user_session_id, pattern_signature))

        except Exception as e:
            logger.error(f"Failed to find similar patterns: {e}")
            return []

    async def _update_pattern_effectiveness(
        self, similar_patterns: List[Dict[str, Any]], new_effectiveness: float
    ) -> None:
        """Update effectiveness scores for similar patterns."""
        try:
            for pattern in similar_patterns:
                # Update effectiveness using exponential moving average
                current_effectiveness = pattern.get('effectiveness_score', 0.0)
                alpha = 0.3  # Learning rate
                updated_effectiveness = alpha * new_effectiveness + (1 - alpha) * current_effectiveness

                update_query = """
                UPDATE navigation_patterns
                SET effectiveness_score = $1,
                    pattern_frequency = pattern_frequency + 1,
                    last_occurrence = NOW()
                WHERE id = $2
                """

                await self.database.execute_query(
                    update_query, (updated_effectiveness, pattern['id'])
                )

        except Exception as e:
            logger.error(f"Failed to update pattern effectiveness: {e}")

    # Learning Profile Management

    async def _ensure_learning_profile(self, user_session_id: str, workspace_path: str) -> None:
        """Ensure user has a learning profile."""
        await self.get_learning_profile(user_session_id, workspace_path)

    async def _update_learning_profile(self, sequence: NavigationSequence) -> None:
        """Update learning profile based on completed sequence."""
        try:
            profile = await self.get_learning_profile(
                sequence.user_session_id,
                getattr(sequence, 'workspace_path', 'default')
            )

            # Update session statistics
            profile.session_count += 1
            profile.total_navigation_time_minutes += sequence.total_duration_ms / 60000

            # Update attention span (exponential moving average)
            alpha = 0.2
            if sequence.attention_span_seconds > 0:
                new_attention_minutes = sequence.attention_span_seconds / 60
                profile.average_attention_span_minutes = (
                    alpha * new_attention_minutes +
                    (1 - alpha) * profile.average_attention_span_minutes
                )

            # Update complexity tolerance based on successful navigation
            if sequence.effectiveness_score > 0.7 and sequence.average_complexity > profile.optimal_complexity_range[1]:
                # User successfully handled higher complexity
                new_upper_bound = min(1.0, profile.optimal_complexity_range[1] + 0.05)
                profile.optimal_complexity_range = (profile.optimal_complexity_range[0], new_upper_bound)

            # Update context switch tolerance
            if sequence.effectiveness_score > 0.7:
                if sequence.context_switches > profile.context_switch_tolerance:
                    profile.context_switch_tolerance = min(10, sequence.context_switches)

                # Track successful patterns
                pattern_signature = self._generate_pattern_signature(sequence)
                if pattern_signature not in profile.successful_patterns:
                    profile.successful_patterns.append(pattern_signature)
                    # Keep only recent successful patterns
                    profile.successful_patterns = profile.successful_patterns[-20:]

            # Update learning phase
            await self._update_learning_phase(profile)

            # Store updated profile
            await self._store_learning_profile(profile)

        except Exception as e:
            logger.error(f"Failed to update learning profile: {e}")

    async def _update_learning_phase(self, profile: PersonalLearningProfile) -> None:
        """Update learning phase based on pattern confidence and session count."""
        if profile.session_count < 5:
            profile.learning_phase = LearningPhase.EXPLORATION
        elif profile.session_count < 15:
            profile.learning_phase = LearningPhase.PATTERN_DETECTION
        elif profile.pattern_confidence < self.convergence_threshold:
            profile.learning_phase = LearningPhase.OPTIMIZATION
        else:
            profile.learning_phase = LearningPhase.CONVERGENCE

    async def _store_learning_profile(self, profile: PersonalLearningProfile) -> None:
        """Store learning profile in database."""
        try:
            upsert_query = """
            INSERT INTO learning_profiles (
                user_session_id, workspace_path, attention_span_minutes,
                optimal_result_limit, context_switch_tolerance,
                progressive_disclosure_preference, session_count,
                learning_convergence_score, adaptation_rate
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT (user_session_id, workspace_path)
            DO UPDATE SET
                attention_span_minutes = EXCLUDED.attention_span_minutes,
                optimal_result_limit = EXCLUDED.optimal_result_limit,
                context_switch_tolerance = EXCLUDED.context_switch_tolerance,
                progressive_disclosure_preference = EXCLUDED.progressive_disclosure_preference,
                session_count = EXCLUDED.session_count,
                learning_convergence_score = EXCLUDED.learning_convergence_score,
                adaptation_rate = EXCLUDED.adaptation_rate,
                updated_at = NOW()
            """

            await self.database.execute_query(upsert_query, (
                profile.user_session_id,
                profile.workspace_path,
                profile.average_attention_span_minutes,
                profile.preferred_result_limit,
                profile.context_switch_tolerance,
                profile.progressive_disclosure_preference,
                profile.session_count,
                profile.pattern_confidence,
                profile.adaptation_rate
            ))

        except Exception as e:
            logger.error(f"Failed to store learning profile: {e}")

    # Adaptive Recommendations

    async def _detect_attention_state(
        self, profile: PersonalLearningProfile, current_context: Dict[str, Any] = None
    ) -> AttentionState:
        """Detect current attention state based on learned patterns."""
        if not current_context:
            return AttentionState.MODERATE_FOCUS

        # Analyze current session time vs optimal attention span
        session_duration_minutes = current_context.get('session_duration_minutes', 0)

        if session_duration_minutes > profile.average_attention_span_minutes * 1.5:
            return AttentionState.FATIGUE

        # Check for hyperfocus indicators
        recent_complexity = current_context.get('recent_average_complexity', 0.5)
        if recent_complexity > 0.8 and session_duration_minutes > 60:
            return AttentionState.HYPERFOCUS

        # Check time of day against peak focus times
        current_hour = datetime.now().hour
        if any(abs(current_hour - int(peak_time.split(':')[0])) <= 1
               for peak_time in profile.peak_focus_times):
            return AttentionState.PEAK_FOCUS

        # Default assessment based on session progress
        focus_ratio = session_duration_minutes / profile.average_attention_span_minutes
        if focus_ratio < 0.3:
            return AttentionState.PEAK_FOCUS
        elif focus_ratio < 0.7:
            return AttentionState.MODERATE_FOCUS
        else:
            return AttentionState.LOW_FOCUS

    def _recommend_navigation_mode(
        self, profile: PersonalLearningProfile, attention_state: AttentionState
    ) -> NavigationMode:
        """Recommend navigation mode based on attention state."""
        if attention_state in [AttentionState.LOW_FOCUS, AttentionState.FATIGUE]:
            return NavigationMode.FOCUS
        elif attention_state == AttentionState.PEAK_FOCUS:
            return NavigationMode.COMPREHENSIVE
        else:
            return NavigationMode.EXPLORE

    def _recommend_result_limit(
        self, profile: PersonalLearningProfile, attention_state: AttentionState
    ) -> int:
        """Recommend result limit based on attention state and learned preferences."""
        base_limit = profile.preferred_result_limit

        if attention_state == AttentionState.LOW_FOCUS:
            return max(3, base_limit // 2)
        elif attention_state == AttentionState.FATIGUE:
            return max(3, base_limit // 3)
        elif attention_state == AttentionState.PEAK_FOCUS:
            return min(50, base_limit * 2)
        else:
            return base_limit

    def _recommend_complexity_filter(
        self, profile: PersonalLearningProfile, attention_state: AttentionState
    ) -> float:
        """Recommend complexity filter threshold."""
        base_threshold = profile.optimal_complexity_range[1]

        if attention_state == AttentionState.LOW_FOCUS:
            return min(base_threshold, 0.4)
        elif attention_state == AttentionState.FATIGUE:
            return min(base_threshold, 0.3)
        elif attention_state == AttentionState.PEAK_FOCUS:
            return min(1.0, base_threshold + 0.2)
        else:
            return base_threshold

    def _suggest_break_if_needed(
        self, profile: PersonalLearningProfile, current_context: Dict[str, Any] = None
    ) -> Optional[str]:
        """Suggest break if needed based on learned patterns."""
        if not current_context:
            return None

        session_duration = current_context.get('session_duration_minutes', 0)

        if session_duration > profile.average_attention_span_minutes * 1.2:
            return f"💡 Consider a short break - you've been focused for {session_duration:.0f} minutes"

        return None

    def _recommend_focus_optimization(
        self, profile: PersonalLearningProfile, attention_state: AttentionState
    ) -> List[str]:
        """Recommend focus optimization strategies."""
        recommendations = []

        if attention_state == AttentionState.LOW_FOCUS:
            recommendations.append("🎯 Enable focus mode to reduce distractions")
            recommendations.append("📋 Break current task into smaller steps")

        elif attention_state == AttentionState.FATIGUE:
            recommendations.append("☕ Take a 5-10 minute break")
            recommendations.append("🧘 Try simple breathing exercise")

        elif attention_state == AttentionState.HYPERFOCUS:
            recommendations.append("⏰ Set timer to check bigger picture periodically")
            recommendations.append("🗺️ Review overall progress every 30 minutes")

        return recommendations

    # Utility Functions

    def _generate_sequence_id(self, user_session_id: str) -> str:
        """Generate unique sequence ID."""
        timestamp = datetime.now().isoformat()
        return hashlib.md5(f"{user_session_id}_{timestamp}".encode()).hexdigest()[:12]

    async def _calculate_sequence_effectiveness(
        self, sequence: NavigationSequence, user_satisfaction: Optional[float] = None
    ) -> float:
        """Calculate effectiveness score for a navigation sequence."""
        effectiveness_factors = []

        # Completion status
        if sequence.completion_status == "completed":
            effectiveness_factors.append(1.0)
        elif sequence.completion_status == "partially_completed":
            effectiveness_factors.append(0.6)
        else:
            effectiveness_factors.append(0.2)

        # Duration efficiency (not too fast, not too slow)
        if 30000 <= sequence.total_duration_ms <= 300000:  # 30s to 5min
            effectiveness_factors.append(1.0)
        elif sequence.total_duration_ms < 10000:  # Too fast, might be superficial
            effectiveness_factors.append(0.5)
        else:  # Too slow, might indicate confusion
            effectiveness_factors.append(0.7)

        # Context switching penalty
        if sequence.context_switches <= 3:
            effectiveness_factors.append(1.0)
        elif sequence.context_switches <= 6:
            effectiveness_factors.append(0.8)
        else:
            effectiveness_factors.append(0.5)

        # User satisfaction if provided
        if user_satisfaction is not None:
            effectiveness_factors.append(user_satisfaction)

        return statistics.mean(effectiveness_factors)

    async def _store_navigation_sequence(self, sequence: NavigationSequence) -> None:
        """Store navigation sequence in database."""
        try:
            pattern_signature = self._generate_pattern_signature(sequence)

            insert_query = """
            INSERT INTO navigation_patterns (
                user_session_id, workspace_path, pattern_sequence, sequence_hash,
                pattern_type, context_switches, total_duration_ms, complexity_progression,
                effectiveness_score, completion_status, attention_span_seconds,
                cognitive_fatigue_score, pattern_frequency
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            """

            # Convert actions to dict with datetime serialization
            pattern_data = []
            for action in sequence.actions:
                action_dict = asdict(action)
                # Convert datetime to ISO format string for JSON serialization
                if isinstance(action_dict.get('timestamp'), datetime):
                    action_dict['timestamp'] = action_dict['timestamp'].isoformat()
                pattern_data.append(action_dict)

            # Calculate average complexity for storage (schema expects single REAL, not array)
            avg_complexity = (
                statistics.mean(sequence.complexity_progression)
                if sequence.complexity_progression
                else 0.0
            )

            await self.database.execute_query(insert_query, (
                sequence.user_session_id,
                getattr(sequence, 'workspace_path', 'default'),
                json.dumps(pattern_data),
                pattern_signature,
                "exploration",  # Pattern type
                sequence.context_switches,
                sequence.total_duration_ms,
                avg_complexity,  # Average complexity (REAL type)
                sequence.effectiveness_score,
                sequence.completion_status,
                sequence.attention_span_seconds,
                0.0,  # Cognitive fatigue score (would be calculated)
                1     # Initial frequency
            ))

        except Exception as e:
            logger.error(f"Failed to store navigation sequence: {e}")

    async def _check_learning_convergence(self, user_session_id: str) -> None:
        """Check if learning has converged for user."""
        try:
            # Query recent pattern effectiveness
            query = """
            SELECT AVG(effectiveness_score) as avg_effectiveness,
                   COUNT(*) as pattern_count,
                   STDDEV(effectiveness_score) as effectiveness_variance
            FROM navigation_patterns
            WHERE user_session_id = $1
              AND created_at > NOW() - INTERVAL '7 days'
            """

            results = await self.database.execute_query(query, (user_session_id,))

            if results and results[0]['pattern_count'] >= 10:
                avg_effectiveness = results[0]['avg_effectiveness'] or 0.0
                variance = results[0]['effectiveness_variance'] or 1.0

                # Convergence criteria: high effectiveness, low variance
                if avg_effectiveness > 0.7 and variance < 0.2:
                    # Update learning profile to convergence phase
                    profile_key = f"{user_session_id}_default"  # Simplified workspace
                    if profile_key in self.learning_profiles:
                        profile = self.learning_profiles[profile_key]
                        profile.learning_phase = LearningPhase.CONVERGENCE
                        profile.pattern_confidence = min(1.0, avg_effectiveness)
                        await self._store_learning_profile(profile)

                        logger.info(f"🎯 Learning convergence achieved for user {user_session_id}")

        except Exception as e:
            logger.error(f"Failed to check learning convergence: {e}")


# Convenience functions for integration
async def create_adaptive_learning_engine(
    database: SerenaIntelligenceDatabase,
    graph_operations: SerenaGraphOperations,
    performance_monitor: PerformanceMonitor = None
) -> AdaptiveLearningEngine:
    """Create adaptive learning engine instance."""
    return AdaptiveLearningEngine(database, graph_operations, performance_monitor)


async def simulate_learning_convergence(
    learning_engine: AdaptiveLearningEngine,
    user_session_id: str,
    workspace_path: str,
    days: int = 7
) -> Dict[str, Any]:
    """Simulate learning convergence over specified days."""
    simulation_results = {
        "user_session_id": user_session_id,
        "simulation_days": days,
        "sequences_generated": 0,
        "final_effectiveness": 0.0,
        "convergence_achieved": False,
        "learning_progression": []
    }

    try:
        # Simulate navigation sessions over time
        sessions_per_day = 5  # Average ADHD user sessions

        for day in range(days):
            daily_effectiveness = []

            for session in range(sessions_per_day):
                # Start sequence
                sequence_id = await learning_engine.start_navigation_sequence(
                    user_session_id, workspace_path
                )

                # Simulate navigation actions (improving over time)
                improvement_factor = min(1.0, (day * sessions_per_day + session) / (days * sessions_per_day))
                effectiveness = 0.3 + (improvement_factor * 0.6)  # 0.3 to 0.9

                # Record some actions
                for action_idx in range(3, 8):  # 3-7 actions per sequence
                    await learning_engine.record_navigation_action(
                        sequence_id=sequence_id,
                        action_type="view_element",
                        element_id=action_idx,
                        duration_ms=2000 + (action_idx * 500),
                        success=True
                    )

                # End sequence
                completed_sequence = await learning_engine.end_navigation_sequence(
                    sequence_id, "completed", effectiveness
                )

                daily_effectiveness.append(completed_sequence.effectiveness_score)
                simulation_results["sequences_generated"] += 1

            # Track daily progression
            avg_daily_effectiveness = statistics.mean(daily_effectiveness)
            simulation_results["learning_progression"].append({
                "day": day + 1,
                "average_effectiveness": avg_daily_effectiveness,
                "sequences": len(daily_effectiveness)
            })

        # Get final learning profile
        final_profile = await learning_engine.get_learning_profile(user_session_id, workspace_path)
        simulation_results["final_effectiveness"] = final_profile.pattern_confidence
        simulation_results["convergence_achieved"] = final_profile.learning_phase == LearningPhase.CONVERGENCE

        logger.info(f"📊 Learning simulation complete: "
                   f"convergence {'achieved' if simulation_results['convergence_achieved'] else 'not achieved'}")

        return simulation_results

    except Exception as e:
        logger.error(f"Learning simulation failed: {e}")
        simulation_results["error"] = str(e)
        return simulation_results


if __name__ == "__main__":
    # Quick test when run directly
    async def main():
        print("🧠 Serena Adaptive Learning Engine")
        print("Personal navigation pattern recognition for ADHD optimization")
        print("✅ Module loaded successfully")

    asyncio.run(main())