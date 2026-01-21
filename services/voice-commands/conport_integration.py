#!/usr/bin/env python3
"""
ConPort Integration for Voice Commands
Stores decomposed tasks in ConPort knowledge graph
"""

import asyncio
import json
import httpx
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class VoiceConPortIntegration:
    """Integrate voice-decomposed tasks with ConPort"""

    def __init__(self, conport_url: str = "http://localhost:3004"):
        self.conport_url = conport_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=10.0)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def store_voice_decomposition(self,
                                       user_id: str,
                                       original_task: str,
                                       decomposition: Dict[str, Any],
                                       workspace_id: str = "/Users/hue/code/dopemux-mvp") -> Dict[str, Any]:
        """Store voice-decomposed tasks in ConPort"""

        try:
            # Create a decision record for the voice decomposition
            decision_data = {
                "summary": f"Voice decomposition: {original_task[:50]}...",
                "rationale": f"User requested voice decomposition of task using Zen MCP analysis. Generated {len(decomposition.get('sub_tasks', []))} ADHD-optimized sub-tasks.",
                "implementation_details": json.dumps({
                    "voice_input": original_task,
                    "decomposition": decomposition,
                    "zen_mcp_used": True,
                    "adhd_optimized": True
                }),
                "tags": ["voice-commands", "task-decomposition", "zen-mcp", "adhd-optimization"]
            }

            # Store decision in ConPort
            response = await self.client.post(
                f"{self.conport_url}/api/v1/decisions",
                json=decision_data,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code != 200:
                logger.warning(f"Failed to store decision in ConPort: {response.status_code}")
                return {"success": False, "error": "Failed to store in ConPort"}

            decision_result = response.json()

            # Create progress entries for each sub-task
            sub_tasks = decomposition.get("sub_tasks", [])
            created_tasks = []

            for i, sub_task in enumerate(sub_tasks):
                task_data = {
                    "description": f"{sub_task['description']} (Voice decomposed sub-task {i+1})",
                    "status": "TODO",
                    "parent_id": None,  # Could link to parent task if known
                    "metadata": {
                        "voice_decomposition": True,
                        "original_task": original_task,
                        "estimated_time": sub_task.get("estimated_time", 25),
                        "complexity_score": sub_task.get("complexity_score", 0.5),
                        "accommodations": sub_task.get("accommodations", ""),
                        "zen_mcp_generated": True
                    }
                }

                # Store progress entry
                progress_response = await self.client.post(
                    f"{self.conport_url}/api/v1/progress",
                    json=task_data,
                    headers={"Content-Type": "application/json"}
                )

                if progress_response.status_code == 200:
                    created_tasks.append(progress_response.json())
                else:
                    logger.warning(f"Failed to create sub-task {i+1}: {progress_response.status_code}")

            # Link decision to progress entries
            for task in created_tasks:
                link_data = {
                    "source_item_type": "decision",
                    "source_item_id": str(decision_result.get("id", "")),
                    "target_item_type": "progress_entry",
                    "target_item_id": str(task.get("id", "")),
                    "relationship_type": "generated_sub_tasks",
                    "description": "Voice decomposition generated these ADHD-optimized sub-tasks"
                }

                await self.client.post(
                    f"{self.conport_url}/api/v1/links",
                    json=link_data,
                    headers={"Content-Type": "application/json"}
                )

            return {
                "success": True,
                "decision_id": decision_result.get("id"),
                "sub_tasks_created": len(created_tasks),
                "sub_task_ids": [task.get("id") for task in created_tasks]
            }

        except Exception as e:
            logger.error(f"ConPort integration failed: {e}")
            return {"success": False, "error": str(e)}

async def test_integration():
    """Test the ConPort integration"""
    async with VoiceConPortIntegration() as integration:
        test_decomposition = {
            "complexity_score": 0.6,
            "estimated_total_time": 45,
            "sub_tasks": [
                {
                    "description": "Research authentication patterns",
                    "estimated_time": 15,
                    "complexity_score": 0.4,
                    "accommodations": "Set 15-minute timer, work in quiet space"
                },
                {
                    "description": "Implement core authentication logic",
                    "estimated_time": 20,
                    "complexity_score": 0.7,
                    "accommodations": "Take breaks, use noise-cancelling headphones"
                }
            ]
        }

        result = await integration.store_voice_decomposition(
            user_id="test_user",
            original_task="Implement user authentication system",
            decomposition=test_decomposition
        )

        logger.info(f"Integration test result: {result}")

if __name__ == "__main__":
    asyncio.run(test_integration())