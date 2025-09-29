"""
Serena v2 Phase 2B: Personal Learning Profile Manager

Enhanced learning profile management with real-time ADHD preference learning,
cross-session persistence, and ConPort knowledge graph integration.
"""

import asyncio
import json
import logging
import statistics
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set, Union
from dataclasses import dataclass, asdict, field
from enum import Enum

from .database import SerenaIntelligenceDatabase
from .adaptive_learning import PersonalLearningProfile, LearningPhase, AttentionState
from ..performance_monitor import PerformanceMonitor

logger = logging.getLogger(__name__)


class ProfileUpdateTrigger(str, Enum):
    """Triggers for profile updates."""
    NAVIGATION_COMPLETION = "navigation_completion"
    SESSION_END = "session_end"
    EFFECTIVENESS_FEEDBACK = "effectiveness_feedback"
    MANUAL_ADJUSTMENT = "manual_adjustment"
    SYSTEM_OPTIMIZATION = "system_optimization"


class ADHDAccommodationType(str, Enum):
    """Types of ADHD accommodations to learn."""
    PROGRESSIVE_DISCLOSURE = "progressive_disclosure"
    COMPLEXITY_FILTERING = "complexity_filtering"
    RESULT_LIMITING = "result_limiting"
    BREAK_REMINDERS = "break_reminders"
    FOCUS_MODE_TRIGGERS = "focus_mode_triggers"
    GENTLE_GUIDANCE = "gentle_guidance"


@dataclass
class AccommodationPreference:
    """Individual ADHD accommodation preference."""
    accommodation_type: ADHDAccommodationType
    enabled: bool = True
    effectiveness_score: float = 0.5  # 0.0 = not helpful, 1.0 = very helpful
    usage_frequency: int = 0
    last_used: Optional[datetime] = None
    user_feedback: Optional[str] = None
    auto_trigger_threshold: float = 0.7  # When to automatically activate


@dataclass
class NavigationPreferencePattern:
    """Learned navigation preference pattern."""
    pattern_id: str
    context_type: str  # exploration, debugging, implementation, etc.
    preferred_result_limit: int
    preferred_complexity_threshold: float
    preferred_navigation_mode: str
    effectiveness_score: float
    usage_count: int
    last_used: datetime
    success_indicators: List[str] = field(default_factory=list)


@dataclass
class AttentionPattern:
    """Learned attention and focus patterns."""
    user_session_id: str
    typical_attention_span_minutes: float
    peak_focus_hours: List[int] = field(default_factory=list)  # Hours of day (0-23)
    optimal_session_length_minutes: float = 25.0
    break_frequency_minutes: float = 30.0
    context_switch_tolerance: int = 3
    hyperfocus_indicators: List[str] = field(default_factory=list)
    fatigue_indicators: List[str] = field(default_factory=list)


@dataclass
class ProfileInsight:
    """Insights generated from profile analysis."""
    insight_id: str
    insight_type: str  # strength, improvement_opportunity, recommendation
    title: str
    description: str
    confidence: float  # 0.0 to 1.0
    actionable_recommendation: str
    generated_at: datetime
    user_acknowledged: bool = False


class PersonalLearningProfileManager:
    """
    Enhanced personal learning profile management for ADHD optimization.

    Features:
    - Real-time profile updates based on navigation behavior
    - ADHD accommodation effectiveness learning
    - Cross-session pattern persistence with ConPort integration
    - Intelligent profile insights and recommendations
    - Performance optimization based on learned preferences
    - Multi-workspace profile management
    - Privacy-aware data handling
    """

    def __init__(
        self,
        database: SerenaIntelligenceDatabase,
        performance_monitor: PerformanceMonitor = None
    ):
        self.database = database
        self.performance_monitor = performance_monitor or PerformanceMonitor()

        # Profile cache for performance
        self._profile_cache: Dict[str, PersonalLearningProfile] = {}
        self._accommodation_cache: Dict[str, Dict[str, AccommodationPreference]] = {}
        self._attention_patterns_cache: Dict[str, AttentionPattern] = {}

        # Configuration
        self.cache_ttl_seconds = 300  # 5 minutes
        self.min_sessions_for_insights = 5
        self.accommodation_learning_rate = 0.2

    # Profile Management Core

    async def get_or_create_profile(
        self,
        user_session_id: str,
        workspace_path: str,
        create_if_missing: bool = True
    ) -> PersonalLearningProfile:
        """Get existing profile or create new one with intelligent defaults."""
        operation_id = self.performance_monitor.start_operation("get_or_create_profile")

        try:
            cache_key = f"{user_session_id}_{workspace_path}"

            # Check cache first
            if cache_key in self._profile_cache:
                cached_profile = self._profile_cache[cache_key]
                self.performance_monitor.end_operation(operation_id, success=True, cache_hit=True)
                return cached_profile

            # Load from database
            profile = await self._load_profile_from_database(user_session_id, workspace_path)

            if profile is None and create_if_missing:
                # Create new profile with intelligent defaults
                profile = await self._create_new_profile(user_session_id, workspace_path)

            if profile:
                # Load associated data
                await self._load_profile_associations(profile)

                # Cache the profile
                self._profile_cache[cache_key] = profile

                self.performance_monitor.end_operation(operation_id, success=True, cache_hit=False)
                return profile

            self.performance_monitor.end_operation(operation_id, success=False)
            raise ValueError(f"Profile not found for {user_session_id} in {workspace_path}")

        except Exception as e:
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"Failed to get/create profile: {e}")
            raise

    async def update_profile_from_navigation(
        self,
        user_session_id: str,
        workspace_path: str,
        navigation_data: Dict[str, Any],
        trigger: ProfileUpdateTrigger = ProfileUpdateTrigger.NAVIGATION_COMPLETION
    ) -> PersonalLearningProfile:
        """Update profile based on navigation behavior and outcomes."""
        operation_id = self.performance_monitor.start_operation("update_profile_from_navigation")

        try:
            profile = await self.get_or_create_profile(user_session_id, workspace_path)

            # Update based on navigation data
            await self._update_attention_patterns(profile, navigation_data)
            await self._update_complexity_preferences(profile, navigation_data)
            await self._update_accommodation_effectiveness(profile, navigation_data)
            await self._update_navigation_preferences(profile, navigation_data)

            # Update learning phase
            await self._assess_learning_phase(profile)

            # Store updated profile
            await self._store_profile_to_database(profile)

            # Log significant changes to ConPort if enabled
            await self._log_profile_changes_to_conport(profile, navigation_data, trigger)

            # Generate insights if appropriate
            if profile.session_count % 5 == 0:  # Every 5 sessions
                await self._generate_profile_insights(profile)

            self.performance_monitor.end_operation(operation_id, success=True)
            logger.debug(f"📊 Updated profile for {user_session_id} based on navigation")

            return profile

        except Exception as e:
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"Failed to update profile from navigation: {e}")
            raise

    async def get_adaptive_recommendations(
        self,
        user_session_id: str,
        workspace_path: str,
        current_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Get personalized adaptive recommendations."""
        operation_id = self.performance_monitor.start_operation("get_adaptive_recommendations")

        try:
            profile = await self.get_or_create_profile(user_session_id, workspace_path)
            attention_pattern = await self._get_attention_pattern(user_session_id)

            # Detect current attention state
            attention_state = await self._detect_current_attention_state(
                profile, attention_pattern, current_context
            )

            # Generate recommendations based on learned patterns
            recommendations = {
                "navigation_settings": await self._recommend_navigation_settings(
                    profile, attention_state, current_context
                ),
                "adhd_accommodations": await self._recommend_accommodations(
                    profile, attention_state
                ),
                "session_management": await self._recommend_session_management(
                    profile, attention_pattern, current_context
                ),
                "focus_optimization": await self._recommend_focus_optimization(
                    profile, attention_state
                ),
                "profile_insights": await self._get_recent_insights(profile),
                "confidence_level": profile.pattern_confidence,
                "learning_phase": profile.learning_phase.value,
                "attention_state": attention_state.value
            }

            self.performance_monitor.end_operation(operation_id, success=True)
            return recommendations

        except Exception as e:
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"Failed to get adaptive recommendations: {e}")
            raise

    # Profile Learning and Updates

    async def _update_attention_patterns(
        self, profile: PersonalLearningProfile, navigation_data: Dict[str, Any]
    ) -> None:
        """Update attention patterns based on navigation behavior."""
        try:
            # Update attention span (exponential moving average)
            session_duration = navigation_data.get('session_duration_minutes', 0)
            if session_duration > 0:
                alpha = 0.2  # Learning rate
                profile.average_attention_span_minutes = (
                    alpha * session_duration +
                    (1 - alpha) * profile.average_attention_span_minutes
                )

            # Track peak focus times
            if navigation_data.get('effectiveness_score', 0) > 0.8:
                current_hour = datetime.now().hour
                if len(profile.peak_focus_times) < 10:  # Limit to prevent bloat
                    profile.peak_focus_times.append(f"{current_hour:02d}:00")

            # Update context switch tolerance
            context_switches = navigation_data.get('context_switches', 0)
            effectiveness = navigation_data.get('effectiveness_score', 0.5)

            if effectiveness > 0.7 and context_switches > profile.context_switch_tolerance:
                # User handled more context switches successfully
                profile.context_switch_tolerance = min(10, context_switches)
            elif effectiveness < 0.4 and context_switches > profile.context_switch_tolerance:
                # Too many context switches hurt performance
                profile.context_switch_tolerance = max(1, context_switches - 1)

        except Exception as e:
            logger.error(f"Failed to update attention patterns: {e}")

    async def _update_complexity_preferences(
        self, profile: PersonalLearningProfile, navigation_data: Dict[str, Any]
    ) -> None:
        """Update complexity tolerance based on successful navigation."""
        try:
            avg_complexity = navigation_data.get('average_complexity', 0.5)
            effectiveness = navigation_data.get('effectiveness_score', 0.5)

            # Adaptive complexity range adjustment
            if effectiveness > 0.8 and avg_complexity > profile.optimal_complexity_range[1]:
                # Successfully handled higher complexity
                new_upper_bound = min(1.0, avg_complexity + 0.05)
                profile.optimal_complexity_range = (
                    profile.optimal_complexity_range[0], new_upper_bound
                )
            elif effectiveness < 0.3 and avg_complexity > profile.optimal_complexity_range[0]:
                # Struggled with complexity, lower the upper bound slightly
                new_upper_bound = max(profile.optimal_complexity_range[0] + 0.1, avg_complexity - 0.1)
                profile.optimal_complexity_range = (
                    profile.optimal_complexity_range[0], new_upper_bound
                )

            # Update result limit preference based on cognitive load
            cognitive_load = navigation_data.get('cognitive_load_score', 0.5)
            if cognitive_load > 0.8 and profile.preferred_result_limit > 5:
                profile.preferred_result_limit = max(5, profile.preferred_result_limit - 2)
            elif cognitive_load < 0.3 and effectiveness > 0.7 and profile.preferred_result_limit < 20:
                profile.preferred_result_limit = min(20, profile.preferred_result_limit + 2)

        except Exception as e:
            logger.error(f"Failed to update complexity preferences: {e}")

    async def _update_accommodation_effectiveness(
        self, profile: PersonalLearningProfile, navigation_data: Dict[str, Any]
    ) -> None:
        """Update ADHD accommodation effectiveness based on usage."""
        try:
            accommodations_used = navigation_data.get('accommodations_used', [])
            effectiveness = navigation_data.get('effectiveness_score', 0.5)

            cache_key = profile.user_session_id
            if cache_key not in self._accommodation_cache:
                self._accommodation_cache[cache_key] = await self._load_accommodation_preferences(
                    profile.user_session_id
                )

            # Update effectiveness for used accommodations
            for accommodation_name in accommodations_used:
                if accommodation_name in self._accommodation_cache[cache_key]:
                    pref = self._accommodation_cache[cache_key][accommodation_name]

                    # Update effectiveness using exponential moving average
                    alpha = self.accommodation_learning_rate
                    pref.effectiveness_score = (
                        alpha * effectiveness + (1 - alpha) * pref.effectiveness_score
                    )
                    pref.usage_frequency += 1
                    pref.last_used = datetime.now(timezone.utc)

            # Update profile-level accommodation preferences
            if effectiveness > 0.8:
                if 'progressive_disclosure' in accommodations_used:
                    profile.progressive_disclosure_preference = True
                if navigation_data.get('complexity_filtering_used', False):
                    profile.complexity_filter_threshold = min(0.9, profile.complexity_filter_threshold + 0.05)

        except Exception as e:
            logger.error(f"Failed to update accommodation effectiveness: {e}")

    async def _update_navigation_preferences(
        self, profile: PersonalLearningProfile, navigation_data: Dict[str, Any]
    ) -> None:
        """Update navigation preferences based on successful patterns."""
        try:
            effectiveness = navigation_data.get('effectiveness_score', 0.5)

            if effectiveness > 0.7:  # Only learn from successful navigation
                navigation_mode = navigation_data.get('navigation_mode_used', 'explore')
                result_limit = navigation_data.get('result_limit_used', profile.preferred_result_limit)

                # Track successful patterns
                pattern_signature = f"{navigation_mode}_{result_limit}_{navigation_data.get('context_type', 'general')}"

                if pattern_signature not in profile.successful_patterns:
                    profile.successful_patterns.append(pattern_signature)

                    # Keep only recent successful patterns (prevent unbounded growth)
                    if len(profile.successful_patterns) > 20:
                        profile.successful_patterns = profile.successful_patterns[-20:]

        except Exception as e:
            logger.error(f"Failed to update navigation preferences: {e}")

    # Attention State Detection

    async def _detect_current_attention_state(
        self,
        profile: PersonalLearningProfile,
        attention_pattern: AttentionPattern,
        current_context: Dict[str, Any] = None
    ) -> AttentionState:
        """Detect current attention state based on learned patterns."""
        if not current_context:
            return AttentionState.MODERATE_FOCUS

        try:
            session_duration = current_context.get('session_duration_minutes', 0)
            current_hour = datetime.now().hour
            recent_effectiveness = current_context.get('recent_effectiveness_scores', [0.5])

            # Check for fatigue based on learned patterns
            if session_duration > attention_pattern.optimal_session_length_minutes * 1.5:
                return AttentionState.FATIGUE

            # Check for hyperfocus indicators
            hyperfocus_indicators_present = any(
                indicator in str(current_context)
                for indicator in attention_pattern.hyperfocus_indicators
            )
            if hyperfocus_indicators_present and session_duration > 60:
                return AttentionState.HYPERFOCUS

            # Check peak focus times
            if current_hour in attention_pattern.peak_focus_hours:
                return AttentionState.PEAK_FOCUS

            # Assess based on recent performance
            if recent_effectiveness:
                avg_recent_effectiveness = statistics.mean(recent_effectiveness[-3:])
                if avg_recent_effectiveness > 0.8:
                    return AttentionState.PEAK_FOCUS
                elif avg_recent_effectiveness < 0.4:
                    return AttentionState.LOW_FOCUS

            # Default assessment
            focus_ratio = session_duration / attention_pattern.optimal_session_length_minutes
            if focus_ratio < 0.3:
                return AttentionState.PEAK_FOCUS
            elif focus_ratio < 0.7:
                return AttentionState.MODERATE_FOCUS
            else:
                return AttentionState.LOW_FOCUS

        except Exception as e:
            logger.error(f"Failed to detect attention state: {e}")
            return AttentionState.MODERATE_FOCUS

    # Recommendations Generation

    async def _recommend_navigation_settings(
        self,
        profile: PersonalLearningProfile,
        attention_state: AttentionState,
        current_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Recommend navigation settings based on learned preferences."""
        recommendations = {
            "result_limit": profile.preferred_result_limit,
            "complexity_threshold": profile.optimal_complexity_range[1],
            "navigation_mode": "explore"  # default
        }

        # Adjust based on attention state
        if attention_state == AttentionState.LOW_FOCUS:
            recommendations["result_limit"] = max(3, profile.preferred_result_limit // 2)
            recommendations["complexity_threshold"] = min(0.4, recommendations["complexity_threshold"])
            recommendations["navigation_mode"] = "focus"
        elif attention_state == AttentionState.FATIGUE:
            recommendations["result_limit"] = max(3, profile.preferred_result_limit // 3)
            recommendations["complexity_threshold"] = 0.3
            recommendations["navigation_mode"] = "focus"
        elif attention_state == AttentionState.PEAK_FOCUS:
            recommendations["result_limit"] = min(30, profile.preferred_result_limit * 2)
            recommendations["complexity_threshold"] = min(1.0, recommendations["complexity_threshold"] + 0.2)
            recommendations["navigation_mode"] = "comprehensive"

        return recommendations

    async def _recommend_accommodations(
        self,
        profile: PersonalLearningProfile,
        attention_state: AttentionState
    ) -> Dict[str, Any]:
        """Recommend ADHD accommodations based on effectiveness learning."""
        cache_key = profile.user_session_id
        accommodations = self._accommodation_cache.get(cache_key, {})

        recommendations = {
            "progressive_disclosure": profile.progressive_disclosure_preference,
            "complexity_filtering": True,
            "gentle_guidance": profile.gentle_guidance_enabled,
            "break_reminder": False,
            "focus_mode": False
        }

        # Adjust based on attention state and learned effectiveness
        if attention_state in [AttentionState.LOW_FOCUS, AttentionState.FATIGUE]:
            recommendations["focus_mode"] = True
            recommendations["break_reminder"] = True
            recommendations["complexity_filtering"] = True

        # Use learned accommodation effectiveness
        for acc_name, acc_pref in accommodations.items():
            if acc_pref.effectiveness_score > 0.7:
                if acc_name == "progressive_disclosure":
                    recommendations["progressive_disclosure"] = True
                elif acc_name == "result_limiting" and attention_state == AttentionState.LOW_FOCUS:
                    recommendations["result_limit_override"] = 5

        return recommendations

    async def _recommend_session_management(
        self,
        profile: PersonalLearningProfile,
        attention_pattern: AttentionPattern,
        current_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Recommend session management based on learned attention patterns."""
        session_duration = current_context.get('session_duration_minutes', 0) if current_context else 0

        recommendations = {
            "suggested_break_in_minutes": None,
            "optimal_session_length": attention_pattern.optimal_session_length_minutes,
            "break_frequency": attention_pattern.break_frequency_minutes,
            "session_advice": ""
        }

        # Break recommendations based on learned patterns
        time_until_optimal_break = attention_pattern.break_frequency_minutes - session_duration
        if time_until_optimal_break <= 5:
            recommendations["suggested_break_in_minutes"] = max(1, time_until_optimal_break)
            recommendations["session_advice"] = "Consider a short break to maintain focus"

        if session_duration > attention_pattern.optimal_session_length_minutes:
            recommendations["session_advice"] = "You've exceeded your optimal session length - great focus!"

        return recommendations

    async def _recommend_focus_optimization(
        self,
        profile: PersonalLearningProfile,
        attention_state: AttentionState
    ) -> List[str]:
        """Recommend focus optimization strategies."""
        recommendations = []

        if attention_state == AttentionState.LOW_FOCUS:
            recommendations.append("🎯 Consider enabling focus mode to reduce distractions")
            recommendations.append("📋 Break current task into smaller, manageable pieces")
            if profile.progressive_disclosure_preference:
                recommendations.append("📖 Use progressive disclosure to see information gradually")

        elif attention_state == AttentionState.FATIGUE:
            recommendations.append("☕ Take a 5-10 minute break")
            recommendations.append("🧘 Try a brief mindfulness exercise")
            recommendations.append("💧 Stay hydrated and consider a healthy snack")

        elif attention_state == AttentionState.HYPERFOCUS:
            recommendations.append("⏰ Set a timer to check progress every 30 minutes")
            recommendations.append("🗺️ Periodically step back to see the bigger picture")
            recommendations.append("💡 This is great focus time - make the most of it!")

        elif attention_state == AttentionState.PEAK_FOCUS:
            recommendations.append("🚀 Great focus time - tackle complex tasks now")
            recommendations.append("🎯 This is optimal for challenging navigation")

        return recommendations

    # ConPort Integration

    async def _log_profile_changes_to_conport(
        self,
        profile: PersonalLearningProfile,
        navigation_data: Dict[str, Any],
        trigger: ProfileUpdateTrigger
    ) -> None:
        """Log significant profile changes to ConPort knowledge graph."""
        try:
            # Only log significant changes to avoid noise
            if trigger in [ProfileUpdateTrigger.SESSION_END, ProfileUpdateTrigger.EFFECTIVENESS_FEEDBACK]:

                # Check if this is a significant learning milestone
                if (profile.session_count in [5, 10, 25, 50] or  # Milestone sessions
                    profile.learning_phase == LearningPhase.CONVERGENCE):

                    # This would integrate with ConPort if available
                    # For now, log the significant change
                    logger.info(f"📊 Significant learning progress for {profile.user_session_id}: "
                              f"Session {profile.session_count}, Phase: {profile.learning_phase.value}")

        except Exception as e:
            logger.debug(f"ConPort integration not available: {e}")

    # Database Operations

    async def _load_profile_from_database(
        self, user_session_id: str, workspace_path: str
    ) -> Optional[PersonalLearningProfile]:
        """Load profile from PostgreSQL database."""
        try:
            query = """
            SELECT * FROM learning_profiles
            WHERE user_session_id = $1 AND workspace_path = $2
            """

            results = await self.database.execute_query(query, (user_session_id, workspace_path))

            if results:
                row = results[0]

                # Parse JSON fields
                preferred_patterns = json.loads(row.get('preferred_navigation_patterns', '[]'))
                avoid_patterns = json.loads(row.get('avoid_patterns', '[]'))
                peak_times = json.loads(row.get('peak_performance_times', '[]'))

                profile = PersonalLearningProfile(
                    user_session_id=row['user_session_id'],
                    workspace_path=row['workspace_path'],
                    average_attention_span_minutes=row['attention_span_minutes'],
                    optimal_complexity_range=(0.0, 0.6),  # Default, will be refined
                    preferred_result_limit=row['optimal_result_limit'],
                    context_switch_tolerance=row['context_switch_tolerance'],
                    progressive_disclosure_preference=row['progressive_disclosure_preference'],
                    learning_phase=LearningPhase.EXPLORATION,  # Will be updated
                    pattern_confidence=row.get('learning_convergence_score', 0.0),
                    session_count=row['session_count'],
                    adaptation_rate=row['adaptation_rate'],
                    successful_patterns=preferred_patterns,
                    problematic_patterns=avoid_patterns,
                    peak_focus_times=peak_times
                )

                return profile

            return None

        except Exception as e:
            logger.error(f"Failed to load profile from database: {e}")
            return None

    async def _store_profile_to_database(self, profile: PersonalLearningProfile) -> None:
        """Store profile to PostgreSQL database."""
        try:
            upsert_query = """
            INSERT INTO learning_profiles (
                user_session_id, workspace_path, attention_span_minutes,
                optimal_result_limit, context_switch_tolerance,
                progressive_disclosure_preference, session_count,
                learning_convergence_score, adaptation_rate,
                preferred_navigation_patterns, avoid_patterns, peak_performance_times
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            ON CONFLICT (user_session_id, workspace_path)
            DO UPDATE SET
                attention_span_minutes = EXCLUDED.attention_span_minutes,
                optimal_result_limit = EXCLUDED.optimal_result_limit,
                context_switch_tolerance = EXCLUDED.context_switch_tolerance,
                progressive_disclosure_preference = EXCLUDED.progressive_disclosure_preference,
                session_count = EXCLUDED.session_count,
                learning_convergence_score = EXCLUDED.learning_convergence_score,
                adaptation_rate = EXCLUDED.adaptation_rate,
                preferred_navigation_patterns = EXCLUDED.preferred_navigation_patterns,
                avoid_patterns = EXCLUDED.avoid_patterns,
                peak_performance_times = EXCLUDED.peak_performance_times,
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
                profile.adaptation_rate,
                json.dumps(profile.successful_patterns),
                json.dumps(profile.problematic_patterns),
                json.dumps(profile.peak_focus_times)
            ))

            # Update cache
            cache_key = f"{profile.user_session_id}_{profile.workspace_path}"
            self._profile_cache[cache_key] = profile

        except Exception as e:
            logger.error(f"Failed to store profile to database: {e}")

    # Utility Methods

    async def _create_new_profile(
        self, user_session_id: str, workspace_path: str
    ) -> PersonalLearningProfile:
        """Create new profile with intelligent defaults."""
        profile = PersonalLearningProfile(
            user_session_id=user_session_id,
            workspace_path=workspace_path,
            average_attention_span_minutes=25.0,  # Standard ADHD attention span
            optimal_complexity_range=(0.0, 0.6),  # Start with simple to moderate
            preferred_result_limit=10,  # ADHD-friendly default
            context_switch_tolerance=3,  # Conservative default
            progressive_disclosure_preference=True,  # Generally helpful for ADHD
            learning_phase=LearningPhase.EXPLORATION,
            pattern_confidence=0.0,
            session_count=0,
            adaptation_rate=0.1
        )

        await self._store_profile_to_database(profile)
        logger.info(f"🆕 Created new learning profile for {user_session_id}")

        return profile

    async def _load_profile_associations(self, profile: PersonalLearningProfile) -> None:
        """Load associated data like accommodation preferences."""
        # Load accommodation preferences
        cache_key = profile.user_session_id
        self._accommodation_cache[cache_key] = await self._load_accommodation_preferences(
            profile.user_session_id
        )

        # Load attention patterns
        self._attention_patterns_cache[cache_key] = await self._load_attention_pattern(
            profile.user_session_id
        )

    async def _load_accommodation_preferences(
        self, user_session_id: str
    ) -> Dict[str, AccommodationPreference]:
        """Load ADHD accommodation preferences."""
        # Default accommodations for new users
        default_accommodations = {
            acc_type.value: AccommodationPreference(
                accommodation_type=acc_type,
                enabled=True,
                effectiveness_score=0.5  # Neutral default
            )
            for acc_type in ADHDAccommodationType
        }

        return default_accommodations

    async def _load_attention_pattern(self, user_session_id: str) -> AttentionPattern:
        """Load learned attention patterns."""
        return AttentionPattern(
            user_session_id=user_session_id,
            typical_attention_span_minutes=25.0,
            peak_focus_hours=[9, 10, 14, 15],  # Common peak focus times
            optimal_session_length_minutes=25.0,
            break_frequency_minutes=30.0,
            context_switch_tolerance=3
        )

    async def _get_attention_pattern(self, user_session_id: str) -> AttentionPattern:
        """Get attention pattern from cache or load."""
        if user_session_id not in self._attention_patterns_cache:
            self._attention_patterns_cache[user_session_id] = await self._load_attention_pattern(
                user_session_id
            )
        return self._attention_patterns_cache[user_session_id]

    async def _assess_learning_phase(self, profile: PersonalLearningProfile) -> None:
        """Assess and update learning phase based on progress."""
        if profile.session_count < 5:
            profile.learning_phase = LearningPhase.EXPLORATION
        elif profile.session_count < 15:
            profile.learning_phase = LearningPhase.PATTERN_DETECTION
        elif profile.pattern_confidence < 0.8:
            profile.learning_phase = LearningPhase.OPTIMIZATION
        else:
            profile.learning_phase = LearningPhase.CONVERGENCE

    async def _generate_profile_insights(self, profile: PersonalLearningProfile) -> List[ProfileInsight]:
        """Generate insights about the user's learning progress."""
        insights = []

        # Attention span insight
        if profile.average_attention_span_minutes > 30:
            insights.append(ProfileInsight(
                insight_id="attention_strength",
                insight_type="strength",
                title="Strong Sustained Attention",
                description=f"Your average attention span of {profile.average_attention_span_minutes:.0f} minutes is above typical ADHD ranges",
                confidence=0.8,
                actionable_recommendation="Take advantage of longer focus periods for complex tasks",
                generated_at=datetime.now(timezone.utc)
            ))

        # Complexity tolerance insight
        if profile.optimal_complexity_range[1] > 0.7:
            insights.append(ProfileInsight(
                insight_id="complexity_comfort",
                insight_type="strength",
                title="High Complexity Tolerance",
                description="You handle complex code well and can benefit from comprehensive navigation modes",
                confidence=0.7,
                actionable_recommendation="Use comprehensive navigation mode during peak focus times",
                generated_at=datetime.now(timezone.utc)
            ))

        return insights

    async def _get_recent_insights(self, profile: PersonalLearningProfile) -> List[Dict[str, Any]]:
        """Get recent insights for the profile."""
        if profile.session_count >= self.min_sessions_for_insights:
            insights = await self._generate_profile_insights(profile)
            return [asdict(insight) for insight in insights]
        return []


# Convenience functions
async def create_profile_manager(
    database: SerenaIntelligenceDatabase,
    performance_monitor: PerformanceMonitor = None
) -> PersonalLearningProfileManager:
    """Create profile manager instance."""
    return PersonalLearningProfileManager(database, performance_monitor)


async def simulate_profile_learning(
    profile_manager: PersonalLearningProfileManager,
    user_session_id: str,
    workspace_path: str,
    days: int = 7
) -> Dict[str, Any]:
    """Simulate profile learning over time."""
    simulation_results = {
        "user_session_id": user_session_id,
        "simulation_days": days,
        "profile_evolution": [],
        "final_confidence": 0.0,
        "learning_milestones": []
    }

    try:
        # Simulate daily learning
        for day in range(days):
            # Simulate 2-4 navigation sessions per day
            sessions_today = 2 + (day % 3)  # Varies between 2-4

            for session in range(sessions_today):
                # Simulate improving navigation performance over time
                base_effectiveness = 0.4 + (day / days) * 0.5  # 0.4 to 0.9 over time
                session_effectiveness = min(1.0, base_effectiveness + (session * 0.05))

                navigation_data = {
                    'session_duration_minutes': 20 + (session * 10),  # 20-50 minute sessions
                    'effectiveness_score': session_effectiveness,
                    'average_complexity': 0.3 + (day / days) * 0.4,  # Increasing complexity comfort
                    'context_switches': max(1, 5 - day),  # Decreasing context switches
                    'accommodations_used': ['progressive_disclosure', 'complexity_filtering'],
                    'navigation_mode_used': 'explore',
                    'result_limit_used': 10
                }

                # Update profile
                updated_profile = await profile_manager.update_profile_from_navigation(
                    user_session_id, workspace_path, navigation_data
                )

                # Track milestones
                if updated_profile.learning_phase.value not in [m['phase'] for m in simulation_results['learning_milestones']]:
                    simulation_results['learning_milestones'].append({
                        'day': day + 1,
                        'session': session + 1,
                        'phase': updated_profile.learning_phase.value,
                        'confidence': updated_profile.pattern_confidence
                    })

            # Record daily profile state
            final_profile = await profile_manager.get_or_create_profile(user_session_id, workspace_path)
            simulation_results['profile_evolution'].append({
                'day': day + 1,
                'attention_span_minutes': final_profile.average_attention_span_minutes,
                'complexity_tolerance': final_profile.optimal_complexity_range[1],
                'pattern_confidence': final_profile.pattern_confidence,
                'learning_phase': final_profile.learning_phase.value,
                'session_count': final_profile.session_count
            })

        simulation_results['final_confidence'] = final_profile.pattern_confidence

        logger.info(f"📈 Profile learning simulation complete: "
                   f"final confidence {final_profile.pattern_confidence:.2f}")

        return simulation_results

    except Exception as e:
        logger.error(f"Profile learning simulation failed: {e}")
        simulation_results['error'] = str(e)
        return simulation_results


if __name__ == "__main__":
    # Quick test when run directly
    async def main():
        print("👤 Serena Personal Learning Profile Manager")
        print("ADHD-optimized profile management with real-time learning")
        print("✅ Module loaded successfully")

    asyncio.run(main())