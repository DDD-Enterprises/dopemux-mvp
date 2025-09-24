"""
ConPort Memory System for Dopemux

Unified memory graph implementation combining:
- Project memory (decisions, files, tasks, relationships) via MCP
- Vector search via Milvus for semantic recall
- Graph operations via SQL/PostgreSQL (future Neo4j)
- Integration with Zep for conversational memory
"""

__version__ = "1.0.0"
__author__ = "Dopemux Team"
