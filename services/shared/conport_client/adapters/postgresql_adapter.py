"""
PostgreSQL AGE adapter for ConPort client.

Uses psycopg2/asyncpg to connect to PostgreSQL with AGE extension.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from ..backends import BackendType
from ..models import Decision, ProgressEntry, ActiveContext


logger = logging.getLogger(__name__)


class PostgreSQLAGEAdapter:
    """
    PostgreSQL AGE backend adapter.

    Connects to ConPort PostgreSQL database using asyncpg.
    """

    backend_type = BackendType.POSTGRESQL_AGE

    def __init__(self, config):
        """Initialize PostgreSQL adapter."""
        self.config = config
        self.pool = None  # Connection pool (lazy init)

    async def _ensure_pool(self):
        """Ensure connection pool exists (lazy initialization)."""
        if self.pool is not None:
            return

        try:
            import asyncpg

            self.pool = await asyncpg.create_pool(
                host=self.config.pg_host,
                port=self.config.pg_port,
                user=self.config.pg_user,
                password=self.config.pg_password,
                database=self.config.pg_database,
                min_size=2,
                max_size=10,
            )

            logger.info(f"PostgreSQL connection pool created ({self.config.pg_host}:{self.config.pg_port})")

        except ImportError:
            raise RuntimeError("asyncpg not installed: pip install asyncpg")
        except Exception as e:
            raise RuntimeError(f"Failed to create PostgreSQL pool: {e}")

    async def log_decision(
        self,
        workspace_id: str,
        summary: str,
        rationale: Optional[str] = None,
        implementation_details: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Decision:
        """Log decision to PostgreSQL."""
        await self._ensure_pool()

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO ag_catalog.decisions
                (workspace_id, summary, rationale, implementation_details, tags)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id, summary, rationale, implementation_details, tags, timestamp
                """,
                workspace_id,
                summary,
                rationale,
                implementation_details,
                tags or [],
            )

            return Decision(
                id=row["id"],
                summary=row["summary"],
                rationale=row["rationale"],
                implementation_details=row["implementation_details"],
                tags=row["tags"] or [],
                timestamp=row["timestamp"],
            )

    async def get_decisions(
        self,
        workspace_id: str,
        limit: Optional[int] = None,
        tags: Optional[List[str]] = None,
    ) -> List[Decision]:
        """Get decisions from PostgreSQL."""
        await self._ensure_pool()

        query = "SELECT id, summary, rationale, implementation_details, tags, timestamp FROM ag_catalog.decisions WHERE workspace_id = $1"
        params = [workspace_id]

        # TODO: Add tag filtering

        query += " ORDER BY timestamp DESC"

        if limit:
            query += f" LIMIT {limit}"

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)

            return [
                Decision(
                    id=row["id"],
                    summary=row["summary"],
                    rationale=row["rationale"],
                    implementation_details=row["implementation_details"],
                    tags=row["tags"] or [],
                    timestamp=row["timestamp"],
                )
                for row in rows
            ]

    async def get_active_context(
        self, workspace_id: str, session_id: str = "default"
    ) -> ActiveContext:
        """Get active context from PostgreSQL."""
        await self._ensure_pool()

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT workspace_id, session_id, active_context, updated_at
                FROM ag_catalog.workspace_contexts
                WHERE workspace_id = $1 AND session_id = $2
                """,
                workspace_id,
                session_id,
            )

            if row:
                # Parse JSON content
                content = json.loads(row["active_context"]) if row["active_context"] else {}

                return ActiveContext(
                    workspace_id=row["workspace_id"],
                    session_id=row["session_id"],
                    content=content,
                    updated_at=row["updated_at"],
                )
            else:
                # Return empty context
                return ActiveContext(
                    workspace_id=workspace_id,
                    session_id=session_id,
                    content={},
                )

    async def update_active_context(
        self, workspace_id: str, session_id: str, content: Dict[str, Any]
    ) -> None:
        """Update active context in PostgreSQL."""
        await self._ensure_pool()

        content_json = json.dumps(content)

        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO ag_catalog.workspace_contexts (workspace_id, session_id, active_context)
                VALUES ($1, $2, $3)
                ON CONFLICT (workspace_id, session_id)
                DO UPDATE SET active_context = $3, updated_at = NOW()
                """,
                workspace_id,
                session_id,
                content_json,
            )

    async def log_progress(
        self,
        workspace_id: str,
        status: str,
        description: str,
        parent_id: Optional[int] = None,
        linked_item_type: Optional[str] = None,
        linked_item_id: Optional[str] = None,
    ) -> ProgressEntry:
        """Log progress entry."""
        await self._ensure_pool()

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO ag_catalog.progress_entries
                (workspace_id, status, description, parent_id, linked_item_type, linked_item_id)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id, status, description, parent_id, linked_item_type, linked_item_id, timestamp
                """,
                workspace_id,
                status,
                description,
                parent_id,
                linked_item_type,
                linked_item_id,
            )

            return ProgressEntry(
                id=row["id"],
                status=row["status"],
                description=row["description"],
                parent_id=row["parent_id"],
                linked_item_type=row["linked_item_type"],
                linked_item_id=row["linked_item_id"],
                timestamp=row["timestamp"],
            )

    async def get_progress(
        self,
        workspace_id: str,
        status_filter: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[ProgressEntry]:
        """Get progress entries."""
        await self._ensure_pool()

        query = "SELECT id, status, description, parent_id, linked_item_type, linked_item_id, timestamp FROM ag_catalog.progress_entries WHERE workspace_id = $1"
        params = [workspace_id]

        if status_filter:
            query += " AND status = $2"
            params.append(status_filter)

        query += " ORDER BY timestamp DESC"

        if limit:
            query += f" LIMIT {limit}"

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)

            return [
                ProgressEntry(
                    id=row["id"],
                    status=row["status"],
                    description=row["description"],
                    parent_id=row["parent_id"],
                    linked_item_type=row["linked_item_type"],
                    linked_item_id=row["linked_item_id"],
                    timestamp=row["timestamp"],
                )
                for row in rows
            ]

    async def get_all_active_sessions(
        self, workspace_id: str
    ) -> List[Dict[str, Any]]:
        """Get all active sessions for workspace (Serena F002)."""
        await self._ensure_pool()

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    session_id,
                    worktree_path,
                    branch,
                    active_context as focus,
                    EXTRACT(EPOCH FROM (NOW() - updated_at)) / 60 as minutes_ago,
                    status,
                    updated_at
                FROM ag_catalog.workspace_contexts
                WHERE workspace_id = $1
                  AND status = 'active'
                  AND updated_at > NOW() - INTERVAL '24 hours'
                ORDER BY updated_at DESC
                """,
                workspace_id,
            )

            return [dict(row) for row in rows]

    async def get_custom_data(
        self,
        workspace_id: str,
        category: str,
        key: Optional[str] = None,
    ) -> Any:
        """Get custom data from ConPort."""
        await self._ensure_pool()

        async with self.pool.acquire() as conn:
            if key:
                row = await conn.fetchrow(
                    "SELECT value FROM ag_catalog.custom_data WHERE workspace_id = $1 AND category = $2 AND key = $3",
                    workspace_id,
                    category,
                    key,
                )
                if row:
                    import json
                    try:
                        return json.loads(row["value"])
                    except json.JSONDecodeError:
                        return row["value"]
                return None
            else:
                rows = await conn.fetch(
                    "SELECT key, value FROM ag_catalog.custom_data WHERE workspace_id = $1 AND category = $2",
                    workspace_id,
                    category,
                )
                import json
                result = {}
                for row in rows:
                    try:
                        result[row["key"]] = json.loads(row["value"])
                    except json.JSONDecodeError:
                        result[row["key"]] = row["value"]
                return result

    async def log_custom_data(
        self,
        workspace_id: str,
        category: str,
        key: str,
        value: Any,
    ) -> bool:
        """Log custom data to ConPort."""
        await self._ensure_pool()

        import json

        value_json = json.dumps(value) if isinstance(value, dict) else value

        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO ag_catalog.custom_data
                    (workspace_id, category, key, value, created_at, updated_at)
                VALUES ($1, $2, $3, $4, NOW(), NOW())
                ON CONFLICT (workspace_id, category, key)
                DO UPDATE SET
                    value = EXCLUDED.value,
                    updated_at = NOW()
                """,
                workspace_id,
                category,
                key,
                value_json,
            )

        return True

    async def get_recent_decisions(
        self, workspace_id: str, limit: int = 5
    ) -> List[Decision]:
        """Get recent decisions (for ADHD context awareness)."""
        await self._ensure_pool()

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, summary, timestamp
                FROM ag_catalog.decisions
                WHERE workspace_id = $1
                ORDER BY timestamp DESC
                LIMIT $2
                """,
                workspace_id,
                limit,
            )

            return [
                Decision(
                    id=row["id"],
                    summary=row["summary"],
                    rationale=None,
                    implementation_details=None,
                    tags=[],
                    timestamp=row["timestamp"],
                )
                for row in rows
            ]

    async def health_check(self) -> Dict[str, Any]:
        """Check PostgreSQL connection health."""
        try:
            await self._ensure_pool()

            async with self.pool.acquire() as conn:
                result = await conn.fetchval("SELECT 1")

            return {
                "status": "healthy",
                "backend": "postgresql_age",
                "connected": True,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "backend": "postgresql_age",
                "connected": False,
                "error": str(e),
            }
