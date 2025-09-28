"""
Provider implementations for the embedding system.

Contains concrete implementations of embedding and reranking providers
for different AI services and local models.
"""

from .voyage import VoyageAPIClient

__all__ = [
    "VoyageAPIClient"
]