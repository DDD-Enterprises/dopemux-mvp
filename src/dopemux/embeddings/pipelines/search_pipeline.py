"""
Search Pipeline

Orchestrates the complete search workflow including query processing,
hybrid BM25+vector search, result enhancement, and integration enrichment
for production-grade semantic search.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from ..core import AdvancedEmbeddingConfig, SearchResult, SearchError
from ..providers import VoyageAPIClient
from ..storage import HybridVectorStore
from ..enhancers import ConsensusValidator
from ..integrations import BaseIntegration
from .base import BasePipeline, PipelineStage, PipelineResult

logger = logging.getLogger(__name__)


class SearchPipeline(BasePipeline):
    """
    End-to-end search processing pipeline.

    Orchestrates query processing, hybrid search execution,
    result enhancement, and integration enrichment for
    comprehensive semantic search workflows.
    """

    def __init__(self, config: AdvancedEmbeddingConfig,
                 vector_store: HybridVectorStore,
                 provider: Optional[VoyageAPIClient] = None,
                 enhancer: Optional[ConsensusValidator] = None,
                 integrations: Optional[List[BaseIntegration]] = None,
                 pipeline_id: str = "search_pipeline"):
        """
        Initialize search processing pipeline.

        Args:
            config: Embedding configuration
            vector_store: Hybrid vector store for search
            provider: Embedding provider (optional)
            enhancer: Result enhancer (optional)
            integrations: External system integrations (optional)
            pipeline_id: Unique pipeline identifier
        """
        super().__init__(config, pipeline_id)

        self.vector_store = vector_store
        self.provider = provider
        self.enhancer = enhancer
        self.integrations = integrations or []

        # Search state
        self.query: str = ""
        self.search_params: Dict[str, Any] = {}
        self.raw_results: List[SearchResult] = []
        self.enhanced_results: List[SearchResult] = []

        # Register pipeline stages
        self._register_stages()

        logger.info(f"🔍 Search pipeline initialized with {len(self.integrations)} integrations")

    def _register_stages(self):
        """Register pipeline stage handlers."""
        self.register_stage_handler(PipelineStage.VALIDATION, self._validate_stage)
        self.register_stage_handler(PipelineStage.PROCESSING, self._search_stage)
        self.register_stage_handler(PipelineStage.ENHANCEMENT, self._enhancement_stage)
        self.register_stage_handler(PipelineStage.COMPLETION, self._completion_stage)

    async def execute(self, query: str, **search_params) -> PipelineResult:
        """
        Execute the complete search pipeline.

        Args:
            query: Search query text
            **search_params: Additional search parameters
                - k: Number of results (default: 10)
                - enable_reranking: Use cross-encoder reranking (default: True)
                - enable_enhancement: Apply quality enhancement (default: True)
                - search_context: Additional context for integrations

        Returns:
            Pipeline execution result with search results
        """
        self.start_time = datetime.now()
        self.query = query
        self.search_params = search_params

        if self.config.enable_progress_tracking:
            print(f"🔍 Starting search pipeline: '{query}'")

        try:
            # Define pipeline stages
            stages = [
                (PipelineStage.VALIDATION, self._validate_stage, query, search_params),
                (PipelineStage.PROCESSING, self._search_stage),
                (PipelineStage.ENHANCEMENT, self._enhancement_stage),
                (PipelineStage.COMPLETION, self._completion_stage)
            ]

            # Execute stages
            stage_results = await self.run_with_stages(stages)

            # Calculate final result
            overall_success = all(r.success for r in stage_results)
            total_processed = len(self.enhanced_results)

            final_result = PipelineResult(
                success=overall_success,
                stage=PipelineStage.COMPLETION,
                processed_items=total_processed,
                duration_seconds=(datetime.now() - self.start_time).total_seconds(),
                metadata={
                    "query": query,
                    "search_params": search_params,
                    "results_count": len(self.enhanced_results),
                    "search_results": [r.__dict__ for r in self.enhanced_results],
                    "integrations_used": len(self.integrations)
                }
            )

            self.end_time = datetime.now()

            if self.config.enable_progress_tracking:
                if overall_success:
                    print(f"✅ Search completed: {total_processed} results found")
                else:
                    print(f"⚠️ Search completed with issues")

            return final_result

        except Exception as e:
            self.end_time = datetime.now()
            error_result = PipelineResult(
                success=False,
                stage=self.current_stage,
                duration_seconds=(datetime.now() - self.start_time).total_seconds(),
                errors=[str(e)]
            )

            logger.error(f"❌ Search pipeline failed: {e}")
            return error_result

    async def validate_inputs(self, query: str, search_params: Dict[str, Any]) -> bool:
        """
        Validate search inputs before execution.

        Args:
            query: Search query to validate
            search_params: Search parameters to validate

        Returns:
            True if inputs are valid
        """
        if not query or not isinstance(query, str):
            logger.error("❌ Query must be a non-empty string")
            return False

        if len(query.strip()) == 0:
            logger.error("❌ Query cannot be empty")
            return False

        # Validate search parameters
        k = search_params.get("k", 10)
        if not isinstance(k, int) or k <= 0:
            logger.error("❌ Parameter 'k' must be a positive integer")
            return False

        if k > 1000:
            logger.warning("⚠️ Large k value may impact performance")

        return True

    async def _validate_stage(self, query: str, search_params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate search inputs and pipeline components."""
        validation_start = datetime.now()

        # Validate inputs
        if not await self.validate_inputs(query, search_params):
            raise SearchError("Search input validation failed")

        # Validate vector store
        if not self.vector_store:
            raise SearchError("Vector store not available")

        # Check vector store has documents
        store_stats = self.vector_store.get_stats()
        doc_count = store_stats.get("documents", {}).get("document_count", 0)

        if doc_count == 0:
            logger.warning("⚠️ Vector store appears to be empty")

        # Validate provider if needed
        if not self.config.use_on_premise and not self.provider:
            logger.warning("⚠️ No provider available for query embedding")

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
            "query_length": len(query),
            "search_params": search_params,
            "vector_store_docs": doc_count,
            "provider_ready": self.provider is not None,
            "integration_status": integration_status,
            "validation_duration": validation_duration
        }

    async def _search_stage(self) -> Dict[str, Any]:
        """Execute hybrid search against vector store."""
        search_start = datetime.now()

        k = self.search_params.get("k", 10)
        enable_reranking = self.search_params.get("enable_reranking", True)

        if self.config.enable_progress_tracking:
            print(f"🔍 Executing hybrid search for '{self.query}' (k={k})...")

        try:
            # Execute hybrid search
            self.raw_results = await self.vector_store.hybrid_search(
                query=self.query,
                k=k,
                enable_reranking=enable_reranking
            )

            search_duration = (datetime.now() - search_start).total_seconds()

            # Update metrics
            self.metrics.searches_performed += 1

            if self.config.enable_progress_tracking:
                print(f"📊 Found {len(self.raw_results)} results in {search_duration:.2f}s")

            return {
                "results_count": len(self.raw_results),
                "search_duration": search_duration,
                "search_method": "hybrid",
                "reranking_enabled": enable_reranking,
                "top_scores": [r.score for r in self.raw_results[:3]]  # Top 3 scores
            }

        except Exception as e:
            logger.error(f"❌ Search execution failed: {e}")
            raise SearchError(f"Search execution failed: {e}") from e

    async def _enhancement_stage(self) -> Dict[str, Any]:
        """Apply enhancements to search results."""
        enhancement_start = datetime.now()
        enhanced_count = 0

        # Start with raw results
        self.enhanced_results = self.raw_results.copy()

        if not self.enhanced_results:
            logger.debug("ℹ️ No results to enhance")
            return {"enhanced_count": 0, "enhancement_duration": 0}

        enhancement_tasks = []

        # Apply consensus validation enhancement
        if self.enhancer and self.search_params.get("enable_enhancement", True):
            if self.config.enable_progress_tracking:
                print(f"✨ Applying consensus validation...")

            try:
                self.enhanced_results = await self.enhancer.enhance_results(
                    self.query,
                    self.enhanced_results
                )
                enhanced_count += len(self.enhanced_results)
                enhancement_tasks.append("consensus_validation")

            except Exception as e:
                logger.warning(f"⚠️ Consensus enhancement failed: {e}")

        # Apply integration enhancements
        search_context = self.search_params.get("search_context", {})

        for integration in self.integrations:
            try:
                integration_name = integration.__class__.__name__

                if self.config.enable_progress_tracking:
                    print(f"🔗 Enhancing with {integration_name}...")

                self.enhanced_results = await integration.enhance_search_results(
                    self.enhanced_results,
                    {
                        "query": self.query,
                        "search_params": self.search_params,
                        **search_context
                    }
                )

                enhancement_tasks.append(integration_name)

            except Exception as e:
                logger.warning(f"⚠️ Integration enhancement failed for {integration_name}: {e}")

        enhancement_duration = (datetime.now() - enhancement_start).total_seconds()

        return {
            "enhanced_count": enhanced_count,
            "enhancement_duration": enhancement_duration,
            "enhancement_tasks": enhancement_tasks,
            "final_results_count": len(self.enhanced_results)
        }

    async def _completion_stage(self) -> Dict[str, Any]:
        """Complete search pipeline and prepare final results."""
        completion_start = datetime.now()

        # Sort results by score if not already sorted
        self.enhanced_results.sort(key=lambda x: x.score, reverse=True)

        # Apply ADHD-friendly result metadata
        self._add_adhd_metadata()

        # Calculate search quality metrics
        quality_metrics = self._calculate_quality_metrics()

        # Cleanup resources
        await self.cleanup()

        completion_duration = (datetime.now() - completion_start).total_seconds()

        return {
            "final_results_count": len(self.enhanced_results),
            "quality_metrics": quality_metrics,
            "completion_duration": completion_duration,
            "total_pipeline_duration": (datetime.now() - self.start_time).total_seconds()
        }

    def _add_adhd_metadata(self):
        """Add ADHD-friendly metadata to search results."""
        for i, result in enumerate(self.enhanced_results):
            # Add ranking information
            result.metadata["result_rank"] = i + 1

            # Add reading time estimate
            word_count = len(result.content.split())
            reading_time = max(1, word_count // 200)  # ~200 words per minute
            result.metadata["estimated_reading_time"] = f"{reading_time} min"

            # Add complexity indicator
            if len(result.content) > 1000:
                result.metadata["complexity"] = "high"
            elif len(result.content) > 300:
                result.metadata["complexity"] = "medium"
            else:
                result.metadata["complexity"] = "low"

            # Add relevance indicator
            if result.score > 0.8:
                result.metadata["relevance"] = "high"
            elif result.score > 0.5:
                result.metadata["relevance"] = "medium"
            else:
                result.metadata["relevance"] = "low"

    def _calculate_quality_metrics(self) -> Dict[str, Any]:
        """Calculate search quality metrics."""
        if not self.enhanced_results:
            return {"no_results": True}

        scores = [r.score for r in self.enhanced_results]

        return {
            "results_count": len(self.enhanced_results),
            "avg_score": sum(scores) / len(scores),
            "max_score": max(scores),
            "min_score": min(scores),
            "score_variance": self._calculate_variance(scores),
            "has_high_confidence": max(scores) > 0.8,
            "has_low_confidence": min(scores) < 0.3
        }

    def _calculate_variance(self, scores: List[float]) -> float:
        """Calculate variance of scores."""
        if len(scores) <= 1:
            return 0.0

        mean = sum(scores) / len(scores)
        variance = sum((x - mean) ** 2 for x in scores) / len(scores)
        return variance

    async def cleanup(self) -> None:
        """Clean up pipeline resources after execution."""
        try:
            # Clear search state
            self.raw_results.clear()

            logger.debug("🧹 Search pipeline cleanup completed")

        except Exception as e:
            logger.warning(f"⚠️ Search cleanup warning: {e}")

    async def get_search_status(self) -> Dict[str, Any]:
        """
        Get current search status for monitoring.

        Returns:
            Current search pipeline status
        """
        return {
            "pipeline_id": self.pipeline_id,
            "current_stage": self.current_stage.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "query": self.query,
            "search_params": self.search_params,
            "raw_results_count": len(self.raw_results),
            "enhanced_results_count": len(self.enhanced_results),
            "metrics": self.metrics.get_summary()
        }

    def get_results(self) -> List[SearchResult]:
        """
        Get final enhanced search results.

        Returns:
            List of enhanced search results
        """
        return self.enhanced_results.copy()

    def display_results(self, max_results: int = 5):
        """
        Display ADHD-friendly search results summary.

        Args:
            max_results: Maximum number of results to display
        """
        if not self.enhanced_results:
            print("🔍 No results found")
            return

        print(f"🔍 Search Results for: '{self.query}'")
        print("=" * 50)

        for i, result in enumerate(self.enhanced_results[:max_results]):
            rank = i + 1
            score = result.score
            relevance = result.metadata.get("relevance", "unknown")
            reading_time = result.metadata.get("estimated_reading_time", "unknown")

            # Relevance emoji
            relevance_emoji = {"high": "🟢", "medium": "🟡", "low": "🔴"}.get(relevance, "⚪")

            print(f"{rank}. {relevance_emoji} Score: {score:.3f} | Read: {reading_time}")
            print(f"   📄 {result.doc_id}")

            # Show content preview (first 100 chars)
            content_preview = result.content[:100]
            if len(result.content) > 100:
                content_preview += "..."
            print(f"   💬 {content_preview}")
            print()

        if len(self.enhanced_results) > max_results:
            print(f"   ... and {len(self.enhanced_results) - max_results} more results")

        # Show search summary
        total_time = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        print(f"⏱️ Search completed in {total_time:.2f}s | {len(self.enhanced_results)} total results")