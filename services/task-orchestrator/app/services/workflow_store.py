"""Persistence layer for Stage-1/Stage-2 workflow entities."""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

# Ensure repo-root imports work in isolated service runtime.
def _find_repo_root():
    curr = Path(__file__).resolve().parent
    while curr.parent != curr:
        if (curr / "services").exists() and (curr / "src").exists():
            return curr
        curr = curr.parent
    # Fallback to a reasonable default if markers not found
    try:
        return Path(__file__).resolve().parents[4]
    except IndexError:
        return Path(__file__).resolve().parents[2]

REPO_ROOT = _find_repo_root()
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.shared.dopecon_bridge_client import (  # type: ignore
    AsyncDopeconBridgeClient,
    DopeconBridgeConfig,
    DopeconBridgeError,
)

logger = logging.getLogger(__name__)


class WorkflowStoreError(RuntimeError):
    """Raised for workflow persistence failures."""


class WorkflowStore:
    """Read/write workflow ideas and epics via DopeconBridge custom_data."""

    IDEAS_CATEGORY = "workflow_ideas"
    EPICS_CATEGORY = "workflow_epics"

    def __init__(
        self,
        workspace_id: str,
        *,
        bridge_url: Optional[str] = None,
        bridge_token: Optional[str] = None,
        source_plane: Optional[str] = None,
        timeout: float = 10.0,
    ) -> None:
        self.workspace_id = workspace_id
        self._client = AsyncDopeconBridgeClient(
            config=DopeconBridgeConfig(
                base_url=bridge_url or os.getenv("DOPECON_BRIDGE_URL", "http://localhost:3016"),
                token=bridge_token if bridge_token is not None else os.getenv("DOPECON_BRIDGE_TOKEN"),
                timeout=timeout,
                source_plane=source_plane or os.getenv("DOPECON_BRIDGE_SOURCE_PLANE", "cognitive_plane"),
            )
        )

    async def close(self) -> None:
        """Close underlying async client."""
        await self._client.aclose()

    async def upsert_custom_data(
        self,
        *,
        category: str,
        key: str,
        value: Mapping[str, Any],
    ) -> bool:
        """Upsert custom_data entry through DopeconBridge."""
        try:
            return await self._client.save_custom_data(
                workspace_id=self.workspace_id,
                category=category,
                key=key,
                value=value,
            )
        except DopeconBridgeError as exc:
            raise WorkflowStoreError(str(exc)) from exc
        except Exception as exc:
            raise WorkflowStoreError(f"Failed to upsert custom_data {category}/{key}: {exc}") from exc

    async def get_custom_data(
        self,
        *,
        category: str,
        key: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get raw custom_data entries from DopeconBridge."""
        try:
            items = await self._client.get_custom_data(
                workspace_id=self.workspace_id,
                category=category,
                key=key,
                limit=limit,
            )
            return [self._normalize_entry(item) for item in items]
        except DopeconBridgeError as exc:
            raise WorkflowStoreError(str(exc)) from exc
        except Exception as exc:
            raise WorkflowStoreError(f"Failed to fetch custom_data {category}: {exc}") from exc

    async def save_idea(self, idea: Mapping[str, Any]) -> bool:
        idea_id = str(idea.get("id", ""))
        if not idea_id:
            raise WorkflowStoreError("idea id is required")
        return await self.upsert_custom_data(
            category=self.IDEAS_CATEGORY,
            key=idea_id,
            value=idea,
        )

    async def save_epic(self, epic: Mapping[str, Any]) -> bool:
        epic_id = str(epic.get("id", ""))
        if not epic_id:
            raise WorkflowStoreError("epic id is required")
        return await self.upsert_custom_data(
            category=self.EPICS_CATEGORY,
            key=epic_id,
            value=epic,
        )

    async def get_idea(self, idea_id: str) -> Optional[Dict[str, Any]]:
        rows = await self.get_custom_data(
            category=self.IDEAS_CATEGORY,
            key=idea_id,
            limit=1,
        )
        if not rows:
            return None
        return self._payload_from_row(rows[0], fallback_id=idea_id)

    async def get_epic(self, epic_id: str) -> Optional[Dict[str, Any]]:
        rows = await self.get_custom_data(
            category=self.EPICS_CATEGORY,
            key=epic_id,
            limit=1,
        )
        if not rows:
            return None
        return self._payload_from_row(rows[0], fallback_id=epic_id)

    async def list_ideas(
        self,
        *,
        status: Optional[str] = None,
        tag: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        rows = await self.get_custom_data(
            category=self.IDEAS_CATEGORY,
            limit=max(limit, 1),
        )
        ideas = [
            self._payload_from_row(row)
            for row in rows
        ]
        filtered = [item for item in ideas if item]
        if status:
            filtered = [item for item in filtered if item.get("status") == status]
        if tag:
            filtered = [item for item in filtered if tag in (item.get("tags") or [])]
        filtered.sort(key=lambda item: str(item.get("created_at", "")), reverse=True)
        return filtered[:limit]

    async def list_epics(
        self,
        *,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        tag: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        rows = await self.get_custom_data(
            category=self.EPICS_CATEGORY,
            limit=max(limit, 1),
        )
        epics = [self._payload_from_row(row) for row in rows]
        filtered = [item for item in epics if item]
        if status:
            filtered = [item for item in filtered if item.get("status") == status]
        if priority:
            filtered = [item for item in filtered if item.get("priority") == priority]
        if tag:
            filtered = [item for item in filtered if tag in (item.get("tags") or [])]
        filtered.sort(key=lambda item: str(item.get("created_at", "")), reverse=True)
        return filtered[:limit]

    @staticmethod
    def _normalize_entry(entry: Mapping[str, Any]) -> Dict[str, Any]:
        """Convert generic mapping to plain dict with safe value payload."""
        item = dict(entry)
        value = item.get("value")
        if isinstance(value, str):
            try:
                item["value"] = json.loads(value)
            except json.JSONDecodeError:
                logger.warning("custom_data value was non-JSON string")
                item["value"] = {}
        elif value is None:
            item["value"] = {}
        return item

    @staticmethod
    def _payload_from_row(row: Mapping[str, Any], fallback_id: Optional[str] = None) -> Dict[str, Any]:
        payload = dict(row.get("value") or {})
        if "id" not in payload:
            payload["id"] = row.get("key") or fallback_id
        if "updated_at" not in payload and row.get("timestamp"):
            payload["updated_at"] = row.get("timestamp")
        return payload

