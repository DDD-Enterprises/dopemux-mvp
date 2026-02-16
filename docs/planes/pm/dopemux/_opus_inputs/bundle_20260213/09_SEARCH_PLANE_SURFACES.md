# 09 Search Plane Surfaces

## Scope covered
- `dope-context` (confirmed active in `compose.yml`)
- `serena` (confirmed service exists; runtime behavior partly UNKNOWN)

## Dope-context (proven)

| area | observed behavior | determinism posture |
|---|---|---|
| Retrieval stack | hybrid search (dense + BM25) + optional reranker | non-deterministic risk when rerank fails/fallback path changes ordering |
| Dynamic result count | `top_k` can be overridden via ADHD feature flag integration | non-deterministic by user state/feature flag state |
| Cache/snapshot use | BM25 index loaded from snapshot file if present | cache/file freshness affects ranking |
| Workspace scoping | workspace-derived hashed collection names (`code_<hash>`, `docs_<hash>`) \| scoped to workspace path, not explicit `workspace_id`/`worktree_id` in event envelope |
| Qdrant writes | indexing pipeline creates collections + upserts points | index update timing affects retrieval results |

## Serena (proven vs unknown)

| question | status | evidence |
|---|---|---|
| Serena exists as a service? | **YES** | `compose.yml:538-558` |
| Serena is MCP server or internal service? | **MCP server process in active compose path** | docker wrapper executes `serena start-mcp-server` via `mcp-proxy` |
| What it reads/writes (Redis/Qdrant/Postgres/filesystem)? | **UNKNOWN for compose-deployed Serena runtime** | Dockerfile installs external Git package (`git+https://github.com/oraios/serena.git`) so runtime internals are outside this repo snapshot |
| Does Serena caching affect ranking determinism? | **UNKNOWN for compose-deployed runtime** | no local source-of-truth for external package internals in this repo |

Note: repo also contains `services/serena/` source tree, but compose path for active `serena` points to `docker/mcp-servers/serena` wrapper, not directly to `services/serena`.

## Evidence excerpts
- `services/dope-context/src/mcp/server.py:155-176`
```text
async def get_dynamic_top_k(user_id: str = "default", requested_top_k: int = 10) -> int:
    """
    Get dynamic top_k from ADHD Engine based on user's attention state.
    """
    if adhd_config and feature_flags:
        try:
            from feature_flags import FEATURE_ADHD_ENGINE_DOPE_CONTEXT

            if await feature_flags.is_enabled(
                FEATURE_ADHD_ENGINE_DOPE_CONTEXT,
                "dope-context",
                user_id
            ):
                return await adhd_config.get_max_results(user_id)
```
- `services/dope-context/src/mcp/server.py:810-823`
```text
        # Load BM25 index from cache if available
        bm25_index = BM25Index()
        bm25_cache_path = get_snapshot_dir(workspace) / "bm25_index.pkl"

        if bm25_cache_path.exists():
            try:
                with open(bm25_cache_path, 'rb') as f:
                    raw = f.read()
                import json, pickle
                try:
                    cached = json.loads(raw.decode('utf-8')) if raw.strip().startswith(b'{') else pickle.loads(raw)
                except Exception:
                    cached = pickle.loads(raw)
```
- `services/dope-context/src/mcp/server.py:917-925`
```text
        if use_reranking and search_results:
            try:
                rerank_response = await reranker.rerank(
                    query=query,
                    results=search_results[:50],  # Rerank top-50
                )

                # Return top-k from reranked
                final_results = rerank_response.top_results[:top_k]
```
- `services/dope-context/src/mcp/server.py:958-963`
```text
            except Exception as rerank_error:
                logger.warning(f"Reranking failed, returning dense results: {rerank_error}")
                # Fall through to return without reranking

        # Return without reranking (or reranking failed)
        raw_results = [
```
- `services/dope-context/src/utils/workspace.py:163-168`
```text
    workspace_hash = workspace_to_hash(workspace_path)

    return (
        f"code_{workspace_hash}",
        f"docs_{workspace_hash}",
    )
```
- `compose.yml:538-552`
```text
  serena:
    build:
      context: ./docker/mcp-servers/serena
      dockerfile: Dockerfile
    container_name: dopemux-mcp-serena
    restart: unless-stopped
    networks:
- dopemux-network
    ports:
- "3006:3006"
- "4006:4006"
    environment:
- MCP_SERVER_PORT=3006
- HTTP_PORT=4006
- WORKSPACE_ID=${WORKSPACE_ID:-/workspace}
```
- `docker/mcp-servers/serena/Dockerfile:11-13`
```text
# Install dependencies (including serena from git)
# Pinning to main branch for now, ideally should be a tag
RUN pip install "git+https://github.com/oraios/serena.git" mcp-proxy fastapi uvicorn
```
- `docker/mcp-servers/serena/wrapper.py:29-37`
```text
        cmd = [
            'mcp-proxy',
            '--transport', 'streamablehttp',
            '--port', str(self.port),
            '--host', '0.0.0.0',
            '--allow-origin', '*',
            '--',
            'serena', 'start-mcp-server'
        ]
```
