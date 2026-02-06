"""File-backed fallback adapter for ConPort client."""

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..backends import BackendType
from ..models import ActiveContext, Decision, ProgressEntry


class FileAdapter:
    """
    Lightweight JSON-backed ConPort adapter.

    This adapter is used as a universal fallback when network/database backends
    are unavailable.
    """

    backend_type = BackendType.FILE

    def __init__(self, config):
        self.config = config
        workspace_key = str(config.workspace_id).replace("/", "_").strip("_") or "default"
        default_path = Path.home() / ".dopemux" / "conport_fallback" / f"{workspace_key}.json"
        self.storage_path = Path(config.db_path) if config.db_path else default_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

    async def _load_store(self) -> Dict[str, Any]:
        def _read() -> Dict[str, Any]:
            if not self.storage_path.exists():
                return {
                    "counters": {"decision": 0, "progress": 0},
                    "decisions": {},
                    "progress": {},
                    "contexts": {},
                    "custom_data": {},
                }
            return json.loads(self.storage_path.read_text(encoding="utf-8"))

        return await asyncio.to_thread(_read)

    async def _save_store(self, payload: Dict[str, Any]) -> None:
        def _write() -> None:
            self.storage_path.write_text(
                json.dumps(payload, indent=2, sort_keys=True),
                encoding="utf-8",
            )

        await asyncio.to_thread(_write)

    async def log_decision(
        self,
        workspace_id: str,
        summary: str,
        rationale: Optional[str] = None,
        implementation_details: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Decision:
        store = await self._load_store()
        store["counters"]["decision"] += 1
        item_id = store["counters"]["decision"]

        entry = {
            "id": item_id,
            "summary": summary,
            "rationale": rationale,
            "implementation_details": implementation_details,
            "tags": tags or [],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        store["decisions"].setdefault(workspace_id, []).append(entry)
        await self._save_store(store)
        return Decision(**entry)

    async def get_decisions(
        self,
        workspace_id: str,
        limit: Optional[int] = None,
        tags: Optional[List[str]] = None,
    ) -> List[Decision]:
        store = await self._load_store()
        decisions = list(store["decisions"].get(workspace_id, []))
        if tags:
            tag_set = set(tags)
            decisions = [d for d in decisions if tag_set.intersection(set(d.get("tags", [])))]
        decisions.sort(key=lambda d: d.get("timestamp", ""), reverse=True)
        if limit:
            decisions = decisions[:limit]
        return [Decision(**item) for item in decisions]

    async def get_recent_decisions(self, workspace_id: str, limit: int = 5) -> List[Decision]:
        return await self.get_decisions(workspace_id, limit=limit)

    async def get_active_context(
        self,
        workspace_id: str,
        session_id: str = "default",
    ) -> ActiveContext:
        store = await self._load_store()
        contexts = store["contexts"].get(workspace_id, {})
        payload = contexts.get(session_id)
        if not payload:
            return ActiveContext(workspace_id=workspace_id, session_id=session_id, content={})
        return ActiveContext(**payload)

    async def update_active_context(
        self,
        workspace_id: str,
        session_id: str,
        content: Dict[str, Any],
    ) -> None:
        store = await self._load_store()
        store["contexts"].setdefault(workspace_id, {})[session_id] = {
            "workspace_id": workspace_id,
            "session_id": session_id,
            "content": content,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        await self._save_store(store)

    async def get_all_active_sessions(self, workspace_id: str) -> List[Dict[str, Any]]:
        store = await self._load_store()
        contexts = store["contexts"].get(workspace_id, {})
        sessions = []
        for session_id, data in contexts.items():
            sessions.append(
                {
                    "session_id": session_id,
                    "worktree_path": workspace_id,
                    "branch": None,
                    "focus": data.get("content", {}),
                    "status": "active",
                    "updated_at": data.get("updated_at"),
                }
            )
        return sessions

    async def log_progress(
        self,
        workspace_id: str,
        status: str,
        description: str,
        parent_id: Optional[int] = None,
        linked_item_type: Optional[str] = None,
        linked_item_id: Optional[str] = None,
    ) -> ProgressEntry:
        store = await self._load_store()
        store["counters"]["progress"] += 1
        item_id = store["counters"]["progress"]

        entry = {
            "id": item_id,
            "status": status,
            "description": description,
            "parent_id": parent_id,
            "linked_item_type": linked_item_type,
            "linked_item_id": linked_item_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        store["progress"].setdefault(workspace_id, []).append(entry)
        await self._save_store(store)
        return ProgressEntry(**entry)

    async def get_progress(
        self,
        workspace_id: str,
        status_filter: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[ProgressEntry]:
        store = await self._load_store()
        progress = list(store["progress"].get(workspace_id, []))
        if status_filter:
            progress = [p for p in progress if p.get("status") == status_filter]
        progress.sort(key=lambda item: item.get("timestamp", ""), reverse=True)
        if limit:
            progress = progress[:limit]
        return [ProgressEntry(**item) for item in progress]

    async def get_custom_data(
        self,
        workspace_id: str,
        category: str,
        key: Optional[str] = None,
    ) -> Any:
        store = await self._load_store()
        category_data = store["custom_data"].setdefault(workspace_id, {}).setdefault(category, {})
        if key is None:
            return dict(category_data)
        return category_data.get(key)

    async def log_custom_data(
        self,
        workspace_id: str,
        category: str,
        key: str,
        value: Any,
    ) -> bool:
        store = await self._load_store()
        store["custom_data"].setdefault(workspace_id, {}).setdefault(category, {})[key] = value
        await self._save_store(store)
        return True

    async def health_check(self) -> Dict[str, Any]:
        return {
            "status": "ok",
            "backend": self.backend_type.value,
            "storage_path": str(self.storage_path),
        }
