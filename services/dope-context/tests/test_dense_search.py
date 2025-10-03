"""
Tests for Multi-Vector Dense Search - Task 4
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.search.dense_search import (
    MultiVectorSearch,
    SearchProfile,
    SearchResult,
)


@pytest.fixture
def search():
    """Create MultiVectorSearch instance with mocked client."""
    with patch("src.search.dense_search.AsyncQdrantClient") as mock_client:
        mock_instance = AsyncMock()
        mock_client.return_value = mock_instance

        search = MultiVectorSearch(
            collection_name="test_collection",
            url="localhost",
            port=6333,
        )

        # Store mock for access in tests
        search._mock_client = mock_instance

        return search


@pytest.fixture
def sample_vectors():
    """Create sample vectors."""
    return {
        "content": [0.1] * 1024,
        "title": [0.2] * 1024,
        "breadcrumb": [0.3] * 1024,
    }


@pytest.fixture
def sample_payload():
    """Create sample payload."""
    return {
        "file_path": "src/utils.py",
        "function_name": "calculate",
        "language": "python",
        "raw_code": "def calculate(): pass",
        "context_snippet": "Test function",
        "workspace_id": "test-workspace",
    }


def test_search_profiles():
    """Test search profile configurations."""
    # Implementation profile
    impl = SearchProfile.implementation()
    assert impl.top_k == 100
    assert impl.content_weight == 0.7
    assert impl.title_weight == 0.2
    assert impl.breadcrumb_weight == 0.1
    assert impl.ef == 150

    # Debugging profile
    debug = SearchProfile.debugging()
    assert debug.top_k == 50
    assert debug.content_weight == 0.5
    assert debug.title_weight == 0.4

    # Exploration profile
    explore = SearchProfile.exploration()
    assert explore.top_k == 200
    assert explore.breadcrumb_weight == 0.2


@pytest.mark.asyncio
async def test_create_collection(search):
    """Test collection creation."""
    # Mock no existing collections
    mock_collections = MagicMock()
    mock_collections.collections = []
    search._mock_client.get_collections.return_value = mock_collections

    await search.create_collection()

    # Verify create_collection was called
    search._mock_client.create_collection.assert_called_once()

    call_kwargs = search._mock_client.create_collection.call_args[1]
    assert call_kwargs["collection_name"] == "test_collection"
    assert "content_vec" in call_kwargs["vectors_config"]
    assert "title_vec" in call_kwargs["vectors_config"]
    assert "breadcrumb_vec" in call_kwargs["vectors_config"]


@pytest.mark.asyncio
async def test_create_collection_already_exists(search):
    """Test collection creation when already exists."""
    # Mock existing collection
    mock_collection = MagicMock()
    mock_collection.name = "test_collection"

    mock_collections = MagicMock()
    mock_collections.collections = [mock_collection]
    search._mock_client.get_collections.return_value = mock_collections

    await search.create_collection()

    # Should not create
    search._mock_client.create_collection.assert_not_called()


@pytest.mark.asyncio
async def test_insert_point(search, sample_vectors, sample_payload):
    """Test single point insertion."""
    point_id = await search.insert_point(
        content_vector=sample_vectors["content"],
        title_vector=sample_vectors["title"],
        breadcrumb_vector=sample_vectors["breadcrumb"],
        payload=sample_payload,
    )

    assert isinstance(point_id, str)
    search._mock_client.upsert.assert_called_once()

    call_args = search._mock_client.upsert.call_args[1]
    assert call_args["collection_name"] == "test_collection"
    assert len(call_args["points"]) == 1


@pytest.mark.asyncio
async def test_insert_point_with_custom_id(search, sample_vectors, sample_payload):
    """Test point insertion with custom ID."""
    custom_id = "custom-id-123"

    point_id = await search.insert_point(
        content_vector=sample_vectors["content"],
        title_vector=sample_vectors["title"],
        breadcrumb_vector=sample_vectors["breadcrumb"],
        payload=sample_payload,
        point_id=custom_id,
    )

    assert point_id == custom_id


@pytest.mark.asyncio
async def test_insert_points_batch(search, sample_vectors, sample_payload):
    """Test batch point insertion."""
    points = [
        (
            sample_vectors["content"],
            sample_vectors["title"],
            sample_vectors["breadcrumb"],
            sample_payload,
            None,
        )
        for _ in range(5)
    ]

    point_ids = await search.insert_points_batch(points)

    assert len(point_ids) == 5
    search._mock_client.upsert.assert_called_once()

    call_args = search._mock_client.upsert.call_args[1]
    assert len(call_args["points"]) == 5


@pytest.mark.asyncio
async def test_search_multi_vector(search, sample_vectors):
    """Test multi-vector search with weighted fusion."""

    # Mock search results for each vector
    def create_mock_result(point_id, score):
        result = MagicMock()
        result.id = point_id
        result.score = score
        result.payload = {
            "file_path": f"file{point_id}.py",
            "function_name": f"func{point_id}",
            "language": "python",
            "raw_code": "code",
        }
        return result

    # Content results
    search._mock_client.search.side_effect = [
        [create_mock_result("1", 0.9), create_mock_result("2", 0.8)],  # content
        [create_mock_result("1", 0.85), create_mock_result("3", 0.75)],  # title
        [create_mock_result("2", 0.88), create_mock_result("3", 0.70)],  # breadcrumb
    ]

    results = await search.search(
        query_content_vector=sample_vectors["content"],
        query_title_vector=sample_vectors["title"],
        query_breadcrumb_vector=sample_vectors["breadcrumb"],
        profile=SearchProfile.implementation(),
    )

    # Should call search 3 times (one for each vector)
    assert search._mock_client.search.call_count == 3

    # Should return fused results
    assert len(results) > 0
    assert all(isinstance(r, SearchResult) for r in results)

    # Results should be sorted by fused score
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)


@pytest.mark.asyncio
async def test_search_with_filter(search, sample_vectors):
    """Test search with filters."""
    search._mock_client.search.return_value = []

    await search.search(
        query_content_vector=sample_vectors["content"],
        query_title_vector=sample_vectors["title"],
        query_breadcrumb_vector=sample_vectors["breadcrumb"],
        filter_by={"language": "python", "workspace_id": "test"},
    )

    # Verify filter was passed to search calls
    calls = search._mock_client.search.call_args_list
    for call in calls:
        assert call[1]["query_filter"] is not None


@pytest.mark.asyncio
async def test_search_with_different_profiles(search, sample_vectors):
    """Test search with different profiles."""
    search._mock_client.search.return_value = []

    # Debugging profile
    await search.search(
        query_content_vector=sample_vectors["content"],
        query_title_vector=sample_vectors["title"],
        query_breadcrumb_vector=sample_vectors["breadcrumb"],
        profile=SearchProfile.debugging(),
    )

    # Verify top_k and ef from profile
    calls = search._mock_client.search.call_args_list
    for call in calls:
        assert call[1]["limit"] == 50  # debugging profile top_k
        assert call[1]["search_params"].hnsw_ef == 120  # debugging profile ef


@pytest.mark.asyncio
async def test_delete_points(search):
    """Test point deletion."""
    point_ids = ["id1", "id2", "id3"]

    await search.delete_points(point_ids)

    search._mock_client.delete.assert_called_once()
    call_args = search._mock_client.delete.call_args[1]
    assert call_args["collection_name"] == "test_collection"


@pytest.mark.asyncio
async def test_delete_collection(search):
    """Test collection deletion."""
    await search.delete_collection()

    search._mock_client.delete_collection.assert_called_once_with(
        collection_name="test_collection"
    )


@pytest.mark.asyncio
async def test_get_collection_info(search):
    """Test getting collection information."""
    mock_info = MagicMock()
    mock_info.config = MagicMock()
    mock_info.config.name = "test_collection"
    mock_info.points_count = 100
    mock_info.status = "green"

    search._mock_client.get_collection.return_value = mock_info

    info = await search.get_collection_info()

    assert info["name"] == "test_collection"
    assert info["vectors_count"] == 100
    assert info["status"] == "green"


def test_search_result_creation():
    """Test SearchResult dataclass."""
    result = SearchResult(
        id="test-id",
        score=0.95,
        payload={"key": "value"},
        file_path="src/test.py",
        function_name="test_func",
        language="python",
        content="def test_func(): pass",
        context_snippet="Test function",
    )

    assert result.id == "test-id"
    assert result.score == 0.95
    assert result.file_path == "src/test.py"
    assert result.function_name == "test_func"


def test_hnsw_config():
    """Test HNSW configuration."""
    search = MultiVectorSearch()

    assert search.hnsw_config.m == 16
    assert search.hnsw_config.ef_construct == 200
