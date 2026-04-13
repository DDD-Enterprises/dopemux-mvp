"""
Serena v2 - Complete Enterprise Navigation Intelligence (31 Components)

PHASE 2E COMPLETE SYSTEM: Layer 1 + Phase 2A-2E Intelligence
- Layer 1: Enhanced LSP with Tree-sitter, claude-context, ADHD optimization (8 components)
- Phase 2A: PostgreSQL database, schema management, graph operations (6 components)
- Phase 2B: Adaptive learning, pattern recognition, effectiveness tracking (7 components)
- Phase 2C: Intelligent relationships, ConPort bridge, real-time scoring (6 components)
- Phase 2D: Strategy templates, pattern reuse, evolution system (6 components)
- Phase 2E: Cognitive load orchestration, fatigue detection, harmonization (6 components)

Enterprise Features:
- Real claude-context MCP integration for semantic search
- PostgreSQL-powered code relationship intelligence
- Adaptive learning with personalized navigation profiles
- ADHD-optimized cognitive load management with fatigue detection
- Cross-session pattern persistence and template evolution
- Complete system integration with <200ms performance targets
"""

# Layer 1 Components
from .enhanced_lsp import EnhancedLSPWrapper, LSPConfig, LSPResponse
from .navigation_cache import NavigationCache, NavigationCacheConfig
from .adhd_features import ADHDCodeNavigator, CodeComplexityAnalyzer
from .focus_manager import FocusManager, FocusMode, AttentionState
from .performance_monitor import PerformanceMonitor, PerformanceTarget, PerformanceLevel
from .tree_sitter_analyzer import TreeSitterAnalyzer, StructuralElement, CodeComplexity
from .claude_context_integration import ClaudeContextIntegration, ClaudeContextConfig, SemanticSearchResult
from .mcp_client import McpClient, McpResponse

# Phase 2A-2E Intelligence Components (import everything from intelligence module)
from .intelligence import *

__all__ = [
    # Layer 1 Components
    "EnhancedLSPWrapper", "LSPConfig", "LSPResponse",
    "NavigationCache", "NavigationCacheConfig",
    "ADHDCodeNavigator", "CodeComplexityAnalyzer",
    "FocusManager", "FocusMode", "AttentionState",
    "PerformanceMonitor", "PerformanceTarget", "PerformanceLevel",
    "TreeSitterAnalyzer", "StructuralElement", "CodeComplexity",
    "ClaudeContextIntegration", "ClaudeContextConfig", "SemanticSearchResult",
    "McpClient", "McpResponse",

    # Intelligence Module Components (Phase 2A-2E, 23 components)
    # Phase 2A: Database Layer
    "SerenaIntelligenceDatabase", "DatabaseConfig", "DatabaseMetrics",
    "create_intelligence_database", "test_database_performance",
    "SerenaSchemaManager", "MigrationStatus", "MigrationStep", "MigrationResult",
    "setup_phase2_schema", "migrate_from_layer1",
    "SerenaGraphOperations", "RelationshipType", "NavigationMode",
    "CodeElementNode", "RelationshipEdge", "NavigationPath",
    "create_graph_operations", "quick_performance_test",
    "SerenaLayer1IntegrationTest", "IntegrationTestResult", "run_integration_test_suite",

    # Phase 2B: Adaptive Learning
    "AdaptiveLearningEngine", "NavigationSequence", "NavigationAction",
    "PersonalLearningProfile", "LearningPhase", "AttentionState",
    "create_adaptive_learning_engine", "simulate_learning_convergence",
    "PersonalLearningProfileManager", "AccommodationPreference",
    "NavigationPreferencePattern", "AttentionPattern", "ProfileInsight",
    "create_profile_manager", "simulate_profile_learning",
    "AdvancedPatternRecognition", "NavigationPatternType", "PatternComplexity",
    "RecognizedPattern", "PatternPrediction", "create_pattern_recognition_engine",
    "EffectivenessTracker", "EffectivenessDimension", "EffectivenessProfile",
    "ABTest", "ImprovementRecommendation", "create_effectiveness_tracker",
    "ContextSwitchingOptimizer", "ContextSwitchEvent", "ContextSwitchType",
    "SwitchSeverity", "InterruptionType", "SwitchingPattern",
    "TaskContinuationContext", "create_context_switching_optimizer",
    "LearningConvergenceValidator", "ConvergenceTestSuite", "ConvergenceResult",
    "ConvergenceMetric", "LearningSimulationScenario", "run_quick_convergence_test",

    # Phase 2C: Intelligent Relationships
    "IntelligentRelationshipBuilder", "IntelligentRelationship", "RelationshipSuggestion",
    "NavigationContext", "RelationshipRelevance", "RelationshipContext",
    "create_intelligent_relationship_builder", "test_relationship_suggestions",
    "EnhancedTreeSitterIntegration", "PersonalizedStructuralElement",
    "EnhancedRelationshipDiscovery", "IntelligentStructuralRelationship",
    "create_enhanced_tree_sitter_integration",
    "ConPortKnowledgeGraphBridge", "ConPortCodeLink", "DecisionCodeContext",
    "CodeDecisionInsight", "ConPortItemType", "create_conport_bridge", "test_conport_integration",
    "ADHDRelationshipFilter", "FilteringStrategy", "FilteringResult",
    "FilteringDecision", "CognitiveLoadCategory", "create_adhd_relationship_filter", "test_adhd_filtering",
    "RealtimeRelevanceScorer", "DynamicRelationshipScore", "RelevanceScore",
    "ScoringDimension", "ScoringTrigger", "create_realtime_relevance_scorer", "test_realtime_scoring",
    "NavigationSuccessValidator", "TestSuiteResult", "NavigationAttempt",
    "NavigationSuccessMetric", "TestScenario", "NavigationTask",
    "create_navigation_success_validator", "quick_success_validation_test",

    # Phase 2D: Pattern Store & Reuse
    "StrategyTemplateManager", "NavigationStrategyTemplate", "StrategyStep",
    "TemplateComplexity", "AccommodationType", "TemplateLibrary",
    "create_strategy_template_manager", "validate_template_library",
    "PersonalPatternAdapter", "PersonalizationDelta", "PersonalizedTemplate",
    "PersonalizationType", "PersonalizationOrigin", "DeltaCluster", "create_personal_pattern_adapter",
    "CrossSessionPersistenceBridge", "TemplateEvolutionProposal", "SyncStatus",
    "SyncHealthStatus", "create_cross_session_persistence_bridge", "test_persistence_bridge",
    "EffectivenessEvolutionSystem", "EvolutionOpportunity", "EvolutionExperiment",
    "EvolutionTrigger", "EvolutionStrategy", "create_effectiveness_evolution_system",
    "run_evolution_monitoring_cycle",
    "PatternReuseRecommendationEngine", "PatternRecommendation", "RecommendationConfidence",
    "RecommendationReason", "TimeReductionCategory", "RecommendationResult",
    "create_pattern_reuse_recommendation_engine", "test_recommendation_engine",
    "PerformanceValidationSystem", "NavigationGoal", "PerformanceValidationResult",
    "NavigationGoalType", "ValidationMethod", "ValidationExperiment",
    "create_performance_validation_system", "validate_30_percent_target",

    # Phase 2E: Cognitive Load Management
    "CognitiveLoadOrchestrator", "CognitiveLoadReading", "CognitiveLoadState",
    "OrchestrationState", "AdaptiveResponse", "create_cognitive_load_orchestrator", "test_cognitive_orchestration",
    "ProgressiveDisclosureDirector", "DisclosureLevel", "DisclosureCoordination",
    "ComponentDisclosureState", "DisclosureStrategy", "create_progressive_disclosure_director", "test_progressive_disclosure",
    "FatigueDetectionEngine", "FatigueDetection", "FatigueSeverity",
    "AdaptiveResponsePlan", "FatigueResponseResult", "FatigueIndicator",
    "create_fatigue_detection_engine", "test_fatigue_detection",
    "PersonalizedThresholdCoordinator", "ThresholdCoordination", "ThresholdType",
    "ThresholdValue", "ThresholdAdaptationPlan", "create_personalized_threshold_coordinator", "test_threshold_coordination",
    "AccommodationHarmonizer", "AccommodationProfile", "AccommodationState",
    "SystemAccommodationType", "AccommodationEffectiveness", "create_accommodation_harmonizer", "test_accommodation_harmonization",
    "CompleteSystemIntegrationTest", "SystemIntegrationResult", "ComponentHealth",
    "IntegrationTestScenario", "run_complete_system_integration_test", "validate_production_readiness",

    # Complete System Convenience Functions
    "setup_phase2_intelligence", "validate_phase2_deployment",
    "setup_complete_adaptive_learning_system", "setup_complete_intelligent_relationship_system",
    "setup_complete_pattern_store_system", "setup_complete_cognitive_load_management_system",
    "get_phase2_status"
]

__version__ = "2.0.0-phase2e"