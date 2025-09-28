"""
Integration tests for the complete embedding system.

Tests end-to-end workflows including document processing, search, and integrations.
"""

import pytest
import numpy as np
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from dopemux.embeddings import (
    AdvancedEmbeddingConfig,
    HybridVectorStore,
    VoyageAPIClient,
    ConsensusValidator,
    ConPortAdapter,
    DocumentPipeline,
    SearchPipeline,
    create_production_config
)
from dopemux.embeddings.core import SecurityLevel, IndexType


@pytest.mark.integration
class TestEmbeddingSystemIntegration:
    """Integration tests for the complete embedding system."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test storage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def production_config(self):
        """Create production-like configuration."""
        return create_production_config(
            embedding_dimension=384,  # Smaller for testing
            batch_size=2,
            enable_progress_tracking=False  # Reduce noise in tests
        )

    @pytest.fixture
    def mock_voyage_client(self):
        """Create mock Voyage API client."""
        client = AsyncMock(spec=VoyageAPIClient)

        # Mock embedding responses with consistent dimensions
        def mock_embed_texts(texts):
            return [np.random.random(384).tolist() for _ in texts]

        client.embed_texts.side_effect = mock_embed_texts
        client.validate_connection.return_value = True
        return client

    @pytest.fixture
    def mock_conport_client(self):
        """Create mock ConPort client."""
        client = AsyncMock()
        client.get_active_context.return_value = {"status": "active"}
        client.log_custom_data.return_value = None
        client.semantic_search_conport.return_value = []
        return client

    @pytest.fixture
    async def vector_store(self, production_config, mock_voyage_client, temp_dir):
        """Create initialized vector store."""
        store = HybridVectorStore(production_config, api_client=mock_voyage_client)
        await store.initialize()
        return store

    @pytest.fixture
    def consensus_validator(self, production_config):
        """Create consensus validator with mocked providers."""
        with patch.multiple(
            'dopemux.embeddings.enhancers.consensus',
            openai=MagicMock(),
            cohere=MagicMock(),
            AsyncOpenAI=MagicMock()
        ):
            validator = ConsensusValidator(production_config)
            return validator

    @pytest.fixture
    def conport_adapter(self, production_config, mock_conport_client):
        """Create ConPort adapter."""
        return ConPortAdapter(
            production_config,
            workspace_id="/test/workspace",
            conport_client=mock_conport_client
        )

    @pytest.mark.asyncio
    async def test_end_to_end_document_processing(
        self,
        production_config,
        vector_store,
        mock_voyage_client,
        consensus_validator,
        conport_adapter
    ):
        """Test complete document processing workflow."""
        # Create document pipeline
        pipeline = DocumentPipeline(
            config=production_config,
            vector_store=vector_store,
            provider=mock_voyage_client,
            enhancer=consensus_validator,
            integrations=[conport_adapter]
        )

        # Test documents
        documents = [
            {
                "id": "doc1",
                "content": "Machine learning algorithms for data analysis",
                "metadata": {"type": "technical", "author": "research_team"}
            },
            {
                "id": "doc2",
                "content": "User guide for getting started with the platform",
                "metadata": {"type": "documentation", "level": "beginner"}
            },
            {
                "id": "doc3",
                "content": "Advanced neural network architectures and deep learning",
                "metadata": {"type": "technical", "level": "advanced"}
            }
        ]

        # Execute pipeline
        result = await pipeline.execute(documents)

        # Verify successful processing
        assert result.success is True
        assert result.metadata["documents_processed"] == 3
        assert result.metadata["documents_failed"] == 0

        # Verify documents were stored
        store_stats = vector_store.get_stats()
        assert store_stats["documents"]["document_count"] == 3

        # Verify embeddings were generated
        mock_voyage_client.embed_texts.assert_called()

        # Verify integration was called
        conport_adapter.conport_client.log_custom_data.assert_called()

    @pytest.mark.asyncio
    async def test_end_to_end_search_workflow(
        self,
        production_config,
        vector_store,
        mock_voyage_client,
        consensus_validator,
        conport_adapter
    ):
        """Test complete search workflow."""
        # First, add some documents
        documents = [
            {"id": "ml_doc", "content": "Machine learning and artificial intelligence"},
            {"id": "web_doc", "content": "Web development with JavaScript and React"},
            {"id": "data_doc", "content": "Data science and statistical analysis"}
        ]
        await vector_store.add_documents(documents)

        # Create search pipeline
        search_pipeline = SearchPipeline(
            config=production_config,
            vector_store=vector_store,
            provider=mock_voyage_client,
            enhancer=consensus_validator,
            integrations=[conport_adapter]
        )

        # Execute search
        result = await search_pipeline.execute(
            query="machine learning algorithms",
            k=2,
            enable_reranking=True,
            enable_enhancement=True
        )

        # Verify successful search
        assert result.success is True
        assert "search_results" in result.metadata
        assert len(result.metadata["search_results"]) <= 2

        # Verify search results have proper structure
        search_results = search_pipeline.get_results()
        for sr in search_results:
            assert hasattr(sr, 'doc_id')
            assert hasattr(sr, 'score')
            assert hasattr(sr, 'content')
            assert isinstance(sr.metadata, dict)

    @pytest.mark.asyncio
    async def test_hybrid_search_functionality(self, vector_store, mock_voyage_client):
        """Test hybrid search combining vector and lexical search."""
        # Add test documents with diverse content
        documents = [
            {"id": "exact_match", "content": "machine learning algorithms optimization"},
            {"id": "semantic_match", "content": "AI models for pattern recognition"},
            {"id": "unrelated", "content": "cooking recipes and kitchen tips"}
        ]
        await vector_store.add_documents(documents)

        # Test lexical search (should find exact_match first)
        lexical_results = await vector_store.lexical_search("machine learning", k=3)
        assert len(lexical_results) > 0
        assert lexical_results[0].doc_id == "exact_match"

        # Test vector search (should find semantic similarities)
        query_vector = np.random.random(384)  # Match config dimension
        vector_results = await vector_store.vector_search(query_vector, k=3)
        assert len(vector_results) <= 3

        # Test hybrid search (should combine both approaches)
        hybrid_results = await vector_store.hybrid_search("machine learning", k=3)
        assert len(hybrid_results) <= 3

        # Should include results from both lexical and semantic search
        doc_ids = [r.doc_id for r in hybrid_results]
        assert "exact_match" in doc_ids or "semantic_match" in doc_ids

    @pytest.mark.asyncio
    async def test_document_update_and_deletion(self, vector_store, mock_voyage_client):
        """Test document update and deletion operations."""
        # Add initial document
        initial_doc = {"id": "update_test", "content": "Original content"}
        await vector_store.add_documents([initial_doc])

        # Verify document exists
        results = await vector_store.lexical_search("Original", k=1)
        assert len(results) == 1
        assert results[0].doc_id == "update_test"

        # Update document
        updated_doc = {"id": "update_test", "content": "Updated machine learning content"}
        await vector_store.update_document("update_test", updated_doc)

        # Verify update worked
        results = await vector_store.lexical_search("machine learning", k=1)
        assert len(results) == 1
        assert results[0].doc_id == "update_test"

        # Old content should not be found
        results = await vector_store.lexical_search("Original", k=10)
        update_test_results = [r for r in results if r.doc_id == "update_test"]
        assert len(update_test_results) == 0

        # Delete document
        await vector_store.delete_document("update_test")

        # Verify deletion
        stats = vector_store.get_stats()
        # Document count should reflect deletion
        assert stats["documents"]["document_count"] == 0

    @pytest.mark.asyncio
    async def test_consensus_validation_integration(
        self,
        production_config,
        consensus_validator
    ):
        """Test consensus validation with multiple providers."""
        # Mock provider responses
        with patch.object(consensus_validator, '_get_provider_assessment') as mock_assess:
            # Mock consistent high-quality responses
            mock_assess.side_effect = [
                {"quality_score": 0.85, "confidence": 0.9, "reasoning": "High quality technical content"},
                {"quality_score": 0.82, "confidence": 0.88, "reasoning": "Well-structured information"}
            ]

            result = await consensus_validator.validate_quality(
                doc_id="test_doc",
                content="Comprehensive guide to machine learning algorithms with practical examples",
                embedding=[0.1] * 384
            )

            # Should reach consensus
            assert result.consensus_reached is True
            assert result.overall_quality_score > 0.8
            assert len(result.provider_results) == 2

    @pytest.mark.asyncio
    async def test_conport_integration_workflow(
        self,
        production_config,
        conport_adapter,
        mock_conport_client
    ):
        """Test ConPort integration workflow."""
        # Test connection validation
        is_connected = await conport_adapter.validate_connection()
        assert is_connected is True

        # Test storing embeddings
        documents = [
            {
                "id": "conport_test",
                "content": "Test document for ConPort integration",
                "metadata": {"urgency": "high", "complexity": "medium"}
            }
        ]
        embeddings = [[0.1] * 384]

        await conport_adapter.store_embeddings(documents, embeddings)

        # Verify ConPort client was called
        mock_conport_client.log_custom_data.assert_called()
        call_args = mock_conport_client.log_custom_data.call_args[1]

        assert call_args["category"] == "DocumentEmbeddings"
        assert "conport_test" in call_args["key"]
        assert "adhd_metadata" in call_args["value"]

    @pytest.mark.asyncio
    async def test_error_handling_and_resilience(
        self,
        production_config,
        vector_store,
        mock_voyage_client,
        conport_adapter
    ):
        """Test system resilience to various error conditions."""
        # Create pipeline
        pipeline = DocumentPipeline(
            config=production_config,
            vector_store=vector_store,
            provider=mock_voyage_client,
            integrations=[conport_adapter]
        )

        # Test with invalid documents (should handle gracefully)
        invalid_documents = [
            {"id": "valid_doc", "content": "Valid content"},
            {"missing_content": "This doc has no content field"},
            {"id": "empty_content", "content": ""}
        ]

        result = await pipeline.execute(invalid_documents)

        # Should process valid documents despite invalid ones
        assert result.metadata["documents_processed"] >= 1

        # Test provider failure handling
        mock_voyage_client.embed_texts.side_effect = Exception("API Rate Limit")

        result = await pipeline.execute([{"id": "test", "content": "test content"}])

        # Should handle provider failure gracefully
        assert result.success is False
        assert "error" in str(result.errors[0]).lower()

    @pytest.mark.asyncio
    async def test_performance_with_large_batch(
        self,
        production_config,
        vector_store,
        mock_voyage_client
    ):
        """Test system performance with larger document batches."""
        # Create large batch of documents
        documents = [
            {
                "id": f"perf_doc_{i}",
                "content": f"Performance test document {i} with machine learning content",
                "metadata": {"batch": "performance_test", "index": i}
            }
            for i in range(20)  # Larger batch
        ]

        # Create pipeline
        pipeline = DocumentPipeline(
            config=production_config,
            vector_store=vector_store,
            provider=mock_voyage_client
        )

        # Measure processing time
        import time
        start_time = time.time()

        result = await pipeline.execute(documents)

        end_time = time.time()
        processing_time = end_time - start_time

        # Verify all documents processed
        assert result.success is True
        assert result.metadata["documents_processed"] == 20

        # Performance should be reasonable (adjust threshold as needed)
        assert processing_time < 30  # Should complete within 30 seconds

        # Verify batching occurred (should make multiple API calls)
        call_count = mock_voyage_client.embed_texts.call_count
        expected_batches = (20 + production_config.batch_size - 1) // production_config.batch_size
        assert call_count == expected_batches

    @pytest.mark.asyncio
    async def test_configuration_variations(self, mock_voyage_client, temp_dir):
        """Test system behavior with different configuration options."""
        # Test high-security configuration
        secure_config = AdvancedEmbeddingConfig(
            security_level=SecurityLevel.RESTRICTED,
            enable_pii_detection=True,
            pii_redaction_mode="remove",
            embedding_dimension=384
        )

        secure_store = HybridVectorStore(secure_config, api_client=mock_voyage_client)
        await secure_store.initialize()

        # Should handle PII-containing documents
        pii_docs = [
            {
                "id": "pii_test",
                "content": "Contact John at john.doe@email.com for support, phone: 555-123-4567",
                "metadata": {"contains_pii": True}
            }
        ]

        # Should process successfully (PII handling mocked)
        await secure_store.add_documents(pii_docs)

        # Test research configuration
        research_config = AdvancedEmbeddingConfig(
            enable_consensus_validation=True,
            enable_reranking=True,
            enable_quantization=True,
            embedding_dimension=384
        )

        research_store = HybridVectorStore(research_config, api_client=mock_voyage_client)
        await research_store.initialize()

        # Should handle research workflows
        research_docs = [{"id": "research_doc", "content": "Research methodology and analysis"}]
        await research_store.add_documents(research_docs)

        results = await research_store.hybrid_search("research", k=1, enable_reranking=True)
        assert len(results) <= 1

    @pytest.mark.asyncio
    async def test_concurrent_operations(
        self,
        production_config,
        vector_store,
        mock_voyage_client
    ):
        """Test concurrent document processing and search operations."""
        # Prepare documents for concurrent processing
        doc_batches = [
            [{"id": f"batch1_doc{i}", "content": f"Batch 1 content {i}"} for i in range(3)],
            [{"id": f"batch2_doc{i}", "content": f"Batch 2 content {i}"} for i in range(3)],
            [{"id": f"batch3_doc{i}", "content": f"Batch 3 content {i}"} for i in range(3)]
        ]

        # Create multiple pipelines
        pipelines = [
            DocumentPipeline(
                config=production_config,
                vector_store=vector_store,
                provider=mock_voyage_client
            )
            for _ in range(3)
        ]

        # Execute concurrent processing
        tasks = [
            pipeline.execute(batch)
            for pipeline, batch in zip(pipelines, doc_batches)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should succeed
        for result in results:
            assert not isinstance(result, Exception)
            assert result.success is True

        # Verify all documents were processed
        stats = vector_store.get_stats()
        assert stats["documents"]["document_count"] == 9  # 3 batches × 3 docs each

    @pytest.mark.asyncio
    async def test_system_health_monitoring(
        self,
        production_config,
        vector_store,
        mock_voyage_client,
        consensus_validator,
        conport_adapter
    ):
        """Test system health monitoring and metrics collection."""
        # Test component health checks
        store_healthy = await vector_store.validate_connection()
        assert store_healthy is True

        provider_healthy = await mock_voyage_client.validate_connection()
        assert provider_healthy is True

        validator_healthy = await consensus_validator.validate_connection()
        assert validator_healthy is True

        adapter_healthy = await conport_adapter.validate_connection()
        assert adapter_healthy is True

        # Test metrics collection
        store_stats = vector_store.get_stats()
        assert "documents" in store_stats
        assert "vector_index" in store_stats
        assert "lexical_index" in store_stats

        # Test enhancement metrics
        enhancement_stats = consensus_validator.get_enhancement_stats()
        assert "total_validations" in enhancement_stats
        assert "consensus_rate" in enhancement_stats

        # Test provider metrics
        provider_metrics = await mock_voyage_client.get_health_metrics()
        assert hasattr(provider_metrics, 'provider_name')


if __name__ == "__main__":
    pytest.main([
        __file__,
        "-v",
        "-m", "integration",
        "--cov=dopemux.embeddings",
        "--cov-report=term-missing"
    ])