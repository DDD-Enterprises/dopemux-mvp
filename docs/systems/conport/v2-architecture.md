---
id: v2-architecture
title: V2 Architecture
type: system-doc
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
---
# ConPort v2 Architecture Documentation

## 🚀 Overview

ConPort v2 represents a complete architectural transformation from the original SQLite-based system to a production-grade, async-first platform optimized for ADHD developers. The v2 architecture addresses critical scalability bottlenecks while enhancing the user experience with progressive operations and intelligent caching.

## 🏗️ System Architecture

### **High-Level Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│                    Enhanced MCP Handlers                    │
│  ┌─────────────────┐ ┌─────────────────┐ ┌──────────────┐  │
│  │ Context Ops     │ │ Decision Ops    │ │ Search Ops   │  │
│  │ - Product       │ │ - Log/Query     │ │ - Semantic   │  │
│  │ - Active        │ │ - Batch Ops     │ │ - Hybrid     │  │
│  │ - History       │ │ - Vector Sync   │ │ - Cached     │  │
│  └─────────────────┘ └─────────────────┘ └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
           │                    │                    │
           ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ AsyncDatabase   │  │ QdrantVectorStore│  │ RedisCache      │
│                 │  │                 │  │                 │
│ PostgreSQL      │  │ Vector Search   │  │ Intelligent     │
│ - Multi-writer  │  │ - 384-dim       │  │ - TTL Strategy  │
│ - Connection    │  │ - HNSW Index    │  │ - Prefetching   │
│   Pooling       │  │ - Cosine Sim    │  │ - Access Track  │
│ - Transactions  │  │ - Workspace     │  │ - Batch Ops     │
│ - History Diff  │  │   Isolation     │  │ - Performance   │
└─────────────────┘  └─────────────────┘  └─────────────────┘
           │                    │                    │
           ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                  Async Embedding Pipeline                   │
│  ┌─────────────────┐ ┌─────────────────┐ ┌──────────────┐  │
│  │ Priority Queue  │ │ Worker Pool     │ │ Text Cache   │  │
│  │ - Urgent First  │ │ - 2 Workers     │ │ - LRU 10K    │  │
│  │ - Batch Groups  │ │ - GPU Optimize  │ │ - Dedup Hash │  │
│  │ - Progress      │ │ - Model Warm    │ │ - Fast Lookup│  │
│  └─────────────────┘ └─────────────────┘ └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 🗄️ Data Layer Details

### **PostgreSQL Schema Enhancement**

#### **Multi-Workspace Design**

```sql
-- Workspace isolation and management
CREATE TABLE workspaces (
    id SERIAL PRIMARY KEY,
    workspace_id TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_active TIMESTAMPTZ DEFAULT NOW(),
    settings JSONB DEFAULT '{}'::jsonb
);

-- Enhanced contexts with versioning
CREATE TABLE product_contexts (
    workspace_id TEXT NOT NULL REFERENCES workspaces(workspace_id) ON DELETE CASCADE,
    content JSONB NOT NULL DEFAULT '{}'::jsonb,
    version INTEGER DEFAULT 1,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (workspace_id)
);
```

#### **Advanced Indexing Strategy**

```sql
-- Performance-optimized indexes
CREATE INDEX idx_decisions_workspace_timestamp ON decisions(workspace_id, timestamp DESC);
CREATE INDEX idx_decisions_tags ON decisions USING gin(tags);
CREATE INDEX idx_progress_workspace_status ON progress_entries(workspace_id, status);
CREATE INDEX idx_custom_data_value ON custom_data USING gin(value);

-- Full-text search with PostgreSQL
CREATE INDEX idx_decisions_fts ON decisions
USING gin(to_tsvector('english', summary || ' ' || COALESCE(rationale, '')));
```

#### **Efficient History Storage**

```sql
-- Context history with diff compression
CREATE TABLE context_history (
    id SERIAL PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    context_type TEXT NOT NULL,  -- 'product' or 'active'
    version INTEGER NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    content JSONB NOT NULL,      -- Full content snapshot
    change_source TEXT,
    diff JSONB                   -- Only store changes for efficiency
);
```

### **Qdrant Vector Configuration**

#### **Collection Setup**

```python
collection_config = {
    "vectors_config": VectorParams(
        size=384,  # all-MiniLM-L6-v2 dimension
        distance=Distance.COSINE
    ),
    "optimizers_config": {
        "default_segment_number": 2,
        "max_segment_size": 50000,
        "memmap_threshold": 50000,
        "indexing_threshold": 10000,
        "flush_interval_sec": 30
    },
    "hnsw_config": {
        "m": 32,           # Expert-validated from embeddings system
        "ef_construct": 128,
        "full_scan_threshold": 10000,
        "max_indexing_threads": 2
    }
}
```

#### **Vector Point Structure**

```python
point_structure = {
    "id": "{workspace_id}_{item_type}_{item_id}",
    "vector": [384 float values],
    "payload": {
        "workspace_id": str,
        "item_type": "decision|progress_entry|system_pattern|custom_data",
        "item_id": str,
        "conport_item_id": str,  # Link back to PostgreSQL
        "content_preview": str,   # First 200 chars for quick view
        "tags": str,             # Comma-separated for filtering
        "timestamp_created": str,
        "complexity_score": float,
        "context_relevance": float
    }
}
```

### **Redis Cache Architecture**

#### **Cache Key Patterns**

```
conport:v2:{workspace_id}:context:product:current
conport:v2:{workspace_id}:context:active:current
conport:v2:{workspace_id}:decisions:recent:10
conport:v2:{workspace_id}:search:semantic:{query_hash}
conport:v2:{workspace_id}:stats:performance
```

#### **Intelligent TTL Strategy**

```python
ttl_strategy = {
    "contexts": 1800,        # 30 min - change frequently
    "decisions": 7200,       # 2 hours - stable references
    "search_results": 1800,  # 30 min - query dependent
    "system_patterns": 3600, # 1 hour - moderate stability
    "performance_stats": 300 # 5 min - monitoring data
}
```

#### **Access Pattern Tracking**

```python
# Intelligent prefetching based on usage
access_patterns = {
    "key": [timestamp1, timestamp2, ...],  # Recent access times
    "frequency": calculated_frequency,
    "prefetch_priority": 0.0 to 1.0
}

# Auto-prefetch when frequency > threshold
if len(access_patterns["key"]) > 5:  # 5+ accesses in 24h
    queue_prefetch(related_keys)
```

## ⚡ Embedding Pipeline Architecture

### **Async Processing Flow**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Text Input      │───▶│ Priority Queue  │───▶│ Worker Pool     │
│ - Decision text │    │ - Urgent first  │    │ - 2 async       │
│ - Progress desc │    │ - Batch group   │    │ - Model shared  │
│ - Pattern info  │    │ - Queue limit   │    │ - GPU optimize  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Vector Storage  │◀───│ Result Cache    │◀───│ Batch Process   │
│ - Qdrant upsert │    │ - Text hash     │    │ - 32 batch size │
│ - Metadata      │    │ - LRU eviction  │    │ - Progress      │
│ - Point ID      │    │ - 10K entries   │    │ - Error handle  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### **Request Processing Logic**

```python
class EmbeddingRequest:
    id: str                    # Unique request identifier
    text: str                  # Text to embed
    workspace_id: str          # Workspace context
    item_type: str            # decision, progress_entry, etc.
    item_id: str              # Database ID for linking
    metadata: Dict[str, Any]  # Additional context
    priority: int             # 0=urgent, 1=normal, 2=background
    callback: Optional[Callable] # Completion notification

# Processing workflow:
1. Text → Hash → Cache Check → Queue (if miss) → Worker → Model → Vector → Cache + Store
2. Parallel: Metadata Enhancement → Context Analysis → Related Item Discovery
3. Result: Vector + Enhanced Metadata → Qdrant Point → PostgreSQL Reference
```

### **Batch Optimization Strategy**

```python
batch_processing = {
    "collection_strategy": "time_and_size",  # Collect until batch_size OR timeout
    "batch_size": 32,                       # Optimal for sentence-transformers
    "timeout": 2.0,                         # Max wait time in seconds
    "priority_ordering": True,              # Urgent requests first
    "deduplication": True,                  # Skip duplicate texts
    "progress_tracking": True               # Visual feedback for ADHD users
}

# Worker coordination
worker_pool = {
    "worker_count": 2,                      # Optimal for single GPU
    "load_balancing": "round_robin",
    "failure_handling": "retry_with_backoff",
    "model_sharing": True,                  # Single model instance
    "warm_up_strategy": "on_initialization"
}
```

## 🔍 Query System Architecture

### **Semantic Search Pipeline**

```python
async def semantic_search_flow(query_text: str, workspace_id: str):
    # 1. Query Processing
    query_hash = hash_query(query_text, filters)
    cached_results = await cache.get_search_results(workspace_id, query_hash)

    if cached_results:
        return cached_results  # ~1ms response time

    # 2. Vector Generation
    query_vector = await embedding_pipeline.embed_text_sync(
        text=query_text,
        workspace_id=workspace_id,
        item_type="query",
        item_id="search"
    )

    # 3. Vector Search
    vector_results = await vector_store.search(
        workspace_id=workspace_id,
        query_vector=query_vector,
        limit=limit * 2,  # Get extra for filtering
        filters=workspace_filter
    )

    # 4. Result Enrichment
    enriched_results = await _enrich_with_database_data(vector_results)

    # 5. ADHD Optimization
    progressive_results = await adhd_navigator.apply_progressive_disclosure(
        enriched_results, max_initial_items=10
    )

    # 6. Cache Storage
    await cache.cache_search_results(workspace_id, query_hash, progressive_results)

    return progressive_results
```

### **Hybrid Query Capabilities**

**Vector + Structured Combination:**

```python
# Example: Find decisions related to authentication with recent activity
hybrid_query = {
    "semantic_component": {
        "query": "JWT authentication security implementation",
        "vector_weight": 0.7
    },
    "structured_component": {
        "filters": {
            "tags": ["authentication", "security"],
            "date_range": "last_30_days",
            "item_types": ["decision", "system_pattern"]
        },
        "structured_weight": 0.3
    },
    "fusion_method": "reciprocal_rank_fusion"
}
```

### **ADHD-Optimized Query Features**

**Progressive Result Loading:**

```python
# Initial quick results for immediate feedback
initial_results = await quick_semantic_search(query, limit=5)
ui.show_results(initial_results, "🔍 Initial results...")

# Background: Full search with enrichment
full_results = await comprehensive_search(query, limit=20)
ui.update_results(full_results, "✅ Complete results loaded")

# Context-aware expansion
if user_requests_more:
    expanded = await expand_search_context(query, current_results)
    ui.show_expanded(expanded, "📚 Extended context loaded")
```

## 📊 Performance Characteristics

### **Throughput Metrics**

- **Database Operations**: 1000+ ops/sec with connection pooling
- **Vector Search**: <100ms for workspace-scoped queries
- **Cache Hit Rate**: 80%+ for frequently accessed contexts
- **Embedding Generation**: 50 texts/sec with batching

### **Latency Targets**

- **Context Retrieval**: <50ms (cached), <200ms (database)
- **Decision Logging**: <100ms (async embedding)
- **Semantic Search**: <500ms (vector + enrichment)
- **Batch Operations**: Background with progress tracking

### **Scalability Factors**

- **Workspaces**: 1000+ concurrent workspaces supported
- **Data Volume**: 10M+ decisions/entries per workspace
- **Vector Storage**: 1M+ embeddings with efficient indexing
- **Cache Memory**: 1GB+ Redis with intelligent eviction

## 🧠 ADHD Optimization Features

### **Progressive Operations**

- **Batch Progress Tracking**: Visual feedback during long operations
- **Intelligent Chunking**: Break large operations into manageable pieces
- **Gentle Error Handling**: Friendly error messages with recovery suggestions
- **Context Preservation**: Maintain state across interruptions

### **Cognitive Load Management**

- **Result Limiting**: Smart defaults to prevent overwhelm
- **Complexity Indicators**: Visual cues for decision/pattern complexity
- **Priority Highlighting**: Important items shown first
- **Contextual Guidance**: Helpful suggestions without being overwhelming

### **Focus-Aware Features**

- **Context-Sensitive Caching**: Prefetch based on current work area
- **Related Item Discovery**: Surface relevant connections automatically
- **Session Continuity**: Restore context across development sessions
- **Attention Preservation**: Minimize cognitive interruptions

## 🔗 Integration Points

### **MCP Tool Interface**

```python
# Enhanced MCP tools with v2 capabilities
tools_v2 = {
    "get_product_context_v2": "Enhanced with caching and metadata",
    "log_decision_v2": "Async embedding generation",
    "semantic_search_conport_v2": "Qdrant-powered semantic search",
    "batch_operations_v2": "Parallel processing with progress",
    "get_system_health_v2": "Comprehensive component monitoring"
}
```

### **Backward Compatibility**

- **Existing MCP tools**: Maintained for gradual migration
- **Data migration path**: Automated SQLite → PostgreSQL conversion
- **Feature flags**: Toggle between v1 and v2 implementations
- **Graceful degradation**: Fallback to v1 if v2 components unavailable

## 🚨 Production Considerations

### **Deployment Requirements**

- **PostgreSQL 14+**: For JSONB and async support
- **Qdrant 1.7+**: For vector search capabilities
- **Redis 6+**: For advanced data structures
- **Python 3.10+**: For asyncio and typing features

### **Resource Allocation**

```yaml
# Recommended production resources
postgresql:
  cpu: 2 cores
  memory: 4GB
  storage: 50GB SSD
  connections: 100

qdrant:
  cpu: 2 cores
  memory: 8GB    # Vector storage in memory
  storage: 20GB SSD

redis:
  cpu: 1 core
  memory: 2GB
  persistence: rdb_snapshot

conport_service:
  cpu: 1 core
  memory: 1GB
  workers: 2
```

### **Monitoring & Health Checks**

```python
# Comprehensive health monitoring
health_endpoints = {
    "/health/database": "PostgreSQL connection and query performance",
    "/health/vector": "Qdrant collection stats and search latency",
    "/health/cache": "Redis connectivity and hit rates",
    "/health/embedding": "Pipeline queue and processing stats",
    "/health/system": "Overall system status and recommendations"
}

# ADHD-friendly status indicators
status_levels = {
    "🚀 Excellent": "All systems optimal, peak performance",
    "✅ Good": "Minor issues, fully functional",
    "⚠️ Degraded": "Some components slow, still usable",
    "🔴 Critical": "Major issues, reduced functionality"
}
```

## 🔄 Migration Strategy

### **SQLite to PostgreSQL Migration**

```python
# Automated migration process
migration_steps = [
    "1. Export SQLite data to JSON",
    "2. Create PostgreSQL schema",
    "3. Transform and load data with workspace mapping",
    "4. Generate embeddings for existing content",
    "5. Populate Qdrant with vectors",
    "6. Warm Redis cache with frequent data",
    "7. Validate data integrity",
    "8. Switch MCP handlers to v2",
    "9. Monitor performance and rollback capability"
]
```

### **Zero-Downtime Migration**

- **Dual-write period**: Write to both v1 and v2 during transition
- **Feature flag control**: Gradual user migration
- **Rollback capability**: Instant fallback to v1 if issues
- **Data validation**: Continuous integrity checking

## 📈 Performance Monitoring

### **Key Metrics Dashboard**

```python
performance_metrics = {
    "database": {
        "connection_pool_usage": "percentage",
        "query_latency_p95": "milliseconds",
        "transaction_throughput": "ops/second",
        "active_connections": "count"
    },
    "vector_store": {
        "search_latency_p95": "milliseconds",
        "indexing_throughput": "vectors/second",
        "memory_usage": "GB",
        "collection_size": "count"
    },
    "cache": {
        "hit_rate": "percentage",
        "memory_usage": "MB",
        "operation_latency": "milliseconds",
        "eviction_rate": "keys/minute"
    },
    "embedding_pipeline": {
        "queue_size": "count",
        "processing_rate": "embeddings/second",
        "cache_hit_rate": "percentage",
        "average_batch_size": "count"
    }
}
```

## 🎯 ADHD-Specific Features

### **Progressive Disclosure System**

```python
# Complexity-aware result presentation
result_presentation = {
    "initial_load": {
        "max_items": 10,
        "complexity_filter": 0.7,  # Hide complex items initially
        "prioritization": "importance_score",
        "visual_indicators": True
    },
    "expansion": {
        "batch_size": 5,           # Load 5 more at a time
        "expansion_threshold": 0.8, # User must scroll 80% before more load
        "complexity_graduation": True, # Show slightly more complex items
        "context_preservation": True   # Maintain scroll position
    }
}
```

### **Cognitive Load Management**

```python
# Adaptive complexity scoring
complexity_calculation = {
    "decision_complexity": {
        "text_length": 0.2,        # Longer decisions = more complex
        "tag_count": 0.1,          # More tags = more context needed
        "implementation_detail": 0.3, # Technical details increase complexity
        "age": -0.1                # Recent decisions slightly less complex
    },
    "result_set_complexity": {
        "item_count": 0.4,         # More results = higher cognitive load
        "diversity": 0.3,          # Mixed types = more context switching
        "time_spread": 0.2,        # Results spanning time = more analysis
        "relationship_density": 0.1 # Highly connected = more complex
    }
}
```

### **Context Switching Minimization**

```python
# ADHD-friendly batching strategies
batching_strategies = {
    "temporal_batching": {
        "description": "Group operations by time to reduce interruptions",
        "window_size": "5_seconds",
        "max_batch_size": 50,
        "priority_ordering": True
    },
    "semantic_batching": {
        "description": "Group related operations for coherent context",
        "similarity_threshold": 0.8,
        "max_group_size": 20,
        "context_preservation": True
    },
    "complexity_batching": {
        "description": "Process simple operations first for quick wins",
        "complexity_ordering": "ascending",
        "break_points": [0.3, 0.6, 0.9],  # Natural breakpoints
        "progress_celebration": True       # Acknowledge completions
    }
}
```

## 🔧 Configuration Examples

### **Production Configuration**

```python
# Complete production setup
production_config = {
    "database": {
        "host": "localhost",
        "port": 5432,
        "user": "conport",
        "database": "conport",
        "min_size": 5,
        "max_size": 20,
        "max_queries": 50000
    },
    "vector_store": {
        "host": "localhost",
        "port": 6333,
        "collection_name": "conport_knowledge",
        "vector_size": 384,
        "distance": "Cosine"
    },
    "cache": {
        "redis_url": "redis://localhost:6379",
        "default_ttl": 3600,
        "context_ttl": 1800,
        "decision_ttl": 7200
    },
    "embedding_pipeline": {
        "model_name": "all-MiniLM-L6-v2",
        "batch_size": 32,
        "worker_count": 2,
        "cache_embeddings": True,
        "device": "auto"
    }
}
```

### **ADHD Developer Configuration**

```python
# ADHD-optimized settings
adhd_config = {
    "progressive_disclosure": {
        "max_initial_results": 8,    # Fewer items to prevent overwhelm
        "expansion_batch_size": 3,   # Small increments
        "complexity_threshold": 0.6, # Hide complex items initially
        "visual_indicators": True    # Show complexity visually
    },
    "cognitive_load": {
        "break_suggestions": True,   # Suggest breaks during heavy operations
        "complexity_warnings": True, # Warn about complex decisions/patterns
        "context_preservation": True,# Maintain context across interruptions
        "gentle_guidance": True      # Encouraging, not overwhelming feedback
    },
    "performance": {
        "cache_aggressively": True,  # Prioritize speed over freshness
        "prefetch_related": True,    # Load related items proactively
        "batch_operations": True,    # Group operations to reduce interruptions
        "progress_feedback": True    # Always show progress for operations >2s
    }
}
```

This architecture provides a solid foundation for ADHD-optimized development tooling with enterprise-grade performance and scalability.
