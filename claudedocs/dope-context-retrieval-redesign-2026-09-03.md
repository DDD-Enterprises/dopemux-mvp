---
title: dope-context Retrieval Stack — Target Design and Implementation Plan
date: 2026-09-03
author: Claude (Fable 5.1), session 89799646
status: PROPOSED — Revision 2.3; D1–D3 RULED by operator 2026-09-03 (see "Revision 2.3"); eval/ carve-out landed with ADR-226 (B12 closed); whole-repo benchmark NOT_RUN — blocked on OPENAI_API_KEY inside `mcp-dope-context` (empty) for the `Bhl` arm
base: origin/main 04be55535 (services/dope-context byte-identical to e07ff3efc)
branch: claude/dope-context-retrieval-redesign-2026-09-03
supersedes: nothing; extends claudedocs/dope-context-modernization-audit-2026-09-03.md
related-packets: TP-DOPECONTEXT-VECTOR-SPACE-0004 (DECISION_REQUIRED), -COLLECTION-GATE-0003, -TEST-HARNESS-0005, -SERVICE-HARDENING-0006, -VOYAGE4-REPAIR-0002 (AUTHORIZED_FOR_IMPLEMENTATION)
---

# 0. Reading guide (ADHD-first)

Three things to know, then details on request:

1. **Every stage has a confirmed defect** — 73 findings across four audits (§2). Nothing here is
   speculative; each finding has a file:line in the audit document.
2. **The models are one generation stale on code** — `voyage-code-3` → `voyage-code-4` (live-verified
   from the container today, §3.1) and the context generator `gpt-5-mini` is deprecated with a
   2026-12-11 shutdown → `gpt-5.6-luna`.
3. **Worktrees multiply cost by 23×** — identity is `md5(workspace_path)`, so each of the 23 checkouts
   of this repo gets its own collection pair and full re-embed. The target is one project-scoped,
   blob-content-addressed collection with worktree membership as payload (§4.1).

Decisions needed from you are in §8 (three, each with a recommendation). Wave 0 (benchmark harness)
needs none of them and costs < $0.10.

---

# 1. Authority and evidence base

| Layer | Source | Status |
|---|---|---|
| User instruction | "worktrees … optimal state … detailed design and implementation plan … most recent Voyage models … optimize every stage" | governs |
| Runtime code | `services/dope-context/src/**` at 04be55535 | inspected (4 audit subagents + spot-checks) |
| Live deployment | container `mcp-dope-context` (image == source, verified by MD5), Qdrant server **1.19.0**, `qdrant-client` **1.19.0**, `voyageai` **0.3.7** in harness / **0.5.0** in container | probed 2026-09-03 |
| Vendor facts | Voyage / Qdrant / OpenAI / Anthropic vendor pages, fetched 2026-09-03 by research subagent, URLs in audit appendix | verified unless marked UNVERIFIED |
| Packets | `task-packets/dope-context/TP-DOPECONTEXT-*.md` | read; statuses in §7.4 |
| Fleet design | `claudedocs/mcp-fleet-multi-instance-design-2026-07-28.md` §row "dope-context" | read; this design amends that row (§4.1) |
| PAL chain | `mcp__pal__*` | **NOT_RUN — PAL MCP not connected in this session** (ToolSearch surfaces no pal tools). Substitute: fresh adversarial-review subagent on this document, labelled as such in §9. |

Truth Order applied: runtime code outranks the audit prose, the README, and the archived benchmark
doc (`docs/archive/sessions/dope-context/benchmark-results.md`, which the earlier audit found unsourced).

---

# 2. Current state — one paragraph per stage, defects by ID

Defect IDs refer to `claudedocs/dope-context-modernization-audit-2026-09-03.md` (E = embeddings/rerank/
context, C = chunking/preprocessing, R = retrieval, S = sync/autonomous). Only BLOCKER/HIGH are listed
here; the audit holds all 73.

**Pre-processing / discovery.** The live MCP `index_workspace` path passes `exclude_patterns=None`, so the
dataclass default (`.venv`, `node_modules`, `.worktrees`, `dist`, `build`, `site-packages`) is bypassed and
`_discover_files` sees **220,846** files in this repo vs **~3,072** with the defaults (C1). `.gitignore` is
never consulted anywhere (S5). `.worktrees/` (15 nested checkouts) is inside the scan. PDF/DOCX/HTML
extraction inserts the literal two-character sequence `\n` (C12). `filter_language="python"` can never match
because the payload stores the suffix (`py`), not the language (C13).

**Chunking.** Python files are chunked twice: one whole-file `module` chunk plus one per class/function
(C2) — 1.96× content amplification measured (227,336 chars from 116,731). `max_chunk_tokens` is not
enforced on the AST path; a 27,682-token chunk is emitted and the entire file is then silently dropped by
`ContextualizedEmbedder` (C3, E12). Chunk identity is positional (`sha256(path, start_line, end_line)`),
so an insertion at the top of a file re-embeds every symbol below it and orphans the old points (C4).
TS/JS class and interface names are lost (`type_identifier` not handled) and methods, interfaces, enums,
type aliases and exports are never chunked (C9, C10). Markdown headings inside fenced blocks corrupt the
section hierarchy (C5); the header line is embedded twice (C23). The `chunker_version` string does not
change when the LLM context generator changes, so mixed-provenance vectors silently share one manifest
(E6).

**Context generation.** `OpenAIContextGenerator` defaults to `gpt-5-mini` — **deprecated, shutdown
2026-12-11** (§3.3) — with `max_completion_tokens=200` and no `reasoning_effort`, so a reasoning model can
spend the whole budget thinking and return empty context (E8). Any exception yields a placeholder that is
embedded as if it were real context (E7). Fan-out is an unbounded `asyncio.gather` per file (E22). The
Claude generator's price table is hard-coded and wrong for Haiku 4.5 (E9).

**Embedding.** Voyage clients are built with `max_retries=0`; a single 429 drops the batch (E1).
Three separate Voyage calls per file (content, title, breadcrumb) instead of accumulated batches (E14).
Only RPM is rate-limited, never TPM; the limiter sleeps while holding its lock (E16). `VoyageTokenCounter`
has an unbounded process-lifetime cache (E10). `voyage-code-4` is absent from `model_registry.py` (§3.1).

**Indexing / Qdrant.** All chunks for the whole workspace are held in RAM before the first upsert (C7);
2.0 s `asyncio.sleep` per file — ~102 min of pure sleep for the 3,072-file default corpus (C6). Full
re-embed every run: no content-hash skip, cold cache (C8, C25). `sync_workspace(auto_reindex=True)` starts
from an empty snapshot and deletes nothing for the manual path; the autonomous path discards
`changed_files` and full-reindexes on every watchdog trigger (S1) and **never deletes** vectors for deleted
or renamed files (S2, S8). BM25 pickle writes are non-atomic (S9). The `__manifest__` fingerprint omits
`context_provider`, `output_dtype`, and the payload schema version (E6, R-manifest).

**Retrieval.** `HybridSearch` runs three dense queries sequentially and fuses **raw dot-product scores
with BM25 scores by weighted sum** — scales are incomparable, which the Qdrant docs explicitly warn
against (R2, §3.2). The BM25 index is an in-process `rank_bm25` object rebuilt from *all* payloads on
every cold start and stale after any incremental change (R3, R7). Token budgeting uses `chars/3` instead
of real token counts (E17). `degraded` / `budget_starvation` in `TruncationResult` are never set (E2, E4).
`RerankQueryTooLargeError` is swallowed into a silent dense-only fallback (E3). Index and query models
now agree in the default config (`server.py:1237-1239` uses `content_profile.model`), but
`tests/test_vector_space_invariants.py::test_code_content_index_and_query_models_agree` still hard-codes
`voyage-code-3` and XFAILs — the test is stale, not the code (R1 corrected).

**Worktrees (this session's measurements).** `git worktree list` = **23** entries: main checkout + 15 under
`.worktrees/`, 2 under `.claude/worktrees/`, 4 siblings under `/Users/hue/code/_worktrees/`, 1 sibling
`dopemux-mvp-review-quiescence`. Identity is `workspace_to_hash(resolved_path) = md5(path)[:16]`
(`src/utils/workspace.py`), so every worktree is a distinct tenant with its own `code_<hash>` /
`docs_<hash>` pair, its own `~/.dope-context/snapshots/<hash>/`, and its own BM25 pickle. Host snapshot
directory shows **39** distinct workspace hashes (7.6 MB) — historical fan-out evidence. The container
mounts `/Users/hue/code → /workspaces (ro)`, so every checkout is reachable; but the container's own
env pins `DOPEMUX_WORKSPACE_ROOT=/workspaces/dNh_CRM`, and Qdrant currently holds exactly **one**
collection (`code_2bd1584a_7a3fda64c982`, 1 point) belonging to that other project. **There is no live
dopemux-mvp index to migrate** — the redesign is a cold start, which removes the migration risk entirely.

Cost consequence today: indexing every worktree = 23 × (full corpus embed + LLM context generation).
At the packet's measured 6.9 M tokens for repo `.py` alone, that is ≈ 23 × $1.24 ≈ **$28 of embeddings
plus 23× the LLM context spend per full pass**, for content that is > 95 % byte-identical across checkouts.

---

# 3. Verified vendor facts that change the design

## 3.1 Voyage (docs.voyageai.com, blog.voyageai.com; fetched 2026-09-03)

| Role | Current pin | Target | Why | Verified |
|---|---|---|---|---|
| Code content | `voyage-code-3` ($0.18/M) | **`voyage-code-4`** ($0.12/M, 32K ctx, 2048/1024/512/256 Matryoshka) | +27.54 % NDCG@10 on the vendor's agentic code-retrieval suite, +13.98 % on the classic suite; 33 % cheaper | **Live probe from container 2026-09-03:** `embed(model="voyage-code-4", output_dimension=1024)` → 1024 float; `output_dtype="int8"` → 1024 int; `input_type="query", output_dimension=512` → 512. 11 tokens each. |
| Docs content | `voyage-context-4` | keep | current model; $0.12/M; 120K tokens/request, ≤16K chunks, `chunk_fn`, auto-chunking | vendor page |
| General | `voyage-4` | keep | shared 4-series space (`voyage-4-large/-4/-4-lite/-4-nano` **only**) | vendor page, exact quote in audit |
| Rerank | `rerank-2.5` ($0.05/M, 8K query cap, 600K total) | keep; `rerank-3` **preview**, behind a flag only | `rerank-3`/`-lite` exist but have no published limits and no API-reference entry | vendor page; limits UNVERIFIED |
| SDK | `voyageai>=0.5.0,<0.6` (container) / 0.3.7 (harness) | keep 0.5.0; add runtime assert | `contextualized_embed` has `enable_auto_chunking`, `chunk_fn`, `output_dimension`, `output_dtype`; `rerank` has `truncation`, `top_k`, **no** `return_documents` | client.py on main |

**Cross-space rule (fail-closed):** vendor claims interchangeability only inside the 4-series quartet.
No claim exists for `voyage-code-4` ↔ `voyage-4`, `voyage-context-4` ↔ anything, or `-3` ↔ `-4`.
Therefore every named vector is indexed and queried by **one** model, and a model change bumps the
manifest fingerprint and forces re-embed. Equal dimensionality is never evidence (packet invariant).

Deprecation: Voyage publishes **no shutdown dates** for `-3` models; `voyage-code-3`/`voyage-context-3`
remain callable. The switch is on quality/price, not on a clock.

## 3.2 Qdrant 1.19.0 (server + client both verified in-container)

Available now, no upgrade needed: native BM25 sparse vectors (`models.Document(text, model="Qdrant/bm25")`
with mandatory `SparseVectorParams(modifier=Modifier.IDF)`, **per-tenant IDF** in 1.19), `query_points`
with `Prefetch` + `FusionQuery(RRF|DBSF)` or `RrfQuery(Rrf(k=…, weights=[…]))` — **`k` defaults to 2,
not 60**; TurboQuant 1/1.5/2/4-bit; scalar int8; memory tiers `pinned|cached|cold` replacing `on_disk`;
`Datatype.float16|uint8|turbo4`. Rescoring is **off by default** for scalar and 4-bit TurboQuant and must
be set explicitly. Vendor decision rule: RRF is "the safe default"; weighted RRF only with an eval set;
naive linear blending of dense and sparse scores is discouraged (exactly what `HybridSearch` does today).
Breaking: client 1.19 removed `add()`/`query()` helpers; server 1.18 removed all legacy search methods —
the service uses neither, verified by grep.

## 3.3 Context-generation LLM (developers.openai.com; fetched 2026-09-03)

`gpt-5-mini-2025-08-07` and `gpt-5-nano` → **shutdown 2026-12-11**; `gpt-4.1-nano` → 2026-10-23.
Cheapest current model with prompt caching: **`gpt-5.6-luna`** — $0.20 / $0.02 cached / $1.20 per M,
1.05 M context, min cacheable prefix 1,024 tokens, **cache writes cost 1.25× on GPT-5.6+**. `gpt-5.1-mini`
does not exist. Alternative already wired: `ClaudeContextGenerator` (Claude Haiku 4.5, $1 / $5 per M, adaptive
thinking, prompt caching). Both are per-chunk calls, so a stable ≥1,024-token prefix (system + whole
file) followed by the chunk is the cache-friendly shape for either.

## 3.4 Chunking / reranking research (arXiv 2506.15655, 2605.04763, 2510.20609; Anthropic contextual retrieval)

- Structure-aware **split-and-merge on the AST**, sized in **non-whitespace characters** (cAST): +4.3
  Recall@5 on RepoEval. Effect of size is non-monotonic; ~1,500–2,000 nws chars (≈400–800 tokens) is the
  measured sweet spot; 8–16-line chunks underperform at every context length.
- **Scope-context headers** (path → class → def chain, imports, signature) prepended before embedding moved
  agent accuracy more than chunk size did; BM25 stayed load-bearing for identifier queries (99.6 % vs 99.0 %).
- Anthropic: 50–100-token generated context prepended to **both** the embedding text and the BM25 text;
  retrieve ~150 → rerank → **20** (20 beat 10 and 5); reranking cut retrieval failures 67 %.
- Voyage positions `voyage-context-*` as the LLM-free alternative and cites +6.76 % over Anthropic's
  method on their benchmark; this is why the design keeps contextualized embeddings for docs and makes
  the LLM prefix optional for code (§4.3, D3).

---

# 4. Target design

Guiding constraints: fail-closed contracts, one model per named vector, no full-workspace RAM residency,
no process-lifetime caches without bounds, every optimization measurable by the Wave 0 harness.

## 4.1 Identity: project-scoped collections, blob-addressed points, worktree membership as payload

**Project identity** `project_id = sha256(realpath(git rev-parse --git-common-dir))[:16]`. For every
worktree of this repo that resolves to `/Users/hue/code/dopemux-mvp/.git` (verified for
`.worktrees/audit-economy-ci-routing-001`), so all 23 checkouts map to one project. Non-git directories
fall back to today's `md5(path)` with `identity_version: 1` so external projects (dNh_CRM) are unaffected.

**Worktree identity** `wt_id = sha256(realpath(worktree_root))[:12]`; the existing per-call
`workspace_path` parameter keeps its meaning and resolves to `(project_id, wt_id)`.

**Collections** `code_<project_id>` / `docs_<project_id>`; `__manifest__` v2 adds `identity_version: 2`,
`project_id`, `common_dir`, `payload_schema: 2`, `context_provider`, `output_dtype`, `sparse: "Qdrant/bm25@idf"`.
Any mismatch on these fields is a `CollectionCompatibilityError` exactly as today's gate behaves.

**File universe per worktree** `git -C <wt> ls-files -s -z --cached --others --exclude-standard` — gives
`(mode, blob_oid, rel_path)` for tracked files and `rel_path` for untracked-but-not-ignored files (the latter
hashed locally with `git hash-object`-equivalent SHA-1 so ids are identical to what git would assign). This
single call replaces `_discover_files` + `.gitignore` guessing, excludes nested worktrees automatically
(`git ls-files` never descends into another worktree), and makes `.venv`/`node_modules` questions moot when
they are ignored. The hard-coded exclude list remains as a second gate for non-git directories.

**Point identity** `point_id = uuid5(NS, f"{project_id}|{rel_path}|{blob_oid}|{chunk_ordinal}|{chunker_version}|{profile_fingerprint}")`.
Content-addressed: the same blob at the same path chunks identically in every worktree, so its points are
shared. An insertion at the top of a file changes `blob_oid` and re-embeds that file only (C4 fixed);
unchanged files across worktrees cost nothing.

**Payload additions** `worktrees: [wt_id, …]` (array, indexed keyword), `blob_oid`, `rel_path`,
`branch_hint` (informational). Query filter: `MatchAny(worktrees=[wt_id])`. A `search_code` call with a
`workspace_path` that is a worktree sees exactly that worktree's tree.

**Sync algorithm (per worktree, incremental by construction)**
1. `desired = {(rel_path, blob_oid)}` from `git ls-files`; `current = snapshot[wt_id]` (same shape).
2. `added = desired − current`, `removed = current − desired`.
3. For `removed`: scroll points by `(rel_path, blob_oid)`; remove `wt_id` from `worktrees`; delete the
   point if the array becomes empty (S2/S8 fixed — deletes and renames finally propagate).
4. For `added`: if points for `(rel_path, blob_oid, chunker_version, fingerprint)` already exist (another
   worktree has them) → set-payload add `wt_id` (no embed). Else chunk → embed → upsert with
   `worktrees=[wt_id]`.
5. Persist snapshot atomically (tmp + `os.replace`; S9 fixed); manifest untouched.

Marginal cost of the 23rd worktree ≈ its diff against any already-indexed worktree — for the 15 in-repo
feature branches that is typically tens of files, i.e. cents. Autonomous mode threads `changed_files`
straight into step 1 as a delta instead of discarding it (S1 fixed).

**Fleet-design amendment.** The row "dope-context / qdrant — collection `code_<md5(workspace_path)>`"
becomes "collection `code_<project_id>` with worktree membership payload; `workspace_path` per call
resolves to `(project_id, wt_id)`". Sharing class stays host-singleton; the `HOST_CODE_PARENT_DIR` mount
already covers all checkouts. This is a contract change to a canonical-writer surface (manifest + collection
naming) → **D2** in §8.

## 4.2 Models and profiles (index == query for every named vector)

| Named vector | Collection | Model | input_type | dim | store dtype | notes |
|---|---|---|---|---|---|---|
| `content_vec` | code | **`voyage-code-4`** (D1) | document / query | 1024 | float32 → int8 scalar-quantized in Qdrant, originals `cold` | replaces context-4 on code; see benchmark gate |
| `title_vec` | code | `voyage-code-4` | document / query | 512 | float16 | Matryoshka 512 — titles are short; halves RAM |
| `breadcrumb_vec` | code | `voyage-code-4` | document / query | 512 | float16 | same |
| `bm25` (sparse) | code | `Qdrant/bm25` + IDF | — | — | — | replaces `rank_bm25` pickles (R3/R7/S9) |
| `content_vec` | docs | `voyage-context-4`, `enable_auto_chunking=False`, our chunks | document / query | 1024 | int8 SQ | request partitioned ≤120K tokens / ≤16K chunks (E12 fixed) |
| `title_vec`, `breadcrumb_vec` | docs | `voyage-4` | document / query | 512 | float16 | 4-series; never mixed with code vectors |
| `bm25` (sparse) | docs | `Qdrant/bm25` + IDF | — | — | — | |

Rerank: `rerank-2.5`, `truncation=True`, `top_k=20` from 150 candidates; `rerank-3` selectable via
`DOPE_CONTEXT_RERANK_MODEL` but refused by the registry unless `DOPE_CONTEXT_ALLOW_PREVIEW_MODELS=1`
(limits unpublished). Registry gains `voyage-code-4` (price 0.12, ctx 32K, dims {2048,1024,512,256},
dtypes {float,int8,uint8,binary} — the last three verified live for int8 only; `binary` stays
UNVERIFIED and is not used), `rerank-3`, `rerank-3-lite` (preview flag), and drops nothing (legacy
`voyage-code-3`/`-context-3` remain resolvable behind the existing `DOPE_CONTEXT_ALLOW_LEGACY_CONTEXT3`).

Fingerprint v2 = `sha256(model_ids ∪ dims ∪ dtypes ∪ input_types ∪ chunker_version ∪ context_provider:model ∪ payload_schema ∪ sparse_model)`.
Changing the context generator or output dtype now forces a fresh collection (E6 fixed).

## 4.3 Chunking v2 (`CODE_CHUNKER_VERSION = "v2"`, `DOCS_CHUNKER_VERSION = "v2"`)

**Code (tree-sitter, all four grammars present in-container):**
- cAST split-and-merge: walk top-level nodes; a node whose size ≤ `target` becomes a chunk; siblings are
  merged while the merged size ≤ `target`; oversize nodes recurse into children (class → methods; function →
  statement blocks) until ≤ `hard_cap`. Sizes are **non-whitespace chars** (`target=1800`, `hard_cap=6000`
  ≈ 1.5K tokens) with a real-tokenizer assertion `tokens ≤ max_chunk_tokens` before emit; anything still over
  is line-split with a 10 % overlap and flagged `oversize=True` (C3 fixed: no chunk can sink a file).
- No whole-file `module` chunk. A file gets one **file-summary chunk** (path, module docstring, import
  list, top-level symbol signatures — ≤ 300 tokens) so file-level queries still hit (C2 fixed, amplification
  ≈ 1.05×).
- TS/JS: handle `type_identifier`, `property_identifier`; chunk `method_definition`, `interface_declaration`,
  `enum_declaration`, `type_alias_declaration`, `lexical_declaration` with arrow functions, and unwrap
  `export_statement` (C9/C10 fixed). Python: `decorated_definition` unwrapped; `qualified_name = Class.method`.
- **Scope header** prepended to the *embedded* text only (not to `content` in payload): `# path: … | scope:
  Class.method | imports: a, b | signature: def …`. The same header text is also what the BM25 sparse vector
  is built from (contextual BM25, §3.4). Display text stays the raw code.
- Metadata additions: `nws_chars`, `tokens` (real count, stored — feeds the token budget, E17 fixed),
  `symbol_kind`, `qualified_name`, `language` (canonical name, so `filter_language="python"` works — C13 fixed).

**Docs (markdown/rst/txt + PDF/DOCX via existing extractors):**
- Fence-aware header parser (a `#` inside ``` is content, C5 fixed); front-matter parsed into
  `title`/`tags` (C24); heading emitted once as `section_path`, not duplicated into the body (C23);
  sections merged up to `target=1800` nws chars, split on paragraph/sentence boundaries above `hard_cap`;
  tiny trailing sections merged into their predecessor (C14).
- Extraction bug: `"\n".join` (C12).
- Contextualized embedding gets the section chunks of one document as one `inputs[i]` list so the model sees
  document context; documents over 120K tokens are partitioned at section boundaries (E12).

**Context generation (optional layer, default per D3):** provider-agnostic `ContextGenerator` with
`gpt-5.6-luna` (`reasoning_effort="minimal"`, `max_completion_tokens=160`, prompt-cached file prefix) or
Claude Haiku 4.5 (adaptive thinking, `cache_control` on the file block). Exceptions **raise**, never
placeholder-embed (E7 fixed); concurrency bounded by a per-provider semaphore (E22). Context text is
prepended to the scope header for both dense and sparse. Off by default for code (Voyage's own guidance
plus the scope header covers most of the gain at zero LLM cost), on by default for docs? — no: docs use
`voyage-context-4` which already contextualizes; LLM context is **off** for docs. So the LLM layer is a
tunable for code only, measured by Wave 0.

## 4.4 Indexing pipeline v2

- **Streaming**: files are processed in bounded batches (`embedding_batch_size` by token budget: ≤ 1,000
  inputs and ≤ 100K tokens per Voyage request for code-4 — its per-request limit is UNVERIFIED, so the
  conservative 4-series small-model figure is used; ≤ 120K for context-4); each batch is embedded and
  upserted before the next is read (C7 fixed). One `read_text` per file (C30).
- **Accumulated batching** across files for content/title/breadcrumb (E14 fixed) — three requests per
  batch, not per file.
- **Rate control**: token-bucket limiter with both RPM and TPM from the registry, sleeping outside the lock
  (E16); `max_retries=5` with jittered backoff on 429/5xx (E1); the 2.0 s per-file sleep is deleted (C6).
- **Embedding cache**: SQLite at `~/.dope-context/cache/embeddings.sqlite` keyed by
  `(blob_oid, chunk_ordinal, fingerprint)` with LRU eviction by size; replaces the process-lifetime dicts
  (E10, E11). Cross-worktree reuse comes from point identity (§4.1), the cache only saves re-runs after
  collection recreation.
- **Snapshot** load-then-merge (S15); atomic writes (S9); one snapshot per `wt_id` under the project dir.
- **Autonomous**: watchdog deltas go to `sync_worktree(changed=…)`; periodic full reconcile every N hours
  compares `git ls-files` against the snapshot only (no re-hash of unchanged blobs — git already did it).

## 4.5 Retrieval v2

```
query ─┬─ dense: code-4 query embed (content 1024, title 512, breadcrumb 512)
       └─ sparse: Qdrant/bm25 inference on query text
Qdrant query_points(prefetch=[content(limit=150), title(60), breadcrumb(60), bm25(150)],
                    query=RrfQuery(Rrf(k=60, weights=[1.0, 0.5, 0.5, 1.0])),
                    filter=worktrees ∋ wt_id ∧ language ∧ path_prefix, limit=150,
                    search_params=Quantization(rescore=True, oversampling=2.0))
→ rerank-2.5(query, top-150 raw code, top_k=20, truncation=True)
→ token-budget pack (real `tokens` payload field) → response with degraded/budget flags populated
```
- One round-trip instead of three sequential dense queries + an in-process BM25 (R2/R3/R7 fixed).
- RRF `k=60` explicit (Qdrant default 2 is far more top-heavy); weights start at the values above and are
  tuned only against the Wave 0 eval set — never by intuition (vendor rule §3.2).
- Rerank failure modes: `RerankQueryTooLargeError` → truncate query to the model's cap and retry once;
  any other rerank exception → return fused order with `reranked=False, degraded=True,
  degraded_reason="rerank_failed:<type>"` (E2/E3/E4 fixed, never silent).
- Quantization: scalar int8 `quantile=0.99`, quantized `pinned`, originals `cold`, `rescore=True` set
  explicitly (default is off for scalar). TurboQuant 4-bit is the documented alternative and is exposed
  as a config switch; not default until Wave 0 measures recall on this corpus (vendor validated binary
  only at 1536-d and 4096-d).
- `RetrievalResult` gains `worktree`, `blob_oid`, `qualified_name`, `score_components` (per-prefetch rank)
  for explainability.

## 4.6 Contracts and observability

- `__manifest__` v2 (above); `assert_manifest_compatible` unchanged in spirit, extended fields.
- `TruncationResult.degraded/budget_starvation` actually set; `get_cost_summary` counts requests before
  computing hit ratio (E21); `VoyageTokenCounter` bounded LRU (E10); Claude price table replaced by the
  registry (E9).
- Health: `/health` reports `identity_version`, collection names, sparse model, and last sync per worktree.
- Tests: `tests/test_code_chunker.py`, `tests/test_document_processor.py` (none exist today — C31),
  `tests/test_identity_worktrees.py`, `tests/test_hybrid_query_contract.py` (asserts one `query_points`
  call with 4 prefetches and `Rrf(k=60)`), and the invariants test rewritten to assert
  index/query profile equality for all six vectors from the registry, not hard-coded IDs.

---

# 5. What is *not* changed (deliberately)

- MCP tool names and argument shapes (`search_code`, `index_workspace`, `sync_workspace`, …) — callers
  unaffected; `workspace_path` semantics preserved.
- Sharing class (host-singleton) and mounts.
- `voyage-context-4` for docs; `rerank-2.5` as default; `voyage-4` general.
- Legacy `-3` resolution paths (flag-gated), so rollback is configuration, not code.

---

# 6. Expected outcomes (to be measured, not asserted)

| Metric | Today (measured) | Target | Measured by |
|---|---|---|---|
| Files scanned, this repo | 220,846 | ≈ 3,000 (git-tracked, non-ignored) | Wave 1 test |
| Content amplification (Python) | 1.96× | ≤ 1.10× | Wave 2 test on `services/dope-context/src` |
| Full index wall-clock, 3,072 files | ≥ 102 min sleep floor + serial embeds | < 10 min | Wave 3 run log |
| Worktree #2..#23 marginal embed cost | 100 % of corpus each | ≈ diff size | Wave 3 run log (two worktrees) |
| Recall@20 on Wave 0 query set (code) | unknown | ≥ today + 10 pts, or D1 falls back | Wave 0 harness |
| Rename/delete propagation | never | same sync cycle | Wave 3 test |
| Hybrid query round-trips | 3 dense + local BM25 | 1 | Wave 4 test |

---

# 7. Implementation plan

Waves are sequential unless marked ∥. Each wave is one PR-sized change with its own tests, a `PASS/FAIL/
NOT_RUN` matrix, and a proof bundle per AGENTS.md §8. File ownership is disjoint between ∥ waves so they can
be implemented by parallel agents without merge conflicts.

## Wave 0 — Evaluation harness + model decision benchmark (no product code; ~$0.10)
- `services/dope-context/eval/queries.jsonl`: ~40 symptom-style queries over `services/dope-context/src`
  with ground-truth `(rel_path, qualified_name)` — authored from the audit findings (each finding names a
  file:line, which is a free labelled query).
- `services/dope-context/eval/run_eval.py`: offline harness — chunk with the chosen chunker, embed with
  profile P, index into a throwaway Qdrant collection, run the query set, report Recall@{5,20}, MRR,
  NDCG@10 per profile; prints cost from the tracker.
- Profiles: **A** context-4 both sides (today), **B′** code-4 both sides, **B′+hdr** code-4 with scope
  header, **B′+hdr+llm** with `gpt-5.6-luna` context. Budget: 95,711 tokens × 4 ≈ $0.06 embeddings +
  ≈ $0.03 LLM.
- Output: numbers into `TP-DOPECONTEXT-VECTOR-SPACE-0004` → status moves from `DECISION_REQUIRED` to a
  recorded decision (packet invariant: "recorded with the measurements that produced it").
- Gate to Wave 2: B′ ≥ A on Recall@20; otherwise D1 flips to keeping context-4 for code and the rest of the
  plan is unchanged.

### Wave 0 smoke results (2026-09-03)

**Setup.** 41 queries, 455 chunks from `services/dope-context/src`, Qdrant throwaway collections, harness
at `services/dope-context/eval/run_eval.py` (untracked, pending packet amendment to Allowed Files per B12).
Results in `claudedocs/dope-context-eval-results-2026-09-03.md` (relocated from `eval/`: `markdown-location-guard` forbids `.md` there). Total cost: **$0.047747**.

| Profile | Description | Recall@5 | Recall@20 | MRR | NDCG@10 | Cost (USD) |
|---|---|---|---|---|---|---|
| A | `voyage-context-4` contextual, both sides | 1.000 | 1.000 | 0.8537 | 0.8914 | $0.015421 |
| B | `voyage-code-4` flat dense | 1.000 | 1.000 | 0.9187 | 0.9396 | $0.015369 |
| Bh | B + scope-header prefix (file path + qualified symbol) | 1.000 | 1.000 | 0.7935 | 0.8461 | $0.016709 |
| Bhl | Bh + LLM situating context | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | $0.000000 |
| CTRL | context-4 index queried with `voyage-code-3` (historical embedding-space mismatch) | 0.000 | 0.0244 | 0.0017 | 0.000 | $0.000248 |

Bhl's status is `NOT_RUN` because `OPENAI_API_KEY` was not set in the container; the harness skipped it per
its designed fallback rather than failing.

**Findings, stated with their limits:**
1. Recall is saturated on this 455-chunk corpus, so this run is **NOT decision-grade** — it is a
   harness-correctness smoke, not a benchmark result.
2. The only discriminating signal at this scale is MRR: **B > A > Bh**.
3. The scope-header prefix **hurt** MRR (0.9187 → 0.7935) on this corpus. Do not adopt scope-header
   prefixing (§4.3) without re-measuring on the whole-repo run.
4. CTRL confirms the historical index/query mismatch is catastrophic (Recall@5 = 0), which justifies the
   fingerprint gate already in this design (§3.1 cross-space rule, §4.2 fingerprint v2).
5. The harness contains **no BM25 and no rerank path**. The hybrid + `rerank-3` layer proposed in §4.5
   remains **UNMEASURED** and must be a profile in the whole-repo (~$6.82) run before it is adopted.
6. A replicate of B/Bh reproduced MRR/NDCG identical to four decimals — Voyage embeddings are
   deterministic across runs (replicate cost $0.032078; rows not kept).

**Identifier-query subset**: n=2 — too small to draw a separate conclusion; both hits land in top-20 for
A/B/Bh and both miss for CTRL, consistent with the whole-set pattern, but with n=2 this moves in lockstep
rather than being independent evidence.

## Wave 1 — Correctness fixes with no schema impact (small, mergeable first) ∥-safe with Wave 0
Owner files: `voyage_embedder.py`, `contextualized_embedder.py`, `voyage_reranker.py`, `model_tokenizer.py`,
`token_budget.py`, `openai_generator.py`, `claude_generator.py`, `document_processor.py` (newline bug
only), `indexing_pipeline.py` (exclude default + sleep removal only), `server.py` (exclude passthrough,
`filter_language` canonicalisation, degraded flags).
- E1 retries; E7 raise-not-placeholder; E8 `reasoning_effort` + model swap to `gpt-5.6-luna`; E9 price
  from registry; E10/E11 bounded caches; E16 limiter; E2/E3/E4 degraded flags; E17 real tokens where the
  payload has them, `chars/3` only as fallback; E21 cost stats; C1 exclude passthrough (default list
  applied when `None`); C6 sleep removed; C12 `"\n"`; C13 language canonical.
- Registry: add `voyage-code-4`, `rerank-3`, `rerank-3-lite` (preview flag), `voyageai>=0.5.0` runtime
  assert. Defaults unchanged in this wave (still context-4 on code) so no manifest bump.
- Tests: extend existing suites; add `test_openai_generator.py`, `test_registry_code4.py`.
- Overlaps `TP-DOPECONTEXT-VOYAGE4-REPAIR-0002` (AUTHORIZED) — this wave *is* that packet's remaining
  scope plus the audit's E-series; the packet is cited in the PR.

## Wave 2 — Chunking v2 (code + docs)
Owner files: `code_chunker.py`, `document_processor.py`, new `chunk_sizing.py`, new tests.
- cAST split-and-merge, no module chunk, file-summary chunk, TS/JS coverage, scope header, real token
  count, fence-aware markdown, front-matter, single heading, `CODE_CHUNKER_VERSION="v2"`.
- Acceptance: amplification ≤ 1.10× on `src/`; zero chunks > `max_chunk_tokens`; TS fixture yields class,
  interface, method chunks with names; markdown fixture with fenced `#` keeps hierarchy; unit coverage for
  both chunkers (C31).

## Wave 3 — Identity v2 + streaming pipeline + worktree-aware sync (**requires D2**)
Owner files: `utils/workspace.py`, `index_profile.py` (fingerprint v2), `pipeline/indexing_pipeline.py`,
`pipeline/docs_pipeline.py`, `sync/*`, `autonomous/*`, `server.py` (identity resolution, manifest v2),
new `identity.py`, new `git_universe.py`.
- `git ls-files` universe; project/worktree ids; blob-addressed point ids; `worktrees` payload; sync
  algorithm §4.1; streaming batches; SQLite embedding cache; atomic snapshots; autonomous deltas.
- Acceptance: index worktree A then worktree B (a feature branch) — B's run embeds only the diff (log
  asserts embed count ≤ changed files' chunks); delete a file in B → its points lose `wt_B`, remain for A;
  delete in both → point gone; rename → old path gone, new path present, one embed.
- Manifest bump → new collections `code_<project_id>`; old `code_<md5>` collections are left in place and
  listed by a `dope-context gc --orphans` command (no automatic deletion).

## Wave 4 — Retrieval v2 (Qdrant-native hybrid) ∥ with Wave 3 (disjoint files)
Owner files: `search/dense_search.py`, `search/hybrid_search.py`, `search/bm25_index.py` (deleted),
`rerank/voyage_reranker.py` (retry-once path), `server.py` search handlers only.
- Sparse `bm25` named vector on both collections; single `query_points` with prefetch + `Rrf(k=60)`;
  rerank 150 → 20; quantization config with explicit rescore; `score_components` in results.
- Acceptance: contract test asserts one `query_points` call with four prefetches; recall on the Wave 0 set
  ≥ Wave 0's best profile (fusion must not regress the dense-only number); latency p95 measured.

## Wave 5 — Model default switch + docs + packet closure
- `DEFAULT_CODE_MODEL="voyage-code-4"` (per Wave 0 result), Dockerfile envs, README example payload,
  `constraints.txt` comment, fleet-design row amendment, `TP-DOPECONTEXT-VECTOR-SPACE-0004` closed with
  numbers, `-COLLECTION-GATE-0003`/`-TEST-HARNESS-0005`/`-SERVICE-HARDENING-0006` cross-referenced,
  CTX3-series marked superseded.
- Container rebuild + live reindex of this repo from the main worktree, then one feature worktree,
  with the run log attached as proof.

## 7.4 Packet reconciliation

| Packet | Status today | Relationship |
|---|---|---|
| VECTOR-SPACE-0004 | `DECISION_REQUIRED`, benchmark funded | Wave 0 executes its approved benchmark with B′ = code-4 instead of code-3 (cheaper, newer); decision recorded there |
| VOYAGE4-REPAIR-0002 | `AUTHORIZED_FOR_IMPLEMENTATION` | Wave 1 delivers its remaining scope |
| COLLECTION-GATE-0003 | `IMPLEMENTATION_CANDIDATE` (gate landed) | Wave 3 extends the manifest to v2 under the same gate |
| TEST-HARNESS-0005 | `IMPLEMENTATION_CANDIDATE` | Wave 0 harness + Wave 2/4 tests satisfy it |
| SERVICE-HARDENING-0006 | `IMPLEMENTATION_CANDIDATE` (blocked) | Wave 1 E-series + Wave 3 sync fixes cover its hardening items |
| CTX3-0001…0006 | no status field | superseded by context-4; no action |

No dope-context retrieval program exists in the task-orchestrator (only an unrelated terminal item matched);
loading Waves 0–5 as a work tree is available on request and not done here.

---

# 8. Decisions required (max three)

**D1 — Code vector space.** Recommend **B′: `voyage-code-4` on both index and query**, gated by the Wave 0
benchmark (B′ ≥ A on Recall@20). Fallback: keep `voyage-context-4` on code (today's A). Rationale: vendor's
code-specific model, +27.5 % on agentic retrieval, 33 % cheaper than code-3, live-verified today; A stays
available behind config. Pricing is not a factor between B′ and A: both `voyage-code-4` and
`voyage-context-4` are $0.12/M tokens (verified 2026-09-03, Revision 2.2) — price is no longer a
differentiator. The Wave 0 smoke run (§7, 41 queries/455 chunks) shows B > A on MRR but is explicitly
NOT decision-grade on this small corpus; D1 rests on the whole-repo benchmark, not on price.

**D2 — Identity contract change.** Recommend **approve** project-scoped collections with worktree
membership (§4.1). It changes collection naming and the manifest schema (canonical-writer surface) and
amends one row of the accepted fleet design. Fallback: keep per-worktree collections and accept the 23×
cost; Waves 1, 2, 4 still apply.

**D3 — LLM context layer for code.** Recommend **off by default** (scope header only), with
`gpt-5.6-luna` as the provider when enabled. Alternative: Claude Haiku 4.5 (already wired, 5× the price
per token, higher quality unknown on this corpus). Wave 0 profile `B′+hdr+llm` measures whether it earns
its cost.

---

# 9. Validation status of this document

| Check | Result |
|---|---|
| Baseline test suite in the implementation worktree (`mise exec -- python -m pytest tests -q`) | **PASS** — 115 passed, 2 skipped, 1 xfailed (1.65 s) |
| `voyage-code-4` callable (float/int8 1024, query 512) | **PASS** — live from `mcp-dope-context` |
| Qdrant 1.19 client surface (IDF, TurboQuant, Rrf, Memory, Datatype) | **PASS** — all present |
| Container image == source | **PASS** — MD5 match (sync audit) |
| PAL `analyze → planner → codereview → precommit` | **NOT_RUN** — PAL MCP not connected this session |
| Adversarial design review (fresh subagent, PAL substitute) | NOT_RUN at time of writing — scheduled next |
| Any product code changed | **none** — this document and the audit are the only files |

Remaining uncertainty (explicit): `voyage-code-4` per-request token limit and `binary` dtype (UNVERIFIED,
not relied on); `rerank-3` limits (not used); whether B′ beats A on *this* corpus (Wave 0 exists to answer
it); TurboQuant recall at 1024-d (config switch, not default).

---

## Revision 2 — 2026-09-03, after adversarial review (APPROVE_WITH_CHANGES, 13 blocking)

Reviewer: fresh agent, adversarial persona, no session context. Where this revision conflicts with the numbered sections above, **this revision wins**. Each blocking finding was reproduced by the author before being accepted; three probe transcripts are in Appendix A.

### R2.1 Reproduction results

| # | Reviewer claim | Author verdict | Evidence |
|---|---|---|---|
| B1 | `git rev-parse --git-common-dir` fails inside the container for linked worktrees | **CONFIRMED** | `.git` file contains `gitdir: /Users/hue/code/dopemux-mvp/.git/worktrees/…` (host path) → `fatal: not a git repository` in `mcp-dope-context` (git 2.47.3). Main checkout resolves to `/workspaces/dopemux-mvp/.git`. |
| B2 | common-dir is relative | CONFIRMED, trivially fixed | `--path-format=absolute` returns `/workspaces/dopemux-mvp/.git`. |
| B3 | Fusion queries ignore the top-level filter → worktree isolation silently broken | **REFUTED on the live server** (holds only for the in-memory/local client the reviewer cited) | Qdrant 1.19.0, throwaway 2-point collection, RRF over two named vectors with top-level `query_filter` on `worktrees` → returned `[1]` only; per-prefetch filter → `[1]`. Design still puts the filter in *both* places (local-mode tests use `:memory:`). |
| B4 | `fastembed` absent; `Qdrant/bm25` would also discard `code_aware_tokenizer` | **CONFIRMED** | `importlib.util.find_spec("fastembed")` → `None` in the container. Sparse encoder redesigned (§R2.2-4.5). |
| B5 | Manifest bump in Wave 1 forces a full re-embed before any benefit lands | CONFIRMED on inspection | moved to Wave 2 (§R2.2-7). |
| B6 | Waves not file-disjoint | CONFIRMED on inspection | re-cut (§R2.2-7). |
| B7 | §2 defect IDs do not match the committed audit document | **CONFIRMED** | §2 cites the four *stage report* series (E/C/R/S) delivered in-session; the audit document uses its own M/E/C/I/R table. Crosswalk in Appendix B; §2 is to be read through it. |
| B8 | `worktrees[]` array is a read-modify-write → lost update with two indexers | CONFIRMED on inspection | replaced by per-worktree keys (§R2.2-4.2). |
| B9 | absolute `file_path` in payload leaks the indexing worktree's path | CONFIRMED on inspection | §R2.2-4.4. |
| B10 | `profile_digest` dropped from manifest | CONFIRMED on inspection | restored (§R2.2-4.3). |
| B11 | `docs_search` path not covered | CONFIRMED on inspection | §R2.2-4.6. |
| B12 | Wave 0 lacks the packet's control profile; `eval/` not in Allowed Files | CONFIRMED | CTRL profile instruction sent to the Wave 0 runner (index `voyage-context-4`, query `voyage-code-3`). `eval/` needs a packet amendment → supervisor. |
| B13 | Residue chunk after a 4.5×max split | CONFIRMED on inspection | §R2.2-4.7. |

### R2.2 Amendments

**4.1 Identity (supersedes).** Never depend on `git -C <worktree>` succeeding inside the container.
1. Read `<wt>/.git`. Directory → `common_dir = <wt>/.git`. File `gitdir: <p>` → `common_dir = <p>` with a trailing `/worktrees/<name>` removed.
2. Canonicalise: if the path starts with `$HOST_CODE_PARENT_DIR` (the container already receives it for its mounts) rewrite that prefix to `/workspaces`; if it already starts with `/workspaces`, keep it. Main checkout and linked worktrees therefore both canonicalise to `/workspaces/dopemux-mvp/.git`.
3. `project_id = sha256(canonical common_dir)[:16]`; `worktree_id = sha256(canonical worktree path)[:16]`; human label = basename, stored in the manifest only.
4. File universe: `GIT_DIR=<canonical gitdir> GIT_WORK_TREE=<wt> git ls-files -z --cached --others --exclude-standard` (with `GIT_DIR` set git does not consult the `.git` file). Wave 2 must carry a test that runs this against a linked worktree *with a host-path gitdir*.
5. **Fail closed.** No prefix rule applies, `HOST_CODE_PARENT_DIR` unset, or git exits non-zero → `IdentityResolutionError`; the shared collection is never written under a guessed identity. Only with `DOPE_CONTEXT_ALLOW_UNSHARED_IDENTITY=1` does the service fall back to a per-path collection, and then `identity_mode: "path-fallback"` is written into the manifest and logged at WARNING on every run.

**4.2 Membership (supersedes `worktrees[]`).** Membership is one payload key per worktree: `wt_<worktree_id>: true`. Add = `set_payload({"wt_<id>": true}, points=ids)` — a server-side key merge, no read-modify-write, so two indexers of different worktrees cannot clobber each other. Remove = `delete_payload(keys=["wt_<id>"], points=ids)`. Each key gets a `bool` payload index on first use (idempotent). Orphan sweep (points left with no `wt_*` key) runs only inside a project-level `fcntl.flock(LOCK_EX)` on `/workspaces/<project>/.dopemux/index.lock` (a shared mount, so it serialises across that project's containers); adds take `LOCK_SH`. Query filter: `must: [{key: "wt_<id>", match: {value: true}}]` — placed in **every prefetch and at top level** (B3).

**4.3 Manifest.** Keeps `profile_digest` (B10) and adds `identity_version: 2`, `identity_mode`, `chunker_version`, `sparse_encoder_version`, `sparse_avg_len`. The bump lands in **Wave 2**, the only schema-changing wave (B5).

**4.4 Payload.** `file_path` is stored **relative to the worktree root**; no absolute path is stored (B9). Results are rendered as `<querying worktree>/<rel>`, which is also what makes a cross-worktree hit usable.

**4.5 Sparse vectors (supersedes).** No `fastembed`, no `models.Document` (B4). A client-side `SparseEncoder`: tokens from the existing `code_aware_tokenizer` (camelCase/snake_case split, lowercase, no stopwords); term id = 31-bit hash of the token; value = BM25 term-frequency saturation `tf·(k1+1) / (tf + k1·(1 − b + b·len/avg_len))`, k1 = 1.2, b = 0.75, `avg_len` from the manifest (recomputed on full index; drift tolerated on incremental runs). Qdrant applies IDF server-side (`Modifier.IDF`). Zero new dependencies; identifier matching behaves as today. `sparse_encoder_version` changes force a re-index.

**4.6 Docs search (new).** `docs_search` applies the same `wt_*` filter and relative-path layout; the docs pipeline's deterministic ids make the membership keys reusable unchanged (B11).

**4.7 Residue chunks (new).** After a symbol is split by `max_chunk_tokens`, a trailing piece < 25 % of the limit merges into the previous piece of the same parent symbol when the merged piece is ≤ 1.1× the limit; otherwise it stands alone. Test fixture: a 4.5× function (B13).

**7 Waves (supersedes; file-disjoint).**
- Wave 0 — eval only: `eval/*`, `benchmarks/*` (packet amendment for `eval/` required). Includes the CTRL profile. The 41-file run is a smoke test; the decision-grade run is the whole repo at the packet's measured **$6.82 ≤ $10 ceiling** — recommend authorising it before deciding D1 (reviewer Q2, B12).
- Wave 1 — behaviour only, manifest-compatible: `voyage_embedder.py`, `voyage_reranker.py`, `token_budget.py`, `model_tokenizer.py`, `indexing_pipeline.py` (sleep/gather/RAM), `code_chunker.py`.
- Wave 2 — schema + identity + sparse: `workspace.py`, `index_profile.py`, `dense_search.py`, `hybrid_search.py`, new `sparse_encoder.py`, Qdrant-facing handlers in `server.py`; manifest bump here.
- Wave 3 — sync/autonomy: `autonomous/*`, `sync/*`, autonomy handlers in `server.py`. Shares `server.py` with Wave 2, so it **starts only after Wave 2 merges** (sequential, not parallel).
- Wave 4 — context generation: `context/*`.

### Appendix A — probe transcripts (verbatim, 2026-09-03, container `mcp-dope-context`, Qdrant 1.19.0)

```
fastembed: MISSING
TOP-LEVEL filter, fusion -> ids: [1] (expect [1] if honoured)
PER-PREFETCH filter, fusion -> ids: [1] (expect [1])
Qdrant server: green | point 1 payload: {'worktrees': ['A']}
cleaned up eval_filtertest_7097e9a6
```
```
--- linked worktree in container ---
gitdir: /Users/hue/code/dopemux-mvp/.git/worktrees/dope-context-retrieval-redesign-001
fatal: not a git repository: /Users/hue/code/dopemux-mvp/.git/worktrees/dope-context-retrieval-redesign-001
--- main checkout in container ---
/workspaces/dopemux-mvp/.git
--- git version ---
git version 2.47.3
```
Vendor-model probes (Voyage `voyage-code-3` / `voyage-context-4` / `rerank-2.5` acceptance, voyageai 0.5.0 `contextualized_embed` signature) were run earlier in the authoring session; their raw output is **not** reproduced here and must be re-run and pasted in by Wave 0 before D1 is decided (reviewer Q3).

### Appendix B — defect-ID crosswalk (stage report → committed audit table)

Embeddings: E1→E1 · E2→R8 · E3→R9 · E4→R10 · E6→E2 · E7→E3 · E8→M1 · E9→M3 · E10→E9 · E11→M5 · E12→E5 · E14→E7 · E16→E4 · E17→(no audit row; stage-only) · E21→E10 · E22→E11.
Chunking: C1→I1 · C2→C1 · C3→C2 · C4→I2 · C5→C6 · C6→I5 · C7→I6 · C8→I7 · C9→C3 · C10→C4 · C12→C5 · C13→C8 · C14→C7 · C23→C9 · C24→C10 · C25→C11 · C30→I15 · C31→C18.
Retrieval: R1→R1 · R2→R2/R7 · R3→R3 · R7→≈R5 (topic-mapped, verify).
Sync: S1→I4 · S2→I9/I3 · S5→I11 · S8→≈I3 · S9→I13 · **S15→UNKNOWN** (no such stage finding; treat as an authoring typo to be resolved in the edit pass).

---

## Revision 2.1 — vendor probe corrections (2026-09-03, same session)

Trigger: reviewer Q3 (raw vendor transcripts). Re-running the probes from `mcp-dope-context` (voyageai 0.5.0, live key) produced facts that **contradict §3** of this design; this section supersedes §3's model matrix and the Appendix A placeholder paragraph.

1. **`voyage-code-4` exists** and is accepted (1024-dim). It is not an alias: cosine to `voyage-4` = 0.774, to `voyage-code-3` = −0.019 on the same text. §3's treatment of the code-4 line as unavailable was wrong.
2. **`rerank-3` and `rerank-3-lite` exist.** `rerank-2.5` is not the newest reranker; the rerank choice is re-opened and goes to measurement (profile Dh).
3. Supported lists, verbatim from the API's rejection of an unknown name (the API does reject unknowns — control `voyage-code-99`, `voyage-context-5`, `rerank-9` all → `InvalidRequestError`):
   - embed: `['voyage-4-large', 'voyage-4', 'voyage-4-lite', 'voyage-code-4', 'voyage-3', 'voyage-3-lite', 'voyage-finance-2', 'voyage-large-2-instruct', 'voyage-law-2', 'voyage-code-2', 'voyage-02', 'voyage-2', 'voyage-01', 'voyage-lite-01', 'voyage-lite-01-instruct', 'voyage-lite-02-instruct', 'voyage-code-3', 'voyage-3-large', 'voyage-3-5', 'voyage-3-5-lite', 'voyage-code-3-5', 'voyage-multilingual-2', 'voyage-large-2', 'voyage-3.5', 'voyage-3.5-lite', 'voyage-code-3.5']`
   - rerank: `['rerank-lite-1', 'rerank-2-lite', 'rerank-2', 'rerank-3', 'rerank-3-lite', 'rerank-2.5', 'rerank-2.5-lite']`
   - contextualized: `['voyage-context-3', 'voyage-context-4']`
4. Space sharing — single-sample cosines, indicative only, **not decision-grade**: `context-4[doc]` vs `voyage-4-large[doc]` 0.832 · vs `voyage-4[doc]` 0.748 · vs `voyage-code-4[doc]` 0.484 · vs `voyage-code-3[doc]` −0.021. Same-model `context-4` doc/query baseline 0.607; cross-model queries against a `context-4` document: `voyage-4` 0.564, `voyage-code-4` 0.508, `voyage-code-3` 0.015. Reading: the voyage-4 general family and `context-4` are partially interoperable (consistent with the vendor's shared-space claim), `voyage-code-4` is its own space, `voyage-code-3` is orthogonal (the historical R1 bug). Consequence: the manifest gate stays, and for `voyage-code-4` index and query model **must** be identical.
5. **Pricing verified 2026-09-03 — supersedes this point's original "UNKNOWN in this session" claim.**
   See Revision 2.2 below for the full table and citation. `rerank-3` and `rerank-3-lite` were also
   live-verified against the Voyage API on 2026-09-03 (both return results): neither their existence nor
   their price is unknown any longer. Registry rows can now carry the `# verified <date> <url>` audit M4
   required; cost columns no longer need the `total_tokens`-only fallback — see Wave 0 smoke results (§7)
   for measured costs.
6. D1 option set becomes A / B / Bh / Bhl / CTRL / **D** (`voyage-code-4` dense, index+query) / **Dh** (D + hybrid BM25 + `rerank-3`, fallback `rerank-2.5` if rejected). The Wave 0 runner was instructed to add CTRL, D and Dh; **the smoke run that actually executed (§7 Wave 0 smoke results, 2026-09-03) only covers A / B / Bh / Bhl / CTRL — B is this design's D (`voyage-code-4` dense, index+query). Dh (hybrid BM25 + `rerank-3`) was never run: the harness has no BM25/rerank path, so that layer stays UNMEASURED (Revision 2.2) until the whole-repo run.**
7. Wave 1 scope addition: `model_registry.py` entries for `voyage-code-4`, `rerank-3`, `rerank-3-lite` (and `voyage-code-3.5` if measured), dims and prices verified (prices now verified 2026-09-03, Revision 2.2) — the registry fails closed on unknown names, so no D-profile can run in the service without this.

### Appendix A (continued) — vendor probe transcripts, verbatim

```
voyageai 0.5.0 | key present: True
contextualized_embed sig: (inputs: Union[List[List[str]], List[str]], model: str, input_type: Optional[str] = None, output_dtype: Optional[str] = None, output_dimension: Optional[int] =
embed voyage-code-3    OK dim=1024 tokens=9
embed voyage-code-4    OK dim=1024 tokens=9
embed voyage-3-large   OK dim=1024 tokens=9
embed voyage-3.5       OK dim=1024 tokens=9
embed voyage-4         OK dim=1024 tokens=9
embed voyage-4-large   OK dim=1024 tokens=9
embed voyage-4-lite    OK dim=1024 tokens=9
ctx   voyage-context-3 OK dim=1024 n=2 tokens=20
ctx   voyage-context-4 OK dim=1024 n=2 tokens=20
rerank rerank-2.5      OK top=0 score=0.828 tokens=22
rerank rerank-2.5-lite OK top=0 score=0.797 tokens=22
rerank rerank-2        OK top=0 score=0.734 tokens=22
```
```
CONTROL voyage-code-99   rejected: InvalidRequestError: Model voyage-code-99 is not supported. Supported models are [...]
CONTROL voyage-context-5 rejected: InvalidRequestError: Model voyage-context-5 is not supported. Supported models are [...]
CONTROL rerank-9         rejected: InvalidRequestError: Model rerank-9 is not supported. Supported models are [...]
cos(voyage-code-4,voyage-4) = 0.7741
cos(voyage-code-4,voyage-4-large) = 0.6951
cos(voyage-code-4,voyage-4-lite) = 0.6949
cos(voyage-code-4,voyage-code-3) = -0.0187
cos(voyage-4,voyage-4-large) = 0.9262
cos(voyage-4,voyage-3-large) = -0.0021
cos(ctx4[doc], voyage-4[doc]) = 0.7479 | cos(ctx4[doc], voyage-4[query 'parse a manifest file']) = 0.5637
cos(ctx4[doc], voyage-4-large[doc]) = 0.8323 | cos(ctx4[doc], voyage-4-large[query 'parse a manifest file']) = 0.5597
cos(ctx4[doc], voyage-code-4[doc]) = 0.4837 | cos(ctx4[doc], voyage-code-4[query 'parse a manifest file']) = 0.5076
cos(ctx4[doc], voyage-code-3[doc]) = -0.0206 | cos(ctx4[doc], voyage-code-3[query 'parse a manifest file']) = 0.0154
cos(ctx4[doc], ctx4[query]) = 0.6074   (same-model baseline)
```

---

## Revision 2.2 — 2026-09-03, Voyage pricing verified + Wave 0 smoke results

Rev 2.2 (2026-09-03): Voyage pricing verified from vendor page; Wave 0 smoke results added; hybrid/rerank
layer marked UNMEASURED.

**Pricing (supersedes Revision 2.1 §5's "UNKNOWN in this session").** Source:
https://docs.voyageai.com/docs/pricing, read 2026-09-03.

| Model | Price (USD / M tokens) |
|---|---|
| `voyage-code-4` | $0.12 |
| `voyage-context-4` | $0.12 |
| `voyage-4-large` | $0.12 |
| `voyage-4` | $0.06 |
| `voyage-4-lite` | $0.02 |
| `voyage-code-3` | $0.18 |
| `rerank-3` | $0.05 |
| `rerank-3-lite` | $0.02 |
| `rerank-2.5` | $0.05 |

`rerank-3` and `rerank-3-lite` were also live-verified against the Voyage API on 2026-09-03 (both return
results) — neither their existence nor their price is unknown any longer. `voyage-code-4` and
`voyage-context-4` are priced identically ($0.12/M), so **price is not a differentiator for D1** (§8); the
choice between them rests on the whole-repo benchmark (~$6.82, §7 Wave 0), not on cost. `voyage-code-3.5`
pricing remains unmeasured (not used by this design).

**Wave 0 smoke results**: see the new "Wave 0 smoke results (2026-09-03)" subsection under §7 "Wave 0 —
Evaluation harness + model decision benchmark" for the full setup, results table, and findings. Headline:
the 41-query/455-chunk run is a harness-correctness smoke, not decision-grade; the harness has no BM25 or
rerank path, so the hybrid + `rerank-3` layer in §4.5 has **no coverage** here and remains **UNMEASURED**
pending the whole-repo run. It also means the design's planned `Dh` profile (Revision 2.1 §6) was never
executed — only A/B/Bh/Bhl/CTRL ran, with B standing in for `D`.

## Revision 2.3 — 2026-09-03, operator rulings on D1–D3 + benchmark preconditions

**Rulings (operator, this session, via the D1–D3 prompt; recorded as understood — correct here if misread):**

| Decision | Ruling | Condition |
|---|---|---|
| D1 — code vector space | **B′ approved**: `voyage-code-4` on both index and query | Still gated: B′ ≥ A on Recall@20 in the **whole-repo** benchmark; smoke run is not decision-grade. Packet `TP-DOPECONTEXT-VECTOR-SPACE-0004` stays `DECISION_REQUIRED` until that result is filed. |
| D2 — identity contract | **Approved**: project-scoped collections, worktree membership as payload (§4.1) | Wave 3 may be planned; canonical-writer inspection of the manifest schema remains required before any edit. `WAVES_1_4_SRC_LIFT=NOT_AUTHORIZED` (packet 0004) is unchanged — this ruling is a design decision, not a src/ lift authorization. |
| D3 — LLM context layer for code | **Off by default** (scope header only); `gpt-5.6-luna` when enabled | `Bhl` arm of the benchmark measures whether it earns its cost. |

**Packet amendment for `eval/` (B12): CLOSED.** Packet 0004 carries
`SEAM_CARVEOUT_STATUS=OPERATOR_APPROVED_2026-09-03_LANDED_WITH_ADR_226`,
`SEAM_CARVEOUT_SCOPE=services/dope-context/eval/**`, `SEAM_CARVEOUT_AUTHORIZES_CONTENT_EDITS=NO`
(observed 2026-09-03 in the packet file).

**Whole-repo benchmark (measured $6.82 ≤ $10 ceiling): NOT_RUN. Preconditions observed 2026-09-03:**

- `docker inspect mcp-dope-context`: `VOYAGE_API_KEY` set; **`OPENAI_API_KEY` empty**; `ANTHROPIC_API_KEY` empty.
  Arms A / B / Bh / CTRL can run; **`Bhl` (D3 measurement, `gpt-5.6-luna`) cannot** until the key reaches the
  container.
- `compose.yml:402` maps `OPENAI_API_KEY=${OPENAI_API_KEY}`; `/Users/hue/code/dopemux-mvp/.env` (compose
  working_dir) has a non-empty `OPENAI_API_KEY` line but no `VOYAGE_API_KEY` line — the running container
  predates the current `.env` or was started with a different env. Host shell: both keys unset.
- The running container's compose config also includes
  `.../dopemux-mcp-reset-recovery-001-r3/proof/TP-DMX-MCP-RESET-RECOVERY-001/runtime/dope-context-readonly.override.yml`
  (read-only-facade variant). The harness writes to its own Qdrant collections via `--qdrant-url`, so this is
  noted, not assessed as a blocker.
- Options (operator choice, max 3): (a) `dopemux mcp stop/start dope-context` so the container re-reads `.env`,
  then run all five arms; (b) run A/B/Bh/CTRL now, defer `Bhl`; (c) inject the key per-exec
  (`docker exec -e OPENAI_API_KEY=… `) — not recommended (key in shell history / process list).
