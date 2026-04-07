"""
Task-Orchestrator MCP Tools.

MCP tool definitions for task orchestration.
"""

import logging
from typing import Any, Dict, List, Optional

from ..adhd import adhd_monitor
from ..agents import agent_coordinator
from ..core import leantime_client, redis_manager
from ..models import TaskStatus


logger = logging.getLogger(__name__)


# MCP Tool Definitions
MCP_TOOLS = [
    {
        "name": "analyze_dependencies",
        "description": "Analyze task dependencies and detect conflicts",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tasks": {
                    "type": "array",
                    "description": "List of tasks to analyze",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "title": {"type": "string"},
                            "description": {"type": "string"}
                        }
                    }
                }
            },
            "required": ["tasks"]
        }
    },
    {
        "name": "batch_tasks",
        "description": "Batch tasks into ADHD-friendly groups for focused work sessions",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Task IDs to batch"
                },
                "session_minutes": {
                    "type": "integer",
                    "default": 25,
                    "description": "Target session duration in minutes"
                }
            },
            "required": ["task_ids"]
        }
    },
    {
        "name": "get_adhd_state",
        "description": "Get current ADHD state including session duration, break needs, and cognitive load",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_task_recommendations",
        "description": "Get ADHD-aware task recommendations based on current energy and focus",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "default": 5,
                    "description": "Maximum recommendations to return"
                },
                "energy_level": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Current energy level"
                }
            }
        }
    },
    {
        "name": "record_break",
        "description": "Record that a break was taken to reset ADHD counters",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_agent_status",
        "description": "Get status of all AI agents in the coordination pool",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    }
]


async def handle_tool_call(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP tool call and return result."""
    try:
        if tool_name == "analyze_dependencies":
            return await _analyze_dependencies(arguments.get("tasks", []))
        
        elif tool_name == "batch_tasks":
            return await _batch_tasks(
                arguments.get("task_ids", []),
                arguments.get("session_minutes", 25)
            )
        
        elif tool_name == "get_adhd_state":
            return adhd_monitor.get_adhd_state()
        
        elif tool_name == "get_task_recommendations":
            return await _get_task_recommendations(
                arguments.get("limit", 5),
                arguments.get("energy_level")
            )
        
        elif tool_name == "record_break":
            adhd_monitor.record_break()
            return {"success": True, "message": "Break recorded"}
        
        elif tool_name == "get_agent_status":
            return agent_coordinator.get_agent_status()
        
        else:
            return {"error": f"Unknown tool: {tool_name}"}

    except Exception as e:
        logger.error(f"Tool call failed: {tool_name} - {e}")
        return {"error": str(e)}


async def _analyze_dependencies(tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze task dependencies."""
    if not tasks:
        return {"dependencies": [], "conflicts": []}

    dependencies = []
    conflicts = []

    # Simple keyword-based dependency detection
    for i, task in enumerate(tasks):
        task_id = task.get("id", f"task_{i}")
        title = task.get("title", "").lower()
        description = task.get("description", "").lower()
        text = f"{title} {description}"

        # Check for dependency keywords referencing other tasks
        for j, other_task in enumerate(tasks):
            if i == j:
                continue
            other_title = other_task.get("title", "").lower()
            other_id = other_task.get("id", f"task_{j}")
            
            # Basic keyword matching
            if other_title and other_title in text:
                dependencies.append({
                    "task_id": task_id,
                    "depends_on": [other_id],
                    "confidence": 0.7
                })

    return {
        "dependencies": dependencies,
        "conflicts": conflicts,
        "analyzed_count": len(tasks)
    }


async def _batch_tasks(task_ids: List[str], session_minutes: int) -> Dict[str, Any]:
    """Batch tasks into ADHD-friendly groups."""
    if not task_ids:
        return {"batches": []}

    # Simple batching: group by estimated session capacity
    batch_size = max(1, session_minutes // 10)  # ~10 min per task
    batches = []
    
    for i in range(0, len(task_ids), batch_size):
        batch = task_ids[i:i + batch_size]
        batches.append({
            "batch_id": f"batch_{i // batch_size + 1}",
            "tasks": batch,
            "estimated_minutes": len(batch) * 10,
            "break_after": True
        })

    return {
        "batches": batches,
        "total_batches": len(batches),
        "session_minutes": session_minutes
    }


async def _get_task_recommendations(limit: int, energy_level: Optional[str] = None) -> Dict[str, Any]:
    """Get ADHD-aware task recommendations."""
    adhd_state = adhd_monitor.get_adhd_state()
    
    recommendations = []
    
    # If break needed, recommend taking a break first
    if adhd_state.get("break_needed"):
        recommendations.append({
            "id": "break",
            "title": "Take a Break",
            "priority": "high",
            "reason": "Session duration exceeded recommended limit",
            "estimated_minutes": 10
        })

    # Add placeholder recommendations based on energy
    energy = energy_level or "medium"
    if energy == "low":
        recommendations.append({
            "id": "review",
            "title": "Review Documentation",
            "priority": "low",
            "reason": "Low-energy task suitable for current state",
            "estimated_minutes": 15
        })
    elif energy == "high":
        recommendations.append({
            "id": "implement",
            "title": "Feature Implementation",
            "priority": "high",
            "reason": "High-energy task for focused work",
            "estimated_minutes": 25
        })

    return {
        "recommendations": recommendations[:limit],
        "adhd_state": adhd_state,
        "energy_level": energy
    }
