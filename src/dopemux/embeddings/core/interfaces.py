"""
Core interfaces and protocols for the embedding system.

Defines abstract base classes that enable provider-agnostic implementations
and clean dependency injection patterns.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol

from .types import SearchResult


class EmbeddingProvider(ABC):
    """
    Abstract base class for embedding providers.

    Enables pluggable embedding models (Voyage, OpenAI, Cohere, local models).
    """

    @abstractmethod
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors

        Raises:
            EmbeddingError: When embedding generation fails
        """
        pass

    @abstractmethod
    async def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a single query.

        Args:
            query: Query text to embed

        Returns:
            Query embedding vector

        Raises:
            EmbeddingError: When embedding generation fails
        """
        pass

    @abstractmethod
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by this provider."""
        pass

    @abstractmethod
    def get_cost_estimate(self) -> Dict[str, float]:
        """
        Get cost estimate based on usage.

        Returns:
            Dictionary with cost breakdown and usage metrics
        """
        pass


class RerankProvider(ABC):
    """
    Abstract base class for reranking providers.

    Enables pluggable reranking models for search result refinement.
    """

    @abstractmethod
    async def rerank(self, query: str, documents: List[str]) -> List[float]:
        """
        Rerank documents based on relevance to query.

        Args:
            query: Search query
            documents: List of documents to rerank

        Returns:
            List of relevance scores (0.0 to 1.0)

        Raises:
            RerankError: When reranking fails
        """
        pass

    @abstractmethod
    def get_cost_estimate(self) -> Dict[str, float]:
        """Get cost estimate for reranking operations."""
        pass


class VectorStore(ABC):
    """
    Abstract base class for vector storage backends.

    Enables pluggable vector storage (HNSW, IVF-PQ, cloud solutions).
    """

    @abstractmethod
    async def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """
        Add documents to the vector store.

        Args:
            documents: List of documents with content and metadata

        Raises:
            VectorStoreError: When document addition fails
        """
        pass

    @abstractmethod
    async def search(self, query_vector: List[float], k: int = 10) -> List[SearchResult]:
        """
        Search for similar documents using vector similarity.

        Args:
            query_vector: Query embedding vector
            k: Number of results to return

        Returns:
            List of search results ordered by similarity

        Raises:
            SearchError: When search fails
        """
        pass

    @abstractmethod
    async def delete_documents(self, doc_ids: List[str]) -> None:
        """
        Delete documents from the vector store.

        Args:
            doc_ids: List of document IDs to delete

        Raises:
            VectorStoreError: When deletion fails
        """
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        pass


class TextSearchIndex(ABC):
    """
    Abstract base class for text search indices (e.g., BM25).

    Enables lexical search capabilities in hybrid systems.
    """

    @abstractmethod
    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """
        Add documents to the text search index.

        Args:
            documents: List of documents with content and metadata

        Raises:
            IndexError: When document addition fails
        """
        pass

    @abstractmethod
    def search(self, query: str, k: int = 10) -> List[SearchResult]:
        """
        Search documents using lexical matching.

        Args:
            query: Search query text
            k: Number of results to return

        Returns:
            List of search results ordered by lexical relevance

        Raises:
            SearchError: When search fails
        """
        pass

    @abstractmethod
    def delete_documents(self, doc_ids: List[str]) -> None:
        """
        Delete documents from the index.

        Args:
            doc_ids: List of document IDs to delete

        Raises:
            IndexError: When deletion fails
        """
        pass


class HybridRanker(ABC):
    """
    Abstract base class for hybrid ranking algorithms.

    Combines lexical and semantic search results using various fusion methods.
    """

    @abstractmethod
    def fuse_scores(self, lexical_results: List[SearchResult],
                   vector_results: List[SearchResult]) -> List[SearchResult]:
        """
        Fuse lexical and vector search results.

        Args:
            lexical_results: Results from text search (e.g., BM25)
            vector_results: Results from vector search

        Returns:
            Fused and reranked search results

        Raises:
            FusionError: When score fusion fails
        """
        pass


# Protocol for async context managers (used by providers)
class AsyncContextManager(Protocol):
    """Protocol for async context manager support."""

    async def __aenter__(self):
        """Async context manager entry."""
        ...

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        ...


# Custom exceptions
class EmbeddingError(Exception):
    """Raised when embedding generation fails."""
    pass


class RerankError(Exception):
    """Raised when reranking fails."""
    pass


class VectorStoreError(Exception):
    """Raised when vector store operations fail."""
    pass


class SearchError(Exception):
    """Raised when search operations fail."""
    pass


class FusionError(Exception):
    """Raised when score fusion fails."""
    pass


class IndexError(Exception):
    """Raised when text index operations fail."""
    pass