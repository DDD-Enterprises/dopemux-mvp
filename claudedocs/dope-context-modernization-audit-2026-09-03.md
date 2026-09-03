---
title: dope-context Modernization Audit — models, chunking, preprocessing, indexing, retrieval
date: 2026-09-03
author: Claude (Fable 5.1) + 4 audit subagents (Sonnet/Opus) + 1 researcher
scope: services/dope-context (source, tests, container, live Qdrant)
status: AUDIT ONLY — no source files modified
supersedes-context: services/dope-context/docs/04-explanation/dope-context-post-merge-audit-pr-1112-2026-07-26.md (F-001..F-017)
---

# 0. Headline verdict

**Models: mostly current. Pipeline: not.** The Voyage side (`voyage-context-4` for content, `voyage-code-3`
for title/breadcrumb, `rerank-2.5`) is correctly wired, manifest-gated, and matches what the container runs.
The LLM context generator is stale (`gpt-5-mini`, mis-budgeted for a reasoning model) and two of three
generator modules are dead code on retired model IDs.

But the surrounding chunking → preprocessing → indexing → retrieval chain has **11 blocker-class defects**
that make retrieval quality and cost far worse than the model choice would suggest. The three that matter most:

1. **Retrieval is silently un-retryable and lossy.** Every Voyage client is built with the SDK default
   `max_retries=0`; a single 429/503 during indexing is swallowed into `[], []` and the file is absent from the
   index with no error surfaced.
2. **The index accumulates ghosts and can be quietly cross-model.** Positional chunk IDs + no per-file delete
   means every edit leaks stale chunks forever; the documented `voyage-context-3` rollback env var re-creates
   the original F-001 cross-model split *on the query side only*, and the response reports the wrong model.
3. **Cost/latency is dominated by pipeline waste, not model price.** Whole-file `module` chunks (≈2× content
   amplification), a hard-coded 2 s sleep per file, one OpenAI request per chunk with unbounded concurrency,
   the safe exclude list overridden so `.venv`/`.worktrees`/`node_modules` get indexed, BM25 unpickled from
   disk on every search, docs storing the identical vector three times.

There is **no retrieval-quality measurement** (no golden set, recall@k, MRR, nDCG) anywhere, so none of the
above would be caught by CI. The test suite is green (115 passed / 2 skipped / 1 xfail) because it tests
contracts and invariants, not relevance.

**Live-state fact that changes what "fix and re-index" means:** the running container is scoped to
`/workspaces/dNh_CRM`, and the only Qdrant collection (`code_2bd1584a_7a3fda64c982`) holds **1 point**.
There is no indexed collection for `dopemux-mvp` at all. Re-indexing this repo is a cold start, not a migration.

# 1. Scope and method

**Inspected (direct, by me):** `src/embeddings/{model_registry,voyage_embedder,contextualized_embedder}.py`,
`src/rerank/voyage_reranker.py`, `src/context/openai_generator.py`, `src/preprocessing/code_chunker.py`,
`src/search/{dense_search,hybrid_search}.py`, `src/pipeline/{indexing_pipeline,docs_pipeline}.py`,
`src/mcp/server.py` (search/index/sync paths), `src/index_profile.py`, `src/utils/token_budget.py`,
`Dockerfile`, `constraints.txt`, `config/multi_index_config.yaml`, `tests/`.

**Delegated (4 audit subagents, each report spot-checked by me at its top 4–5 claims before inclusion):**
embeddings/rerank/context-gen; chunking/preprocessing/pipelines; retrieval/search/rerank; sync/autonomous +
test run + deployment state. **Researcher subagent:** live vendor model/pricing verification (§2).

**Environments probed:** harness/mise Python 3.12.13 (`voyageai 0.3.7`, no `tree_sitter`, no `rank_bm25`);
container `mcp-dope-context` (Python 3.11, `voyageai 0.5.0`, `tree_sitter 0.26.0`, `rank-bm25 0.2.2`,
`qdrant-client 1.19.0`, `anthropic 1.3.0`); Qdrant at `localhost:6333`.

**Verdict labels.** `VERIFIED` = I directly re-ran the grep/probe. `CONFIRMED` = subagent produced file:line
evidence I did not independently re-run. `PLAUSIBLE` = reasoned from code, not executed.

# 2. Models — what is wired vs what is current

## 2.1 Wired today (VERIFIED)

| Role | Model | Where | Container env |
|---|---|---|---|
| Code content (`content_vec`) | `voyage-context-4` (contextualized endpoint, 1024-dim, float) | `model_registry.py:113`, `index_profile.py` | `DOPE_CONTEXT_CONTEXTUAL_EMBED_MODEL=voyage-context-4` |
| Code title/breadcrumb | `voyage-code-3` (embeddings endpoint, 1024-dim) | `model_registry.py` | `DOPE_CONTEXT_CODE_EMBED_MODEL=voyage-code-3` |
| Docs content | `voyage-context-4` | same | `DOPE_CONTEXT_DOC_EMBED_MODEL=voyage-context-4` |
| Rerank | `rerank-2.5` (600k-token / 1000-doc envelope) | `voyage_reranker.py:23-26` | `DOPE_CONTEXT_RERANK_MODEL=rerank-2.5` |
| LLM contextual prefix | `gpt-5-mini` via `chat.completions`, `max_completion_tokens=200`, no `reasoning_effort` | `openai_generator.py:59,141-142` | `OPENAI_API_KEY` set in container |
| (dead) | `claude-3-5-haiku-20241022`, `temperature=0.0`, Claude-3-Haiku pricing constants | `claude_generator.py:115,64-67,255` | never imported |
| (dead) | `xai/grok-code-fast-1` | `grok_generator.py:46` | never imported |

Registry also carries `voyage-4`, `voyage-4-large`, `voyage-4-lite`, `voyage-3-lite`, `voyage-context-3`,
`rerank-2.5-lite`; all seven Voyage IDs resolve real HF tokenizer repos in-container (CONFIRMED), so the
Voyage-4 family IDs are real, not invented.

## 2.2 Vendor-current check (researcher subagent)

> **PENDING** — researcher subagent `a25e699a4f147985a` still running at time of writing. This section will
> be filled with: latest Voyage embedding/contextualized/rerank model IDs + pricing + URLs; whether
> `voyage-context-4` / `voyage-code-3` / `rerank-2.5` are superseded; current cheapest OpenAI chat model IDs
> for short context-generation calls (is `gpt-5-mini` superseded by a 5.5/5.6 -mini/-nano?), with prompt-cache
> support. Anything not confirmable will be marked UNVERIFIED.

What I already know without the researcher: a web search earlier in this session surfaced GPT-5.5 and GPT-5.6
family IDs, so `gpt-5-mini` is at minimum not the newest tier (exact successor ID: UNVERIFIED until §2.2 lands).
The Anthropic ID in `claude_generator.py` is definitively retired (current: `claude-haiku-4-5`,
`claude-sonnet-5`, `claude-opus-5`), and its `temperature` parameter is rejected by 4.6+ models.

## 2.3 Model-level findings

| # | Sev | Verdict | Finding | Fix |
|---|---|---|---|---|
| M1 | HIGH | PLAUSIBLE | `gpt-5-mini` with `max_completion_tokens=200` and no `reasoning_effort`: reasoning tokens consume the cap first → empty `content` → `AttributeError` on `.strip()` → caught at `openai_generator.py:173` → placeholder `f"Code from {file_path}"` is embedded as if real context. Run reports success. | `reasoning_effort="minimal"`, cap ≥1000, treat empty content as failure (count, don't substitute). |
| M2 | HIGH | VERIFIED | Context prompt (`_build_prompt`, `openai_generator.py:217-236`) sends only path + line range + chunk body — no imports, module docstring, or parent class. This is *not* Anthropic-style contextual retrieval (whole-doc situating); it is a per-chunk paraphrase. `voyage-context-4` already sees all sibling chunks, so the LLM prefix adds little and costs one call per chunk. | Either supply file-level context (imports/docstring/`parent_symbol`) or drop the LLM prefix for code and rely on the contextualized embedder. Measure with §6 golden set before deciding. |
| M3 | HIGH | CONFIRMED | `claude_generator.py` + `grok_generator.py` dead, retired IDs, wrong pricing (3-Haiku prices for 3.5-Haiku, ~3.2× under-report). | Delete both, or update to `claude-haiku-4-5`, drop `temperature`, read pricing from registry. |
| M4 | LOW | PLAUSIBLE | OpenAI pricing table: `gpt-5-mini` row is byte-identical to `gpt-4o-mini` (`0.15/0.60`) — likely copied, unsourced. Voyage-4 prices unsourced. All feed `total_cost_usd`. | `# verified <date> <url>` per row, as `RERANK_MAX_QUERY_TOKENS` already does. |
| M5 | MEDIUM | VERIFIED | `voyageai 0.3.7` on the repo's own mise interpreter lacks `enable_auto_chunking`; `contextualized_embedder.py:234` always sends it → every contextualized embed hard-fails outside Docker. Container pins 0.5.0 so prod is fine. | Omit kwarg when `False`; assert `voyageai>=0.5.0` at import. |

# 3. Findings by area

Severity: **BLOCKER** = wrong results or unbounded cost/data loss on the default path; **HIGH** = materially
degrades quality/cost; **MEDIUM** = efficiency/telemetry; **LOW** = hygiene.

## 3.1 Embeddings, rate limiting, caching

| # | Sev | Verdict | File:line | Finding | Fix |
|---|---|---|---|---|---|
| E1 | BLOCKER | VERIFIED | `voyage_embedder.py:129`, `contextualized_embedder.py:109`, `voyage_reranker.py:112` | `AsyncClient(api_key=api_key)` → SDK default `max_retries=0, timeout=None` (signature checked). No retry/backoff layer anywhere. `indexing_pipeline.py:377` swallows into `[], []`, `processed_files` still increments → file silently missing. | `AsyncClient(api_key, max_retries=5, timeout=120.0)`; make `_process_file` re-raise or record transport failures. |
| E2 | HIGH | CONFIRMED | `indexing_pipeline.py:300-322`, `index_profile.py:222`, `model_registry.py:185-203` | Fingerprint/manifest omits whether LLM context was used and by which model. Index built with vs without `OPENAI_API_KEY` embeds different strings, same fingerprint → mixed vectors pass `compare_collection_manifests`. | Add `context_provider` (`"openai:<model>"`/`"none"`) to `VectorProfile.fingerprint_payload()` and manifest. |
| E3 | HIGH | VERIFIED | `openai_generator.py:209-215` | `asyncio.gather` over every chunk, no semaphore; `IndexingConfig.context_batch_size=10` never read. 400-chunk file → 400 concurrent requests → 429s → placeholder context embedded. | Semaphore sized from `context_batch_size`; propagate failures. |
| E4 | MEDIUM | CONFIRMED | `voyage_embedder.py:140-154`, `contextualized_embedder.py:148-162` | RPM-only limiter (default 2000); no TPM accounting although token counts are computed. `asyncio.sleep` held under `_rate_limit_lock` serializes all callers. | Rolling `(ts, tokens)` deque gating on RPM+TPM; release lock before sleeping. |
| E5 | MEDIUM | CONFIRMED | `contextualized_embedder.py:342-348,465-469`; `model_tokenizer.py:155-158` | A single document > `max_request_tokens` (120k) raises; in `embed_documents_batch` it kills the whole batch. Pipelines call `embed_document` once per file with all chunks + LLM prefix. | Partition one document across requests, or fail per-document. |
| E6 | MEDIUM | CONFIRMED | `voyage_embedder.py:116,391` | `max_batch_size=128` caps every batch though registry allows 1000; `IndexingConfig.embedding_batch_size=8` dead. Title/breadcrumb texts are tiny → ~8× request count. | Default to `spec.max_request_inputs`. |
| E7 | MEDIUM | CONFIRMED | `indexing_pipeline.py:300-322` | 3 Voyage requests per file, serial; title/breadcrumb never accumulated across files. | Accumulate and flush at registry batch size. |
| E8 | MEDIUM | CONFIRMED | `voyage_embedder.py:349-364` | No intra-batch dedupe by cache key (`__init__`, `main`, `run` repeat across hundreds of files). | Dedupe `uncached_requests` by key, fan out response. |
| E9 | MEDIUM | CONFIRMED | `model_tokenizer.py:57,102-127`; `server.py:392-407` | `VoyageTokenCounter._cache` unbounded (missed by F-012); reranker's counter lives process-lifetime via `lru_cache`. | Same bounded-eviction as sibling caches. |
| E10 | LOW | CONFIRMED | `openai_generator.py:118-127` | `total_requests` incremented only on miss → `cache_rate` > 1.0; `_cache` unbounded, expired entries never deleted. | Increment at top; bound. |
| E11 | LOW | CONFIRMED | `contextualized_embedder.py:386,507` | Returned texts re-tokenized though `counts` computed just before. | Reuse when `returned_texts == chunks`. |
| E12 | LOW | CONFIRMED | `voyage_embedder.py:226-243`, `contextualized_embedder.py:241-263` | Bare `TypeError` catch conflates SDK-internal errors with unknown-kwarg. | Gate on `inspect.signature` at construction. |

## 3.2 Chunking and preprocessing

| # | Sev | Verdict | File:line | Finding | Fix |
|---|---|---|---|---|---|
| C1 | BLOCKER | VERIFIED | `code_chunker.py:221` | Python target types include `"module"` → whole file emitted as a `block` chunk **plus** every class/function; classes also re-contain their methods. Subagent measured `server.py`: 74 chunks, 217,336 chars from 110,731 (1.96×); largest chunk = entire 3,298-line file (~27.7k tokens). Paid twice at Voyage, once more per chunk at OpenAI; whole-file chunk out-scores every specific chunk in that file. | Drop `"module"`; if a file-level chunk is wanted, synthesize a *residue* chunk of uncovered top-level lines. |
| C2 | BLOCKER | VERIFIED | `code_chunker.py:55,324` | `max_chunk_tokens=1024` is enforced **only** in the line fallback (`:324` is the sole comparison). AST chunks unbounded → chunk > `per_input_tokens` (32k) raises in `embed_document` → caught at `indexing_pipeline.py:377` → **whole file dropped**. ≥4 tracked files exceed on size alone. | Split oversize nodes (by body statement, then lines); guard per-file sum; catch per chunk-group, not per file. |
| C3 | HIGH | CONFIRMED | `code_chunker.py:158-165` | TS/TSX class names lost (`type_identifier` not accepted) → `symbol_name=None` → `title_texts="class_3"`, breadcrumb `"path:3"` — two of three vectors carry no signal for every TS class. | Use `child_by_field_name("name")`; accept `type_identifier`/`property_identifier`. |
| C4 | HIGH | CONFIRMED | `code_chunker.py:227-247` | JS/TS: no `method_definition`, no `interface_/type_alias_/enum_declaration`, no top-level/program chunk → methods and top-level code unindexed (inverse of C1). Only `python/javascript/typescript/tsx` have grammars; go/rust wheels are installed in-container but unused. | Add node types; unwrap `export_statement`; wire go/rust. |
| C5 | HIGH | VERIFIED | `document_processor.py:143,154,173` | `"\\n\\n".join(...)` — literal backslash-n two-char sequences, not newlines. DOCX/HTML collapse to one paragraph and the garbage is embedded/returned. | `"\n\n"`, `"\n"`. |
| C6 | BLOCKER | VERIFIED | `document_processor.py:329` | Markdown header regex `^(#{1,6})\s+(.+)` has no fence state → `# comment` inside ```` ```bash ```` becomes an H1, evicting the real heading from `section_hierarchy`; code blocks split mid-fence. 18,759 `.md` files in repo, most with fences. | Track ```` ``` ````/`~~~` state; skip header match inside fences. |
| C7 | HIGH | CONFIRMED | `document_processor.py:336,393,355-362` | Sections < 100 chars dropped entirely; on mid-doc guard failure `current_section` isn't reset while hierarchy is → text emitted under the *next* section's path. | Always flush/reset on header; merge undersized forward carrying hierarchy. |
| C8 | HIGH | CONFIRMED | `code_chunker.py:139-142`, `server.py:1466,1282` | `language` payload is the bare suffix (`py`/`ts`); `search_code` docstring promises `python`/`typescript` → documented filter values return zero results. | Normalize suffix → canonical name. |
| C9 | MEDIUM | CONFIRMED | `document_processor.py:365,338-344` | Section header duplicated at top of every markdown chunk. | Prepend `current_hierarchy[:-1]` only. |
| C10 | MEDIUM | CONFIRMED | `document_processor.py:510` | YAML frontmatter embedded raw, never parsed; `title` = filename stem. | Strip/parse; map `title`/`tags`. |
| C11 | MEDIUM | CONFIRMED | `docs_pipeline.py:260-265`, `document_processor.py:482-488` | `chunk_overlap` dead on the structured path that actually runs (effective 0). Defensible for `voyage-context-4`, but undocumented. | Document as intentional or implement. |
| C12 | MEDIUM | CONFIRMED | `code_chunker.py:319-346` | Line fallback can't split one long line (minified JS) → C2 file-drop; ignores `target_/min_chunk_tokens`; zero overlap. | Hard-split lines > max. |
| C13 | MEDIUM | CONFIRMED | `indexing_pipeline.py:342-358` | Code payload discards `parent_symbol`, `chunk_type`, `content_hash`, qualified name; breadcrumb = `file.symbol` (class dropped). | Add fields; build breadcrumb from qualified name. |
| C14 | MEDIUM | VERIFIED | `code_chunker.py:46,320` | `tokens_estimate = len//4` while a real `VoyageTokenCounter` exists; fallback chunker uses the same estimate for its only size check. | Use the counter (or `tiktoken` as docs do). |
| C15 | HIGH | CONFIRMED | `docs_pipeline.py:72`, `document_processor.py:134-135`, `pyproject.toml` | `.pdf` advertised in defaults and docstring; `PyPDF2` not installed in container nor declared → every PDF is an `error_documents` count. `magic` likewise absent. | Add `pypdf>=4` to `[services]` and migrate import, or remove `*.pdf` from defaults. |
| C16 | LOW | CONFIRMED | `code_chunker.py:54-62`, `indexing_pipeline.py:69-70` | Dead knobs: `target_chunk_tokens`, `min_chunk_tokens`, `prefer_semantic_boundaries`, `include_parent_context`, `context_batch_size`, `embedding_batch_size`. Live path constructs `CodeChunker()` with no config (`server.py:945`). | Wire or delete. |
| C17 | LOW | CONFIRMED | `config/multi_index_config.yaml` | Loaded by nothing (zero `yaml` imports in service); contradicts runtime on chunk sizes, chunker, context method, batch size; `api`/`chat` indices have no implementation. | Load it or move to `docs/` as a design sketch. |
| C18 | LOW | CONFIRMED | `tests/` | No `test_code_chunker.py`, no `test_document_processor.py` → C1–C12 invisible to CI. | Add. |

## 3.3 Indexing, sync, autonomous

| # | Sev | Verdict | File:line | Finding | Fix |
|---|---|---|---|---|---|
| I1 | BLOCKER | VERIFIED | `server.py:971` | `exclude_patterns=exclude_patterns or ["*test*", "*__pycache__*"]` overrides the 13-entry safe default in `IndexingConfig` (`.venv`, `.worktrees`, `node_modules`, `dist`, `build`, `site-packages`…). Used by the `index_workspace` tool **and** every autonomous `index_callback`. Subagent measured on this repo: 277,172 glob matches → 220,848 survive (135,659 in `.venv`, 143,978 in `.worktrees`, 49,575 in `node_modules`) vs 3,072 tracked code files. No `.gitignore` handling anywhere. `_sync_workspace_impl(auto_reindex=True)` does *not* override → the two reindex paths disagree. Docstring at `:1040` claims node_modules/.git excluded. | Delete the `or [...]`; add `git check-ignore --stdin` / `pathspec`; segment-based matching. |
| I2 | BLOCKER | VERIFIED | `indexing_pipeline.py:190-193,480`; `sync/incremental_indexer.py:199,239` | Chunk ID = `sha256(f"{file_path}:{start}:{end}")` (absolute path, positional). One inserted line re-IDs every chunk below; old points never deleted (`index_workspace` only upserts; `get_chunks_to_delete_for_file`/`remove_file_mapping` have zero callers). Stale `raw_code` stays searchable forever. Docs pipeline gets this right (`docs_pipeline.py:320-322`). | ID on `(relative_path, qualified_name, content_hash)` or delete-by-`file_path` filter before upsert. |
| I3 | HIGH | VERIFIED | `server.py:2516-2530` | Removed-file deletion also matches by **basename** → deleting `services/a/utils.py` deletes every indexed `utils.py`, `__init__.py`, `models.py`… Also a full scroll + client-side match. | Drop basename branch; server-side `FilterSelector` with `MatchAny`. |
| I4 | HIGH | VERIFIED | `server.py:2789-2793,3020-3026`; `autonomous_controller.py:157` | Autonomous `index_callback(ws_path, changed_files)` never passes `changed_files` → every watchdog/periodic trigger is a **full workspace reindex**. README:448 "only changed files reindexed" is false for the autonomous path. | Thread `changed_files` into the scoped delete+reindex logic that `_sync_workspace_impl` already has. |
| I5 | HIGH | VERIFIED | `indexing_pipeline.py:429,455` | `delay_per_file = 2.0` s, serial, unconditional (even with no context generator). Comment cites Anthropic 50 RPM; live generator is OpenAI. 3,072 files = 102 min sleeping; at I1's 220k files = 122 h. | Delete; bounded `asyncio.Semaphore` over files; rely on embedder limiters. |
| I6 | HIGH | CONFIRMED | `indexing_pipeline.py:424,435,464` | All vectors for the workspace held in RAM until the loop finishes (~1.8 GB at 3k files). | Flush every `qdrant_batch_size`. |
| I7 | HIGH | CONFIRMED | `indexing_pipeline.py:237-375`; `server.py:952-965,1794-1800` | No content-hash skip; fresh embedders per call → 24 h cache always cold; full cost on every run for unchanged content. `content_hash` computed and used for nothing. | Load prior snapshot, skip unchanged files/chunks; hoist embedders to singletons. |
| I8 | HIGH | CONFIRMED | `server.py:2504-2510`; `indexing_pipeline.py:420,496` | `sync_workspace(auto_reindex=True)` builds a fresh `ChunkSnapshot` scoped to changed files and saves it → every unchanged file vanishes from the snapshot. | Load-and-merge as `index_single_file` does (`:541-545`). |
| I9 | MEDIUM | CONFIRMED | `docs_pipeline.py:326-365` | Docs deleted from disk never removed from the docs collection (stale reconciliation only for still-discovered files). | Diff payload index vs visited set after loop. |
| I10 | MEDIUM | CONFIRMED | `server.py:973,1804,884,912,2485,2507` | `workspace_id` in three incompatible formats (16-hex vs absolute path). Latent (nothing filters on it yet). | `workspace_identity_from_path` at all sites. |
| I11 | MEDIUM | CONFIRMED | `file_synchronizer.py:129-154,166-206`; `watchdog_monitor.py:79-96` | Ignore matching is raw substring (`"dist" in path` excludes `distributed_lock.py`); full SHA-256 of every file every 10-min tick, no mtime/size short-circuit; `.venv` not excluded by *this* scanner's defaults. Three inconsistent ignore implementations. | One segment-based matcher + gitignore; stat pre-check. |
| I12 | MEDIUM | CONFIRMED | `watchdog_monitor.py:201-233,98-116` | Recursive OS watch over entire workspace before filtering (inotify limit risk); `FileMovedEvent.dest_path` ignored → renames orphan the old vector. | Exclude dirs at schedule time; handle `dest_path`. |
| I13 | MEDIUM | CONFIRMED | `server.py:1001-1013,2550-2562` | No lock across concurrent index runs; BM25 pickle written non-atomically (no tmp+rename, unlike the two snapshot writers). | `asyncio.Lock` per workspace; atomic write. |
| I14 | MEDIUM | CONFIRMED | `pipeline/docs_pipeline.py:311` | Docs write the **identical** vector into `content_vec`/`title_vec`/`breadcrumb_vec` → 3× storage, 3× HNSW, zero signal (fusion is provably `s·0.85+s·0.10+s·0.05 = s`). | Real title/breadcrumb embeds, or single-vector docs collection. |
| I15 | LOW | CONFIRMED | `server.py:938`/`indexing_pipeline.py:417`; `code_chunker.py:377`/`indexing_pipeline.py:439` | `create_collection` called twice per run (idempotent now); each file read from disk twice. | Drop pipeline-side call; return source text from `_process_file`. |
| I16 | LOW | CONFIRMED | `bridge_adapter.py`, `src/integration_bridge_connector.py` | Dead; the latter's import path points at a non-existent dir. | Delete. |

## 3.4 Retrieval, fusion, rerank, result shaping

| # | Sev | Verdict | File:line | Finding | Fix |
|---|---|---|---|---|---|
| R1 | BLOCKER | VERIFIED | `server.py:445-448,1159,1920`; `model_registry.py:168-182` | `_get_cached_contextualized_embedder(api_key)` builds `ContextualizedEmbedder(api_key, cache_ttl_hours=24)` — no `default_model`, so it defaults from `DOPE_CONTEXT_DOC_EMBED_MODEL` (`voyage-context-4`). `resolve_context_model` returns *configured* when requested is `voyage-context-3` and `ALLOW_LEGACY` unset. Under the documented rollback `DOPE_CONTEXT_CONTEXTUAL_EMBED_MODEL=voyage-context-3`, index embeds with context-3 (explicit `default_model`), **query embeds with context-4** — same dim/endpoint so Qdrant accepts; collection-name digest can't catch it; response reports `content_vec_model=voyage-context-3`. F-001 re-created on the read side. `test_vector_space_invariants.py` never permutes this env var and its assertion is tautological; the `xfail(strict=True)` guard asserts a hardcoded `"voyage-code-3"` literal so it will xfail forever. | Cache key on `(api_key, model, dim, dtype)` and pass profile values; assert `response.model == profile.model` after every query embed, fail closed. Fix the test. |
| R2 | BLOCKER | VERIFIED | `server.py:1165-1188`; `hybrid_search.py:111-141,177-182` | BM25 (`rank_bm25.BM25Okapi`) is built only on full index / `auto_reindex=True`, pickled to `~/.dope-context/snapshots/<hash>/bm25_index.pkl`, and **re-read + `pickle.loads` on every search**, synchronously in an async handler, including every chunk's `raw_code`. `get_document` is a linear scan called per fused id. At 50k chunks: hundreds of MB deserialized per query, multi-second, event-loop-blocking. `pickle.loads` on a user-writable cache = RCE surface (code comments acknowledge). | Qdrant-native sparse vectors + Query API `prefetch` + `FusionQuery(RRF)`: one round trip, per-upsert maintenance, no process state. Deletes R2, R6, R8, I13 at once. |
| R3 | HIGH | VERIFIED | `server.py:1207,1313`; `voyage_reranker.py:101,238` | `top_n_display=10` default; `_split` slices to it; handler then `[:top_k]` → `top_k>10` silently clipped to 10 with reranking on (documented max 50). `cached_results` computed and never returned. | Pass `top_n_display=top_k`; include in cache key. |
| R4 | HIGH | VERIFIED | `dense_search.py:86-97`; `server.py:1327-1330,1375` | `SearchResult` has no `start_line`/`end_line`; handler uses `getattr(..., None)` → **always `null`** on both paths. Payload has them. | Read from `payload`, or add fields. |
| R5 | HIGH | VERIFIED | `dense_search.py:455-493` | Three `query_points` calls are sequential `await`s (not `gather`); fusion sums weighted DOT scores from **two different models** (context-4 vs code-3) with incomparable distributions; absent-from-list = 0 rather than unknown → rewards multi-list presence, lets implicit 0 beat a real negative. `hnsw_config` applied only to `content_vec`. | Single Query API call with `prefetch` per named vector + RRF; uniform HNSW. |
| R6 | HIGH | CONFIRMED | `hybrid_search.py:267-323` | RRF computed, then discarded for candidate selection only; final order = `0.7·dense/max + 0.3·sparse/max` → BM25-only hits capped at 0.3, can never outrank dense (defeats exact-identifier queries); `score/max` ill-defined when BM25 max ≤ 0; `max()` recomputed inside loop; BM25 returns `top_k` even at score 0. | One fusion (RRF or weighted RRF); filter `score > 0`. |
| R7 | HIGH | CONFIRMED | `server.py:2429,2544-2560,2798`; `hybrid_search.py:305-320` | BM25 stale by default (autonomous `sync_callback` uses `auto_reindex=False`); fusion synthesizes results from BM25 alone → **deleted code served as live hits**. Docs lane has no sparse index at all (`fusion_strategy: dense`). | Superseded by R2. Never synthesize from BM25 alone. |
| R8 | MEDIUM | VERIFIED | `token_budget.py:35-36,254-274`; `server.py:1351-1352,1412-1413` | `budget_starvation` / `degraded_guarantee_applied` never assigned → always `false` on the MCP contract surface, including when degrade branch fires. Fabricated telemetry. | Set both in the degrade branch. |
| R9 | HIGH | VERIFIED | `server.py:1359`; `voyage_reranker.py:29,177-183` | `RerankQueryTooLargeError(ValueError)` documented as deliberately uncaught (F-014 fail-loud) but the only prod call site catches bare `Exception` → silent dense-order fallback. Invariant holds only in tests. | Catch the subclass separately and return an error payload. |
| R10 | HIGH | CONFIRMED | `voyage_reranker.py:58,229-258`; `server.py:1326,1354` | `RerankResponse.failure_reason` never populated → `rerank_failure_reason: null` next to `rerank_degraded: true`; cost tracker `add_request` runs before the mapping loop so a degraded response still bills. Reranker text = `context_snippet + content`, no file path/symbol. | Populate reason; move `add_request`; prepend path+symbol header. |
| R11 | MEDIUM | CONFIRMED | `server.py:1315-1333,1366-1379`; `dense_search.py:395-404` | No per-file dedupe (large file crowds out all others — worst case for a "max 10 results" ADHD product); no `score_threshold` anywhere. | Cap per file (2); threshold on fused score. |
| R12 | MEDIUM | CONFIRMED | `dense_search.py:139-175` | No quantization, no `on_disk`, no `optimizers_config`. 50k chunks × 3 × 1024 × 4 B = 614 MB RAM per workspace × N worktrees. | Scalar int8 quantization `always_ram=True`, originals `on_disk=True`. |
| R13 | MEDIUM | CONFIRMED | `server.py:341-365,1091,2272-2284` | ADHD `get_dynamic_top_k` *replaces* caller's `top_k` (not caps), breaking `search_all`'s code/docs budget split; `src/attention_aware_search.py` is dead and disagrees with the live mapping. | `min(requested, adhd_max)` once at tool boundary; delete dead module. |
| R14 | MEDIUM | CONFIRMED | `metrics_tracker.py:151-180,273-287` | Full JSON read+rewrite per search, blocking, unbounded, 3× per `search_all`; plaintext query log forever. | JSONL append off-loop; retention cap. |
| R15 | MEDIUM | CONFIRMED | `dense_search.py:134,545-598`; `server.py:779-789,1539-1543,1701-1708` | `AsyncQdrantClient` per call, never closed (a 10-workspace `get_index_status` leaks 21); `get_all_payloads` full scroll ×2 per sync with `raw_code`. | Shared client per URL with close; `FilterSelector` deletes. |
| R16 | MEDIUM | CONFIRMED | `server.py:411-430,433-448`; `dense_search.py:406-522` | Manifest gate (`_assert_compatible`) runs on writes only; `search()` never calls it; cached search instance built without a manifest. Read-side protection = collection-name digest only (defeated by R1). | Assert on first search per collection (cached). |
| R17 | LOW | CONFIRMED | `dense_search.py:443-451`; `server.py:1235-1263,1154,1993,1110-1115,474-486` | `__manifest__` `must_not` filter unindexed; query embeds sequential; profiles rebuilt 2–3× per search; docs `chunk_id=f"doc_chunk_{i}"` positional; error dicts counted in `total_results`; `_initialize_components` + globals unreachable dead code (~90 lines). | `HasIdCondition`; `gather`; cache profile; return point id; count errors separately; delete. |
| R18 | HIGH | CONFIRMED | `tests/` | **No retrieval-quality measurement anywhere** — no golden set, recall@k, MRR, nDCG. Nothing in R3–R7, R11, C1, I14 would be caught. | 30–50 query golden set from repo history → recall@10 / MRR gate in CI. |

## 3.5 Deployment and test-harness facts (VERIFIED)

- Container `mcp-dope-context` is **healthy and byte-identical to source** (MD5 of `model_registry.py`,
  `server.py` match), but scoped to `DOPEMUX_WORKSPACE_ROOT=/workspaces/dNh_CRM`.
- Qdrant `localhost:6333` has exactly one collection `code_2bd1584a_7a3fda64c982` (= `dNh_CRM` hash) with
  `points_count: 1`. **No collection exists for `dopemux-mvp`** (hash `3ca12e07`). Nothing here is
  currently serving real retrieval for this repo.
- Tests: `cd services/dope-context && mise exec -- python -m pytest tests -x -q` → **115 passed, 2 skipped,
  1 xfailed** (the xfail is the stale F-001 guard, see R1). Running from repo root fails collection
  (`No module named 'src.autonomous'`) — cwd issue, not a bug.
- `hybrid_search.py:11` imports `rank_bm25` unguarded; `server.py:75` imports it at module level → the
  service **cannot start on the repo's own mise interpreter** (masked by `conftest` stubs). Container has it.
- README claims not backed by code: incremental autonomous reindex (I4); "automatic cleanup" (I2/I9);
  eight named test files/dirs that don't exist; "encryption at rest / API-key auth / audit logging / content
  filtering" (no code); "78.7% cache hit rate, 94% satisfaction" (no metrics code).

# 4. What is already good (keep)

- `index_profile.py` — profile-digest-in-collection-name, fail-closed `assert_manifest_compatible`, legacy
  classification, index/query equality matrix. Structurally prevents the mixed-space class in the default config.
- Manifest sentinel inside the collection sharing the Qdrant volume lifecycle; excluded from search and
  `get_all_payloads` with a comment naming the consumers it would poison; 7 gate tests.
- `model_registry.py` centralizes real vendor limits and fails closed on unknown model/endpoint mismatch.
- `input_type` is correct on both sides (`document` index / `query` query) and validated fail-closed.
- `output_dimension`/`output_dtype` reach the API; fallbacks refuse to strip non-default shapes.
- Both embedding caches bounded (F-012), copy-on-read, keyed on model+input_type+dim+dtype(+chunking).
- `allocate_total_tokens` largest-remainder split preserves exact sums; `token_count_exact` never launders
  an estimate as exact; `_unavailable_models` correctly handles `lru_cache`-doesn't-memoize-exceptions.
- `return_documents` reranker bug is genuinely fixed (verified against 0.3.7 and 0.5.0 signatures).
- Docs pipeline idempotency: `uuid5` ordinal point IDs, contiguous-ordinal invariant, upsert-before-delete.
- Token-budget module: `max(bytes/3, lexical)` estimate, binary-search truncation at Unicode boundaries,
  never-return-empty guarantee.
- `code_aware_tokenizer` (camelCase/snake/digit boundaries, no stopwords) is a good BM25 tokenizer.
- Determinism: RRF ties by id, final `(-score, id)` sort, deterministic point/manifest IDs — tested.
- `clear_index` requires proof id + exact approval phrase. Dockerfile healthcheck `|| exit 1` with rationale.
- Scars (F-001…F-017) annotated at the exact lines — this is why the audit could be precise.

# 5. Remediation plan — three phases, in dependency order

**Phase 1 — stop the bleeding (correctness; small diffs; no schema change).**
E1 retries · I1 exclude override · C5 literal `\n` · C6 fence state · R4 start/end_line · R3 top_k clip ·
R9 fail-loud rerank · R8/R10 telemetry flags · I5 delete 2 s sleep · E3 semaphore · M1 `reasoning_effort` +
empty-content-as-failure · R1 embedder cache key + post-embed model assertion + fix the tautological test ·
I3 drop basename delete · C8 language normalization. Add `test_code_chunker.py`, `test_document_processor.py`.
*All Phase-1 items require a full re-index afterward (C-class changes chunk boundaries) — which is a cold start
anyway since no `dopemux-mvp` collection exists.*

**Phase 2 — make the index honest and incremental (schema bump → `CODE_CHUNKER_VERSION` v2 + manifest field).**
C1 drop `module` chunk · C2 size-bound AST chunks · C3/C4 TS/JS node types · C13 payload fields
(`parent_symbol`, `qualified_name`, `content_hash`, `chunk_type`) · I2 stable IDs + delete-by-file ·
I4 thread `changed_files` · I7 content-hash skip + singleton embedders · I8 snapshot merge · E2 `context_provider`
in fingerprint · I14 docs single-vector or real title/breadcrumb · C15 pypdf or drop `.pdf`.

**Phase 3 — replace the retrieval core (biggest quality + latency win; one design decision).**
R2/R5/R6/R7: Qdrant-native sparse vectors + Query API `prefetch` (content/title/breadcrumb dense + BM25 sparse)
+ server-side RRF, one round trip, per-upsert maintained; drop pickle, drop process-local BM25, drop raw-score
blending. R12 int8 quantization. R11 per-file cap + threshold. R18 **golden set + recall@10/MRR gate first** —
Phase 3 must be measured against Phase 2, not assumed. Decide M2 (keep/drop LLM prefix for code) on that
measurement, and swap `gpt-5-mini` for whatever §2.2 confirms as the current cheap tier.

Deferred/cleanup: M3 delete dead generators · I16 dead bridge modules · R13 dead attention module · R17
`_initialize_components` · C17 YAML · README claims (§3.5).

# 6. Governance block

**Change Summary:** None. Audit only; one new file (this report).
**Authority Used:** latest user instruction → runtime code (`services/dope-context/src/**`, container
`mcp-dope-context`, Qdrant `localhost:6333`) → tests → `README.md`/`config/multi_index_config.yaml` (found
to disagree with runtime; runtime wins) → prior audit `dope-context-post-merge-audit-pr-1112-2026-07-26.md`.
**Analysis Performed:** direct inspection + grep/sed of every file cited under VERIFIED; 4 audit subagents
each spot-checked at their top 4–5 claims (all passed); SDK signature probes on `voyageai` 0.3.7/0.5.0;
container env/MD5/pip probes; live Qdrant collection listing; pytest run.
**Validation Performed:** pytest `services/dope-context/tests` — **PASS** (115/2 skipped/1 xfail);
container health + image freshness — **PASS**; Qdrant reachability — **PASS**; retrieval-quality
measurement — **NOT_RUN** (no harness exists; R18); vendor model currency — **NOT_RUN** pending §2.2;
findings marked CONFIRMED/PLAUSIBLE — **NOT_RUN** by me (subagent evidence only).
**Remaining Uncertainty:** §2.2 model currency; subagent-measured counts (220,848 files, 1.96× amplification)
not re-run by me; M1 reasoning-token exhaustion is reasoned, not reproduced against the API.
**Files Touched:** `claudedocs/dope-context-modernization-audit-2026-09-03.md` (new).
**Git State:** untracked new file; no source changes; branch unchanged.
**Rollback Plan:** `rm claudedocs/dope-context-modernization-audit-2026-09-03.md`.
**Requested Next Step:** pick one — (a) authorize Phase 1 as a single PR against `services/dope-context`
(I'd start with E1, I1, C5, C6, R1, R4 — all ≤10-line diffs), (b) build the R18 golden set first so Phases 2–3
are measured, or (c) file this as Task Packets in the orchestrator and stop here.
