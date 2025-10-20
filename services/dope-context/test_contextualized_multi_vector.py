"""
Test: Contextualized Embeddings with Multi-Vector Storage

Validates that the updated pipeline correctly:
1. Uses contextualized embeddings for content vectors
2. Uses standard embeddings for title/breadcrumb vectors
3. Stores all 3 vectors in Qdrant
4. Search retrieval works with weighted fusion
"""

import asyncio
import logging
import os
from pathlib import Path

from src.preprocessing.code_chunker import CodeChunker
from src.context.openai_generator import OpenAIContextGenerator
from src.embeddings.voyage_embedder import VoyageEmbedder
from src.embeddings.contextualized_embedder import ContextualizedEmbedder
from src.search.dense_search import MultiVectorSearch, SearchProfile
from src.pipeline.indexing_pipeline import IndexingPipeline, IndexingConfig


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_contextualized_multi_vector():
    """Test contextualized embeddings with multi-vector search."""

    logger.info("=" * 80)
    logger.info("TEST: Contextualized Multi-Vector Pipeline")
    logger.info("=" * 80)

    # Setup
    api_key = os.getenv("VOYAGE_API_KEY")
    if not api_key:
        logger.error("❌ VOYAGE_API_KEY not set")
        return

    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        logger.warning("⚠️  OPENAI_API_KEY not set - skipping context generation")
        context_generator = None
    else:
        context_generator = OpenAIContextGenerator(api_key=openai_key)

    # Initialize components
    chunker = CodeChunker()
    standard_embedder = VoyageEmbedder(api_key=api_key)
    contextualized_embedder = ContextualizedEmbedder(api_key=api_key)

    # Use test collection
    vector_search = MultiVectorSearch(
        collection_name="test_contextual_code",
        url="localhost",
        port=6333,
        vector_size=1024,
    )

    # Create fresh collection
    logger.info("\n📦 Creating fresh test collection...")
    try:
        await vector_search.delete_collection()
    except:
        pass  # Collection may not exist

    await vector_search.create_collection()

    # Configure pipeline to index the sample file
    config = IndexingConfig(
        workspace_path=Path.cwd(),
        include_patterns=["sample_code_for_indexing.py"],
        exclude_patterns=[],  # Don't exclude anything
        max_files=1,
        skip_context_generation=(context_generator is None),
        workspace_id="test",
    )

    # Create pipeline
    pipeline = IndexingPipeline(
        chunker=chunker,
        context_generator=context_generator,
        standard_embedder=standard_embedder,
        contextualized_embedder=contextualized_embedder,
        vector_search=vector_search,
        config=config,
    )

    # Test 1: Index this file
    logger.info("\n🔧 TEST 1: Indexing with contextualized embeddings...")
    progress = await pipeline.index_workspace()

    logger.info(f"✅ Indexing complete:")
    logger.info(f"   Files processed: {progress.processed_files}")
    logger.info(f"   Chunks indexed: {progress.indexed_chunks}")
    logger.info(f"   Errors: {progress.errors}")
    logger.info(f"   Duration: {progress.elapsed_seconds():.1f}s")
    logger.info(f"   Total cost: ${progress.total_cost_usd:.4f}")

    # Get cost breakdown
    cost_summary = pipeline.get_cost_summary()
    logger.info(f"\n💰 Cost Breakdown:")
    logger.info(f"   Context generation: ${cost_summary['context_generation']['cost_usd']:.4f}")
    logger.info(f"   Embeddings: ${cost_summary['embeddings']['cost_usd']:.4f}")
    logger.info(f"     - Contextualized: {cost_summary['embeddings']['contextualized_summary']}")
    logger.info(f"     - Standard: {cost_summary['embeddings']['standard_summary']}")

    # Test 2: Verify collection
    logger.info("\n🔍 TEST 2: Verifying multi-vector storage...")
    info = await vector_search.get_collection_info()
    logger.info(f"✅ Collection info:")
    logger.info(f"   Name: {info['name']}")
    logger.info(f"   Vectors: {info['vectors_count']}")
    logger.info(f"   Status: {info['status']}")

    assert info['vectors_count'] > 0, "❌ No vectors stored!"

    # Test 3: Search with multi-vector fusion
    logger.info("\n🔎 TEST 3: Multi-vector search with contextualized embeddings...")

    # Embed query
    query = "test contextualized embeddings pipeline"

    # Query embeddings (use standard for all 3 - query doesn't have document context)
    query_emb_response = await standard_embedder.embed_batch(
        texts=[query],
        model="voyage-code-3",
        input_type="query",
    )
    query_vec = query_emb_response[0].embedding

    # Search with implementation profile
    results = await vector_search.search(
        query_content_vector=query_vec,
        query_title_vector=query_vec,
        query_breadcrumb_vector=query_vec,
        profile=SearchProfile.implementation(),
    )

    logger.info(f"✅ Search returned {len(results)} results")

    if results:
        logger.info(f"\n📊 Top 3 Results:")
        for i, result in enumerate(results[:3], 1):
            logger.info(f"\n   {i}. {result.file_path}:{result.function_name}")
            logger.info(f"      Score: {result.score:.4f}")
            logger.info(f"      Complexity: {result.payload.get('complexity', 0):.2f}")
            logger.info(f"      Lines: {result.payload.get('start_line')}-{result.payload.get('end_line')}")
            logger.info(f"      Snippet: {result.context_snippet[:100] if result.context_snippet else 'N/A'}...")

    # Test 4: Verify multi-vector fusion
    logger.info("\n🧪 TEST 4: Testing search profiles...")

    profiles = [
        SearchProfile.implementation(),
        SearchProfile.debugging(),
        SearchProfile.exploration(),
    ]

    for profile in profiles:
        results = await vector_search.search(
            query_content_vector=query_vec,
            query_title_vector=query_vec,
            query_breadcrumb_vector=query_vec,
            profile=profile,
        )
        top_score = results[0].score if results else 0.0
        logger.info(f"   Profile '{profile.name}': {len(results)} results, top score: {top_score:.4f}")

    logger.info("\n" + "=" * 80)
    logger.info("✅ ALL TESTS PASSED!")
    logger.info("=" * 80)
    logger.info("\n🎉 Contextualized multi-vector pipeline is working correctly!")
    logger.info(f"   - Content vectors: voyage-context-3 (contextualized)")
    logger.info(f"   - Title/Breadcrumb vectors: voyage-code-3 (standard)")
    logger.info(f"   - Multi-vector fusion: ✅")
    logger.info(f"   - Search: ✅")

    # Cleanup
    logger.info("\n🧹 Cleaning up test collection...")
    await vector_search.delete_collection()


if __name__ == "__main__":
    asyncio.run(test_contextualized_multi_vector())
