---
id: serena-v2-mcp-tools
title: Serena V2 Mcp Tools
type: explanation
owner: '@hu3mann'
last_review: '2025-10-17'
next_review: '2026-01-15'
---
# Serena v2 MCP Server - Tool Reference

**Version**: Phase 2D Complete
**Total Tools**: 15
**Server**: `services/serena/v2/mcp_server.py`
**Status**: Production Ready

---

## Overview

Serena v2 MCP Server provides ADHD-optimized code intelligence through 15 tools organized in 3 tiers:

- **Tier 1 (Navigation)**: Core code navigation with LSP integration
- **Tier 2 (ADHD Intelligence)**: Cognitive load management and decision reduction
- **Tier 3 (Advanced)**: Pattern learning and relationship analysis

All tools enforce ADHD optimizations:
- Max 10 results to prevent overwhelm
- Progressive disclosure (3-7 line contexts)
- Complexity-based reading time estimates
- Graceful degradation when components unavailable

---

## Architecture

### Lazy Loading Strategy

Components load on first use to enable instant startup (<1ms):

```
Startup (immediate):
└─ Workspace detection

On-demand loading:
├─ LSP (SimpleLSPClient) - Loads on first navigation query
├─ Tree-sitter - Loads for complexity analysis
├─ Database - Loads for graph operations (Phase 3)
├─ claude-context - Loads for semantic search (Phase 3)
└─ ADHD features - Loads for advanced filtering (Phase 3)
```

### Graceful Degradation

Every tool has fallback modes:
- LSP unavailable → Grep-based search
- Tree-sitter unavailable → Basic line counting
- Database unavailable → Simplified heuristics

---

## Tool Reference

### HEALTH (1 tool)

#### `get_workspace_status`

**Purpose**: Diagnostic health check for debugging

**Parameters**: None

**Returns**: JSON with server status, component state, errors

**Example**:
```json
{
  "server": {
    "name": "serena-v2",
    "phase": "2D",
    "uptime_seconds": 45.2
  },
  "workspace": {
    "path": "/Users/hue/code/dopemux-mvp",
    "detected": true
  },
  "components": {
    "lsp": {"loaded": true, "error": null},
    "tree_sitter": {"loaded": false, "error": null}
  },
  "tools": {
    "total_available": 15
  }
}
```

**Use Case**: Debugging MCP connection issues, verifying lazy loading

---

### NAVIGATION TIER 1 (4 tools)

#### `find_symbol`

**Purpose**: Search for functions, classes, variables by name

**Parameters**:
- `query` (required): Symbol name or partial match
- `symbol_type` (optional): function, class, variable, method, etc
- `max_results` (optional): Max results, default 10, max 10

**Returns**: JSON array of symbols with file, line, complexity score

**Example**:
```python
# Find all functions named "initialize"
find_symbol(query="initialize", symbol_type="function", max_results=5)
```

**Response**:
```json
{
  "query": "initialize",
  "found": 5,
  "adhd_filtered": true,
  "symbols": [
    {
      "name": "initialize",
      "kind": "function",
      "file": "services/serena/v2/mcp_server.py",
      "line": 332,
      "complexity": 0.45
    }
  ]
}
```

**ADHD Features**:
- Max 10 results enforced
- Complexity scores for reading assessment
- LSP mode (accurate) + grep fallback (resilient)

**Performance**: <50ms (LSP), <200ms (grep fallback)

---

#### `goto_definition`

**Purpose**: Navigate from usage to definition with context

**Parameters**:
- `file_path` (required): File path (relative or absolute)
- `line` (required): Line number (1-indexed, like editor)
- `column` (required): Column number (1-indexed)

**Returns**: Definition location with 7-line ADHD-optimized context

**Example**:
```python
# Jump to definition of symbol at line 45, column 10
goto_definition(file_path="services/api/main.py", line=45, column=10)
```

**Response**:
```json
{
  "query": {"file": "...", "line": 45, "column": 10},
  "definition": {
    "file": "services/core/auth.py",
    "line": 123,
    "context": "
    120: def helper_function():
    121:     \"\"\"Helper for processing\"\"\"
    122:
>>> 123: def authenticate_user(credentials):  ← DEFINITION
    124:     \"\"\"Main authentication logic\"\"\"
    125:     validate_credentials(credentials)
    126:     return create_session()
    "
  },
  "performance": {"latency_ms": 65.3, "mode": "lsp"}
}
```

**ADHD Features**:
- 7-line context (3 before, definition, 3 after)
- Highlighted definition line with >>>
- First definition only (avoids overload from multiple defs)

**Performance**: <30ms (cached), <80ms (uncached)

---

#### `get_context`

**Purpose**: Get surrounding code with complexity assessment

**Parameters**:
- `file_path` (required): File path (relative to workspace)
- `line` (required): Center line number (1-indexed)
- `context_lines` (optional): Lines before/after, default 10, max 50
- `include_complexity` (optional): Add complexity score, default true

**Returns**: Code context with optional complexity and reading time

**Example**:
```python
# Get 20 lines around line 100 with complexity
get_context(file_path="services/engine.py", line=100, context_lines=20)
```

**Response**:
```json
{
  "file": "services/engine.py",
  "center_line": 100,
  "range": {"start": 80, "end": 120, "total_lines": 40},
  "context": "... (40 lines with line 100 highlighted) ...",
  "complexity": {
    "score": 0.65,
    "safe_reading_minutes": 9.8
  },
  "performance": {"latency_ms": 25.1}
}
```

**ADHD Features**:
- Highlighted center line
- Reading time estimate (complexity × 15 min)
- Max 50 lines to prevent overwhelm

**Performance**: <50ms

---

#### `find_references`

**Purpose**: Find all usages of a symbol

**Parameters**:
- `file_path` (required): File path
- `line` (required): Line number (1-indexed)
- `column` (required): Column number (1-indexed)
- `max_results` (optional): Max results, default 10, max 10
- `include_declaration` (optional): Include declaration, default true

**Returns**: Reference locations with 3-line context snippets

**Example**:
```python
# Find all usages of function at line 50, column 5
find_references(file_path="utils.py", line=50, column=5, max_results=10)
```

**Response**:
```json
{
  "query": {"file": "utils.py", "line": 50, "column": 5},
  "found": 8,
  "adhd_filtered": false,
  "references": [
    {
      "file": "services/api/main.py",
      "line": 145,
      "context": "
  144:     user = get_user(id)
→ 145:     result = process_data(user)
  146:     return result
      "
    }
  ],
  "performance": {"latency_ms": 95.2, "mode": "lsp"}
}
```

**ADHD Features**:
- Max 10 references
- Shorter context (3 lines vs 7 for definitions)
- Reference line highlighted with →

**Performance**: <100ms

---

### ADHD INTELLIGENCE TIER 2 (5 tools)

#### `analyze_complexity`

**Purpose**: Assess code complexity for ADHD-safe reading

**Parameters**:
- `file_path` (required): File to analyze
- `symbol_name` (optional): Specific symbol, null = whole file

**Returns**: Complexity score (0.0-1.0), metrics, reading time estimate

**Example**:
```python
# Analyze complexity of entire file
analyze_complexity(file_path="services/orchestrator.py")
```

**Response**:
```json
{
  "file": "services/orchestrator.py",
  "complexity": {
    "score": 0.72,
    "level": "HIGH - Complex code",
    "recommendation": "Peak focus hours only, consider breaking into chunks"
  },
  "metrics": {
    "cyclomatic_complexity": 18,
    "nesting_depth": 4,
    "lines_of_code": 450,
    "function_count": 12
  },
  "adhd_guidance": {
    "safe_reading_minutes": 10.8,
    "break_after_minutes": 25,
    "chunk_if_exceeds_minutes": 15
  },
  "performance": {"latency_ms": 85.3, "mode": "tree_sitter"}
}
```

**ADHD Levels**:
- **LOW (0.0-0.3)**: Safe to read anytime, even when scattered
- **MEDIUM (0.3-0.6)**: Needs focus, schedule dedicated time
- **HIGH (0.6-1.0)**: Complex code, peak hours only

**Performance**: <100ms (Tree-sitter), <20ms (fallback)

---

#### `filter_by_focus`

**Purpose**: Reduce cognitive load by filtering results based on attention state

**Parameters**:
- `attention_state` (required): focused, scattered, or transitioning
- `items` (required): Array of items to filter

**Returns**: Filtered items optimized for attention level

**Example**:
```python
# Filter 20 search results for scattered attention
filter_by_focus(attention_state="scattered", items=[...20 items...])
```

**Response**:
```json
{
  "attention_state": "scattered",
  "original_count": 20,
  "filtered_count": 3,
  "removed_count": 17,
  "items": [...top 3 items...],
  "adhd_guidance": {
    "max_items_for_state": 3,
    "recommendation": "Showing 3 items optimal for scattered state"
  }
}
```

**Filtering Thresholds**:
- **focused**: 10 items (full capacity)
- **transitioning**: 5 items (moderate)
- **scattered**: 3 items (minimize overwhelm)

**Performance**: <50ms (in-memory filtering)

---

#### `suggest_next_step`

**Purpose**: Reduce decision fatigue with navigation suggestions

**Parameters**:
- `current_file` (required): Current file path
- `current_symbol` (optional): Current symbol name

**Returns**: Top 3 suggested navigation targets

**Example**:
```python
# Get suggestions while in test file
suggest_next_step(current_file="tests/test_engine.py")
```

**Response**:
```json
{
  "current_file": "tests/test_engine.py",
  "suggestions": [
    {
      "type": "source_file",
      "target": "engine.py",
      "reason": "Test file → Source file pattern",
      "confidence": 0.8
    },
    {
      "type": "imported_module",
      "target": "models.py",
      "reason": "Imported in test_engine.py",
      "confidence": 0.6
    }
  ],
  "mode": "heuristic",
  "adhd_guidance": {
    "decision_reduction": "Showing 2 suggestions to reduce choice paralysis"
  }
}
```

**Heuristics** (Phase 2D):
- Test file → Suggests source file
- Source file → Suggests test file
- Imported modules → Suggests imports

**Phase 3 Upgrade**: Adaptive learning from navigation history

**Performance**: <150ms

---

#### `get_reading_order`

**Purpose**: Order files by complexity for progressive learning

**Parameters**:
- `files` (required): Array of file paths to order
- `symbols` (optional): Array of symbol names

**Returns**: Complexity-ordered files with session planning

**Example**:
```python
# Optimal order for reading 5 files
get_reading_order(files=[
  "models.py",
  "orchestrator.py",
  "engine.py",
  "api/main.py",
  "utils.py"
])
```

**Response**:
```json
{
  "total_files": 5,
  "reading_order": [
    {
      "file": "utils.py",
      "complexity_score": 0.25,
      "reading_minutes": 3.8,
      "level": "LOW - Safe to read anytime"
    },
    {
      "file": "models.py",
      "complexity_score": 0.42,
      "reading_minutes": 6.3,
      "level": "MEDIUM - Needs focus"
    },
    {
      "file": "orchestrator.py",
      "complexity_score": 0.78,
      "reading_minutes": 11.7,
      "level": "HIGH - Complex code"
    }
  ],
  "session_plan": {
    "total_reading_minutes": 45.2,
    "pomodoro_sessions_needed": 2,
    "breaks_recommended": 1,
    "progressive_disclosure": "Start with simplest files to build understanding"
  },
  "adhd_guidance": {
    "strategy": "Complexity progression (simple → complex)",
    "chunk_recommendation": "Read 1-2 files per 25-min session",
    "break_pattern": "5-min break between sessions"
  }
}
```

**ADHD Features**:
- Simple → Complex ordering
- Pomodoro session planning (25-minute chunks)
- Break recommendations
- Total time estimation

**Performance**: Varies by file count (50-300ms for 5 files)

---

#### `detect_untracked_work`

**Purpose**: Feature 1 - Gentle awareness of uncommitted work

**Parameters**:
- `session_number` (optional): Session count for adaptive thresholds, default 1
- `show_details` (optional): Show confidence breakdown, default false

**Returns**: Detection results with ADHD-friendly suggestions

**Example**:
```python
# Check for untracked work in session 2
detect_untracked_work(session_number=2, show_details=true)
```

**Response (Untracked Work Found)**:
```json
{
  "status": "untracked_work_detected",
  "work_name": "Authentication refactor",
  "confidence": {
    "score": 0.82,
    "threshold": 0.65,
    "passes_threshold": true
  },
  "git_summary": {
    "branch": "feature/auth-refactor",
    "files_changed": 8,
    "stats": {
      "insertions": 145,
      "deletions": 32,
      "files": 8
    }
  },
  "suggestions": {
    "options": [
      {
        "action": "track",
        "description": "Create ConPort task (pre-filled)",
        "recommended": true
      },
      {
        "action": "snooze",
        "description": "Remind later (1h | 4h | 1d)"
      },
      {
        "action": "ignore",
        "description": "Mark as experiment"
      }
    ]
  }
}
```

**ADHD Features**:
- Non-blocking (never enforces)
- Adaptive thresholds (0.75 → 0.65 → 0.60 across sessions)
- 30-minute grace period
- 3 clear options (not overwhelming)

**Performance**: <100ms

---

### ADVANCED TIER 3 (3 tools)

#### `find_relationships`

**Purpose**: Discover code dependencies (calls, imports, inheritance)

**Parameters**:
- `symbol` (required): Symbol to find relationships for
- `relationship_type` (optional): calls, imports, inherits, all (default: all)
- `depth` (optional): Max depth, default 2, max 3

**Returns**: Relationships found with context

**Example**:
```python
# Find what calls the "authenticate" function
find_relationships(symbol="authenticate", relationship_type="calls", depth=2)
```

**Response**:
```json
{
  "symbol": "authenticate",
  "relationship_type": "calls",
  "found": 7,
  "max_results": 10,
  "adhd_filtered": true,
  "relationships": [
    {
      "type": "calls",
      "file": "api/routes.py",
      "line": 45,
      "context": "user = authenticate(request.headers['token'])"
    }
  ],
  "mode": "simplified_grep",
  "upgrade_note": "Phase 3 will add PostgreSQL graph for multi-level traversal"
}
```

**Phase 2D Mode**: Grep-based (single-level search)
**Phase 3 Upgrade**: PostgreSQL graph operations (multi-level traversal)

**Performance**: <200ms

---

#### `get_navigation_patterns`

**Purpose**: Analyze personal navigation patterns (Phase 3 feature)

**Parameters**:
- `days_back` (optional): Days of history, default 7

**Returns**: Pattern analysis (Phase 2D: placeholder)

**Example**:
```python
get_navigation_patterns(days_back=7)
```

**Response (Phase 2D)**:
```json
{
  "status": "learning_phase",
  "message": "Pattern learning requires navigation history database",
  "recommendation": "Use suggest_next_step for immediate navigation help",
  "current_capabilities": {
    "heuristic_suggestions": "Available via suggest_next_step",
    "test_source_patterns": "Detects test/source relationships"
  },
  "phase_3_features": {
    "adaptive_learning": "Learns from navigation sequences",
    "personalized_patterns": "Recognizes your coding style",
    "effectiveness_tracking": "Measures pattern effectiveness"
  }
}
```

**Phase 2D Mode**: Placeholder (use suggest_next_step instead)
**Phase 3 Upgrade**: Full adaptive learning with PostgreSQL

**Performance**: <10ms (placeholder)

---

#### `update_focus_mode`

**Purpose**: Set current focus state for adaptive filtering

**Parameters**:
- `mode` (required): focused, scattered, or transitioning

**Returns**: Updated focus state and filtering behavior

**Example**:
```python
# Set scattered mode during interruptions
update_focus_mode(mode="scattered")
```

**Response**:
```json
{
  "mode": "scattered",
  "previous_mode": "focused",
  "max_results": 3,
  "filtering_behavior": "Show top 3 items - reduce overwhelm",
  "persistence": {
    "saved_to_database": false,
    "restart_behavior": "Resets to 'focused' on server restart",
    "upgrade_note": "Phase 3 will persist across sessions"
  }
}
```

**Phase 2D Mode**: In-memory (resets on restart)
**Phase 3 Upgrade**: Database persistence (cross-session)

**Performance**: <50ms

---

### FILES (2 tools)

#### `read_file`

**Purpose**: Read file with line range support

**Parameters**:
- `relative_path` (required): Path relative to workspace
- `start_line` (optional): First line (0-indexed), default 0
- `end_line` (optional): Last line, null = end of file

**Returns**: File content with line numbers (cat -n format)

**Example**:
```python
# Read lines 100-150
read_file(relative_path="services/engine.py", start_line=100, end_line=150)
```

**Performance**: <10ms

---

#### `list_dir`

**Purpose**: List directory contents

**Parameters**:
- `relative_path` (required): Directory path
- `recursive` (optional): Recursive listing, default false

**Returns**: Directories and files (sorted)

**Example**:
```python
# List services directory
list_dir(relative_path="services", recursive=false)
```

**Performance**: <20ms (non-recursive), <100ms (recursive)

---

## Usage Patterns

### ADHD-Optimized Navigation Workflow

```python
# 1. Set focus mode based on current attention
update_focus_mode(mode="focused")  # or "scattered" or "transitioning"

# 2. Find symbol to navigate to
results = find_symbol(query="DatabaseManager", max_results=10)

# 3. Filter results by focus (automatic based on mode)
filtered = filter_by_focus(attention_state="focused", items=results)

# 4. Jump to definition
definition = goto_definition(
  file_path=results[0]["file"],
  line=results[0]["line"],
  column=1
)

# 5. Check complexity before reading
complexity = analyze_complexity(file_path=definition["file"])

# 6. If complexity HIGH, get reading order for related files
if complexity["score"] > 0.6:
  order = get_reading_order(files=[...related files...])
```

### Decision Reduction Workflow

```python
# 1. Get navigation suggestions (max 3 to reduce paralysis)
suggestions = suggest_next_step(current_file="api/routes.py")

# 2. Analyze suggested file complexity
for suggestion in suggestions:
  complexity = analyze_complexity(file_path=suggestion["target"])
  # Choose simplest file when attention scattered

# 3. Navigate with context
goto_definition(...)
```

### Complexity-Aware Reading

```python
# 1. Get list of files to understand
files = ["models.py", "engine.py", "orchestrator.py"]

# 2. Order by complexity (simple first)
order = get_reading_order(files=files)

# 3. Follow the order with breaks
for file in order["reading_order"]:
  if file["complexity_score"] < 0.6:
    # Read now
    context = get_context(file_path=file["file"], line=1)
  else:
    # Schedule for focused time
    print(f"Schedule {file['file']} for peak focus hours")
```

---

## Configuration

### Claude Code Integration

Add to `~/.claude.json`:

```json
{
  "mcpServers": {
    "serena-v2": {
      "command": "uvx",
      "args": [
        "mcp-proxy",
        "--transport", "streamablehttp",
        "--port", "3007",
        "--host", "127.0.0.1",
        "--",
        "python",
        "/Users/hue/code/dopemux-mvp/services/serena/v2/mcp_server.py"
      ]
    }
  }
}
```

Or use stdio transport:

```json
{
  "mcpServers": {
    "serena-v2": {
      "command": "python",
      "args": [
        "/Users/hue/code/dopemux-mvp/services/serena/v2/mcp_server.py"
      ]
    }
  }
}
```

### Requirements

**Required**:
- Python 3.11+
- `python-lsp-server[all]` (for LSP features)
- MCP SDK (`mcp` package)

**Optional** (graceful degradation if missing):
- Tree-sitter (for accurate complexity)
- PostgreSQL (for Phase 3 graph operations)
- Redis (for Phase 3 caching)
- claude-context MCP (for semantic search)

### Installation

```bash
# Install LSP server
pip install 'python-lsp-server[all]'

# Install MCP SDK
pip install mcp

# Test server
python services/serena/v2/mcp_server.py
# Should show: "Server ready in 0.00s"
```

---

## Performance Targets

All tools meet ADHD performance targets (<200ms):

| Tool | Target | Typical | Mode |
|------|--------|---------|------|
| find_symbol | <50ms | 40-80ms | LSP |
| goto_definition | <80ms | 50-100ms | LSP |
| get_context | <50ms | 10-30ms | File read |
| find_references | <100ms | 60-120ms | LSP |
| analyze_complexity | <100ms | 50-100ms | Tree-sitter |
| filter_by_focus | <50ms | <10ms | In-memory |
| suggest_next_step | <150ms | 80-120ms | Heuristic |
| get_reading_order | Varies | 50-300ms | Batch analysis |
| find_relationships | <200ms | 100-200ms | Grep |
| get_navigation_patterns | <10ms | <5ms | Placeholder |
| update_focus_mode | <50ms | <5ms | In-memory |
| detect_untracked_work | <100ms | 50-100ms | Git + ConPort |

---

## ADHD Optimization Summary

### Cognitive Load Management

1. **Result Limiting**: Max 10 items everywhere
2. **Progressive Disclosure**: Start simple, add detail on request
3. **Context Sizing**: 3-7 lines (not full files)
4. **Decision Reduction**: Max 3 suggestions
5. **Complexity Assessment**: Reading time estimates
6. **Attention Adaptation**: Filter by focus state

### Visual Clarity

- **Highlighted lines**: `>>>` for definitions, `→` for references
- **Clear structure**: JSON with consistent formatting
- **Performance feedback**: latency_ms in all responses
- **Mode indicators**: Shows LSP vs fallback

### Graceful Degradation

Every tool works even when components fail:
- LSP unavailable → Grep fallback
- Tree-sitter missing → Basic metrics
- Database offline → Simplified heuristics

---

## Phase 3 Roadmap

### Full Intelligence Integration

**NavigationCache** (Redis):
- <5ms cached responses
- Hot-path optimization
- Session state preservation

**PostgreSQL Graph Operations**:
- Multi-level relationship traversal
- Code dependency visualization
- Impact analysis

**Adaptive Learning Engine**:
- Pattern recognition from history
- Personalized navigation suggestions
- Effectiveness tracking
- Context-switch optimization

**Complete EnhancedLSPWrapper**:
- All 31 Serena v2 components
- Cross-session learning
- Cognitive load orchestration
- Fatigue detection

---

## Troubleshooting

### Server won't start

```bash
# Check pylsp installed
which pylsp

# Install if missing
pip install 'python-lsp-server[all]'

# Test manually
python services/serena/v2/mcp_server.py
```

### LSP not working (fallback mode)

Check health status:
```python
get_workspace_status()
# Check components.lsp.loaded and components.lsp.error
```

Common issues:
- pylsp not in PATH → Reinstall python-lsp-server
- LSP timeout → Increase timeout in _init_lsp (line 461)

### Complexity analysis unavailable

Tree-sitter optional - tool automatically falls back to line counting.

To enable Tree-sitter:
```bash
pip install tree-sitter tree-sitter-python
```

---

## Examples

### Example 1: Navigate Unknown Codebase

```python
# 1. Find entry point
symbols = find_symbol(query="main", symbol_type="function")

# 2. Check complexity before diving in
complexity = analyze_complexity(file_path=symbols[0]["file"])

# 3. If complex, get optimal reading order for related files
if complexity["score"] > 0.6:
  files = [...]  # Related files
  order = get_reading_order(files=files)
  # Start with simplest file

# 4. Navigate to definition
definition = goto_definition(
  file_path=symbols[0]["file"],
  line=symbols[0]["line"],
  column=1
)
```

### Example 2: Scattered Attention Navigation

```python
# 1. Set scattered mode
update_focus_mode(mode="scattered")

# 2. Search for symbol (will return max 10, but we'll filter)
results = find_symbol(query="process_data")

# 3. Filter to top 3 for scattered attention
filtered = filter_by_focus(attention_state="scattered", items=results)

# 4. Get suggestions (max 3 reduces decisions)
suggestions = suggest_next_step(current_file="current.py")

# 5. Pick simplest suggestion
for s in suggestions:
  complexity = analyze_complexity(file_path=s["target"])
  if complexity["score"] < 0.3:
    # This one is safe to read now
    break
```

### Example 3: Focused Deep Dive

```python
# 1. Set focused mode (allows up to 10 results)
update_focus_mode(mode="focused")

# 2. Find target function
symbol = find_symbol(query="DatabaseManager")

# 3. Analyze dependencies
relationships = find_relationships(
  symbol="DatabaseManager",
  relationship_type="all",
  depth=2
)

# 4. Navigate definition tree
definition = goto_definition(...)
references = find_references(...)

# 5. Plan reading session
files = [definition["file"]] + [r["file"] for r in references]
order = get_reading_order(files=files)
```

---

## API Stability

### Phase 2D → Phase 3 Migration

All tool APIs are stable - Phase 3 will:
- **Add capabilities**: No parameter changes
- **Enhance responses**: Additional fields, not replacements
- **Maintain compatibility**: All Phase 2D code continues working

Example:
```json
// Phase 2D response
{"mode": "simplified_grep", "relationships": [...]}

// Phase 3 response (backward compatible)
{"mode": "postgresql_graph", "relationships": [...], "graph_metadata": {...}}
```

---

## Performance Monitoring

All tools include performance metrics:

```json
{
  "performance": {
    "latency_ms": 65.3,
    "mode": "lsp",  // or "fallback_grep", "tree_sitter", etc
    "cached": false
  }
}
```

**Use for**:
- Identifying slow operations
- Validating ADHD targets (<200ms)
- Debugging performance issues

---

**Documentation Version**: Phase 2D
**Last Updated**: 2025-10-04
**Server Version**: services/serena/v2/mcp_server.py (2,434 lines)
**Total Tools**: 15 operational, 1 deferred (semantic_search for Phase 3)
