"""Vector store implementation using ChromaDB for conversation indexing."""

import json
import logging
import uuid
from typing import Any, Optional
from datetime import datetime
from dataclasses import dataclass

try:
    import chromadb
    from chromadb.config import Settings
    from chromadb.utils import embedding_functions
except ImportError:
    chromadb = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

from chatx.schemas.validator import validate_data

logger = logging.getLogger(__name__)


@dataclass
class IndexingConfig:
    """Configuration for vector indexing."""
    collection_prefix: str = "chatx"
    embedding_model: str = "all-MiniLM-L6-v2"  # Compact, fast model
    chunk_size: int = 512  # Max tokens per embedding
    persist_directory: str = "./.chroma_db"
    distance_metric: str = "cosine"  # cosine, l2, ip
    batch_size: int = 100  # Embedding batch size
    

@dataclass
class SearchResult:
    """Search result from vector store."""
    chunk_id: str
    score: float
    text: str
    metadata: dict[str, Any]
    message_ids: list[str]


class ChromaDBVectorStore:
    """Production ChromaDB vector store for conversation indexing."""
    
    def __init__(self, config: Optional[IndexingConfig] = None):
        """Initialize ChromaDB vector store.
        
        Args:
            config: Indexing configuration
        """
        if chromadb is None:
            raise ImportError("chromadb not available. Install with: pip install chromadb")
        
        self.config = config or IndexingConfig()
        self.client: Optional[chromadb.Client] = None
        self.collections: dict[str, chromadb.Collection] = {}
        
        # Initialize embedding function
        if SentenceTransformer is not None:
            self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=self.config.embedding_model
            )
        else:
            # Fallback to default embedding function
            self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
        
        logger.info(f"Initialized ChromaDB store with model: {self.config.embedding_model}")
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def connect(self) -> None:
        """Connect to ChromaDB."""
        try:
            # Create persistent client
            self.client = chromadb.PersistentClient(
                path=self.config.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,  # Disable telemetry for privacy
                    allow_reset=False,  # Prevent accidental data loss
                )
            )
            logger.info(f"Connected to ChromaDB at: {self.config.persist_directory}")
            
        except Exception as e:
            logger.error(f"Failed to connect to ChromaDB: {e}")
            raise
    
    def close(self) -> None:
        """Close ChromaDB connection."""
        if self.client:
            # ChromaDB handles cleanup automatically
            self.client = None
            self.collections.clear()
            logger.info("Closed ChromaDB connection")
    
    def _get_collection_name(self, contact: str) -> str:
        """Generate collection name for contact."""
        # Sanitize contact for collection name
        sanitized = contact.replace("@", "_at_").replace("+", "_plus_").replace(" ", "_")
        return f"{self.config.collection_prefix}_{sanitized}"
    
    def create_collection(self, contact: str, overwrite: bool = False) -> chromadb.Collection:
        """Create or get collection for contact.
        
        Args:
            contact: Contact identifier
            overwrite: Whether to overwrite existing collection
            
        Returns:
            ChromaDB collection
        """
        if not self.client:
            raise RuntimeError("Not connected to ChromaDB")
        
        collection_name = self._get_collection_name(contact)
        
        if overwrite and collection_name in self.collections:
            try:
                self.client.delete_collection(collection_name)
                logger.info(f"Deleted existing collection: {collection_name}")
            except Exception as e:
                logger.warning(f"Could not delete collection {collection_name}: {e}")
        
        try:
            collection = self.client.get_or_create_collection(
                name=collection_name,
                embedding_function=self.embedding_function,
                metadata={
                    "contact": contact,
                    "created_at": datetime.now().isoformat(),
                    "distance_metric": self.config.distance_metric,
                }
            )
            self.collections[collection_name] = collection
            logger.info(f"Created/retrieved collection: {collection_name}")
            return collection
            
        except Exception as e:
            logger.error(f"Failed to create collection {collection_name}: {e}")
            raise
    
    def _prepare_chunk_for_indexing(self, chunk: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
        """Prepare chunk data for indexing.
        
        Args:
            chunk: Chunk dictionary
            
        Returns:
            Tuple of (chunk_id, text, metadata)
        """
        chunk_id = chunk.get("chunk_id", str(uuid.uuid4()))
        text = chunk.get("text", "")
        
        # Extract metadata for filtering
        meta = chunk.get("meta", {})
        
        # Build search metadata (excluding large fields)
        search_metadata = {
            "conv_id": chunk.get("conv_id", ""),
            "platform": meta.get("platform", ""),
            "date_start": meta.get("date_start", ""),
            "date_end": meta.get("date_end", ""),
            "message_count": len(meta.get("message_ids", [])),
            "char_count": meta.get("char_count", len(text)),
            "token_estimate": meta.get("token_estimate", 0),
            "window_method": meta.get("window", {}).get("method", ""),
            "window_index": meta.get("window", {}).get("index", 0),
        }
        
        # Add labels if present
        if "labels_coarse" in meta:
            search_metadata["labels_coarse"] = meta["labels_coarse"]
        
        # Add redaction info if present
        provenance = chunk.get("provenance", {})
        if "redaction" in provenance:
            search_metadata["redaction_coverage"] = provenance["redaction"]["coverage"]
            search_metadata["redacted"] = True
        else:
            search_metadata["redacted"] = False
        
        return chunk_id, text, search_metadata
    
    def index_chunks(
        self,
        chunks: list[dict[str, Any]],
        contact: str,
        batch_size: Optional[int] = None
    ) -> dict[str, Any]:
        """Index conversation chunks for search.
        
        Args:
            chunks: List of chunk dictionaries
            contact: Contact identifier
            batch_size: Batch size for indexing (uses config default if None)
            
        Returns:
            Indexing statistics
        """
        if not chunks:
            return {"indexed": 0, "errors": 0, "collection": ""}
        
        batch_size = batch_size or self.config.batch_size
        collection = self.create_collection(contact)
        
        logger.info(f"Indexing {len(chunks)} chunks for contact: {contact}")
        
        indexed_count = 0
        error_count = 0
        
        # Process in batches
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            
            try:
                # Prepare batch data
                ids = []
                texts = []
                metadatas = []
                
                for chunk in batch:
                    try:
                        chunk_id, text, metadata = self._prepare_chunk_for_indexing(chunk)
                        
                        # Skip empty texts
                        if not text.strip():
                            continue
                        
                        ids.append(chunk_id)
                        texts.append(text)
                        metadatas.append(metadata)
                        
                    except Exception as e:
                        logger.error(f"Error preparing chunk {chunk.get('chunk_id', 'unknown')}: {e}")
                        error_count += 1
                
                # Add to collection
                if ids:
                    collection.add(
                        ids=ids,
                        documents=texts,
                        metadatas=metadatas
                    )
                    indexed_count += len(ids)
                    logger.debug(f"Indexed batch {i//batch_size + 1}: {len(ids)} chunks")
                
            except Exception as e:
                logger.error(f"Error indexing batch {i//batch_size + 1}: {e}")
                error_count += len(batch)
        
        stats = {
            "indexed": indexed_count,
            "errors": error_count,
            "collection": collection.name,
            "total_in_collection": collection.count(),
        }
        
        logger.info(f"Indexing complete: {stats}")
        return stats
    
    def search(
        self,
        query: str,
        contact: str,
        k: int = 10,
        filters: Optional[dict[str, Any]] = None
    ) -> list[SearchResult]:
        """Search for relevant chunks.
        
        Args:
            query: Search query text
            contact: Contact identifier  
            k: Number of results to return
            filters: Optional metadata filters
            
        Returns:
            List of search results
        """
        collection_name = self._get_collection_name(contact)
        
        if collection_name not in self.collections:
            # Try to get existing collection
            try:
                collection = self.client.get_collection(collection_name)
                self.collections[collection_name] = collection
            except Exception:
                logger.error(f"Collection not found for contact: {contact}")
                return []
        
        collection = self.collections[collection_name]
        
        try:
            # Build where clause from filters
            where_clause = {}
            if filters:
                # Convert filters to ChromaDB where clause format
                for key, value in filters.items():
                    if isinstance(value, list):
                        # Handle array filters (e.g., labels)
                        if value:  # Only add if non-empty
                            where_clause[key] = {"$in": value}
                    elif value is not None:
                        where_clause[key] = value
            
            # Perform search
            results = collection.query(
                query_texts=[query],
                n_results=k,
                where=where_clause if where_clause else None
            )
            
            # Convert to SearchResult objects
            search_results = []
            if results["ids"] and results["ids"][0]:  # ChromaDB returns nested lists
                for i in range(len(results["ids"][0])):
                    result = SearchResult(
                        chunk_id=results["ids"][0][i],
                        score=1.0 - results["distances"][0][i],  # Convert distance to similarity
                        text=results["documents"][0][i],
                        metadata=results["metadatas"][0][i] or {},
                        message_ids=results["metadatas"][0][i].get("message_ids", [])
                    )
                    search_results.append(result)
            
            logger.debug(f"Search returned {len(search_results)} results for query: {query[:50]}...")
            return search_results
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    def update_chunk_metadata(
        self,
        contact: str,
        chunk_id: str,
        metadata_updates: dict[str, Any]
    ) -> bool:
        """Update metadata for a specific chunk.
        
        Args:
            contact: Contact identifier
            chunk_id: Chunk identifier
            metadata_updates: Metadata fields to update
            
        Returns:
            True if successful, False otherwise
        """
        collection_name = self._get_collection_name(contact)
        
        if collection_name not in self.collections:
            try:
                collection = self.client.get_collection(collection_name)
                self.collections[collection_name] = collection
            except Exception:
                logger.error(f"Collection not found for contact: {contact}")
                return False
        
        collection = self.collections[collection_name]
        
        try:
            # Get current metadata
            result = collection.get(ids=[chunk_id], include=["metadatas"])
            if not result["ids"]:
                logger.error(f"Chunk not found: {chunk_id}")
                return False
            
            # Update metadata
            current_metadata = result["metadatas"][0] or {}
            current_metadata.update(metadata_updates)
            
            # Update in collection
            collection.update(
                ids=[chunk_id],
                metadatas=[current_metadata]
            )
            
            logger.debug(f"Updated metadata for chunk: {chunk_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating chunk metadata: {e}")
            return False
    
    def get_collection_stats(self, contact: str) -> dict[str, Any]:
        """Get statistics for a collection.
        
        Args:
            contact: Contact identifier
            
        Returns:
            Collection statistics
        """
        collection_name = self._get_collection_name(contact)
        
        if collection_name not in self.collections:
            try:
                collection = self.client.get_collection(collection_name)
                self.collections[collection_name] = collection
            except Exception:
                return {"exists": False}
        
        collection = self.collections[collection_name]
        
        try:
            count = collection.count()
            metadata = collection.metadata
            
            # Sample some entries to get metadata stats
            sample_size = min(100, count)
            if count > 0:
                sample = collection.get(limit=sample_size, include=["metadatas"])
                
                # Analyze metadata
                platforms = set()
                date_range = {"start": None, "end": None}
                redacted_count = 0
                
                for meta in sample["metadatas"]:
                    if meta:
                        platforms.add(meta.get("platform", "unknown"))
                        
                        if meta.get("redacted"):
                            redacted_count += 1
                        
                        # Track date range
                        date_start = meta.get("date_start")
                        if date_start:
                            if not date_range["start"] or date_start < date_range["start"]:
                                date_range["start"] = date_start
                        
                        date_end = meta.get("date_end")
                        if date_end:
                            if not date_range["end"] or date_end > date_range["end"]:
                                date_range["end"] = date_end
                
                return {
                    "exists": True,
                    "total_chunks": count,
                    "platforms": list(platforms),
                    "date_range": date_range,
                    "redacted_percentage": (redacted_count / sample_size) * 100,
                    "collection_metadata": metadata,
                    "sample_size": sample_size,
                }
            else:
                return {
                    "exists": True,
                    "total_chunks": 0,
                    "collection_metadata": metadata,
                }
                
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {"exists": False, "error": str(e)}
    
    def list_collections(self) -> list[dict[str, Any]]:
        """List all collections.
        
        Returns:
            List of collection information
        """
        if not self.client:
            raise RuntimeError("Not connected to ChromaDB")
        
        try:
            collections = self.client.list_collections()
            
            result = []
            for collection in collections:
                # Extract contact from collection name
                if collection.name.startswith(self.config.collection_prefix + "_"):
                    contact = collection.name[len(self.config.collection_prefix) + 1:]
                    contact = contact.replace("_at_", "@").replace("_plus_", "+").replace("_", " ")
                    
                    result.append({
                        "collection_name": collection.name,
                        "contact": contact,
                        "count": collection.count(),
                        "metadata": collection.metadata,
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"Error listing collections: {e}")
            return []
    
    def delete_collection(self, contact: str) -> bool:
        """Delete collection for contact.
        
        Args:
            contact: Contact identifier
            
        Returns:
            True if successful, False otherwise
        """
        collection_name = self._get_collection_name(contact)
        
        try:
            self.client.delete_collection(collection_name)
            if collection_name in self.collections:
                del self.collections[collection_name]
            
            logger.info(f"Deleted collection: {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting collection {collection_name}: {e}")
            return False
