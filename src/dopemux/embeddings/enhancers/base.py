"""
Base abstractions for embedding enhancement layers.

Provides abstract interfaces for quality assurance, validation,
and enhancement systems.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from ..core import SearchResult


class BaseEnhancer(ABC):
    """
    Abstract base class for embedding enhancement layers.

    Enhancement layers provide quality assurance, validation,
    and improvement capabilities for embedding systems.
    """

    @abstractmethod
    async def enhance_results(self, query: str, results: List[SearchResult]) -> List[SearchResult]:
        """
        Enhance search results with additional quality metrics.

        Args:
            query: Original search query
            results: Search results to enhance

        Returns:
            Enhanced search results with additional metrics
        """
        pass

    @abstractmethod
    def get_enhancement_stats(self) -> Dict[str, Any]:
        """
        Get statistics about enhancement operations.

        Returns:
            Dictionary with enhancement statistics
        """
        pass

    @abstractmethod
    async def validate_quality(self, document_id: str, content: str,
                              embedding: List[float]) -> Dict[str, Any]:
        """
        Validate the quality of an embedding.

        Args:
            document_id: Unique document identifier
            content: Original document content
            embedding: Document embedding to validate

        Returns:
            Validation results with quality metrics
        """
        pass