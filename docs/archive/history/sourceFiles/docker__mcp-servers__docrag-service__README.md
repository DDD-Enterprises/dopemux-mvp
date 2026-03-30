# DocRAG Service

A semantic search service for Dopemux that provides document ingestion and retrieval using Milvus vector database and Voyage AI embeddings with reranking.

## Features

- **Document Processing**: Support for PDF, Markdown, HTML, DOCX, and plain text files
- **Semantic Search**: Dense vector search using Voyage AI embeddings
- **Hybrid Search**: Optional combination of dense and sparse (BM25-like) retrieval
- **Reranking**: Voyage AI rerank-2.5 for improved relevance ordering
- **MCP Integration**: Native Model Context Protocol server for Claude integration
- **REST API**: Full FastAPI interface for programmatic access
- **CLI Tools**: Command-line utilities for batch document ingestion

## Architecture

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   Documents │───▶│   DocRAG     │───▶│   Milvus    │
│ (PDF, MD,   │    │   Service    │    │  Vector DB  │
│  HTML, etc) │    └──────┬───────┘    └─────────────┘
└─────────────┘           │                     ▲
                          ▼                     │
                   ┌──────────────┐            │
                   │  Voyage AI   │────────────┘
                   │ Embeddings & │
                   │  Reranking   │
                   └──────────────┘
```

## Quick Start

### 1. Environment Setup

```bash
cp .env.example .env
# Edit .env with your Voyage AI API key
```

### 2. Start with Docker Compose

The service is included in the main Dopemux MCP stack:

```bash
cd docker/mcp-servers
docker-compose up docrag-service
```

### 3. Ingest Documents

```bash
# Single document
docker exec mcp-docrag docrag-ingest /workspace/docs/README.md

# Entire directory
docker exec mcp-docrag docrag-ingest --directory /workspace/docs
```

### 4. Search Documents

Using the MCP interface:
```python
# Via Claude Code MCP tools
docs_search("How to configure semantic search?")
```

Using the REST API:
```bash
curl -X POST http://localhost:3009/api/search \\
  -H "Content-Type: application/json" \\
  -d '{"query": "semantic search configuration", "limit": 5}'
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VOYAGEAI_API_KEY` | - | **Required** Voyage AI API key |
| `DOCRAG_PORT` | 3009 | Service port |
| `MILVUS_HOST` | milvus | Milvus server host |
| `DOCS_COLLECTION_NAME` | docs_index | Milvus collection name |
| `ENABLE_HYBRID_SEARCH` | true | Enable hybrid dense+sparse search |
| `ENABLE_RERANKING` | true | Enable Voyage reranking |
| `DEFAULT_CHUNK_SIZE` | 1000 | Document chunk size |
| `MAX_FILE_SIZE_MB` | 50 | Maximum file size limit |

### Chunking Strategy

- **Default**: 1000 characters with 100 character overlap
- **Adaptive**: Preserves paragraph and sentence boundaries
- **Token-aware**: Uses tiktoken for accurate token counting

### Search Modes

1. **Dense Search**: Pure semantic vector search
2. **Hybrid Search**: Combines dense vectors with sparse (BM25-like) scoring
3. **Reranked Search**: Applies Voyage rerank-2.5 for optimal relevance

## API Reference

### MCP Tools

#### `docs_search(query, limit=8, hybrid=false, rerank=true)`
Search documents using semantic search.

#### `docs_ingest(source_path, chunk_size=1000, force_reindex=false)`
Ingest a document into the search index.

#### `docs_health()`
Get service health status.

### REST Endpoints

- `GET /health` - Health check
- `POST /api/search` - Search documents
- `POST /api/ingest` - Ingest document
- `GET /mcp/tools` - List MCP tools

## Integration with Dopemux

### MCP Server Configuration

Add to your Claude Code MCP configuration:

```json
{
  "docrag": {
    "command": "docker",
    "args": ["exec", "-i", "mcp-docrag", "python", "-m", "docrag.main"],
    "env": {
      "VOYAGEAI_API_KEY": "${VOYAGEAI_API_KEY}"
    }
  }
}
```

### Document Organization

The service integrates with the RFC architecture:

- **Code Search**: Handled by Claude-Context (excluded from DocRAG)
- **Document Search**: All non-code files processed by DocRAG
- **Hybrid Queries**: Router determines which service to use

## Performance

### Typical Latencies
- **Search**: p95 < 350ms (warm cache)
- **Ingestion**: ~1-3s per document (depends on size)
- **Reranking**: +50-100ms per query

### Scaling
- **Single Instance**: Handles ~100 QPS search
- **Horizontal**: Scale with load balancer + shared Milvus
- **Vertical**: Increase memory for larger embeddings cache

## Security

### Access Control
- File type restrictions (configurable extensions)
- File size limits (default 50MB)
- Metadata-based ACL support
- Content sensitivity classification

### Privacy
- Self-hosted Milvus for sensitive data
- Optional external API usage (Voyage AI)
- Audit logging for compliance

## Troubleshooting

### Common Issues

1. **Milvus Connection Failed**
   ```bash
   # Check Milvus status
   docker logs milvus-standalone

   # Verify network connectivity
   docker exec mcp-docrag curl -f http://milvus:19530/healthz
   ```

2. **Voyage API Errors**
   ```bash
   # Check API key
   echo $VOYAGEAI_API_KEY

   # Test connectivity
   curl -H "Authorization: Bearer $VOYAGEAI_API_KEY" \\
        https://api.voyageai.com/v1/models
   ```

3. **Import Errors**
   ```bash
   # Check dependencies
   docker exec mcp-docrag pip list | grep -E "(pymilvus|voyageai)"

   # Rebuild if needed
   docker-compose build docrag-service
   ```

### Monitoring

View logs:
```bash
docker logs mcp-docrag --follow
```

Check metrics:
```bash
curl http://localhost:3009/health
```

## Development

### Local Setup

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Start development server
python -m docrag.main
```

### Adding New Document Types

1. Extend `DocumentType` enum in `models.py`
2. Add extraction logic in `processing.py`
3. Update file type detection
4. Add tests for new format

## Related Documentation

- [RFC-0042: Hybrid MCP Semantic Search](../../docs/91-rfc/rfc-0042-semantic-search-mcp.md)
- [ADR-0028: Hybrid MCP Architecture](../../docs/90-adr/adr-0028-hybrid-mcp-semantic-search.md)
- [Arc42 Architecture](../../docs/94-architecture/arc42-dopemux-semantic-search.md)