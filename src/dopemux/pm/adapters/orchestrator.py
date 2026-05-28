"""Task Orchestrator backend adapter for PM-plane workflow integration."""

import json
import logging
import os
from typing import Any, Dict, List, Optional
import httpx
from dopemux.orchestrator.idempotency import IdempotencyStore, IdempotencyState

logger = logging.getLogger(__name__)

class TaskOrchestratorAdapter:
    """Adapter for communicating with the task-orchestrator HTTP API."""

    def __init__(self, base_url: Optional[str] = None):
        # Active runtime authority is app.main on port 8000 in this checkout.
        self.base_url = (base_url or os.getenv("TASK_ORCHESTRATOR_URL", "http://localhost:8000")).rstrip("/")

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
        # Active runtime authority is app.main on port 8000 in this checkout.
        self.base_url = (base_url or os.getenv("TASK_ORCHESTRATOR_URL", "http://localhost:8000")).rstrip("/")
        self.default_project_id = default_project_id
        self.client = httpx.Client(timeout=10.0)
        self.idempotency_store = IdempotencyStore()

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        """Helper to make an HTTP request."""
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

        # 3-phase idempotency state machine transitions
        if idempotency_key:
            # We call the atomic, thread-safe claim_transition method.
            claim = self.idempotency_store.claim_transition(
                idempotency_key=idempotency_key,
                project_id=project_id,
                workflow_id=workflow_id,
                transition_name=transition_name
            )

            if claim["action"] == "COMPLETED":
                if claim["response_json"]:
                    return json.loads(claim["response_json"])
                return {"status": "success", "idempotency_cached": True}

        try:
            response = self._request("POST", f"/api/projects/{project_id}/workflow/transition", json=payload)
            response.raise_for_status()
            result = response.json()

            if idempotency_key:
                self.idempotency_store.update_status(
                    idempotency_key=idempotency_key,
                    status=IdempotencyState.COMPLETED,
                    response_json=json.dumps(result)
                )

            return result
        except Exception as e:
            if idempotency_key:
                try:
                    self.idempotency_store.update_status(
                        idempotency_key=idempotency_key,
                        status=IdempotencyState.INTENT
                    )
                except Exception as rollback_err:
                    logger.error(f"Failed to rollback idempotency status: {rollback_err}")
            logger.error(f"Failed to execute transition on task-orchestrator: {e}")
            raise

    def close(self):
        self.client.close()
