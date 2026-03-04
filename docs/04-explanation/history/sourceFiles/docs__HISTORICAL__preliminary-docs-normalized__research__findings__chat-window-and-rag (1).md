# Document RAG Systems for dopemux: comprehensive research and recommendations

## Executive Summary

Based on extensive research into document RAG (Retrieval-Augmented Generation) systems for multi-LLM chat applications, this report recommends **DSPy with LiteLLM** as the primary RAG framework, **Qdrant** for vector storage with **Neo4j integration for GraphRAG**, and **Textual** for TUI implementation. The analysis reveals that modern RAG systems can achieve **20-25% accuracy improvements** when combining vector and graph approaches, while **hybrid search strategies** combining dense, sparse, and keyword retrieval provide optimal performance. For dopemux's tmux-based architecture with existing Redis, Qdrant, and Neo4j infrastructure, a production-ready solution can be implemented with performance benchmarks showing sub-100ms query latencies at 99% recall.

## RAG Framework Recommendations for Multi-LLM Chat

### Primary Recommendation: DSPy with LiteLLM

**DSPy** emerges as the standout framework for dopemux's multi-LLM requirements, offering:
- **Universal provider support** through LiteLLM integration (40+ providers including OpenAI, Claude, Gemini)
- **Declarative self-improving architecture** with automatic prompt optimization algorithms (MIPRO, GEPA)
- **Native session management** with advanced context handling
- **Modular design** perfect for provider switching mid-conversation

Implementation pattern for dopemux:
```python
import dspy
from litellm import completion

# Configure multiple providers
openai_llm = dspy.LM('openai/gpt-4o', max_tokens=1000)
claude_llm = dspy.LM('anthropic/claude-3-sonnet', max_tokens=1000)
gemini_llm = dspy.LM('google/gemini-1.5-pro', max_tokens=1000)

class MultiLLMRAG(dspy.Module):
    def forward(self, question, provider="openai"):
        llm_map = {"openai": openai_llm, "claude": claude_llm, "gemini": gemini_llm}
        with dspy.settings.context(lm=llm_map[provider]):
            context = self.retrieve(question).passages
            return self.generate_answer(context=context, question=question)
```

### Alternative Frameworks Evaluated

**Kotaemon** offers excellent user-friendliness with multi-user support and hybrid RAG pipelines, making it ideal if dopemux requires a polished UI alongside terminal interfaces. **LangChain** provides the largest ecosystem (700+ integrations) but requires more complex setup. **RAGFlow** and **Dify** excel for enterprise deployments with visual workflow builders.

## Document Processing Architecture

### Optimal Chunking Strategy

Research indicates a **hybrid chunking approach** delivers best results:

1. **Adaptive chunking based on content type**:
   - Technical documentation: 150-500 tokens with recursive splitting
   - Code files: 100 tokens with 15 token overlap
   - Conversational data: 300-800 tokens with speaker attribution
   - General documents: 500-1000 tokens with 100-200 token overlap

2. **Context-enriched chunking**: Attach metadata from neighboring chunks using windowed summarization for better retrieval understanding

3. **Implementation recommendation**: Use Unstructured.io's smart chunking strategies (by title, by page, by similarity) combined with LayoutPDFReader for context-aware processing

### Embedding Model Selection

**Top performers for production** (MTEB benchmark 2024-2025):
1. **SFR-Embedding-Mistral** (7B): 67.56% average score, best overall performance
2. **voyage-lite-02-instruct** (1.2B): 67.13% score, excellent efficiency
3. **OpenAI text-embedding-3-large**: 64.59% score, production-ready with strong API support

For dopemux, recommend **text-embedding-3-large** for premium quality or **BGE-M3** for open-source multilingual support with multi-functionality.

### Retrieval Techniques

**Three-way hybrid search** provides optimal performance:
```python
Hybrid Score = 0.7 × Dense_Score + 0.2 × Sparse_Score + 0.1 × BM25_Score
```

This approach combines:
- **Dense retrieval**: Semantic similarity using embedding vectors
- **Sparse retrieval**: SPLADE or traditional keyword matching  
- **Full-text search**: BM25 for exact term matching

Performance improvements show **8.9x QPS improvement** with optimized HNSW and better robustness across domains.

## Database Integration Patterns

### Qdrant Configuration for Production

```python
from qdrant_client import QdrantClient, models

client.create_collection(
    collection_name="rag_documents",
    vectors_config={
        "dense": models.VectorParams(size=1536, distance=models.Distance.COSINE),
        "sparse": models.SparseVectorParams()
    },
    optimizers_config=models.OptimizersConfigDiff(
        default_segment_number=0,
        max_segment_size=20000,
        memmap_threshold=20000
    ),
    quantization_config=models.BinaryQuantization(
        binary=models.BinaryQuantizationConfig(always_ram=True)
    )
)
```

Key optimizations:
- **Binary quantization** reduces memory by 30x with minimal accuracy loss
- **Hybrid search** combining dense and sparse vectors
- **Async batch processing** for high-throughput ingestion
- **Metadata indexing** on frequently filtered fields

### Neo4j GraphRAG Integration

Production implementations show **20-25% accuracy improvements** when combining graph and vector approaches:

```python
from neo4j_graphrag.retrievers import QdrantNeo4jRetriever

retriever = QdrantNeo4jRetriever(
    driver=neo4j_driver,
    client=qdrant_client,
    collection_name="document_chunks",
    id_property_external="neo4j_id",
    embedder=OpenAIEmbeddings(model="text-embedding-3-large")
)
```

Benefits include:
- **Relationship awareness** for complex entity connections
- **Multi-hop reasoning** through graph traversal
- **Explainable results** with clear reasoning paths

### Redis Integration for Session Management

Leverage existing Redis infrastructure for:
```python
from redisvl.extensions.session_manager import SemanticSessionManager

semantic_session = SemanticSessionManager(name='dopemux_session')
relevant_context = semantic_session.get_relevant(query="current input", top_k=5)
```

## Document Parsing Solutions

### Recommended Parsing Stack

1. **Primary**: **Docling by IBM** for comprehensive multi-format support
   - Handles PDF, DOCX, PPTX, HTML, images with advanced layout understanding
   - Built-in OCR with multiple engine support
   - Native LangChain/LlamaIndex integrations

2. **Specialized tools**:
   - **PyMuPDF4LLM**: Fast PDF to Markdown conversion
   - **Marker**: High-performance with 25 pages/second on GPU
   - **LlamaParse**: Premium quality for complex documents

3. **Table extraction**: Combine Unstructured.io's high-resolution strategy with specialized tools like Camelot for precise table extraction

### Context Maintenance Across LLM Switches

Implement a unified context management system:
```python
class MultiProviderContext:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.max_tokens = 4000
        
    def format_for_provider(self, messages, provider):
        if provider == "openai":
            return messages  # Native ChatML
        elif provider == "anthropic":
            return self.convert_to_anthropic_format(messages)
        elif provider == "llama":
            return self.convert_to_llama_format(messages)
```

Use **sliding window buffers** for recent context and **semantic compression** for older conversations to maintain coherence across provider switches.

## TUI Implementation with Textual

### Architecture for dopemux Integration

**Textual** framework provides the best foundation for tmux-compatible TUI:

```python
from textual.app import App
from textual.widgets import ScrollView, Input, Header, Footer

class DopemuxRAGChat(App):
    def compose(self):
        yield Header()
        yield Container(
            ScrollView(id="conversation"),
            Horizontal(
                Input(placeholder="Message or drag file...", id="input"),
                Button("🎤", id="voice"),
                Button("📎", id="file")
            )
        )
        yield Footer()
```

Key features:
- **Full tmux compatibility** with seamless pane integration
- **Rich markdown rendering** with syntax highlighting
- **Async operations** for non-blocking I/O
- **16.7M colors** and mouse support

### Voice Chat Integration

Implement push-to-talk with **Faster-Whisper** for STT (4x faster than OpenAI Whisper):
```python
from faster_whisper import WhisperModel
import sounddevice as sd

class VoiceInput:
    def __init__(self):
        self.model = WhisperModel("base")
        
    def transcribe_audio(self, audio_buffer):
        segments, info = self.model.transcribe(audio_buffer)
        return " ".join([s.text for s in segments])
```

For TTS, use **ElevenLabs** for premium quality (75ms latency) or **pyttsx3** for offline operation.

## Performance and Scalability Considerations

### Benchmark Results

Recent benchmarks show:
- **Qdrant**: 626 QPS at 99.5% recall for 1M vectors
- **Redis Query Engine**: 9.7x lower latencies than pgvector
- **Hybrid search**: 2.1x speedup with optimization
- **GraphRAG**: 20-25% accuracy improvement over vector-only

### Optimization Strategies

1. **Caching architecture**:
```python
class RAGCache:
    def __init__(self):
        self.redis_client = redis.Redis(max_connections=20)
    
    def cache_results(self, ttl=3600):
        # Implement semantic caching for repeated queries
```

2. **Connection pooling** for Qdrant and Neo4j with circuit breakers for failover
3. **Batch processing** with 50% cost reduction for non-real-time operations
4. **Incremental indexing** for dynamic document updates

### Scalability Recommendations

For dopemux's architecture:
- **Small scale (< 10K docs)**: Current infrastructure sufficient
- **Medium scale (10-100K docs)**: Add horizontal scaling for Qdrant
- **Large scale (100K+ docs)**: Implement sharding and multi-region deployment

## Cost Analysis and Deployment Options

### Open Source Implementation Costs

For dopemux with existing infrastructure:
- **Embedding generation**: Self-hosted BGE models (~$200-500/month compute)
- **Vector operations**: Minimal with existing Qdrant
- **LLM inference**: API costs based on provider selection
- **Total estimated**: $500-1500/month for medium-scale deployment

### Commercial Alternatives Comparison

- **Pinecone**: $150-500/month for 10K documents
- **Azure AI Search**: $250-500/month with recent 85% cost reduction
- **OpenAI Assistants**: $0.20/GB per day plus token costs

Given dopemux's existing infrastructure, **open source approach is recommended** for better cost efficiency and control.

## Implementation Roadmap

### Phase 1: Core RAG Pipeline (Week 1-2)
1. Integrate DSPy with LiteLLM for multi-LLM support
2. Configure Qdrant collections with hybrid search
3. Implement Docling for document parsing
4. Set up Redis semantic session management

### Phase 2: Advanced Features (Week 3-4)
1. Add Neo4j GraphRAG integration
2. Implement adaptive chunking strategies
3. Deploy Textual TUI with file upload
4. Add caching and optimization layers

### Phase 3: Voice and Polish (Week 5-6)
1. Integrate Faster-Whisper for voice input
2. Add push-to-talk functionality
3. Implement comprehensive error handling
4. Performance testing and optimization

## Successful Implementation Examples

1. **Lettria's Production GraphRAG**: Achieved 20-25% accuracy improvement in aerospace and finance applications using Qdrant + Neo4j
2. **Microsoft's GraphRAG**: Demonstrated cost optimization through graph summarization
3. **MongoDB Atlas Vector Search**: 100 tokens with 15 token overlap proved optimal for code repositories

## Key Success Factors

1. **Start with hybrid search** combining dense, sparse, and keyword approaches
2. **Implement smart chunking** adapted to document types
3. **Use connection pooling** and caching extensively
4. **Monitor performance** with comprehensive metrics
5. **Plan for provider failures** with fallback strategies

This comprehensive research provides dopemux with a clear path to implementing a state-of-the-art document RAG system that leverages existing infrastructure while supporting multi-LLM chat capabilities through a sophisticated terminal interface.
