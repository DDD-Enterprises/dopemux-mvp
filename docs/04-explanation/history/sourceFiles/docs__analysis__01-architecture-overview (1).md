# Dopemux Orchestration System - Architecture Overview

## Executive Summary

The Dopemux orchestration system integrates multiple PM tools, memory layers, and role-based workflows to create an ADHD-optimized development platform. The architecture supports seamless context switching, progressive disclosure, and intelligent task decomposition across multiple client interfaces.

## Core Components

### 1. PM Layer (Project Management Truth)

```
Leantime (MySQL) ← sync ↔ Task-Orchestrator (AI Workspace) ← analysis → Task-Master (PRD Parser)
```

**Leantime** - Human-facing source of truth
- ADHD-optimized UI with neurodiversity accommodations
- MySQL backend with REST API
- Strategy → Plans → Projects → Milestones → Tasks hierarchy
- Handles user management, permissions, schedules

**Task-Orchestrator** - AI workspace bridge
- 37 MCP tools for Projects/Features/Tasks management
- 9 templates, 5 workflow prompts
- Dependency management with collision prevention
- Bidirectional sync with Leantime (external_id mapping)

**Task-Master** - Code-aware task generation
- PRD parsing into task proposals
- Codebase analysis when using Claude Code provider
- Research assistance and complexity analysis
- Feeds enriched tasks into Task-Orchestrator → Leantime

### 2. Memory & Retrieval Architecture

```
┌─ Redis Cache (Semantic) ─┐
│  ├─ Code Search ──────────┼─→ Claude-Context ──→ Milvus (Code Vectors)
│  ├─ Doc Search ──────────┼─→ Doc-Context ─────→ Milvus (Doc Vectors) + OpenSearch (BM25)
│  └─ Project Memory ──────┼─→ ConPort ──────────→ Neo4j (Knowledge Graph)
└───────────────────────────┘
```

**Claude-Context** (Existing)
- Semantic code search optimized for large repositories
- Milvus vector database for embeddings
- MCP-native with tools: search, get_context, refresh_index

**Doc-Context** (To Build)
- Document RAG with hybrid search architecture
- Dense: Milvus vectors with contextualized chunk embeddings (Voyage context-3)
- Sparse: OpenSearch/Meilisearch for BM25 full-text search
- Fusion: RRF (Reciprocal Rank Fusion) → Voyage rerank-2.5
- Tools: doc.search_hybrid, doc.get_snippets, doc.cite, doc.refresh_index

**ConPort** (Context Portal)
- Structured project memory as graph nodes
- Decision lineage, ADRs, component relationships
- User trait learning for ADHD accommodations
- Memory write-points during role transitions

**Redis Semantic Cache**
- Query embedding similarity matching
- Distance threshold-based cache hits
- Invalidation on document/code updates
- 60%+ hit rate target for repeated queries

### 3. Orchestration Layer

**MetaMCP** - Single MCP aggregation point
- Role-based workspace isolation
- Tool access control per development phase
- Rate limiting and authentication
- Unified MCP interface for all clients

**Tool Census Automation**
- MetaMCP.list_tools() → ConPort persistence
- Diff reports on configuration changes
- Role → tool access matrix maintenance
- MCP discovery primitive compliance

### 4. Client Integration Matrix

| Client | Connection | Use Case |
|--------|------------|----------|
| Claude Code | Native MCP | Interactive development, tool invocation |
| Codex CLI | stdio/http | Command-line automation, scripting |
| Dopemux CLI | MetaMCP | Agentic workflows, batch processing |
| tmux interface | Multi-pane | Long-running agents, session persistence |
| Zed (ACP) | Agent protocol | Chat-triggered workflows, hot agent swap |

### 5. Role Pipeline (13 Specialized Roles)

```
Product Owner → Researcher → Product Architect → Engineering Architect
  ↓
Planner → Task Planner → TDD Engineer → Implementer → Validator
  ↓
Docs Writer → PR/QA → Scrum Master
```

Each role configured with:
- **System Prompt** (20% context budget)
- **Tool Whitelist** (role-specific MCP tools)
- **Retrieval Policy** (dense vs sparse search weights)
- **Memory IO** (read/write checkpoints in ConPort)
- **Context Budget** (40% task, 30% retrieval, 10% memory)

## Key Architectural Decisions

### ✅ Validated Choices

1. **Keep All Three PM Tools**: Leantime (human truth), Task-Orchestrator (AI workspace), Task-Master (PRD analysis)
2. **Keep Claude-Context + ConPort**: Code retrieval vs structured project memory - different purposes
3. **Build Doc-Context MCP**: Mirror Claude-Context patterns for document RAG
4. **Use MetaMCP Aggregation**: Single point for role-based tool routing
5. **Hybrid Search Strategy**: Dense + sparse fusion with reranking
6. **Git Worktree Isolation**: Namespace collections/labels per {worktree_id}

### 🏗️ Implementation Phases

**Phase 1: Foundation** (Week 1)
- Docker compose with dopemux-net bridge
- Deploy datastores: Milvus, Redis, MySQL, Neo4j, OpenSearch
- Install Leantime with API access
- Basic MetaMCP setup

**Phase 2: Integration** (Week 2)
- Build Doc-Context MCP server
- Configure Task-Orchestrator templates
- Set up role-based MetaMCP workspaces
- Implement Leantime ↔ Task-Orchestrator sync

**Phase 3: Optimization** (Week 3-4)
- Tune semantic caching thresholds
- Add ADHD personalization layer (trait learning)
- Implement git worktree namespacing
- Add concurrency safety (idempotency keys, outbox pattern)

## Integration Patterns

### Cross-Client Invariants
- All clients access same tool surface via MetaMCP
- Docker user-defined bridge for service discovery
- Consistent MCP protocol (stdio/http) across interfaces
- Session state preserved across client switches

### Concurrency & Safety
- Idempotency keys on every write operation
- Transactional outbox for cross-datastore consistency
- Milvus consistency: bounded (dev loops) → strong (releases)
- Task-Orchestrator collision prevention for multi-agent scenarios

### ADHD Accommodations
- Progressive disclosure: essential info first, details on request
- Micro-wins: visible progress bars and checkpoints
- Context reduction: 25-minute task chunking
- Decision fatigue: maximum 3 options presented
- Trait learning: ConPort graph nodes adapt workflows

## Success Metrics

- **Retrieval Quality**: P@10 > 0.8 for code and document search
- **Response Latency**: < 200ms for hybrid search with reranking
- **Cache Efficiency**: > 60% hit rate on repeated queries
- **Role Handoffs**: < 5s transition time between pipeline stages
- **ADHD Support**: 25% reduction in context switches

## Risk Mitigation

1. **Start Single-Agent**: Validate architecture before scaling to multi-agent
2. **Bounded Consistency First**: Upgrade to strong consistency for critical workflows
3. **Circuit Breakers**: Fallback paths for each external service integration
4. **Comprehensive Logging**: Debug capabilities across all components
5. **Incremental Rollout**: Each phase delivers independent value

---

Generated: 2025-09-24
Status: Architecture validated through thinkdeep analysis
Next: Implementation Phase 1 foundation setup