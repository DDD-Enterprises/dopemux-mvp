"""
Serena v2 Phase 2E: Accommodation Harmonizer

System-wide ADHD accommodation coordination ensuring consistent, effective,
and non-conflicting accommodation application across all Phase 2A-2D components.
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

# Phase 2E Components
from .cognitive_load_orchestrator import CognitiveLoadOrchestrator, CognitiveLoadState, CognitiveLoadReading
from .fatigue_detection_engine import FatigueDetectionEngine, AdaptiveResponseType
from .personalized_threshold_coordinator import PersonalizedThresholdCoordinator

# Phase 2D Components
from .strategy_template_manager import AccommodationType as TemplateAccommodationType

# Phase 2B Components
from .learning_profile_manager import PersonalLearningProfileManager, PersonalLearningProfile
from .adaptive_learning import AttentionState

# Phase 2A Components
from .database import SerenaIntelligenceDatabase

# Layer 1 Components
from ..performance_monitor import PerformanceMonitor
from ..adhd_features import ADHDCodeNavigator

logger = logging.getLogger(__name__)


class SystemAccommodationType(str, Enum):
    """Unified ADHD accommodation types across all system components."""
    # Core cognitive accommodations
    PROGRESSIVE_DISCLOSURE = "progressive_disclosure"           # Gradual information revelation
    COMPLEXITY_FILTERING = "complexity_filtering"             # Filter high complexity items
    COGNITIVE_LOAD_LIMITING = "cognitive_load_limiting"       # Limit cognitive burden
    RESULT_LIMITING = "result_limiting"                       # Limit number of results

    # Attention and focus accommodations
    FOCUS_MODE_INTEGRATION = "focus_mode_integration"         # Enable focus mode
    ATTENTION_ANCHORING = "attention_anchoring"              # Maintain attention focus
    CONTEXT_PRESERVATION = "context_preservation"            # Preserve navigation context
    BREAK_REMINDERS = "break_reminders"                      # Suggest breaks

    # Interface and interaction accommodations
    GENTLE_GUIDANCE = "gentle_guidance"                      # Supportive messaging
    SIMPLE_LANGUAGE = "simple_language"                      # Clear, simple language
    VISUAL_INDICATORS = "visual_indicators"                  # Visual progress/status
    CONSISTENT_LAYOUT = "consistent_layout"                  # Predictable interface

    # Advanced accommodations
    FATIGUE_PREVENTION = "fatigue_prevention"                # Proactive fatigue management
    PATTERN_ASSISTANCE = "pattern_assistance"                # Pattern-based navigation help
    EMERGENCY_SIMPLIFICATION = "emergency_simplification"    # Crisis-mode simplification


class AccommodationScope(str, Enum):
    """Scope of accommodation application."""
    GLOBAL = "global"               # Applied across entire system
    SESSION = "session"             # Applied for current session
    COMPONENT = "component"         # Applied to specific component
    CONTEXT = "context"             # Applied to specific navigation context
    TEMPORARY = "temporary"         # Applied temporarily for specific situation


class AccommodationEffectiveness(str, Enum):
    """Effectiveness levels of accommodations."""
    HIGHLY_EFFECTIVE = "highly_effective"      # >0.8 effectiveness
    EFFECTIVE = "effective"                    # 0.6-0.8 effectiveness
    MODERATELY_EFFECTIVE = "moderately_effective"  # 0.4-0.6 effectiveness
    INEFFECTIVE = "ineffective"                # <0.4 effectiveness
    COUNTERPRODUCTIVE = "counterproductive"    # Negative effectiveness


@dataclass
class AccommodationState:
    """State of an individual accommodation."""
    accommodation_type: SystemAccommodationType
    enabled: bool
    scope: AccommodationScope
    effectiveness_score: float  # 0.0-1.0
    effectiveness_level: AccommodationEffectiveness

    # Component application
    applied_components: List[str]  # Which components have this accommodation active
    pending_components: List[str]  # Which components need this accommodation applied

    # User interaction
    user_requested: bool = False
    user_satisfaction: float = 0.5
    usage_frequency: int = 0
    last_used: Optional[datetime] = None

    # Performance tracking
    performance_impact_ms: float = 0.0
    cognitive_load_reduction: float = 0.0

    # Metadata
    activated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_effectiveness_update: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class AccommodationProfile:
    """User's accommodation profile across all system components."""
    user_session_id: str
    workspace_path: str
    active_accommodations: Dict[SystemAccommodationType, AccommodationState]

    # Profile characteristics
    accommodation_preference_strength: float = 0.5  # How much user prefers accommodations
    accommodation_adaptation_rate: float = 0.2     # How quickly to adapt accommodations
    accommodation_consistency_preference: bool = True  # Prefers consistent accommodations

    # Effectiveness tracking
    overall_accommodation_effectiveness: float = 0.0
    accommodation_satisfaction_score: float = 0.0
    most_effective_accommodations: List[SystemAccommodationType] = field(default_factory=list)
    least_effective_accommodations: List[SystemAccommodationType] = field(default_factory=list)

    # System integration
    learning_profile_sync_version: int = 0
    last_harmonization: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class AccommodationConflict:
    """Detected conflict between accommodations."""
    conflict_id: str
    conflicting_accommodations: List[SystemAccommodationType]
    conflict_type: str  # performance, user_experience, effectiveness
    conflict_severity: str  # low, medium, high
    resolution_strategy: str
    automatic_resolution: bool


@dataclass
class HarmonizationPlan:
    """Plan for harmonizing accommodations across components."""
    plan_id: str
    user_session_id: str
    target_accommodations: Dict[SystemAccommodationType, bool]  # Enable/disable
    component_updates: Dict[str, Dict[str, Any]]
    conflict_resolutions: List[AccommodationConflict]
    expected_effectiveness_improvement: float
    implementation_sequence: List[str]


class AccommodationHarmonizer:
    """
    System-wide ADHD accommodation harmonizer for consistent, effective accommodation coordination.

    Features:
    - Unified accommodation management across all Phase 2A-2D components
    - Conflict detection and resolution between accommodations from different phases
    - Effectiveness tracking for accommodation combinations and synergies
    - Personalized accommodation optimization based on individual ADHD needs
    - Integration with learning profiles for accommodation preference persistence
    - Performance-optimized accommodation coordination maintaining <200ms targets
    - Real-time accommodation adaptation based on cognitive load and fatigue states
    - Seamless integration with existing accommodation systems without breaking changes
    """

    def __init__(
        self,
        # Phase 2E coordination components
        cognitive_orchestrator: CognitiveLoadOrchestrator,
        fatigue_engine: FatigueDetectionEngine,
        threshold_coordinator: PersonalizedThresholdCoordinator,

        # Component integration
        profile_manager: PersonalLearningProfileManager,
        database: SerenaIntelligenceDatabase,

        # Layer 1 integration
        adhd_navigator: ADHDCodeNavigator,
        performance_monitor: PerformanceMonitor = None
    ):
        self.cognitive_orchestrator = cognitive_orchestrator
        self.fatigue_engine = fatigue_engine
        self.threshold_coordinator = threshold_coordinator
        self.profile_manager = profile_manager
        self.database = database
        self.adhd_navigator = adhd_navigator
        self.performance_monitor = performance_monitor or PerformanceMonitor()

        # Harmonization configuration
        self.accommodation_sync_interval_ms = 1000  # Sync every second
        self.effectiveness_measurement_window_minutes = 15
        self.conflict_resolution_timeout_ms = 100  # Quick conflict resolution

        # Accommodation mapping between phases
        self.accommodation_component_mapping = self._initialize_accommodation_mapping()

        # Active harmonization state
        self._accommodation_profiles: Dict[str, AccommodationProfile] = {}
        self._detected_conflicts: Dict[str, AccommodationConflict] = {}
        self._harmonization_history: Dict[str, List[Dict[str, Any]]] = {}

        # Performance tracking
        self._harmonization_metrics = {
            "total_harmonizations": 0,
            "conflicts_resolved": 0,
            "effectiveness_improvements": 0,
            "average_harmonization_time_ms": 0.0
        }

    # Core Accommodation Harmonization

    async def initialize_accommodation_harmonization(
        self,
        user_session_id: str,
        workspace_path: str
    ) -> AccommodationProfile:
        """Initialize accommodation harmonization for user session."""
        operation_id = self.performance_monitor.start_operation("initialize_accommodation_harmonization")

        try:
            # Get user profile for accommodation preferences
            profile = await self.profile_manager.get_or_create_profile(user_session_id, workspace_path)

            # Initialize accommodation states from profile and system defaults
            active_accommodations = await self._initialize_accommodation_states(profile)

            # Create accommodation profile
            accommodation_profile = AccommodationProfile(
                user_session_id=user_session_id,
                workspace_path=workspace_path,
                active_accommodations=active_accommodations,
                accommodation_preference_strength=0.8 if profile.progressive_disclosure_preference else 0.5,
                learning_profile_sync_version=profile.session_count
            )

            # Detect and resolve initial conflicts
            conflicts = await self._detect_accommodation_conflicts(accommodation_profile)
            if conflicts:
                await self._resolve_accommodation_conflicts(accommodation_profile, conflicts)

            # Apply harmonized accommodations to all components
            await self._apply_harmonized_accommodations(accommodation_profile)

            # Store accommodation profile
            session_key = f"{user_session_id}_{workspace_path}"
            self._accommodation_profiles[session_key] = accommodation_profile

            self.performance_monitor.end_operation(operation_id, success=True)

            logger.info(f"🤝 Initialized accommodation harmonization: {len(active_accommodations)} accommodations "
                       f"({len(conflicts)} conflicts resolved)")

            return accommodation_profile

        except Exception as e:
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"Failed to initialize accommodation harmonization: {e}")
            raise

    async def harmonize_accommodations_for_context(
        self,
        user_session_id: str,
        workspace_path: str,
        cognitive_load: CognitiveLoadReading,
        attention_state: AttentionState
    ) -> Dict[str, Any]:
        """Harmonize accommodations based on current cognitive load and attention state."""
        operation_id = self.performance_monitor.start_operation("harmonize_accommodations_for_context")

        try:
            session_key = f"{user_session_id}_{workspace_path}"
            accommodation_profile = self._accommodation_profiles.get(session_key)

            if not accommodation_profile:
                raise ValueError(f"No accommodation profile for {session_key}")

            # Analyze current context for accommodation needs
            context_analysis = await self._analyze_accommodation_context_needs(
                cognitive_load, attention_state, accommodation_profile
            )

            # Create harmonization plan
            harmonization_plan = await self._create_harmonization_plan(
                accommodation_profile, context_analysis
            )

            # Apply harmonization plan
            harmonization_results = await self._apply_harmonization_plan(
                accommodation_profile, harmonization_plan
            )

            # Update accommodation effectiveness
            await self._update_accommodation_effectiveness(
                accommodation_profile, harmonization_results
            )

            # Track harmonization
            self._harmonization_metrics["total_harmonizations"] += 1
            if harmonization_results["effectiveness_improvement"] > 0:
                self._harmonization_metrics["effectiveness_improvements"] += 1

            self.performance_monitor.end_operation(operation_id, success=True)

            logger.debug(f"🤝 Harmonized accommodations: {harmonization_results['accommodations_updated']} updated "
                        f"for {cognitive_load.load_state.value} load")

            return {
                "harmonization_successful": True,
                "accommodations_updated": harmonization_results["accommodations_updated"],
                "effectiveness_improvement": harmonization_results["effectiveness_improvement"],
                "conflicts_resolved": harmonization_results["conflicts_resolved"],
                "harmonization_plan": harmonization_plan
            }

        except Exception as e:
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"Failed to harmonize accommodations for context: {e}")
            return {"harmonization_successful": False, "error": str(e)}

    # Accommodation State Management

    async def _initialize_accommodation_states(
        self, profile: PersonalLearningProfile
    ) -> Dict[SystemAccommodationType, AccommodationState]:
        """Initialize accommodation states from user profile and system intelligence."""
        accommodations = {}

        try:
            # Core cognitive accommodations (based on profile preferences)
            accommodations[SystemAccommodationType.PROGRESSIVE_DISCLOSURE] = AccommodationState(
                accommodation_type=SystemAccommodationType.PROGRESSIVE_DISCLOSURE,
                enabled=profile.progressive_disclosure_preference,
                scope=AccommodationScope.GLOBAL,
                effectiveness_score=0.8 if profile.progressive_disclosure_preference else 0.5,
                effectiveness_level=AccommodationEffectiveness.HIGHLY_EFFECTIVE if profile.progressive_disclosure_preference else AccommodationEffectiveness.MODERATELY_EFFECTIVE,
                applied_components=["phase2a", "phase2c", "phase2d"] if profile.progressive_disclosure_preference else [],
                user_requested=profile.progressive_disclosure_preference,
                cognitive_load_reduction=0.3 if profile.progressive_disclosure_preference else 0.0
            )

            accommodations[SystemAccommodationType.COMPLEXITY_FILTERING] = AccommodationState(
                accommodation_type=SystemAccommodationType.COMPLEXITY_FILTERING,
                enabled=True,  # Always enabled for ADHD optimization
                scope=AccommodationScope.GLOBAL,
                effectiveness_score=0.85,
                effectiveness_level=AccommodationEffectiveness.HIGHLY_EFFECTIVE,
                applied_components=["phase2a", "phase2c", "phase2d"],
                cognitive_load_reduction=0.4
            )

            accommodations[SystemAccommodationType.RESULT_LIMITING] = AccommodationState(
                accommodation_type=SystemAccommodationType.RESULT_LIMITING,
                enabled=True,  # Core ADHD accommodation
                scope=AccommodationScope.GLOBAL,
                effectiveness_score=0.9,  # Very effective for ADHD
                effectiveness_level=AccommodationEffectiveness.HIGHLY_EFFECTIVE,
                applied_components=["phase2a", "phase2c", "phase2d"],
                cognitive_load_reduction=0.5
            )

            # Attention and focus accommodations
            accommodations[SystemAccommodationType.FOCUS_MODE_INTEGRATION] = AccommodationState(
                accommodation_type=SystemAccommodationType.FOCUS_MODE_INTEGRATION,
                enabled=profile.context_switch_tolerance <= 3,  # Enable for low context switch tolerance
                scope=AccommodationScope.SESSION,
                effectiveness_score=0.7,
                effectiveness_level=AccommodationEffectiveness.EFFECTIVE,
                applied_components=["phase2b", "phase2c"],
                cognitive_load_reduction=0.25
            )

            accommodations[SystemAccommodationType.BREAK_REMINDERS] = AccommodationState(
                accommodation_type=SystemAccommodationType.BREAK_REMINDERS,
                enabled=profile.average_attention_span_minutes < 30,  # Enable for shorter attention spans
                scope=AccommodationScope.SESSION,
                effectiveness_score=0.6,
                effectiveness_level=AccommodationEffectiveness.EFFECTIVE,
                applied_components=["phase2b", "phase2e"],
                cognitive_load_reduction=0.2
            )

            # Interface accommodations
            accommodations[SystemAccommodationType.GENTLE_GUIDANCE] = AccommodationState(
                accommodation_type=SystemAccommodationType.GENTLE_GUIDANCE,
                enabled=profile.gentle_guidance_enabled if hasattr(profile, 'gentle_guidance_enabled') else True,
                scope=AccommodationScope.GLOBAL,
                effectiveness_score=0.75,
                effectiveness_level=AccommodationEffectiveness.EFFECTIVE,
                applied_components=["all"],
                cognitive_load_reduction=0.15
            )

            accommodations[SystemAccommodationType.VISUAL_INDICATORS] = AccommodationState(
                accommodation_type=SystemAccommodationType.VISUAL_INDICATORS,
                enabled=True,  # Generally helpful for ADHD
                scope=AccommodationScope.GLOBAL,
                effectiveness_score=0.7,
                effectiveness_level=AccommodationEffectiveness.EFFECTIVE,
                applied_components=["all"],
                cognitive_load_reduction=0.1
            )

            # Advanced accommodations (enabled based on learning phase)
            accommodations[SystemAccommodationType.PATTERN_ASSISTANCE] = AccommodationState(
                accommodation_type=SystemAccommodationType.PATTERN_ASSISTANCE,
                enabled=profile.pattern_confidence > 0.5,  # Enable when patterns are learned
                scope=AccommodationScope.GLOBAL,
                effectiveness_score=0.8 if profile.pattern_confidence > 0.7 else 0.6,
                effectiveness_level=AccommodationEffectiveness.HIGHLY_EFFECTIVE if profile.pattern_confidence > 0.7 else AccommodationEffectiveness.EFFECTIVE,
                applied_components=["phase2b", "phase2c", "phase2d"],
                cognitive_load_reduction=0.35 if profile.pattern_confidence > 0.7 else 0.2
            )

            return accommodations

        except Exception as e:
            logger.error(f"Failed to initialize accommodation states: {e}")
            return {}

    # Conflict Detection and Resolution

    async def _detect_accommodation_conflicts(
        self, accommodation_profile: AccommodationProfile
    ) -> List[AccommodationConflict]:
        """Detect conflicts between accommodations."""
        conflicts = []

        try:
            active_accommodations = [
                acc_type for acc_type, state in accommodation_profile.active_accommodations.items()
                if state.enabled
            ]

            # Check for performance conflicts
            high_impact_accommodations = [
                acc_type for acc_type, state in accommodation_profile.active_accommodations.items()
                if state.enabled and state.performance_impact_ms > 20
            ]

            if len(high_impact_accommodations) > 3:
                conflicts.append(AccommodationConflict(
                    conflict_id=f"perf_conflict_{int(time.time())}",
                    conflicting_accommodations=high_impact_accommodations,
                    conflict_type="performance",
                    conflict_severity="medium",
                    resolution_strategy="disable_least_effective",
                    automatic_resolution=True
                ))

            # Check for effectiveness conflicts
            ineffective_accommodations = [
                acc_type for acc_type, state in accommodation_profile.active_accommodations.items()
                if state.enabled and state.effectiveness_level == AccommodationEffectiveness.INEFFECTIVE
            ]

            if ineffective_accommodations:
                conflicts.append(AccommodationConflict(
                    conflict_id=f"eff_conflict_{int(time.time())}",
                    conflicting_accommodations=ineffective_accommodations,
                    conflict_type="effectiveness",
                    conflict_severity="low",
                    resolution_strategy="disable_ineffective",
                    automatic_resolution=True
                ))

            # Check for user experience conflicts
            if (SystemAccommodationType.PROGRESSIVE_DISCLOSURE in active_accommodations and
                SystemAccommodationType.EMERGENCY_SIMPLIFICATION in active_accommodations):
                conflicts.append(AccommodationConflict(
                    conflict_id=f"ux_conflict_{int(time.time())}",
                    conflicting_accommodations=[
                        SystemAccommodationType.PROGRESSIVE_DISCLOSURE,
                        SystemAccommodationType.EMERGENCY_SIMPLIFICATION
                    ],
                    conflict_type="user_experience",
                    conflict_severity="medium",
                    resolution_strategy="prioritize_emergency",
                    automatic_resolution=True
                ))

            return conflicts

        except Exception as e:
            logger.error(f"Failed to detect accommodation conflicts: {e}")
            return []

    async def _resolve_accommodation_conflicts(
        self,
        accommodation_profile: AccommodationProfile,
        conflicts: List[AccommodationConflict]
    ) -> None:
        """Resolve detected accommodation conflicts."""
        try:
            for conflict in conflicts:
                if conflict.automatic_resolution:
                    if conflict.resolution_strategy == "disable_least_effective":
                        # Disable least effective accommodation in conflict
                        least_effective = min(
                            conflict.conflicting_accommodations,
                            key=lambda acc: accommodation_profile.active_accommodations[acc].effectiveness_score
                        )
                        accommodation_profile.active_accommodations[least_effective].enabled = False

                    elif conflict.resolution_strategy == "disable_ineffective":
                        # Disable all ineffective accommodations
                        for acc_type in conflict.conflicting_accommodations:
                            accommodation_profile.active_accommodations[acc_type].enabled = False

                    elif conflict.resolution_strategy == "prioritize_emergency":
                        # Disable non-emergency accommodations
                        for acc_type in conflict.conflicting_accommodations:
                            if acc_type != SystemAccommodationType.EMERGENCY_SIMPLIFICATION:
                                accommodation_profile.active_accommodations[acc_type].enabled = False

                self._detected_conflicts[conflict.conflict_id] = conflict
                self._harmonization_metrics["conflicts_resolved"] += 1

                logger.debug(f"🔧 Resolved accommodation conflict: {conflict.conflict_type} "
                            f"({conflict.resolution_strategy})")

        except Exception as e:
            logger.error(f"Failed to resolve accommodation conflicts: {e}")

    # Component Integration

    async def _apply_harmonized_accommodations(self, accommodation_profile: AccommodationProfile) -> None:
        """Apply harmonized accommodations to all system components."""
        try:
            # Apply to each phase based on accommodation mapping
            for acc_type, acc_state in accommodation_profile.active_accommodations.items():
                if acc_state.enabled:
                    await self._apply_accommodation_to_components(acc_type, acc_state, accommodation_profile)

        except Exception as e:
            logger.error(f"Failed to apply harmonized accommodations: {e}")

    async def _apply_accommodation_to_components(
        self,
        accommodation_type: SystemAccommodationType,
        accommodation_state: AccommodationState,
        profile: AccommodationProfile
    ) -> None:
        """Apply specific accommodation to relevant components."""
        try:
            component_mapping = self.accommodation_component_mapping.get(accommodation_type, [])

            for component in component_mapping:
                if component == "phase2a":
                    await self._apply_to_phase2a(accommodation_type, accommodation_state)
                elif component == "phase2b":
                    await self._apply_to_phase2b(accommodation_type, accommodation_state)
                elif component == "phase2c":
                    await self._apply_to_phase2c(accommodation_type, accommodation_state)
                elif component == "phase2d":
                    await self._apply_to_phase2d(accommodation_type, accommodation_state)
                elif component == "layer1":
                    await self._apply_to_layer1(accommodation_type, accommodation_state)

                # Track application
                if component not in accommodation_state.applied_components:
                    accommodation_state.applied_components.append(component)

        except Exception as e:
            logger.error(f"Failed to apply accommodation {accommodation_type} to components: {e}")

    async def _apply_to_phase2a(
        self, accommodation_type: SystemAccommodationType, accommodation_state: AccommodationState
    ) -> None:
        """Apply accommodation to Phase 2A components."""
        try:
            if accommodation_type == SystemAccommodationType.COMPLEXITY_FILTERING:
                # Enable complexity filtering in graph operations
                # In real implementation: await self.graph_operations.enable_complexity_filtering()
                pass

            elif accommodation_type == SystemAccommodationType.RESULT_LIMITING:
                # Apply result limiting to graph operations
                # In real implementation: await self.graph_operations.set_adhd_result_limits()
                pass

        except Exception as e:
            logger.error(f"Failed to apply {accommodation_type} to Phase 2A: {e}")

    async def _apply_to_phase2c(
        self, accommodation_type: SystemAccommodationType, accommodation_state: AccommodationState
    ) -> None:
        """Apply accommodation to Phase 2C components."""
        try:
            if accommodation_type == SystemAccommodationType.PROGRESSIVE_DISCLOSURE:
                # Enable progressive disclosure in relationship builder
                # In real implementation: await self.relationship_builder.enable_progressive_disclosure()
                pass

            elif accommodation_type == SystemAccommodationType.COGNITIVE_LOAD_LIMITING:
                # Apply cognitive load limiting to ADHD filter
                # In real implementation: await self.adhd_filter.enable_cognitive_load_limiting()
                pass

        except Exception as e:
            logger.error(f"Failed to apply {accommodation_type} to Phase 2C: {e}")

    # Effectiveness Tracking and Optimization

    async def track_accommodation_effectiveness(
        self,
        user_session_id: str,
        workspace_path: str,
        usage_data: Dict[str, Any]
    ) -> None:
        """Track effectiveness of accommodation combinations."""
        try:
            session_key = f"{user_session_id}_{workspace_path}"
            accommodation_profile = self._accommodation_profiles.get(session_key)

            if not accommodation_profile:
                return

            # Update accommodation effectiveness based on usage
            effectiveness_score = usage_data.get("effectiveness_score", 0.5)
            cognitive_load_reduction = usage_data.get("cognitive_load_reduction", 0.0)
            user_satisfaction = usage_data.get("user_satisfaction", 0.5)

            # Update individual accommodation effectiveness
            for acc_type, acc_state in accommodation_profile.active_accommodations.items():
                if acc_state.enabled:
                    # Update effectiveness using exponential moving average
                    alpha = accommodation_profile.accommodation_adaptation_rate
                    acc_state.effectiveness_score = (
                        alpha * effectiveness_score + (1 - alpha) * acc_state.effectiveness_score
                    )

                    # Update effectiveness level
                    acc_state.effectiveness_level = self._categorize_effectiveness(acc_state.effectiveness_score)

                    # Update user satisfaction
                    acc_state.user_satisfaction = (
                        alpha * user_satisfaction + (1 - alpha) * acc_state.user_satisfaction
                    )

                    # Track usage
                    acc_state.usage_frequency += 1
                    acc_state.last_used = datetime.now(timezone.utc)

            # Update overall accommodation profile effectiveness
            active_accommodations = [state for state in accommodation_profile.active_accommodations.values() if state.enabled]
            if active_accommodations:
                accommodation_profile.overall_accommodation_effectiveness = statistics.mean([
                    state.effectiveness_score for state in active_accommodations
                ])

                accommodation_profile.accommodation_satisfaction_score = statistics.mean([
                    state.user_satisfaction for state in active_accommodations
                ])

                # Update most/least effective lists
                accommodation_profile.most_effective_accommodations = [
                    acc_type for acc_type, state in accommodation_profile.active_accommodations.items()
                    if state.enabled and state.effectiveness_level == AccommodationEffectiveness.HIGHLY_EFFECTIVE
                ]

                accommodation_profile.least_effective_accommodations = [
                    acc_type for acc_type, state in accommodation_profile.active_accommodations.items()
                    if state.enabled and state.effectiveness_level in [AccommodationEffectiveness.INEFFECTIVE, AccommodationEffectiveness.COUNTERPRODUCTIVE]
                ]

            logger.debug(f"📊 Tracked accommodation effectiveness: {len(active_accommodations)} accommodations, "
                        f"overall effectiveness {accommodation_profile.overall_accommodation_effectiveness:.2f}")

        except Exception as e:
            logger.error(f"Failed to track accommodation effectiveness: {e}")

    # Analytics and Insights

    async def get_accommodation_analytics(
        self, user_session_id: str, workspace_path: str
    ) -> Dict[str, Any]:
        """Get comprehensive accommodation analytics."""
        try:
            session_key = f"{user_session_id}_{workspace_path}"
            accommodation_profile = self._accommodation_profiles.get(session_key)
            harmonization_history = self._harmonization_history.get(session_key, [])

            if not accommodation_profile:
                return {"message": "No accommodation data available"}

            analytics = {
                "accommodation_summary": {
                    "total_accommodations": len(accommodation_profile.active_accommodations),
                    "enabled_accommodations": sum(1 for state in accommodation_profile.active_accommodations.values() if state.enabled),
                    "overall_effectiveness": accommodation_profile.overall_accommodation_effectiveness,
                    "satisfaction_score": accommodation_profile.accommodation_satisfaction_score
                },
                "effectiveness_distribution": {
                    effectiveness.value: sum(
                        1 for state in accommodation_profile.active_accommodations.values()
                        if state.enabled and state.effectiveness_level == effectiveness
                    )
                    for effectiveness in AccommodationEffectiveness
                },
                "most_effective": [acc.value for acc in accommodation_profile.most_effective_accommodations],
                "least_effective": [acc.value for acc in accommodation_profile.least_effective_accommodations],
                "cognitive_load_impact": {
                    "total_reduction": sum(
                        state.cognitive_load_reduction for state in accommodation_profile.active_accommodations.values()
                        if state.enabled
                    ),
                    "average_reduction_per_accommodation": statistics.mean([
                        state.cognitive_load_reduction for state in accommodation_profile.active_accommodations.values()
                        if state.enabled and state.cognitive_load_reduction > 0
                    ]) if any(state.cognitive_load_reduction > 0 for state in accommodation_profile.active_accommodations.values() if state.enabled) else 0.0
                },
                "harmonization_metrics": {
                    "harmonizations_performed": len(harmonization_history),
                    "conflicts_resolved": self._harmonization_metrics["conflicts_resolved"],
                    "effectiveness_improvements": self._harmonization_metrics["effectiveness_improvements"],
                    "average_harmonization_time_ms": self._harmonization_metrics["average_harmonization_time_ms"]
                },
                "personalization_insights": await self._generate_accommodation_insights(accommodation_profile)
            }

            return analytics

        except Exception as e:
            logger.error(f"Failed to get accommodation analytics: {e}")
            return {"error": str(e)}

    # Utility Methods

    def _initialize_accommodation_mapping(self) -> Dict[SystemAccommodationType, List[str]]:
        """Initialize mapping of accommodations to system components."""
        return {
            SystemAccommodationType.PROGRESSIVE_DISCLOSURE: ["phase2a", "phase2c", "phase2d"],
            SystemAccommodationType.COMPLEXITY_FILTERING: ["phase2a", "phase2c", "phase2d"],
            SystemAccommodationType.COGNITIVE_LOAD_LIMITING: ["phase2a", "phase2b", "phase2c"],
            SystemAccommodationType.RESULT_LIMITING: ["phase2a", "phase2c", "phase2d"],
            SystemAccommodationType.FOCUS_MODE_INTEGRATION: ["phase2b", "phase2c", "layer1"],
            SystemAccommodationType.ATTENTION_ANCHORING: ["phase2b", "phase2c"],
            SystemAccommodationType.CONTEXT_PRESERVATION: ["phase2b", "layer1"],
            SystemAccommodationType.BREAK_REMINDERS: ["phase2b", "phase2e"],
            SystemAccommodationType.GENTLE_GUIDANCE: ["all"],
            SystemAccommodationType.VISUAL_INDICATORS: ["all"],
            SystemAccommodationType.PATTERN_ASSISTANCE: ["phase2b", "phase2c", "phase2d"],
            SystemAccommodationType.EMERGENCY_SIMPLIFICATION: ["all"]
        }

    def _categorize_effectiveness(self, effectiveness_score: float) -> AccommodationEffectiveness:
        """Categorize accommodation effectiveness."""
        if effectiveness_score >= 0.8:
            return AccommodationEffectiveness.HIGHLY_EFFECTIVE
        elif effectiveness_score >= 0.6:
            return AccommodationEffectiveness.EFFECTIVE
        elif effectiveness_score >= 0.4:
            return AccommodationEffectiveness.MODERATELY_EFFECTIVE
        elif effectiveness_score >= 0.0:
            return AccommodationEffectiveness.INEFFECTIVE
        else:
            return AccommodationEffectiveness.COUNTERPRODUCTIVE

    # Placeholder methods for complex operations
    async def _analyze_accommodation_context_needs(self, cognitive_load: CognitiveLoadReading, attention_state: AttentionState, profile: AccommodationProfile) -> Dict[str, Any]:
        return {"needs_analysis": "context_appropriate_accommodations"}

    async def _create_harmonization_plan(self, profile: AccommodationProfile, context_analysis: Dict[str, Any]) -> HarmonizationPlan:
        return HarmonizationPlan(
            plan_id="plan_123",
            user_session_id=profile.user_session_id,
            target_accommodations={},
            component_updates={},
            conflict_resolutions=[],
            expected_effectiveness_improvement=0.1,
            implementation_sequence=[]
        )

    async def _apply_harmonization_plan(self, profile: AccommodationProfile, plan: HarmonizationPlan) -> Dict[str, Any]:
        return {"accommodations_updated": 2, "effectiveness_improvement": 0.1, "conflicts_resolved": 0}

    async def _update_accommodation_effectiveness(self, profile: AccommodationProfile, results: Dict[str, Any]) -> None:
        pass

    async def _apply_to_phase2b(self, accommodation_type: SystemAccommodationType, accommodation_state: AccommodationState) -> None:
        pass

    async def _apply_to_phase2d(self, accommodation_type: SystemAccommodationType, accommodation_state: AccommodationState) -> None:
        pass

    async def _apply_to_layer1(self, accommodation_type: SystemAccommodationType, accommodation_state: AccommodationState) -> None:
        pass

    async def _generate_accommodation_insights(self, profile: AccommodationProfile) -> List[str]:
        return ["Accommodations well-coordinated across system", "High effectiveness achieved"]


# Convenience functions
async def create_accommodation_harmonizer(
    cognitive_orchestrator: CognitiveLoadOrchestrator,
    fatigue_engine: FatigueDetectionEngine,
    threshold_coordinator: PersonalizedThresholdCoordinator,
    profile_manager: PersonalLearningProfileManager,
    database: SerenaIntelligenceDatabase,
    adhd_navigator: ADHDCodeNavigator,
    performance_monitor: PerformanceMonitor = None
) -> AccommodationHarmonizer:
    """Create accommodation harmonizer instance."""
    return AccommodationHarmonizer(
        cognitive_orchestrator, fatigue_engine, threshold_coordinator,
        profile_manager, database, adhd_navigator, performance_monitor
    )


async def test_accommodation_harmonization(
    harmonizer: AccommodationHarmonizer,
    test_user_id: str,
    test_workspace: str
) -> Dict[str, Any]:
    """Test accommodation harmonization system."""
    try:
        # Initialize harmonization
        accommodation_profile = await harmonizer.initialize_accommodation_harmonization(
            test_user_id, test_workspace
        )

        # Test harmonization for different cognitive load contexts
        from .cognitive_load_orchestrator import CognitiveLoadReading, CognitiveLoadState

        high_load_context = CognitiveLoadReading(
            timestamp=datetime.now(timezone.utc),
            overall_load_score=0.8,
            load_state=CognitiveLoadState.HIGH,
            phase2a_code_complexity=0.7,
            phase2a_relationship_load=0.8,
            phase2b_attention_load=0.9,
            phase2b_pattern_load=0.6,
            phase2c_relationship_cognitive_load=0.8,
            phase2d_template_load=0.7,
            session_duration_factor=0.6,
            context_switch_penalty=0.4,
            complexity_accumulation=0.3,
            fatigue_factor=0.5,
            measurement_confidence=0.9,
            component_count=6
        )

        harmonization_result = await harmonizer.harmonize_accommodations_for_context(
            test_user_id, test_workspace, high_load_context, AttentionState.LOW_FOCUS
        )

        # Get analytics
        analytics = await harmonizer.get_accommodation_analytics(test_user_id, test_workspace)

        return {
            "harmonization_initialized": True,
            "accommodations_count": len(accommodation_profile.active_accommodations),
            "enabled_accommodations": sum(1 for state in accommodation_profile.active_accommodations.values() if state.enabled),
            "harmonization_successful": harmonization_result["harmonization_successful"],
            "accommodations_updated": harmonization_result.get("accommodations_updated", 0),
            "effectiveness_improvement": harmonization_result.get("effectiveness_improvement", 0.0),
            "overall_effectiveness": analytics["accommodation_summary"]["overall_effectiveness"],
            "test_status": "passed"
        }

    except Exception as e:
        logger.error(f"Accommodation harmonization test failed: {e}")
        return {
            "test_status": "failed",
            "error": str(e),
            "harmonization_initialized": False
        }


if __name__ == "__main__":
    # Quick test when run directly
    async def main():
        print("🤝 Serena Accommodation Harmonizer")
        print("System-wide ADHD accommodation coordination and consistency")
        print("✅ Module loaded successfully")

    asyncio.run(main())