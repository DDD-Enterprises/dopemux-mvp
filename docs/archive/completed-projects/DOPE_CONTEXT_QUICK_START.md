---
id: DOPE_CONTEXT_QUICK_START
title: Dope_Context_Quick_Start
type: explanation
owner: '@hu3mann'
last_review: '2026-02-01'
next_review: '2026-05-02'
---
# Dope-Context Multi-Workspace Quick Start

## Running Tests

```bash
# From repo root
cd /Users/dopemux/code/dopemux-mvp

# Run all multi-workspace tests
PYTHONPATH="$(pwd)/services/dope-context" python3 -m pytest \
  services/dope-context/tests/test_mcp_server.py -k "multi" -v

# Run specific test
PYTHONPATH="$(pwd)/services/dope-context" python3 -m pytest \
  services/dope-context/tests/test_mcp_server.py::test_search_code_multi_workspace -v

# Run all dope-context tests
PYTHONPATH="$(pwd)/services/dope-context" python3 -m pytest \
  services/dope-context/tests/test_mcp_server.py -v
```

## Using Multi-Workspace Features

### In Python Code
```python
from src.mcp.server import search_code, docs_search, sync_workspace

# Single workspace (backward compatible)
results = await search_code(
    query="authentication",
    workspace_path="/path/to/workspace"
)
# Returns: List[Dict]

# Multiple workspaces
results = await search_code(
    query="authentication",
    workspace_paths=["/path/ws1", "/path/ws2"]
)
# Returns: {
#   "workspace_count": 2,
#   "total_results": 15,
#   "results": [...]
# }
```

### Via MCP Protocol
```json
{
  "method": "tools/call",
  "params": {
    "name": "search_code",
    "arguments": {
      "query": "authentication logic",
      "workspace_paths": [
        "/Users/dev/project-main",
        "/Users/dev/project-feature-branch"
      ]
    }
  }
}
```

## Running Autonomous Indexing

### Single Workspace (Auto-detect)
```bash
cd /path/to/your/project
python scripts/autonomous-indexing-daemon.py
```

### Multiple Workspaces (CLI)
```bash
python scripts/autonomous-indexing-daemon.py \
  --workspace /path/to/main \
  --workspace /path/to/worktree-a \
  --workspace /path/to/worktree-b
```

### Multiple Workspaces (Environment Variable)
```bash
DOPE_CONTEXT_WORKSPACES="/path/main,/path/worktree-a,/path/worktree-b" \
  python scripts/autonomous-indexing-daemon.py
```

## Environment Setup

Required environment variables:
```bash
# Voyage AI for embeddings
export VOYAGE_API_KEY="your-key"

# Optional: OpenAI for context generation
export OPENAI_API_KEY="your-key"

# Qdrant vector database
export QDRANT_URL="localhost"
export QDRANT_PORT="6333"

# Multi-workspace configuration
export DOPE_CONTEXT_WORKSPACES="/path/ws1,/path/ws2"
```

## API Functions

All functions support both `workspace_path` (single) and `workspace_paths` (multiple):

1. **search_code()** - Search code with hybrid dense+sparse
2. **docs_search()** - Search documentation
3. **search_all()** - Combined code + docs search
4. **sync_workspace()** - Sync workspace files
5. **sync_docs()** - Sync documentation files

## Return Value Patterns

### Single Workspace
```python
# Returns the direct implementation result
results = await search_code(workspace_path="/path")
# Type: List[Dict] - simple list of results
```

### Multiple Workspaces
```python
# Returns aggregated structure
results = await search_code(workspace_paths=["/p1", "/p2"])
# Type: Dict = {
#   "workspace_count": 2,
#   "total_results": 10,
#   "results": [
#     {
#       "workspace": "/p1",
#       "results": [...],  # Same format as single
#       "result_count": 5
#     },
#     {
#       "workspace": "/p2",
#       "results": [...],
#       "result_count": 5
#     }
#   ]
# }
```

## Testing in Constrained Environments

No pip installs needed! The code has fallbacks for:
- tiktoken → character-based estimation
- BeautifulSoup, docx, markdown, PyPDF2 → stubs
- tree_sitter → stubs
- voyageai, qdrant_client, rank_bm25 → test stubs

```bash
# Works even without heavy dependencies
PYTHONPATH="$(pwd)/services/dope-context" python3 -m pytest \
  services/dope-context/tests/test_mcp_server.py
```

## Common Issues

### Import Errors
**Problem**: `ModuleNotFoundError: No module named 'src'`
**Solution**: Set PYTHONPATH correctly:
```bash
PYTHONPATH="$(pwd)/services/dope-context" python3 -m pytest ...
```

### Async Test Failures
**Problem**: `async def functions are not natively supported`
**Solution**: Tests use `@pytest.mark.anyio` (not `asyncio`)

### Collection Errors
**Problem**: Tests fail to collect
**Solution**: Heavy dependencies have fallback stubs - ensure you're using the updated code

## File Locations

```
services/dope-context/
├── src/
│   ├── mcp/
│   │   └── server.py          # Multi-workspace API functions
│   ├── preprocessing/
│   │   ├── document_processor.py  # Fallback imports
│   │   └── code_chunker.py        # tree_sitter fallback
│   └── ...
├── tests/
│   └── test_mcp_server.py     # Multi-workspace tests
└── ...

scripts/
├── autonomous-indexing-daemon.py      # Long-running daemon ✓
└── enable-autonomous-indexing.py      # Bootstrap script
```

## Next Steps

1. Read `DOPE_CONTEXT_MULTI_WORKSPACE_COMPLETE.md` for full details
2. Run tests to verify your environment
3. Try the daemon with multiple workspaces
4. Check out the multi-workspace test examples for patterns

---

Questions? Check the main documentation or test files for examples.
