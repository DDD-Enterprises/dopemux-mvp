"""
F-NEW-7 Phase 2: Unified Query Layer
Enables cross-workspace search and relationship traversal for multi-user support.

ADHD Optimization: <200ms target for cross-workspace queries
Architecture: PostgreSQL with composite indexes + Redis caching
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID

import asyncpg
from redis import asyncio as redis

logger = logging.getLogger(__name__)


@dataclass
class UnifiedSearchResult:
    """Cross-workspace search result with metadata."""
    decision_id: str
    workspace_id: str
    summary: str
    rationale: str
    created_at: datetime
    relevance_score: float
    user_id: str
    tags: List[str]


@dataclass
class WorkspaceSummary:
    """Per-workspace statistics."""
    workspace_id: str
    name: str
    total_decisions: int
    recent_decisions_7d: int
    total_progress: int
    in_progress_count: int
    last_activity: Optional[datetime]


class UnifiedQueryAPI:
    """
    Unified query layer for cross-workspace operations.

    Features:
    - Cross-workspace full-text search
    - Multi-workspace relationship traversal
    - Workspace aggregations and summaries
    - ADHD-optimized caching (5min workspace list, 1min results)
    """

    def __init__(
        self,
        db_pool: asyncpg.Pool,
        redis_client: redis.Redis,
        schema: str = "public"
    ):
        self.db_pool = db_pool
        self.redis = redis_client
        self.schema = schema

        # Cache TTLs (ADHD-optimized)
        self.workspace_list_ttl = 300  # 5 minutes
        self.search_results_ttl = 60   # 1 minute
        self.relationship_ttl = 1800   # 30 minutes

    async def search_across_workspaces(
        self,
        user_id: str,
        query: str,
        workspaces: Optional[List[str]] = None,
        limit: int = 50
    ) -> List[UnifiedSearchResult]:
        """
        Cross-workspace full-text search.

        Args:
            user_id: User identifier
            query: Search query
            workspaces: Specific workspaces to search (None = all user's workspaces)
            limit: Max results (default 50, ADHD-safe)

        Returns:
            Search results ranked by relevance + recency

        Performance: <200ms target (ADHD requirement)
        """
        # Check cache first
        cache_key = f"unified_search:{user_id}:{query}:{','.join(workspaces or ['all'])}"
        cached = await self.redis.get(cache_key)
        if cached:
            logger.debug(f"Cache hit for unified search: {user_id}")
            results_data = json.loads(cached)
            return [UnifiedSearchResult(**r) for r in results_data]

        # Get user's workspaces if not specified
        if workspaces is None:
            workspaces = await self._get_user_workspaces(user_id)

        async with self.db_pool.acquire() as conn:
            has_user_id = await self._column_exists(conn, "decisions", "user_id")
            if has_user_id:
                sql = f"""
                    SELECT
                        id::text as decision_id,
                        workspace_id,
                        summary,
                        rationale,
                        created_at,
                        ts_rank(
                            to_tsvector('english', summary || ' ' || COALESCE(rationale, '')),
                            plainto_tsquery('english', $1)
                        ) as relevance_score,
                        user_id,
                        tags
                    FROM {self.schema}.decisions
                    WHERE user_id = $2
                      AND workspace_id = ANY($3)
                      AND to_tsvector('english', summary || ' ' || COALESCE(rationale, ''))
                          @@ plainto_tsquery('english', $1)
                    ORDER BY relevance_score DESC, created_at DESC
                    LIMIT $4
                """
                rows = await conn.fetch(sql, query, user_id, workspaces, limit)
            else:
                sql = f"""
                    SELECT
                        id::text as decision_id,
                        workspace_id,
                        summary,
                        rationale,
                        created_at,
                        ts_rank(
                            to_tsvector('english', summary || ' ' || COALESCE(rationale, '')),
                            plainto_tsquery('english', $1)
                        ) as relevance_score,
                        tags
                    FROM {self.schema}.decisions
                    WHERE workspace_id = ANY($2)
                      AND to_tsvector('english', summary || ' ' || COALESCE(rationale, ''))
                          @@ plainto_tsquery('english', $1)
                    ORDER BY relevance_score DESC, created_at DESC
                    LIMIT $3
                """
                rows = await conn.fetch(sql, query, workspaces, limit)

        results = [
            UnifiedSearchResult(
                decision_id=row['decision_id'],
                workspace_id=row['workspace_id'],
                summary=row['summary'],
                rationale=row['rationale'] or '',
                created_at=row['created_at'],
                relevance_score=float(row['relevance_score']),
                user_id=row['user_id'] if has_user_id else user_id,
                tags=row['tags'] or []
            )
            for row in rows
        ]

        # Cache results
        results_data = [
            {
                'decision_id': r.decision_id,
                'workspace_id': r.workspace_id,
                'summary': r.summary,
                'rationale': r.rationale,
                'created_at': r.created_at.isoformat(),
                'relevance_score': r.relevance_score,
                'user_id': r.user_id,
                'tags': r.tags
            }
            for r in results
        ]
        await self.redis.setex(
            cache_key,
            self.search_results_ttl,
            json.dumps(results_data, default=str)
        )

        logger.info(f"Unified search: {len(results)} results for '{query}' across {len(workspaces)} workspaces")
        return results

    async def get_related_decisions(
        self,
        decision_id: str,
        user_id: str,
        include_workspaces: bool = True,
        max_depth: int = 3
    ) -> Dict[str, Any]:
        """
        Multi-workspace relationship traversal.

        Args:
            decision_id: Starting decision
            user_id: User identifier (for permission check)
            include_workspaces: Include cross-workspace relationships
            max_depth: Max traversal depth (default 3, ADHD-safe)

        Returns:
            Graph of related decisions with relationships

        Performance: <500ms for depth-3
        """
        # Check cache
        cache_key = f"relationships:{decision_id}:{user_id}:{include_workspaces}:{max_depth}"
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        async with self.db_pool.acquire() as conn:
            has_user_id = await self._column_exists(conn, "decisions", "user_id")
            if has_user_id:
                cross_workspace_clause = (
                    "AND (d.workspace_id = dg.workspace_id OR $4 = true)"
                    if include_workspaces else ""
                )
                sql = f"""
                    WITH RECURSIVE decision_graph AS (
                        -- Base case: starting decision
                        SELECT
                            id::text as id, workspace_id, summary, 0 as depth,
                            ARRAY[id::text] as path
                        FROM {self.schema}.decisions
                        WHERE id::text = $1 AND user_id = $2

                        UNION

                        -- Recursive case: follow relationships
                        SELECT
                            d.id::text as id, d.workspace_id, d.summary, dg.depth + 1,
                            dg.path || d.id::text
                        FROM decision_graph dg
                        INNER JOIN {self.schema}.entity_relationships r
                            ON (dg.id = r.source_id::text OR dg.id = r.target_id::text)
                        INNER JOIN {self.schema}.decisions d
                            ON (
                                (r.target_id::text = d.id::text AND r.source_id::text = dg.id)
                                OR (r.source_id::text = d.id::text AND r.target_id::text = dg.id)
                            )
                        WHERE d.user_id = $2
                          AND dg.depth < $3
                          AND NOT (d.id::text = ANY(dg.path))
                          {cross_workspace_clause}
                    )
                    SELECT DISTINCT id, workspace_id, summary, depth
                    FROM decision_graph
                    ORDER BY depth, id
                """
                args = (
                    (str(decision_id), user_id, max_depth, include_workspaces)
                    if include_workspaces else (str(decision_id), user_id, max_depth)
                )
            else:
                cross_workspace_clause = (
                    "AND (d.workspace_id = dg.workspace_id OR $3 = true)"
                    if include_workspaces else ""
                )
                sql = f"""
                    WITH RECURSIVE decision_graph AS (
                        -- Base case: starting decision
                        SELECT
                            id::text as id, workspace_id, summary, 0 as depth,
                            ARRAY[id::text] as path
                        FROM {self.schema}.decisions
                        WHERE id::text = $1

                        UNION

                        -- Recursive case: follow relationships
                        SELECT
                            d.id::text as id, d.workspace_id, d.summary, dg.depth + 1,
                            dg.path || d.id::text
                        FROM decision_graph dg
                        INNER JOIN {self.schema}.entity_relationships r
                            ON (dg.id = r.source_id::text OR dg.id = r.target_id::text)
                        INNER JOIN {self.schema}.decisions d
                            ON (
                                (r.target_id::text = d.id::text AND r.source_id::text = dg.id)
                                OR (r.source_id::text = d.id::text AND r.target_id::text = dg.id)
                            )
                        WHERE dg.depth < $2
                          AND NOT (d.id::text = ANY(dg.path))
                          {cross_workspace_clause}
                    )
                    SELECT DISTINCT id, workspace_id, summary, depth
                    FROM decision_graph
                    ORDER BY depth, id
                """
                args = (
                    (str(decision_id), max_depth, include_workspaces)
                    if include_workspaces else (str(decision_id), max_depth)
                )

            rows = await conn.fetch(sql, *args)

        graph = {
            'root': str(decision_id),
            'nodes': [
                {
                    'id': row['id'],
                    'workspace_id': row['workspace_id'],
                    'summary': row['summary'],
                    'depth': row['depth']
                }
                for row in rows
            ],
            'total_nodes': len(rows),
            'max_depth_reached': max(row['depth'] for row in rows) if rows else 0
        }

        # Cache graph
        await self.redis.setex(
            cache_key,
            self.relationship_ttl,
            json.dumps(graph)
        )

        logger.info(f"Relationship graph: {len(rows)} nodes, depth {graph['max_depth_reached']}")
        return graph

    async def get_workspace_summary(self, user_id: str) -> List[WorkspaceSummary]:
        """
        Per-workspace statistics for user.

        Args:
            user_id: User identifier

        Returns:
            List of workspace summaries with activity metrics

        Performance: <100ms
        """
        # Check cache
        cache_key = f"workspace_summary:{user_id}"
        cached = await self.redis.get(cache_key)
        if cached:
            summaries_data = json.loads(cached)
            return [WorkspaceSummary(**s) for s in summaries_data]

        async with self.db_pool.acquire() as conn:
            decisions_have_user_id = await self._column_exists(conn, "decisions", "user_id")
            progress_has_user_id = await self._column_exists(conn, "progress_entries", "user_id")
            user_join_clause = " AND p.user_id = d.user_id" if progress_has_user_id else ""
            user_where_clause = "WHERE d.user_id = $1" if decisions_have_user_id else ""
            sql = f"""
                SELECT
                    d.workspace_id,
                    d.workspace_id as name,
                    COUNT(DISTINCT d.id) as total_decisions,
                    COUNT(DISTINCT d.id) FILTER (
                        WHERE d.created_at >= NOW() - INTERVAL '7 days'
                    ) as recent_decisions_7d,
                    COUNT(DISTINCT p.id) as total_progress,
                    COUNT(DISTINCT p.id) FILTER (
                        WHERE p.status = 'IN_PROGRESS'
                    ) as in_progress_count,
                    MAX(GREATEST(d.created_at, p.created_at)) as last_activity
                FROM {self.schema}.decisions d
                LEFT JOIN {self.schema}.progress_entries p
                    ON p.workspace_id = d.workspace_id{user_join_clause}
                {user_where_clause}
                GROUP BY d.workspace_id
                ORDER BY last_activity DESC NULLS LAST
            """
            rows = (
                await conn.fetch(sql, user_id)
                if decisions_have_user_id else await conn.fetch(sql)
            )

        summaries = [
            WorkspaceSummary(
                workspace_id=row['workspace_id'],
                name=row['name'],
                total_decisions=row['total_decisions'],
                recent_decisions_7d=row['recent_decisions_7d'],
                total_progress=row['total_progress'],
                in_progress_count=row['in_progress_count'],
                last_activity=row['last_activity']
            )
            for row in rows
        ]

        # Cache summaries
        summaries_data = [
            {
                'workspace_id': s.workspace_id,
                'name': s.name,
                'total_decisions': s.total_decisions,
                'recent_decisions_7d': s.recent_decisions_7d,
                'total_progress': s.total_progress,
                'in_progress_count': s.in_progress_count,
                'last_activity': s.last_activity.isoformat() if s.last_activity else None
            }
            for s in summaries
        ]
        await self.redis.setex(
            cache_key,
            self.workspace_list_ttl,
            json.dumps(summaries_data, default=str)
        )

        logger.info(f"Workspace summary: {len(summaries)} workspaces for {user_id}")
        return summaries

    async def _get_user_workspaces(self, user_id: str) -> List[str]:
        """Get all workspace IDs for a user (cached)."""
        cache_key = f"user_workspaces:{user_id}"
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        async with self.db_pool.acquire() as conn:
            has_user_id = await self._column_exists(conn, "decisions", "user_id")
            if has_user_id:
                sql = f"""
                    SELECT DISTINCT workspace_id
                    FROM {self.schema}.decisions
                    WHERE user_id = $1
                    ORDER BY workspace_id
                """
                rows = await conn.fetch(sql, user_id)
            else:
                sql = f"""
                    SELECT DISTINCT workspace_id
                    FROM {self.schema}.decisions
                    ORDER BY workspace_id
                """
                rows = await conn.fetch(sql)

        workspaces = [row['workspace_id'] for row in rows]

        # Cache workspace list
        await self.redis.setex(
            cache_key,
            self.workspace_list_ttl,
            json.dumps(workspaces)
        )

        return workspaces

    async def _column_exists(self, conn: asyncpg.Connection, table_name: str, column_name: str) -> bool:
        """Return whether the configured schema exposes a column."""
        sql = """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = $1
                  AND table_name = $2
                  AND column_name = $3
            )
        """
        return bool(await conn.fetchval(sql, self.schema, table_name, column_name))
