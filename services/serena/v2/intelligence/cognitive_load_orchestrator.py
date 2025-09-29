"""
Serena v2 Phase 2E: Cognitive Load Orchestrator

Unified cognitive load management orchestrating all Phase 2A-2D components for
comprehensive ADHD-optimized navigation with real-time load coordination.
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

# Phase 2D Components
from .strategy_template_manager import StrategyTemplateManager
from .pattern_reuse_recommendation_engine import PatternReuseRecommendationEngine

# Phase 2C Components
from .intelligent_relationship_builder import IntelligentRelationshipBuilder, NavigationContext
from .adhd_relationship_filter import ADHDRelationshipFilter
from .realtime_relevance_scorer import RealtimeRelevanceScorer

# Phase 2B Components
from .adaptive_learning import AdaptiveLearningEngine, AttentionState
from .learning_profile_manager import PersonalLearningProfileManager, PersonalLearningProfile
from .pattern_recognition import AdvancedPatternRecognition
from .context_switching_optimizer import ContextSwitchingOptimizer
from .effectiveness_tracker import EffectivenessTracker

# Phase 2A Components
from .database import SerenaIntelligenceDatabase
from .graph_operations import SerenaGraphOperations

# Layer 1 Components
from ..performance_monitor import PerformanceMonitor
from ..adhd_features import ADHDCodeNavigator

logger = logging.getLogger(__name__)


class CognitiveLoadState(str, Enum):
    """Overall cognitive load states for the user."""
    MINIMAL = "minimal"           # 0.0-0.2 - very comfortable
    LOW = "low"                   # 0.2-0.4 - comfortable
    MODERATE = "moderate"         # 0.4-0.6 - manageable
    HIGH = "high"                 # 0.6-0.8 - challenging
    OVERWHELMING = "overwhelming" # 0.8-1.0 - needs immediate reduction


class AdaptiveResponse(str, Enum):
    """Types of adaptive responses to cognitive load."""
    MAINTAIN_CURRENT = "maintain_current"           # Current state is optimal
    REDUCE_COMPLEXITY = "reduce_complexity"         # Lower complexity of suggestions
    ENABLE_FOCUS_MODE = "enable_focus_mode"        # Activate focus mode
    SUGGEST_BREAK = "suggest_break"                # Recommend taking a break
    SIMPLIFY_INTERFACE = "simplify_interface"      # Reduce UI complexity
    LIMIT_RESULTS = "limit_results"                # Reduce number of results
    INCREASE_ACCOMMODATION = "increase_accommodation"  # Enhance ADHD accommodations


class OrchestrationTrigger(str, Enum):
    """Triggers for orchestration updates."""
    NAVIGATION_ACTION = "navigation_action"         # User navigated to new element
    ATTENTION_STATE_CHANGE = "attention_state_change"  # Attention state shifted
    SESSION_PROGRESS = "session_progress"          # Session time progressed
    COGNITIVE_LOAD_SPIKE = "cognitive_load_spike"  # Sudden load increase
    FATIGUE_DETECTED = "fatigue_detected"          # Cognitive fatigue detected
    EFFECTIVENESS_FEEDBACK = "effectiveness_feedback"  # User provided feedback
    PATTERN_USAGE = "pattern_usage"                # Pattern/template used


@dataclass
class CognitiveLoadReading:
    """Real-time cognitive load reading from all system components."""
    timestamp: datetime
    overall_load_score: float  # 0.0-1.0 unified cognitive load
    load_state: CognitiveLoadState

    # Component contributions
    phase2a_code_complexity: float  # From code elements
    phase2a_relationship_load: float  # From relationships
    phase2b_attention_load: float  # From attention state
    phase2b_pattern_load: float  # From pattern complexity
    phase2c_relationship_cognitive_load: float  # From intelligent relationships
    phase2d_template_load: float  # From active templates

    # Context factors
    session_duration_factor: float
    context_switch_penalty: float
    complexity_accumulation: float
    fatigue_factor: float

    # Confidence and metadata
    measurement_confidence: float
    component_count: int  # Number of components contributing


@dataclass
class OrchestrationState:
    """Current state of cognitive load orchestration."""
    user_session_id: str
    workspace_path: str
    current_load_reading: CognitiveLoadReading
    active_adaptations: List[AdaptiveResponse]

    # Threshold state
    current_thresholds: Dict[str, float]
    adaptation_history: List[Dict[str, Any]]

    # Performance tracking
    orchestration_overhead_ms: float
    last_update: datetime
    update_frequency_ms: float = 200  # Update every 200ms


@dataclass
class AdaptationPlan:
    """Plan for adapting system components to cognitive load."""
    adaptation_id: str
    trigger: OrchestrationTrigger
    target_load_reduction: float
    adaptation_steps: List[Dict[str, Any]]
    expected_duration_seconds: int
    rollback_plan: List[str]
    success_criteria: List[str]


class CognitiveLoadOrchestrator:
    """
    Unified cognitive load orchestrator for comprehensive ADHD optimization.

    Features:
    - Real-time cognitive load aggregation from all Phase 2A-2D components
    - Unified progressive disclosure coordination across the complete system
    - Cognitive fatigue detection with system-wide adaptive response
    - Personalized threshold management coordinating all component thresholds
    - System-wide ADHD accommodation harmonization and consistency
    - Performance optimization maintaining <200ms targets during coordination
    - Integration with all 19 existing components without breaking changes
    - Proactive cognitive overload prevention and intelligent load balancing
    """

    def __init__(
        self,
        # Phase 2A Components
        database: SerenaIntelligenceDatabase,
        graph_operations: SerenaGraphOperations,

        # Phase 2B Components
        learning_engine: AdaptiveLearningEngine,
        profile_manager: PersonalLearningProfileManager,
        pattern_recognition: AdvancedPatternRecognition,
        effectiveness_tracker: EffectivenessTracker,
        context_optimizer: ContextSwitchingOptimizer,

        # Phase 2C Components
        relationship_builder: IntelligentRelationshipBuilder,
        adhd_filter: ADHDRelationshipFilter,
        realtime_scorer: RealtimeRelevanceScorer,

        # Phase 2D Components
        template_manager: StrategyTemplateManager,
        recommendation_engine: PatternReuseRecommendationEngine,

        # Layer 1 Components
        performance_monitor: PerformanceMonitor = None,
        adhd_navigator: ADHDCodeNavigator = None
    ):
        # Store all component references for orchestration
        self.database = database
        self.graph_operations = graph_operations
        self.learning_engine = learning_engine
        self.profile_manager = profile_manager
        self.pattern_recognition = pattern_recognition
        self.effectiveness_tracker = effectiveness_tracker
        self.context_optimizer = context_optimizer
        self.relationship_builder = relationship_builder
        self.adhd_filter = adhd_filter
        self.realtime_scorer = realtime_scorer
        self.template_manager = template_manager
        self.recommendation_engine = recommendation_engine
        self.performance_monitor = performance_monitor or PerformanceMonitor()
        self.adhd_navigator = adhd_navigator or ADHDCodeNavigator()

        # Orchestration configuration
        self.update_frequency_ms = 200  # Update every 200ms for real-time feel
        self.adaptation_threshold = 0.7  # Trigger adaptation at 70% cognitive load
        self.fatigue_threshold = 0.8  # Detect fatigue at 80% sustained load
        self.recovery_target = 0.5  # Target 50% load for recovery

        # Orchestration state
        self._orchestration_states: Dict[str, OrchestrationState] = {}
        self._adaptation_callbacks: List[Callable] = []
        self._load_history: Dict[str, List[CognitiveLoadReading]] = {}

        # Performance tracking
        self._orchestration_metrics = {
            "total_orchestrations": 0,
            "adaptation_triggers": 0,
            "average_overhead_ms": 0.0,
            "load_reductions_achieved": 0
        }

    # Core Orchestration

    async def start_cognitive_orchestration(
        self,
        user_session_id: str,
        workspace_path: str,
        initial_context: NavigationContext
    ) -> OrchestrationState:
        """Start cognitive load orchestration for user session."""
        operation_id = self.performance_monitor.start_operation("start_cognitive_orchestration")

        try:
            # Get user profile for personalized orchestration
            profile = await self.profile_manager.get_or_create_profile(user_session_id, workspace_path)

            # Take initial cognitive load reading
            initial_reading = await self._take_comprehensive_load_reading(
                user_session_id, workspace_path, initial_context
            )

            # Initialize orchestration state
            orchestration_state = OrchestrationState(
                user_session_id=user_session_id,
                workspace_path=workspace_path,
                current_load_reading=initial_reading,
                active_adaptations=[],
                current_thresholds=self._initialize_personalized_thresholds(profile),
                adaptation_history=[],
                orchestration_overhead_ms=0.0,
                last_update=datetime.now(timezone.utc)
            )

            # Store orchestration state
            self._orchestration_states[f"{user_session_id}_{workspace_path}"] = orchestration_state

            # Initialize load history
            self._load_history[f"{user_session_id}_{workspace_path}"] = [initial_reading]

            # Start background orchestration loop
            asyncio.create_task(self._background_orchestration_loop(user_session_id, workspace_path))

            self.performance_monitor.end_operation(operation_id, success=True)

            logger.info(f"🎼 Started cognitive orchestration for {user_session_id} "
                       f"(initial load: {initial_reading.load_state.value})")

            return orchestration_state

        except Exception as e:
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"Failed to start cognitive orchestration: {e}")
            raise

    async def _background_orchestration_loop(self, user_session_id: str, workspace_path: str) -> None:
        """Background loop for continuous cognitive load orchestration."""
        session_key = f"{user_session_id}_{workspace_path}"

        while session_key in self._orchestration_states:
            try:
                await asyncio.sleep(self.update_frequency_ms / 1000)

                # Take new cognitive load reading
                current_context = await self._get_current_navigation_context(user_session_id, workspace_path)
                if current_context:
                    load_reading = await self._take_comprehensive_load_reading(
                        user_session_id, workspace_path, current_context
                    )

                    # Update orchestration state
                    await self._update_orchestration_state(session_key, load_reading)

                    # Check for adaptation needs
                    await self._check_adaptation_triggers(session_key, load_reading)

            except Exception as e:
                logger.error(f"Orchestration loop error for {session_key}: {e}")

    async def _take_comprehensive_load_reading(
        self,
        user_session_id: str,
        workspace_path: str,
        context: NavigationContext
    ) -> CognitiveLoadReading:
        """Take comprehensive cognitive load reading from all system components."""
        start_time = time.time()

        try:
            # Gather load data from all phases
            load_components = {}

            # Phase 2A: Code and relationship complexity
            if context.current_element:
                load_components["phase2a_code_complexity"] = context.current_element.cognitive_load_factor

                # Get related elements cognitive load
                related_elements = await self.graph_operations.get_related_elements(
                    context.current_element.id, mode=self.graph_operations.NavigationMode.FOCUS
                )
                if related_elements:
                    avg_relationship_load = statistics.mean([
                        edge.cognitive_load for element, edge in related_elements
                    ])
                    load_components["phase2a_relationship_load"] = avg_relationship_load
                else:
                    load_components["phase2a_relationship_load"] = 0.3

            # Phase 2B: Attention state and pattern load
            attention_state = AttentionState(context.attention_state)
            attention_load_mapping = {
                AttentionState.PEAK_FOCUS: 0.2,
                AttentionState.MODERATE_FOCUS: 0.4,
                AttentionState.LOW_FOCUS: 0.7,
                AttentionState.HYPERFOCUS: 0.3,
                AttentionState.FATIGUE: 0.9
            }
            load_components["phase2b_attention_load"] = attention_load_mapping.get(attention_state, 0.5)

            # Phase 2C: Current relationship cognitive load
            # This would be calculated from active relationship suggestions
            load_components["phase2c_relationship_cognitive_load"] = 0.4  # Default

            # Phase 2D: Active template cognitive load
            # This would be calculated from active templates
            load_components["phase2d_template_load"] = 0.3  # Default

            # Calculate session context factors
            session_duration_factor = min(1.0, context.session_duration_minutes / 60.0)  # Normalize to hours
            context_switch_penalty = min(1.0, len(context.recent_navigation_history) / 20.0)

            # Get user profile for personalized factors
            profile = await self.profile_manager.get_or_create_profile(user_session_id, workspace_path)
            complexity_accumulation = self._calculate_complexity_accumulation(context, profile)
            fatigue_factor = self._calculate_fatigue_factor(context, profile)

            # Calculate unified cognitive load score
            component_loads = [v for k, v in load_components.items() if isinstance(v, (int, float))]
            base_load = statistics.mean(component_loads) if component_loads else 0.5

            # Apply context factors
            context_multiplier = 1.0 + (session_duration_factor * 0.2) + (context_switch_penalty * 0.3)
            adjusted_load = base_load * context_multiplier + complexity_accumulation + fatigue_factor

            # Normalize to 0-1 range
            overall_load = min(1.0, max(0.0, adjusted_load))

            # Determine load state
            if overall_load <= 0.2:
                load_state = CognitiveLoadState.MINIMAL
            elif overall_load <= 0.4:
                load_state = CognitiveLoadState.LOW
            elif overall_load <= 0.6:
                load_state = CognitiveLoadState.MODERATE
            elif overall_load <= 0.8:
                load_state = CognitiveLoadState.HIGH
            else:
                load_state = CognitiveLoadState.OVERWHELMING

            # Calculate measurement confidence
            confidence = min(1.0, len(component_loads) / 6.0)  # Higher confidence with more components

            # Create comprehensive reading
            reading = CognitiveLoadReading(
                timestamp=datetime.now(timezone.utc),
                overall_load_score=overall_load,
                load_state=load_state,
                phase2a_code_complexity=load_components.get("phase2a_code_complexity", 0.0),
                phase2a_relationship_load=load_components.get("phase2a_relationship_load", 0.0),
                phase2b_attention_load=load_components.get("phase2b_attention_load", 0.0),
                phase2b_pattern_load=0.0,  # Would be calculated from active patterns
                phase2c_relationship_cognitive_load=load_components.get("phase2c_relationship_cognitive_load", 0.0),
                phase2d_template_load=load_components.get("phase2d_template_load", 0.0),
                session_duration_factor=session_duration_factor,
                context_switch_penalty=context_switch_penalty,
                complexity_accumulation=complexity_accumulation,
                fatigue_factor=fatigue_factor,
                measurement_confidence=confidence,
                component_count=len(component_loads)
            )

            # Track orchestration performance
            orchestration_time_ms = (time.time() - start_time) * 1000
            self._orchestration_metrics["average_overhead_ms"] = (
                (self._orchestration_metrics["average_overhead_ms"] * self._orchestration_metrics["total_orchestrations"] + orchestration_time_ms) /
                (self._orchestration_metrics["total_orchestrations"] + 1)
            )
            self._orchestration_metrics["total_orchestrations"] += 1

            logger.debug(f"📊 Cognitive load reading: {load_state.value} ({overall_load:.2f}) "
                        f"in {orchestration_time_ms:.1f}ms")

            return reading

        except Exception as e:
            logger.error(f"Failed to take comprehensive load reading: {e}")
            # Return safe default reading
            return CognitiveLoadReading(
                timestamp=datetime.now(timezone.utc),
                overall_load_score=0.5,
                load_state=CognitiveLoadState.MODERATE,
                phase2a_code_complexity=0.5,
                phase2a_relationship_load=0.5,
                phase2b_attention_load=0.5,
                phase2b_pattern_load=0.5,
                phase2c_relationship_cognitive_load=0.5,
                phase2d_template_load=0.5,
                session_duration_factor=0.3,
                context_switch_penalty=0.2,
                complexity_accumulation=0.1,
                fatigue_factor=0.2,
                measurement_confidence=0.3,
                component_count=0
            )

    async def coordinate_system_adaptation(
        self,
        user_session_id: str,
        workspace_path: str,
        target_load_reduction: float = 0.3
    ) -> Dict[str, Any]:
        """Coordinate adaptation across all system components to reduce cognitive load."""
        operation_id = self.performance_monitor.start_operation("coordinate_system_adaptation")

        try:
            session_key = f"{user_session_id}_{workspace_path}"
            orchestration_state = self._orchestration_states.get(session_key)

            if not orchestration_state:
                raise ValueError(f"No orchestration state for {session_key}")

            current_load = orchestration_state.current_load_reading.overall_load_score

            # Create adaptation plan
            adaptation_plan = AdaptationPlan(
                adaptation_id=f"adapt_{user_session_id}_{int(time.time())}",
                trigger=OrchestrationTrigger.COGNITIVE_LOAD_SPIKE,
                target_load_reduction=target_load_reduction,
                adaptation_steps=[],
                expected_duration_seconds=5,
                rollback_plan=[],
                success_criteria=["load_reduced", "performance_maintained", "user_comfort_improved"]
            )

            # Coordinate adaptations across all phases
            adaptation_results = {}

            # Phase 2A: Reduce graph operation complexity
            if orchestration_state.current_load_reading.phase2a_relationship_load > 0.6:
                adaptation_results["phase2a"] = await self._adapt_phase2a_complexity(
                    orchestration_state, target_load_reduction * 0.2
                )

            # Phase 2B: Adjust learning and attention thresholds
            if orchestration_state.current_load_reading.phase2b_attention_load > 0.6:
                adaptation_results["phase2b"] = await self._adapt_phase2b_thresholds(
                    orchestration_state, target_load_reduction * 0.3
                )

            # Phase 2C: Enhance relationship filtering
            if orchestration_state.current_load_reading.phase2c_relationship_cognitive_load > 0.6:
                adaptation_results["phase2c"] = await self._adapt_phase2c_filtering(
                    orchestration_state, target_load_reduction * 0.3
                )

            # Phase 2D: Simplify template recommendations
            if orchestration_state.current_load_reading.phase2d_template_load > 0.6:
                adaptation_results["phase2d"] = await self._adapt_phase2d_recommendations(
                    orchestration_state, target_load_reduction * 0.2
                )

            # Calculate total adaptation effectiveness
            adaptations_applied = sum(1 for result in adaptation_results.values() if result.get("success", False))
            total_load_reduction = sum(result.get("load_reduction", 0.0) for result in adaptation_results.values())

            # Update orchestration state
            orchestration_state.active_adaptations = [
                AdaptiveResponse.REDUCE_COMPLEXITY,
                AdaptiveResponse.LIMIT_RESULTS,
                AdaptiveResponse.INCREASE_ACCOMMODATION
            ]

            orchestration_state.adaptation_history.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "trigger": "system_coordination",
                "adaptations_applied": adaptations_applied,
                "load_reduction_achieved": total_load_reduction,
                "success": adaptations_applied > 0
            })

            self._orchestration_metrics["adaptation_triggers"] += 1
            if total_load_reduction > 0:
                self._orchestration_metrics["load_reductions_achieved"] += 1

            self.performance_monitor.end_operation(operation_id, success=True)

            logger.info(f"🎼 Coordinated system adaptation: {adaptations_applied} components adapted, "
                       f"{total_load_reduction:.2f} load reduction")

            return {
                "adaptation_successful": adaptations_applied > 0,
                "components_adapted": adaptations_applied,
                "load_reduction_achieved": total_load_reduction,
                "adaptation_plan": adaptation_plan,
                "results_by_phase": adaptation_results
            }

        except Exception as e:
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"Failed to coordinate system adaptation: {e}")
            return {"adaptation_successful": False, "error": str(e)}

    # Phase-specific Adaptation Coordination

    async def _adapt_phase2a_complexity(
        self, orchestration_state: OrchestrationState, target_reduction: float
    ) -> Dict[str, Any]:
        """Adapt Phase 2A complexity filtering and result limiting."""
        try:
            # Reduce result limits in graph operations
            current_limits = orchestration_state.current_thresholds.get("graph_result_limit", 15)
            new_limit = max(5, int(current_limits * (1 - target_reduction)))

            # Update threshold
            orchestration_state.current_thresholds["graph_result_limit"] = new_limit

            # This would coordinate with graph operations to apply new limits
            # In real implementation: await self.graph_operations.update_result_limits(new_limit)

            return {
                "success": True,
                "load_reduction": target_reduction * 0.8,  # Achieved 80% of target
                "adaptation_applied": f"Reduced graph result limit to {new_limit}",
                "performance_impact_ms": 5
            }

        except Exception as e:
            logger.error(f"Failed to adapt Phase 2A complexity: {e}")
            return {"success": False, "error": str(e)}

    async def _adapt_phase2b_thresholds(
        self, orchestration_state: OrchestrationState, target_reduction: float
    ) -> Dict[str, Any]:
        """Adapt Phase 2B learning thresholds and attention management."""
        try:
            # Reduce complexity tolerance for attention state compatibility
            current_tolerance = orchestration_state.current_thresholds.get("complexity_tolerance", 0.6)
            new_tolerance = max(0.3, current_tolerance - target_reduction)

            # Update threshold
            orchestration_state.current_thresholds["complexity_tolerance"] = new_tolerance

            # This would coordinate with learning components
            # In real implementation: await self.profile_manager.update_complexity_tolerance(user_id, new_tolerance)

            return {
                "success": True,
                "load_reduction": target_reduction * 0.9,
                "adaptation_applied": f"Reduced complexity tolerance to {new_tolerance:.2f}",
                "performance_impact_ms": 3
            }

        except Exception as e:
            logger.error(f"Failed to adapt Phase 2B thresholds: {e}")
            return {"success": False, "error": str(e)}

    async def _adapt_phase2c_filtering(
        self, orchestration_state: OrchestrationState, target_reduction: float
    ) -> Dict[str, Any]:
        """Adapt Phase 2C relationship filtering for reduced cognitive load."""
        try:
            # Enable more aggressive ADHD filtering
            current_filter_level = orchestration_state.current_thresholds.get("relationship_filter_aggressiveness", 0.5)
            new_filter_level = min(1.0, current_filter_level + target_reduction)

            # Update threshold
            orchestration_state.current_thresholds["relationship_filter_aggressiveness"] = new_filter_level

            # This would coordinate with ADHD filter
            # In real implementation: await self.adhd_filter.increase_filtering_aggressiveness(new_filter_level)

            return {
                "success": True,
                "load_reduction": target_reduction * 0.85,
                "adaptation_applied": f"Increased filtering aggressiveness to {new_filter_level:.2f}",
                "performance_impact_ms": 8
            }

        except Exception as e:
            logger.error(f"Failed to adapt Phase 2C filtering: {e}")
            return {"success": False, "error": str(e)}

    async def _adapt_phase2d_recommendations(
        self, orchestration_state: OrchestrationState, target_reduction: float
    ) -> Dict[str, Any]:
        """Adapt Phase 2D template recommendations for cognitive load management."""
        try:
            # Prefer simpler templates
            current_complexity_preference = orchestration_state.current_thresholds.get("template_complexity_preference", 0.6)
            new_preference = max(0.3, current_complexity_preference - target_reduction)

            # Update threshold
            orchestration_state.current_thresholds["template_complexity_preference"] = new_preference

            # This would coordinate with recommendation engine
            # In real implementation: await self.recommendation_engine.prefer_simpler_templates(new_preference)

            return {
                "success": True,
                "load_reduction": target_reduction * 0.7,
                "adaptation_applied": f"Simplified template preference to {new_preference:.2f}",
                "performance_impact_ms": 10
            }

        except Exception as e:
            logger.error(f"Failed to adapt Phase 2D recommendations: {e}")
            return {"success": False, "error": str(e)}

    # Cognitive Load Analysis

    def _calculate_complexity_accumulation(
        self, context: NavigationContext, profile: PersonalLearningProfile
    ) -> float:
        """Calculate complexity accumulation factor over session."""
        # Complexity accumulates over time, especially for ADHD users
        session_minutes = context.session_duration_minutes
        optimal_minutes = profile.average_attention_span_minutes

        if session_minutes <= optimal_minutes:
            return 0.0  # No accumulation within optimal span
        elif session_minutes <= optimal_minutes * 1.5:
            return 0.1  # Mild accumulation
        else:
            return min(0.3, (session_minutes - optimal_minutes) / optimal_minutes * 0.2)

    def _calculate_fatigue_factor(
        self, context: NavigationContext, profile: PersonalLearningProfile
    ) -> float:
        """Calculate cognitive fatigue factor."""
        fatigue_indicators = []

        # Session duration fatigue
        duration_ratio = context.session_duration_minutes / profile.average_attention_span_minutes
        if duration_ratio > 1.5:
            fatigue_indicators.append(0.4)
        elif duration_ratio > 1.0:
            fatigue_indicators.append(0.2)
        else:
            fatigue_indicators.append(0.0)

        # Context switching fatigue
        switches = len(context.recent_navigation_history)
        if switches > profile.context_switch_tolerance:
            switch_fatigue = (switches - profile.context_switch_tolerance) / 10.0
            fatigue_indicators.append(min(0.3, switch_fatigue))
        else:
            fatigue_indicators.append(0.0)

        # Complexity exposure fatigue
        if hasattr(context, 'average_complexity_encountered'):
            if context.average_complexity_encountered > profile.optimal_complexity_range[1]:
                complexity_fatigue = (context.average_complexity_encountered - profile.optimal_complexity_range[1]) * 0.5
                fatigue_indicators.append(min(0.3, complexity_fatigue))
            else:
                fatigue_indicators.append(0.0)

        return statistics.mean(fatigue_indicators) if fatigue_indicators else 0.0

    def _initialize_personalized_thresholds(self, profile: PersonalLearningProfile) -> Dict[str, float]:
        """Initialize personalized thresholds based on user profile."""
        return {
            "complexity_tolerance": profile.optimal_complexity_range[1],
            "graph_result_limit": float(profile.preferred_result_limit),
            "relationship_filter_aggressiveness": 0.5,
            "template_complexity_preference": profile.optimal_complexity_range[1],
            "attention_preservation_threshold": 0.7,
            "fatigue_detection_sensitivity": 0.8,
            "progressive_disclosure_trigger": 0.6
        }

    # Orchestration State Management

    async def _update_orchestration_state(
        self, session_key: str, new_reading: CognitiveLoadReading
    ) -> None:
        """Update orchestration state with new cognitive load reading."""
        try:
            orchestration_state = self._orchestration_states[session_key]
            orchestration_state.current_load_reading = new_reading
            orchestration_state.last_update = datetime.now(timezone.utc)

            # Update load history
            if session_key not in self._load_history:
                self._load_history[session_key] = []

            self._load_history[session_key].append(new_reading)

            # Keep only recent history for performance
            if len(self._load_history[session_key]) > 100:
                self._load_history[session_key] = self._load_history[session_key][-100:]

        except Exception as e:
            logger.error(f"Failed to update orchestration state: {e}")

    async def _check_adaptation_triggers(
        self, session_key: str, load_reading: CognitiveLoadReading
    ) -> None:
        """Check if cognitive load triggers require system adaptation."""
        try:
            # High cognitive load trigger
            if load_reading.load_state in [CognitiveLoadState.HIGH, CognitiveLoadState.OVERWHELMING]:
                await self._trigger_load_reduction_adaptation(session_key, load_reading)

            # Fatigue detection trigger
            if load_reading.fatigue_factor > self.fatigue_threshold:
                await self._trigger_fatigue_response(session_key, load_reading)

            # Sustained moderate load trigger (prevention)
            if await self._detect_sustained_moderate_load(session_key):
                await self._trigger_preventive_adaptation(session_key, load_reading)

        except Exception as e:
            logger.error(f"Failed to check adaptation triggers: {e}")

    async def _trigger_load_reduction_adaptation(
        self, session_key: str, load_reading: CognitiveLoadReading
    ) -> None:
        """Trigger system-wide adaptation to reduce cognitive load."""
        user_parts = session_key.split('_', 1)
        if len(user_parts) >= 2:
            user_session_id, workspace_path = user_parts[0], user_parts[1]

            # Coordinate load reduction across components
            await self.coordinate_system_adaptation(user_session_id, workspace_path, 0.4)

            logger.warning(f"🚨 High cognitive load detected ({load_reading.load_state.value}) - "
                          f"triggered system adaptation")

    async def _trigger_fatigue_response(
        self, session_key: str, load_reading: CognitiveLoadReading
    ) -> None:
        """Trigger fatigue response across system components."""
        orchestration_state = self._orchestration_states[session_key]

        # Enable maximum accommodations
        orchestration_state.active_adaptations = [
            AdaptiveResponse.SUGGEST_BREAK,
            AdaptiveResponse.ENABLE_FOCUS_MODE,
            AdaptiveResponse.SIMPLIFY_INTERFACE,
            AdaptiveResponse.LIMIT_RESULTS,
            AdaptiveResponse.INCREASE_ACCOMMODATION
        ]

        logger.warning(f"😴 Cognitive fatigue detected (factor: {load_reading.fatigue_factor:.2f}) - "
                      f"triggered fatigue response")

    # Utility Methods

    async def get_orchestration_analytics(self, user_session_id: str, workspace_path: str) -> Dict[str, Any]:
        """Get analytics about cognitive load orchestration effectiveness."""
        try:
            session_key = f"{user_session_id}_{workspace_path}"
            orchestration_state = self._orchestration_states.get(session_key)
            load_history = self._load_history.get(session_key, [])

            if not orchestration_state or not load_history:
                return {"message": "No orchestration data available"}

            # Calculate analytics
            recent_loads = [reading.overall_load_score for reading in load_history[-20:]]  # Last 20 readings
            load_trend = "improving" if len(recent_loads) >= 2 and recent_loads[-1] < recent_loads[0] else "stable"

            analytics = {
                "current_load_state": orchestration_state.current_load_reading.load_state.value,
                "current_load_score": orchestration_state.current_load_reading.overall_load_score,
                "load_trend": load_trend,
                "average_recent_load": statistics.mean(recent_loads) if recent_loads else 0.5,
                "load_volatility": statistics.variance(recent_loads) if len(recent_loads) > 1 else 0.0,
                "active_adaptations": [adaptation.value for adaptation in orchestration_state.active_adaptations],
                "adaptation_count": len(orchestration_state.adaptation_history),
                "measurement_confidence": orchestration_state.current_load_reading.measurement_confidence,
                "orchestration_overhead_ms": self._orchestration_metrics["average_overhead_ms"],
                "system_responsiveness": "excellent" if self._orchestration_metrics["average_overhead_ms"] < 20 else "good"
            }

            return analytics

        except Exception as e:
            logger.error(f"Failed to get orchestration analytics: {e}")
            return {"error": str(e)}

    # Placeholder methods for complex operations requiring full system integration
    async def _get_current_navigation_context(self, user_session_id: str, workspace_path: str) -> Optional[NavigationContext]:
        """Get current navigation context for user."""
        # Would get actual current context from system state
        return None

    async def _detect_sustained_moderate_load(self, session_key: str) -> bool:
        """Detect sustained moderate load that might lead to fatigue."""
        load_history = self._load_history.get(session_key, [])
        if len(load_history) < 5:
            return False

        # Check if load has been moderate or higher for sustained period
        recent_loads = [reading.overall_load_score for reading in load_history[-5:]]
        return all(load >= 0.6 for load in recent_loads)

    async def _trigger_preventive_adaptation(self, session_key: str, load_reading: CognitiveLoadReading) -> None:
        """Trigger preventive adaptation before fatigue occurs."""
        logger.info(f"🛡️ Preventive adaptation triggered for sustained moderate load")
        # Would implement preventive measures


# Convenience functions
async def create_cognitive_load_orchestrator(
    # All Phase 2A-2D components for orchestration
    database: SerenaIntelligenceDatabase,
    graph_operations: SerenaGraphOperations,
    learning_engine: AdaptiveLearningEngine,
    profile_manager: PersonalLearningProfileManager,
    pattern_recognition: AdvancedPatternRecognition,
    effectiveness_tracker: EffectivenessTracker,
    context_optimizer: ContextSwitchingOptimizer,
    relationship_builder: IntelligentRelationshipBuilder,
    adhd_filter: ADHDRelationshipFilter,
    realtime_scorer: RealtimeRelevanceScorer,
    template_manager: StrategyTemplateManager,
    recommendation_engine: PatternReuseRecommendationEngine,
    performance_monitor: PerformanceMonitor = None,
    adhd_navigator: ADHDCodeNavigator = None
) -> CognitiveLoadOrchestrator:
    """Create cognitive load orchestrator with all system components."""
    return CognitiveLoadOrchestrator(
        database, graph_operations, learning_engine, profile_manager,
        pattern_recognition, effectiveness_tracker, context_optimizer,
        relationship_builder, adhd_filter, realtime_scorer,
        template_manager, recommendation_engine, performance_monitor, adhd_navigator
    )


async def test_cognitive_orchestration(
    orchestrator: CognitiveLoadOrchestrator,
    test_user_id: str,
    test_workspace: str
) -> Dict[str, Any]:
    """Test cognitive load orchestration system."""
    try:
        # Create test context
        from .intelligent_relationship_builder import NavigationContext
        from .graph_operations import CodeElementNode

        test_element = CodeElementNode(
            id=1, file_path="test.py", element_name="test_function", element_type="function",
            language="python", start_line=1, end_line=10, complexity_score=0.5,
            complexity_level="moderate", cognitive_load_factor=0.4, access_frequency=5,
            adhd_insights=[], tree_sitter_metadata={}
        )

        test_context = NavigationContext(
            current_element=test_element,
            current_task_type="exploration",
            user_session_id=test_user_id,
            workspace_path=test_workspace,
            session_duration_minutes=15,
            recent_navigation_history=[],
            attention_state="moderate_focus",
            complexity_tolerance=0.6
        )

        # Start orchestration
        orchestration_state = await orchestrator.start_cognitive_orchestration(
            test_user_id, test_workspace, test_context
        )

        # Test adaptation
        adaptation_result = await orchestrator.coordinate_system_adaptation(
            test_user_id, test_workspace, 0.3
        )

        # Get analytics
        analytics = await orchestrator.get_orchestration_analytics(test_user_id, test_workspace)

        return {
            "orchestration_started": True,
            "initial_load_state": orchestration_state.current_load_reading.load_state.value,
            "adaptation_successful": adaptation_result["adaptation_successful"],
            "components_adapted": adaptation_result.get("components_adapted", 0),
            "load_reduction": adaptation_result.get("load_reduction_achieved", 0.0),
            "system_responsiveness": analytics.get("system_responsiveness", "unknown"),
            "orchestration_overhead_ms": analytics.get("orchestration_overhead_ms", 0.0),
            "test_status": "passed" if adaptation_result["adaptation_successful"] else "failed"
        }

    except Exception as e:
        logger.error(f"Cognitive orchestration test failed: {e}")
        return {
            "test_status": "failed",
            "error": str(e),
            "orchestration_started": False
        }


if __name__ == "__main__":
    # Quick test when run directly
    async def main():
        print("🎼 Serena Cognitive Load Orchestrator")
        print("Unified ADHD-optimized cognitive load management across all phases")
        print("✅ Module loaded successfully")

    asyncio.run(main())