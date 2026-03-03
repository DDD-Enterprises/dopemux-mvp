# Voyage AI Models Integration Reference

## Overview

The Dopemux RAG system leverages specialized Voyage AI models for high-quality embeddings and reranking. This document provides comprehensive integration details, API specifications, and optimization guidelines for the embedding and reranking components.

## Model Portfolio

### Embedding Models

| Model | Purpose | Dimensions | Max Input | Performance |
|-------|---------|------------|-----------|-------------|
| voyage-context-3 | Documentation | 1024 (default) | 32,000 tokens | Best for long text |
| voyage-code-3 | Source code | 1024 (default) | 16,000 tokens | Code-specialized |

### Reranking Models

| Model | Purpose | Max Input | Latency | Performance Boost |
|-------|---------|-----------|---------|-------------------|
| rerank-2.5 | Production quality | 32,000 tokens | ~1.5s/64 candidates | +7-8% NDCG@10 |
| rerank-2.5-lite | Speed-optimized | 32,000 tokens | ~0.8s/64 candidates | +5-6% NDCG@10 |

## Embedding Model Specifications

### voyage-context-3 (Documentation)

#### Model Capabilities
- **Optimized for**: Long-form text, documentation, explanatory content
- **Context Awareness**: Encodes global document structure and relationships
- **Dimension Flexibility**: Supports 1024, 512, 256 dimensions with minimal quality loss
- **Normalization**: Outputs L2-normalized vectors for cosine similarity

#### API Integration
```python
import voyageai

# Initialize client
vo = voyageai.Client(api_key="your-api-key")

# Embed documentation chunks
def embed_documents(texts, model="voyage-context-3"):
    """Embed documentation text with optimal settings."""
    response = vo.embed(
        texts=texts,
        model=model,
        input_type="document",  # Optimize for indexing
        truncation=True,
        dimensions=1024  # Full dimension for max quality
    )
    return response.embeddings

# Example usage
doc_chunks = [
    "This section describes the authentication service architecture...",
    "The caching layer uses Redis for session storage..."
]
embeddings = embed_documents(doc_chunks)
```

#### Preprocessing Requirements
```python
def preprocess_doc_chunk(text, prelude):
    """Prepare document text for embedding with context."""
    # Combine prelude with content for richer embeddings
    combined_text = f"{prelude}\n\n{text}" if prelude else text

    # Clean and normalize
    normalized = clean_text(combined_text)

    # Ensure within token limit (32k tokens ≈ 120k chars)
    if len(normalized) > 120000:
        normalized = truncate_intelligently(normalized, max_chars=120000)

    return normalized
```

### voyage-code-3 (Source Code)

#### Model Capabilities
- **Optimized for**: Programming languages, code structure, API patterns
- **Syntax Awareness**: Understands code semantics across 40+ languages
- **Performance**: 13-17% better than OpenAI models on code retrieval tasks
- **Efficiency**: Maintains quality at reduced dimensions (512d with <2% loss)

#### API Integration
```python
def embed_code(code_snippets, model="voyage-code-3"):
    """Embed code with specialized optimization."""
    response = vo.embed(
        texts=code_snippets,
        model=model,
        input_type="document",
        truncation=True,
        dimensions=1024  # Use full dimension for complex code
    )
    return response.embeddings

# Example usage
code_chunks = [
    """
    def authenticate_user(username, password):
        '''Authenticate user credentials against LDAP.'''
        if not username or not password:
            raise ValueError("Missing credentials")
        return ldap.authenticate(username, password)
    """,
    """
    // Redis cache configuration
    const redis = new Redis({
        host: process.env.REDIS_HOST,
        port: process.env.REDIS_PORT,
        retryDelayOnFailover: 100
    });
    """
]
code_embeddings = embed_code(code_chunks)
```

#### Code-Specific Preprocessing
```python
def preprocess_code_chunk(code, file_path, start_line, end_line, prelude=None):
    """Prepare code for embedding with context."""
    # Add contextual information
    context_header = f"# File: {file_path} (lines {start_line}-{end_line})\n"

    # Optional prelude for complex code
    if prelude:
        context_header += f"# {prelude}\n"

    full_content = f"{context_header}{code}"

    # Respect 16k token limit for code model
    if len(full_content) > 60000:  # ~16k tokens ≈ 60k chars
        full_content = truncate_code_intelligently(full_content, max_chars=60000)

    return full_content
```

## Reranking Model Integration

### rerank-2.5 (Production)

#### Model Capabilities
- **Cross-Attention**: Deep interaction between query and each candidate
- **Instruction Following**: Accepts natural language ranking guidance
- **High Throughput**: Processes 64 candidates in ~1.5 seconds on GPU
- **Quality**: Consistent 7-8% improvement in ranking accuracy

#### API Integration
```python
def rerank_candidates(query, candidates, instruction, model="rerank-2.5"):
    """Rerank candidates with role-specific instruction."""

    # Prepare reranking input
    rerank_input = [
        {
            "query": query,
            "document": candidate["text"]
        }
        for candidate in candidates
    ]

    # Execute reranking with instruction
    response = vo.rerank(
        query=query,
        documents=[c["text"] for c in candidates],
        model=model,
        top_k=len(candidates),  # Get scores for all
        instruction=instruction  # Role-specific guidance
    )

    return response.results

# Example usage
reranked = rerank_candidates(
    query="How does the authentication service store tokens?",
    candidates=initial_candidates,
    instruction="Prioritize code snippets and implementation details; use design docs only if code context is insufficient."
)
```

#### Role-Specific Instructions

```python
RERANK_INSTRUCTIONS = {
    "Developer:CodeImplementation": {
        "instruction": """Prioritize code snippets, implementation details, and concrete examples.
        Surface working code over documentation. Focus on executable patterns and API usage.""",
        "boost_types": ["code", "example", "implementation"]
    },

    "Developer:Debugging": {
        "instruction": """Emphasize error handling, logging, debugging tools, and troubleshooting patterns.
        Prioritize code that shows error conditions and their resolution.""",
        "boost_types": ["error_handling", "debugging", "logs"]
    },

    "Architect:SystemDesign": {
        "instruction": """Focus on high-level architecture, design patterns, and system interactions.
        Prioritize ADRs, design documents, and architectural code examples over implementation details.""",
        "boost_types": ["architecture", "design", "patterns", "adr"]
    },

    "SRE:IncidentResponse": {
        "instruction": """Prioritize operational runbooks, monitoring configurations, deployment code,
        and incident response procedures. Focus on actionable operational guidance.""",
        "boost_types": ["runbook", "monitoring", "deployment", "operations"]
    },

    "PM:FeatureDiscussion": {
        "instruction": """Focus exclusively on user-facing feature descriptions, requirements,
        and product specifications. Avoid technical implementation details and code.""",
        "boost_types": ["requirements", "features", "specs", "user_stories"]
    }
}
```

### rerank-2.5-lite (Speed-Optimized)

#### Performance Characteristics
```python
RERANKER_PERFORMANCE = {
    "rerank-2.5": {
        "latency_p50": 1200,  # ms for 64 candidates
        "latency_p95": 1800,
        "accuracy_boost": 0.078,  # +7.8% NDCG@10
        "throughput": 40  # candidates/second
    },
    "rerank-2.5-lite": {
        "latency_p50": 800,   # ms for 64 candidates
        "latency_p95": 1200,
        "accuracy_boost": 0.056,  # +5.6% NDCG@10
        "throughput": 60  # candidates/second
    }
}
```

#### Dynamic Model Selection
```python
def select_reranker_model(num_candidates, latency_target_ms, accuracy_priority):
    """Select optimal reranker based on requirements."""

    if accuracy_priority and latency_target_ms > 1500:
        return "rerank-2.5"
    elif num_candidates > 32 and latency_target_ms < 1000:
        return "rerank-2.5-lite"
    elif accuracy_priority:
        return "rerank-2.5"
    else:
        return "rerank-2.5-lite"

# Usage in production
model = select_reranker_model(
    num_candidates=len(candidates),
    latency_target_ms=1200,
    accuracy_priority=role in ["Architect", "PM"]  # High accuracy for strategic roles
)
```

## Performance Optimization

### Batch Processing

#### Embedding Batch Optimization
```python
def batch_embed_documents(texts, batch_size=100, model="voyage-context-3"):
    """Efficiently embed large document collections."""
    embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]

        try:
            batch_embeddings = vo.embed(
                texts=batch,
                model=model,
                input_type="document",
                dimensions=1024
            ).embeddings

            embeddings.extend(batch_embeddings)

            # Rate limiting
            time.sleep(0.1)  # Respect API limits

        except Exception as e:
            logger.error(f"Batch embedding failed: {e}")
            # Retry with smaller batch or individual requests

    return embeddings
```

#### Reranking Batch Optimization
```python
def batch_rerank_with_fallback(query, candidates_groups, instruction):
    """Rerank multiple candidate groups with fallback strategies."""
    results = []

    for candidates in candidates_groups:
        try:
            # Try full reranking first
            reranked = vo.rerank(
                query=query,
                documents=[c["text"] for c in candidates],
                model="rerank-2.5",
                instruction=instruction,
                top_k=min(12, len(candidates))
            ).results

            results.append(reranked)

        except Exception as e:
            logger.warning(f"Reranking failed: {e}, falling back to lite model")

            # Fallback to lite model
            try:
                reranked = vo.rerank(
                    query=query,
                    documents=[c["text"] for c in candidates],
                    model="rerank-2.5-lite",
                    instruction=instruction,
                    top_k=min(12, len(candidates))
                ).results

                results.append(reranked)

            except Exception as e2:
                logger.error(f"Lite reranking also failed: {e2}")
                # Return original ordering as last resort
                results.append(candidates[:12])

    return results
```

### Caching Strategy

#### Embedding Cache
```python
from functools import lru_cache
import hashlib

class EmbeddingCache:
    def __init__(self, max_size=10000):
        self.cache = {}
        self.max_size = max_size

    def get_cache_key(self, text, model):
        """Generate stable cache key for text."""
        content_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
        return f"{model}:{content_hash}"

    @lru_cache(maxsize=10000)
    def get_embedding(self, text, model="voyage-context-3"):
        """Get embedding with caching."""
        cache_key = self.get_cache_key(text, model)

        if cache_key in self.cache:
            return self.cache[cache_key]

        # Generate new embedding
        response = vo.embed(texts=[text], model=model)
        embedding = response.embeddings[0]

        # Cache result
        if len(self.cache) < self.max_size:
            self.cache[cache_key] = embedding

        return embedding
```

#### Reranking Cache
```python
class RerankerCache:
    def __init__(self, ttl_seconds=3600):  # 1 hour TTL
        self.cache = {}
        self.ttl = ttl_seconds

    def get_cache_key(self, query, candidates_hash, instruction):
        """Generate cache key for reranking request."""
        key_content = f"{query}:{candidates_hash}:{instruction}"
        return hashlib.sha256(key_content.encode()).hexdigest()[:16]

    def get_candidates_hash(self, candidates):
        """Generate hash for candidate set."""
        candidate_texts = [c["text"][:100] for c in candidates]  # First 100 chars
        combined = "|".join(sorted(candidate_texts))
        return hashlib.sha256(combined.encode()).hexdigest()[:8]

    def get_reranked(self, query, candidates, instruction):
        """Get reranked results with caching."""
        candidates_hash = self.get_candidates_hash(candidates)
        cache_key = self.get_cache_key(query, candidates_hash, instruction)

        # Check cache
        now = time.time()
        if cache_key in self.cache:
            cached_result, timestamp = self.cache[cache_key]
            if now - timestamp < self.ttl:
                return cached_result

        # Generate new ranking
        reranked = vo.rerank(
            query=query,
            documents=[c["text"] for c in candidates],
            instruction=instruction,
            model="rerank-2.5"
        ).results

        # Cache result
        self.cache[cache_key] = (reranked, now)

        return reranked
```

## Error Handling and Fallbacks

### Robust API Integration
```python
import backoff
from typing import List, Dict, Any

class VoyageAPIClient:
    def __init__(self, api_key: str, max_retries: int = 3):
        self.client = voyageai.Client(api_key=api_key)
        self.max_retries = max_retries

    @backoff.on_exception(
        backoff.expo,
        (voyageai.RateLimitError, voyageai.ServerError),
        max_tries=3
    )
    def embed_with_retry(self, texts: List[str], model: str = "voyage-context-3"):
        """Embed with automatic retry and backoff."""
        try:
            response = self.client.embed(
                texts=texts,
                model=model,
                input_type="document",
                truncation=True
            )
            return response.embeddings

        except voyageai.InvalidRequestError as e:
            logger.error(f"Invalid request: {e}")
            # Return zero vectors as fallback
            return [[0.0] * 1024 for _ in texts]

        except Exception as e:
            logger.error(f"Unexpected embedding error: {e}")
            raise

    def rerank_with_fallback(self, query: str, documents: List[str],
                           instruction: str = None):
        """Rerank with comprehensive fallback strategy."""

        # Try primary model
        try:
            return self.client.rerank(
                query=query,
                documents=documents,
                model="rerank-2.5",
                instruction=instruction
            ).results

        except voyageai.RateLimitError:
            logger.warning("Rate limited, trying lite model")
            time.sleep(1)

            # Fallback to lite model
            try:
                return self.client.rerank(
                    query=query,
                    documents=documents,
                    model="rerank-2.5-lite",
                    instruction=instruction
                ).results

            except Exception as e:
                logger.error(f"Lite model also failed: {e}")
                # Return original order with decreasing scores
                return [
                    {"index": i, "relevance_score": 1.0 - (i * 0.1)}
                    for i in range(len(documents))
                ]

        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            # Final fallback: return original order
            return [
                {"index": i, "relevance_score": 0.5}
                for i in range(len(documents))
            ]
```

### Circuit Breaker Pattern
```python
from enum import Enum
import threading

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class VoyageCircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        self._lock = threading.Lock()

    def can_execute(self):
        """Check if API call should be attempted."""
        with self._lock:
            if self.state == CircuitState.CLOSED:
                return True

            if self.state == CircuitState.OPEN:
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    return True
                return False

            # HALF_OPEN state
            return True

    def record_success(self):
        """Record successful API call."""
        with self._lock:
            self.failure_count = 0
            self.state = CircuitState.CLOSED

    def record_failure(self):
        """Record failed API call."""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
```

## Monitoring and Observability

### API Usage Tracking
```python
class VoyageMetrics:
    def __init__(self):
        self.embedding_calls = 0
        self.embedding_tokens = 0
        self.rerank_calls = 0
        self.rerank_documents = 0
        self.errors = defaultdict(int)
        self.latencies = []

    def record_embedding(self, num_texts, total_tokens, latency_ms):
        """Record embedding API usage."""
        self.embedding_calls += 1
        self.embedding_tokens += total_tokens
        self.latencies.append(latency_ms)

    def record_reranking(self, num_documents, latency_ms):
        """Record reranking API usage."""
        self.rerank_calls += 1
        self.rerank_documents += num_documents
        self.latencies.append(latency_ms)

    def record_error(self, error_type):
        """Record API error."""
        self.errors[error_type] += 1

    def get_summary(self):
        """Get usage summary."""
        return {
            "embedding_calls": self.embedding_calls,
            "embedding_tokens": self.embedding_tokens,
            "rerank_calls": self.rerank_calls,
            "rerank_documents": self.rerank_documents,
            "avg_latency_ms": sum(self.latencies) / len(self.latencies) if self.latencies else 0,
            "p95_latency_ms": sorted(self.latencies)[int(0.95 * len(self.latencies))] if self.latencies else 0,
            "error_counts": dict(self.errors)
        }
```

### Cost Monitoring
```python
VOYAGE_PRICING = {
    "voyage-context-3": {
        "price_per_1k_tokens": 0.00012,  # $0.00012 per 1K tokens
        "max_tokens_per_request": 32000
    },
    "voyage-code-3": {
        "price_per_1k_tokens": 0.00012,
        "max_tokens_per_request": 16000
    },
    "rerank-2.5": {
        "price_per_1k_tokens": 0.00050,  # $0.0005 per 1K tokens
        "max_tokens_per_request": 32000
    },
    "rerank-2.5-lite": {
        "price_per_1k_tokens": 0.00025,  # $0.00025 per 1K tokens
        "max_tokens_per_request": 32000
    }
}

def estimate_cost(model, num_tokens):
    """Estimate API cost for usage."""
    pricing = VOYAGE_PRICING.get(model, {})
    price_per_1k = pricing.get("price_per_1k_tokens", 0)
    return (num_tokens / 1000) * price_per_1k
```

## Related Documentation

- **[RAG System Overview](../../94-architecture/rag/rag-system-overview.md)** - Complete system architecture
- **[Hybrid Retrieval Design](../../94-architecture/rag/hybrid-retrieval-design.md)** - Pipeline implementation
- **[Milvus Configuration](./milvus-configuration-reference.md)** - Vector database setup
- **[Setup Guide](../../02-how-to/rag/setup-rag-pipeline.md)** - Implementation instructions

---

**Status**: Reference Complete
**Last Updated**: 2025-09-23
**Version**: 1.0