# ARCHITECTURE_AND_INTENDED_USES.md — Serena v2

Analyzed ref: `fe48c0a874ac25ed179b9ddb091252a6dbe9b5c2`

## 1. System Overview

Serena v2 is an ADHD-optimized code intelligence MCP server that provides 33 tools for code navigation, complexity analysis, untracked work detection, and pattern learning. It runs as a stdio MCP server (`services/serena/mcp_server.py`) within the Dopemux multi-service ecosystem.

**Server name**: `serena-v2` (via `Server("serena-v2")`)
**Transport**: stdio (primary), HTTP (dashboard), SSE (Docker wrapper — different codebase)
**Module version**: `2.0.0`

## 2. Architecture Layers

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 1: MCP Protocol Interface                                 │
│  mcp_server.py (5378 lines) — SerenaV2MCPServer                 │
│  33 registered tools, list_tools/call_tool dispatch,             │
│  lazy component loading, ADHD result limits                      │
├─────────────────────────────────────────────────────────────────┤
│  Layer 2: Feature Modules (services/serena/*.py, ~43 files)      │
│  untracked_work_detector, git_detector, pattern_learner,         │
│  abandonment_tracker, revival_suggester, metrics_dashboard,      │
│  navigation_cache, enhanced_lsp, adhd_features, focus_manager,  │
│  code_structure_analyzer, tree_sitter_analyzer, session_manager, │
│  session_lifecycle_manager, multi_workspace_wrapper,             │
│  conport_client_unified, file_watcher, eventbus_consumer         │
├─────────────────────────────────────────────────────────────────┤
│  Layer 3: Intelligence Engine (intelligence/*.py, 27 modules)    │
│  database, graph_operations, conport_bridge, adaptive_learning, │
│  pattern_recognition, effectiveness_tracker, context_switching, │
│  cognitive_load_orchestrator, fatigue_detection, schema_manager, │
│  cross_session_persistence_bridge, enhanced_tree_sitter          │
├─────────────────────────────────────────────────────────────────┤
│  Layer 4: External Dependencies                                  │
│  PostgreSQL (asyncpg), Redis (async), ConPort (port 5455),      │
│  LSP servers (pylsp), tree-sitter, ADHD Engine, Dope-Context    │
└─────────────────────────────────────────────────────────────────┘
```

## 3. mcp_server.py as Orchestrator

The `SerenaV2MCPServer` class (line 378) is the sole orchestrator. It:

1. **Initializes** with lazy component tracking (6 components: database, lsp, claude_context, tree_sitter, adhd_features, conport)
2. **Detects workspace** by walking up directories looking for `.git` (line 456)
3. **Registers tools** via `@self.server.list_tools()` (33 Tool definitions) and `@self.server.call_tool()` (33 dispatch branches)
4. **Manages component lifecycle** via `_ensure_component(name)` — loads on first use, tracks errors
5. **Applies ADHD limits** dynamically via `get_dynamic_max_results()` integration with external ADHD Engine
6. **Routes multi-workspace** calls to `SerenaMultiWorkspace` wrapper when `workspace_paths` provided

### Lazy Loading Strategy
```
Startup: Workspace detection + file watcher only (<100ms target)
On first tool use: Load required component via _ensure_component()
On failure: Log error, set initialization_errors[component], continue with fallback
```

### Response Pattern
All tools return `TextContent(type="text", text=<json_string>)`. JSON payloads include:
- `performance.latency_ms` — timing information
- `adhd_guidance` — ADHD-specific recommendations (on applicable tools)
- `mode` — "lsp", "fallback_grep", "fallback_basic", "heuristic", etc.

## 4. Intelligence Engine Decomposition

The `intelligence/` package contains 27 Python modules + 4 test files + 1 SQL schema:

### Database/Storage (3 modules)
| Module | Lines | Purpose |
|--------|-------|---------|
| `database.py` | ~1,200 | async PostgreSQL pool via asyncpg, query methods, connection management |
| `schema_manager.py` | ~450 | Schema migrations, version tracking |
| `cross_session_persistence_bridge.py` | ~850 | Bidirectional ConPort ↔ intelligence DB sync |

### Graph/Relationships (3 modules)
| Module | Lines | Purpose |
|--------|-------|---------|
| `graph_operations.py` | ~1,100 | Code relationship graph, traversal, `CodeElementNode`, `RelationshipEdge` |
| `intelligent_relationship_builder.py` | ~950 | Smart relationship discovery, import/call analysis |
| `adhd_relationship_filter.py` | ~650 | Cognitive load filtering for relationships |

### Learning/Adaptation (5 modules)
| Module | Lines | Purpose |
|--------|-------|---------|
| `adaptive_learning.py` | ~1,400 | Core learning engine, `NavigationSequence`, `PersonalLearningProfile` |
| `learning_profile_manager.py` | ~700 | Personal profile CRUD, preference tracking |
| `pattern_recognition.py` | ~1,050 | Navigation pattern detection, `RecognizedPattern`, `PatternPrediction` |
| `personal_pattern_adapter.py` | ~600 | Per-user pattern adaptation |
| `pattern_reuse_recommendation_engine.py` | ~700 | Strategy reuse recommendations |

### Effectiveness/Validation (4 modules)
| Module | Lines | Purpose |
|--------|-------|---------|
| `effectiveness_tracker.py` | ~997 | Effectiveness measurement, A/B testing |
| `effectiveness_evolution_system.py` | ~800 | Evolution tracking over time |
| `navigation_success_validator.py` | ~550 | Success criteria validation |
| `performance_validation_system.py` | ~500 | Performance benchmarking |

### ADHD/Cognitive (5 modules)
| Module | Lines | Purpose |
|--------|-------|---------|
| `cognitive_load_orchestrator.py` | ~900 | Overall cognitive load management |
| `accommodation_harmonizer.py` | ~700 | Accommodation strategy harmonization |
| `fatigue_detection_engine.py` | ~650 | Fatigue pattern detection |
| `progressive_disclosure_director.py` | ~600 | Progressive disclosure control |
| `context_switching_optimizer.py` | ~800 | Context switch detection and optimization |

### Scoring/Analysis (3 modules)
| Module | Lines | Purpose |
|--------|-------|---------|
| `realtime_relevance_scorer.py` | ~750 | Real-time relevance scoring |
| `personalized_threshold_coordinator.py` | ~600 | Per-user threshold tuning |
| `strategy_template_manager.py` | ~500 | Strategy template CRUD |

### Integration (2 modules)
| Module | Lines | Purpose |
|--------|-------|---------|
| `conport_bridge.py` | ~949 | ConPort knowledge graph bridge |
| `enhanced_tree_sitter.py` | ~800 | Enhanced AST analysis |

### Package Init
`intelligence/__init__.py` imports all 27 modules. However, `mcp_server.py` only lazily imports specific ones as needed. Many intelligence modules may not be actively called at runtime.

## 5. ConPort Bridge Integration

Source: `intelligence/conport_bridge.py` (949 lines)
Class: `ConPortKnowledgeGraphBridge`

### Read Operations
- `_get_recent_conport_decisions()` — Fetch recent decisions from ConPort
- `_get_conport_item_details()` — Get details of specific ConPort items
- `_find_conport_links_for_element()` — Find ConPort links for code elements

### Write Operations
- `create_code_decision_link()` — Stores links in intelligence PostgreSQL (NOT directly to ConPort)

### Discovery
- `discover_automatic_links()` — Scans code elements, finds potential ConPort connections

### ADHD Filtering
- `_apply_adhd_context_filtering()` — Reduces cognitive load of ConPort query results

### Authority Boundary
Serena's ConPort bridge stores integration links in its OWN PostgreSQL database (`conport_integration_links` table), not directly in ConPort. It READS from ConPort but only WRITES to ConPort via the `conport_client_unified.py` adapter (for progress entries, custom data).

## 6. Navigation Cache (Redis)

Source: `navigation_cache.py`
Class: `NavigationCache` with `NavigationCacheConfig` (Pydantic model)

- **Ephemeral**: All data lost on Redis restart
- **DB index**: 1 (separate from ConPort cache)
- **Key prefix**: `serena:v2:nav`
- **TTLs**: 5min (default), 10min (symbols), 30min (definitions), 15min (references), 3min (fallback results)
- **Features**: Context-aware prefetching, navigation breadcrumbs, focus session state, cache warming
- **Used by**: `find_symbol_tool` (cache read/write with key `find_symbol:{query}:{type}:{max}`)

## 7. Session Management

### SessionLifecycleManager (session_lifecycle_manager.py)
- `start_session()` — Create session with worktree detection
- `update_session()` — Update focus/content
- `complete_session()` — End session with duration tracking
- `cleanup_stale_sessions()` — 24h auto-expire

### SessionManager (session_manager.py)
- Wraps lifecycle manager with worktree detection
- Auto-detects git worktree info
- Integrates with ConPort for session persistence

### NOTE: Session tools are DEAD CODE
The `initialize_session_tool`, `get_multi_session_dashboard_tool`, and `get_session_info_tool` handlers exist in `mcp_server.py` but are NOT registered in `list_tools()` or dispatched in `call_tool()`. Session management is not exposed via MCP.

## 8. Feature Modules

### Feature 1: Untracked Work Detection (6 tools)
- **Detection**: `untracked_work_detector.py` — Multi-signal confidence scoring (git + ConPort + filesystem)
- **Storage**: `untracked_work_storage.py` — ConPort-backed work item persistence
- **Git analysis**: `git_detector.py` — Uncommitted work detection, branch analysis
- **Adaptive thresholds**: Confidence threshold decreases across sessions (0.75 → 0.65 → 0.60)
- **Grace period**: 30-minute grace for exploratory work
- **Auto-track**: When confidence >= 0.85, auto-create ConPort task

### Feature 4: Branch Organization (1 tool)
- `git_detector.py:suggest_branch_organization()` — Clusters uncommitted files by directory

### Feature 5: Pattern Learning (2 tools)
- `pattern_learner.py` — In-memory LRU cache with pattern statistics
- Categories: file_extension, directory, branch_prefix

### Feature 6: Abandonment Detection (3 tools)
- `abandonment_tracker.py` — Calculates abandonment scores for idle work
- `revival_suggester.py` — Suggests reviving abandoned work

### Feature 7: Metrics Dashboard (3 tools)
- `metrics_dashboard.py` — 3-level progressive disclosure (summary → breakdown → trends)
- Saves snapshots to ConPort for historical tracking

## 9. ADHD Optimization Patterns

### Dynamic Result Limits
`get_dynamic_max_results(user_id, default_max)` at line 97 queries the external ADHD Engine (`services/adhd_engine/`) to get user-specific limits based on attention state:
- focused: up to 40 results
- scattered: 3 results
- transitioning: 5 results

### Progressive Disclosure
- `adhd_features.py:507` — `ProgressiveDisclosure.apply_to_results()`
- 3-level dashboard (level 1: summary, level 2: breakdown, level 3: trends)
- Max 5 items per section, max 10 results per tool

### Cognitive Load Management
- `adhd_features.py:581` — `CognitiveLoadManager`
- Complexity scoring: 0.0-1.0 with LOW/MEDIUM/HIGH assessment
- Safe reading time estimates
- 25-minute Pomodoro session planning

### LSP Bypass
- `mcp_server.py:572` — `_should_use_lsp()` — Skip LSP if workspace has >5000 Python files
- Prevents LSP timeout on large workspaces

## 10. Dual Codebase Issue

### services/serena/ (this analysis)
- 54K+ lines of custom dopemux code
- 33 MCP tools via stdio
- Intelligence engine with 27 modules
- Uses mcp SDK directly
- No Dockerfile, no requirements.txt

### docker/mcp-servers-source/serena/ (Docker deployment)
- Thin wrapper (~135 lines wrapper.py)
- Installs upstream `oraios/serena` via pip
- Runs `serena start-mcp-server` (upstream binary)
- Wrapped by mcp-proxy for SSE transport
- Completely different tool surface

### compose.yml references
- `compose.yml` builds from `./docker/mcp-servers/serena` (this directory does NOT exist — stale path)
- Exposes ports 3006 (MCP) and 4006 (info server)
- Health check on port 4006

**Impact**: The Docker-deployed "Serena" service exposes the upstream oraios/serena tool surface, NOT the 33-tool surface documented here. The `services/serena/` codebase appears to run only in local stdio mode.

## 11. Intended Uses

### Docs Say
- `services/registry.yaml`: "Serena MCP — ADHD accommodation server"
- `mcp_server.py` docstring: "Exposes 31-component ADHD-optimized code intelligence via MCP protocol"
- `__init__.py`: "Serena — ADHD-Optimized Code Intelligence System"

### Code Does
- 33 MCP tools for code navigation, complexity analysis, untracked work detection, and ADHD accommodations
- Lazy component loading for fast startup
- Fallback strategies (LSP → grep, Tree-sitter → line counting)
- Multi-workspace support via `SerenaMultiWorkspace` wrapper
- Integration with ConPort for state persistence
- Redis caching for 100x navigation speedup

### Tests Verify
- `tests/test_serena_http.py`: HTTP health and metrics endpoints
- `tests/test_multi_workspace.py`: Multi-workspace resolution
- `intelligence/test_database.py`: Database operations
- `intelligence/integration_test.py`: Full integration
- `intelligence/convergence_test.py`: Learning convergence
