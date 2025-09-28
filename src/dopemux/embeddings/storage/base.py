"""
Base classes and interfaces for storage components.

Defines abstract base classes for vector indices, text indices,
and storage backends to enable pluggable implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple

import numpy as np

from ..core import SearchResult


class BaseVectorIndex(ABC):
    """
    Abstract base class for vector index implementations.

    Enables pluggable vector storage backends (HNSW, IVF-PQ, FAISS, etc.)
    with consistent interface for embedding storage and retrieval.
    """

    @abstractmethod
    def add_vectors(self, vectors: np.ndarray, ids: List[str]) -> None:
        """
        Add vectors to the index.

        Args:
            vectors: Array of embedding vectors to add
            ids: Corresponding document IDs

        Raises:
            VectorStoreError: When vector addition fails
        """
        pass

    @abstractmethod
    def search(self, query_vector: np.ndarray, k: int) -> Tuple[List[float], List[int]]:
        """
        Search for similar vectors.

        Args:
            query_vector: Query embedding vector
            k: Number of nearest neighbors to return

        Returns:
            Tuple of (scores, indices) where scores are similarity scores
            and indices are internal vector indices

        Raises:
            SearchError: When search fails
        """
        pass

    @abstractmethod
    def save(self, path: str) -> None:
        """
        Save index to disk.

        Args:
            path: File path to save the index

        Raises:
            VectorStoreError: When saving fails
        """
        pass

    @abstractmethod
    def load(self, path: str) -> None:
        """
        Load index from disk.

        Args:
            path: File path to load the index from

        Raises:
            VectorStoreError: When loading fails
        """
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """
        Get index statistics.

        Returns:
            Dictionary with index statistics (size, count, memory usage, etc.)
        """
        pass


class BaseTextIndex(ABC):
    """
    Abstract base class for text search indices.

    Enables pluggable lexical search backends (BM25, TF-IDF, etc.)
    for keyword-based document retrieval.
    """

    @abstractmethod
    def add_documents(self, documents: List[str], ids: List[str]) -> None:
        """
        Add documents to the text index.

        Args:
            documents: List of document texts
            ids: Corresponding document IDs

        Raises:
            IndexError: When document addition fails
        """
        pass

    @abstractmethod
    def search(self, query: str, k: int) -> List[Tuple[str, float]]:
        """
        Search documents using lexical matching.

        Args:
            query: Search query text
            k: Number of results to return

        Returns:
            List of (document_id, score) tuples ordered by relevance

        Raises:
            SearchError: When search fails
        """
        pass

    @abstractmethod
    def save(self, path: str) -> None:
        """
        Save text index to disk.

        Args:
            path: File path to save the index

        Raises:
            IndexError: When saving fails
        """
        pass

    @abstractmethod
    def load(self, path: str) -> None:
        """
        Load text index from disk.

        Args:
            path: File path to load the index from

        Raises:
            IndexError: When loading fails
        """
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """
        Get text index statistics.

        Returns:
            Dictionary with index statistics (document count, vocabulary size, etc.)
        """
        pass


class BaseRanker(ABC):
    """
    Abstract base class for result ranking algorithms.

    Enables pluggable fusion strategies for combining lexical and semantic
    search results with different weighting and learning approaches.
    """

    @abstractmethod
    def fuse_scores(self, lexical_results: List[Tuple[str, float]],
                   vector_results: List[Tuple[str, float]]) -> List[SearchResult]:
        """
        Fuse lexical and vector search results.

        Args:
            lexical_results: Results from text search as (doc_id, score) tuples
            vector_results: Results from vector search as (doc_id, score) tuples

        Returns:
            Fused and reranked search results

        Raises:
            FusionError: When score fusion fails
        """
        pass

    @abstractmethod
    def train(self, training_data: List[Tuple[str, str, float]]) -> None:
        """
        Train the ranker on labeled data (if applicable).

        Args:
            training_data: List of (query, document, relevance_score) tuples

        Raises:
            RerankError: When training fails
        """
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """
        Get ranker statistics.

        Returns:
            Dictionary with ranker statistics (training status, performance, etc.)
        """
        pass


class BaseDocumentStore(ABC):
    """
    Abstract base class for document storage backends.

    Enables pluggable document storage (in-memory, disk, database)
    for retrieving full document content and metadata.
    """

    @abstractmethod
    def store_document(self, doc_id: str, content: str, metadata: Dict[str, Any]) -> None:
        """
        Store a document with metadata.

        Args:
            doc_id: Unique document identifier
            content: Document content
            metadata: Document metadata

        Raises:
            VectorStoreError: When storage fails
        """
        pass

    @abstractmethod
    def get_document(self, doc_id: str) -> Dict[str, Any]:
        """
        Retrieve a document by ID.

        Args:
            doc_id: Document identifier

        Returns:
            Dictionary with content and metadata

        Raises:
            VectorStoreError: When document not found
        """
        pass

    @abstractmethod
    def get_documents(self, doc_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Retrieve multiple documents by IDs.

        Args:
            doc_ids: List of document identifiers

        Returns:
            List of documents with content and metadata

        Raises:
            VectorStoreError: When retrieval fails
        """
        pass

    @abstractmethod
    def delete_document(self, doc_id: str) -> None:
        """
        Delete a document.

        Args:
            doc_id: Document identifier

        Raises:
            VectorStoreError: When deletion fails
        """
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """
        Get document store statistics.

        Returns:
            Dictionary with storage statistics
        """
        pass