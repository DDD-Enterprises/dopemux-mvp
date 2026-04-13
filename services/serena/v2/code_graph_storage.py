"""
PostgreSQL Code Structure Graph Storage for Serena v2

Persistent storage for code relationships, import graphs, and call hierarchies.
Provides graph query capabilities for intelligent navigation assistance.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

import asyncpg
from asyncpg import Pool, Connection

logger = logging.getLogger(__name__)


class RelationshipType(str, Enum):
    """Types of code relationships."""
    IMPORTS = "imports"
    CALLS = "calls"
    INHERITS = "inherits"
    IMPLEMENTS = "implements"
    REFERENCES = "references"
    DEFINES = "defines"
    CONTAINS = "contains"
    DEPENDS_ON = "depends_on"


class NodeType(str, Enum):
    """Types of code nodes."""
    FILE = "file"
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    VARIABLE = "variable"
    CONSTANT = "constant"
    INTERFACE = "interface"
    ENUM = "enum"


@dataclass
class CodeNode:
    """Represents a code element in the graph."""
    id: str
    node_type: NodeType
    name: str
    file_path: str
    workspace_id: str

    # Location information
    start_line: int = 0
    end_line: int = 0
    start_column: int = 0
    end_column: int = 0

    # Metadata
    language: str = ""
    namespace: Optional[str] = None
    docstring: Optional[str] = None
    complexity_score: float = 0.5
    cognitive_load: float = 0.5

    # ADHD optimization
    requires_focus: bool = False
    adhd_summary: Optional[str] = None

    # Timestamps
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.updated_at is None:
            self.updated_at = self.created_at


@dataclass
class CodeRelationship:
    """Represents a relationship between code elements."""
    source_node_id: str
    target_node_id: str
    relationship_type: RelationshipType

    # Relationship metadata
    strength: float = 1.0  # Relationship strength (0.0-1.0)
    context: Dict[str, Any] = None
    line_number: Optional[int] = None

    # Timestamps
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.context is None:
            self.context = {}
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.updated_at is None:
            self.updated_at = self.created_at


class CodeGraphConfig:
    """Configuration for code graph storage."""
    def __init__(
        self,
        postgres_url: str = "postgresql://localhost:5432/serena_code_graph",
        max_connections: int = 10,
        connection_timeout: float = 30.0
    ):
        self.postgres_url = postgres_url
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout


class CodeGraphStorage:
    """
    PostgreSQL-based storage for code structure graphs with ADHD optimizations.

    Features:
    - Graph storage with efficient relationship queries
    - Workspace isolation for multi-instance support
    - ADHD-optimized query results with complexity filtering
    - Historical tracking of code structure evolution
    - Integration with Tree-sitter analyzer and claude-context
    """

    def __init__(self, config: CodeGraphConfig):
        self.config = config
        self.pool: Optional[Pool] = None
        self._initialized = False

        # Query performance optimization
        self.query_cache: Dict[str, Tuple[Any, datetime]] = {}
        self.cache_ttl = 300  # 5 minutes

    async def initialize(self) -> None:
        """Initialize PostgreSQL connection pool and create schema."""
        if self._initialized:
            return

        logger.info("🗄️ Initializing Code Graph Storage...")

        try:
            # Create connection pool
            self.pool = await asyncpg.create_pool(
                self.config.postgres_url,
                min_size=2,
                max_size=self.config.max_connections,
                command_timeout=self.config.connection_timeout
            )

            # Create schema
            await self._create_schema()

            self._initialized = True
            logger.info("✅ Code Graph Storage ready!")

        except Exception as e:
            logger.error(f"Failed to initialize code graph storage: {e}")
            raise RuntimeError(f"Code graph storage initialization failed: {e}")

    async def _create_schema(self) -> None:
        """Create database schema for code graph storage."""
        schema_sql = """
        -- Code nodes table
        CREATE TABLE IF NOT EXISTS code_nodes (
            id TEXT PRIMARY KEY,
            workspace_id TEXT NOT NULL,
            node_type TEXT NOT NULL,
            name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            start_line INTEGER DEFAULT 0,
            end_line INTEGER DEFAULT 0,
            start_column INTEGER DEFAULT 0,
            end_column INTEGER DEFAULT 0,
            language TEXT DEFAULT '',
            namespace TEXT,
            docstring TEXT,
            complexity_score REAL DEFAULT 0.5,
            cognitive_load REAL DEFAULT 0.5,
            requires_focus BOOLEAN DEFAULT FALSE,
            adhd_summary TEXT,
            metadata JSONB DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );

        -- Code relationships table
        CREATE TABLE IF NOT EXISTS code_relationships (
            id SERIAL PRIMARY KEY,
            workspace_id TEXT NOT NULL,
            source_node_id TEXT NOT NULL REFERENCES code_nodes(id) ON DELETE CASCADE,
            target_node_id TEXT NOT NULL REFERENCES code_nodes(id) ON DELETE CASCADE,
            relationship_type TEXT NOT NULL,
            strength REAL DEFAULT 1.0,
            context JSONB DEFAULT '{}'::jsonb,
            line_number INTEGER,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );

        -- File analysis history
        CREATE TABLE IF NOT EXISTS file_analysis_history (
            id SERIAL PRIMARY KEY,
            workspace_id TEXT NOT NULL,
            file_path TEXT NOT NULL,
            analysis_timestamp TIMESTAMPTZ DEFAULT NOW(),
            symbol_count INTEGER DEFAULT 0,
            complexity_score REAL DEFAULT 0.5,
            adhd_score REAL DEFAULT 0.5,
            analysis_data JSONB DEFAULT '{}'::jsonb
        );

        -- Create indexes for performance
        CREATE INDEX IF NOT EXISTS idx_code_nodes_workspace ON code_nodes(workspace_id);
        CREATE INDEX IF NOT EXISTS idx_code_nodes_file_path ON code_nodes(workspace_id, file_path);
        CREATE INDEX IF NOT EXISTS idx_code_nodes_type ON code_nodes(workspace_id, node_type);
        CREATE INDEX IF NOT EXISTS idx_code_nodes_name ON code_nodes(workspace_id, name);

        CREATE INDEX IF NOT EXISTS idx_relationships_workspace ON code_relationships(workspace_id);
        CREATE INDEX IF NOT EXISTS idx_relationships_source ON code_relationships(workspace_id, source_node_id);
        CREATE INDEX IF NOT EXISTS idx_relationships_target ON code_relationships(workspace_id, target_node_id);
        CREATE INDEX IF NOT EXISTS idx_relationships_type ON code_relationships(workspace_id, relationship_type);

        CREATE INDEX IF NOT EXISTS idx_file_history_workspace ON file_analysis_history(workspace_id, file_path);
        CREATE INDEX IF NOT EXISTS idx_file_history_timestamp ON file_analysis_history(analysis_timestamp DESC);

        -- Full-text search for code nodes
        CREATE INDEX IF NOT EXISTS idx_code_nodes_fts
        ON code_nodes USING gin(to_tsvector('english', name || ' ' || COALESCE(docstring, '')));
        """

        async with self.pool.acquire() as conn:
            await conn.execute(schema_sql)
            logger.info("✅ Code graph schema created")

    # Node Management

    async def upsert_code_node(self, node: CodeNode) -> bool:
        """Insert or update code node."""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO code_nodes (
                        id, workspace_id, node_type, name, file_path,
                        start_line, end_line, start_column, end_column,
                        language, namespace, docstring, complexity_score,
                        cognitive_load, requires_focus, adhd_summary, updated_at
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, NOW())
                    ON CONFLICT (id)
                    DO UPDATE SET
                        node_type = EXCLUDED.node_type,
                        name = EXCLUDED.name,
                        file_path = EXCLUDED.file_path,
                        start_line = EXCLUDED.start_line,
                        end_line = EXCLUDED.end_line,
                        start_column = EXCLUDED.start_column,
                        end_column = EXCLUDED.end_column,
                        language = EXCLUDED.language,
                        namespace = EXCLUDED.namespace,
                        docstring = EXCLUDED.docstring,
                        complexity_score = EXCLUDED.complexity_score,
                        cognitive_load = EXCLUDED.cognitive_load,
                        requires_focus = EXCLUDED.requires_focus,
                        adhd_summary = EXCLUDED.adhd_summary,
                        updated_at = NOW()
                """,
                    node.id, node.workspace_id, node.node_type.value, node.name, node.file_path,
                    node.start_line, node.end_line, node.start_column, node.end_column,
                    node.language, node.namespace, node.docstring, node.complexity_score,
                    node.cognitive_load, node.requires_focus, node.adhd_summary
                )

            return True

        except Exception as e:
            logger.error(f"Node upsert failed: {e}")
            return False

    async def upsert_relationship(self, relationship: CodeRelationship, workspace_id: str) -> bool:
        """Insert or update code relationship."""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO code_relationships (
                        workspace_id, source_node_id, target_node_id, relationship_type,
                        strength, context, line_number, updated_at
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
                    ON CONFLICT (workspace_id, source_node_id, target_node_id, relationship_type)
                    DO UPDATE SET
                        strength = EXCLUDED.strength,
                        context = EXCLUDED.context,
                        line_number = EXCLUDED.line_number,
                        updated_at = NOW()
                """,
                    workspace_id, relationship.source_node_id, relationship.target_node_id,
                    relationship.relationship_type.value, relationship.strength,
                    json.dumps(relationship.context), relationship.line_number
                )

            return True

        except Exception as e:
            logger.error(f"Relationship upsert failed: {e}")
            return False

    # Graph Queries

    async def find_related_nodes(
        self,
        node_id: str,
        workspace_id: str,
        relationship_types: Optional[List[RelationshipType]] = None,
        max_depth: int = 2,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Find nodes related to given node with ADHD optimization."""
        try:
            # Build relationship type filter
            type_filter = ""
            if relationship_types:
                type_placeholders = ','.join(f"${i+4}" for i in range(len(relationship_types)))
                type_filter = f"AND r.relationship_type = ANY(ARRAY[{type_placeholders}])"

            # Graph traversal query with depth limit
            query = f"""
                WITH RECURSIVE related_nodes AS (
                    -- Base case: direct relationships
                    SELECT
                        n.*, r.relationship_type, r.strength, 1 as depth,
                        r.source_node_id as path_source
                    FROM code_nodes n
                    JOIN code_relationships r ON (n.id = r.target_node_id OR n.id = r.source_node_id)
                    WHERE (r.source_node_id = $1 OR r.target_node_id = $1)
                      AND n.workspace_id = $2
                      AND n.id != $1
                      {type_filter}

                    UNION

                    -- Recursive case: indirect relationships
                    SELECT
                        n.*, r.relationship_type, r.strength, rn.depth + 1,
                        rn.path_source
                    FROM code_nodes n
                    JOIN code_relationships r ON (n.id = r.target_node_id OR n.id = r.source_node_id)
                    JOIN related_nodes rn ON (r.source_node_id = rn.id OR r.target_node_id = rn.id)
                    WHERE n.workspace_id = $2
                      AND n.id != rn.id
                      AND rn.depth < $3
                      {type_filter}
                )
                SELECT DISTINCT ON (id)
                    id, node_type, name, file_path, complexity_score, cognitive_load,
                    requires_focus, adhd_summary, relationship_type, strength, depth
                FROM related_nodes
                ORDER BY id, depth ASC, strength DESC
                LIMIT ${"4" if not relationship_types else str(4 + len(relationship_types))}
            """

            params = [node_id, workspace_id, max_depth, limit]
            if relationship_types:
                params.extend([rt.value for rt in relationship_types])

            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, *params)

                # Convert to ADHD-friendly format
                related_nodes = []
                for row in rows:
                    node_info = {
                        "id": row["id"],
                        "node_type": row["node_type"],
                        "name": row["name"],
                        "file_path": row["file_path"],
                        "file_name": Path(row["file_path"]).name,
                        "complexity_score": float(row["complexity_score"]),
                        "cognitive_load": float(row["cognitive_load"]),
                        "requires_focus": row["requires_focus"],
                        "adhd_summary": row["adhd_summary"],
                        "relationship": {
                            "type": row["relationship_type"],
                            "strength": float(row["strength"]),
                            "depth": row["depth"]
                        },
                        "adhd_guidance": self._generate_navigation_guidance(
                            row["cognitive_load"], row["requires_focus"]
                        )
                    }
                    related_nodes.append(node_info)

                # Sort by relevance for ADHD users
                related_nodes.sort(key=lambda n: (
                    n["relationship"]["depth"],           # Closer relationships first
                    -n["relationship"]["strength"],       # Stronger relationships first
                    n["cognitive_load"]                   # Lower cognitive load first
                ))

                logger.debug(f"🕸️ Found {len(related_nodes)} related nodes for {node_id}")
                return related_nodes

        except Exception as e:
            logger.error(f"Related nodes query failed: {e}")
            return []

    async def find_import_dependencies(
        self,
        file_path: str,
        workspace_id: str,
        max_depth: int = 3
    ) -> Dict[str, Any]:
        """Find import dependencies for file with ADHD visualization."""
        try:
            # Get file node ID
            file_node_id = self._generate_file_node_id(file_path, workspace_id)

            # Query import relationships
            query = """
                WITH RECURSIVE import_tree AS (
                    -- Direct imports
                    SELECT
                        target.file_path, target.name, target.node_type,
                        r.strength, 1 as depth, ARRAY[source.file_path] as path
                    FROM code_nodes source
                    JOIN code_relationships r ON source.id = r.source_node_id
                    JOIN code_nodes target ON r.target_node_id = target.id
                    WHERE source.file_path = $1
                      AND source.workspace_id = $2
                      AND r.relationship_type = 'imports'

                    UNION

                    -- Indirect imports
                    SELECT
                        target.file_path, target.name, target.node_type,
                        r.strength, it.depth + 1, it.path || target.file_path
                    FROM import_tree it
                    JOIN code_nodes source ON source.file_path = it.file_path
                    JOIN code_relationships r ON source.id = r.source_node_id
                    JOIN code_nodes target ON r.target_node_id = target.id
                    WHERE target.workspace_id = $2
                      AND r.relationship_type = 'imports'
                      AND it.depth < $3
                      AND NOT (target.file_path = ANY(it.path))  -- Prevent cycles
                )
                SELECT * FROM import_tree ORDER BY depth, strength DESC;
            """

            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, file_path, workspace_id, max_depth)

                # Build dependency tree structure
                dependency_tree = self._build_dependency_tree(rows, file_path)

                return {
                    "root_file": file_path,
                    "total_dependencies": len(rows),
                    "direct_dependencies": len([r for r in rows if r["depth"] == 1]),
                    "max_depth": max(row["depth"] for row in rows) if rows else 0,
                    "dependency_tree": dependency_tree,
                    "adhd_assessment": self._assess_dependency_complexity(rows),
                    "navigation_suggestions": self._generate_dependency_navigation_suggestions(dependency_tree)
                }

        except Exception as e:
            logger.error(f"Import dependency analysis failed: {e}")
            return {}

    async def find_call_hierarchy(
        self,
        function_name: str,
        file_path: str,
        workspace_id: str,
        direction: str = "both"  # "callers", "callees", "both"
    ) -> Dict[str, Any]:
        """Find call hierarchy for function with ADHD optimization."""
        try:
            # Generate function node ID
            function_node_id = self._generate_function_node_id(function_name, file_path, workspace_id)

            callers = []
            callees = []

            if direction in ["callers", "both"]:
                # Find who calls this function
                caller_query = """
                    SELECT
                        source.name as caller_name, source.file_path as caller_file,
                        source.node_type, source.complexity_score, source.cognitive_load,
                        r.line_number, r.context
                    FROM code_relationships r
                    JOIN code_nodes source ON r.source_node_id = source.id
                    JOIN code_nodes target ON r.target_node_id = target.id
                    WHERE target.id = $1
                      AND target.workspace_id = $2
                      AND r.relationship_type = 'calls'
                    ORDER BY source.complexity_score ASC  -- Simpler callers first for ADHD
                    LIMIT 20;
                """

                async with self.pool.acquire() as conn:
                    caller_rows = await conn.fetch(caller_query, function_node_id, workspace_id)
                    callers = [dict(row) for row in caller_rows]

            if direction in ["callees", "both"]:
                # Find what this function calls
                callee_query = """
                    SELECT
                        target.name as callee_name, target.file_path as callee_file,
                        target.node_type, target.complexity_score, target.cognitive_load,
                        r.line_number, r.context
                    FROM code_relationships r
                    JOIN code_nodes source ON r.source_node_id = source.id
                    JOIN code_nodes target ON r.target_node_id = target.id
                    WHERE source.id = $1
                      AND source.workspace_id = $2
                      AND r.relationship_type = 'calls'
                    ORDER BY target.complexity_score ASC  -- Simpler callees first for ADHD
                    LIMIT 20;
                """

                async with self.pool.acquire() as conn:
                    callee_rows = await conn.fetch(callee_query, function_node_id, workspace_id)
                    callees = [dict(row) for row in callee_rows]

            return {
                "function_name": function_name,
                "file_path": file_path,
                "callers": callers,
                "callees": callees,
                "caller_count": len(callers),
                "callee_count": len(callees),
                "complexity_assessment": self._assess_call_hierarchy_complexity(callers, callees),
                "adhd_navigation_tips": self._generate_call_hierarchy_tips(callers, callees)
            }

        except Exception as e:
            logger.error(f"Call hierarchy analysis failed: {e}")
            return {}

    # ADHD-Optimized Queries

    async def find_simple_entry_points(
        self,
        workspace_id: str,
        max_complexity: float = 0.4
    ) -> List[Dict[str, Any]]:
        """Find simple entry points for ADHD users to start exploring."""
        try:
            query = """
                SELECT id, name, file_path, node_type, complexity_score, cognitive_load, adhd_summary
                FROM code_nodes
                WHERE workspace_id = $1
                  AND node_type IN ('function', 'method')
                  AND complexity_score <= $2
                  AND NOT requires_focus
                ORDER BY complexity_score ASC, cognitive_load ASC
                LIMIT 10;
            """

            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, workspace_id, max_complexity)

                entry_points = []
                for row in rows:
                    entry_point = {
                        "id": row["id"],
                        "name": row["name"],
                        "file_name": Path(row["file_path"]).name,
                        "file_path": row["file_path"],
                        "type": row["node_type"],
                        "complexity": f"{row['complexity_score']:.1%}",
                        "cognitive_load": f"{row['cognitive_load']:.1%}",
                        "adhd_summary": row["adhd_summary"] or f"Simple {row['node_type']}: {row['name']}",
                        "why_good_start": self._explain_why_good_entry_point(row)
                    }
                    entry_points.append(entry_point)

                return entry_points

        except Exception as e:
            logger.error(f"Entry point search failed: {e}")
            return []

    async def find_focus_worthy_areas(
        self,
        workspace_id: str,
        min_complexity: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Find areas that require focused attention."""
        try:
            query = """
                SELECT id, name, file_path, node_type, complexity_score, cognitive_load, adhd_summary
                FROM code_nodes
                WHERE workspace_id = $1
                  AND (complexity_score >= $2 OR requires_focus = TRUE)
                ORDER BY complexity_score DESC, cognitive_load DESC
                LIMIT 15;
            """

            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, workspace_id, min_complexity)

                focus_areas = []
                for row in rows:
                    focus_area = {
                        "id": row["id"],
                        "name": row["name"],
                        "file_name": Path(row["file_path"]).name,
                        "file_path": row["file_path"],
                        "type": row["node_type"],
                        "complexity": f"{row['complexity_score']:.1%}",
                        "cognitive_load": f"{row['cognitive_load']:.1%}",
                        "adhd_summary": row["adhd_summary"] or f"Complex {row['node_type']}: {row['name']}",
                        "focus_recommendation": self._generate_focus_recommendation(row),
                        "preparation_tips": self._generate_preparation_tips(row)
                    }
                    focus_areas.append(focus_area)

                return focus_areas

        except Exception as e:
            logger.error(f"Focus area search failed: {e}")
            return []

    # Batch Operations for Performance

    async def batch_store_analysis(
        self,
        workspace_id: str,
        analysis_data: Dict[str, Any],
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """Store complete code analysis in batch for performance."""
        try:
            files_analyzed = analysis_data.get("files", {})
            relationships = analysis_data.get("relationships", [])

            stats = {"nodes_stored": 0, "relationships_stored": 0, "errors": 0}

            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    # Store all nodes
                    for file_path, file_analysis in files_analyzed.items():
                        try:
                            symbols = file_analysis.get("symbols", [])

                            for symbol_data in symbols:
                                node = CodeNode(
                                    id=self._generate_symbol_node_id(symbol_data, workspace_id),
                                    workspace_id=workspace_id,
                                    node_type=NodeType(symbol_data.get("symbol_type", "function")),
                                    name=symbol_data.get("name", "unknown"),
                                    file_path=file_path,
                                    start_line=symbol_data.get("start_line", 0),
                                    end_line=symbol_data.get("end_line", 0),
                                    language=file_analysis.get("language", ""),
                                    complexity_score=symbol_data.get("complexity_score", 0.5),
                                    cognitive_load=symbol_data.get("cognitive_load", 0.5),
                                    requires_focus=symbol_data.get("requires_focus", False),
                                    adhd_summary=symbol_data.get("adhd_friendly_summary")
                                )

                                if await self.upsert_code_node(node):
                                    stats["nodes_stored"] += 1

                            if progress_callback:
                                progress_callback(f"📊 Stored {stats['nodes_stored']} nodes from {Path(file_path).name}")

                        except Exception as e:
                            logger.error(f"Failed to store analysis for {file_path}: {e}")
                            stats["errors"] += 1

                    # Store relationships
                    for rel_data in relationships:
                        try:
                            relationship = CodeRelationship(
                                source_node_id=rel_data.get("source_node_id"),
                                target_node_id=rel_data.get("target_node_id"),
                                relationship_type=RelationshipType(rel_data.get("relationship_type", "references")),
                                strength=rel_data.get("strength", 1.0),
                                context=rel_data.get("context", {}),
                                line_number=rel_data.get("line_number")
                            )

                            if await self.upsert_relationship(relationship, workspace_id):
                                stats["relationships_stored"] += 1

                        except Exception as e:
                            logger.error(f"Failed to store relationship: {e}")
                            stats["errors"] += 1

            if progress_callback:
                progress_callback(f"✅ Batch storage complete: {stats['nodes_stored']} nodes, {stats['relationships_stored']} relationships")

            return stats

        except Exception as e:
            logger.error(f"Batch storage failed: {e}")
            return {"error": str(e)}

    # Utility Methods

    def _generate_file_node_id(self, file_path: str, workspace_id: str) -> str:
        """Generate consistent node ID for file."""
        import hashlib
        path_hash = hashlib.sha256(f"{workspace_id}:{file_path}".encode()).hexdigest()[:12]
        return f"file_{path_hash}"

    def _generate_function_node_id(self, function_name: str, file_path: str, workspace_id: str) -> str:
        """Generate consistent node ID for function."""
        import hashlib
        func_hash = hashlib.sha256(f"{workspace_id}:{file_path}:{function_name}".encode()).hexdigest()[:12]
        return f"func_{func_hash}"

    def _generate_symbol_node_id(self, symbol_data: Dict[str, Any], workspace_id: str) -> str:
        """Generate consistent node ID for symbol."""
        import hashlib
        symbol_string = f"{workspace_id}:{symbol_data.get('file_path')}:{symbol_data.get('name')}:{symbol_data.get('symbol_type')}"
        symbol_hash = hashlib.sha256(symbol_string.encode()).hexdigest()[:12]
        return f"sym_{symbol_hash}"

    def _build_dependency_tree(self, rows: List[Dict], root_file: str) -> Dict[str, Any]:
        """Build hierarchical dependency tree structure."""
        try:
            tree = {"file": root_file, "children": []}

            # Group by depth
            by_depth = {}
            for row in rows:
                depth = row["depth"]
                if depth not in by_depth:
                    by_depth[depth] = []
                by_depth[depth].append(row)

            # Build tree structure (simplified)
            for depth in sorted(by_depth.keys()):
                depth_items = by_depth[depth]
                tree["children"].extend([
                    {
                        "file": row["file_path"],
                        "name": row["name"],
                        "type": row["node_type"],
                        "depth": depth,
                        "strength": row["strength"]
                    }
                    for row in depth_items[:10]  # Limit for ADHD
                ])

            return tree

        except Exception:
            return {"file": root_file, "children": []}

    def _assess_dependency_complexity(self, dependencies: List[Dict]) -> str:
        """Assess dependency complexity for ADHD users."""
        if not dependencies:
            return "🟢 No dependencies - self-contained"

        total_deps = len(dependencies)
        max_depth = max(dep.get("depth", 1) for dep in dependencies)

        if total_deps <= 3 and max_depth <= 2:
            return "🟢 Simple dependencies - easy to understand"
        elif total_deps <= 10 and max_depth <= 3:
            return "🟡 Moderate dependencies - manageable complexity"
        elif total_deps <= 20:
            return "🟠 Complex dependencies - focus mode recommended"
        else:
            return "🔴 Very complex - consider breaking into smaller modules"

    def _generate_navigation_guidance(self, cognitive_load: float, requires_focus: bool) -> str:
        """Generate ADHD-friendly navigation guidance."""
        if requires_focus:
            return "🎯 High complexity - review during peak focus time"
        elif cognitive_load > 0.6:
            return "🧠 Moderate complexity - good for focused sessions"
        else:
            return "✅ Low complexity - good starting point"

    def _explain_why_good_entry_point(self, node_data: Dict) -> str:
        """Explain why a node is a good entry point for ADHD users."""
        reasons = []

        if node_data["complexity_score"] < 0.3:
            reasons.append("low complexity")
        if node_data["cognitive_load"] < 0.4:
            reasons.append("minimal cognitive load")
        if not node_data["requires_focus"]:
            reasons.append("no focused attention required")

        return f"Good starting point: {', '.join(reasons) if reasons else 'straightforward to understand'}"

    def _generate_focus_recommendation(self, node_data: Dict) -> str:
        """Generate focus recommendation for complex area."""
        complexity = node_data["complexity_score"]
        if complexity > 0.9:
            return "🚀 Peak focus recommended - tackle during your best cognitive hours"
        elif complexity > 0.7:
            return "🎯 Focused attention needed - minimize distractions"
        else:
            return "💡 Moderate focus required - good for focused work sessions"

    def _generate_preparation_tips(self, node_data: Dict) -> List[str]:
        """Generate preparation tips for complex areas."""
        tips = [
            "📖 Review related documentation first",
            "🎯 Enable focus mode to minimize distractions",
            "☕ Ensure you're well-rested and hydrated"
        ]

        if node_data["cognitive_load"] > 0.8:
            tips.append("🧠 Consider breaking into smaller exploration sessions")

        return tips

    # Health and Monitoring

    async def get_graph_health(self) -> Dict[str, Any]:
        """Get code graph storage health."""
        try:
            async with self.pool.acquire() as conn:
                # Get basic statistics
                stats = await conn.fetchrow("""
                    SELECT
                        COUNT(*) as total_nodes,
                        COUNT(DISTINCT workspace_id) as workspaces,
                        COUNT(DISTINCT file_path) as files,
                        AVG(complexity_score) as avg_complexity
                    FROM code_nodes;
                """)

                relationship_stats = await conn.fetchrow("""
                    SELECT
                        COUNT(*) as total_relationships,
                        COUNT(DISTINCT relationship_type) as relationship_types
                    FROM code_relationships;
                """)

                return {
                    "status": "🗄️ Active",
                    "database": {
                        "total_nodes": stats["total_nodes"],
                        "workspaces": stats["workspaces"],
                        "files_analyzed": stats["files"],
                        "average_complexity": f"{stats['avg_complexity']:.2f}" if stats["avg_complexity"] else "0.00"
                    },
                    "relationships": {
                        "total_relationships": relationship_stats["total_relationships"],
                        "relationship_types": relationship_stats["relationship_types"]
                    },
                    "connection_pool": {
                        "size": self.pool.get_size() if self.pool else 0,
                        "idle_connections": self.pool.get_idle_size() if self.pool else 0
                    }
                }

        except Exception as e:
            logger.error(f"Graph health check failed: {e}")
            return {"status": "🔴 Error", "error": str(e)}

    async def close(self) -> None:
        """Close graph storage connections."""
        if self.pool:
            await self.pool.close()
        logger.info("🗄️ Code graph storage closed")

    # Additional placeholder methods for full implementation
    def _generate_dependency_navigation_suggestions(self, tree: Dict) -> List[str]:
        return ["🔍 Start with direct dependencies", "📚 Review imported modules first"]

    def _assess_call_hierarchy_complexity(self, callers: List, callees: List) -> str:
        total_calls = len(callers) + len(callees)
        if total_calls <= 5:
            return "🟢 Simple call pattern"
        elif total_calls <= 15:
            return "🟡 Moderate call complexity"
        else:
            return "🟠 Complex call hierarchy"

    def _generate_call_hierarchy_tips(self, callers: List, callees: List) -> List[str]:
        return ["🎯 Review callers first to understand usage", "🔍 Then explore callees to understand implementation"]


# Factory function
async def create_code_graph_storage(
    config: CodeGraphConfig,
    workspace_id: str
) -> CodeGraphStorage:
    """Create and initialize code graph storage."""
    storage = CodeGraphStorage(config)
    await storage.initialize()
    return storage