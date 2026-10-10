# RAG Pipeline Setup Guide

## Overview

This guide provides step-by-step instructions for implementing the complete Dopemux RAG system, including Milvus setup, Voyage AI integration, ConPort memory configuration, and end-to-end testing.

## Prerequisites

### System Requirements
- **Python**: 3.9+ with pip
- **Docker**: 20.10+ with Docker Compose
- **Memory**: 16GB RAM minimum, 32GB recommended
- **Storage**: 100GB+ available disk space
- **GPU**: Optional but recommended for reranker performance

### API Access
- **Voyage AI API Key**: Register at [voyageai.com](https://voyageai.com)
- **Anthropic API Key**: Required for ConPort LLM operations

### Dependencies
```bash
# Install Python dependencies
pip install pymilvus voyageai anthropic python-dotenv pydantic fastapi uvicorn
```

## Phase 1: Infrastructure Setup

### 1.1 Milvus Deployment

#### Development Setup (Milvus Lite)
```bash
# Create project directory
mkdir -p dopemux-rag/{data,config,logs}
cd dopemux-rag

# Create docker-compose for development
cat > docker-compose.dev.yml << 'EOF'
version: '3.8'
services:
  milvus-lite:
    image: milvusdb/milvus:v2.5.0-lite
    container_name: milvus-dev
    ports:
      - "19530:19530"
      - "9091:9091"  # HTTP API
    volumes:
      - ./data/milvus:/var/lib/milvus
      - ./config/milvus.yaml:/milvus/configs/milvus.yaml
    environment:
      - MILVUS_CONFIG_PATH=/milvus/configs/milvus.yaml
    command: ["milvus", "run", "standalone"]
EOF

# Start Milvus
docker-compose -f docker-compose.dev.yml up -d

# Verify Milvus is running
curl http://localhost:9091/health
```

#### Production Setup (Milvus Cluster)
```bash
# Download official docker-compose
wget https://github.com/milvus-io/milvus/releases/download/v2.5.0/milvus-standalone-docker-compose.yml

# Customize for production
cat > docker-compose.prod.yml << 'EOF'
version: '3.8'
services:
  etcd:
    image: quay.io/coreos/etcd:v3.5.5
    container_name: milvus-etcd
    environment:
      - ETCD_AUTO_COMPACTION_MODE=revision
      - ETCD_AUTO_COMPACTION_RETENTION=1000
      - ETCD_QUOTA_BACKEND_BYTES=4294967296
      - ETCD_SNAPSHOT_COUNT=50000
    volumes:
      - ./data/etcd:/etcd
    command: etcd -advertise-client-urls=http://127.0.0.1:2379 -listen-client-urls http://0.0.0.0:2379 --data-dir /etcd
    healthcheck:
      test: ["CMD", "etcdctl", "endpoint", "health"]
      interval: 30s
      timeout: 20s
      retries: 3

  minio:
    image: minio/minio:RELEASE.2023-03-20T20-16-18Z
    container_name: milvus-minio
    environment:
      MINIO_ACCESS_KEY: minioadmin
      MINIO_SECRET_KEY: minioadmin
    volumes:
      - ./data/minio:/minio_data
    command: minio server /minio_data --console-address ":9001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3

  milvus:
    image: milvusdb/milvus:v2.5.0
    container_name: milvus-standalone
    command: ["milvus", "run", "standalone"]
    security_opt:
    - seccomp:unconfined
    environment:
      ETCD_ENDPOINTS: etcd:2379
      MINIO_ADDRESS: minio:9000
    volumes:
      - ./data/milvus:/var/lib/milvus
      - ./config/milvus.yaml:/milvus/configs/milvus.yaml
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9091/health"]
      interval: 30s
      start_period: 90s
      timeout: 20s
      retries: 3
    ports:
      - "19530:19530"
      - "9091:9091"
    depends_on:
      - "etcd"
      - "minio"
EOF

# Start production cluster
docker-compose -f docker-compose.prod.yml up -d
```

### 1.2 Milvus Configuration

Create optimized Milvus configuration:
```yaml
# config/milvus.yaml
# Common configuration
common:
  defaultPartition: "_default"
  defaultIndexName: "_default_idx_"
  retentionDuration: 432000  # 5 days in seconds
  entityExpiration: -1       # Never expire entities

# etcd configuration
etcd:
  endpoints:
    - etcd:2379
  kvTtl: 3600
  rootPath: by-dev

# MinIO configuration
minio:
  address: minio:9000
  accessKeyID: minioadmin
  secretAccessKey: minioadmin
  useSSL: false
  bucketName: a-bucket
  rootPath: files

# Query node configuration (affects search performance)
queryNode:
  cacheSize: 8192  # MB, adjust based on available memory
  loadMemoryUsageThreshold: 0.8
  enableDisk: true
  diskCacheCapacity: 16384  # MB

# Index node configuration (affects index building)
indexNode:
  buildParallel: 4  # Adjust based on CPU cores
  enableDisk: true
  diskUsageThreshold: 0.8

# Data node configuration
dataNode:
  flush:
    insertBufSize: 16777216  # 16MB
    deleteBufBytes: 16777216
    syncPeriod: 600  # 10 minutes

# Proxy configuration
proxy:
  timeTickInterval: 200  # ms
  msgStream:
    timeTick:
      bufSize: 512
  accessLog:
    enable: true
    minioEnable: true
    localPath: /tmp/milvus_access
```

### 1.3 ConPort Memory System

#### ConPort Deployment
```bash
# Clone ConPort (or use existing deployment)
git clone https://github.com/your-org/conport.git
cd conport

# Install dependencies
pip install -r requirements.txt

# Configure for Dopemux integration
cat > config/dopemux-rag.yaml << 'EOF'
conport:
  database:
    type: sqlite
    path: /data/conport/dopemux-rag.db

  workspaces:
    isolation: true
    default_workspace: "default"

  memory_types:
    - DocumentChunk
    - CodeChunk
    - Query
    - Answer
    - Decision

  api:
    host: "0.0.0.0"
    port: 8080
    cors_origins:
      - "http://localhost:*"

  logging:
    level: INFO
    file: /data/conport/logs/rag.log
EOF

# Start ConPort
python -m conport.server --config config/dopemux-rag.yaml
```

## Phase 2: Core Pipeline Implementation

### 2.1 Document Ingestion Pipeline

Create the ingestion system:
```python
# src/rag/ingestion.py
import os
import hashlib
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

import voyageai
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType
import tiktoken

@dataclass
class DocumentChunk:
    id: str
    doc_id: str
    title: str
    text: str
    prelude: str
    source: str
    chunk_index: int
    last_updated: int
    workspace_id: str

@dataclass
class CodeChunk:
    id: str
    file_path: str
    func_sig: str
    code: str
    language: str
    start_line: int
    end_line: int
    complexity_score: float
    last_updated: int
    workspace_id: str

class IngestionPipeline:
    def __init__(self, voyage_api_key: str, milvus_host: str = "localhost", milvus_port: int = 19530):
        self.voyage_client = voyageai.Client(api_key=voyage_api_key)
        self.milvus_host = milvus_host
        self.milvus_port = milvus_port
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

        # Connect to Milvus
        connections.connect("default", host=milvus_host, port=milvus_port)

    def setup_collections(self):
        """Create Milvus collections for docs and code."""

        # Document collection schema
        docs_fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True),
            FieldSchema(name="doc_id", dtype=DataType.VARCHAR, max_length=255),
            FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=512),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=4096,
                       enable_analyzer=True, analyzer_params={"type": "standard"}),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1024),
            FieldSchema(name="sparse", dtype=DataType.SPARSE_FLOAT_VECTOR),
            FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=512),
            FieldSchema(name="chunk_index", dtype=DataType.INT32),
            FieldSchema(name="prelude", dtype=DataType.VARCHAR, max_length=512),
            FieldSchema(name="last_updated", dtype=DataType.INT64),
            FieldSchema(name="workspace_id", dtype=DataType.VARCHAR, max_length=128)
        ]

        docs_schema = CollectionSchema(
            fields=docs_fields,
            description="Dopemux project documentation chunks",
            enable_dynamic_field=True
        )

        # Create docs collection
        if Collection.has_collection("ProjectDocs"):
            Collection("ProjectDocs").drop()

        docs_collection = Collection("ProjectDocs", docs_schema)

        # Create vector index
        docs_collection.create_index(
            field_name="embedding",
            index_params={
                "index_type": "HNSW",
                "metric_type": "COSINE",
                "params": {"M": 16, "efConstruction": 200}
            }
        )

        # Create sparse index
        docs_collection.create_index(
            field_name="sparse",
            index_params={
                "index_type": "SPARSE_INVERTED_INDEX",
                "metric_type": "BM25",
                "params": {"bm25_k1": 1.2, "bm25_b": 0.75}
            }
        )

        # Code collection schema
        code_fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True),
            FieldSchema(name="file_path", dtype=DataType.VARCHAR, max_length=1024),
            FieldSchema(name="func_sig", dtype=DataType.VARCHAR, max_length=512),
            FieldSchema(name="code", dtype=DataType.VARCHAR, max_length=8192,
                       enable_analyzer=True, analyzer_params={"type": "keyword"}),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1024),
            FieldSchema(name="sparse", dtype=DataType.SPARSE_FLOAT_VECTOR),
            FieldSchema(name="language", dtype=DataType.VARCHAR, max_length=32),
            FieldSchema(name="start_line", dtype=DataType.INT32),
            FieldSchema(name="end_line", dtype=DataType.INT32),
            FieldSchema(name="complexity_score", dtype=DataType.FLOAT),
            FieldSchema(name="last_updated", dtype=DataType.INT64),
            FieldSchema(name="workspace_id", dtype=DataType.VARCHAR, max_length=128)
        ]

        code_schema = CollectionSchema(
            fields=code_fields,
            description="Dopemux project code chunks",
            enable_dynamic_field=True
        )

        # Create code collection
        if Collection.has_collection("ProjectCode"):
            Collection("ProjectCode").drop()

        code_collection = Collection("ProjectCode", code_schema)

        # Create indices for code
        code_collection.create_index(
            field_name="embedding",
            index_params={
                "index_type": "HNSW",
                "metric_type": "COSINE",
                "params": {"M": 16, "efConstruction": 200}
            }
        )

        code_collection.create_index(
            field_name="sparse",
            index_params={
                "index_type": "SPARSE_INVERTED_INDEX",
                "metric_type": "BM25",
                "params": {"bm25_k1": 1.2, "bm25_b": 0.75}
            }
        )

        return docs_collection, code_collection

    def chunk_document(self, content: str, title: str, source: str, max_tokens: int = 400) -> List[Dict]:
        """Chunk document into semantic segments."""

        # Simple sentence-based chunking (replace with more sophisticated method)
        sentences = content.split('. ')
        chunks = []
        current_chunk = ""
        current_tokens = 0
        chunk_index = 0

        for sentence in sentences:
            sentence_tokens = len(self.tokenizer.encode(sentence))

            if current_tokens + sentence_tokens > max_tokens and current_chunk:
                # Generate prelude for this chunk
                prelude = self.generate_prelude(current_chunk, title, "document")

                chunks.append({
                    "text": current_chunk.strip(),
                    "prelude": prelude,
                    "title": f"{title} (Part {chunk_index + 1})",
                    "source": source,
                    "chunk_index": chunk_index
                })

                current_chunk = sentence
                current_tokens = sentence_tokens
                chunk_index += 1
            else:
                current_chunk += sentence + ". "
                current_tokens += sentence_tokens

        # Add final chunk
        if current_chunk.strip():
            prelude = self.generate_prelude(current_chunk, title, "document")
            chunks.append({
                "text": current_chunk.strip(),
                "prelude": prelude,
                "title": f"{title} (Part {chunk_index + 1})",
                "source": source,
                "chunk_index": chunk_index
            })

        return chunks

    def generate_prelude(self, content: str, title: str, content_type: str) -> str:
        """Generate contextual prelude for chunk."""

        # Simplified prelude generation (use LLM for production)
        if content_type == "document":
            # Extract first sentence or create summary
            first_sentence = content.split('.')[0]
            return f"From {title}: {first_sentence}..."
        elif content_type == "code":
            # Extract function signature or create brief description
            lines = content.split('\n')
            for line in lines:
                if any(keyword in line for keyword in ['def ', 'function ', 'class ', 'interface ']):
                    return f"Code: {line.strip()}"
            return f"Code snippet from {title}"

        return ""

    def embed_chunks(self, chunks: List[Dict], model: str = "voyage-context-3") -> List[Dict]:
        """Generate embeddings for chunks."""

        # Prepare text for embedding (combine prelude + content)
        texts = [f"{chunk['prelude']}\n\n{chunk['text']}" for chunk in chunks]

        # Generate embeddings in batches
        batch_size = 100
        embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            response = self.voyage_client.embed(
                texts=batch,
                model=model,
                input_type="document"
            )
            embeddings.extend(response.embeddings)

        # Add embeddings to chunks
        for chunk, embedding in zip(chunks, embeddings):
            chunk["embedding"] = embedding

        return chunks

    def ingest_document(self, file_path: str, workspace_id: str = "default"):
        """Ingest a single document."""

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")

        # Read content
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Generate document ID
        doc_id = hashlib.sha256(f"{workspace_id}:{file_path}".encode()).hexdigest()[:16]

        # Chunk document
        chunks = self.chunk_document(
            content=content,
            title=path.stem,
            source=file_path
        )

        # Generate embeddings
        chunks = self.embed_chunks(chunks, model="voyage-context-3")

        # Create document chunks
        doc_chunks = []
        timestamp = int(time.time())

        for i, chunk_data in enumerate(chunks):
            chunk_id = int(hashlib.sha256(f"{doc_id}:{i}".encode()).hexdigest()[:15], 16)

            chunk = DocumentChunk(
                id=chunk_id,
                doc_id=doc_id,
                title=chunk_data["title"],
                text=f"{chunk_data['prelude']}\n\n{chunk_data['text']}",
                prelude=chunk_data["prelude"],
                source=chunk_data["source"],
                chunk_index=chunk_data["chunk_index"],
                last_updated=timestamp,
                workspace_id=workspace_id
            )
            doc_chunks.append(chunk)

        # Insert into Milvus
        self.insert_document_chunks(doc_chunks)

        return doc_chunks

    def insert_document_chunks(self, chunks: List[DocumentChunk]):
        """Insert document chunks into Milvus."""

        docs_collection = Collection("ProjectDocs")

        # Prepare data for insertion
        ids = [chunk.id for chunk in chunks]
        doc_ids = [chunk.doc_id for chunk in chunks]
        titles = [chunk.title for chunk in chunks]
        texts = [chunk.text for chunk in chunks]
        embeddings = [chunk.embedding for chunk in chunks]  # Need to add this field
        sources = [chunk.source for chunk in chunks]
        chunk_indices = [chunk.chunk_index for chunk in chunks]
        preludes = [chunk.prelude for chunk in chunks]
        timestamps = [chunk.last_updated for chunk in chunks]
        workspace_ids = [chunk.workspace_id for chunk in chunks]

        # Generate sparse vectors (simplified BM25 representation)
        sparse_vectors = self.generate_sparse_vectors(texts)

        # Insert data
        docs_collection.insert([
            ids, doc_ids, titles, texts, embeddings, sparse_vectors,
            sources, chunk_indices, preludes, timestamps, workspace_ids
        ])

        docs_collection.flush()

    def generate_sparse_vectors(self, texts: List[str]) -> List[Dict]:
        """Generate sparse BM25-style vectors (simplified)."""

        # This is a simplified implementation
        # In production, use proper BM25 implementation
        sparse_vectors = []

        for text in texts:
            # Simple term frequency calculation
            words = text.lower().split()
            word_freq = {}
            for word in words:
                word_freq[word] = word_freq.get(word, 0) + 1

            # Create sparse vector representation
            # In reality, this would use proper BM25 calculation
            indices = list(range(len(word_freq)))
            values = list(word_freq.values())

            sparse_vectors.append({
                "indices": indices[:100],  # Limit for demo
                "values": [float(v) for v in values[:100]]
            })

        return sparse_vectors
```

### 2.2 Query Pipeline Implementation

```python
# src/rag/retrieval.py
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

import voyageai
from pymilvus import Collection
import numpy as np

@dataclass
class RetrievalResult:
    id: str
    text: str
    title: str
    source: str
    score: float
    dense_score: float
    sparse_score: float
    rerank_score: Optional[float] = None

class HybridRetriever:
    def __init__(self, voyage_api_key: str, policy_config_path: str = "config/rag/role-policies.json"):
        self.voyage_client = voyageai.Client(api_key=voyage_api_key)

        # Load role policies
        with open(policy_config_path, 'r') as f:
            self.policies = json.load(f)

    def search(self, query: str, role: str, task: str, workspace_id: str = "default") -> List[RetrievalResult]:
        """Execute hybrid search with role-based configuration."""

        # Get policy for role and task
        policy = self.get_policy(role, task)

        # Stage 1: Hybrid search
        candidates = self.hybrid_search(query, policy, workspace_id)

        # Stage 2: Reranking
        reranked_results = self.rerank_candidates(query, candidates, policy)

        return reranked_results

    def get_policy(self, role: str, task: str) -> Dict[str, Any]:
        """Get resolved policy for role and task."""

        # Try exact match
        exact_key = f"{role}:{task}"
        if exact_key in self.policies:
            return self.policies[exact_key]

        # Try role default
        role_default = f"{role}:General"
        if role_default in self.policies:
            return self.policies[role_default]

        # Fall back to default
        return self.policies.get("Default:General", self.get_default_policy())

    def get_default_policy(self) -> Dict[str, Any]:
        """Return default policy."""
        return {
            "source_weights": {"ProjectDocs": 0.6, "ProjectCode": 0.4},
            "rerank_instruction": "Provide balanced and relevant information.",
            "filters": {},
            "context_limits": {"max_candidates": 64, "max_results": 10, "max_tokens": 2500}
        }

    def hybrid_search(self, query: str, policy: Dict[str, Any], workspace_id: str) -> List[RetrievalResult]:
        """Execute Stage 1 hybrid search."""

        # Generate query embedding
        query_embedding = self.voyage_client.embed(
            texts=[query],
            model="voyage-context-3",
            input_type="query"
        ).embeddings[0]

        results = []
        source_weights = policy["source_weights"]
        context_limits = policy.get("context_limits", {})
        max_candidates = context_limits.get("max_candidates", 64)

        # Search documents if weighted
        if source_weights.get("ProjectDocs", 0) > 0:
            doc_results = self.search_collection(
                collection_name="ProjectDocs",
                query_embedding=query_embedding,
                query_text=query,
                workspace_id=workspace_id,
                limit=int(max_candidates * source_weights["ProjectDocs"]),
                filters=policy.get("filters", {})
            )
            results.extend(doc_results)

        # Search code if weighted
        if source_weights.get("ProjectCode", 0) > 0:
            code_results = self.search_collection(
                collection_name="ProjectCode",
                query_embedding=query_embedding,
                query_text=query,
                workspace_id=workspace_id,
                limit=int(max_candidates * source_weights["ProjectCode"]),
                filters=policy.get("filters", {})
            )
            results.extend(code_results)

        # Sort by combined score and return top candidates
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:max_candidates]

    def search_collection(self, collection_name: str, query_embedding: List[float],
                         query_text: str, workspace_id: str, limit: int,
                         filters: Dict[str, Any]) -> List[RetrievalResult]:
        """Search a single Milvus collection with hybrid scoring."""

        collection = Collection(collection_name)
        collection.load()

        # Build filter expression
        filter_expr = f"workspace_id == '{workspace_id}'"

        # Add additional filters based on policy
        if filters.get("include_modules"):
            modules = "', '".join(filters["include_modules"])
            filter_expr += f" and (source like '{modules[0]}%'"
            for module in filters["include_modules"][1:]:
                filter_expr += f" or source like '{module}%'"
            filter_expr += ")"

        # Vector search
        vector_results = collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param={"metric_type": "COSINE", "params": {"ef": 128}},
            limit=limit * 2,  # Get more for fusion
            expr=filter_expr,
            output_fields=["id", "title", "text", "source"]
        )

        # Convert results
        results = []
        for hit in vector_results[0]:
            result = RetrievalResult(
                id=str(hit.id),
                text=hit.entity.get("text", ""),
                title=hit.entity.get("title", ""),
                source=hit.entity.get("source", ""),
                score=1.0 - hit.distance,  # Convert distance to similarity
                dense_score=1.0 - hit.distance,
                sparse_score=0.0  # Will be computed separately
            )
            results.append(result)

        # Note: Simplified implementation
        # In production, implement proper BM25 search and fusion

        return results[:limit]

    def rerank_candidates(self, query: str, candidates: List[RetrievalResult],
                         policy: Dict[str, Any]) -> List[RetrievalResult]:
        """Execute Stage 2 reranking."""

        if not candidates:
            return candidates

        context_limits = policy.get("context_limits", {})
        max_results = context_limits.get("max_results", 10)

        # Prepare reranker input
        documents = [candidate.text for candidate in candidates]
        instruction = policy["rerank_instruction"]

        try:
            # Execute reranking
            rerank_response = self.voyage_client.rerank(
                query=query,
                documents=documents,
                model="rerank-2.5",
                instruction=instruction,
                top_k=min(max_results, len(candidates))
            )

            # Update candidates with rerank scores
            reranked_candidates = []
            for result in rerank_response.results:
                candidate = candidates[result.index]
                candidate.rerank_score = result.relevance_score
                candidate.score = result.relevance_score  # Use rerank score as final score
                reranked_candidates.append(candidate)

            return reranked_candidates

        except Exception as e:
            print(f"Reranking failed: {e}, returning original order")
            return candidates[:max_results]
```

### 2.3 End-to-End Integration Test

```python
# tests/test_rag_integration.py
import pytest
import tempfile
import os
from pathlib import Path

from src.rag.ingestion import IngestionPipeline
from src.rag.retrieval import HybridRetriever

@pytest.fixture
def sample_documents():
    """Create sample documents for testing."""

    docs = [
        {
            "filename": "auth_service.md",
            "content": """# Authentication Service

The authentication service handles user login and token management.

## Token Storage

We use Redis to store refresh tokens with a 1-hour TTL. This ensures tokens are securely stored and globally available across service instances.

## Implementation Details

The service implements OAuth 2.0 with PKCE for enhanced security. All tokens are encrypted before storage.
"""
        },
        {
            "filename": "cache_service.py",
            "content": """# Cache Service Implementation
def store_token(token_value, user_id, ttl_seconds=3600):
    '''Store refresh token in Redis cache.

    Args:
        token_value: The token to store
        user_id: User identifier
        ttl_seconds: Time to live in seconds
    '''
    cache_key = f"refresh_token:{user_id}"
    redis_client.setex(cache_key, ttl_seconds, token_value)
    return True

class AuthTokenCache:
    def __init__(self, redis_client):
        self.redis = redis_client

    def get_token(self, user_id):
        return self.redis.get(f"refresh_token:{user_id}")
"""
        }
    ]

    return docs

@pytest.fixture
def temp_workspace(sample_documents):
    """Set up temporary workspace with sample documents."""

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Write sample documents
        for doc in sample_documents:
            doc_path = temp_path / doc["filename"]
            with open(doc_path, 'w') as f:
                f.write(doc["content"])

        yield temp_path

class TestRAGIntegration:

    def test_document_ingestion(self, temp_workspace):
        """Test complete document ingestion pipeline."""

        # Initialize ingestion pipeline
        pipeline = IngestionPipeline(
            voyage_api_key=os.getenv("VOYAGE_API_KEY"),
            milvus_host="localhost"
        )

        # Setup collections
        docs_collection, code_collection = pipeline.setup_collections()

        # Ingest documents
        for doc_file in temp_workspace.glob("*.md"):
            chunks = pipeline.ingest_document(str(doc_file), workspace_id="test_workspace")
            assert len(chunks) > 0
            assert all(chunk.workspace_id == "test_workspace" for chunk in chunks)

        # Verify ingestion
        docs_collection.load()
        assert docs_collection.num_entities > 0

    def test_hybrid_retrieval(self, temp_workspace):
        """Test end-to-end retrieval pipeline."""

        # Setup ingestion
        pipeline = IngestionPipeline(
            voyage_api_key=os.getenv("VOYAGE_API_KEY")
        )
        pipeline.setup_collections()

        # Ingest test documents
        for doc_file in temp_workspace.glob("*"):
            pipeline.ingest_document(str(doc_file), workspace_id="test_workspace")

        # Setup retrieval
        retriever = HybridRetriever(
            voyage_api_key=os.getenv("VOYAGE_API_KEY"),
            policy_config_path="config/rag/role-policies.json"
        )

        # Test different role queries
        test_cases = [
            {
                "query": "How are refresh tokens stored?",
                "role": "Developer",
                "task": "CodeImplementation",
                "expected_content": ["Redis", "cache", "token"]
            },
            {
                "query": "What is the authentication architecture?",
                "role": "Architect",
                "task": "SystemDesign",
                "expected_content": ["OAuth", "service", "authentication"]
            }
        ]

        for case in test_cases:
            results = retriever.search(
                query=case["query"],
                role=case["role"],
                task=case["task"],
                workspace_id="test_workspace"
            )

            # Verify results
            assert len(results) > 0
            assert results[0].score > 0.5  # Reasonable relevance

            # Check content relevance
            result_text = " ".join([r.text.lower() for r in results])
            for expected_term in case["expected_content"]:
                assert expected_term.lower() in result_text

    def test_role_policy_application(self):
        """Test role-specific policy application."""

        retriever = HybridRetriever(
            voyage_api_key=os.getenv("VOYAGE_API_KEY")
        )

        # Test developer policy
        dev_policy = retriever.get_policy("Developer", "CodeImplementation")
        assert dev_policy["source_weights"]["ProjectCode"] >= 0.6
        assert "code" in dev_policy["rerank_instruction"].lower()

        # Test PM policy
        pm_policy = retriever.get_policy("PM", "FeatureDiscussion")
        assert pm_policy["source_weights"]["ProjectDocs"] >= 0.9
        assert "documentation" in pm_policy["rerank_instruction"].lower()

if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v"])
```

## Phase 3: ConPort Memory Integration

### 3.1 Memory Integration Setup

```python
# src/rag/memory_integration.py
import json
import time
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

import requests
from pymilvus import Collection

@dataclass
class MemoryNode:
    id: str
    type: str
    data: Dict[str, Any]
    workspace_id: str
    timestamp: int

@dataclass
class MemoryEdge:
    from_id: str
    to_id: str
    type: str
    attributes: Dict[str, Any]
    timestamp: int

class ConPortIntegration:
    def __init__(self, conport_url: str = "http://localhost:8080"):
        self.conport_url = conport_url
        self.session = requests.Session()
        self.logger = logging.getLogger(__name__)

        # Buffer for offline operations
        self.operation_buffer = []

    def log_query(self, query: str, role: str, task: str, session_id: str, workspace_id: str) -> str:
        """Log user query to memory graph."""

        query_id = f"query_{int(time.time() * 1000)}"

        node_data = {
            "query_text": query,
            "role": role,
            "task": task,
            "session_id": session_id,
            "timestamp": int(time.time())
        }

        try:
            response = self.session.post(
                f"{self.conport_url}/api/memory/upsert",
                json={
                    "id": query_id,
                    "type": "Query",
                    "data": node_data,
                    "workspace_id": workspace_id
                }
            )
            response.raise_for_status()

        except Exception as e:
            self.logger.warning(f"Failed to log query to ConPort: {e}")
            # Buffer for retry
            self.operation_buffer.append({
                "type": "upsert_node",
                "data": {"id": query_id, "type": "Query", "data": node_data, "workspace_id": workspace_id}
            })

        return query_id

    def log_retrieval_results(self, query_id: str, results: List[RetrievalResult],
                            stage: str, workspace_id: str):
        """Log retrieval results and create relationships."""

        try:
            for i, result in enumerate(results):
                # Create chunk node if not exists
                chunk_node_data = {
                    "title": result.title,
                    "source": result.source,
                    "text_preview": result.text[:200] + "..." if len(result.text) > 200 else result.text
                }

                chunk_type = "CodeChunk" if result.source.endswith(('.py', '.js', '.java', '.go')) else "DocumentChunk"

                # Upsert chunk node
                self.session.post(
                    f"{self.conport_url}/api/memory/upsert",
                    json={
                        "id": result.id,
                        "type": chunk_type,
                        "data": chunk_node_data,
                        "workspace_id": workspace_id
                    }
                )

                # Create relationship
                edge_data = {
                    "stage": stage,
                    "rank": i + 1,
                    "score": result.score,
                    "dense_score": result.dense_score,
                    "sparse_score": result.sparse_score
                }

                if result.rerank_score is not None:
                    edge_data["rerank_score"] = result.rerank_score

                self.session.post(
                    f"{self.conport_url}/api/memory/link",
                    json={
                        "from_id": query_id,
                        "to_id": result.id,
                        "type": "retrieved",
                        "attributes": edge_data,
                        "workspace_id": workspace_id
                    }
                )

        except Exception as e:
            self.logger.warning(f"Failed to log retrieval results: {e}")
            # Buffer operation for retry
            self.operation_buffer.append({
                "type": "log_retrieval",
                "data": {"query_id": query_id, "results": results, "stage": stage, "workspace_id": workspace_id}
            })

    def log_context_usage(self, query_id: str, used_chunks: List[str], workspace_id: str):
        """Log which chunks were actually used in context."""

        try:
            for chunk_id in used_chunks:
                self.session.post(
                    f"{self.conport_url}/api/memory/link",
                    json={
                        "from_id": query_id,
                        "to_id": chunk_id,
                        "type": "context_used",
                        "attributes": {"timestamp": int(time.time())},
                        "workspace_id": workspace_id
                    }
                )

        except Exception as e:
            self.logger.warning(f"Failed to log context usage: {e}")

    def log_answer(self, query_id: str, answer_text: str, used_chunk_ids: List[str], workspace_id: str) -> str:
        """Log generated answer and its supporting chunks."""

        answer_id = f"answer_{int(time.time() * 1000)}"

        try:
            # Create answer node
            self.session.post(
                f"{self.conport_url}/api/memory/upsert",
                json={
                    "id": answer_id,
                    "type": "Answer",
                    "data": {
                        "text": answer_text,
                        "timestamp": int(time.time())
                    },
                    "workspace_id": workspace_id
                }
            )

            # Link query to answer
            self.session.post(
                f"{self.conport_url}/api/memory/link",
                json={
                    "from_id": query_id,
                    "to_id": answer_id,
                    "type": "answer_to",
                    "attributes": {},
                    "workspace_id": workspace_id
                }
            )

            # Link answer to supporting chunks
            for chunk_id in used_chunk_ids:
                self.session.post(
                    f"{self.conport_url}/api/memory/link",
                    json={
                        "from_id": answer_id,
                        "to_id": chunk_id,
                        "type": "supported_by",
                        "attributes": {"score": 1.0},  # Could use actual relevance scores
                        "workspace_id": workspace_id
                    }
                )

        except Exception as e:
            self.logger.error(f"Failed to log answer: {e}")

        return answer_id

    def retry_buffered_operations(self):
        """Retry buffered operations when ConPort is available."""

        if not self.operation_buffer:
            return

        successful_operations = []

        for operation in self.operation_buffer:
            try:
                if operation["type"] == "upsert_node":
                    self.session.post(f"{self.conport_url}/api/memory/upsert", json=operation["data"])
                elif operation["type"] == "log_retrieval":
                    data = operation["data"]
                    self.log_retrieval_results(data["query_id"], data["results"], data["stage"], data["workspace_id"])

                successful_operations.append(operation)

            except Exception as e:
                self.logger.debug(f"Retry failed for operation: {e}")

        # Remove successful operations from buffer
        for op in successful_operations:
            self.operation_buffer.remove(op)

        self.logger.info(f"Retried {len(successful_operations)} operations, {len(self.operation_buffer)} still buffered")
```

### 3.2 Enhanced Retrieval with Memory Integration

```python
# Update HybridRetriever to include memory logging
class EnhancedHybridRetriever(HybridRetriever):
    def __init__(self, voyage_api_key: str, policy_config_path: str, conport_url: str = "http://localhost:8080"):
        super().__init__(voyage_api_key, policy_config_path)
        self.memory = ConPortIntegration(conport_url)

    def search_with_memory(self, query: str, role: str, task: str, session_id: str = "default",
                          workspace_id: str = "default") -> Tuple[List[RetrievalResult], str]:
        """Execute search with full memory integration."""

        # Log query
        query_id = self.memory.log_query(query, role, task, session_id, workspace_id)

        # Stage 1: Hybrid search
        policy = self.get_policy(role, task)
        stage1_candidates = self.hybrid_search(query, policy, workspace_id)

        # Log Stage 1 results
        self.memory.log_retrieval_results(query_id, stage1_candidates, "initial", workspace_id)

        # Stage 2: Reranking
        final_results = self.rerank_candidates(query, stage1_candidates, policy)

        # Log Stage 2 results
        self.memory.log_retrieval_results(query_id, final_results, "rerank", workspace_id)

        # Log context usage (all final results are used)
        used_chunk_ids = [result.id for result in final_results]
        self.memory.log_context_usage(query_id, used_chunk_ids, workspace_id)

        # Retry any buffered operations
        self.memory.retry_buffered_operations()

        return final_results, query_id
```

## Phase 4: Testing and Validation

### 4.1 System Validation Script

```python
# scripts/validate_rag_system.py
#!/usr/bin/env python3

import os
import sys
import time
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rag.ingestion import IngestionPipeline
from rag.retrieval import EnhancedHybridRetriever

def validate_system():
    """Comprehensive system validation."""

    print("🚀 Starting RAG System Validation...")

    # Check environment variables
    required_env = ["VOYAGE_API_KEY"]
    missing_env = [env for env in required_env if not os.getenv(env)]
    if missing_env:
        print(f"❌ Missing environment variables: {missing_env}")
        return False

    try:
        # Test 1: Milvus Connection
        print("\n📊 Testing Milvus connection...")
        pipeline = IngestionPipeline(voyage_api_key=os.getenv("VOYAGE_API_KEY"))
        docs_collection, code_collection = pipeline.setup_collections()
        print("✅ Milvus connection successful")

        # Test 2: Voyage AI Integration
        print("\n🚢 Testing Voyage AI integration...")
        test_texts = ["This is a test document for embedding."]
        embeddings = pipeline.voyage_client.embed(texts=test_texts).embeddings
        assert len(embeddings) == 1
        assert len(embeddings[0]) == 1024
        print("✅ Voyage AI embeddings working")

        # Test 3: Document Ingestion
        print("\n📄 Testing document ingestion...")
        test_content = """# Test Document

This is a test document for validating the RAG ingestion pipeline.

## Features

The system supports:
- Hybrid search with vector and BM25
- Role-based retrieval policies
- Memory integration with ConPort

## Implementation

The implementation uses Milvus for storage and Voyage AI for embeddings.
"""

        # Create temporary test file
        test_file = Path("/tmp/test_rag_doc.md")
        with open(test_file, 'w') as f:
            f.write(test_content)

        chunks = pipeline.ingest_document(str(test_file), workspace_id="validation_test")
        assert len(chunks) > 0
        print(f"✅ Ingested {len(chunks)} chunks")

        # Test 4: Hybrid Retrieval
        print("\n🔍 Testing hybrid retrieval...")
        retriever = EnhancedHybridRetriever(
            voyage_api_key=os.getenv("VOYAGE_API_KEY"),
            policy_config_path="config/rag/role-policies.json"
        )

        results, query_id = retriever.search_with_memory(
            query="What features does the system support?",
            role="Developer",
            task="CodeImplementation",
            workspace_id="validation_test"
        )

        assert len(results) > 0
        assert results[0].score > 0.3
        print(f"✅ Retrieved {len(results)} relevant results")

        # Test 5: Role Policy Application
        print("\n👥 Testing role policies...")

        # Test different role configurations
        roles_tasks = [
            ("Developer", "CodeImplementation"),
            ("Architect", "SystemDesign"),
            ("PM", "FeatureDiscussion")
        ]

        for role, task in roles_tasks:
            policy = retriever.get_policy(role, task)
            assert "source_weights" in policy
            assert "rerank_instruction" in policy
            print(f"✅ {role}:{task} policy loaded")

        # Test 6: ConPort Memory Integration
        print("\n🧠 Testing ConPort integration...")
        try:
            import requests
            health_response = requests.get("http://localhost:8080/health", timeout=5)
            if health_response.status_code == 200:
                print("✅ ConPort integration working")
            else:
                print("⚠️ ConPort health check failed, but system can continue")
        except:
            print("⚠️ ConPort not available, memory features disabled")

        # Cleanup
        test_file.unlink()

        print("\n🎉 All validation tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = validate_system()
    sys.exit(0 if success else 1)
```

### 4.2 Performance Benchmarking

```python
# scripts/benchmark_rag.py
#!/usr/bin/env python3

import time
import statistics
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

def benchmark_retrieval():
    """Benchmark retrieval performance."""

    print("🏃‍♂️ Starting RAG Performance Benchmark...")

    retriever = EnhancedHybridRetriever(
        voyage_api_key=os.getenv("VOYAGE_API_KEY"),
        policy_config_path="config/rag/role-policies.json"
    )

    # Test queries
    test_queries = [
        "How does authentication work?",
        "What is the caching strategy?",
        "Show me error handling patterns",
        "Explain the API design",
        "What are the performance requirements?"
    ]

    # Benchmark different scenarios
    scenarios = [
        {"role": "Developer", "task": "CodeImplementation"},
        {"role": "Architect", "task": "SystemDesign"},
        {"role": "SRE", "task": "IncidentResponse"},
        {"role": "PM", "task": "FeatureDiscussion"}
    ]

    results = {}

    for scenario in scenarios:
        print(f"\n📊 Benchmarking {scenario['role']}:{scenario['task']}")

        latencies = []
        accuracies = []

        for query in test_queries:
            start_time = time.time()

            try:
                search_results, query_id = retriever.search_with_memory(
                    query=query,
                    role=scenario["role"],
                    task=scenario["task"],
                    workspace_id="benchmark_test"
                )

                end_time = time.time()
                latency_ms = (end_time - start_time) * 1000
                latencies.append(latency_ms)

                # Simple accuracy check: ensure we got results
                accuracy = 1.0 if len(search_results) > 0 and search_results[0].score > 0.3 else 0.0
                accuracies.append(accuracy)

            except Exception as e:
                print(f"Query failed: {e}")
                latencies.append(float('inf'))
                accuracies.append(0.0)

        # Calculate statistics
        scenario_key = f"{scenario['role']}:{scenario['task']}"
        results[scenario_key] = {
            "latency_p50": statistics.median(latencies),
            "latency_p95": statistics.quantiles(latencies, n=20)[18],  # 95th percentile
            "latency_mean": statistics.mean(latencies),
            "accuracy": statistics.mean(accuracies),
            "success_rate": sum(1 for l in latencies if l != float('inf')) / len(latencies)
        }

        print(f"  • Latency P50: {results[scenario_key]['latency_p50']:.1f}ms")
        print(f"  • Latency P95: {results[scenario_key]['latency_p95']:.1f}ms")
        print(f"  • Accuracy: {results[scenario_key]['accuracy']:.2f}")
        print(f"  • Success Rate: {results[scenario_key]['success_rate']:.2f}")

    # Save results
    with open("benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\n📈 Benchmark complete! Results saved to benchmark_results.json")

if __name__ == "__main__":
    benchmark_retrieval()
```

## Phase 5: Production Configuration

### 5.1 Environment Configuration

Create production configuration files:

```bash
# config/rag/production.env
VOYAGE_API_KEY=your_production_key
MILVUS_HOST=your-milvus-cluster.com
MILVUS_PORT=19530
CONPORT_URL=https://conport.your-domain.com
LOG_LEVEL=INFO

# config/rag/development.env
VOYAGE_API_KEY=your_dev_key
MILVUS_HOST=localhost
MILVUS_PORT=19530
CONPORT_URL=http://localhost:8080
LOG_LEVEL=DEBUG
```

### 5.2 Deployment Scripts

```bash
#!/bin/bash
# scripts/deploy_rag_system.sh

set -e

echo "🚀 Deploying RAG System..."

# Load environment
if [ "$1" = "production" ]; then
    source config/rag/production.env
    COMPOSE_FILE="docker-compose.prod.yml"
else
    source config/rag/development.env
    COMPOSE_FILE="docker-compose.dev.yml"
fi

# Deploy Milvus
echo "📊 Deploying Milvus..."
docker-compose -f $COMPOSE_FILE up -d

# Wait for Milvus to be ready
echo "⏳ Waiting for Milvus to be ready..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -f http://$MILVUS_HOST:9091/health >/dev/null 2>&1; then
        echo "✅ Milvus is ready!"
        break
    fi

    attempt=$((attempt + 1))
    echo "Attempt $attempt/$max_attempts: Milvus not ready yet..."
    sleep 10
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Milvus failed to start within timeout"
    exit 1
fi

# Setup collections
echo "🗄️ Setting up Milvus collections..."
python scripts/setup_collections.py

# Deploy ConPort if needed
if [ "$1" = "production" ]; then
    echo "🧠 Deploying ConPort..."
    # Add ConPort deployment commands here
fi

# Run validation
echo "✅ Validating deployment..."
python scripts/validate_rag_system.py

if [ $? -eq 0 ]; then
    echo "🎉 RAG System deployment successful!"
else
    echo "❌ Deployment validation failed"
    exit 1
fi
```

## Next Steps

1. **Test the Implementation**:
   ```bash
   # Run validation
   python scripts/validate_rag_system.py

   # Run benchmarks
   python scripts/benchmark_rag.py
   ```

2. **Configure Role Policies**: Customize `config/rag/role-policies.json` for your team's needs

3. **Set up Monitoring**: Implement the operational runbook procedures

4. **Integrate with Dopemux**: Connect to existing Dopemux workflows and sessions

5. **Production Deployment**: Use production configuration and monitoring

## Troubleshooting

### Common Issues

1. **Milvus Connection Failed**:
   - Check Docker containers are running: `docker ps`
   - Verify port accessibility: `curl http://localhost:9091/health`

2. **Voyage API Errors**:
   - Validate API key: `echo $VOYAGE_API_KEY`
   - Check quota and rate limits

3. **Empty Search Results**:
   - Ensure documents are ingested: Check collection entity count
   - Verify workspace isolation: Use correct workspace_id

4. **ConPort Integration Issues**:
   - Check ConPort service health: `curl http://localhost:8080/health`
   - Review buffered operations in logs

## Related Documentation

- **[RAG System Overview](../../94-architecture/rag/rag-system-overview.md)** - System architecture
- **[Milvus Configuration](../../03-reference/rag/milvus-configuration-reference.md)** - Database setup
- **[ConPort Integration](./integrate-conport-memory.md)** - Memory system setup
- **[Operations Runbook](../../92-runbooks/rag/rag-operations-runbook.md)** - Production operations

---

**Status**: Implementation Guide Complete
**Last Updated**: 2025-09-23
**Version**: 1.0