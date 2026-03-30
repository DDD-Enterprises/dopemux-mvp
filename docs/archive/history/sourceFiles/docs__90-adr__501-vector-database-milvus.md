# ADR-501: Vector Database Selection (Milvus)

**Status**: Accepted
**Date**: 2025-09-20
**Deciders**: @hu3mann, DOPEMUX memory architecture team
**Tags**: #critical #vector-database #semantic-search #rag

## 🎯 Context

DOPEMUX requires semantic search capabilities for code patterns, documentation retrieval, and contextual understanding. Traditional keyword-based search is insufficient for AI-powered development workflows that need to understand code semantics and find similar patterns.

### Semantic Search Requirements
- **Code similarity**: Find similar functions, patterns, and implementations
- **Documentation retrieval**: Context7-style documentation access with relevance ranking
- **Pattern recognition**: Identify recurring code patterns and architectural decisions
- **Cross-project learning**: Apply patterns learned from one project to another
- **ADHD accommodation**: Intelligent context suggestions without explicit search

### Vector Database Options Evaluated
1. **Milvus**: Open-source vector database with hybrid search
2. **Pinecone**: Managed vector database service
3. **Weaviate**: Vector database with built-in ML models
4. **Chroma**: Lightweight embedding database
5. **PostgreSQL with pgvector**: Extension for existing database
6. **Qdrant**: Vector similarity search engine

### Key Decision Factors
- **Hybrid search**: Support both vector similarity and keyword matching
- **Performance**: Sub-100ms queries for real-time development workflow
- **Scalability**: Handle large codebases and documentation corpora
- **Integration**: Work with claude-context MCP server
- **Local deployment**: Support offline development environments
- **Cost**: Open-source with reasonable resource requirements

## 🎪 Decision

**DOPEMUX will use Milvus as the vector database** for semantic search and RAG capabilities.

### Technical Implementation
- **Embedding model**: OpenAI text-embedding-3-large (3072 dimensions)
- **Index type**: HNSW (Hierarchical Navigable Small World) for balanced performance
- **Similarity metric**: Cosine similarity for semantic relevance
- **Collection strategy**: Separate collections for code, docs, and patterns
- **Hybrid search**: Combine vector similarity with BM25 keyword matching

### Architecture Integration
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ User Query      │───►│ Embedding Gen   │───►│ Milvus Search   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────▼─────────┐
│ Ranked Results  │◄───│ Hybrid Scoring  │◄───│ Vector Results   │
└─────────────────┘    └─────────────────┘    └─────────────────────┘
```

### Data Collections
- **`codebase_vectors`**: Code embeddings with metadata (file, function, language)
- **`documentation_vectors`**: Documentation chunks with source links
- **`pattern_vectors`**: Learned patterns and architectural decisions
- **`conversation_vectors`**: Agent conversation history for context retrieval

### Performance Optimizations
- **Indexing strategy**: HNSW with ef_construction=200, M=16
- **Caching**: Redis integration for frequently accessed vectors
- **Batch processing**: Bulk embedding generation and insertion
- **Resource limits**: Memory-mapped storage for large collections

## 🔄 Consequences

### Positive
- ✅ **Semantic understanding**: Find relevant code by meaning, not just keywords
- ✅ **Hybrid search**: Best of both vector similarity and keyword matching
- ✅ **High performance**: <100ms queries for real-time development
- ✅ **Open source**: No vendor lock-in, full control over data
- ✅ **Scalability**: Handles large codebases efficiently
- ✅ **Rich metadata**: Support for complex filtering and faceting
- ✅ **ADHD-friendly**: Intelligent suggestions reduce search cognitive load
- ✅ **Integration ready**: Works seamlessly with claude-context MCP server

### Negative
- ❌ **Resource intensive**: Requires significant memory for vector storage
- ❌ **Setup complexity**: More complex than simple keyword search
- ❌ **Embedding dependency**: Requires stable embedding API access
- ❌ **Index maintenance**: Periodic reindexing needed for optimal performance
- ❌ **Cold start**: Initial embedding generation takes time

### Neutral
- ℹ️ **Learning curve**: Team needs vector database expertise
- ℹ️ **Operational overhead**: Additional database to monitor and maintain
- ℹ️ **Version compatibility**: Need to track Milvus version compatibility

## 🧠 ADHD Considerations

### Cognitive Load Reduction
- **Intelligent suggestions**: Surface relevant code without explicit search queries
- **Context awareness**: Understand what user is working on and suggest related patterns
- **Pattern recognition**: Automatically identify similar problems and solutions
- **Reduced decision fatigue**: Present most relevant results first

### Attention-Friendly Features
- **Instant results**: <100ms response time prevents attention drift
- **Progressive disclosure**: Most relevant results first, details on demand
- **Visual relevance**: Clear relevance scoring and similarity indicators
- **Context preservation**: Remember successful search patterns

### Integration with ADHD Workflow
- **Automatic context**: Suggest relevant patterns based on current work
- **Break recovery**: Help restore context after attention breaks
- **Learning assistance**: Surface previously successful solutions
- **Decision support**: Provide examples when facing architectural choices

## 🔗 References
- [Multi-Level Memory Architecture](003-multi-level-memory-architecture.md)
- [Claude-Context MCP Integration](../04-explanation/architecture/mcp-integration.md)
- [Semantic Search Explanation](../04-explanation/features/mcp-ecosystem.md)
- [DOPEMUX Memory Architecture](../HISTORICAL/preliminary-docs-normalized/docs/DOPEMUX_MEMORY_ARCHITECTURE.md)
- Milvus Documentation: Vector similarity search and hybrid search
- Implementation: claude-context MCP server with Milvus backend