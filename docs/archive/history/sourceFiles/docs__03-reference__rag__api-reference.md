# RAG API Reference

## Overview

This document provides comprehensive API reference for the Dopemux RAG system components, including the main retrieval interfaces, memory integration APIs, and utility functions.

## Core RAG APIs

### HybridRetriever

#### `search(query, role, task, workspace_id)`

Execute hybrid search with role-based configuration.

**Parameters:**
- `query` (str): User query text
- `role` (str): User role (Developer, Architect, SRE, PM)
- `task` (str): Current task (CodeImplementation, SystemDesign, etc.)
- `workspace_id` (str, optional): Project workspace identifier (default: "default")

**Returns:**
- `List[RetrievalResult]`: Ranked list of relevant results

**Example:**
```python
retriever = HybridRetriever(
    voyage_api_key="your_key",
    policy_config_path="config/rag/role-policies.json"
)

results = retriever.search(
    query="How does authentication work?",
    role="Developer",
    task="CodeImplementation",
    workspace_id="auth_service"
)
```

#### `get_policy(role, task)`

Retrieve role-specific retrieval policy.

**Parameters:**
- `role` (str): User role
- `task` (str): Current task

**Returns:**
- `Dict[str, Any]`: Policy configuration object

**Example:**
```python
policy = retriever.get_policy("Developer", "Debugging")
print(policy["source_weights"])  # {"ProjectCode": 0.7, "ProjectDocs": 0.3}
```

### MemoryAwareRetriever

#### `search_with_memory(query, role, task, session_id, workspace_id)`

Execute search with full memory integration and logging.

**Parameters:**
- `query` (str): User query text
- `role` (str): User role
- `task` (str): Current task
- `session_id` (str, optional): Chat session identifier (default: "default")
- `workspace_id` (str, optional): Project workspace identifier (default: "default")

**Returns:**
- `Tuple[List[RetrievalResult], str]`: (results, query_id)

**Example:**
```python
retriever = MemoryAwareRetriever(
    voyage_api_key="your_key",
    policy_config_path="config/rag/role-policies.json",
    conport_url="http://localhost:8080"
)

results, query_id = retriever.search_with_memory(
    query="Show me error handling patterns",
    role="Developer",
    task="Debugging",
    session_id="dev_session_123",
    workspace_id="payment_service"
)
```

#### `log_answer_with_memory(query_id, answer_text, used_results, workspace_id, confidence_score)`

Log generated answer with memory integration.

**Parameters:**
- `query_id` (str): Query identifier from search
- `answer_text` (str): Generated answer content
- `used_results` (List[RetrievalResult]): Results used in answer generation
- `workspace_id` (str): Project workspace identifier
- `confidence_score` (float, optional): Answer confidence (0.0-1.0, default: 0.8)

**Returns:**
- `str`: Answer identifier

#### `promote_decision_to_memory(decision_text, related_query_id, workspace_id, tags)`

Promote conversation insights to persistent memory.

**Parameters:**
- `decision_text` (str): Decision or insight description
- `related_query_id` (str): Related query identifier
- `workspace_id` (str): Project workspace identifier
- `tags` (List[str], optional): Categorization tags

**Returns:**
- `str`: Decision identifier

## Data Models

### RetrievalResult

```python
@dataclass
class RetrievalResult:
    id: str                    # Unique result identifier
    text: str                  # Content text
    title: str                 # Result title/name
    source: str                # Source file/document path
    score: float               # Final relevance score
    dense_score: float         # Vector similarity score
    sparse_score: float        # BM25 relevance score
    rerank_score: Optional[float]  # Reranker score (if applied)
```

### PolicyConfiguration

```python
@dataclass
class PolicyConfiguration:
    source_weights: Dict[str, float]  # ProjectCode/ProjectDocs weights
    rerank_instruction: str           # Natural language reranker guidance
    filters: Dict[str, Any]           # Content filtering rules
    fusion_weights: Dict[str, float]  # Dense/sparse fusion weights
    context_limits: Dict[str, int]    # Candidate and result limits
    must_include: Dict[str, bool]     # Required content flags
```

## Ingestion APIs

### IngestionPipeline

#### `__init__(voyage_api_key, milvus_host, milvus_port)`

Initialize ingestion pipeline with external service connections.

**Parameters:**
- `voyage_api_key` (str): Voyage AI API key
- `milvus_host` (str, optional): Milvus server host (default: "localhost")
- `milvus_port` (int, optional): Milvus server port (default: 19530)

#### `setup_collections()`

Create and configure Milvus collections for documents and code.

**Returns:**
- `Tuple[Collection, Collection]`: (docs_collection, code_collection)

**Example:**
```python
pipeline = IngestionPipeline(voyage_api_key="your_key")
docs_collection, code_collection = pipeline.setup_collections()
```

#### `ingest_document(file_path, workspace_id)`

Ingest a single document into the system.

**Parameters:**
- `file_path` (str): Absolute path to document file
- `workspace_id` (str, optional): Project workspace identifier (default: "default")

**Returns:**
- `List[DocumentChunk]`: List of created document chunks

**Example:**
```python
chunks = pipeline.ingest_document(
    file_path="/path/to/api_documentation.md",
    workspace_id="payment_service"
)
print(f"Created {len(chunks)} chunks")
```

#### `chunk_document(content, title, source, max_tokens)`

Split document content into semantic chunks.

**Parameters:**
- `content` (str): Document text content
- `title` (str): Document title
- `source` (str): Source identifier
- `max_tokens` (int, optional): Maximum tokens per chunk (default: 400)

**Returns:**
- `List[Dict]`: List of chunk data dictionaries

#### `generate_prelude(content, title, content_type)`

Generate contextual prelude for content chunk.

**Parameters:**
- `content` (str): Chunk content
- `title` (str): Content title
- `content_type` (str): "document" or "code"

**Returns:**
- `str`: Generated prelude text

## Memory APIs

### ConPortMemoryLogger

#### `__init__(conport_url, max_workers, buffer_size)`

Initialize memory logger with ConPort integration.

**Parameters:**
- `conport_url` (str, optional): ConPort service URL (default: "http://localhost:8080")
- `max_workers` (int, optional): Thread pool size (default: 4)
- `buffer_size` (int, optional): Operation buffer size (default: 1000)

#### `log_query_async(query, role, task, session_id, workspace_id)`

Asynchronously log user query to memory graph.

**Parameters:**
- `query` (str): Query text
- `role` (str): User role
- `task` (str): Current task
- `session_id` (str): Session identifier
- `workspace_id` (str): Project workspace identifier

**Returns:**
- `str`: Query identifier (returned immediately)

#### `log_retrieval_batch(query_id, results, stage, workspace_id)`

Log batch of retrieval results.

**Parameters:**
- `query_id` (str): Query identifier
- `results` (List[RetrievalResult]): Retrieved results
- `stage` (str): Retrieval stage ("initial" or "rerank")
- `workspace_id` (str): Project workspace identifier

**Returns:**
- `None` (asynchronous operation)

#### `query_memory_graph(query_text, workspace_id, max_hops)`

Query the memory graph for related content.

**Parameters:**
- `query_text` (str): Query to search for
- `workspace_id` (str): Project workspace identifier
- `max_hops` (int, optional): Maximum graph traversal hops (default: 2)

**Returns:**
- `List[Dict[str, Any]]`: Related memory nodes and edges

**Example:**
```python
memory_logger = ConPortMemoryLogger()

# Query for related content
related = memory_logger.query_memory_graph(
    query_text="authentication tokens",
    workspace_id="auth_service",
    max_hops=2
)

for item in related:
    print(f"Found: {item['type']} - {item['data']['title']}")
```

#### `get_buffer_status()`

Get status of buffered operations.

**Returns:**
- `Dict[str, Any]`: Buffer status information

```python
{
    "buffered_count": 15,
    "buffer_capacity": 1000,
    "oldest_buffered": 1640995200,
    "buffer_types": {
        "log_query": 8,
        "log_retrieval_batch": 5,
        "log_context_usage": 2
    }
}
```

## Configuration APIs

### PolicyManager

#### `__init__(config_path)`

Initialize policy manager with configuration file.

**Parameters:**
- `config_path` (str, optional): Path to policy JSON file (default: "config/rag/role-policies.json")

#### `load_policies()`

Load policies from configuration file.

**Raises:**
- `FileNotFoundError`: If policy file doesn't exist
- `ValueError`: If policy validation fails
- `json.JSONDecodeError`: If JSON is malformed

#### `get_policy(role, task)`

Get resolved policy for role and task combination.

**Parameters:**
- `role` (str): User role
- `task` (str): Current task

**Returns:**
- `Dict[str, Any]`: Resolved policy configuration

#### `reload_policies()`

Hot-reload policies from configuration file.

## Health Check APIs

### RAGHealthMonitor

#### `__init__(config)`

Initialize health monitor with system configuration.

**Parameters:**
- `config` (Dict[str, Any]): Configuration dictionary

```python
config = {
    "voyage_api_key": "your_key",
    "milvus_host": "localhost",
    "milvus_port": 19530,
    "conport_url": "http://localhost:8080"
}

monitor = RAGHealthMonitor(config)
```

#### `check_overall_system()`

Check health of all system components.

**Returns:**
- `Dict[str, Any]`: Comprehensive health status

```python
{
    "overall_status": "healthy",
    "services": {
        "milvus": {
            "status": "healthy",
            "entity_counts": {"ProjectDocs": 5420, "ProjectCode": 2180}
        },
        "conport": {
            "status": "healthy",
            "memory_stats": {"total_nodes": 12500, "total_edges": 45000}
        },
        "voyage": {
            "status": "healthy",
            "embedding_latency_ms": 120,
            "rerank_latency_ms": 850
        }
    },
    "timestamp": 1640995200
}
```

#### `check_milvus_health()`

Check Milvus database health specifically.

**Returns:**
- `Dict[str, Any]`: Milvus health status

#### `check_conport_health()`

Check ConPort memory system health.

**Returns:**
- `Dict[str, Any]`: ConPort health status

#### `check_voyage_health()`

Check Voyage AI service health.

**Returns:**
- `Dict[str, Any]`: Voyage AI health status

## Performance Monitoring APIs

### PerformanceTracker

#### `track_latency(operation_name)`

Decorator for tracking operation latency.

**Parameters:**
- `operation_name` (str): Name of operation to track

**Example:**
```python
perf_tracker = PerformanceTracker()

@perf_tracker.track_latency("search_operation")
def search_documents(query):
    # Search implementation
    return results
```

#### `record_metric(operation, latency_ms, success)`

Manually record performance metric.

**Parameters:**
- `operation` (str): Operation name
- `latency_ms` (float): Operation latency in milliseconds
- `success` (bool): Whether operation succeeded

#### `get_stats(operation)`

Get performance statistics for an operation.

**Parameters:**
- `operation` (str): Operation name

**Returns:**
- `Dict[str, Any]`: Performance statistics

```python
{
    "count": 1250,
    "success_rate": 0.98,
    "latency_p50": 145.2,
    "latency_p95": 892.1,
    "latency_mean": 203.4
}
```

## Error Handling

### Common Exceptions

#### `RAGConfigurationError`

Raised when configuration is invalid or missing.

```python
try:
    retriever = HybridRetriever(
        voyage_api_key="invalid_key",
        policy_config_path="missing_file.json"
    )
except RAGConfigurationError as e:
    print(f"Configuration error: {e}")
```

#### `RetrievalError`

Raised when retrieval operation fails.

```python
try:
    results = retriever.search(query="test", role="Developer", task="CodeImplementation")
except RetrievalError as e:
    print(f"Retrieval failed: {e}")
    # Handle gracefully
```

#### `MemoryError`

Raised when memory operations fail critically.

```python
try:
    query_id = memory_logger.log_query_async(...)
except MemoryError as e:
    print(f"Memory logging failed: {e}")
    # Continue without memory features
```

## Usage Examples

### Complete RAG Workflow

```python
import os
from src.rag.memory_retrieval import MemoryAwareRetriever

# Initialize system
retriever = MemoryAwareRetriever(
    voyage_api_key=os.getenv("VOYAGE_API_KEY"),
    policy_config_path="config/rag/role-policies.json",
    conport_url="http://localhost:8080"
)

# Execute search with memory
results, query_id = retriever.search_with_memory(
    query="How should I handle authentication errors?",
    role="Developer",
    task="Debugging",
    session_id="debug_session_456",
    workspace_id="user_service"
)

# Process results
print(f"Found {len(results)} relevant results:")
for i, result in enumerate(results):
    print(f"{i+1}. {result.title} (score: {result.score:.3f})")
    print(f"   Source: {result.source}")
    print(f"   Preview: {result.text[:100]}...")

# Log answer
answer = "To handle authentication errors, use try-catch blocks..."
answer_id = retriever.log_answer_with_memory(
    query_id=query_id,
    answer_text=answer,
    used_results=results[:3],  # Top 3 results used
    workspace_id="user_service",
    confidence_score=0.9
)

print(f"Answer logged with ID: {answer_id}")
```

### Health Monitoring

```python
from src.rag.health import RAGHealthMonitor

# Monitor system health
config = {
    "voyage_api_key": os.getenv("VOYAGE_API_KEY"),
    "milvus_host": "localhost",
    "milvus_port": 19530,
    "conport_url": "http://localhost:8080"
}

monitor = RAGHealthMonitor(config)
health = monitor.check_overall_system()

if health["overall_status"] == "healthy":
    print("✅ All systems operational")
else:
    print("⚠️ System issues detected:")
    for service, status in health["services"].items():
        if status["status"] != "healthy":
            print(f"  - {service}: {status['status']}")
```

### Performance Tracking

```python
from src.rag.performance import PerformanceTracker

# Track performance
perf_tracker = PerformanceTracker()

# Get operation statistics
search_stats = perf_tracker.get_stats("hybrid_search")
rerank_stats = perf_tracker.get_stats("rerank_candidates")

print(f"Search P95: {search_stats['latency_p95']:.1f}ms")
print(f"Rerank P95: {rerank_stats['latency_p95']:.1f}ms")
print(f"Success rate: {search_stats['success_rate']:.2%}")
```

## Rate Limits and Quotas

### Voyage AI Limits
- **Embedding API**: 1000 requests/minute
- **Reranking API**: 100 requests/minute
- **Token limits**: 32K tokens per request

### System Defaults
- **Max concurrent queries**: 20
- **Query timeout**: 30 seconds
- **Memory buffer size**: 1000 operations
- **Cache TTL**: 1 hour

## Related Documentation

- **[RAG System Overview](../../94-architecture/rag/rag-system-overview.md)** - Complete system architecture
- **[Setup Guide](../../02-how-to/rag/setup-rag-pipeline.md)** - Implementation instructions
- **[Role Policy Schema](./role-policy-schema.md)** - Policy configuration format
- **[Operations Runbook](../../92-runbooks/rag/rag-operations-runbook.md)** - Production operations

---

**Status**: API Reference Complete
**Last Updated**: 2025-09-23
**Version**: 1.0