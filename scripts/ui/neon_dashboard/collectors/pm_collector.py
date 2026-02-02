"""Collectors that power the planning / PM mode."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List

from .base_collector import BaseCollector
from ..config.settings import PMModeSettings


import logging

logger = logging.getLogger(__name__)


class PMCollector(BaseCollector):
    """Pulls sprint + task data from Leantime and ConPort."""
    def __init__(self, settings: PMModeSettings):
        super().__init__(cache_ttl=15.0, timeout=3.0)
        self.settings = settings

    async def fetch(self) -> Dict[str, Any]:
        epics, sprint_meta = await asyncio.gather(
            self.fetch_leantime_epics(),
            self.fetch_conport_sprint(),
            return_exceptions=True,
        )
        return {
            "epics": self._normalize_epics(epics),
            "sprint": sprint_meta if isinstance(sprint_meta, dict) else self._fallback_sprint(),
        }

    async def fetch_leantime_epics(self) -> Any:
        url = f"{self.settings.leantime_url.rstrip('/')}/api/epics"
        payload = await self._http_json(url)
        if not payload:
            return self._fallback_epics()
        return payload

    async def fetch_conport_sprint(self) -> Dict[str, Any]:
        url = f"{self.settings.conport_url.rstrip('/')}/api/sprint"
        payload = await self._http_json(url)
        if not payload:
            return self._fallback_sprint()
        return payload

    def _normalize_epics(self, payload: Any) -> List[Dict[str, Any]]:
        if isinstance(payload, Exception) or payload is None:
            payload = self._fallback_epics()
        epics: List[Dict[str, Any]] = []
        for raw_epic in payload:
            epic_tasks = []
            for task in raw_epic.get("tasks", []):
                subtasks = task.get("subtasks") or []
                epic_tasks.append(
                    {
                        "id": task.get("id"),
                        "name": task.get("name"),
                        "status": (task.get("status") or "TODO").upper(),
                        "estimate": task.get("estimate") or 0,
                        "spent": task.get("spent") or 0,
                        "subtasks": [
                            {
                                "id": sub.get("id"),
                                "name": sub.get("name"),
                                "status": (sub.get("status") or "TODO").upper(),
                            }
                            for sub in subtasks
                        ],
                    }
                )
            epics.append(
                {
                    "id": raw_epic.get("id"),
                    "name": raw_epic.get("name"),
                    "completion": int(raw_epic.get("completion", 0)),
                    "tasks": epic_tasks,
                }
            )
        return epics

    @staticmethod
    def _fallback_epics() -> List[Dict[str, Any]]:
        return [
            {
                "id": "epic-dash",
                "name": "Dope Layout",
                "completion": 65,
                "tasks": [
                    {
                        "id": "task-pane",
                        "name": "Code panes",
                        "status": "IN_PROGRESS",
                        "estimate": 4,
                        "spent": 2.5,
                        "subtasks": [
                            {"id": "sub-textual", "name": "Textual integration", "status": "DONE"},
                            {"id": "sub-rich", "name": "Rich renderables", "status": "IN_PROGRESS"},
                        ],
                    },
                    {
                        "id": "task-testing",
                        "name": "Integration testing",
                        "status": "TODO",
                        "estimate": 2,
                        "spent": 0,
                        "subtasks": [],
                    },
                ],
            }
        ]

    @staticmethod
    def _fallback_sprint() -> Dict[str, Any]:
        return {
            "name": "Q1 2025 Sprint",
            "progress": 65,
            "overdue_tasks": 2,
            "active_tasks": 3,
            "blocked_tasks": 0,
            "completed_tasks": 8,
            "estimate_hours": 40,
            "spent_hours": 26,
            "today_focus": "Code panes",
        }

