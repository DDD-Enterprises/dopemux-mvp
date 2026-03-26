# APPENDIX_A_SOURCE_INDEX.md — Serena v2 Phase 1 Discovery

Analyzed ref: `fe48c0a874ac25ed179b9ddb091252a6dbe9b5c2`

## Group 1: Root Docs

| File | Lines | Purpose |
|------|-------|---------|
| `services/serena/__init__.py` | 5 | Package init, `__version__ = "2.0.0"` |

*No README, CHANGELOG, or LICENSE files exist within `services/serena/`.*

## Group 2: Documentation (docs/)

| File | Purpose |
|------|---------|
| `.claude/modules/cognitive-plane/serena-lsp.md` | Claude module: Serena LSP config |
| `docs/archive/sessions/serena/conport-schema-f5.md` | Session notes: ConPort schema for F5 |
| `docs/archive/sessions/serena/f6-completion.md` | Session notes: F6 completion |
| `docs/archive/sessions/serena/session-2025-10-24.md` | Session notes |
| `docs/archive/sessions/serena/token-limit-fix.md` | Session notes: token limit fix |
| `docs/archive/sessions/serena/session-handoff-2025-10-18.md` | Session handoff |
| `docs/archive/sessions/serena/v2/f002-completion-summary-2.md` | F002 completion |
| `docs/archive/sessions/serena/v2/ux-polish-checklist.md` | UX polish checklist |
| `docs/archive/sessions/serena/v2/f001-enhanced-build-summary-2.md` | F001 enhanced build |
| `docs/archive/sessions/serena/v2/f002-user-guide.md` | F002 user guide |
| `docs/archive/sessions/serena/v2/f002-implementation-plan-2.md` | F002 implementation plan |
| `docs/archive/sessions/serena/v2/f001-enhanced-completion-2.md` | F001 enhanced completion |
| `docs/archive/sessions/serena/v2/f-new-1-f-new-2-completion-2.md` | F-NEW-1/2 completion |
| `docs/archive/sessions/serena/v2/f001-usage-examples.md` | F001 usage examples |
| `docs/archive/sessions/serena/v2/f5-completion-summary-2.md` | F5 completion |
| `docs/archive/sessions/serena/v2/SESSION_HANDOFF_20251018.md` | Session handoff |
| `docs/archive/sessions/serena/v2/f7-completion-summary-2.md` | F7 completion |
| `docs/archive/sessions/serena/v2/f001-test-results-2.md` | F001 test results |
| `docs/archive/sessions/serena/v2/f002-migration-success-2.md` | F002 migration |
| `docs/archive/empty-stubs/serena-v2-deployment.md` | Empty stub |
| `docs/archive/claude-sessions/serena-adhd-cross-system-analysis-20251023-2.md` | ADHD cross-system analysis |
| `docs/archive/claude-sessions/serena-v2-analysis-2025-10-16.md` | v2 analysis |
| `docker/mcp-servers-source/serena/README.md` | Docker serena README |

## Group 3: Source Code (services/serena/)

### 3a. MCP Server / Entry Points

| File | Lines | Key Classes/Functions |
|------|-------|----------------------|
| `mcp_server.py` | 5378 | `SerenaV2MCPServer`, `SimpleLSPClient`, `main()`, 32 tools |
| `http_server.py` | 577 | FastAPI `app`, `/health`, `/api/*` endpoints |
| `mcp_client.py` | 469 | MCP client implementation |

### 3b. ADHD / Cognitive Modules

| File | Lines | Key Classes |
|------|-------|------------|
| `adhd_features.py` | 834 | `CodeComplexityAnalyzer`, `ADHDCodeNavigator`, `ProgressiveDisclosure`, `CognitiveLoadManager` |
| `focus_manager.py` | 723 | `FocusManager`, `FocusMode`, `AttentionState`, `FocusSession` |

### 3c. Navigation / Code Analysis

| File | Lines | Key Classes |
|------|-------|------------|
| `enhanced_lsp.py` | 985 | `EnhancedLSPWrapper`, `LSPConfig`, `LSPResponse` |
| `code_structure_analyzer.py` | 897 | `CodeStructureAnalyzer`, `CodeSymbol`, `ImportRelationship` |
| `tree_sitter_analyzer.py` | 715 | Tree-sitter analysis |
| `navigation_cache.py` | 1008 | `NavigationCache`, `NavigationCacheConfig` (Redis) |
| `code_graph_storage.py` | 901 | Code graph storage |
| `indexing_pipeline.py` | 933 | Indexing pipeline |

### 3d. Feature Modules (F1-F7)

| File | Lines | Feature | Key Classes |
|------|-------|---------|------------|
| `untracked_work_detector.py` | 382 | F1 | `UntrackedWorkDetector` |
| `untracked_work_storage.py` | 973 | F1 | `UntrackedWorkStorage`, `UntrackedWorkStatus` |
| `git_detector.py` | 696 | F1/F4 | `GitWorkDetector` |
| `pattern_learner.py` | 410 | F5 | `PatternLearner`, `PatternCache` |
| `abandonment_tracker.py` | 285 | F6 | `AbandonmentTracker` |
| `revival_suggester.py` | 276 | F6 | `RevivalSuggester` |
| `metrics_dashboard.py` | 559 | F7 | `MetricsAggregator`, `MetricsDashboard` |
| `false_starts_aggregator.py` | 203 | — | `FalseStartsAggregator` |
| `batch_track_tool.py` | 71 | — | Batch tracking |
| `design_first_detector.py` | 256 | — | Design-first detection |

### 3e. Session / Lifecycle Management

| File | Lines | Key Classes |
|------|-------|------------|
| `session_manager.py` | 377 | `SessionManager` |
| `session_lifecycle_manager.py` | 650 | `SessionLifecycleManager`, `SessionState` |
| `session_id_generator.py` | 195 | Session ID generation |
| `multi_session_dashboard.py` | 295 | Multi-session dashboard |

### 3f. Integration / Bridge

| File | Lines | Key Classes |
|------|-------|------------|
| `conport_client_unified.py` | 264 | `ConPortDBClient` (PostgreSQL direct) |
| `conport_matcher.py` | 312 | ConPort matching |
| `bridge_adapter.py` | 332 | `SerenaBridgeAdapter` |
| `eventbus_consumer.py` | 290 | `EventBusConsumer`, `DecisionCache` (Redis streams) |
| `integration_bridge_connector.py` | 108 | Integration bridge |
| `claude_context_integration.py` | 937 | Dope-context integration |
| `kg_integration.py` | 273 | Knowledge graph integration |
| `kg_provider.py` | 309 | KG provider |

### 3g. Multi-Workspace / Infrastructure

| File | Lines | Key Classes |
|------|-------|------------|
| `multi_workspace_wrapper.py` | 558 | `SerenaMultiWorkspace` |
| `file_watcher.py` | 290 | `SerenaFileWatcher`, `FileWatcherManager` |
| `performance_monitor.py` | 550 | `PerformanceMonitor` |
| `redis_optimizer.py` | 511 | Redis optimizer |
| `priority_context_builder.py` | 295 | Priority context builder |
| `auto_activator.py` | 468 | Auto-activator |
| `worktree_detector.py` | 305 | Worktree detector |
| `developer_learning_engine.py` | 1043 | Developer learning engine |
| `layer1_validation.py` | 618 | Layer 1 validation |
| `demo_hover_integration.py` | 159 | Demo: hover integration |

### 3h. Intelligence Sub-Package (services/serena/intelligence/)

| File | Lines | Key Classes/Exports |
|------|-------|--------------------|
| `__init__.py` | 1154 | Full system wiring, all module exports, setup functions |
| `database.py` | 521 | `SerenaIntelligenceDatabase`, `DatabaseConfig` (asyncpg) |
| `schema_manager.py` | 618 | `SerenaSchemaManager`, `MigrationStatus` |
| `schema.sql` | 350 | DDL: 6 PostgreSQL tables |
| `graph_operations.py` | 764 | `SerenaGraphOperations`, `CodeElementNode`, `RelationshipEdge` |
| `conport_bridge.py` | 949 | `ConPortKnowledgeGraphBridge`, `ConPortCodeLink`, `DecisionCodeContext` |
| `adaptive_learning.py` | 929 | `AdaptiveLearningEngine`, `PersonalLearningProfile` |
| `learning_profile_manager.py` | 897 | `PersonalLearningProfileManager` |
| `pattern_recognition.py` | 1050 | `AdvancedPatternRecognition`, `RecognizedPattern` |
| `effectiveness_tracker.py` | 997 | `EffectivenessTracker`, `ABTest` |
| `effectiveness_evolution_system.py` | 904 | Effectiveness evolution |
| `context_switching_optimizer.py` | 1039 | `ContextSwitchingOptimizer`, `ContextSwitchEvent` |
| `intelligent_relationship_builder.py` | 1161 | `IntelligentRelationshipBuilder` |
| `enhanced_tree_sitter.py` | 970 | `EnhancedTreeSitterIntegration` |
| `cognitive_load_orchestrator.py` | 915 | Cognitive load orchestrator |
| `accommodation_harmonizer.py` | 910 | Accommodation harmonizer |
| `adhd_relationship_filter.py` | 869 | ADHD relationship filter |
| `fatigue_detection_engine.py` | 982 | Fatigue detection |
| `progressive_disclosure_director.py` | 1019 | Progressive disclosure director |
| `realtime_relevance_scorer.py` | 1052 | Real-time relevance scorer |
| `personal_pattern_adapter.py` | 950 | Personal pattern adapter |
| `personalized_threshold_coordinator.py` | 953 | Personalized threshold coordinator |
| `strategy_template_manager.py` | 867 | Strategy template manager |
| `cross_session_persistence_bridge.py` | 850 | Cross-session persistence (ConPort ↔ Postgres) |
| `pattern_reuse_recommendation_engine.py` | 1059 | Pattern reuse recommendation |
| `navigation_success_validator.py` | 906 | Navigation success validator |

## Group 4: Tests

| File | Lines | What it Tests |
|------|-------|--------------|
| `tests/test_serena_http.py` | ~50 | HTTP health, metrics, pattern limit |
| `tests/test_multi_workspace.py` | ~50 | Workspace resolution utility |
| `test_conport_integration.py` | 74 | ConPort integration |
| `test_f001_enhanced.py` | 216 | Feature 1 enhanced detection |
| `test_http_server.py` | 94 | HTTP server endpoints |
| `test_token_limit_fix.py` | 127 | Token limit fix |
| `validate_f002_components.py` | 209 | F002 component validation |
| `intelligence/test_database.py` | 550 | Database unit tests |
| `intelligence/integration_test.py` | 708 | Integration test suite |
| `intelligence/convergence_test.py` | 943 | Learning convergence tests |
| `intelligence/complete_system_integration_test.py` | 814 | Full system integration |
| `intelligence/performance_validation_system.py` | 943 | Performance validation |

## Group 5: Build/Runtime

| File | Purpose |
|------|---------|
| `services/serena/src/dopemux_serena.egg-info/PKG-INFO` | Package metadata: dopemux-serena 0.1.0 |
| `services/serena/src/dopemux_serena.egg-info/requires.txt` | Runtime dependencies |
| `services/serena/src/dopemux_serena.egg-info/entry_points.txt` | Entry points |
| `services/serena/migrations/002_add_session_support.sql` | Migration: session support |
| `services/serena/migrations/002_add_session_support_adapted.sql` | Migration: adapted |
| `services/serena/migrations/002_add_session_support_final.sql` | Migration: final |
| `services/serena/migrations/002_session_support_simple.sql` | Migration: simple |

## Group 6: Docker/Compose/Config

| File | Purpose |
|------|---------|
| `docker/mcp-servers-source/serena/Dockerfile` | python:3.11-slim, upstream serena pip install |
| `docker/mcp-servers-source/serena/wrapper.py` | mcp-proxy SSE transport wrapper |
| `docker/mcp-servers-source/serena/info_server.py` | FastAPI health/info on port 4006 |
| `docker/mcp-servers-source/serena/start_with_info.sh` | Docker entrypoint (parallel processes) |
| `compose.yml` (serena service block) | Port 3006/4006, builds docker/mcp-servers-source/serena |
| `compose/legacy/docker-compose.master.yml` (serena-v2 block) | Legacy master compose |
| `compose/legacy/docker-compose.staging.yml` (serena-mcp block) | Legacy staging compose |
| `services/registry.yaml` (serena entry) | Port 3006, /health, category: mcp |
| `config/profiles/adhd-default.yaml` | References serena |
| `config/profiles/web-dev.yaml` | References serena |
| `config/profiles/python-ml.yaml` | References serena |

## Summary Counts

| Group | Files | Total Lines (approx) |
|-------|-------|---------------------|
| Source (services/serena/*.py) | 43 | ~27,395 |
| Intelligence (intelligence/*.py) | 27 | ~27,243 |
| Tests | 12 | ~4,778 |
| Build/Runtime | 7 | — |
| Docker/Compose/Config | 10 | — |
| Documentation | 23 | — |
| **Total** | **122** | **~54,638+ lines of Python** |
