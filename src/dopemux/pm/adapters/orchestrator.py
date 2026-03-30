"""Task Orchestrator backend adapters for PM-plane workflow integration."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


class _BaseTaskOrchestratorAdapter:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or os.getenv("TASK_ORCHESTRATOR_URL", "http://localhost:3014")).rstrip("/")

    @staticmethod
    def _transition_payload(
        workflow_id: str,
        transition_name: str,
        *,
        actor: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        expected_version: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "workflow_id": workflow_id,
            "transition": transition_name,
        }
        if actor is not None:
            payload["actor"] = actor
        if idempotency_key is not None:
            payload["idempotency_key"] = idempotency_key
        if expected_version is not None:
            payload["expected_version"] = expected_version
        if reason is not None:
            payload["reason"] = reason
        return payload


class TaskOrchestratorAdapter(_BaseTaskOrchestratorAdapter):
    """Async adapter for communicating with the task-orchestrator HTTP API."""

    async def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        async with httpx.AsyncClient(timeout=10.0) as client:
            return await client.request(method, f"{self.base_url}{path}", **kwargs)

    async def get_queue(self, project_id: str) -> Dict[str, Any]:
        try:
            response = await self._request("GET", f"/api/projects/{project_id}/workflow/queue")
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            logger.error("Failed to get queue from task-orchestrator: %s", exc)
            raise

    async def get_blockers(self, project_id: str) -> Dict[str, Any]:
        try:
            response = await self._request("GET", f"/api/projects/{project_id}/workflow/blockers")
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            logger.error("Failed to get blockers from task-orchestrator: %s", exc)
            raise

    async def get_state(self, project_id: str) -> Dict[str, Any]:
        try:
            response = await self._request("GET", f"/api/projects/{project_id}/workflow/state")
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            logger.error("Failed to get state from task-orchestrator: %s", exc)
            raise

    async def transition(
        self,
        project_id: str,
        workflow_id: str,
        transition_name: str,
        *,
        actor: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        expected_version: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = self._transition_payload(
            workflow_id,
            transition_name,
            actor=actor,
            idempotency_key=idempotency_key,
            expected_version=expected_version,
            reason=reason,
        )
        try:
            response = await self._request("POST", f"/api/projects/{project_id}/workflow/transition", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            logger.error("Failed to execute transition on task-orchestrator: %s", exc)
            raise

    async def health(self) -> bool:
        try:
            response = await self._request("GET", "/health")
            return response.status_code == 200
        except Exception:
            return False


class SyncTaskOrchestratorAdapter(_BaseTaskOrchestratorAdapter):
    """Synchronous adapter for PM write callers that need direct HTTP transitions."""

    def __init__(self, base_url: Optional[str] = None, *, default_project_id: str = "default"):
        super().__init__(base_url)
        self.default_project_id = default_project_id
        self._client = httpx.Client(timeout=10.0)

    def close(self) -> None:
        self._client.close()

    def transition(
        self,
        *,
        project_id: Optional[str] = None,
        workflow_id: str,
        transition_name: str,
        actor: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        expected_version: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = self._transition_payload(
            workflow_id,
            transition_name,
            actor=actor,
            idempotency_key=idempotency_key,
            expected_version=expected_version,
            reason=reason,
        )
        resolved_project_id = project_id or self.default_project_id
        try:
            response = self._client.post(
                f"{self.base_url}/api/projects/{resolved_project_id}/workflow/transition",
                json=payload,
            )
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            logger.error("Failed to execute sync transition on task-orchestrator: %s", exc)
            raise
