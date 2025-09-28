"""
Unit tests for embedding pipeline orchestrators.

Tests the DocumentPipeline, SearchPipeline, and SyncPipeline components.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import asyncio

from dopemux.embeddings.pipelines import (
    DocumentPipeline,
    SearchPipeline,
    SyncPipeline,
    BasePipeline,
    PipelineStage,
    PipelineResult
)
from dopemux.embeddings.core import AdvancedEmbeddingConfig, SearchResult
from dopemux.embeddings.storage import HybridVectorStore
from dopemux.embeddings.providers import VoyageAPIClient
from dopemux.embeddings.enhancers import ConsensusValidator
from dopemux.embeddings.integrations import ConPortAdapter


class TestPipelineStage:
    """Test PipelineStage enum."""

    def test_pipeline_stage_values(self):
        """Test pipeline stage enum values."""
        assert PipelineStage.VALIDATION.value == "validation"
        assert PipelineStage.PROCESSING.value == "processing"
        assert PipelineStage.STORAGE.value == "storage"
        assert PipelineStage.ENHANCEMENT.value == "enhancement"
        assert PipelineStage.COMPLETION.value == "completion"


class TestPipelineResult:
    """Test PipelineResult dataclass."""

    def test_result_creation_success(self):
        """Test creating successful pipeline result."""
        result = PipelineResult(
            success=True,
            stage=PipelineStage.COMPLETION,
            processed_items=10,
            duration_seconds=5.5,
            metadata={"batch_size": 10}
        )

        assert result.success is True
        assert result.stage == PipelineStage.COMPLETION
        assert result.processed_items == 10
        assert result.duration_seconds == 5.5
        assert result.metadata["batch_size"] == 10

    def test_result_creation_failure(self):
        """Test creating failed pipeline result."""
        result = PipelineResult(
            success=False,
            stage=PipelineStage.PROCESSING,
            failed_items=5,
            errors=["Network timeout", "Invalid input"]
        )

        assert result.success is False
        assert result.stage == PipelineStage.PROCESSING
        assert result.failed_items == 5
        assert len(result.errors) == 2


class TestBasePipeline:
    """Test base pipeline abstract class."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return AdvancedEmbeddingConfig(enable_progress_tracking=True)

    def test_base_pipeline_cannot_instantiate(self):
        """Test that BasePipeline cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BasePipeline()  # Should fail - abstract class

    def test_base_pipeline_interface(self):
        """Test that BasePipeline defines required interface."""
        # Check that abstract methods are defined
        assert hasattr(BasePipeline, 'execute')
        assert hasattr(BasePipeline, 'cleanup')


class TestDocumentPipeline:
    """Test document processing pipeline."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return AdvancedEmbeddingConfig(
            batch_size=4,
            enable_progress_tracking=True
        )

    @pytest.fixture
    def mock_vector_store(self):
        """Create mock vector store."""
        store = AsyncMock(spec=HybridVectorStore)
        store.add_documents.return_value = None
        store.get_stats.return_value = {"documents": {"document_count": 0}}
        return store

    @pytest.fixture
    def mock_provider(self):
        """Create mock embedding provider."""
        provider = AsyncMock(spec=VoyageAPIClient)
        provider.embed_texts.return_value = [[0.1] * 2048, [0.2] * 2048]
        return provider

    @pytest.fixture
    def mock_enhancer(self):
        """Create mock consensus enhancer."""
        enhancer = AsyncMock(spec=ConsensusValidator)
        enhancer.validate_quality.return_value = MagicMock(
            quality_score=0.8,
            consensus_reached=True
        )
        return enhancer

    @pytest.fixture
    def mock_integration(self):
        """Create mock integration."""
        integration = AsyncMock(spec=ConPortAdapter)
        integration.validate_connection.return_value = True
        integration.store_embeddings.return_value = None
        return integration

    @pytest.fixture
    def pipeline(self, config, mock_vector_store, mock_provider, mock_enhancer, mock_integration):
        """Create document pipeline."""
        return DocumentPipeline(
            config=config,
            vector_store=mock_vector_store,
            provider=mock_provider,
            enhancer=mock_enhancer,
            integrations=[mock_integration]
        )

    def test_pipeline_initialization(self, pipeline, config):
        """Test document pipeline initialization."""
        assert pipeline.config == config
        assert pipeline.vector_store is not None
        assert pipeline.provider is not None
        assert pipeline.enhancer is not None
        assert len(pipeline.integrations) == 1

    @pytest.mark.asyncio
    async def test_validate_inputs_valid(self, pipeline):
        """Test input validation with valid documents."""
        valid_docs = [
            {"id": "doc1", "content": "Valid content"},
            {"id": "doc2", "content": "Another valid content"}
        ]

        is_valid = await pipeline.validate_inputs(valid_docs)
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_inputs_invalid(self, pipeline):
        """Test input validation with invalid documents."""
        # Missing required fields
        invalid_docs = [
            {"content": "Missing ID"},
            {"id": "doc2"}  # Missing content
        ]

        is_valid = await pipeline.validate_inputs(invalid_docs)
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_inputs_empty(self, pipeline):
        """Test input validation with empty document list."""
        is_valid = await pipeline.validate_inputs([])
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_execute_pipeline_success(self, pipeline):
        """Test successful pipeline execution."""
        documents = [
            {"id": "doc1", "content": "First document"},
            {"id": "doc2", "content": "Second document"}
        ]

        result = await pipeline.execute(documents)

        assert isinstance(result, PipelineResult)
        assert result.success is True
        assert result.stage == PipelineStage.COMPLETION
        assert result.processed_items > 0

    @pytest.mark.asyncio
    async def test_execute_pipeline_with_batching(self, pipeline):
        """Test pipeline execution with large document set requiring batching."""
        # Create more documents than batch size
        documents = [
            {"id": f"doc{i}", "content": f"Document {i} content"}
            for i in range(10)  # Larger than batch_size of 4
        ]

        result = await pipeline.execute(documents)

        assert result.success is True
        # Should have processed all documents despite batching
        assert result.metadata["documents_processed"] == 10

    @pytest.mark.asyncio
    async def test_execute_pipeline_validation_failure(self, pipeline):
        """Test pipeline execution with validation failure."""
        invalid_documents = [
            {"invalid": "missing required fields"}
        ]

        result = await pipeline.execute(invalid_documents)

        assert result.success is False
        assert "validation" in str(result.errors[0]).lower()

    @pytest.mark.asyncio
    async def test_execute_pipeline_provider_failure(self, pipeline):
        """Test pipeline execution with provider failure."""
        documents = [{"id": "doc1", "content": "Test content"}]

        # Mock provider to fail
        pipeline.provider.embed_texts.side_effect = Exception("API Error")

        result = await pipeline.execute(documents)

        # Should handle error gracefully
        assert result.success is False

    @pytest.mark.asyncio
    async def test_processing_stage_with_embeddings(self, pipeline):
        """Test processing stage generates embeddings."""
        documents = [
            {"id": "doc1", "content": "Test content 1"},
            {"id": "doc2", "content": "Test content 2"}
        ]
        pipeline.documents_to_process = documents

        stage_result = await pipeline._processing_stage()

        assert stage_result["processed_count"] == 2
        assert stage_result["failed_count"] == 0
        # Should have called provider for embeddings
        pipeline.provider.embed_texts.assert_called()

    @pytest.mark.asyncio
    async def test_processing_stage_on_premise_mode(self, pipeline):
        """Test processing stage in on-premise mode."""
        pipeline.config.use_on_premise = True
        documents = [{"id": "doc1", "content": "Test content"}]
        pipeline.documents_to_process = documents

        stage_result = await pipeline._processing_stage()

        # Should process without calling external provider
        assert stage_result["processed_count"] == 1
        pipeline.provider.embed_texts.assert_not_called()

    @pytest.mark.asyncio
    async def test_storage_stage(self, pipeline):
        """Test storage stage stores documents."""
        pipeline.processed_documents = [
            {"id": "doc1", "content": "Content", "embedding": [0.1] * 2048}
        ]

        stage_result = await pipeline._storage_stage()

        assert stage_result["stored_count"] == 1
        pipeline.vector_store.add_documents.assert_called_once()

    @pytest.mark.asyncio
    async def test_enhancement_stage(self, pipeline):
        """Test enhancement stage applies quality validation."""
        pipeline.processed_documents = [
            {"id": "doc1", "content": "Content", "embedding": [0.1] * 2048}
        ]

        stage_result = await pipeline._enhancement_stage()

        assert "enhanced_count" in stage_result
        # Should have called enhancer
        pipeline.enhancer.validate_quality.assert_called()

    @pytest.mark.asyncio
    async def test_completion_stage_with_integrations(self, pipeline):
        """Test completion stage syncs with integrations."""
        pipeline.processed_documents = [
            {"id": "doc1", "content": "Content", "embedding": [0.1] * 2048}
        ]

        stage_result = await pipeline._completion_stage()

        assert "sync_results" in stage_result
        # Should have synced with integration
        pipeline.integrations[0].store_embeddings.assert_called()

    @pytest.mark.asyncio
    async def test_get_processing_status(self, pipeline):
        """Test getting processing status."""
        pipeline.pipeline_id = "test_pipeline"
        pipeline.current_stage = PipelineStage.PROCESSING
        pipeline.start_time = datetime.now()

        status = await pipeline.get_processing_status()

        assert status["pipeline_id"] == "test_pipeline"
        assert status["current_stage"] == "processing"
        assert "start_time" in status

    @pytest.mark.asyncio
    async def test_progress_tracking_enabled(self, pipeline):
        """Test progress tracking output."""
        documents = [{"id": "doc1", "content": "Test content"}]

        with patch('builtins.print') as mock_print:
            await pipeline.execute(documents)

            # Should have printed progress messages
            mock_print.assert_called()
            progress_calls = [call for call in mock_print.call_args_list
                            if "pipeline" in str(call).lower()]
            assert len(progress_calls) > 0


class TestSearchPipeline:
    """Test search processing pipeline."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return AdvancedEmbeddingConfig(enable_progress_tracking=True)

    @pytest.fixture
    def mock_vector_store(self):
        """Create mock vector store."""
        store = AsyncMock(spec=HybridVectorStore)
        store.hybrid_search.return_value = [
            SearchResult("doc1", 0.9, "First result", {}),
            SearchResult("doc2", 0.7, "Second result", {})
        ]
        store.get_stats.return_value = {"documents": {"document_count": 100}}
        return store

    @pytest.fixture
    def mock_enhancer(self):
        """Create mock enhancer."""
        enhancer = AsyncMock(spec=ConsensusValidator)
        enhancer.enhance_results.return_value = [
            SearchResult("doc1", 0.95, "Enhanced first result", {"enhanced": True}),
            SearchResult("doc2", 0.75, "Enhanced second result", {"enhanced": True})
        ]
        return enhancer

    @pytest.fixture
    def mock_integration(self):
        """Create mock integration."""
        integration = AsyncMock(spec=ConPortAdapter)
        integration.validate_connection.return_value = True
        integration.enhance_search_results.return_value = [
            SearchResult("doc1", 0.95, "Context enhanced", {"context": "added"}),
            SearchResult("doc2", 0.75, "Context enhanced", {"context": "added"})
        ]
        return integration

    @pytest.fixture
    def search_pipeline(self, config, mock_vector_store, mock_enhancer, mock_integration):
        """Create search pipeline."""
        return SearchPipeline(
            config=config,
            vector_store=mock_vector_store,
            enhancer=mock_enhancer,
            integrations=[mock_integration]
        )

    def test_search_pipeline_initialization(self, search_pipeline, config):
        """Test search pipeline initialization."""
        assert search_pipeline.config == config
        assert search_pipeline.vector_store is not None
        assert search_pipeline.enhancer is not None
        assert len(search_pipeline.integrations) == 1

    @pytest.mark.asyncio
    async def test_validate_inputs_valid_query(self, search_pipeline):
        """Test input validation with valid search query."""
        is_valid = await search_pipeline.validate_inputs("machine learning", {"k": 10})
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_inputs_invalid_query(self, search_pipeline):
        """Test input validation with invalid queries."""
        # Empty query
        is_valid = await search_pipeline.validate_inputs("", {"k": 10})
        assert is_valid is False

        # Non-string query
        is_valid = await search_pipeline.validate_inputs(123, {"k": 10})
        assert is_valid is False

        # Invalid k parameter
        is_valid = await search_pipeline.validate_inputs("test", {"k": -1})
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_execute_search_pipeline_success(self, search_pipeline):
        """Test successful search pipeline execution."""
        result = await search_pipeline.execute("machine learning", k=5)

        assert isinstance(result, PipelineResult)
        assert result.success is True
        assert result.stage == PipelineStage.COMPLETION
        assert "search_results" in result.metadata

    @pytest.mark.asyncio
    async def test_search_stage_execution(self, search_pipeline):
        """Test search stage execution."""
        search_pipeline.query = "test query"
        search_pipeline.search_params = {"k": 5, "enable_reranking": True}

        stage_result = await search_pipeline._search_stage()

        assert stage_result["results_count"] == 2
        assert stage_result["search_method"] == "hybrid"
        assert stage_result["reranking_enabled"] is True
        # Should have called vector store
        search_pipeline.vector_store.hybrid_search.assert_called_with(
            query="test query",
            k=5,
            enable_reranking=True
        )

    @pytest.mark.asyncio
    async def test_enhancement_stage_with_consensus(self, search_pipeline):
        """Test enhancement stage with consensus validation."""
        search_pipeline.raw_results = [
            SearchResult("doc1", 0.9, "Content", {}),
            SearchResult("doc2", 0.7, "Content", {})
        ]
        search_pipeline.query = "test query"
        search_pipeline.search_params = {"enable_enhancement": True}

        stage_result = await search_pipeline._enhancement_stage()

        assert "enhanced_count" in stage_result
        assert stage_result["final_results_count"] == 2
        # Should have called enhancer
        search_pipeline.enhancer.enhance_results.assert_called()

    @pytest.mark.asyncio
    async def test_enhancement_stage_with_integrations(self, search_pipeline):
        """Test enhancement stage with integration enrichment."""
        search_pipeline.raw_results = [SearchResult("doc1", 0.9, "Content", {})]
        search_pipeline.enhanced_results = [SearchResult("doc1", 0.9, "Content", {})]
        search_pipeline.query = "test query"
        search_pipeline.search_params = {"search_context": {"user_intent": "learning"}}

        stage_result = await search_pipeline._enhancement_stage()

        # Should have enhanced with integration
        search_pipeline.integrations[0].enhance_search_results.assert_called()

    @pytest.mark.asyncio
    async def test_completion_stage_adds_adhd_metadata(self, search_pipeline):
        """Test completion stage adds ADHD-friendly metadata."""
        search_pipeline.enhanced_results = [
            SearchResult("doc1", 0.9, "Long content " * 100, {}),
            SearchResult("doc2", 0.7, "Short content", {})
        ]

        stage_result = await search_pipeline._completion_stage()

        # Should have added ADHD metadata
        result1 = search_pipeline.enhanced_results[0]
        assert "result_rank" in result1.metadata
        assert "estimated_reading_time" in result1.metadata
        assert "complexity" in result1.metadata
        assert "relevance" in result1.metadata

    @pytest.mark.asyncio
    async def test_search_with_empty_vector_store(self, search_pipeline):
        """Test search with empty vector store."""
        # Mock empty store
        search_pipeline.vector_store.get_stats.return_value = {"documents": {"document_count": 0}}
        search_pipeline.vector_store.hybrid_search.return_value = []

        result = await search_pipeline.execute("test query")

        # Should still succeed but with no results
        assert result.success is True
        assert result.metadata["results_count"] == 0

    @pytest.mark.asyncio
    async def test_get_search_status(self, search_pipeline):
        """Test getting search status."""
        search_pipeline.pipeline_id = "search_123"
        search_pipeline.current_stage = PipelineStage.PROCESSING
        search_pipeline.query = "test query"

        status = await search_pipeline.get_search_status()

        assert status["pipeline_id"] == "search_123"
        assert status["query"] == "test query"
        assert status["current_stage"] == "processing"

    def test_display_results_console_output(self, search_pipeline):
        """Test displaying results to console."""
        search_pipeline.enhanced_results = [
            SearchResult("doc1", 0.9, "High quality content", {"relevance": "high"}),
            SearchResult("doc2", 0.7, "Medium quality content", {"relevance": "medium"})
        ]
        search_pipeline.query = "test query"
        search_pipeline.start_time = datetime.now()

        with patch('builtins.print') as mock_print:
            search_pipeline.display_results(max_results=2)

            # Should have printed formatted results
            mock_print.assert_called()
            print_calls = [str(call) for call in mock_print.call_args_list]
            result_output = ' '.join(print_calls)

            assert "test query" in result_output
            assert "doc1" in result_output
            assert "🟢" in result_output  # High relevance emoji


class TestSyncPipeline:
    """Test synchronization pipeline."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return AdvancedEmbeddingConfig(enable_progress_tracking=True)

    @pytest.fixture
    def mock_vector_store(self):
        """Create mock vector store."""
        store = AsyncMock(spec=HybridVectorStore)
        store.get_stats.return_value = {"documents": {"document_count": 100}}
        return store

    @pytest.fixture
    def mock_integrations(self):
        """Create mock integrations."""
        integration1 = AsyncMock(spec=ConPortAdapter)
        integration1.validate_connection.return_value = True
        integration1.get_sync_status.return_value = {"last_sync": "2024-01-01T00:00:00"}

        integration2 = AsyncMock(spec=ConPortAdapter)
        integration2.validate_connection.return_value = True
        integration2.get_sync_status.return_value = {"last_sync": "2024-01-01T00:00:00"}

        return [integration1, integration2]

    @pytest.fixture
    def sync_pipeline(self, config, mock_vector_store, mock_integrations):
        """Create sync pipeline."""
        return SyncPipeline(
            config=config,
            vector_store=mock_vector_store,
            integrations=mock_integrations
        )

    def test_sync_pipeline_initialization(self, sync_pipeline, config):
        """Test sync pipeline initialization."""
        assert sync_pipeline.config == config
        assert sync_pipeline.vector_store is not None
        assert len(sync_pipeline.integrations) == 2

    @pytest.mark.asyncio
    async def test_execute_sync_pipeline_success(self, sync_pipeline):
        """Test successful sync pipeline execution."""
        sync_config = {
            "sync_direction": "bidirectional",
            "conflict_resolution": "latest_wins",
            "incremental": True
        }

        result = await sync_pipeline.execute(sync_config)

        assert isinstance(result, PipelineResult)
        assert result.success is True
        assert result.stage == PipelineStage.COMPLETION

    @pytest.mark.asyncio
    async def test_sync_validation_stage(self, sync_pipeline):
        """Test sync validation stage."""
        sync_config = {"sync_direction": "push"}

        stage_result = await sync_pipeline._validate_stage(sync_config)

        assert "integration_health" in stage_result
        assert stage_result["vector_store_ready"] is True

    @pytest.mark.asyncio
    async def test_incremental_sync(self, sync_pipeline):
        """Test incremental synchronization."""
        sync_pipeline.sync_config = {"incremental": True, "since_timestamp": "2024-01-01T00:00:00"}

        stage_result = await sync_pipeline._sync_stage()

        assert stage_result["sync_type"] == "incremental"
        assert "items_synced" in stage_result

    @pytest.mark.asyncio
    async def test_full_sync(self, sync_pipeline):
        """Test full synchronization."""
        sync_pipeline.sync_config = {"incremental": False}

        stage_result = await sync_pipeline._sync_stage()

        assert stage_result["sync_type"] == "full"

    @pytest.mark.asyncio
    async def test_conflict_resolution(self, sync_pipeline):
        """Test conflict resolution during sync."""
        # Simulate conflicts
        conflicts = [
            {"id": "doc1", "local_version": 1, "remote_version": 2},
            {"id": "doc2", "local_version": 3, "remote_version": 2}
        ]

        resolved = await sync_pipeline._resolve_conflicts(conflicts, "latest_wins")

        # Should resolve all conflicts
        assert len(resolved) == 2
        # Should pick latest versions
        assert all(r["resolved"] for r in resolved)

    @pytest.mark.asyncio
    async def test_sync_pipeline_with_failures(self, sync_pipeline):
        """Test sync pipeline with some integration failures."""
        # Make one integration fail
        sync_pipeline.integrations[0].validate_connection.return_value = False

        result = await sync_pipeline.execute({"sync_direction": "push"})

        # Should still succeed with partial sync
        assert result.success is True
        assert "partial_success" in str(result.metadata)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=dopemux.embeddings.pipelines", "--cov-report=term-missing"])