"""
Unified ConPort Client with backend abstraction.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any

from .models import Decision, ProgressEntry, ActiveContext
from .backends import BackendType, get_backend_adapter


logger = logging.getLogger(__name__)


@dataclass
class ConPortConfig:
    """Configuration for ConPort client."""

    workspace_id: str
    backend: Optional[BackendType] = None  # Auto-detect if None
    db_path: Optional[str] = None  # For SQLite backend
    mcp_url: Optional[str] = None  # For MCP RPC backend
    pg_host: str = "localhost"
    pg_port: int = 5455
    pg_user: str = "dopemux_age"
    pg_password: str = "dopemux_age_dev_password"
    pg_database: str = "dopemux_knowledge_graph"


class ConPortClient:
    """
    Unified ConPort client with backend abstraction.

    Automatically selects best available backend or uses specified backend.
    """

    def __init__(self, workspace_id: str = None, config: ConPortConfig = None, **kwargs):
        """
        Initialize ConPort client.

        Args:
            workspace_id: Workspace path
            config: ConPortConfig object
            **kwargs: Config overrides (workspace_id, backend, db_path, etc.)
        """
        # Build config
        if config:
            self.config = config
        else:
            # Auto-detect workspace
            if not workspace_id:
                workspace_id = str(Path.cwd())

            self.config = ConPortConfig(workspace_id=workspace_id, **kwargs)

        # Get backend adapter
        self.backend = get_backend_adapter(self.config)

        logger.info(
            f"ConPortClient initialized: workspace={Path(self.config.workspace_id).name}, "
            f"backend={self.backend.backend_type.value}"
        )

    async def log_decision(
        self,
        summary: str,
        rationale: Optional[str] = None,
        implementation_details: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Decision:
        """Log a decision."""
        return await self.backend.log_decision(
            workspace_id=self.config.workspace_id,
            summary=summary,
            rationale=rationale,
            implementation_details=implementation_details,
            tags=tags or [],
        )

    async def get_decisions(
        self, limit: Optional[int] = None, tags: Optional[List[str]] = None
    ) -> List[Decision]:
        """Get decisions."""
        return await self.backend.get_decisions(
            workspace_id=self.config.workspace_id,
            limit=limit,
            tags=tags,
        )

    async def get_active_context(self, session_id: str = "default") -> ActiveContext:
        """Get active context."""
        return await self.backend.get_active_context(
            workspace_id=self.config.workspace_id,
            session_id=session_id,
        )

    async def update_active_context(
        self, content: Dict[str, Any], session_id: str = "default"
    ) -> None:
        """Update active context."""
        await self.backend.update_active_context(
            workspace_id=self.config.workspace_id,
            session_id=session_id,
            content=content,
        )

    async def log_progress(
        self,
        status: str,
        description: str,
        parent_id: Optional[int] = None,
        linked_item_type: Optional[str] = None,
        linked_item_id: Optional[str] = None,
    ) -> ProgressEntry:
        """Log progress entry."""
        return await self.backend.log_progress(
            workspace_id=self.config.workspace_id,
            status=status,
            description=description,
            parent_id=parent_id,
            linked_item_type=linked_item_type,
            linked_item_id=linked_item_id,
        )

    async def get_progress(
        self,
        status_filter: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[ProgressEntry]:
        """Get progress entries."""
        return await self.backend.get_progress(
            workspace_id=self.config.workspace_id,
            status_filter=status_filter,
            limit=limit,
        )

    async def get_all_active_sessions(self) -> List[Dict]:
        """Get all active sessions for workspace (Serena F002)."""
        return await self.backend.get_all_active_sessions(self.config.workspace_id)

    async def get_custom_data(
        self, category: str, key: Optional[str] = None
    ) -> Any:
        """Get custom data from ConPort."""
        return await self.backend.get_custom_data(
            self.config.workspace_id, category, key
        )

    async def log_custom_data(self, category: str, key: str, value: Any) -> bool:
        """Log custom data to ConPort."""
        return await self.backend.log_custom_data(
            self.config.workspace_id, category, key, value
        )

    async def get_recent_decisions(self, limit: int = 5) -> List:
        """Get recent decisions (for ADHD context awareness)."""
        return await self.backend.get_recent_decisions(
            self.config.workspace_id, limit
        )

    async def health_check(self) -> Dict[str, Any]:
        """Check backend health."""
        return await self.backend.health_check()

    def get_backend_type(self) -> BackendType:
        """Get current backend type."""
        return self.backend.backend_type
