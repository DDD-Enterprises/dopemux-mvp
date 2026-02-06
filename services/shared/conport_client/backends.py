"""
Backend adapters for ConPort client.
"""

import logging

from enum import Enum
from typing import Protocol, List, Optional, Dict, Any
from .models import Decision, ProgressEntry, ActiveContext


logger = logging.getLogger(__name__)

class BackendType(Enum):
    """Available backend types."""

    POSTGRESQL_AGE = "postgresql_age"
    SQLITE = "sqlite"
    MCP_RPC = "mcp"
    FILE = "file"


class ConPortBackend(Protocol):
    """Protocol for ConPort backend adapters."""

    backend_type: BackendType

    async def log_decision(
        self, workspace_id: str, summary: str, rationale: str = None,
        implementation_details: str = None, tags: List[str] = None
    ) -> Decision: ...

    async def get_decisions(
        self, workspace_id: str, limit: int = None, tags: List[str] = None
    ) -> List[Decision]: ...

    async def get_active_context(
        self, workspace_id: str, session_id: str = "default"
    ) -> ActiveContext: ...

    async def update_active_context(
        self, workspace_id: str, session_id: str, content: Dict[str, Any]
    ) -> None: ...

    async def log_progress(
        self, workspace_id: str, status: str, description: str,
        parent_id: int = None, linked_item_type: str = None, linked_item_id: str = None
    ) -> ProgressEntry: ...

    async def get_progress(
        self, workspace_id: str, status_filter: str = None, limit: int = None
    ) -> List[ProgressEntry]: ...

    async def health_check(self) -> Dict[str, Any]: ...


def get_backend_adapter(config) -> ConPortBackend:
    """
    Get appropriate backend adapter based on config.

    Auto-detects best available backend if not specified.
    """
    # If backend specified, use it
    if config.backend:
        if config.backend == BackendType.POSTGRESQL_AGE:
            from .adapters.postgresql_adapter import PostgreSQLAGEAdapter
            return PostgreSQLAGEAdapter(config)
        elif config.backend == BackendType.SQLITE:
            from .adapters.sqlite_adapter import SQLiteAdapter
            return SQLiteAdapter(config)
        # Add other backends as needed

    # Auto-detect: Try PostgreSQL AGE first (production default)
    try:
        from .adapters.postgresql_adapter import PostgreSQLAGEAdapter
        adapter = PostgreSQLAGEAdapter(config)
        # Connection is validated lazily on first async call.
        return adapter
    except Exception as e:
        logger.warning("PostgreSQL adapter unavailable, falling back to file backend: %s", e)
    # Fallback to file-based (always works)
    from .adapters.file_adapter import FileAdapter
    return FileAdapter(config)
