# DISCOVERY_NOTES.md — Serena v2 Phase 1 Discovery

## 1. Repo Identity Snapshot

- **Repository**: `<REPO_ROOT>` (local)
- **Remote**: (local-only analysis)
- **Target**: `services/serena/` (the "Serena v2" MCP server)
- **Package name (egg-info)**: `dopemux-serena` version `0.1.0`
- **Module `__version__`**: `"2.0.0"` (in `services/serena/__init__.py`)

## 2. Analyzed Ref

```
fe48c0a874ac25ed179b9ddb091252a6dbe9b5c2
```

## 3. Default Branch

Active branch at analysis time: `codex/main-drain-20260306`
(Default branch not separately queried — this was the checked-out ref.)

## 4. High-Confidence Active Modules

### 4.1 MCP Server Entry Point
- **`services/serena/mcp_server.py`** (5378 lines): The single MCP entry point. Contains `SerenaV2MCPServer` class. Uses `mcp.server.Server("serena-v2")` and `mcp.server.stdio.stdio_server` for transport. Registers 32 tools via `list_tools()` / `call_tool()` dispatch pattern.

### 4.2 HTTP API (Dashboard)
- **`services/serena/http_server.py`** (577 lines): Standalone FastAPI server on port 8003. Endpoints: `/health`, `/api/metrics`, `/api/detections/summary`, `/api/patterns/top`, `/api/patterns/{pattern_id}`. Uses mock data with real aggregator fallback.

### 4.3 Core Feature Modules (actively wired into mcp_server.py)
| Module | Evidence of wiring |
|--------|--------------------|
| `untracked_work_detector.py` | Imported & used in `detect_untracked_work_tool()` |
| `untracked_work_storage.py` | Used by `track_untracked_work_tool()`, `snooze_untracked_work_tool()`, `ignore_untracked_work_tool()` |
| `git_detector.py` | Used by `untracked_work_detector.py`, `suggest_branch_organization_tool()` |
| `pattern_learner.py` | Used by `get_pattern_stats_tool()`, `get_top_patterns_tool()` |
| `abandonment_tracker.py` | Used by `get_abandoned_work_tool()`, `mark_abandoned_tool()` |
| `revival_suggester.py` | Used by `get_abandoned_work_tool()` |
| `metrics_dashboard.py` | Used by `get_metrics_dashboard_tool()`, `get_metric_history_tool()`, `save_metrics_snapshot_tool()` |
| `navigation_cache.py` | Used by find_symbol_tool() via `_ensure_component("navigation_cache")` |
| `enhanced_lsp.py` | Used by find_symbol/goto_definition via `_ensure_component("lsp")` |
| `adhd_features.py` | Used by find_symbol, complexity tools via `_ensure_component("adhd_features")` |
| `code_structure_analyzer.py` | Used by complexity analysis |
| `tree_sitter_analyzer.py` | Used by analyze_complexity via `_ensure_component("tree_sitter")` |
| `focus_manager.py` | Used by `update_focus_mode_tool()` |
| `conport_client_unified.py` | Used by `_ensure_conport_client()` for ConPort DB access |
| `multi_workspace_wrapper.py` | Used by multi-workspace variants of several tools |
| `file_watcher.py` | Started on initialize() via `_ensure_component("file_watcher")` |
| `session_manager.py` | Used by session tools (handler exists but not in list_tools) |
| `session_lifecycle_manager.py` | Used by session lifecycle |

### 4.4 Intelligence Sub-Package (31 modules)
All modules in `services/serena/intelligence/` are imported via `intelligence/__init__.py`. Key active modules:
- `database.py` — PostgreSQL layer via asyncpg
- `graph_operations.py` — Code relationship graph
- `conport_bridge.py` — ConPort knowledge graph bridge
- `adaptive_learning.py` — Learning engine
- `pattern_recognition.py` — Pattern detection
- `effectiveness_tracker.py` — Effectiveness measurement
- `context_switching_optimizer.py` — Context switch detection
- `learning_profile_manager.py` — Personal learning profiles
- `schema_manager.py` — DB migrations
- `enhanced_tree_sitter.py` — AST analysis
- `intelligent_relationship_builder.py` — Smart relationship discovery

## 5. Deprecated/Legacy Modules

### 5.1 No explicit v1 code found under services/serena/
There is no `v1/` directory or files explicitly marked v1. The module header says "Serena v2 MCP Server — Phase 2 + Enhanced Features".

### 5.2 Docker wrapper uses external serena package
The Docker build (`docker/mcp-servers-source/serena/Dockerfile`) installs `git+https://github.com/oraios/serena.git@f561204840eb4a96c6956d5cd98712f8ed52d0cb` — this is the **upstream open-source Serena** (different from the dopemux-internal `services/serena/`). The wrapper runs `serena start-mcp-server` from the pip-installed package, NOT from `services/serena/mcp_server.py`.

**DISCREPANCY**: The compose.yml Docker service builds from `docker/mcp-servers-source/serena/` which uses the **upstream oraios/serena**, while the actual MCP server code at `services/serena/mcp_server.py` is a completely independent, much larger implementation. These are two different codebases with the same name.

### 5.3 Legacy compose references
- `compose/legacy/docker-compose.staging.yml` references a `serena-mcp` service (port 3001 via Traefik)
- `compose/legacy/docker-compose.master.yml` references `serena-v2` building from `docker/mcp-servers/serena` (a directory that does not exist — likely stale reference to a deleted or renamed path)

### 5.4 Potentially orphaned handler methods
These tool handler methods exist in `mcp_server.py` but are NOT listed in `list_tools()` and NOT dispatched in `call_tool()`:
- `detect_untracked_work_enhanced_tool()` (line 3076)
- `initialize_session_tool()` (line 3262)
- `get_multi_session_dashboard_tool()` (line 3338)
- `get_session_info_tool()` (line 3397)

These are dead code — handler implementations with no registration or dispatch.

## 6. Runtime Entrypoints Discovered

| Entrypoint | Transport | File | Line |
|-----------|-----------|------|------|
| `main()` → `stdio_server()` | **stdio** | `mcp_server.py` | 5326 |
| `if __name__ == "__main__"` | stdio (via asyncio.run) | `mcp_server.py` | 5371 |
| FastAPI `app` | **HTTP** | `http_server.py` | 54 |
| `uvicorn.run(port=8003)` | HTTP | `http_server.py` | 572 |
| Docker wrapper: `mcp-proxy --transport sse` → `serena start-mcp-server` | **SSE** (via mcp-proxy) | `docker/mcp-servers-source/serena/wrapper.py` | 34 |
| Docker info_server: `uvicorn(port=4006)` | HTTP | `docker/mcp-servers-source/serena/info_server.py` | — |

**Summary of transports**:
- **stdio**: Primary transport for local MCP (mcp_server.py main())
- **HTTP**: Dashboard API (http_server.py, FastAPI on 8003) + info server (Docker, 4006)
- **SSE**: Docker container transport via mcp-proxy wrapping upstream serena package (NOT services/serena/ code)

## 7. Callable/Tool/API Registration Locations (ALL tools, with tier)

### 7.1 MCP Tools (registered in `mcp_server.py:724-1467` via `list_tools()`)

Total registered tools: **32** (code says "21+" in docstring, "24" in main() log)

| # | Tool Name | Tier | Description | Line (Tool def) | Handler Line |
|---|-----------|------|-------------|-----------------|-------------|
| 1 | `get_workspace_status` | Health | System health/diagnostics | 728 | 1552 |
| 2 | `find_symbol` | Tier 1 Navigation | LSP symbol search, ADHD-filtered | 737 | 1617 |
| 3 | `goto_definition` | Tier 1 Navigation | LSP definition navigation | 763 | 1783 |
| 4 | `get_context` | Tier 1 Navigation | Surrounding code with complexity | 785 | 1956 |
| 5 | `find_references` | Tier 1 Navigation | LSP reference finder | 815 | 2073 |
| 6 | `analyze_complexity` | Tier 2 ADHD | Tree-sitter complexity scoring | 854 | 2302 |
| 7 | `filter_by_focus` | Tier 2 ADHD | Attention-state filtering | 881 | 2470 |
| 8 | `suggest_next_step` | Tier 2 ADHD | Navigation suggestions | 901 | 2518 |
| 9 | `predict_navigation_from_git` | Enhanced Navigation | Git history pattern prediction | 919 | 5069 |
| 10 | `find_similar_code` | Enhanced Navigation | Semantic search via dope-context | 938 | 4969 |
| 11 | `find_test_file` | Enhanced Navigation | TDD test file finder | 973 | 5148 |
| 12 | `get_unified_complexity` | Enhanced Navigation | Multi-signal complexity | 996 | 5262 |
| 13 | `get_reading_order` | Tier 2 ADHD | Complexity-ordered reading | 1028 | 2603 |
| 14 | `find_relationships` | Tier 3 Advanced | Grep-based call/import detection | 1057 | 2700 |
| 15 | `get_navigation_patterns` | Tier 3 Advanced | Navigation history analysis | 1084 | 2809 |
| 16 | `update_focus_mode` | Tier 3 Advanced | Focus state setter | 1108 | 2862 |
| 17 | `detect_untracked_work` | Feature 1 Detection | ADHD untracked work detection | 1123 | 2910 |
| 18 | `track_untracked_work` | Feature 1 Action | Create ConPort task | 1144 | 4217 |
| 19 | `snooze_untracked_work` | Feature 1 Action | Snooze reminder | 1168 | 4319 |
| 20 | `ignore_untracked_work` | Feature 1 Action | Mark abandoned | 1188 | 4401 |
| 21 | `suggest_branch_organization` | Feature 4 | Git branch clustering | 1206 | 3449 |
| 22 | `get_pattern_stats` | Feature 5 Analytics | Pattern learning stats | 1222 | 3555 |
| 23 | `get_top_patterns` | Feature 5 Analytics | Top learned patterns | 1231 | 3635 |
| 24 | `get_abandoned_work` | Feature 6 Analytics | Idle work detection | 1261 | 3697 |
| 25 | `mark_abandoned` | Feature 6 Action | Record cleanup action | 1291 | 3798 |
| 26 | `get_abandonment_stats` | Feature 6 Analytics | Abandonment statistics | 1310 | 3866 |
| 27 | `get_metrics_dashboard` | Feature 7 Analytics | Aggregate metrics (3 levels) | 1319 | 3940 |
| 28 | `get_metric_history` | Feature 7 Analytics | Time-series metric data | 1344 | 4017 |
| 29 | `save_metrics_snapshot` | Feature 7 Internal | Save daily metrics to ConPort | 1370 | 4125 |
| 30 | `get_untracked_work_config` | Feature 1 Config | Get user config | 1379 | 4464 |
| 31 | `update_untracked_work_config` | Feature 1 Config | Update user config | 1388 | 4522 |
| 32 | `read_file` | Files | Read workspace file | 1426 | 4816 |
| 33 | `list_dir` | Files | List directory | 1449 | 4892 |

**Note**: The `call_tool()` dispatch at line 1470 dispatches to all 33 tools listed above (32 in list_tools array, dispatched by name in call_tool). However `main()` claims "24 tools" in its log output.

### 7.2 Unregistered Handler Methods (dead code)
| Handler | Line | Purpose |
|---------|------|---------|
| `detect_untracked_work_enhanced_tool()` | 3076 | Enhanced version of Feature 1 |
| `initialize_session_tool()` | 3262 | Session initialization |
| `get_multi_session_dashboard_tool()` | 3338 | Multi-session overview |
| `get_session_info_tool()` | 3397 | Current session info |

### 7.3 HTTP Endpoints (http_server.py)
| Endpoint | Method | Line |
|----------|--------|------|
| `/` | GET | 328 |
| `/health` | GET | 351 |
| `/api/metrics` | GET | 368 |
| `/api/detections/summary` | GET | 407 |
| `/api/patterns/top` | GET | 449 |
| `/api/patterns/{pattern_id}` | GET | 505 |

### 7.4 Docker Info Server Endpoints (info_server.py)
| Endpoint | Method | Port |
|----------|--------|------|
| `/health` | GET | 4006 |
| `/info` | GET | 4006 |

## 8. DTO/Parser/Validator Locations

| Type | Location | Key Classes/Structures |
|------|----------|----------------------|
| Dataclass DTO | `intelligence/conport_bridge.py` | `ConPortCodeLink`, `DecisionCodeContext`, `CodeDecisionInsight` |
| Enum | `intelligence/conport_bridge.py` | `ConPortItemType`, `LinkStrength`, `ContextRelevance` |
| Dataclass | `intelligence/graph_operations.py` | `CodeElementNode`, `RelationshipEdge`, `NavigationPath` |
| Enum | `intelligence/graph_operations.py` | `RelationshipType`, `NavigationMode` |
| Dataclass | `intelligence/adaptive_learning.py` | `NavigationSequence`, `NavigationAction`, `PersonalLearningProfile` |
| Enum | `intelligence/adaptive_learning.py` | `LearningPhase`, `AttentionState` |
| Dataclass | `intelligence/pattern_recognition.py` | `RecognizedPattern`, `PatternPrediction` |
| Enum | `intelligence/pattern_recognition.py` | `NavigationPatternType`, `PatternComplexity` |
| Dataclass | `intelligence/context_switching_optimizer.py` | `ContextSwitchEvent`, `SwitchingPattern`, `TaskContinuationContext` |
| Enum | `intelligence/context_switching_optimizer.py` | `ContextSwitchType`, `SwitchSeverity`, `InterruptionType` |
| Dataclass | `intelligence/database.py` | `DatabaseConfig`, `DatabaseMetrics` |
| Enum | `intelligence/database.py` | `QueryPerformanceLevel` |
| Dataclass | `session_lifecycle_manager.py` | `SessionState` |
| Dataclass | `code_structure_analyzer.py` | `CodeSymbol`, `ImportRelationship`, `CallRelationship` |
| Enum | `code_structure_analyzer.py` | `LanguageSupport` |
| Pydantic Model | `navigation_cache.py` | `NavigationCacheConfig` |
| Enum | `focus_manager.py` | `FocusMode`, `AttentionState` |
| Dataclass | `focus_manager.py` | `FocusSession` |
| Enum | `untracked_work_storage.py` | `UntrackedWorkStatus` |
| LSP classes | `enhanced_lsp.py` | `LSPConfig`, `LSPResponse`, `EnhancedLSPWrapper` |

**Input validation**: Tool parameter schemas are defined inline in `list_tools()` as JSON Schema objects with types, enums, min/max constraints, and defaults. No separate schema files exist.

## 9. Workflow/State/Gating Locations

| Concern | Module | Key Logic |
|---------|--------|-----------|
| Focus mode state | `mcp_server.py:421` | `self.current_focus_mode` (in-memory, resets on restart) |
| Focus sessions (timed) | `focus_manager.py` | `FocusManager`, 25-minute focus windows |
| Attention state assessment | `focus_manager.py:339` | `_assess_attention_state()`, break suggestion |
| ADHD result filtering | `adhd_features.py` | `ADHDCodeNavigator.filter_symbols_for_focus()` |
| Progressive disclosure | `adhd_features.py:507` | `ProgressiveDisclosure.apply_to_results()` |
| Cognitive load management | `adhd_features.py:581` | `CognitiveLoadManager` |
| Dynamic result limits | `mcp_server.py:97` | `get_dynamic_max_results()` via ADHD engine |
| Lazy component loading | `mcp_server.py:592` | `_ensure_component()` — gate on component availability |
| LSP bypass decision | `mcp_server.py:572` | `_should_use_lsp()` — skip LSP if >5K Python files |
| Session lifecycle | `session_lifecycle_manager.py` | `start_session()`, `update_session()`, `complete_session()`, `cleanup_stale_sessions()` |
| Untracked work reminders | `untracked_work_storage.py:632` | `should_remind_now()`, quiet hours, snooze logic |
| Threshold adaptation | `untracked_work_detector.py:246` | `_threshold_for_session()` — confidence threshold rises with session number |

## 10. Persistence/Storage Locations

| Store | Type | Module | Details |
|-------|------|--------|---------|
| PostgreSQL (asyncpg) | Durable | `intelligence/database.py` | Code elements, relationships, navigation patterns, learning profiles, strategies, ConPort links |
| PostgreSQL schema | Durable | `intelligence/schema.sql` | 6 tables: `code_elements`, `code_relationships`, `navigation_patterns`, `learning_profiles`, `navigation_strategies`, `conport_integration_links` |
| Redis | Cache/Ephemeral | `navigation_cache.py` | LSP results, symbol cache, definition cache, focus context, navigation breadcrumbs, tree-sitter analysis. Key prefix: `serena:v2:nav`, db_index=1 |
| Redis Streams | Event | `eventbus_consumer.py` | Decision cache from dopecon-bridge events |
| ConPort (PostgreSQL) | Durable | `conport_client_unified.py` | Active context, progress entries, custom data. Host: localhost:5455, DB: `dopemux_knowledge_graph` |
| ConPort (via bridge) | Durable | `bridge_adapter.py` | Decision search, navigation state save/restore |
| File-based (ConPort sync) | Durable | `untracked_work_storage.py` | Work items stored via ConPort custom_data |
| In-memory | Ephemeral | `mcp_server.py:421` | `current_focus_mode` — resets on restart |
| In-memory LRU | Cache | `pattern_learner.py:26` | `PatternCache` — in-memory LRU with TTL |
| Cross-session bridge | Sync | `intelligence/cross_session_persistence_bridge.py` | ConPort ↔ PostgreSQL bidirectional sync |

## 11. Transport Locations

| Transport | File | Mechanism | Port |
|-----------|------|-----------|------|
| **stdio** | `mcp_server.py:5362` | `mcp.server.stdio.stdio_server()` | N/A (stdin/stdout) |
| **HTTP** (FastAPI) | `http_server.py:54` | FastAPI + uvicorn | 8003 |
| **SSE** (Docker) | `docker/mcp-servers-source/serena/wrapper.py:34` | mcp-proxy wrapping upstream `serena start-mcp-server` | 3006 |
| **HTTP** (Docker info) | `docker/mcp-servers-source/serena/info_server.py` | FastAPI + uvicorn | 4006 |

**IMPORTANT**: The SSE Docker transport wraps the **upstream oraios/serena pip package**, NOT the `services/serena/mcp_server.py` code. These are two entirely different server implementations.

## 12. Export/Report/File-Generation Surfaces

| Surface | Module | Details |
|---------|--------|---------|
| Metrics snapshot | `metrics_dashboard.py:458` | `save_daily_snapshot()` writes to ConPort |
| Metrics formatting (3 levels) | `metrics_dashboard.py:302-403` | `format_level1()`, `format_level2()`, `format_level3()` |
| ADHD-friendly formatting | `http_server.py:211` | `format_adhd_friendly()` normalizes payloads |
| Dashboard JSON responses | `http_server.py` | All `/api/*` endpoints return JSON |
| Tool responses | `mcp_server.py` | All tools return `TextContent(type="text", text=json.dumps(...))` |

No file-generation, export-to-disk, or report-file-writing surfaces were found. All output is API-level (JSON over MCP stdio or HTTP).

## 13. Architecture/Module Boundary Notes

### 13.1 Three-Layer Architecture
```
┌─────────────────────────────────────────────────────┐
│  MCP Entry Point: mcp_server.py (SerenaV2MCPServer) │
│  32 tools, stdio transport, lazy component loading  │
├─────────────────────────────────────────────────────┤
│  Feature Modules (services/serena/*.py)              │
│  untracked_work, git_detector, pattern_learner,      │
│  abandonment, metrics, focus, sessions, cache        │
├─────────────────────────────────────────────────────┤
│  Intelligence Engine (intelligence/*.py, 31 modules) │
│  database, graph_ops, conport_bridge, adaptive_learn,│
│  pattern_recognition, effectiveness, context_switch  │
├─────────────────────────────────────────────────────┤
│  External Dependencies                               │
│  PostgreSQL (asyncpg), Redis, ConPort (port 5455),   │
│  LSP servers, tree-sitter, ADHD Engine               │
└─────────────────────────────────────────────────────┘
```

### 13.2 Intelligence Engine Decomposition (31 modules)
Organized by concern:

**Database/Storage (3)**:
- `database.py` — async PostgreSQL pool
- `schema_manager.py` — schema migrations
- `cross_session_persistence_bridge.py` — ConPort ↔ Postgres sync

**Graph/Relationships (3)**:
- `graph_operations.py` — code relationship graph
- `intelligent_relationship_builder.py` — smart relationship discovery
- `adhd_relationship_filter.py` — ADHD-aware relationship filtering

**Learning/Adaptation (5)**:
- `adaptive_learning.py` — learning engine core
- `learning_profile_manager.py` — personal profiles
- `pattern_recognition.py` — navigation patterns
- `personal_pattern_adapter.py` — personalized adaptation
- `pattern_reuse_recommendation_engine.py` — pattern reuse

**Effectiveness/Validation (4)**:
- `effectiveness_tracker.py` — effectiveness measurement
- `effectiveness_evolution_system.py` — evolution tracking
- `navigation_success_validator.py` — success validation
- `performance_validation_system.py` — performance testing

**ADHD/Cognitive (5)**:
- `cognitive_load_orchestrator.py` — cognitive load management
- `accommodation_harmonizer.py` — accommodation harmonization
- `fatigue_detection_engine.py` — fatigue detection
- `progressive_disclosure_director.py` — progressive disclosure
- `context_switching_optimizer.py` — context switch optimization

**Scoring/Analysis (3)**:
- `realtime_relevance_scorer.py` — real-time relevance
- `personalized_threshold_coordinator.py` — threshold personalization
- `strategy_template_manager.py` — strategy templates

**Integration (2)**:
- `conport_bridge.py` — ConPort knowledge graph bridge
- `enhanced_tree_sitter.py` — enhanced AST analysis

**Testing (4)**:
- `test_database.py`
- `integration_test.py`
- `convergence_test.py`
- `complete_system_integration_test.py`

**Config (1)**:
- `schema.sql` — DDL

### 13.3 ConPort Bridge Deep Dive
`intelligence/conport_bridge.py` (949 lines):
- Class: `ConPortKnowledgeGraphBridge`
- **Reads from ConPort**: `_get_recent_conport_decisions()`, `_get_conport_item_details()`, `_find_conport_links_for_element()`
- **Writes to ConPort**: Via `create_code_decision_link()` which stores links in the intelligence PostgreSQL database (NOT directly to ConPort)
- **Discovery method**: `discover_automatic_links()` scans code elements and finds potential ConPort connections
- **ADHD filtering**: `_apply_adhd_context_filtering()` reduces cognitive load of ConPort results
- **Effectiveness tracking**: `user_found_helpful`, `effectiveness_score`, `usage_frequency` fields on `ConPortCodeLink`

### 13.4 Dual Serena Codebases (CRITICAL finding)
There are TWO separate "Serena" implementations:
1. **`services/serena/`** — 54,638+ lines of custom dopemux code, 32 MCP tools, intelligence engine. Runs via stdio.
2. **`docker/mcp-servers-source/serena/`** — Thin wrapper around `pip install git+https://github.com/oraios/serena.git@f561204840eb4a96c6956d5cd98712f8ed52d0cb` (upstream OSS). Runs via mcp-proxy SSE.

The compose.yml service builds from (2), NOT from (1). This is a significant architectural divergence.

## 14. Intended-Use Notes

### Docs say:
- `services/registry.yaml`: "Serena MCP — ADHD accommodation server", port 3006, category: mcp
- `mcp_server.py` docstring: "Exposes 31-component ADHD-optimized code intelligence via MCP protocol"
- `http_server.py` docstring: "ADHD-optimized pattern detection metrics"
- `__init__.py`: "Serena — ADHD-Optimized Code Intelligence System"
- Docker info_server.py: "ADHD-Optimized Code Navigation & Project Memory"

### Code does:
- 32 MCP tools across 5 tiers: Health (1), Tier 1 Navigation (4), Enhanced Navigation (4), Tier 2 ADHD (4), Tier 3 Advanced (3), Feature 1 (6), Feature 4-7 (8), Files (2)
- Lazy-loads 6 components: database, lsp, claude_context, tree_sitter, adhd_features, conport
- Connects to: PostgreSQL (intelligence DB), Redis (navigation cache), ConPort (decision context), LSP servers, tree-sitter, ADHD Engine
- stdio transport for MCP, separate FastAPI HTTP for dashboard
- 4 handler methods exist without registration (dead code)

### Tests verify:
- `tests/test_serena_http.py`: Health endpoint contract, metrics payload, pattern limit enforcement
- `tests/test_multi_workspace.py`: Workspace resolution utility
- `test_conport_integration.py`: ConPort integration (in-tree test)
- `test_f001_enhanced.py`: Feature 1 enhanced tests
- `test_token_limit_fix.py`: Token limit fix
- `intelligence/test_database.py`: Database unit tests
- `intelligence/integration_test.py`: Full integration suite
- `intelligence/convergence_test.py`: Learning convergence validation
- `intelligence/complete_system_integration_test.py`: Full system test

## 15. Missing Evidence

| Item | Status | Notes |
|------|--------|-------|
| No README.md in `services/serena/` | MISSING | No service-level documentation |
| No requirements.txt in `services/serena/` | MISSING | Dependencies only in egg-info PKG-INFO |
| No pyproject.toml in `services/serena/` | MISSING | Build config absent (egg-info exists under `src/`) |
| No Dockerfile in `services/serena/` | MISSING | Docker build at `docker/mcp-servers-source/serena/` uses different code |
| docker/mcp-servers/ directory | MISSING | compose.yml references `./docker/mcp-servers/serena` which doesn't exist |
| Compose service ↔ services/serena alignment | BROKEN | compose.yml builds upstream serena, not dopemux services/serena/ |
| Intelligence DB initialization evidence | UNKNOWN | schema.sql exists but no evidence of automatic migration at startup |
| ADHD Engine integration verification | UNKNOWN | `_get_adhd_config()` imports from `adhd_engine` module (external to serena) — not verified |
| Full test coverage data | UNKNOWN | No coverage report found |
| Whether intelligence modules are actually called at runtime vs just imported | PARTIAL | `__init__.py` imports all 31 modules, but `mcp_server.py` only imports specific ones lazily |

## 16. Explicit Readiness Judgment

### **READY_FOR_PHASE_2**

**Justification**:
1. ✅ MCP tool registration fully located — 32 tools with exact names, schemas, tiers, handler locations
2. ✅ Entry points confirmed — stdio (mcp_server.py), HTTP (http_server.py), SSE (Docker wrapper)
3. ✅ ConPort bridge integration mapped — reads/writes/discovery methods documented
4. ✅ Persistence model clear — PostgreSQL (intelligence DB), Redis (cache), ConPort (decisions), in-memory (focus state)
5. ✅ Architecture boundaries identified — 3-layer with intelligence engine decomposition
6. ✅ All 76 Python files catalogued and categorized
7. ✅ Dead code identified — 4 unregistered tool handlers
8. ⚠️ Critical finding: Dual Serena codebase divergence (must be addressed in Phase 2 extraction scope)
9. ⚠️ Missing build/package files in services/serena/ (egg-info only)

**Recommendation**: Phase 2 extraction should target `services/serena/` (the 54K+ line dopemux implementation), NOT the Docker wrapper of upstream oraios/serena. The Docker/compose alignment issue should be documented as a known architectural gap.
