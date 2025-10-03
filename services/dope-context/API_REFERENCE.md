# Dope-Context API Reference

Complete documentation for all 9 MCP tools.

---

## Indexing Tools

### `index_workspace`

Index code files in a workspace for semantic search.

**Signature:**
```python
index_workspace(
    workspace_path: str,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
    max_files: Optional[int] = None
) -> Dict
```

**Parameters:**
- `workspace_path` (required): Absolute path to workspace root
- `include_patterns`: File patterns to include (default: `["*.py", "*.js", "*.ts", "*.tsx"]`)
- `exclude_patterns`: Patterns to exclude (default: `["*test*", "*__pycache__*"]`)
- `max_files`: Maximum files to process (optional, for testing)

**Returns:**
```json
{
  "files": "150/150",
  "chunks": "1250/1250",
  "completion": "100.0%",
  "errors": 0,
  "elapsed_seconds": 45.3,
  "total_cost_usd": 0.2150
}
```

**Example:**
```python
# Basic indexing
result = index_workspace("/Users/you/my-project")

# Custom patterns
result = index_workspace(
    "/Users/you/my-project",
    include_patterns=["*.py", "*.go", "*.rs"],
    exclude_patterns=["vendor/*", "*_test.go"],
    max_files=500
)
```

**Notes:**
- Creates collection: `code_{workspace_hash}`
- Uses Tree-sitter for AST-aware chunking
- Generates Claude contexts (requires ANTHROPIC_API_KEY)
- Embeds with voyage-code-3 (3 vectors per chunk)
- Stores in Qdrant with multi-vector schema

---

### `index_docs`

Index documents (PDF, Markdown, HTML, DOCX, text) in workspace.

**Signature:**
```python
index_docs(
    workspace_path: str,
    include_patterns: Optional[List[str]] = None
) -> Dict
```

**Parameters:**
- `workspace_path` (required): Absolute path to workspace root
- `include_patterns`: File patterns (default: `["*.md", "*.txt", "*.pdf", "*.html"]`)

**Returns:**
```json
{
  "docs_processed": 25,
  "chunks_indexed": 450,
  "errors": 0
}
```

**Example:**
```python
# Index all docs
result = index_docs("/Users/you/my-project")

# Only markdown
result = index_docs(
    "/Users/you/my-project",
    include_patterns=["*.md"]
)
```

**Notes:**
- Creates collection: `docs_{workspace_hash}`
- Simple chunking (1000 chars, 100 overlap) for MVP
- Embeds with voyage-context-3
- Future: Will use DocumentProcessor for PDF/DOCX extraction

---

## Search Tools

### `search_code`

Hybrid semantic + keyword search for code.

**Signature:**
```python
search_code(
    query: str,
    top_k: int = 10,
    profile: str = "implementation",
    use_reranking: bool = True,
    filter_language: Optional[str] = None,
    workspace_path: Optional[str] = None
) -> List[Dict]
```

**Parameters:**
- `query` (required): Natural language search query
- `top_k`: Number of results (default: 10, ADHD-optimized)
- `profile`: Search profile - `"implementation"`, `"debugging"`, or `"exploration"`
- `use_reranking`: Enable Voyage reranking (default: True)
- `filter_language`: Filter by language - `"python"`, `"javascript"`, `"typescript"`
- `workspace_path`: Workspace path (auto-detects from cwd if None)

**Search Profiles:**

**implementation** (default):
- top_k: 100 candidates
- Weights: content 70%, title 20%, breadcrumb 10%
- Use for: Finding implementation examples

**debugging**:
- top_k: 50 candidates
- Weights: content 50%, title 40%, breadcrumb 10%
- Use for: Finding specific functions by name

**exploration**:
- top_k: 200 candidates
- Weights: content 60%, title 20%, breadcrumb 20%
- Use for: Broad codebase exploration

**Returns:**
```json
[
  {
    "file_path": "src/auth/jwt.py",
    "function_name": "verify_token",
    "language": "python",
    "code": "def verify_token(token: str) -> bool:\n    ...",
    "context": "This function from src/auth/jwt.py verifies JWT tokens...",
    "relevance_score": 0.95,
    "original_rank": 3,
    "reranked": true
  }
]
```

**Example:**
```python
# Simple search
results = search_code("async database connection pooling")

# Debugging-focused
results = search_code(
    "calculateUserScore",
    profile="debugging",
    filter_language="python"
)

# Without reranking (faster)
results = search_code(
    "error handling",
    use_reranking=False,
    top_k=20
)
```

---

### `docs_search`

Semantic search for documents.

**Signature:**
```python
docs_search(
    query: str,
    top_k: int = 10,
    filter_doc_type: Optional[str] = None,
    workspace_path: Optional[str] = None
) -> List[Dict]
```

**Parameters:**
- `query` (required): Natural language query
- `top_k`: Number of results (default: 10)
- `filter_doc_type`: Filter by type - `"md"`, `"pdf"`, `"html"`, `"txt"`
- `workspace_path`: Workspace path (auto-detects if None)

**Returns:**
```json
[
  {
    "source_path": "docs/api/authentication.md",
    "text": "## Authentication\n\nThe API uses JWT tokens...",
    "score": 0.88,
    "doc_type": "md"
  }
]
```

**Example:**
```python
# Search all docs
results = docs_search("API rate limiting configuration")

# Only markdown files
results = docs_search(
    "deployment guide",
    filter_doc_type="md"
)
```

---

### `search_all`

Unified search across BOTH code and documents.

**Signature:**
```python
search_all(
    query: str,
    top_k: int = 10,
    workspace_path: Optional[str] = None
) -> Dict
```

**Parameters:**
- `query` (required): Search query
- `top_k`: Total results (split 50/50 between code and docs)
- `workspace_path`: Workspace path (auto-detects if None)

**Returns:**
```json
{
  "workspace": "/Users/you/my-project",
  "code_results": [
    {
      "file_path": "src/auth.py",
      "function_name": "authenticate_user",
      "code": "...",
      "score": 0.92
    }
  ],
  "docs_results": [
    {
      "source_path": "docs/auth.md",
      "text": "## Authentication...",
      "score": 0.85
    }
  ],
  "total_results": 10
}
```

**Example:**
```python
# Find code AND documentation
results = search_all("user authentication flow")

# Iterate results
for code_result in results["code_results"]:
    print(f"Code: {code_result['file_path']}")

for doc_result in results["docs_results"]:
    print(f"Doc: {doc_result['source_path']}")
```

---

## Sync Tools

### `sync_workspace`

Detect code file changes for incremental indexing.

**Signature:**
```python
sync_workspace(
    workspace_path: str,
    include_patterns: Optional[List[str]] = None
) -> Dict
```

**Parameters:**
- `workspace_path` (required): Absolute workspace path
- `include_patterns`: File patterns to track (default: code files)

**Returns:**
```json
{
  "workspace": "/Users/you/my-project",
  "changes": 8,
  "added": 2,
  "modified": 5,
  "removed": 1,
  "message": "Detected 8 changes. Run index_workspace to update."
}
```

**Example:**
```python
# Check for changes
changes = sync_workspace("/Users/you/my-project")

if changes["changes"] > 0:
    # Reindex (smart: only updates changed files)
    index_workspace("/Users/you/my-project")
```

**How It Works:**
1. Loads previous snapshot from `~/.dope-context/snapshots/{hash}/snapshot.json`
2. Scans workspace, computes SHA256 for each file
3. Compares hashes to detect changes
4. Saves new snapshot
5. Returns change statistics

**Notes:**
- First run: All files marked as "added"
- Fast: Only hashes files, doesn't embed
- Atomic: Snapshot writes are atomic (no corruption)
- Per-workspace: Each workspace has separate snapshot

---

### `sync_docs`

Detect document changes for incremental indexing.

**Signature:**
```python
sync_docs(
    workspace_path: str,
    include_patterns: Optional[List[str]] = None
) -> Dict
```

**Parameters:**
- `workspace_path` (required): Absolute workspace path
- `include_patterns`: File patterns (default: `["*.md", "*.pdf", "*.html", "*.txt"]`)

**Returns:**
Same format as `sync_workspace`

**Example:**
```python
# Check for doc changes
changes = sync_docs("/Users/you/my-project")

if changes["changes"] > 0:
    index_docs("/Users/you/my-project")
```

---

## Management Tools

### `get_index_status`

Get index statistics and cost summary.

**Signature:**
```python
get_index_status() -> Dict
```

**Returns:**
```json
{
  "collection_name": "code_3ca12e07",
  "total_vectors": 1250,
  "status": "green",
  "embedding_cost_summary": {
    "total_requests": 150,
    "total_tokens": 125000,
    "total_cost_usd": 0.015,
    "cache_hits": 25,
    "cache_rate": 0.167
  },
  "context_cost_summary": {
    "total_requests": 150,
    "total_input_tokens": 50000,
    "total_output_tokens": 7500,
    "total_cost_usd": 0.022
  }
}
```

**Example:**
```python
status = get_index_status()
print(f"Indexed {status['total_vectors']} code chunks")
print(f"Total cost: ${status['embedding_cost_summary']['total_cost_usd']:.4f}")
```

---

### `clear_index`

Delete index collection (cleanup/reset).

**Signature:**
```python
clear_index() -> Dict
```

**Returns:**
```json
{
  "status": "success",
  "message": "Code index cleared"
}
```

**Example:**
```python
# Reset index
clear_index()

# Then reindex
index_workspace("/Users/you/my-project")
```

**Warning:** This deletes the collection. Snapshots are preserved, so you can reindex quickly.

---

## Workflow Examples

### Initial Setup

```python
# 1. Index your codebase
index_workspace("/Users/you/my-project")

# 2. Index documentation
index_docs("/Users/you/my-project")

# 3. Search!
results = search_all("authentication implementation")
```

### Daily Workflow

```python
# Morning: Check for changes
code_changes = sync_workspace("/Users/you/my-project")
doc_changes = sync_docs("/Users/you/my-project")

# If changes detected, reindex
if code_changes["changes"] > 0:
    index_workspace("/Users/you/my-project")

if doc_changes["changes"] > 0:
    index_docs("/Users/you/my-project")

# Throughout the day: Search as needed
results = search_code("error handling patterns")
```

### Working with Multiple Projects

```python
# Index all your projects
index_workspace("/Users/you/project-a")
index_workspace("/Users/you/project-b")
index_workspace("/Users/you/project-c")

# Search is automatically scoped to current project
# (based on where Claude Code is running)
results = search_code("database connection")  # Only searches current project

# Or explicitly specify
results = search_code("auth", workspace_path="/Users/you/project-b")
```

---

## Error Handling

All tools return structured errors:

```json
{
  "error": "WorkspaceNotFound",
  "message": "Workspace path does not exist: /invalid/path",
  "details": {}
}
```

Common errors:
- `WorkspaceNotFound`: Invalid workspace path
- `CollectionNotFound`: Workspace not indexed yet (run index_workspace first)
- `APIKeyMissing`: VOYAGE_API_KEY not set
- `EmbeddingFailed`: Voyage API error (check network, quota)
- `QdrantConnectionFailed`: Can't connect to Qdrant (check if running)

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `VOYAGE_API_KEY` | Yes | - | VoyageAI API key |
| `ANTHROPIC_API_KEY` | No | - | Claude API key (improves quality) |
| `QDRANT_URL` | No | `localhost` | Qdrant server URL |
| `QDRANT_PORT` | No | `6333` | Qdrant server port |
| `WORKSPACE_ID` | No | Auto-detected | Override workspace detection |

### Search Profiles

**Implementation Profile** (default):
```python
{
    "top_k": 100,
    "content_weight": 0.7,
    "title_weight": 0.2,
    "breadcrumb_weight": 0.1,
    "ef": 150  # HNSW search quality
}
```

**Debugging Profile**:
```python
{
    "top_k": 50,
    "content_weight": 0.5,
    "title_weight": 0.4,  # Higher title weight
    "breadcrumb_weight": 0.1,
    "ef": 120
}
```

**Exploration Profile**:
```python
{
    "top_k": 200,
    "content_weight": 0.6,
    "title_weight": 0.2,
    "breadcrumb_weight": 0.2,  # Higher breadcrumb weight
    "ef": 180
}
```

---

## Advanced Usage

### Batching Strategy

The pipeline automatically batches for efficiency:
- **Context Generation**: 10 chunks per Claude API call
- **Embeddings**: 8 texts per Voyage API call
- **Qdrant Inserts**: 100 points per batch

### Cost Optimization

```python
# Skip context generation (faster, cheaper, lower quality)
# Set ANTHROPIC_API_KEY to empty or don't set it
# Falls back to simple context: "Code from {file} (lines X-Y)"

# Disable reranking (faster, lower cost)
results = search_code("query", use_reranking=False)

# Limit results
results = search_code("query", top_k=5)  # Fewer = cheaper reranking
```

### Multi-Vector Weighting

Can be customized in `SearchProfile` class:

```python
from src.search.dense_search import SearchProfile

custom_profile = SearchProfile(
    name="custom",
    top_k=150,
    content_weight=0.8,  # Emphasize content
    title_weight=0.15,
    breadcrumb_weight=0.05,
    ef=180
)
```

---

## Performance Metrics

See [PERFORMANCE_TUNING.md](PERFORMANCE_TUNING.md) for detailed optimization guide.

**Typical Performance:**
- Search latency: <500ms p95 (code), <400ms (docs)
- Indexing throughput: 2-5 files/second
- Sync check: 100-500ms (depends on file count)
- Memory usage: ~200MB per workspace

---

## Troubleshooting

### "CollectionNotFound" error

```python
# Solution: Index the workspace first
index_workspace("/Users/you/my-project")
```

### Search returns no results

```python
# Check if workspace is indexed
status = get_index_status()
print(status["total_vectors"])  # Should be > 0

# Check workspace detection
from src.utils.workspace import get_workspace_root, get_collection_names
workspace = get_workspace_root()
code_coll, _ = get_collection_names(workspace)
print(f"Searching in: {code_coll}")
```

### Slow searches

```python
# Disable reranking
results = search_code("query", use_reranking=False)

# Use debugging profile (fewer candidates)
results = search_code("query", profile="debugging")

# Reduce top_k
results = search_code("query", top_k=5)
```

### High costs

```python
# Check cost summary
status = get_index_status()
print(status["embedding_cost_summary"])

# Optimize:
# - Skip ANTHROPIC_API_KEY (no context generation)
# - Disable reranking
# - Use smaller top_k
# - Increase cache_ttl_hours in VoyageEmbedder
```

---

## Integration with Dopemux

Dope-Context integrates with Dopemux ConPort for session management:

```python
# Store indexed workspaces in ConPort
from mcp__conport import log_custom_data

log_custom_data(
    workspace_id="/Users/hue/code/dopemux-mvp",
    category="indexed_workspaces",
    key="my-project",
    value={
        "path": "/Users/you/my-project",
        "code_collection": "code_3ca12e07",
        "docs_collection": "docs_3ca12e07",
        "last_indexed": "2025-10-03T10:00:00Z"
    }
)
```

---

## API Versioning

Current version: 1.0.0

Breaking changes will increment major version.
