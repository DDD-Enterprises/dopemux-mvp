"""DopeconBridge adapter used by ADHD Engine services."""

from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, List

from services.shared.dopecon_bridge_client import (
    DopeconBridgeClient,
    DopeconBridgeConfig,
    DopeconBridgeError,
)

from .config import settings
from .conport_client_unified import ConPortSQLiteClient

logger = logging.getLogger(__name__)


class ConPortBridgeAdapter:
    """Facade that routes persistence through the DopeconBridge."""

    PROGRESS_CATEGORY = "adhd_progress_entries"

    def __init__(
        self,
        workspace_id: str,
        *,
        base_url: Optional[str] = None,
        token: Optional[str] = None,
        source_plane: Optional[str] = None,
    ) -> None:
        self.workspace_id = workspace_id
        self._client: Optional[DopeconBridgeClient] = None
        self._fallback = ConPortSQLiteClient(
            db_path=f"{workspace_id}/context_portal/context.db",
            workspace_id=workspace_id,
            read_only=False,
        )

        try:
            cfg = DopeconBridgeConfig(
                base_url=base_url or settings.dopecon_bridge_url,
                token=token or settings.dopecon_bridge_token,
                source_plane=source_plane or settings.dopecon_bridge_source_plane,
            )
            self._client = DopeconBridgeClient(cfg)
            logger.info(
                "DopeconBridge adapter ready (%s)", cfg.base_url
            )
        except Exception as exc:  # pragma: no cover - network/env specific
            logger.warning(
                "DopeconBridge unavailable (%s); using local stub", exc
            )
            self._client = None

    # ------------------------------------------------------------------
    # Custom data helpers
    # ------------------------------------------------------------------

    def get_custom_data(self, category: str, key: Optional[str] = None, limit: int = 50):
        if not self._client:
            return self._fallback.get_custom_data(category=category, key=key)

        try:
            records = self._client.get_custom_data(
                workspace_id=self.workspace_id,
                category=category,
                key=key,
                limit=limit,
            )
            if key:
                for record in records:
                    if record.get("key") == key:
                        return record.get("value")
                return None
            return {record.get("key"): record.get("value") for record in records}
        except DopeconBridgeError as exc:
            logger.error("Failed to fetch custom data from bridge: %s", exc)
            return {}

    def write_custom_data(self, category: str, key: str, value: Any) -> bool:
        if not self._client:
            return self._fallback.write_custom_data(category=category, key=key, value=value)

        try:
            return self._client.save_custom_data(
                workspace_id=self.workspace_id,
                category=category,
                key=key,
                value=value,
            )
        except DopeconBridgeError as exc:
            logger.error("Failed to save custom data via bridge: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Progress helpers
    # ------------------------------------------------------------------

    def get_progress_entries(
        self,
        limit: int = 20,
        status_filter: Optional[str] = None,
        hours_ago: int = 24,
    ) -> List[Dict[str, Any]]:
        records = self.get_custom_data(self.PROGRESS_CATEGORY) or {}
        entries: List[Dict[str, Any]] = list(records.values()) if isinstance(records, dict) else []

        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
        filtered = []
        for entry in entries:
            ts = self._parse_timestamp(entry.get("timestamp"))
            if ts and ts < cutoff:
                continue
            if status_filter and entry.get("status") != status_filter:
                continue
            filtered.append(entry)

        filtered.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
        return filtered[:limit]

    def log_progress_entry(
        self,
        *,
        status: str,
        description: str,
        parent_id: Optional[int] = None,
    ) -> Optional[str]:
        entry_id = str(uuid.uuid4())
        entry = {
            "id": entry_id,
            "status": status,
            "description": description,
            "parent_id": parent_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if not self.write_custom_data(self.PROGRESS_CATEGORY, entry_id, entry):
            return None

        # Emit event for downstream consumers (best-effort)
        if self._client:
            try:
                self._client.publish_event(
                    event_type="adhd.progress.entry",
                    data={"entry_id": entry_id, **entry},
                    stream="dopemux:events",
                    source="adhd-engine",
                )
            except DopeconBridgeError as exc:
                logger.debug("Progress entry event failed (non-blocking): %s", exc)

        return entry_id

    # ------------------------------------------------------------------

    def close(self) -> None:
        if self._client:
            self._client.close()

    @staticmethod
    def _parse_timestamp(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None

