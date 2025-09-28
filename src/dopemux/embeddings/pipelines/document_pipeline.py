"""
Document Processing Pipeline

Orchestrates the complete document embedding workflow from ingestion
through embedding generation to storage and indexing. Coordinates
providers, storage, enhancers, and integrations for end-to-end processing.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from ..core import AdvancedEmbeddingConfig, SearchResult, EmbeddingError
from ..providers import VoyageAPIClient
from ..storage import HybridVectorStore
from ..enhancers import ConsensusValidator
from ..integrations import BaseIntegration
from .base import BasePipeline, PipelineStage, PipelineResult

logger = logging.getLogger(__name__)


class DocumentPipeline(BasePipeline):
    """
    End-to-end document processing pipeline.

    Orchestrates document ingestion, embedding generation, storage,
    quality validation, and integration sync for production-grade
    embedding workflows.
    """

    def __init__(self, config: AdvancedEmbeddingConfig,
                 vector_store: HybridVectorStore,
                 provider: Optional[VoyageAPIClient] = None,
                 enhancer: Optional[ConsensusValidator] = None,
                 integrations: Optional[List[BaseIntegration]] = None,
                 pipeline_id: str = "document_pipeline"):
        """
        Initialize document processing pipeline.

        Args:
            config: Embedding configuration
            vector_store: Hybrid vector store for document storage
            provider: Embedding provider (optional)
            enhancer: Quality enhancer (optional)
            integrations: External system integrations (optional)
            pipeline_id: Unique pipeline identifier
        """
        super().__init__(config, pipeline_id)

        self.vector_store = vector_store
        self.provider = provider
        self.enhancer = enhancer
        self.integrations = integrations or []

        # Processing state
        self.documents_to_process: List[Dict[str, Any]] = []
        self.processed_documents: List[Dict[str, Any]] = []
        self.failed_documents: List[Dict[str, Any]] = []

        # Register pipeline stages
        self._register_stages()

        logger.info(f"📄 Document pipeline initialized with {len(self.integrations)} integrations")

    def _register_stages(self):
        """Register pipeline stage handlers."""
        self.register_stage_handler(PipelineStage.VALIDATION, self._validate_stage)
        self.register_stage_handler(PipelineStage.PROCESSING, self._processing_stage)
        self.register_stage_handler(PipelineStage.STORAGE, self._storage_stage)
        self.register_stage_handler(PipelineStage.ENHANCEMENT, self._enhancement_stage)
        self.register_stage_handler(PipelineStage.COMPLETION, self._completion_stage)

    async def execute(self, documents: List[Dict[str, Any]]) -> PipelineResult:
        """
        Execute the complete document processing pipeline.

        Args:
            documents: List of documents to process with id, content, metadata

        Returns:
            Pipeline execution result
        """
        self.start_time = datetime.now()
        self.documents_to_process = documents.copy()

        if self.config.enable_progress_tracking:
            print(f"🚀 Starting document pipeline: {len(documents)} documents")

        try:
            # Define pipeline stages
            stages = [
                (PipelineStage.VALIDATION, self._validate_stage, documents),
                (PipelineStage.PROCESSING, self._processing_stage),
                (PipelineStage.STORAGE, self._storage_stage),
                (PipelineStage.ENHANCEMENT, self._enhancement_stage),
                (PipelineStage.COMPLETION, self._completion_stage)
            ]

            # Execute stages
            stage_results = await self.run_with_stages(stages)

            # Calculate final result
            overall_success = all(r.success for r in stage_results)
            total_processed = sum(r.processed_items for r in stage_results)
            total_failed = sum(r.failed_items for r in stage_results)

            final_result = PipelineResult(
                success=overall_success,
                stage=PipelineStage.COMPLETION,
                processed_items=total_processed,
                failed_items=total_failed,
                duration_seconds=(datetime.now() - self.start_time).total_seconds(),
                metadata={
                    "documents_input": len(documents),
                    "documents_processed": len(self.processed_documents),
                    "documents_failed": len(self.failed_documents),
                    "integrations_used": len(self.integrations)
                }
            )

            self.end_time = datetime.now()

            if self.config.enable_progress_tracking:
                if overall_success:
                    print(f"✅ Pipeline completed successfully: {total_processed} documents processed")
                else:
                    print(f"⚠️ Pipeline completed with issues: {total_processed} processed, {total_failed} failed")

            return final_result

        except Exception as e:
            self.end_time = datetime.now()
            error_result = PipelineResult(
                success=False,
                stage=self.current_stage,
                duration_seconds=(datetime.now() - self.start_time).total_seconds(),
                errors=[str(e)]
            )

            logger.error(f"❌ Document pipeline failed: {e}")
            return error_result

    async def validate_inputs(self, documents: List[Dict[str, Any]]) -> bool:
        """
        Validate pipeline inputs before execution.

        Args:
            documents: Documents to validate

        Returns:
            True if all documents are valid
        """
        if not documents:
            logger.warning("⚠️ No documents provided for processing")
            return False

        for i, doc in enumerate(documents):
            if not isinstance(doc, dict):
                logger.error(f"❌ Document {i} is not a dictionary")
                return False

            if "id" not in doc:
                logger.error(f"❌ Document {i} missing required 'id' field")
                return False

            if "content" not in doc:
                logger.error(f"❌ Document {i} missing required 'content' field")
                return False

            if not isinstance(doc["content"], str):
                logger.error(f"❌ Document {i} content is not a string")
                return False

            if len(doc["content"].strip()) == 0:
                logger.warning(f"⚠️ Document {i} has empty content")

        return True

    async def _validate_stage(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate input documents and pipeline components."""
        validation_start = datetime.now()

        # Validate inputs
        if not await self.validate_inputs(documents):
            raise EmbeddingError("Document validation failed")

        # Validate vector store
        if not self.vector_store:
            raise EmbeddingError("Vector store not available")

        # Validate provider if using API
        if not self.config.use_on_premise and not self.provider:
            raise EmbeddingError("Embedding provider required for API mode")

        # Test integrations
        integration_status = {}
        for integration in self.integrations:
            try:
                is_healthy = await integration.validate_connection()
                integration_status[integration.__class__.__name__] = is_healthy
            except Exception as e:
                logger.warning(f"⚠️ Integration {integration.__class__.__name__} validation failed: {e}")
                integration_status[integration.__class__.__name__] = False

        validation_duration = (datetime.now() - validation_start).total_seconds()

        return {
            "documents_count": len(documents),
            "vector_store_ready": True,
            "provider_ready": self.provider is not None,
            "integration_status": integration_status,
            "validation_duration": validation_duration
        }

    async def _processing_stage(self) -> Dict[str, Any]:
        """Generate embeddings for documents."""
        processing_start = datetime.now()
        processed_count = 0
        failed_count = 0

        if self.config.enable_progress_tracking:
            print(f"🔄 Generating embeddings for {len(self.documents_to_process)} documents...")

        # Process documents in batches
        batch_size = self.config.batch_size

        for i in range(0, len(self.documents_to_process), batch_size):
            batch = self.documents_to_process[i:i + batch_size]

            try:
                # Prepare batch content
                batch_content = [doc["content"] for doc in batch]

                # Generate embeddings if using API
                if self.provider and not self.config.use_on_premise:
                    embeddings = await self.provider.embed_texts(batch_content)

                    # Add embeddings to documents
                    for doc, embedding in zip(batch, embeddings):
                        doc["embedding"] = embedding
                        self.processed_documents.append(doc)
                        processed_count += 1
                else:
                    # On-premise mode - mark for storage without embeddings
                    for doc in batch:
                        self.processed_documents.append(doc)
                        processed_count += 1

                # Update metrics
                self.metrics.documents_processed += len(batch)
                if self.provider:
                    self.metrics.documents_embedded += len(batch)

                if self.config.enable_progress_tracking:
                    progress = (i + len(batch)) / len(self.documents_to_process)
                    print(f"📊 Progress: {progress:.1%} ({processed_count} processed)")

            except Exception as e:
                logger.error(f"❌ Batch processing failed: {e}")

                # Add failed documents to failed list
                for doc in batch:
                    self.failed_documents.append({
                        "document": doc,
                        "error": str(e)
                    })
                    failed_count += 1

                self.metrics.documents_failed += len(batch)

        processing_duration = (datetime.now() - processing_start).total_seconds()

        return {
            "processed_count": processed_count,
            "failed_count": failed_count,
            "processing_duration": processing_duration,
            "batches_processed": (len(self.documents_to_process) + batch_size - 1) // batch_size
        }

    async def _storage_stage(self) -> Dict[str, Any]:
        """Store processed documents in vector store."""
        storage_start = datetime.now()

        if not self.processed_documents:
            logger.warning("⚠️ No processed documents to store")
            return {"stored_count": 0, "storage_duration": 0}

        if self.config.enable_progress_tracking:
            print(f"💾 Storing {len(self.processed_documents)} documents...")

        try:
            # Add documents to vector store
            await self.vector_store.add_documents(self.processed_documents)

            storage_duration = (datetime.now() - storage_start).total_seconds()

            return {
                "stored_count": len(self.processed_documents),
                "storage_duration": storage_duration,
                "vector_store_stats": self.vector_store.get_stats()
            }

        except Exception as e:
            logger.error(f"❌ Storage failed: {e}")
            raise EmbeddingError(f"Document storage failed: {e}") from e

    async def _enhancement_stage(self) -> Dict[str, Any]:
        """Apply quality enhancements and validations."""
        enhancement_start = datetime.now()
        enhanced_count = 0

        if not self.enhancer:
            logger.debug("ℹ️ No enhancer configured - skipping enhancement")
            return {"enhanced_count": 0, "enhancement_duration": 0}

        if self.config.enable_progress_tracking:
            print(f"✨ Applying quality enhancements...")

        try:
            # Apply consensus validation to top documents
            validation_limit = min(len(self.processed_documents), 10)  # Limit for cost control

            for doc in self.processed_documents[:validation_limit]:
                if "embedding" in doc:
                    try:
                        validation_result = await self.enhancer.validate_quality(
                            doc["id"],
                            doc["content"],
                            doc["embedding"]
                        )

                        # Add validation metadata
                        doc.setdefault("metadata", {})["consensus_validation"] = validation_result
                        enhanced_count += 1

                    except Exception as e:
                        logger.warning(f"⚠️ Enhancement failed for {doc['id']}: {e}")

            enhancement_duration = (datetime.now() - enhancement_start).total_seconds()

            return {
                "enhanced_count": enhanced_count,
                "enhancement_duration": enhancement_duration,
                "enhancer_stats": self.enhancer.get_enhancement_stats()
            }

        except Exception as e:
            logger.error(f"❌ Enhancement stage failed: {e}")
            # Don't fail pipeline for enhancement errors
            return {
                "enhanced_count": 0,
                "enhancement_duration": (datetime.now() - enhancement_start).total_seconds(),
                "enhancement_error": str(e)
            }

    async def _completion_stage(self) -> Dict[str, Any]:
        """Complete pipeline and sync with integrations."""
        completion_start = datetime.now()
        sync_results = {}

        if self.config.enable_progress_tracking:
            print(f"🔄 Syncing with {len(self.integrations)} integrations...")

        # Sync with integrations
        for integration in self.integrations:
            try:
                integration_name = integration.__class__.__name__

                # Store embeddings in integration
                if self.processed_documents:
                    documents_with_embeddings = [
                        doc for doc in self.processed_documents
                        if "embedding" in doc
                    ]

                    if documents_with_embeddings:
                        embeddings = [doc["embedding"] for doc in documents_with_embeddings]
                        await integration.store_embeddings(documents_with_embeddings, embeddings)

                sync_results[integration_name] = {
                    "success": True,
                    "documents_synced": len(self.processed_documents)
                }

            except Exception as e:
                logger.warning(f"⚠️ Integration sync failed for {integration_name}: {e}")
                sync_results[integration_name] = {
                    "success": False,
                    "error": str(e)
                }

        # Cleanup resources
        await self.cleanup()

        completion_duration = (datetime.now() - completion_start).total_seconds()

        return {
            "sync_results": sync_results,
            "completion_duration": completion_duration,
            "total_pipeline_duration": (datetime.now() - self.start_time).total_seconds()
        }

    async def cleanup(self) -> None:
        """Clean up pipeline resources after execution."""
        try:
            # Close provider connections
            if self.provider:
                # VoyageAPIClient is async context manager
                pass

            # Clear processing state
            self.documents_to_process.clear()

            logger.debug("🧹 Pipeline cleanup completed")

        except Exception as e:
            logger.warning(f"⚠️ Cleanup warning: {e}")

    async def get_processing_status(self) -> Dict[str, Any]:
        """
        Get current processing status for monitoring.

        Returns:
            Current pipeline status information
        """
        return {
            "pipeline_id": self.pipeline_id,
            "current_stage": self.current_stage.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "documents_total": len(self.documents_to_process),
            "documents_processed": len(self.processed_documents),
            "documents_failed": len(self.failed_documents),
            "processing_rate": self._calculate_processing_rate(),
            "estimated_completion": self._estimate_completion_time(),
            "metrics": self.metrics.get_summary()
        }

    def _calculate_processing_rate(self) -> float:
        """Calculate documents processed per second."""
        if not self.start_time or not self.processed_documents:
            return 0.0

        elapsed = (datetime.now() - self.start_time).total_seconds()
        return len(self.processed_documents) / elapsed if elapsed > 0 else 0.0

    def _estimate_completion_time(self) -> Optional[str]:
        """Estimate pipeline completion time."""
        if not self.start_time or not self.documents_to_process:
            return None

        processed = len(self.processed_documents)
        total = len(self.documents_to_process)

        if processed == 0:
            return None

        elapsed = (datetime.now() - self.start_time).total_seconds()
        rate = processed / elapsed
        remaining = total - processed

        if rate > 0:
            eta_seconds = remaining / rate
            eta_time = datetime.now().timestamp() + eta_seconds
            return datetime.fromtimestamp(eta_time).isoformat()

        return None