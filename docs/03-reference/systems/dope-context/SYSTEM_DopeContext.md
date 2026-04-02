# SYSTEM_DopeContext

## 1. Purpose

dope-context is the repository's code-and-document retrieval service. In the inspected runtime, its canonical surface is the FastMCP server in `services/dope-context/src/mcp/server.py`, which indexes workspace code into `code_{workspace_hash}` collections, indexes workspace documents into `docs_{workspace_hash}` collections, and serves retrieval over MCP plus a small HTTP surface. Its authority slice is retrieval and index behavior only. It is not PM truth, not durable memory truth, not chronicle authority, and not the system of record for the code, documents, decisions, or history it returns. Indexed material remains owned by upstream files and systems.

## 2. Core Responsibilities

- Code indexing for retrieval is a canonical dope-context responsibility. `index_workspace()` in `services/dope-context/src/mcp/server.py` creates a workspace-scoped code collection in Qdrant, runs `IndexingPipeline.index_workspace()`, and writes a BM25 cache under `~/.dope-context/snapshots/{workspace_hash}/bm25_index.pkl`.
- Documentation indexing for retrieval is a canonical dope-context responsibility. `index_docs()` in `services/dope-context/src/mcp/server.py` runs `DocIndexingPipeline.index_workspace()` from `services/dope-context/src/pipeline/docs_pipeline.py`, and that pipeline discovers and processes `*.md`, `*.markdown`, `*.txt`, `*.html`, `*.htm`, `*.pdf`, and `*.docx`.
- Retrieval/search serving is a canonical dope-context responsibility. `search_code()`, `docs_search()`, and `search_all()` are registered MCP tools in `services/dope-context/src/mcp/server.py`.
- Code retrieval behavior is canonical within the retrieval plane. `search_code()` uses Voyage embeddings, Qdrant-backed multi-vector search, optional BM25 fusion through `HybridSearch`, optional Voyage reranking, and token-budget truncation. This is proven in `services/dope-context/src/mcp/server.py` and `services/dope-context/src/search/hybrid_search.py`.
- Docs retrieval behavior is canonical within the retrieval plane. `docs_search()` embeds queries with `voyage-context-3`, queries the docs collection via `DocumentSearch`, and truncates output to fit token budget. This is proven in `services/dope-context/src/mcp/server.py` and `services/dope-context/src/search/docs_search.py`.
- Retrieval maintenance is an operational dope-context responsibility. `sync_workspace()` and `sync_docs()` detect changed files and can reindex changed code files; autonomous indexing tools start watchdog-style monitoring and periodic sync through `AutonomousController`.
- Bootstrap/startup autoindexing is an operational dope-context responsibility. `services/dope-context/src/mcp/server.py` exposes `/autoindex/bootstrap` and `/autoindex/status`, and `src/dopemux/cli.py` posts to `/autoindex/bootstrap` through `_trigger_dope_context_autoindex_startup()`.
- MCP/transport exposure is an operational dope-context responsibility. `_resolve_transport_runtime()` supports `stdio`, `http`, `sse`, and `streamable-http`, and `services/dope-context/Dockerfile` starts `python -m src.mcp.server`.
- Optional enrichment from other systems is directly observed but not authoritative. `search_all()` can include decision matches only when `configure_decision_auto_indexing()` has enabled bridge-backed lookup; those responses are explicitly tagged with `decision_authority: "memory_plane"` and `code_docs_authority: "search_plane"`. Optional event emission to dopecon-bridge is also present behind an import gate via `integration_bridge_connector.py`.
- `get_chunk_complexity()` is an observed analysis surface, but it is not proven to participate in canonical indexing or search ranking. Treat it as an auxiliary runtime tool, not a core retrieval authority slice.

## 3. Non-Responsibilities

- dope-context does not own PM authority. No inspected runtime path makes it canonical for tasks, sprint state, queue ordering, or Leantime/task-orchestrator writes.
- dope-context does not own chronicle or durable memory authority.
- dope-context does not own ConPort's structured decision or progress authority.
- dope-context does not own dope-memory chronology.
- dope-context does not own bridge or proxy authority. `dopecon-bridge`, MCP proxy config, and wrapper scripts expose or route transport, but they are not controlled by dope-context.
- dope-context is not the system of record for retrieved code or retrieved documents. Qdrant collections and snapshot files are derived retrieval artifacts.
- dope-context is not the system of record for retrieved decisions. In `search_all()`, decision data is optional and bridge-fetched from outside dope-context.
- dope-context is not proven to own any canonical API index, chat index, or global cross-repo knowledge base. `services/dope-context/config/multi_index_config.yaml` describes `api` and `chat` indices, but the inspected runtime does not implement them.

## 4. Key Surfaces

- Canonical retrieval runtime:
  `services/dope-context/src/mcp/server.py` is the canonical runtime surface observed in this checkout.
  `services/dope-context/Dockerfile` ends with `CMD ["python", "-m", "src.mcp.server"]`.
  `/info` returns `canonical_entrypoint: "python -m src.mcp.server"`.
- Retrieval/search API surfaces:
  MCP tools observed in `services/dope-context/src/mcp/server.py` include `index_workspace`, `search_code`, `get_index_status`, `clear_index`, `index_docs`, `docs_search`, `search_all`, `sync_workspace`, `sync_docs`, autonomous indexing controls, metrics tools, `configure_decision_auto_indexing`, and `get_chunk_complexity`.
- MCP/HTTP transport exposure:
  The same runtime registers `/health`, `/info`, `/autoindex/bootstrap`, and `/autoindex/status`.
  Transport resolution supports `stdio`, `http`, `sse`, and `streamable-http`.
  `docker/compose.core.yml` publishes dope-context on port `3010`.
- Autoindex/bootstrap/startup surfaces:
  `/autoindex/bootstrap` starts one bootstrap pass plus autonomous indexing startup for code and docs.
  `src/dopemux/cli.py` calls that endpoint during startup when `DOPEMUX_AUTO_INDEX_ON_STARTUP` is enabled.
- Storage/index/snapshot surfaces:
  `services/dope-context/src/utils/workspace.py` names collections as `code_{hash}` and `docs_{hash}` and places snapshot material under `~/.dope-context/snapshots/{workspace_hash}/`.
  `services/dope-context/src/mcp/server.py` uses that snapshot directory for BM25 cache, bootstrap marker, and decision sync config.
  These artifacts are derived retrieval state, not stronger authority.
- Non-canonical or secondary surfaces:
  `services/dope-context/src/mcp/simple_server.py` exists, but Docker and `/info` both point to `src.mcp.server`, not `simple_server.py`.
  `services/dope-context/bridge_adapter.py` exists, but it is not part of the inspected canonical retrieval runtime path.

## 5. System Boundaries

- dopemux:
  dope-context receives startup bootstrap requests from `src/dopemux/cli.py` at `/autoindex/bootstrap`.
  dope-context serves retrieval tools and health/info/bootstrap endpoints back to dopemux clients and operator flows.
  dope-context does not control dopemux CLI policy, session state, or PM authority.
- ConPort:
  dope-context does not own ConPort state.
  The inspected runtime can optionally include decision search results in `search_all()`, but it reaches them through dopecon-bridge, not by becoming ConPort authority.
  Optional event emission for search activity is present through `integration_bridge_connector.py`, but that is an integration path, not ownership.
- dope-memory:
  No direct dope-memory runtime coupling was proven in the inspected dope-context server.
  dope-context does not control chronology, receipts, or durable memory truth.
- task-orchestrator:
  No direct runtime call from dope-context to task-orchestrator was proven in the inspected dope-context server.
  dope-context does not control workflow state, scheduling, or PM normalization.
- dopecon-bridge:
  dope-context can receive optional decision-search responses from `GET /kg/decisions/search` when decision retrieval is enabled.
  dope-context can emit optional non-blocking search-related events to bridge-side integration code when the integration module imports successfully.
  dope-context does not control bridge routing, bridge storage, or bridge authority.

## 6. Authority Model

- Canonical:
  dope-context is canonical for retrieval and index behavior implemented by its own runtime. That includes workspace collection naming, retrieval-side indexing, retrieval tool behavior, and retrieval-side bootstrap/autonomous maintenance.
- Derived:
  Qdrant collections, BM25 caches, snapshot files, bootstrap markers, and decision sync config under `~/.dope-context/snapshots/{workspace_hash}/` are derived artifacts.
  Retrieved code, docs, and optional decision matches are derived views over upstream systems.
- Operational:
  Docker/compose wiring, transport selection, wrapper scripts, proxy config, and dopemux startup hooks are operational surfaces around dope-context.
  Autonomous indexing is operational maintenance for retrieval freshness, not proof of truth ownership.
- Unknown:
  Strong guarantees about index completeness, freshness across all paths, ranking quality, long-term durability, or cross-system consistency are not proven by the inspected runtime and tests.
  `bridge_adapter.py` suggests a broader "context" integration surface, but its canonical runtime role is UNKNOWN from the current evidence.

Indexed material remains owned upstream. Repository files remain the authority for code. Source documents remain the authority for documents. Optional decision results remain owned by their upstream memory/decision systems.

## 7. Known Drift / Issues

- Wrapper/runtime mismatch is evidence-backed drift. `scripts/mcp-wrappers/dope-context-wrapper.sh` executes `python /app/server.py`, but `services/dope-context/Dockerfile` runs `python -m src.mcp.server`. `repo-truth-pack/dope-context/DRIFT_REPORT.md` flags the same mismatch.
- Config/runtime mismatch is evidence-backed drift. `services/dope-context/config/multi_index_config.yaml` describes `api` and `chat` indices, but the inspected runtime surfaces implement only code and docs indexing/search.
- Legacy config-target drift is evidence-backed. `src/dopemux/config/manager.py` repairs legacy `services/dope-context/run_mcp.sh` references when that wrapper is missing, replacing them with generated `claude-context` config.
- Naming drift is present in MCP registry/config. `src/dopemux/mcp/registry.yaml` contains both `claude-context` and `dope-context` entries pointing at the same dope-context docker service on port `3010`.
- `/info` protocol reporting drift is evidence-backed. `repo-truth-pack/dope-context/DRIFT_REPORT.md` notes that `/info` reports `"protocol": "sse"` for non-stdio transports, even when runtime transport is `http` or `streamable-http`.
- Optional integration coverage is incomplete. `repo-truth-pack/dope-context/DRIFT_REPORT.md` records test gaps for ConPort integration, ADHD-driven `top_k`, and end-to-end decision search.
- Some older docs describe dope-context more broadly than the inspected runtime proves. The runtime code is narrower: retrieval plus indexing/search maintenance, with optional enrichments and transport surfaces.

## 8. Working Rules

- Treat dope-context as retrieval/indexing authority only.
- Treat retrieved results as leads back to source authority, not as canonical state.
- Trace code hits back to repository files before treating them as truth.
- Trace document hits back to source documents before treating them as truth.
- Do not use `search_all()` decision results as canonical ConPort, PM, or memory state.
- Keep dope-context, ConPort, dope-memory, and dopecon-bridge distinct even when one enriches another.
- Treat Qdrant collections, BM25 caches, snapshot files, and bootstrap markers as derived artifacts.
- Preserve `UNKNOWN` where indexing completeness, storage guarantees, freshness, or broader context-management behavior are not proven.
