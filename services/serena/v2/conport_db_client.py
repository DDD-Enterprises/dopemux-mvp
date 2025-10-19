"""
ConPort Database Client - Direct PostgreSQL Connection

Lightweight client for Serena v2 to query ConPort database directly.
Uses asyncpg for async operations matching Serena's async architecture.

Part of F001/F002 ConPort Integration
"""

import asyncpg
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import logging
import os
import json

logger = logging.getLogger(__name__)


class ConPortDBClient:
    """
    Direct PostgreSQL client for ConPort database.

    Provides async methods for F001/F002 to query:
    - workspace_contexts (sessions, active context)
    - custom_data (untracked work, sprint data)
    - progress_entries (tasks, TODO items)

    Connection Details:
    - Host: localhost (docker mapped)
    - Port: 5455
    - Database: dopemux_knowledge_graph
    - User: dopemux_age
    - Schema: ag_catalog
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5455,
        database: str = "dopemux_knowledge_graph",
        user: str = "dopemux_age",
        password: Optional[str] = None
    ):
        """
        Initialize ConPort database client.

        Args:
            host: PostgreSQL host
            port: PostgreSQL port
            database: Database name
            user: Database user
            password: Optional password (from env if not provided)
        """
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password or os.getenv("CONPORT_DB_PASSWORD", "dopemux_age_dev_password")

        self._pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Establish connection pool."""
        if self._pool:
            return

        try:
            self._pool = await asyncpg.create_pool(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            logger.info(f"Connected to ConPort database: {self.database}@{self.host}:{self.port}")

        except Exception as e:
            logger.error(f"Failed to connect to ConPort database: {e}")
            raise

    async def disconnect(self):
        """Close connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("Disconnected from ConPort database")

    async def get_active_context(self, workspace_id: str, session_id: str = None) -> Optional[Dict]:
        """
        Get active context for workspace/session.

        Args:
            workspace_id: Workspace identifier
            session_id: Optional session ID (None = get default session)

        Returns:
            Active context dict or None
        """
        if not self._pool:
            await self.connect()

        try:
            if session_id:
                query = """
                    SELECT * FROM ag_catalog.workspace_contexts
                    WHERE workspace_id = $1 AND session_id = $2
                    LIMIT 1
                """
                row = await self._pool.fetchrow(query, workspace_id, session_id)
            else:
                query = """
                    SELECT * FROM ag_catalog.workspace_contexts
                    WHERE workspace_id = $1 AND session_id = 'default'
                    LIMIT 1
                """
                row = await self._pool.fetchrow(query, workspace_id)

            if row:
                return dict(row)
            return None

        except Exception as e:
            logger.error(f"Failed to get active context: {e}")
            return None

    async def get_all_active_sessions(self, workspace_id: str) -> List[Dict]:
        """
        Get all active sessions for workspace.

        Used by F002 multi-session dashboard.

        Args:
            workspace_id: Workspace identifier

        Returns:
            List of session dicts
        """
        if not self._pool:
            await self.connect()

        try:
            query = """
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
            """
            rows = await self._pool.fetch(query, workspace_id)
            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get active sessions: {e}")
            return []

    async def update_active_context(
        self,
        workspace_id: str,
        session_id: str,
        content: Dict[str, Any]
    ) -> bool:
        """
        Update or insert active context.

        Args:
            workspace_id: Workspace identifier
            session_id: Session identifier
            content: Context data to store

        Returns:
            True if successful
        """
        if not self._pool:
            await self.connect()

        try:
            # Extract fields
            active_context = content.get('current_focus') or content.get('active_context')
            worktree_path = content.get('worktree_path')
            branch = content.get('branch')
            status = content.get('status', 'active')

            # Upsert
            query = """
                INSERT INTO ag_catalog.workspace_contexts
                    (workspace_id, session_id, active_context, worktree_path, branch, status, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (workspace_id, session_id)
                DO UPDATE SET
                    active_context = EXCLUDED.active_context,
                    worktree_path = EXCLUDED.worktree_path,
                    branch = EXCLUDED.branch,
                    status = EXCLUDED.status,
                    updated_at = EXCLUDED.updated_at
            """
            await self._pool.execute(
                query,
                workspace_id,
                session_id,
                active_context,
                worktree_path,
                branch,
                status,
                datetime.now(timezone.utc)
            )

            return True

        except Exception as e:
            logger.error(f"Failed to update active context: {e}")
            return False

    async def get_custom_data(
        self,
        workspace_id: str,
        category: str,
        key: Optional[str] = None
    ) -> List[Dict]:
        """
        Get custom data from ConPort.

        Used by F001 E1 (false_starts_aggregator) for untracked work stats.

        Args:
            workspace_id: Workspace identifier
            category: Data category (e.g., "untracked_work")
            key: Optional specific key

        Returns:
            List of custom data entries
        """
        if not self._pool:
            await self.connect()

        try:
            if key:
                query = """
                    SELECT * FROM ag_catalog.custom_data
                    WHERE workspace_id = $1 AND category = $2 AND key = $3
                """
                rows = await self._pool.fetch(query, workspace_id, category, key)
            else:
                query = """
                    SELECT * FROM ag_catalog.custom_data
                    WHERE workspace_id = $1 AND category = $2
                """
                rows = await self._pool.fetch(query, workspace_id, category)

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get custom data: {e}")
            return []

    async def get_progress(
        self,
        workspace_id: str,
        status_filter: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Get progress entries from ConPort.

        Used by F001 E4 (priority_context_builder) for active task queries.

        Args:
            workspace_id: Workspace identifier
            status_filter: Optional list of statuses (e.g., ["IN_PROGRESS", "TODO"])

        Returns:
            List of progress entry dicts
        """
        if not self._pool:
            await self.connect()

        try:
            if status_filter:
                query = """
                    SELECT * FROM ag_catalog.progress_entries
                    WHERE workspace_id = $1 AND status = ANY($2)
                    ORDER BY updated_at DESC
                """
                rows = await self._pool.fetch(query, workspace_id, status_filter)
            else:
                query = """
                    SELECT * FROM ag_catalog.progress_entries
                    WHERE workspace_id = $1
                    ORDER BY updated_at DESC
                """
                rows = await self._pool.fetch(query, workspace_id)

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get progress entries: {e}")
            return []

    async def log_custom_data(
        self,
        workspace_id: str,
        category: str,
        key: str,
        value: Any
    ) -> bool:
        """
        Log custom data to ConPort.

        Args:
            workspace_id: Workspace identifier
            category: Data category
            key: Data key
            value: Data value (will be JSON-serialized)

        Returns:
            True if successful
        """
        if not self._pool:
            await self.connect()

        try:
            # Convert value to JSON string if dict
            if isinstance(value, dict):
                value_json = json.dumps(value)
            else:
                value_json = value

            query = """
                INSERT INTO ag_catalog.custom_data
                    (workspace_id, category, key, value, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (workspace_id, category, key)
                DO UPDATE SET
                    value = EXCLUDED.value,
                    updated_at = EXCLUDED.updated_at
            """
            await self._pool.execute(
                query,
                workspace_id,
                category,
                key,
                value_json,
                datetime.now(timezone.utc),
                datetime.now(timezone.utc)
            )

            return True

        except Exception as e:
            logger.error(f"Failed to log custom data: {e}")
            return False

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
