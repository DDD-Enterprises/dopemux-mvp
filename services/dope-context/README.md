# Dope-Context - Semantic Code & Documentation Search

Dope-Context provides intelligent semantic search across codebases and documentation using advanced AI-powered retrieval. Optimized for ADHD developers with progressive disclosure, complexity scoring, and cognitive load management.

## 🎯 Overview

### Core Capabilities
- **AST-Aware Code Search**: Tree-sitter parsing for accurate code understanding
- **Semantic Documentation Search**: Multi-format document indexing (PDF, Markdown, HTML)
- **Autonomous Indexing**: Zero-touch background indexing with file watching
- **ADHD Optimization**: Complexity scoring and progressive disclosure for safe reading

### Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Code Search   │────│   Qdrant Vector  │────│  Documentation  │
│   (AST-aware)   │    │     Database     │    │    Search       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                       │
         ├─ Complexity Scoring    ├─ Voyage Embeddings   ├─ Multi-format
         ├─ Progressive Disclosure├─ Neural Reranking    ├─ Structure-aware
         └─ ADHD-safe Results     └─ Cache Optimization  └─ Chunking
```

## 🔍 Search APIs

### Code Search - `mcp__dope-context__search_code`

**Purpose**: Find relevant code using semantic understanding and AST analysis

**Parameters**:
- `query`: Natural language search query ("authentication middleware")
- `top_k`: Results to return (default: 10, max: 50)
- `profile`: Search profile (implementation/debugging/exploration)
- `filter_language`: Language filter (python/javascript/typescript)
- `workspace_path`: Auto-detects workspace
- `enrich_with_graph`: Include Serena relationship data

**Example**:
```python
mcp__dope-context__search_code(
    query="JWT authentication flow",
    top_k=5,
    profile="implementation"
)
```

**Response**:
```json
[{
  "file_path": "/path/to/auth.py",
  "function_name": "authenticate_user",
  "language": "python",
  "code": "...JWT validation code...",
  "context": "Validates JWT tokens with proper error handling",
  "relevance_score": 0.87,
  "complexity": 0.34,
  "relationships": {
    "callers": 3,
    "callees": 7,
    "impact_score": 0.72
  }
}]
```

### Documentation Search - `mcp__dope-context__docs_search`

**Purpose**: Search across documentation with structure-aware chunking

**Parameters**:
- `query`: Natural language query ("architecture patterns")
- `top_k`: Results to return (default: 10)
- `filter_doc_type`: File type filter (md/pdf/html/txt)
- `workspace_path`: Auto-detects workspace
- `max_content_length`: Content truncation limit

**Example**:
```python
mcp__dope-context__docs_search(
    query="two-plane architecture coordination",
    top_k=3,
    filter_doc_type="md"
)
```

**Response**:
```json
{
  "lane_used": "docs",
  "fusion_strategy": "dense",
  "rerank_used": false,
  "embed_model_used": "voyage-context-3",
  "timings_ms": {"embed": 12.0, "search": 8.0, "fuse": 0.0, "rerank": 0.0},
  "results": [{
    "rank": 1,
    "source_uri": "/docs/architecture.md",
    "source_path": "/docs/architecture.md",
    "snippet": "...coordination patterns between planes...",
    "text": "...coordination patterns between planes...",
    "score": 0.91,
    "doc_type": "md",
    "chunk_id": "docs/architecture.md::chunk::1"
  }]
}
```

### Unified Search - `mcp__dope-context__search_all`

**Purpose**: Search code + docs, with optional ConPort decision context

**Parameters**:
- `query`: Natural language query
- `top_k`: Total result budget
- `workspace_path`: Auto-detects workspace
- `include_decisions`: Include decision matches when configured (default `true`)

**Example**:
```python
mcp__dope-context__search_all(
    query="SuperClaude MCP integration patterns",
    top_k=10
)
```

**Response**:
```json
{
  "code_results": [...],
  "docs_results": [...],
  "decision_results": [...],
  "decision_search_enabled": true,
  "total_results": 10
}
```

### Decision Retrieval Config - `mcp__dope-context__configure_decision_auto_indexing`

**Purpose**: Configure workspace-scoped decision retrieval for `search_all`

**Parameters**:
- `workspace_path`: Target workspace
- `enabled`: Enable/disable decision retrieval
- `bridge_url`: Dopecon-bridge base URL (default `http://localhost:3016`)
- `decision_limit`: Max decision matches per unified search
- `auto_include_in_search_all`: Automatically include decisions in `search_all`

**Example**:
```python
mcp__dope-context__configure_decision_auto_indexing(
    workspace_path="/path/to/project",
    enabled=True,
    bridge_url="http://localhost:3016",
    decision_limit=6,
    auto_include_in_search_all=True
)
```

## 🏗️ Indexing Operations

### Code Indexing - `mcp__dope-context__index_workspace`

**Purpose**: Index codebase for semantic search

**Parameters**:
- `workspace_path`: Path to index
- `workspace_paths`: Optional list of workspaces to batch (sequential) index
- `include_patterns`: File patterns (default: code files)
- `exclude_patterns`: Files to exclude
- `max_files`: Limit for large repos

**Example**:
```python
mcp__dope-context__index_workspace(
    workspace_path="/path/to/project",
    include_patterns=["*.py", "*.ts"],
    max_files=1000
)
```

### Documentation Indexing - `mcp__dope-context__index_docs`

**Purpose**: Index documentation files

**Parameters**:
- `workspace_path`: Path to docs
- `workspace_paths`: Optional list of workspaces to process in one call
- `include_patterns`: Doc patterns (default: md/pdf/html)

**Example**:
```python
mcp__dope-context__index_docs(
    workspace_path="/path/to/project",
    include_patterns=["*.md", "*.pdf"]
)
```

### Incremental Sync - `mcp__dope-context__sync_workspace/docs`

**Purpose**: Update indexes with file changes

**Parameters**:
- `workspace_path`: Path to sync
- `auto_reindex`: Automatically reindex changed files

## 🤖 Autonomous Indexing

### Background Code Indexing - `mcp__dope-context__start_autonomous_indexing`

**Purpose**: Zero-touch indexing with file watching

**Features**:
- File watcher detects changes immediately
- 5-second debouncing prevents excessive reindexing
- 10-minute periodic fallback
- ADHD-friendly: no manual intervention needed

Provide `workspace_paths` to enable watchers across multiple repositories/worktrees in one call.

**Example**:
```python
mcp__dope-context__start_autonomous_indexing(
    workspace_paths=[
        "/path/to/project",
        "/path/to/worktree-b"
    ],
    debounce_seconds=5,
    periodic_interval=600
)
```

### Background Docs Indexing - `mcp__dope-context__start_autonomous_docs_indexing`

**Purpose**: Autonomous documentation indexing

**Features**:
- Watches documentation files
- Automatic reindexing on changes
- Structure-aware chunking for better search

`workspace_paths` works here too, so you can monitor multiple docs directories per command.

```python
mcp__dope-context__start_autonomous_docs_indexing(
    workspace_paths=[
        "/path/to/project",
        "/path/to/worktree-b"
    ],
    debounce_seconds=5,
    periodic_interval=600
)
```

## 🚀 Startup Autoindex (Dopemux CLI)

`dopemux start`, `dopemux launch`, and `dopemux dope` trigger an autoindex bootstrap for the current workspace:

1. Batch bootstrap: `index_workspace` + `index_docs` (one-time per workspace snapshot by default)
2. Ongoing updates: `start_autonomous_indexing` + `start_autonomous_docs_indexing`

Control flags:

- `DOPEMUX_AUTO_INDEX_ON_STARTUP=0` disables startup trigger
- `DOPEMUX_AUTO_INDEX_DEBOUNCE_SECONDS` overrides watcher debounce (default `5.0`)
- `DOPEMUX_AUTO_INDEX_PERIODIC_SECONDS` overrides periodic fallback (default `600`)

## 🧱 Trinity Boundaries (Enforced)

- Search plane authority: code/docs retrieval, fusion, rerank, and search provenance
- Memory plane authority: decision lifecycle and decision truth records
- `search_all` decision integration is read-only enrichment via dopecon-bridge
- Decision enrichment defaults to Top-3 (`decision_limit=3`) and is clamped to max 10
- Unified search responses include `trinity_boundaries` metadata to expose effective rails

## 📊 Management APIs

### Index Status - `mcp__dope-context__get_index_status`

**Purpose**: Check indexing status and statistics

**Parameters**:
- `workspace_path`: Single workspace to inspect (defaults to current)
- `workspace_paths`: Optional list of workspaces for aggregated reporting

**Returns**:
```json
{
  "workspace_count": 2,
  "workspaces": [
    {
      "workspace": "/Users/hue/code/dopemux-mvp",
      "workspace_hash": "3ca12e07",
      "code_collection": {"status": "green", "total_vectors": 15432},
      "docs_collection": {"status": "green", "total_vectors": 2156},
      "snapshot": {"files_indexed": 1250, "total_chunks": 15432, "last_snapshot": "2025-01-31T10:30:00Z"}
    }
  ],
  "code_collections": {
    "workspace_hash": {
      "files_indexed": 1250,
      "last_updated": "2025-01-31T10:30:00Z",
      "total_chunks": 15432
    }
  },
  "docs_collections": {
    "workspace_hash": {
      "files_indexed": 89,
      "last_updated": "2025-01-31T10:25:00Z",
      "total_chunks": 2156
    }
  }
}
```

### Clear Indexes - `mcp__dope-context__clear_index`

**Purpose**: Reset indexes for fresh start

**Parameters**:
- `workspace_path`: Workspace whose indexes should be removed
- `target`: `"code"`, `"docs"`, or `"both"` (default `"code"`)

### Search Metrics - `mcp__dope-context__get_search_metrics`

**Purpose**: Analyze search usage patterns

**Returns**:
- Total searches performed
- Explicit vs implicit searches
- Scenario breakdown
- Tool usage statistics

## 🧠 ADHD Optimizations

### Complexity Scoring
**Code Complexity**: 0.0-1.0 scale based on AST analysis
- Nesting depth and control flow
- Function call density
- Cognitive load indicators

**Docs Complexity**: 0.0-1.0 scale based on content analysis
- Code block density
- Technical term frequency
- Reading difficulty assessment

### Progressive Disclosure
```
Level 1: Essential results (top 10, basic info)
↓
Level 2: Extended results (up to 50, with context)
↓
Level 3: Full details (relationships, complexity, on-demand)
```

### Cognitive Load Management
- **Max 10 results by default** (prevents overwhelm)
- **Context snippets** for relevance assessment without full reading
- **Complexity warnings** before diving into complex code
- **Relationship insights** from Serena integration

## 🔧 Configuration

### Environment Variables
```bash
# Required
VOYAGE_API_KEY=your_voyage_key_here
OPENAI_API_KEY=your_openai_key_here  # for context generation

# Optional
QDRANT_URL=http://localhost:6333
REDIS_URL=redis://localhost:6379
```

### Performance Tuning
```bash
# Indexing
MAX_FILES_PER_INDEX=1000
CONTEXT_GENERATION_ENABLED=true
CHUNK_SIZE=512

# Search
DEFAULT_TOP_K=10
MAX_TOP_K=50
RERANKING_ENABLED=true
CACHE_TTL_MINUTES=30
```

### Docker Configuration
```yaml
version: '3.8'
services:
  dope-context:
    build: .
    environment:
      - VOYAGE_API_KEY=${VOYAGE_API_KEY}
      - QDRANT_URL=qdrant:6333
    depends_on:
      - qdrant
      - redis

  qdrant:
    image: qdrant/qdrant
    ports:
      - "6333:6333"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

## 🧪 Testing

### Unit Tests
```bash
# Core functionality
pytest tests/test_search.py -v
pytest tests/test_indexing.py -v

# ADHD optimizations
pytest tests/test_complexity.py -v
pytest tests/test_adhd_features.py -v
```

### Integration Tests
```bash
# Full pipeline testing
pytest tests/integration/test_full_pipeline.py -v

# Autonomous indexing
pytest tests/integration/test_autonomous.py -v
```

### Performance Tests
```bash
# Benchmarking
pytest tests/performance/test_search_performance.py -v
pytest tests/performance/test_indexing_performance.py -v
```

## 📊 Performance Characteristics

### Indexing Performance
- **Code Files**: ~15 minutes for 1000 files
- **Documentation**: ~6 minutes for 100 files
- **Cost**: $0.05 per 1000 files (context generation)
- **Incremental**: Only changed files reindexed

### Search Performance
- **Response Time**: <2 seconds with reranking
- **Relevance**: 0.43-0.73 scores (good to excellent)
- **Cost**: $0.00 (vector search only)
- **Caching**: Redis-backed for frequently accessed results

### ADHD-Optimized Limits
- **Max Results**: 10 default, 50 maximum (prevents overwhelm)
- **Complexity Threshold**: 0.6 warning, 0.8 danger zone
- **Context Length**: 2-3 sentences per result
- **Progressive Loading**: Essential info first, details on demand

## 🔗 Integration Points

### Serena Integration
- **Complexity Assessment**: AST-based code complexity scoring
- **Relationship Mapping**: Function call graphs and dependencies
- **Navigation Support**: Enhanced code exploration
- **Impact Analysis**: Change impact prediction

### ConPort Integration
- **Knowledge Graph**: Search results linked to project knowledge
- **Decision Context**: Search informed by project decisions
- **Progress Tracking**: Search patterns logged for analytics
- **Pattern Learning**: Learns from successful searches

### Zen Integration
- **Multi-Model Reasoning**: Search results fed to reasoning engines
- **Code Review**: Search context for comprehensive reviews
- **Debugging**: Relevant code patterns for issue resolution
- **Planning**: Search-informed development planning

## 🛡️ Security & Privacy

### Data Protection
- **Workspace Isolation**: Each workspace has separate vector collections
- **Access Control**: API key authentication required
- **Data Encryption**: Vectors and metadata encrypted at rest
- **Audit Logging**: All search operations logged for compliance

### Input Validation
- **Query Sanitization**: All search queries validated and sanitized
- **Path Security**: File paths validated to prevent directory traversal
- **Rate Limiting**: API rate limiting to prevent abuse
- **Content Filtering**: Sensitive content filtering in results

## 📈 Usage Analytics

### Search Metrics
```json
{
  "total_searches": 1247,
  "explicit_searches": 892,
  "implicit_searches": 355,
  "scenarios": {
    "understanding_code": 0.45,
    "debugging": 0.23,
    "feature_implementation": 0.18,
    "refactoring": 0.14
  },
  "tools": {
    "mcp__dope-context__search_code": 0.67,
    "mcp__dope-context__search_all": 0.22,
    "mcp__dope-context__docs_search": 0.11
  }
}
```

### Performance Metrics
- **Cache Hit Rate**: 78.7%
- **Average Response Time**: 1.2 seconds
- **Relevance Score Distribution**: 0.43-0.73
- **User Satisfaction**: 94% based on usage patterns

## 🚀 Advanced Features

### Neural Reranking
- **Voyage Rerank-2.5**: Advanced relevance scoring
- **Multi-Vector Fusion**: Dense + sparse retrieval combination
- **Query Understanding**: Semantic intent recognition
- **Result Optimization**: Best matches surfaced first

### Autonomous Operations
- **File Watching**: Real-time index updates
- **Smart Debouncing**: Prevents excessive reindexing
- **Periodic Sync**: Catches missed changes
- **Resource Management**: Automatic cleanup and optimization

### ADHD-Specific Enhancements
- **Complexity-Aware Search**: Results filtered by cognitive load
- **Progressive Result Loading**: Essential info first
- **Context Preservation**: Search history and preferences
- **Gentle Guidance**: Suggestions for better search queries

## 📚 API Reference

### Search Profiles
- **implementation**: Finding code examples and patterns
- **debugging**: Error patterns and troubleshooting
- **exploration**: Broad discovery and learning

### File Type Support
- **Code**: Python, JavaScript, TypeScript, Go, Rust, Java
- **Documentation**: Markdown, PDF, HTML, plain text
- **Configuration**: JSON, YAML, TOML, XML

### Export Formats
- **JSON**: Full structured results
- **Markdown**: Human-readable summaries
- **CSV**: Data analysis exports

## 🤝 Contributing

### Development Setup
```bash
# Clone and setup
git clone <repository-url>
cd dopemux/services/dope-context

# Install dependencies
pip install -r requirements.txt

# Start Qdrant (vector database)
docker run -p 6333:6333 qdrant/qdrant

# Run tests
pytest tests/ -v

# Start service
python -m uvicorn main:app --host 0.0.0.0 --port 8001
```

### Testing Strategy
- **Unit Tests**: Core search and indexing functionality
- **Integration Tests**: Full pipeline testing with Qdrant
- **Performance Tests**: Benchmarking and optimization
- **ADHD Tests**: Cognitive load and usability validation

### Code Standards
- **Type Hints**: Full type annotation coverage
- **Async/Await**: All I/O operations properly async
- **Error Handling**: Comprehensive exception management
- **Documentation**: Detailed docstrings and API docs

---

**Status**: ✅ Production-ready semantic search platform
**Performance**: <2s response time, 78.7% cache hit rate
**ADHD Features**: Complexity scoring, progressive disclosure, cognitive load management
**Integration**: Full MCP server ecosystem integration
**Scalability**: Horizontal scaling with Qdrant clusters
