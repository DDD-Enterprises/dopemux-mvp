# RFC-001: Dopemux Unified Memory Graph (ConPort + Milvus + SQL/Neo4j + Zep)

**Status**: Draft
**Date**: September 21, 2025
**Authors**: Dopemux Team

## Summary

Stand up a unified memory layer for Dopemux that:
- Exposes project memory (decisions, files, tasks, APIs, relationships) via ConPort (MCP server)
- Uses Milvus as a vector index for decisions, chats, files, tasks (semantic recall), while a relational/graph store is the source of truth for nodes/edges
- Provides conversational memory now with Zep (summaries + vector search + fact extraction)
- Keeps Letta for agent-level tiered memory (working/recall/archival) and persistence
- Aligns with our stated stack decisions: ConPort for project memory, Letta as the primary memory framework

## Motivation

- Agents and tools need consistent access to why decisions were made and what they affect. ConPort already provides "project memory and decision tracking" via MCP
- We've standardized on MCP servers; wiring memory through MCP keeps all clients (multi-LLM chat, Claude Code, Codex CLI, future orchestrators) portable
- Zep is a fast path to high-quality chat UX while we evolve the project graph

## Goals / Non-Goals

### Goals
1. Consolidate project memory behind ConPort MCP with SQL (now) → Neo4j (later)
2. Add Milvus for kNN search on decisions, messages, files, tasks
3. Use Zep to provide conversation summaries + retrieval in the multi-LLM chat window
4. Normalize a conversation schema that ingests Claude Code & Codex CLI histories into the graph + vector index

### Non-Goals
- Replace Letta: Letta remains the agent memory fabric (tiers, persistence)
- Use Milvus as a graph DB: it's the vector index, not the graph truth

## Design

### 1) Data Model (graph truth + vector recall)

**Nodes**: decision, task, file, endpoint, message, agent, thread, run
**Edges**: affects, depends_on, implements, discussed_in, produced_by, belongs_to_thread
**Truth store**: SQLite/Postgres now, Neo4j later for native graph queries
**Vector store**: Milvus collections per entity type; metadata back-refs to graph IDs

#### Milvus Collection Layout

```
collection: decisions | fields: id:string, ts:int, type:string, meta:json, embedding:FLOAT_VECTOR
collection: messages  | same fields
collection: files     | same fields (+path)
collection: tasks     | same fields
```

Using HNSW or IVF_FLAT; filters on ts/type/agent/repo

### 2) MCP Tooling (ConPort)

Add/confirm MCP tools on ConPort:
- `mem.upsert({type,id,text,metadata})` → write to SQL/Neo4j and embed+upsert to Milvus
- `mem.search({type?,query,filters?,k,with_rerank?})` → Milvus ANN + (optional) Voyage rerank
- `graph.link({from_id,to_id,rel})`, `graph.neighbors({id,depth,rel?})` → SQL now / Neo4j later

### 3) Conversational Memory (Zep + Letta)

- Zep stores chat turns, generates summaries, and supports vector queries for chat retrieval
- Letta remains the agent-tier memory (working/recall/archival) with persistent state and automated eviction/summarization under pressure

### 4) Orchestrator Integration (multi-LLM chat window)

- The multi-LLM pane is the entry point: every message.created → mem.upsert and optional graph.link
- Conversations flow into Zep for immediate UX; promoted artifacts (decisions/plans) are mirrored into ConPort's project graph

### 5) History Ingestion (Claude Code & Codex CLI)

Normalized JSONL:
```json
{"type":"message","id":"...","role":"user|assistant|tool","thread":"...","text":"...","ts":...,"source":"claude-code|codex-cli","meta":{...}}
{"type":"decision","id":"...","text":"...","links":[{"rel":"affects","to":"file:src/foo.ts"}],"ts":...}
```

Importer steps:
1. Parse logs → JSONL
2. For each line: mem.upsert (graphs & vectors); for decisions/files/tasks → graph.link

### 6) Observability & Data Lake Hooks

Emit OpenTelemetry events to Kafka; route to ClickHouse (realtime metrics), S3/Parquet (long-term chats), and Milvus (embeddings).

### 7) Security & Privacy

Namespaced graph IDs per repo/project, RBAC/ACLs at ConPort; encrypted Milvus and SQL at rest; redact secrets before upsert.

## Alternatives Considered

- **Milvus-only (no graph)**: rejected; hard to express traversals/impacts
- **Zep-only for both project + chat**: rejected; we need explicit graph relations and MCP-wide tools
- **Postpone Zep**: rejected; quick UX win now

## Rollout Plan (Phased)

- **Phase 1** (week 1): ConPort + SQLite truth; Milvus for vectors; Zep for chat; importers for Claude Code & Codex CLI
- **Phase 2**: Introduce graph.neighbors views in tmux panes; show "why/impact" next to code panes
- **Phase 3**: Migrate truth to Neo4j; enable richer queries and visual graph

## Test Plan

- **Unit**: tool contract tests for mem.upsert/search, graph.link/neighbors
- **Integration**: ingest a known decision → verify Milvus recall and graph traversal to affected files
- **E2E**: import a week of Claude Code logs; ask "why did we choose X?" → assert surfaced decision + linked PR/files

## API Sketches (for ConPort MCP)

### mem.upsert (request/response)
```json
// req
{"type":"decision","id":"dec_123","text":"Adopt pgvector for code index","metadata":{"repo":"dopemux","author":"hue","ts":1695250000}}
// res
{"ok":true,"id":"dec_123"}
```

### mem.search
```json
{"type":"decision","query":"pgvector code index","k":8,"filters":{"repo":"dopemux"}}
```

### graph.link
```json
{"from_id":"dec_123","to_id":"file:src/indexer.ts","rel":"affects"}
```

### graph.neighbors
```json
{"id":"dec_123","depth":2,"rel":"affects|discussed_in"}
```

## Minimal "Week 1" Tasks (runnable order)

1. Docker up: Milvus, Postgres/SQLite, Zep, ConPort (with new tools)
2. Implement mem.upsert/search, graph.link/neighbors in ConPort (SQL + Milvus)
3. Wire multi-LLM chat to emit message.created → Zep + ConPort
4. Import Claude Code & Codex CLI logs via JSONL → ConPort