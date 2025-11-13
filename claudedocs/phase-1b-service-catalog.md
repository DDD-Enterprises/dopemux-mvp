# Phase 1B: Service Catalog via Serena
**Date**: 2025-10-16
**Duration**: 20 minutes
**Method**: Direct file navigation + semantic search
**Status**: ✅ Complete

---

## Service Inventory (12 Services)

| # | Service | Entry Point | Type | Port | Status |
|---|---------|-------------|------|------|--------|
| 1 | adhd_engine | main.py:164 | FastAPI | 8090 | ✅ Implemented |
| 2 | claude-context | N/A | TypeScript MCP | - | ⚠️ Legacy? |
| 3 | conport_kg | orchestrator.py:1 | Python module | - | ✅ Implemented |
| 4 | conport_kg_ui | App.tsx:18 | React CLI | - | ✅ Implemented |
| 5 | dope-context | server.py:1170 | FastMCP | - | ✅ Implemented |
| 6 | dopemux-gpt-researcher | main.py | FastAPI | 8000 | ✅ Implemented |
| 7 | mcp-dopecon-bridge | main.py | FastAPI | 3016 | ✅ Production |
| 8 | ml-risk-assessment | TBD | Python | - | ? |
| 9 | orchestrator | main.py | Python | - | ? |
| 10 | serena | server.py:1 | MCP Wrapper | - | ✅ Implemented |
| 11 | task-orchestrator | server.py:522 | MCP Wrapper | - | ✅ Implemented |
| 12 | taskmaster | server.py | MCP | - | ? |

---

## Detailed Service Catalog

### 1. ADHD Accommodation Engine ✅
**Path**: `services/adhd_engine/`
**Entry**: `main.py` (164 lines)
**Type**: FastAPI microservice
**Port**: 8090 (default)

**Features**:
- 7 REST API endpoints for ADHD assessments
- 6 background async monitors
- Redis persistence for user profiles
- DopeconBridge connection planned (Day 4)

**API Endpoints**:
- `GET /` - Service info
- `GET /health` - Health check with accommodation stats
- `/api/v1/*` - ADHD assessment endpoints

**Technology**: FastAPI + Redis + Background asyncio tasks
**ADHD Features**: Energy tracking, attention monitoring, accommodation suggestions
**Migration**: Path C - Week 1 (Decision #140)

---

### 2. Claude-Context ⚠️
**Path**: `services/claude-context/`
**Type**: TypeScript/Milvus-based context system
**Status**: Unknown (appears to be legacy system?)

**Investigation Needed**: Determine if active or superseded by dope-context

---

### 3. ConPort Knowledge Graph ✅
**Path**: `services/conport_kg/`
**Entry**: `orchestrator.py` (KG Intelligence Orchestrator)
**Type**: Python module (PostgreSQL AGE backend)

**Features**:
- Event-driven query triggers
- Background analysis and suggestions
- ADHD-safe proactive assistance
- Two-Plane integration

**Query Classes**:
- `OverviewQueries` - High-level summaries
- `ExplorationQueries` - Graph traversal
- `DeepContextQueries` - Full decision context

**Automation**:
- `on_decision_logged` → Find similar + auto-create tasks
- `on_task_started` → Load decision context
- `on_file_opened` → Show related decisions
- `on_sprint_planning` → Pre-cache genealogy

**Technology**: PostgreSQL AGE (graph database) + Redis caching
**Architecture**: CONPORT-KG-2025 Phase 8 (Automation Layer)

---

### 4. ConPort KG UI ✅
**Path**: `services/conport_kg_ui/src/`
**Entry**: `App.tsx:18` (Main component)
**Type**: React Ink CLI (terminal UI)

**Components** (26 code chunks indexed):
- `App.tsx` - View routing (browser → explorer → viewer)
- `DecisionBrowser.tsx` - Top-3 ADHD pattern, keyboard navigation
- `GenealogyExplorer.tsx` - 1-hop/2-hop neighborhood visualization
- `DeepContextViewer.tsx` - Full decision context with cognitive load indicator

**Features**:
- ADHD-optimized (Top-3 display, progressive disclosure)
- Keyboard-first UI (↑↓ navigate, Enter select, 'q' quit)
- DopeconBridge client (HTTP API on port 3016)
- React Ink terminal rendering

**Technology**: React + Ink + TypeScript
**Quality**: Well-structured with proper error handling

---

### 5. Dope-Context ✅
**Path**: `services/dope-context/src/`
**Entry**: `mcp/server.py` (1170 lines)
**Type**: FastMCP server

**Features** (just audited and fixed!):
- AST-aware code chunking (Tree-sitter)
- Multi-vector embeddings (voyage-code-3)
- Hybrid search (dense + BM25 + RRF fusion)
- Neural reranking (Voyage rerank-2.5)
- Document search (voyage-context-3)
- Multi-project isolation (hash-based collections)

**MCP Tools**: 9 total
- index_workspace, search_code, docs_search, search_all
- sync_workspace, sync_docs
- get_index_status, clear_index

**Technology**: Qdrant + VoyageAI + Claude (context generation)
**Performance**: < 2s search latency, proper 700-char chunking ✅
**Recent Fixes**: Document chunking bug (447 → 4,413 chunks)

---

### 6. Dopemux GPT-Researcher ✅
**Path**: `services/dopemux-gpt-researcher/`
**Entry**: `backend/main.py`
**Type**: FastAPI microservice
**Port**: 8000 (default)

**Features**:
- Real-time progress streaming
- Pause/resume functionality
- ConPort memory integration
- Transparent planning phase
- Multi-search engine support

**Endpoints**:
- `GET /health`
- `POST /research/create`
- `GET /research/{task_id}/plan`
- `POST /research/{task_id}/execute/{question_index}`
- `WS /ws/progress/{user_id}` - WebSocket progress streaming

**Technology**: FastAPI + WebSockets + Search engines
**ADHD Features**: Progress streaming, pause/resume, session persistence

---

### 7. MCP DopeconBridge ⚠️
**Path**: `services/mcp-dopecon-bridge/`
**Entry**: `main.py` (large file, hit token limit)
**Type**: FastAPI coordination layer
**Port**: BASE+16 (3016 default)

**Purpose**: Cross-plane communication, authority enforcement, event routing

**Known Features** (from architecture audit):
- Authority middleware (`KGAuthorityMiddleware`)
- Multi-instance support
- PostgreSQL shared state
- Redis caching
- Port allocation

**Status**: ⚠️ **Implemented but disconnected** (services don't use it!)
**Finding**: Architecture violation - services bypass DopeconBridge

---

### 8. Task-Orchestrator ✅
**Path**: `services/task-orchestrator/`
**Entry**: `server.py` (522 lines, MCP wrapper)
**Type**: MCP server wrapping Kotlin application

**Features**:
- 37 specialized orchestration tools
- Dependency analysis with conflict detection
- Event emission to Redis event bus
- ADHD-friendly visualization (critical path, batches)
- Multi-instance coordination

**Orchestration Tools**:
- analyze_dependencies, detect_conflicts, resolve_conflict
- find_critical_path, batch_tasks, parallelize_tasks
- sequence_tasks, estimate_timeline, identify_blockers
- optimize_workflow

**Technology**: Python wrapper → Kotlin task-orchestrator (Java/.jar)
**ADHD Features**: Max 3 parallel tasks, conflict alerts, dependency viz
**Event Integration**: Redis Streams for coordination

---

### 9. Serena ✅
**Path**: `services/serena/`
**Entry**: `server.py` (MCP wrapper)
**Sub-version**: `v2/` directory (enhanced version)

**Features**:
- LSP functionality (code navigation, symbols, completion)
- Semantic code navigation
- Project context understanding
- Session persistence
- ADHD-optimized (max 10 results, progressive disclosure)

**Technology**: Python MCP wrapper for LSP servers
**Event Integration**: Redis event bus
**Version**: v2 active (Phase 2 enhancements complete)

---

### 10-12. Services Requiring Investigation

**ML Risk Assessment**: `services/ml-risk-assessment/`
**Orchestrator**: `services/orchestrator/src/main.py`
**Taskmaster**: `services/taskmaster/server.py`

**Action**: Deeper investigation needed in later phases

---

## Service Architecture Patterns

### By Technology Stack

**FastAPI Services** (4):
- ADHD Engine (8090)
- GPT-Researcher (8000)
- DopeconBridge (3016)
- (ML Risk Assessment - TBD)

**MCP Servers** (4):
- Dope-Context (FastMCP)
- Serena (MCP wrapper)
- Task-Orchestrator (MCP wrapper → Kotlin)
- Taskmaster (MCP)

**Python Modules** (2):
- ConPort KG (orchestrator module)
- Orchestrator (main module)

**UI Applications** (1):
- ConPort KG UI (React Ink)

---

### By Two-Plane Architecture

**PM Plane**:
- Taskmaster (PRD parsing)
- Task-Orchestrator (dependency analysis)
- (Leantime - external)

**Cognitive Plane**:
- Serena (LSP navigation)
- ConPort KG (decisions, knowledge graph)
- Dope-Context (semantic search)
- ADHD Engine (accommodations)

**Coordination Layer**:
- DopeconBridge (PORT+16) - ⚠️ **DISCONNECTED**

**Cross-Plane**:
- GPT-Researcher
- ML Risk Assessment

---

## Service Dependencies

### Database Dependencies

**PostgreSQL**:
- ConPort KG (AGE extension for graph)
- DopeconBridge (shared state)

**Redis**:
- ADHD Engine (user profiles, state)
- Serena (caching, navigation)
- Task-Orchestrator (event bus)
- DopeconBridge (caching)

**Qdrant**:
- Dope-Context (vector storage)

**SQLite**:
- ADHD Engine → ConPort direct writes (❌ VIOLATION)

---

### Event Bus Dependencies

**Redis Streams** (Event Bus):
- Task-Orchestrator (producer/consumer)
- Serena (producer/consumer)
- ADHD Engine (planned integration)
- DopeconBridge (coordinator)

**Status**: Event bus infrastructure exists, partial adoption

---

## Key Findings

### Architecture Compliance

✅ **Well-Designed**:
- Clear service boundaries
- Microservice architecture
- Event-driven coordination (designed)

⚠️ **Partially Implemented**:
- DopeconBridge exists but services bypass it
- Direct database access patterns (ADHD Engine → ConPort SQLite)
- Event bus partially adopted

❌ **Violations Found**:
- ADHD Engine direct ConPort database writes
- ConPort orchestrator not wired to DopeconBridge (TODOs)

### Service Maturity Levels

**Production-Ready** (4):
- Dope-Context ✅ (just fixed chunking bug)
- ConPort KG UI ✅ (well-structured React)
- ADHD Engine ✅ (FastAPI with proper lifecycle)
- Serena v2 ✅ (LSP with ADHD features)

**Functional But Disconnected** (2):
- DopeconBridge (exists, unused)
- ConPort Orchestrator (TODOs for bridge integration)

**Wrapper/Proxy Services** (2):
- Task-Orchestrator wrapper
- Serena wrapper

**Needs Investigation** (4):
- Claude-Context (legacy?)
- ML Risk Assessment
- Orchestrator
- Taskmaster

---

## Phase 1B Conclusion

**12 services cataloged** with varying maturity levels.

**Critical Architectural Finding**: DopeconBridge is implemented but disconnected from services, leading to authority boundary violations.

**Next Phase**: Map actual dependencies and config to verify architecture compliance.

---

**Phase 1B Complete** ✅
**Time**: ~20 minutes
**Next**: Phase 1C - Dependency & Config Mapping (30 min)
