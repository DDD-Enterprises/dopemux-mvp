#!/usr/bin/env python3
"""
ConPort Memory MCP Server

Implements the unified memory graph for Dopemux with:
- mem.upsert/search tools for semantic memory operations
- graph.link/neighbors tools for relationship management
- Integration with Milvus (vectors) and PostgreSQL (truth)
- Support for Zep conversational memory
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence
from uuid import uuid4

import asyncpg
from milvus import MilvusClient
from pydantic import BaseModel
import voyageai
from mcp import types
from mcp.server import Server
from mcp.server.stdio import stdio_server


# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("conport.memory_server")


class MemoryConfig:
    """Configuration for ConPort memory system."""

    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL", "postgresql://dopemux:dopemux_dev_password@localhost:5432/dopemux_memory")
        self.milvus_host = os.getenv("MILVUS_HOST", "localhost")
        self.milvus_port = int(os.getenv("MILVUS_PORT", "19530"))
        self.zep_api_url = os.getenv("ZEP_API_URL", "http://localhost:8000")
        self.voyage_api_key = os.getenv("VOYAGE_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "voyage-code-3")
        self.embedding_dimension = int(os.getenv("EMBEDDING_DIMENSION", "1024"))


class MemoryNode(BaseModel):
    """Represents a node in the memory graph."""
    id: str
    type: str  # decision, task, file, endpoint, message, agent, thread, run
    text: str
    metadata: Dict[str, Any] = {}
    repo: Optional[str] = None
    author: Optional[str] = None


class MemoryEdge(BaseModel):
    """Represents an edge in the memory graph."""
    from_id: str
    to_id: str
    relation: str  # affects, depends_on, implements, discussed_in, produced_by, belongs_to_thread
    metadata: Dict[str, Any] = {}


class MilvusManager:
    """Manages Milvus vector database operations."""

    def __init__(self, config: MemoryConfig):
        self.config = config
        self.client: Optional[MilvusClient] = None
        self.voyage_client = None

        if config.voyage_api_key:
            self.voyage_client = voyageai.Client(api_key=config.voyage_api_key)

    async def connect(self):
        """Connect to Milvus."""
        try:
            self.client = MilvusClient(
                uri=f"http://{self.config.milvus_host}:{self.config.milvus_port}"
            )
            logger.info(f"Connected to Milvus at {self.config.milvus_host}:{self.config.milvus_port}")
            await self._ensure_collections()
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            raise

    async def _ensure_collections(self):
        """Ensure required Milvus collections exist."""
        collections = ["decisions", "messages", "files", "tasks", "agents", "threads", "runs"]

        for collection_name in collections:
            if not self.client.has_collection(collection_name):
                # Create collection with schema
                schema = {
                    "fields": [
                        {"name": "id", "type": "VARCHAR", "max_length": 255, "is_primary": True},
                        {"name": "ts", "type": "INT64"},
                        {"name": "type", "type": "VARCHAR", "max_length": 50},
                        {"name": "repo", "type": "VARCHAR", "max_length": 255},
                        {"name": "author", "type": "VARCHAR", "max_length": 255},
                        {"name": "embedding", "type": "FLOAT_VECTOR", "dim": self.config.embedding_dimension}
                    ]
                }

                self.client.create_collection(
                    collection_name=collection_name,
                    schema=schema,
                    index_params={"index_type": "HNSW", "metric_type": "COSINE", "params": {"M": 16, "efConstruction": 256}}
                )
                logger.info(f"Created Milvus collection: {collection_name}")

    async def embed_text(self, text: str) -> List[float]:
        """Generate embeddings for text using Voyage AI."""
        if not self.voyage_client:
            logger.warning("No Voyage API key configured, using dummy embedding")
            return [0.0] * self.config.embedding_dimension

        try:
            result = self.voyage_client.embed([text], model=self.config.embedding_model)
            return result.embeddings[0]
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return [0.0] * self.config.embedding_dimension

    async def upsert_node(self, node: MemoryNode) -> bool:
        """Insert or update a node in Milvus."""
        try:
            collection_name = f"{node.type}s" if not node.type.endswith('s') else node.type
            if collection_name not in ["decisions", "messages", "files", "tasks", "agents", "threads", "runs"]:
                collection_name = "messages"  # Default fallback

            # Generate embedding
            embedding = await self.embed_text(node.text)

            # Prepare data for Milvus
            data = [{
                "id": node.id,
                "ts": int(datetime.now().timestamp()),
                "type": node.type,
                "repo": node.repo or "",
                "author": node.author or "",
                "embedding": embedding
            }]

            # Upsert to Milvus
            self.client.upsert(collection_name=collection_name, data=data)
            logger.debug(f"Upserted node {node.id} to Milvus collection {collection_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to upsert node to Milvus: {e}")
            return False

    async def search_similar(self, query_text: str, collection_type: Optional[str] = None,
                           limit: int = 10, filters: Optional[Dict] = None) -> List[Dict]:
        """Search for similar nodes using vector similarity."""
        try:
            # Generate query embedding
            query_embedding = await self.embed_text(query_text)

            # Determine collections to search
            collections = []
            if collection_type:
                collection_name = f"{collection_type}s" if not collection_type.endswith('s') else collection_type
                collections = [collection_name] if collection_name in ["decisions", "messages", "files", "tasks", "agents", "threads", "runs"] else ["messages"]
            else:
                collections = ["decisions", "messages", "files", "tasks"]  # Search most relevant collections

            all_results = []

            for collection_name in collections:
                if not self.client.has_collection(collection_name):
                    continue

                # Build filter expression
                filter_expr = ""
                if filters:
                    filter_parts = []
                    for key, value in filters.items():
                        if key in ["repo", "author", "type"]:
                            filter_parts.append(f'{key} == "{value}"')
                    if filter_parts:
                        filter_expr = " and ".join(filter_parts)

                # Search
                search_params = {"metric_type": "COSINE", "params": {"ef": 64}}
                results = self.client.search(
                    collection_name=collection_name,
                    data=[query_embedding],
                    anns_field="embedding",
                    search_params=search_params,
                    limit=limit,
                    expr=filter_expr if filter_expr else None,
                    output_fields=["id", "ts", "type", "repo", "author"]
                )

                # Process results
                for result in results[0]:  # First query results
                    all_results.append({
                        "id": result["entity"]["id"],
                        "type": result["entity"]["type"],
                        "repo": result["entity"]["repo"],
                        "author": result["entity"]["author"],
                        "score": result["distance"],
                        "collection": collection_name
                    })

            # Sort by score and return top results
            all_results.sort(key=lambda x: x["score"], reverse=True)
            return all_results[:limit]

        except Exception as e:
            logger.error(f"Failed to search Milvus: {e}")
            return []


class PostgreSQLManager:
    """Manages PostgreSQL database operations for graph truth."""

    def __init__(self, config: MemoryConfig):
        self.config = config
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Connect to PostgreSQL."""
        try:
            self.pool = await asyncpg.create_pool(self.config.database_url)
            logger.info("Connected to PostgreSQL")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise

    async def upsert_node(self, node: MemoryNode) -> bool:
        """Insert or update a node in PostgreSQL."""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO nodes (id, type, text, metadata, repo, author, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, CURRENT_TIMESTAMP)
                    ON CONFLICT (id) DO UPDATE SET
                        type = EXCLUDED.type,
                        text = EXCLUDED.text,
                        metadata = EXCLUDED.metadata,
                        repo = EXCLUDED.repo,
                        author = EXCLUDED.author,
                        updated_at = CURRENT_TIMESTAMP
                """, node.id, node.type, node.text, json.dumps(node.metadata), node.repo, node.author)

            logger.debug(f"Upserted node {node.id} to PostgreSQL")
            return True

        except Exception as e:
            logger.error(f"Failed to upsert node to PostgreSQL: {e}")
            return False

    async def link_nodes(self, edge: MemoryEdge) -> bool:
        """Create a link between two nodes."""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO edges (from_id, to_id, relation, metadata)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (from_id, to_id, relation) DO UPDATE SET
                        metadata = EXCLUDED.metadata
                """, edge.from_id, edge.to_id, edge.relation, json.dumps(edge.metadata))

            logger.debug(f"Created edge {edge.from_id} -> {edge.to_id} ({edge.relation})")
            return True

        except Exception as e:
            logger.error(f"Failed to create edge: {e}")
            return False

    async def get_neighbors(self, node_id: str, depth: int = 1, relation: Optional[str] = None) -> List[Dict]:
        """Get neighboring nodes in the graph."""
        try:
            async with self.pool.acquire() as conn:
                # Build query based on parameters
                if relation:
                    query = """
                        WITH RECURSIVE neighbors AS (
                            SELECT n.id, n.type, n.text, n.metadata, n.repo, n.author, 0 as depth
                            FROM nodes n WHERE n.id = $1

                            UNION ALL

                            SELECT n.id, n.type, n.text, n.metadata, n.repo, n.author, nb.depth + 1
                            FROM nodes n
                            JOIN edges e ON (e.to_id = n.id OR e.from_id = n.id)
                            JOIN neighbors nb ON (e.from_id = nb.id OR e.to_id = nb.id)
                            WHERE nb.depth < $2 AND e.relation = $3 AND n.id != nb.id
                        )
                        SELECT DISTINCT * FROM neighbors ORDER BY depth, id
                    """
                    rows = await conn.fetch(query, node_id, depth, relation)
                else:
                    query = """
                        WITH RECURSIVE neighbors AS (
                            SELECT n.id, n.type, n.text, n.metadata, n.repo, n.author, 0 as depth
                            FROM nodes n WHERE n.id = $1

                            UNION ALL

                            SELECT n.id, n.type, n.text, n.metadata, n.repo, n.author, nb.depth + 1
                            FROM nodes n
                            JOIN edges e ON (e.to_id = n.id OR e.from_id = n.id)
                            JOIN neighbors nb ON (e.from_id = nb.id OR e.to_id = nb.id)
                            WHERE nb.depth < $2 AND n.id != nb.id
                        )
                        SELECT DISTINCT * FROM neighbors ORDER BY depth, id
                    """
                    rows = await conn.fetch(query, node_id, depth)

                # Convert to dictionaries
                neighbors = []
                for row in rows:
                    neighbors.append({
                        "id": row["id"],
                        "type": row["type"],
                        "text": row["text"],
                        "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                        "repo": row["repo"],
                        "author": row["author"],
                        "depth": row["depth"]
                    })

                return neighbors

        except Exception as e:
            logger.error(f"Failed to get neighbors: {e}")
            return []

    async def search_nodes(self, filters: Optional[Dict] = None, limit: int = 100) -> List[Dict]:
        """Search nodes by metadata filters."""
        try:
            async with self.pool.acquire() as conn:
                query = "SELECT id, type, text, metadata, repo, author, created_at FROM nodes"
                params = []

                if filters:
                    conditions = []
                    param_count = 1

                    for key, value in filters.items():
                        if key in ["type", "repo", "author"]:
                            conditions.append(f"{key} = ${param_count}")
                            params.append(value)
                            param_count += 1
                        elif key == "text_contains":
                            conditions.append(f"text ILIKE ${param_count}")
                            params.append(f"%{value}%")
                            param_count += 1

                    if conditions:
                        query += " WHERE " + " AND ".join(conditions)

                query += f" ORDER BY created_at DESC LIMIT ${param_count}"
                params.append(limit)

                rows = await conn.fetch(query, *params)

                # Convert to dictionaries
                nodes = []
                for row in rows:
                    nodes.append({
                        "id": row["id"],
                        "type": row["type"],
                        "text": row["text"],
                        "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                        "repo": row["repo"],
                        "author": row["author"],
                        "created_at": row["created_at"].isoformat()
                    })

                return nodes

        except Exception as e:
            logger.error(f"Failed to search nodes: {e}")
            return []


class ConPortMemoryServer:
    """Main ConPort Memory MCP Server."""

    def __init__(self):
        self.config = MemoryConfig()
        self.milvus = MilvusManager(self.config)
        self.postgres = PostgreSQLManager(self.config)
        self.server = Server("conport-memory")

        # Register MCP tools
        self._register_tools()

    def _register_tools(self):
        """Register MCP tools for memory operations."""

        @self.server.list_tools()
        async def list_tools() -> List[types.Tool]:
            """List available memory tools."""
            return [
                types.Tool(
                    name="mem.upsert",
                    description="Store or update a node in the memory graph with vector embedding",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "type": {"type": "string", "description": "Node type (decision, task, file, message, etc.)"},
                            "id": {"type": "string", "description": "Unique identifier for the node"},
                            "text": {"type": "string", "description": "Text content to embed and store"},
                            "metadata": {"type": "object", "description": "Additional metadata"},
                            "repo": {"type": "string", "description": "Repository/project name"},
                            "author": {"type": "string", "description": "Author/creator"}
                        },
                        "required": ["type", "id", "text"]
                    }
                ),
                types.Tool(
                    name="mem.search",
                    description="Search memory using semantic vector similarity",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query text"},
                            "type": {"type": "string", "description": "Optional: filter by node type"},
                            "k": {"type": "integer", "description": "Number of results to return", "default": 10},
                            "filters": {"type": "object", "description": "Additional filters (repo, author, etc.)"}
                        },
                        "required": ["query"]
                    }
                ),
                types.Tool(
                    name="graph.link",
                    description="Create a relationship between two nodes in the graph",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "from_id": {"type": "string", "description": "Source node ID"},
                            "to_id": {"type": "string", "description": "Target node ID"},
                            "relation": {"type": "string", "description": "Relationship type (affects, depends_on, implements, etc.)"},
                            "metadata": {"type": "object", "description": "Additional relationship metadata"}
                        },
                        "required": ["from_id", "to_id", "relation"]
                    }
                ),
                types.Tool(
                    name="graph.neighbors",
                    description="Find neighboring nodes in the graph by traversing relationships",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "id": {"type": "string", "description": "Starting node ID"},
                            "depth": {"type": "integer", "description": "Traversal depth", "default": 1},
                            "relation": {"type": "string", "description": "Optional: filter by specific relationship type"}
                        },
                        "required": ["id"]
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> Sequence[types.TextContent]:
            """Handle tool calls."""
            try:
                if name == "mem.upsert":
                    return await self._handle_mem_upsert(arguments)
                elif name == "mem.search":
                    return await self._handle_mem_search(arguments)
                elif name == "graph.link":
                    return await self._handle_graph_link(arguments)
                elif name == "graph.neighbors":
                    return await self._handle_graph_neighbors(arguments)
                else:
                    return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
            except Exception as e:
                logger.error(f"Tool call failed: {e}")
                return [types.TextContent(type="text", text=f"Error: {str(e)}")]

    async def _handle_mem_upsert(self, args: Dict[str, Any]) -> Sequence[types.TextContent]:
        """Handle mem.upsert tool call."""
        node = MemoryNode(
            id=args["id"],
            type=args["type"],
            text=args["text"],
            metadata=args.get("metadata", {}),
            repo=args.get("repo"),
            author=args.get("author")
        )

        # Store in both PostgreSQL (truth) and Milvus (vectors)
        pg_success = await self.postgres.upsert_node(node)
        milvus_success = await self.milvus.upsert_node(node)

        if pg_success and milvus_success:
            return [types.TextContent(type="text", text=json.dumps({"ok": True, "id": node.id}))]
        else:
            return [types.TextContent(type="text", text=json.dumps({"ok": False, "error": "Failed to store node"}))]

    async def _handle_mem_search(self, args: Dict[str, Any]) -> Sequence[types.TextContent]:
        """Handle mem.search tool call."""
        query = args["query"]
        node_type = args.get("type")
        k = args.get("k", 10)
        filters = args.get("filters", {})

        # Search using Milvus vector similarity
        vector_results = await self.milvus.search_similar(query, node_type, k, filters)

        # Get full node details from PostgreSQL
        results = []
        for vector_result in vector_results:
            # Get detailed node information from PostgreSQL
            pg_results = await self.postgres.search_nodes({"type": vector_result["type"]}, limit=1)
            for pg_result in pg_results:
                if pg_result["id"] == vector_result["id"]:
                    results.append({
                        **pg_result,
                        "similarity_score": vector_result["score"]
                    })
                    break

        return [types.TextContent(type="text", text=json.dumps({"results": results}))]

    async def _handle_graph_link(self, args: Dict[str, Any]) -> Sequence[types.TextContent]:
        """Handle graph.link tool call."""
        edge = MemoryEdge(
            from_id=args["from_id"],
            to_id=args["to_id"],
            relation=args["relation"],
            metadata=args.get("metadata", {})
        )

        success = await self.postgres.link_nodes(edge)

        if success:
            return [types.TextContent(type="text", text=json.dumps({"ok": True}))]
        else:
            return [types.TextContent(type="text", text=json.dumps({"ok": False, "error": "Failed to create link"}))]

    async def _handle_graph_neighbors(self, args: Dict[str, Any]) -> Sequence[types.TextContent]:
        """Handle graph.neighbors tool call."""
        node_id = args["id"]
        depth = args.get("depth", 1)
        relation = args.get("relation")

        neighbors = await self.postgres.get_neighbors(node_id, depth, relation)

        return [types.TextContent(type="text", text=json.dumps({"neighbors": neighbors}))]

    async def start(self):
        """Start the ConPort memory server."""
        logger.info("Starting ConPort Memory Server...")

        # Connect to databases
        await self.postgres.connect()
        await self.milvus.connect()

        logger.info("ConPort Memory Server ready")


async def main():
    """Main entry point for ConPort Memory Server."""
    server_instance = ConPortMemoryServer()

    try:
        await server_instance.start()

        # Run the MCP server
        async with stdio_server() as (read_stream, write_stream):
            await server_instance.server.run(
                read_stream, write_stream, server_instance.server.create_initialization_options()
            )
    except Exception as e:
        logger.error(f"Server failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())