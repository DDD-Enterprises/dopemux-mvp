# Milvus Configuration Reference

## Overview

This document provides detailed configuration specifications for the Milvus vector database components in the Dopemux RAG system. It covers collection schemas, index parameters, search configurations, and operational settings for both DocRAG and CodeRAG collections.

## Deployment Configuration

### Development Setup (Milvus Lite)
```yaml
# milvus-lite.yaml
version: "3.8"
services:
  milvus-lite:
    image: milvusdb/milvus:v2.5.0-lite
    ports:
      - "19530:19530"
    volumes:
      - ./data/milvus:/var/lib/milvus
    environment:
      MILVUS_CONFIG_PATH: /milvus/configs/milvus.yaml
```

### Production Setup (Milvus Cluster)
```yaml
# milvus-cluster.yaml
version: "3.8"
services:
  etcd:
    image: quay.io/coreos/etcd:v3.5.5
    environment:
      - ETCD_AUTO_COMPACTION_MODE=revision
      - ETCD_AUTO_COMPACTION_RETENTION=1000
      - ETCD_QUOTA_BACKEND_BYTES=4294967296
      - ETCD_SNAPSHOT_COUNT=50000
    volumes:
      - ${DOCKER_VOLUME_DIRECTORY:-.}/volumes/etcd:/etcd

  minio:
    image: minio/minio:RELEASE.2023-03-20T20-16-18Z
    environment:
      MINIO_ACCESS_KEY: minioadmin
      MINIO_SECRET_KEY: minioadmin
    volumes:
      - ${DOCKER_VOLUME_DIRECTORY:-.}/volumes/minio:/minio_data
    command: minio server /minio_data --console-address ":9001"

  milvus:
    image: milvusdb/milvus:v2.5.0
    command: ["milvus", "run", "standalone"]
    environment:
      ETCD_ENDPOINTS: etcd:2379
      MINIO_ADDRESS: minio:9000
    volumes:
      - ${DOCKER_VOLUME_DIRECTORY:-.}/volumes/milvus:/var/lib/milvus
    ports:
      - "19530:19530"
    depends_on:
      - "etcd"
      - "minio"
```

## Collection Schemas

### ProjectDocs Collection

#### Schema Definition
```python
from pymilvus import CollectionSchema, FieldSchema, DataType

# Field definitions
fields = [
    FieldSchema(
        name="id",
        dtype=DataType.INT64,
        is_primary=True,
        auto_id=False,
        description="Unique chunk identifier"
    ),
    FieldSchema(
        name="doc_id",
        dtype=DataType.VARCHAR,
        max_length=255,
        description="Source document identifier"
    ),
    FieldSchema(
        name="title",
        dtype=DataType.VARCHAR,
        max_length=512,
        description="Document/section title"
    ),
    FieldSchema(
        name="text",
        dtype=DataType.VARCHAR,
        max_length=4096,
        description="Chunk content including prelude",
        enable_analyzer=True,
        analyzer_params={
            "type": "standard",
            "tokenizer": "standard",
            "filter": ["lowercase", "stop"]
        }
    ),
    FieldSchema(
        name="embedding",
        dtype=DataType.FLOAT_VECTOR,
        dim=1024,
        description="Dense vector from voyage-context-3"
    ),
    FieldSchema(
        name="sparse",
        dtype=DataType.SPARSE_FLOAT_VECTOR,
        description="BM25 sparse vector"
    ),
    FieldSchema(
        name="source",
        dtype=DataType.VARCHAR,
        max_length=512,
        description="Source file path or URL"
    ),
    FieldSchema(
        name="chunk_index",
        dtype=DataType.INT32,
        description="Chunk position in source document"
    ),
    FieldSchema(
        name="prelude",
        dtype=DataType.VARCHAR,
        max_length=512,
        description="Contextual summary/prelude"
    ),
    FieldSchema(
        name="last_updated",
        dtype=DataType.INT64,
        description="Unix timestamp of last update"
    ),
    FieldSchema(
        name="workspace_id",
        dtype=DataType.VARCHAR,
        max_length=128,
        description="Project workspace identifier"
    )
]

# Create collection schema
docs_schema = CollectionSchema(
    fields=fields,
    description="Dopemux project documentation chunks",
    enable_dynamic_field=True
)
```

#### Collection Creation
```python
from pymilvus import Collection

# Create collection with partitioning by workspace
docs_collection = Collection(
    name="ProjectDocs",
    schema=docs_schema,
    using='default'
)

# Create partition for workspace isolation
docs_collection.create_partition("workspace_default")
```

### ProjectCode Collection

#### Schema Definition
```python
# Field definitions for code collection
code_fields = [
    FieldSchema(
        name="id",
        dtype=DataType.INT64,
        is_primary=True,
        auto_id=False,
        description="Unique code chunk identifier"
    ),
    FieldSchema(
        name="file_path",
        dtype=DataType.VARCHAR,
        max_length=1024,
        description="Source file path"
    ),
    FieldSchema(
        name="func_sig",
        dtype=DataType.VARCHAR,
        max_length=512,
        description="Function/class signature"
    ),
    FieldSchema(
        name="code",
        dtype=DataType.VARCHAR,
        max_length=8192,
        description="Code content with optional prelude",
        enable_analyzer=True,
        analyzer_params={
            "type": "keyword",  # Code-aware analyzer
            "tokenizer": "code_aware",
            "filter": ["lowercase"]  # Minimal filtering for code
        }
    ),
    FieldSchema(
        name="embedding",
        dtype=DataType.FLOAT_VECTOR,
        dim=1024,
        description="Dense vector from voyage-code-3"
    ),
    FieldSchema(
        name="sparse",
        dtype=DataType.SPARSE_FLOAT_VECTOR,
        description="BM25 sparse vector for code"
    ),
    FieldSchema(
        name="language",
        dtype=DataType.VARCHAR,
        max_length=32,
        description="Programming language"
    ),
    FieldSchema(
        name="start_line",
        dtype=DataType.INT32,
        description="Starting line number in source file"
    ),
    FieldSchema(
        name="end_line",
        dtype=DataType.INT32,
        description="Ending line number in source file"
    ),
    FieldSchema(
        name="complexity_score",
        dtype=DataType.FLOAT,
        description="Cyclomatic complexity estimate"
    ),
    FieldSchema(
        name="last_updated",
        dtype=DataType.INT64,
        description="Unix timestamp of last update"
    ),
    FieldSchema(
        name="workspace_id",
        dtype=DataType.VARCHAR,
        max_length=128,
        description="Project workspace identifier"
    )
]

code_schema = CollectionSchema(
    fields=code_fields,
    description="Dopemux project code chunks",
    enable_dynamic_field=True
)
```

## Index Configuration

### HNSW Vector Index

#### DocRAG Collection Index
```python
# Vector index for documents
docs_vector_index = {
    "index_type": "HNSW",
    "metric_type": "COSINE",
    "params": {
        "M": 16,                    # Number of bi-directional links per node
        "efConstruction": 200,      # Size of candidate set during construction
        "max_degree": 64,          # Maximum degree of node in graph
        "search_list_size": 100     # Size of search list during search
    }
}

# Create index
docs_collection.create_index(
    field_name="embedding",
    index_params=docs_vector_index,
    index_name="docs_vector_idx"
)

# Configure search parameters
docs_search_params = {
    "metric_type": "COSINE",
    "params": {
        "ef": 128,              # Size of search list during query
        "round_decimal": 4      # Precision for similarity scores
    }
}
```

#### CodeRAG Collection Index
```python
# Vector index for code (optimized for larger collection)
code_vector_index = {
    "index_type": "HNSW",
    "metric_type": "COSINE",
    "params": {
        "M": 16,
        "efConstruction": 200,
        "max_degree": 64,
        "search_list_size": 100
    }
}

code_collection.create_index(
    field_name="embedding",
    index_params=code_vector_index,
    index_name="code_vector_idx"
)

code_search_params = {
    "metric_type": "COSINE",
    "params": {
        "ef": 128,
        "round_decimal": 4
    }
}
```

### BM25 Sparse Index

#### Document BM25 Configuration
```python
# BM25 index for documents
docs_bm25_index = {
    "index_type": "SPARSE_INVERTED_INDEX",
    "metric_type": "BM25",
    "params": {
        "bm25_k1": 1.2,        # Term frequency saturation parameter
        "bm25_b": 0.75,        # Length normalization parameter
        "bm25_k3": 8.0         # Query frequency saturation
    }
}

docs_collection.create_index(
    field_name="sparse",
    index_params=docs_bm25_index,
    index_name="docs_bm25_idx"
)
```

#### Code BM25 Configuration
```python
# BM25 index for code (tuned for identifier matching)
code_bm25_index = {
    "index_type": "SPARSE_INVERTED_INDEX",
    "metric_type": "BM25",
    "params": {
        "bm25_k1": 1.2,
        "bm25_b": 0.75,
        "bm25_k3": 8.0
    }
}

code_collection.create_index(
    field_name="sparse",
    index_params=code_bm25_index,
    index_name="code_bm25_idx"
)
```

## Search Configuration

### Hybrid Search Parameters

#### Document Search Configuration
```python
# Hybrid search for documents
docs_hybrid_config = {
    "vector_search": {
        "collection_name": "ProjectDocs",
        "field_name": "embedding",
        "limit": 64,
        "metric_type": "COSINE",
        "params": {"ef": 128},
        "filter": "workspace_id == 'project_alpha'"  # Project isolation
    },
    "sparse_search": {
        "collection_name": "ProjectDocs",
        "field_name": "sparse",
        "limit": 64,
        "metric_type": "BM25"
    },
    "fusion": {
        "strategy": "weighted_sum",
        "weights": [0.65, 0.35],    # Dense, Sparse
        "normalize": True
    }
}
```

#### Code Search Configuration
```python
# Hybrid search for code
code_hybrid_config = {
    "vector_search": {
        "collection_name": "ProjectCode",
        "field_name": "embedding",
        "limit": 48,
        "metric_type": "COSINE",
        "params": {"ef": 128},
        "filter": "workspace_id == 'project_alpha'"
    },
    "sparse_search": {
        "collection_name": "ProjectCode",
        "field_name": "sparse",
        "limit": 48,
        "metric_type": "BM25"
    },
    "fusion": {
        "strategy": "weighted_sum",
        "weights": [0.55, 0.45],    # More balanced for code
        "normalize": True
    }
}
```

### Performance Tuning Parameters

#### Search Optimization Levels
```python
# Recall-optimized (higher quality, more latency)
high_recall_params = {
    "ef": 256,
    "limit": 100,
    "round_decimal": 6,
    "nprobe": 64  # For IVF indices if used
}

# Balanced (production default)
balanced_params = {
    "ef": 128,
    "limit": 64,
    "round_decimal": 4,
    "nprobe": 32
}

# Speed-optimized (lower latency, acceptable recall)
fast_params = {
    "ef": 64,
    "limit": 32,
    "round_decimal": 2,
    "nprobe": 16
}
```

## Custom Analyzers

### Code-Aware Analyzer Configuration
```json
{
  "analyzer_name": "code_aware",
  "type": "custom",
  "tokenizer": {
    "type": "pattern",
    "pattern": "[\\W&&[^._]]|(?<=\\p{Lower})(?=\\p{Upper})|(?<=\\p{Upper})(?=\\p{Upper}\\p{Lower})",
    "flags": "CASE_INSENSITIVE"
  },
  "filters": [
    {
      "type": "lowercase"
    },
    {
      "type": "stop",
      "stopwords": []  # Minimal stopword removal for code
    }
  ]
}
```

### Standard English Analyzer
```json
{
  "analyzer_name": "standard_english",
  "type": "standard",
  "tokenizer": {
    "type": "standard"
  },
  "filters": [
    {
      "type": "lowercase"
    },
    {
      "type": "stop",
      "stopwords": "_english_"
    }
  ]
}
```

## Connection Configuration

### Python Client Configuration
```python
from pymilvus import connections, Collection

# Connection parameters
milvus_config = {
    "alias": "default",
    "host": "localhost",
    "port": "19530",
    "user": "",  # Optional authentication
    "password": "",
    "secure": False,  # Set to True for TLS
    "timeout": 30,
    "retry_on_rpc_failure": True,
    "retry_on_rate_limit": True
}

# Establish connection
connections.connect(**milvus_config)

# Connection pooling settings
pool_config = {
    "pool_size": 10,
    "max_idle_time": 300,
    "retry_connect_times": 3
}
```

### Connection String Format
```
# Local development
milvus://localhost:19530/default

# With authentication
milvus://username:password@host:19530/database

# Zilliz Cloud
https://your-cluster.zillizcloud.com:443
```

## Monitoring and Metrics Configuration

### Resource Monitoring
```yaml
# milvus.yaml resource configuration
common:
  defaultPartition: "_default"
  defaultIndexName: "_default_idx_"

etcd:
  endpoints:
    - localhost:2379

minio:
  address: localhost:9000
  accessKeyID: minioadmin
  secretAccessKey: minioadmin

queryCoord:
  autoBalance: true

queryNode:
  cacheSize: 32  # GB
  numCPU: 8

indexCoord:
  gc:
    interval: 600  # seconds

indexNode:
  buildParallel: 4

dataCoord:
  segment:
    maxSize: 1024  # MB
    sealProportion: 0.8
```

### Performance Metrics Collection
```python
# Metrics to track
performance_metrics = {
    "query_latency": {
        "p50": "< 100ms",
        "p95": "< 500ms",
        "p99": "< 1000ms"
    },
    "throughput": {
        "queries_per_second": "> 50",
        "insertions_per_second": "> 1000"
    },
    "resource_usage": {
        "memory_usage": "< 80%",
        "cpu_usage": "< 70%",
        "disk_usage": "< 90%"
    },
    "index_metrics": {
        "build_time": "< 300s",
        "index_size": "< 10GB per collection"
    }
}
```

## Security Configuration

### Authentication Setup
```python
# Enable authentication in milvus.yaml
common:
  security:
    authorizationEnabled: true

# Create users and roles
from pymilvus import utility

# Create role with specific privileges
utility.create_role("rag_reader", using="default")
utility.grant_privilege(
    role_name="rag_reader",
    object_type="Collection",
    privilege="Search",
    object_name="ProjectDocs",
    using="default"
)

# Create user and assign role
utility.create_user("rag_service", "secure_password", using="default")
utility.add_user_to_role("rag_service", "rag_reader", using="default")
```

### TLS Configuration
```yaml
# milvus.yaml TLS settings
proxy:
  http:
    enabled: true
    port: 9091
  grpc:
    serverMaxRecvSize: 268435456
    tls:
      enabled: true
      cert: /path/to/server.crt
      key: /path/to/server.key
      ca: /path/to/ca.crt
```

## Backup and Recovery

### Backup Configuration
```python
# Backup utility configuration
backup_config = {
    "schedule": "0 2 * * *",  # Daily at 2 AM
    "retention_days": 30,
    "compression": True,
    "destination": "/backups/milvus",
    "collections": ["ProjectDocs", "ProjectCode"]
}

# Create backup
from milvus_backup import create_backup
create_backup(
    collection_name="ProjectDocs",
    backup_name=f"docs_backup_{datetime.now().isoformat()}",
    **backup_config
)
```

### Recovery Procedures
```python
# Restore from backup
from milvus_backup import restore_backup
restore_backup(
    backup_name="docs_backup_2025-09-23",
    collection_name="ProjectDocs_restored"
)

# Verify restoration
collection = Collection("ProjectDocs_restored")
print(f"Restored collection has {collection.num_entities} entities")
```

## Troubleshooting

### Common Configuration Issues

#### Memory Issues
```python
# Adjust segment size for large collections
data_coord_config = {
    "segment": {
        "maxSize": 512,  # Reduce from default 1024MB
        "sealProportion": 0.8
    }
}
```

#### Performance Issues
```python
# Optimize search parameters
optimized_search = {
    "ef": 64,        # Reduce from 128 for speed
    "nprobe": 16,    # Reduce search scope
    "limit": 32      # Reduce result count
}
```

#### Connection Issues
```python
# Robust connection handling
def connect_with_retry(max_retries=3):
    for attempt in range(max_retries):
        try:
            connections.connect("default", **milvus_config)
            break
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(2 ** attempt)  # Exponential backoff
```

## Environment-Specific Configurations

### Development
```yaml
# Small-scale development setup
milvus_dev:
  resources:
    memory: "4Gi"
    cpu: "2"
  storage: "10Gi"
  replicas: 1
```

### Staging
```yaml
# Mid-scale staging setup
milvus_staging:
  resources:
    memory: "16Gi"
    cpu: "8"
  storage: "100Gi"
  replicas: 2
```

### Production
```yaml
# High-availability production setup
milvus_prod:
  resources:
    memory: "32Gi"
    cpu: "16"
  storage: "1Ti"
  replicas: 3
  backup:
    enabled: true
    schedule: "0 2 * * *"
```

## Related Documentation

- **[RAG System Overview](../../94-architecture/rag/rag-system-overview.md)** - Complete system architecture
- **[Hybrid Retrieval Design](../../94-architecture/rag/hybrid-retrieval-design.md)** - Pipeline implementation details
- **[Setup Guide](../../02-how-to/rag/setup-rag-pipeline.md)** - Step-by-step implementation
- **[Operations Runbook](../../92-runbooks/rag/rag-operations-runbook.md)** - Production operations

---

**Status**: Reference Complete
**Last Updated**: 2025-09-23
**Version**: 1.0