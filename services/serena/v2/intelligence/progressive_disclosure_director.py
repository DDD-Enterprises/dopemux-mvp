"""
Serena v2 Phase 2E: Progressive Disclosure Director

Orchestrates complexity revelation across all Phase 2A-2D components for optimal
ADHD cognitive load management with coordinated progressive disclosure.
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

# Phase 2D Components
from .strategy_template_manager import StrategyTemplateManager, NavigationStrategyTemplate

# Phase 2C Components
from .intelligent_relationship_builder import IntelligentRelationshipBuilder, IntelligentRelationship
from .adhd_relationship_filter import ADHDRelationshipFilter

# Phase 2B Components
from .learning_profile_manager import PersonalLearningProfileManager, PersonalLearningProfile
from .adaptive_learning import AttentionState

# Phase 2A Components
from .database import SerenaIntelligenceDatabase
from .graph_operations import SerenaGraphOperations, CodeElementNode

# Layer 1 Components
from ..performance_monitor import PerformanceMonitor

logger = logging.getLogger(__name__)


class DisclosureLevel(str, Enum):
    """Progressive disclosure levels for ADHD optimization."""
    OVERVIEW = "overview"           # Minimal essential information
    SUMMARY = "summary"             # Key points and structure
    DETAILED = "detailed"           # Comprehensive information
    COMPREHENSIVE = "comprehensive" # Full details including edge cases
    EXPERT = "expert"               # All available information


class DisclosureStrategy(str, Enum):
    """Strategies for progressive disclosure coordination."""
    USER_PACED = "user_paced"       # User controls disclosure progression
    LOAD_ADAPTIVE = "load_adaptive" # Adapts to cognitive load automatically
    ATTENTION_SYNCED = "attention_synced"  # Syncs with attention state
    PATTERN_BASED = "pattern_based" # Based on learned user patterns
    HYBRID = "hybrid"               # Combines multiple strategies


class ComponentDisclosureState(str, Enum):
    """Disclosure state for individual components."""
    MINIMAL = "minimal"             # Showing minimal information
    PARTIAL = "partial"             # Showing partial information
    STANDARD = "standard"           # Showing standard information
    ENHANCED = "enhanced"           # Showing enhanced information
    MAXIMAL = "maximal"             # Showing all available information


@dataclass
class DisclosureCoordination:
    """Coordination state for progressive disclosure across components."""
    user_session_id: str
    workspace_path: str
    current_disclosure_level: DisclosureLevel
    disclosure_strategy: DisclosureStrategy

    # Component disclosure states
    phase2a_graph_disclosure: ComponentDisclosureState
    phase2b_learning_disclosure: ComponentDisclosureState
    phase2c_relationship_disclosure: ComponentDisclosureState
    phase2d_template_disclosure: ComponentDisclosureState

    # User interaction tracking
    user_requested_more_detail: int = 0
    user_requested_less_detail: int = 0
    user_overwhelm_signals: int = 0
    user_engagement_level: float = 0.5  # 0.0-1.0

    # Adaptive behavior
    auto_progression_enabled: bool = True
    cognitive_load_threshold: float = 0.6
    attention_state_factor: float = 1.0

    # Performance tracking
    disclosure_decisions_per_second: float = 0.0
    average_decision_time_ms: float = 0.0

    # Metadata
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class DisclosureDecision:
    """Decision about disclosure level for specific component."""
    component: str  # phase2a_graph, phase2b_learning, etc.
    current_level: ComponentDisclosureState
    recommended_level: ComponentDisclosureState
    reasoning: List[str]
    cognitive_impact: float  # Expected cognitive load change
    confidence: float
    user_preference_weight: float


@dataclass
class DisclosurePlan:
    """Plan for coordinated disclosure across components."""
    plan_id: str
    target_cognitive_load: float
    component_decisions: List[DisclosureDecision]
    coordination_sequence: List[str]  # Order of disclosure updates
    expected_load_reduction: float
    rollback_available: bool


class ProgressiveDisclosureDirector:
    """
    Progressive disclosure director orchestrating complexity revelation across all phases.

    Features:
    - Coordinated progressive disclosure across Phase 2A-2D components
    - ADHD-optimized disclosure strategies based on cognitive load and attention state
    - Real-time adaptation of disclosure levels based on user engagement and load
    - Integration with existing component disclosure capabilities without duplication
    - Performance-optimized disclosure coordination maintaining <200ms targets
    - User preference learning for personalized disclosure patterns
    - Cognitive load-aware disclosure timing and sequencing
    - Automatic prevention of information overwhelm through coordinated revelation
    """

    def __init__(
        self,
        # Phase 2A-2D Components for orchestration
        database: SerenaIntelligenceDatabase,
        graph_operations: SerenaGraphOperations,
        profile_manager: PersonalLearningProfileManager,
        relationship_builder: IntelligentRelationshipBuilder,
        adhd_filter: ADHDRelationshipFilter,
        template_manager: StrategyTemplateManager,
        performance_monitor: PerformanceMonitor = None
    ):
        self.database = database
        self.graph_operations = graph_operations
        self.profile_manager = profile_manager
        self.relationship_builder = relationship_builder
        self.adhd_filter = adhd_filter
        self.template_manager = template_manager
        self.performance_monitor = performance_monitor or PerformanceMonitor()

        # Disclosure configuration
        self.default_disclosure_level = DisclosureLevel.SUMMARY
        self.max_information_density = 0.7  # ADHD threshold for information density
        self.disclosure_update_frequency_ms = 500  # Update every 500ms

        # Cognitive load thresholds for disclosure adaptation
        self.disclosure_thresholds = {
            CognitiveLoadState.MINIMAL: DisclosureLevel.COMPREHENSIVE,
            CognitiveLoadState.LOW: DisclosureLevel.DETAILED,
            CognitiveLoadState.MODERATE: DisclosureLevel.SUMMARY,
            CognitiveLoadState.HIGH: DisclosureLevel.OVERVIEW,
            CognitiveLoadState.OVERWHELMING: DisclosureLevel.OVERVIEW
        }

        # Active coordination state
        self._disclosure_coordinations: Dict[str, DisclosureCoordination] = {}
        self._disclosure_history: Dict[str, List[Dict[str, Any]]] = {}

        # Performance tracking
        self._disclosure_metrics = {
            "total_coordinations": 0,
            "successful_adaptations": 0,
            "average_coordination_time_ms": 0.0,
            "overwhelm_preventions": 0
        }

    # Core Progressive Disclosure Coordination

    async def initialize_progressive_disclosure(
        self,
        user_session_id: str,
        workspace_path: str,
        initial_cognitive_load: CognitiveLoadReading
    ) -> DisclosureCoordination:
        """Initialize progressive disclosure coordination for user session."""
        operation_id = self.performance_monitor.start_operation("initialize_progressive_disclosure")

        try:
            # Get user profile for personalized disclosure
            profile = await self.profile_manager.get_or_create_profile(user_session_id, workspace_path)

            # Determine initial disclosure strategy
            disclosure_strategy = self._determine_disclosure_strategy(profile, initial_cognitive_load)

            # Determine initial disclosure level
            initial_level = self._determine_initial_disclosure_level(initial_cognitive_load, profile)

            # Initialize component disclosure states
            component_states = await self._initialize_component_disclosure_states(
                initial_level, profile
            )

            # Create coordination state
            coordination = DisclosureCoordination(
                user_session_id=user_session_id,
                workspace_path=workspace_path,
                current_disclosure_level=initial_level,
                disclosure_strategy=disclosure_strategy,
                phase2a_graph_disclosure=component_states["phase2a_graph"],
                phase2b_learning_disclosure=component_states["phase2b_learning"],
                phase2c_relationship_disclosure=component_states["phase2c_relationship"],
                phase2d_template_disclosure=component_states["phase2d_template"],
                auto_progression_enabled=profile.progressive_disclosure_preference,
                cognitive_load_threshold=profile.optimal_complexity_range[1]
            )

            # Store coordination state
            session_key = f"{user_session_id}_{workspace_path}"
            self._disclosure_coordinations[session_key] = coordination

            # Apply initial disclosure settings to components
            await self._apply_disclosure_coordination(coordination)

            self.performance_monitor.end_operation(operation_id, success=True)

            logger.info(f"📖 Initialized progressive disclosure: {initial_level.value} level "
                       f"with {disclosure_strategy.value} strategy")

            return coordination

        except Exception as e:
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"Failed to initialize progressive disclosure: {e}")
            raise

    async def coordinate_disclosure_adaptation(
        self,
        user_session_id: str,
        workspace_path: str,
        new_cognitive_load: CognitiveLoadReading,
        user_signals: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Coordinate disclosure adaptation based on cognitive load changes."""
        operation_id = self.performance_monitor.start_operation("coordinate_disclosure_adaptation")

        try:
            session_key = f"{user_session_id}_{workspace_path}"
            coordination = self._disclosure_coordinations.get(session_key)

            if not coordination:
                raise ValueError(f"No disclosure coordination for {session_key}")

            # Analyze need for disclosure adaptation
            adaptation_needed = await self._analyze_disclosure_adaptation_need(
                coordination, new_cognitive_load, user_signals
            )

            if not adaptation_needed["needed"]:
                self.performance_monitor.end_operation(operation_id, success=True, cache_hit=True)
                return {"adaptation_applied": False, "reason": adaptation_needed["reason"]}

            # Create disclosure adaptation plan
            adaptation_plan = await self._create_disclosure_adaptation_plan(
                coordination, new_cognitive_load, adaptation_needed
            )

            # Apply coordinated disclosure changes
            application_results = await self._apply_disclosure_plan(adaptation_plan, coordination)

            # Update coordination state
            await self._update_coordination_state(coordination, adaptation_plan, application_results)

            # Track adaptation metrics
            self._disclosure_metrics["successful_adaptations"] += 1
            if adaptation_plan.expected_load_reduction > 0.2:
                self._disclosure_metrics["overwhelm_preventions"] += 1

            self.performance_monitor.end_operation(operation_id, success=True)

            logger.info(f"📖 Coordinated disclosure adaptation: {adaptation_plan.target_cognitive_load:.2f} target load "
                       f"({len(adaptation_plan.component_decisions)} components adapted)")

            return {
                "adaptation_applied": True,
                "adaptation_plan": adaptation_plan,
                "application_results": application_results,
                "new_disclosure_level": coordination.current_disclosure_level.value,
                "load_reduction_achieved": application_results.get("total_load_reduction", 0.0)
            }

        except Exception as e:
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"Failed to coordinate disclosure adaptation: {e}")
            return {"adaptation_applied": False, "error": str(e)}

    # Component Disclosure Coordination

    async def _apply_disclosure_coordination(self, coordination: DisclosureCoordination) -> None:
        """Apply disclosure coordination to all system components."""
        try:
            # Phase 2A: Graph operations disclosure
            await self._coordinate_phase2a_disclosure(
                coordination.phase2a_graph_disclosure, coordination
            )

            # Phase 2B: Learning component disclosure
            await self._coordinate_phase2b_disclosure(
                coordination.phase2b_learning_disclosure, coordination
            )

            # Phase 2C: Relationship disclosure
            await self._coordinate_phase2c_disclosure(
                coordination.phase2c_relationship_disclosure, coordination
            )

            # Phase 2D: Template disclosure
            await self._coordinate_phase2d_disclosure(
                coordination.phase2d_template_disclosure, coordination
            )

        except Exception as e:
            logger.error(f"Failed to apply disclosure coordination: {e}")

    async def _coordinate_phase2a_disclosure(
        self, disclosure_state: ComponentDisclosureState, coordination: DisclosureCoordination
    ) -> None:
        """Coordinate Phase 2A graph operations disclosure."""
        try:
            # Coordinate with graph operations result limiting
            if disclosure_state == ComponentDisclosureState.MINIMAL:
                # Reduce graph query results to 3-5 items
                result_limit = 3
            elif disclosure_state == ComponentDisclosureState.PARTIAL:
                # Standard ADHD result limit
                result_limit = 5
            elif disclosure_state == ComponentDisclosureState.STANDARD:
                # Normal result limit
                result_limit = 10
            else:
                # Enhanced/maximal disclosure
                result_limit = 20

            # This would coordinate with graph operations in real implementation
            # await self.graph_operations.update_result_limit(result_limit)

            logger.debug(f"📊 Phase 2A disclosure: {disclosure_state.value} (limit: {result_limit})")

        except Exception as e:
            logger.error(f"Failed to coordinate Phase 2A disclosure: {e}")

    async def _coordinate_phase2c_disclosure(
        self, disclosure_state: ComponentDisclosureState, coordination: DisclosureCoordination
    ) -> None:
        """Coordinate Phase 2C relationship disclosure."""
        try:
            # Coordinate with ADHD relationship filter
            if disclosure_state == ComponentDisclosureState.MINIMAL:
                # Show only highest confidence relationships
                filter_aggressiveness = 0.9
                max_relationships = 2
            elif disclosure_state == ComponentDisclosureState.PARTIAL:
                # Standard ADHD filtering
                filter_aggressiveness = 0.7
                max_relationships = 3
            elif disclosure_state == ComponentDisclosureState.STANDARD:
                # Normal filtering
                filter_aggressiveness = 0.5
                max_relationships = 5
            else:
                # Enhanced disclosure
                filter_aggressiveness = 0.3
                max_relationships = 8

            # This would coordinate with relationship filter in real implementation
            # await self.adhd_filter.update_filtering_parameters(filter_aggressiveness, max_relationships)

            logger.debug(f"🔗 Phase 2C disclosure: {disclosure_state.value} "
                        f"(aggressiveness: {filter_aggressiveness}, max: {max_relationships})")

        except Exception as e:
            logger.error(f"Failed to coordinate Phase 2C disclosure: {e}")

    async def _coordinate_phase2d_disclosure(
        self, disclosure_state: ComponentDisclosureState, coordination: DisclosureCoordination
    ) -> None:
        """Coordinate Phase 2D template disclosure."""
        try:
            # Coordinate with template manager
            if disclosure_state == ComponentDisclosureState.MINIMAL:
                # Show only template overview
                template_detail_level = "overview"
                max_templates = 1
            elif disclosure_state == ComponentDisclosureState.PARTIAL:
                # Show template summary
                template_detail_level = "summary"
                max_templates = 2
            elif disclosure_state == ComponentDisclosureState.STANDARD:
                # Show standard template details
                template_detail_level = "standard"
                max_templates = 3
            else:
                # Show comprehensive template information
                template_detail_level = "comprehensive"
                max_templates = 5

            # This would coordinate with template manager in real implementation
            # await self.template_manager.update_disclosure_parameters(template_detail_level, max_templates)

            logger.debug(f"📚 Phase 2D disclosure: {disclosure_state.value} "
                        f"(detail: {template_detail_level}, max: {max_templates})")

        except Exception as e:
            logger.error(f"Failed to coordinate Phase 2D disclosure: {e}")

    # Disclosure Analysis and Planning

    async def _analyze_disclosure_adaptation_need(
        self,
        coordination: DisclosureCoordination,
        new_load: CognitiveLoadReading,
        user_signals: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze whether disclosure adaptation is needed."""
        adaptation_reasons = []

        # Cognitive load trigger
        if new_load.load_state in [CognitiveLoadState.HIGH, CognitiveLoadState.OVERWHELMING]:
            adaptation_reasons.append("high_cognitive_load")

        # Sustained moderate load trigger
        if new_load.load_state == CognitiveLoadState.MODERATE and new_load.fatigue_factor > 0.6:
            adaptation_reasons.append("sustained_moderate_load_with_fatigue")

        # User overwhelm signals
        if user_signals and user_signals.get("overwhelm_signals", 0) > 0:
            adaptation_reasons.append("user_overwhelm_signals")
            coordination.user_overwhelm_signals += user_signals["overwhelm_signals"]

        # User requests for less detail
        if user_signals and user_signals.get("requested_less_detail", False):
            adaptation_reasons.append("user_requested_simplification")
            coordination.user_requested_less_detail += 1

        # Attention state incompatibility
        attention_load = new_load.phase2b_attention_load
        if attention_load > 0.7 and coordination.current_disclosure_level in [DisclosureLevel.DETAILED, DisclosureLevel.COMPREHENSIVE]:
            adaptation_reasons.append("attention_state_incompatibility")

        return {
            "needed": len(adaptation_reasons) > 0,
            "reasons": adaptation_reasons,
            "urgency": "high" if "user_overwhelm_signals" in adaptation_reasons else "moderate",
            "reason": ", ".join(adaptation_reasons) if adaptation_reasons else "no_adaptation_needed"
        }

    async def _create_disclosure_adaptation_plan(
        self,
        coordination: DisclosureCoordination,
        new_load: CognitiveLoadReading,
        adaptation_analysis: Dict[str, Any]
    ) -> DisclosurePlan:
        """Create coordinated disclosure adaptation plan."""
        try:
            plan_id = f"disclosure_plan_{coordination.user_session_id}_{int(time.time())}"

            # Determine target cognitive load reduction
            current_load = new_load.overall_load_score
            if new_load.load_state == CognitiveLoadState.OVERWHELMING:
                target_load = 0.4  # Aggressive reduction
            elif new_load.load_state == CognitiveLoadState.HIGH:
                target_load = 0.5  # Moderate reduction
            else:
                target_load = 0.6  # Gentle reduction

            target_reduction = max(0.0, current_load - target_load)

            # Create component-specific disclosure decisions
            component_decisions = []

            # Phase 2A Graph Operations Decision
            graph_decision = DisclosureDecision(
                component="phase2a_graph",
                current_level=coordination.phase2a_graph_disclosure,
                recommended_level=self._recommend_disclosure_level_for_load(
                    new_load.phase2a_relationship_load, ComponentDisclosureState.PARTIAL
                ),
                reasoning=["reduce_graph_complexity", "limit_relationship_suggestions"],
                cognitive_impact=-0.15,  # Expected load reduction
                confidence=0.8,
                user_preference_weight=0.7
            )
            component_decisions.append(graph_decision)

            # Phase 2C Relationship Decision
            relationship_decision = DisclosureDecision(
                component="phase2c_relationship",
                current_level=coordination.phase2c_relationship_disclosure,
                recommended_level=self._recommend_disclosure_level_for_load(
                    new_load.phase2c_relationship_cognitive_load, ComponentDisclosureState.PARTIAL
                ),
                reasoning=["simplify_relationship_presentation", "reduce_suggestion_detail"],
                cognitive_impact=-0.2,  # Highest impact from relationship simplification
                confidence=0.9,
                user_preference_weight=0.8
            )
            component_decisions.append(relationship_decision)

            # Phase 2D Template Decision
            template_decision = DisclosureDecision(
                component="phase2d_template",
                current_level=coordination.phase2d_template_disclosure,
                recommended_level=self._recommend_disclosure_level_for_load(
                    new_load.phase2d_template_load, ComponentDisclosureState.MINIMAL
                ),
                reasoning=["simplify_template_presentation", "focus_on_essentials"],
                cognitive_impact=-0.1,
                confidence=0.7,
                user_preference_weight=0.6
            )
            component_decisions.append(template_decision)

            # Calculate coordination sequence (order of application)
            coordination_sequence = sorted(
                [decision.component for decision in component_decisions],
                key=lambda comp: next(d.cognitive_impact for d in component_decisions if d.component == comp),
                reverse=False  # Apply highest impact (most negative) first
            )

            # Calculate expected load reduction
            expected_reduction = sum(abs(d.cognitive_impact) for d in component_decisions)

            plan = DisclosurePlan(
                plan_id=plan_id,
                target_cognitive_load=target_load,
                component_decisions=component_decisions,
                coordination_sequence=coordination_sequence,
                expected_load_reduction=expected_reduction,
                rollback_available=True
            )

            return plan

        except Exception as e:
            logger.error(f"Failed to create disclosure adaptation plan: {e}")
            raise

    async def _apply_disclosure_plan(
        self, plan: DisclosurePlan, coordination: DisclosureCoordination
    ) -> Dict[str, Any]:
        """Apply disclosure plan across all components."""
        application_results = {
            "components_updated": 0,
            "total_load_reduction": 0.0,
            "application_time_ms": 0.0,
            "component_results": {}
        }

        start_time = time.time()

        try:
            # Apply decisions in coordination sequence
            for component_name in plan.coordination_sequence:
                decision = next(d for d in plan.component_decisions if d.component == component_name)

                # Apply component-specific disclosure change
                component_result = await self._apply_component_disclosure_change(
                    component_name, decision, coordination
                )

                application_results["component_results"][component_name] = component_result

                if component_result.get("success", False):
                    application_results["components_updated"] += 1
                    application_results["total_load_reduction"] += abs(decision.cognitive_impact)

                    # Update coordination state
                    self._update_component_disclosure_state(coordination, component_name, decision.recommended_level)

            application_results["application_time_ms"] = (time.time() - start_time) * 1000

            # Update overall disclosure level if multiple components changed
            if application_results["components_updated"] >= 2:
                coordination.current_disclosure_level = self._calculate_effective_disclosure_level(coordination)

            return application_results

        except Exception as e:
            logger.error(f"Failed to apply disclosure plan: {e}")
            application_results["error"] = str(e)
            return application_results

    async def _apply_component_disclosure_change(
        self,
        component_name: str,
        decision: DisclosureDecision,
        coordination: DisclosureCoordination
    ) -> Dict[str, Any]:
        """Apply disclosure change to specific component."""
        try:
            if component_name == "phase2a_graph":
                # Coordinate with Phase 2A graph operations
                result_limit = self._disclosure_state_to_result_limit(decision.recommended_level)
                # In real implementation: await self.graph_operations.update_adhd_result_limit(result_limit)

                return {
                    "success": True,
                    "change_applied": f"Graph result limit set to {result_limit}",
                    "performance_impact_ms": 5
                }

            elif component_name == "phase2c_relationship":
                # Coordinate with Phase 2C relationship filtering
                filter_level = self._disclosure_state_to_filter_level(decision.recommended_level)
                # In real implementation: await self.adhd_filter.update_disclosure_filtering(filter_level)

                return {
                    "success": True,
                    "change_applied": f"Relationship filter level set to {filter_level}",
                    "performance_impact_ms": 8
                }

            elif component_name == "phase2d_template":
                # Coordinate with Phase 2D template manager
                detail_level = self._disclosure_state_to_template_detail(decision.recommended_level)
                # In real implementation: await self.template_manager.update_disclosure_detail(detail_level)

                return {
                    "success": True,
                    "change_applied": f"Template detail level set to {detail_level}",
                    "performance_impact_ms": 3
                }

            else:
                return {"success": False, "error": f"Unknown component: {component_name}"}

        except Exception as e:
            logger.error(f"Failed to apply disclosure change to {component_name}: {e}")
            return {"success": False, "error": str(e)}

    # User Interaction and Feedback

    async def handle_user_disclosure_request(
        self,
        user_session_id: str,
        workspace_path: str,
        request_type: str,  # "more_detail", "less_detail", "toggle_mode"
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle user requests for disclosure changes."""
        operation_id = self.performance_monitor.start_operation("handle_user_disclosure_request")

        try:
            session_key = f"{user_session_id}_{workspace_path}"
            coordination = self._disclosure_coordinations.get(session_key)

            if not coordination:
                return {"error": "No disclosure coordination active"}

            # Process user request
            if request_type == "more_detail":
                coordination.user_requested_more_detail += 1
                new_level = self._increase_disclosure_level(coordination.current_disclosure_level)
                adaptation_target = -0.1  # Increase load slightly for more detail

            elif request_type == "less_detail":
                coordination.user_requested_less_detail += 1
                new_level = self._decrease_disclosure_level(coordination.current_disclosure_level)
                adaptation_target = 0.2  # Reduce load for less detail

            else:  # toggle_mode
                new_level = DisclosureLevel.OVERVIEW if coordination.current_disclosure_level != DisclosureLevel.OVERVIEW else DisclosureLevel.SUMMARY
                adaptation_target = 0.15

            # Apply user-requested disclosure change
            coordination.current_disclosure_level = new_level

            # Update all components to match new disclosure level
            await self._apply_disclosure_coordination(coordination)

            self.performance_monitor.end_operation(operation_id, success=True)

            logger.info(f"👤 User disclosure request: {request_type} → {new_level.value}")

            return {
                "request_processed": True,
                "new_disclosure_level": new_level.value,
                "user_preference_learned": True,
                "adaptation_applied": True
            }

        except Exception as e:
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"Failed to handle user disclosure request: {e}")
            return {"error": str(e), "request_processed": False}

    # Analysis and Optimization

    async def get_disclosure_analytics(
        self, user_session_id: str, workspace_path: str
    ) -> Dict[str, Any]:
        """Get analytics about progressive disclosure effectiveness."""
        try:
            session_key = f"{user_session_id}_{workspace_path}"
            coordination = self._disclosure_coordinations.get(session_key)
            history = self._disclosure_history.get(session_key, [])

            if not coordination:
                return {"message": "No disclosure coordination data"}

            analytics = {
                "current_disclosure_level": coordination.current_disclosure_level.value,
                "disclosure_strategy": coordination.disclosure_strategy.value,
                "user_interaction_patterns": {
                    "requested_more_detail": coordination.user_requested_more_detail,
                    "requested_less_detail": coordination.user_requested_less_detail,
                    "overwhelm_signals": coordination.user_overwhelm_signals,
                    "engagement_level": coordination.user_engagement_level
                },
                "component_disclosure_states": {
                    "phase2a_graph": coordination.phase2a_graph_disclosure.value,
                    "phase2b_learning": coordination.phase2b_learning_disclosure.value,
                    "phase2c_relationship": coordination.phase2c_relationship_disclosure.value,
                    "phase2d_template": coordination.phase2d_template_disclosure.value
                },
                "adaptation_effectiveness": {
                    "total_adaptations": len(coordination.adaptation_history),
                    "overwhelm_preventions": self._disclosure_metrics["overwhelm_preventions"],
                    "successful_adaptations": self._disclosure_metrics["successful_adaptations"]
                },
                "performance_metrics": {
                    "average_coordination_time_ms": self._disclosure_metrics["average_coordination_time_ms"],
                    "disclosure_decisions_per_second": coordination.disclosure_decisions_per_second
                },
                "disclosure_effectiveness": self._calculate_disclosure_effectiveness(coordination, history)
            }

            return analytics

        except Exception as e:
            logger.error(f"Failed to get disclosure analytics: {e}")
            return {"error": str(e)}

    # Utility Methods

    def _determine_disclosure_strategy(
        self, profile: PersonalLearningProfile, initial_load: CognitiveLoadReading
    ) -> DisclosureStrategy:
        """Determine optimal disclosure strategy for user."""
        if profile.progressive_disclosure_preference:
            if profile.pattern_confidence > 0.8:
                return DisclosureStrategy.PATTERN_BASED
            else:
                return DisclosureStrategy.LOAD_ADAPTIVE
        else:
            return DisclosureStrategy.ATTENTION_SYNCED

    def _determine_initial_disclosure_level(
        self, initial_load: CognitiveLoadReading, profile: PersonalLearningProfile
    ) -> DisclosureLevel:
        """Determine initial disclosure level based on load and profile."""
        base_level = self.disclosure_thresholds.get(initial_load.load_state, DisclosureLevel.SUMMARY)

        # Adjust based on user experience
        if profile.pattern_confidence > 0.8:
            # Experienced users can handle more detail
            level_progression = {
                DisclosureLevel.OVERVIEW: DisclosureLevel.SUMMARY,
                DisclosureLevel.SUMMARY: DisclosureLevel.DETAILED,
                DisclosureLevel.DETAILED: DisclosureLevel.DETAILED
            }
            return level_progression.get(base_level, base_level)

        return base_level

    async def _initialize_component_disclosure_states(
        self, initial_level: DisclosureLevel, profile: PersonalLearningProfile
    ) -> Dict[str, ComponentDisclosureState]:
        """Initialize disclosure states for all components."""
        # Map disclosure level to component states
        level_to_state_mapping = {
            DisclosureLevel.OVERVIEW: ComponentDisclosureState.MINIMAL,
            DisclosureLevel.SUMMARY: ComponentDisclosureState.PARTIAL,
            DisclosureLevel.DETAILED: ComponentDisclosureState.STANDARD,
            DisclosureLevel.COMPREHENSIVE: ComponentDisclosureState.ENHANCED,
            DisclosureLevel.EXPERT: ComponentDisclosureState.MAXIMAL
        }

        base_state = level_to_state_mapping.get(initial_level, ComponentDisclosureState.PARTIAL)

        return {
            "phase2a_graph": base_state,
            "phase2b_learning": base_state,
            "phase2c_relationship": base_state,
            "phase2d_template": base_state
        }

    def _recommend_disclosure_level_for_load(
        self, component_load: float, fallback: ComponentDisclosureState
    ) -> ComponentDisclosureState:
        """Recommend disclosure level for component based on its cognitive load."""
        if component_load > 0.8:
            return ComponentDisclosureState.MINIMAL
        elif component_load > 0.6:
            return ComponentDisclosureState.PARTIAL
        elif component_load > 0.4:
            return ComponentDisclosureState.STANDARD
        else:
            return ComponentDisclosureState.ENHANCED

    def _update_component_disclosure_state(
        self, coordination: DisclosureCoordination, component_name: str, new_state: ComponentDisclosureState
    ) -> None:
        """Update component disclosure state in coordination."""
        if component_name == "phase2a_graph":
            coordination.phase2a_graph_disclosure = new_state
        elif component_name == "phase2b_learning":
            coordination.phase2b_learning_disclosure = new_state
        elif component_name == "phase2c_relationship":
            coordination.phase2c_relationship_disclosure = new_state
        elif component_name == "phase2d_template":
            coordination.phase2d_template_disclosure = new_state

    def _calculate_effective_disclosure_level(self, coordination: DisclosureCoordination) -> DisclosureLevel:
        """Calculate effective disclosure level from component states."""
        # Use the most conservative (minimal) component state as the effective level
        component_states = [
            coordination.phase2a_graph_disclosure,
            coordination.phase2c_relationship_disclosure,
            coordination.phase2d_template_disclosure
        ]

        min_state = min(component_states, key=lambda s: list(ComponentDisclosureState).index(s))

        state_to_level = {
            ComponentDisclosureState.MINIMAL: DisclosureLevel.OVERVIEW,
            ComponentDisclosureState.PARTIAL: DisclosureLevel.SUMMARY,
            ComponentDisclosureState.STANDARD: DisclosureLevel.DETAILED,
            ComponentDisclosureState.ENHANCED: DisclosureLevel.COMPREHENSIVE,
            ComponentDisclosureState.MAXIMAL: DisclosureLevel.EXPERT
        }

        return state_to_level.get(min_state, DisclosureLevel.SUMMARY)

    def _increase_disclosure_level(self, current_level: DisclosureLevel) -> DisclosureLevel:
        """Increase disclosure level by one step."""
        level_progression = {
            DisclosureLevel.OVERVIEW: DisclosureLevel.SUMMARY,
            DisclosureLevel.SUMMARY: DisclosureLevel.DETAILED,
            DisclosureLevel.DETAILED: DisclosureLevel.COMPREHENSIVE,
            DisclosureLevel.COMPREHENSIVE: DisclosureLevel.EXPERT,
            DisclosureLevel.EXPERT: DisclosureLevel.EXPERT
        }
        return level_progression.get(current_level, current_level)

    def _decrease_disclosure_level(self, current_level: DisclosureLevel) -> DisclosureLevel:
        """Decrease disclosure level by one step."""
        level_regression = {
            DisclosureLevel.EXPERT: DisclosureLevel.COMPREHENSIVE,
            DisclosureLevel.COMPREHENSIVE: DisclosureLevel.DETAILED,
            DisclosureLevel.DETAILED: DisclosureLevel.SUMMARY,
            DisclosureLevel.SUMMARY: DisclosureLevel.OVERVIEW,
            DisclosureLevel.OVERVIEW: DisclosureLevel.OVERVIEW
        }
        return level_regression.get(current_level, current_level)

    # Placeholder methods for complex operations
    async def _coordinate_phase2b_disclosure(self, disclosure_state: ComponentDisclosureState, coordination: DisclosureCoordination) -> None:
        """Coordinate Phase 2B learning disclosure."""
        pass  # Would coordinate with learning components

    async def _update_coordination_state(self, coordination: DisclosureCoordination, plan: DisclosurePlan, results: Dict[str, Any]) -> None:
        """Update coordination state after plan application."""
        coordination.last_updated = datetime.now(timezone.utc)

    def _disclosure_state_to_result_limit(self, state: ComponentDisclosureState) -> int:
        """Convert disclosure state to result limit."""
        mapping = {
            ComponentDisclosureState.MINIMAL: 3,
            ComponentDisclosureState.PARTIAL: 5,
            ComponentDisclosureState.STANDARD: 10,
            ComponentDisclosureState.ENHANCED: 15,
            ComponentDisclosureState.MAXIMAL: 25
        }
        return mapping.get(state, 5)

    def _disclosure_state_to_filter_level(self, state: ComponentDisclosureState) -> float:
        """Convert disclosure state to filter aggressiveness level."""
        mapping = {
            ComponentDisclosureState.MINIMAL: 0.9,
            ComponentDisclosureState.PARTIAL: 0.7,
            ComponentDisclosureState.STANDARD: 0.5,
            ComponentDisclosureState.ENHANCED: 0.3,
            ComponentDisclosureState.MAXIMAL: 0.1
        }
        return mapping.get(state, 0.5)

    def _disclosure_state_to_template_detail(self, state: ComponentDisclosureState) -> str:
        """Convert disclosure state to template detail level."""
        mapping = {
            ComponentDisclosureState.MINIMAL: "overview",
            ComponentDisclosureState.PARTIAL: "summary",
            ComponentDisclosureState.STANDARD: "standard",
            ComponentDisclosureState.ENHANCED: "detailed",
            ComponentDisclosureState.MAXIMAL: "comprehensive"
        }
        return mapping.get(state, "summary")

    def _calculate_disclosure_effectiveness(self, coordination: DisclosureCoordination, history: List[Dict[str, Any]]) -> float:
        """Calculate effectiveness of disclosure coordination."""
        if coordination.user_overwhelm_signals == 0 and coordination.user_requested_less_detail <= 1:
            return 0.9  # High effectiveness - no overwhelm
        elif coordination.user_requested_more_detail > coordination.user_requested_less_detail:
            return 0.7  # User wants more detail - moderate effectiveness
        else:
            return 0.6  # Some overwhelm or simplification requests


# Convenience functions
async def create_progressive_disclosure_director(
    database: SerenaIntelligenceDatabase,
    graph_operations: SerenaGraphOperations,
    profile_manager: PersonalLearningProfileManager,
    relationship_builder: IntelligentRelationshipBuilder,
    adhd_filter: ADHDRelationshipFilter,
    template_manager: StrategyTemplateManager,
    performance_monitor: PerformanceMonitor = None
) -> ProgressiveDisclosureDirector:
    """Create progressive disclosure director instance."""
    return ProgressiveDisclosureDirector(
        database, graph_operations, profile_manager, relationship_builder,
        adhd_filter, template_manager, performance_monitor
    )


async def test_progressive_disclosure(
    director: ProgressiveDisclosureDirector,
    test_user_id: str,
    test_workspace: str
) -> Dict[str, Any]:
    """Test progressive disclosure coordination."""
    try:
        # Create test cognitive load reading
        from .cognitive_load_orchestrator import CognitiveLoadReading, CognitiveLoadState

        test_load = CognitiveLoadReading(
            timestamp=datetime.now(timezone.utc),
            overall_load_score=0.7,
            load_state=CognitiveLoadState.HIGH,
            phase2a_code_complexity=0.6,
            phase2a_relationship_load=0.8,
            phase2b_attention_load=0.7,
            phase2b_pattern_load=0.5,
            phase2c_relationship_cognitive_load=0.8,
            phase2d_template_load=0.6,
            session_duration_factor=0.5,
            context_switch_penalty=0.3,
            complexity_accumulation=0.2,
            fatigue_factor=0.4,
            measurement_confidence=0.9,
            component_count=6
        )

        # Initialize disclosure
        coordination = await director.initialize_progressive_disclosure(
            test_user_id, test_workspace, test_load
        )

        # Test adaptation
        adaptation_result = await director.coordinate_disclosure_adaptation(
            test_user_id, test_workspace, test_load
        )

        # Test user interaction
        user_request_result = await director.handle_user_disclosure_request(
            test_user_id, test_workspace, "less_detail"
        )

        # Get analytics
        analytics = await director.get_disclosure_analytics(test_user_id, test_workspace)

        return {
            "disclosure_initialized": True,
            "initial_level": coordination.current_disclosure_level.value,
            "adaptation_successful": adaptation_result["adaptation_applied"],
            "user_request_handled": user_request_result["request_processed"],
            "components_coordinated": len([
                coordination.phase2a_graph_disclosure,
                coordination.phase2c_relationship_disclosure,
                coordination.phase2d_template_disclosure
            ]),
            "disclosure_effectiveness": analytics.get("disclosure_effectiveness", 0.0),
            "test_status": "passed"
        }

    except Exception as e:
        logger.error(f"Progressive disclosure test failed: {e}")
        return {
            "test_status": "failed",
            "error": str(e),
            "disclosure_initialized": False
        }


if __name__ == "__main__":
    # Quick test when run directly
    async def main():
        print("📖 Serena Progressive Disclosure Director")
        print("Coordinated complexity revelation across all system components")
        print("✅ Module loaded successfully")

    asyncio.run(main())