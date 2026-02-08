"""
Serena v2 ConPort Client - Unified Client Integration

Adapter that wraps the unified ConPort client to match Serena's existing API.
This enables gradual migration without breaking existing code.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

# Add shared modules to path
SHARED_DIR = Path(__file__).parent.parent.parent / "shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from conport_client import ConPortClient, ConPortConfig


logger = logging.getLogger(__name__)


class ConPortDBClient:
    """
    Unified ConPort client adapter for Serena v2.

    Wraps the shared ConPortClient to match Serena's existing API.
    Enables migration without changing Serena's code.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5455,
        database: str = "dopemux_knowledge_graph",
        user: str = "dopemux_age",
        password: Optional[str] = None,
    ):
        """
        Initialize ConPort client (matches old API).

        Args:
            host: PostgreSQL host
            port: PostgreSQL port
            database: Database name
            user: Database user
            password: Password (from env if not provided)
        """
        # Create config for unified client
        config = ConPortConfig(
            workspace_id=os.getenv("WORKSPACE_ROOT", str(Path.cwd())),
            backend="postgresql_age",
            pg_host=host,
            pg_port=port,
            pg_user=user,
            pg_password=password or os.getenv(
                "CONPORT_DB_PASSWORD", "dopemux_age_dev_password"
            ),
            pg_database=database,
        )

        # Create unified client
        self.client = ConPortClient(config=config)
        self._pool = None  # Compatibility attribute

        logger.info(
            f"Initialized unified ConPort client (adapter): {database}@{host}:{port}"
        )

    async def connect(self):
        """Establish connection (compatibility method)."""
        # Unified client connects lazily, this is a no-op
        logger.debug("Connect called (no-op for unified client)")

    async def disconnect(self):
        """Close connection (compatibility method)."""
        # Unified client manages connections internally
        logger.debug("Disconnect called (no-op for unified client)")

    async def get_active_context(
        self, workspace_id: str, session_id: str = None
    ) -> Optional[Dict]:
        """
        Get active context for workspace/session.

        Args:
            workspace_id: Workspace identifier (ignored, uses config)
            session_id: Optional session ID

        Returns:
            Active context dict or None
        """
        context = await self.client.get_active_context(
            session_id=session_id or "default"
        )

        if context and context.content:
            # Return in old format
            return {
                "workspace_id": context.workspace_id,
                "session_id": context.session_id,
                "active_context": context.content,
                "updated_at": context.updated_at,
            }

        return None

    async def get_all_active_sessions(self, workspace_id: str) -> List[Dict]:
        """
        Get all active sessions for workspace.

        Args:
            workspace_id: Workspace identifier (ignored, uses config)

        Returns:
            List of session dicts
        """
        return await self.client.get_all_active_sessions()

    async def update_active_context(
        self, workspace_id: str, session_id: str, content: Dict[str, Any]
    ) -> bool:
        """
        Update or insert active context.

        Args:
            workspace_id: Workspace identifier (ignored, uses config)
            session_id: Session identifier
            content: Context data to store

        Returns:
            True if successful
        """
        try:
            await self.client.update_active_context(
                content=content, session_id=session_id
            )
            return True
        except Exception as e:
            logger.error(f"Failed to update active context: {e}")
            return False

    async def get_custom_data(
        self, workspace_id: str, category: str, key: Optional[str] = None
    ) -> List[Dict]:
        """
        Get custom data from ConPort.

        Args:
            workspace_id: Workspace identifier (ignored, uses config)
            category: Data category
            key: Optional specific key

        Returns:
            List of custom data entries (or single value if key provided)
        """
        result = await self.client.get_custom_data(category=category, key=key)

        if key:
            # Return as list for compatibility
            return [{"key": key, "value": result}] if result else []
        else:
            # Convert dict to list of dicts
            return [{"key": k, "value": v} for k, v in result.items()]

    async def get_progress(
        self, workspace_id: str, status_filter: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Get progress entries from ConPort.

        Args:
            workspace_id: Workspace identifier (ignored, uses config)
            status_filter: Optional list of statuses

        Returns:
            List of progress entry dicts
        """
        # Unified client takes single status, not list
        # For now, just use first status if list provided
        status = status_filter[0] if status_filter else None

        entries = await self.client.get_progress(status_filter=status)

        return [
            {
                "id": e.id,
                "status": e.status,
                "description": e.description,
                "parent_id": e.parent_id,
                "linked_item_type": e.linked_item_type,
                "linked_item_id": e.linked_item_id,
                "timestamp": e.timestamp,
            }
            for e in entries
        ]

    async def log_progress(
        self,
        workspace_id: str,
        status: str,
        description: str,
        parent_id: Optional[int] = None,
        linked_item_type: Optional[str] = None,
        linked_item_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Log progress entry to ConPort.

        Args:
            workspace_id: Workspace identifier (ignored, uses config)
            status: Progress status (TODO/IN_PROGRESS/DONE/BLOCKED)
            description: Human-readable task description
            parent_id: Optional parent progress entry ID
            linked_item_type: Optional linked item type
            linked_item_id: Optional linked item ID

        Returns:
            Dict matching legacy Serena expectations.
        """
        entry = await self.client.log_progress(
            status=status,
            description=description,
            parent_id=parent_id,
            linked_item_type=linked_item_type,
            linked_item_id=linked_item_id,
        )
        return {
            "id": entry.id,
            "status": entry.status,
            "description": entry.description,
            "parent_id": entry.parent_id,
            "linked_item_type": entry.linked_item_type,
            "linked_item_id": entry.linked_item_id,
            "timestamp": entry.timestamp,
        }

    async def log_custom_data(
        self, workspace_id: str, category: str, key: str, value: Any
    ) -> bool:
        """
        Log custom data to ConPort.

        Args:
            workspace_id: Workspace identifier (ignored, uses config)
            category: Data category
            key: Data key
            value: Data value

        Returns:
            True if successful
        """
        return await self.client.log_custom_data(category, key, value)

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
