"""
GPT-Researcher DopeconBridge Adapter

Replaces ConPort MCP discrete integration with DopeconBridge client usage.
Provides the same adapter interface for research task persistence.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import sys
import os

# Add shared modules to path
SHARED_DIR = Path(__file__).parent.parent.parent.parent / "shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from dopecon_bridge_client import (
    AsyncDopeconBridgeClient,
    DopeconBridgeConfig,
)

logger = logging.getLogger(__name__)


class ResearchBridgeAdapter:
    """
    DopeconBridge adapter for GPT-Researcher.
    
    Provides ADHD-optimized features:
    - Automatic state persistence via bridge
    - Research session recovery
    - Integration with decision history
    - Progress tracking
    """

    def __init__(self, workspace_id: str):
        """
        Initialize research bridge adapter.
        
        Args:
            workspace_id: Workspace path
        """
        self.workspace_id = workspace_id
        
        # Initialize DopeconBridge client
        config = DopeconBridgeConfig.from_env()
        self.client = AsyncDopeconBridgeClient(config=config)
        
        logger.info(
            f"✅ Research DopeconBridge adapter initialized "
            f"(workspace: {workspace_id})"
        )

    async def close(self):
        """Close the bridge client."""
        await self.client.aclose()

    async def save_research_state(
        self,
        task_id: str,
        state_data: Dict[str, Any],
    ) -> bool:
        """
        Save research task state via DopeconBridge.
        
        Args:
            task_id: Research task identifier
            state_data: Task state to save
            
        Returns:
            True if successful
        """
        try:
            success = await self.client.save_custom_data(
                workspace_id=self.workspace_id,
                category="research_tasks",
                key=task_id,
                value=state_data,
            )
            
            if success:
                # Publish event for state save
                await self.client.publish_event(
                    event_type="research.state.saved",
                    data={
                        "task_id": task_id,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                    source="gpt-researcher",
                )
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to save research state via bridge: {e}")
            return False

    async def get_research_state(
        self,
        task_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get research task state via DopeconBridge.
        
        Args:
            task_id: Research task identifier
            
        Returns:
            Task state or None
        """
        try:
            results = await self.client.get_custom_data(
                workspace_id=self.workspace_id,
                category="research_tasks",
                key=task_id,
                limit=1,
            )
            
            if results:
                return results[0].get("value", {})
            return None
            
        except Exception as e:
            logger.error(f"Failed to get research state via bridge: {e}")
            return None

    async def log_research_progress(
        self,
        task_id: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Log research progress via DopeconBridge.
        
        Args:
            task_id: Research task identifier
            description: Progress description
            metadata: Optional metadata
            
        Returns:
            True if successful
        """
        try:
            result = await self.client.create_progress_entry(
                description=f"Research: {description}",
                status="IN_PROGRESS",
                metadata={
                    "research_task_id": task_id,
                    "source": "gpt-researcher",
                    **(metadata or {}),
                },
                workspace_id=self.workspace_id,
            )
            
            # Publish event
            await self.client.publish_event(
                event_type="research.progress.logged",
                data={
                    "task_id": task_id,
                    "description": description,
                    "progress_id": result.get("id"),
                },
                source="gpt-researcher",
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to log research progress via bridge: {e}")
            return False

    async def create_research_decision(
        self,
        task_id: str,
        summary: str,
        findings: str,
        sources: List[str],
    ) -> Optional[str]:
        """
        Create a decision record for research findings via DopeconBridge.
        
        Args:
            task_id: Research task identifier
            summary: Research summary
            findings: Detailed findings
            sources: Source URLs
            
        Returns:
            Decision ID or None
        """
        try:
            result = await self.client.create_decision(
                summary=summary,
                rationale=f"Research findings for task {task_id}",
                implementation_details=json.dumps({
                    "findings": findings,
                    "sources": sources,
                    "research_task_id": task_id,
                }, indent=2),
                tags=["research", "gpt-researcher", "automated"],
                workspace_id=self.workspace_id,
            )
            
            decision_id = result.get("id")
            
            if decision_id:
                # Publish event
                await self.client.publish_event(
                    event_type="research.decision.created",
                    data={
                        "task_id": task_id,
                        "decision_id": decision_id,
                        "source_count": len(sources),
                    },
                    source="gpt-researcher",
                )
            
            return decision_id
            
        except Exception as e:
            logger.error(f"Failed to create research decision via bridge: {e}")
            return None

    async def link_to_project(
        self,
        research_task_id: str,
        project_id: str,
    ) -> bool:
        """
        Link research task to project via DopeconBridge.
        
        Args:
            research_task_id: Research task ID
            project_id: Project ID
            
        Returns:
            True if successful
        """
        try:
            await self.client.create_link(
                source_item_type="research_task",
                source_item_id=research_task_id,
                target_item_type="project",
                target_item_id=project_id,
                relationship_type="supports",
                description="Research task supports project goals",
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to link research to project via bridge: {e}")
            return False

    async def publish_research_event(
        self,
        event_type: str,
        data: Dict[str, Any],
    ) -> bool:
        """
        Publish a research event via DopeconBridge.
        
        Args:
            event_type: Event type (will be prefixed with "research.")
            data: Event data
            
        Returns:
            True if successful
        """
        try:
            await self.client.publish_event(
                event_type=f"research.{event_type}",
                data=data,
                source="gpt-researcher",
            )
            return True
        except Exception as e:
            logger.error(f"Failed to publish research event: {e}")
            return False
