"""Multi-vector ChromaDB implementation for psychology-aware forensic chat analysis."""

import json
import logging
import uuid
import numpy as np
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, Set
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

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

from chatx.indexing.vector_store import ChromaDBVectorStore, SearchResult
from chatx.schemas.validator import validate_data

logger = logging.getLogger(__name__)


class VectorSpace(Enum):
    """Vector embedding spaces for multi-dimensional indexing."""
    SEMANTIC = "semantic"      # Semantic content similarity
    PSYCHOLOGICAL = "psychological"  # Emotional/psychological patterns
    TEMPORAL = "temporal"      # Conversation flow and timing patterns  
    STRUCTURAL = "structural"  # Communication patterns and speech acts


@dataclass
class MultiVectorConfig:
    """Configuration for multi-vector indexing with privacy boundaries."""
    collection_prefix: str = "chatx_multi"
    persist_directory: str = "./.chroma_multi_db"
    distance_metric: str = "cosine"
    batch_size: int = 50  # Smaller batches for multi-vector processing
    
    # Vector space configurations
    vector_spaces: Dict[VectorSpace, Dict[str, Any]] = field(default_factory=lambda: {
        VectorSpace.SEMANTIC: {
            "model": "all-MiniLM-L6-v2",
            "dimension": 384,
            "privacy_tier": "both"  # Can use both coarse and fine labels
        },
        VectorSpace.PSYCHOLOGICAL: {
            "model": "all-mpnet-base-v2", 
            "dimension": 768,
            "privacy_tier": "tiered"  # Respects privacy boundaries
        },
        VectorSpace.TEMPORAL: {
            "model": "custom_temporal",
            "dimension": 256,
            "privacy_tier": "local"  # Local processing only
        },
        VectorSpace.STRUCTURAL: {
            "model": "custom_structural", 
            "dimension": 128,
            "privacy_tier": "both"
        }
    })
    
    # Privacy configuration
    enable_cloud_embedding: bool = False  # Disabled by default
    coarse_labels_only_cloud: bool = True  # Only coarse labels to cloud
    fine_labels_local_only: bool = True   # Fine labels stay local
    
    # Performance tuning
    parallel_embeddings: bool = True
    max_workers: int = 4
    cache_embeddings: bool = True
    cache_ttl_hours: int = 24


@dataclass
class MultiVectorSearchResult:
    """Enhanced search result with multi-vector scoring."""
    chunk_id: str
    scores: Dict[VectorSpace, float]  # Score per vector space
    combined_score: float
    text: str
    metadata: Dict[str, Any]
    message_ids: List[str]
    vector_contributions: Dict[VectorSpace, float]  # How much each space contributed
    privacy_tier: str  # "local_only" or "cloud_safe"


class PrivacyGate:
    """Privacy gate for enforcing label visibility boundaries."""
    
    COARSE_LABELS = {
        "stress", "intimacy", "conflict", "support", "planning", "social", 
        "work", "family", "health", "emotion", "communication", "time",
        "attention", "boundaries", "trust", "respect", "care", "growth"
    }
    
    FINE_LABELS_LOCAL_ONLY = {
        "sexuality", "substances", "mental_health_specific", "financial_details",
        "location_specific", "family_conflict", "relationship_issues", 
        "personal_secrets", "vulnerability_specific", "trauma_indicators"
    }
    
    @classmethod
    def filter_labels_for_cloud(cls, labels: List[str]) -> List[str]:
        """Filter labels to only include cloud-safe coarse labels."""
        return [label for label in labels if label in cls.COARSE_LABELS]
    
    @classmethod
    def get_privacy_tier(cls, labels: List[str]) -> str:
        """Determine privacy tier based on labels present."""
        if any(label in cls.FINE_LABELS_LOCAL_ONLY for label in labels):
            return "local_only"
        return "cloud_safe"
    
    @classmethod
    def validate_cloud_payload(cls, chunk: Dict[str, Any]) -> bool:
        """Validate chunk is safe for cloud processing."""
        meta = chunk.get("meta", {})
        labels_coarse = meta.get("labels_coarse", [])
        labels_fine = meta.get("labels_fine_local", [])
        
        # Check no fine labels are present
        if labels_fine:
            logger.warning(f"Fine labels detected in cloud payload: {labels_fine}")
            return False
        
        # Check coarse labels are actually coarse
        for label in labels_coarse:
            if label in cls.FINE_LABELS_LOCAL_ONLY:
                logger.warning(f"Fine label '{label}' found in coarse labels")
                return False
        
        return True


class MultiVectorEmbedder:
    """Multi-vector embedding generator with privacy awareness."""
    
    def __init__(self, config: MultiVectorConfig):
        self.config = config
        self.models = {}
        self.privacy_gate = PrivacyGate()
        self._load_embedding_models()
    
    def _load_embedding_models(self) -> None:
        """Load embedding models for each vector space."""
        if SentenceTransformer is None:
            raise ImportError("sentence-transformers required for multi-vector embeddings")
        
        for space, space_config in self.config.vector_spaces.items():
            model_name = space_config["model"]
            
            if model_name.startswith("custom_"):
                # Custom models handled separately
                logger.info(f"Custom model placeholder for {space.value}: {model_name}")
                self.models[space] = None
            else:
                try:
                    logger.info(f"Loading {space.value} model: {model_name}")
                    self.models[space] = SentenceTransformer(model_name)
                except Exception as e:
                    logger.error(f"Failed to load {space.value} model {model_name}: {e}")
                    self.models[space] = None
    
    def generate_embeddings(
        self, 
        texts: List[str], 
        privacy_tier: str = "local_only"
    ) -> Dict[VectorSpace, List[List[float]]]:
        """Generate embeddings across all vector spaces."""
        results = {}
        
        if self.config.parallel_embeddings and len(texts) > 1:
            # Parallel embedding generation
            with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                futures = {}
                
                for space, model in self.models.items():
                    if model is None:
                        continue
                        
                    space_config = self.config.vector_spaces[space]
                    
                    # Check privacy constraints
                    if privacy_tier == "cloud_safe" and space_config["privacy_tier"] == "local":
                        continue
                    
                    future = executor.submit(self._embed_single_space, model, texts, space)
                    futures[future] = space
                
                for future in as_completed(futures):
                    space = futures[future]
                    try:
                        embeddings = future.result()
                        results[space] = embeddings
                    except Exception as e:
                        logger.error(f"Failed to generate {space.value} embeddings: {e}")
        else:
            # Sequential embedding generation
            for space, model in self.models.items():
                if model is None:
                    continue
                    
                space_config = self.config.vector_spaces[space]
                
                # Check privacy constraints
                if privacy_tier == "cloud_safe" and space_config["privacy_tier"] == "local":
                    continue
                
                try:
                    embeddings = self._embed_single_space(model, texts, space)
                    results[space] = embeddings
                except Exception as e:
                    logger.error(f"Failed to generate {space.value} embeddings: {e}")
        
        return results
    
    def _embed_single_space(
        self, 
        model: SentenceTransformer, 
        texts: List[str], 
        space: VectorSpace
    ) -> List[List[float]]:
        """Generate embeddings for a single vector space."""
        start_time = time.time()
        
        if space == VectorSpace.TEMPORAL:
            # Custom temporal encoding
            embeddings = self._generate_temporal_embeddings(texts)
        elif space == VectorSpace.STRUCTURAL:
            # Custom structural encoding
            embeddings = self._generate_structural_embeddings(texts)
        else:
            # Standard transformer embeddings
            embeddings = model.encode(texts, convert_to_tensor=False)
            embeddings = [emb.tolist() for emb in embeddings]
        
        duration = time.time() - start_time
        logger.debug(f"{space.value} embeddings generated in {duration:.2f}s for {len(texts)} texts")
        
        return embeddings
    
    def _generate_temporal_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate temporal pattern embeddings (custom implementation)."""
        # Placeholder for temporal pattern analysis
        # In production, this would analyze conversation flow patterns,
        # response times, message frequency, etc.
        embeddings = []
        for text in texts:
            # Simple feature extraction for demo
            features = [
                len(text),  # Text length
                text.count('?'),  # Question marks
                text.count('!'),  # Exclamation marks
                text.count('.'),  # Periods
                text.count(','),  # Commas
            ]
            # Pad to 256 dimensions
            features.extend([0.0] * (256 - len(features)))
            embeddings.append(features[:256])
        
        return embeddings
    
    def _generate_structural_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate structural communication pattern embeddings."""
        # Placeholder for structural pattern analysis
        # In production, this would analyze speech acts, turn-taking patterns,
        # communication styles, etc.
        embeddings = []
        for text in texts:
            # Simple structural features for demo
            features = [
                1.0 if text.startswith(("I ", "i ")) else 0.0,  # First person
                1.0 if "you" in text.lower() else 0.0,  # Second person
                1.0 if any(word in text.lower() for word in ["sorry", "apologize"]) else 0.0,
                1.0 if any(word in text.lower() for word in ["thank", "thanks"]) else 0.0,
                len(text.split()),  # Word count
            ]
            # Pad to 128 dimensions
            features.extend([0.0] * (128 - len(features)))
            embeddings.append(features[:128])
        
        return embeddings


class MultiVectorChromaDBStore:
    """Multi-vector ChromaDB store with psychology-aware search."""
    
    def __init__(self, config: Optional[MultiVectorConfig] = None):
        """Initialize multi-vector ChromaDB store."""
        if chromadb is None:
            raise ImportError("chromadb not available. Install with: pip install chromadb")
        
        self.config = config or MultiVectorConfig()
        self.client: Optional[chromadb.Client] = None
        self.collections: Dict[str, Dict[VectorSpace, chromadb.Collection]] = {}
        self.embedder = MultiVectorEmbedder(self.config)
        self.privacy_gate = PrivacyGate()
        
        logger.info("Initialized Multi-Vector ChromaDB store")
    
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
            self.client = chromadb.PersistentClient(
                path=self.config.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=False,
                )
            )
            logger.info(f"Connected to Multi-Vector ChromaDB at: {self.config.persist_directory}")
        except Exception as e:
            logger.error(f"Failed to connect to Multi-Vector ChromaDB: {e}")
            raise
    
    def close(self) -> None:
        """Close ChromaDB connection."""
        if self.client:
            self.client = None
            self.collections.clear()
            logger.info("Closed Multi-Vector ChromaDB connection")
    
    def _get_collection_name(self, contact: str, space: VectorSpace) -> str:
        """Generate collection name for contact and vector space."""
        sanitized = contact.replace("@", "_at_").replace("+", "_plus_").replace(" ", "_")
        return f"{self.config.collection_prefix}_{sanitized}_{space.value}"
    
    def create_collections(
        self, 
        contact: str, 
        overwrite: bool = False
    ) -> Dict[VectorSpace, chromadb.Collection]:
        """Create or get collections for all vector spaces."""
        if not self.client:
            raise RuntimeError("Not connected to ChromaDB")
        
        collections = {}
        
        for space in VectorSpace:
            if self.embedder.models[space] is None:
                logger.warning(f"Skipping {space.value} - model not available")
                continue
            
            collection_name = self._get_collection_name(contact, space)
            
            if overwrite:
                try:
                    self.client.delete_collection(collection_name)
                    logger.info(f"Deleted existing collection: {collection_name}")
                except Exception as e:
                    logger.debug(f"Collection {collection_name} didn't exist: {e}")
            
            try:
                # Create embedding function for this space
                space_config = self.config.vector_spaces[space]
                
                if space_config["model"].startswith("custom_"):
                    # Use default embedding function for custom models
                    embedding_function = embedding_functions.DefaultEmbeddingFunction()
                else:
                    embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                        model_name=space_config["model"]
                    )
                
                collection = self.client.get_or_create_collection(
                    name=collection_name,
                    embedding_function=embedding_function,
                    metadata={
                        "contact": contact,
                        "vector_space": space.value,
                        "created_at": datetime.now().isoformat(),
                        "distance_metric": self.config.distance_metric,
                        "privacy_tier": space_config["privacy_tier"],
                        "dimension": space_config["dimension"],
                    }
                )
                
                collections[space] = collection
                logger.info(f"Created/retrieved collection: {collection_name}")
                
            except Exception as e:
                logger.error(f"Failed to create collection {collection_name}: {e}")
        
        if contact not in self.collections:
            self.collections[contact] = {}
        self.collections[contact].update(collections)
        
        return collections
    
    def index_chunks(
        self,
        chunks: List[Dict[str, Any]],
        contact: str,
        batch_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """Index conversation chunks across all vector spaces."""
        if not chunks:
            return {"indexed": 0, "errors": 0, "collections": {}}
        
        batch_size = batch_size or self.config.batch_size
        collections = self.create_collections(contact)
        
        logger.info(f"Multi-vector indexing {len(chunks)} chunks for contact: {contact}")
        
        total_indexed = 0
        total_errors = 0
        collection_stats = {}
        
        # Process chunks in batches
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            
            try:
                # Prepare batch data
                batch_data = []
                texts = []
                
                for chunk in batch:
                    chunk_id, text, metadata = self._prepare_chunk_for_indexing(chunk)
                    if not text.strip():
                        continue
                    
                    batch_data.append((chunk_id, text, metadata, chunk))
                    texts.append(text)
                
                if not batch_data:
                    continue
                
                # Determine privacy tier for batch
                privacy_tiers = [
                    self.privacy_gate.get_privacy_tier(
                        metadata.get("labels_coarse", []) + metadata.get("labels_fine_local", [])
                    ) for _, _, metadata, _ in batch_data
                ]
                
                # Use most restrictive privacy tier
                batch_privacy_tier = "local_only" if "local_only" in privacy_tiers else "cloud_safe"
                
                # Generate embeddings for all spaces
                all_embeddings = self.embedder.generate_embeddings(texts, batch_privacy_tier)
                
                # Index across vector spaces
                for space, embeddings in all_embeddings.items():
                    if space not in collections:
                        continue
                    
                    collection = collections[space]
                    
                    try:
                        # Prepare data for this vector space
                        ids = [data[0] for data in batch_data]
                        docs = [data[1] for data in batch_data]
                        metas = []
                        
                        for j, (_, _, metadata, original_chunk) in enumerate(batch_data):
                            # Add vector space specific metadata
                            space_metadata = metadata.copy()
                            space_metadata["vector_space"] = space.value
                            space_metadata["privacy_tier"] = batch_privacy_tier
                            
                            # Filter labels based on privacy tier and vector space
                            if space.value == "psychological":
                                # Psychology space gets appropriate labels based on privacy
                                if batch_privacy_tier == "cloud_safe":
                                    space_metadata["labels"] = self.privacy_gate.filter_labels_for_cloud(
                                        metadata.get("labels_coarse", [])
                                    )
                                else:
                                    space_metadata["labels"] = (
                                        metadata.get("labels_coarse", []) + 
                                        metadata.get("labels_fine_local", [])
                                    )
                            
                            metas.append(space_metadata)
                        
                        # Add to collection (ChromaDB will handle embedding if needed)
                        if space.value.startswith("custom_"):
                            # For custom embeddings, we need to add with embeddings
                            collection.add(
                                ids=ids,
                                documents=docs,
                                metadatas=metas,
                                embeddings=embeddings
                            )
                        else:
                            # For standard models, ChromaDB handles embedding
                            collection.add(
                                ids=ids,
                                documents=docs,
                                metadatas=metas
                            )
                        
                        indexed_count = len(ids)
                        total_indexed += indexed_count
                        
                        if space not in collection_stats:
                            collection_stats[space.value] = {"indexed": 0, "errors": 0}
                        collection_stats[space.value]["indexed"] += indexed_count
                        
                        logger.debug(f"Indexed batch {i//batch_size + 1} in {space.value}: {indexed_count} chunks")
                        
                    except Exception as e:
                        logger.error(f"Error indexing batch {i//batch_size + 1} in {space.value}: {e}")
                        error_count = len(batch_data)
                        total_errors += error_count
                        
                        if space not in collection_stats:
                            collection_stats[space.value] = {"indexed": 0, "errors": 0}
                        collection_stats[space.value]["errors"] += error_count
                
            except Exception as e:
                logger.error(f"Error processing batch {i//batch_size + 1}: {e}")
                total_errors += len(batch)
        
        # Calculate final statistics
        final_stats = {
            "total_indexed": total_indexed,
            "total_errors": total_errors,
            "collections": collection_stats,
            "contact": contact,
        }
        
        # Add collection counts
        for space, collection in collections.items():
            try:
                final_stats["collections"][space.value]["total_in_collection"] = collection.count()
            except Exception as e:
                logger.error(f"Failed to get count for {space.value}: {e}")
        
        logger.info(f"Multi-vector indexing complete: {final_stats}")
        return final_stats
    
    def _prepare_chunk_for_indexing(self, chunk: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any]]:
        """Prepare chunk data for multi-vector indexing."""
        chunk_id = chunk.get("chunk_id", str(uuid.uuid4()))
        text = chunk.get("text", "")
        
        # Extract metadata for filtering
        meta = chunk.get("meta", {})
        
        # Build search metadata
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
        
        # Add labels with privacy awareness
        if "labels_coarse" in meta:
            search_metadata["labels_coarse"] = meta["labels_coarse"]
        
        if "labels_fine_local" in meta:
            search_metadata["labels_fine_local"] = meta["labels_fine_local"]
        
        # Add message IDs for citation
        if "message_ids" in meta:
            search_metadata["message_ids"] = meta["message_ids"]
        
        # Add redaction info
        provenance = chunk.get("provenance", {})
        if "redaction" in provenance:
            search_metadata["redaction_coverage"] = provenance["redaction"]["coverage"]
            search_metadata["redacted"] = True
        else:
            search_metadata["redacted"] = False
        
        return chunk_id, text, search_metadata
    
    def search_multi_vector(
        self,
        query: str,
        contact: str,
        k: int = 10,
        vector_weights: Optional[Dict[VectorSpace, float]] = None,
        filters: Optional[Dict[str, Any]] = None,
        require_privacy_tier: Optional[str] = None
    ) -> List[MultiVectorSearchResult]:
        """Perform psychology-aware multi-vector search."""
        if contact not in self.collections:
            logger.error(f"No collections found for contact: {contact}")
            return []
        
        collections = self.collections[contact]
        vector_weights = vector_weights or {space: 1.0 for space in VectorSpace}
        
        # Generate query embeddings
        query_embeddings = self.embedder.generate_embeddings([query])
        
        # Search across vector spaces
        all_results = {}
        
        for space, collection in collections.items():
            if space not in query_embeddings:
                continue
            
            try:
                # Build where clause
                where_clause = {}
                if filters:
                    for key, value in filters.items():
                        if isinstance(value, list):
                            if value:
                                where_clause[key] = {"$in": value}
                        elif value is not None:
                            where_clause[key] = value
                
                # Add privacy tier filter if specified
                if require_privacy_tier:
                    where_clause["privacy_tier"] = require_privacy_tier
                
                # Perform search in this vector space
                results = collection.query(
                    query_texts=[query],
                    n_results=k * 2,  # Get more results for fusion
                    where=where_clause if where_clause else None
                )
                
                if results["ids"] and results["ids"][0]:
                    for i in range(len(results["ids"][0])):
                        chunk_id = results["ids"][0][i]
                        score = 1.0 - results["distances"][0][i]  # Convert distance to similarity
                        
                        if chunk_id not in all_results:
                            all_results[chunk_id] = {
                                "text": results["documents"][0][i],
                                "metadata": results["metadatas"][0][i] or {},
                                "scores": {},
                                "message_ids": results["metadatas"][0][i].get("message_ids", [])
                            }
                        
                        all_results[chunk_id]["scores"][space] = score
                
            except Exception as e:
                logger.error(f"Search error in {space.value}: {e}")
        
        # Combine and rank results
        combined_results = []
        
        for chunk_id, result_data in all_results.items():
            scores = result_data["scores"]
            
            # Calculate weighted combined score
            combined_score = 0.0
            total_weight = 0.0
            vector_contributions = {}
            
            for space, score in scores.items():
                weight = vector_weights.get(space, 1.0)
                contribution = score * weight
                combined_score += contribution
                total_weight += weight
                vector_contributions[space] = contribution
            
            if total_weight > 0:
                combined_score /= total_weight
            
            # Determine privacy tier
            metadata = result_data["metadata"]
            labels_coarse = metadata.get("labels_coarse", [])
            labels_fine = metadata.get("labels_fine_local", [])
            privacy_tier = self.privacy_gate.get_privacy_tier(labels_coarse + labels_fine)
            
            multi_result = MultiVectorSearchResult(
                chunk_id=chunk_id,
                scores=scores,
                combined_score=combined_score,
                text=result_data["text"],
                metadata=metadata,
                message_ids=result_data["message_ids"],
                vector_contributions=vector_contributions,
                privacy_tier=privacy_tier
            )
            
            combined_results.append(multi_result)
        
        # Sort by combined score and limit results
        combined_results.sort(key=lambda x: x.combined_score, reverse=True)
        final_results = combined_results[:k]
        
        logger.debug(f"Multi-vector search returned {len(final_results)} results")
        return final_results
    
    def get_psychology_insights(
        self,
        contact: str,
        time_range: Optional[Tuple[str, str]] = None,
        label_focus: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get psychological insights from indexed conversations."""
        if contact not in self.collections or VectorSpace.PSYCHOLOGICAL not in self.collections[contact]:
            return {"error": "No psychological vectors found for contact"}
        
        collection = self.collections[contact][VectorSpace.PSYCHOLOGICAL]
        
        try:
            # Build filters
            where_clause = {}
            if time_range:
                # Add date range filters
                where_clause["date_start"] = {"$gte": time_range[0]}
                where_clause["date_end"] = {"$lte": time_range[1]}
            
            if label_focus:
                where_clause["labels"] = {"$in": label_focus}
            
            # Get sample of chunks for analysis
            sample_results = collection.get(
                limit=1000,
                where=where_clause if where_clause else None,
                include=["metadatas"]
            )
            
            if not sample_results["ids"]:
                return {"message": "No chunks found for analysis"}
            
            # Analyze psychological patterns
            label_counts = {}
            temporal_patterns = {}
            privacy_distribution = {"local_only": 0, "cloud_safe": 0}
            
            for metadata in sample_results["metadatas"]:
                if not metadata:
                    continue
                
                # Count labels
                for label in metadata.get("labels", []):
                    label_counts[label] = label_counts.get(label, 0) + 1
                
                # Track privacy distribution
                privacy_tier = metadata.get("privacy_tier", "cloud_safe")
                privacy_distribution[privacy_tier] += 1
                
                # Temporal analysis (simplified)
                date_start = metadata.get("date_start", "")
                if date_start:
                    date_key = date_start[:7]  # YYYY-MM
                    if date_key not in temporal_patterns:
                        temporal_patterns[date_key] = {}
                    
                    for label in metadata.get("labels", []):
                        if label not in temporal_patterns[date_key]:
                            temporal_patterns[date_key][label] = 0
                        temporal_patterns[date_key][label] += 1
            
            return {
                "total_chunks": len(sample_results["ids"]),
                "label_distribution": dict(sorted(label_counts.items(), key=lambda x: x[1], reverse=True)),
                "temporal_patterns": temporal_patterns,
                "privacy_distribution": privacy_distribution,
                "top_labels": list(sorted(label_counts.keys(), key=lambda x: label_counts[x], reverse=True))[:10],
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating psychology insights: {e}")
            return {"error": str(e)}


# Backward compatibility wrapper
class EnhancedVectorStore(ChromaDBVectorStore):
    """Enhanced vector store that delegates to multi-vector implementation when needed."""
    
    def __init__(self, config: Optional[Union[Any, MultiVectorConfig]] = None, enable_multi_vector: bool = False):
        """Initialize enhanced vector store with optional multi-vector support."""
        self.enable_multi_vector = enable_multi_vector
        
        if enable_multi_vector:
            if hasattr(config, 'collection_prefix') and not isinstance(config, MultiVectorConfig):
                # Convert to MultiVectorConfig
                multi_config = MultiVectorConfig(
                    collection_prefix=config.collection_prefix,
                    persist_directory=config.persist_directory + "_multi",
                    distance_metric=config.distance_metric,
                    batch_size=config.batch_size
                )
            else:
                multi_config = config or MultiVectorConfig()
            
            self.multi_store = MultiVectorChromaDBStore(multi_config)
            self.config = multi_config
        else:
            # Standard single-vector implementation
            from chatx.indexing.vector_store import IndexingConfig
            single_config = config if hasattr(config, 'collection_prefix') else IndexingConfig()
            super().__init__(single_config)
            self.multi_store = None
    
    def index_chunks(self, chunks: List[Dict[str, Any]], contact: str, **kwargs) -> Dict[str, Any]:
        """Index chunks with multi-vector support if enabled."""
        if self.enable_multi_vector and self.multi_store:
            return self.multi_store.index_chunks(chunks, contact, **kwargs)
        else:
            return super().index_chunks(chunks, contact, **kwargs)
    
    def search_psychology_aware(
        self,
        query: str,
        contact: str,
        psychology_weight: float = 0.3,
        **kwargs
    ) -> List[Union[SearchResult, MultiVectorSearchResult]]:
        """Perform psychology-aware search."""
        if self.enable_multi_vector and self.multi_store:
            vector_weights = {
                VectorSpace.SEMANTIC: 0.4,
                VectorSpace.PSYCHOLOGICAL: psychology_weight,
                VectorSpace.TEMPORAL: 0.2,
                VectorSpace.STRUCTURAL: 0.1
            }
            return self.multi_store.search_multi_vector(
                query=query,
                contact=contact,
                vector_weights=vector_weights,
                **kwargs
            )
        else:
            # Fallback to standard search
            return super().search(query, contact, **kwargs)