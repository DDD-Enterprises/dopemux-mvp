#!/usr/bin/env python3
"""
Voice Commands DopeconBridge Adapter

Replaces direct ConPort HTTP calls with DopeconBridge client usage.
All ConPort interactions now flow through the DopeconBridge for
proper cross-plane coordination and event tracking.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add shared modules to path
SHARED_DIR = Path(__file__).parent.parent / "shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from dopecon_bridge_client import (
    AsyncDopeconBridgeClient,
    DopeconBridgeConfig,
)

logger = logging.getLogger(__name__)


class VoiceCommandsBridgeAdapter:
    """
    DopeconBridge adapter for voice commands service.
    
    Replaces VoiceConPortIntegration with bridge-backed implementation.
    """

    def __init__(
        self,
        workspace_id: str,
        base_url: str = None,
        token: str = None,
    ):
        """
        Initialize adapter with DopeconBridge client.

        Args:
            workspace_id: Workspace identifier
            base_url: DopeconBridge URL (defaults from env)
            token: Optional auth token (defaults from env)
        """
        self.workspace_id = workspace_id
        
        config = DopeconBridgeConfig.from_env()
        if base_url:
            config = DopeconBridgeConfig(
                base_url=base_url,
                token=token or config.token,
                source_plane="cognitive_plane",
            )
        
        self.client = AsyncDopeconBridgeClient(config=config)
        logger.info(
            f"✅ Voice Commands DopeconBridge adapter initialized "
            f"(workspace: {workspace_id})"
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def store_voice_decomposition(
        self,
        user_id: str,
        original_task: str,
        decomposition: Dict[str, Any],
        workspace_id: str = None,
    ) -> Dict[str, Any]:
        """
        Store voice-decomposed tasks via DopeconBridge.
        
        Creates:
        - Decision record for the decomposition
        - Progress entries for each sub-task
        - Links connecting decisions to tasks
        
        Args:
            user_id: User who created the decomposition
            original_task: Original task description
            decomposition: Decomposition result from voice processor
            workspace_id: Optional workspace override
            
        Returns:
            Result dict with success status and IDs
        """
        workspace = workspace_id or self.workspace_id

        try:
            # Publish event for voice decomposition started
            await self.client.publish_event(
                event_type="voice.decomposition.started",
                data={
                    "user_id": user_id,
                    "task": original_task,
                    "sub_task_count": len(decomposition.get("sub_tasks", [])),
                },
                source="voice-commands",
            )

            # Create decision record via bridge
            decision_data = await self.client.create_decision(
                summary=f"Voice decomposition: {original_task[:50]}...",
                rationale=(
                    f"User requested voice decomposition of task using Zen MCP analysis. "
                    f"Generated {len(decomposition.get('sub_tasks', []))} "
                    f"ADHD-optimized sub-tasks."
                ),
                implementation_details=json.dumps({
                    "voice_input": original_task,
                    "decomposition": decomposition,
                    "zen_mcp_used": True,
                    "adhd_optimized": True,
                }, indent=2),
                tags=[
                    "voice-commands",
                    "task-decomposition",
                    "zen-mcp",
                    "adhd-optimization",
                ],
                workspace_id=workspace,
            )

            decision_id = decision_data.get("id")
            if not decision_id:
                logger.warning("No decision ID returned from bridge")
                return {"success": False, "error": "Failed to create decision"}

            # Create progress entries for sub-tasks
            sub_tasks = decomposition.get("sub_tasks", [])
            created_tasks = []

            for i, sub_task in enumerate(sub_tasks):
                task_result = await self.client.create_progress_entry(
                    description=(
                        f"{sub_task['description']} "
                        f"(Voice decomposed sub-task {i+1})"
                    ),
                    status="TODO",
                    metadata={
                        "voice_decomposition": True,
                        "original_task": original_task,
                        "estimated_time": sub_task.get("estimated_time", 25),
                        "complexity_score": sub_task.get("complexity_score", 0.5),
                        "accommodations": sub_task.get("accommodations", ""),
                        "zen_mcp_generated": True,
                        "user_id": user_id,
                    },
                    workspace_id=workspace,
                )

                task_id = task_result.get("id")
                if task_id:
                    created_tasks.append(task_result)

                    # Link decision to task
                    try:
                        await self.client.create_link(
                            source_item_type="decision",
                            source_item_id=str(decision_id),
                            target_item_type="progress_entry",
                            target_item_id=str(task_id),
                            relationship_type="generated_sub_tasks",
                            description=(
                                "Voice decomposition generated these "
                                "ADHD-optimized sub-tasks"
                            ),
                        )
                    except Exception as e:
                        logger.warning(f"Failed to link decision to task: {e}")
                else:
                    logger.warning(f"Failed to create sub-task {i+1}")

            # Publish completion event
            await self.client.publish_event(
                event_type="voice.decomposition.completed",
                data={
                    "user_id": user_id,
                    "decision_id": decision_id,
                    "sub_tasks_created": len(created_tasks),
                    "workspace_id": workspace,
                },
                source="voice-commands",
            )

            return {
                "success": True,
                "decision_id": decision_id,
                "sub_tasks_created": len(created_tasks),
                "sub_task_ids": [task.get("id") for task in created_tasks],
            }

        except Exception as exc:
            logger.error(f"Voice decomposition storage failed: {exc}")
            
            # Publish failure event
            try:
                await self.client.publish_event(
                    event_type="voice.decomposition.failed",
                    data={
                        "user_id": user_id,
                        "task": original_task,
                        "error": str(exc),
                    },
                    source="voice-commands",
                )
            except Exception as publish_exc:
                logger.error(f"Failed to publish voice decomposition failure event: {publish_exc}")
            return {"success": False, "error": str(exc)}
