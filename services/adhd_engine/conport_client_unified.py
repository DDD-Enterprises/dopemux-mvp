"""
ADHD Engine ConPort Client - Stub Version for MVP

Stub ConPort client for ADHD Engine MVP.
ConPort integration disabled due to dependency complexity.
Returns empty/default data for all queries.

Future: Replace with full ConPort integration for pattern learning.
"""

import logging
from collections import defaultdict
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class ConPortSQLiteClient:
    """
    Stub ConPort client for ADHD Engine MVP.

    ConPort integration disabled for MVP due to dependency complexity.
    Returns empty/default data for all queries to enable ADHD Engine operation
    without PostgreSQL dependency.

    Future Enhancement: Full ConPort integration for:
    - Task completion tracking
    - Decision genealogy
    - Pattern learning persistence
    - ML training data
    """

    def __init__(
        self,
        db_path: str,
        workspace_id: str,
        read_only: bool = True,
    ):
        """
        Initialize stub ConPort client.

        Args:
            db_path: IGNORED (kept for API compatibility)
            workspace_id: Workspace identifier
            read_only: IGNORED
        """
        self.workspace_id = workspace_id
        self.read_only = read_only
        self._custom_data: Dict[str, Dict[str, Any]] = defaultdict(dict)
        logger.warning(f"ConPort stub client initialized (no persistence) for {workspace_id}")

    def get_progress(self, *args, **kwargs) -> List:
        """Stub: Return empty progress list"""
        return []

    def get_decisions(self, *args, **kwargs) -> List:
        """Stub: Return empty decisions list"""
        return []

    def write_custom_data(self, category: str, key: str, value: Any) -> bool:
        """Stub implementation that stores data in-memory."""
        self._custom_data[category][key] = value
        return True

    def get_custom_data(self, category: str = None, key: str = None) -> Dict:
        """Stub: Return stored data."""
        if category is None:
            return {}
        if key is None:
            return self._custom_data.get(category, {})
        return self._custom_data.get(category, {}).get(key)

    def get_progress_entries(
        self,
        limit: int = 20,
        status_filter: Optional[str] = None,
        hours_ago: int = 24,
    ) -> List[Dict[str, Any]]:
        """Stub: Return empty progress entries"""
        return []

    def get_recent_decisions(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Stub: Return empty decisions"""
        return []

    def log_progress_entry(
        self,
        status: str,
        description: str,
        parent_id: Optional[int] = None,
    ) -> Optional[int]:
        """Stub: Return fake ID"""
        return 1

    def _get_connection(self, write_mode: bool = False):
        """Compatibility method (no-op)"""
        return None

    def close(self):
        """Stub: Do nothing"""
        pass
