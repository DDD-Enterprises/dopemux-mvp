#!/usr/bin/env python3
"""
ConPort MCP Tool Definitions for Cross-Project Memory Hub

This module defines the MCP tools that expose ConPort's cross-project memory
capabilities to AI agents. The tools provide a clean interface for managing
decisions, work items, artifacts, and knowledge graph relationships.

Architecture:
- decisions/* namespace: Atomic decision nodes
- work/* namespace: Upcoming queue and done history
- artifacts/* namespace: Files, screenshots, diffs, etc.
- knowledge_edges: Relationships between entities
- semantic_chunks: Vector embeddings for search
"""

import json
import uuid
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum

# MCP Tool Framework
from mcp import Tool, ToolResult
from mcp.types import TextContent, ImageContent

# Database connection (assuming asyncpg or similar)
import asyncpg
from pgvector.asyncpg import register_vector

class EntityType(Enum):
    DECISION = "decision"
    WORK_ITEM = "work_item"
    ARTIFACT = "artifact"

class RelationshipType(Enum):
    IMPLEMENTS = "implements"
    VALIDATES = "validates"
    DEPENDS_ON = "depends_on"
    REFERENCES = "references"
    CREATED_BY = "created_by"
    ATTACHED_TO = "attached_to"

@dataclass
class Decision:
    """Cross-project decision node"""
    id: str
    workspace_id: str
    title: str
    rationale: Optional[str] = None
    implementation_details: Optional[str] = None
    who: Optional[str] = None
    when_ts: datetime = None
    links: List[Dict] = None
    tags: List[str] = None
    metadata: Dict = None

    def __post_init__(self):
        if self.id is None:
            self.id = f"decisions/{datetime.now().strftime('%Y-%m-%d')}-{str(uuid.uuid4())[:8]}"
        if self.when_ts is None:
            self.when_ts = datetime.now()
        if self.links is None:
            self.links = []
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}

@dataclass
class WorkItem:
    """Unified work item across projects"""
    id: str
    workspace_id: str
    title: str
    description: Optional[str] = None
    status: str = "upcoming"
    priority: str = "medium"
    due_date: Optional[date] = None
    source: str = "manual"
    source_ref: Optional[str] = None
    tags: List[str] = None
    cognitive_load: int = 5
    energy_required: str = "medium"
    links: List[Dict] = None
    metadata: Dict = None

    def __post_init__(self):
        if self.id is None:
            self.id = f"work/{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"
        if self.tags is None:
            self.tags = []
        if self.links is None:
            self.links = []
        if self.metadata is None:
            self.metadata = {}

@dataclass
class Artifact:
    """File artifact with metadata"""
    id: str
    workspace_id: str
    kind: str
    title: str
    description: Optional[str] = None
    path: Optional[str] = None
    hash: Optional[str] = None
    size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    metadata: Dict = None
    links: List[Dict] = None

    def __post_init__(self):
        if self.id is None:
            self.id = f"artifacts/{self.kind}-{str(uuid.uuid4())[:8]}"
        if self.metadata is None:
            self.metadata = {}
        if self.links is None:
            self.links = []

class ConPortMCPTools:
    """MCP Tool definitions for ConPort cross-project memory hub"""

    def __init__(self, db_pool):
        self.db_pool = db_pool

    # =====================================================
    # DECISIONS TOOLS
    # =====================================================

    async def add_decision(self, workspace_id: str, title: str, rationale: str = None,
                          implementation_details: str = None, tags: List[str] = None,
                          links: List[Dict] = None) -> Dict:
        """Log a new decision with rationale and links"""
        decision = Decision(
            id=None,
            workspace_id=workspace_id,
            title=title,
            rationale=rationale,
            implementation_details=implementation_details,
            who="ai-agent",  # Could be parameterized
            tags=tags or [],
            links=links or []
        )

        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO decisions (id, workspace_id, title, rationale,
                                     implementation_details, who, tags, links)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """, decision.id, decision.workspace_id, decision.title,
                 decision.rationale, decision.implementation_details,
                 decision.who, decision.tags, json.dumps(decision.links))

        return {"decision_id": decision.id, "status": "logged"}

    async def get_decisions(self, workspace_id: str, since: datetime = None,
                           tags_filter: List[str] = None, limit: int = 10) -> List[Dict]:
        """Retrieve decisions with optional filtering"""
        query = """
            SELECT id, title, rationale, who, when_ts, tags, links
            FROM decisions
            WHERE workspace_id = $1
        """
        params = [workspace_id]

        if since:
            query += " AND when_ts >= $2"
            params.append(since)

        if tags_filter:
            query += f" AND tags && ${len(params) + 1}"
            params.append(tags_filter)

        query += f" ORDER BY when_ts DESC LIMIT ${len(params) + 1}"
        params.append(limit)

        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)

        return [dict(row) for row in rows]

    # =====================================================
    # WORK ITEMS TOOLS
    # =====================================================

    async def upcoming_add(self, workspace_id: str, title: str, description: str = None,
                          priority: str = "medium", due_date: date = None,
                          source: str = "manual", source_ref: str = None,
                          tags: List[str] = None) -> Dict:
        """Add a new work item to the upcoming queue"""
        work_item = WorkItem(
            id=None,
            workspace_id=workspace_id,
            title=title,
            description=description,
            priority=priority,
            due_date=due_date,
            source=source,
            source_ref=source_ref,
            tags=tags or []
        )

        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO work_items (id, workspace_id, title, description,
                                      priority, due_date, source, source_ref, tags)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, work_item.id, work_item.workspace_id, work_item.title,
                 work_item.description, work_item.priority, work_item.due_date,
                 work_item.source, work_item.source_ref, work_item.tags)

        return {"work_item_id": work_item.id, "status": "added"}

    async def upcoming_next(self, workspace_id: str, project: str = None,
                           limit: int = 3) -> List[Dict]:
        """Get next upcoming work items, optionally filtered by project"""
        query = """
            SELECT id, title, description, priority, due_date, source, tags,
                   cognitive_load, energy_required
            FROM work_items
            WHERE workspace_id = $1 AND status = 'upcoming'
        """
        params = [workspace_id]

        if project:
            query += " AND ($2 = ANY(tags) OR source_ref LIKE $3)"
            params.extend([project, f"%{project}%"])

        query += f" ORDER BY priority DESC, due_date ASC NULLS LAST LIMIT ${len(params) + 1}"
        params.append(limit)

        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)

        return [dict(row) for row in rows]

    async def work_update_status(self, workspace_id: str, work_item_id: str,
                                status: str) -> Dict:
        """Update work item status"""
        async with self.db_pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE work_items
                SET status = $1, updated_at = NOW(),
                    completed_at = CASE WHEN $1 = 'done' THEN NOW() ELSE NULL END
                WHERE workspace_id = $2 AND id = $3
            """, status, workspace_id, work_item_id)

        return {"status": "updated", "rows_affected": result.split()[1]}

    # =====================================================
    # ARTIFACTS TOOLS
    # =====================================================

    async def attach_artifact(self, workspace_id: str, kind: str, title: str,
                            path: str, description: str = None,
                            work_item_id: str = None) -> Dict:
        """Attach an artifact (screenshot, diff, etc.) with optional work item link"""
        artifact = Artifact(
            id=None,
            workspace_id=workspace_id,
            kind=kind,
            title=title,
            description=description,
            path=path
        )

        # Create relationship if work_item_id provided
        links = []
        if work_item_id:
            links.append({
                "type": "work_item",
                "id": work_item_id,
                "relationship": "attached_to"
            })

        async with self.db_pool.acquire() as conn:
            # Insert artifact
            await conn.execute("""
                INSERT INTO artifacts (id, workspace_id, kind, title, description, path, links)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, artifact.id, artifact.workspace_id, artifact.kind, artifact.title,
                 artifact.description, artifact.path, json.dumps(links))

            # Create knowledge graph edge if work item linked
            if work_item_id:
                await conn.execute("""
                    INSERT INTO knowledge_edges (source_type, source_id, target_type, target_id, relationship_type)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT DO NOTHING
                """, "artifact", artifact.id, "work_item", work_item_id, "attached_to")

        return {"artifact_id": artifact.id, "status": "attached"}

    async def list_artifacts(self, workspace_id: str, kind: str = None,
                           work_item_id: str = None, limit: int = 10) -> List[Dict]:
        """List artifacts with optional filtering"""
        query = """
            SELECT id, kind, title, description, path, size_bytes, mime_type, created_at
            FROM artifacts
            WHERE workspace_id = $1
        """
        params = [workspace_id]

        if kind:
            query += f" AND kind = ${len(params) + 1}"
            params.append(kind)

        if work_item_id:
            query += f" AND links @> ${len(params) + 1}"
            params.append(json.dumps([{"type": "work_item", "id": work_item_id}]))

        query += f" ORDER BY created_at DESC LIMIT ${len(params) + 1}"
        params.append(limit)

        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)

        return [dict(row) for row in rows]

    # =====================================================
    # KNOWLEDGE GRAPH TOOLS
    # =====================================================

    async def graph_link(self, workspace_id: str, source_type: str, source_id: str,
                        target_type: str, target_id: str, relationship_type: str,
                        description: str = None) -> Dict:
        """Create a relationship between two entities"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO knowledge_edges (source_type, source_id, target_type, target_id,
                                          relationship_type, description)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (source_type, source_id, target_type, target_id, relationship_type)
                DO UPDATE SET description = EXCLUDED.description
            """, source_type, source_id, target_type, target_id, relationship_type, description)

        return {"status": "linked"}

    async def graph_query(self, workspace_id: str, entity_type: str, entity_id: str,
                         relationship_filter: str = None, limit: int = 10) -> List[Dict]:
        """Query knowledge graph relationships for an entity"""
        query = """
            SELECT source_type, source_id, target_type, target_id,
                   relationship_type, description, weight, created_at
            FROM knowledge_edges
            WHERE (source_type = $1 AND source_id = $2) OR (target_type = $1 AND target_id = $2)
        """
        params = [entity_type, entity_id]

        if relationship_filter:
            query += f" AND relationship_type = ${len(params) + 1}"
            params.append(relationship_filter)

        query += f" ORDER BY created_at DESC LIMIT ${len(params) + 1}"
        params.append(limit)

        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)

        return [dict(row) for row in rows]

    # =====================================================
    # SEMANTIC SEARCH TOOLS
    # =====================================================

    async def semantic_search(self, workspace_id: str, query: str, entity_types: List[str] = None,
                            top_k: int = 5) -> List[Dict]:
        """Semantic search across entities using vector similarity"""
        # This would integrate with Voyage embeddings
        # Simplified implementation - in practice would use vector search
        entity_filter = ""
        if entity_types:
            entity_filter = f" AND entity_type IN ({','.join(f'${i+3}' for i in range(len(entity_types)))})"

        query_sql = f"""
            SELECT entity_type, entity_id, content, chunk_index,
                   1 - (embedding <=> $1::vector) as similarity_score
            FROM semantic_chunks
            WHERE workspace_id = $2 {entity_filter}
            ORDER BY embedding <=> $1::vector
            LIMIT $3
        """

        # Note: This requires actual embedding generation for the query
        # In practice, you'd call Voyage API here
        async with self.db_pool.acquire() as conn:
            # Placeholder - actual implementation would embed the query first
            rows = await conn.fetch("""
                SELECT entity_type, entity_id, content, chunk_index, 0.5 as similarity_score
                FROM semantic_chunks
                WHERE workspace_id = $1
                ORDER BY created_at DESC
                LIMIT $2
            """, workspace_id, top_k)

        return [dict(row) for row in rows]

# =====================================================
# MCP TOOL REGISTRATION
# =====================================================

def register_conport_tools(mcp_server, db_pool):
    """Register ConPort MCP tools with the server"""
    tools = ConPortMCPTools(db_pool)

    # Decision tools
    mcp_server.register_tool(
        Tool(
            name="conport_decisions_add",
            description="Log a new decision with rationale and links",
            input_schema={
                "type": "object",
                "properties": {
                    "workspace_id": {"type": "string"},
                    "title": {"type": "string"},
                    "rationale": {"type": "string"},
                    "implementation_details": {"type": "string"},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "links": {"type": "array", "items": {"type": "object"}}
                },
                "required": ["workspace_id", "title"]
            }
        ),
        lambda args: tools.add_decision(**args)
    )

    mcp_server.register_tool(
        Tool(
            name="conport_decisions_get",
            description="Retrieve decisions with optional filtering",
            input_schema={
                "type": "object",
                "properties": {
                    "workspace_id": {"type": "string"},
                    "since": {"type": "string", "format": "date-time"},
                    "tags_filter": {"type": "array", "items": {"type": "string"}},
                    "limit": {"type": "integer", "default": 10}
                },
                "required": ["workspace_id"]
            }
        ),
        lambda args: tools.get_decisions(**args)
    )

    # Work item tools
    mcp_server.register_tool(
        Tool(
            name="conport_work_upcoming_add",
            description="Add a new work item to the upcoming queue",
            input_schema={
                "type": "object",
                "properties": {
                    "workspace_id": {"type": "string"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                    "due_date": {"type": "string", "format": "date"},
                    "source": {"type": "string"},
                    "source_ref": {"type": "string"},
                    "tags": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["workspace_id", "title"]
            }
        ),
        lambda args: tools.upcoming_add(**args)
    )

    mcp_server.register_tool(
        Tool(
            name="conport_work_upcoming_next",
            description="Get next upcoming work items",
            input_schema={
                "type": "object",
                "properties": {
                    "workspace_id": {"type": "string"},
                    "project": {"type": "string"},
                    "limit": {"type": "integer", "default": 3}
                },
                "required": ["workspace_id"]
            }
        ),
        lambda args: tools.upcoming_next(**args)
    )

    # Artifact tools
    mcp_server.register_tool(
        Tool(
            name="conport_artifacts_attach",
            description="Attach an artifact with optional work item link",
            input_schema={
                "type": "object",
                "properties": {
                    "workspace_id": {"type": "string"},
                    "kind": {"type": "string"},
                    "title": {"type": "string"},
                    "path": {"type": "string"},
                    "description": {"type": "string"},
                    "work_item_id": {"type": "string"}
                },
                "required": ["workspace_id", "kind", "title", "path"]
            }
        ),
        lambda args: tools.attach_artifact(**args)
    )

    # Knowledge graph tools
    mcp_server.register_tool(
        Tool(
            name="conport_graph_link",
            description="Create a relationship between two entities",
            input_schema={
                "type": "object",
                "properties": {
                    "workspace_id": {"type": "string"},
                    "source_type": {"type": "string", "enum": ["decision", "work_item", "artifact"]},
                    "source_id": {"type": "string"},
                    "target_type": {"type": "string", "enum": ["decision", "work_item", "artifact"]},
                    "target_id": {"type": "string"},
                    "relationship_type": {"type": "string"},
                    "description": {"type": "string"}
                },
                "required": ["workspace_id", "source_type", "source_id", "target_type", "target_id", "relationship_type"]
            }
        ),
        lambda args: tools.graph_link(**args)
    )

    mcp_server.register_tool(
        Tool(
            name="conport_graph_query",
            description="Query knowledge graph relationships for an entity",
            input_schema={
                "type": "object",
                "properties": {
                    "workspace_id": {"type": "string"},
                    "entity_type": {"type": "string"},
                    "entity_id": {"type": "string"},
                    "relationship_filter": {"type": "string"},
                    "limit": {"type": "integer", "default": 10}
                },
                "required": ["workspace_id", "entity_type", "entity_id"]
            }
        ),
        lambda args: tools.graph_query(**args)
    )

    return mcp_server