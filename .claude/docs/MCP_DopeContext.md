# Dope-Context MCP - Semantic Code & Docs Search

**Provider**: Dopemux
**Purpose**: AST-aware code search and multi-format document search with ADHD optimizations
**Version**: v2.0 - Structure-Aware Chunking (2025-10-23)
**Status**: ✅ Fully Operational + Optimized

## Overview

Dope-Context provides unified semantic search across code and documentation using hybrid dense+sparse search with neural reranking. Built specifically for ADHD developers with progressive disclosure, complexity scoring, and cognitive load management.

## Core Capabilities

### 1. Code Search - AST-Aware Semantic Retrieval
**Tool**: `mcp__dope-context__search_code`

**Features**:
- **AST-Aware Chunking**: Tree-sitter parses code into functions/classes/methods
- **Complexity Scoring**: 0.0-1.0 cognitive load assessment per chunk
- **Multi-Vector Embeddings**: Content + title + breadcrumb (Voyage voyage-code-3)
- **Hybrid Search**: Dense (semantic) + BM25 (keyword) with RRF fusion
- **Neural Reranking**: Voyage rerank-2.5 for top-10 precision
- **Context Generation**: gpt-5-mini generates 2-3 sentence descriptions

**Search Profiles**:
- `implementation`: Finding code examples (weights: 0.7/0.2/0.1)
- `debugging`: Error patterns and handlers (weights: 0.5/0.3/0.2)
- `exploration`: Broad discovery (weights: 0.4/0.4/0.2)

**Parameters**:
- `query`: Natural language search ("OAuth authentication flow")
- `top_k`: Results to return (default 10, max 50 for ADHD)
- `profile`: Search profile (default: "implementation")
- `use_reranking`: Enable Voyage rerank (default: True)
- `filter_language`: Filter by language (python, javascript, typescript)
- `workspace_path`: Auto-detects workspace from cwd if not provided (worktree-aware)

**Example**:
```python
mcp__dope-context__search_code(
    query="authentication middleware session management",
    top_k=5,
    profile="implementation"
)
```

**Returns**:
```python
[{
    "file_path": "/path/to/file.ts",
    "function_name": "authMiddleware",
    "language": "ts",
    "code": "...",  # Full code chunk
    "context": "Middleware that validates JWT tokens...",  # gpt-5-mini description
    "relevance_score": 0.73,
    "complexity": 0.42  # ADHD cognitive load score
}]
```

### 2. Documentation Search - Multi-Format Retrieval ✨ OPTIMIZED
**Tool**: `mcp__dope-context__docs_search`

**Features**:
- **Multi-Format**: PDF, Markdown, HTML, DOCX, plain text
- **✨ STRUCTURE-AWARE CHUNKING**: Markdown chunks by sections (not arbitrary chars!)
- **Hierarchy Preservation**: Parent headers included for context
- **Complexity Scoring**: 0.0-1.0 ADHD cognitive load per chunk
- **Section Metadata**: hierarchy, level, type, parent path
- **Smart Breadcrumbs**: "Main > Subtopic > Detail" instead of just filename
- **Token Validation**: Auto-splits chunks >8K tokens for Voyage compatibility
- **Contextualized Embeddings**: voyage-context-3 for document understanding
- **Enhanced Multi-Vector**: Content + title + hierarchy-based breadcrumb

**Parameters**:
- `query`: Natural language ("architecture decision records")
- `top_k`: Results (default 10)
- `filter_doc_type`: Optional filter (md, pdf, html, txt)
- `workspace_path`: Auto-detects if not provided (worktree-aware)

**Example**:
```python
mcp__dope-context__docs_search(
    query="two-plane architecture coordination patterns",
    top_k=3,
    filter_doc_type="md"
)
```

**Returns**:
```python
[{
    "source_path": "/path/to/doc.md",
    "text": "...chunk text...",
    "score": 0.56,
    "doc_type": "md"
}]
```

### 3. Unified Search - Code + Docs Together
**Tool**: `mcp__dope-context__search_all`

**Features**:
- **Parallel Search**: Searches both code and docs simultaneously
- **Result Fusion**: Combines and balances code + docs results
- **Complete Context**: Understand implementation with its documentation
- **Cross-Reference**: Verify code matches documented behavior

**Parameters**:
- `query`: Natural language
- `top_k`: Total results (split 50/50 between code and docs)
- `workspace_path`: Auto-detects

**Use Cases**:
- Feature exploration: Code alongside design docs
- Onboarding: Learn codebase with documentation
- Cross-reference: Validate implementation matches specs
- Complete context: Full picture of a feature

**Example**:
```python
mcp__dope-context__search_all(
    query="SuperClaude MCP integration patterns",
    top_k=10  # 5 code + 5 docs
)
```

### 4. Indexing Operations

**Code Indexing**: `mcp__dope-context__index_workspace`
```python
mcp__dope-context__index_workspace(
    workspace_path="/path/to/project",
    include_patterns=["*.py", "*.ts", "*.js", "*.tsx"],
    exclude_patterns=["*test*", "*node_modules*"],
    max_files=50  # Start small, no limit for full index
)
```

**Docs Indexing**: `mcp__dope-context__index_docs`
```python
mcp__dope-context__index_docs(
    workspace_path="/path/to/project",
    include_patterns=["*.md", "*.pdf"]
)
```

**Status Check**: `mcp__dope-context__get_index_status`
```python
mcp__dope-context__get_index_status()
# Returns collection info, vector counts, cost summary
```

**Clear Index**: `mcp__dope-context__clear_index`
```python
mcp__dope-context__clear_index()
# Deletes collection for re-indexing
```

### 5. Incremental Sync

**Code Sync**: `mcp__dope-context__sync_workspace`
- Detects added/modified/removed files using SHA256 snapshots
- Reports changes, doesn't auto-reindex
- Use to see what needs updating

**Docs Sync**: `mcp__dope-context__sync_docs`
- Same change detection for documents
- Incremental update capability

### 6. Autonomous Indexing ✨ NEW (Zero-Touch Operation)

**What**: Automatic file-watching and reindexing for code AND docs!

**Code Auto-Indexing**: `mcp__dope-context__start_autonomous_indexing`
```python
# Start watching code files
await mcp__dope-context__start_autonomous_indexing(
    debounce_seconds=5.0,      # Wait 5s after changes
    periodic_interval=600       # Fallback check every 10min
)
# Edit any .py/.ts/.js file → auto-indexed in 5s!
```

**Docs Auto-Indexing**: `mcp__dope-context__start_autonomous_docs_indexing`
```python
# Start watching documentation files
await mcp__dope-context__start_autonomous_docs_indexing(
    debounce_seconds=5.0,
    periodic_interval=600
)
# Edit any .md/.pdf file → auto-indexed in 5s!
```

**Check Status**: `mcp__dope-context__get_autonomous_status`
```python
status = await mcp__dope-context__get_autonomous_status()
# {
#   "summary": {
#     "code_active": 1,
#     "docs_active": 1
#   },
#   "code_controllers": [...],
#   "docs_controllers": [...]
# }
```

**Stop**: `stop_autonomous_indexing()` or `stop_autonomous_docs_indexing()`

**ADHD Benefits**:
- ✅ Zero manual intervention (no "did I reindex?" anxiety)
- ✅ Always current (search reflects latest edits)
- ✅ No cognitive overhead (happens automatically)
- ✅ Interrupt-safe (periodic fallback catches missed events)

**Architecture**:
```
Edit file → Watchdog detects → 5s debounce → Auto-reindex → Searchable!
                                     ↓
                             Periodic check (10min fallback)
```

## ADHD Optimizations

### Progressive Disclosure
```
Top 10 results shown immediately (prevents overwhelm)
↓
40 additional results cached (available on "show more")
↓
Full result set available if needed
```

### Complexity Scoring (AST-Aware for Code, Content-Aware for Docs)

**Code chunks** scored 0.0-1.0:
- Nesting depth (if/for/while inside if/for/while)
- Control flow complexity
- Function call density
- Cognitive load indicators

**Docs chunks** scored 0.0-1.0:
- Code blocks: +0.3 complexity
- Tables: +0.2
- Length: up to +0.3
- Technical density: +0.2 (CONSTANTS, API_NAMES)

**Complexity Scale**:
```
0.0-0.3: Low complexity (safe to read now)
0.3-0.6: Medium (needs focus)
0.6-1.0: High (schedule dedicated time)
```

**ADHD Benefit**: Know before reading if you have the mental bandwidth!

### Context Snippets
- gpt-5-mini generates 2-3 sentence descriptions
- Helps assess relevance without reading full code
- Reduces cognitive overhead of result scanning

### Max Results Enforcement
- Hard limit: 10 results per query (ADHD-safe)
- Can request up to 50 if needed
- Default: Conservative 10 to prevent choice paralysis

## Performance

### Indexing (Validated 2025-10-16)
- **50 Code Files**: ~15 minutes with context generation
- **428 Docs**: ~6 minutes
- **Cost**: $0.05 per 50 code files
- **Throughput**: 2-3 files/minute

### Search (Validated 2025-10-16)
- **Response Time**: < 2 seconds with reranking
- **Relevance**: 0.43-0.73 scores (good to excellent)
- **Cost Per Query**: $0.00 (vector search only)

### Workspace Isolation
- **Collection Naming**: `code_{md5_hash}`, `docs_{md5_hash}`
- **Example**: `code_3ca12e07` for `/Users/hue/code/dopemux-mvp`
- **Benefit**: No data leakage between projects

## Best Practices

### When to Search Code
```
BEFORE implementing:
- Find similar implementations
- Understand existing patterns
- Check architectural approach

DURING debugging:
- Locate error handling
- Find related code
- Understand call paths

WHEN refactoring:
- Find all related code
- Understand impact
- Locate dependencies
```

### When to Search Docs
```
BEFORE designing:
- Review ADRs
- Check established patterns
- Understand constraints

DURING planning:
- Find related features
- Check requirements
- Review decisions

WHEN onboarding:
- Understand architecture
- Learn conventions
- Read explanations
```

### When to Use Unified Search
```
FEATURE EXPLORATION:
- Code + design docs together
- Implementation + specifications
- Examples + explanations

CROSS-REFERENCING:
- Verify code matches docs
- Find documentation for code
- Find code implementing docs

LEARNING:
- Understand with context
- See theory + practice
- Complete picture
```

## Integration with SuperClaude Commands

Dope-Context enhances SuperClaude workflows:

- `/sc:implement` → Search for similar implementations before coding
- `/sc:troubleshoot` → Find error patterns and handlers
- `/sc:explain` → Search docs + code for complete understanding
- `/sc:improve` → Find high-complexity code needing refactoring
- `/sc:design` → Search ADRs and architecture docs before designing

## Cost Management

### Indexing Costs (One-Time Per Workspace)
- **Context Generation**: ~$0.001 per file (gpt-5-mini)
- **Embeddings**: ~$0.0004 per file (Voyage)
- **Total**: ~$0.001 per code file
- **Typical Workspace**: $0.20-$1.00 for 200-1000 files

### Operational Costs (Zero!)
- **Search**: $0.00 (vector search, no API calls)
- **Reranking**: Included in Voyage tier
- **Updates**: Only changed files re-indexed

### Budget-Friendly Tips
```
1. Skip context generation: Set skip_context_generation=True (saves 70% cost)
2. Index incrementally: Use sync tools to detect changes
3. Limit scope: Use include/exclude patterns wisely
4. Start small: Index 50-100 files first, expand as needed
```

## Troubleshooting

### MCP Timeout on Large Indexing
**Issue**: Indexing >100 files times out

**Solution**: Use direct Python scripts:
```bash
cd services/dope-context
python test_indexing.py      # For code (editable config inside)
python test_docs_indexing.py  # For docs
```

### Tree-Sitter Parse Errors
**Issue**: "Parse error for py: Parsing failed"

**Solution**: Upgrade tree-sitter
```bash
pip install --upgrade tree-sitter>=0.25.2
```

**Fallback**: System gracefully uses line-based chunking if tree-sitter fails

### Empty Docs Search Results
**Issue**: source_path and text fields empty

**Status**: Fix applied to `dense_search.py`, needs MCP restart
**Timeline**: Will work on next Claude Code session restart

### Large Docs Token Overflow
**Issue**: Some docs exceed 32K token limit

**Solution**: Already fixed with 8K token validation and auto-splitting
**Impact**: A few extra-large docs may skip (expected)

## Git Worktree Support

### Workspace Auto-Detection
Dope-Context automatically detects which git worktree you're in:
- Uses current working directory by default
- Searches code/docs within detected workspace only
- Each worktree maintains independent Qdrant collection
- Parallel indexing across multiple worktrees supported

### Worktree Workflows

**Index different worktrees independently:**
```python
# In worktree 1: /Users/hue/code/ui-build
mcp__dope-context__index_workspace()  # Indexes ui-build code

# In worktree 2: /Users/hue/code/backend-work
mcp__dope-context__index_workspace()  # Indexes backend-work code
```

**Search stays isolated to current worktree:**
```python
# Searches only within current worktree
mcp__dope-context__search_code(
    query="authentication flow"
)  # workspace_path auto-detected from cwd
```

**Cross-worktree search (manual):**
```python
# Explicitly search another worktree
mcp__dope-context__search_code(
    query="authentication flow",
    workspace_path="/Users/hue/code/ui-build"
)
```

### Collection Naming
- Pattern: `dopemux_code_{workspace_hash}` and `dopemux_docs_{workspace_hash}`
- Hash based on workspace absolute path
- Each worktree gets unique collections in Qdrant
- Main repo and worktrees have separate indexed content

### ADHD Benefits
- **Context Isolation**: Search results scoped to current work
- **No Interference**: ui-build search won't return main branch code
- **Parallel Work**: Multiple worktrees indexed simultaneously
- **Mental Clarity**: Physical directory = search boundary

## Requirements

### API Keys
- `VOYAGE_API_KEY`: Required for embeddings and reranking
- `OPENAI_API_KEY`: Optional for context generation (recommended)
- `ANTHROPIC_API_KEY`: Alternative for context generation

### Infrastructure
- **Qdrant**: Vector database (port 6333)
- **Python 3.11+**: With tree-sitter 0.25.2+
- **Disk Space**: ~100MB per 1000 indexed files

### Dependencies (requirements.txt)
```
tree-sitter>=0.25.2
tree-sitter-python==0.23.0
tree-sitter-javascript==0.23.0
tree-sitter-typescript==0.23.0
voyageai>=0.2.3
qdrant-client>=1.15.0
openai>=1.0.0
```

## Limitations

### Known Issues (Non-Blocking)
1. **MCP Timeout**: Large indexing operations (>100 files) timeout
   - Workaround: Use direct Python scripts
2. **Some Large Docs Skip**: Files >32K tokens after splitting
   - Impact: Minimal (only a few comprehensive technical docs)
3. **Docs Formatting**: Minor MCP response formatting issue
   - Status: Fixed, awaits server restart

### Performance Considerations
- **Indexing**: ~3-15 minutes depending on file count and context generation
- **First Search**: Slight delay for collection warm-up
- **Incremental Updates**: Only changed files re-indexed

## Example Workflows

### Initial Setup
```python
# 1. Index your code
mcp__dope-context__index_workspace(
    workspace_path="/your/project",
    include_patterns=["*.py", "*.ts"],
    max_files=50  # Start small
)

# 2. Index your docs
mcp__dope-context__index_docs(
    workspace_path="/your/project",
    include_patterns=["*.md"]
)

# 3. Check status
mcp__dope-context__get_index_status()
```

### Daily Development
```python
# Morning: Check for changes
mcp__dope-context__sync_workspace(workspace_path="/your/project")

# Find similar code before implementing
mcp__dope-context__search_code(
    query="authentication middleware patterns",
    profile="implementation"
)

# Debug an issue
mcp__dope-context__search_code(
    query="error handling connection timeout",
    profile="debugging"
)

# Learn about a feature
mcp__dope-context__search_all(
    query="two-plane architecture coordination"
)
```

### Code Review Prep
```python
# Find high-complexity code
mcp__dope-context__search_code(
    query="complex business logic calculations",
    profile="exploration"
)
# Review results with complexity > 0.6 for refactoring opportunities
```

---

## 🎓 Why Dope-Context for ADHD

### Before Dope-Context
```
grep -r "authentication" .
→ 847 results across 203 files
→ Overwhelming, can't process
→ Give up or spend hours manually filtering
```

### With Dope-Context
```
mcp__dope-context__search_code("authentication flow")
→ 5 most relevant results
→ Sorted by relevance
→ With context snippets
→ Complexity scores shown
→ Read top 2, implement
```

### ADHD Benefits
1. **Decision Reduction**: 5-10 results vs hundreds of grep matches
2. **Semantic Understanding**: Finds related code even without exact keywords
3. **Complexity Awareness**: Know what's "safe to read now" vs "schedule focus time"
4. **Context Preservation**: Descriptions help resume after interruptions
5. **Progressive Disclosure**: See essentials first, details on demand

---

**Status**: ✅ Fully validated (2025-10-16)
**Testing**: Comprehensive (see `services/dope-context/FINAL_TEST_REPORT.md`)
**Ready**: Production use with all ADHD optimizations operational
