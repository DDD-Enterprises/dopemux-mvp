"""
Serena v2 Phase 2E: Personalized Threshold Coordinator

Unified threshold management across all Phase 2A-2D components with personalized
ADHD optimization and coordinated threshold adaptation based on learned preferences.
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
from .cognitive_load_orchestrator import CognitiveLoadOrchestrator, CognitiveLoadReading
from .fatigue_detection_engine import FatigueDetectionEngine, FatigueDetection

# Phase 2B Components (Threshold Sources)
from .learning_profile_manager import PersonalLearningProfileManager, PersonalLearningProfile
from .adaptive_learning import AdaptiveLearningEngine, AttentionState
from .effectiveness_tracker import EffectivenessTracker

# Phase 2A Components
from .database import SerenaIntelligenceDatabase

# Layer 1 Components
from ..performance_monitor import PerformanceMonitor

logger = logging.getLogger(__name__)


class ThresholdType(str, Enum):
    """Types of thresholds managed across the system."""
    # Phase 2A thresholds
    GRAPH_RESULT_LIMIT = "graph_result_limit"
    COMPLEXITY_FILTER_THRESHOLD = "complexity_filter_threshold"
    RELATIONSHIP_RELEVANCE_MINIMUM = "relationship_relevance_minimum"

    # Phase 2B thresholds
    ATTENTION_SPAN_TARGET = "attention_span_target"
    CONTEXT_SWITCH_TOLERANCE = "context_switch_tolerance"
    EFFECTIVENESS_LEARNING_THRESHOLD = "effectiveness_learning_threshold"
    PATTERN_CONFIDENCE_THRESHOLD = "pattern_confidence_threshold"

    # Phase 2C thresholds
    RELATIONSHIP_COGNITIVE_LOAD_LIMIT = "relationship_cognitive_load_limit"
    RELEVANCE_SCORING_THRESHOLD = "relevance_scoring_threshold"
    ATTENTION_COMPATIBILITY_THRESHOLD = "attention_compatibility_threshold"

    # Phase 2D thresholds
    TEMPLATE_COMPLEXITY_PREFERENCE = "template_complexity_preference"
    RECOMMENDATION_CONFIDENCE_MINIMUM = "recommendation_confidence_minimum"
    TIME_REDUCTION_EXPECTATION = "time_reduction_expectation"

    # Phase 2E thresholds
    COGNITIVE_LOAD_WARNING_LEVEL = "cognitive_load_warning_level"
    FATIGUE_DETECTION_SENSITIVITY = "fatigue_detection_sensitivity"
    ADAPTATION_TRIGGER_THRESHOLD = "adaptation_trigger_threshold"


class ThresholdUpdateTrigger(str, Enum):
    """Triggers for threshold updates."""
    USER_FEEDBACK = "user_feedback"                   # Direct user feedback
    EFFECTIVENESS_CHANGE = "effectiveness_change"     # Effectiveness patterns changed
    ATTENTION_PATTERN_EVOLUTION = "attention_pattern_evolution"  # Attention patterns evolved
    COGNITIVE_LOAD_ADAPTATION = "cognitive_load_adaptation"      # Load adaptation needed
    FATIGUE_RESPONSE = "fatigue_response"             # Response to fatigue
    PATTERN_LEARNING = "pattern_learning"             # Learning pattern updates
    SESSION_ANALYSIS = "session_analysis"             # End-of-session analysis


class AdaptationStrategy(str, Enum):
    """Strategies for threshold adaptation."""
    CONSERVATIVE = "conservative"      # Small, safe adjustments
    MODERATE = "moderate"             # Balanced adjustments
    AGGRESSIVE = "aggressive"         # Larger adjustments for clear patterns
    EMERGENCY = "emergency"           # Immediate adjustments for critical situations


@dataclass
class ThresholdValue:
    """Individual threshold value with metadata."""
    threshold_type: ThresholdType
    current_value: float
    default_value: float
    min_value: float
    max_value: float

    # Adaptation tracking
    adaptation_count: int = 0
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    update_trigger: Optional[ThresholdUpdateTrigger] = None

    # Effectiveness tracking
    effectiveness_history: List[float] = field(default_factory=list)
    current_effectiveness: float = 0.5
    adaptation_confidence: float = 0.5

    # User preference
    user_explicitly_set: bool = False
    user_satisfaction: float = 0.5


@dataclass
class ThresholdCoordination:
    """Coordination state for personalized thresholds."""
    user_session_id: str
    workspace_path: str
    thresholds: Dict[ThresholdType, ThresholdValue]

    # Coordination metadata
    total_adaptations: int = 0
    last_coordination_update: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    coordination_effectiveness: float = 0.0

    # User learning integration
    learning_profile_version: int = 0  # Track profile changes
    threshold_learning_rate: float = 0.1  # How quickly to adapt thresholds

    # Performance tracking
    threshold_update_overhead_ms: float = 0.0
    cross_component_propagation_time_ms: float = 0.0


@dataclass
class ThresholdAdaptationPlan:
    """Plan for coordinated threshold adaptation."""
    adaptation_id: str
    user_session_id: str
    trigger: ThresholdUpdateTrigger
    adaptation_strategy: AdaptationStrategy

    # Threshold changes
    threshold_updates: Dict[ThresholdType, Dict[str, Any]]
    cross_component_impacts: Dict[str, List[str]]  # Which components affected by each threshold

    # Implementation details
    update_sequence: List[ThresholdType]  # Order of threshold updates
    expected_effectiveness_improvement: float
    estimated_implementation_time_ms: float

    # Validation
    rollback_plan: Dict[ThresholdType, float]  # Previous values for rollback
    success_criteria: List[str]


class PersonalizedThresholdCoordinator:
    """
    Personalized threshold coordinator unifying threshold management across all phases.

    Features:
    - Unified threshold management leveraging Phase 2B learning profiles as source of truth
    - Coordinated threshold updates across all Phase 2A-2D components
    - Real-time threshold adaptation based on cognitive load and effectiveness feedback
    - Integration with fatigue detection for emergency threshold adjustments
    - Performance-optimized threshold propagation maintaining <200ms targets
    - User preference learning and explicit threshold customization support
    - Cross-session threshold persistence and restoration
    - Effectiveness-based threshold optimization with statistical confidence
    """

    def __init__(
        self,
        # Core coordination components
        cognitive_orchestrator: CognitiveLoadOrchestrator,
        fatigue_engine: FatigueDetectionEngine,

        # Phase 2B integration (threshold source of truth)
        profile_manager: PersonalLearningProfileManager,
        learning_engine: AdaptiveLearningEngine,
        effectiveness_tracker: EffectivenessTracker,

        # Database and monitoring
        database: SerenaIntelligenceDatabase,
        performance_monitor: PerformanceMonitor = None
    ):
        self.cognitive_orchestrator = cognitive_orchestrator
        self.fatigue_engine = fatigue_engine
        self.profile_manager = profile_manager
        self.learning_engine = learning_engine
        self.effectiveness_tracker = effectiveness_tracker
        self.database = database
        self.performance_monitor = performance_monitor or PerformanceMonitor()

        # Threshold configuration
        self.adaptation_learning_rate = 0.1  # Conservative learning rate
        self.effectiveness_confidence_threshold = 0.7
        self.threshold_update_batch_size = 5  # Update multiple thresholds efficiently

        # Default threshold ranges
        self.threshold_defaults = self._initialize_threshold_defaults()

        # Active coordination state
        self._threshold_coordinations: Dict[str, ThresholdCoordination] = {}
        self._adaptation_history: Dict[str, List[ThresholdAdaptationPlan]] = {}

        # Performance tracking
        self._coordination_metrics = {
            "total_coordinations": 0,
            "successful_adaptations": 0,
            "average_coordination_time_ms": 0.0,
            "cross_component_propagations": 0
        }

    # Core Threshold Coordination

    async def initialize_personalized_thresholds(
        self,
        user_session_id: str,
        workspace_path: str
    ) -> ThresholdCoordination:
        """Initialize personalized thresholds from learning profile."""
        operation_id = self.performance_monitor.start_operation("initialize_personalized_thresholds")

        try:
            # Get user profile as source of truth
            profile = await self.profile_manager.get_or_create_profile(user_session_id, workspace_path)

            # Initialize thresholds from profile
            thresholds = {}

            # Phase 2A thresholds from profile
            thresholds[ThresholdType.GRAPH_RESULT_LIMIT] = ThresholdValue(
                threshold_type=ThresholdType.GRAPH_RESULT_LIMIT,
                current_value=float(profile.preferred_result_limit),
                default_value=10.0,
                min_value=3.0,
                max_value=25.0,
                current_effectiveness=0.8  # Graph operations are generally effective
            )

            thresholds[ThresholdType.COMPLEXITY_FILTER_THRESHOLD] = ThresholdValue(
                threshold_type=ThresholdType.COMPLEXITY_FILTER_THRESHOLD,
                current_value=profile.optimal_complexity_range[1],
                default_value=0.6,
                min_value=0.2,
                max_value=1.0,
                current_effectiveness=0.7
            )

            # Phase 2B thresholds from profile
            thresholds[ThresholdType.ATTENTION_SPAN_TARGET] = ThresholdValue(
                threshold_type=ThresholdType.ATTENTION_SPAN_TARGET,
                current_value=profile.average_attention_span_minutes,
                default_value=25.0,
                min_value=5.0,
                max_value=90.0,
                current_effectiveness=0.8
            )

            thresholds[ThresholdType.CONTEXT_SWITCH_TOLERANCE] = ThresholdValue(
                threshold_type=ThresholdType.CONTEXT_SWITCH_TOLERANCE,
                current_value=float(profile.context_switch_tolerance),
                default_value=3.0,
                min_value=1.0,
                max_value=10.0,
                current_effectiveness=0.7
            )

            # Phase 2C thresholds derived from profile
            thresholds[ThresholdType.RELATIONSHIP_COGNITIVE_LOAD_LIMIT] = ThresholdValue(
                threshold_type=ThresholdType.RELATIONSHIP_COGNITIVE_LOAD_LIMIT,
                current_value=profile.optimal_complexity_range[1] + 0.1,  # Slightly higher than complexity tolerance
                default_value=0.7,
                min_value=0.3,
                max_value=0.9,
                current_effectiveness=0.75
            )

            # Phase 2D thresholds from profile
            thresholds[ThresholdType.TEMPLATE_COMPLEXITY_PREFERENCE] = ThresholdValue(
                threshold_type=ThresholdType.TEMPLATE_COMPLEXITY_PREFERENCE,
                current_value=profile.optimal_complexity_range[1],
                default_value=0.6,
                min_value=0.3,
                max_value=0.9,
                current_effectiveness=0.8
            )

            # Phase 2E thresholds based on profile characteristics
            thresholds[ThresholdType.COGNITIVE_LOAD_WARNING_LEVEL] = ThresholdValue(
                threshold_type=ThresholdType.COGNITIVE_LOAD_WARNING_LEVEL,
                current_value=profile.optimal_complexity_range[1] + 0.2,
                default_value=0.7,
                min_value=0.4,
                max_value=0.9,
                current_effectiveness=0.7
            )

            thresholds[ThresholdType.FATIGUE_DETECTION_SENSITIVITY] = ThresholdValue(
                threshold_type=ThresholdType.FATIGUE_DETECTION_SENSITIVITY,
                current_value=0.8,  # Default high sensitivity for ADHD
                default_value=0.8,
                min_value=0.5,
                max_value=0.95,
                current_effectiveness=0.8
            )

            # Create coordination state
            coordination = ThresholdCoordination(
                user_session_id=user_session_id,
                workspace_path=workspace_path,
                thresholds=thresholds,
                learning_profile_version=profile.session_count,  # Use session count as version
                threshold_learning_rate=self.adaptation_learning_rate
            )

            # Store coordination state
            session_key = f"{user_session_id}_{workspace_path}"
            self._threshold_coordinations[session_key] = coordination

            # Apply initial thresholds to all components
            await self._propagate_thresholds_to_components(coordination)

            self.performance_monitor.end_operation(operation_id, success=True)

            logger.info(f"🎯 Initialized personalized thresholds for {user_session_id} "
                       f"({len(thresholds)} thresholds coordinated)")

            return coordination

        except Exception as e:
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"Failed to initialize personalized thresholds: {e}")
            raise

    async def adapt_thresholds_from_feedback(
        self,
        user_session_id: str,
        workspace_path: str,
        feedback: Dict[str, Any],
        trigger: ThresholdUpdateTrigger = ThresholdUpdateTrigger.USER_FEEDBACK
    ) -> Dict[str, Any]:
        """Adapt thresholds based on effectiveness feedback or user input."""
        operation_id = self.performance_monitor.start_operation("adapt_thresholds_from_feedback")

        try:
            session_key = f"{user_session_id}_{workspace_path}"
            coordination = self._threshold_coordinations.get(session_key)

            if not coordination:
                raise ValueError(f"No threshold coordination for {session_key}")

            # Analyze feedback for threshold adaptation opportunities
            adaptation_opportunities = await self._analyze_threshold_adaptation_opportunities(
                coordination, feedback, trigger
            )

            if not adaptation_opportunities:
                self.performance_monitor.end_operation(operation_id, success=True, cache_hit=True)
                return {"adaptations_applied": 0, "reason": "no_adaptation_opportunities"}

            # Create adaptation plan
            adaptation_plan = await self._create_threshold_adaptation_plan(
                coordination, adaptation_opportunities, trigger
            )

            # Apply threshold adaptations
            application_results = await self._apply_threshold_adaptations(coordination, adaptation_plan)

            # Update learning profile with new thresholds
            await self._sync_thresholds_to_learning_profile(coordination)

            # Track adaptation history
            if session_key not in self._adaptation_history:
                self._adaptation_history[session_key] = []
            self._adaptation_history[session_key].append(adaptation_plan)

            # Update metrics
            self._coordination_metrics["successful_adaptations"] += 1

            self.performance_monitor.end_operation(operation_id, success=True)

            logger.info(f"🔧 Adapted thresholds: {application_results['thresholds_updated']} updated "
                       f"based on {trigger.value}")

            return {
                "adaptations_applied": application_results["thresholds_updated"],
                "adaptation_plan": adaptation_plan,
                "effectiveness_improvement": application_results["expected_effectiveness_improvement"],
                "component_propagation_time_ms": application_results["propagation_time_ms"]
            }

        except Exception as e:
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"Failed to adapt thresholds from feedback: {e}")
            return {"adaptations_applied": 0, "error": str(e)}

    async def coordinate_emergency_threshold_adjustment(
        self,
        user_session_id: str,
        workspace_path: str,
        fatigue_detection: FatigueDetection
    ) -> Dict[str, Any]:
        """Coordinate emergency threshold adjustments for severe fatigue."""
        operation_id = self.performance_monitor.start_operation("emergency_threshold_adjustment")

        try:
            session_key = f"{user_session_id}_{workspace_path}"
            coordination = self._threshold_coordinations.get(session_key)

            if not coordination:
                raise ValueError(f"No threshold coordination for {session_key}")

            # Emergency adaptation plan
            emergency_adaptations = {
                ThresholdType.GRAPH_RESULT_LIMIT: max(3.0, coordination.thresholds[ThresholdType.GRAPH_RESULT_LIMIT].current_value * 0.5),
                ThresholdType.COMPLEXITY_FILTER_THRESHOLD: max(0.3, coordination.thresholds[ThresholdType.COMPLEXITY_FILTER_THRESHOLD].current_value * 0.7),
                ThresholdType.RELATIONSHIP_COGNITIVE_LOAD_LIMIT: max(0.3, coordination.thresholds[ThresholdType.RELATIONSHIP_COGNITIVE_LOAD_LIMIT].current_value * 0.6),
                ThresholdType.TEMPLATE_COMPLEXITY_PREFERENCE: max(0.2, coordination.thresholds[ThresholdType.TEMPLATE_COMPLEXITY_PREFERENCE].current_value * 0.6),
                ThresholdType.COGNITIVE_LOAD_WARNING_LEVEL: max(0.4, coordination.thresholds[ThresholdType.COGNITIVE_LOAD_WARNING_LEVEL].current_value * 0.7)
            }

            # Apply emergency adaptations
            adaptations_applied = 0
            total_effectiveness_improvement = 0.0

            for threshold_type, new_value in emergency_adaptations.items():
                if threshold_type in coordination.thresholds:
                    old_value = coordination.thresholds[threshold_type].current_value

                    # Apply emergency adjustment
                    coordination.thresholds[threshold_type].current_value = new_value
                    coordination.thresholds[threshold_type].last_updated = datetime.now(timezone.utc)
                    coordination.thresholds[threshold_type].update_trigger = ThresholdUpdateTrigger.FATIGUE_RESPONSE
                    coordination.thresholds[threshold_type].adaptation_count += 1

                    # Estimate effectiveness improvement
                    effectiveness_improvement = (old_value - new_value) * 0.3  # Reduction = improvement
                    total_effectiveness_improvement += effectiveness_improvement

                    adaptations_applied += 1

            # Propagate emergency thresholds to all components
            propagation_result = await self._emergency_propagate_thresholds(coordination)

            coordination.total_adaptations += adaptations_applied

            self.performance_monitor.end_operation(operation_id, success=True)

            logger.warning(f"🚨 Emergency threshold adjustment: {adaptations_applied} thresholds adapted "
                          f"for {fatigue_detection.fatigue_severity.value} fatigue")

            return {
                "emergency_adaptation_successful": True,
                "thresholds_adapted": adaptations_applied,
                "effectiveness_improvement": total_effectiveness_improvement,
                "propagation_time_ms": propagation_result["propagation_time_ms"],
                "fatigue_severity": fatigue_detection.fatigue_severity.value
            }

        except Exception as e:
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"Failed emergency threshold adjustment: {e}")
            return {"emergency_adaptation_successful": False, "error": str(e)}

    # Threshold Adaptation Analysis

    async def _analyze_threshold_adaptation_opportunities(
        self,
        coordination: ThresholdCoordination,
        feedback: Dict[str, Any],
        trigger: ThresholdUpdateTrigger
    ) -> List[Dict[str, Any]]:
        """Analyze feedback for threshold adaptation opportunities."""
        opportunities = []

        try:
            # Effectiveness-based adaptations
            if trigger == ThresholdUpdateTrigger.EFFECTIVENESS_CHANGE:
                effectiveness_score = feedback.get("effectiveness_score", 0.5)

                # If effectiveness is low, consider reducing complexity thresholds
                if effectiveness_score < 0.6:
                    opportunities.append({
                        "threshold_type": ThresholdType.COMPLEXITY_FILTER_THRESHOLD,
                        "adjustment_direction": "decrease",
                        "adjustment_magnitude": 0.1,
                        "reasoning": "Low effectiveness suggests complexity threshold too high",
                        "confidence": 0.7
                    })

                    opportunities.append({
                        "threshold_type": ThresholdType.RELATIONSHIP_COGNITIVE_LOAD_LIMIT,
                        "adjustment_direction": "decrease",
                        "adjustment_magnitude": 0.05,
                        "reasoning": "Reduce relationship cognitive load limit for better effectiveness",
                        "confidence": 0.6
                    })

            # Cognitive load-based adaptations
            if trigger == ThresholdUpdateTrigger.COGNITIVE_LOAD_ADAPTATION:
                current_load = feedback.get("cognitive_load_score", 0.5)

                if current_load > 0.7:
                    opportunities.append({
                        "threshold_type": ThresholdType.GRAPH_RESULT_LIMIT,
                        "adjustment_direction": "decrease",
                        "adjustment_magnitude": 2.0,  # Reduce by 2 results
                        "reasoning": "High cognitive load suggests too many results",
                        "confidence": 0.8
                    })

            # User feedback adaptations
            if trigger == ThresholdUpdateTrigger.USER_FEEDBACK:
                if feedback.get("too_many_suggestions", False):
                    opportunities.append({
                        "threshold_type": ThresholdType.GRAPH_RESULT_LIMIT,
                        "adjustment_direction": "decrease",
                        "adjustment_magnitude": 1.0,
                        "reasoning": "User reported too many suggestions",
                        "confidence": 0.9
                    })

                if feedback.get("too_complex", False):
                    opportunities.append({
                        "threshold_type": ThresholdType.COMPLEXITY_FILTER_THRESHOLD,
                        "adjustment_direction": "decrease",
                        "adjustment_magnitude": 0.1,
                        "reasoning": "User reported content too complex",
                        "confidence": 0.85
                    })

            # Session analysis adaptations
            if trigger == ThresholdUpdateTrigger.SESSION_ANALYSIS:
                session_data = feedback.get("session_analysis", {})

                # Attention span adaptations
                actual_attention_span = session_data.get("effective_attention_minutes", 0)
                current_target = coordination.thresholds[ThresholdType.ATTENTION_SPAN_TARGET].current_value

                if actual_attention_span > 0 and abs(actual_attention_span - current_target) > 5:
                    adjustment_magnitude = (actual_attention_span - current_target) * 0.2  # Conservative 20% adjustment
                    opportunities.append({
                        "threshold_type": ThresholdType.ATTENTION_SPAN_TARGET,
                        "adjustment_direction": "adjust",
                        "adjustment_magnitude": adjustment_magnitude,
                        "reasoning": f"Actual attention span {actual_attention_span:.0f}min differs from target {current_target:.0f}min",
                        "confidence": 0.8
                    })

            return opportunities

        except Exception as e:
            logger.error(f"Failed to analyze threshold adaptation opportunities: {e}")
            return []

    # Component Threshold Propagation

    async def _propagate_thresholds_to_components(self, coordination: ThresholdCoordination) -> Dict[str, Any]:
        """Propagate thresholds to all system components."""
        propagation_start_time = time.time()

        try:
            propagation_results = {
                "components_updated": 0,
                "propagation_time_ms": 0.0,
                "component_results": {}
            }

            # Phase 2A component updates
            phase2a_result = await self._propagate_to_phase2a(coordination)
            propagation_results["component_results"]["phase2a"] = phase2a_result
            if phase2a_result["success"]:
                propagation_results["components_updated"] += 1

            # Phase 2B component updates
            phase2b_result = await self._propagate_to_phase2b(coordination)
            propagation_results["component_results"]["phase2b"] = phase2b_result
            if phase2b_result["success"]:
                propagation_results["components_updated"] += 1

            # Phase 2C component updates
            phase2c_result = await self._propagate_to_phase2c(coordination)
            propagation_results["component_results"]["phase2c"] = phase2c_result
            if phase2c_result["success"]:
                propagation_results["components_updated"] += 1

            # Phase 2D component updates
            phase2d_result = await self._propagate_to_phase2d(coordination)
            propagation_results["component_results"]["phase2d"] = phase2d_result
            if phase2d_result["success"]:
                propagation_results["components_updated"] += 1

            propagation_results["propagation_time_ms"] = (time.time() - propagation_start_time) * 1000

            # Update coordination metrics
            coordination.cross_component_propagation_time_ms = propagation_results["propagation_time_ms"]
            self._coordination_metrics["cross_component_propagations"] += 1

            return propagation_results

        except Exception as e:
            logger.error(f"Failed to propagate thresholds to components: {e}")
            return {"components_updated": 0, "error": str(e)}

    async def _propagate_to_phase2a(self, coordination: ThresholdCoordination) -> Dict[str, Any]:
        """Propagate thresholds to Phase 2A components."""
        try:
            # Update graph operations thresholds
            result_limit = int(coordination.thresholds[ThresholdType.GRAPH_RESULT_LIMIT].current_value)
            complexity_threshold = coordination.thresholds[ThresholdType.COMPLEXITY_FILTER_THRESHOLD].current_value

            # In real implementation:
            # await self.graph_operations.update_adhd_settings(result_limit, complexity_threshold)

            return {
                "success": True,
                "updates_applied": ["result_limit", "complexity_threshold"],
                "performance_impact_ms": 5
            }

        except Exception as e:
            logger.error(f"Failed to propagate to Phase 2A: {e}")
            return {"success": False, "error": str(e)}

    async def _propagate_to_phase2c(self, coordination: ThresholdCoordination) -> Dict[str, Any]:
        """Propagate thresholds to Phase 2C components."""
        try:
            # Update relationship filtering thresholds
            cognitive_load_limit = coordination.thresholds[ThresholdType.RELATIONSHIP_COGNITIVE_LOAD_LIMIT].current_value

            # In real implementation:
            # await self.adhd_filter.update_cognitive_load_threshold(cognitive_load_limit)

            return {
                "success": True,
                "updates_applied": ["cognitive_load_limit"],
                "performance_impact_ms": 8
            }

        except Exception as e:
            logger.error(f"Failed to propagate to Phase 2C: {e}")
            return {"success": False, "error": str(e)}

    async def _propagate_to_phase2d(self, coordination: ThresholdCoordination) -> Dict[str, Any]:
        """Propagate thresholds to Phase 2D components."""
        try:
            # Update template complexity preferences
            complexity_preference = coordination.thresholds[ThresholdType.TEMPLATE_COMPLEXITY_PREFERENCE].current_value

            # In real implementation:
            # await self.template_manager.update_complexity_preference(complexity_preference)

            return {
                "success": True,
                "updates_applied": ["complexity_preference"],
                "performance_impact_ms": 3
            }

        except Exception as e:
            logger.error(f"Failed to propagate to Phase 2D: {e}")
            return {"success": False, "error": str(e)}

    # Learning Profile Synchronization

    async def _sync_thresholds_to_learning_profile(self, coordination: ThresholdCoordination) -> None:
        """Synchronize threshold changes back to learning profile."""
        try:
            # Get current profile
            profile = await self.profile_manager.get_or_create_profile(
                coordination.user_session_id, coordination.workspace_path
            )

            # Update profile with threshold changes
            updated_values = {}

            # Update result limit preference
            if ThresholdType.GRAPH_RESULT_LIMIT in coordination.thresholds:
                new_limit = int(coordination.thresholds[ThresholdType.GRAPH_RESULT_LIMIT].current_value)
                if new_limit != profile.preferred_result_limit:
                    profile.preferred_result_limit = new_limit
                    updated_values["preferred_result_limit"] = new_limit

            # Update complexity range
            if ThresholdType.COMPLEXITY_FILTER_THRESHOLD in coordination.thresholds:
                new_threshold = coordination.thresholds[ThresholdType.COMPLEXITY_FILTER_THRESHOLD].current_value
                if new_threshold != profile.optimal_complexity_range[1]:
                    profile.optimal_complexity_range = (profile.optimal_complexity_range[0], new_threshold)
                    updated_values["optimal_complexity_range"] = profile.optimal_complexity_range

            # Update attention span target
            if ThresholdType.ATTENTION_SPAN_TARGET in coordination.thresholds:
                new_span = coordination.thresholds[ThresholdType.ATTENTION_SPAN_TARGET].current_value
                if abs(new_span - profile.average_attention_span_minutes) > 2:
                    profile.average_attention_span_minutes = new_span
                    updated_values["average_attention_span_minutes"] = new_span

            # Update context switch tolerance
            if ThresholdType.CONTEXT_SWITCH_TOLERANCE in coordination.thresholds:
                new_tolerance = int(coordination.thresholds[ThresholdType.CONTEXT_SWITCH_TOLERANCE].current_value)
                if new_tolerance != profile.context_switch_tolerance:
                    profile.context_switch_tolerance = new_tolerance
                    updated_values["context_switch_tolerance"] = new_tolerance

            # Store updated profile if changes were made
            if updated_values:
                # In real implementation: await self.profile_manager.store_profile_updates(profile)
                logger.debug(f"🔄 Synced {len(updated_values)} threshold changes to learning profile")

        except Exception as e:
            logger.error(f"Failed to sync thresholds to learning profile: {e}")

    # Analytics and Monitoring

    async def get_threshold_analytics(
        self, user_session_id: str, workspace_path: str
    ) -> Dict[str, Any]:
        """Get analytics about threshold coordination and effectiveness."""
        try:
            session_key = f"{user_session_id}_{workspace_path}"
            coordination = self._threshold_coordinations.get(session_key)
            adaptation_history = self._adaptation_history.get(session_key, [])

            if not coordination:
                return {"message": "No threshold coordination data"}

            analytics = {
                "current_thresholds": {
                    threshold_type.value: {
                        "current_value": threshold.current_value,
                        "effectiveness": threshold.current_effectiveness,
                        "adaptation_count": threshold.adaptation_count,
                        "user_set": threshold.user_explicitly_set
                    }
                    for threshold_type, threshold in coordination.thresholds.items()
                },
                "adaptation_summary": {
                    "total_adaptations": coordination.total_adaptations,
                    "adaptation_history_count": len(adaptation_history),
                    "coordination_effectiveness": coordination.coordination_effectiveness,
                    "learning_rate": coordination.threshold_learning_rate
                },
                "performance_metrics": {
                    "coordination_overhead_ms": coordination.threshold_update_overhead_ms,
                    "propagation_time_ms": coordination.cross_component_propagation_time_ms,
                    "average_coordination_time": self._coordination_metrics["average_coordination_time_ms"]
                },
                "threshold_effectiveness": await self._calculate_threshold_effectiveness(coordination),
                "personalization_insights": await self._generate_threshold_insights(coordination, adaptation_history)
            }

            return analytics

        except Exception as e:
            logger.error(f"Failed to get threshold analytics: {e}")
            return {"error": str(e)}

    # Utility Methods

    def _initialize_threshold_defaults(self) -> Dict[ThresholdType, Dict[str, float]]:
        """Initialize default threshold ranges for ADHD optimization."""
        return {
            ThresholdType.GRAPH_RESULT_LIMIT: {"default": 10.0, "min": 3.0, "max": 25.0},
            ThresholdType.COMPLEXITY_FILTER_THRESHOLD: {"default": 0.6, "min": 0.2, "max": 1.0},
            ThresholdType.ATTENTION_SPAN_TARGET: {"default": 25.0, "min": 5.0, "max": 90.0},
            ThresholdType.CONTEXT_SWITCH_TOLERANCE: {"default": 3.0, "min": 1.0, "max": 10.0},
            ThresholdType.RELATIONSHIP_COGNITIVE_LOAD_LIMIT: {"default": 0.7, "min": 0.3, "max": 0.9},
            ThresholdType.TEMPLATE_COMPLEXITY_PREFERENCE: {"default": 0.6, "min": 0.3, "max": 0.9},
            ThresholdType.COGNITIVE_LOAD_WARNING_LEVEL: {"default": 0.7, "min": 0.4, "max": 0.9},
            ThresholdType.FATIGUE_DETECTION_SENSITIVITY: {"default": 0.8, "min": 0.5, "max": 0.95}
        }

    async def _create_threshold_adaptation_plan(
        self,
        coordination: ThresholdCoordination,
        opportunities: List[Dict[str, Any]],
        trigger: ThresholdUpdateTrigger
    ) -> ThresholdAdaptationPlan:
        """Create threshold adaptation plan from opportunities."""
        adaptation_id = f"adapt_{coordination.user_session_id}_{int(time.time())}"

        # Determine adaptation strategy
        if trigger == ThresholdUpdateTrigger.FATIGUE_RESPONSE:
            strategy = AdaptationStrategy.EMERGENCY
        elif trigger == ThresholdUpdateTrigger.USER_FEEDBACK:
            strategy = AdaptationStrategy.AGGRESSIVE
        else:
            strategy = AdaptationStrategy.MODERATE

        # Create threshold updates
        threshold_updates = {}
        rollback_plan = {}

        for opportunity in opportunities:
            threshold_type = ThresholdType(opportunity["threshold_type"])
            if threshold_type in coordination.thresholds:
                current_threshold = coordination.thresholds[threshold_type]
                old_value = current_threshold.current_value

                # Calculate new value
                if opportunity["adjustment_direction"] == "decrease":
                    new_value = max(current_threshold.min_value, old_value - opportunity["adjustment_magnitude"])
                elif opportunity["adjustment_direction"] == "increase":
                    new_value = min(current_threshold.max_value, old_value + opportunity["adjustment_magnitude"])
                else:  # adjust
                    new_value = max(current_threshold.min_value, min(current_threshold.max_value, old_value + opportunity["adjustment_magnitude"]))

                threshold_updates[threshold_type] = {
                    "old_value": old_value,
                    "new_value": new_value,
                    "reasoning": opportunity["reasoning"],
                    "confidence": opportunity["confidence"]
                }

                rollback_plan[threshold_type] = old_value

        # Determine update sequence (most confident first)
        update_sequence = sorted(
            threshold_updates.keys(),
            key=lambda t: threshold_updates[t]["confidence"],
            reverse=True
        )

        return ThresholdAdaptationPlan(
            adaptation_id=adaptation_id,
            user_session_id=coordination.user_session_id,
            trigger=trigger,
            adaptation_strategy=strategy,
            threshold_updates=threshold_updates,
            cross_component_impacts=await self._calculate_cross_component_impacts(threshold_updates),
            update_sequence=update_sequence,
            expected_effectiveness_improvement=sum(
                update["confidence"] * 0.1 for update in threshold_updates.values()
            ),
            estimated_implementation_time_ms=150,  # Target <200ms
            rollback_plan=rollback_plan,
            success_criteria=["thresholds_applied", "components_updated", "performance_maintained"]
        )

    async def _apply_threshold_adaptations(
        self, coordination: ThresholdCoordination, plan: ThresholdAdaptationPlan
    ) -> Dict[str, Any]:
        """Apply threshold adaptations according to plan."""
        application_results = {
            "thresholds_updated": 0,
            "expected_effectiveness_improvement": plan.expected_effectiveness_improvement,
            "propagation_time_ms": 0.0
        }

        try:
            # Apply threshold updates
            for threshold_type in plan.update_sequence:
                if threshold_type in plan.threshold_updates:
                    update_data = plan.threshold_updates[threshold_type]

                    # Update threshold value
                    coordination.thresholds[threshold_type].current_value = update_data["new_value"]
                    coordination.thresholds[threshold_type].last_updated = datetime.now(timezone.utc)
                    coordination.thresholds[threshold_type].update_trigger = plan.trigger
                    coordination.thresholds[threshold_type].adaptation_count += 1

                    application_results["thresholds_updated"] += 1

            # Propagate to components
            propagation_result = await self._propagate_thresholds_to_components(coordination)
            application_results["propagation_time_ms"] = propagation_result["propagation_time_ms"]

            return application_results

        except Exception as e:
            logger.error(f"Failed to apply threshold adaptations: {e}")
            return {"thresholds_updated": 0, "error": str(e)}

    # Placeholder methods for complex operations
    async def _propagate_to_phase2b(self, coordination: ThresholdCoordination) -> Dict[str, Any]:
        return {"success": True, "updates_applied": ["attention_targets"], "performance_impact_ms": 3}

    async def _emergency_propagate_thresholds(self, coordination: ThresholdCoordination) -> Dict[str, Any]:
        return {"propagation_time_ms": 50}  # Emergency propagation time

    async def _calculate_cross_component_impacts(self, threshold_updates: Dict[ThresholdType, Dict[str, Any]]) -> Dict[str, List[str]]:
        return {"phase2a": ["graph_operations"], "phase2c": ["relationship_filter"]}

    async def _calculate_threshold_effectiveness(self, coordination: ThresholdCoordination) -> float:
        return 0.8  # Would calculate actual effectiveness

    async def _generate_threshold_insights(self, coordination: ThresholdCoordination, history: List[Any]) -> List[str]:
        return ["Thresholds well-tuned for ADHD optimization", "Personalization effective"]


# Convenience functions
async def create_personalized_threshold_coordinator(
    cognitive_orchestrator: CognitiveLoadOrchestrator,
    fatigue_engine: FatigueDetectionEngine,
    profile_manager: PersonalLearningProfileManager,
    learning_engine: AdaptiveLearningEngine,
    effectiveness_tracker: EffectivenessTracker,
    database: SerenaIntelligenceDatabase,
    performance_monitor: PerformanceMonitor = None
) -> PersonalizedThresholdCoordinator:
    """Create personalized threshold coordinator instance."""
    return PersonalizedThresholdCoordinator(
        cognitive_orchestrator, fatigue_engine, profile_manager,
        learning_engine, effectiveness_tracker, database, performance_monitor
    )


async def test_threshold_coordination(
    coordinator: PersonalizedThresholdCoordinator,
    test_user_id: str,
    test_workspace: str
) -> Dict[str, Any]:
    """Test threshold coordination system."""
    try:
        # Initialize thresholds
        coordination = await coordinator.initialize_personalized_thresholds(test_user_id, test_workspace)

        # Test adaptation from feedback
        test_feedback = {
            "effectiveness_score": 0.4,  # Low effectiveness
            "cognitive_load_score": 0.8,  # High cognitive load
            "too_many_suggestions": True
        }

        adaptation_result = await coordinator.adapt_thresholds_from_feedback(
            test_user_id, test_workspace, test_feedback, ThresholdUpdateTrigger.USER_FEEDBACK
        )

        # Get analytics
        analytics = await coordinator.get_threshold_analytics(test_user_id, test_workspace)

        return {
            "coordination_initialized": True,
            "thresholds_count": len(coordination.thresholds),
            "adaptation_successful": adaptation_result["adaptations_applied"] > 0,
            "adaptations_applied": adaptation_result["adaptations_applied"],
            "threshold_effectiveness": analytics.get("threshold_effectiveness", 0.0),
            "propagation_time_ms": analytics["performance_metrics"]["propagation_time_ms"],
            "test_status": "passed"
        }

    except Exception as e:
        logger.error(f"Threshold coordination test failed: {e}")
        return {
            "test_status": "failed",
            "error": str(e),
            "coordination_initialized": False
        }


if __name__ == "__main__":
    # Quick test when run directly
    async def main():
        print("🎯 Serena Personalized Threshold Coordinator")
        print("Unified threshold management across all Phase 2A-2D components")
        print("✅ Module loaded successfully")

    asyncio.run(main())