#!/usr/bin/env python3
"""
Voice Task Decomposer - ADHD-Optimized Voice Commands for Task Breakdown
Integrates with Zen MCP for intelligent task decomposition and complexity scoring.
"""

import asyncio
import json
import logging
import os
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VoiceTaskDecomposer:
    """Voice-activated task decomposition using Zen MCP"""

    def __init__(self, zen_url: str = "http://localhost:3003"):
        self.zen_url = zen_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=30.0)
        self.adhd_engine_url = "http://localhost:8095"

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def process_voice_command(self, voice_input: str, user_id: str = "default") -> Dict[str, Any]:
        """
        Process voice command for task decomposition.

        Expected formats:
        - "decompose task X" or "break down task X"
        - "decompose the authentication implementation"
        - "break down this complex feature"
        """
        try:
            # Extract task description from voice input
            task_description = self._extract_task_description(voice_input)

            if not task_description:
                return {
                    "success": False,
                    "response": "I couldn't understand the task you want to decompose. Please say something like 'decompose the authentication task' or 'break down this feature'."
                }

            # Get ADHD context for personalized decomposition
            adhd_context = await self._get_adhd_context(user_id)

            # Use Zen MCP for intelligent task decomposition
            decomposition = await self._decompose_with_zen(task_description, adhd_context)

            # Format voice response
            voice_response = self._format_voice_response(decomposition, task_description)

            return {
                "success": True,
                "task_description": task_description,
                "decomposition": decomposition,
                "voice_response": voice_response,
                "sub_tasks": decomposition.get("sub_tasks", [])
            }

        except Exception as e:
            logger.error(f"Voice command processing failed: {e}")
            return {
                "success": False,
                "response": f"Sorry, I encountered an error processing your voice command: {str(e)}"
            }

    def _extract_task_description(self, voice_input: str) -> Optional[str]:
        """Extract task description from voice input using pattern matching"""

        # Common patterns for task decomposition requests
        patterns = [
            r"(?:decompose|break down|split up|divide)\s+(?:the\s+)?(?:task\s+)?(.+)",
            r"(?:decompose|break down|split up|divide)\s+(.+)",
            r"(?:how\s+(?:do|should)\s+i)\s+(.+)",
            r"(?:what\s+(?:are|is)\s+the\s+steps\s+(?:for|to))\s+(.+)"
        ]

        for pattern in patterns:
            match = re.search(pattern, voice_input, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    async def _get_adhd_context(self, user_id: str) -> Dict[str, Any]:
        """Get ADHD context for personalized task decomposition"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.adhd_engine_url}/api/v1/attention-state/{user_id}")
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.warning(f"Could not get ADHD context: {e}")

        return {"attention_state": "focused", "focus_duration": 25}

    async def _decompose_with_zen(self, task_description: str, adhd_context: Dict[str, Any]) -> Dict[str, Any]:
        """Use Zen MCP for intelligent task decomposition"""

        # Prepare prompt for Zen MCP
        prompt = f"""
        Analyze and decompose this task for an ADHD developer: "{task_description}"

        ADHD Context:
        - Attention State: {adhd_context.get('attention_state', 'unknown')}
        - Focus Duration: {adhd_context.get('focus_duration', 25)} minutes
        - Current Energy: Consider the developer's current cognitive state

        Provide:
        1. Overall task complexity (0.0-1.0 scale)
        2. Recommended session duration
        3. 3-7 ADHD-optimized sub-tasks with:
           - Clear, actionable descriptions
           - Estimated time (in minutes)
           - Cognitive complexity score (0.0-1.0)
           - ADHD accommodation notes
        4. Dependencies between sub-tasks
        5. Break recommendations between sessions

        Format as JSON with keys: complexity_score, estimated_total_time, sub_tasks[], dependencies[], break_recommendations[]
        """

        try:
            # Call Zen MCP for task analysis
            zen_payload = {
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "model": "auto",
                "temperature": 0.3,
                "max_tokens": 2000
            }

            response = await self.client.post(
                f"{self.zen_url}/v1/chat/completions",
                json=zen_payload,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "{}")

                # Parse JSON response
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    # Fallback: create structured response from text
                    return self._create_fallback_decomposition(task_description, adhd_context)

            else:
                logger.warning(f"Zen MCP call failed: {response.status_code}")
                return self._create_fallback_decomposition(task_description, adhd_context)

        except Exception as e:
            logger.error(f"Zen MCP integration failed: {e}")
            return self._create_fallback_decomposition(task_description, adhd_context)

    def _create_fallback_decomposition(self, task_description: str, adhd_context: Dict[str, Any]) -> Dict[str, Any]:
        """Create basic task decomposition when Zen MCP is unavailable"""

        # Simple heuristic-based decomposition
        words = len(task_description.split())
        complexity = min(0.8, words / 50)  # Rough complexity estimate

        # Create 3-5 basic sub-tasks
        sub_tasks = [
            {
                "description": f"Plan and research {task_description}",
                "estimated_time": 15,
                "complexity_score": 0.3,
                "accommodations": "Set timer, work in quiet environment"
            },
            {
                "description": f"Implement core functionality for {task_description}",
                "estimated_time": 25,
                "complexity_score": complexity,
                "accommodations": "Take breaks every 15 minutes, use noise-cancelling headphones"
            },
            {
                "description": f"Test and refine {task_description}",
                "estimated_time": 20,
                "complexity_score": 0.4,
                "accommodations": "Work in short focused bursts, review work frequently"
            }
        ]

        return {
            "complexity_score": complexity,
            "estimated_total_time": sum(task["estimated_time"] for task in sub_tasks),
            "sub_tasks": sub_tasks,
            "dependencies": ["Complete planning before implementation", "Test after implementation"],
            "break_recommendations": ["5-minute break after planning", "10-minute break after implementation"]
        }

    def _format_voice_response(self, decomposition: Dict[str, Any], original_task: str) -> str:
        """Format decomposition results into natural voice response"""

        sub_tasks = decomposition.get("sub_tasks", [])
        total_time = decomposition.get("estimated_total_time", 0)
        complexity = decomposition.get("complexity_score", 0.5)

        # Create voice-friendly response
        response_parts = []

        # Introduction
        response_parts.append(f"I've decomposed '{original_task}' into {len(sub_tasks)} manageable tasks.")

        # Overall assessment
        if complexity < 0.3:
            response_parts.append("This appears to be a straightforward task.")
        elif complexity < 0.7:
            response_parts.append("This is a moderately complex task.")
        else:
            response_parts.append("This is quite complex - we'll break it into smaller, focused sessions.")

        response_parts.append(f"Total estimated time: {total_time} minutes.")

        # Sub-tasks
        response_parts.append("Here are the sub-tasks:")
        for i, task in enumerate(sub_tasks, 1):
            time_str = f"{task['estimated_time']} minutes"
            response_parts.append(f"{i}. {task['description']} - about {time_str}")

        # ADHD accommodations
        accommodations = []
        for task in sub_tasks:
            if "accommodations" in task:
                accommodations.extend(task["accommodations"].split(", "))

        if accommodations:
            unique_accommodations = list(set(accommodations[:3]))  # Limit to 3
            response_parts.append(f"ADHD accommodations: {', '.join(unique_accommodations)}")

        # Break recommendations
        breaks = decomposition.get("break_recommendations", [])
        if breaks:
            response_parts.append(f"Break recommendations: {', '.join(breaks[:2])}")

        return " ".join(response_parts)

async def main():
    """Command-line interface for testing voice task decomposition"""
    import argparse

    parser = argparse.ArgumentParser(description="Voice Task Decomposer")
    parser.add_argument("voice_input", help="Voice input text to process")
    parser.add_argument("--user-id", default="default", help="User ID for personalization")
    parser.add_argument("--zen-url", default="http://localhost:3003", help="Zen MCP URL")

    args = parser.parse_args()

    async with VoiceTaskDecomposer(args.zen_url) as decomposer:
        result = await decomposer.process_voice_command(args.voice_input, args.user_id)

        if result["success"]:
            print("✅ Task Decomposition Successful")
            print(f"📝 Original Task: {result['task_description']}")
            print(f"🎯 Voice Response: {result['voice_response']}")
            print("\n📋 Sub-tasks:")
            for i, task in enumerate(result['sub_tasks'], 1):
                print(f"  {i}. {task['description']} ({task.get('estimated_time', '?')} min)")
                if 'accommodations' in task:
                    print(f"     💡 {task['accommodations']}")
        else:
            print(f"❌ Failed: {result['response']}")

if __name__ == "__main__":
    asyncio.run(main())