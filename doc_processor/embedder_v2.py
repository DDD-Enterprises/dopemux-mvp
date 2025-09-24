"""
Max-Performance Document Embedding System with Voyage Context-3 + Milvus + Reranker

Production-ready retrieval stack optimized for accuracy and performance:
- Voyage Context-3 contextualized embeddings (2048-dim, 32K context)
- Milvus HNSW with BM25 hybrid search
- Voyage Rerank-2.5 second-stage reranking (32K context)
"""

import json
import numpy as np
import asyncio
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
import hashlib
import re

try:
    from pymilvus import (
        connections, FieldSchema, CollectionSchema, DataType, Collection,
        utility, MilvusClient, AnnSearchRequest, RRFRanker
    )
    MILVUS_AVAILABLE = True
except ImportError:
    MILVUS_AVAILABLE = False
    print("⚠️ Milvus not available. Install with: pip install pymilvus>=2.3.0")

try:
    import voyageai
    VOYAGE_AVAILABLE = True
except ImportError:
    VOYAGE_AVAILABLE = False
    print("⚠️ Voyage AI not available. Install with: pip install voyageai>=0.2.0")

from .normalizer import AtomicUnit


@dataclass
class EmbeddedChunk:
    """Represents a contextualized chunk with embedding."""
    chunk_id: str
    doc_id: str
    chunk_index: int
    content: str
    title: str
    doc_type: str
    embedding: List[float]
    sparse_vector: Optional[Dict[int, float]] = None
    metadata: Dict[str, Any] = None
    created_at: str = ""


@dataclass
class SearchResult:
    """Search result with relevance scores."""
    chunk_id: str
    content: str
    title: str
    doc_type: str
    dense_score: float
    sparse_score: float = 0.0
    hybrid_score: float = 0.0
    rerank_score: float = 0.0
    metadata: Dict[str, Any] = None


class MaxPerformanceEmbedder:
    """
    Max-performance document embedding system with production optimizations.

    Features:
    - Voyage Context-3 contextualized embeddings (2048-dim, 32K context)
    - Milvus HNSW index with optimized parameters (M=64, efConstruction=500)
    - BM25 hybrid search for exact token matching
    - Voyage Rerank-2.5 second-stage reranking
    - Section-aware chunking without overlap
    """

    def __init__(self,
                 collection_name: str = "dopemux_docs_context3_2048",  # New collection for 2048D
                 milvus_host: str = "localhost",
                 milvus_port: int = 19530,
                 milvus_uri: Optional[str] = None,  # File-based URI for Milvus Lite
                 embedding_dim: int = 2048,  # voyage-context-3 dimension
                 chunk_size: int = 1000,
                 chunk_overlap: int = 0):  # No overlap for contextualized embeddings

        if not VOYAGE_AVAILABLE:
            raise ImportError("Voyage AI not available. Install with: pip install voyageai>=0.2.0")
        if not MILVUS_AVAILABLE:
            raise ImportError("Milvus not available. Install with: pip install pymilvus>=2.3.0")

        self.collection_name = collection_name
        self.milvus_host = milvus_host
        self.milvus_port = milvus_port
        self.milvus_uri = milvus_uri  # File-based URI for Milvus Lite
        self.embedding_dim = embedding_dim
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Initialize Voyage AI client
        self.voyage_client = voyageai.Client()

        # Initialize Milvus
        self._setup_milvus()

        # Reranker settings
        self.rerank_model = "rerank-2.5"
        self.rerank_context_limit = 32000

        print(f"✅ Max-Performance Embedder initialized:")
        print(f"   📐 Embedding: voyage-context-3 ({embedding_dim}D)")
        print(f"   🗄️ Vector DB: Milvus HNSW + BM25 hybrid")
        print(f"   🔄 Reranker: voyage-rerank-2.5 (32K context)")

    def _setup_milvus(self):
        """Setup Milvus connection and collection with production schema (supports Lite and server)."""
        try:
            if self.milvus_uri:
                # Use Milvus Lite with file-based storage
                from pymilvus import MilvusClient
                self.milvus_client = MilvusClient(self.milvus_uri)
                print(f"✅ Connected to Milvus Lite at {self.milvus_uri}")
                self._setup_milvus_lite_collection()
            else:
                # Use traditional server-based Milvus
                connections.connect("default", host=self.milvus_host, port=self.milvus_port)
                print(f"✅ Connected to Milvus server at {self.milvus_host}:{self.milvus_port}")
                self._setup_milvus_server_collection()

        except Exception as e:
            print(f"❌ Error setting up Milvus: {e}")
            raise e

    def _setup_milvus_lite_collection(self):
        """Setup collection for Milvus Lite."""
        # Check if collection exists
        collections = self.milvus_client.list_collections()
        if self.collection_name not in collections:
            # Create collection with 2048D vectors for voyage-context-3
            self.milvus_client.create_collection(
                collection_name=self.collection_name,
                dimension=self.embedding_dim,
                auto_id=False
            )
            print(f"✅ Created Milvus Lite collection: {self.collection_name} ({self.embedding_dim}D)")
        else:
            print(f"✅ Using existing Milvus Lite collection: {self.collection_name}")

    def _setup_milvus_server_collection(self):
        """Setup collection for traditional Milvus server."""
        # Original server-based collection setup with dense + sparse vectors
        fields = [
            FieldSchema(
                name="id",
                dtype=DataType.INT64,
                is_primary=True,
                auto_id=True
            ),
            FieldSchema(
                name="chunk_id",
                dtype=DataType.VARCHAR,
                max_length=255
            ),
            FieldSchema(
                name="doc_id",
                dtype=DataType.VARCHAR,
                max_length=255
            ),
            FieldSchema(
                name="chunk_index",
                dtype=DataType.INT64
            ),
            FieldSchema(
                name="content",
                dtype=DataType.VARCHAR,
                max_length=65535
            ),
            FieldSchema(
                name="title",
                dtype=DataType.VARCHAR,
                max_length=512
            ),
            FieldSchema(
                name="doc_type",
                dtype=DataType.VARCHAR,
                max_length=64
            ),
            FieldSchema(
                name="dense_vector",
                dtype=DataType.FLOAT_VECTOR,
                dim=self.embedding_dim
            ),
            FieldSchema(
                name="sparse_vector",
                dtype=DataType.SPARSE_FLOAT_VECTOR
            ),
            FieldSchema(
                name="text_for_bm25",
                dtype=DataType.VARCHAR,
                max_length=65535,
                enable_analyzer=True,
                analyzer_params={"tokenizer": "standard"},
                enable_match=True
            ),
            FieldSchema(
                name="metadata",
                dtype=DataType.JSON
            ),
            FieldSchema(
                name="created_at",
                dtype=DataType.VARCHAR,
                max_length=64
            )
        ]

        schema = CollectionSchema(
            fields,
            description="Max-performance document collection with dense+sparse vectors"
        )

        # Create or get collection
        if utility.has_collection(self.collection_name):
            print(f"📚 Using existing collection: {self.collection_name}")
            self.collection = Collection(self.collection_name)
        else:
            print(f"📚 Creating new collection: {self.collection_name}")
            self.collection = Collection(self.collection_name, schema)
            self._create_indexes()

    def _create_indexes(self):
        """Create production-optimized indexes."""
        print("🔧 Creating production indexes...")

        try:
            # HNSW index on dense vectors (max-quality settings)
            dense_index_params = {
                "metric_type": "COSINE",
                "index_type": "HNSW",
                "params": {
                    "M": 64,                    # Higher M = denser graph = higher recall
                    "efConstruction": 500       # Higher = better graph quality
                }
            }

            self.collection.create_index(
                field_name="dense_vector",
                index_params=dense_index_params
            )
            print("✅ Created HNSW index on dense_vector (M=64, efConstruction=500)")

        except Exception as e:
            print(f"⚠️ Dense index creation issue: {e}")

        try:
            # Sparse index for BM25 (only if supported)
            sparse_index_params = {
                "index_type": "SPARSE_INVERTED_INDEX",
                "metric_type": "IP"
            }

            self.collection.create_index(
                field_name="sparse_vector",
                index_params=sparse_index_params
            )
            print("✅ Created sparse inverted index for BM25")

        except Exception as e:
            print(f"⚠️ Sparse index creation issue (continuing without BM25): {e}")

        # Load collection
        try:
            self.collection.load()
            print("✅ Collection loaded and ready")
        except Exception as e:
            print(f"⚠️ Collection load issue: {e}")
            # Try creating a simpler collection schema
            self._create_simple_collection()

    async def process_atomic_units(self, atomic_units: List[AtomicUnit]) -> Dict[str, int]:
        """
        Process atomic units with contextualized embeddings.

        Groups units by document for contextualized embedding, then indexes
        all chunks with dense + sparse vectors.
        """
        print(f"🚀 Processing {len(atomic_units)} atomic units with max-performance stack...")

        # Group units by document for contextualized embedding
        doc_groups = self._group_by_document(atomic_units)
        print(f"📄 Grouped into {len(doc_groups)} documents")

        all_chunks = []
        processed_docs = 0

        for doc_path, units in doc_groups.items():
            try:
                # Create section-aware chunks without overlap
                chunks = self._create_contextualized_chunks(units, doc_path)

                # Get contextualized embeddings for entire document
                embedded_chunks = await self._embed_document_chunks(chunks)

                all_chunks.extend(embedded_chunks)
                processed_docs += 1

                if processed_docs % 10 == 0:
                    print(f"📊 Processed {processed_docs}/{len(doc_groups)} documents...")

            except Exception as e:
                print(f"⚠️ Error processing document {doc_path}: {e}")
                continue

        # Insert all chunks into Milvus
        print(f"💾 Indexing {len(all_chunks)} chunks in Milvus...")
        await self._insert_chunks(all_chunks)

        return {
            "documents_processed": processed_docs,
            "chunks_created": len(all_chunks),
            "embedding_dimension": self.embedding_dim
        }

    def _group_by_document(self, atomic_units: List[AtomicUnit]) -> Dict[str, List[AtomicUnit]]:
        """Group atomic units by source document."""
        doc_groups = {}
        for unit in atomic_units:
            if unit.source_file not in doc_groups:
                doc_groups[unit.source_file] = []
            doc_groups[unit.source_file].append(unit)
        return doc_groups

    def _create_contextualized_chunks(self, units: List[AtomicUnit], doc_path: str) -> List[Dict[str, Any]]:
        """
        Create section-aware chunks without overlap for contextualized embeddings.

        Voyage Context-3 explicitly recommends no overlap for contextualized embeddings
        since the model sees global document context.
        """
        chunks = []

        # Sort units by line numbers to maintain document order
        sorted_units = sorted(units, key=lambda u: u.line_start)

        current_chunk = ""
        current_metadata = {}
        chunk_index = 0

        for unit in sorted_units:
            unit_content = f"{unit.title or ''}\n{unit.content}".strip()

            # If adding this unit would exceed chunk size, start new chunk
            if current_chunk and len(current_chunk) + len(unit_content) > self.chunk_size:
                if current_chunk.strip():
                    chunks.append({
                        "chunk_id": f"{Path(doc_path).stem}-{chunk_index}",
                        "doc_id": doc_path,
                        "chunk_index": chunk_index,
                        "content": current_chunk.strip(),
                        "title": current_metadata.get("title", ""),
                        "doc_type": current_metadata.get("doc_type", "Document"),
                        "metadata": current_metadata
                    })
                    chunk_index += 1

                current_chunk = unit_content
                current_metadata = {
                    "title": unit.title or f"Section {chunk_index}",
                    "doc_type": unit.doc_type,
                    "tags": unit.tags,
                    "entity_type": unit.entity_type
                }
            else:
                if current_chunk:
                    current_chunk += f"\n\n{unit_content}"
                else:
                    current_chunk = unit_content
                    current_metadata = {
                        "title": unit.title or f"Section {chunk_index}",
                        "doc_type": unit.doc_type,
                        "tags": unit.tags,
                        "entity_type": unit.entity_type
                    }

        # Add final chunk
        if current_chunk.strip():
            chunks.append({
                "chunk_id": f"{Path(doc_path).stem}-{chunk_index}",
                "doc_id": doc_path,
                "chunk_index": chunk_index,
                "content": current_chunk.strip(),
                "title": current_metadata.get("title", ""),
                "doc_type": current_metadata.get("doc_type", "Document"),
                "metadata": current_metadata
            })

        return chunks

    async def _embed_document_chunks(self, chunks: List[Dict[str, Any]]) -> List[EmbeddedChunk]:
        """
        Generate contextualized embeddings for document chunks.

        Uses Voyage Context-3 contextualized embeddings endpoint for max quality.
        """
        if not chunks:
            return []

        try:
            # Prepare chunk texts for contextualized embedding
            chunk_texts = [chunk["content"] for chunk in chunks]

            # Get contextualized embeddings using voyage-context-3
            # Pass chunks as list - each chunk gets context from surrounding chunks
            response = await asyncio.to_thread(
                self.voyage_client.contextualized_embed,
                inputs=[chunk_texts],  # Single document as list of chunks
                model="voyage-context-3",
                input_type="document",
                output_dimension=2048  # Get 2048-dimensional embeddings
            )

            # Get embeddings for each chunk (contextualized with surrounding chunks)
            chunk_embeddings = response.results[0].embeddings

            # Create embedded chunks - each gets its own contextualized embedding
            embedded_chunks = []
            for i, chunk in enumerate(chunks):
                # Generate BM25 sparse vector for this specific chunk
                sparse_vector = self._generate_bm25_vector(chunk["content"])

                embedded_chunk = EmbeddedChunk(
                    chunk_id=chunk["chunk_id"],
                    doc_id=chunk["doc_id"],
                    chunk_index=chunk["chunk_index"],
                    content=chunk["content"],
                    title=chunk["title"],
                    doc_type=chunk["doc_type"],
                    embedding=chunk_embeddings[i],  # Each chunk gets its contextualized embedding
                    sparse_vector=sparse_vector,
                    metadata=chunk["metadata"],
                    created_at=time.strftime("%Y-%m-%d %H:%M:%S")
                )
                embedded_chunks.append(embedded_chunk)

            return embedded_chunks

        except Exception as e:
            print(f"⚠️ Error embedding chunks: {e}")
            return []

    def _generate_bm25_vector(self, text: str) -> Dict[int, float]:
        """
        Generate BM25 sparse vector for hybrid search.

        This is a simplified implementation - in production, use Milvus BM25 function.
        """
        # Simple tokenization and term frequency
        tokens = re.findall(r'\b\w+\b', text.lower())
        term_freq = {}

        for token in tokens:
            term_freq[token] = term_freq.get(token, 0) + 1

        # Convert to sparse vector format (simplified)
        # In production, use Milvus BM25 function that maps terms to indices
        sparse_vector = {}
        for i, (term, freq) in enumerate(term_freq.items()):
            if i < 1000:  # Limit vocabulary size
                term_hash = hash(term) % 10000  # Simple hash to index
                sparse_vector[term_hash] = float(freq)

        return sparse_vector

    async def _insert_chunks(self, chunks: List[EmbeddedChunk]):
        """Insert embedded chunks into Milvus collection."""
        if not chunks:
            return

        # Prepare data for insertion
        data = []
        for chunk in chunks:
            # Ensure sparse vector is properly formatted
            sparse_vector = chunk.sparse_vector
            if sparse_vector is None or len(sparse_vector) == 0:
                sparse_vector = {0: 0.0}  # Default sparse vector

            data.append({
                "chunk_id": str(chunk.chunk_id),
                "doc_id": str(chunk.doc_id),
                "chunk_index": int(chunk.chunk_index),
                "content": str(chunk.content),
                "title": str(chunk.title or ""),
                "doc_type": str(chunk.doc_type),
                "dense_vector": list(chunk.embedding),  # Ensure it's a list
                "sparse_vector": sparse_vector,
                "text_for_bm25": str(chunk.content),
                "metadata": chunk.metadata or {},
                "created_at": str(chunk.created_at)
            })

        # Insert in batches
        batch_size = 100
        total_inserted = 0

        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            try:
                if hasattr(self, 'milvus_client') and self.milvus_client:
                    # Use Milvus Lite client
                    batch_for_lite = []
                    for item in batch:
                        # Prepare simplified data format for Milvus Lite
                        batch_for_lite.append({
                            "id": item["chunk_id"],
                            "vector": item["dense_vector"],
                            "content": item["content"],
                            "title": item["title"],
                            "doc_type": item["doc_type"]
                        })
                    result = self.milvus_client.insert(
                        collection_name=self.collection_name,
                        data=batch_for_lite
                    )
                elif hasattr(self, 'collection') and self.collection:
                    # Use server-based Milvus
                    result = self.collection.insert(batch)
                else:
                    raise Exception("No Milvus client or collection available")

                total_inserted += len(batch)

                if total_inserted % 500 == 0:
                    print(f"💾 Inserted {total_inserted}/{len(data)} chunks...")

            except Exception as e:
                print(f"⚠️ Error inserting batch: {e}")
                continue

        # Flush to ensure data is persisted (only for server-based Milvus)
        if hasattr(self, 'collection') and self.collection:
            self.collection.flush()
        elif hasattr(self, 'milvus_client') and self.milvus_client:
            # Milvus Lite auto-flushes, no explicit flush needed
            pass

        print(f"✅ Successfully inserted {total_inserted} chunks")

    async def hybrid_search(self,
                          query: str,
                          top_k: int = 60,
                          dense_weight: float = 0.7,
                          sparse_weight: float = 0.3,
                          use_reranker: bool = True,
                          rerank_top_n: int = 200) -> List[SearchResult]:
        """
        Max-performance hybrid search with dense + BM25 + reranking.

        Pipeline:
        1. Dense search (HNSW) → top 200
        2. BM25 search → top 200
        3. Hybrid fusion (RRF) → top 200-300
        4. Rerank with voyage-rerank-2.5 → final top_k
        """
        try:
            # Step 1: Get query embedding (use regular embed for queries)
            query_response = await asyncio.to_thread(
                self.voyage_client.embed,
                texts=[query],  # Single query string in list
                model="voyage-3",  # Use voyage-3 for query embeddings (same vector space)
                input_type="query",
                output_dimension=2048  # Match contextualized embedding dimensions
            )
            query_vector = query_response.embeddings[0]

            # Step 2: Dense search with optimized parameters
            dense_search_params = {
                "metric_type": "COSINE",
                "params": {"ef": max(rerank_top_n * 4, top_k * 4)}  # ef ≥ 4×topK for stable recall
            }

            dense_request = AnnSearchRequest(
                data=[query_vector],
                anns_field="dense_vector",
                param=dense_search_params,
                limit=rerank_top_n,
                expr=None
            )

            # Step 3: BM25 search (simplified - in production use Milvus BM25 function)
            sparse_vector = self._generate_bm25_vector(query)
            sparse_request = AnnSearchRequest(
                data=[sparse_vector],
                anns_field="sparse_vector",
                param={"metric_type": "IP"},
                limit=rerank_top_n,
                expr=None
            )

            # Step 4: Hybrid search with RRF ranking
            hybrid_results = self.collection.hybrid_search(
                reqs=[dense_request, sparse_request],
                rerank=RRFRanker(),
                limit=rerank_top_n,
                output_fields=["chunk_id", "content", "title", "doc_type", "metadata"]
            )

            # Step 5: Process results
            search_results = []
            for hit in hybrid_results[0]:
                result = SearchResult(
                    chunk_id=hit.entity.get("chunk_id"),
                    content=hit.entity.get("content"),
                    title=hit.entity.get("title"),
                    doc_type=hit.entity.get("doc_type"),
                    dense_score=0.0,  # Would need separate dense search to get
                    sparse_score=0.0,  # Would need separate sparse search to get
                    hybrid_score=hit.score,
                    metadata=hit.entity.get("metadata", {})
                )
                search_results.append(result)

            # Step 6: Rerank with Voyage Rerank-2.5
            if use_reranker and len(search_results) > top_k:
                search_results = await self._rerank_results(query, search_results, top_k)

            return search_results[:top_k]

        except Exception as e:
            print(f"❌ Error in hybrid search: {e}")
            return []

    async def _rerank_results(self,
                            query: str,
                            results: List[SearchResult],
                            top_k: int) -> List[SearchResult]:
        """
        Rerank results using Voyage Rerank-2.5 with 32K context.
        """
        try:
            # Prepare documents for reranking
            documents = []
            for result in results:
                # Combine content with metadata for richer context
                doc_text = f"Title: {result.title}\nType: {result.doc_type}\nContent: {result.content}"

                # Truncate to fit within 32K context limit
                if len(doc_text) > self.rerank_context_limit:
                    doc_text = doc_text[:self.rerank_context_limit]

                documents.append(doc_text)

            # Call reranker
            rerank_response = await asyncio.to_thread(
                self.voyage_client.rerank,
                query=query,
                documents=documents,
                model=self.rerank_model,
                top_k=top_k
            )

            # Update results with rerank scores
            reranked_results = []
            for result in rerank_response.results:
                original_result = results[result.index]
                original_result.rerank_score = result.relevance_score
                reranked_results.append(original_result)

            print(f"🔄 Reranked {len(results)} → {len(reranked_results)} results")
            return reranked_results

        except Exception as e:
            print(f"⚠️ Error in reranking: {e}")
            # Return original results if reranking fails
            return results[:top_k]

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        try:
            stats = self.collection.describe()
            count = self.collection.num_entities

            return {
                "collection_name": self.collection_name,
                "total_entities": count,
                "embedding_dimension": self.embedding_dim,
                "schema": str(stats)
            }
        except Exception as e:
            return {"error": str(e)}


# Integration with existing pipeline
async def upgrade_embeddings_to_max_performance(atomic_units: List[AtomicUnit],
                                               output_dir: Path = Path("build")):
    """
    Upgrade existing atomic units to max-performance embedding system.

    This replaces the basic embedder with the production-ready stack.
    """
    print("🚀 Upgrading to max-performance embedding stack...")

    embedder = MaxPerformanceEmbedder(
        collection_name="dopemux_docs_max_perf",
        embedding_dim=2048  # Max quality settings
    )

    results = await embedder.process_atomic_units(atomic_units)

    # Save embedder stats
    from pathlib import Path
    output_path = Path(output_dir)
    stats_file = output_path / "embedding_stats.json"
    with open(stats_file, 'w') as f:
        json.dump({
            "embedder_type": "max_performance",
            "model": "voyage-context-3",
            "embedding_dimension": 2048,
            "reranker": "voyage-rerank-2.5",
            "index_type": "HNSW_COSINE",
            "hybrid_search": True,
            **results
        }, f, indent=2)

    print(f"✅ Max-performance embedding complete: {results}")
    return embedder, results