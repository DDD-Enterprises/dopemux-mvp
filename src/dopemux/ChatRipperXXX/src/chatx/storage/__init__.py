"""Storage layer abstractions and implementations."""

from .base import (
    BaseGraphStore,
    GraphNode,
    GraphRelationship,
    ConversationGraph,
    PatternMatch,
    TemporalEvolution,
    RelationshipTypes,
    PatternTypes
)

try:
    from .graph import Neo4jGraphStore
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False

__all__ = [
    "BaseGraphStore",
    "GraphNode", 
    "GraphRelationship",
    "ConversationGraph",
    "PatternMatch",
    "TemporalEvolution",
    "RelationshipTypes",
    "PatternTypes"
]

if NEO4J_AVAILABLE:
    __all__.append("Neo4jGraphStore")