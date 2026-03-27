# Semantic Search Implementation Notes

## Claude-Context Configuration (exclude /docs)

```json
{
  "roots": ["src", "packages", "apps", "services"],
  "exclude": ["docs/**", "**/*.pdf", "**/*.html", "**/*.md"],
  "embeddings": { "provider": "voyageai", "model": "voyage-code-3" }
}
```

## Milvus docs_index Schema (logical)

- **id:** VARCHAR (PK)
- **embedding:** FLOAT_VECTOR (dim = doc model)
- **text:** VARCHAR (≤ 8k)
- **meta:** JSON (path, title, page, section, tags, acl, hash, timestamps)
- **Optional:** sparse_vector: SPARSE_FLOAT_VECTOR for hybrid

## Index Parameters (defaults)

- **Dense:** HNSW M=16, efConstruction=200; Search ef=64 (tune 64–128)
- **Metric:** COSINE (or IP)
- **Sparse:** SPARSE_INVERTED_INDEX

## DocRAG Search (pseudocode)

```python
results32 = milvus.search(dense_query, limit=32, [optional sparse_query, weights])
reranked = voyage.rerank("rerank-2.5", query, [r.text for r in results32], top_n=8)
return top8 with metadata
```

## Dopemux MCP Wiring (example)

```json
{
  "mcpServers": {
    "claude-context": {
      "command": "npx",
      "args": ["-y", "@zilliz/claude-context-mcp@latest"]
    },
    "milvus": {
      "command": "mcp-server-milvus",
      "env": { "MILVUS_URI": "http://milvus:19530" }
    },
    "docs-rag": {
      "command": "./bin/docrag"
    },
    "pluggedin": {
      "command": "npx",
      "args": ["-y", "@pluggedin/pluggedin-mcp-proxy@latest"],
      "env": { "PLUGGEDIN_API_KEY": "${PLUGGEDIN_API_KEY}" }
    }
  }
}
```

## Rollout Checklist

- [ ] Exclude docs in CC; rebuild code_index
- [ ] Create docs_index; set index params; load eval deck
- [ ] Deploy DocRAG with reranker; feature flag for hybrid
- [ ] Add routing + tools; wire logs & metrics
- [ ] Run A/B on hybrid weights; lock SLOs