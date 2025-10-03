# Claude-Context v2

Next-generation semantic code search and DocuRAG system for Dopemux.

## Features

- **Semantic Code Search**: VoyageAI voyage-code-3 embeddings with multi-vector retrieval
- **Hybrid Search**: Dense vectors + BM25 sparse with RRF fusion (v2)
- **Advanced Reranking**: voyage-rerank-2.5 for quality optimization
- **ARM M4 Pro Compatible**: Qdrant vector database with proven compatibility
- **ADHD Optimized**: Progressive disclosure, visual progress, result limiting
- **MCP Interface**: FastMCP server for Claude Code integration

## Quick Start

### Installation

```bash
cd services/claude-context-v2
pip install -r requirements.txt
```

### Configuration

Set your VoyageAI API key:
```bash
export VOYAGE_API_KEY="your-voyage-api-key"
```

### Usage

```bash
# Start MCP server (stdio mode)
python src/mcp/server.py

# Or via Docker
docker-compose up claude-context-v2
```

## Architecture

```
┌─────────────────────────────────────────┐
│       Claude Code (via MCP)             │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│     MCP Server (FastMCP stdio)          │
│  Tools: semantic_search, code_search,   │
│         index_workspace, search_stats   │
└────────────────┬────────────────────────┘
                 │
        ┌────────┼────────┐
        │        │        │
┌───────▼──┐ ┌──▼─────┐ ┌▼────────┐
│Preprocess│ │ Search │ │ Rerank  │
│ Pipeline │ │ Engine │ │  Layer  │
└───────┬──┘ └──┬─────┘ └┬────────┘
        │       │         │
        │   ┌───▼─────────▼───┐
        │   │    VoyageAI     │
        │   │  (Embed+Rerank) │
        │   └───┬─────────────┘
        │       │
    ┌───▼───────▼──┐
    │    Qdrant    │
    │ Multi-Vector │
    │   Store      │
    └──────────────┘
```

## Configuration Defaults

All defaults are in `config/defaults.yaml` with citations and tuning guidance.

**Key Parameters**:
- Embeddings: voyage-code-3 (1024d), DOT similarity
- Chunking: 500 tokens + 12% overlap
- HNSW: m=16, ef_construct=200, ef=150
- Reranking: top-50 → rerank → top-10
- Rate limits: 60 RPM with exponential backoff

## Development Status

**Phase 1**: Vector Store - VALIDATED (Qdrant ARM M4 Pro)
**Phase 2**: VoyageAI Integration - NEXT
**Phase 3**: Preprocessing Pipeline - PLANNED
**Phase 4**: Dense Search Engine - PLANNED
**Phase 5**: Reranking Layer - PLANNED
**Phase 6**: MCP Server - PLANNED
**Phase 7**: Dopemux Integration - PLANNED

## Testing

```bash
# Run full test suite
pytest tests/

# ARM M4 compatibility
pytest tests/test_qdrant_arm.py

# VoyageAI integration
pytest tests/test_voyageai.py

# Search quality benchmarks
pytest tests/test_search_quality.py
```

## Tuning Playbook

Ordered by impact on quality:

1. **ef parameter**: 100 → 150 → 200 (tune recall vs latency)
2. **Chunk size**: 400 → 500 → 600 tokens (measure Recall@10)
3. **Rerank candidates**: 50 → 75 → 100 (if latency allows)
4. **Dimension**: 1024 → 512 → 256 (Matryoshka for cost)
5. **Overlap**: 10% → 12% → 15% (marginal gains)

## Integration

### ConPort
- Log indexing decisions
- Track search effectiveness metrics
- Store query patterns

### Serena LSP
- Use Tree-sitter for code chunking
- Coordinate semantic + symbol search
- Cross-reference results

### Dopemux Event Bus
- Publish indexing progress
- Emit search events for ADHD dashboard
- Trigger incremental updates (v2)
