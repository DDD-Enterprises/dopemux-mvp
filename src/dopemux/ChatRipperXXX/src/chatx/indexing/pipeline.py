"""Indexing pipeline for conversation chunks and enrichments."""

import json
import logging
import uuid
from pathlib import Path
from typing import Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

from chatx.indexing.vector_store import ChromaDBVectorStore, IndexingConfig, SearchResult
from chatx.schemas.validator import validate_data, quarantine_invalid_data

logger = logging.getLogger(__name__)


@dataclass
class IndexingMetrics:
    """Metrics for indexing operations."""
    chunks_processed: int = 0
    chunks_indexed: int = 0
    chunks_skipped: int = 0
    validation_errors: int = 0
    indexing_errors: int = 0
    processing_time_seconds: float = 0.0
    collections_created: int = 0
    embeddings_generated: int = 0
    
    def get_summary(self) -> dict[str, Any]:
        """Get metrics summary."""
        success_rate = (
            self.chunks_indexed / self.chunks_processed
            if self.chunks_processed > 0 else 0
        )
        
        throughput = (
            self.chunks_indexed / self.processing_time_seconds
            if self.processing_time_seconds > 0 else 0
        )
        
        return {
            **asdict(self),
            "success_rate": success_rate,
            "indexing_throughput": throughput,
        }


@dataclass
class SearchConfig:
    """Configuration for search operations."""
    k: int = 10  # Number of results
    score_threshold: float = 0.0  # Minimum similarity score
    date_range_days: Optional[int] = None  # Restrict to recent days
    include_labels: Optional[list[str]] = None  # Include chunks with these labels
    exclude_labels: Optional[list[str]] = None  # Exclude chunks with these labels
    platform_filter: Optional[str] = None  # Filter by platform
    redacted_only: bool = True  # Only search redacted content


class IndexingPipeline:
    """Pipeline for indexing conversation chunks and enabling search."""
    
    def __init__(
        self,
        vector_store: Optional[ChromaDBVectorStore] = None,
        indexing_config: Optional[IndexingConfig] = None,
        output_dir: Optional[Path] = None,
        validate_schemas: bool = True,
    ):
        """Initialize indexing pipeline.
        
        Args:
            vector_store: Vector store instance (creates default if None)
            indexing_config: Indexing configuration
            output_dir: Directory for outputs and reports
            validate_schemas: Whether to validate schemas
        """
        self.indexing_config = indexing_config or IndexingConfig()
        self.vector_store = vector_store
        self.output_dir = output_dir or Path("./out")
        self.validate_schemas = validate_schemas
        
        # Metrics tracking
        self.metrics = IndexingMetrics()
        
        # Run tracking
        self.run_id = str(uuid.uuid4())
        
        logger.info(f"Initialized indexing pipeline with run_id: {self.run_id}")
        logger.info(f"Embedding model: {self.indexing_config.embedding_model}")
    
    def __enter__(self):
        """Context manager entry."""
        if self.vector_store is None:
            self.vector_store = ChromaDBVectorStore(self.indexing_config)
        
        self.vector_store.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.vector_store:
            self.vector_store.close()
    
    def _validate_and_filter_chunks(self, chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Validate chunks and filter invalid ones."""
        if not self.validate_schemas:
            return chunks
        
        # Validate chunks against schema
        valid_chunks, invalid_chunks = quarantine_invalid_data(
            chunks,
            "chunk",
            quarantine_dir=self.output_dir / "quarantine"
        )
        
        if invalid_chunks:
            logger.warning(f"Quarantined {len(invalid_chunks)} invalid chunks")
            self.metrics.validation_errors += len(invalid_chunks)
        
        return valid_chunks
    
    def _filter_chunks_for_indexing(self, chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Filter chunks suitable for indexing."""
        filtered_chunks = []
        
        for chunk in chunks:
            # Skip chunks without text
            if not chunk.get("text", "").strip():
                self.metrics.chunks_skipped += 1
                continue
            
            # Check for redaction metadata (recommended for privacy)
            provenance = chunk.get("provenance", {})
            if "redaction" not in provenance:
                logger.warning(f"Chunk {chunk.get('chunk_id', 'unknown')} lacks redaction metadata")
            
            # Check redaction coverage if available
            redaction_info = provenance.get("redaction", {})
            coverage = redaction_info.get("coverage", 0.0)
            if coverage < 0.99:  # Less than 99% redaction coverage
                logger.warning(f"Chunk {chunk.get('chunk_id', 'unknown')} has low redaction coverage: {coverage:.2%}")
            
            filtered_chunks.append(chunk)
        
        logger.info(f"Filtered {len(filtered_chunks)} chunks for indexing from {len(chunks)} total")
        return filtered_chunks
    
    def index_chunks(
        self,
        chunks: list[dict[str, Any]],
        contact: str,
        overwrite_collection: bool = False,
        batch_size: Optional[int] = None
    ) -> tuple[dict[str, Any], Path]:
        """Index conversation chunks for search.
        
        Args:
            chunks: List of chunk dictionaries
            contact: Contact identifier
            overwrite_collection: Whether to overwrite existing collection
            batch_size: Batch size for processing
            
        Returns:
            Tuple of (indexing_stats, report_file_path)
        """
        logger.info(f"Starting indexing of {len(chunks)} chunks for contact: {contact}")
        start_time = datetime.now()
        
        try:
            # Validate chunks
            valid_chunks = self._validate_and_filter_chunks(chunks)
            self.metrics.chunks_processed = len(chunks)
            
            # Filter for indexing
            indexable_chunks = self._filter_chunks_for_indexing(valid_chunks)
            
            if not indexable_chunks:
                logger.warning("No chunks suitable for indexing")
                return {"indexed": 0, "errors": len(chunks)}, self._save_indexing_report({})
            
            # Create/get collection
            if overwrite_collection:
                logger.info(f"Overwriting existing collection for contact: {contact}")
                
            # Create or overwrite target collection

            self.vector_store.create_collection(contact, overwrite=overwrite_collection)
            self.metrics.collections_created = 1

            # Index chunks
            indexing_stats = self.vector_store.index_chunks(
                indexable_chunks,
                contact,
                batch_size=batch_size
            )
            
            # Update metrics
            self.metrics.chunks_indexed = indexing_stats["indexed"]
            self.metrics.indexing_errors = indexing_stats["errors"]
            self.metrics.embeddings_generated = indexing_stats["indexed"]  # One embedding per chunk
            
            finished_time = datetime.now()
            self.metrics.processing_time_seconds = (finished_time - start_time).total_seconds()
            
            # Enhanced statistics
            enhanced_stats = {
                **indexing_stats,
                "contact": contact,
                "processing_time_seconds": self.metrics.processing_time_seconds,
                "throughput_chunks_per_second": (
                    self.metrics.chunks_indexed / self.metrics.processing_time_seconds
                    if self.metrics.processing_time_seconds > 0 else 0
                ),
                "validation_errors": self.metrics.validation_errors,
                "chunks_skipped": self.metrics.chunks_skipped,
                "run_id": self.run_id,
                "timestamp": finished_time.isoformat(),
            }
            
            # Save report
            report_path = self._save_indexing_report(enhanced_stats)
            
            logger.info(f"Indexing complete: {self.metrics.chunks_indexed} chunks indexed in {self.metrics.processing_time_seconds:.2f}s")
            
            return enhanced_stats, report_path
            
        except Exception as e:
            logger.error(f"Error during indexing: {e}")
            self.metrics.indexing_errors += len(chunks)
            raise
    
    def search_chunks(
        self,
        query: str,
        contact: str,
        config: Optional[SearchConfig] = None
    ) -> list[SearchResult]:
        """Search for relevant chunks.
        
        Args:
            query: Search query
            contact: Contact identifier
            config: Search configuration
            
        Returns:
            List of search results
        """
        config = config or SearchConfig()
        
        # Build filters from config
        filters = {}
        
        if config.platform_filter:
            filters["platform"] = config.platform_filter
        
        if config.redacted_only:
            filters["redacted"] = True
        
        if config.include_labels:
            # Note: This would need special handling in ChromaDB for array fields
            pass  # ChromaDB array filtering is complex, might need post-processing
        
        # Perform search
        results = self.vector_store.search(
            query=query,
            contact=contact,
            k=config.k,
            filters=filters if filters else None
        )
        
        # Apply post-processing filters
        filtered_results = []
        for result in results:
            # Score threshold
            if result.score < config.score_threshold:
                continue
            
            # Date range filter
            if config.date_range_days:
                # Would need to parse date from metadata and filter
                pass
            
            # Label filters (post-processing)
            if config.include_labels or config.exclude_labels:
                chunk_labels = result.metadata.get("labels_coarse", [])
                
                if config.include_labels:
                    if not any(label in chunk_labels for label in config.include_labels):
                        continue
                
                if config.exclude_labels:
                    if any(label in chunk_labels for label in config.exclude_labels):
                        continue
            
            filtered_results.append(result)
        
        logger.info(f"Search returned {len(filtered_results)} results for query: {query[:50]}...")
        return filtered_results
    
    def update_chunk_enrichments(
        self,
        enrichments: list[dict[str, Any]],
        contact: str
    ) -> dict[str, Any]:
        """Update chunks with enrichment metadata.
        
        Args:
            enrichments: List of enrichment dictionaries
            contact: Contact identifier
            
        Returns:
            Update statistics
        """
        updated_count = 0
        error_count = 0
        
        for enrichment in enrichments:
            try:
                msg_id = enrichment.get("msg_id")
                if not msg_id:
                    error_count += 1
                    continue
                
                # Build metadata update from enrichment
                metadata_update = {
                    "speech_act": enrichment.get("speech_act"),
                    "emotion_primary": enrichment.get("emotion_primary"),
                    "stance": enrichment.get("stance"),
                    "confidence_llm": enrichment.get("confidence_llm", 0.0),
                    "coarse_labels": enrichment.get("coarse_labels", []),
                    "enriched": True,
                    "enriched_at": datetime.now().isoformat(),
                }
                
                # Remove None values
                metadata_update = {k: v for k, v in metadata_update.items() if v is not None}
                
                # Update chunk metadata (would need chunk_id mapping)
                # This is simplified - in practice you'd need to map msg_id to chunk_id
                success = self.vector_store.update_chunk_metadata(
                    contact=contact,
                    chunk_id=msg_id,  # Assuming msg_id maps to chunk_id
                    metadata_updates=metadata_update
                )
                
                if success:
                    updated_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                logger.error(f"Error updating enrichment for {enrichment.get('msg_id')}: {e}")
                error_count += 1
        
        stats = {
            "enrichments_processed": len(enrichments),
            "chunks_updated": updated_count,
            "errors": error_count,
            "contact": contact,
        }
        
        logger.info(f"Enrichment update complete: {stats}")
        return stats
    
    def get_collection_info(self, contact: str) -> dict[str, Any]:
        """Get information about a collection.
        
        Args:
            contact: Contact identifier
            
        Returns:
            Collection information
        """
        return self.vector_store.get_collection_stats(contact)
    
    def list_all_collections(self) -> list[dict[str, Any]]:
        """List all indexed collections.
        
        Returns:
            List of collection information
        """
        return self.vector_store.list_collections()
    
    def _save_indexing_report(self, stats: dict[str, Any]) -> Path:
        """Save indexing report to file.
        
        Args:
            stats: Indexing statistics
            
        Returns:
            Path to saved report
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"indexing_report_{timestamp}.json"
        
        # Ensure output directory exists
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Build comprehensive report
        report = {
            "run_id": self.run_id,
            "timestamp": datetime.now().isoformat(),
            "indexing_stats": stats,
            "metrics": self.metrics.get_summary(),
            "configuration": {
                "embedding_model": self.indexing_config.embedding_model,
                "chunk_size": self.indexing_config.chunk_size,
                "batch_size": self.indexing_config.batch_size,
                "distance_metric": self.indexing_config.distance_metric,
            },
        }
        
        # Save report
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Indexing report saved to: {report_file}")
        return report_file
    
    def get_performance_metrics(self) -> dict[str, Any]:
        """Get performance metrics for the indexing pipeline.
        
        Returns:
            Performance metrics dictionary
        """
        return {
            "run_id": self.run_id,
            "metrics": self.metrics.get_summary(),
            "configuration": {
                "embedding_model": self.indexing_config.embedding_model,
                "persist_directory": self.indexing_config.persist_directory,
                "batch_size": self.indexing_config.batch_size,
            },
            "timestamp": datetime.now().isoformat(),
        }
