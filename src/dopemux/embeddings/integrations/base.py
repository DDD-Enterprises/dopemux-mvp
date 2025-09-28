"""
Base abstractions for external system integrations.

Provides abstract interfaces for integrating embedding system
with dopemux components like ConPort, Serena, and others.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ..core import SearchResult, AdvancedEmbeddingConfig


class BaseIntegration(ABC):
    """
    Abstract base class for external system integrations.

    Integration adapters enable the embedding system to work
    seamlessly with other dopemux components.
    """

    def __init__(self, config: AdvancedEmbeddingConfig):
        self.config = config

    @abstractmethod
    async def sync_documents(self, workspace_id: str) -> Dict[str, Any]:
        """
        Synchronize documents from external system.

        Args:
            workspace_id: Workspace identifier

        Returns:
            Sync statistics and results
        """
        pass

    @abstractmethod
    async def store_embeddings(self, documents: List[Dict[str, Any]],
                              embeddings: List[List[float]]) -> None:
        """
        Store embeddings back to external system.

        Args:
            documents: Document metadata
            embeddings: Generated embeddings
        """
        pass

    @abstractmethod
    async def enhance_search_results(self, results: List[SearchResult],
                                   context: Dict[str, Any]) -> List[SearchResult]:
        """
        Enhance search results with external system data.

        Args:
            results: Raw search results
            context: Additional context from external system

        Returns:
            Enhanced search results
        """
        pass

    @abstractmethod
    def get_integration_status(self) -> Dict[str, Any]:
        """
        Get integration health and status information.

        Returns:
            Status dictionary with connection info
        """
        pass

    @abstractmethod
    async def validate_connection(self) -> bool:
        """
        Validate connection to external system.

        Returns:
            True if connection is healthy
        """
        pass