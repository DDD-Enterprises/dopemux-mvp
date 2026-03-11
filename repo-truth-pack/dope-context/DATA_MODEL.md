# DATA_MODEL.md — dope-context

**Analyzed ref:** `fe48c0a874ac25ed179b9ddb091252a6dbe9b5c2`

---

## 1. Qdrant Collections

### Collection Naming Convention
**Source:** `src/utils/workspace.py:176-177`

```python
code_collection = f"code_{workspace_hash}"
docs_collection = f"docs_{workspace_hash}"
```

Where `workspace_hash` is derived from `workspace_to_hash(workspace_path)` — a deterministic hash of the resolved workspace path.

### Vector Configuration
**Source:** `config/multi_index_config.yaml:9-17`, `src/search/dense_search.py`

| Property | Value | Evidence |
|----------|-------|----------|
| Embedding dimension | 1024 | `multi_index_config.yaml:9` |
| Distance metric | DOT | `dense_search.py` (imports `Distance`) |
| Named vectors per collection | 3 | `multi_index_config.yaml:11-17` |

### Named Vectors

| Vector Name | Purpose | Embedding Model (Code) | Embedding Model (Docs) |
|-------------|---------|----------------------|----------------------|
| `content_vec` | Main content embedding | voyage-code-3 (contextualized) | voyage-context-3 |
| `title_vec` | Title/function name embedding | voyage-code-3 (standard) | voyage-context-3 |
| `breadcrumb_vec` | Path/breadcrumb embedding | voyage-code-3 (standard) | voyage-context-3 |

**Note:** For docs search, all three vectors receive the same embedding from a single `voyage-context-3` call (server.py:1700-1704).

---

## 2. Code Index Payload Schema

Derived from `_search_code_impl` response building (server.py:1222-1270) and `CodeChunk` dataclass:

```json
{
  "file_path": "string — relative path within workspace",
  "function_name": "string|null — AST-extracted function/class name",
  "language": "string|null — detected language",
  "content": "string — code chunk text",
  "context_snippet": "string|null — LLM-generated context summary",
  "start_line": "integer|null — chunk start line",
  "end_line": "integer|null — chunk end line",
  "score": "number — search relevance score"
}
```

### CodeChunk Dataclass (src/preprocessing/code_chunker.py)

| Field | Type | Description |
|-------|------|-------------|
| `content` | str | Raw code text |
| `file_path` | str | Source file path |
| `function_name` | Optional[str] | AST-extracted symbol name |
| `language` | Optional[str] | Detected language |
| `start_line` | int | Start line number |
| `end_line` | int | End line number |
| `context_snippet` | Optional[str] | LLM-generated context |

### ChunkingConfig Dataclass (src/preprocessing/code_chunker.py)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `max_chunk_size` | int | UNKNOWN | Maximum characters per chunk |
| `overlap` | int | UNKNOWN | Overlap between chunks |
| `min_chunk_size` | int | UNKNOWN | Minimum characters per chunk |

---

## 3. Docs Index Payload Schema

Derived from `_docs_search_impl` response building (server.py:1721-1756):

```json
{
  "source_path": "string — document file path",
  "text": "string — truncated chunk text",
  "score": "number — relevance score",
  "doc_type": "string — document type (md, pdf, html, txt, unknown)",
  "truncated": "boolean — whether text was truncated",
  "original_length": "integer — original text length",
  "rank": "integer — result position (1-based)",
  "source_uri": "string — same as source_path",
  "chunk_id": "string — doc_chunk_{rank} or payload chunk_id",
  "snippet": "string — same as text"
}
```

### DocumentType Enum (src/preprocessing/models.py:8)

```python
class DocumentType(str, Enum):
    MARKDOWN = "markdown"
    PDF = "pdf"
    HTML = "html"
    TEXT = "text"
    CODE = "code"
    DOCX = "docx"
```

### ChunkMetadata Dataclass (src/preprocessing/models.py:19)

| Field | Type | Description |
|-------|------|-------------|
| `source_path` | str | Document file path |
| `doc_type` | DocumentType | Document format |
| `chunk_index` | int | Position in document |
| `total_chunks` | int | Total chunks from document |
| `metadata` | Dict | Additional metadata |

### DocumentChunk Dataclass (src/preprocessing/models.py:42)

| Field | Type | Description |
|-------|------|-------------|
| `text` | str | Chunk text content |
| `metadata` | ChunkMetadata | Associated metadata |

---

## 4. Decision Data (Cross-Plane)

Derived from `_search_decisions_impl` (server.py:1946-1957):

```json
{
  "id": "string|null — decision identifier",
  "summary": "string — decision summary/title",
  "timestamp": "string|null — ISO timestamp",
  "source": "conport"
}
```

**Source:** Retrieved via HTTP GET from `{bridge_url}/kg/decisions/search` (dopecon-bridge).
**Authority:** Memory plane (ConPort) — dope-context is read-only consumer.

---

## 5. File-Based Persistence

### Snapshot Directory Structure

```
~/.dope-context/
├── snapshots/
│   └── {workspace_hash}/
│       ├── snapshot.json            — File-level SHA256 hashes
│       ├── chunk_snapshot.json      — Chunk-level metadata
│       ├── bm25_index.pkl           — Pickled BM25 index
│       ├── autoindex_bootstrap.json — Bootstrap idempotence marker
│       └── decision_sync_config.json — Per-workspace decision settings
└── search_metrics.json              — Global search usage analytics
```

### snapshot.json Schema

```json
{
  "workspace_path": "string — resolved workspace path",
  "created_at": "string — ISO timestamp",
  "files": {
    "relative/path.py": {
      "hash": "string — SHA256 hex",
      "size": "integer — file size",
      "mtime": "number — modification time"
    }
  }
}
```

### chunk_snapshot.json Schema

```json
{
  "workspace_path": "string",
  "files": {
    "relative/path.py": {
      "chunks": [
        {
          "chunk_id": "string",
          "content_hash": "string — SHA256"
        }
      ]
    }
  }
}
```

### autoindex_bootstrap.json Schema

```json
{
  "status": "completed",
  "workspace": "string — resolved path",
  "snapshot_signature": "string — git:{SHA} or mtime:{epoch} or path:{workspace}",
  "completed_at": "string — ISO timestamp",
  "trigger": "dopemux_cli_startup"
}
```

### decision_sync_config.json Schema

```json
{
  "enabled": "boolean — default false",
  "bridge_url": "string — default http://localhost:3016",
  "limit": "integer — 1-10, default 3",
  "auto_include_in_search_all": "boolean — default true",
  "updated_at": "string — ISO timestamp"
}
```

### search_metrics.json Schema

Managed by `MetricsTracker` (`src/utils/metrics_tracker.py`). Contains:
- Total search count
- Per-tool search counts
- Per-scenario search counts
- Sample queries per scenario
- Timestamps

---

## 6. BM25 Index Structure

**Source:** server.py:954-959

Pickled dict containing:
```python
{
    "bm25": BM25Okapi,       # rank_bm25 BM25Okapi instance
    "documents": List[Dict],  # All indexed document payloads
    "doc_ids": List[str],     # Document identifiers
}
```

**Note:** Legacy JSON format also supported for reading (server.py:1114-1118).

---

## 7. Embedding Specifications

### Code Embeddings

| Property | Value | Evidence |
|----------|-------|----------|
| Model | `voyage-code-3` | server.py:347, 912, 1160 |
| Dimension | 1024 | multi_index_config.yaml:9 |
| Input types | `query`, `document` | voyage_embedder.py |
| API | Voyage AI | requirements.txt: `voyageai>=0.2.3` |

### Docs Embeddings

| Property | Value | Evidence |
|----------|-------|----------|
| Model | `voyage-context-3` | server.py:1637, docs_pipeline.py |
| Dimension | 1024 | contextualized_embedder.py |
| Cache TTL | 24 hours | server.py:421, 862 |
| Input types | `query`, `document` | contextualized_embedder.py |

### Reranking

| Property | Value | Evidence |
|----------|-------|----------|
| Model | `voyage-rerank-2.5` | voyage_reranker.py |
| Max candidates | 50 | server.py:1216 (`results[:50]`) |
| API | Voyage AI | requirements.txt |

---

## 8. Multi-Index Config (Aspirational)

**Source:** `config/multi_index_config.yaml`

Four index types defined:
1. **code** — Python, JS, TS, Go, Rust (IMPLEMENTED)
2. **docs** — Markdown, PDF, HTML, text (IMPLEMENTED)
3. **api** — OpenAPI/Swagger/GraphQL (NOT IMPLEMENTED)
4. **chat** — Conversation transcripts (NOT IMPLEMENTED)

Only `code` and `docs` have corresponding pipeline implementations.

---

## 9. Docker Volume Mappings

| Mount | Container Path | Content |
|-------|---------------|---------|
| `./services/dope-context/data` | `/app/data` | Search indices (local data) |
| `./services/dope-context/logs` | `/app/logs` | Application logs |
| `${HOST_CODE_PARENT_DIR:-/tmp}` | `/workspaces` | Host source code for indexing |
