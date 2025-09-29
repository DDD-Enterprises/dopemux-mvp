"""
Serena v2 Phase 2: Intelligence Module

PostgreSQL-powered code relationship intelligence with ADHD-optimized navigation,
adaptive learning, and seamless Layer 1 integration.

Features:
- High-performance async PostgreSQL database layer
- ADHD-optimized code relationship graph operations
- Intelligent schema management and migration
- Comprehensive integration testing
- <200ms performance guarantees
- Progressive complexity disclosure
- Cognitive load management

Usage:
    from serena.v2.intelligence import (
        SerenaIntelligenceDatabase,
        SerenaGraphOperations,
        SerenaSchemaManager,
        setup_phase2_intelligence
    )

    # Quick setup
    db, graph_ops = await setup_phase2_intelligence()

    # Find related elements with ADHD optimization
    related = await graph_ops.get_related_elements(
        element_id=123,
        mode=NavigationMode.FOCUS
    )
"""

from typing import Any, Dict, List, Optional, Tuple

from .database import (
    SerenaIntelligenceDatabase,
    DatabaseConfig,
    DatabaseMetrics,
    create_intelligence_database,
    test_database_performance
)

from .schema_manager import (
    SerenaSchemaManager,
    MigrationStatus,
    MigrationStep,
    MigrationResult,
    setup_phase2_schema,
    migrate_from_layer1
)

from .graph_operations import (
    SerenaGraphOperations,
    RelationshipType,
    NavigationMode,
    CodeElementNode,
    RelationshipEdge,
    NavigationPath,
    create_graph_operations,
    quick_performance_test
)

from .integration_test import (
    SerenaLayer1IntegrationTest,
    IntegrationTestResult,
    run_integration_test_suite
)

# Phase 2B: Adaptive Learning Components
from .adaptive_learning import (
    AdaptiveLearningEngine,
    NavigationSequence,
    NavigationAction,
    PersonalLearningProfile,
    LearningPhase,
    AttentionState,
    create_adaptive_learning_engine,
    simulate_learning_convergence
)

from .learning_profile_manager import (
    PersonalLearningProfileManager,
    AccommodationPreference,
    NavigationPreferencePattern,
    AttentionPattern,
    ProfileInsight,
    create_profile_manager,
    simulate_profile_learning
)

from .pattern_recognition import (
    AdvancedPatternRecognition,
    NavigationPatternType,
    PatternComplexity,
    RecognizedPattern,
    PatternPrediction,
    create_pattern_recognition_engine
)

from .effectiveness_tracker import (
    EffectivenessTracker,
    EffectivenessDimension,
    EffectivenessProfile,
    ABTest,
    ImprovementRecommendation,
    create_effectiveness_tracker
)

from .context_switching_optimizer import (
    ContextSwitchingOptimizer,
    ContextSwitchEvent,
    ContextSwitchType,
    SwitchSeverity,
    InterruptionType,
    SwitchingPattern,
    TaskContinuationContext,
    create_context_switching_optimizer
)

from .convergence_test import (
    LearningConvergenceValidator,
    ConvergenceTestSuite,
    ConvergenceResult,
    ConvergenceMetric,
    LearningSimulationScenario,
    run_quick_convergence_test
)

# Phase 2C: Intelligent Relationship Builder Components
from .intelligent_relationship_builder import (
    IntelligentRelationshipBuilder,
    IntelligentRelationship,
    RelationshipSuggestion,
    NavigationContext,
    RelationshipRelevance,
    RelationshipContext,
    create_intelligent_relationship_builder,
    test_relationship_suggestions
)

from .enhanced_tree_sitter import (
    EnhancedTreeSitterIntegration,
    PersonalizedStructuralElement,
    EnhancedRelationshipDiscovery,
    IntelligentStructuralRelationship,
    create_enhanced_tree_sitter_integration
)

from .conport_bridge import (
    ConPortKnowledgeGraphBridge,
    ConPortCodeLink,
    DecisionCodeContext,
    CodeDecisionInsight,
    ConPortItemType,
    create_conport_bridge,
    test_conport_integration
)

from .adhd_relationship_filter import (
    ADHDRelationshipFilter,
    FilteringStrategy,
    FilteringResult,
    FilteringDecision,
    CognitiveLoadCategory,
    create_adhd_relationship_filter,
    test_adhd_filtering
)

from .realtime_relevance_scorer import (
    RealtimeRelevanceScorer,
    DynamicRelationshipScore,
    RelevanceScore,
    ScoringDimension,
    ScoringTrigger,
    create_realtime_relevance_scorer,
    test_realtime_scoring
)

from .navigation_success_validator import (
    NavigationSuccessValidator,
    TestSuiteResult,
    NavigationAttempt,
    NavigationSuccessMetric,
    TestScenario,
    NavigationTask,
    create_navigation_success_validator,
    quick_success_validation_test
)

# Phase 2D: Pattern Store & Reuse System Components
from .strategy_template_manager import (
    StrategyTemplateManager,
    NavigationStrategyTemplate,
    StrategyStep,
    TemplateComplexity,
    AccommodationType,
    TemplateLibrary,
    create_strategy_template_manager,
    validate_template_library
)

from .personal_pattern_adapter import (
    PersonalPatternAdapter,
    PersonalizationDelta,
    PersonalizedTemplate,
    PersonalizationType,
    PersonalizationOrigin,
    DeltaCluster,
    create_personal_pattern_adapter
)

from .cross_session_persistence_bridge import (
    CrossSessionPersistenceBridge,
    TemplateEvolutionProposal,
    SyncStatus,
    SyncHealthStatus,
    create_cross_session_persistence_bridge,
    test_persistence_bridge
)

from .effectiveness_evolution_system import (
    EffectivenessEvolutionSystem,
    EvolutionOpportunity,
    EvolutionExperiment,
    EvolutionTrigger,
    EvolutionStrategy,
    create_effectiveness_evolution_system,
    run_evolution_monitoring_cycle
)

from .pattern_reuse_recommendation_engine import (
    PatternReuseRecommendationEngine,
    PatternRecommendation,
    RecommendationConfidence,
    RecommendationReason,
    TimeReductionCategory,
    RecommendationResult,
    create_pattern_reuse_recommendation_engine,
    test_recommendation_engine
)

from .performance_validation_system import (
    PerformanceValidationSystem,
    NavigationGoal,
    PerformanceValidationResult,
    NavigationGoalType,
    ValidationMethod,
    ValidationExperiment,
    create_performance_validation_system,
    validate_30_percent_target
)

# Phase 2E: Cognitive Load Management Components
from .cognitive_load_orchestrator import (
    CognitiveLoadOrchestrator,
    CognitiveLoadReading,
    CognitiveLoadState,
    OrchestrationState,
    AdaptiveResponse,
    create_cognitive_load_orchestrator,
    test_cognitive_orchestration
)

from .progressive_disclosure_director import (
    ProgressiveDisclosureDirector,
    DisclosureLevel,
    DisclosureCoordination,
    ComponentDisclosureState,
    DisclosureStrategy,
    create_progressive_disclosure_director,
    test_progressive_disclosure
)

from .fatigue_detection_engine import (
    FatigueDetectionEngine,
    FatigueDetection,
    FatigueSeverity,
    AdaptiveResponsePlan,
    FatigueResponseResult,
    FatigueIndicator,
    create_fatigue_detection_engine,
    test_fatigue_detection
)

from .personalized_threshold_coordinator import (
    PersonalizedThresholdCoordinator,
    ThresholdCoordination,
    ThresholdType,
    ThresholdValue,
    ThresholdAdaptationPlan,
    create_personalized_threshold_coordinator,
    test_threshold_coordination
)

from .accommodation_harmonizer import (
    AccommodationHarmonizer,
    AccommodationProfile,
    AccommodationState,
    SystemAccommodationType,
    AccommodationEffectiveness,
    create_accommodation_harmonizer,
    test_accommodation_harmonization
)

from .complete_system_integration_test import (
    CompleteSystemIntegrationTest,
    SystemIntegrationResult,
    ComponentHealth,
    IntegrationTestScenario,
    run_complete_system_integration_test,
    validate_production_readiness
)

# Core exports
__all__ = [
    # Phase 2A: Database Layer
    "SerenaIntelligenceDatabase",
    "DatabaseConfig",
    "DatabaseMetrics",
    "create_intelligence_database",
    "test_database_performance",

    # Phase 2A: Schema Management
    "SerenaSchemaManager",
    "MigrationStatus",
    "MigrationStep",
    "MigrationResult",
    "setup_phase2_schema",
    "migrate_from_layer1",

    # Phase 2A: Graph Operations
    "SerenaGraphOperations",
    "RelationshipType",
    "NavigationMode",
    "CodeElementNode",
    "RelationshipEdge",
    "NavigationPath",
    "create_graph_operations",
    "quick_performance_test",

    # Phase 2A: Integration Testing
    "SerenaLayer1IntegrationTest",
    "IntegrationTestResult",
    "run_integration_test_suite",

    # Phase 2B: Adaptive Learning Engine
    "AdaptiveLearningEngine",
    "NavigationSequence",
    "NavigationAction",
    "PersonalLearningProfile",
    "LearningPhase",
    "AttentionState",
    "create_adaptive_learning_engine",
    "simulate_learning_convergence",

    # Phase 2B: Profile Management
    "PersonalLearningProfileManager",
    "AccommodationPreference",
    "NavigationPreferencePattern",
    "AttentionPattern",
    "ProfileInsight",
    "create_profile_manager",
    "simulate_profile_learning",

    # Phase 2B: Pattern Recognition
    "AdvancedPatternRecognition",
    "NavigationPatternType",
    "PatternComplexity",
    "RecognizedPattern",
    "PatternPrediction",
    "create_pattern_recognition_engine",

    # Phase 2B: Effectiveness Tracking
    "EffectivenessTracker",
    "EffectivenessDimension",
    "EffectivenessProfile",
    "ABTest",
    "ImprovementRecommendation",
    "create_effectiveness_tracker",

    # Phase 2B: Context Switching Optimization
    "ContextSwitchingOptimizer",
    "ContextSwitchEvent",
    "ContextSwitchType",
    "SwitchSeverity",
    "InterruptionType",
    "SwitchingPattern",
    "TaskContinuationContext",
    "create_context_switching_optimizer",

    # Phase 2B: Convergence Testing
    "LearningConvergenceValidator",
    "ConvergenceTestSuite",
    "ConvergenceResult",
    "ConvergenceMetric",
    "LearningSimulationScenario",
    "run_quick_convergence_test",

    # Phase 2C: Intelligent Relationship Builder
    "IntelligentRelationshipBuilder",
    "IntelligentRelationship",
    "RelationshipSuggestion",
    "NavigationContext",
    "RelationshipRelevance",
    "RelationshipContext",
    "create_intelligent_relationship_builder",
    "test_relationship_suggestions",

    # Phase 2C: Enhanced Tree-sitter Integration
    "EnhancedTreeSitterIntegration",
    "PersonalizedStructuralElement",
    "EnhancedRelationshipDiscovery",
    "IntelligentStructuralRelationship",
    "create_enhanced_tree_sitter_integration",

    # Phase 2C: ConPort Knowledge Graph Bridge
    "ConPortKnowledgeGraphBridge",
    "ConPortCodeLink",
    "DecisionCodeContext",
    "CodeDecisionInsight",
    "ConPortItemType",
    "create_conport_bridge",
    "test_conport_integration",

    # Phase 2C: ADHD Relationship Filtering
    "ADHDRelationshipFilter",
    "FilteringStrategy",
    "FilteringResult",
    "FilteringDecision",
    "CognitiveLoadCategory",
    "create_adhd_relationship_filter",
    "test_adhd_filtering",

    # Phase 2C: Real-time Relevance Scoring
    "RealtimeRelevanceScorer",
    "DynamicRelationshipScore",
    "RelevanceScore",
    "ScoringDimension",
    "ScoringTrigger",
    "create_realtime_relevance_scorer",
    "test_realtime_scoring",

    # Phase 2C: Navigation Success Validation
    "NavigationSuccessValidator",
    "TestSuiteResult",
    "NavigationAttempt",
    "NavigationSuccessMetric",
    "TestScenario",
    "NavigationTask",
    "create_navigation_success_validator",
    "quick_success_validation_test",

    # Phase 2D: Strategy Template Management
    "StrategyTemplateManager",
    "NavigationStrategyTemplate",
    "StrategyStep",
    "TemplateComplexity",
    "AccommodationType",
    "TemplateLibrary",
    "create_strategy_template_manager",
    "validate_template_library",

    # Phase 2D: Personal Pattern Adaptation
    "PersonalPatternAdapter",
    "PersonalizationDelta",
    "PersonalizedTemplate",
    "PersonalizationType",
    "PersonalizationOrigin",
    "DeltaCluster",
    "create_personal_pattern_adapter",

    # Phase 2D: Cross-Session Persistence
    "CrossSessionPersistenceBridge",
    "TemplateEvolutionProposal",
    "SyncStatus",
    "SyncHealthStatus",
    "create_cross_session_persistence_bridge",
    "test_persistence_bridge",

    # Phase 2D: Effectiveness Evolution
    "EffectivenessEvolutionSystem",
    "EvolutionOpportunity",
    "EvolutionExperiment",
    "EvolutionTrigger",
    "EvolutionStrategy",
    "create_effectiveness_evolution_system",
    "run_evolution_monitoring_cycle",

    # Phase 2D: Pattern Reuse Recommendation
    "PatternReuseRecommendationEngine",
    "PatternRecommendation",
    "RecommendationConfidence",
    "RecommendationReason",
    "TimeReductionCategory",
    "RecommendationResult",
    "create_pattern_reuse_recommendation_engine",
    "test_recommendation_engine",

    # Phase 2D: Performance Validation
    "PerformanceValidationSystem",
    "NavigationGoal",
    "PerformanceValidationResult",
    "NavigationGoalType",
    "ValidationMethod",
    "ValidationExperiment",
    "create_performance_validation_system",
    "validate_30_percent_target",

    # Phase 2E: Cognitive Load Orchestration
    "CognitiveLoadOrchestrator",
    "CognitiveLoadReading",
    "CognitiveLoadState",
    "OrchestrationState",
    "AdaptiveResponse",
    "create_cognitive_load_orchestrator",
    "test_cognitive_orchestration",

    # Phase 2E: Progressive Disclosure Management
    "ProgressiveDisclosureDirector",
    "DisclosureLevel",
    "DisclosureCoordination",
    "ComponentDisclosureState",
    "DisclosureStrategy",
    "create_progressive_disclosure_director",
    "test_progressive_disclosure",

    # Phase 2E: Fatigue Detection & Response
    "FatigueDetectionEngine",
    "FatigueDetection",
    "FatigueSeverity",
    "AdaptiveResponsePlan",
    "FatigueResponseResult",
    "FatigueIndicator",
    "create_fatigue_detection_engine",
    "test_fatigue_detection",

    # Phase 2E: Threshold Coordination
    "PersonalizedThresholdCoordinator",
    "ThresholdCoordination",
    "ThresholdType",
    "ThresholdValue",
    "ThresholdAdaptationPlan",
    "create_personalized_threshold_coordinator",
    "test_threshold_coordination",

    # Phase 2E: Accommodation Harmonization
    "AccommodationHarmonizer",
    "AccommodationProfile",
    "AccommodationState",
    "SystemAccommodationType",
    "AccommodationEffectiveness",
    "create_accommodation_harmonizer",
    "test_accommodation_harmonization",

    # Phase 2E: Complete System Integration
    "CompleteSystemIntegrationTest",
    "SystemIntegrationResult",
    "ComponentHealth",
    "IntegrationTestScenario",
    "run_complete_system_integration_test",
    "validate_production_readiness",

    # Convenience Functions
    "setup_phase2_intelligence",
    "validate_phase2_deployment",
    "setup_complete_adaptive_learning_system",
    "setup_complete_intelligent_relationship_system",
    "setup_complete_pattern_store_system",
    "setup_complete_cognitive_load_management_system",
    "get_phase2_status"
]

__version__ = "2.0.0-phase2e"


# Convenience functions for common use cases

async def setup_complete_adaptive_learning_system(
    database_config: DatabaseConfig = None,
    performance_monitor = None
) -> dict[str, Any]:
    """
    Set up complete Phase 2B adaptive learning system with all components.

    Returns:
        Dictionary with all initialized Phase 2B components
    """
    from ..performance_monitor import PerformanceMonitor

    if performance_monitor is None:
        performance_monitor = PerformanceMonitor()

    # Create Phase 2A foundation
    database, graph_operations = await setup_phase2_intelligence(database_config, performance_monitor)

    # Create Phase 2B adaptive learning components
    profile_manager = await create_profile_manager(database, performance_monitor)
    pattern_recognition = await create_pattern_recognition_engine(
        database, profile_manager, performance_monitor
    )
    effectiveness_tracker = await create_effectiveness_tracker(
        database, profile_manager, pattern_recognition, performance_monitor
    )
    context_optimizer = await create_context_switching_optimizer(
        database, profile_manager, effectiveness_tracker, performance_monitor
    )
    learning_engine = await create_adaptive_learning_engine(
        database, graph_operations, performance_monitor
    )

    # Create convergence validator
    convergence_validator = LearningConvergenceValidator(
        database, learning_engine, profile_manager, pattern_recognition,
        effectiveness_tracker, context_optimizer, performance_monitor
    )

    return {
        # Phase 2A Components
        "database": database,
        "graph_operations": graph_operations,

        # Phase 2B Components
        "learning_engine": learning_engine,
        "profile_manager": profile_manager,
        "pattern_recognition": pattern_recognition,
        "effectiveness_tracker": effectiveness_tracker,
        "context_optimizer": context_optimizer,
        "convergence_validator": convergence_validator,

        # Monitoring
        "performance_monitor": performance_monitor,

        # System info
        "version": __version__,
        "components_loaded": 7
    }


async def setup_phase2_intelligence(
    database_config: DatabaseConfig = None,
    performance_monitor = None
) -> tuple[SerenaIntelligenceDatabase, SerenaGraphOperations]:
    """
    Quick setup for Phase 2 intelligence with database and graph operations.

    Returns:
        Tuple of (database, graph_operations) ready for use
    """
    from ..performance_monitor import PerformanceMonitor

    if performance_monitor is None:
        performance_monitor = PerformanceMonitor()

    # Create and initialize database
    database = SerenaIntelligenceDatabase(database_config, performance_monitor)
    await database.initialize()

    # Create graph operations
    graph_operations = SerenaGraphOperations(database, performance_monitor)

    return database, graph_operations


async def validate_phase2_deployment(
    database_config: DatabaseConfig = None,
    run_integration_tests: bool = True
) -> dict:
    """
    Validate Phase 2 deployment readiness with comprehensive testing.

    Args:
        database_config: Optional database configuration
        run_integration_tests: Whether to run full integration test suite

    Returns:
        Validation report with deployment readiness assessment
    """
    from ..performance_monitor import PerformanceMonitor

    validation_report = {
        "deployment_ready": False,
        "validation_timestamp": None,
        "component_health": {},
        "performance_compliance": {},
        "integration_results": {},
        "recommendations": []
    }

    try:
        from datetime import datetime, timezone
        validation_report["validation_timestamp"] = datetime.now(timezone.utc).isoformat()

        performance_monitor = PerformanceMonitor()

        # Test database connection and performance
        db_performance = await test_database_performance()
        validation_report["component_health"]["database"] = {
            "available": "error" not in db_performance,
            "performance_ms": db_performance.get("average_query_time_ms", 1000),
            "adhd_compliant": db_performance.get("adhd_compliant", False)
        }

        # Test schema and migration capabilities
        try:
            schema_manager, migration_result = await setup_phase2_schema(
                database_config, performance_monitor
            )
            validation_report["component_health"]["schema"] = {
                "installed": migration_result.success,
                "migration_time_ms": migration_result.duration_ms,
                "adhd_compliant": migration_result.adhd_compliance
            }
        except Exception as e:
            validation_report["component_health"]["schema"] = {
                "installed": False,
                "error": str(e)
            }

        # Test graph operations performance
        if validation_report["component_health"]["database"]["available"]:
            try:
                db = SerenaIntelligenceDatabase(database_config, performance_monitor)
                await db.initialize()

                graph_perf = await quick_performance_test(db)
                validation_report["performance_compliance"]["graph_operations"] = {
                    "all_under_200ms": graph_perf.get("all_under_200ms", False),
                    "average_time_ms": graph_perf.get("average_time_ms", 1000),
                    "adhd_compliant": graph_perf.get("adhd_compliant", False)
                }

                await db.close()
            except Exception as e:
                validation_report["performance_compliance"]["graph_operations"] = {
                    "error": str(e)
                }

        # Run integration tests if requested
        if run_integration_tests:
            try:
                integration_results = await run_integration_test_suite()
                validation_report["integration_results"] = {
                    "all_tests_passed": integration_results["compliance_status"]["all_tests_passed"],
                    "success_rate": integration_results["test_summary"]["success_rate"],
                    "layer1_preserved": integration_results["compliance_status"]["layer1_preserved"],
                    "performance_compliant": integration_results["compliance_status"]["performance_compliant"],
                    "recommendations": integration_results["recommendations"]
                }
            except Exception as e:
                validation_report["integration_results"] = {
                    "error": str(e),
                    "all_tests_passed": False
                }

        # Assess deployment readiness
        db_ready = validation_report["component_health"]["database"]["available"]
        schema_ready = validation_report["component_health"].get("schema", {}).get("installed", False)
        perf_ready = validation_report["performance_compliance"].get("graph_operations", {}).get("adhd_compliant", False)
        integration_ready = validation_report["integration_results"].get("all_tests_passed", False) if run_integration_tests else True

        validation_report["deployment_ready"] = db_ready and schema_ready and perf_ready and integration_ready

        # Generate recommendations
        if not db_ready:
            validation_report["recommendations"].append("🔧 Fix database connection issues")
        if not schema_ready:
            validation_report["recommendations"].append("🏗️ Complete schema installation")
        if not perf_ready:
            validation_report["recommendations"].append("⚡ Optimize performance to meet ADHD targets")
        if run_integration_tests and not integration_ready:
            validation_report["recommendations"].append("🧪 Resolve integration test failures")

        if validation_report["deployment_ready"]:
            validation_report["recommendations"].append("🚀 Phase 2A ready for deployment!")

    except Exception as e:
        validation_report["recommendations"].append(f"💥 Validation failed: {e}")

    return validation_report


async def setup_complete_intelligent_relationship_system(
    database_config: DatabaseConfig = None,
    workspace_id: str = "/default/workspace",
    performance_monitor = None
) -> dict[str, Any]:
    """
    Set up complete Phase 2C intelligent relationship system with all components.

    Returns:
        Dictionary with all initialized Phase 2C components
    """
    from ..performance_monitor import PerformanceMonitor
    from ..tree_sitter_analyzer import TreeSitterAnalyzer

    if performance_monitor is None:
        performance_monitor = PerformanceMonitor()

    # Set up Phase 2B adaptive learning system first
    phase2b_system = await setup_complete_adaptive_learning_system(database_config, performance_monitor)

    # Create Phase 2C components
    base_tree_sitter = TreeSitterAnalyzer()
    await base_tree_sitter.initialize()

    enhanced_tree_sitter = await create_enhanced_tree_sitter_integration(
        base_tree_sitter,
        phase2b_system["database"],
        phase2b_system["learning_engine"],
        phase2b_system["profile_manager"],
        performance_monitor
    )

    conport_bridge = await create_conport_bridge(
        phase2b_system["database"],
        phase2b_system["graph_operations"],
        phase2b_system["profile_manager"],
        workspace_id,
        performance_monitor
    )

    adhd_filter = await create_adhd_relationship_filter(
        phase2b_system["profile_manager"],
        phase2b_system["pattern_recognition"],
        phase2b_system["effectiveness_tracker"],
        performance_monitor
    )

    realtime_scorer = await create_realtime_relevance_scorer(
        phase2b_system["learning_engine"],
        phase2b_system["profile_manager"],
        phase2b_system["pattern_recognition"],
        phase2b_system["effectiveness_tracker"],
        performance_monitor
    )

    relationship_builder = await create_intelligent_relationship_builder(
        phase2b_system["database"],
        phase2b_system["graph_operations"],
        base_tree_sitter,
        phase2b_system["learning_engine"],
        phase2b_system["profile_manager"],
        phase2b_system["pattern_recognition"],
        performance_monitor
    )

    success_validator = await create_navigation_success_validator(
        relationship_builder,
        enhanced_tree_sitter,
        conport_bridge,
        adhd_filter,
        realtime_scorer,
        phase2b_system["database"],
        performance_monitor
    )

    # Combine all systems
    complete_system = {
        # Phase 2A + 2B Components (from previous system)
        **phase2b_system,

        # Phase 2C Components
        "relationship_builder": relationship_builder,
        "enhanced_tree_sitter": enhanced_tree_sitter,
        "conport_bridge": conport_bridge,
        "adhd_filter": adhd_filter,
        "realtime_scorer": realtime_scorer,
        "success_validator": success_validator,

        # System info
        "version": __version__,
        "total_components": 13,  # 7 from 2B + 6 from 2C
        "phase2c_complete": True
    }

    return complete_system


async def setup_complete_pattern_store_system(
    database_config: DatabaseConfig = None,
    workspace_id: str = "/default/workspace",
    performance_monitor = None
) -> dict[str, Any]:
    """
    Set up complete Phase 2D pattern store and reuse system with all components.

    Returns:
        Dictionary with all initialized Phase 2D components
    """
    from ..performance_monitor import PerformanceMonitor

    if performance_monitor is None:
        performance_monitor = PerformanceMonitor()

    # Set up Phase 2C intelligent relationship system first
    phase2c_system = await setup_complete_intelligent_relationship_system(
        database_config, workspace_id, performance_monitor
    )

    # Create Phase 2D pattern store components
    template_manager = await create_strategy_template_manager(
        phase2c_system["database"],
        phase2c_system["profile_manager"],
        phase2c_system["effectiveness_tracker"],
        workspace_id,
        performance_monitor
    )

    pattern_adapter = await create_personal_pattern_adapter(
        phase2c_system["database"],
        template_manager,
        phase2c_system["profile_manager"],
        phase2c_system["effectiveness_tracker"],
        performance_monitor
    )

    persistence_bridge = await create_cross_session_persistence_bridge(
        phase2c_system["database"],
        template_manager,
        pattern_adapter,
        workspace_id,
        performance_monitor
    )

    evolution_system = await create_effectiveness_evolution_system(
        phase2c_system["database"],
        template_manager,
        pattern_adapter,
        phase2c_system["effectiveness_tracker"],
        persistence_bridge,
        performance_monitor
    )

    recommendation_engine = await create_pattern_reuse_recommendation_engine(
        phase2c_system["database"],
        template_manager,
        pattern_adapter,
        phase2c_system["profile_manager"],
        phase2c_system["pattern_recognition"],
        phase2c_system["effectiveness_tracker"],
        persistence_bridge,
        performance_monitor
    )

    validation_system = await create_performance_validation_system(
        phase2c_system["database"],
        recommendation_engine,
        template_manager,
        phase2c_system["profile_manager"],
        performance_monitor
    )

    # Start background processes
    await persistence_bridge.start_background_sync()

    # Combine all systems
    complete_system = {
        # Phase 2A + 2B + 2C Components (from previous system)
        **phase2c_system,

        # Phase 2D Components
        "template_manager": template_manager,
        "pattern_adapter": pattern_adapter,
        "persistence_bridge": persistence_bridge,
        "evolution_system": evolution_system,
        "recommendation_engine": recommendation_engine,
        "validation_system": validation_system,

        # System info
        "version": __version__,
        "total_components": 19,  # 13 from 2C + 6 from 2D
        "phase2d_complete": True,
        "pattern_store_operational": True
    }

    return complete_system


async def setup_complete_cognitive_load_management_system(
    database_config: DatabaseConfig = None,
    workspace_id: str = "/default/workspace",
    performance_monitor = None
) -> dict[str, Any]:
    """
    Set up complete Phase 2E cognitive load management system with all components.

    Returns:
        Dictionary with all initialized Phase 2A-2E components (31 total)
    """
    from ..performance_monitor import PerformanceMonitor
    from ..tree_sitter_analyzer import TreeSitterAnalyzer
    from ..adhd_features import ADHDCodeNavigator

    if performance_monitor is None:
        performance_monitor = PerformanceMonitor()

    # Set up Phase 2D pattern store system first
    phase2d_system = await setup_complete_pattern_store_system(
        database_config, workspace_id, performance_monitor
    )

    # Create Layer 1 components for Phase 2E integration
    tree_sitter = TreeSitterAnalyzer()
    await tree_sitter.initialize()

    adhd_navigator = ADHDCodeNavigator()

    # Create Phase 2E cognitive load management components
    cognitive_orchestrator = await create_cognitive_load_orchestrator(
        # All Phase 2A-2D components for orchestration
        phase2d_system["database"],
        phase2d_system["graph_operations"],
        phase2d_system["learning_engine"],
        phase2d_system["profile_manager"],
        phase2d_system["pattern_recognition"],
        phase2d_system["effectiveness_tracker"],
        phase2d_system["context_optimizer"],
        phase2d_system["relationship_builder"],
        phase2d_system["adhd_filter"],
        phase2d_system["realtime_scorer"],
        phase2d_system["template_manager"],
        phase2d_system["recommendation_engine"],
        performance_monitor,
        adhd_navigator
    )

    disclosure_director = await create_progressive_disclosure_director(
        phase2d_system["database"],
        phase2d_system["graph_operations"],
        phase2d_system["profile_manager"],
        phase2d_system["relationship_builder"],
        phase2d_system["adhd_filter"],
        phase2d_system["template_manager"],
        performance_monitor
    )

    fatigue_engine = await create_fatigue_detection_engine(
        cognitive_orchestrator,
        disclosure_director,
        phase2d_system["learning_engine"],
        phase2d_system["profile_manager"],
        phase2d_system["context_optimizer"],
        phase2d_system["effectiveness_tracker"],
        phase2d_system["database"],
        performance_monitor
    )

    threshold_coordinator = await create_personalized_threshold_coordinator(
        cognitive_orchestrator,
        fatigue_engine,
        phase2d_system["profile_manager"],
        phase2d_system["learning_engine"],
        phase2d_system["effectiveness_tracker"],
        phase2d_system["database"],
        performance_monitor
    )

    accommodation_harmonizer = await create_accommodation_harmonizer(
        cognitive_orchestrator,
        fatigue_engine,
        threshold_coordinator,
        phase2d_system["profile_manager"],
        phase2d_system["database"],
        adhd_navigator,
        performance_monitor
    )

    # Create complete system integration test
    integration_test = CompleteSystemIntegrationTest(workspace_id)

    # Combine all systems - complete Phase 2A-2E (31 components)
    complete_system = {
        # Phase 2A + 2B + 2C + 2D Components (from previous system)
        **phase2d_system,

        # Phase 2E Components
        "cognitive_orchestrator": cognitive_orchestrator,
        "disclosure_director": disclosure_director,
        "fatigue_engine": fatigue_engine,
        "threshold_coordinator": threshold_coordinator,
        "accommodation_harmonizer": accommodation_harmonizer,
        "integration_test": integration_test,

        # Layer 1 components for complete integration
        "tree_sitter_analyzer": tree_sitter,
        "adhd_navigator": adhd_navigator,

        # System info
        "version": __version__,
        "total_components": 31,  # 6+7+6+6+6 = 31 components
        "phase2e_complete": True,
        "cognitive_load_management_operational": True,
        "complete_system_ready": True
    }

    return complete_system


async def get_phase2_status() -> dict:
    """Get current Phase 2 status and health information."""
    from ..redis_optimizer import quick_redis_health_check

    status = {
        "version": __version__,
        "layer1_status": {},
        "phase2_status": {},
        "integration_health": "unknown"
    }

    try:
        # Check Layer 1 Redis health
        redis_health = await quick_redis_health_check()
        status["layer1_status"] = {
            "redis_available": redis_health.get("redis_available", False),
            "performance_ms": redis_health.get("operation_time_ms", 1000),
            "status": redis_health.get("status", "Unknown")
        }

        # Check Phase 2 database health
        db_performance = await test_database_performance()
        status["phase2_status"] = {
            "database_available": "error" not in db_performance,
            "performance_ms": db_performance.get("average_query_time_ms", 1000),
            "adhd_compliant": db_performance.get("adhd_compliant", False)
        }

        # Assess integration health
        layer1_healthy = status["layer1_status"]["redis_available"]
        phase2_healthy = status["phase2_status"]["database_available"]

        if layer1_healthy and phase2_healthy:
            status["integration_health"] = "🚀 Excellent - Hybrid system operational"
        elif layer1_healthy:
            status["integration_health"] = "✅ Layer 1 operational, Phase 2 needs attention"
        elif phase2_healthy:
            status["integration_health"] = "⚠️ Phase 2 operational, Layer 1 needs attention"
        else:
            status["integration_health"] = "🔴 Both layers need attention"

    except Exception as e:
        status["integration_health"] = f"❌ Status check failed: {e}"

    return status


# Initialize module
import logging
logger = logging.getLogger(__name__)
logger.info(f"🧠 Serena v2 Phase 2 Intelligence Module loaded - version {__version__}")