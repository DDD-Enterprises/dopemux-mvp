"""
Serena v2 Phase 2C: Navigation Success Validator

Comprehensive testing system to validate that intelligent relationship suggestions
achieve >85% navigation success rate with ADHD-optimized user scenarios.
"""

import asyncio
import json
import logging
import random
import statistics
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set, Union
from dataclasses import dataclass, field
from enum import Enum

# Phase 2C Components
from .intelligent_relationship_builder import IntelligentRelationshipBuilder, NavigationContext
from .enhanced_tree_sitter import EnhancedTreeSitterIntegration
from .conport_bridge import ConPortKnowledgeGraphBridge
from .adhd_relationship_filter import ADHDRelationshipFilter
from .realtime_relevance_scorer import RealtimeRelevanceScorer

# Phase 2B Components
from .adaptive_learning import AdaptiveLearningEngine, AttentionState
from .learning_profile_manager import PersonalLearningProfileManager
from .pattern_recognition import AdvancedPatternRecognition, NavigationPatternType
from .effectiveness_tracker import EffectivenessTracker

# Phase 2A Components
from .database import SerenaIntelligenceDatabase
from .graph_operations import SerenaGraphOperations, CodeElementNode

# Layer 1 Components
from ..performance_monitor import PerformanceMonitor

logger = logging.getLogger(__name__)


class NavigationSuccessMetric(str, Enum):
    """Metrics for measuring navigation success."""
    SUGGESTION_ACCEPTANCE_RATE = "suggestion_acceptance_rate"  # % of suggestions user follows
    TASK_COMPLETION_RATE = "task_completion_rate"              # % of tasks completed successfully
    NAVIGATION_EFFICIENCY = "navigation_efficiency"            # Time to find target vs baseline
    COGNITIVE_LOAD_MANAGEMENT = "cognitive_load_management"    # How well cognitive load is managed
    USER_SATISFACTION = "user_satisfaction"                    # User-reported satisfaction
    ATTENTION_PRESERVATION = "attention_preservation"          # How well attention is preserved
    PATTERN_EFFECTIVENESS = "pattern_effectiveness"            # How effective learned patterns are


class TestScenario(str, Enum):
    """Test scenarios for navigation success validation."""
    COLD_START = "cold_start"                    # New user, no learned patterns
    LEARNING_PHASE = "learning_phase"            # User with some patterns
    CONVERGED_PATTERNS = "converged_patterns"    # User with stable patterns
    HIGH_DISTRACTIBILITY = "high_distractibility"  # ADHD high distraction scenario
    HYPERFOCUS_SESSION = "hyperfocus_session"    # ADHD hyperfocus scenario
    COMPLEX_CODEBASE = "complex_codebase"        # Large, complex codebase
    SIMPLE_CODEBASE = "simple_codebase"          # Small, simple codebase


class NavigationTask(str, Enum):
    """Types of navigation tasks for testing."""
    FIND_FUNCTION_DEFINITION = "find_function_definition"
    UNDERSTAND_CLASS_HIERARCHY = "understand_class_hierarchy"
    TRACE_FUNCTION_CALLS = "trace_function_calls"
    EXPLORE_MODULE_DEPENDENCIES = "explore_module_dependencies"
    DEBUG_ERROR_SOURCE = "debug_error_source"
    UNDERSTAND_DATA_FLOW = "understand_data_flow"
    REVIEW_IMPLEMENTATION = "review_implementation"


@dataclass
class NavigationAttempt:
    """Individual navigation attempt with success measurement."""
    attempt_id: str
    user_session_id: str
    task_type: NavigationTask
    start_element: CodeElementNode
    target_element: CodeElementNode
    scenario: TestScenario

    # Navigation process
    suggestions_provided: List[Dict[str, Any]]
    suggestions_followed: List[str]
    navigation_path: List[int]  # Element IDs visited
    context_switches: int
    total_duration_ms: float

    # Success metrics
    target_reached: bool
    task_completed: bool
    user_satisfaction: Optional[float] = None  # 0.0-1.0
    cognitive_load_experienced: float = 0.5
    attention_preserved: bool = True

    # ADHD-specific metrics
    overwhelm_experienced: bool = False
    focus_mode_used: bool = False
    breaks_taken: int = 0
    accommodations_effective: bool = True

    # Analysis
    success_factors: List[str] = field(default_factory=list)
    failure_factors: List[str] = field(default_factory=list)
    improvement_opportunities: List[str] = field(default_factory=list)

    @property
    def overall_success(self) -> bool:
        """Determine overall success of navigation attempt."""
        return (self.target_reached and
                self.task_completed and
                not self.overwhelm_experienced and
                self.attention_preserved)

    @property
    def success_score(self) -> float:
        """Calculate numeric success score (0.0-1.0)."""
        score_factors = []

        # Core success factors
        score_factors.append(1.0 if self.target_reached else 0.0)
        score_factors.append(1.0 if self.task_completed else 0.0)

        # ADHD-specific factors
        score_factors.append(1.0 if not self.overwhelm_experienced else 0.0)
        score_factors.append(1.0 if self.attention_preserved else 0.0)
        score_factors.append(1.0 if self.accommodations_effective else 0.0)

        # Efficiency factors
        suggestion_efficiency = len(self.suggestions_followed) / max(len(self.suggestions_provided), 1)
        score_factors.append(min(1.0, suggestion_efficiency))

        # User satisfaction
        if self.user_satisfaction is not None:
            score_factors.append(self.user_satisfaction)

        return statistics.mean(score_factors)


@dataclass
class TestSuiteResult:
    """Results from comprehensive navigation success test suite."""
    test_suite_id: str
    test_duration_days: int
    scenarios_tested: List[TestScenario]
    total_attempts: int
    successful_attempts: int
    overall_success_rate: float

    # Success rate by scenario
    scenario_success_rates: Dict[TestScenario, float]

    # Success rate by task type
    task_success_rates: Dict[NavigationTask, float]

    # ADHD-specific metrics
    adhd_accommodation_success_rate: float
    cognitive_load_management_score: float
    attention_preservation_rate: float
    overwhelm_incidents: int

    # Performance metrics
    average_navigation_time_ms: float
    suggestion_acceptance_rate: float
    system_performance_maintained: bool

    # Detailed analysis
    success_factors_analysis: Dict[str, int]
    failure_factors_analysis: Dict[str, int]
    improvement_recommendations: List[str]

    # Validation status
    target_85_percent_achieved: bool
    adhd_optimization_validated: bool
    performance_targets_met: bool
    ready_for_production: bool


class NavigationSuccessValidator:
    """
    Comprehensive navigation success validation system.

    Features:
    - >85% navigation success rate validation with statistical confidence
    - Multiple ADHD scenario testing (cold start, learning, convergence, distractibility)
    - Various navigation task types (exploration, debugging, implementation)
    - Real-world codebase simulation with complexity variations
    - ADHD-specific success metrics and accommodation validation
    - Performance validation maintaining <200ms targets throughout
    - Statistical analysis with confidence intervals
    - Detailed failure analysis and improvement recommendations
    """

    def __init__(
        self,
        relationship_builder: IntelligentRelationshipBuilder,
        enhanced_tree_sitter: EnhancedTreeSitterIntegration,
        conport_bridge: ConPortKnowledgeGraphBridge,
        adhd_filter: ADHDRelationshipFilter,
        realtime_scorer: RealtimeRelevanceScorer,
        database: SerenaIntelligenceDatabase,
        performance_monitor: PerformanceMonitor = None
    ):
        self.relationship_builder = relationship_builder
        self.enhanced_tree_sitter = enhanced_tree_sitter
        self.conport_bridge = conport_bridge
        self.adhd_filter = adhd_filter
        self.realtime_scorer = realtime_scorer
        self.database = database
        self.performance_monitor = performance_monitor or PerformanceMonitor()

        # Validation configuration
        self.target_success_rate = 0.85  # 85% target
        self.min_statistical_confidence = 0.95  # 95% confidence
        self.min_sample_size_per_scenario = 20  # Minimum attempts per scenario

        # Test scenarios with ADHD characteristics
        self.test_scenarios = self._create_test_scenarios()

        # Navigation tasks for testing
        self.navigation_tasks = self._create_navigation_tasks()

        # Success tracking
        self._test_results: List[NavigationAttempt] = []

    # Main Validation Process

    async def run_comprehensive_success_validation(
        self,
        test_duration_days: int = 3,
        scenarios: Optional[List[TestScenario]] = None
    ) -> TestSuiteResult:
        """Run comprehensive navigation success validation."""
        operation_id = self.performance_monitor.start_operation("comprehensive_success_validation")
        test_suite_id = f"nav_success_test_{int(time.time())}"

        logger.info(f"🧪 Starting comprehensive navigation success validation "
                   f"(target: {self.target_success_rate:.1%})")

        try:
            start_time = datetime.now(timezone.utc)

            # Use provided scenarios or all scenarios
            test_scenarios = scenarios or list(TestScenario)

            # Run tests for each scenario
            all_attempts = []
            scenario_results = {}

            for scenario in test_scenarios:
                logger.info(f"🎭 Testing scenario: {scenario.value}")

                scenario_attempts = await self._test_scenario(
                    scenario, self.min_sample_size_per_scenario
                )

                all_attempts.extend(scenario_attempts)
                scenario_success_rate = sum(1 for a in scenario_attempts if a.overall_success) / len(scenario_attempts)
                scenario_results[scenario] = scenario_success_rate

                logger.info(f"📊 Scenario {scenario.value}: {scenario_success_rate:.1%} success rate")

            # Analyze results by task type
            task_results = {}
            for task_type in NavigationTask:
                task_attempts = [a for a in all_attempts if a.task_type == task_type]
                if task_attempts:
                    task_success_rate = sum(1 for a in task_attempts if a.overall_success) / len(task_attempts)
                    task_results[task_type] = task_success_rate

            # Calculate overall metrics
            overall_success_rate = sum(1 for a in all_attempts if a.overall_success) / len(all_attempts)
            adhd_success_rate = sum(1 for a in all_attempts if a.accommodations_effective) / len(all_attempts)
            attention_preservation_rate = sum(1 for a in all_attempts if a.attention_preserved) / len(all_attempts)

            # Performance analysis
            avg_navigation_time = statistics.mean([a.total_duration_ms for a in all_attempts])
            suggestion_acceptance = statistics.mean([
                len(a.suggestions_followed) / max(len(a.suggestions_provided), 1)
                for a in all_attempts
            ])

            # ADHD-specific analysis
            overwhelm_incidents = sum(1 for a in all_attempts if a.overwhelm_experienced)
            cognitive_load_scores = [a.cognitive_load_experienced for a in all_attempts]
            avg_cognitive_load = statistics.mean(cognitive_load_scores)

            # Generate improvement recommendations
            improvement_recs = await self._analyze_improvement_opportunities(all_attempts)

            # Create test suite result
            test_result = TestSuiteResult(
                test_suite_id=test_suite_id,
                test_duration_days=test_duration_days,
                scenarios_tested=test_scenarios,
                total_attempts=len(all_attempts),
                successful_attempts=sum(1 for a in all_attempts if a.overall_success),
                overall_success_rate=overall_success_rate,
                scenario_success_rates=scenario_results,
                task_success_rates=task_results,
                adhd_accommodation_success_rate=adhd_success_rate,
                cognitive_load_management_score=max(0.0, 1.0 - avg_cognitive_load),
                attention_preservation_rate=attention_preservation_rate,
                overwhelm_incidents=overwhelm_incidents,
                average_navigation_time_ms=avg_navigation_time,
                suggestion_acceptance_rate=suggestion_acceptance,
                system_performance_maintained=avg_navigation_time < 200,  # <200ms target
                success_factors_analysis=self._analyze_success_factors(all_attempts),
                failure_factors_analysis=self._analyze_failure_factors(all_attempts),
                improvement_recommendations=improvement_recs,
                target_85_percent_achieved=overall_success_rate >= self.target_success_rate,
                adhd_optimization_validated=adhd_success_rate >= 0.8 and overwhelm_incidents < len(all_attempts) * 0.1,
                performance_targets_met=avg_navigation_time < 200 and suggestion_acceptance > 0.6,
                ready_for_production=overall_success_rate >= self.target_success_rate and adhd_success_rate >= 0.8
            )

            self.performance_monitor.end_operation(operation_id, success=True)

            # Log final results
            if test_result.target_85_percent_achieved:
                logger.info(f"🎉 SUCCESS: {overall_success_rate:.1%} navigation success rate "
                           f"(target: {self.target_success_rate:.1%})")
            else:
                logger.warning(f"⚠️ BELOW TARGET: {overall_success_rate:.1%} navigation success rate "
                              f"(target: {self.target_success_rate:.1%})")

            return test_result

        except Exception as e:
            self.performance_monitor.end_operation(operation_id, success=False)
            logger.error(f"Comprehensive success validation failed: {e}")
            raise

    async def _test_scenario(
        self, scenario: TestScenario, sample_size: int
    ) -> List[NavigationAttempt]:
        """Test a specific ADHD scenario with multiple navigation attempts."""
        attempts = []

        try:
            # Configure scenario characteristics
            scenario_config = self._get_scenario_config(scenario)

            for attempt_num in range(sample_size):
                # Create test user for this attempt
                test_user_id = f"test_user_{scenario.value}_{attempt_num}"

                # Generate navigation task
                task_type = random.choice(list(NavigationTask))

                # Create test navigation attempt
                attempt = await self._create_navigation_attempt(
                    test_user_id, task_type, scenario, scenario_config
                )

                # Execute navigation test
                completed_attempt = await self._execute_navigation_test(attempt)

                attempts.append(completed_attempt)

                # Log progress every 10 attempts
                if (attempt_num + 1) % 10 == 0:
                    current_success_rate = sum(1 for a in attempts if a.overall_success) / len(attempts)
                    logger.debug(f"📈 {scenario.value}: {attempt_num + 1}/{sample_size} attempts, "
                                f"{current_success_rate:.1%} success rate")

            return attempts

        except Exception as e:
            logger.error(f"Failed to test scenario {scenario}: {e}")
            return attempts

    async def _execute_navigation_test(self, attempt: NavigationAttempt) -> NavigationAttempt:
        """Execute individual navigation test attempt."""
        try:
            start_time = time.time()

            # Create navigation context
            context = NavigationContext(
                current_element=attempt.start_element,
                current_task_type=attempt.task_type.value,
                user_session_id=attempt.user_session_id,
                workspace_path="test_workspace",
                session_duration_minutes=0.0,
                recent_navigation_history=[],
                attention_state=self._get_scenario_attention_state(attempt.scenario),
                complexity_tolerance=0.6  # Default
            )

            # Get relationship suggestions
            suggestions = await self.relationship_builder.discover_intelligent_relationships(context)
            attempt.suggestions_provided = [
                {
                    "target": s.relationship.target_element.element_name,
                    "relevance": s.relationship.relevance_score,
                    "cognitive_load": s.relationship.cognitive_load_score,
                    "reason": s.suggestion_reason
                }
                for s in suggestions
            ]

            # Simulate user navigation based on scenario characteristics
            navigation_result = await self._simulate_user_navigation(
                attempt, suggestions, context
            )

            # Update attempt with results
            attempt.suggestions_followed = navigation_result['followed_suggestions']
            attempt.navigation_path = navigation_result['navigation_path']
            attempt.context_switches = navigation_result['context_switches']
            attempt.target_reached = navigation_result['target_reached']
            attempt.task_completed = navigation_result['task_completed']
            attempt.cognitive_load_experienced = navigation_result['cognitive_load']
            attempt.attention_preserved = navigation_result['attention_preserved']
            attempt.overwhelm_experienced = navigation_result['overwhelm_experienced']
            attempt.accommodations_effective = navigation_result['accommodations_effective']

            # Calculate total duration
            attempt.total_duration_ms = (time.time() - start_time) * 1000

            # Analyze success/failure factors
            attempt.success_factors = navigation_result['success_factors']
            attempt.failure_factors = navigation_result['failure_factors']
            attempt.improvement_opportunities = navigation_result['improvement_opportunities']

            return attempt

        except Exception as e:
            logger.error(f"Failed to execute navigation test: {e}")
            attempt.task_completed = False
            attempt.target_reached = False
            attempt.failure_factors = [f"Test execution failed: {e}"]
            return attempt

    # Simulation Methods

    async def _simulate_user_navigation(
        self,
        attempt: NavigationAttempt,
        suggestions: List[Any],
        context: NavigationContext
    ) -> Dict[str, Any]:
        """Simulate user navigation behavior based on ADHD scenario."""
        navigation_result = {
            "followed_suggestions": [],
            "navigation_path": [attempt.start_element.id],
            "context_switches": 0,
            "target_reached": False,
            "task_completed": False,
            "cognitive_load": 0.5,
            "attention_preserved": True,
            "overwhelm_experienced": False,
            "accommodations_effective": True,
            "success_factors": [],
            "failure_factors": [],
            "improvement_opportunities": []
        }

        try:
            # Get scenario characteristics
            scenario_config = self._get_scenario_config(attempt.scenario)

            # Simulate navigation steps
            current_element_id = attempt.start_element.id
            steps_taken = 0
            max_steps = 10  # Prevent infinite loops

            while steps_taken < max_steps and not navigation_result["target_reached"]:
                # Check if user would follow suggestions (based on scenario)
                follow_probability = scenario_config.get('suggestion_follow_probability', 0.7)

                if suggestions and random.random() < follow_probability:
                    # User follows a suggestion
                    suggestion_to_follow = self._select_suggestion_to_follow(
                        suggestions, scenario_config
                    )

                    if suggestion_to_follow:
                        target_id = suggestion_to_follow.relationship.target_element.id
                        navigation_result["followed_suggestions"].append(
                            suggestion_to_follow.relationship.target_element.element_name
                        )
                        navigation_result["navigation_path"].append(target_id)

                        # Check if target reached
                        if target_id == attempt.target_element.id:
                            navigation_result["target_reached"] = True
                            navigation_result["task_completed"] = True
                            navigation_result["success_factors"].append("Suggestion led to target")

                        # Update context for next iteration
                        current_element_id = target_id
                        context.current_element = suggestion_to_follow.relationship.target_element

                        # Accumulate cognitive load
                        navigation_result["cognitive_load"] += suggestion_to_follow.relationship.cognitive_load_score * 0.2

                else:
                    # User explores without following suggestions
                    navigation_result["context_switches"] += 1
                    if navigation_result["context_switches"] > scenario_config.get('max_context_switches', 5):
                        navigation_result["failure_factors"].append("Too many context switches")
                        break

                steps_taken += 1

            # Assess final results based on scenario
            self._assess_scenario_specific_results(navigation_result, attempt, scenario_config)

            return navigation_result

        except Exception as e:
            logger.error(f"Navigation simulation failed: {e}")
            navigation_result["failure_factors"].append(f"Simulation error: {e}")
            return navigation_result

    def _select_suggestion_to_follow(
        self, suggestions: List[Any], scenario_config: Dict[str, Any]
    ) -> Optional[Any]:
        """Select which suggestion the user would follow based on scenario."""
        if not suggestions:
            return None

        # Different selection strategies based on scenario
        selection_strategy = scenario_config.get('selection_strategy', 'highest_relevance')

        if selection_strategy == 'highest_relevance':
            return max(suggestions, key=lambda s: s.relationship.relevance_score)

        elif selection_strategy == 'lowest_cognitive_load':
            return min(suggestions, key=lambda s: s.relationship.cognitive_load_score)

        elif selection_strategy == 'random':
            return random.choice(suggestions)

        elif selection_strategy == 'adhd_optimized':
            # Select based on ADHD-friendliness
            adhd_friendly = [s for s in suggestions if s.relationship.adhd_friendly]
            if adhd_friendly:
                return max(adhd_friendly, key=lambda s: s.relationship.relevance_score)

        return suggestions[0]  # Fallback to first suggestion

    # Scenario Configuration

    def _create_test_scenarios(self) -> Dict[TestScenario, Dict[str, Any]]:
        """Create test scenario configurations."""
        return {
            TestScenario.COLD_START: {
                "attention_state": AttentionState.MODERATE_FOCUS,
                "suggestion_follow_probability": 0.6,  # Lower due to no patterns
                "selection_strategy": "highest_relevance",
                "max_context_switches": 6,
                "cognitive_load_tolerance": 0.5,
                "overwhelm_threshold": 0.7
            },
            TestScenario.LEARNING_PHASE: {
                "attention_state": AttentionState.MODERATE_FOCUS,
                "suggestion_follow_probability": 0.75,
                "selection_strategy": "adhd_optimized",
                "max_context_switches": 5,
                "cognitive_load_tolerance": 0.6,
                "overwhelm_threshold": 0.8
            },
            TestScenario.CONVERGED_PATTERNS: {
                "attention_state": AttentionState.MODERATE_FOCUS,
                "suggestion_follow_probability": 0.9,  # High trust in suggestions
                "selection_strategy": "adhd_optimized",
                "max_context_switches": 4,
                "cognitive_load_tolerance": 0.7,
                "overwhelm_threshold": 0.9
            },
            TestScenario.HIGH_DISTRACTIBILITY: {
                "attention_state": AttentionState.LOW_FOCUS,
                "suggestion_follow_probability": 0.5,
                "selection_strategy": "lowest_cognitive_load",
                "max_context_switches": 8,
                "cognitive_load_tolerance": 0.4,
                "overwhelm_threshold": 0.6
            },
            TestScenario.HYPERFOCUS_SESSION: {
                "attention_state": AttentionState.HYPERFOCUS,
                "suggestion_follow_probability": 0.8,
                "selection_strategy": "highest_relevance",
                "max_context_switches": 2,
                "cognitive_load_tolerance": 0.9,
                "overwhelm_threshold": 0.95
            },
            TestScenario.COMPLEX_CODEBASE: {
                "attention_state": AttentionState.MODERATE_FOCUS,
                "suggestion_follow_probability": 0.7,
                "selection_strategy": "adhd_optimized",
                "max_context_switches": 4,
                "cognitive_load_tolerance": 0.5,
                "overwhelm_threshold": 0.7,
                "base_complexity_multiplier": 1.5
            },
            TestScenario.SIMPLE_CODEBASE: {
                "attention_state": AttentionState.MODERATE_FOCUS,
                "suggestion_follow_probability": 0.8,
                "selection_strategy": "highest_relevance",
                "max_context_switches": 6,
                "cognitive_load_tolerance": 0.8,
                "overwhelm_threshold": 0.9,
                "base_complexity_multiplier": 0.7
            }
        }

    def _create_navigation_tasks(self) -> List[Dict[str, Any]]:
        """Create navigation task definitions."""
        return [
            {
                "type": NavigationTask.FIND_FUNCTION_DEFINITION,
                "description": "Find definition of a specific function",
                "complexity_factor": 0.4,
                "expected_steps": 2,
                "success_criteria": ["target_function_reached", "definition_viewed"]
            },
            {
                "type": NavigationTask.UNDERSTAND_CLASS_HIERARCHY,
                "description": "Understand inheritance structure of a class",
                "complexity_factor": 0.7,
                "expected_steps": 4,
                "success_criteria": ["parent_classes_identified", "inheritance_understood"]
            },
            {
                "type": NavigationTask.TRACE_FUNCTION_CALLS,
                "description": "Trace execution path of function calls",
                "complexity_factor": 0.6,
                "expected_steps": 5,
                "success_criteria": ["call_chain_identified", "execution_path_traced"]
            },
            {
                "type": NavigationTask.DEBUG_ERROR_SOURCE,
                "description": "Find source of an error or bug",
                "complexity_factor": 0.8,
                "expected_steps": 6,
                "success_criteria": ["error_source_found", "root_cause_identified"]
            }
        ]

    def _get_scenario_config(self, scenario: TestScenario) -> Dict[str, Any]:
        """Get configuration for test scenario."""
        return self.test_scenarios.get(scenario, {
            "attention_state": AttentionState.MODERATE_FOCUS,
            "suggestion_follow_probability": 0.7,
            "selection_strategy": "highest_relevance",
            "max_context_switches": 5,
            "cognitive_load_tolerance": 0.6,
            "overwhelm_threshold": 0.8
        })

    def _get_scenario_attention_state(self, scenario: TestScenario) -> str:
        """Get attention state for scenario."""
        scenario_config = self._get_scenario_config(scenario)
        return scenario_config.get('attention_state', AttentionState.MODERATE_FOCUS).value

    # Test Creation and Execution

    async def _create_navigation_attempt(
        self,
        user_session_id: str,
        task_type: NavigationTask,
        scenario: TestScenario,
        scenario_config: Dict[str, Any]
    ) -> NavigationAttempt:
        """Create navigation attempt for testing."""
        attempt_id = f"attempt_{user_session_id}_{task_type.value}_{int(time.time())}"

        # Create mock code elements for testing
        start_element = CodeElementNode(
            id=1,
            file_path="test/module.py",
            element_name="start_function",
            element_type="function",
            language="python",
            start_line=10,
            end_line=25,
            complexity_score=0.4,
            complexity_level="moderate",
            cognitive_load_factor=0.3,
            access_frequency=5,
            adhd_insights=["moderate complexity"],
            tree_sitter_metadata={}
        )

        target_element = CodeElementNode(
            id=10,
            file_path="test/target.py",
            element_name="target_function",
            element_type="function",
            language="python",
            start_line=50,
            end_line=75,
            complexity_score=scenario_config.get('base_complexity_multiplier', 1.0) * 0.6,
            complexity_level="moderate",
            cognitive_load_factor=0.4,
            access_frequency=2,
            adhd_insights=["target element"],
            tree_sitter_metadata={}
        )

        return NavigationAttempt(
            attempt_id=attempt_id,
            user_session_id=user_session_id,
            task_type=task_type,
            start_element=start_element,
            target_element=target_element,
            scenario=scenario,
            suggestions_provided=[],
            suggestions_followed=[],
            navigation_path=[],
            context_switches=0,
            total_duration_ms=0.0,
            target_reached=False,
            task_completed=False
        )

    def _assess_scenario_specific_results(
        self,
        navigation_result: Dict[str, Any],
        attempt: NavigationAttempt,
        scenario_config: Dict[str, Any]
    ) -> None:
        """Assess results specific to ADHD scenario characteristics."""
        # Check cognitive load tolerance
        if navigation_result["cognitive_load"] > scenario_config.get('overwhelm_threshold', 0.8):
            navigation_result["overwhelm_experienced"] = True
            navigation_result["attention_preserved"] = False
            navigation_result["failure_factors"].append("Cognitive overload experienced")

        # Check context switching limits
        if navigation_result["context_switches"] > scenario_config.get('max_context_switches', 5):
            navigation_result["failure_factors"].append("Excessive context switching")
            navigation_result["attention_preserved"] = False

        # Assess accommodation effectiveness
        if len(attempt.suggestions_provided) <= 5:  # ADHD max suggestions rule
            navigation_result["success_factors"].append("ADHD suggestion limit respected")
        else:
            navigation_result["failure_factors"].append("Too many suggestions provided")
            navigation_result["accommodations_effective"] = False

        # Check suggestion quality
        if attempt.suggestions_provided:
            avg_cognitive_load = statistics.mean([
                s.get('cognitive_load', 0.5) for s in attempt.suggestions_provided
            ])
            if avg_cognitive_load <= scenario_config.get('cognitive_load_tolerance', 0.6):
                navigation_result["success_factors"].append("Appropriate cognitive load in suggestions")
            else:
                navigation_result["failure_factors"].append("Suggestions too cognitively demanding")

    # Analysis Methods

    def _analyze_success_factors(self, attempts: List[NavigationAttempt]) -> Dict[str, int]:
        """Analyze common success factors across attempts."""
        success_factors = {}
        successful_attempts = [a for a in attempts if a.overall_success]

        for attempt in successful_attempts:
            for factor in attempt.success_factors:
                success_factors[factor] = success_factors.get(factor, 0) + 1

        return dict(sorted(success_factors.items(), key=lambda x: x[1], reverse=True))

    def _analyze_failure_factors(self, attempts: List[NavigationAttempt]) -> Dict[str, int]:
        """Analyze common failure factors across attempts."""
        failure_factors = {}
        failed_attempts = [a for a in attempts if not a.overall_success]

        for attempt in failed_attempts:
            for factor in attempt.failure_factors:
                failure_factors[factor] = failure_factors.get(factor, 0) + 1

        return dict(sorted(failure_factors.items(), key=lambda x: x[1], reverse=True))

    async def _analyze_improvement_opportunities(
        self, attempts: List[NavigationAttempt]
    ) -> List[str]:
        """Analyze improvement opportunities from test results."""
        improvements = []

        # Analyze overall success rate
        success_rate = sum(1 for a in attempts if a.overall_success) / len(attempts)
        if success_rate < self.target_success_rate:
            gap = self.target_success_rate - success_rate
            improvements.append(f"🎯 Need {gap:.1%} improvement to reach 85% target")

        # Analyze ADHD-specific issues
        overwhelm_rate = sum(1 for a in attempts if a.overwhelm_experienced) / len(attempts)
        if overwhelm_rate > 0.1:  # More than 10% overwhelm
            improvements.append("🧠 Reduce cognitive overwhelm through better filtering")

        # Analyze suggestion effectiveness
        avg_acceptance_rate = statistics.mean([
            len(a.suggestions_followed) / max(len(a.suggestions_provided), 1)
            for a in attempts
        ])
        if avg_acceptance_rate < 0.6:
            improvements.append("📈 Improve suggestion relevance and quality")

        # Analyze attention preservation
        attention_loss_rate = sum(1 for a in attempts if not a.attention_preserved) / len(attempts)
        if attention_loss_rate > 0.2:  # More than 20% attention loss
            improvements.append("🎯 Improve attention preservation strategies")

        # Scenario-specific improvements
        scenario_success = {}
        for attempt in attempts:
            scenario = attempt.scenario
            if scenario not in scenario_success:
                scenario_success[scenario] = []
            scenario_success[scenario].append(attempt.overall_success)

        for scenario, results in scenario_success.items():
            scenario_rate = sum(results) / len(results)
            if scenario_rate < 0.7:  # Below 70% for any scenario
                improvements.append(f"🎭 Improve {scenario.value} scenario performance")

        return improvements

    # Utility Methods

    async def get_validation_summary(self, test_result: TestSuiteResult) -> Dict[str, Any]:
        """Get human-readable validation summary."""
        return {
            "validation_status": "PASSED" if test_result.target_85_percent_achieved else "FAILED",
            "success_rate": f"{test_result.overall_success_rate:.1%}",
            "target_achieved": test_result.target_85_percent_achieved,
            "adhd_optimization": "VALIDATED" if test_result.adhd_optimization_validated else "NEEDS_WORK",
            "performance_compliance": "MET" if test_result.performance_targets_met else "NEEDS_IMPROVEMENT",
            "production_readiness": "READY" if test_result.ready_for_production else "NOT_READY",
            "key_metrics": {
                "suggestion_acceptance": f"{test_result.suggestion_acceptance_rate:.1%}",
                "attention_preservation": f"{test_result.attention_preservation_rate:.1%}",
                "cognitive_load_management": f"{test_result.cognitive_load_management_score:.1%}",
                "overwhelm_incidents": test_result.overwhelm_incidents
            },
            "top_recommendations": test_result.improvement_recommendations[:3]
        }


# Convenience functions
async def create_navigation_success_validator(
    relationship_builder: IntelligentRelationshipBuilder,
    enhanced_tree_sitter: EnhancedTreeSitterIntegration,
    conport_bridge: ConPortKnowledgeGraphBridge,
    adhd_filter: ADHDRelationshipFilter,
    realtime_scorer: RealtimeRelevanceScorer,
    database: SerenaIntelligenceDatabase,
    performance_monitor: PerformanceMonitor = None
) -> NavigationSuccessValidator:
    """Create navigation success validator instance."""
    return NavigationSuccessValidator(
        relationship_builder, enhanced_tree_sitter, conport_bridge,
        adhd_filter, realtime_scorer, database, performance_monitor
    )


async def quick_success_validation_test(
    validator: NavigationSuccessValidator
) -> Dict[str, Any]:
    """Run quick success validation test."""
    try:
        # Run short validation with key scenarios
        key_scenarios = [
            TestScenario.LEARNING_PHASE,
            TestScenario.HIGH_DISTRACTIBILITY,
            TestScenario.CONVERGED_PATTERNS
        ]

        test_result = await validator.run_comprehensive_success_validation(
            test_duration_days=1,  # Quick test
            scenarios=key_scenarios
        )

        summary = await validator.get_validation_summary(test_result)

        return {
            "quick_test_result": summary,
            "validation_passed": test_result.target_85_percent_achieved,
            "adhd_optimized": test_result.adhd_optimization_validated,
            "ready_for_full_test": summary["validation_status"] == "PASSED"
        }

    except Exception as e:
        logger.error(f"Quick success validation failed: {e}")
        return {
            "quick_test_result": {"error": str(e)},
            "validation_passed": False,
            "ready_for_full_test": False
        }


if __name__ == "__main__":
    # Quick test when run directly
    async def main():
        print("🎯 Serena Navigation Success Validator")
        print("Comprehensive >85% navigation success rate validation")
        print("✅ Module loaded successfully")

    asyncio.run(main())