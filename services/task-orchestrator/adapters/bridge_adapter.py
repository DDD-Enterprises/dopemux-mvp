"""
Task Orchestrator DopeconBridge Adapter

Replaces direct ConPort HTTP calls with DopeconBridge client usage.
Implements the ConPortEventAdapter interface using the bridge as backend.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add shared and parent modules to path
SHARED_DIR = Path(__file__).parent.parent / "shared"
PARENT_DIR = Path(__file__).parent
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

from dopecon_bridge_client import (
    AsyncDopeconBridgeClient,
    DopeconBridgeConfig,
)

# Import orchestrator types
try:
    from enhanced_orchestrator import OrchestrationTask, TaskStatus, AgentType
except ImportError:
    # Fallback for when run from different context
    OrchestrationTask = None
    TaskStatus = None
    AgentType = None

logger = logging.getLogger(__name__)


class TaskOrchestratorBridgeAdapter:
    """
    DopeconBridge adapter for Task Orchestrator.
    
    Provides the same interface as ConPortEventAdapter but uses
    DopeconBridge for all ConPort interactions.
    """

    def __init__(
        self,
        workspace_id: str,
        base_url: str = None,
        token: str = None,
        requester: str = "task-orchestrator",
    ):
        """
        Initialize adapter with DopeconBridge client.

        Args:
            workspace_id: Workspace identifier
            base_url: DopeconBridge URL (defaults from env)
            token: Optional auth token (defaults from env)
            requester: Service name for cross-plane routing
        """
        self.workspace_id = workspace_id
        self.requester = requester
        
        config = DopeconBridgeConfig.from_env()
        if base_url:
            config = DopeconBridgeConfig(
                base_url=base_url,
                token=token or config.token,
                source_plane="cognitive_plane",
            )
        
        self.client = AsyncDopeconBridgeClient(config=config)
        logger.info(
            f"✅ Task Orchestrator DopeconBridge adapter initialized "
            f"(workspace: {workspace_id}, requester: {requester})"
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def close(self):
        """Close the underlying bridge client."""
        await self.client.aclose()

    def _encode_energy_tag(self, energy: str) -> str:
        """Encode energy level as tag."""
        return f"energy-{energy.lower()}"

    def _encode_complexity_tag(self, complexity: float) -> str:
        """Encode complexity score (0.0-1.0) as tag (0-10)."""
        complexity_int = int(complexity * 10)
        complexity_int = max(0, min(10, complexity_int))
        return f"complexity-{complexity_int}"

    def _encode_priority_tag(self, priority: int) -> str:
        """Encode priority (1-5) as tag."""
        priority = max(1, min(5, priority))
        return f"priority-{priority}"

    async def push_task_to_conport(
        self,
        task: "OrchestrationTask",
    ) -> Dict[str, Any]:
        """
        Push orchestration task to ConPort via DopeconBridge.
        
        Creates a progress entry with ADHD metadata preserved as tags.
        
        Args:
            task: OrchestrationTask to push
            
        Returns:
            Result dict with ConPort progress entry ID
        """
        if not task:
            return {"success": False, "error": "No task provided"}

        try:
            # Prepare tags with ADHD metadata
            tags = []
            if hasattr(task, 'energy_level') and task.energy_level:
                tags.append(self._encode_energy_tag(task.energy_level))
            if hasattr(task, 'complexity') and task.complexity is not None:
                tags.append(self._encode_complexity_tag(task.complexity))
            if hasattr(task, 'priority') and task.priority:
                tags.append(self._encode_priority_tag(task.priority))
            if hasattr(task, 'agent_type') and task.agent_type:
                tags.append(f"agent-{task.agent_type.value if hasattr(task.agent_type, 'value') else str(task.agent_type)}")
            
            # Prepare metadata
            metadata = {
                "orchestrator_task_id": task.task_id,
                "orchestrator_source": "task-orchestrator",
            }
            if hasattr(task, 'estimated_duration'):
                metadata["estimated_duration"] = task.estimated_duration
            if hasattr(task, 'dependencies'):
                metadata["dependencies"] = task.dependencies or []

            # Create progress entry via bridge
            result = await self.client.create_progress_entry(
                description=task.description,
                status=task.status.value if hasattr(task.status, 'value') else str(task.status),
                metadata=metadata,
                workspace_id=self.workspace_id,
            )

            # Publish event
            await self.client.publish_event(
                event_type="orchestrator.task.synced",
                data={
                    "task_id": task.task_id,
                    "conport_entry_id": result.get("id"),
                    "status": str(task.status),
                },
                source=self.requester,
            )

            return {
                "success": True,
                "conport_entry_id": result.get("id"),
                "task_id": task.task_id,
            }

        except Exception as e:
            logger.error(f"Failed to push task to ConPort via bridge: {e}")
            return {"success": False, "error": str(e)}

    async def get_progress_entries(
        self,
        limit: int = 50,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get progress entries from ConPort via DopeconBridge.
        
        Args:
            limit: Maximum number of entries to return
            status: Optional status filter
            
        Returns:
            List of progress entry dicts
        """
        try:
            entries = await self.client.get_progress_entries(
                workspace_id=self.workspace_id,
                limit=limit,
                status=status,
            )
            return entries
        except Exception as e:
            logger.error(f"Failed to get progress entries via bridge: {e}")
            return []

    async def route_to_pm_plane(
        self,
        operation: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Route an operation to the PM plane via DopeconBridge.
        
        Args:
            operation: PM plane operation name
            data: Operation data
            
        Returns:
            Response from PM plane
        """
        try:
            response = await self.client.route_pm(
                operation=operation,
                data=data,
                requester=self.requester,
            )
            
            return {
                "success": response.success,
                "data": dict(response.data) if response.data else {},
                "error": response.error,
            }
        except Exception as e:
            logger.error(f"Failed to route to PM plane: {e}")
            return {"success": False, "error": str(e)}

    async def publish_orchestration_event(
        self,
        event_type: str,
        data: Dict[str, Any],
    ) -> bool:
        """
        Publish an orchestration event via DopeconBridge.
        
        Args:
            event_type: Event type identifier
            data: Event data
            
        Returns:
            True if successful
        """
        try:
            await self.client.publish_event(
                event_type=f"orchestrator.{event_type}",
                data=data,
                source=self.requester,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to publish orchestration event: {e}")
            return False
