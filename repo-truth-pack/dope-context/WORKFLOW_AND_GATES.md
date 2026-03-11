# WORKFLOW_AND_GATES.md — dope-context

**Analyzed ref:** `fe48c0a874ac25ed179b9ddb091252a6dbe9b5c2`

---

## 1. Code Indexing Pipeline

**Entry:** `index_workspace` → `_index_workspace_impl` (server.py:881-968)
**Module:** `src/pipeline/indexing_pipeline.py`

```
File Discovery
  → Code Chunking (tree-sitter AST, CodeChunker)
    → Context Generation (OpenAI, optional — gated on OPENAI_API_KEY)
      → Standard Embedding (voyage-code-3, VoyageEmbedder)
      → Contextualized Embedding (voyage-context-3, ContextualizedEmbedder)
        → Multi-Vector Upsert to Qdrant (content_vec, title_vec, breadcrumb_vec)
          → BM25 Index Build (in-memory + pickle to disk)
            → Snapshot Persist (snapshot.json, chunk_snapshot.json)
```

### Gating
| Gate | Condition | Default | Effect |
|------|-----------|---------|--------|
| Context generation | `OPENAI_API_KEY` set | Disabled | Context snippets omitted from embeddings |
| Voyage API key | `VOYAGE_API_KEY` or `VOYAGEAI_API_KEY` | Required | Hard fail if absent |
| Max files | `max_files` parameter | None (unlimited) | Caps file discovery |
| Include patterns | `include_patterns` parameter | `["*.py", "*.js", "*.ts", "*.tsx"]` | Limits file types |
| Exclude patterns | `exclude_patterns` parameter | `["*test*", "*__pycache__*"]` | Excludes paths |

### BM25 Index Build (post-indexing)
After vector indexing, BM25 is built from all Qdrant payloads and persisted to `~/.dope-context/snapshots/{hash}/bm25_index.pkl`. Non-fatal on failure — dense search still works.

---

## 2. Docs Indexing Pipeline

**Entry:** `index_docs` → `_index_docs_impl` (server.py:1552-1585)
**Module:** `src/pipeline/docs_pipeline.py`

```
Document Discovery (*.md, *.pdf, *.html, *.txt)
  → Document Processing (DocumentProcessor — multi-format)
    → Chunking
      → Contextualized Embedding (voyage-context-3)
        → Upsert to Qdrant docs_{hash} collection (content_vec, title_vec, breadcrumb_vec)
```

### Gating
| Gate | Condition | Default | Effect |
|------|-----------|---------|--------|
| Voyage API key | Same as code pipeline | Required | Hard fail |
| Include patterns | `include_patterns` parameter | `["*.md", "*.pdf", "*.html", "*.txt"]` | Limits doc types |

---

## 3. Code Search Pipeline

**Entry:** `search_code` → `_search_code_impl` (server.py:1026-1310)

```
ADHD Dynamic top_k (get_dynamic_top_k)
  → Workspace Resolution
    → API Key Validation
      → Collection Existence Check
        → Query Embedding (voyage-code-3, 3 vectors: content, title, breadcrumb)
          → Hybrid Search (dense multi-vector + BM25 RRF fusion)
            → [Optional] Voyage Reranking (top-50 → top-k)
              → Token Budget Truncation (9000 default, 2000 chars/item)
                → [Optional] Code Graph Enrichment (Serena, top 5)
                  → Return results
```

### Error Handling Path
Each stage has explicit error handling returning structured error dicts:
1. API key missing → `{error: "Voyage API key...", help: "Set VOYAGE_API_KEY..."}`
2. Collection empty → `{error: "Collection '...' is empty", help: "Run index_workspace..."}`
3. Collection inaccessible → `{error: "Collection '...' not found", details: "..."}`
4. Embedding failed → `{error: "Query embedding failed", help: "Check VOYAGE_API_KEY..."}`
5. Search failed → `{error: "Vector search failed", query: "...", collection: "..."}`
6. Reranking failed → Falls through to unreranked results (non-fatal)
7. Graph enrichment failed → Returns unenriched results (non-fatal)

### Search Profiles
| Profile | content_weight | title_weight | breadcrumb_weight | Evidence |
|---------|---------------|-------------|-------------------|----------|
| `implementation` | Default | Default | Default | `SearchProfile.implementation()` |
| `debugging` | Default | Default | Default | `SearchProfile.debugging()` |
| `exploration` | Default | Default | Default | `SearchProfile.exploration()` |

---

## 4. Docs Search Pipeline

**Entry:** `docs_search` → `_docs_search_impl` (server.py:1624-1773)

```
Workspace Resolution
  → API Key Validation
    → Query Embedding (voyage-context-3, single embedding → all 3 vector slots)
      → Dense Search (DocumentSearch.search_documents)
        → Per-Item Truncation (max_content_length chars)
          → Token Budget Truncation (9000 default)
            → Provenance Enrichment (rank, source_uri, chunk_id, snippet)
              → Return results
```

### Gating
- No reranking for docs (code: `rerank_used: false`)
- No BM25/hybrid for docs (dense only)
- `filter_doc_type` optional filtering
- `max_content_length` defaults to 2000 chars

---

## 5. Unified Search Pipeline (search_all)

**Entry:** `search_all` → `_search_all_impl` (server.py:2008-2118)

```
Workspace Resolution
  → Decision Config Loading (decision_sync_config.json)
    → Trinity Boundary Check
      → Budget Split (code_top_k + docs_top_k + decision_top_k)
        → Parallel Execution:
          ├── _search_code_impl (reranking=False, budget=4000 or 3200)
          ├── _docs_search_impl (budget=4000 or 3200, max_content=1500)
          └── [if enabled] _search_decisions_impl (via dopecon-bridge HTTP)
        → Combine results with Trinity boundary metadata
```

### Budget Split Logic (server.py:2030-2042)
| Decisions Enabled | code_top_k | docs_top_k | decision_top_k | code_budget | docs_budget |
|-------------------|-----------|-----------|---------------|-------------|-------------|
| No | top_k/2 | top_k - code | 0 | 4000 | 4000 |
| Yes | (remaining)/2 | remaining - code | min(limit, top_k/3) | 3200 | 3200 |

### Trinity Boundary Gating (server.py:2022-2028)
Decision search is enabled only when ALL conditions are met:
1. `include_decisions=True` (parameter)
2. `decision_config.enabled=True` (persisted config)
3. `decision_config.auto_include_in_search_all=True` (persisted config)
4. `requested_top_k >= 3` (minimum budget)

---

## 6. Decision Search Sub-Pipeline

**Entry:** `_search_decisions_impl` (server.py:1904-1959)

```
Decision Config Loading
  → Config.enabled Check (early exit if False)
    → Bridge URL Resolution (config or DOPECON_BRIDGE_URL)
      → HTTP GET to {bridge_url}/kg/decisions/search?text={query}&limit={limit}
        → Response Normalization ({id, summary, timestamp, source: "conport"})
          → Return (empty array on any failure)
```

### Gating
- 5-second HTTP timeout (aiohttp.ClientTimeout)
- Silent failure (returns empty list on any error)
- Decision limit clamped: `_normalize_decision_limit()` → `max(1, min(parsed, 10))`

---

## 7. Autonomous Indexing Controller

**Entry:** `start_autonomous_indexing` / `start_autonomous_docs_indexing`
**Module:** `src/autonomous/autonomous_controller.py`

```
AutonomousController.start()
  → WatchdogMonitor (file system events)
    → DebouncedFileHandler (5s default debounce)
      → IndexingWorker (async queue consumer)
        → index_callback (→ _index_workspace_impl)
  → PeriodicSync (600s default interval)
    → sync_callback (→ _sync_workspace_impl)
```

### Lifecycle States
| State | Transition | Evidence |
|-------|-----------|----------|
| Inactive | → `start()` | No controller in `_active_controllers` |
| Running | `start()` → active | Watchdog, Worker, PeriodicSync all started |
| Stopped | `stop()` → inactive | All components stopped, removed from registry |
| Already running | `start()` called when active | Returns `{status: "already_running"}` |

### Registry
- Code controllers keyed by `str(workspace)` (server.py:2520)
- Docs controllers keyed by `f"{workspace}:docs"` (server.py:2746)
- Global dict: `AutonomousController.get_active_controllers()` (class-level)

---

## 8. Autoindex Bootstrap Pipeline

**Entry:** `POST /autoindex/bootstrap` → `_run_workspace_autoindex_bootstrap` (server.py:667-746)

```
Workspace Signature Computation (git HEAD or mtime fallback)
  → Marker Check (autoindex_bootstrap.json)
    → [if not bootstrapped or force=True]:
      ├── _index_workspace_impl (full code reindex)
      ├── _index_docs_impl (full docs reindex)
      └── Write bootstrap marker
    → Start Autonomous Code Indexing
    → Start Autonomous Docs Indexing
    → Return combined status
```

### Idempotence Gate
- Marker file: `~/.dope-context/snapshots/{hash}/autoindex_bootstrap.json`
- Skip when: `marker.snapshot_signature == current_signature AND marker.status == "completed"`
- Force: `force=True` bypasses idempotence check
- Signature: `git:{HEAD_SHA}` or `mtime:{epoch}` or `path:{workspace}`

### Concurrency
- One bootstrap task per workspace (`_autoindex_bootstrap_tasks` dict)
- `asyncio.create_task()` for async execution
- `wait_for_completion=True` blocks until done

---

## 9. Sync/Incremental Pipeline

**Entry:** `sync_workspace` → `_sync_workspace_impl` (server.py:2184-2347)
**Module:** `src/sync/file_synchronizer.py`

```
FileSynchronizer.check_changes()
  → SHA256 Snapshot Comparison
    → ChangeSet (added, modified, removed lists)
      → [if auto_reindex=True]:
        ├── Index added+modified files (IndexingPipeline)
        ├── Delete removed file vectors (vector_search.delete_points)
        └── Rebuild BM25 index
      → [else]: Report changes only
```

---

## 10. ADHD Dynamic Top-K

**Entry:** `get_dynamic_top_k` (server.py:313-339)

```
_get_adhd_config() singleton init
  → Feature flag check (FEATURE_ADHD_ENGINE_DOPE_CONTEXT)
    → [if enabled]: adhd_config.get_max_results(user_id)
      → scattered: 5 | focused: 15 | hyperfocused: 40
    → [if disabled]: fallback to requested_top_k
```

### Gating
- Feature-flagged via `FEATURE_ADHD_ENGINE_DOPE_CONTEXT` Redis flag
- Requires ADHD Engine service running
- Graceful degradation on any failure (returns original top_k)

---

## 11. Token Budget Control

**Module:** `src/utils/token_budget.py`

| Parameter | Default | Evidence |
|-----------|---------|----------|
| Safe budget | 9000 tokens | `server.py:1033` (search_code), `server.py:1630` (docs_search) |
| MCP limit | 10,000 tokens | token_budget.py (10% headroom) |
| Per-item max chars (code) | 2000 | `server.py:1242` |
| Per-item max chars (docs) | 2000 | `server.py:1629` (default), 1500 for search_all |
| Unified code budget | 4000 / 3200 | `server.py:2033-2042` |
| Unified docs budget | 4000 / 3200 | `server.py:2033-2042` |

### Truncation Behavior
- Items are dropped from the end until under budget
- Each item's text field is truncated to `per_item_max_chars`
- Returns `TruncationResult` with metadata (truncated, final_count, original_count, estimated_tokens, budget_used_pct)
