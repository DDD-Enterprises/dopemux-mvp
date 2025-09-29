"""
Serena v2 Phase 2E: Fatigue Detection & Adaptive Response Engine

Proactive cognitive fatigue detection with system-wide adaptive response,
integrating with Phase 2B attention management and all component coordination.
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
import math

# Phase 2E Components
from .cognitive_load_orchestrator import CognitiveLoadOrchestrator, CognitiveLoadReading, CognitiveLoadState
from .progressive_disclosure_director import ProgressiveDisclosureDirector, DisclosureLevel

# Phase 2B Components (Integration Points)
from .adaptive_learning import AttentionState, AdaptiveLearningEngine
from .learning_profile_manager import PersonalLearningProfileManager, PersonalLearningProfile
from .context_switching_optimizer import ContextSwitchingOptimizer, ContextSwitchEvent
from .effectiveness_tracker import EffectivenessTracker

# Phase 2A Components
from .database import SerenaIntelligenceDatabase

# Layer 1 Components
from ..performance_monitor import PerformanceMonitor

logger = logging.getLogger(__name__)


class FatigueIndicator(str, Enum):
    """Types of cognitive fatigue indicators."""
    SESSION_DURATION_EXCEEDED = "session_duration_exceeded"       # Session longer than optimal
    ATTENTION_STATE_DEGRADATION = "attention_state_degradation"   # Attention declining
    CONTEXT_SWITCH_FREQUENCY = "context_switch_frequency"         # Too many context switches
    COGNITIVE_LOAD_ACCUMULATION = "cognitive_load_accumulation"   # Sustained high load
    EFFECTIVENESS_DECLINE = "effectiveness_decline"               # Performance declining
    USER_BEHAVIOR_CHANGES = "user_behavior_changes"               # Behavioral fatigue signs
    COMPLEXITY_AVOIDANCE = "complexity_avoidance"                 # Avoiding complex tasks
    INCREASED_ERRORS = "increased_errors"                         # More navigation errors


class FatigueSeverity(str, Enum):
    """Severity levels of cognitive fatigue."""
    NONE = "none"               # No fatigue detected
    MILD = "mild"               # Early fatigue signs
    MODERATE = "moderate"       # Clear fatigue present
    SEVERE = "severe"           # Significant fatigue affecting performance
    CRITICAL = "critical"       # Overwhelming fatigue, immediate intervention needed


class AdaptiveResponseType(str, Enum):
    """Types of adaptive responses to fatigue."""
    GENTLE_WARNING = "gentle_warning"                     # Soft notification
    SUGGEST_BREAK = "suggest_break"                       # Recommend taking a break
    REDUCE_COMPLEXITY = "reduce_complexity"               # Simplify current task
    ENABLE_FOCUS_MODE = "enable_focus_mode"              # Activate focus mode
    LIMIT_INFORMATION = "limit_information"              # Reduce information density
    ENHANCE_ACCOMMODATIONS = "enhance_accommodations"    # Increase ADHD support
    PAUSE_LEARNING = "pause_learning"                    # Stop pattern learning temporarily
    EMERGENCY_SIMPLIFICATION = "emergency_simplification"  # Maximum simplification


@dataclass
class FatigueDetection:
    """Detected cognitive fatigue with analysis."""
    detection_id: str
    user_session_id: str
    workspace_path: str
    detection_timestamp: datetime

    # Fatigue assessment
    fatigue_severity: FatigueSeverity
    confidence: float  # 0.0-1.0 confidence in detection
    contributing_indicators: List[FatigueIndicator]
    fatigue_score: float  # 0.0-1.0 overall fatigue level

    # Context information
    session_duration_minutes: float
    attention_state: AttentionState
    cognitive_load_reading: CognitiveLoadReading
    recent_effectiveness_scores: List[float]

    # Predictive analysis
    estimated_time_to_critical: Optional[float] = None  # Minutes until critical fatigue
    recovery_time_estimate: Optional[float] = None      # Minutes needed for recovery
    intervention_urgency: str = "moderate"              # low, moderate, high, critical


@dataclass
class AdaptiveResponsePlan:
    """Plan for adaptive response to cognitive fatigue."""
    response_id: str
    fatigue_detection: FatigueDetection
    response_strategy: str  # gentle, moderate, aggressive, emergency

    # Response actions
    immediate_responses: List[AdaptiveResponseType]
    component_adaptations: Dict[str, Dict[str, Any]]  # Phase-specific adaptations
    user_guidance: Dict[str, Any]

    # Implementation details
    response_sequence: List[str]  # Order of response application
    expected_fatigue_reduction: float
    estimated_implementation_time_ms: float
    rollback_plan: List[str]

    # Success criteria
    success_indicators: List[str]
    validation_metrics: Dict[str, float]


@dataclass
class FatigueResponseResult:
    """Result of fatigue response implementation."""
    response_plan: AdaptiveResponsePlan
    implementation_successful: bool
    responses_applied: int
    fatigue_reduction_achieved: float
    user_response: Optional[str] = None  # positive, neutral, negative
    system_performance_impact: float = 0.0
    adaptation_effective: bool = True


class FatigueDetectionEngine:
    """
    Cognitive fatigue detection and adaptive response engine.

    Features:
    - Multi-indicator fatigue detection integrating Phase 2B attention management
    - Proactive fatigue prediction preventing cognitive overload before it occurs
    - System-wide adaptive response coordinating all Phase 2A-2D components
    - Integration with context switching optimizer for fatigue pattern recognition
    - ADHD-specific fatigue indicators and personalized threshold adaptation
    - Real-time response coordination maintaining <200ms performance targets
    - User-friendly fatigue communication with gentle guidance and support
    - Recovery time estimation and intervention urgency assessment
    """

    def __init__(
        self,
        # Core orchestration components
        cognitive_orchestrator: CognitiveLoadOrchestrator,
        disclosure_director: ProgressiveDisclosureDirector,

        # Phase 2B integration components
        learning_engine: AdaptiveLearningEngine,
        profile_manager: PersonalLearningProfileManager,
        context_optimizer: ContextSwitchingOptimizer,
        effectiveness_tracker: EffectivenessTracker,

        # Database and monitoring
        database: SerenaIntelligenceDatabase,
        performance_monitor: PerformanceMonitor = None
    ):
        self.cognitive_orchestrator = cognitive_orchestrator
        self.disclosure_director = disclosure_director
        self.learning_engine = learning_engine
        self.profile_manager = profile_manager
        self.context_optimizer = context_optimizer
        self.effectiveness_tracker = effectiveness_tracker
        self.database = database
        self.performance_monitor = performance_monitor or PerformanceMonitor()

        # Fatigue detection configuration
        self.fatigue_detection_interval_ms = 1000  # Check every second
        self.mild_fatigue_threshold = 0.6
        self.moderate_fatigue_threshold = 0.75
        self.severe_fatigue_threshold = 0.85
        self.critical_fatigue_threshold = 0.95

        # Response configuration
        self.response_delay_seconds = 30  # Wait 30s before suggesting breaks
        self.max_concurrent_adaptations = 5

        # Active tracking
        self._active_detections: Dict[str, FatigueDetection] = {}
        self._fatigue_history: Dict[str, List[float]] = {}
        self._response_callbacks: List[Callable] = []

        # Metrics
        self._fatigue_metrics = {
            "total_detections": 0,
            "prevented_overloads": 0,
            "successful_interventions": 0,
            "average_response_time_ms": 0.0
        }

    # Core Fatigue Detection

    async def monitor_cognitive_fatigue(
        self,
        user_session_id: str,
        workspace_path: str,
        cognitive_load: CognitiveLoadReading,
        attention_state: AttentionState,
        recent_context_switches: List[ContextSwitchEvent]
    ) -> Optional[FatigueDetection]:
        """Monitor cognitive fatigue with multi-indicator analysis."""
        operation_id = self.performance_monitor.start_operation("monitor_cognitive_fatigue")

        try:
            # Get user profile for personalized detection
            profile = await self.profile_manager.get_or_create_profile(user_session_id, workspace_path)

            # Analyze fatigue indicators
            fatigue_indicators = await self._analyze_fatigue_indicators(
                cognitive_load, attention_state, recent_context_switches, profile
            )

            # Calculate overall fatigue score
            fatigue_score = self._calculate_overall_fatigue_score(
                fatigue_indicators, cognitive_load, profile
            )

            # Determine fatigue severity
            fatigue_severity = self._determine_fatigue_severity(fatigue_score)

            # If no fatigue, return None
            if fatigue_severity == FatigueSeverity.NONE:
                self.performance_monitor.end_operation(operation_id, success=True, cache_hit=True)
                return None

            # Create fatigue detection
            detection = FatigueDetection(
                detection_id=f"fatigue_{user_session_id}_{int(time.time())}",
                user_session_id=user_session_id,
                workspace_path=workspace_path,
                detection_timestamp=datetime.now(timezone.utc),
                fatigue_severity=fatigue_severity,
                confidence=self._calculate_detection_confidence(fatigue_indicators),
                contributing_indicators=[indicator["type"] for indicator in fatigue_indicators],
                fatigue_score=fatigue_score,
                session_duration_minutes=cognitive_load.session_duration_factor * 60,  # Convert back to minutes
                attention_state=attention_state,
                cognitive_load_reading=cognitive_load,
                recent_effectiveness_scores=await self._get_recent_effectiveness_scores(user_session_id),
                estimated_time_to_critical=self._estimate_time_to_critical_fatigue(
                    fatigue_score, fatigue_indicators
                ),
                recovery_time_estimate=self._estimate_recovery_time(fatigue_severity, profile),
                intervention_urgency=self._assess_intervention_urgency(fatigue_severity, fatigue_indicators)
            )

            # Store detection
            session_key = f"{user_session_id}_{workspace_path}"
            self._active_detections[session_key] = detection

            # Update fatigue history
            if session_key not in self._fatigue_history:
                self._fatigue_history[session_key] = []
            self._fatigue_history[session_key].append(fatigue_score)

            self._fatigue_metrics["total_detections"] += 1

            self.performance_monitor.end_operation(operation_id, success=True)

            logger.warning(f"😴 Cognitive fatigue detected: {fatigue_severity.value} "
                          f"(score: {fatigue_score:.2f}, confidence: {detection.confidence:.2f})")

            return detection

        except Exception as e:
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"Failed to monitor cognitive fatigue: {e}")
            return None

    async def respond_to_fatigue(
        self,
        fatigue_detection: FatigueDetection
    ) -> FatigueResponseResult:
        """Respond to detected cognitive fatigue with coordinated adaptive response."""
        operation_id = self.performance_monitor.start_operation("respond_to_fatigue")

        try:
            # Create adaptive response plan
            response_plan = await self._create_fatigue_response_plan(fatigue_detection)

            # Apply response plan across system components
            implementation_result = await self._implement_fatigue_response(response_plan)

            # Create response result
            response_result = FatigueResponseResult(
                response_plan=response_plan,
                implementation_successful=implementation_result["success"],
                responses_applied=implementation_result["responses_applied"],
                fatigue_reduction_achieved=implementation_result["fatigue_reduction"],
                system_performance_impact=implementation_result["performance_impact_ms"],
                adaptation_effective=implementation_result["effectiveness_score"] > 0.7
            )

            # Update metrics
            if response_result.implementation_successful:
                self._fatigue_metrics["successful_interventions"] += 1

            if fatigue_detection.fatigue_severity in [FatigueSeverity.SEVERE, FatigueSeverity.CRITICAL]:
                self._fatigue_metrics["prevented_overloads"] += 1

            self.performance_monitor.end_operation(operation_id, success=True)

            logger.info(f"🛟 Fatigue response applied: {response_result.responses_applied} adaptations, "
                       f"{response_result.fatigue_reduction_achieved:.2f} load reduction")

            return response_result

        except Exception as e:
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"Failed to respond to fatigue: {e}")
            raise

    # Fatigue Indicator Analysis

    async def _analyze_fatigue_indicators(
        self,
        cognitive_load: CognitiveLoadReading,
        attention_state: AttentionState,
        recent_switches: List[ContextSwitchEvent],
        profile: PersonalLearningProfile
    ) -> List[Dict[str, Any]]:
        """Analyze multiple indicators for cognitive fatigue detection."""
        indicators = []

        try:
            # Session duration indicator
            session_minutes = cognitive_load.session_duration_factor * 60
            if session_minutes > profile.average_attention_span_minutes * 1.2:
                severity = min(1.0, (session_minutes - profile.average_attention_span_minutes) / profile.average_attention_span_minutes)
                indicators.append({
                    "type": FatigueIndicator.SESSION_DURATION_EXCEEDED,
                    "severity": severity,
                    "evidence": f"Session {session_minutes:.0f}min exceeds optimal {profile.average_attention_span_minutes:.0f}min",
                    "confidence": 0.9
                })

            # Attention state degradation indicator
            if attention_state == AttentionState.FATIGUE:
                indicators.append({
                    "type": FatigueIndicator.ATTENTION_STATE_DEGRADATION,
                    "severity": 0.8,
                    "evidence": "Attention state is explicitly fatigue",
                    "confidence": 0.95
                })
            elif attention_state == AttentionState.LOW_FOCUS and cognitive_load.phase2b_attention_load > 0.7:
                indicators.append({
                    "type": FatigueIndicator.ATTENTION_STATE_DEGRADATION,
                    "severity": 0.6,
                    "evidence": "Low focus with high attention load",
                    "confidence": 0.8
                })

            # Context switching indicator
            if recent_switches:
                switch_frequency = len(recent_switches) / max(session_minutes / 60, 0.1)  # Switches per hour
                if switch_frequency > profile.context_switch_tolerance * 2:
                    severity = min(1.0, switch_frequency / (profile.context_switch_tolerance * 4))
                    indicators.append({
                        "type": FatigueIndicator.CONTEXT_SWITCH_FREQUENCY,
                        "severity": severity,
                        "evidence": f"Switch frequency {switch_frequency:.1f}/hr exceeds tolerance",
                        "confidence": 0.7
                    })

            # Cognitive load accumulation indicator
            if cognitive_load.overall_load_score > 0.7 and cognitive_load.fatigue_factor > 0.5:
                indicators.append({
                    "type": FatigueIndicator.COGNITIVE_LOAD_ACCUMULATION,
                    "severity": cognitive_load.overall_load_score,
                    "evidence": f"Sustained high load {cognitive_load.overall_load_score:.2f} with fatigue factor {cognitive_load.fatigue_factor:.2f}",
                    "confidence": 0.85
                })

            # Complexity avoidance indicator (from recent navigation patterns)
            complexity_avoidance = await self._detect_complexity_avoidance_pattern(
                profile.user_session_id, cognitive_load
            )
            if complexity_avoidance > 0.6:
                indicators.append({
                    "type": FatigueIndicator.COMPLEXITY_AVOIDANCE,
                    "severity": complexity_avoidance,
                    "evidence": "User avoiding complex tasks/elements",
                    "confidence": 0.6
                })

            return indicators

        except Exception as e:
            logger.error(f"Failed to analyze fatigue indicators: {e}")
            return []

    def _calculate_overall_fatigue_score(
        self,
        fatigue_indicators: List[Dict[str, Any]],
        cognitive_load: CognitiveLoadReading,
        profile: PersonalLearningProfile
    ) -> float:
        """Calculate overall fatigue score from multiple indicators."""
        if not fatigue_indicators:
            return 0.0

        try:
            # Weight indicators by confidence and severity
            weighted_scores = []
            for indicator in fatigue_indicators:
                severity = indicator.get("severity", 0.0)
                confidence = indicator.get("confidence", 0.5)
                weighted_score = severity * confidence
                weighted_scores.append(weighted_score)

            base_fatigue_score = statistics.mean(weighted_scores)

            # Apply cognitive load amplification
            load_amplifier = 1.0 + (cognitive_load.overall_load_score * 0.3)
            amplified_score = base_fatigue_score * load_amplifier

            # Apply personal fatigue sensitivity
            sensitivity_factor = 1.0 - (profile.pattern_confidence * 0.2)  # Less experienced = more sensitive
            personalized_score = amplified_score * sensitivity_factor

            return min(1.0, max(0.0, personalized_score))

        except Exception as e:
            logger.error(f"Failed to calculate overall fatigue score: {e}")
            return 0.5

    def _determine_fatigue_severity(self, fatigue_score: float) -> FatigueSeverity:
        """Determine fatigue severity from score."""
        if fatigue_score >= self.critical_fatigue_threshold:
            return FatigueSeverity.CRITICAL
        elif fatigue_score >= self.severe_fatigue_threshold:
            return FatigueSeverity.SEVERE
        elif fatigue_score >= self.moderate_fatigue_threshold:
            return FatigueSeverity.MODERATE
        elif fatigue_score >= self.mild_fatigue_threshold:
            return FatigueSeverity.MILD
        else:
            return FatigueSeverity.NONE

    # Adaptive Response Planning

    async def _create_fatigue_response_plan(
        self, fatigue_detection: FatigueDetection
    ) -> AdaptiveResponsePlan:
        """Create comprehensive adaptive response plan for fatigue."""
        try:
            response_id = f"response_{fatigue_detection.detection_id}"

            # Determine response strategy based on severity
            if fatigue_detection.fatigue_severity == FatigueSeverity.CRITICAL:
                response_strategy = "emergency"
                immediate_responses = [
                    AdaptiveResponseType.EMERGENCY_SIMPLIFICATION,
                    AdaptiveResponseType.SUGGEST_BREAK,
                    AdaptiveResponseType.PAUSE_LEARNING
                ]
            elif fatigue_detection.fatigue_severity == FatigueSeverity.SEVERE:
                response_strategy = "aggressive"
                immediate_responses = [
                    AdaptiveResponseType.REDUCE_COMPLEXITY,
                    AdaptiveResponseType.ENABLE_FOCUS_MODE,
                    AdaptiveResponseType.ENHANCE_ACCOMMODATIONS,
                    AdaptiveResponseType.SUGGEST_BREAK
                ]
            elif fatigue_detection.fatigue_severity == FatigueSeverity.MODERATE:
                response_strategy = "moderate"
                immediate_responses = [
                    AdaptiveResponseType.LIMIT_INFORMATION,
                    AdaptiveResponseType.REDUCE_COMPLEXITY,
                    AdaptiveResponseType.ENHANCE_ACCOMMODATIONS
                ]
            else:  # MILD
                response_strategy = "gentle"
                immediate_responses = [
                    AdaptiveResponseType.GENTLE_WARNING,
                    AdaptiveResponseType.LIMIT_INFORMATION
                ]

            # Create component-specific adaptations
            component_adaptations = await self._plan_component_adaptations(
                fatigue_detection, response_strategy
            )

            # Generate user guidance
            user_guidance = await self._generate_fatigue_guidance(fatigue_detection)

            # Determine response sequence
            response_sequence = self._determine_response_sequence(immediate_responses, component_adaptations)

            # Estimate effectiveness
            expected_reduction = self._estimate_fatigue_response_effectiveness(
                fatigue_detection.fatigue_severity, len(immediate_responses)
            )

            plan = AdaptiveResponsePlan(
                response_id=response_id,
                fatigue_detection=fatigue_detection,
                response_strategy=response_strategy,
                immediate_responses=immediate_responses,
                component_adaptations=component_adaptations,
                user_guidance=user_guidance,
                response_sequence=response_sequence,
                expected_fatigue_reduction=expected_reduction,
                estimated_implementation_time_ms=200,  # Target <200ms
                rollback_plan=["restore_previous_settings", "re_enable_learning", "reset_accommodations"],
                success_indicators=["fatigue_score_reduced", "user_comfort_improved", "performance_maintained"],
                validation_metrics={"target_fatigue_reduction": expected_reduction, "max_implementation_time": 200}
            )

            return plan

        except Exception as e:
            logger.error(f"Failed to create fatigue response plan: {e}")
            raise

    async def _implement_fatigue_response(self, response_plan: AdaptiveResponsePlan) -> Dict[str, Any]:
        """Implement fatigue response plan across all system components."""
        implementation_result = {
            "success": True,
            "responses_applied": 0,
            "fatigue_reduction": 0.0,
            "performance_impact_ms": 0.0,
            "effectiveness_score": 0.0,
            "component_results": {}
        }

        start_time = time.time()

        try:
            # Apply immediate responses
            for response_type in response_plan.immediate_responses:
                response_result = await self._apply_immediate_response(response_type, response_plan)
                if response_result.get("success", False):
                    implementation_result["responses_applied"] += 1
                    implementation_result["fatigue_reduction"] += response_result.get("load_reduction", 0.0)

            # Apply component adaptations in sequence
            for component, adaptations in response_plan.component_adaptations.items():
                component_result = await self._apply_component_fatigue_adaptation(
                    component, adaptations, response_plan
                )
                implementation_result["component_results"][component] = component_result

                if component_result.get("success", False):
                    implementation_result["fatigue_reduction"] += component_result.get("load_reduction", 0.0)

            # Calculate overall effectiveness
            target_reduction = response_plan.expected_fatigue_reduction
            actual_reduction = implementation_result["fatigue_reduction"]
            implementation_result["effectiveness_score"] = min(1.0, actual_reduction / max(target_reduction, 0.1))

            implementation_result["performance_impact_ms"] = (time.time() - start_time) * 1000

            # Update metrics
            self._fatigue_metrics["average_response_time_ms"] = (
                (self._fatigue_metrics["average_response_time_ms"] * self._fatigue_metrics["successful_interventions"] +
                 implementation_result["performance_impact_ms"]) /
                (self._fatigue_metrics["successful_interventions"] + 1)
            )

            return implementation_result

        except Exception as e:
            logger.error(f"Failed to implement fatigue response: {e}")
            implementation_result["success"] = False
            implementation_result["error"] = str(e)
            return implementation_result

    # Component-Specific Fatigue Adaptations

    async def _apply_immediate_response(
        self, response_type: AdaptiveResponseType, response_plan: AdaptiveResponsePlan
    ) -> Dict[str, Any]:
        """Apply immediate fatigue response."""
        try:
            if response_type == AdaptiveResponseType.SUGGEST_BREAK:
                # Coordinate break suggestion across components
                break_guidance = response_plan.user_guidance.get("break_suggestion", "Consider taking a 5-10 minute break")
                # In real implementation: await self._send_break_notification(break_guidance)

                return {
                    "success": True,
                    "action": "break_suggested",
                    "load_reduction": 0.3,  # Significant load reduction from break
                    "user_guidance": break_guidance
                }

            elif response_type == AdaptiveResponseType.REDUCE_COMPLEXITY:
                # Coordinate complexity reduction with cognitive orchestrator
                complexity_reduction = await self.cognitive_orchestrator.coordinate_system_adaptation(
                    response_plan.fatigue_detection.user_session_id,
                    response_plan.fatigue_detection.workspace_path,
                    0.3  # 30% complexity reduction
                )

                return {
                    "success": complexity_reduction["adaptation_successful"],
                    "action": "complexity_reduced",
                    "load_reduction": complexity_reduction["load_reduction_achieved"],
                    "components_affected": complexity_reduction["components_adapted"]
                }

            elif response_type == AdaptiveResponseType.ENABLE_FOCUS_MODE:
                # Enable focus mode across components
                # In real implementation: await self._enable_system_wide_focus_mode()

                return {
                    "success": True,
                    "action": "focus_mode_enabled",
                    "load_reduction": 0.2,
                    "focus_enhancements": ["reduced_distractions", "simplified_interface"]
                }

            elif response_type == AdaptiveResponseType.LIMIT_INFORMATION:
                # Coordinate information limiting with disclosure director
                disclosure_adaptation = await self.disclosure_director.coordinate_disclosure_adaptation(
                    response_plan.fatigue_detection.user_session_id,
                    response_plan.fatigue_detection.workspace_path,
                    response_plan.fatigue_detection.cognitive_load_reading
                )

                return {
                    "success": disclosure_adaptation["adaptation_applied"],
                    "action": "information_limited",
                    "load_reduction": disclosure_adaptation.get("load_reduction_achieved", 0.15),
                    "disclosure_level": disclosure_adaptation.get("new_disclosure_level", "summary")
                }

            elif response_type == AdaptiveResponseType.ENHANCE_ACCOMMODATIONS:
                # Enhance ADHD accommodations across all components
                accommodation_result = await self._enhance_system_accommodations(response_plan)

                return {
                    "success": accommodation_result["success"],
                    "action": "accommodations_enhanced",
                    "load_reduction": accommodation_result["load_reduction"],
                    "accommodations_applied": accommodation_result["accommodations"]
                }

            else:
                return {"success": False, "error": f"Unknown response type: {response_type}"}

        except Exception as e:
            logger.error(f"Failed to apply immediate response {response_type}: {e}")
            return {"success": False, "error": str(e)}

    async def _plan_component_adaptations(
        self, fatigue_detection: FatigueDetection, response_strategy: str
    ) -> Dict[str, Dict[str, Any]]:
        """Plan component-specific adaptations for fatigue response."""
        adaptations = {}

        try:
            # Phase 2A adaptations
            adaptations["phase2a"] = {
                "reduce_graph_queries": True,
                "limit_relationship_depth": 2,
                "enable_simple_mode": response_strategy in ["aggressive", "emergency"],
                "cache_aggressively": True
            }

            # Phase 2B adaptations
            adaptations["phase2b"] = {
                "pause_pattern_learning": response_strategy == "emergency",
                "reduce_adaptation_rate": 0.5,
                "simplify_effectiveness_tracking": True,
                "enable_fatigue_mode": True
            }

            # Phase 2C adaptations
            adaptations["phase2c"] = {
                "increase_filter_aggressiveness": 0.8 if response_strategy in ["aggressive", "emergency"] else 0.6,
                "limit_relationship_suggestions": 3 if response_strategy == "emergency" else 5,
                "disable_complex_scoring": response_strategy == "emergency",
                "enable_simple_relevance_only": True
            }

            # Phase 2D adaptations
            adaptations["phase2d"] = {
                "prefer_simple_templates": True,
                "disable_template_personalization": response_strategy == "emergency",
                "limit_template_details": True,
                "enable_quick_recommendations": True
            }

            return adaptations

        except Exception as e:
            logger.error(f"Failed to plan component adaptations: {e}")
            return {}

    async def _generate_fatigue_guidance(self, fatigue_detection: FatigueDetection) -> Dict[str, Any]:
        """Generate user-friendly fatigue guidance."""
        guidance = {
            "primary_message": "",
            "break_suggestion": "",
            "continuation_advice": "",
            "recovery_tips": [],
            "system_adaptations": []
        }

        try:
            severity = fatigue_detection.fatigue_severity

            if severity == FatigueSeverity.CRITICAL:
                guidance["primary_message"] = "🛑 High cognitive load detected - system adapted for easier navigation"
                guidance["break_suggestion"] = "Strong recommendation: Take a 10-15 minute break to recharge"
                guidance["continuation_advice"] = "When you return, the system will be in simplified mode"

            elif severity == FatigueSeverity.SEVERE:
                guidance["primary_message"] = "😴 Cognitive fatigue detected - switching to focus mode"
                guidance["break_suggestion"] = "Consider taking a 5-10 minute break"
                guidance["continuation_advice"] = "Focus mode will reduce distractions and simplify navigation"

            elif severity == FatigueSeverity.MODERATE:
                guidance["primary_message"] = "🧠 Cognitive load elevated - simplifying interface"
                guidance["break_suggestion"] = "A short 2-5 minute break might help"
                guidance["continuation_advice"] = "System has reduced complexity to help you focus"

            else:  # MILD
                guidance["primary_message"] = "💡 Early fatigue signs detected - proactive support enabled"
                guidance["continuation_advice"] = "Enhanced ADHD accommodations are now active"

            # Recovery tips based on detected indicators
            if FatigueIndicator.SESSION_DURATION_EXCEEDED in fatigue_detection.contributing_indicators:
                guidance["recovery_tips"].append("🕐 You've been working longer than optimal - breaks are especially helpful")

            if FatigueIndicator.CONTEXT_SWITCH_FREQUENCY in fatigue_detection.contributing_indicators:
                guidance["recovery_tips"].append("🎯 Focus on one area at a time to reduce mental switching")

            if FatigueIndicator.COGNITIVE_LOAD_ACCUMULATION in fatigue_detection.contributing_indicators:
                guidance["recovery_tips"].append("🧘 Deep breathing or brief meditation can help reset mental state")

            # System adaptations explanation
            guidance["system_adaptations"] = [
                "Reduced number of suggestions to prevent overwhelm",
                "Enhanced ADHD accommodations for easier navigation",
                "Simplified interface to reduce cognitive burden",
                "Focus mode available for distraction-free work"
            ]

            return guidance

        except Exception as e:
            logger.error(f"Failed to generate fatigue guidance: {e}")
            return guidance

    # Integration and Monitoring

    async def start_fatigue_monitoring(
        self, user_session_id: str, workspace_path: str
    ) -> None:
        """Start background fatigue monitoring for user session."""
        session_key = f"{user_session_id}_{workspace_path}"

        async def fatigue_monitoring_loop():
            while session_key in self._active_detections or session_key in self.cognitive_orchestrator._orchestration_states:
                try:
                    await asyncio.sleep(self.fatigue_detection_interval_ms / 1000)

                    # Get current orchestration state for load reading
                    orchestration_state = self.cognitive_orchestrator._orchestration_states.get(session_key)
                    if orchestration_state:
                        current_load = orchestration_state.current_load_reading

                        # Get recent context switches
                        recent_switches = []  # Would get from context optimizer

                        # Monitor for fatigue
                        fatigue_detection = await self.monitor_cognitive_fatigue(
                            user_session_id, workspace_path, current_load,
                            AttentionState(current_load.phase2b_attention_load), recent_switches
                        )

                        # Respond to fatigue if detected
                        if fatigue_detection and fatigue_detection.fatigue_severity != FatigueSeverity.NONE:
                            response_result = await self.respond_to_fatigue(fatigue_detection)

                            # Notify callbacks
                            await self._notify_fatigue_callbacks(fatigue_detection, response_result)

                except Exception as e:
                    logger.error(f"Fatigue monitoring loop error: {e}")

        asyncio.create_task(fatigue_monitoring_loop())
        logger.info(f"🔍 Started fatigue monitoring for {user_session_id}")

    def add_fatigue_response_callback(self, callback: Callable) -> None:
        """Add callback for fatigue response events."""
        self._response_callbacks.append(callback)

    async def _notify_fatigue_callbacks(
        self, detection: FatigueDetection, response: FatigueResponseResult
    ) -> None:
        """Notify registered callbacks about fatigue events."""
        for callback in self._response_callbacks:
            try:
                await callback(detection, response)
            except Exception as e:
                logger.error(f"Fatigue callback failed: {e}")

    # Utility Methods

    def _calculate_detection_confidence(self, indicators: List[Dict[str, Any]]) -> float:
        """Calculate confidence in fatigue detection."""
        if not indicators:
            return 0.0

        # Higher confidence with more indicators and higher individual confidence
        indicator_count_factor = min(1.0, len(indicators) / 3.0)
        avg_confidence = statistics.mean([ind.get("confidence", 0.5) for ind in indicators])

        return indicator_count_factor * avg_confidence

    def _estimate_time_to_critical_fatigue(
        self, current_score: float, indicators: List[Dict[str, Any]]
    ) -> Optional[float]:
        """Estimate time until critical fatigue level."""
        if current_score >= self.critical_fatigue_threshold:
            return 0.0  # Already critical

        # Simple linear extrapolation based on indicators
        severe_indicators = [ind for ind in indicators if ind.get("severity", 0) > 0.8]
        if severe_indicators:
            # Fast progression to critical
            return max(5.0, 30.0 - (current_score * 20))  # 5-30 minutes
        else:
            # Slower progression
            return max(15.0, 60.0 - (current_score * 30))  # 15-60 minutes

    def _estimate_recovery_time(self, severity: FatigueSeverity, profile: PersonalLearningProfile) -> float:
        """Estimate recovery time needed."""
        base_recovery_times = {
            FatigueSeverity.MILD: 2.0,      # 2 minutes
            FatigueSeverity.MODERATE: 5.0,  # 5 minutes
            FatigueSeverity.SEVERE: 10.0,   # 10 minutes
            FatigueSeverity.CRITICAL: 20.0  # 20 minutes
        }

        base_time = base_recovery_times.get(severity, 5.0)

        # Adjust based on user's typical recovery patterns
        if profile.average_attention_span_minutes < 20:  # Short attention span
            return base_time * 1.2  # Need slightly longer recovery
        else:
            return base_time

    def _assess_intervention_urgency(
        self, severity: FatigueSeverity, indicators: List[Dict[str, Any]]
    ) -> str:
        """Assess urgency of intervention."""
        if severity == FatigueSeverity.CRITICAL:
            return "critical"
        elif severity == FatigueSeverity.SEVERE:
            return "high"
        elif any(ind.get("confidence", 0) > 0.9 for ind in indicators):
            return "high"  # High confidence indicators increase urgency
        else:
            return "moderate"

    # Placeholder methods for complex operations
    async def _detect_complexity_avoidance_pattern(self, user_session_id: str, cognitive_load: CognitiveLoadReading) -> float:
        return 0.3  # Would detect actual complexity avoidance patterns

    async def _get_recent_effectiveness_scores(self, user_session_id: str) -> List[float]:
        return [0.7, 0.6, 0.5]  # Would get actual recent effectiveness

    async def _apply_component_fatigue_adaptation(self, component: str, adaptations: Dict[str, Any], response_plan: AdaptiveResponsePlan) -> Dict[str, Any]:
        return {"success": True, "load_reduction": 0.1}  # Would apply actual adaptations

    async def _enhance_system_accommodations(self, response_plan: AdaptiveResponsePlan) -> Dict[str, Any]:
        return {"success": True, "load_reduction": 0.15, "accommodations": ["progressive_disclosure", "focus_mode"]}

    def _determine_response_sequence(self, immediate_responses: List[AdaptiveResponseType], component_adaptations: Dict[str, Dict[str, Any]]) -> List[str]:
        return ["immediate_responses", "component_adaptations"]

    def _estimate_fatigue_response_effectiveness(self, severity: FatigueSeverity, response_count: int) -> float:
        severity_factors = {
            FatigueSeverity.MILD: 0.2,
            FatigueSeverity.MODERATE: 0.3,
            FatigueSeverity.SEVERE: 0.4,
            FatigueSeverity.CRITICAL: 0.5
        }
        base_effectiveness = severity_factors.get(severity, 0.3)
        response_bonus = min(0.3, response_count * 0.05)
        return base_effectiveness + response_bonus


# Convenience functions
async def create_fatigue_detection_engine(
    cognitive_orchestrator: CognitiveLoadOrchestrator,
    disclosure_director: ProgressiveDisclosureDirector,
    learning_engine: AdaptiveLearningEngine,
    profile_manager: PersonalLearningProfileManager,
    context_optimizer: ContextSwitchingOptimizer,
    effectiveness_tracker: EffectivenessTracker,
    database: SerenaIntelligenceDatabase,
    performance_monitor: PerformanceMonitor = None
) -> FatigueDetectionEngine:
    """Create fatigue detection engine instance."""
    return FatigueDetectionEngine(
        cognitive_orchestrator, disclosure_director, learning_engine,
        profile_manager, context_optimizer, effectiveness_tracker,
        database, performance_monitor
    )


async def test_fatigue_detection(
    engine: FatigueDetectionEngine,
    test_user_id: str,
    test_workspace: str
) -> Dict[str, Any]:
    """Test fatigue detection and response system."""
    try:
        # Create test cognitive load with fatigue indicators
        from .cognitive_load_orchestrator import CognitiveLoadReading, CognitiveLoadState

        fatigued_load = CognitiveLoadReading(
            timestamp=datetime.now(timezone.utc),
            overall_load_score=0.8,  # High load
            load_state=CognitiveLoadState.HIGH,
            phase2a_code_complexity=0.7,
            phase2a_relationship_load=0.8,
            phase2b_attention_load=0.9,  # High attention load
            phase2b_pattern_load=0.6,
            phase2c_relationship_cognitive_load=0.8,
            phase2d_template_load=0.7,
            session_duration_factor=0.8,  # Long session
            context_switch_penalty=0.6,   # Many switches
            complexity_accumulation=0.3,
            fatigue_factor=0.7,  # High fatigue factor
            measurement_confidence=0.9,
            component_count=6
        )

        # Test fatigue detection
        fatigue_detection = await engine.monitor_cognitive_fatigue(
            test_user_id, test_workspace, fatigued_load, AttentionState.LOW_FOCUS, []
        )

        if fatigue_detection:
            # Test fatigue response
            response_result = await engine.respond_to_fatigue(fatigue_detection)

            return {
                "fatigue_detected": True,
                "fatigue_severity": fatigue_detection.fatigue_severity.value,
                "fatigue_score": fatigue_detection.fatigue_score,
                "detection_confidence": fatigue_detection.confidence,
                "response_successful": response_result.implementation_successful,
                "responses_applied": response_result.responses_applied,
                "fatigue_reduction": response_result.fatigue_reduction_achieved,
                "test_status": "passed"
            }
        else:
            return {
                "fatigue_detected": False,
                "test_status": "no_fatigue_detected"
            }

    except Exception as e:
        logger.error(f"Fatigue detection test failed: {e}")
        return {
            "test_status": "failed",
            "error": str(e),
            "fatigue_detected": False
        }


if __name__ == "__main__":
    # Quick test when run directly
    async def main():
        print("🛟 Serena Fatigue Detection & Adaptive Response Engine")
        print("Proactive cognitive fatigue management with system-wide coordination")
        print("✅ Module loaded successfully")

    asyncio.run(main())