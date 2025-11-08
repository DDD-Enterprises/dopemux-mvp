"""ConPort bridge adapter stubs for local ADHD engine tests."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .conport_client_unified import ConPortSQLiteClient


class ConPortBridgeAdapter:
    """Lightweight adapter that proxies to the SQLite stub client."""

    def __init__(self, workspace_id: str, db_path: Optional[str] = None) -> None:
        self.workspace_id = workspace_id
        self._client = ConPortSQLiteClient(
            db_path=db_path or f"{workspace_id}/context_portal/context.db",
            workspace_id=workspace_id,
            read_only=False,
        )

    def get_custom_data(self, category: Optional[str] = None, key: Optional[str] = None) -> Dict[str, Any]:
        return self._client.get_custom_data(category=category, key=key)

    def write_custom_data(self, category: str, key: str, value: Any) -> None:
        self._client.write_custom_data(category, key, value)

    def log_progress_entry(self, status: str, description: str, parent_id: Optional[int] = None) -> Optional[int]:
        return self._client.log_progress_entry(status=status, description=description, parent_id=parent_id)

    def get_progress_entries(self, limit: int = 20, status_filter: Optional[str] = None, hours_ago: int = 24) -> List[Dict[str, Any]]:
        return self._client.get_progress_entries(limit=limit, status_filter=status_filter, hours_ago=hours_ago)

    def close(self) -> None:
        self._client.close()
