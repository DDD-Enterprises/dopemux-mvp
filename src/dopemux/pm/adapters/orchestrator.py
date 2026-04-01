"""Task Orchestrator backend adapter for PM-plane workflow integration."""

import logging
import os
from typing import Any, Dict, List, Optional
import httpx

logger = logging.getLogger(__name__)

class TaskOrchestratorAdapter:
    """Adapter for communicating with the task-orchestrator HTTP API."""

    def __init__(self, base_url: Optional[str] = None):
        # Default to PORT_BASE+14 (3014)
        self.base_url = (base_url or os.getenv("TASK_ORCHESTRATOR_URL", "http://localhost:3014")).rstrip("/")

    async def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        """Helper to make an HTTP request."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.request(method, f"{self.base_url}{path}", **kwargs)
            return response

    async def get_queue(self, project_id: str) -> Dict[str, Any]:
        """Get project priority queue."""
        try:
            response = await self._request("GET", f"/api/projects/{project_id}/workflow/queue")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get queue from task-orchestrator: {e}")
            raise

    async def get_blockers(self, project_id: str) -> Dict[str, Any]:
        """Get project blockers."""
        try:
            response = await self._request("GET", f"/api/projects/{project_id}/workflow/blockers")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get blockers from task-orchestrator: {e}")
            raise

    async def get_state(self, project_id: str) -> Dict[str, Any]:
        """Get project workflow state."""
        try:
            response = await self._request("GET", f"/api/projects/{project_id}/workflow/state")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get state from task-orchestrator: {e}")
            raise

    async def transition(self, project_id: str, workflow_id: str, transition_name: str) -> Dict[str, Any]:
        """Execute a workflow transition."""
        payload = {
            "workflow_id": workflow_id,
            "transition": transition_name
        }
        try:
            response = await self._request("POST", f"/api/projects/{project_id}/workflow/transition", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to execute transition on task-orchestrator: {e}")
            raise

    async def get_project_context(self, project_id: str) -> Dict[str, Any]:
        """Get project context from the orchestrator."""
        try:
            response = await self._request("GET", f"/api/projects/{project_id}/context")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get project context from task-orchestrator: {e}")
            raise

    async def get_sprint_snapshot(self, project_id: str) -> Dict[str, Any]:
        """Get sprint snapshot from the orchestrator."""
        try:
            response = await self._request("GET", f"/api/projects/{project_id}/sprint/snapshot")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get sprint snapshot from task-orchestrator: {e}")
            raise

    async def health(self) -> bool:
        """Check health of task-orchestrator."""
        try:
            response = await self._request("GET", "/health")
            return response.status_code == 200
        except Exception:
            return False


class SyncTaskOrchestratorAdapter:
    """Synchronous adapter for communicating with the task-orchestrator HTTP API."""

    def __init__(self, base_url: Optional[str] = None, default_project_id: Optional[str] = None):
        # Default to PORT_BASE+14 (3014)
        self.base_url = (base_url or os.getenv("TASK_ORCHESTRATOR_URL", "http://localhost:3014")).rstrip("/")
        self.default_project_id = default_project_id
        self.client = httpx.Client(timeout=10.0)

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        """Helper to make an HTTP request."""
        m = method.lower()
        if hasattr(self.client, m):
            response = getattr(self.client, m)(f"{self.base_url}{path}", **kwargs)
        else:
            response = self.client.request(method, f"{self.base_url}{path}", **kwargs)
        return response

    def transition(
        self, 
        project_id: str, 
        workflow_id: str, 
        transition_name: str,
        actor: str = "system",
        idempotency_key: Optional[str] = None,
        expected_version: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute a workflow transition."""
        payload = {
            "workflow_id": workflow_id,
            "transition": transition_name,
            "actor": actor,
            "idempotency_key": idempotency_key,
            "expected_version": expected_version,
            "reason": reason,
        }
        try:
            response = self._request("POST", f"/api/projects/{project_id}/workflow/transition", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to execute transition on task-orchestrator: {e}")
            raise

    def close(self):
        self.client.close()
