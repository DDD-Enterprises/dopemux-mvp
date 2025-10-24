"""
ADHD Engine ConPort Client - Unified Client Integration

Adapter that wraps the unified ConPort client to match ADHD Engine's existing API.
Migrates from SQLite to PostgreSQL AGE backend for multi-session support.
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

# Add shared modules to path
SHARED_DIR = Path(__file__).parent.parent / "shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from conport_client import ConPortClient, ConPortConfig


logger = logging.getLogger(__name__)


class ConPortSQLiteClient:
    """
    Unified ConPort client adapter for ADHD Engine.

    NOTE: Despite the name "SQLiteClient", this now uses PostgreSQL AGE backend
    via the unified client. Name preserved for API compatibility during migration.

    Migrated from SQLite to PostgreSQL for:
    - Multi-session support
    - Better performance
    - Unified backend across all systems
    """

    def __init__(
        self,
        db_path: str,
        workspace_id: str,
        read_only: bool = True,
    ):
        """
        Initialize ConPort client (matches old API).

        Args:
            db_path: IGNORED (kept for API compatibility, uses PostgreSQL now)
            workspace_id: Workspace identifier
            read_only: IGNORED (PostgreSQL manages permissions)
        """
        # Create config for unified client (PostgreSQL backend)
        config = ConPortConfig(
            workspace_id=workspace_id,
            backend="postgresql_age",
            pg_host="localhost",
            pg_port=5455,
            pg_user="dopemux_age",
            pg_password="dopemux_age_dev_password",
            pg_database="dopemux_knowledge_graph",
        )

        # Create unified client
        self.client = ConPortClient(config=config)
        self.db_path = db_path  # Stored but unused
        self.workspace_id = workspace_id
        self.read_only = read_only

        logger.info(
            f"Initialized unified ConPort client (ADHD adapter): PostgreSQL backend for {Path(workspace_id).name}"
        )

    def _get_connection(self, write_mode: bool = False):
        """
        Compatibility method (no-op).

        Old SQLite code called this - now handled by unified client internally.
        """
        return None  # Not used, unified client manages connections

    def get_progress_entries(
        self,
        limit: int = 20,
        status_filter: Optional[str] = None,
        hours_ago: int = 24,
    ) -> List[Dict[str, Any]]:
        """
        Get recent progress entries (SYNC wrapper for async call).

        Args:
            limit: Maximum entries
            status_filter: Optional status filter
            hours_ago: IGNORED (PostgreSQL has all data)

        Returns:
            List of progress entry dicts
        """
        import asyncio

        # Run async method synchronously
        loop = asyncio.get_event_loop()
        entries = loop.run_until_complete(
            self.client.get_progress(status_filter=status_filter, limit=limit)
        )

        return [
            {
                "id": e.id,
                "status": e.status,
                "description": e.description,
                "parent_id": e.parent_id,
                "linked_item_type": e.linked_item_type,
                "linked_item_id": e.linked_item_id,
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            }
            for e in entries
        ]

    def get_custom_data(
        self, category: str, key: Optional[str] = None
    ) -> Any:
        """
        Get custom data (SYNC wrapper).

        Args:
            category: Data category
            key: Optional specific key

        Returns:
            Single value or dict of values
        """
        import asyncio

        loop = asyncio.get_event_loop()
        return loop.run_until_complete(
            self.client.get_custom_data(category=category, key=key)
        )

    def get_recent_decisions(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get recent decisions (SYNC wrapper).

        Args:
            limit: Maximum decisions

        Returns:
            List of decision dicts
        """
        import asyncio

        loop = asyncio.get_event_loop()
        decisions = loop.run_until_complete(
            self.client.get_recent_decisions(limit=limit)
        )

        return [
            {
                "id": d.id,
                "summary": d.summary,
                "timestamp": d.timestamp.isoformat() if d.timestamp else None,
            }
            for d in decisions
        ]

    def write_custom_data(self, category: str, key: str, value: Any) -> bool:
        """
        Write custom data (SYNC wrapper).

        Args:
            category: Data category
            key: Data key
            value: Data value

        Returns:
            True if successful
        """
        import asyncio

        loop = asyncio.get_event_loop()
        return loop.run_until_complete(
            self.client.log_custom_data(category=category, key=key, value=value)
        )

    def log_progress_entry(
        self,
        status: str,
        description: str,
        parent_id: Optional[int] = None,
    ) -> Optional[int]:
        """
        Create progress entry (SYNC wrapper).

        Args:
            status: Status (TODO, IN_PROGRESS, DONE, BLOCKED)
            description: Task description
            parent_id: Optional parent task ID

        Returns:
            New progress entry ID
        """
        import asyncio

        loop = asyncio.get_event_loop()
        entry = loop.run_until_complete(
            self.client.log_progress(
                status=status, description=description, parent_id=parent_id
            )
        )

        return entry.id if entry else None

    def health_check(self) -> Dict[str, Any]:
        """
        Check if ConPort is accessible (SYNC wrapper).

        Returns:
            Health status dict
        """
        import asyncio

        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.client.health_check())
