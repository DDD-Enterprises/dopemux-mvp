# Dopemux Context Management

**Project**: Multi-language ADHD-optimized development platform
**Architecture**: Three-layer context system (Memory/Navigation/Retrieval)
**Documentation**: See `docs/DOPEMUX-CONTEXT-DEEP-DIVE.md` for comprehensive analysis

---

## Three-Layer Context Architecture

### Layer 1: ConPort (Memory & Knowledge Graph)

**Purpose**: Persistent memory and decision authority

**Capabilities**:
- Decision logging with full rationale (200+ decisions tracked)
- Progress tracking with ADHD metadata (complexity, energy, cognitive load)
- System pattern library (31+ reusable patterns)
- Active/product context with automatic 30s saves
- Knowledge graph with decision genealogy

**Performance**: 2-5ms queries (40-100x faster than ADHD targets)

**Key Tools**:
- `mcp__conport__log_decision` - Capture architectural decisions
- `mcp__conport__get_active_context` - Restore session state
- `mcp__conport__log_progress` - Track tasks with ADHD metadata
- `mcp__conport__semantic_search_conport` - Vector search across memory

**When to Use**:
- Session start: Restore where you left off
- Decision points: Log rationale for future reference
- Task tracking: Create progress with complexity/energy scores
- Pattern discovery: Search past decisions and solutions

---

### Layer 2: Serena (Navigation & Code Intelligence)

**Purpose**: LSP-powered code intelligence with adaptive learning

**Capabilities**:
- Multi-language LSP (Python/JS/TS/Rust/Go)
- Tree-sitter AST parsing for structural analysis
- Complexity scoring (0.0-1.0) for safe reading assessment
- Adaptive learning from navigation patterns
- Redis caching (1.18ms retrieval)

**Performance**: 78.7ms navigation (2.5x faster than ADHD targets)

**Key Tools**:
- `mcp__serena-v2__find_symbol` - Search functions/classes (max 10 results)
- `mcp__serena-v2__goto_definition` - Navigate to definition with context
- `mcp__serena-v2__find_references` - Find all usages (max 10, 3-line snippets)
- `mcp__serena-v2__analyze_complexity` - Get cognitive load score

**When to Use**:
- Code exploration: Find symbols and navigate structure
- Before reading: Check complexity score for cognitive readiness
- Understanding flow: Find references to see usage patterns
- Context gathering: Get surrounding code with annotations

---

### Layer 3: dope-context (Semantic Retrieval)

**Purpose**: Multi-index semantic search for code and documentation

**Capabilities**:
- 4 specialized indices (Code/Docs/API/Chat)
- Hybrid search (Dense + BM25 + RRF fusion + Reranking)
- Multi-vector embeddings (content/title/breadcrumb)
- Claude-generated contexts (35-67% quality improvement)
- Task profile-based retrieval (implementation/debugging/docs/learning)

**Performance**: <500ms code search, <1200ms with reranking

**Key Tools**:
- `mcp__dope-context__search_code` - Semantic code search with reranking
- `mcp__dope-context__docs_search` - Document search (PDF/Markdown/HTML)
- `mcp__dope-context__search_all` - Unified code + docs search
- `mcp__dope-context__index_workspace` - Index codebase for search

**When to Use**:
- Finding examples: Search for similar implementations
- Documentation lookup: Semantic doc search across formats
- Debugging: Search for error patterns and solutions
- Learning: Explore codebase with natural language queries

---

## Context Flow Patterns

### 1. Session Start (Context Restoration)
```
ConPort.get_active_context() → Current focus, sprint, mode
ConPort.get_recent_activity_summary() → Last 24h changes
Serena → Restore cursor positions and file context
dope-context → Pre-warm cache with recent searches
```

### 2. Code Navigation
```
Query: "Find authentication implementation"
→ ADHD Engine: Detect attention state (focused/scattered)
→ dope-context.search_code() → Top 10 semantic results
→ Serena.find_symbol() + goto_definition() → LSP navigation
→ Serena.analyze_complexity() → Cognitive load check
→ ConPort.log_pattern() → Learn from navigation
```

### 3. Implementation
```
ConPort.log_progress() → Create task with complexity
→ dope-context.search_code(profile="implementation") → Examples
→ Serena.find_references() → Usage patterns
→ Serena → Suggest related files from patterns
→ ConPort → Auto-save context every 30s
```

### 4. Debugging
```
ADHD Engine: Scattered attention detected
→ dope-context.search_code(profile="debugging") → Error handlers
→ Serena.analyze_complexity() → Find complex areas
→ ConPort.search_decisions_fts() → Related past fixes
→ Serena.find_references() → Call sites (max 10)
```

### 5. Decision Logging
```
ConPort.log_decision() → Summary + rationale + implementation
→ ConPort.link_conport_items() → Connect to related decisions
→ dope-context → Index decision for future search
→ Serena → Link decision to affected code files
```

### 6. Session End (Preservation)
```
ConPort.update_active_context() → Save current state
→ Serena → Persist navigation patterns to PostgreSQL
→ Serena → Update pattern learning models
→ dope-context → Save query history
```

---

## ADHD-Specific Accommodations

### Progressive Disclosure (Reduce Overload)
- **Max 10 results initially** (expandable to 50 cached)
- **3-level context depth** (prevents rabbit holes)
- **Complexity-first sorting** (simple code first)
- **Collapsed details** (expand on request)

### Attention State Adaptation
- **Focused (0.7-1.0)**: Full details, multiple options, comprehensive context
- **Scattered (0.3-0.6)**: Essential only, single path, minimal context
- **Transitioning (0.0-0.3)**: Cached results, no new exploration, gentle re-orientation

### Context Preservation (Zero Loss)
- **Auto-save every 30s** (no manual intervention)
- **Cross-session persistence** (resume exactly where left off)
- **Breadcrumb trails** (how you got to current location)
- **Decision rationale** (remember "why" decisions made)

### Energy-Aware Task Matching
- **High energy**: Complex refactoring, new features
- **Medium energy**: Bug fixes, code review
- **Low energy**: Documentation, simple edits
- Tasks tagged with energy requirements in ConPort

### Break Reminders (Hyperfocus Protection)
- **60-min soft warning** (suggest break)
- **90-min hard limit** (enforce break)
- **Pomodoro integration** (25-min focus sessions)
- **Context auto-saved** before breaks

### Visual Complexity Control
- **Minimal**: Essential info only
- **Standard**: Balanced detail
- **Comprehensive**: Full technical details
- **Adaptive**: Changes based on attention state

---

## Integration Points

### ConPort ↔ Serena (Bidirectional)
- Serena stores navigation patterns in ConPort
- ConPort decisions linked to code files via Serena
- Active context flows to Serena for personalization

### ConPort → dope-context (Unidirectional)
- dope-context indexes ConPort decisions
- Semantic search across 200+ decisions

### Serena → dope-context (Shared Infrastructure)
- dope-context uses Serena's Tree-sitter for AST chunking
- Serena's complexity scores feed dope-context ranking

### DopeconBridge (Cross-Plane)
- Coordinates ConPort (cognitive) with Leantime (PM plane)
- Port: PORT_BASE+16
- Enforces authority boundaries

### ADHD Engine (State Orchestrator)
- Detects attention state (focused/scattered/transitioning)
- Configures all three layers for optimal cognitive load
- Adjusts save frequency, result limits, disclosure levels

---

## Performance Summary

| Component | Metric | ADHD Target | Actual | Multiplier |
|-----------|--------|-------------|--------|------------|
| ConPort | Query Speed | 200ms | 2-5ms | 40-100x faster |
| ConPort | Context Restore | 500ms | <100ms | 5x faster |
| Serena | Navigation | 200ms | 78.7ms | 2.5x faster |
| Serena | Cache Retrieval | 50ms | 1.18ms | 42x faster |
| dope-context | Code Search | 1000ms | <500ms | 2x faster |
| dope-context | With Reranking | 2000ms | <1200ms | 1.7x faster |

**All performance targets exceeded** - System optimized for ADHD attention compliance

---

**Goal**: Seamless context transitions with minimal cognitive load
**Method**: Three-layer preservation with attention-aware adaptation
**Storage**: ConPort (persistent), Serena (PostgreSQL), dope-context (Qdrant)
**Cost**: <$0.25 per project for full context intelligence

**See Also**: `docs/DOPEMUX-CONTEXT-DEEP-DIVE.md` for comprehensive analysis
