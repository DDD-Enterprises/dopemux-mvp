# Dope-Context

**Unified code + docs semantic search MCP server for Claude Code**

Multi-project support with perfect workspace isolation, hybrid search (dense + sparse), and incremental sync.

---

## Features

### Code Search
- **AST-Aware Chunking**: Tree-sitter for semantic boundaries (functions, classes)
- **Contextual Embeddings**: Claude-generated contexts (35-67% quality improvement)
- **Multi-Vector**: Separate embeddings for content, title, breadcrumb
- **Hybrid Search**: Dense (semantic) + BM25 (keyword) with RRF fusion
- **Neural Reranking**: Voyage rerank-2.5 with progressive disclosure

### Document Search
- **Multi-Format**: PDF, Markdown, HTML, DOCX, plain text
- **Smart Chunking**: 1000 chars with overlap, preserves structure
- **Semantic Search**: voyage-context-3 embeddings
- **Multi-Vector**: Same 3-vector strategy as code

### Multi-Project Support
- **Perfect Isolation**: Collection-per-workspace (no data leakage)
- **Auto-Detection**: Detects workspace from git root or cwd
- **Incremental Sync**: SHA256-based change detection (Merkle DAG)
- **Snapshot System**: Stores file hashes in ~/.dope-context/

### ADHD Optimizations
- **Progressive Disclosure**: Top-10 display + 40 cached
- **Complexity Scoring**: 0.0-1.0 cognitive load estimation
- **Cost Tracking**: Full API cost monitoring
- **Batching**: Optimized for minimal API calls

---

## Quick Start

### Prerequisites

- Python 3.11+
- Qdrant (vector database)
- API Keys:
  - `VOYAGE_API_KEY` (required)
  - `ANTHROPIC_API_KEY` (optional, improves context quality)

### Installation

```bash
cd services/claude-context-v2  # TODO: Rename to dope-context

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export VOYAGE_API_KEY="your-voyage-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"  # Optional
export QDRANT_URL="localhost"
export QDRANT_PORT="6333"

# Start Qdrant (if not running)
docker run -p 6333:6333 qdrant/qdrant
```

### Claude Code MCP Configuration

```bash
# Add to Claude Code
claude mcp add dope-context \
  -e VOYAGE_API_KEY=your-key \
  -e ANTHROPIC_API_KEY=your-key \
  -e QDRANT_URL=localhost \
  -e QDRANT_PORT=6333 \
  -- python /Users/hue/code/dopemux-mvp/services/claude-context-v2/src/mcp/server.py
```

Or manually edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "dope-context": {
      "command": "python",
      "args": ["/Users/hue/code/dopemux-mvp/services/claude-context-v2/src/mcp/server.py"],
      "env": {
        "VOYAGE_API_KEY": "your-voyage-api-key",
        "ANTHROPIC_API_KEY": "your-anthropic-api-key",
        "QDRANT_URL": "localhost",
        "QDRANT_PORT": "6333"
      }
    }
  }
}
```

---

## Usage

### 1. Index Your Codebase

```python
# In Claude Code
index_workspace("/Users/you/your-project")

# With custom patterns
index_workspace(
    "/Users/you/your-project",
    include_patterns=["*.py", "*.ts", "*.go"],
    exclude_patterns=["*test*", "node_modules"],
    max_files=1000
)
```

### 2. Search Code

```python
# Basic search (auto-detects current workspace)
search_code("async error handling")

# With options
search_code(
    query="JWT authentication",
    top_k=10,
    profile="implementation",  # or "debugging", "exploration"
    use_reranking=True,
    filter_language="python"
)
```

### 3. Index Documents

```python
# Index docs (Markdown, PDF, HTML, DOCX)
index_docs("/Users/you/your-project")

# Search docs
docs_search("API authentication guide")
```

### 4. Unified Search

```python
# Search BOTH code and docs
search_all("user authentication")
# Returns: {workspace, code_results, docs_results, total_results}
```

### 5. Incremental Sync

```python
# After making code changes
sync_workspace("/Users/you/your-project")
# Returns: {added: 2, modified: 5, removed: 1, message: "..."}

# Then reindex only changed files
index_workspace("/Users/you/your-project")  # Smart: only updates changes

# Same for docs
sync_docs("/Users/you/your-project")
index_docs("/Users/you/your-project")
```

---

## Architecture

### Multi-Project Isolation

Each workspace gets dedicated collections:

```
Workspace A (/Users/you/project-a)
├─ Collection: code_3ca12e07  (hash of path)
└─ Collection: docs_3ca12e07

Workspace B (/Users/you/project-b)
├─ Collection: code_f8a9b2c4
└─ Collection: docs_f8a9b2c4

Perfect isolation - no data leakage possible
```

### Code Pipeline

```
Python/JS/TS Files
    ↓
Tree-sitter AST Chunking
    ↓
Claude Context Generation (50-100 tokens)
    ↓
VoyageAI Embedding (voyage-code-3)
    ├─ content_vec (contextualized code)
    ├─ title_vec (function/class name)
    └─ breadcrumb_vec (file.path.symbol)
    ↓
Qdrant Multi-Vector Storage
```

### Search Pipeline

```
Natural Language Query
    ↓
VoyageAI Embedding (3 vectors)
    ↓
Dense Search (multi-vector weighted fusion)
    ↓
BM25 Sparse Search (code-aware tokenizer)
    ↓
RRF Fusion (k=60)
    ↓
Voyage Reranking (top-50 → top-10)
    ↓
Progressive Disclosure (10 + 40 cached)
```

### Sync System

```
FileSynchronizer.check_changes()
├─ Load snapshot from ~/.dope-context/snapshots/{hash}/
├─ Scan workspace (SHA256 all files)
├─ Compare hashes (Merkle DAG-based diff)
├─ Return {added, modified, removed}
└─ Save new snapshot (atomic write)
```

---

## MCP Tools (9 Total)

### Indexing Tools

**index_workspace**(workspace_path, include_patterns?, exclude_patterns?, max_files?)
- Index code files for semantic search
- Auto-detects workspace, creates collection
- Returns: indexing progress summary

**index_docs**(workspace_path, include_patterns?)
- Index documents (PDF, Markdown, HTML, DOCX)
- Creates docs collection for workspace
- Returns: docs processed count

### Search Tools

**search_code**(query, top_k=10, profile="implementation", use_reranking=True, filter_language?, workspace_path?)
- Hybrid code search with reranking
- Auto-detects workspace from cwd
- Returns: list of code results with scores

**docs_search**(query, top_k=10, filter_doc_type?, workspace_path?)
- Semantic document search
- Auto-detects workspace
- Returns: list of doc results

**search_all**(query, top_k=10, workspace_path?)
- Unified search across code + docs
- Splits top_k between both (e.g., 5 code + 5 docs)
- Returns: {workspace, code_results, docs_results}

### Sync Tools

**sync_workspace**(workspace_path, include_patterns?)
- Detect code file changes (incremental)
- SHA256-based change detection
- Returns: change statistics

**sync_docs**(workspace_path, include_patterns?)
- Detect document changes
- Returns: change statistics

### Management Tools

**get_index_status**()
- Get collection statistics
- Returns: vectors count, costs

**clear_index**()
- Delete collection (cleanup)

---

## Performance

See [PERFORMANCE_TUNING.md](PERFORMANCE_TUNING.md) for optimization guide.

---

## Development

### Run Tests

```bash
pytest tests/ -v
# 93/94 tests passing (98.9%)
```

### Project Structure

```
dope-context/
├── src/
│   ├── embeddings/      # VoyageAI multi-model embedder
│   ├── preprocessing/   # Code + doc chunking
│   ├── context/         # Claude context generation
│   ├── search/          # Multi-vector + hybrid + docs
│   ├── rerank/          # Voyage reranking
│   ├── pipeline/        # Indexing orchestration
│   ├── sync/            # FileSynchronizer
│   ├── utils/           # Workspace detection
│   └── mcp/             # FastMCP server (9 tools)
├── tests/               # 9 test files, 93 tests
└── requirements.txt     # Dependencies
```

---

## Related Documentation

- [API Reference](API_REFERENCE.md) - Complete MCP tools documentation
- [Performance Guide](PERFORMANCE_TUNING.md) - Optimization strategies
- [Deployment Guide](DEPLOYMENT.md) - Docker and production setup
- [Architecture](ARCHITECTURE.md) - Technical design details

---

## License

MIT
